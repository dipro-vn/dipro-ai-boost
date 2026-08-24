//! Persists `ContractLockRecord`s and `ViolationEvent`s — one immutable
//! timestamped JSON file per Lock/Re-lock (under
//! `orchestrator_dir::contract_lock_dir`) or per detected violation (under
//! `orchestrator_dir::contract_lock_violations_dir`), mirroring
//! `store::snapshot`'s timestamped-immutable-file convention exactly
//! (never overwritten, sorted by filename — AC-E4-19/26: history retained
//! for both).

use std::path::Path;

use chrono::Utc;
use serde::de::DeserializeOwned;
use serde::Serialize;

use crate::domain::contract_lock::{ContractLockRecord, ViolationEvent};
use crate::error::AppResult;
use crate::store::atomic_write::write_json_atomic;

const TIMESTAMP_FORMAT: &str = "%Y%m%dT%H%M%S%3fZ";

fn write_record<T: Serialize>(dir: &Path, record: &T) -> AppResult<()> {
    let filename = format!("{}.json", Utc::now().format(TIMESTAMP_FORMAT));
    write_json_atomic(&dir.join(filename), record)
}

/// Best-effort — an individual corrupt record is skipped rather than
/// failing the whole list (same philosophy as `run_log::read_run_summary`).
/// See `read_latest_lock`'s doc comment for how this interacts with
/// AC-E4-29.
fn list_records<T: DeserializeOwned>(dir: &Path) -> Vec<T> {
    let mut entries: Vec<(String, T)> = std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .filter_map(|entry| {
            let filename = entry.file_name().to_string_lossy().into_owned();
            let raw = std::fs::read_to_string(entry.path()).ok()?;
            let record: T = serde_json::from_str(&raw).ok()?;
            Some((filename, record))
        })
        .collect();
    // Filenames are timestamps in a sortable format (mirrors
    // `store::snapshot`) — plain string sort is chronological.
    entries.sort_by(|(a, _), (b, _)| b.cmp(a));
    entries.into_iter().map(|(_, record)| record).collect()
}

/// Writes a new lock record — always a new file, never overwrites a prior
/// one (AC-E4-19).
pub fn write_lock_record(dir: &Path, record: &ContractLockRecord) -> AppResult<()> {
    write_record(dir, record)
}

/// Every persisted lock record, newest first.
pub fn list_locks(dir: &Path) -> Vec<ContractLockRecord> {
    list_records(dir)
}

/// The most recently written valid lock record, if any. Note: this is a
/// simpler recovery than AC-E4-29's exact "corrupt lock -> treat as no
/// valid lock at all" flow, which assumes a single mutable `contract.lock`
/// file — this app's history-of-immutable-files design means a corrupt
/// *newest* file falls through to the next most recent valid one instead
/// of unlocking entirely (see this phase's plan doc for the reasoning).
/// `pipeline_state::compute_and_persist` surfaces a warning when this
/// fallback actually happens, so it's never silent.
pub fn read_latest_lock(dir: &Path) -> Option<ContractLockRecord> {
    list_locks(dir).into_iter().next()
}

/// `true` if `dir` contains at least one file that couldn't be parsed as a
/// `ContractLockRecord` — used only to decide whether to surface AC-E4-29's
/// "state.json bị hỏng"-style warning, never to change the log's behavior
/// (that's driven entirely by `read_latest_lock`).
pub fn has_unreadable_lock_file(dir: &Path) -> bool {
    std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .any(|entry| {
            let Ok(raw) = std::fs::read_to_string(entry.path()) else {
                return true;
            };
            serde_json::from_str::<ContractLockRecord>(&raw).is_err()
        })
}

/// AC-E4-26 — writes a new violation event, always a new file, never
/// overwrites a prior one (same "history retained" guarantee as lock
/// records).
pub fn write_violation_event(dir: &Path, event: &ViolationEvent) -> AppResult<()> {
    write_record(dir, event)
}

/// Every persisted violation event, newest first.
pub fn list_violation_events(dir: &Path) -> Vec<ViolationEvent> {
    list_records(dir)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::contract_lock::{FileViolation, ViolationKind};

    fn record(approved_by: &str) -> ContractLockRecord {
        ContractLockRecord {
            locked_at: "2026-08-17T00:00:00Z".to_string(),
            approved_by: approved_by.to_string(),
            confirmed_roles: vec!["PM".to_string(), "QC".to_string()],
            files: vec![],
        }
    }

    fn violation_event(detected_at: &str) -> ViolationEvent {
        ViolationEvent {
            detected_at: detected_at.to_string(),
            files: vec![FileViolation {
                path: "/x/DESIGN.md".to_string(),
                kind: ViolationKind::Modified,
                locked_content: "original".to_string(),
            }],
        }
    }

    #[test]
    fn no_prior_lock_is_none() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("locks");
        assert!(read_latest_lock(&dir).is_none());
        assert!(list_locks(&dir).is_empty());
    }

    #[test]
    fn write_then_read_round_trips() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("locks");
        write_lock_record(&dir, &record("PM A")).unwrap();

        let latest = read_latest_lock(&dir).unwrap();
        assert_eq!(latest.approved_by, "PM A");
    }

    #[test]
    fn never_overwrites_and_lists_newest_first() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("locks");
        write_lock_record(&dir, &record("first")).unwrap();
        std::thread::sleep(std::time::Duration::from_millis(2));
        write_lock_record(&dir, &record("second")).unwrap();

        let all = list_locks(&dir);
        assert_eq!(all.len(), 2);
        assert_eq!(all[0].approved_by, "second");
        assert_eq!(all[1].approved_by, "first");
        assert_eq!(read_latest_lock(&dir).unwrap().approved_by, "second");
    }

    #[test]
    fn a_corrupt_record_file_is_skipped_not_fatal() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("locks");
        std::fs::create_dir_all(&dir).unwrap();
        std::fs::write(dir.join("20260101T000000000Z.json"), "not json").unwrap();
        write_lock_record(&dir, &record("valid")).unwrap();

        let all = list_locks(&dir);
        assert_eq!(all.len(), 1);
        assert_eq!(all[0].approved_by, "valid");
    }

    #[test]
    fn has_unreadable_lock_file_detects_a_corrupt_file() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("locks");
        std::fs::create_dir_all(&dir).unwrap();
        assert!(!has_unreadable_lock_file(&dir));

        std::fs::write(dir.join("20260101T000000000Z.json"), "not json").unwrap();
        assert!(has_unreadable_lock_file(&dir));
    }

    #[test]
    fn violation_events_round_trip_and_never_overwrite() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("violations");
        write_violation_event(&dir, &violation_event("2026-08-17T00:00:00Z")).unwrap();
        std::thread::sleep(std::time::Duration::from_millis(2));
        write_violation_event(&dir, &violation_event("2026-08-17T00:01:00Z")).unwrap();

        let all = list_violation_events(&dir);
        assert_eq!(all.len(), 2);
        assert_eq!(all[0].detected_at, "2026-08-17T00:01:00Z");
        assert_eq!(all[1].detected_at, "2026-08-17T00:00:00Z");
    }
}
