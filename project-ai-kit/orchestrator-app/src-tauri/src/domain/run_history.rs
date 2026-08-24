use serde::{Deserialize, Serialize};

use crate::domain::run_summary::RunOutcome;

/// One immutable row of run history (AC-E6-12..18) — unlike
/// `RunSummary`/`last-run.json` (latest-run-only, overwritten per run),
/// these accumulate forever, one file per run (`store::run_history`), and
/// are what Cost & Reports aggregates.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RunHistoryRecord {
    pub feature: String,
    pub slot: String,
    /// AC-E6-18 — the model ACTUALLY used, taken from the run's own
    /// `SessionStarted` event (the CLI's resolved model id), not from
    /// config. `None` for runs that never started a session
    /// (blocked/skipped/startup failure). Being stored per-record in an
    /// immutable file is what guarantees a later Settings model change
    /// can't rewrite history.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,
    pub outcome: RunOutcome,
    /// AC-E6-13 — `None` means "không có số liệu" (no terminal `result`
    /// line carried a cost). Deliberately NOT 0.0: reports must show the
    /// row as missing and exclude it from totals with a note, never
    /// silently count it as free.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub cost_usd: Option<f64>,
    pub started_at: String,
    pub ended_at: String,
    pub attempt: u32,
}
