use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use crate::domain::node_status::NodeState;
use crate::domain::pipeline_def::slot;
use crate::inference::spec_sections;

/// `design-analysis.md` existing but shorter than this (after trimming
/// whitespace) is treated as incomplete rather than done (AF-3). The SPEC
/// does not give a concrete number for "quá ngắn" — this is an
/// implementation choice, not a value extracted from any document. Revisit
/// if it produces false positives/negatives in practice.
const MIN_DESIGN_ANALYSIS_CHARS: usize = 50;

const NON_REPO_SUBDIRS: &[&str] = &["test-cases"];

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
        .flat_map(|repo| {
            let tasks_dir = repo.join("tasks");
            std::fs::read_dir(&tasks_dir)
                .into_iter()
                .flatten()
                .filter_map(|entry| entry.ok())
                .map(|entry| entry.path())
                .filter(|path| {
                    let name = path.file_name().unwrap_or_default().to_string_lossy();
                    name.starts_with("task-") && name.ends_with(".md")
                })
                .collect::<Vec<_>>()
        })
        .collect()
}

fn any_repo_has_task_files(feature_dir: &Path) -> bool {
    !task_files_in_repos(feature_dir).is_empty()
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

/// `runs_dir` holds app-defined report conventions the kit itself does not
/// specify a path for (AC-E3-05) — `<runs_dir>/<run-id>/<filename>`.
fn run_files(runs_dir: &Path, filename: &str) -> Vec<PathBuf> {
    std::fs::read_dir(runs_dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| path.is_dir())
        .map(|run_dir| run_dir.join(filename))
        .filter(|path| path.is_file())
        .collect()
}

fn any_run_has_file(runs_dir: &Path, filename: &str) -> bool {
    !run_files(runs_dir, filename).is_empty()
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
/// `backend`/`frontend`/`mobile` (stage ⑤) are always `Idle`: there is no
/// agent runner in MVP1, and this function must not "suy từ source code"
/// (SPEC's own words) to guess build status — that would be exactly the
/// kind of guessing the kit's core policy forbids.
pub fn infer_feature_state(feature_dir: &Path, runs_dir: &Path) -> BTreeMap<String, NodeState> {
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

    nodes.insert(
        slot::PM.to_string(),
        if feature_dir.join("PLAN.md").is_file() {
            NodeState::done()
        } else {
            NodeState::idle()
        },
    );

    for build_slot in [slot::BACKEND, slot::FRONTEND, slot::MOBILE] {
        nodes.insert(build_slot.to_string(), NodeState::idle());
    }

    nodes.insert(
        slot::QA.to_string(),
        if any_run_has_file(runs_dir, "qa-report.md") {
            NodeState::done()
        } else {
            NodeState::idle()
        },
    );

    nodes.insert(
        slot::QC_TESTING.to_string(),
        if any_run_has_file(runs_dir, "qc-checklist.md") {
            NodeState::done()
        } else {
            NodeState::idle()
        },
    );

    nodes.insert(
        slot::QC_AUTOMATION.to_string(),
        if any_run_has_file(runs_dir, "execution-report.md") {
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
            let path = feature_dir.join("design-analysis.md");
            if path.is_file() {
                vec![path]
            } else {
                vec![]
            }
        }
        s if s == slot::QC_DESIGN => test_cases_files(feature_dir),
        s if s == slot::TECHLEAD_TASKS => task_files_in_repos(feature_dir),
        s if s == slot::PM => {
            let path = feature_dir.join("PLAN.md");
            if path.is_file() {
                vec![path]
            } else {
                vec![]
            }
        }
        s if s == slot::BACKEND || s == slot::FRONTEND || s == slot::MOBILE => vec![],
        s if s == slot::QA => run_files(runs_dir, "qa-report.md"),
        s if s == slot::QC_TESTING => run_files(runs_dir, "qc-checklist.md"),
        s if s == slot::QC_AUTOMATION => run_files(runs_dir, "execution-report.md"),
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
        s if s == slot::PM => Some(feature_dir.join("PLAN.md")),
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

        let mut computed: Vec<String> = infer_feature_state(&feature_dir, &runs_dir)
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

    #[test]
    fn empty_feature_dir_is_all_idle() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("features/some-feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let nodes = infer_feature_state(&feature_dir, &runs_dir);
        assert_eq!(nodes.len(), 12); // 12 agent slots total across the 8 stages
        assert!(nodes.values().all(|n| n.status == NodeStatus::Idle));
    }

    #[test]
    fn ba_done_when_spec_has_all_7_sections() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(&feature_dir.join("SPEC.md"), COMPLETE_SPEC);
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let nodes = infer_feature_state(&feature_dir, &runs_dir);
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

        let nodes = infer_feature_state(&feature_dir, &runs_dir);
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

        let nodes = infer_feature_state(&feature_dir, &runs_dir);
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

        let nodes = infer_feature_state(&feature_dir, &runs_dir);
        assert_eq!(nodes[slot::TECHLEAD_DESIGN].status, NodeStatus::Idle);
    }

    #[test]
    fn design_analyst_idle_without_file_done_with_content_incomplete_when_short() {
        let tmp = tempfile::tempdir().unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        let empty_feature = tmp.path().join("f1");
        std::fs::create_dir_all(&empty_feature).unwrap();
        assert_eq!(
            infer_feature_state(&empty_feature, &runs_dir)[slot::DESIGN_ANALYST].status,
            NodeStatus::Idle
        );

        let short_feature = tmp.path().join("f2");
        write(&short_feature.join("design-analysis.md"), "too short");
        assert_eq!(
            infer_feature_state(&short_feature, &runs_dir)[slot::DESIGN_ANALYST].status,
            NodeStatus::DoneIncomplete
        );

        let full_feature = tmp.path().join("f3");
        write(
            &full_feature.join("design-analysis.md"),
            &"x".repeat(MIN_DESIGN_ANALYSIS_CHARS + 1),
        );
        assert_eq!(
            infer_feature_state(&full_feature, &runs_dir)[slot::DESIGN_ANALYST].status,
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

        let nodes = infer_feature_state(&feature_dir, &runs_dir);
        assert_eq!(nodes[slot::QC_DESIGN].status, NodeStatus::Done);
    }

    #[test]
    fn techlead_tasks_done_when_any_repo_has_task_files_plan_alone_is_not_enough() {
        let tmp = tempfile::tempdir().unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        // PLAN.md alone must NOT flip techlead-tasks to Done.
        let plan_only = tmp.path().join("plan-only");
        write(&plan_only.join("PLAN.md"), "x");
        let nodes = infer_feature_state(&plan_only, &runs_dir);
        assert_eq!(nodes[slot::TECHLEAD_TASKS].status, NodeStatus::Idle);
        assert_eq!(nodes[slot::PM].status, NodeStatus::Done);

        let with_tasks = tmp.path().join("with-tasks");
        write(&with_tasks.join("backend-repo/tasks/task-1-1.md"), "x");
        let nodes = infer_feature_state(&with_tasks, &runs_dir);
        assert_eq!(nodes[slot::TECHLEAD_TASKS].status, NodeStatus::Done);
        assert_eq!(nodes[slot::PM].status, NodeStatus::Idle);
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

        let nodes = infer_feature_state(&feature_dir, &runs_dir);
        for build_slot in [slot::BACKEND, slot::FRONTEND, slot::MOBILE] {
            assert_eq!(nodes[build_slot].status, NodeStatus::Idle);
        }
    }

    #[test]
    fn qa_qc_testing_qc_automation_read_from_runs_dir() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");
        write(&runs_dir.join("run-1/qa-report.md"), "x");
        write(&runs_dir.join("run-2/execution-report.md"), "x");

        let nodes = infer_feature_state(&feature_dir, &runs_dir);
        assert_eq!(nodes[slot::QA].status, NodeStatus::Done);
        assert_eq!(nodes[slot::QC_AUTOMATION].status, NodeStatus::Done);
        assert_eq!(nodes[slot::QC_TESTING].status, NodeStatus::Idle);
    }

    #[test]
    fn missing_runs_dir_does_not_panic() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let nonexistent_runs_dir = tmp.path().join("does-not-exist");

        let nodes = infer_feature_state(&feature_dir, &nonexistent_runs_dir);
        assert_eq!(nodes[slot::QA].status, NodeStatus::Idle);
    }

    #[test]
    fn artifact_paths_match_what_made_the_node_done() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(&feature_dir.join("SPEC.md"), COMPLETE_SPEC);
        write(&feature_dir.join("backend-repo/DESIGN.md"), "x");
        write(&feature_dir.join("backend-repo/tasks/task-1-1.md"), "x");
        let runs_dir = tmp.path().join("runs");
        write(&runs_dir.join("run-1/qa-report.md"), "x");

        let ba_paths = artifact_paths_for_slot(&feature_dir, &runs_dir, slot::BA);
        assert_eq!(ba_paths, vec![feature_dir.join("SPEC.md")]);

        let design_paths = artifact_paths_for_slot(&feature_dir, &runs_dir, slot::TECHLEAD_DESIGN);
        assert_eq!(
            design_paths,
            vec![feature_dir.join("backend-repo/DESIGN.md")]
        );

        let qa_paths = artifact_paths_for_slot(&feature_dir, &runs_dir, slot::QA);
        assert_eq!(qa_paths, vec![runs_dir.join("run-1/qa-report.md")]);
    }

    #[test]
    fn artifact_paths_empty_for_idle_slots_and_build_slots() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let runs_dir = tmp.path().join("runs");
        std::fs::create_dir_all(&runs_dir).unwrap();

        assert!(artifact_paths_for_slot(&feature_dir, &runs_dir, slot::PM).is_empty());
        assert!(artifact_paths_for_slot(&feature_dir, &runs_dir, slot::BACKEND).is_empty());
        assert!(artifact_paths_for_slot(&feature_dir, &runs_dir, "unknown-slot").is_empty());
    }

    #[test]
    fn all_artifact_paths_unions_every_slot_without_duplicates() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(&feature_dir.join("SPEC.md"), COMPLETE_SPEC);
        write(&feature_dir.join("PLAN.md"), "x");
        write(&feature_dir.join("backend-repo/DESIGN.md"), "x");
        write(&feature_dir.join("backend-repo/tasks/task-1-1.md"), "x");
        let runs_dir = tmp.path().join("runs");
        write(&runs_dir.join("run-1/qa-report.md"), "x");

        let paths = all_artifact_paths(&feature_dir, &runs_dir);
        assert!(paths.contains(&feature_dir.join("SPEC.md")));
        assert!(paths.contains(&feature_dir.join("PLAN.md")));
        assert!(paths.contains(&feature_dir.join("backend-repo/DESIGN.md")));
        assert!(paths.contains(&feature_dir.join("backend-repo/tasks/task-1-1.md")));
        assert!(paths.contains(&runs_dir.join("run-1/qa-report.md")));

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
