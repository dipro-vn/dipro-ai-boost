use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum VersionSource {
    Git,
    Snapshot,
    /// Synthetic entry always present at the top of the list — reads
    /// straight from disk rather than history, so a user can diff
    /// "current" against any past version without an extra step.
    Current,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct VersionRef {
    /// For `Git`: the commit sha. For `Snapshot`: the snapshot's filename.
    /// For `Current`: the literal string `"current"`.
    pub id: String,
    pub label: String,
    pub source: VersionSource,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DiffResult {
    pub from_content: String,
    pub to_content: String,
    /// Which backing history this artifact actually uses — the frontend
    /// shows this so the user knows whether they're comparing real commits
    /// or app-local snapshots (AC-E3-21).
    pub source: VersionSource,
}
