//! Turns a finished `runner::RunResult` into a persisted `RunSummary` and
//! a `NodeState` update — the classification pure file-system inference
//! (`inference::stage_rules`) cannot do on its own: "never ran" and
//! "ran, asked a question, produced nothing" both look like `Idle` on
//! disk. This module is what makes the second case distinguishable, and
//! makes it survive the watcher's next recompute (`pipeline_state`) by
//! persisting the distinguishing signal to disk rather than only in memory.

use std::path::Path;

use crate::agentrun::runner::RunResult;
use crate::agentrun::stream_parser::{self, StreamEvent};
use crate::domain::config_file::PermissionProfile;
use crate::domain::pipeline_def::slot;
use crate::domain::run_summary::{RunOutcome, RunSummary};
use crate::error::AppResult;
use crate::inference::stage_rules;
use crate::store::atomic_write::{write_json_atomic, write_text_atomic};
use crate::store::orchestrator_dir;

pub(crate) fn find_run_finished(events: &[StreamEvent]) -> Option<(bool, f64, String)> {
    events.iter().rev().find_map(|e| match e {
        StreamEvent::RunFinished {
            is_error,
            total_cost_usd,
            session_id,
            ..
        } => Some((*is_error, *total_cost_usd, session_id.clone())),
        _ => None,
    })
}

pub(crate) fn find_session_started(events: &[StreamEvent]) -> Option<String> {
    events.iter().find_map(|e| match e {
        StreamEvent::SessionStarted { session_id, .. } => Some(session_id.clone()),
        _ => None,
    })
}

pub(crate) fn last_assistant_text(events: &[StreamEvent]) -> Option<String> {
    events.iter().rev().find_map(|e| match e {
        StreamEvent::AssistantText { text, .. } => Some(text.clone()),
        _ => None,
    })
}

/// AC-E6-27 — a process that never got a session going has no `stream-json`
/// content at all to explain why (sai model, thiếu quyền, ...); stderr is
/// the only place the CLI would have said. Falls back to a generic message
/// only if stderr itself was empty (e.g. the process was killed before it
/// could write anything).
fn startup_failure_message(stderr: &str, exit_code: Option<i32>) -> String {
    let trimmed = stderr.trim();
    let code_suffix = exit_code
        .map(|code| format!(" (exit code {code})"))
        .unwrap_or_default();
    if trimmed.is_empty() {
        format!(
            "Agent không khởi động được{code_suffix} — không có session nào bắt đầu và không có thông tin lỗi từ stderr"
        )
    } else {
        format!("Agent không khởi động được{code_suffix}: {trimmed}")
    }
}

/// `feature_dir`/`runs_dir` are the same two paths `infer_feature_state`
/// itself takes — this reuses `stage_rules::artifact_paths_for_slot` so
/// "did this run produce the expected artifact" can never disagree with
/// what the Pipeline Board would independently compute from disk.
fn classify_outcome(
    result: &RunResult,
    feature_dir: &Path,
    runs_dir: &Path,
    slot_id: &str,
) -> (RunOutcome, Option<String>) {
    if result.timed_out {
        return (
            RunOutcome::Timeout,
            Some("Agent bị dừng do vượt quá thời gian chờ (timeout)".to_string()),
        );
    }

    let Some((is_error, _cost, _session)) = find_run_finished(&result.events) else {
        // AC-E6-27: distinguish a startup failure (no session ever started —
        // sai model, thiếu quyền, CLI auth lỗi, ...) from a mid-run crash
        // (session started fine, process still ended without a `result`
        // line) — both looked identical before `RunResult` carried stderr.
        let message = if find_session_started(&result.events).is_none() {
            startup_failure_message(&result.stderr, result.exit_code)
        } else {
            match result.exit_code {
                Some(code) => format!(
                    "Process kết thúc giữa chừng (đã bắt đầu session, exit code {code}) mà không có dòng result"
                ),
                None => "Process kết thúc giữa chừng (đã bắt đầu session) mà không có dòng result"
                    .to_string(),
            }
        };
        return (RunOutcome::Failed, Some(message));
    };

    if is_error {
        return (RunOutcome::Failed, last_assistant_text(&result.events));
    }

    let last_message = last_assistant_text(&result.events);

    // Dev slots (backend/frontend/mobile) edit arbitrary files inside an
    // external repo — there is no single predictable path
    // `artifact_paths_for_slot` can check for existence, so it always
    // returns empty for them (see its own match arm). Use the agent's own
    // completion signal instead: `.claude/agents/{backend,frontend,mobile}
    // -agent.md` each mandate `## Output` to start with `✅ task-x-y hoàn
    // thành` on success — a genuine clarifying question never starts this
    // way. If that convention changes in those files, this check must
    // change with it.
    if matches!(slot_id, s if s == slot::BACKEND || s == slot::FRONTEND || s == slot::MOBILE) {
        let completed = last_message
            .as_deref()
            .is_some_and(|t| t.trim_start().starts_with('✅'));
        return if completed {
            (RunOutcome::Done, None)
        } else {
            (RunOutcome::WaitingInput, last_message)
        };
    }

    let produced_artifact =
        !stage_rules::artifact_paths_for_slot(feature_dir, runs_dir, slot_id).is_empty();
    if produced_artifact {
        (RunOutcome::Done, None)
    } else {
        (RunOutcome::WaitingInput, last_message)
    }
}

/// Builds the `RunSummary` for a finished run — pure, no I/O. `attempt` is
/// the caller's responsibility (see `next_attempt`) since it depends on
/// what was previously on disk, which this function deliberately doesn't
/// read itself (keeps it testable without a filesystem).
pub fn build_run_summary(
    result: &RunResult,
    feature_dir: &Path,
    runs_dir: &Path,
    slot_id: &str,
    started_at: String,
    ended_at: String,
    attempt: u32,
) -> RunSummary {
    let (outcome, last_message) = classify_outcome(result, feature_dir, runs_dir, slot_id);
    let session_id = find_run_finished(&result.events)
        .map(|(_, _, session_id)| session_id)
        .or_else(|| find_session_started(&result.events))
        .unwrap_or_default();
    let cost_usd = find_run_finished(&result.events)
        .map(|(_, cost, _)| cost)
        .unwrap_or(0.0);

    RunSummary {
        outcome,
        session_id,
        cost_usd,
        started_at,
        ended_at,
        last_message,
        attempt,
        // Set by `finalize_run`, the only real caller — kept out of this
        // pure classification function on purpose (see its own doc comment).
        prompt: None,
    }
}

/// 1 for a `(feature, slot)` with no prior run recorded; otherwise the
/// previous attempt number + 1.
pub fn next_attempt(agents_root: &Path, feature: &str, slot: &str) -> u32 {
    read_run_summary(agents_root, feature, slot)
        .map(|s| s.attempt + 1)
        .unwrap_or(1)
}

pub fn write_run_summary(
    agents_root: &Path,
    feature: &str,
    slot: &str,
    summary: &RunSummary,
) -> AppResult<()> {
    let path = orchestrator_dir::agent_run_summary_path(agents_root, feature, slot);
    write_json_atomic(&path, summary)
}

/// Best-effort — a missing or corrupt summary is treated as "no prior run"
/// rather than an error, consistent with how `pipeline_state` already
/// treats a missing/corrupt `state.json`.
pub fn read_run_summary(agents_root: &Path, feature: &str, slot: &str) -> Option<RunSummary> {
    let path = orchestrator_dir::agent_run_summary_path(agents_root, feature, slot);
    let raw = std::fs::read_to_string(path).ok()?;
    serde_json::from_str(&raw).ok()
}

/// Persists the raw `stream-json` lines verbatim, one per line — lets a
/// finished run's Log Console be re-opened later without keeping parsed
/// events around in memory.
pub fn write_run_log(
    agents_root: &Path,
    feature: &str,
    slot: &str,
    raw_lines: &[String],
) -> AppResult<()> {
    let path = orchestrator_dir::agent_run_log_path(agents_root, feature, slot);
    write_text_atomic(&path, &raw_lines.join("\n"))
}

/// Re-parses a previously written `log.jsonl` back into `StreamEvent`s —
/// AC-E2-20: the Log Console must be reconstructable after the app restarts,
/// not just while `liveLines` is still live in React state. Best-effort like
/// `read_run_summary`: a missing file (no run yet) is an empty log, not an
/// error.
pub fn read_run_log(agents_root: &Path, feature: &str, slot: &str) -> AppResult<Vec<StreamEvent>> {
    let path = orchestrator_dir::agent_run_log_path(agents_root, feature, slot);
    let raw = match std::fs::read_to_string(path) {
        Ok(raw) => raw,
        Err(_) => return Ok(Vec::new()),
    };
    Ok(raw.lines().flat_map(stream_parser::parse_line).collect())
}

/// Identifies which `(feature, slot)` a run belongs to and where to look
/// for its expected artifact — bundled since every `run_log` entry point
/// needs the same paths/ids together.
pub struct RunContext<'a> {
    pub agents_root: &'a Path,
    pub feature: &'a str,
    pub slot: &'a str,
    pub feature_dir: &'a Path,
    pub runs_dir: &'a Path,
    /// AC-E1-16 — which directory a `WriteScoped` run was supposed to be
    /// confined to. Ignored for other profiles.
    pub permission: PermissionProfile,
}

/// AC-E1-16, detective half — verified via a live spike
/// (`spawn::tests::bypass_permissions_allows_writes_entirely_outside_cwd`)
/// that `--permission-mode bypassPermissions` (unconditional for every
/// headless spawn — see `spawn`'s own top doc comment) disables the CLI's
/// own directory-scoping checks entirely, so nothing this app passes on the
/// command line can PREVENT a `WriteScoped` agent from writing outside
/// `feature_dir`. This instead looks at the `Write`/`Edit` tool calls
/// already captured in the run's events and flags any whose `file_path`
/// falls outside `feature_dir` — after the fact, never claiming to have
/// blocked anything it didn't.
fn writes_outside_scope(events: &[StreamEvent], feature_dir: &Path) -> Vec<String> {
    events
        .iter()
        .filter_map(|event| match event {
            StreamEvent::ToolCall {
                tool_name, input, ..
            } if tool_name == "Write" || tool_name == "Edit" => {
                input.get("file_path").and_then(|v| v.as_str())
            }
            _ => None,
        })
        .filter(|path| orchestrator_dir::assert_within(Path::new(path), feature_dir).is_err())
        .map(str::to_string)
        .collect()
}

/// The CLI's resolved model id from the run's own `SessionStarted` event —
/// AC-E6-18's "model thực tế đã dùng", as opposed to whatever config said.
fn find_session_model(events: &[StreamEvent]) -> Option<String> {
    events.iter().find_map(|e| match e {
        StreamEvent::SessionStarted { model, .. } => Some(model.clone()),
        _ => None,
    })
}

fn append_warning(summary: &mut RunSummary, warning: String) {
    summary.last_message = Some(match summary.last_message.take() {
        Some(existing) => format!("{existing}\n{warning}"),
        None => warning,
    });
}

/// Slots the kit gives no artifact path of its own — AC-E3-05 has the app
/// define and write one, under `runs_dir`, in the filename
/// `classify_outcome`'s `stage_rules::artifact_paths_for_slot` call already
/// expects. Keep this in sync with that function's own `QC_AUTOMATION`
/// match arm — same filename on both sides.
fn runs_dir_report_filename(slot_id: &str) -> Option<&'static str> {
    match slot_id {
        s if s == slot::QC_AUTOMATION => Some("execution-report.md"),
        _ => None,
    }
}

/// Saves the agent's own final report as that slot's AC-E3-05 artifact —
/// MUST run before `build_run_summary`/`classify_outcome`, which reads it
/// right back to decide `Done`. Best-effort: a write failure here should
/// not fail the whole run finalization, only leave the slot `WaitingInput`
/// (no worse than before this existed) — the same tolerance
/// `persist_and_notify`'s own best-effort writes already have elsewhere in
/// this module.
fn write_runs_dir_report(runs_dir: &Path, feature: &str, slot_id: &str, events: &[StreamEvent]) {
    let Some(filename) = runs_dir_report_filename(slot_id) else {
        return;
    };
    let Some(report) = last_assistant_text(events) else {
        return;
    };
    let path = runs_dir
        .join(orchestrator_dir::runs_dir_run_id(feature, slot_id))
        .join(filename);
    let _ = write_text_atomic(&path, &report);
}

/// Ties classification + persistence together — the single call site
/// `commands::agentrun::run_to_completion` uses once a `RunResult` is in
/// hand. Increments `attempt` itself (reads whatever was previously on
/// disk), so callers never need to track retry counts separately.
/// `extra_warning` is a caller-computed advisory (Memory Update Gate,
/// AC-E4-30/31) appended to `last_message` — never affects the outcome.
pub fn finalize_run(
    ctx: &RunContext,
    result: &RunResult,
    started_at: String,
    ended_at: String,
    prompt: &str,
    extra_warning: Option<String>,
) -> AppResult<RunSummary> {
    let attempt = next_attempt(ctx.agents_root, ctx.feature, ctx.slot);
    write_runs_dir_report(ctx.runs_dir, ctx.feature, ctx.slot, &result.events);
    let mut summary = build_run_summary(
        result,
        ctx.feature_dir,
        ctx.runs_dir,
        ctx.slot,
        started_at,
        ended_at,
        attempt,
    );
    // AC-E2-13 — persisted so a Retry after `Failed` can replay this exact
    // input instead of making the user re-pick a folder.
    summary.prompt = Some(prompt.to_string());

    if ctx.permission == PermissionProfile::WriteScoped {
        let escaped = writes_outside_scope(&result.events, ctx.feature_dir);
        if !escaped.is_empty() {
            append_warning(
                &mut summary,
                format!(
                    "⚠ AC-E1-16: agent (write-scoped) đã ghi ngoài phạm vi cho phép ({}): {}",
                    ctx.feature_dir.display(),
                    escaped.join(", ")
                ),
            );
        }
    }

    if let Some(warning) = extra_warning {
        append_warning(&mut summary, warning);
    }

    write_run_summary(ctx.agents_root, ctx.feature, ctx.slot, &summary)?;
    // Skipped when the reader thread already wrote every line to the same
    // path as it arrived — rewriting it would mean holding the whole log in
    // memory a second time just to reproduce what is already there.
    if !result.log_already_on_disk {
        write_run_log(ctx.agents_root, ctx.feature, ctx.slot, &result.raw_lines)?;
    }

    // AC-E6-04/10 — the run finished normally, so the in-flight durability
    // marker (written pre-spawn by `run_to_completion`) no longer applies.
    let _ = std::fs::remove_file(orchestrator_dir::agent_run_marker_path(
        ctx.agents_root,
        ctx.feature,
        ctx.slot,
    ));

    // AC-E6-12..18 — the immutable history row Reports aggregates.
    // Best-effort: a history-write failure must never fail the run itself.
    let record = crate::domain::run_history::RunHistoryRecord {
        feature: ctx.feature.to_string(),
        slot: ctx.slot.to_string(),
        model: find_session_model(&result.events),
        outcome: summary.outcome,
        // AC-E6-13 — None (not 0.0) when no result line carried a cost.
        cost_usd: find_run_finished(&result.events).map(|(_, cost, _)| cost),
        started_at: summary.started_at.clone(),
        ended_at: summary.ended_at.clone(),
        attempt: summary.attempt,
    };
    let _ = crate::store::run_history::write_record(
        &orchestrator_dir::run_history_dir(ctx.agents_root),
        &record,
    );

    Ok(summary)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn write(path: &Path, content: &str) {
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, content).unwrap();
    }

    fn result_with(events: Vec<StreamEvent>) -> RunResult {
        RunResult {
            events,
            raw_lines: vec![],
            log_already_on_disk: false,
            timed_out: false,
            exit_code: None,
            stderr: String::new(),
            stdout_drained: true,
        }
    }

    #[test]
    fn timed_out_run_classifies_as_timeout_regardless_of_events() {
        let tmp = tempfile::tempdir().unwrap();
        let mut result = result_with(vec![]);
        result.timed_out = true;

        let summary = build_run_summary(
            &result,
            &tmp.path().join("feature"),
            &tmp.path().join("runs"),
            "ba",
            "t0".to_string(),
            "t1".to_string(),
            1,
        );
        assert_eq!(summary.outcome, RunOutcome::Timeout);
        assert!(summary.last_message.is_some());
    }

    #[test]
    fn process_exit_without_a_result_line_classifies_as_failed() {
        let tmp = tempfile::tempdir().unwrap();
        let result = result_with(vec![StreamEvent::SessionStarted {
            session_id: "s1".to_string(),
            model: "claude-haiku-4-5".to_string(),
        }]);

        let summary = build_run_summary(
            &result,
            &tmp.path().join("feature"),
            &tmp.path().join("runs"),
            "ba",
            "t0".to_string(),
            "t1".to_string(),
            1,
        );
        assert_eq!(summary.outcome, RunOutcome::Failed);
        // Falls back to the session id it did see, even without a result line.
        assert_eq!(summary.session_id, "s1");
        // AC-E6-27: a session DID start — this must read as a mid-run crash,
        // not a startup failure.
        assert!(summary
            .last_message
            .as_deref()
            .unwrap()
            .contains("giữa chừng"));
    }

    #[test]
    fn no_session_started_classifies_as_startup_failure_using_stderr() {
        let tmp = tempfile::tempdir().unwrap();
        let mut result = result_with(vec![]);
        result.stderr = "Error: model 'bogus-model' not found\n".to_string();

        let summary = build_run_summary(
            &result,
            &tmp.path().join("feature"),
            &tmp.path().join("runs"),
            "ba",
            "t0".to_string(),
            "t1".to_string(),
            1,
        );
        assert_eq!(summary.outcome, RunOutcome::Failed);
        assert!(summary
            .last_message
            .as_deref()
            .unwrap()
            .contains("model 'bogus-model' not found"));
    }

    #[test]
    fn no_session_started_and_empty_stderr_falls_back_to_generic_message() {
        let tmp = tempfile::tempdir().unwrap();
        let result = result_with(vec![]);

        let summary = build_run_summary(
            &result,
            &tmp.path().join("feature"),
            &tmp.path().join("runs"),
            "ba",
            "t0".to_string(),
            "t1".to_string(),
            1,
        );
        assert_eq!(summary.outcome, RunOutcome::Failed);
        assert!(summary
            .last_message
            .as_deref()
            .unwrap()
            .contains("không khởi động được"));
    }

    #[test]
    fn result_line_with_is_error_classifies_as_failed_with_cost_and_session() {
        let tmp = tempfile::tempdir().unwrap();
        let result = result_with(vec![
            StreamEvent::AssistantText {
                message_id: "m1".to_string(),
                text: "Something went wrong".to_string(),
            },
            StreamEvent::RunFinished {
                is_error: true,
                total_cost_usd: 0.02,
                session_id: "s1".to_string(),
                stop_reason: None,
            },
        ]);

        let summary = build_run_summary(
            &result,
            &tmp.path().join("feature"),
            &tmp.path().join("runs"),
            "ba",
            "t0".to_string(),
            "t1".to_string(),
            1,
        );
        assert_eq!(summary.outcome, RunOutcome::Failed);
        assert_eq!(summary.cost_usd, 0.02);
        assert_eq!(summary.session_id, "s1");
        assert_eq!(
            summary.last_message.as_deref(),
            Some("Something went wrong")
        );
    }

    #[test]
    fn success_without_expected_artifact_classifies_as_waiting_input() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");

        let result = result_with(vec![
            StreamEvent::AssistantText {
                message_id: "m1".to_string(),
                text: "What login methods should be supported?".to_string(),
            },
            StreamEvent::RunFinished {
                is_error: false,
                total_cost_usd: 0.03,
                session_id: "s1".to_string(),
                stop_reason: Some("end_turn".to_string()),
            },
        ]);

        let summary = build_run_summary(
            &result,
            &feature_dir,
            &runs_dir,
            "ba",
            "t0".to_string(),
            "t1".to_string(),
            1,
        );
        assert_eq!(summary.outcome, RunOutcome::WaitingInput);
        assert_eq!(
            summary.last_message.as_deref(),
            Some("What login methods should be supported?")
        );
    }

    #[test]
    fn success_with_expected_artifact_classifies_as_done() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("SPEC.md"),
            "## Mô tả nghiệp vụ\nx\n## Actors & Preconditions\nx\n## Happy Path\nx\n## Alternative Flows & Edge Cases\nx\n## Acceptance Criteria\nx\n## Out of Scope\nx\n## Screens\nx\n",
        );
        let runs_dir = tmp.path().join("runs");

        let result = result_with(vec![StreamEvent::RunFinished {
            is_error: false,
            total_cost_usd: 0.04,
            session_id: "s1".to_string(),
            stop_reason: Some("end_turn".to_string()),
        }]);

        let summary = build_run_summary(
            &result,
            &feature_dir,
            &runs_dir,
            "ba",
            "t0".to_string(),
            "t1".to_string(),
            1,
        );
        assert_eq!(summary.outcome, RunOutcome::Done);
        assert!(summary.last_message.is_none());
    }

    #[test]
    fn dev_slot_success_marker_classifies_as_done_even_with_no_artifact() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");

        let result = result_with(vec![
            StreamEvent::AssistantText {
                message_id: "m1".to_string(),
                text: "✅ task-2-1 hoàn thành\n\nFiles đã thay đổi:\n  - order.service.ts"
                    .to_string(),
            },
            StreamEvent::RunFinished {
                is_error: false,
                total_cost_usd: 0.05,
                session_id: "s1".to_string(),
                stop_reason: Some("end_turn".to_string()),
            },
        ]);

        let summary = build_run_summary(
            &result,
            &feature_dir,
            &runs_dir,
            "backend",
            "t0".to_string(),
            "t1".to_string(),
            1,
        );
        assert_eq!(summary.outcome, RunOutcome::Done);
    }

    #[test]
    fn dev_slot_without_success_marker_classifies_as_waiting_input() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");

        let result = result_with(vec![
            StreamEvent::AssistantText {
                message_id: "m1".to_string(),
                text: "Task không đủ context — order status enum có thêm giá trị nào ngoài PENDING/PAID/CANCELLED không?".to_string(),
            },
            StreamEvent::RunFinished {
                is_error: false,
                total_cost_usd: 0.02,
                session_id: "s1".to_string(),
                stop_reason: Some("end_turn".to_string()),
            },
        ]);

        let summary = build_run_summary(
            &result,
            &feature_dir,
            &runs_dir,
            "backend",
            "t0".to_string(),
            "t1".to_string(),
            1,
        );
        assert_eq!(summary.outcome, RunOutcome::WaitingInput);
        assert!(summary
            .last_message
            .as_deref()
            .unwrap()
            .contains("order status enum"));
    }

    #[test]
    fn next_attempt_is_1_when_nothing_on_disk_and_increments_after_a_write() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path();
        assert_eq!(next_attempt(agents_root, "f1", "ba"), 1);

        let summary = RunSummary {
            outcome: RunOutcome::Failed,
            session_id: "s1".to_string(),
            cost_usd: 0.01,
            started_at: "t0".to_string(),
            ended_at: "t1".to_string(),
            last_message: None,
            attempt: 1,
            prompt: None,
        };
        write_run_summary(agents_root, "f1", "ba", &summary).unwrap();
        assert_eq!(next_attempt(agents_root, "f1", "ba"), 2);
        // A different feature/slot is unaffected.
        assert_eq!(next_attempt(agents_root, "f1", "qc-automation"), 1);
        assert_eq!(next_attempt(agents_root, "f2", "ba"), 1);
    }

    #[test]
    fn write_and_read_run_summary_round_trips() {
        let tmp = tempfile::tempdir().unwrap();
        let summary = RunSummary {
            outcome: RunOutcome::WaitingInput,
            session_id: "s1".to_string(),
            cost_usd: 0.05,
            started_at: "t0".to_string(),
            ended_at: "t1".to_string(),
            last_message: Some("A question?".to_string()),
            attempt: 2,
            prompt: Some("original prompt".to_string()),
        };
        write_run_summary(tmp.path(), "f1", "ba", &summary).unwrap();
        let read = read_run_summary(tmp.path(), "f1", "ba").unwrap();
        assert_eq!(read.outcome, RunOutcome::WaitingInput);
        assert_eq!(read.attempt, 2);
    }

    #[test]
    fn read_run_summary_is_none_when_missing_or_corrupt() {
        let tmp = tempfile::tempdir().unwrap();
        assert!(read_run_summary(tmp.path(), "f1", "ba").is_none());

        let path = orchestrator_dir::agent_run_summary_path(tmp.path(), "f1", "ba");
        write(&path, "not json");
        assert!(read_run_summary(tmp.path(), "f1", "ba").is_none());
    }

    #[test]
    fn write_run_log_persists_raw_lines_joined_by_newline() {
        let tmp = tempfile::tempdir().unwrap();
        let lines = vec![
            r#"{"type":"system"}"#.to_string(),
            r#"{"type":"result"}"#.to_string(),
        ];
        write_run_log(tmp.path(), "f1", "ba", &lines).unwrap();

        let path = orchestrator_dir::agent_run_log_path(tmp.path(), "f1", "ba");
        let content = std::fs::read_to_string(path).unwrap();
        assert_eq!(content, lines.join("\n"));
    }

    #[test]
    fn read_run_log_is_empty_when_missing_and_reparses_written_lines() {
        let tmp = tempfile::tempdir().unwrap();
        assert_eq!(read_run_log(tmp.path(), "f1", "ba").unwrap(), Vec::new());

        let lines = vec![
            r#"{"type":"system","subtype":"init","session_id":"s1","model":"claude-haiku-4-5"}"#
                .to_string(),
            r#"{"type":"result","is_error":false,"total_cost_usd":0.04,"session_id":"s1","stop_reason":"end_turn"}"#
                .to_string(),
        ];
        write_run_log(tmp.path(), "f1", "ba", &lines).unwrap();

        let events = read_run_log(tmp.path(), "f1", "ba").unwrap();
        assert_eq!(
            events,
            vec![
                StreamEvent::SessionStarted {
                    session_id: "s1".to_string(),
                    model: "claude-haiku-4-5".to_string(),
                },
                StreamEvent::RunFinished {
                    is_error: false,
                    total_cost_usd: 0.04,
                    session_id: "s1".to_string(),
                    stop_reason: Some("end_turn".to_string()),
                },
            ]
        );
    }

    #[test]
    fn finalize_run_persists_summary_and_log_and_increments_attempt_on_retry() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let feature_dir = tmp.path().join("docs/features/f1");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");

        let result = RunResult {
            events: vec![
                StreamEvent::AssistantText {
                    message_id: "m1".to_string(),
                    text: "What auth provider?".to_string(),
                },
                StreamEvent::RunFinished {
                    is_error: false,
                    total_cost_usd: 0.02,
                    session_id: "s1".to_string(),
                    stop_reason: Some("end_turn".to_string()),
                },
            ],
            raw_lines: vec![r#"{"type":"result"}"#.to_string()],
            log_already_on_disk: false,
            timed_out: false,
            exit_code: Some(0),
            stderr: String::new(),
            stdout_drained: true,
        };

        let ctx = RunContext {
            agents_root: &agents_root,
            feature: "f1",
            slot: "ba",
            feature_dir: &feature_dir,
            runs_dir: &runs_dir,
            permission: PermissionProfile::WriteScoped,
        };

        let summary = finalize_run(
            &ctx,
            &result,
            "t0".to_string(),
            "t1".to_string(),
            "prompt",
            None,
        )
        .unwrap();
        assert_eq!(summary.outcome, RunOutcome::WaitingInput);
        assert_eq!(summary.attempt, 1);

        let persisted = read_run_summary(&agents_root, "f1", "ba").unwrap();
        assert_eq!(persisted.attempt, 1);
        // AC-E2-13 — the prompt survives the write/read round-trip so a
        // later Retry can replay it.
        assert_eq!(persisted.prompt.as_deref(), Some("prompt"));
        let log_path = orchestrator_dir::agent_run_log_path(&agents_root, "f1", "ba");
        assert_eq!(
            std::fs::read_to_string(log_path).unwrap(),
            r#"{"type":"result"}"#
        );

        // A retry (same feature/slot, new result) increments attempt.
        let retry_summary = finalize_run(
            &ctx,
            &result,
            "t2".to_string(),
            "t3".to_string(),
            "prompt",
            None,
        )
        .unwrap();
        assert_eq!(retry_summary.attempt, 2);
    }

    /// AC-E3-05, the actual bug report: `qc-automation` has no artifact path
    /// of its own in the kit, so before this the slot stayed `WaitingInput`
    /// forever no matter what the agent said — nothing ever wrote
    /// `execution-report.md`. `finalize_run` must now save it itself, in
    /// time for the SAME call's `classify_outcome` to see it and return
    /// `Done`.
    #[test]
    fn finalize_run_writes_the_execution_report_and_marks_the_slot_done() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let feature_dir = tmp.path().join("docs/features/f1");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");

        let result = RunResult {
            events: vec![
                StreamEvent::AssistantText {
                    message_id: "m1".to_string(),
                    text: "## Execution Report — f1\n✅ PASS — E2E suite xanh".to_string(),
                },
                StreamEvent::RunFinished {
                    is_error: false,
                    total_cost_usd: 0.02,
                    session_id: "s1".to_string(),
                    stop_reason: Some("end_turn".to_string()),
                },
            ],
            raw_lines: vec![r#"{"type":"result"}"#.to_string()],
            log_already_on_disk: false,
            timed_out: false,
            exit_code: Some(0),
            stderr: String::new(),
            stdout_drained: true,
        };

        let ctx = RunContext {
            agents_root: &agents_root,
            feature: "f1",
            slot: "qc-automation",
            feature_dir: &feature_dir,
            runs_dir: &runs_dir,
            permission: PermissionProfile::WriteScoped,
        };

        let summary = finalize_run(
            &ctx,
            &result,
            "t0".to_string(),
            "t1".to_string(),
            "prompt",
            None,
        )
        .unwrap();
        assert_eq!(summary.outcome, RunOutcome::Done);

        let report_path = runs_dir.join("f1--qc-automation/execution-report.md");
        assert_eq!(
            std::fs::read_to_string(report_path).unwrap(),
            "## Execution Report — f1\n✅ PASS — E2E suite xanh"
        );
    }

    /// A slot with no `runs_dir_report_filename` mapping (e.g. `ba`, which
    /// has its own `SPEC.md`-based artifact path) must never get a stray
    /// `runs_dir` entry written for it.
    #[test]
    fn finalize_run_writes_no_runs_dir_report_for_slots_outside_the_convention() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let feature_dir = tmp.path().join("docs/features/f1");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");

        let result = RunResult {
            events: vec![
                StreamEvent::AssistantText {
                    message_id: "m1".to_string(),
                    text: "✅ task-1-1 hoàn thành".to_string(),
                },
                StreamEvent::RunFinished {
                    is_error: false,
                    total_cost_usd: 0.02,
                    session_id: "s1".to_string(),
                    stop_reason: Some("end_turn".to_string()),
                },
            ],
            raw_lines: vec![r#"{"type":"result"}"#.to_string()],
            log_already_on_disk: false,
            timed_out: false,
            exit_code: Some(0),
            stderr: String::new(),
            stdout_drained: true,
        };

        let ctx = RunContext {
            agents_root: &agents_root,
            feature: "f1",
            slot: "backend",
            feature_dir: &feature_dir,
            runs_dir: &runs_dir,
            permission: PermissionProfile::WriteScoped,
        };

        finalize_run(&ctx, &result, "t0".to_string(), "t1".to_string(), "prompt", None).unwrap();

        assert!(!runs_dir.exists() || std::fs::read_dir(&runs_dir).unwrap().next().is_none());
    }

    #[test]
    fn writes_outside_scope_flags_only_paths_outside_feature_dir() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let outside_dir = tmp.path().join("outside");
        std::fs::create_dir_all(&outside_dir).unwrap();

        let inside_path = feature_dir.join("SPEC.md");
        std::fs::write(&inside_path, "x").unwrap();
        let outside_path = outside_dir.join("escaped.txt");
        std::fs::write(&outside_path, "x").unwrap();

        let events = vec![
            StreamEvent::ToolCall {
                message_id: "m1".to_string(),
                tool_use_id: "t1".to_string(),
                tool_name: "Write".to_string(),
                input: serde_json::json!({"file_path": inside_path.display().to_string(), "content": "x"}),
            },
            StreamEvent::ToolCall {
                message_id: "m1".to_string(),
                tool_use_id: "t2".to_string(),
                tool_name: "Write".to_string(),
                input: serde_json::json!({"file_path": outside_path.display().to_string(), "content": "x"}),
            },
            // A non-Write/Edit tool call must never be treated as a write.
            StreamEvent::ToolCall {
                message_id: "m1".to_string(),
                tool_use_id: "t3".to_string(),
                tool_name: "Read".to_string(),
                input: serde_json::json!({"file_path": outside_path.display().to_string()}),
            },
        ];

        let escaped = writes_outside_scope(&events, &feature_dir);
        assert_eq!(escaped.len(), 1);
        assert!(escaped[0].contains("escaped.txt"));
    }

    #[test]
    fn finalize_run_warns_when_write_scoped_run_wrote_outside_feature_dir() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let feature_dir = tmp.path().join("docs/features/f1");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let outside_dir = tmp.path().join("outside");
        std::fs::create_dir_all(&outside_dir).unwrap();
        let outside_path = outside_dir.join("escaped.txt");
        std::fs::write(&outside_path, "x").unwrap();
        let runs_dir = tmp.path().join("runs");

        let result = RunResult {
            events: vec![
                StreamEvent::ToolCall {
                    message_id: "m1".to_string(),
                    tool_use_id: "t1".to_string(),
                    tool_name: "Write".to_string(),
                    input: serde_json::json!({"file_path": outside_path.display().to_string(), "content": "x"}),
                },
                StreamEvent::RunFinished {
                    is_error: false,
                    total_cost_usd: 0.01,
                    session_id: "s1".to_string(),
                    stop_reason: Some("end_turn".to_string()),
                },
            ],
            raw_lines: vec![],
            log_already_on_disk: false,
            timed_out: false,
            exit_code: Some(0),
            stderr: String::new(),
            stdout_drained: true,
        };

        let ctx = RunContext {
            agents_root: &agents_root,
            feature: "f1",
            slot: "ba",
            feature_dir: &feature_dir,
            runs_dir: &runs_dir,
            permission: PermissionProfile::WriteScoped,
        };
        let summary = finalize_run(
            &ctx,
            &result,
            "t0".to_string(),
            "t1".to_string(),
            "prompt",
            None,
        )
        .unwrap();
        assert!(summary
            .last_message
            .as_deref()
            .unwrap()
            .contains("AC-E1-16"));
        assert!(summary
            .last_message
            .as_deref()
            .unwrap()
            .contains("escaped.txt"));
    }

    #[test]
    fn finalize_run_does_not_warn_for_full_profile_writing_outside_feature_dir() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let feature_dir = tmp.path().join("docs/features/f1");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let outside_dir = tmp.path().join("outside");
        std::fs::create_dir_all(&outside_dir).unwrap();
        let outside_path = outside_dir.join("elsewhere.txt");
        std::fs::write(&outside_path, "x").unwrap();
        let runs_dir = tmp.path().join("runs");

        let result = RunResult {
            events: vec![
                StreamEvent::ToolCall {
                    message_id: "m1".to_string(),
                    tool_use_id: "t1".to_string(),
                    tool_name: "Write".to_string(),
                    input: serde_json::json!({"file_path": outside_path.display().to_string(), "content": "x"}),
                },
                StreamEvent::RunFinished {
                    is_error: false,
                    total_cost_usd: 0.01,
                    session_id: "s1".to_string(),
                    stop_reason: Some("end_turn".to_string()),
                },
            ],
            raw_lines: vec![],
            log_already_on_disk: false,
            timed_out: false,
            exit_code: Some(0),
            stderr: String::new(),
            stdout_drained: true,
        };

        let ctx = RunContext {
            agents_root: &agents_root,
            feature: "f1",
            slot: "backend",
            feature_dir: &feature_dir,
            runs_dir: &runs_dir,
            permission: PermissionProfile::Full,
        };
        let summary = finalize_run(
            &ctx,
            &result,
            "t0".to_string(),
            "t1".to_string(),
            "prompt",
            None,
        )
        .unwrap();
        assert!(summary.last_message.is_none());
    }
}
