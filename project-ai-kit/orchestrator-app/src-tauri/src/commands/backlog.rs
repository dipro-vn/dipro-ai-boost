//! Push task files to Backlog by running the kit's own `pm-agent`
//! (AC-E5-01..13).
//!
//! The app deliberately does NOT call the Backlog write API itself. Issue
//! Subject/Description/Type conventions live in
//! `.claude/context/backlog-workflow.md` and are already implemented by
//! `pm-agent` Bước 4 through the project's `backlog` MCP server — going
//! through the agent is what makes AC-E5-06 ("app không dùng convention
//! riêng") true by construction instead of by copy-paste. It also means no
//! Backlog credential is needed here: the MCP server owns that.
//!
//! This runs on a pseudo-slot (`backlog-push`) rather than a pipeline slot:
//! logs and summaries land under `.orchestrator/agent-runs/<feature>/
//! backlog-push/` and reuse the whole live-log/answer/kill machinery, while
//! staying out of `state.json` (which only ever holds pipeline slots).

use std::path::{Path, PathBuf};

use tauri::{AppHandle, Emitter, Manager, State};

use crate::agentrun::process_registry::RunKey;
use crate::agentrun::run_log;
use crate::agentrun::runner;
use crate::agentrun::spawn::{self, SpawnParams};
use crate::app_state::AppState;
use crate::auth;
use crate::domain::config_file::{self, AgentConfig, PermissionProfile, ProjectConfig};
use crate::domain::project::ProjectPaths;
use crate::domain::run_summary::{RunOutcome, RunSummary};
use crate::domain::running_marker::RunningMarker;
use crate::error::{AppError, AppResult};
use crate::inference::task_meta::{self, TaskMeta};
use crate::store::backlog_map::{self, BacklogMapping};
use crate::store::orchestrator_dir;

/// Pseudo-slot id. Not present in `pipeline.json` on purpose — see the
/// module docs.
pub const BACKLOG_PUSH_SLOT: &str = "backlog-push";

const AGENT_NAME: &str = "pm-agent";

#[derive(Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
struct RunFinishedPayload {
    feature: String,
    slot: String,
    summary: RunSummary,
}

/// Everything the Backlog screen renders before/after a push.
#[derive(Debug, Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BacklogPushView {
    pub tasks: Vec<TaskMeta>,
    pub mapping: BacklogMapping,
    /// Task files that have no issue yet — AC-E5-11's "chỉ hiện task chưa
    /// có issue" on a second push.
    pub pending: Vec<String>,
    /// AC-E5-12 — task files missing the required Estimated Hours.
    pub missing_estimate: Vec<String>,
    /// Corrupt-mapping notice from `store::backlog_map`, if any.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub warning: Option<String>,
    pub running: bool,
}

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

fn feature_dir(docs_root: &Path, feature: &str) -> PathBuf {
    docs_root.join("features").join(feature)
}

/// `pm-agent`'s config from Settings, but always with `Full` permission:
/// the push needs the `mcp__backlog__*` tools and a `Write` for the mapping
/// file, and `--tools` would otherwise filter both out.
fn push_agent_config(agents_root: &Path) -> AgentConfig {
    let from_disk = std::fs::read_to_string(orchestrator_dir::config_json_path(agents_root))
        .ok()
        .and_then(|raw| serde_json::from_str::<ProjectConfig>(&raw).ok())
        .and_then(|cfg| cfg.agents.get(AGENT_NAME).cloned());

    AgentConfig {
        permission: PermissionProfile::Full,
        ..from_disk.unwrap_or_else(|| AgentConfig {
            model: config_file::default_model_for(AGENT_NAME),
            max_turns: config_file::DEFAULT_MAX_TURNS,
            permission: PermissionProfile::Full,
            stale: false,
            newly_discovered: false,
            timeout_minutes: config_file::DEFAULT_TIMEOUT_MINUTES,
        })
    }
}

/// The instruction handed to `pm-agent`. Pure so the important bits (the
/// absolute paths, the already-pushed list, the incremental-write rule) are
/// unit-testable without spawning anything.
pub fn build_backlog_push_prompt(
    feature: &str,
    feature_dir: &Path,
    mapping_path: &Path,
    tasks: &[TaskMeta],
    already_pushed: &[String],
) -> String {
    let mut prompt = String::new();
    prompt.push_str(&format!(
        "Thực hiện Bước 4 (`/create-backlog`) của bạn cho feature `{feature}`.\n\n\
         Thư mục feature (đường dẫn tuyệt đối): {}\n\n",
        feature_dir.display()
    ));

    prompt.push_str("Các task file cần tạo issue (đường dẫn tương đối so với thư mục feature):\n");
    for task in tasks {
        let estimate = task
            .estimate
            .as_deref()
            .unwrap_or("THIẾU — hỏi user trước khi tạo");
        let phase = task
            .phase
            .map(|p| p.to_string())
            .unwrap_or_else(|| "?".to_string());
        prompt.push_str(&format!(
            "- {} (phase {phase}, estimate: {estimate})\n",
            task.relative_path
        ));
    }

    if already_pushed.is_empty() {
        prompt.push_str("\nChưa có task nào được đẩy lên Backlog trước đó.\n");
    } else {
        // AC-E5-11 — the agent must not create a second issue for these.
        prompt.push_str(
            "\nCÁC TASK SAU ĐÃ CÓ ISSUE RỒI — TUYỆT ĐỐI KHÔNG tạo issue mới cho chúng:\n",
        );
        for line in already_pushed {
            prompt.push_str(&format!("- {line}\n"));
        }
    }

    prompt.push_str(&format!(
        "\nQuy tắc bắt buộc:\n\
         1. Tuân thủ đúng `.claude/context/backlog-workflow.md` (Subject, Issue Type, \
         description template) — không tự đặt convention riêng.\n\
         2. Hỏi user đủ 5 thông tin bắt buộc (Parent Issue, Category, Milestone, Assignee, \
         URL THAM KHẢO base) TRƯỚC khi tạo bất kỳ issue nào. Chỉ chọn giá trị có thật lấy \
         từ `mcp__backlog__get_categories` / `get_version_milestone_list` / `get_users` / \
         `get_issue_types` / `get_priorities` — không đoán, không tự tạo mới.\n\
         3. Tạo ĐÚNG MỘT issue mẫu trước, đưa issue key + link cho user xem, rồi DỪNG LẠI \
         chờ user xác nhận. Chỉ tạo phần còn lại sau khi user đồng ý.\n\
         4. KHÔNG sửa nội dung bất kỳ file task-*.md nào — chỉ đọc.\n\
         5. Sau MỖI issue được tạo thành công, cập nhật ngay file mapping tại:\n   {}\n   \
         Định dạng JSON (ghi đè toàn bộ file bằng danh sách đầy đủ tính tới thời điểm đó, \
         giữ nguyên các entry đã có):\n   \
         {{\"issues\":[{{\"taskFile\":\"<đường dẫn tương đối>\",\"issueKey\":\"PROJ-123\",\
         \"phase\":1}}],\"pushedAt\":\"<ISO8601>\",\"parentIssue\":\"<parent issue key>\"}}\n   \
         Ghi sau từng issue (không đợi tới cuối) để nếu bị gián đoạn thì lần chạy sau biết \
         cái nào đã tạo.\n\
         6. Cuối cùng báo cáo danh sách issue key nhóm theo phase.\n",
        mapping_path.display()
    ));

    prompt
}

fn build_view(
    agents_root: &Path,
    docs_root: &Path,
    feature: &str,
    running: bool,
) -> BacklogPushView {
    let tasks = task_meta::collect_task_meta(&feature_dir(docs_root, feature));
    let (mapping, warning) = backlog_map::read_mapping(agents_root, feature);

    let pending: Vec<String> = tasks
        .iter()
        .filter(|task| {
            !mapping
                .issues
                .iter()
                .any(|link| link.task_file == task.relative_path)
        })
        .map(|task| task.relative_path.clone())
        .collect();

    let missing_estimate: Vec<String> = tasks
        .iter()
        .filter(|task| task.estimate.is_none())
        .map(|task| task.relative_path.clone())
        .collect();

    BacklogPushView {
        tasks,
        mapping,
        pending,
        missing_estimate,
        warning,
        running,
    }
}

/// What the Backlog screen shows before pushing (and refreshes after).
#[tauri::command]
pub fn get_backlog_push_view(
    state: State<AppState>,
    feature: String,
) -> AppResult<BacklogPushView> {
    let project = current_project(&state)?;
    Ok(build_view(
        Path::new(&project.agents_root),
        Path::new(&project.docs_root),
        &feature,
        state.is_running(&feature, BACKLOG_PUSH_SLOT),
    ))
}

/// AC-E5-18 — current sha256 of one task file, compared client-side
/// against the hash captured at the last status refresh to show a "lệch"
/// marker. `None` when the file is unreadable/gone: the UI then says
/// nothing rather than claiming drift. Read-only, like everything else this
/// module does to task files.
#[tauri::command]
pub fn hash_task_file(
    state: State<AppState>,
    feature: String,
    task_file: String,
) -> AppResult<Option<String>> {
    let project = current_project(&state)?;
    let feature_dir = feature_dir(Path::new(&project.docs_root), &feature);
    let path = feature_dir.join(&task_file);
    // Path comes from a mapping file the agent wrote — re-assert it stays
    // inside the feature directory before reading it.
    let Ok(path) = orchestrator_dir::assert_within(&path, &feature_dir) else {
        return Ok(None);
    };
    Ok(std::fs::read_to_string(path)
        .ok()
        .map(|content| crate::inference::contract_lock_rules::sha256_hex(&content)))
}

/// Starts a push (`answer: None`) or delivers the user's reply into the
/// running agent's session (`answer: Some`) — same `--resume` mechanism as
/// `send_clarification_answer`, since each `claude -p` call exits when it
/// asks a question (A5).
#[tauri::command]
pub fn push_to_backlog(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
    answer: Option<String>,
) -> AppResult<()> {
    if !spawn::is_claude_cli_available() {
        return Err(AppError::Invalid {
            message: crate::agentrun::cli_path::not_found_message(),
        });
    }
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let docs_root = PathBuf::from(&project.docs_root);
    // Fail before starting the background push when API-key mode has no
    // keychain credential. The resolver is used again immediately before
    // the child process is built.
    auth::resolve_for_spawn(&agents_root)?;

    if state.is_running(&feature, BACKLOG_PUSH_SLOT) {
        return Err(AppError::Invalid {
            message: "Đang có lượt đẩy Backlog chạy cho feature này".to_string(),
        });
    }

    let feature_dir = feature_dir(&docs_root, &feature);
    if !feature_dir.is_dir() {
        return Err(AppError::Invalid {
            message: format!("Không tìm thấy thư mục feature: {}", feature_dir.display()),
        });
    }

    let view = build_view(&agents_root, &docs_root, &feature, false);
    if view.tasks.is_empty() {
        return Err(AppError::Invalid {
            message: "Feature này chưa có file tasks/task-*.md nào để đẩy".to_string(),
        });
    }

    // A reply continues the session that asked; a fresh push starts one.
    let (prompt, resume_session_id) = match answer {
        Some(answer) => {
            let session_id = run_log::read_run_summary(&agents_root, &feature, BACKLOG_PUSH_SLOT)
                .map(|summary| summary.session_id)
                .filter(|id| !id.is_empty())
                .ok_or_else(|| AppError::Invalid {
                    message: "Không tìm thấy phiên đẩy Backlog trước đó để trả lời tiếp"
                        .to_string(),
                })?;
            (answer, Some(session_id))
        }
        None => {
            if view.pending.is_empty() {
                return Err(AppError::Invalid {
                    message: "Mọi task của feature này đã có issue trên Backlog".to_string(),
                });
            }
            backlog_map::ensure_mapping_dir(&agents_root, &feature).map_err(|err| {
                AppError::Invalid {
                    message: format!("Không tạo được thư mục mapping: {err}"),
                }
            })?;
            let already_pushed: Vec<String> = view
                .mapping
                .issues
                .iter()
                .map(|link| format!("{} → {}", link.task_file, link.issue_key))
                .collect();
            let pending_tasks: Vec<TaskMeta> = view
                .tasks
                .iter()
                .filter(|task| view.pending.contains(&task.relative_path))
                .cloned()
                .collect();
            (
                build_backlog_push_prompt(
                    &feature,
                    &feature_dir,
                    &orchestrator_dir::backlog_mapping_path(&agents_root, &feature),
                    &pending_tasks,
                    &already_pushed,
                ),
                None,
            )
        }
    };

    std::thread::spawn(move || {
        run_push(
            app,
            agents_root,
            docs_root,
            feature,
            prompt,
            resume_session_id,
        );
    });
    Ok(())
}

/// Blocking — runs on its own thread. Mirrors `run_to_completion`'s
/// spawn/stream/persist shape minus everything pipeline-specific (gates,
/// artifact inference, `advance_pipeline`).
fn run_push(
    app: AppHandle,
    agents_root: PathBuf,
    docs_root: PathBuf,
    feature: String,
    prompt: String,
    resume_session_id: Option<String>,
) {
    let issues_before = backlog_map::read_mapping(&agents_root, &feature)
        .0
        .issues
        .len();
    let started_at = chrono::Utc::now().to_rfc3339();
    let config = push_agent_config(&agents_root);
    let resolved_auth = match auth::resolve_for_spawn(&agents_root) {
        Ok(auth) => auth,
        Err(_) => return,
    };
    let key = RunKey {
        feature: feature.clone(),
        slot: BACKLOG_PUSH_SLOT.to_string(),
    };

    let (tx, rx) = std::sync::mpsc::channel();
    let forwarder = runner::spawn_event_forwarder(
        app.clone(),
        feature.clone(),
        BACKLOG_PUSH_SLOT.to_string(),
        rx,
    );

    // cwd is agentsRoot, NOT the feature dir: that is where the project's
    // `.claude/settings.json` (and therefore the `backlog` MCP server)
    // lives, and the CLI resolves MCP config from its working directory.
    // Task files live under docsRoot, hence the `--add-dir`.
    let add_dirs = vec![docs_root.clone()];
    let params = SpawnParams {
        agent_name: AGENT_NAME,
        prompt: &prompt,
        cwd: &agents_root,
        config: &config,
        resume_session_id: resume_session_id.as_deref(),
        add_dirs: &add_dirs,
        auth: match (resolved_auth.mode, resolved_auth.api_key.as_deref()) {
            (crate::domain::config_file::ClaudeAuthMode::CliDefault, _) => {
                spawn::SpawnAuth::CliDefault
            }
            (crate::domain::config_file::ClaudeAuthMode::Subscription, _) => {
                spawn::SpawnAuth::Subscription
            }
            (crate::domain::config_file::ClaudeAuthMode::Console, _) => spawn::SpawnAuth::Console,
            (crate::domain::config_file::ClaudeAuthMode::ApiKey, Some(key)) => {
                spawn::SpawnAuth::ApiKey(key)
            }
            (crate::domain::config_file::ClaudeAuthMode::ApiKey, None) => {
                spawn::SpawnAuth::CliDefault
            }
        },
    };

    let attempt = run_log::next_attempt(&agents_root, &feature, BACKLOG_PUSH_SLOT);
    let marker_path =
        orchestrator_dir::agent_run_marker_path(&agents_root, &feature, BACKLOG_PUSH_SLOT);
    if let Some(parent) = marker_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let marker = RunningMarker {
        pid: None,
        started_at: started_at.clone(),
        attempt,
        prompt: Some(prompt.clone()),
    };
    let _ = crate::store::atomic_write::write_json_atomic(&marker_path, &marker);
    let durability = runner::RunDurability {
        marker_path: marker_path.clone(),
        marker,
        log_path: orchestrator_dir::agent_run_log_path(&agents_root, &feature, BACKLOG_PUSH_SLOT),
    };

    let registry = &app.state::<AppState>().agent_runs;
    let timeout = std::time::Duration::from_secs(u64::from(config.timeout_minutes) * 60);
    let result = runner::run_and_stream(registry, key, &params, tx, timeout, Some(durability));
    let _ = forwarder.join();
    let ended_at = chrono::Utc::now().to_rfc3339();

    let Ok(result) = result else {
        let _ = std::fs::remove_file(&marker_path);
        return;
    };
    let _ = std::fs::remove_file(&marker_path);

    let issues_after = backlog_map::read_mapping(&agents_root, &feature)
        .0
        .issues
        .len();
    let (outcome, message) = classify_push(&result, issues_before, issues_after);

    let summary = RunSummary {
        outcome,
        session_id: run_log::find_run_finished(&result.events)
            .map(|(_, _, session_id)| session_id)
            .or_else(|| run_log::find_session_started(&result.events))
            .unwrap_or_default(),
        cost_usd: run_log::find_run_finished(&result.events)
            .map(|(_, cost, _)| cost)
            .unwrap_or(0.0),
        started_at: started_at.clone(),
        ended_at: ended_at.clone(),
        last_message: message.or_else(|| run_log::last_assistant_text(&result.events)),
        attempt,
        prompt: Some(prompt),
    };

    let _ = run_log::write_run_summary(&agents_root, &feature, BACKLOG_PUSH_SLOT, &summary);
    if !result.log_already_on_disk {
        let _ = run_log::write_run_log(&agents_root, &feature, BACKLOG_PUSH_SLOT, &result.raw_lines);
    }

    // Cost of a push shows up in Reports like any other run (AC-E6-12).
    let _ = crate::store::run_history::write_record(
        &orchestrator_dir::run_history_dir(&agents_root),
        &crate::domain::run_history::RunHistoryRecord {
            feature: feature.clone(),
            slot: BACKLOG_PUSH_SLOT.to_string(),
            model: None,
            outcome,
            cost_usd: run_log::find_run_finished(&result.events).map(|(_, cost, _)| cost),
            started_at,
            ended_at,
            attempt,
        },
    );

    let _ = app.emit(
        crate::commands::agentrun::EVENT_RUN_FINISHED,
        RunFinishedPayload {
            feature,
            slot: BACKLOG_PUSH_SLOT.to_string(),
            summary,
        },
    );
}

/// Pure classification: the mapping file is the artifact this run is judged
/// by, exactly like a pipeline slot is judged by its `.md` output.
fn classify_push(
    result: &runner::RunResult,
    issues_before: usize,
    issues_after: usize,
) -> (RunOutcome, Option<String>) {
    if result.timed_out {
        return (
            RunOutcome::Timeout,
            Some("Quá thời gian chờ — agent bị dừng giữa chừng.".to_string()),
        );
    }
    if result.exit_code != Some(0) {
        let detail = if result.stderr.trim().is_empty() {
            "Agent kết thúc với lỗi.".to_string()
        } else {
            format!("Agent kết thúc với lỗi: {}", result.stderr.trim())
        };
        return (RunOutcome::Failed, Some(detail));
    }
    if issues_after > issues_before {
        return (
            RunOutcome::Done,
            Some(format!(
                "Đã tạo {} issue mới (tổng {issues_after}).",
                issues_after - issues_before
            )),
        );
    }
    // Clean exit with no new issue = the agent stopped to ask something
    // (the 5 metadata questions, or the sample-issue confirmation) — same
    // heuristic as pipeline slots (A4).
    (RunOutcome::WaitingInput, None)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn task(path: &str, phase: Option<u32>, estimate: Option<&str>) -> TaskMeta {
        TaskMeta {
            relative_path: path.to_string(),
            title: "T".to_string(),
            phase,
            estimate: estimate.map(str::to_string),
        }
    }

    fn result(exit_code: Option<i32>, timed_out: bool) -> runner::RunResult {
        runner::RunResult {
            events: vec![],
            raw_lines: vec![],
            log_already_on_disk: false,
            timed_out,
            exit_code,
            stderr: String::new(),
            stdout_drained: true,
        }
    }

    #[test]
    fn prompt_carries_absolute_paths_and_the_sample_first_rule() {
        let prompt = build_backlog_push_prompt(
            "user-login",
            Path::new("/docs/features/user-login"),
            Path::new("/agents/.orchestrator/backlog/user-login/mapping.json"),
            &[task("api/tasks/task-1-1.md", Some(1), Some("4h"))],
            &[],
        );
        assert!(prompt.contains("/docs/features/user-login"));
        assert!(prompt.contains("/agents/.orchestrator/backlog/user-login/mapping.json"));
        assert!(prompt.contains("api/tasks/task-1-1.md"));
        assert!(prompt.contains("ĐÚNG MỘT issue mẫu"));
        assert!(prompt.contains("backlog-workflow.md"));
        // AC-E5-13 — the instruction never to edit task files.
        assert!(prompt.contains("KHÔNG sửa nội dung bất kỳ file task-*.md"));
        assert!(prompt.contains("Chưa có task nào được đẩy"));
    }

    /// AC-E5-11 — a second push must tell the agent what already exists.
    #[test]
    fn prompt_lists_already_pushed_tasks_as_do_not_recreate() {
        let prompt = build_backlog_push_prompt(
            "f",
            Path::new("/d/f"),
            Path::new("/m.json"),
            &[task("api/tasks/task-2-1.md", Some(2), Some("2h"))],
            &["api/tasks/task-1-1.md → PROJ-11".to_string()],
        );
        assert!(prompt.contains("TUYỆT ĐỐI KHÔNG tạo issue mới"));
        assert!(prompt.contains("api/tasks/task-1-1.md → PROJ-11"));
    }

    /// AC-E5-12 — a task without Estimated Hours is flagged to the agent
    /// too, not just in the UI.
    #[test]
    fn prompt_marks_a_missing_estimate() {
        let prompt = build_backlog_push_prompt(
            "f",
            Path::new("/d/f"),
            Path::new("/m.json"),
            &[task("api/tasks/task-1-1.md", Some(1), None)],
            &[],
        );
        assert!(prompt.contains("THIẾU — hỏi user trước khi tạo"));
    }

    #[test]
    fn new_issues_in_the_mapping_mean_done() {
        let (outcome, message) = classify_push(&result(Some(0), false), 0, 3);
        assert_eq!(outcome, RunOutcome::Done);
        assert!(message.unwrap().contains("3 issue mới"));
    }

    #[test]
    fn clean_exit_without_new_issues_means_the_agent_asked_something() {
        let (outcome, _) = classify_push(&result(Some(0), false), 2, 2);
        assert_eq!(outcome, RunOutcome::WaitingInput);
    }

    #[test]
    fn non_zero_exit_is_failed_and_timeout_is_timeout() {
        assert_eq!(
            classify_push(&result(Some(1), false), 0, 0).0,
            RunOutcome::Failed
        );
        assert_eq!(
            classify_push(&result(None, true), 0, 0).0,
            RunOutcome::Timeout
        );
    }

    /// The push must be judged by the mapping file, never by "the agent
    /// exited 0" alone — otherwise a run that asked a question would look
    /// like a completed push.
    #[test]
    fn partial_progress_still_counts_as_done() {
        let (outcome, message) = classify_push(&result(Some(0), false), 1, 2);
        assert_eq!(outcome, RunOutcome::Done);
        assert!(message.unwrap().contains("1 issue mới"));
    }
}
