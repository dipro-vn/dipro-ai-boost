use std::fs::OpenOptions;
use std::path::{Component, Path, PathBuf};

use tauri::State;

use crate::agentrun::import_filter::{to_pattern_path, ImportFilter};
use crate::app_state::AppState;
use crate::domain::explorer::{DirEntry, ExplorerRootEntry};
use crate::domain::pipeline_def::slot;
use crate::domain::project::ProjectPaths;
use crate::error::{AppError, AppResult};
use crate::store::contract_lock;
use crate::store::orchestrator_dir::assert_within;

const PROTECTED_COMPONENTS: &[&str] = &[".claude", ".git", ".orchestrator"];
const MAX_DELETE_SCAN_ENTRIES: usize = 20_000;

const RUN_SLOTS: &[&str] = &[
    slot::BA,
    slot::TECHLEAD_DESIGN,
    slot::DESIGN_ANALYST,
    slot::QC_DESIGN,
    slot::TECHLEAD_TASKS,
    slot::BACKEND,
    slot::FRONTEND,
    slot::MOBILE,
    slot::QA,
    slot::QC_TESTING,
    slot::QC_AUTOMATION,
    // Legacy ids kept as literals so deleting a feature still sweeps run
    // dirs left behind by the removed `pm-agent` and Backlog push.
    "pm",
    "backlog-push",
];

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

/// The longest shared path prefix of every path given, or `None` if they
/// share nothing beyond the filesystem root itself (different drives on
/// Windows, or otherwise no common directory at all) — that case is not a
/// meaningful "project folder" to browse, so the caller falls back to
/// listing each root separately instead.
fn common_ancestor(paths: &[PathBuf]) -> Option<PathBuf> {
    let mut iter = paths.iter();
    let first = iter.next()?;
    let mut common: Vec<Component> = first.components().collect();

    for path in iter {
        let components: Vec<Component> = path.components().collect();
        let shared = common
            .iter()
            .zip(components.iter())
            .take_while(|(a, b)| a == b)
            .count();
        common.truncate(shared);
        if common.is_empty() {
            return None;
        }
    }

    // A single `RootDir` (`/`) — or a bare drive prefix on Windows — is not
    // a meaningful project root; every unrelated directory on the machine
    // would satisfy it.
    if common.len() <= 1 {
        return None;
    }
    Some(common.into_iter().collect())
}

/// The root(s) the folder explorer offers to browse — one unified
/// "Project" entry at the common ancestor of all 3 project roots when one
/// exists (the common case: `agentsRoot`/`docsRoot`/`repositoryRoot` are
/// all subdirectories of the folder the user actually opened), otherwise
/// one entry per root so nothing becomes unreachable.
fn resolve_explorer_roots(project: &ProjectPaths) -> AppResult<Vec<ExplorerRootEntry>> {
    let canonical_roots = [
        dunce::canonicalize(&project.agents_root)?,
        dunce::canonicalize(&project.docs_root)?,
        dunce::canonicalize(&project.repository_root)?,
    ];

    if let Some(common) = common_ancestor(&canonical_roots) {
        return Ok(vec![ExplorerRootEntry {
            label: "Project".to_string(),
            path: common.display().to_string(),
        }]);
    }

    Ok(vec![
        ExplorerRootEntry {
            label: "Agents/Kit".to_string(),
            path: project.agents_root.clone(),
        },
        ExplorerRootEntry {
            label: "Docs".to_string(),
            path: project.docs_root.clone(),
        },
        ExplorerRootEntry {
            label: "Repository".to_string(),
            path: project.repository_root.clone(),
        },
    ])
}

/// The folder explorer's browsable root(s) for the open project — the
/// frontend renders one tree per entry (usually just one, "the whole
/// project folder"; see `resolve_explorer_roots`).
#[tauri::command]
pub fn get_explorer_roots(state: State<AppState>) -> AppResult<Vec<ExplorerRootEntry>> {
    let project = current_project(&state)?;
    resolve_explorer_roots(&project)
}

/// Resolves `path` against whichever root(s) `resolve_explorer_roots`
/// currently exposes — always the exact same set the frontend was given,
/// so a path can never be listed without also having been an offered root
/// (or a descendant reached by expanding one). Also returns the canonical
/// form of the matched root, needed to compute a filter-relative path for
/// `ImportFilter`.
fn resolve_within_explorer_roots(
    project: &ProjectPaths,
    path: &str,
) -> AppResult<(PathBuf, PathBuf)> {
    let requested = PathBuf::from(path);
    let roots = resolve_explorer_roots(project)?;
    for entry in &roots {
        let root = Path::new(&entry.path);
        if let Ok(canonical) = assert_within(&requested, root) {
            let canonical_root = dunce::canonicalize(root)?;
            return Ok((canonical, canonical_root));
        }
    }
    Err(AppError::PathOutsideRoot {
        path: requested.display().to_string(),
    })
}

fn is_within_declared_root(project: &ProjectPaths, path: &Path) -> bool {
    [
        Path::new(&project.agents_root),
        Path::new(&project.docs_root),
        Path::new(&project.repository_root),
    ]
    .iter()
    .any(|root| assert_within(path, root).is_ok())
}

fn is_declared_root(project: &ProjectPaths, path: &Path) -> bool {
    [
        Path::new(&project.agents_root),
        Path::new(&project.docs_root),
        Path::new(&project.repository_root),
    ]
    .iter()
    .any(|root| dunce::canonicalize(root).ok().as_deref() == Some(path))
}

fn has_protected_component(path: &Path) -> bool {
    path.components().any(|component| {
        let Component::Normal(value) = component else {
            return false;
        };
        PROTECTED_COMPONENTS
            .iter()
            .any(|protected| value == std::ffi::OsStr::new(protected))
    })
}

fn is_restricted_path(filter: &ImportFilter, path: &Path, explorer_root: &Path) -> bool {
    path.strip_prefix(explorer_root)
        .ok()
        .map(|relative| {
            filter
                .exclusion_reason(&to_pattern_path(relative))
                .is_some()
        })
        .unwrap_or(true)
}

fn can_modify_path(
    project: &ProjectPaths,
    filter: &ImportFilter,
    path: &Path,
    explorer_root: &Path,
) -> bool {
    is_within_declared_root(project, path)
        && !has_protected_component(path)
        && !is_restricted_path(filter, path, explorer_root)
}

fn validate_entry_name(name: &str) -> AppResult<&str> {
    let trimmed = name.trim();
    if trimmed.is_empty()
        || trimmed == "."
        || trimmed == ".."
        || trimmed.contains('/')
        || trimmed.contains('\\')
        || trimmed.chars().any(char::is_control)
    {
        return Err(AppError::Invalid {
            message: "Tên file/folder không hợp lệ — chỉ nhập một tên đơn, không chứa path"
                .to_string(),
        });
    }

    let mut components = Path::new(trimmed).components();
    if !matches!(components.next(), Some(Component::Normal(_))) || components.next().is_some() {
        return Err(AppError::Invalid {
            message: "Tên file/folder không hợp lệ — chỉ nhập một tên đơn, không chứa path"
                .to_string(),
        });
    }

    Ok(trimmed)
}

fn resolve_modifiable_parent(
    project: &ProjectPaths,
    parent_path: &str,
) -> AppResult<(PathBuf, PathBuf, ImportFilter)> {
    let (canonical_parent, explorer_root) = resolve_within_explorer_roots(project, parent_path)?;
    if !canonical_parent.is_dir() {
        return Err(AppError::Invalid {
            message: format!("Không phải thư mục: {}", canonical_parent.display()),
        });
    }

    let filter = ImportFilter::for_project(Path::new(&project.agents_root));
    if !can_modify_path(project, &filter, &canonical_parent, &explorer_root) {
        return Err(AppError::Invalid {
            message: "Không được phép ghi vào thư mục này".to_string(),
        });
    }

    Ok((canonical_parent, explorer_root, filter))
}

fn entry_for_path(
    project: &ProjectPaths,
    filter: &ImportFilter,
    path: &Path,
    explorer_root: &Path,
) -> AppResult<DirEntry> {
    let canonical = dunce::canonicalize(path)?;
    let name = canonical
        .file_name()
        .map(|value| value.to_string_lossy().into_owned())
        .ok_or_else(|| AppError::Invalid {
            message: format!("Không lấy được tên path: {}", canonical.display()),
        })?;
    Ok(DirEntry {
        name,
        path: canonical.display().to_string(),
        is_dir: canonical.is_dir(),
        is_restricted: is_restricted_path(filter, &canonical, explorer_root),
        can_modify: can_modify_path(project, filter, &canonical, explorer_root),
    })
}

fn map_create_error(error: std::io::Error, path: &Path) -> AppError {
    if error.kind() == std::io::ErrorKind::AlreadyExists {
        AppError::Invalid {
            message: format!("File/folder đã tồn tại: {}", path.display()),
        }
    } else {
        AppError::Io(error)
    }
}

fn feature_name_for_path(project: &ProjectPaths, path: &Path) -> Option<String> {
    let features_root = dunce::canonicalize(Path::new(&project.docs_root).join("features")).ok()?;
    let relative = path.strip_prefix(features_root).ok()?;
    let first = relative.components().next()?;
    match first {
        Component::Normal(name) => Some(name.to_string_lossy().into_owned()),
        _ => None,
    }
}

fn running_slots_for_feature(state: &State<AppState>, feature: &str) -> Vec<String> {
    RUN_SLOTS
        .iter()
        .filter(|slot_id| state.is_running(feature, slot_id))
        .map(|slot_id| (*slot_id).to_string())
        .collect()
}

fn locked_files_under(project: &ProjectPaths, path: &Path) -> Vec<String> {
    let Some(feature) = feature_name_for_path(project, path) else {
        return Vec::new();
    };
    let lock_dir = crate::store::orchestrator_dir::contract_lock_dir(
        Path::new(&project.agents_root),
        &feature,
    );
    let Some(lock) = contract_lock::read_latest_lock(&lock_dir) else {
        return Vec::new();
    };
    lock.files
        .into_iter()
        .filter_map(|file| {
            let locked_path = PathBuf::from(&file.path);
            locked_path.starts_with(path).then_some(file.path)
        })
        .collect()
}

#[derive(Debug, Default)]
struct DeleteScan {
    file_count: usize,
    folder_count: usize,
    protected_paths: Vec<String>,
    symlink_paths: Vec<String>,
    scanned_entries: usize,
}

fn scan_delete_tree(
    project: &ProjectPaths,
    filter: &ImportFilter,
    explorer_root: &Path,
    directory: &Path,
    scan: &mut DeleteScan,
) -> AppResult<()> {
    for item in std::fs::read_dir(directory)?.flatten() {
        scan.scanned_entries += 1;
        if scan.scanned_entries > MAX_DELETE_SCAN_ENTRIES {
            return Err(AppError::Invalid {
                message: "Thư mục quá lớn để preview xoá trong Explorer".to_string(),
            });
        }

        let child = item.path();
        let metadata = std::fs::symlink_metadata(&child)?;
        if metadata.file_type().is_symlink() {
            scan.symlink_paths.push(child.display().to_string());
            continue;
        }

        let canonical = dunce::canonicalize(&child)?;
        let can_modify = can_modify_path(project, filter, &canonical, explorer_root);
        if !can_modify {
            scan.protected_paths.push(canonical.display().to_string());
            if metadata.is_dir() {
                scan.folder_count += 1;
            } else {
                scan.file_count += 1;
            }
            continue;
        }

        if metadata.is_dir() {
            scan.folder_count += 1;
            scan_delete_tree(project, filter, explorer_root, &canonical, scan)?;
        } else {
            scan.file_count += 1;
        }
    }
    Ok(())
}

#[derive(Debug, Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ExplorerDeletePreview {
    pub path: String,
    pub name: String,
    pub file_count: usize,
    pub folder_count: usize,
    pub running_slots: Vec<String>,
    pub locked_files: Vec<String>,
    pub protected_paths: Vec<String>,
    pub symlink_paths: Vec<String>,
}

fn resolve_deletable_folder(
    project: &ProjectPaths,
    path: &str,
) -> AppResult<(PathBuf, PathBuf, ImportFilter)> {
    let (canonical, explorer_root) = resolve_within_explorer_roots(project, path)?;
    if !canonical.is_dir() {
        return Err(AppError::Invalid {
            message: format!("Chỉ có thể xoá folder: {}", canonical.display()),
        });
    }

    let filter = ImportFilter::for_project(Path::new(&project.agents_root));
    if !can_modify_path(project, &filter, &canonical, &explorer_root) {
        return Err(AppError::Invalid {
            message: "Không được phép xoá thư mục này".to_string(),
        });
    }

    if is_declared_root(project, &canonical)
        || dunce::canonicalize(Path::new(&project.docs_root).join("features"))
            .ok()
            .as_deref()
            == Some(&canonical)
    {
        return Err(AppError::Invalid {
            message: "Không thể xoá root do project quản lý".to_string(),
        });
    }

    let features_root = dunce::canonicalize(Path::new(&project.docs_root).join("features"));
    if features_root
        .ok()
        .as_ref()
        .is_some_and(|root| canonical.parent() == Some(root))
    {
        return Err(AppError::Invalid {
            message: "Không xoá feature từ Explorer — dùng thao tác Xoá feature để dọn cả dữ liệu liên quan".to_string(),
        });
    }

    Ok((canonical, explorer_root, filter))
}

/// One level of a directory under one of the explorer's roots — lazy
/// rather than a recursive walk, since the browsed folder can contain
/// multiple full source repos (`node_modules`, `.git`, build output); a
/// single recursive call could return an enormous payload and stall the
/// UI. The frontend calls this again for each folder the user expands,
/// mirroring how a normal file-explorer sidebar works.
#[tauri::command]
pub fn list_directory(state: State<AppState>, path: String) -> AppResult<Vec<DirEntry>> {
    let project = current_project(&state)?;
    let (canonical_dir, canonical_root) = resolve_within_explorer_roots(&project, &path)?;

    if !canonical_dir.is_dir() {
        return Err(AppError::Invalid {
            message: format!("Không phải thư mục: {}", canonical_dir.display()),
        });
    }

    let filter = ImportFilter::for_project(Path::new(&project.agents_root));
    let mut entries: Vec<DirEntry> = std::fs::read_dir(&canonical_dir)?
        .flatten()
        .filter_map(|entry| {
            let child_path = entry.path();
            let rel = child_path.strip_prefix(&canonical_root).ok()?;
            let is_restricted = filter.exclusion_reason(&to_pattern_path(rel)).is_some();
            Some(DirEntry {
                name: entry.file_name().to_string_lossy().into_owned(),
                path: child_path.display().to_string(),
                is_dir: child_path.is_dir(),
                is_restricted,
                can_modify: dunce::canonicalize(&child_path)
                    .ok()
                    .is_some_and(|canonical| {
                        can_modify_path(&project, &filter, &canonical, &canonical_root)
                    }),
            })
        })
        .collect();

    // Directories first, then case-insensitive alphabetical — `read_dir`'s
    // own order is filesystem-dependent.
    entries.sort_by(|a, b| {
        b.is_dir
            .cmp(&a.is_dir)
            .then_with(|| a.name.to_lowercase().cmp(&b.name.to_lowercase()))
    });
    Ok(entries)
}

/// Creates one empty file below a modifiable Explorer folder. The backend
/// derives the target from `parent_path` + `name`; the frontend never gets to
/// submit an arbitrary full path for writing.
#[tauri::command]
pub fn create_explorer_file(
    state: State<AppState>,
    parent_path: String,
    name: String,
) -> AppResult<DirEntry> {
    let project = current_project(&state)?;
    let (parent, explorer_root, filter) = resolve_modifiable_parent(&project, &parent_path)?;
    let name = validate_entry_name(&name)?;
    let target = parent.join(name);

    if has_protected_component(&target) || is_restricted_path(&filter, &target, &explorer_root) {
        return Err(AppError::Invalid {
            message: "Không được phép tạo file tại vị trí này".to_string(),
        });
    }

    OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&target)
        .map_err(|error| map_create_error(error, &target))?;

    entry_for_path(&project, &filter, &target, &explorer_root)
}

/// Creates one empty folder below a modifiable Explorer folder.
#[tauri::command]
pub fn create_explorer_folder(
    state: State<AppState>,
    parent_path: String,
    name: String,
) -> AppResult<DirEntry> {
    let project = current_project(&state)?;
    let (parent, explorer_root, filter) = resolve_modifiable_parent(&project, &parent_path)?;
    let name = validate_entry_name(&name)?;
    let target = parent.join(name);

    if has_protected_component(&target) || is_restricted_path(&filter, &target, &explorer_root) {
        return Err(AppError::Invalid {
            message: "Không được phép tạo folder tại vị trí này".to_string(),
        });
    }

    std::fs::create_dir(&target).map_err(|error| map_create_error(error, &target))?;
    entry_for_path(&project, &filter, &target, &explorer_root)
}

#[tauri::command]
pub fn preview_delete_explorer_entry(
    state: State<AppState>,
    path: String,
) -> AppResult<ExplorerDeletePreview> {
    let project = current_project(&state)?;
    let (canonical, explorer_root, filter) = resolve_deletable_folder(&project, &path)?;
    let mut scan = DeleteScan::default();
    scan_delete_tree(&project, &filter, &explorer_root, &canonical, &mut scan)?;

    let feature = feature_name_for_path(&project, &canonical);
    let running_slots = feature
        .as_deref()
        .map(|feature| running_slots_for_feature(&state, feature))
        .unwrap_or_default();

    Ok(ExplorerDeletePreview {
        path: canonical.display().to_string(),
        name: canonical
            .file_name()
            .map(|value| value.to_string_lossy().into_owned())
            .unwrap_or_default(),
        file_count: scan.file_count,
        folder_count: scan.folder_count,
        running_slots,
        locked_files: locked_files_under(&project, &canonical),
        protected_paths: scan.protected_paths,
        symlink_paths: scan.symlink_paths,
    })
}

#[tauri::command]
pub fn delete_explorer_entry(
    state: State<AppState>,
    path: String,
    confirmation: String,
) -> AppResult<()> {
    let project = current_project(&state)?;
    let preview = preview_delete_explorer_entry(state, path)?;

    if confirmation.trim() != preview.name {
        return Err(AppError::Invalid {
            message: "Tên xác nhận không khớp — gõ đúng tên folder để xoá".to_string(),
        });
    }
    if !preview.running_slots.is_empty() {
        return Err(AppError::Invalid {
            message: format!(
                "Đang có agent chạy cho feature này ({}) — dừng agent trước khi xoá",
                preview.running_slots.join(", ")
            ),
        });
    }
    if !preview.locked_files.is_empty() {
        return Err(AppError::Invalid {
            message: "Folder chứa file đang bị Contract Lock bảo vệ — không thể xoá".to_string(),
        });
    }
    if !preview.protected_paths.is_empty() || !preview.symlink_paths.is_empty() {
        return Err(AppError::Invalid {
            message: "Folder chứa path được bảo vệ hoặc symlink — không thể xoá an toàn"
                .to_string(),
        });
    }

    let (canonical, _explorer_root, _filter) = resolve_deletable_folder(&project, &preview.path)?;
    std::fs::remove_dir_all(canonical)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn write(path: &Path, content: &str) {
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, content).unwrap();
    }

    /// `project-ai-kit/example-project/` — same fixture `commands::project`
    /// tests use. `agentsRoot`/`docsRoot`/`repositoryRoot` are `kit-repo/`,
    /// `docs/`, `repos/`, all direct children of `example-project/` — this
    /// pins down the exact real-world case that motivated the unified-tree
    /// design: the common ancestor is the actual project folder the user
    /// opened, `sample-inputs/`/`README.md`/`context.md` included even
    /// though none of them is any of the 3 declared roots.
    #[test]
    fn resolve_explorer_roots_on_the_example_project_fixture_is_its_shared_root() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../example-project")
            .canonicalize()
            .expect("example-project fixture must exist — see repo root");

        let project = ProjectPaths {
            agents_root: root.join("kit-repo").display().to_string(),
            docs_root: root.join("docs").display().to_string(),
            repository_root: root.join("repos").display().to_string(),
        };

        let roots = resolve_explorer_roots(&project).unwrap();
        assert_eq!(roots.len(), 1);
        assert_eq!(PathBuf::from(&roots[0].path), root);
    }

    #[test]
    fn resolve_explorer_roots_finds_the_shared_project_folder() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("project/kit-repo");
        let docs_root = tmp.path().join("project/docs");
        let repository_root = tmp.path().join("project/repos");
        std::fs::create_dir_all(&agents_root).unwrap();
        std::fs::create_dir_all(&docs_root).unwrap();
        std::fs::create_dir_all(&repository_root).unwrap();

        let project = ProjectPaths {
            agents_root: agents_root.display().to_string(),
            docs_root: docs_root.display().to_string(),
            repository_root: repository_root.display().to_string(),
        };

        let roots = resolve_explorer_roots(&project).unwrap();
        assert_eq!(roots.len(), 1);
        assert_eq!(roots[0].label, "Project");
        let expected = dunce::canonicalize(tmp.path().join("project")).unwrap();
        assert_eq!(PathBuf::from(&roots[0].path), expected);
    }

    /// `resolve_explorer_roots` canonicalizes real paths on disk, so its
    /// "no common ancestor → 3 separate roots" branch can't be exercised
    /// with fake divergent paths the way `common_ancestor` itself can
    /// (below) — a real test would need genuinely unrelated filesystem
    /// mounts. `common_ancestor`'s own unit tests cover that branch's
    /// logic directly and are what `resolve_explorer_roots` delegates to.
    #[test]
    fn common_ancestor_is_none_when_paths_share_only_the_filesystem_root() {
        assert!(common_ancestor(&[PathBuf::from("/a/b"), PathBuf::from("/c/d")]).is_none());
    }

    #[test]
    fn common_ancestor_finds_the_shared_prefix() {
        let common = common_ancestor(&[
            PathBuf::from("/tmp/project/kit-repo"),
            PathBuf::from("/tmp/project/docs"),
            PathBuf::from("/tmp/project/repos/api"),
        ]);
        assert_eq!(common, Some(PathBuf::from("/tmp/project")));
    }

    #[test]
    fn list_directory_flags_restricted_entries_without_hiding_them() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("project/agents");
        let docs_root = tmp.path().join("project/docs");
        let repository_root = tmp.path().join("project/repos");
        std::fs::create_dir_all(&agents_root).unwrap();
        std::fs::create_dir_all(&docs_root).unwrap();
        write(&repository_root.join("README.md"), "# hi");
        write(&repository_root.join(".env"), "SECRET=1");

        let project = ProjectPaths {
            agents_root: agents_root.display().to_string(),
            docs_root: docs_root.display().to_string(),
            repository_root: repository_root.display().to_string(),
        };

        let (canonical_dir, _canonical_root) =
            resolve_within_explorer_roots(&project, &repository_root.display().to_string())
                .unwrap();

        let filter = ImportFilter::for_project(Path::new(&project.agents_root));
        // Same relative-path computation `list_directory` does internally,
        // but against the PROJECT root (common ancestor), matching what a
        // real call resolves `canonical_root` to in unified mode.
        let project_root = dunce::canonicalize(tmp.path().join("project")).unwrap();
        let mut entries: Vec<DirEntry> = std::fs::read_dir(&canonical_dir)
            .unwrap()
            .flatten()
            .filter_map(|entry| {
                let child_path = entry.path();
                let rel = child_path.strip_prefix(&project_root).ok()?;
                let is_restricted = filter.exclusion_reason(&to_pattern_path(rel)).is_some();
                let canonical = dunce::canonicalize(&child_path).ok()?;
                Some(DirEntry {
                    name: entry.file_name().to_string_lossy().into_owned(),
                    path: child_path.display().to_string(),
                    is_dir: child_path.is_dir(),
                    is_restricted,
                    can_modify: can_modify_path(&project, &filter, &canonical, &project_root),
                })
            })
            .collect();
        entries.sort_by(|a, b| a.name.cmp(&b.name));

        assert_eq!(entries.len(), 2);
        let env_entry = entries.iter().find(|e| e.name == ".env").unwrap();
        assert!(env_entry.is_restricted);
        assert!(!env_entry.can_modify);
        let readme_entry = entries.iter().find(|e| e.name == "README.md").unwrap();
        assert!(!readme_entry.is_restricted);
        assert!(readme_entry.can_modify);
    }

    #[test]
    fn validate_entry_name_rejects_paths_and_control_characters() {
        assert!(validate_entry_name("README.md").is_ok());
        assert!(validate_entry_name("  folder-name  ").is_ok());
        assert!(validate_entry_name("").is_err());
        assert!(validate_entry_name(".").is_err());
        assert!(validate_entry_name("../outside").is_err());
        assert!(validate_entry_name("nested/file.md").is_err());
        assert!(validate_entry_name("nested\\file.md").is_err());
        assert!(validate_entry_name("bad\nname").is_err());
    }

    #[test]
    fn can_modify_path_only_allows_declared_roots_and_excludes_protected_paths() {
        let tmp = tempfile::tempdir().unwrap();
        let project_root = tmp.path().join("project");
        let agents_root = project_root.join("kit-repo");
        let docs_root = project_root.join("docs");
        let repository_root = project_root.join("repos");
        std::fs::create_dir_all(agents_root.join(".claude")).unwrap();
        std::fs::create_dir_all(&docs_root).unwrap();
        std::fs::create_dir_all(repository_root.join("src")).unwrap();
        let project = ProjectPaths {
            agents_root: agents_root.display().to_string(),
            docs_root: docs_root.display().to_string(),
            repository_root: repository_root.display().to_string(),
        };
        let explorer_root = dunce::canonicalize(&project_root).unwrap();
        let filter = ImportFilter::for_project(Path::new(&project.agents_root));

        assert!(can_modify_path(
            &project,
            &filter,
            &dunce::canonicalize(repository_root.join("src")).unwrap(),
            &explorer_root,
        ));
        assert!(!can_modify_path(
            &project,
            &filter,
            &dunce::canonicalize(project_root.join("outside"))
                .unwrap_or_else(|_| project_root.join("outside")),
            &explorer_root,
        ));
        assert!(!can_modify_path(
            &project,
            &filter,
            &dunce::canonicalize(agents_root.join(".claude")).unwrap(),
            &explorer_root,
        ));
    }
}
