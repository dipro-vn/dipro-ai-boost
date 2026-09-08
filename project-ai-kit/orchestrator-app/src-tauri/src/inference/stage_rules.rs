use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use crate::domain::node_status::NodeState;
use crate::domain::pipeline_def::slot;
use crate::domain::project::EcosystemRepo;
use crate::inference::spec_sections;

/// `design-analysis.md` existing but shorter than this (after trimming
/// whitespace) is treated as incomplete rather than done (AF-3). The SPEC
/// does not give a concrete number for "quá ngắn" — this is an
/// implementation choice, not a value extracted from any document. Revisit
/// if it produces false positives/negatives in practice.
const MIN_DESIGN_ANALYSIS_CHARS: usize = 50;

/// Subdirectories of a feature folder that are NOT a repo. `repo_subdirs`
/// otherwise counts every directory as one, which would make
/// `design-resources/` (the design-analyst's exported icons/images,
/// AC-E2-37a) look like a repo with no `DESIGN.md` and no `tasks/` — and,
/// worse, push a genuinely single-repo feature over the "touches ≥2 repos"
/// line that `inference::contract_lock_rules` uses for AC-E4-11.
///
/// Every entry here is a folder the kit itself writes under a feature:
/// `test-cases/` and `bug-reports/` come from `qc-agent`
/// (`.claude/agents/qc-agent.md` § Output), `design-resources/` and
/// `screenshot-design/` from `design-analyst-agent` (its own file names
/// exactly three write locations — keep this list matching that one).
/// Missing one is not cosmetic — an unlisted folder counts as an undeclared
/// repo, which is enough on its own to switch off both the Contract Lock
/// scope rule and the stage ⑤ "has work" rule for the whole feature, since
/// neither will draw a conclusion from an Ecosystem it cannot fully
/// resolve.
const NON_REPO_SUBDIRS: &[&str] = &[
    "test-cases",
    "design-resources",
    "screenshot-design",
    "bug-reports",
];

/// `pub(crate)` — also reused by `inference::contract_lock_rules` (AC-E4-11:
/// a feature touching only one repo doesn't need Contract Lock).
pub(crate) fn repo_subdirs(feature_dir: &Path) -> Vec<std::path::PathBuf> {
    std::fs::read_dir(feature_dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| path.is_dir())
        .filter(|path| {
            path.file_name()
                .and_then(|n| n.to_str())
                .map(|name| !name.starts_with('.') && !NON_REPO_SUBDIRS.contains(&name))
                .unwrap_or(false)
        })
        .collect()
}

/// Collects, rather than just checking existence — used both for the
/// `Done`/`Idle` boolean checks below AND `artifact_paths_for_slot`
/// (§ node detail panel), so the two can never disagree about what counts.
/// `pub(crate)` — also reused by `inference::api_definition` to enumerate
/// every `DESIGN.md` across every repo for a feature.
pub(crate) fn files_in_repos(feature_dir: &Path, relative_file: &str) -> Vec<PathBuf> {
    repo_subdirs(feature_dir)
        .into_iter()
        .map(|repo| repo.join(relative_file))
        .filter(|path| path.is_file())
        .collect()
}

fn any_repo_has_file(feature_dir: &Path, relative_file: &str) -> bool {
    !files_in_repos(feature_dir, relative_file).is_empty()
}

/// `pub(crate)` — also reused by `commands::agentrun::lock_contract`
/// (AC-E4-18) to find the task files to hand `backend-agent`, the same way
/// it expects to be invoked normally (`task-x-y.md`, not a bare `DESIGN.md`
/// pointer — verified against `.claude/agents/backend-agent.md`'s own
/// `## Quy trình làm việc`).
pub(crate) fn task_files_in_repos(feature_dir: &Path) -> Vec<PathBuf> {
    repo_subdirs(feature_dir)
        .into_iter()
        .flat_map(|repo| task_files_in_dir(&repo))
        .collect()
}

fn any_repo_has_task_files(feature_dir: &Path) -> bool {
    !task_files_in_repos(feature_dir).is_empty()
}

/// The roles of the repos this feature ACTUALLY touches, read off its own
/// subfolder names (`<feature>/<repo-name>/DESIGN.md` — the layout
/// `.claude/rules/project-structure.md` mandates), matched against the
/// Ecosystem table by repo name.
///
/// Returns the unmatched folder names too, and callers must treat those as
/// "unknown", never as "not a backend": if `AGENTS.md` has no Ecosystem
/// table, or a folder is named after a repo that was never declared, every
/// role lookup silently comes back false. Deciding "no backend here" from
/// that would switch off both Contract Lock and the BE->FE ordering across
/// the whole project — everything would look like it worked while
/// enforcing nothing.
pub(crate) fn feature_scope_roles(
    feature_dir: &Path,
    ecosystem: &[EcosystemRepo],
) -> (Vec<String>, Vec<String>) {
    let mut roles = Vec::new();
    let mut unmatched = Vec::new();
    for dir in repo_subdirs(feature_dir) {
        let Some(name) = dir.file_name().and_then(|n| n.to_str()) else {
            continue;
        };
        match ecosystem
            .iter()
            .find(|repo| repo.name.eq_ignore_ascii_case(name))
        {
            // A repo whose role cell couldn't be read is "unknown", not
            // "some other role" — same reasoning as an unmatched folder.
            Some(repo) => match repo.role_key.as_deref() {
                Some(role) => roles.push(role.to_string()),
                None => unmatched.push(name.to_string()),
            },
            None => unmatched.push(name.to_string()),
        }
    }
    (roles, unmatched)
}

/// Which stage ⑤ slots have NOTHING to do in this feature.
///
/// Two independent reasons a build slot can have no work, checked in this
/// order:
///
/// 1. Ecosystem-level (permanent, project-wide, always resolvable): this
///    project's Ecosystem table declares no repo at all for that role
///    (`agentrun::readiness::RepoReadiness::RoleNotInEcosystem`) — e.g. a
///    web-only project has no `mobile` repo, ever, in any feature. This
///    doesn't need a single task file to exist and isn't affected by any
///    OTHER subfolder's name — a stage ⑥ (`qc-automation`) that waits for
///    stage ⑤ to finish must not stay blocked on a slot that can never run
///    here.
///    Deliberately excludes `RoleUnreadable`: that means some OTHER repo's
///    Vai trò cell couldn't be parsed, not that this role is absent —
///    concluding "no work" there would hide a real config typo instead of
///    surfacing it. Also requires `ecosystem` to be non-empty: an entirely
///    empty Ecosystem almost always means `/init-kit` hasn't populated
///    `AGENTS.md` yet, not "this project confidently has zero repos of any
///    role" — treating that the same as a deliberately-configured, merely
///    sparse Ecosystem (like backend+frontend-only, no mobile) would mark
///    every build slot `Skipped` the moment a brand-new project opens.
/// 2. Feature-level (task-file-based, same as before): the kit's own
///    layout answers this — `techlead-tasks-agent` writes
///    `<feature>/<repo>/tasks/task-*.md` for exactly the repos that have
///    work (its Bước 4 assigns Phase 1–2 to `backend`, Phase 3 to
///    `frontend`/`mobile`). A repo with no task file has nothing for its
///    agent to run. Stays behind both existing guards — bails out to
///    "assume every slot has work" unless EVERY subfolder resolved to a
///    declared repo (`feature_scope_roles`) and at least one task file
///    exists anywhere: concluding "no backend" from an Ecosystem table the
///    app couldn't read, or before `techlead-tasks` has even run, would
///    drop the BE->FE ordering for a feature nobody has scoped yet.
pub(crate) fn slots_without_work_in_feature(
    feature_dir: &Path,
    ecosystem: &[EcosystemRepo],
) -> Vec<String> {
    let build_slots = [
        (slot::BACKEND, "backend"),
        (slot::FRONTEND, "frontend"),
        (slot::MOBILE, "mobile"),
    ];

    let mut without_work: Vec<String> = if ecosystem.is_empty() {
        Vec::new()
    } else {
        build_slots
            .iter()
            .filter(|(slot_id, _)| {
                matches!(
                    crate::agentrun::readiness::resolve_repo_readiness(ecosystem, slot_id),
                    crate::agentrun::readiness::RepoReadiness::RoleNotInEcosystem
                )
            })
            .map(|(slot_id, _)| slot_id.to_string())
            .collect()
    };

    if any_repo_has_task_files(feature_dir) {
        let (_, unmatched) = feature_scope_roles(feature_dir, ecosystem);
        if unmatched.is_empty() {
            for (slot_id, role) in build_slots {
                if !without_work.iter().any(|s| s == slot_id)
                    && !role_has_task_files(feature_dir, ecosystem, role)
                {
                    without_work.push(slot_id.to_string());
                }
            }
        }
    }

    without_work
}

/// True when some repo of `role` has at least one `task-*.md` for this
/// feature. Deliberately not `DESIGN.md`: Tech Lead Design writes a
/// `DESIGN.md` for a repo it merely *considered* (the landing-page project
/// has one that says "N/A — không có endpoint mới"), whereas a task file
/// only exists when there is actual work.
fn role_has_task_files(feature_dir: &Path, ecosystem: &[EcosystemRepo], role: &str) -> bool {
    repo_subdirs(feature_dir).iter().any(|dir| {
        let Some(name) = dir.file_name().and_then(|n| n.to_str()) else {
            return false;
        };
        let is_role = ecosystem.iter().any(|repo| {
            repo.name.eq_ignore_ascii_case(name) && repo.role_key.as_deref() == Some(role)
        });
        is_role && !task_files_in_dir(dir).is_empty()
    })
}

fn task_files_in_dir(repo_dir: &Path) -> Vec<PathBuf> {
    std::fs::read_dir(repo_dir.join("tasks"))
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| {
            let name = path.file_name().unwrap_or_default().to_string_lossy();
            name.starts_with("task-") && name.ends_with(".md")
        })
        .collect()
}

fn test_cases_files(feature_dir: &Path) -> Vec<PathBuf> {
    let test_cases_dir = feature_dir.join("test-cases");
    std::fs::read_dir(&test_cases_dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| path.is_dir())
        .map(|module_dir| module_dir.join("test-cases.md"))
        .filter(|path| path.is_file())
        .collect()
}

fn any_test_cases_file(feature_dir: &Path) -> bool {
    !test_cases_files(feature_dir).is_empty()
}

/// AC-E3-01 / AC-E3-04a — the icons and images `design-analyst-agent`
/// exports next to `design-analysis.md`. Display-only: listed as artifacts
/// of the Design-Analyst node, never consulted by `infer_design_analyst`,
/// so a feature with no assets is still `done`.
///
/// `pub(crate)` — `commands::agentrun` also asks whether the folder has
/// anything in it before naming it to `frontend-agent`/`mobile-agent`.
pub(crate) fn design_resources_files(feature_dir: &Path) -> Vec<PathBuf> {
    files_directly_in(feature_dir, "design-resources")
}

/// The full-frame reference screenshots `design-analyst-agent` writes for
/// `frontend-agent`/`mobile-agent` to compare their UI against. Sibling of
/// `design_resources_files` and deliberately separate: these are NOT assets
/// to embed in code, so nothing may copy them into a repo's asset folder.
pub(crate) fn screenshot_design_files(feature_dir: &Path) -> Vec<PathBuf> {
    files_directly_in(feature_dir, "screenshot-design")
}

/// Flat (non-recursive) and sorted: the agent writes straight into these
/// folders, and a stable order keeps the node detail panel from reshuffling
/// between polls.
fn files_directly_in(feature_dir: &Path, subdir: &str) -> Vec<PathBuf> {
    let mut files: Vec<PathBuf> = std::fs::read_dir(feature_dir.join(subdir))
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| path.is_file())
        .collect();
    files.sort();
    files
}

/// `runs_dir` holds app-defined report conventions the kit itself does not
/// specify a path for (AC-E3-05) — `<runs_dir>/<run-id>/<filename>`, written
/// by `agentrun::run_log::finalize_run`. `runs_dir` is a single flat
/// namespace shared by every feature in the project, so only `run-id`
/// entries prefixed for THIS feature are considered — see
/// `store::orchestrator_dir::runs_dir_prefix`. Without this filter, a QA
/// report from one feature would make every OTHER feature's QA node read
/// as `Done` too.
fn run_files(runs_dir: &Path, feature: &str, filename: &str) -> Vec<PathBuf> {
    let prefix = crate::store::orchestrator_dir::runs_dir_prefix(feature);
    std::fs::read_dir(runs_dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| path.is_dir())
        .filter(|path| {
            path.file_name()
                .and_then(|n| n.to_str())
                .map(|name| name.starts_with(&prefix))
                .unwrap_or(false)
        })
        .map(|run_dir| run_dir.join(filename))
        .filter(|path| path.is_file())
        .collect()
}

fn any_run_has_file(runs_dir: &Path, feature: &str, filename: &str) -> bool {
    !run_files(runs_dir, feature, filename).is_empty()
}

/// The feature slug is always `feature_dir`'s own last path component — the
/// same convention every caller already builds `feature_dir` with
/// (`docs_root.join("features").join(feature)`). Deriving it here instead
/// of threading a separate `feature: &str` through `infer_feature_state`
/// and its ~15 test call sites keeps this an internal detail of the
/// `runs_dir` scoping, not a public signature change.
fn feature_slug(feature_dir: &Path) -> &str {
    feature_dir.file_name().and_then(|n| n.to_str()).unwrap_or("")
}

fn infer_ba(feature_dir: &Path) -> NodeState {
    let spec_path = feature_dir.join("SPEC.md");
    let Ok(content) = std::fs::read_to_string(&spec_path) else {
        return NodeState::idle();
    };
    let missing = spec_sections::missing_sections(&content);
    if missing.is_empty() {
        NodeState::done()
    } else {
        NodeState::done_incomplete(format!("Thiếu section: {}", missing.join(", ")))
    }
}

fn infer_design_analyst(feature_dir: &Path) -> NodeState {
    let path = feature_dir.join("design-analysis.md");
    let Ok(content) = std::fs::read_to_string(&path) else {
        return NodeState::idle();
    };
    // MVP1 does not read MCP config (AC-E1-25..27 deferred to MVP3), so the
    // `Blocked` branch this stage has in the full SPEC ("không có + không
    // MCP Figma → Blocked") cannot be computed here — only Idle/Done/
    // DoneIncomplete are reachable from this function.
    if content.trim().chars().count() < MIN_DESIGN_ANALYSIS_CHARS {
        NodeState::done_incomplete("design-analysis.md tồn tại nhưng quá ngắn")
    } else {
        NodeState::done()
    }
}

/// Computes every node's status for one feature, purely from what's on
/// disk right now. No prior state is consulted — the caller (fswatch) is
/// responsible for deciding whether the result differs from what was
/// cached before and needs writing/emitting.
///
/// `backend`/`frontend`/`mobile` (stage ⑤) leave no artifact behind, so
/// this function must not "suy từ source code" (SPEC's own words) to guess
/// whether one has run — that is exactly the guessing the kit's core policy
/// forbids, and `pipeline_state::apply_agent_run_metadata` layers the real
/// run log on top afterwards.
///
/// It CAN say a slot has nothing to do, though, and that is not a guess:
/// no `task-*.md` for that repo role means its agent has no input. Left as
/// `Idle`, such a slot blocked stage ⑥ forever (`is_complete` needs every
/// stage ⑤ slot `Done` or `Skipped`) and, through `after_slots`, blocked
/// Frontend behind a Backend that was never going to run.
pub fn infer_feature_state(
    feature_dir: &Path,
    runs_dir: &Path,
    ecosystem: &[EcosystemRepo],
) -> BTreeMap<String, NodeState> {
    let mut nodes = BTreeMap::new();

    nodes.insert(slot::BA.to_string(), infer_ba(feature_dir));

    nodes.insert(
        slot::TECHLEAD_DESIGN.to_string(),
        if any_repo_has_file(feature_dir, "DESIGN.md") {
            NodeState::done()
        } else {
            NodeState::idle()
        },
    );

    nodes.insert(
        slot::DESIGN_ANALYST.to_string(),
        infer_design_analyst(feature_dir),
    );

    nodes.insert(
        slot::QC_DESIGN.to_string(),
        if any_test_cases_file(feature_dir) {
            NodeState::done()
        } else {
            NodeState::idle()
        },
    );

    nodes.insert(
        slot::TECHLEAD_TASKS.to_string(),
        if any_repo_has_task_files(feature_dir) {
            NodeState::done()
        } else {
            NodeState::idle()
        },
    );

    let without_work = slots_without_work_in_feature(feature_dir, ecosystem);
    for build_slot in [slot::BACKEND, slot::FRONTEND, slot::MOBILE] {
        let node = if without_work.iter().any(|id| id == build_slot) {
            let role = crate::agentrun::readiness::slot_repo_role(build_slot).unwrap_or(build_slot);
            let detail = if !ecosystem.is_empty()
                && matches!(
                    crate::agentrun::readiness::resolve_repo_readiness(ecosystem, build_slot),
                    crate::agentrun::readiness::RepoReadiness::RoleNotInEcosystem
                )
            {
                format!("Dự án không có repo vai trò {role} trong Ecosystem — agent này không áp dụng.")
            } else {
                format!("Feature này không có task nào cho {build_slot} — agent không áp dụng.")
            };
            NodeState::skipped(detail)
        } else {
            NodeState::idle()
        };
        nodes.insert(build_slot.to_string(), node);
    }

    let feature = feature_slug(feature_dir);

    nodes.insert(
        slot::QC_AUTOMATION.to_string(),
        if any_run_has_file(runs_dir, feature, "execution-report.md") {
            NodeState::done()
        } else {
            NodeState::idle()
        },
    );

    nodes
}

/// The artifact path(s) backing a given slot's current status — used by the
/// node detail panel (AC-E3-13). Uses the exact same collectors as
/// `infer_feature_state` so "is this node done" and "what artifact made it
/// so" can never disagree. Unknown `slot_id` (shouldn't happen — the
/// frontend only ever passes ids from `PipelineDef`) returns an empty list
/// rather than panicking.
pub fn artifact_paths_for_slot(feature_dir: &Path, runs_dir: &Path, slot_id: &str) -> Vec<PathBuf> {
    let feature = feature_slug(feature_dir);
    match slot_id {
        s if s == slot::BA => {
            let path = feature_dir.join("SPEC.md");
            if path.is_file() {
                vec![path]
            } else {
                vec![]
            }
        }
        s if s == slot::TECHLEAD_DESIGN => files_in_repos(feature_dir, "DESIGN.md"),
        s if s == slot::DESIGN_ANALYST => {
            // `design-analysis.md` FIRST, then the exported assets:
            // `AgentStepPanel` auto-opens `artifacts[0]` in the preview
            // modal, and `read_artifact` reads as UTF-8 — landing on a
            // `.png` there would surface an encoding error instead of the
            // analysis the user came to read.
            let mut paths = Vec::new();
            let analysis = feature_dir.join("design-analysis.md");
            if analysis.is_file() {
                paths.push(analysis);
            }
            paths.extend(design_resources_files(feature_dir));
            paths.extend(screenshot_design_files(feature_dir));
            paths
        }
        s if s == slot::QC_DESIGN => test_cases_files(feature_dir),
        s if s == slot::TECHLEAD_TASKS => task_files_in_repos(feature_dir),
        s if s == slot::BACKEND || s == slot::FRONTEND || s == slot::MOBILE => vec![],
        s if s == slot::QC_AUTOMATION => run_files(runs_dir, feature, "execution-report.md"),
        _ => vec![],
    }
}

/// The single deterministic path for slots whose artifact is exactly one
/// fixed file — returned regardless of whether it currently exists, unlike
/// `artifact_paths_for_slot` (which only reports paths that are actually
/// there). AC-E3-06 needs this to name a file that was just deleted, after
/// the fact. `None` for slots whose artifact set is inherently variable
/// (per-repo, per-run) — naming "which one" of several would be guessing.
pub fn canonical_single_artifact_path(feature_dir: &Path, slot_id: &str) -> Option<PathBuf> {
    match slot_id {
        s if s == slot::BA => Some(feature_dir.join("SPEC.md")),
        s if s == slot::DESIGN_ANALYST => Some(feature_dir.join("design-analysis.md")),
        _ => None,
    }
}

/// Every artifact path that currently exists for a feature, across all
/// slots — the snapshot subsystem (T1.6) needs this to know what to watch
/// for non-git-tracked artifacts, without duplicating the per-slot file
/// rules a second time.
pub fn all_artifact_paths(feature_dir: &Path, runs_dir: &Path) -> Vec<PathBuf> {
    let mut paths: Vec<PathBuf> = crate::domain::pipeline_def::PipelineDef::default()
        .stages
        .into_iter()
        .flat_map(|stage| stage.agents)
        .flat_map(|agent| artifact_paths_for_slot(feature_dir, runs_dir, &agent.id))
        .collect();
    paths.sort();
    paths.dedup();
    paths
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::node_status::NodeStatus;

    fn write(path: &Path, content: &str) {
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, content).unwrap();
    }

    const COMPLETE_SPEC: &str = "## Mô tả nghiệp vụ\nx\n## Actors & Preconditions\nx\n## Happy Path\nx\n## Alternative Flows & Edge Cases\nx\n## Acceptance Criteria\nx\n## Out of Scope\nx\n## Screens\nx\n";

    /// Guards against slot-id drift between this module and
    /// `pipeline_def::PipelineDef::default()` — if someone adds/renames a
    /// slot in one place and forgets the other, this catches it instead of
    /// silently producing a node the frontend never sees (or a `PipelineDef`
    /// slot with no computed state).
    #[test]
    fn produced_slot_ids_exactly_match_pipeline_def_slots() {
        use crate::domain::pipeline_def::PipelineDef;

        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let mut computed: Vec<String> = infer_feature_state(&feature_dir, &runs_dir, &[])
            .into_keys()
            .collect();
        computed.sort();

        let mut declared: Vec<String> = PipelineDef::default()
            .stages
            .into_iter()
            .flat_map(|stage| stage.agents)
            .map(|agent| agent.id)
            .collect();
        declared.sort();

        assert_eq!(computed, declared);
    }

    fn eco(entries: &[(&str, &str)]) -> Vec<EcosystemRepo> {
        entries
            .iter()
            .map(|(name, role)| EcosystemRepo {
                name: name.to_string(),
                declared_path: format!("repos/{name}"),
                role: role.to_string(),
                role_key: crate::agents_reader::canonical_role(role).map(str::to_string),
                stack: "x".to_string(),
                cloned: true,
                resolved_path: Some(format!("/tmp/{name}")),
            })
            .collect()
    }

    fn touch(path: &Path) {
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, "x").unwrap();
    }

    /// The reported case: a landing page whose Tech Lead produced tasks for
    /// `frontend` only. Backend and Mobile have nothing to run, so Frontend
    /// must not be told to wait for them.
    #[test]
    fn a_feature_planned_for_frontend_only_leaves_backend_and_mobile_without_work() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("landing-page");
        touch(&feature_dir.join("frontend/DESIGN.md"));
        touch(&feature_dir.join("frontend/tasks/task-3-1.md"));

        let ecosystem = eco(&[("backend", "backend"), ("frontend", "frontend")]);
        let without = slots_without_work_in_feature(&feature_dir, &ecosystem);
        assert!(without.contains(&slot::BACKEND.to_string()));
        assert!(without.contains(&slot::MOBILE.to_string()));
        assert!(!without.contains(&slot::FRONTEND.to_string()));
    }

    /// A real cross-repo feature must keep every dependency it has.
    #[test]
    fn a_feature_planned_for_both_sides_leaves_neither_without_work() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("user-login");
        touch(&feature_dir.join("api/tasks/task-2-1.md"));
        touch(&feature_dir.join("web/tasks/task-3-1.md"));

        let ecosystem = eco(&[("api", "backend"), ("web", "frontend")]);
        let without = slots_without_work_in_feature(&feature_dir, &ecosystem);
        assert!(!without.contains(&slot::BACKEND.to_string()));
        assert!(!without.contains(&slot::FRONTEND.to_string()));
        // No mobile repo touched -> nothing for that agent either.
        assert!(without.contains(&slot::MOBILE.to_string()));
    }

    /// Tech Lead Design writes a `DESIGN.md` even for a repo it merely
    /// considered — the landing-page project has one saying "N/A, không có
    /// endpoint mới". A task file is what means real work.
    #[test]
    fn a_repo_with_a_design_but_no_task_counts_as_having_no_work() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("f");
        touch(&feature_dir.join("api/DESIGN.md"));
        touch(&feature_dir.join("web/tasks/task-3-1.md"));

        let ecosystem = eco(&[("api", "backend"), ("web", "frontend")]);
        assert!(slots_without_work_in_feature(&feature_dir, &ecosystem)
            .contains(&slot::BACKEND.to_string()));
    }

    /// `bug-reports/` is written by `qc-agent`, and leaving it off
    /// `NON_REPO_SUBDIRS` was enough to disable this whole rule on a real
    /// project: the folder read as an undeclared repo, `unmatched` was
    /// non-empty, and the safety chock below then (correctly) refused to
    /// conclude anything. Same omission also kept Contract Lock's
    /// single-repo rule from firing.
    ///
    /// `screenshot-design/` was the same omission a second time — it is the
    /// third write location `design-analyst-agent.md` declares, and it went
    /// unlisted here until stage ⑤ started reading it.
    #[test]
    fn kit_written_artifact_folders_are_not_mistaken_for_repos() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("landing-page");
        touch(&feature_dir.join("frontend/tasks/task-3-1.md"));
        touch(&feature_dir.join("test-cases/landing-page/test-cases.md"));
        touch(&feature_dir.join("design-resources/hero.png"));
        touch(&feature_dir.join("screenshot-design/WB_AUTH_001.png"));
        std::fs::create_dir_all(feature_dir.join("bug-reports")).unwrap();

        assert_eq!(repo_subdirs(&feature_dir).len(), 1);

        let ecosystem = eco(&[("backend", "backend"), ("frontend", "frontend")]);
        assert!(slots_without_work_in_feature(&feature_dir, &ecosystem)
            .contains(&slot::BACKEND.to_string()));
    }

    /// The safety chock, same one Contract Lock uses: an unmatched feature
    /// subfolder must never make the task-file-based pass read a role that
    /// genuinely HAS work (and every role IS declared in the Ecosystem) as
    /// "no work", or the BE->FE ordering silently disappears. Uses an
    /// Ecosystem that declares all 3 roles so the (separate, unaffected by
    /// this guard) Ecosystem-absence pass never fires here — isolates the
    /// guard this test is actually about.
    #[test]
    fn an_unmatched_folder_never_declares_a_declared_roles_slot_workless() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("f");
        touch(&feature_dir.join("mystery/tasks/task-1-1.md"));

        let ecosystem = eco(&[("backend", "backend"), ("frontend", "frontend"), ("mobile", "mobile")]);
        assert!(slots_without_work_in_feature(&feature_dir, &ecosystem).is_empty());
    }

    /// A completely empty Ecosystem almost always means `/init-kit` hasn't
    /// populated `AGENTS.md` yet, not "this project confidently has zero
    /// repos of any role" — must never be read as "every build slot has no
    /// work" the moment a brand-new project opens.
    #[test]
    fn a_completely_empty_ecosystem_never_declares_any_slot_workless() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("f");
        touch(&feature_dir.join("mystery/tasks/task-1-1.md"));

        assert!(slots_without_work_in_feature(&feature_dir, &[]).is_empty());
    }

    /// Nothing planned yet is not the same as nothing to do — otherwise a
    /// brand-new feature shows all of stage ⑤ as "không áp dụng". Ecosystem
    /// here declares all 3 roles so this stays isolated from the (separate)
    /// Ecosystem-absence pass, which doesn't wait for task files at all.
    #[test]
    fn a_feature_with_no_tasks_at_all_is_not_treated_as_workless() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("f");
        touch(&feature_dir.join("SPEC.md"));

        let ecosystem = eco(&[("api", "backend"), ("web", "frontend"), ("app", "mobile")]);
        assert!(slots_without_work_in_feature(&feature_dir, &ecosystem).is_empty());
    }

    /// The actual reported bug: a project whose Ecosystem simply never
    /// declared a `mobile` repo must have `mobile` come back without-work
    /// immediately — even before `techlead-tasks` has written a single task
    /// file anywhere (guard 1 alone would otherwise say "wait, nothing
    /// planned yet" and leave it `Idle` forever, blocking stage ⑥ on a slot
    /// that can never run in this project).
    #[test]
    fn a_role_absent_from_a_configured_ecosystem_is_without_work_before_any_task_file_exists() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("f");
        std::fs::create_dir_all(&feature_dir).unwrap();

        let ecosystem = eco(&[("backend", "backend"), ("frontend", "frontend")]);
        let without = slots_without_work_in_feature(&feature_dir, &ecosystem);
        assert!(without.contains(&slot::MOBILE.to_string()));
        assert!(!without.contains(&slot::BACKEND.to_string()));
        assert!(!without.contains(&slot::FRONTEND.to_string()));
    }

    /// Same absent-role case, but now with real task files present AND an
    /// unrelated unmatched folder that trips guard 2 for the task-file
    /// pass — the Ecosystem-absence pass must keep flagging `mobile`
    /// regardless, since the two passes are independent. Backend must NOT
    /// be flagged: it genuinely has a task file, and guard 2 correctly
    /// refuses to conclude anything about it from an unresolvable folder.
    #[test]
    fn a_role_absent_from_ecosystem_is_without_work_even_when_an_unrelated_folder_is_unmatched() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("f");
        touch(&feature_dir.join("backend/tasks/task-1-1.md"));
        touch(&feature_dir.join("mystery/tasks/task-9-9.md"));

        let ecosystem = eco(&[("backend", "backend"), ("frontend", "frontend")]);
        let without = slots_without_work_in_feature(&feature_dir, &ecosystem);
        assert!(without.contains(&slot::MOBILE.to_string()));
        assert!(!without.contains(&slot::BACKEND.to_string()));
    }

    /// A role missing from `role_key` resolution because some OTHER repo's
    /// Vai trò cell is unreadable (`RepoReadiness::RoleUnreadable`) must NOT
    /// be treated the same as a role that's confidently absent
    /// (`RoleNotInEcosystem`) — that would hide a real `AGENTS.md` typo
    /// behind a silent "không áp dụng" instead of surfacing it.
    #[test]
    fn a_role_missing_only_because_a_sibling_roles_cell_is_unreadable_is_not_assumed_workless() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("f");
        std::fs::create_dir_all(&feature_dir).unwrap();

        let ecosystem = vec![
            EcosystemRepo {
                name: "backend".to_string(),
                declared_path: "repos/backend".to_string(),
                role: "backend".to_string(),
                role_key: Some("backend".to_string()),
                stack: "x".to_string(),
                cloned: true,
                resolved_path: Some("/tmp/backend".to_string()),
            },
            EcosystemRepo {
                name: "mystery-repo".to_string(),
                declared_path: "repos/mystery-repo".to_string(),
                role: "???".to_string(),
                role_key: None,
                stack: "x".to_string(),
                cloned: true,
                resolved_path: Some("/tmp/mystery-repo".to_string()),
            },
        ];
        assert!(!slots_without_work_in_feature(&feature_dir, &ecosystem)
            .contains(&slot::MOBILE.to_string()));
    }

    /// Left `Idle`, a workless build slot blocked stage ⑥ forever:
    /// `is_complete` needs every stage ⑤ slot `Done` or `Skipped`.
    #[test]
    fn build_slots_without_work_are_inferred_as_skipped() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("landing-page");
        let runs_dir = tmp.path().join("runs");
        touch(&feature_dir.join("frontend/tasks/task-3-1.md"));

        let ecosystem = eco(&[("backend", "backend"), ("frontend", "frontend")]);
        let nodes = infer_feature_state(&feature_dir, &runs_dir, &ecosystem);
        assert_eq!(nodes[slot::BACKEND].status, NodeStatus::Skipped);
        assert_eq!(nodes[slot::MOBILE].status, NodeStatus::Skipped);
        // The one that DOES have work stays runnable.
        assert_eq!(nodes[slot::FRONTEND].status, NodeStatus::Idle);
    }

    #[test]
    fn empty_feature_dir_is_all_idle() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("features/some-feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let nodes = infer_feature_state(&feature_dir, &runs_dir, &[]);
        assert_eq!(nodes.len(), 9); // 9 agent slots total across the 8 stages
        assert!(nodes.values().all(|n| n.status == NodeStatus::Idle));
    }

    #[test]
    fn ba_done_when_spec_has_all_7_sections() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(&feature_dir.join("SPEC.md"), COMPLETE_SPEC);
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let nodes = infer_feature_state(&feature_dir, &runs_dir, &[]);
        assert_eq!(nodes[slot::BA].status, NodeStatus::Done);
    }

    #[test]
    fn ba_done_incomplete_when_spec_missing_sections() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("SPEC.md"),
            "## Mô tả nghiệp vụ\nonly this\n",
        );
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let nodes = infer_feature_state(&feature_dir, &runs_dir, &[]);
        let ba = &nodes[slot::BA];
        assert_eq!(ba.status, NodeStatus::DoneIncomplete);
        assert!(ba
            .detail
            .as_ref()
            .unwrap()
            .contains("Actors & Preconditions"));
    }

    #[test]
    fn techlead_design_done_when_any_repo_subdir_has_design_md() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(&feature_dir.join("backend-repo/DESIGN.md"), "content");
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let nodes = infer_feature_state(&feature_dir, &runs_dir, &[]);
        assert_eq!(nodes[slot::TECHLEAD_DESIGN].status, NodeStatus::Done);
    }

    #[test]
    fn test_cases_subdir_is_never_mistaken_for_a_repo() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        // A DESIGN.md accidentally dropped under test-cases/ must not count.
        write(&feature_dir.join("test-cases/module/DESIGN.md"), "x");
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let nodes = infer_feature_state(&feature_dir, &runs_dir, &[]);
        assert_eq!(nodes[slot::TECHLEAD_DESIGN].status, NodeStatus::Idle);
    }

    /// B2 — `design-resources/` is a sibling of the repo subdirs, not one
    /// of them. Regression guard for the two ways it used to leak:
    /// `DESIGN.md` detection, and the repo count `contract_lock_rules`
    /// derives from `repo_subdirs` (AC-E4-11).
    #[test]
    fn design_resources_subdir_is_never_mistaken_for_a_repo() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("design-resources/icon-home.svg"),
            "<svg/>",
        );
        write(&feature_dir.join("design-resources/DESIGN.md"), "x");
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        assert!(repo_subdirs(&feature_dir).is_empty());
        let nodes = infer_feature_state(&feature_dir, &runs_dir, &[]);
        assert_eq!(nodes[slot::TECHLEAD_DESIGN].status, NodeStatus::Idle);
    }

    /// AC-E3-04a — assets are display-only. Their presence or absence must
    /// never move the Design-Analyst node's status.
    #[test]
    fn design_resources_do_not_affect_design_analyst_status() {
        let tmp = tempfile::tempdir().unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        // Assets but no analysis → still Idle.
        let assets_only = tmp.path().join("f1");
        write(
            &assets_only.join("design-resources/icon-home.svg"),
            "<svg/>",
        );
        assert_eq!(
            infer_feature_state(&assets_only, &runs_dir, &[])[slot::DESIGN_ANALYST].status,
            NodeStatus::Idle
        );

        // Analysis but no assets → Done anyway.
        let analysis_only = tmp.path().join("f2");
        write(
            &analysis_only.join("design-analysis.md"),
            &"x".repeat(MIN_DESIGN_ANALYSIS_CHARS + 1),
        );
        assert_eq!(
            infer_feature_state(&analysis_only, &runs_dir, &[])[slot::DESIGN_ANALYST].status,
            NodeStatus::Done
        );
    }

    /// AC-E3-01 — assets show up in the node detail panel, with
    /// `design-analysis.md` first so the auto-opened preview is never a
    /// binary file (`read_artifact` decodes UTF-8).
    #[test]
    fn design_analyst_artifacts_list_analysis_first_then_sorted_assets() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        write(
            &feature_dir.join("design-resources/logo-header.png"),
            "PNG-bytes",
        );
        write(
            &feature_dir.join("design-resources/icon-home.svg"),
            "<svg/>",
        );
        // A nested directory is not an asset file.
        std::fs::create_dir_all(feature_dir.join("design-resources/nested")).unwrap();
        write(
            &feature_dir.join("screenshot-design/WB_AUTH_001.png"),
            "PNG",
        );
        write(&feature_dir.join("design-analysis.md"), "x");

        let paths = artifact_paths_for_slot(&feature_dir, &runs_dir, slot::DESIGN_ANALYST);
        let names: Vec<String> = paths
            .iter()
            .map(|p| p.file_name().unwrap().to_string_lossy().into_owned())
            .collect();
        assert_eq!(
            names,
            vec![
                "design-analysis.md",
                "icon-home.svg",
                "logo-header.png",
                "WB_AUTH_001.png"
            ]
        );
    }

    #[test]
    fn design_analyst_idle_without_file_done_with_content_incomplete_when_short() {
        let tmp = tempfile::tempdir().unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let empty_feature = tmp.path().join("f1");
        std::fs::create_dir_all(&empty_feature).unwrap();
        assert_eq!(
            infer_feature_state(&empty_feature, &runs_dir, &[])[slot::DESIGN_ANALYST].status,
            NodeStatus::Idle
        );

        let short_feature = tmp.path().join("f2");
        write(&short_feature.join("design-analysis.md"), "too short");
        assert_eq!(
            infer_feature_state(&short_feature, &runs_dir, &[])[slot::DESIGN_ANALYST].status,
            NodeStatus::DoneIncomplete
        );

        let full_feature = tmp.path().join("f3");
        write(
            &full_feature.join("design-analysis.md"),
            &"x".repeat(MIN_DESIGN_ANALYSIS_CHARS + 1),
        );
        assert_eq!(
            infer_feature_state(&full_feature, &runs_dir, &[])[slot::DESIGN_ANALYST].status,
            NodeStatus::Done
        );
    }

    #[test]
    fn qc_design_done_when_any_module_has_test_cases_md() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(&feature_dir.join("test-cases/login/test-cases.md"), "x");
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let nodes = infer_feature_state(&feature_dir, &runs_dir, &[]);
        assert_eq!(nodes[slot::QC_DESIGN].status, NodeStatus::Done);
    }

    #[test]
    fn techlead_tasks_done_only_when_a_repo_has_task_files() {
        let tmp = tempfile::tempdir().unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        // A SPEC-only feature dir must NOT flip techlead-tasks to Done.
        let spec_only = tmp.path().join("spec-only");
        write(&spec_only.join("SPEC.md"), "x");
        let nodes = infer_feature_state(&spec_only, &runs_dir, &[]);
        assert_eq!(nodes[slot::TECHLEAD_TASKS].status, NodeStatus::Idle);

        let with_tasks = tmp.path().join("with-tasks");
        write(&with_tasks.join("backend-repo/tasks/task-1-1.md"), "x");
        let nodes = infer_feature_state(&with_tasks, &runs_dir, &[]);
        assert_eq!(nodes[slot::TECHLEAD_TASKS].status, NodeStatus::Done);
    }

    #[test]
    fn build_agents_are_always_idle_regardless_of_source_files() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        // Even if a repo subdir is full of "source code", stage ⑤ must
        // never be inferred from it — MVP1 has no agent runner.
        write(&feature_dir.join("backend-repo/src/index.ts"), "code");
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let nodes = infer_feature_state(&feature_dir, &runs_dir, &[]);
        for build_slot in [slot::BACKEND, slot::FRONTEND, slot::MOBILE] {
            assert_eq!(nodes[build_slot].status, NodeStatus::Idle);
        }
    }

    #[test]
    fn qc_automation_reads_from_runs_dir() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");
        write(
            &runs_dir.join("feature--qc-automation/execution-report.md"),
            "x",
        );

        let nodes = infer_feature_state(&feature_dir, &runs_dir, &[]);
        assert_eq!(nodes[slot::QC_AUTOMATION].status, NodeStatus::Done);
        assert_eq!(nodes[slot::QC_DESIGN].status, NodeStatus::Idle);
    }

    /// The scoping this whole convention exists for: an execution report
    /// belonging to a DIFFERENT feature must never make this feature's node
    /// read as `Done` — see `store::orchestrator_dir::runs_dir_run_id`'s doc
    /// comment for why `runs_dir` can't just be globbed unscoped.
    #[test]
    fn a_report_from_another_feature_never_counts_as_this_features_work() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");
        write(
            &runs_dir.join("other-feature--qc-automation/execution-report.md"),
            "x",
        );

        let nodes = infer_feature_state(&feature_dir, &runs_dir, &[]);
        assert_eq!(nodes[slot::QC_AUTOMATION].status, NodeStatus::Idle);
    }

    #[test]
    fn missing_runs_dir_does_not_panic() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let nonexistent_runs_dir = tmp.path().join("does-not-exist");

        let nodes = infer_feature_state(&feature_dir, &nonexistent_runs_dir, &[]);
        assert_eq!(nodes[slot::QC_AUTOMATION].status, NodeStatus::Idle);
    }

    #[test]
    fn artifact_paths_match_what_made_the_node_done() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(&feature_dir.join("SPEC.md"), COMPLETE_SPEC);
        write(&feature_dir.join("backend-repo/DESIGN.md"), "x");
        write(&feature_dir.join("backend-repo/tasks/task-1-1.md"), "x");
        let runs_dir = tmp.path().join("runs");
        write(
            &runs_dir.join("feature--qc-automation/execution-report.md"),
            "x",
        );

        let ba_paths = artifact_paths_for_slot(&feature_dir, &runs_dir, slot::BA);
        assert_eq!(ba_paths, vec![feature_dir.join("SPEC.md")]);

        let design_paths = artifact_paths_for_slot(&feature_dir, &runs_dir, slot::TECHLEAD_DESIGN);
        assert_eq!(
            design_paths,
            vec![feature_dir.join("backend-repo/DESIGN.md")]
        );

        let automation_paths =
            artifact_paths_for_slot(&feature_dir, &runs_dir, slot::QC_AUTOMATION);
        assert_eq!(
            automation_paths,
            vec![runs_dir.join("feature--qc-automation/execution-report.md")]
        );
    }

    #[test]
    fn artifact_paths_empty_for_idle_slots_and_build_slots() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        assert!(artifact_paths_for_slot(&feature_dir, &runs_dir, slot::QC_DESIGN).is_empty());
        assert!(artifact_paths_for_slot(&feature_dir, &runs_dir, slot::BACKEND).is_empty());
        assert!(artifact_paths_for_slot(&feature_dir, &runs_dir, "unknown-slot").is_empty());
    }

    #[test]
    fn all_artifact_paths_unions_every_slot_without_duplicates() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(&feature_dir.join("SPEC.md"), COMPLETE_SPEC);
        write(&feature_dir.join("backend-repo/DESIGN.md"), "x");
        write(&feature_dir.join("backend-repo/tasks/task-1-1.md"), "x");
        let runs_dir = tmp.path().join("runs");
        write(
            &runs_dir.join("feature--qc-automation/execution-report.md"),
            "x",
        );

        let paths = all_artifact_paths(&feature_dir, &runs_dir);
        assert!(paths.contains(&feature_dir.join("SPEC.md")));
        assert!(paths.contains(&feature_dir.join("backend-repo/DESIGN.md")));
        assert!(paths.contains(&feature_dir.join("backend-repo/tasks/task-1-1.md")));
        assert!(paths.contains(&runs_dir.join("feature--qc-automation/execution-report.md")));

        let mut sorted = paths.clone();
        sorted.sort();
        sorted.dedup();
        assert_eq!(paths, sorted, "must already be deduped");
    }

    #[test]
    fn all_artifact_paths_empty_for_empty_feature() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        assert!(all_artifact_paths(&feature_dir, &runs_dir).is_empty());
    }
}
