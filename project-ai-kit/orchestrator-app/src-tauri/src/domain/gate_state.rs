use serde::{Deserialize, Serialize};

/// AC-E4-01/02/07 (Trigger gate v1). Deliberately a separate concept from
/// `NodeStatus` — a gate isn't an agent run, it's a human checkpoint with
/// its own data (approver, missing-section checklist) that no `NodeState`
/// field models.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "kebab-case")]
pub enum GateStatus {
    /// Open condition not met yet (e.g. `ba-agent` hasn't produced a
    /// complete `SPEC.md`).
    #[default]
    NotReady,
    /// Open condition met — waiting for the PM to Approve or Request
    /// changes.
    PendingReview,
    /// PM approved — sticky for v1 (see `inference::gate_rules`'s doc
    /// comment): once approved, a gate never reopens on its own even if
    /// `SPEC.md` changes again later.
    Approved,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct GateState {
    pub status: GateStatus,
    /// Free-text name entered by whoever clicked Approve — the app has no
    /// user-identity concept at all (v1 explicitly doesn't authenticate
    /// who's confirming, per SPEC), so this is a recorded label, not a
    /// verified identity.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub approved_by: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub approved_at: Option<String>,
    /// AC-E4-02's checklist — empty means `SPEC.md` has all 7 required
    /// sections (see `inference::spec_sections::REQUIRED_SPEC_SECTIONS`).
    #[serde(default)]
    pub missing_sections: Vec<String>,
}
