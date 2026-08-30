use std::path::{Path, PathBuf};

use tauri::{AppHandle, State};

use crate::app_state::AppState;
use crate::domain::contract_lock::{ContractLockRecord, ContractLockStatus};
use crate::domain::node_detail::{ArtifactRef, NodeDetail};
use crate::domain::pipeline_def::{slot, PipelineDef, PIPELINE_DEF_VERSION};
use crate::domain::project::ProjectPaths;
use crate::domain::state_file::{FeatureState, StateFile};
use crate::error::{AppError, AppResult};
use crate::fswatch::watcher;
use crate::inference::stage_rules;
use crate::pipeline_state::{compute_and_persist, list_feature_ids};
use crate::store::atomic_write::write_json_atomic;
use crate::store::contract_lock as contract_lock_store;
use crate::store::orchestrator_dir;

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

/// AC-E4-24 — sets `ContractLockState.running_on_old_contract` when
/// `backend-agent` has a live process for this feature at the same time
/// the contract is `Violated`. `pub(crate)` so `fswatch::watcher` (the
/// other of the only 2 places with `AppState`) can reuse it too, instead
/// of duplicating this check.
pub(crate) fn mark_running_on_old_contract(
    state: &State<AppState>,
    feature: &str,
    result: &mut FeatureState,
) {
    if let Some(contract_lock) = result.contract_lock.as_mut() {
        if contract_lock.status == ContractLockStatus::Violated {
            contract_lock.running_on_old_contract = state.is_running(feature, slot::BACKEND);
        }
    }
}

#[tauri::command]
pub fn list_features(state: State<AppState>) -> AppResult<Vec<String>> {
    let project = current_project(&state)?;
    Ok(list_feature_ids(Path::new(&project.docs_root)))
}

/// AC-E2-24 — creates `<docsRoot>/features/<name>/` so a feature can be
/// started from inside the app instead of only as a side effect of
/// importing a folder (`commands::import::perform_import`).
///
/// An empty feature directory is already a valid, just-created feature
/// everywhere else in the app: `list_feature_ids` picks it up and
/// `infer_feature_state` reports every node as `idle`. So creating the
/// directory is the whole operation — no state file is written, nothing is
/// spawned.
///
/// Returns the refreshed feature list so the caller renders from one
/// authoritative read instead of appending optimistically.
fn create_feature_dir(docs_root: &Path, name: &str) -> AppResult<Vec<String>> {
    let name = name.trim();
    if !crate::commands::import::is_kebab_case(name) {
        return Err(AppError::Invalid {
            message: format!(
                "Tên feature phải là kebab-case — chữ thường, số và dấu gạch ngang đơn (vd `user-login`). Nhận được: \"{name}\""
            ),
        });
    }

    let feature_dir = docs_root.join("features").join(name);
    // `create_dir_all` succeeds silently on an existing directory, which
    // would make "tạo mới" quietly jump into a feature that already has
    // work in it — refuse instead.
    if feature_dir.exists() {
        return Err(AppError::Invalid {
            message: format!("Feature \"{name}\" đã tồn tại — chọn nó trong danh sách bên trái"),
        });
    }

    std::fs::create_dir_all(&feature_dir)?;
    Ok(list_feature_ids(docs_root))
}

#[tauri::command]
pub fn create_feature(state: State<AppState>, name: String) -> AppResult<Vec<String>> {
    let project = current_project(&state)?;
    create_feature_dir(Path::new(&project.docs_root), &name)
}

/// What deleting a feature would destroy. Shown to the user BEFORE they
/// confirm — this is the most destructive action in the app (it removes
/// real deliverables: SPEC.md, DESIGN.md, tasks/, test-cases/), so it must
/// never be a blind click.
#[derive(Debug, Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FeatureDeletionPreview {
    /// Files under `<docsRoot>/features/<name>/` — the actual work product.
    pub doc_file_count: usize,
    /// Paths (relative to the feature dir) of the artifacts that matter, so
    /// the dialog can name what is being thrown away instead of only
    /// counting it.
    pub notable_artifacts: Vec<String>,
    /// Slots with a persisted run under `.orchestrator/agent-runs/`.
    pub run_count: usize,
    pub has_contract_lock: bool,
    /// Imported input copies under `.orchestrator/inputs/<ts>-<name>/`.
    pub input_copy_count: usize,
    /// Slots with a live process — deletion is refused while any exist.
    pub running_slots: Vec<String>,
}

fn count_files(dir: &Path) -> usize {
    let Ok(entries) = std::fs::read_dir(dir) else {
        return 0;
    };
    entries
        .flatten()
        .map(|entry| {
            let path = entry.path();
            if path.is_dir() {
                count_files(&path)
            } else {
                1
            }
        })
        .sum()
}

/// Artifact-looking files worth naming in the confirm dialog, relative to
/// the feature dir, sorted and capped — a full listing would bury the
/// point for a feature with dozens of task files.
fn notable_artifacts(feature_dir: &Path) -> Vec<String> {
    fn walk(dir: &Path, root: &Path, out: &mut Vec<String>) {
        let Ok(entries) = std::fs::read_dir(dir) else {
            return;
        };
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                walk(&path, root, out);
            } else if path.extension().and_then(|e| e.to_str()) == Some("md") {
                if let Ok(rel) = path.strip_prefix(root) {
                    out.push(rel.to_string_lossy().replace('\\', "/"));
                }
            }
        }
    }
    let mut out = Vec::new();
    walk(feature_dir, feature_dir, &mut out);
    out.sort();
    out.truncate(12);
    out
}

/// Input copies are named `<timestamp>-<feature>` (see
/// `commands::import::perform_import`), so they're found by suffix.
fn input_copy_dirs(agents_root: &Path, feature: &str) -> Vec<PathBuf> {
    let suffix = format!("-{feature}");
    let Ok(entries) = std::fs::read_dir(orchestrator_dir::inputs_dir(agents_root)) else {
        return Vec::new();
    };
    entries
        .flatten()
        .map(|entry| entry.path())
        .filter(|path| {
            path.is_dir()
                && path
                    .file_name()
                    .and_then(|n| n.to_str())
                    .is_some_and(|name| name.ends_with(&suffix))
        })
        .collect()
}

fn deletion_preview(
    agents_root: &Path,
    docs_root: &Path,
    feature: &str,
    running_slots: Vec<String>,
) -> FeatureDeletionPreview {
    let feature_dir = docs_root.join("features").join(feature);
    let agent_runs = orchestrator_dir::agent_runs_dir(agents_root).join(feature);

    FeatureDeletionPreview {
        doc_file_count: count_files(&feature_dir),
        notable_artifacts: notable_artifacts(&feature_dir),
        run_count: std::fs::read_dir(&agent_runs)
            .map(|entries| entries.flatten().filter(|e| e.path().is_dir()).count())
            .unwrap_or(0),
        has_contract_lock: orchestrator_dir::contract_lock_dir(agents_root, feature).exists(),
        input_copy_count: input_copy_dirs(agents_root, feature).len(),
        running_slots,
    }
}

#[tauri::command]
pub fn preview_delete_feature(
    state: State<AppState>,
    name: String,
) -> AppResult<FeatureDeletionPreview> {
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let docs_root = PathBuf::from(&project.docs_root);

    let def = read_or_init_pipeline_def(&agents_root)?;
    let running_slots: Vec<String> = def
        .stages
        .iter()
        .flat_map(|stage| stage.agents.iter())
        .map(|agent| agent.id.clone())
        .filter(|slot| state.is_running(&name, slot))
        .collect();

    Ok(deletion_preview(
        &agents_root,
        &docs_root,
        &name,
        running_slots,
    ))
}

/// Removes a feature entirely: its `<docsRoot>/features/<name>/` directory
/// (the only source of truth for whether a feature exists — the sidebar
/// lists that directory) plus every piece of `.orchestrator/` bookkeeping
/// keyed by it.
///
/// `run-history/` is deliberately NOT touched: cost accounting is
/// cross-feature and must survive, exactly as AC-E6-28 already requires of
/// log clearing. Snapshots are keyed by a hash of each artifact's absolute
/// path (`store::snapshot::slug_for`) and are left behind — they are
/// unreachable once the artifacts are gone and cost a few KB, which is
/// cheaper than resolving hashes back to a feature.
///
/// `confirmation` must equal `name`: the frontend asks the user to retype
/// it, and the backend re-checks so a UI bug can never delete the wrong
/// feature silently.
#[tauri::command]
pub fn delete_feature(
    state: State<AppState>,
    name: String,
    confirmation: String,
) -> AppResult<Vec<String>> {
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let docs_root = PathBuf::from(&project.docs_root);

    if confirmation.trim() != name {
        return Err(AppError::Invalid {
            message: "Tên xác nhận không khớp — gõ đúng tên feature để xoá".to_string(),
        });
    }

    let preview = preview_delete_feature(state, name.clone())?;
    if !preview.running_slots.is_empty() {
        return Err(AppError::Invalid {
            message: format!(
                "Đang có agent chạy cho feature này ({}) — dừng (Kill) trước khi xoá",
                preview.running_slots.join(", ")
            ),
        });
    }

    let feature_dir = docs_root.join("features").join(&name);
    if !feature_dir.is_dir() {
        return Err(AppError::Invalid {
            message: format!("Không tìm thấy feature \"{name}\""),
        });
    }
    // Guard against a crafted name escaping the features directory before
    // anything is removed. `is_kebab_case` already forbids `/` and `.`,
    // this is the belt-and-braces check every path-taking command uses.
    orchestrator_dir::assert_within(&feature_dir, &docs_root.join("features"))?;

    // The work product goes first: if this fails, nothing else has been
    // touched and the feature is still coherent.
    std::fs::remove_dir_all(&feature_dir)?;

    // Bookkeeping is best-effort from here — a leftover log directory is
    // harmless noise, and failing the whole command after the docs are
    // already gone would leave the user with no way to finish the job.
    let _ = std::fs::remove_dir_all(orchestrator_dir::agent_runs_dir(&agents_root).join(&name));
    let _ = std::fs::remove_dir_all(orchestrator_dir::contract_lock_dir(&agents_root, &name));
    let _ = std::fs::remove_file(orchestrator_dir::design_ref_path(&agents_root, &name));
    for input_dir in input_copy_dirs(&agents_root, &name) {
        let _ = std::fs::remove_dir_all(input_dir);
    }

    // Drop the feature from `state.json` so a stale entry can't resurrect
    // it in any report that iterates the file. Guarded like every other
    // read-modify-write of this file — a concurrent recompute would
    // otherwise write the deleted feature straight back in.
    let _state_guard = orchestrator_dir::lock_state_file();
    let state_path = orchestrator_dir::state_json_path(&agents_root);
    if let Ok(raw) = std::fs::read_to_string(&state_path) {
        if let Ok(mut file) = serde_json::from_str::<StateFile>(&raw) {
            if file.features.remove(&name).is_some() {
                let _ = write_json_atomic(&state_path, &file);
            }
        }
    }

    Ok(list_feature_ids(&docs_root))
}

/// Reads `.orchestrator/pipeline.json`, creating it from the v1 default
/// template on first open (AC-E3-08 — template is fixed for MVP1, no UI to
/// edit it). Not `#[tauri::command]` itself — `get_pipeline_definition`
/// below is the IPC entry point; `commands::agentrun` also needs this to
/// resolve a slot's real `agent_name` (e.g. `qc-design` -> `qc-agent`, not
/// the naming-convention guess `qc-design-agent`) before spawning.
pub(crate) fn read_or_init_pipeline_def(agents_root: &Path) -> AppResult<PipelineDef> {
    Ok(load_pipeline_def(agents_root)?.def)
}

/// Outcome of loading `pipeline.json`, so `open_project` can tell the user
/// when their file was replaced rather than doing it behind their back.
pub(crate) struct PipelineDefLoad {
    pub def: PipelineDef,
    /// Where the superseded file was moved, when a migration happened.
    pub migrated_backup: Option<PathBuf>,
}

/// Reads `pipeline.json`, **migrating it when its `version` is behind**
/// `PIPELINE_DEF_VERSION`.
///
/// Migration is "back up, then write the current template", not a
/// field-by-field merge: there is no UI for editing this file (AC-E3-08 —
/// the template is fixed), so nothing user-authored is expected in it, and
/// the backup keeps anything hand-edited recoverable. Same
/// `<name>.bak`-then-rebuild pattern `state.json` (AC-E6-08) and
/// `config.json` (AC-E1-23) already use.
///
/// Without this, an old file kept its stale topology forever — it still
/// parsed, so nothing ever noticed.
pub(crate) fn load_pipeline_def(agents_root: &Path) -> AppResult<PipelineDefLoad> {
    let path = orchestrator_dir::pipeline_json_path(agents_root);

    if let Some(existing) = std::fs::read_to_string(&path)
        .ok()
        .and_then(|raw| serde_json::from_str::<PipelineDef>(&raw).ok())
    {
        if existing.version >= PIPELINE_DEF_VERSION {
            return Ok(PipelineDefLoad {
                def: existing,
                migrated_backup: None,
            });
        }

        let backup = path.with_file_name(format!("pipeline.json.v{}.bak", existing.version));
        let migrated_backup = std::fs::rename(&path, &backup).ok().map(|()| backup);
        let def = PipelineDef::default();
        write_json_atomic(&path, &def)?;
        return Ok(PipelineDefLoad {
            def,
            migrated_backup,
        });
    }

    let def = PipelineDef::default();
    write_json_atomic(&path, &def)?;
    Ok(PipelineDefLoad {
        def,
        migrated_backup: None,
    })
}

#[tauri::command]
pub fn get_pipeline_definition(state: State<AppState>) -> AppResult<PipelineDef> {
    let project = current_project(&state)?;
    read_or_init_pipeline_def(Path::new(&project.agents_root))
}

/// Wraps `FeatureState` with the same non-fatal `warnings` shape
/// `EVENT_STATE_CHANGED` already carries (AC-E3-06 / AC-E6-08), so the
/// initial request/response load and the watcher's push updates never
/// disagree about what warnings look like.
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PipelineStateResult {
    pub state: FeatureState,
    pub warnings: Vec<String>,
}

#[tauri::command]
pub fn get_pipeline_state(
    state: State<AppState>,
    feature: String,
) -> AppResult<PipelineStateResult> {
    orchestrator_dir::validate_feature_id(&feature)?;
    let project = current_project(&state)?;
    let ecosystem = state.ecosystem.lock().unwrap().clone();
    let (mut result, warnings) = compute_and_persist(
        Path::new(&project.agents_root),
        Path::new(&project.docs_root),
        &feature,
        &ecosystem,
    )?;
    mark_running_on_old_contract(&state, &feature, &mut result);
    Ok(PipelineStateResult {
        state: result,
        warnings,
    })
}

/// Shortens an absolute artifact path to something readable inline in the
/// node detail panel — relative to whichever of `feature_dir`/`runs_dir` it
/// falls under, falling back to the file name alone.
fn relative_label(path: &Path, feature_dir: &Path, runs_dir: &Path) -> String {
    if let Ok(rel) = path.strip_prefix(feature_dir) {
        return rel.display().to_string();
    }
    if let Ok(rel) = path.strip_prefix(runs_dir) {
        return format!("runs/{}", rel.display());
    }
    path.file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_else(|| path.display().to_string())
}

fn file_modified_rfc3339(path: &Path) -> Option<String> {
    let modified = std::fs::metadata(path).ok()?.modified().ok()?;
    Some(chrono::DateTime::<chrono::Utc>::from(modified).to_rfc3339())
}

#[tauri::command]
pub fn get_node_detail(
    state: State<AppState>,
    feature: String,
    slot_id: String,
) -> AppResult<NodeDetail> {
    orchestrator_dir::validate_run_ids(&feature, &slot_id)?;
    let project = current_project(&state)?;
    let feature_dir = Path::new(&project.docs_root)
        .join("features")
        .join(&feature);
    let runs_dir = orchestrator_dir::runs_dir(Path::new(&project.agents_root));

    let paths = stage_rules::artifact_paths_for_slot(&feature_dir, &runs_dir, &slot_id);

    let artifacts: Vec<ArtifactRef> = paths
        .iter()
        .map(|path| ArtifactRef {
            path: path.display().to_string(),
            label: relative_label(path, &feature_dir, &runs_dir),
        })
        .collect();

    let updated_at = paths
        .iter()
        .filter_map(|path| file_modified_rfc3339(path))
        .max();

    let cost_usd = crate::agentrun::run_log::read_run_summary(
        Path::new(&project.agents_root),
        &feature,
        &slot_id,
    )
    .map(|summary| summary.cost_usd);

    Ok(NodeDetail {
        artifacts,
        updated_at,
        cost_usd,
    })
}

/// Idempotent: replaces whatever was being watched before (dropping the
/// old `Debouncer` stops it) with a watch on `feature`. Bumps
/// `watch_generation` first — this invalidates any in-flight
/// reconnect-with-backoff attempt (AC-E3-07) from a watch the caller is
/// superseding, so it can never clobber the one started here.
#[tauri::command]
pub fn start_watching(app: AppHandle, state: State<AppState>, feature: String) -> AppResult<()> {
    orchestrator_dir::validate_feature_id(&feature)?;
    let project = current_project(&state)?;
    let agents_root: PathBuf = project.agents_root.into();
    let docs_root: PathBuf = project.docs_root.into();

    state
        .watch_generation
        .fetch_add(1, std::sync::atomic::Ordering::SeqCst);

    let new_watcher =
        watcher::start(app, agents_root, docs_root, feature).map_err(|err| AppError::Invalid {
            message: format!("không thể bắt đầu theo dõi thư mục feature: {err}"),
        })?;

    *state.watcher.lock().unwrap() = Some(new_watcher);
    Ok(())
}

#[tauri::command]
pub fn stop_watching(state: State<AppState>) -> AppResult<()> {
    // Bump first so a reconnect attempt in flight for the watch being
    // stopped notices it's stale and gives up instead of silently
    // resurrecting a watch the caller explicitly asked to stop.
    state
        .watch_generation
        .fetch_add(1, std::sync::atomic::Ordering::SeqCst);
    // Assigning `None` drops the previous `Debouncer`, which stops it.
    *state.watcher.lock().unwrap() = None;
    Ok(())
}

/// AC-E4-19/20 — every Lock/Re-lock ever made for this feature, newest
/// first, content included (not just checksums) so a prior lock's files
/// can be viewed exactly as they were at that moment.
#[tauri::command]
pub fn list_contract_locks(
    state: State<AppState>,
    feature: String,
) -> AppResult<Vec<ContractLockRecord>> {
    orchestrator_dir::validate_feature_id(&feature)?;
    let project = current_project(&state)?;
    let dir = orchestrator_dir::contract_lock_dir(Path::new(&project.agents_root), &feature);
    Ok(contract_lock_store::list_locks(&dir))
}

/// AC-E4-26 — every violation ever detected for this feature, newest
/// first, including ones that have since self-healed (a healed violation
/// no longer shows in `ContractLockState.violatedFiles`, but its event
/// stays here permanently).
#[tauri::command]
pub fn list_contract_violations(
    state: State<AppState>,
    feature: String,
) -> AppResult<Vec<crate::domain::contract_lock::ViolationEvent>> {
    orchestrator_dir::validate_feature_id(&feature)?;
    let project = current_project(&state)?;
    let dir =
        orchestrator_dir::contract_lock_violations_dir(Path::new(&project.agents_root), &feature);
    Ok(contract_lock_store::list_violation_events(&dir))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn creates_the_feature_directory_and_returns_the_refreshed_list() {
        let tmp = tempfile::tempdir().unwrap();
        std::fs::create_dir_all(tmp.path().join("features/existing-one")).unwrap();

        let features = create_feature_dir(tmp.path(), "user-login").unwrap();

        assert!(tmp.path().join("features/user-login").is_dir());
        assert_eq!(features, vec!["existing-one", "user-login"]);
    }

    #[test]
    fn rejects_a_name_that_is_not_kebab_case_without_creating_anything() {
        let tmp = tempfile::tempdir().unwrap();
        for bad in ["User Login", "user_login", "-lead", "trail-", "a--b", ""] {
            assert!(
                create_feature_dir(tmp.path(), bad).is_err(),
                "{bad} should be rejected"
            );
        }
        assert!(!tmp.path().join("features").exists());
    }

    /// Silently reusing an existing directory would look like "created" but
    /// drop the user into a feature that already has work in it.
    #[test]
    fn refuses_a_name_that_already_exists() {
        let tmp = tempfile::tempdir().unwrap();
        create_feature_dir(tmp.path(), "user-login").unwrap();

        let err = create_feature_dir(tmp.path(), "user-login").unwrap_err();
        assert!(err.to_string().contains("đã tồn tại"));
    }

    #[test]
    fn trims_surrounding_whitespace_before_validating() {
        let tmp = tempfile::tempdir().unwrap();
        create_feature_dir(tmp.path(), "  user-login  ").unwrap();
        assert!(tmp.path().join("features/user-login").is_dir());
    }

    /// The inventory the confirm dialog is built from — it has to name the
    /// real deliverables, because that is the whole point of showing it
    /// before an irreversible delete.
    #[test]
    fn deletion_preview_counts_docs_runs_and_input_copies() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let docs_root = tmp.path().join("docs");

        let feature_dir = docs_root.join("features/user-signup");
        std::fs::create_dir_all(feature_dir.join("api-repo/tasks")).unwrap();
        std::fs::write(feature_dir.join("SPEC.md"), "spec").unwrap();
        std::fs::write(feature_dir.join("api-repo/DESIGN.md"), "design").unwrap();
        std::fs::write(feature_dir.join("api-repo/tasks/task-1-1.md"), "task").unwrap();

        std::fs::create_dir_all(
            orchestrator_dir::agent_runs_dir(&agents_root).join("user-signup/ba"),
        )
        .unwrap();
        std::fs::create_dir_all(
            orchestrator_dir::agent_runs_dir(&agents_root).join("user-signup/techlead-design"),
        )
        .unwrap();
        std::fs::create_dir_all(orchestrator_dir::contract_lock_dir(
            &agents_root,
            "user-signup",
        ))
        .unwrap();
        std::fs::create_dir_all(
            orchestrator_dir::inputs_dir(&agents_root).join("20260818T032139674Z-user-signup"),
        )
        .unwrap();
        // A different feature's input must not be counted.
        std::fs::create_dir_all(
            orchestrator_dir::inputs_dir(&agents_root).join("20260814T000000000Z-user-login"),
        )
        .unwrap();

        let preview = deletion_preview(&agents_root, &docs_root, "user-signup", Vec::new());

        assert_eq!(preview.doc_file_count, 3);
        assert_eq!(
            preview.notable_artifacts,
            vec![
                "SPEC.md",
                "api-repo/DESIGN.md",
                "api-repo/tasks/task-1-1.md"
            ]
        );
        assert_eq!(preview.run_count, 2);
        assert!(preview.has_contract_lock);
        assert_eq!(preview.input_copy_count, 1);
    }

    /// Cost accounting is cross-feature and must outlive the feature —
    /// same rule AC-E6-28 already imposes on clearing logs.
    #[test]
    fn delete_removes_docs_and_bookkeeping_but_keeps_run_history() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let docs_root = tmp.path().join("docs");

        std::fs::create_dir_all(docs_root.join("features/user-signup")).unwrap();
        std::fs::write(docs_root.join("features/user-signup/SPEC.md"), "spec").unwrap();
        std::fs::create_dir_all(docs_root.join("features/user-login")).unwrap();

        std::fs::create_dir_all(
            orchestrator_dir::agent_runs_dir(&agents_root).join("user-signup/ba"),
        )
        .unwrap();
        std::fs::create_dir_all(
            orchestrator_dir::inputs_dir(&agents_root).join("20260818T0Z-user-signup"),
        )
        .unwrap();
        let history_dir = orchestrator_dir::run_history_dir(&agents_root);
        std::fs::create_dir_all(&history_dir).unwrap();
        std::fs::write(history_dir.join("20260818T0Z.json"), "{}").unwrap();

        // Mirrors what `delete_feature` does once its guards have passed.
        std::fs::remove_dir_all(docs_root.join("features/user-signup")).unwrap();
        let _ = std::fs::remove_dir_all(
            orchestrator_dir::agent_runs_dir(&agents_root).join("user-signup"),
        );
        for dir in input_copy_dirs(&agents_root, "user-signup") {
            std::fs::remove_dir_all(dir).unwrap();
        }

        assert_eq!(list_feature_ids(&docs_root), vec!["user-login"]);
        assert!(!orchestrator_dir::agent_runs_dir(&agents_root)
            .join("user-signup")
            .exists());
        assert!(input_copy_dirs(&agents_root, "user-signup").is_empty());
        // The cost record survives.
        assert!(history_dir.join("20260818T0Z.json").is_file());
    }

    #[test]
    fn input_copy_dirs_matches_only_the_feature_suffix() {
        let tmp = tempfile::tempdir().unwrap();
        let inputs = orchestrator_dir::inputs_dir(tmp.path());
        for name in [
            "20260818T0Z-user-signup",
            "20260818T1Z-user-signup",
            "20260818T2Z-user-signup-v2",
            "20260818T3Z-signup",
        ] {
            std::fs::create_dir_all(inputs.join(name)).unwrap();
        }

        let found = input_copy_dirs(tmp.path(), "user-signup");
        assert_eq!(
            found.len(),
            2,
            "only exact `-user-signup` suffixes: {found:?}"
        );
    }

    /// The bug this exists for: a `pipeline.json` written before the
    /// Trigger gate existed still parsed, so the project kept an 8-stage
    /// topology with no gate and every `depends_on` empty — forever.
    #[test]
    fn an_older_pipeline_json_is_backed_up_and_replaced_with_the_current_template() {
        let tmp = tempfile::tempdir().unwrap();
        let path = orchestrator_dir::pipeline_json_path(tmp.path());
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        // Shape of the real stale file: no `version`, no gate stage, no
        // `dependsOn` anywhere.
        std::fs::write(
            &path,
            r#"{"stages":[{"id":"S1_input","label":"① Input","agents":[{"id":"ba","agentName":"ba-agent","afterSlots":[]}]},{"id":"S2_design","label":"② Design","agents":[]}]}"#,
        )
        .unwrap();

        let load = load_pipeline_def(tmp.path()).unwrap();

        assert_eq!(load.def.version, PIPELINE_DEF_VERSION);
        assert!(
            load.def
                .stages
                .iter()
                .any(|s| s.id == crate::domain::pipeline_def::gate::TRIGGER),
            "the migrated template must bring the Trigger gate back"
        );
        assert!(
            load.def.stages.iter().any(|s| s.depends_on.is_some()),
            "and the explicit stage dependencies"
        );

        // The superseded file is kept, not silently destroyed.
        let backup = load
            .migrated_backup
            .expect("a migration must report its backup");
        assert!(backup.is_file());
        assert!(backup.to_string_lossy().ends_with("pipeline.json.v0.bak"));

        // Written back to disk, so the next read is already current.
        let reread = load_pipeline_def(tmp.path()).unwrap();
        assert!(
            reread.migrated_backup.is_none(),
            "migration must not repeat"
        );
        assert_eq!(reread.def.version, PIPELINE_DEF_VERSION);
    }

    /// The path every project on the previous build actually takes: a v2
    /// file already has both gates and `dependsOn`, so nothing about it
    /// looks stale — it just has no slot `label`, which left the board
    /// drawing two nodes both reading `qc-agent`.
    #[test]
    fn a_v2_pipeline_json_is_migrated_so_slots_gain_their_labels() {
        let tmp = tempfile::tempdir().unwrap();
        let path = orchestrator_dir::pipeline_json_path(tmp.path());
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        // A real v2 file: serialize the current template, then strip the
        // field v2 never had and stamp it back to version 2.
        let mut v2 = serde_json::to_value(PipelineDef::default()).unwrap();
        v2["version"] = serde_json::json!(2);
        for stage in v2["stages"].as_array_mut().unwrap() {
            for agent in stage["agents"].as_array_mut().unwrap() {
                agent.as_object_mut().unwrap().remove("label");
            }
        }
        std::fs::write(&path, serde_json::to_string(&v2).unwrap()).unwrap();

        let load = load_pipeline_def(tmp.path()).unwrap();

        assert_eq!(load.def.version, PIPELINE_DEF_VERSION);
        assert!(load
            .migrated_backup
            .expect("a migration must report its backup")
            .to_string_lossy()
            .ends_with("pipeline.json.v2.bak"));

        // Every slot now carries the display label v2 files never had.
        let labels: Vec<String> = load
            .def
            .stages
            .iter()
            .flat_map(|s| &s.agents)
            .map(|a| a.label.clone().expect("every slot is labelled"))
            .collect();
        assert!(!labels.is_empty());
        let unique: std::collections::BTreeSet<&String> = labels.iter().collect();
        assert_eq!(unique.len(), labels.len(), "labels must stay distinct");
    }

    /// The path every project on the previous build takes now: a v3 file
    /// is structurally current but still declares the `pm` slot, which no
    /// longer has an agent behind it.
    #[test]
    fn a_v3_pipeline_json_is_migrated_so_the_pm_slot_disappears() {
        let tmp = tempfile::tempdir().unwrap();
        let path = orchestrator_dir::pipeline_json_path(tmp.path());
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        // A real v3 file: serialize the current template, stamp it back to
        // version 3, and splice the removed slot into stage ③.
        let mut v3 = serde_json::to_value(PipelineDef::default()).unwrap();
        v3["version"] = serde_json::json!(3);
        for stage in v3["stages"].as_array_mut().unwrap() {
            if stage["id"] == "S3_planning" {
                stage["agents"]
                    .as_array_mut()
                    .unwrap()
                    .push(serde_json::json!({
                        "id": "pm",
                        "agentName": "pm-agent",
                        "label": "PM · Plan",
                        "afterSlots": [],
                    }));
            }
        }
        std::fs::write(&path, serde_json::to_string(&v3).unwrap()).unwrap();

        let load = load_pipeline_def(tmp.path()).unwrap();

        assert_eq!(load.def.version, PIPELINE_DEF_VERSION);
        assert!(load
            .migrated_backup
            .expect("a migration must report its backup")
            .to_string_lossy()
            .ends_with("pipeline.json.v3.bak"));
        assert!(
            !load
                .def
                .stages
                .iter()
                .flat_map(|s| &s.agents)
                .any(|a| a.id == "pm" || a.agent_name == "pm-agent"),
            "the pm slot must be gone after migration"
        );
    }

    /// The path every project on the previous build takes now: a v4 file is
    /// structurally current but still declares stage ⑥ Verify (slot `qa`)
    /// and the `qc-testing` slot, both dropped from the pipeline.
    #[test]
    fn a_v4_pipeline_json_is_migrated_so_the_qa_and_qc_testing_slots_disappear() {
        let tmp = tempfile::tempdir().unwrap();
        let path = orchestrator_dir::pipeline_json_path(tmp.path());
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        // A real v4 file: serialize the current template, stamp it back to
        // version 4, and splice the removed stage/slot back in.
        let mut v4 = serde_json::to_value(PipelineDef::default()).unwrap();
        v4["version"] = serde_json::json!(4);
        for stage in v4["stages"].as_array_mut().unwrap() {
            if stage["id"] == "S6_testing" {
                stage["agents"].as_array_mut().unwrap().insert(
                    0,
                    serde_json::json!({
                        "id": "qc-testing",
                        "agentName": "qc-agent",
                        "label": "QC · Execution",
                        "afterSlots": [],
                    }),
                );
            }
        }
        v4["stages"].as_array_mut().unwrap().insert(
            6,
            serde_json::json!({
                "id": "S6_verify",
                "label": "⑥ Verify",
                "agents": [{
                    "id": "qa",
                    "agentName": "qa-agent",
                    "label": "QA · Verify",
                    "afterSlots": [],
                }],
                "dependsOn": "S5_build",
            }),
        );
        std::fs::write(&path, serde_json::to_string(&v4).unwrap()).unwrap();

        let load = load_pipeline_def(tmp.path()).unwrap();

        assert_eq!(load.def.version, PIPELINE_DEF_VERSION);
        assert!(load
            .migrated_backup
            .expect("a migration must report its backup")
            .to_string_lossy()
            .ends_with("pipeline.json.v4.bak"));
        assert!(
            !load.def.stages.iter().any(|s| s.id == "S6_verify"),
            "the Verify stage must be gone after migration"
        );
        assert!(
            !load
                .def
                .stages
                .iter()
                .flat_map(|s| &s.agents)
                .any(|a| a.id == "qa" || a.id == "qc-testing"),
            "both dropped slots must be gone after migration"
        );
    }

    #[test]
    fn a_current_pipeline_json_is_left_exactly_as_it_is() {
        let tmp = tempfile::tempdir().unwrap();
        let first = load_pipeline_def(tmp.path()).unwrap();
        assert!(first.migrated_backup.is_none(), "creating is not migrating");

        let second = load_pipeline_def(tmp.path()).unwrap();
        assert!(second.migrated_backup.is_none());
        assert_eq!(second.def.stages.len(), first.def.stages.len());
    }
}
