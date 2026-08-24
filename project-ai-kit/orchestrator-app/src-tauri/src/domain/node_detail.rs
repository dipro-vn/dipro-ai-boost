use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ArtifactRef {
    pub path: String,
    /// Path relative to the feature dir (or `runs/<run-id>/…` for
    /// QA/QC reports) — short enough to show inline in the panel.
    pub label: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct NodeDetail {
    pub artifacts: Vec<ArtifactRef>,
    /// RFC3339, from the most recently modified artifact's mtime. `None`
    /// when there are no artifacts yet.
    pub updated_at: Option<String>,
    /// `None` when no agent run has happened for this slot yet — never
    /// `0.0` as a stand-in for "unknown" (AC-E3-13).
    pub cost_usd: Option<f64>,
}
