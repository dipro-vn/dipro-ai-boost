//! "Can this slot be run right now?" — a PURE function over
//! (`PipelineDef`, current slot statuses, passed gates, discovered agents).
//!
//! This replaces the old auto-chaining engine (`compute_chain_actions`).
//! The pipeline no longer starts anything by itself: every run is a
//! deliberate click, because every run costs real money and approving one
//! gate used to silently launch three agents at once (B22). The dependency
//! rules are unchanged — they just answer a different question now:
//! instead of "who should I spawn next", it is "may the user spawn this".
//!
//! Rules (same as the chaining engine encoded, same tests ported):
//! - A stage is complete ⇔ every slot is `Done` or `Skipped`.
//!   `DoneIncomplete` deliberately does NOT count — an artifact that exists
//!   but is missing required content shouldn't feed the next stage.
//! - Intra-stage `after_slots`: a slot is blocked until every slot it waits
//!   for is `Done` (`frontend`/`mobile` after `backend`).
//! - The predecessor stage comes from `depends_on`, falling back to list
//!   order for a `pipeline.json` written before that field existed.
//! - A gate stage in front (Trigger, Contract Lock, ⑧ Deploy) blocks until
//!   the human passes it.
//! - A slot whose agent file isn't in the kit can't run at all.
//! - A slot that targets a repo (backend/frontend/mobile) can't run when
//!   that repo is missing from the Ecosystem table or not on disk
//!   (AC-E2-11/12). Same check `run_to_completion` makes right before
//!   spawning — shared here so the Run button can say so BEFORE the click
//!   instead of the user paying for a blocked run to find out.

use std::collections::BTreeMap;

use serde::Serialize;

use crate::domain::node_status::NodeStatus;
use crate::domain::pipeline_def::{slot, PipelineDef};
use crate::domain::project::EcosystemRepo;

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(
    tag = "kind",
    rename_all = "camelCase",
    rename_all_fields = "camelCase"
)]
pub enum SlotReadiness {
    /// Everything upstream is satisfied — the Run button is enabled.
    Ready,
    /// Upstream slots that still have to finish, named so the UI can say
    /// exactly what is being waited on.
    Waiting { blocked_by: Vec<String> },
    /// A gate stage in front hasn't been approved/locked yet.
    GateNotPassed { gate_label: String },
    /// `.claude/agents/<agent_name>.md` doesn't exist in this project's kit.
    AgentMissing { agent_name: String },
    /// AC-E2-11 — the repo this slot targets is declared in `AGENTS.md` but
    /// its path resolves to nothing on disk. Carries `declared_path` too:
    /// the usual cause is a wrong `repositoryRoot`, not a missing clone, and
    /// the user can only tell the two apart by seeing the declared path.
    RepoNotCloned {
        repo_name: String,
        declared_path: String,
    },
    /// AC-E2-12 — no repo of this role exists in the Ecosystem at all, so
    /// the slot doesn't apply to this project.
    RepoRoleMissing { role: String },
    /// The slot isn't declared in `pipeline.json` at all.
    UnknownSlot,
}

/// The repo role a slot works in, or `None` for slots that operate at the
/// feature/docs level (BA, Tech Lead, PM, QC...) and never touch a repo.
pub fn slot_repo_role(slot_id: &str) -> Option<&'static str> {
    match slot_id {
        s if s == slot::BACKEND => Some("backend"),
        s if s == slot::FRONTEND => Some("frontend"),
        s if s == slot::MOBILE => Some("mobile"),
        _ => None,
    }
}

/// AC-E2-11/12. Only `backend`/`frontend`/`mobile` target a specific repo
/// role; every other slot works at the feature/docs level and is always
/// `Ready`.
#[derive(Debug)]
pub enum RepoReadiness {
    Ready,
    /// AC-E2-12 — no repo of this role exists in the Ecosystem at all.
    RoleNotInEcosystem,
    /// AC-E2-11 — a repo of this role exists but isn't cloned yet. Carries
    /// the repo's name and declared path so the message can be specific.
    RepoNotCloned {
        name: String,
        declared_path: String,
    },
}

pub fn resolve_repo_readiness(ecosystem: &[EcosystemRepo], slot_id: &str) -> RepoReadiness {
    let Some(role) = slot_repo_role(slot_id) else {
        return RepoReadiness::Ready;
    };
    match ecosystem
        .iter()
        .find(|repo| repo.role.eq_ignore_ascii_case(role))
    {
        None => RepoReadiness::RoleNotInEcosystem,
        Some(repo) if !repo.cloned => RepoReadiness::RepoNotCloned {
            name: repo.name.clone(),
            declared_path: repo.declared_path.clone(),
        },
        Some(_) => RepoReadiness::Ready,
    }
}

/// Stage nuôi `stage_idx`: theo `depends_on`, không có thì lùi về stage
/// liền trước (`pipeline.json` viết trước khi có field đó).
fn predecessor_index(def: &PipelineDef, stage_idx: usize) -> Option<usize> {
    let stage = &def.stages[stage_idx];
    def.stages
        .iter()
        .position(|s| Some(s.id.as_str()) == stage.depends_on.as_deref())
        .or_else(|| (stage.depends_on.is_none() && stage_idx > 0).then(|| stage_idx - 1))
}

fn is_complete(status: Option<&NodeStatus>) -> bool {
    matches!(status, Some(NodeStatus::Done) | Some(NodeStatus::Skipped))
}

/// `statuses` is keyed by slot id; a missing entry counts as `Idle`.
/// `passed_gates` holds the stage ids of gates the user has already cleared
/// (Trigger gate approved, Contract Lock locked) — gate state lives outside
/// `statuses`, which only ever holds agent slots.
///
/// `skipped_gates` là loại khác hẳn: gate KHÔNG áp dụng cho feature này
/// (Contract Lock trên feature 1 repo). Nó không mở khoá gì cả — nó trong
/// suốt, nên phải nhìn xuyên qua tới stage nuôi chính nó. Gộp chung vào
/// `passed_gates` thì stage ⑤ mở ngay cả khi feature mới chỉ có `INPUT.md`.
pub fn compute_slot_readiness(
    def: &PipelineDef,
    statuses: &BTreeMap<String, NodeStatus>,
    passed_gates: &[String],
    skipped_gates: &[String],
    agents_found: &[String],
    ecosystem: &[EcosystemRepo],
    slot_id: &str,
) -> SlotReadiness {
    let Some(stage_idx) = def
        .stages
        .iter()
        .position(|stage| stage.agents.iter().any(|a| a.id == slot_id))
    else {
        return SlotReadiness::UnknownSlot;
    };
    let stage = &def.stages[stage_idx];
    let agent_slot = stage
        .agents
        .iter()
        .find(|a| a.id == slot_id)
        .expect("slot was just located in this stage");

    if !agents_found.contains(&agent_slot.agent_name) {
        return SlotReadiness::AgentMissing {
            agent_name: agent_slot.agent_name.clone(),
        };
    }

    // Before any dependency talk: a missing repo is a configuration problem
    // that waiting will never resolve, so it outranks "chờ stage trước".
    match resolve_repo_readiness(ecosystem, slot_id) {
        RepoReadiness::RepoNotCloned {
            name,
            declared_path,
        } => {
            return SlotReadiness::RepoNotCloned {
                repo_name: name,
                declared_path,
            }
        }
        RepoReadiness::RoleNotInEcosystem => {
            return SlotReadiness::RepoRoleMissing {
                role: slot_repo_role(slot_id).unwrap_or(slot_id).to_string(),
            }
        }
        RepoReadiness::Ready => {}
    }

    // Intra-stage dependencies first: they're the most specific answer, and
    // the most common one the user will hit (FE/Mobile waiting on backend).
    let unmet: Vec<String> = agent_slot
        .after_slots
        .iter()
        .filter(|dep| !matches!(statuses.get(dep.as_str()), Some(NodeStatus::Done)))
        .cloned()
        .collect();
    if !unmet.is_empty() {
        return SlotReadiness::Waiting { blocked_by: unmet };
    }

    // Then whatever stage feeds this one. Gate được người duyệt thì DỪNG ở
    // đó — chữ ký đó chính là điều kiện. Gate không áp dụng thì đi tiếp
    // xuống stage nuôi nó, vì nó không xác nhận điều gì cả.
    let mut cursor = stage_idx;
    for _ in 0..def.stages.len() {
        let Some(pred_idx) = predecessor_index(def, cursor) else {
            return SlotReadiness::Ready; // first stage — nothing upstream
        };
        let predecessor = &def.stages[pred_idx];

        if predecessor.agents.is_empty() {
            if passed_gates.iter().any(|id| id == &predecessor.id) {
                return SlotReadiness::Ready;
            }
            if !skipped_gates.iter().any(|id| id == &predecessor.id) {
                return SlotReadiness::GateNotPassed {
                    gate_label: predecessor.label.clone(),
                };
            }
            cursor = pred_idx;
            continue;
        }

        let incomplete: Vec<String> = predecessor
            .agents
            .iter()
            .filter(|a| !is_complete(statuses.get(&a.id)))
            .map(|a| a.id.clone())
            .collect();
        return if incomplete.is_empty() {
            SlotReadiness::Ready
        } else {
            SlotReadiness::Waiting {
                blocked_by: incomplete,
            }
        };
    }
    // `depends_on` vòng lặp — pipeline.json hỏng. Không chặn người dùng vì
    // một file cấu hình sai; guard này chỉ để vòng lặp trên luôn kết thúc.
    SlotReadiness::Ready
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::pipeline_def::{gate, slot};

    /// Every agent name from the default template — "the kit is complete".
    fn all_agents() -> Vec<String> {
        PipelineDef::default()
            .stages
            .into_iter()
            .flat_map(|s| s.agents)
            .map(|a| a.agent_name)
            .collect()
    }

    fn repo(name: &str, role: &str, cloned: bool) -> EcosystemRepo {
        EcosystemRepo {
            name: name.to_string(),
            declared_path: name.to_string(),
            role: role.to_string(),
            stack: String::new(),
            cloned,
        }
    }

    /// Every dev repo present and cloned — the baseline for the dependency
    /// tests, which are about stage order, not about repos.
    fn full_ecosystem() -> Vec<EcosystemRepo> {
        vec![
            repo("api", "backend", true),
            repo("web", "frontend", true),
            repo("app", "mobile", true),
        ]
    }

    fn statuses(entries: &[(&str, NodeStatus)]) -> BTreeMap<String, NodeStatus> {
        entries.iter().map(|(k, v)| (k.to_string(), *v)).collect()
    }

    fn readiness(
        st: &BTreeMap<String, NodeStatus>,
        passed_gates: &[String],
        slot_id: &str,
    ) -> SlotReadiness {
        compute_slot_readiness(
            &PipelineDef::default(),
            st,
            passed_gates,
            &[],
            &all_agents(),
            &full_ecosystem(),
            slot_id,
        )
    }

    /// Ported from `stage_two_complete_spawns_stage_three_in_parallel`.
    #[test]
    fn stage_three_is_ready_once_stage_two_is_complete() {
        let st = statuses(&[
            (slot::TECHLEAD_DESIGN, NodeStatus::Done),
            (slot::DESIGN_ANALYST, NodeStatus::Skipped),
            (slot::QC_DESIGN, NodeStatus::Done),
        ]);
        assert_eq!(
            readiness(&st, &[], slot::TECHLEAD_TASKS),
            SlotReadiness::Ready
        );
        assert_eq!(readiness(&st, &[], slot::PM), SlotReadiness::Ready);
    }

    /// Ported from `incomplete_stage_spawns_nothing` — and now the UI can
    /// say WHICH slot it is waiting for.
    #[test]
    fn an_incomplete_predecessor_stage_names_what_is_missing() {
        let st = statuses(&[
            (slot::TECHLEAD_DESIGN, NodeStatus::Done),
            (slot::DESIGN_ANALYST, NodeStatus::Skipped),
            (slot::QC_DESIGN, NodeStatus::Running),
        ]);
        assert_eq!(
            readiness(&st, &[], slot::TECHLEAD_TASKS),
            SlotReadiness::Waiting {
                blocked_by: vec![slot::QC_DESIGN.to_string()]
            }
        );
    }

    /// `DoneIncomplete` must not unlock the next stage.
    #[test]
    fn done_incomplete_does_not_count_as_complete() {
        let st = statuses(&[
            (slot::TECHLEAD_DESIGN, NodeStatus::DoneIncomplete),
            (slot::DESIGN_ANALYST, NodeStatus::Skipped),
            (slot::QC_DESIGN, NodeStatus::Done),
        ]);
        assert!(matches!(
            readiness(&st, &[], slot::TECHLEAD_TASKS),
            SlotReadiness::Waiting { .. }
        ));
    }

    /// Ported from `backend_done_spawns_frontend_and_mobile_in_parallel`.
    #[test]
    fn frontend_and_mobile_wait_for_backend_then_become_ready() {
        let locked = vec![gate::CONTRACT_LOCK.to_string()];

        let before = statuses(&[(slot::BACKEND, NodeStatus::Running)]);
        assert_eq!(
            readiness(&before, &locked, slot::FRONTEND),
            SlotReadiness::Waiting {
                blocked_by: vec![slot::BACKEND.to_string()]
            }
        );

        let after = statuses(&[(slot::BACKEND, NodeStatus::Done)]);
        assert_eq!(
            readiness(&after, &locked, slot::FRONTEND),
            SlotReadiness::Ready
        );
        assert_eq!(
            readiness(&after, &locked, slot::MOBILE),
            SlotReadiness::Ready
        );
    }

    /// A `Skipped` backend does NOT satisfy `after_slots` — that rule is
    /// stricter than stage completeness on purpose: FE/Mobile need the
    /// backend's API contract, not merely its absence.
    #[test]
    fn skipped_backend_still_blocks_frontend() {
        let st = statuses(&[(slot::BACKEND, NodeStatus::Skipped)]);
        assert!(matches!(
            readiness(&st, &[gate::CONTRACT_LOCK.to_string()], slot::FRONTEND),
            SlotReadiness::Waiting { .. }
        ));
    }

    /// Ported from the gate-stops-the-chain tests: a gate in front blocks
    /// until the human clears it.
    #[test]
    fn a_gate_in_front_blocks_until_passed() {
        let st = statuses(&[(slot::BA, NodeStatus::Done)]);

        let blocked = readiness(&st, &[], slot::TECHLEAD_DESIGN);
        assert!(
            matches!(blocked, SlotReadiness::GateNotPassed { .. }),
            "got {blocked:?}"
        );

        assert_eq!(
            readiness(&st, &[gate::TRIGGER.to_string()], slot::TECHLEAD_DESIGN),
            SlotReadiness::Ready
        );
    }

    // --- repo readiness (AC-E2-11/12), moved here from `commands::agentrun`
    // so the Run button and the pre-spawn guard can never disagree ---

    #[test]
    fn slots_without_a_repo_role_are_always_ready() {
        for non_repo_slot in [slot::BA, slot::TECHLEAD_DESIGN, slot::PM, slot::QA] {
            assert!(matches!(
                resolve_repo_readiness(&[], non_repo_slot),
                RepoReadiness::Ready
            ));
        }
    }

    #[test]
    fn backend_slot_ready_when_matching_repo_is_cloned() {
        assert!(matches!(
            resolve_repo_readiness(&[repo("api", "backend", true)], slot::BACKEND),
            RepoReadiness::Ready
        ));
    }

    #[test]
    fn ac_e2_11_backend_slot_blocked_when_repo_not_cloned() {
        match resolve_repo_readiness(&[repo("api", "backend", false)], slot::BACKEND) {
            RepoReadiness::RepoNotCloned {
                name,
                declared_path,
            } => {
                assert_eq!(name, "api");
                assert_eq!(declared_path, "api");
            }
            other => panic!("expected RepoNotCloned, got a different readiness ({other:?})"),
        }
    }

    #[test]
    fn ac_e2_12_mobile_slot_skipped_when_no_mobile_repo_declared() {
        let ecosystem = vec![repo("api", "backend", true), repo("web", "frontend", true)];
        assert!(matches!(
            resolve_repo_readiness(&ecosystem, slot::MOBILE),
            RepoReadiness::RoleNotInEcosystem
        ));
    }

    #[test]
    fn repo_role_matching_is_case_insensitive() {
        assert!(matches!(
            resolve_repo_readiness(&[repo("api", "Backend", true)], slot::BACKEND),
            RepoReadiness::Ready
        ));
    }

    /// The gap this whole change closes: with the repo missing the Run
    /// button used to look enabled, and the user only learned otherwise by
    /// clicking and paying for a blocked run.
    #[test]
    fn backend_is_not_runnable_when_its_repo_is_not_cloned() {
        let st = statuses(&[(slot::BA, NodeStatus::Done)]);
        assert_eq!(
            compute_slot_readiness(
                &PipelineDef::default(),
                &st,
                &[gate::TRIGGER.to_string(), gate::CONTRACT_LOCK.to_string()],
                &[],
                &all_agents(),
                &[repo("example-api", "backend", false)],
                slot::BACKEND,
            ),
            SlotReadiness::RepoNotCloned {
                repo_name: "example-api".to_string(),
                declared_path: "example-api".to_string(),
            }
        );
    }

    #[test]
    fn a_slot_whose_repo_role_is_absent_reports_the_role() {
        let st = statuses(&[(slot::BA, NodeStatus::Done)]);
        assert_eq!(
            compute_slot_readiness(
                &PipelineDef::default(),
                &st,
                &[gate::TRIGGER.to_string(), gate::CONTRACT_LOCK.to_string()],
                &[],
                &all_agents(),
                &[repo("api", "backend", true)],
                slot::MOBILE,
            ),
            SlotReadiness::RepoRoleMissing {
                role: "mobile".to_string()
            }
        );
    }

    /// A repo problem is a configuration problem — waiting never fixes it,
    /// so it must win over "đang chờ stage trước".
    #[test]
    fn a_missing_repo_outranks_an_unfinished_predecessor() {
        assert_eq!(
            compute_slot_readiness(
                &PipelineDef::default(),
                &statuses(&[]),
                &[],
                &[],
                &all_agents(),
                &[repo("example-api", "backend", false)],
                slot::BACKEND,
            ),
            SlotReadiness::RepoNotCloned {
                repo_name: "example-api".to_string(),
                declared_path: "example-api".to_string(),
            }
        );
    }

    /// Ported from the skip-missing-agent behaviour (AC-E2-40).
    #[test]
    fn a_slot_whose_agent_file_is_absent_reports_the_agent_name() {
        let def = PipelineDef::default();
        let without_analyst: Vec<String> = all_agents()
            .into_iter()
            .filter(|name| name != "design-analyst-agent")
            .collect();

        assert_eq!(
            compute_slot_readiness(
                &def,
                &statuses(&[(slot::BA, NodeStatus::Done)]),
                &[gate::TRIGGER.to_string()],
                &[],
                &without_analyst,
                &full_ecosystem(),
                slot::DESIGN_ANALYST,
            ),
            SlotReadiness::AgentMissing {
                agent_name: "design-analyst-agent".to_string()
            }
        );
    }

    #[test]
    fn the_first_stage_is_always_ready() {
        assert_eq!(
            readiness(&statuses(&[]), &[], slot::BA),
            SlotReadiness::Ready
        );
    }

    #[test]
    fn an_unknown_slot_is_reported_rather_than_assumed_runnable() {
        assert_eq!(
            readiness(&statuses(&[]), &[], "not-a-slot"),
            SlotReadiness::UnknownSlot
        );
    }
}
