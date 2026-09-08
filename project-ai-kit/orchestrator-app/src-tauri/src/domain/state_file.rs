use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::domain::contract_lock::ContractLockState;
use crate::domain::gate_state::GateState;
use crate::domain::node_status::NodeState;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct FeatureState {
    /// Keyed by `domain::pipeline_def::slot::*` id.
    pub nodes: BTreeMap<String, NodeState>,
    /// Keyed by gate stage id (e.g. `"S1b_trigger"`) — separate from
    /// `nodes` since a gate isn't an agent run and carries different data
    /// (approver, checklist). `#[serde(default)]` so a `state.json` from
    /// before this field existed still deserializes.
    #[serde(default)]
    pub gates: BTreeMap<String, GateState>,
    /// The Contract Lock gate (AC-E4-08..20) — a dedicated field rather
    /// than another `gates` entry, since its data shape (files, checksums,
    /// roles, content) has nothing in common with `GateState`, and there's
    /// only ever one per feature. `None` before it's ever been computed
    /// (or for a `state.json` from before this field existed).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub contract_lock: Option<ContractLockState>,
    /// RFC3339, stamped whenever this feature's state is recomputed.
    pub updated_at: String,
}

/// `.ai-boost/state.json`. Only holds what MVP1 can actually compute —
/// per-feature node states from file-system inference. Run history / cost
/// (mentioned in `OVERVIEW.md` §6's illustrative `state.json` shape) has no
/// producer until MVP2's agent runner exists, so it isn't modeled here yet.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct StateFile {
    /// Keyed by feature id (folder name under `features/`).
    pub features: BTreeMap<String, FeatureState>,
}
