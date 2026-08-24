//! Crash-recovery for agent runs (AC-E6-04/07/09/10). A `running.json`
//! marker (written pre-spawn, deleted on finalize) that still exists when a
//! project is opened means the previous app instance died mid-run:
//!
//! - marker's PID dead (or never recorded) → the run becomes an
//!   `interrupted` summary — session id recovered from the incrementally
//!   written `log.jsonl`, so Resume can `--resume` it (AC-E6-05);
//! - PID alive and still a claude process → an orphan the user decides
//!   about: re-attach (watch until it exits) or kill (AC-E6-10).
//!
//! No Tauri dependency — the command layer in `commands::agentrun` does the
//! event emission; everything here is plain filesystem + process checks so
//! it's testable with a fake liveness function.

use std::path::Path;

use serde::Serialize;

use crate::agentrun::procutil;
use crate::agentrun::run_log;
use crate::domain::run_summary::{RunOutcome, RunSummary};
use crate::domain::running_marker::RunningMarker;
use crate::store::atomic_write::write_json_atomic;
use crate::store::orchestrator_dir;

/// A still-live agent process left behind by a previous app instance.
#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct OrphanInfo {
    pub feature: String,
    pub slot: String,
    pub pid: u32,
}

/// A slot the scan just marked `interrupted` — returned so the caller can
/// put a line in `open_project`'s warnings.
#[derive(Debug, Clone)]
pub struct InterruptedSlot {
    pub feature: String,
    pub slot: String,
}

/// True when `pid` is alive AND its command name looks like an agent
/// process (`claude` itself, or the `node` runtime it ships as) — the name
/// check guards against PID reuse by an unrelated process, which matters
/// most for `resolve_orphan`'s kill path.
pub fn pid_is_live_agent(pid: u32) -> bool {
    match procutil::pid_command_name(pid) {
        // Windows reports `claude.exe` / `node.exe`; `contains` covers
        // both spellings without a second platform branch here.
        Some(name) => name.contains("claude") || name.contains("node"),
        None => false,
    }
}

fn read_marker(path: &Path) -> Option<RunningMarker> {
    let raw = std::fs::read_to_string(path).ok()?;
    serde_json::from_str(&raw).ok()
}

/// Writes the `interrupted` summary + history row for a marker whose
/// process is gone, then removes the marker. Session id (for Resume) comes
/// from the incrementally written `log.jsonl` — empty when the run died
/// before the CLI ever reported one, which `resume_run` turns into a clear
/// "use Re-run" error instead of silently starting over (AC-E6-06).
pub fn mark_interrupted(
    agents_root: &Path,
    feature: &str,
    slot: &str,
    marker: &RunningMarker,
    message: String,
) {
    let events = run_log::read_run_log(agents_root, feature, slot).unwrap_or_default();
    let session_id = run_log::find_run_finished(&events)
        .map(|(_, _, sid)| sid)
        .or_else(|| run_log::find_session_started(&events))
        .unwrap_or_default();

    let summary = RunSummary {
        outcome: RunOutcome::Interrupted,
        session_id,
        // No `result` line ever arrived — cost genuinely unknown. The
        // summary field is f64 (0.0 shows as such in the panel), but the
        // history row below carries `None` per AC-E6-13.
        cost_usd: 0.0,
        started_at: marker.started_at.clone(),
        ended_at: chrono::Utc::now().to_rfc3339(),
        last_message: Some(message),
        attempt: marker.attempt,
        prompt: marker.prompt.clone(),
    };
    let _ = write_json_atomic(
        &orchestrator_dir::agent_run_summary_path(agents_root, feature, slot),
        &summary,
    );

    let record = crate::domain::run_history::RunHistoryRecord {
        feature: feature.to_string(),
        slot: slot.to_string(),
        model: None,
        outcome: RunOutcome::Interrupted,
        cost_usd: None,
        started_at: summary.started_at.clone(),
        ended_at: summary.ended_at.clone(),
        attempt: summary.attempt,
    };
    let _ = crate::store::run_history::write_record(
        &orchestrator_dir::run_history_dir(agents_root),
        &record,
    );

    let _ = std::fs::remove_file(orchestrator_dir::agent_run_marker_path(
        agents_root,
        feature,
        slot,
    ));
}

/// Scans every `agent-runs/<feature>/<slot>/running.json`. Dead-process
/// markers become `interrupted` summaries on the spot; live ones are
/// returned as orphans, marker untouched, for the user to decide
/// (AC-E6-10). Idempotent — `open_project` may run it repeatedly.
///
/// `is_ours` reports whether THIS app instance is currently running that
/// `(feature, slot)`. Such a run owns its marker legitimately and must be
/// skipped entirely: calling it an orphan would put a Kill button in front
/// of the user that terminates a live run, and would fight with the
/// `running` status the same marker now drives.
pub fn scan_stale_runs(
    agents_root: &Path,
    is_live_agent: impl Fn(u32) -> bool,
    is_ours: impl Fn(&str, &str) -> bool,
) -> (Vec<InterruptedSlot>, Vec<OrphanInfo>) {
    let mut interrupted = Vec::new();
    let mut orphans = Vec::new();

    let agent_runs = orchestrator_dir::agent_runs_dir(agents_root);
    let Ok(features) = std::fs::read_dir(&agent_runs) else {
        return (interrupted, orphans);
    };
    for feature_entry in features.flatten() {
        let Ok(slots) = std::fs::read_dir(feature_entry.path()) else {
            continue;
        };
        let feature = feature_entry.file_name().to_string_lossy().to_string();
        for slot_entry in slots.flatten() {
            let slot = slot_entry.file_name().to_string_lossy().to_string();
            if is_ours(&feature, &slot) {
                continue;
            }
            let marker_path = slot_entry.path().join("running.json");
            let Some(marker) = read_marker(&marker_path) else {
                continue;
            };

            match marker.pid {
                Some(pid) if is_live_agent(pid) => {
                    orphans.push(OrphanInfo {
                        feature: feature.clone(),
                        slot,
                        pid,
                    });
                }
                _ => {
                    mark_interrupted(
                        agents_root,
                        &feature,
                        &slot,
                        &marker,
                        "Bị gián đoạn — app đóng khi agent đang chạy. Chọn Resume (chạy tiếp phiên cũ) hoặc Re-run (chạy lại từ đầu)."
                            .to_string(),
                    );
                    interrupted.push(InterruptedSlot {
                        feature: feature.clone(),
                        slot,
                    });
                }
            }
        }
    }

    (interrupted, orphans)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn marker_at(agents_root: &Path, feature: &str, slot: &str, marker: &RunningMarker) {
        let path = orchestrator_dir::agent_run_marker_path(agents_root, feature, slot);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        write_json_atomic(&path, marker).unwrap();
    }

    fn base_marker(pid: Option<u32>) -> RunningMarker {
        RunningMarker {
            pid,
            started_at: "2026-08-17T00:00:00Z".to_string(),
            attempt: 3,
            prompt: Some("original prompt".to_string()),
        }
    }

    #[test]
    fn dead_pid_marker_becomes_interrupted_summary_and_marker_is_removed() {
        let tmp = tempfile::tempdir().unwrap();
        marker_at(tmp.path(), "feat-a", "backend", &base_marker(Some(999)));

        // Session id recovery from the incrementally written log.
        let log_path = orchestrator_dir::agent_run_log_path(tmp.path(), "feat-a", "backend");
        std::fs::write(
            &log_path,
            r#"{"type":"system","subtype":"init","session_id":"sess-recovered","model":"claude-x","tools":[]}"#,
        )
        .unwrap();

        let (interrupted, orphans) = scan_stale_runs(tmp.path(), |_| false, |_, _| false);

        assert_eq!(interrupted.len(), 1);
        assert!(orphans.is_empty());
        let summary = run_log::read_run_summary(tmp.path(), "feat-a", "backend").unwrap();
        assert_eq!(summary.outcome, RunOutcome::Interrupted);
        assert_eq!(summary.session_id, "sess-recovered");
        assert_eq!(summary.attempt, 3);
        assert_eq!(summary.prompt.as_deref(), Some("original prompt"));
        assert!(!orchestrator_dir::agent_run_marker_path(tmp.path(), "feat-a", "backend").exists());
        // History row written with no cost (AC-E6-13).
        let records =
            crate::store::run_history::list_records(&orchestrator_dir::run_history_dir(tmp.path()));
        assert_eq!(records.len(), 1);
        assert!(records[0].cost_usd.is_none());
    }

    #[test]
    fn live_pid_marker_is_reported_as_orphan_and_left_alone() {
        let tmp = tempfile::tempdir().unwrap();
        marker_at(tmp.path(), "feat-a", "frontend", &base_marker(Some(4242)));

        let (interrupted, orphans) = scan_stale_runs(tmp.path(), |pid| pid == 4242, |_, _| false);

        assert!(interrupted.is_empty());
        assert_eq!(orphans.len(), 1);
        assert_eq!(orphans[0].pid, 4242);
        assert!(orchestrator_dir::agent_run_marker_path(tmp.path(), "feat-a", "frontend").exists());
        assert!(run_log::read_run_summary(tmp.path(), "feat-a", "frontend").is_none());
    }

    #[test]
    fn marker_without_pid_counts_as_interrupted_and_multiple_slots_are_independent() {
        // AC-E6-09 — two interrupted slots each get their own summary.
        let tmp = tempfile::tempdir().unwrap();
        marker_at(tmp.path(), "feat-a", "backend", &base_marker(None));
        marker_at(tmp.path(), "feat-a", "mobile", &base_marker(Some(1)));

        let (interrupted, orphans) = scan_stale_runs(tmp.path(), |_| false, |_, _| false);

        assert_eq!(interrupted.len(), 2);
        assert!(orphans.is_empty());
        for slot in ["backend", "mobile"] {
            let summary = run_log::read_run_summary(tmp.path(), "feat-a", slot).unwrap();
            assert_eq!(summary.outcome, RunOutcome::Interrupted);
        }
    }

    #[test]
    fn scan_is_a_noop_without_markers() {
        let tmp = tempfile::tempdir().unwrap();
        std::fs::create_dir_all(orchestrator_dir::agent_runs_dir(tmp.path())).unwrap();
        let (interrupted, orphans) = scan_stale_runs(tmp.path(), |_| true, |_, _| false);
        assert!(interrupted.is_empty());
        assert!(orphans.is_empty());
    }

    /// The Board re-scans on every mount, including while our own agent is
    /// mid-run. Reporting that as an orphan would offer a Kill button that
    /// terminates a live run — and would contradict the `running` status the
    /// very same marker drives.
    #[test]
    fn a_run_this_instance_owns_is_never_reported_as_an_orphan() {
        let tmp = tempfile::tempdir().unwrap();
        marker_at(tmp.path(), "feat-a", "ba", &base_marker(Some(4242)));

        let (interrupted, orphans) = scan_stale_runs(
            tmp.path(),
            |_| true,
            |feature, slot| feature == "feat-a" && slot == "ba",
        );

        assert!(orphans.is_empty(), "live run of ours must not be an orphan");
        assert!(interrupted.is_empty(), "and must not be marked interrupted");
        // Its marker is left exactly where the running run expects it.
        assert!(orchestrator_dir::agent_run_marker_path(tmp.path(), "feat-a", "ba").exists());
        assert!(run_log::read_run_summary(tmp.path(), "feat-a", "ba").is_none());
    }
}
