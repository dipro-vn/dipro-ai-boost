use serde::{Deserialize, Serialize};

/// On-disk marker that a run is (or was) in flight for one `(feature,
/// slot)` — written just before spawn, updated with the child's PID right
/// after, and deleted by `run_log::finalize_run`. A marker that still
/// exists at startup means the app closed while the run was live: the PID
/// is checked, a dead process becomes an `interrupted` summary, a live one
/// is an orphan the user can re-attach to or kill (AC-E6-04/10).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RunningMarker {
    /// `None` between marker creation and a successful spawn — a crash in
    /// that window still marks the slot interrupted, there's just no
    /// process to look for.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pid: Option<u32>,
    pub started_at: String,
    /// Same 1-based attempt the eventual `RunSummary` would have carried —
    /// an interrupted summary reuses it instead of `next_attempt`, since
    /// it describes the same run, not a new one.
    pub attempt: u32,
    /// The exact prompt of the in-flight run, so Re-run after an
    /// interruption can replay it (mirrors `RunSummary.prompt`).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub prompt: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trips_with_and_without_pid() {
        let marker = RunningMarker {
            pid: None,
            started_at: "2026-08-17T00:00:00Z".to_string(),
            attempt: 2,
            prompt: Some("do the thing".to_string()),
        };
        let json = serde_json::to_string(&marker).unwrap();
        assert!(!json.contains("pid"));
        let back: RunningMarker = serde_json::from_str(&json).unwrap();
        assert_eq!(back.attempt, 2);

        let with_pid = RunningMarker {
            pid: Some(4242),
            ..marker
        };
        let json = serde_json::to_string(&with_pid).unwrap();
        let back: RunningMarker = serde_json::from_str(&json).unwrap();
        assert_eq!(back.pid, Some(4242));
    }
}
