//! Persists `RunHistoryRecord`s — one immutable timestamped JSON file per
//! run under `.ai-boost/run-history/` (flat, cross-feature — the
//! Reports History tab lists every feature's runs from one directory),
//! mirroring `store::contract_lock`'s convention. Never overwritten; this
//! is why deleting run LOGS (AC-E6-28) can never lose cost data.

use std::path::Path;

use chrono::Utc;

use crate::domain::run_history::RunHistoryRecord;
use crate::error::AppResult;
use crate::store::atomic_write::write_json_atomic;

const TIMESTAMP_FORMAT: &str = "%Y%m%dT%H%M%S%3fZ";

pub fn write_record(dir: &Path, record: &RunHistoryRecord) -> AppResult<()> {
    let filename = format!("{}.json", Utc::now().format(TIMESTAMP_FORMAT));
    write_json_atomic(&dir.join(filename), record)
}

/// Every record, newest first. Best-effort — a corrupt file is skipped
/// rather than failing the whole list.
pub fn list_records(dir: &Path) -> Vec<RunHistoryRecord> {
    let mut entries: Vec<(String, RunHistoryRecord)> = std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .filter_map(|entry| {
            let filename = entry.file_name().to_string_lossy().into_owned();
            let raw = std::fs::read_to_string(entry.path()).ok()?;
            let record: RunHistoryRecord = serde_json::from_str(&raw).ok()?;
            Some((filename, record))
        })
        .collect();
    entries.sort_by(|(a, _), (b, _)| b.cmp(a));
    entries.into_iter().map(|(_, record)| record).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::run_summary::RunOutcome;

    fn record(feature: &str, cost: Option<f64>) -> RunHistoryRecord {
        RunHistoryRecord {
            feature: feature.to_string(),
            slot: "ba".to_string(),
            model: Some("claude-haiku-4-5".to_string()),
            outcome: RunOutcome::Done,
            cost_usd: cost,
            started_at: "t0".to_string(),
            ended_at: "t1".to_string(),
            attempt: 1,
        }
    }

    #[test]
    fn round_trips_and_lists_newest_first() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("history");
        write_record(&dir, &record("first", Some(0.01))).unwrap();
        std::thread::sleep(std::time::Duration::from_millis(2));
        write_record(&dir, &record("second", None)).unwrap();

        let all = list_records(&dir);
        assert_eq!(all.len(), 2);
        assert_eq!(all[0].feature, "second");
        assert_eq!(all[0].cost_usd, None); // AC-E6-13: missing stays missing
        assert_eq!(all[1].cost_usd, Some(0.01));
    }

    #[test]
    fn corrupt_record_is_skipped_and_missing_dir_is_empty() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("history");
        assert!(list_records(&dir).is_empty());
        std::fs::create_dir_all(&dir).unwrap();
        std::fs::write(dir.join("20260101T000000000Z.json"), "not json").unwrap();
        write_record(&dir, &record("ok", Some(0.02))).unwrap();
        assert_eq!(list_records(&dir).len(), 1);
    }
}
