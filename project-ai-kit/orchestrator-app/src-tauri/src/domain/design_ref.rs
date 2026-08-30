use serde::{Deserialize, Serialize};

/// The Figma selection URL the user gave `design-analyst` for one feature.
///
/// Deliberately a single *mutable* record, not a timestamped history like
/// `store::contract_lock`'s lock files: a newer URL simply replaces the old
/// one, exactly as `ContractLockSkip` replaces itself. Nothing downstream
/// has a use for "which URL did we analyse three runs ago".
///
/// It exists because the URL used to live only in the frontend's zustand
/// draft — cleared the moment the run started — so `frontend-agent` and
/// `mobile-agent` had no way to reach the design their task was about.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DesignRef {
    pub url: String,
    /// RFC3339, so the UI can say how stale the stored URL is if it ever
    /// needs to.
    pub updated_at: String,
    /// Which slot's input produced it — `design-analyst` today, kept as a
    /// field so a second source (a future per-repo design node) is not a
    /// schema change.
    pub source_slot: String,
}
