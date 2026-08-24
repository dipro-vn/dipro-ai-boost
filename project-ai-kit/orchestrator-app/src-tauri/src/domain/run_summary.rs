use serde::{Deserialize, Serialize};

/// What one agent run ended up producing — persisted to disk so it can be
/// re-derived on every recompute (`pipeline_state::apply_agent_run_metadata`)
/// the same way pure file-system inference is, rather than living only in
/// memory and silently reverting on the next watcher tick.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum RunOutcome {
    /// The expected artifact now exists — pure inference already reflects
    /// this correctly on its own; this variant exists so `RunSummary` can
    /// still be written (and its cost/session/timing merged in) without
    /// needing a status override.
    Done,
    /// Non-zero exit, or `result.is_error == true`, or process ran but
    /// never emitted a `result` line at all.
    Failed,
    /// Exceeded its configured timeout and was killed (AC-E2-10) —
    /// deliberately distinct from `Failed` so the UI can say "timeout"
    /// specifically, even though both map to `NodeStatus::Failed`.
    Timeout,
    /// Exited cleanly (no error) but the expected artifact never appeared —
    /// inferred as having asked the user a question (AC-E2-15).
    WaitingInput,
    /// AC-E2-11 — never spawned at all: this slot targets an Ecosystem repo
    /// that hasn't been cloned yet. `last_message` names the missing repo.
    Blocked,
    /// AC-E2-12 — never spawned at all: this slot targets a repo role the
    /// project's Ecosystem doesn't have (e.g. `mobile-agent` with no mobile
    /// repo declared).
    Skipped,
    /// AC-E6-04 — the app closed (or crashed) while this run was still in
    /// flight: a `running.json` marker was found at startup with no live
    /// process behind it. Distinct from `Failed` so the UI can offer
    /// Resume/Re-run instead of Retry.
    Interrupted,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RunSummary {
    pub outcome: RunOutcome,
    pub session_id: String,
    pub cost_usd: f64,
    pub started_at: String,
    pub ended_at: String,
    /// The agent's own last message — the question, for `WaitingInput`; the
    /// error text, for `Failed`/`Timeout`. `None` for `Done`.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_message: Option<String>,
    /// 1 for the first run of this `(feature, slot)`, incremented by 1 each
    /// Retry (AC-E2-13). Not reset by a successful run — the Retry button's
    /// max-attempts check only matters while the slot keeps failing, but
    /// nothing about that logic depends on resetting this back to 1.
    #[serde(default = "first_attempt")]
    pub attempt: u32,
    /// AC-E2-13 — the exact prompt handed to `spawn::build_command` for
    /// this run, so a Retry after `Failed` can spawn the same agent again
    /// with the SAME input instead of making the user re-pick a folder.
    /// `None` for a run that was never actually spawned (blocked/skipped —
    /// `commands::agentrun::record_pre_spawn_outcome`) and for any
    /// `RunSummary` persisted before this field existed.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub prompt: Option<String>,
}

fn first_attempt() -> u32 {
    1
}

/// Default per `orchestrator-project-config/SPEC.md`'s Retry AC (AC-E2-13):
/// up to this many retries after the first attempt before the button is
/// disabled.
// Exposed to the frontend's Retry button in T2.4/T2.5 (via a command that
// reads the current `RunSummary.attempt` and calls this).
#[allow(dead_code)]
pub const DEFAULT_MAX_RETRIES: u32 = 2;

/// `attempt` is 1-based (the first run is attempt 1, not a retry) — Retry
/// stays enabled through `attempt <= 1 + max_retries`.
#[allow(dead_code)]
pub fn can_retry(attempt: u32, max_retries: u32) -> bool {
    attempt <= 1 + max_retries
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_max_retries_allows_exactly_2_retries_after_the_first_attempt() {
        assert!(can_retry(1, DEFAULT_MAX_RETRIES)); // first attempt just failed
        assert!(can_retry(2, DEFAULT_MAX_RETRIES)); // 1st retry just failed
        assert!(can_retry(3, DEFAULT_MAX_RETRIES)); // 2nd retry just failed
        assert!(!can_retry(4, DEFAULT_MAX_RETRIES)); // would be a 3rd retry — disabled
    }

    #[test]
    fn old_json_without_attempt_field_defaults_to_1() {
        let json = r#"{"outcome":"failed","sessionId":"s1","costUsd":0.01,"startedAt":"t1","endedAt":"t2"}"#;
        let summary: RunSummary = serde_json::from_str(json).unwrap();
        assert_eq!(summary.attempt, 1);
    }
}
