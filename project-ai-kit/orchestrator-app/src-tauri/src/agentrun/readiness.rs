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
use crate::domain::pipeline_def::{is_checkpoint_stage, slot, PipelineDef};
use crate::domain::pipeline_expand;
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
    /// No repo matched this role, but at least one repo's Vai trò cell
    /// couldn't be read as a role at all — so "this project has no frontend"
    /// is almost certainly the wrong conclusion to hand the user. Names the
    /// offending repos and their cells verbatim so the fix is a one-line
    /// edit in `AGENTS.md` rather than a hunt.
    RepoRoleUnreadable {
        role: String,
        entries: Vec<UnreadableRole>,
    },
    /// This feature has no `task-*.md` for the repo role this slot targets,
    /// so there is nothing for its agent to do — distinct from
    /// `RepoRoleMissing` (the PROJECT has no such repo at all) and from a
    /// manual Skip (the user decided, rather than the plan).
    NoWorkInFeature { role: String },
    /// The slot isn't declared in `pipeline.json` at all.
    UnknownSlot,
}

/// The Ecosystem row a slot works in, or `None` for slots that operate at
/// the feature/docs level (BA, Tech Lead, QC...) and never touch a repo.
pub fn slot_repo<'a>(ecosystem: &'a [EcosystemRepo], slot_id: &str) -> Option<&'a EcosystemRepo> {
    pipeline_expand::slot_repo(ecosystem, slot_id)
}

/// Whether a slot targets a repo at all — the test every "is this a dev
/// slot" branch wants.
///
/// A string test, not an Ecosystem lookup, so it still answers correctly
/// for a run log written before the repo was removed from `AGENTS.md`. The
/// three legacy role ids stay recognised because `expand_build_stage` falls
/// back to them when the Ecosystem is empty.
pub fn slot_targets_repo(slot_id: &str) -> bool {
    pipeline_expand::is_build_slot(slot_id)
        || slot_id == slot::BACKEND
        || slot_id == slot::FRONTEND
        || slot_id == slot::MOBILE
}

/// What to call this slot's target in a user-facing reason: the repo name
/// for a per-repo build slot, else the legacy role, else the raw id.
///
/// With four web repos, "project không có repo vai trò frontend" names
/// nothing the user can act on — the repo name does.
fn slot_target_label(ecosystem: &[EcosystemRepo], slot_id: &str) -> String {
    if let Some(repo) = pipeline_expand::slot_repo(ecosystem, slot_id) {
        return repo.name.clone();
    }
    static_slot_role(slot_id).unwrap_or(slot_id).to_string()
}

/// The role of the legacy static slots. Only reachable through
/// `expand_build_stage`'s empty-Ecosystem fallback.
fn static_slot_role(slot_id: &str) -> Option<&'static str> {
    match slot_id {
        s if s == slot::BACKEND => Some("backend"),
        s if s == slot::FRONTEND => Some("frontend"),
        s if s == slot::MOBILE => Some("mobile"),
        _ => None,
    }
}

/// One Ecosystem row whose Vai trò cell the app could not read, quoted
/// back verbatim for the error message.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct UnreadableRole {
    pub repo_name: String,
    pub declared_role: String,
}

/// AC-E2-11/12. Only `backend`/`frontend`/`mobile` target a specific repo
/// role; every other slot works at the feature/docs level and is always
/// `Ready`.
#[derive(Debug)]
pub enum RepoReadiness {
    Ready,
    /// AC-E2-12 — no repo of this role exists in the Ecosystem at all.
    RoleNotInEcosystem,
    /// No repo matched, and the Ecosystem contains rows whose Vai trò cell
    /// is unreadable — report those instead of claiming the role is absent.
    RoleUnreadable { entries: Vec<UnreadableRole> },
    /// AC-E2-11 — a repo of this role exists but isn't cloned yet. Carries
    /// the repo's name and declared path so the message can be specific.
    RepoNotCloned {
        name: String,
        declared_path: String,
    },
    /// The slot names a repo the Ecosystem no longer lists.
    RepoNotInEcosystem,
}

pub fn resolve_repo_readiness(ecosystem: &[EcosystemRepo], slot_id: &str) -> RepoReadiness {
    // A per-repo build slot judges its OWN repo. The old code took the
    // first repo of the slot's role, so in a project with four web repos
    // the Frontend node reported whatever the first one happened to be —
    // Ready while the repo actually being built sat uncloned.
    if let Some(repo) = pipeline_expand::slot_repo(ecosystem, slot_id) {
        return if repo.cloned {
            RepoReadiness::Ready
        } else {
            RepoReadiness::RepoNotCloned {
                name: repo.name.clone(),
                declared_path: repo.declared_path.clone(),
            }
        };
    }
    if pipeline_expand::is_build_slot(slot_id) {
        // Unreachable while the def and the Ecosystem come from one
        // snapshot (`pipeline_def_for` guarantees that). Reported rather
        // than waved through as Ready, because "run an agent for a repo we
        // cannot identify" is the one outcome worth refusing.
        return RepoReadiness::RepoNotInEcosystem;
    }

    let Some(role) = static_slot_role(slot_id) else {
        return RepoReadiness::Ready;
    };
    // Matches on `role_key`, never on the raw `role` cell — that cell is
    // prose in the field ("frontend — nơi landing page được implement") and
    // comparing it whole is what made a fully-configured project report
    // "no repo with role frontend".
    match ecosystem
        .iter()
        .find(|repo| repo.role_key.as_deref() == Some(role))
    {
        None => {
            // Distinguishing these two matters: "project has no frontend
            // repo" is a legitimate, permanent state (AC-E2-12), whereas an
            // unreadable Vai trò cell is a typo the user can fix in a
            // second — but only if the app says so instead of blaming the
            // project's shape.
            let unreadable: Vec<UnreadableRole> = ecosystem
                .iter()
                .filter(|repo| repo.role_key.is_none())
                .map(|repo| UnreadableRole {
                    repo_name: repo.name.clone(),
                    declared_role: repo.role.clone(),
                })
                .collect();
            if unreadable.is_empty() {
                RepoReadiness::RoleNotInEcosystem
            } else {
                RepoReadiness::RoleUnreadable {
                    entries: unreadable,
                }
            }
        }
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
// Eight independent facts about the project and the feature, none of which
// groups naturally with another — bundling them into a struct just to
// satisfy the lint would hide the signature rather than clarify it. If this
// grows again, the right move is a `ReadinessInputs` struct built once per
// feature (`get_slot_readiness` already computes all of them once and loops
// over slots), as its own refactor rather than inside a bug fix.
#[allow(clippy::too_many_arguments)]
pub fn compute_slot_readiness(
    def: &PipelineDef,
    statuses: &BTreeMap<String, NodeStatus>,
    passed_gates: &[String],
    skipped_gates: &[String],
    agents_found: &[String],
    ecosystem: &[EcosystemRepo],
    slots_without_work: &[String],
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
        RepoReadiness::RepoNotInEcosystem => {
            return SlotReadiness::RepoRoleMissing {
                role: slot_id.to_string(),
            }
        }
        RepoReadiness::RoleNotInEcosystem => {
            return SlotReadiness::RepoRoleMissing {
                role: static_slot_role(slot_id).unwrap_or(slot_id).to_string(),
            }
        }
        RepoReadiness::RoleUnreadable { entries } => {
            return SlotReadiness::RepoRoleUnreadable {
                role: static_slot_role(slot_id).unwrap_or(slot_id).to_string(),
                entries,
            }
        }
        RepoReadiness::Ready => {}
    }

    // Nothing planned for this slot in this feature — like a missing repo,
    // waiting will never resolve it, so it outranks dependency talk.
    if slots_without_work.iter().any(|id| id == slot_id) {
        return SlotReadiness::NoWorkInFeature {
            role: slot_target_label(ecosystem, slot_id),
        };
    }

    // Intra-stage dependencies first: they're the most specific answer, and
    // the most common one the user will hit (FE/Mobile waiting on backend).
    //
    // A dependency with no work in this feature is dropped rather than
    // waited on: `after_slots` exists so FE/Mobile get the backend's API
    // contract, and a backend with no task file is never going to produce
    // one. This is NOT the same as accepting `Skipped` — a manual Skip is
    // the user overriding a backend that WAS planned, and that still
    // blocks (see `skipped_backend_still_blocks_frontend`).
    let unmet: Vec<String> = agent_slot
        .after_slots
        .iter()
        .filter(|dep| !slots_without_work.iter().any(|id| id == dep.as_str()))
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

        if is_checkpoint_stage(&predecessor.id) {
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
            // Derived exactly as the parser does, so a fixture can never
            // claim a role the real pipeline wouldn't read off that cell.
            role_key: crate::agents_reader::canonical_role(role).map(str::to_string),
            stack: String::new(),
            cloned,
            resolved_path: cloned.then(|| format!("/tmp/{name}")),
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
            &[],
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

    /// The reported bug. A backend with no task file in this feature will
    /// never produce an API contract, so waiting on it is waiting forever.
    #[test]
    fn frontend_does_not_wait_on_a_backend_that_has_no_work_in_this_feature() {
        let locked = vec![gate::CONTRACT_LOCK.to_string()];
        let without_work = vec![slot::BACKEND.to_string()];
        let st = statuses(&[(slot::BACKEND, NodeStatus::Skipped)]);

        assert_eq!(
            compute_slot_readiness(
                &PipelineDef::default(),
                &st,
                &locked,
                &[],
                &all_agents(),
                &full_ecosystem(),
                &without_work,
                slot::FRONTEND,
            ),
            SlotReadiness::Ready
        );

        // And the workless slot itself says so instead of offering a Run
        // button for an agent with no task to read.
        assert_eq!(
            compute_slot_readiness(
                &PipelineDef::default(),
                &st,
                &locked,
                &[],
                &all_agents(),
                &full_ecosystem(),
                &without_work,
                slot::BACKEND,
            ),
            SlotReadiness::NoWorkInFeature {
                role: "backend".to_string()
            }
        );
    }

    /// The knock-on effect of leaving workless build slots `Idle`: stage ⑥
    /// needs every stage ⑤ slot `Done` or `Skipped`, so Testing sat blocked
    /// on a backend and a mobile that were never going to run.
    #[test]
    fn testing_opens_once_the_only_build_slot_with_work_is_done() {
        let st = statuses(&[
            (slot::BACKEND, NodeStatus::Skipped),
            (slot::FRONTEND, NodeStatus::Done),
            (slot::MOBILE, NodeStatus::Skipped),
        ]);
        assert_eq!(
            compute_slot_readiness(
                &PipelineDef::default(),
                &st,
                &[gate::CONTRACT_LOCK.to_string()],
                &[],
                &all_agents(),
                &full_ecosystem(),
                &[slot::BACKEND.to_string(), slot::MOBILE.to_string()],
                slot::QC_AUTOMATION,
            ),
            SlotReadiness::Ready
        );
    }

    /// The distinction that must survive: "the plan has no backend work" is
    /// not "the user pressed Skip on backend work that WAS planned". Only
    /// the first one drops the dependency.
    #[test]
    fn a_manual_skip_still_blocks_frontend_when_the_backend_did_have_work() {
        let st = statuses(&[(slot::BACKEND, NodeStatus::Skipped)]);
        assert!(matches!(
            compute_slot_readiness(
                &PipelineDef::default(),
                &st,
                &[gate::CONTRACT_LOCK.to_string()],
                &[],
                &all_agents(),
                &full_ecosystem(),
                &[], // backend HAS work in this feature
                slot::FRONTEND,
            ),
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

    /// A skipped gate is transparent, not a pass: readiness has to keep
    /// walking to the stage that FEEDS the gate and judge that. Treating it
    /// as a pass would open stage ⑤ on a feature whose Planning hasn't run.
    ///
    /// Until Contract Lock learned to skip itself for backend-less features
    /// (AC-E4-11a) this branch was only reachable via the rare single-repo
    /// case, and nothing here exercised it at all.
    #[test]
    fn a_skipped_gate_is_transparent_but_still_defers_to_the_stage_behind_it() {
        let skipped = vec![gate::CONTRACT_LOCK.to_string()];
        let passed = vec![gate::TRIGGER.to_string()];

        let planning_unfinished = statuses(&[
            (slot::BA, NodeStatus::Done),
            (slot::TECHLEAD_DESIGN, NodeStatus::Done),
            (slot::DESIGN_ANALYST, NodeStatus::Skipped),
            (slot::QC_DESIGN, NodeStatus::Done),
            (slot::TECHLEAD_TASKS, NodeStatus::Idle),
        ]);
        let blocked = compute_slot_readiness(
            &PipelineDef::default(),
            &planning_unfinished,
            &passed,
            &skipped,
            &all_agents(),
            &full_ecosystem(),
            &[],
            slot::BACKEND,
        );
        assert!(
            !matches!(blocked, SlotReadiness::Ready),
            "a skipped gate must not paper over unfinished Planning, got {blocked:?}"
        );

        let mut planning_done = planning_unfinished.clone();
        planning_done.insert(slot::TECHLEAD_TASKS.to_string(), NodeStatus::Done);
        assert_eq!(
            compute_slot_readiness(
                &PipelineDef::default(),
                &planning_done,
                &passed,
                &skipped,
                &all_agents(),
                &full_ecosystem(),
                &[],
                slot::BACKEND,
            ),
            SlotReadiness::Ready
        );

        // Same state, gate NOT skipped — must block. This is what proves
        // the assertion above is about the skip and nothing else.
        assert!(
            matches!(
                compute_slot_readiness(
                    &PipelineDef::default(),
                    &planning_done,
                    &passed,
                    &[],
                    &all_agents(),
                    &full_ecosystem(),
                    &[],
                    slot::BACKEND,
                ),
                SlotReadiness::GateNotPassed { .. }
            ),
            "without the skip the Contract Lock gate must still block"
        );
    }

    // --- repo readiness (AC-E2-11/12), moved here from `commands::agentrun`
    // so the Run button and the pre-spawn guard can never disagree ---

    #[test]
    fn slots_without_a_repo_role_are_always_ready() {
        for non_repo_slot in [
            slot::BA,
            slot::TECHLEAD_DESIGN,
            slot::TECHLEAD_TASKS,
            slot::QC_AUTOMATION,
        ] {
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

    /// "Project không có repo vai trò frontend" is a very wrong thing to
    /// tell someone whose `repos/frontend` is right there — the real cause
    /// is a Vai trò cell the app couldn't read. Two different problems, two
    /// different messages.
    #[test]
    fn an_unreadable_role_cell_is_reported_as_such_not_as_a_missing_repo() {
        let eco = vec![
            repo("frontend", "frontend — nơi landing page được implement", true),
            repo("backend", "backend — template residual", true),
        ];
        // Both now resolve, which is the whole point of the fix.
        assert!(matches!(
            resolve_repo_readiness(&eco, slot::FRONTEND),
            RepoReadiness::Ready
        ));

        let broken = vec![repo("frontend", "trang chủ", true)];
        match resolve_repo_readiness(&broken, slot::FRONTEND) {
            RepoReadiness::RoleUnreadable { entries } => {
                assert_eq!(entries.len(), 1);
                assert_eq!(entries[0].repo_name, "frontend");
                assert_eq!(entries[0].declared_role, "trang chủ");
            }
            other => panic!("expected RoleUnreadable, got {other:?}"),
        }
    }

    /// The distinction has to survive: a project that really has no mobile
    /// repo must keep saying so (AC-E2-12), not get reclassified as a typo.
    #[test]
    fn a_genuinely_absent_role_still_reports_role_not_in_ecosystem() {
        let eco = vec![repo("shop-api", "backend", true)];
        assert!(matches!(
            resolve_repo_readiness(&eco, slot::MOBILE),
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
                &[],
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
                &[],
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
                &[],
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
                &[],
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
