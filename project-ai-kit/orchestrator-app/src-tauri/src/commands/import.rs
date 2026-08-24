use std::path::{Path, PathBuf};

use tauri::State;

use crate::agentrun::import_filter::{to_pattern_path, ImportFilter};
use crate::app_state::AppState;
use crate::domain::import::{ExcludedFile, ImportPreview, ImportedRun};
use crate::domain::project::ProjectPaths;
use crate::error::{AppError, AppResult};
use crate::store::orchestrator_dir;

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

/// Depth-first, relative to `root`. Read errors on a subdirectory (e.g. a
/// broken symlink) are skipped rather than failing the whole walk — one bad
/// entry shouldn't block importing everything else.
fn walk_relative_files(root: &Path) -> Vec<PathBuf> {
    fn walk(dir: &Path, root: &Path, out: &mut Vec<PathBuf>) {
        let Ok(entries) = std::fs::read_dir(dir) else {
            return;
        };
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                walk(&path, root, out);
            } else if let Ok(rel) = path.strip_prefix(root) {
                out.push(rel.to_path_buf());
            }
        }
    }
    let mut out = Vec::new();
    walk(root, root, &mut out);
    out.sort();
    out
}

fn compute_preview(source: &Path, filter: &ImportFilter) -> AppResult<ImportPreview> {
    if !source.is_dir() {
        return Err(AppError::Invalid {
            message: format!("{} không phải một thư mục tồn tại", source.display()),
        });
    }

    let mut included = Vec::new();
    let mut excluded = Vec::new();
    for rel in walk_relative_files(source) {
        let rel_str = to_pattern_path(&rel);
        match filter.exclusion_reason(&rel_str) {
            Some(reason) => excluded.push(ExcludedFile {
                relative_path: rel_str,
                reason,
            }),
            None => included.push(rel_str),
        }
    }
    Ok(ImportPreview { included, excluded })
}

/// AC-E2-22 — shown to the user before they confirm. Read-only: never
/// touches `source_folder` itself (AC-E2-31).
#[tauri::command]
pub fn preview_import(state: State<AppState>, source_folder: String) -> AppResult<ImportPreview> {
    let project = current_project(&state)?;
    let filter = ImportFilter::for_project(Path::new(&project.agents_root));
    compute_preview(Path::new(&source_folder), &filter)
}

const FEATURE_NAME_MAX_LEN: usize = 100;

/// kebab-case: lowercase ASCII letters, digits, single hyphens between
/// segments — no leading/trailing/doubled hyphens (AC-E2-24).
///
/// `pub(crate)` so `commands::pipeline::create_feature` validates a typed
/// feature name with the exact same rule an imported one goes through —
/// two definitions would drift and let the sidebar create a directory the
/// import path would later reject.
///
/// Note this doubles as the path-safety guarantee for anything that joins
/// a feature name onto a root: the allowed character set excludes `/`,
/// `\`, and `.`, so `..` traversal is impossible by construction.
pub(crate) fn is_kebab_case(name: &str) -> bool {
    !name.is_empty()
        && name.len() <= FEATURE_NAME_MAX_LEN
        && name
            .chars()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-')
        && !name.starts_with('-')
        && !name.ends_with('-')
        && !name.contains("--")
}

/// Validates the feature name, re-runs the same preview `preview_import`
/// showed (so what gets copied always matches what the user confirmed —
/// never trusts a preview the frontend cached earlier), copies every
/// included file into `.orchestrator/inputs/<run-id>/`, and creates
/// `<docsRoot>/features/<feature_name>/` so the feature appears on the
/// Pipeline Board immediately (AC-E3-01 already treats an empty feature
/// directory as a valid, just-created feature). Takes already-resolved
/// paths (not `State`) so it's directly testable — the command wrapper
/// below just resolves the currently open project first.
fn perform_import(
    agents_root: &Path,
    docs_root: &Path,
    source: &Path,
    feature_name: &str,
    filter: &ImportFilter,
) -> AppResult<ImportedRun> {
    if !is_kebab_case(feature_name) {
        return Err(AppError::Invalid {
            message: format!(
                "Tên feature phải là kebab-case (chữ thường, số, dấu -): \"{feature_name}\""
            ),
        });
    }

    let preview = compute_preview(source, filter)?;
    if preview.included.is_empty() {
        return Err(AppError::Invalid {
            message: "Folder rỗng hoặc không có file nào đọc được — không tạo run".to_string(),
        });
    }

    let run_id = format!(
        "{}-{feature_name}",
        chrono::Utc::now().format("%Y%m%dT%H%M%S%3fZ")
    );
    let dest_root = orchestrator_dir::inputs_dir(agents_root).join(&run_id);

    for rel in &preview.included {
        let src_file = source.join(rel);
        let dest_file = dest_root.join(rel);
        if let Some(parent) = dest_file.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::copy(&src_file, &dest_file)?;
    }

    std::fs::create_dir_all(docs_root.join("features").join(feature_name))?;

    Ok(ImportedRun {
        run_id,
        copied_path: dest_root.display().to_string(),
        feature_name: feature_name.to_string(),
        files: preview.included,
    })
}

#[tauri::command]
pub fn import_folder(
    state: State<AppState>,
    source_folder: String,
    feature_name: String,
) -> AppResult<ImportedRun> {
    let project = current_project(&state)?;
    let agents_root = Path::new(&project.agents_root);
    let docs_root = Path::new(&project.docs_root);
    let filter = ImportFilter::for_project(agents_root);
    perform_import(
        agents_root,
        docs_root,
        Path::new(&source_folder),
        &feature_name,
        &filter,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    fn write(path: &Path, content: &str) {
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, content).unwrap();
    }

    #[test]
    fn kebab_case_validation() {
        assert!(is_kebab_case("user-login"));
        assert!(is_kebab_case("payment-checkout-2"));
        assert!(!is_kebab_case(""));
        assert!(!is_kebab_case("User-Login"));
        assert!(!is_kebab_case("user_login"));
        assert!(!is_kebab_case("-user-login"));
        assert!(!is_kebab_case("user-login-"));
        assert!(!is_kebab_case("user--login"));
        assert!(!is_kebab_case("user login"));
    }

    #[test]
    fn compute_preview_splits_included_and_excluded_with_reasons() {
        let tmp = tempfile::tempdir().unwrap();
        let source = tmp.path().join("source");
        write(&source.join("brief.md"), "content");
        write(&source.join("secrets/.env"), "SECRET=1");

        let filter = ImportFilter::for_project(tmp.path()); // no restricted-paths.json -> builtin fallback
        let preview = compute_preview(&source, &filter).unwrap();

        assert_eq!(preview.included, vec!["brief.md".to_string()]);
        assert_eq!(preview.excluded.len(), 1);
        assert_eq!(preview.excluded[0].relative_path, "secrets/.env");
    }

    #[test]
    fn compute_preview_rejects_a_source_that_is_not_a_directory() {
        let tmp = tempfile::tempdir().unwrap();
        let not_a_dir = tmp.path().join("file.txt");
        write(&not_a_dir, "x");

        let filter = ImportFilter::for_project(tmp.path());
        assert!(compute_preview(&not_a_dir, &filter).is_err());
    }

    #[test]
    fn perform_import_rejects_a_non_kebab_case_feature_name() {
        let tmp = tempfile::tempdir().unwrap();
        let source = tmp.path().join("source");
        write(&source.join("brief.md"), "content");
        let filter = ImportFilter::for_project(tmp.path());

        let err = perform_import(
            tmp.path(),
            &tmp.path().join("docs"),
            &source,
            "User Login",
            &filter,
        )
        .unwrap_err();
        assert!(matches!(err, AppError::Invalid { .. }));
    }

    #[test]
    fn perform_import_rejects_a_folder_with_nothing_readable_without_copying_anything() {
        let tmp = tempfile::tempdir().unwrap();
        let source = tmp.path().join("source");
        // Only a secret file — nothing survives filtering (AC-E2-30).
        write(&source.join(".env"), "SECRET=1");
        let filter = ImportFilter::for_project(tmp.path());

        let err = perform_import(
            tmp.path(),
            &tmp.path().join("docs"),
            &source,
            "user-login",
            &filter,
        )
        .unwrap_err();
        assert!(matches!(err, AppError::Invalid { .. }));
        assert!(!orchestrator_dir::inputs_dir(tmp.path()).exists());
    }

    #[test]
    fn perform_import_copies_included_files_and_creates_the_feature_dir() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents");
        let docs_root = tmp.path().join("docs");
        let source = tmp.path().join("source");
        write(&source.join("brief.md"), "please build a login page");
        write(&source.join("assets/logo.png"), "not a real image");
        write(&source.join(".env"), "SECRET=1");
        let filter = ImportFilter::for_project(&agents_root);

        let run = perform_import(&agents_root, &docs_root, &source, "user-login", &filter).unwrap();

        assert_eq!(run.feature_name, "user-login");
        assert!(run.run_id.ends_with("-user-login"));

        let copied_root = PathBuf::from(&run.copied_path);
        assert_eq!(
            std::fs::read_to_string(copied_root.join("brief.md")).unwrap(),
            "please build a login page"
        );
        assert!(copied_root.join("assets/logo.png").is_file());
        // The excluded secret must never be copied.
        assert!(!copied_root.join(".env").exists());

        // The original source is untouched (AC-E2-31).
        assert!(source.join(".env").is_file());

        assert!(docs_root.join("features/user-login").is_dir());

        // The prompt names every copied file, so the agent never has to
        // guess (it has no directory-listing tool) — and the excluded
        // secret must not appear in that list either.
        assert_eq!(run.files, vec!["assets/logo.png", "brief.md"]);
    }
}
