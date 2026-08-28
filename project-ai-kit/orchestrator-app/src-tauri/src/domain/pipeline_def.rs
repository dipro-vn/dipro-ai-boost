use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AgentSlot {
    /// Stable id used as the key in `FeatureState.nodes` — must match
    /// exactly what `inference::stage_rules` computes. Kept as string
    /// constants below rather than duplicated literals, to keep the two
    /// modules from drifting apart.
    pub id: String,
    /// The `.claude/agents/<agent_name>.md` this slot corresponds to.
    pub agent_name: String,
    /// Display name on the Board. Deliberately separate from `agent_name`:
    /// two slots can share one agent file (`qc-design`/`qc-testing` both
    /// map to `qc-agent`), and the board then renders two nodes with the
    /// same visible name and no way to tell what either one does.
    /// Presentation-only — never used for readiness or spawning. `None`
    /// falls back to `agent_name`, so a `pipeline.json` written before this
    /// field existed still renders exactly as it did.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub label: Option<String>,
    /// AC-E2-03 — slot ids in the SAME stage this slot must wait for
    /// (`frontend`/`mobile` wait for `backend`). Empty for every other
    /// slot. `#[serde(default)]` so a `pipeline.json` written before this
    /// field existed still deserializes.
    #[serde(default)]
    pub after_slots: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct StageDef {
    pub id: String,
    pub label: String,
    pub agents: Vec<AgentSlot>,
    /// AC-E2-01 — the stage that must be complete before this one may
    /// start, declared explicitly rather than inferred from list order.
    /// `None` for the first stage. `#[serde(default)]` so an old
    /// `pipeline.json` still deserializes — readiness treats a
    /// missing value on a non-first stage as "depends on the previous
    /// stage in list order" (see `agentrun::readiness`).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub depends_on: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PipelineDef {
    /// Schema version of the stage topology below.
    ///
    /// Exists because a `pipeline.json` written by an older build stays on
    /// disk forever otherwise: it still parses (serde fills new fields with
    /// defaults), so the project silently keeps the old topology. That
    /// really happened — a file written before the Trigger gate existed
    /// left a project with 8 stages, no gate, and every `depends_on` empty,
    /// which let the old chaining engine walk straight past the gate.
    /// `commands::pipeline::load_pipeline_def` migrates anything below
    /// `PIPELINE_DEF_VERSION`.
    ///
    /// `0` for files written before this field existed.
    #[serde(default)]
    pub version: u32,
    pub stages: Vec<StageDef>,
}

/// Bump whenever `PipelineDef::default()`'s stage topology changes, so
/// existing projects pick the change up instead of keeping a stale file.
/// `1` = the pre-gate 8-stage layout (never carried this field, reads as
/// `0`); `2` = the 9-stage layout with both gates and explicit
/// `depends_on`; `3` = the same layout plus a per-slot display `label`;
/// `4` = the `pm` slot removed from stage ③ along with `pm-agent`.
pub const PIPELINE_DEF_VERSION: u32 = 4;

/// Slot ids — the single source of truth `inference::stage_rules` keys its
/// output by. Stage ④ (Contract Lock) and ⑧ (Deploy) intentionally have no
/// slots: they're gates/manual checklists, not agents (AC-E4/§Deploy —
/// "không tự suy, không hiện badge").
pub mod slot {
    pub const BA: &str = "ba";
    pub const TECHLEAD_DESIGN: &str = "techlead-design";
    pub const DESIGN_ANALYST: &str = "design-analyst";
    pub const QC_DESIGN: &str = "qc-design";
    pub const TECHLEAD_TASKS: &str = "techlead-tasks";
    pub const BACKEND: &str = "backend";
    pub const FRONTEND: &str = "frontend";
    pub const MOBILE: &str = "mobile";
    pub const QA: &str = "qa";
    pub const QC_TESTING: &str = "qc-testing";
    pub const QC_AUTOMATION: &str = "qc-automation";
}

/// Gate stage ids — the single source of truth for `FeatureState.gates`/
/// `FeatureState.contract_lock` keys and for identifying which `StageDef`
/// a gate-specific frontend panel (e.g. `TriggerGatePanel`,
/// `ContractLockPanel`) applies to. Only the gates the app actually
/// implements get a constant here; `S8_deploy` stays purely structural
/// (empty `agents`) until MVP4 builds it.
pub mod gate {
    pub const TRIGGER: &str = "S1b_trigger";
    pub const CONTRACT_LOCK: &str = "S4_contract_lock";
}

fn slot(id: &str, agent_name: &str, label: &str) -> AgentSlot {
    AgentSlot {
        id: id.to_string(),
        agent_name: agent_name.to_string(),
        label: Some(label.to_string()),
        after_slots: vec![],
    }
}

fn slot_after(id: &str, agent_name: &str, label: &str, after: &[&str]) -> AgentSlot {
    AgentSlot {
        id: id.to_string(),
        agent_name: agent_name.to_string(),
        label: Some(label.to_string()),
        after_slots: after.iter().map(|s| s.to_string()).collect(),
    }
}

/// The v1 template — matches the ①..⑧ numbering (decision B8) and the
/// per-stage agent table in `orchestrator-pipeline-execution/SPEC.md`.
/// Declared explicitly rather than inferred from `.claude/agents/` file
/// names, per `AC-E2-01` — including the inter-stage `depends_on` chain
/// and the one intra-stage dependency (⑤: FE/Mobile after BE, AC-E2-03).
impl Default for PipelineDef {
    fn default() -> Self {
        PipelineDef {
            version: PIPELINE_DEF_VERSION,
            stages: vec![
                StageDef {
                    id: "S1_input".to_string(),
                    label: "① Input".to_string(),
                    agents: vec![slot(slot::BA, "ba-agent", "BA · SPEC")],
                    depends_on: None,
                },
                // AC-E4-01..07 — a gate stage like ④/⑧ (empty `agents`,
                // rendered as a clickable gate node by `PipelineTree.tsx`
                // with zero frontend changes needed). Sits between ① and ②
                // — `ba-agent` finishing does not by itself spawn stage ②;
                // only `commands::agentrun::approve_trigger_gate` does.
                StageDef {
                    id: gate::TRIGGER.to_string(),
                    label: "🚦 Trigger Gate".to_string(),
                    agents: vec![],
                    depends_on: Some("S1_input".to_string()),
                },
                StageDef {
                    id: "S2_design".to_string(),
                    label: "② Design".to_string(),
                    agents: vec![
                        slot(
                            slot::TECHLEAD_DESIGN,
                            "techlead-design-agent",
                            "Tech Lead · Design",
                        ),
                        // Agent file does not exist in the kit yet (B17) —
                        // this slot is declared regardless so the node
                        // shows up as `idle` rather than being silently
                        // absent from the board.
                        slot(
                            slot::DESIGN_ANALYST,
                            "design-analyst-agent",
                            "Design Analyst",
                        ),
                        slot(slot::QC_DESIGN, "qc-agent", "QC · Test Cases"),
                    ],
                    depends_on: Some(gate::TRIGGER.to_string()),
                },
                StageDef {
                    id: "S3_planning".to_string(),
                    label: "③ Planning".to_string(),
                    agents: vec![slot(
                        slot::TECHLEAD_TASKS,
                        "techlead-tasks-agent",
                        "Tech Lead · Tasks",
                    )],
                    depends_on: Some("S2_design".to_string()),
                },
                StageDef {
                    id: gate::CONTRACT_LOCK.to_string(),
                    label: "④ Contract Lock".to_string(),
                    agents: vec![],
                    depends_on: Some("S3_planning".to_string()),
                },
                StageDef {
                    id: "S5_build".to_string(),
                    label: "⑤ Build".to_string(),
                    agents: vec![
                        slot(slot::BACKEND, "backend-agent", "Backend"),
                        slot_after(
                            slot::FRONTEND,
                            "frontend-agent",
                            "Frontend",
                            &[slot::BACKEND],
                        ),
                        slot_after(slot::MOBILE, "mobile-agent", "Mobile", &[slot::BACKEND]),
                    ],
                    depends_on: Some(gate::CONTRACT_LOCK.to_string()),
                },
                StageDef {
                    id: "S6_verify".to_string(),
                    label: "⑥ Verify".to_string(),
                    agents: vec![slot(slot::QA, "qa-agent", "QA · Verify")],
                    depends_on: Some("S5_build".to_string()),
                },
                StageDef {
                    id: "S7_testing".to_string(),
                    label: "⑦ Testing".to_string(),
                    agents: vec![
                        slot(slot::QC_TESTING, "qc-agent", "QC · Execution"),
                        slot(
                            slot::QC_AUTOMATION,
                            "qc-automation-agent",
                            "QC · Automation",
                        ),
                    ],
                    depends_on: Some("S6_verify".to_string()),
                },
                StageDef {
                    id: "S8_deploy".to_string(),
                    label: "⑧ Deploy".to_string(),
                    agents: vec![],
                    depends_on: Some("S7_testing".to_string()),
                },
            ],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A `pipeline.json` written before `depends_on`/`after_slots` existed
    /// must still deserialize — old projects keep working, they just don't
    /// get the new fields until the file is regenerated.
    #[test]
    fn old_pipeline_json_without_dependency_fields_still_deserializes() {
        let old_shape = r#"{
            "stages": [
                { "id": "S1_input", "label": "① Input",
                  "agents": [{ "id": "ba", "agentName": "ba-agent" }] },
                { "id": "S2_design", "label": "② Design", "agents": [] }
            ]
        }"#;
        let def: PipelineDef = serde_json::from_str(old_shape).unwrap();
        assert_eq!(def.stages.len(), 2);
        assert!(def.stages[0].depends_on.is_none());
        assert!(def.stages[0].agents[0].after_slots.is_empty());
        // No `label` in the file — the board falls back to `agentName`.
        assert!(def.stages[0].agents[0].label.is_none());
    }

    #[test]
    fn default_template_declares_the_full_dependency_chain() {
        let def = PipelineDef::default();
        // Every stage except the first declares its predecessor explicitly.
        assert!(def.stages[0].depends_on.is_none());
        for pair in def.stages.windows(2) {
            assert_eq!(pair[1].depends_on.as_deref(), Some(pair[0].id.as_str()));
        }
        // AC-E2-03 — FE/Mobile wait for BE within stage ⑤.
        let build = def.stages.iter().find(|s| s.id == "S5_build").unwrap();
        for slot_id in [slot::FRONTEND, slot::MOBILE] {
            let s = build.agents.iter().find(|a| a.id == slot_id).unwrap();
            assert_eq!(s.after_slots, vec![slot::BACKEND.to_string()]);
        }
        assert!(build
            .agents
            .iter()
            .find(|a| a.id == slot::BACKEND)
            .unwrap()
            .after_slots
            .is_empty());
    }

    #[test]
    fn every_slot_in_default_template_has_a_label() {
        for stage in PipelineDef::default().stages {
            for agent in stage.agents {
                let label = agent.label.unwrap_or_default();
                assert!(!label.trim().is_empty(), "slot {} has no label", agent.id);
            }
        }
    }

    /// The reason `label` exists: `qc-design` and `qc-testing` both spawn
    /// `qc-agent`, so before this the board drew two nodes reading
    /// `qc-agent` with nothing to tell them apart. Guards the next slot
    /// that reuses an agent file and forgets to name itself.
    #[test]
    fn slot_labels_are_unique_across_the_template() {
        let mut seen = std::collections::BTreeSet::new();
        for stage in PipelineDef::default().stages {
            for agent in stage.agents {
                let label = agent.label.expect("every slot is labelled");
                assert!(seen.insert(label.clone()), "duplicate slot label {label}");
            }
        }
    }
}
