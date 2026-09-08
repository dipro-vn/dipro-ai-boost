//! Bridges pure inference (`inference::stage_rules`) with persistence
//! (`store::atomic_write`) and the watcher. Both the `get_pipeline_state`
//! command and the fswatch debounce callback go through
//! [`compute_and_persist`] so there is exactly one place that decides how a
//! freshly-computed `FeatureState` gets written into `state.json`.

use std::collections::BTreeMap;
use std::path::Path;

use crate::agentrun::run_log;
use crate::domain::node_status::{NodeState, NodeStatus};
use crate::domain::pipeline_def::gate;
use crate::domain::project::EcosystemRepo;
use crate::domain::run_summary::RunOutcome;
use crate::domain::state_file::{FeatureState, StateFile};
use crate::error::AppResult;
use crate::gitutil::git_source;
use crate::inference::{contract_lock_rules, gate_rules, stage_rules};
use crate::store::atomic_write::write_json_atomic;
use crate::store::contract_lock;
use crate::store::orchestrator_dir;
use crate::store::snapshot;

/// MVP1 always recomputes from disk rather than trusting a cached value —
/// inference is a handful of file reads, cheap enough that "always fresh"
/// is simpler and more honest than cache invalidation logic.
///
/// The `Vec<String>` half of the return is user-facing warnings surfaced
/// alongside the state rather than as an `Err` — a corrupted `state.json`
/// (AC-E6-08) or a deleted tracked artifact (AC-E3-06) must never stop the
/// Board from getting a usable `FeatureState`, only tell the user what
/// happened.
pub fn compute_and_persist(
    agents_root: &Path,
    docs_root: &Path,
    feature: &str,
    ecosystem: &[EcosystemRepo],
) -> AppResult<(FeatureState, Vec<String>)> {
    // Held for the whole read-modify-write below — see `lock_state_file`.
    // Without it two threads both read, both compute, and the second write
    // drops whatever the first one had just added.
    let _state_guard = orchestrator_dir::lock_state_file();

    let feature_dir = docs_root.join("features").join(feature);
    let runs_dir = orchestrator_dir::runs_dir(agents_root);

    let mut warnings = Vec::new();
    let state_path = orchestrator_dir::state_json_path(agents_root);
    let mut file: StateFile = match std::fs::read_to_string(&state_path) {
        Ok(raw) => match serde_json::from_str(&raw) {
            Ok(parsed) => parsed,
            Err(_) => {
                // AC-E6-08 — corrupted state.json: back it up (mirrors
                // `commands::project::load_or_reset_config`'s
                // `config.json.bak` pattern), dựng lại từ artifact trên
                // đĩa (the `infer_feature_state` call above already did
                // that), and say so — never silently overwrite.
                let backup_path = state_path.with_file_name("state.json.bak");
                if std::fs::rename(&state_path, &backup_path).is_ok() {
                    warnings.push(format!(
                        "state.json bị hỏng, đã backup thành {} và dựng lại từ artifact trên disk",
                        backup_path.display()
                    ));
                }
                StateFile::default()
            }
        },
        Err(_) => StateFile::default(),
    };

    let mut nodes = stage_rules::infer_feature_state(&feature_dir, &runs_dir, ecosystem);
    apply_agent_run_metadata(agents_root, feature, &mut nodes);

    // AC-E4-01/02/07 — read the previously persisted gate (if any) so
    // `infer_trigger_gate_state` can keep an `Approved` gate sticky rather
    // than recomputing it away.
    let previous_trigger_gate = file
        .features
        .get(feature)
        .and_then(|f| f.gates.get(gate::TRIGGER));
    let mut gates = BTreeMap::new();
    gates.insert(
        gate::TRIGGER.to_string(),
        gate_rules::infer_trigger_gate_state(&feature_dir, previous_trigger_gate),
    );

    // AC-E4-08..20 — unlike the Trigger gate (whose approval lives directly
    // in `state.json`, itself the source of truth), lock records live in
    // their own immutable-history directory (`store::contract_lock`,
    // AC-E4-19) — `state.json`'s own previous `contract_lock` field is only
    // ever a cache of what THIS function last computed, never where a lock
    // actually gets written. Reading it here instead of the real directory
    // would mean a freshly-written lock is never discovered. Must read the
    // real directory every time, same "always recompute from disk"
    // philosophy the rest of this function already follows.
    let contract_lock_dir = orchestrator_dir::contract_lock_dir(agents_root, feature);
    let previous_lock = contract_lock::read_latest_lock(&contract_lock_dir);
    let skip = contract_lock::read_skip(&contract_lock_dir);
    let contract_lock = contract_lock_rules::infer_contract_lock_state(
        &feature_dir,
        ecosystem,
        previous_lock,
        skip,
    );

    // AC-E4-29 (adapted — see this phase's plan doc for why the recovery
    // differs from the single-mutable-file model the AC assumes): never
    // silently fall back to an older lock without saying so.
    if contract_lock::has_unreadable_lock_file(&contract_lock_dir) {
        warnings.push(
            "Một hoặc nhiều file lịch sử Contract Lock bị hỏng, đã bỏ qua khi tính trạng thái hiện tại"
                .to_string(),
        );
    }

    // AC-E4-26 — log the moment a violation is first detected (transition
    // into `Violated`), not on every recompute while it's already
    // `Violated` — this is the one place `state.json`'s own previous value
    // is the right "previous" to compare against (unlike lock stickiness
    // above): it's only asking "did *this function* just observe a change",
    // not "what is the durable truth" (that's still the checksum
    // comparison inside `infer_contract_lock_state` itself).
    let was_already_violated = file
        .features
        .get(feature)
        .and_then(|f| f.contract_lock.as_ref())
        .map(|cl| cl.status == crate::domain::contract_lock::ContractLockStatus::Violated)
        .unwrap_or(false);
    if contract_lock.status == crate::domain::contract_lock::ContractLockStatus::Violated
        && !was_already_violated
    {
        let violations_dir = orchestrator_dir::contract_lock_violations_dir(agents_root, feature);
        let event = crate::domain::contract_lock::ViolationEvent {
            detected_at: chrono::Utc::now().to_rfc3339(),
            files: contract_lock.violated_files.clone(),
        };
        let _ = contract_lock::write_violation_event(&violations_dir, &event);
    }

    let state = FeatureState {
        nodes,
        gates,
        contract_lock: Some(contract_lock),
        updated_at: chrono::Utc::now().to_rfc3339(),
    };

    warn_about_vanished_artifacts(&feature_dir, feature, &file, &state, &mut warnings);

    file.features.insert(feature.to_string(), state.clone());
    write_json_atomic(&state_path, &file)?;

    // Best-effort: a snapshot failure for one artifact must not prevent
    // the (more important) FeatureState from being returned to the UI.
    snapshot_untracked_artifacts(agents_root, &feature_dir, &runs_dir);

    Ok((state, warnings))
}

/// AC-E3-06 — a slot that was `Done`/`DoneIncomplete` in the previously
/// persisted state and is now `Idle` in the freshly computed one means its
/// artifact disappeared from under it; name the file rather than letting
/// the Board silently revert to `Idle`. Only the single-file slots can be
/// named this way (see `canonical_single_artifact_path`) — a multi-file
/// slot going empty produces no warning here, since which specific file
/// vanished can't be known without guessing.
fn warn_about_vanished_artifacts(
    feature_dir: &Path,
    feature: &str,
    previous_file: &StateFile,
    new_state: &FeatureState,
    warnings: &mut Vec<String>,
) {
    let Some(previous) = previous_file.features.get(feature) else {
        return;
    };
    for (slot_id, old_node) in &previous.nodes {
        let was_tracked = matches!(
            old_node.status,
            NodeStatus::Done | NodeStatus::DoneIncomplete
        );
        let now_idle = new_state
            .nodes
            .get(slot_id)
            .map(|n| n.status == NodeStatus::Idle)
            .unwrap_or(false);
        if !was_tracked || !now_idle {
            continue;
        }
        if let Some(path) = stage_rules::canonical_single_artifact_path(feature_dir, slot_id) {
            if !path.is_file() {
                warnings.push(format!(
                    "Artifact {} của bước \"{slot_id}\" đã bị xoá — trạng thái quay về chưa xử lý.",
                    path.display()
                ));
            }
        }
    }
}

/// Layers T2.3's agent-run bookkeeping onto pure file-system inference —
/// "never ran" and "ran, ended without producing an artifact" both look
/// like `Idle` from disk alone, so this is what tells them apart, re-read
/// on every call (same "always recompute from disk" model as inference
/// itself, so it survives the watcher's next tick instead of only living
/// in memory). A live run (`running.json`) wins outright; otherwise the
/// persisted outcome only overrides `status` when inference says `Idle` —
/// a `Done`/`DoneIncomplete` node from a real artifact is left alone, and
/// cost/session/timing metadata is layered on top of it either way.
fn apply_agent_run_metadata(
    agents_root: &Path,
    feature: &str,
    nodes: &mut BTreeMap<String, NodeState>,
) {
    for (slot_id, node) in nodes.iter_mut() {
        // A live run outranks everything else: the marker is written before
        // the process spawns and removed by `finalize_run`, so its presence
        // means "running right now". Checked before the summary lookup
        // because a first run has a marker and no summary yet — without
        // this the Board showed "Chưa bắt đầu" for the whole run.
        if orchestrator_dir::agent_run_marker_path(agents_root, feature, slot_id).exists() {
            *node = NodeState::running();
            continue;
        }

        let Some(summary) = run_log::read_run_summary(agents_root, feature, slot_id) else {
            continue;
        };

        // Stage ⑤ slots leave no artifact behind (`artifact_paths_for_slot`
        // returns nothing for them), so inference can't see them at all and
        // their run log is the ONLY evidence they ran — it has to override
        // whatever default `infer_feature_state` put there. Without this a
        // successful backend run stayed `Idle` forever, which made
        // `after_slots: [backend]` unsatisfiable in every project and left
        // stage ⑥ waiting on a stage ⑤ that could never complete.
        //
        // Every other slot is the opposite: the artifact on disk is the
        // truth, and a `Done` run must not paper over one that inference
        // judged `DoneIncomplete`.
        let run_log_is_authoritative = crate::agentrun::readiness::slot_targets_repo(slot_id);
        if run_log_is_authoritative || node.status == NodeStatus::Idle {
            *node = match summary.outcome {
                RunOutcome::WaitingInput => {
                    NodeState::waiting_input(summary.last_message.clone().unwrap_or_default())
                }
                RunOutcome::Failed | RunOutcome::Timeout => {
                    NodeState::failed(summary.last_message.clone().unwrap_or_default())
                }
                RunOutcome::Blocked => {
                    NodeState::blocked(summary.last_message.clone().unwrap_or_default())
                }
                RunOutcome::Skipped => {
                    NodeState::skipped(summary.last_message.clone().unwrap_or_default())
                }
                RunOutcome::Interrupted => {
                    NodeState::interrupted(summary.last_message.clone().unwrap_or_default())
                }
                RunOutcome::Done if run_log_is_authoritative => NodeState::done(),
                RunOutcome::Done => node.clone(),
            };
        }

        *node = node.clone().with_run_metadata(
            summary.session_id.clone(),
            summary.cost_usd,
            summary.started_at.clone(),
            summary.ended_at.clone(),
        );
    }
}

/// For every artifact that isn't inside a git repository, keeps
/// `.orchestrator/snapshots/` up to date so T1.6's diff feature has
/// history to compare against — git-tracked artifacts use real git
/// history instead and are skipped here entirely (see
/// `gitutil::git_source`).
fn snapshot_untracked_artifacts(agents_root: &Path, feature_dir: &Path, runs_dir: &Path) {
    for path in stage_rules::all_artifact_paths(feature_dir, runs_dir) {
        if git_source::is_git_tracked(&path) {
            continue;
        }
        let Ok(content) = std::fs::read_to_string(&path) else {
            continue;
        };
        let dir = snapshot::snapshot_dir(agents_root, &path);
        let _ = snapshot::write_snapshot_if_changed(&dir, &content);
    }
}

/// `<docsRoot>/features/*` — every directory is a feature id, no filtering
/// (a feature folder without `SPEC.md` yet is still a valid, just-created
/// feature — AC-E3-01 watches for it to appear).
pub fn list_feature_ids(docs_root: &Path) -> Vec<String> {
    let features_dir = docs_root.join("features");
    let mut ids: Vec<String> = std::fs::read_dir(&features_dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.path().is_dir())
        .filter_map(|entry| entry.file_name().to_str().map(str::to_owned))
        .collect();
    ids.sort();
    ids
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn list_feature_ids_returns_sorted_directory_names() {
        let tmp = tempfile::tempdir().unwrap();
        let features_dir = tmp.path().join("features");
        std::fs::create_dir_all(features_dir.join("zeta")).unwrap();
        std::fs::create_dir_all(features_dir.join("alpha")).unwrap();
        std::fs::write(features_dir.join("not-a-dir.txt"), "x").unwrap();

        let ids = list_feature_ids(tmp.path());
        assert_eq!(ids, vec!["alpha", "zeta"]);
    }

    #[test]
    fn list_feature_ids_empty_when_features_dir_missing() {
        let tmp = tempfile::tempdir().unwrap();
        assert!(list_feature_ids(tmp.path()).is_empty());
    }

    #[test]
    fn compute_and_persist_merges_into_existing_state_without_clobbering_other_features() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let docs_root = tmp.path().join("docs-root");
        std::fs::create_dir_all(docs_root.join("features/feature-a")).unwrap();
        std::fs::create_dir_all(docs_root.join("features/feature-b")).unwrap();
        std::fs::create_dir_all(&agents_root).unwrap();

        compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        compute_and_persist(&agents_root, &docs_root, "feature-b", &[]).unwrap();

        let state_path = orchestrator_dir::state_json_path(&agents_root);
        let raw = std::fs::read_to_string(state_path).unwrap();
        let file: StateFile = serde_json::from_str(&raw).unwrap();
        assert_eq!(file.features.len(), 2);
        assert!(file.features.contains_key("feature-a"));
        assert!(file.features.contains_key("feature-b"));
    }

    /// The sequential test above passed all along — which is exactly why the
    /// bug hid. `compute_and_persist` reads `state.json`, computes, then
    /// writes; nothing holds a lock across those three steps, and the real
    /// app calls it from three different threads at once (the watcher's
    /// debounce, a run finishing, and the `get_pipeline_state` IPC). The
    /// loser of the interleaving writes a copy read before the winner's
    /// update, silently dropping it — and a Trigger-gate approval lives
    /// ONLY in this file, so what gets dropped can be a user's approval.
    ///
    /// Repeated because a race is probabilistic: one round proves nothing,
    /// a dropped feature in any round proves the bug.
    #[test]
    fn concurrent_compute_and_persist_never_drops_the_other_feature() {
        for round in 0..25 {
            let tmp = tempfile::tempdir().unwrap();
            let agents_root = tmp.path().join("agents-root");
            let docs_root = tmp.path().join("docs-root");
            std::fs::create_dir_all(docs_root.join("features/feature-a")).unwrap();
            std::fs::create_dir_all(docs_root.join("features/feature-b")).unwrap();
            std::fs::create_dir_all(&agents_root).unwrap();

            std::thread::scope(|scope| {
                for feature in ["feature-a", "feature-b"] {
                    let agents_root = agents_root.clone();
                    let docs_root = docs_root.clone();
                    scope.spawn(move || {
                        compute_and_persist(&agents_root, &docs_root, feature, &[]).unwrap();
                    });
                }
            });

            let raw =
                std::fs::read_to_string(orchestrator_dir::state_json_path(&agents_root)).unwrap();
            let file: StateFile = serde_json::from_str(&raw).unwrap();
            assert_eq!(
                file.features.len(),
                2,
                "round {round}: một feature bị ghi đè mất — {:?}",
                file.features.keys().collect::<Vec<_>>()
            );
        }
    }

    /// `project-ai-kit/example-project/` — synthetic fixture (T1.7), not
    /// real client data. `agents_root` here is always a fresh tempdir (this
    /// module never needs to read from it, only write `.orchestrator/`
    /// under it), so these tests never touch the checked-in fixture's own
    /// `.orchestrator/` from an earlier manual run.
    fn fixture_docs_root() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../example-project/docs")
            .canonicalize()
            .expect("example-project fixture must exist — see repo root")
    }

    fn copy_dir_recursive(src: &Path, dst: &Path) {
        std::fs::create_dir_all(dst).unwrap();
        for entry in std::fs::read_dir(src).unwrap() {
            let entry = entry.unwrap();
            let path = entry.path();
            let dest_path = dst.join(entry.file_name());
            if path.is_dir() {
                copy_dir_recursive(&path, &dest_path);
            } else {
                std::fs::copy(&path, &dest_path).unwrap();
            }
        }
    }

    /// README.md's "Dữ liệu mẫu" table, executed for real instead of just
    /// documented — this is the automated stand-in for T1.7's manual
    /// walkthrough (this session has no GUI to click through). Reads
    /// directly from the fixture; writes only into a fresh tempdir
    /// `agents_root`, so the checked-in fixture is never mutated.
    #[test]
    fn compute_and_persist_matches_readme_expected_states_for_example_project() {
        let agents_root = tempfile::tempdir().unwrap();
        let docs_root = fixture_docs_root();

        let (user_login, _) =
            compute_and_persist(agents_root.path(), &docs_root, "user-login", &[]).unwrap();
        for done_slot in [
            "ba",
            "techlead-design",
            "design-analyst",
            "qc-design",
            "techlead-tasks",
        ] {
            assert_eq!(
                user_login.nodes[done_slot].status,
                crate::domain::node_status::NodeStatus::Done,
                "slot {done_slot} should be Done for user-login"
            );
        }
        for idle_slot in ["backend", "frontend", "mobile", "qc-automation"] {
            assert_eq!(
                user_login.nodes[idle_slot].status,
                crate::domain::node_status::NodeStatus::Idle,
                "slot {idle_slot} has no agent runner in MVP1, must stay Idle"
            );
        }

        let (payment, _) =
            compute_and_persist(agents_root.path(), &docs_root, "payment-checkout", &[]).unwrap();
        assert_eq!(
            payment.nodes["ba"].status,
            crate::domain::node_status::NodeStatus::DoneIncomplete
        );
        assert!(payment.nodes["ba"].detail.is_some());
        for other_slot in payment.nodes.keys().filter(|k| k.as_str() != "ba") {
            assert_eq!(
                payment.nodes[other_slot].status,
                crate::domain::node_status::NodeStatus::Idle
            );
        }

        let (notification, _) =
            compute_and_persist(agents_root.path(), &docs_root, "notification-center", &[])
                .unwrap();
        assert!(notification
            .nodes
            .values()
            .all(|n| n.status == crate::domain::node_status::NodeStatus::Idle));
    }

    /// Exercises the full T1.6 diff stack (snapshot capture on
    /// `compute_and_persist` → change detection → 2 retrievable versions)
    /// against a real multi-file artifact from the fixture, not a
    /// single-line synthetic string. `docs_root` is copied into a tempdir
    /// so the SPEC.md mutation never touches the checked-in fixture.
    #[test]
    fn snapshot_capture_and_diff_across_repeated_runs_on_example_project_fixture() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let docs_root = tmp.path().join("docs");
        std::fs::create_dir_all(&agents_root).unwrap();
        copy_dir_recursive(&fixture_docs_root(), &docs_root);

        let spec_path = docs_root.join("features/user-login/SPEC.md");
        let original_content = std::fs::read_to_string(&spec_path).unwrap();
        assert!(
            !git_source::is_git_tracked(&spec_path),
            "fixture has no git init anywhere — must fall back to snapshot"
        );

        compute_and_persist(&agents_root, &docs_root, "user-login", &[]).unwrap();
        let snapshot_dir = snapshot::snapshot_dir(&agents_root, &spec_path);
        let versions_after_first_run = snapshot::list_snapshot_versions(&snapshot_dir);
        assert_eq!(versions_after_first_run.len(), 1);
        assert_eq!(
            snapshot::read_snapshot(&snapshot_dir, &versions_after_first_run[0].id).unwrap(),
            original_content
        );

        let modified_content = format!("{original_content}\n<!-- T1.7 fixture edit marker -->\n");
        std::fs::write(&spec_path, &modified_content).unwrap();
        // A second run within the same millisecond as the first would
        // collide on the snapshot filename (see `store::snapshot`'s own
        // test for the same caveat).
        std::thread::sleep(std::time::Duration::from_millis(2));

        compute_and_persist(&agents_root, &docs_root, "user-login", &[]).unwrap();
        let versions_after_second_run = snapshot::list_snapshot_versions(&snapshot_dir);
        assert_eq!(versions_after_second_run.len(), 2);
        // Newest first.
        assert_eq!(
            snapshot::read_snapshot(&snapshot_dir, &versions_after_second_run[0].id).unwrap(),
            modified_content
        );
        assert_eq!(
            snapshot::read_snapshot(&snapshot_dir, &versions_after_second_run[1].id).unwrap(),
            original_content
        );
    }

    #[test]
    fn corrupted_state_json_is_backed_up_and_reconstructed_with_a_warning() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let docs_root = tmp.path().join("docs-root");
        std::fs::create_dir_all(docs_root.join("features/feature-a")).unwrap();

        let state_path = orchestrator_dir::state_json_path(&agents_root);
        std::fs::create_dir_all(state_path.parent().unwrap()).unwrap();
        std::fs::write(&state_path, "not valid json").unwrap();

        let (state, warnings) =
            compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        assert!(!state.nodes.is_empty());
        assert!(warnings.iter().any(|w| w.contains("state.json bị hỏng")));

        let backup_path = state_path.with_file_name("state.json.bak");
        assert_eq!(
            std::fs::read_to_string(&backup_path).unwrap(),
            "not valid json"
        );
        // The rebuilt state.json must be valid JSON containing the feature.
        let rebuilt: StateFile =
            serde_json::from_str(&std::fs::read_to_string(&state_path).unwrap()).unwrap();
        assert!(rebuilt.features.contains_key("feature-a"));
    }

    #[test]
    fn deleted_ba_artifact_warns_and_reverts_to_idle() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let feature_dir = tmp.path().join("docs-root/features/feature-a");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let spec_path = feature_dir.join("SPEC.md");
        std::fs::write(
            &spec_path,
            "## Mô tả nghiệp vụ\nx\n## Actors & Preconditions\nx\n## Happy Path\nx\n## Alternative Flows & Edge Cases\nx\n## Acceptance Criteria\nx\n## Out of Scope\nx\n## Screens\nx\n",
        )
        .unwrap();
        let docs_root = tmp.path().join("docs-root");

        let (first, first_warnings) =
            compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        assert_eq!(
            first.nodes["ba"].status,
            crate::domain::node_status::NodeStatus::Done
        );
        assert!(first_warnings.is_empty());

        std::fs::remove_file(&spec_path).unwrap();

        let (second, second_warnings) =
            compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        assert_eq!(
            second.nodes["ba"].status,
            crate::domain::node_status::NodeStatus::Idle
        );
        assert!(second_warnings
            .iter()
            .any(|w| w.contains("SPEC.md") && w.contains("ba")));
    }

    #[test]
    fn compute_and_persist_carries_trigger_gate_through_and_keeps_it_sticky_once_approved() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let feature_dir = tmp.path().join("docs-root/features/feature-a");
        std::fs::create_dir_all(&feature_dir).unwrap();
        let docs_root = tmp.path().join("docs-root");

        let (first, _) = compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        assert_eq!(
            first.gates[crate::domain::pipeline_def::gate::TRIGGER].status,
            crate::domain::gate_state::GateStatus::NotReady
        );

        // Simulate an approval having been persisted directly (as
        // `commands::agentrun::approve_trigger_gate` will do) — recompute
        // must not revoke it.
        let state_path = orchestrator_dir::state_json_path(&agents_root);
        let mut file: StateFile =
            serde_json::from_str(&std::fs::read_to_string(&state_path).unwrap()).unwrap();
        file.features.get_mut("feature-a").unwrap().gates.insert(
            crate::domain::pipeline_def::gate::TRIGGER.to_string(),
            crate::domain::gate_state::GateState {
                status: crate::domain::gate_state::GateStatus::Approved,
                approved_by: Some("PM Test".to_string()),
                approved_at: Some("2026-08-17T00:00:00Z".to_string()),
                missing_sections: vec![],
            },
        );
        write_json_atomic(&state_path, &file).unwrap();

        let (second, _) = compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        let gate = &second.gates[crate::domain::pipeline_def::gate::TRIGGER];
        assert_eq!(gate.status, crate::domain::gate_state::GateStatus::Approved);
        assert_eq!(gate.approved_by.as_deref(), Some("PM Test"));
    }

    #[test]
    fn compute_and_persist_detects_a_violation_and_logs_it_exactly_once() {
        use crate::domain::contract_lock::{ContractLockRecord, ContractLockStatus, LockedFile};

        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let docs_root = tmp.path().join("docs-root");
        let design_md = docs_root.join("features/feature-a/api/DESIGN.md");
        std::fs::create_dir_all(design_md.parent().unwrap()).unwrap();
        std::fs::write(&design_md, "original content").unwrap();

        let lock_dir = orchestrator_dir::contract_lock_dir(&agents_root, "feature-a");
        contract_lock::write_lock_record(
            &lock_dir,
            &ContractLockRecord {
                locked_at: "2026-08-17T00:00:00Z".to_string(),
                approved_by: "PM Test".to_string(),
                confirmed_roles: vec!["PM".to_string(), "QC".to_string()],
                files: vec![LockedFile {
                    path: design_md.display().to_string(),
                    checksum_sha256: contract_lock_rules::sha256_hex("original content"),
                    content: "original content".to_string(),
                }],
            },
        )
        .unwrap();

        // Not yet edited — stays Locked, no violation logged.
        let (clean, _) = compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        assert_eq!(
            clean.contract_lock.unwrap().status,
            ContractLockStatus::Locked
        );
        let violations_dir =
            orchestrator_dir::contract_lock_violations_dir(&agents_root, "feature-a");
        assert!(contract_lock::list_violation_events(&violations_dir).is_empty());

        std::fs::write(&design_md, "edited content").unwrap();

        let (violated, _) =
            compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        assert_eq!(
            violated.contract_lock.unwrap().status,
            ContractLockStatus::Violated
        );
        assert_eq!(
            contract_lock::list_violation_events(&violations_dir).len(),
            1
        );

        // A second recompute while still violated must not log a duplicate
        // event — only the transition into `Violated` gets logged.
        let (still_violated, _) =
            compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        assert_eq!(
            still_violated.contract_lock.unwrap().status,
            ContractLockStatus::Violated
        );
        assert_eq!(
            contract_lock::list_violation_events(&violations_dir).len(),
            1
        );
    }

    /// AC-E6-04 — an `interrupted` summary written by the startup scan must
    fn summary(outcome: RunOutcome) -> crate::domain::run_summary::RunSummary {
        crate::domain::run_summary::RunSummary {
            outcome,
            session_id: "sess-1".to_string(),
            cost_usd: 0.0,
            started_at: "2026-08-17T00:00:00Z".to_string(),
            ended_at: "2026-08-17T00:05:00Z".to_string(),
            last_message: None,
            attempt: 1,
            prompt: None,
        }
    }

    fn write_summary(agents_root: &Path, feature: &str, slot: &str, outcome: RunOutcome) {
        let path = orchestrator_dir::agent_run_summary_path(agents_root, feature, slot);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        crate::store::atomic_write::write_json_atomic(&path, &summary(outcome)).unwrap();
    }

    /// Stage ⑤ slots produce no artifact, so inference always called them
    /// `Idle` and `RunOutcome::Done` mapped to "keep what inference said" —
    /// i.e. a successful backend run stayed `Idle` forever. That made
    /// `after_slots: [backend]` unsatisfiable in EVERY project and left
    /// stage ⑥ waiting on a stage ⑤ that could never complete.
    #[test]
    fn a_successful_build_run_actually_reaches_done() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let docs_root = tmp.path().join("docs-root");
        std::fs::create_dir_all(docs_root.join("features/feature-a")).unwrap();
        std::fs::create_dir_all(&agents_root).unwrap();

        write_summary(&agents_root, "feature-a", "backend", RunOutcome::Done);

        let (state, _) = compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        assert_eq!(
            state.nodes.get("backend").unwrap().status,
            crate::domain::node_status::NodeStatus::Done
        );
    }

    /// The other half: for a slot that DOES leave an artifact, the artifact
    /// stays the truth. A `Done` run must not paper over a `SPEC.md` that
    /// inference judged incomplete.
    #[test]
    fn a_done_run_never_upgrades_an_incomplete_artifact() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let docs_root = tmp.path().join("docs-root");
        let feature_dir = docs_root.join("features/feature-a");
        std::fs::create_dir_all(&feature_dir).unwrap();
        std::fs::create_dir_all(&agents_root).unwrap();
        // Present but missing the required sections.
        std::fs::write(feature_dir.join("SPEC.md"), "# Chỉ có tiêu đề\n").unwrap();

        write_summary(&agents_root, "feature-a", "ba", RunOutcome::Done);

        let (state, _) = compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        assert_eq!(
            state.nodes.get("ba").unwrap().status,
            crate::domain::node_status::NodeStatus::DoneIncomplete
        );
    }

    /// surface as `NodeStatus::Interrupted` in state.json, distinct from
    /// `failed`, whenever inference alone would call the slot idle.
    #[test]
    fn interrupted_run_summary_overrides_idle_node_status() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let docs_root = tmp.path().join("docs-root");
        std::fs::create_dir_all(docs_root.join("features/feature-a")).unwrap();
        std::fs::create_dir_all(&agents_root).unwrap();

        let summary = crate::domain::run_summary::RunSummary {
            outcome: RunOutcome::Interrupted,
            session_id: "sess-1".to_string(),
            cost_usd: 0.0,
            started_at: "2026-08-17T00:00:00Z".to_string(),
            ended_at: "2026-08-17T00:05:00Z".to_string(),
            last_message: Some("Bị gián đoạn — app đóng khi agent đang chạy.".to_string()),
            attempt: 1,
            prompt: Some("original".to_string()),
        };
        let path = orchestrator_dir::agent_run_summary_path(&agents_root, "feature-a", "ba");
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        crate::store::atomic_write::write_json_atomic(&path, &summary).unwrap();

        let (state, _) = compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        let node = state.nodes.get("ba").unwrap();
        assert_eq!(
            node.status,
            crate::domain::node_status::NodeStatus::Interrupted
        );
        assert_eq!(node.session_id.as_deref(), Some("sess-1"));
    }

    /// A live run must win over everything else on the Board — this is the
    /// bug where a node sat on "Chưa bắt đầu" for an entire agent run
    /// because only finished outcomes were ever mapped.
    #[test]
    fn a_running_marker_shows_the_node_as_running() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let docs_root = tmp.path().join("docs-root");
        std::fs::create_dir_all(docs_root.join("features/feature-a")).unwrap();
        std::fs::create_dir_all(&agents_root).unwrap();

        let marker_path = orchestrator_dir::agent_run_marker_path(&agents_root, "feature-a", "ba");
        std::fs::create_dir_all(marker_path.parent().unwrap()).unwrap();
        crate::store::atomic_write::write_json_atomic(
            &marker_path,
            &crate::domain::running_marker::RunningMarker {
                pid: Some(1234),
                started_at: "2026-08-18T03:21:40Z".to_string(),
                attempt: 1,
                prompt: Some("phân tích input".to_string()),
            },
        )
        .unwrap();

        let (state, _) = compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        assert_eq!(
            state.nodes.get("ba").unwrap().status,
            crate::domain::node_status::NodeStatus::Running
        );
    }

    /// ...and the marker outranks a stale summary from the previous run
    /// rather than showing that run's outcome while a new one is in flight.
    #[test]
    fn a_running_marker_outranks_a_previous_runs_summary() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let docs_root = tmp.path().join("docs-root");
        std::fs::create_dir_all(docs_root.join("features/feature-a")).unwrap();
        std::fs::create_dir_all(&agents_root).unwrap();

        let summary_path =
            orchestrator_dir::agent_run_summary_path(&agents_root, "feature-a", "ba");
        std::fs::create_dir_all(summary_path.parent().unwrap()).unwrap();
        crate::store::atomic_write::write_json_atomic(
            &summary_path,
            &crate::domain::run_summary::RunSummary {
                outcome: RunOutcome::Failed,
                session_id: "old".to_string(),
                cost_usd: 0.5,
                started_at: "2026-08-18T02:00:00Z".to_string(),
                ended_at: "2026-08-18T02:01:00Z".to_string(),
                last_message: Some("lần trước hỏng".to_string()),
                attempt: 1,
                prompt: None,
            },
        )
        .unwrap();
        crate::store::atomic_write::write_json_atomic(
            &orchestrator_dir::agent_run_marker_path(&agents_root, "feature-a", "ba"),
            &crate::domain::running_marker::RunningMarker {
                pid: Some(1234),
                started_at: "2026-08-18T03:00:00Z".to_string(),
                attempt: 2,
                prompt: None,
            },
        )
        .unwrap();

        let (state, _) = compute_and_persist(&agents_root, &docs_root, "feature-a", &[]).unwrap();
        let node = state.nodes.get("ba").unwrap();
        assert_eq!(node.status, crate::domain::node_status::NodeStatus::Running);
        // The previous run's numbers must not sit next to "đang chạy".
        assert!(node.cost_usd.is_none());
        assert!(node.session_id.is_none());
    }
}
