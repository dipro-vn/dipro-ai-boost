use serde::{Deserialize, Serialize};

/// All 7 SPEC-defined node states, plus `DoneIncomplete` (used when an
/// artifact exists but is missing required content — e.g. `SPEC.md` without
/// all its sections) and `DonePartial`. MVP1 can only ever produce `Idle`,
/// `Done`, `DonePartial`, and
/// `DoneIncomplete` from pure file-system inference — `Running`,
/// `WaitingInput`, `Failed`, `Blocked`, and `Skipped` all require a live
/// agent runner (MVP2+). The type still models all of them now so the
/// contract doesn't change out from under the frontend later.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum NodeStatus {
    Idle,
    Running,
    WaitingInput,
    Done,
    DoneIncomplete,
    /// Agent giao xong phần nó tự kiểm chứng được, nhưng TỰ KHAI là thiếu
    /// output phụ thuộc công cụ ngoài — hiện chỉ có BA: Output 1-3 (Figma
    /// MCP) và Output 5 (mkdocs) ghi `❌ Skipped` trong `## BA Deliverables`.
    ///
    /// Khác `DoneIncomplete` ở đúng một điểm quan trọng: nó **tính là hoàn
    /// thành** với `readiness::is_complete`, nên stage kế tiếp vẫn mở. Chặn
    /// pipeline vì một MCP người dùng chưa cấu hình là phạt họ cho thứ app
    /// không tự kiểm chứng được — nên nó cảnh báo, không chặn.
    DonePartial,
    Failed,
    Blocked,
    Skipped,
    /// AC-E6-04 — the app closed while this slot's agent was still running.
    /// Deliberately distinct from `Failed`: the UI offers Resume/Re-run here
    /// instead of Retry.
    Interrupted,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct NodeState {
    pub status: NodeStatus,
    /// Elaboration for non-obvious states — missing SPEC sections, why
    /// something is blocked, etc. `None` for the common `Idle`/`Done` case.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub detail: Option<String>,
    /// The 4 fields below are set only once an agent run has actually
    /// happened for this slot (MVP2+, AC-E2-08) — `None` for anything
    /// inferred purely from artifact presence. Layered on top of whatever
    /// `status` pure file-system inference computed (see
    /// `pipeline_state::apply_agent_run_metadata`) — a `Done` node can
    /// still carry the cost/session/timing of the run that produced it.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub session_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub cost_usd: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub started_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ended_at: Option<String>,
}

impl NodeState {
    pub fn idle() -> Self {
        NodeState {
            status: NodeStatus::Idle,
            detail: None,
            session_id: None,
            cost_usd: None,
            started_at: None,
            ended_at: None,
        }
    }

    pub fn done() -> Self {
        NodeState {
            status: NodeStatus::Done,
            detail: None,
            session_id: None,
            cost_usd: None,
            started_at: None,
            ended_at: None,
        }
    }

    pub fn done_incomplete(detail: impl Into<String>) -> Self {
        NodeState {
            status: NodeStatus::DoneIncomplete,
            detail: Some(detail.into()),
            session_id: None,
            cost_usd: None,
            started_at: None,
            ended_at: None,
        }
    }

    pub fn done_partial(detail: impl Into<String>) -> Self {
        NodeState {
            status: NodeStatus::DonePartial,
            detail: Some(detail.into()),
            session_id: None,
            cost_usd: None,
            started_at: None,
            ended_at: None,
        }
    }

    /// The agent ended its turn without producing the expected artifact and
    /// without erroring — inferred as having asked a question (AC-E2-15).
    /// `detail` is the agent's own last message, shown as the question.
    pub fn waiting_input(detail: impl Into<String>) -> Self {
        NodeState {
            status: NodeStatus::WaitingInput,
            detail: Some(detail.into()),
            session_id: None,
            cost_usd: None,
            started_at: None,
            ended_at: None,
        }
    }

    /// The agent exited with an error (or was killed for exceeding its
    /// timeout — AC-E2-10, `detail` says so explicitly to keep this
    /// distinguishable from an error the agent itself reported).
    pub fn failed(detail: impl Into<String>) -> Self {
        NodeState {
            status: NodeStatus::Failed,
            detail: Some(detail.into()),
            session_id: None,
            cost_usd: None,
            started_at: None,
            ended_at: None,
        }
    }

    /// AC-E2-11 — never spawned: the Ecosystem repo this slot targets
    /// hasn't been cloned yet. `detail` names the missing repo.
    pub fn blocked(detail: impl Into<String>) -> Self {
        NodeState {
            status: NodeStatus::Blocked,
            detail: Some(detail.into()),
            session_id: None,
            cost_usd: None,
            started_at: None,
            ended_at: None,
        }
    }

    /// AC-E2-12 — never spawned: the project's Ecosystem has no repo for
    /// the role this slot targets.
    pub fn skipped(detail: impl Into<String>) -> Self {
        NodeState {
            status: NodeStatus::Skipped,
            detail: Some(detail.into()),
            session_id: None,
            cost_usd: None,
            started_at: None,
            ended_at: None,
        }
    }

    /// A live run: a `running.json` marker exists for this slot and its
    /// process is still ours. Carries no run metadata — the previous run's
    /// cost/session would be misleading next to "đang chạy", and the live
    /// figures belong to the streaming log panel, not to `state.json`.
    pub fn running() -> Self {
        NodeState {
            status: NodeStatus::Running,
            detail: None,
            session_id: None,
            cost_usd: None,
            started_at: None,
            ended_at: None,
        }
    }

    /// AC-E6-04 — the app closed while this slot's agent was running.
    /// `detail` explains what happened and points at Resume/Re-run.
    pub fn interrupted(detail: impl Into<String>) -> Self {
        NodeState {
            status: NodeStatus::Interrupted,
            detail: Some(detail.into()),
            session_id: None,
            cost_usd: None,
            started_at: None,
            ended_at: None,
        }
    }

    pub fn with_run_metadata(
        mut self,
        session_id: String,
        cost_usd: f64,
        started_at: String,
        ended_at: String,
    ) -> Self {
        self.session_id = Some(session_id);
        self.cost_usd = Some(cost_usd);
        self.started_at = Some(started_at);
        self.ended_at = Some(ended_at);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A `state.json` written by MVP1 (before run-metadata fields existed)
    /// must still deserialize under MVP2's `NodeState` — old projects that
    /// opened the app before this change must not break.
    #[test]
    fn mvp1_shaped_json_without_run_metadata_fields_still_deserializes() {
        let old_shape = r#"{"status":"done-incomplete","detail":"Thiếu section: X"}"#;
        let node: NodeState = serde_json::from_str(old_shape).unwrap();
        assert_eq!(node.status, NodeStatus::DoneIncomplete);
        assert_eq!(node.detail.as_deref(), Some("Thiếu section: X"));
        assert!(node.session_id.is_none());
        assert!(node.cost_usd.is_none());
    }

    #[test]
    fn with_run_metadata_layers_onto_any_status_without_changing_it() {
        let node = NodeState::done().with_run_metadata(
            "sess-1".to_string(),
            0.05,
            "2026-01-01T00:00:00Z".to_string(),
            "2026-01-01T00:01:00Z".to_string(),
        );
        assert_eq!(node.status, NodeStatus::Done);
        assert_eq!(node.session_id.as_deref(), Some("sess-1"));
        assert_eq!(node.cost_usd, Some(0.05));
    }

    #[test]
    fn run_metadata_fields_are_omitted_from_json_when_absent() {
        // skip_serializing_if keeps state.json diffs small and old-app
        // round-trips lossless for the common case.
        let json = serde_json::to_string(&NodeState::idle()).unwrap();
        assert!(!json.contains("sessionId"));
        assert!(!json.contains("costUsd"));
    }
}
