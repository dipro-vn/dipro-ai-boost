use std::path::{Path, PathBuf};

use tauri::State;

use crate::agentrun::import_filter::{to_pattern_path, ImportFilter};
use crate::app_state::AppState;
use crate::domain::artifact::ArtifactContent;
use crate::domain::project::ProjectPaths;
use crate::domain::version_ref::{DiffResult, VersionRef, VersionSource};
use crate::error::{AppError, AppResult};
use crate::gitutil::git_source;
use crate::store::orchestrator_dir::assert_within_any;
use crate::store::snapshot;

const CURRENT_VERSION_ID: &str = "current";

/// Generous for text/markdown/code, small enough to never stall the IPC
/// thread on a large binary/log/lockfile — a class of file `docsRoot`
/// never realistically contained but `repositoryRoot` (browsable via the
/// folder explorer) can.
const MAX_PREVIEW_BYTES: u64 = 2 * 1024 * 1024;

/// Refuses to return content for a path matching the open project's own
/// restricted-paths config — defense in depth independent of any UI-level
/// check (e.g. the folder explorer disabling a click), so a `.env`/key
/// file is never readable through this command no matter how `path` was
/// supplied. Checked against whichever of the 3 roots `canonical` is
/// actually under.
fn assert_not_restricted(project: &ProjectPaths, canonical: &Path) -> AppResult<()> {
    let filter = ImportFilter::for_project(Path::new(&project.agents_root));
    for root_str in [
        &project.agents_root,
        &project.docs_root,
        &project.repository_root,
    ] {
        let Ok(canonical_root) = dunce::canonicalize(Path::new(root_str)) else {
            continue;
        };
        if let Ok(rel) = canonical.strip_prefix(&canonical_root) {
            if let Some(reason) = filter.exclusion_reason(&to_pattern_path(rel)) {
                return Err(AppError::RestrictedPath {
                    path: canonical.display().to_string(),
                    reason,
                });
            }
            break;
        }
    }
    Ok(())
}

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

/// Resolves `path` (frontend-supplied, untrusted) to a canonical path
/// guaranteed to be within the open project — every diff/version command
/// goes through this, same as `read_artifact`.
fn resolve_and_guard(state: &State<AppState>, path: &str) -> AppResult<(ProjectPaths, PathBuf)> {
    let project = current_project(state)?;
    let requested = PathBuf::from(path);
    let agents_root = Path::new(&project.agents_root);
    let docs_root = Path::new(&project.docs_root);
    let repository_root = Path::new(&project.repository_root);
    let canonical = assert_within_any(&requested, &[agents_root, docs_root, repository_root])?;
    Ok((project, canonical))
}

/// Reads any text artifact under the currently open project. `path` comes
/// from the frontend (a value the user ultimately clicked, e.g. from
/// `NodeDetail.artifacts`), so it is NEVER trusted without the path-guard —
/// this is the one command in MVP1 where an unchecked path could read
/// anything on disk the app's process can see.
#[tauri::command]
pub fn read_artifact(state: State<AppState>, path: String) -> AppResult<ArtifactContent> {
    let (project, canonical) = resolve_and_guard(&state, &path)?;

    if !canonical.is_file() {
        return Err(AppError::Invalid {
            message: format!("Không phải file: {}", canonical.display()),
        });
    }

    assert_not_restricted(&project, &canonical)?;

    let size_bytes = std::fs::metadata(&canonical)?.len();
    if size_bytes > MAX_PREVIEW_BYTES {
        return Err(AppError::Invalid {
            message: format!(
                "File quá lớn để xem trước ({} MB, giới hạn {} MB)",
                size_bytes / 1_000_000,
                MAX_PREVIEW_BYTES / 1_000_000
            ),
        });
    }

    let content = std::fs::read_to_string(&canonical)?;
    let line_count = content.lines().count();

    Ok(ArtifactContent {
        content,
        size_bytes,
        line_count,
    })
}

fn synthetic_current_version() -> VersionRef {
    VersionRef {
        id: CURRENT_VERSION_ID.to_string(),
        label: "Hiện tại".to_string(),
        source: VersionSource::Current,
        timestamp: chrono::Utc::now().to_rfc3339(),
    }
}

/// Lists versions available to diff for one artifact — always starts with
/// a synthetic "current" entry read straight from disk, followed by either
/// real git history OR local snapshot history, whichever backs this
/// specific artifact (never both — a file is either inside a git repo or
/// it isn't). AC-E3-21.
#[tauri::command]
pub fn list_artifact_versions(state: State<AppState>, path: String) -> AppResult<Vec<VersionRef>> {
    let (project, canonical) = resolve_and_guard(&state, &path)?;

    let mut versions = vec![synthetic_current_version()];

    if git_source::is_git_tracked(&canonical) {
        versions.extend(git_source::list_git_versions(&canonical)?);
    } else {
        let dir = snapshot::snapshot_dir(Path::new(&project.agents_root), &canonical);
        versions.extend(snapshot::list_snapshot_versions(&dir));
    }

    Ok(versions)
}

/// Returns full content for both `from_id` and `to_id` — the frontend
/// (`react-diff-viewer-continued`) computes the visual diff itself; Rust's
/// only job here is fetching the right two blobs of text.
#[tauri::command]
pub fn diff_artifact(
    state: State<AppState>,
    path: String,
    from_id: String,
    to_id: String,
) -> AppResult<DiffResult> {
    let (project, canonical) = resolve_and_guard(&state, &path)?;
    let is_git = git_source::is_git_tracked(&canonical);
    let source = if is_git {
        VersionSource::Git
    } else {
        VersionSource::Snapshot
    };

    let read_version = |id: &str| -> AppResult<String> {
        if id == CURRENT_VERSION_ID {
            return Ok(std::fs::read_to_string(&canonical)?);
        }
        if is_git {
            git_source::read_at_commit(&canonical, id)
        } else {
            let dir = snapshot::snapshot_dir(Path::new(&project.agents_root), &canonical);
            snapshot::read_snapshot(&dir, id)
        }
    };

    Ok(DiffResult {
        from_content: read_version(&from_id)?,
        to_content: read_version(&to_id)?,
        source,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    /// `read_artifact`'s actual command wrapper needs a live `AppState`
    /// (Tauri `State<T>` can't be constructed outside a running app), so
    /// this exercises the same path-guard composition it uses —
    /// `assert_within_any` over the 3 project roots — directly, the same
    /// way the command does internally. Full command-level coverage is
    /// exercised manually via T1.7 against a real project.
    #[test]
    fn path_within_any_of_the_3_roots_is_allowed() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let docs_root = tmp.path().join("docs");
        let repository_root = tmp.path().join("repos");
        std::fs::create_dir_all(&agents_root).unwrap();
        std::fs::create_dir_all(&docs_root).unwrap();
        std::fs::create_dir_all(&repository_root).unwrap();

        let spec = docs_root.join("features/f1/SPEC.md");
        std::fs::create_dir_all(spec.parent().unwrap()).unwrap();
        std::fs::write(&spec, "# SPEC").unwrap();

        assert!(assert_within_any(&spec, &[&agents_root, &docs_root, &repository_root]).is_ok());
    }

    #[test]
    fn path_outside_all_3_roots_is_rejected() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let docs_root = tmp.path().join("docs");
        let repository_root = tmp.path().join("repos");
        std::fs::create_dir_all(&agents_root).unwrap();
        std::fs::create_dir_all(&docs_root).unwrap();
        std::fs::create_dir_all(&repository_root).unwrap();

        let outside_dir = tmp.path().join("elsewhere");
        std::fs::create_dir_all(&outside_dir).unwrap();
        let secret = outside_dir.join("secret.md");
        std::fs::write(&secret, "should never be readable").unwrap();

        assert!(assert_within_any(&secret, &[&agents_root, &docs_root, &repository_root]).is_err());
    }

    #[test]
    fn assert_not_restricted_rejects_env_file_under_repository_root() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let repository_root = tmp.path().join("repos");
        std::fs::create_dir_all(&agents_root).unwrap();
        let env_file = repository_root.join("service/.env");
        std::fs::create_dir_all(env_file.parent().unwrap()).unwrap();
        std::fs::write(&env_file, "SECRET=1").unwrap();

        let project = ProjectPaths {
            agents_root: agents_root.display().to_string(),
            docs_root: tmp.path().join("docs").display().to_string(),
            repository_root: repository_root.display().to_string(),
        };
        let canonical = dunce::canonicalize(&env_file).unwrap();

        let err = assert_not_restricted(&project, &canonical).unwrap_err();
        assert!(matches!(err, AppError::RestrictedPath { .. }));
    }

    #[test]
    fn assert_not_restricted_allows_ordinary_file() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let repository_root = tmp.path().join("repos");
        std::fs::create_dir_all(&agents_root).unwrap();
        let readme = repository_root.join("README.md");
        std::fs::create_dir_all(readme.parent().unwrap()).unwrap();
        std::fs::write(&readme, "# hi").unwrap();

        let project = ProjectPaths {
            agents_root: agents_root.display().to_string(),
            docs_root: tmp.path().join("docs").display().to_string(),
            repository_root: repository_root.display().to_string(),
        };
        let canonical = dunce::canonicalize(&readme).unwrap();

        assert!(assert_not_restricted(&project, &canonical).is_ok());
    }
}
