use std::path::{Component, Path, PathBuf};

use tauri::{AppHandle, State};
use tauri_plugin_store::StoreExt;

use crate::agentrun::cli_path;
use crate::agents_reader;
use crate::app_state::AppState;
use crate::domain::config_file::ProjectConfig;
use crate::domain::project::{
    DetectedPaths, EcosystemRepo, ProjectInitStatus, ProjectPaths, ProjectSummary,
    RecentProjectEntry,
};
use crate::error::{AppError, AppResult};
use crate::fs_detect;
use crate::store::atomic_write::write_json_atomic;
use crate::store::kit_template;
use crate::store::orchestrator_dir;

const SETTINGS_STORE: &str = "settings.json";
const RECENT_PROJECTS_KEY: &str = "recentProjects";
const AGENTS_MD_FILENAME: &str = "AGENTS.md";

fn path_to_string(path: &Path) -> String {
    path.display().to_string()
}

fn validate_new_project_name(value: &str) -> AppResult<String> {
    let name = value.trim();
    let component_count = Path::new(name).components().count();
    let is_reserved_windows_name = {
        let stem = name.split('.').next().unwrap_or(name).to_ascii_uppercase();
        matches!(stem.as_str(), "CON" | "PRN" | "AUX" | "NUL")
            || (stem.len() == 4
                && (stem.starts_with("COM") || stem.starts_with("LPT"))
                && stem.as_bytes()[3].is_ascii_digit())
    };

    if name.is_empty()
        || name.len() > 100
        || component_count != 1
        || !matches!(
            Path::new(name).components().next(),
            Some(Component::Normal(_))
        )
        || name.chars().any(|character| {
            character.is_control() || character == '/' || character == '\\' || character == ':'
        })
        || name.ends_with('.')
        || name.ends_with(' ')
        || is_reserved_windows_name
    {
        return Err(AppError::Invalid {
            message: "Tên project phải là một tên thư mục hợp lệ, không chứa dấu phân cách hoặc ký tự đặc biệt".to_string(),
        });
    }

    Ok(name.to_string())
}

fn new_project_paths(destination: &Path) -> ProjectPaths {
    ProjectPaths {
        agents_root: path_to_string(destination),
        docs_root: path_to_string(&destination.join("docs")),
        repository_root: path_to_string(&destination.join("repos")),
    }
}

#[tauri::command]
pub fn detect_project_paths(root_hint: String) -> DetectedPaths {
    let root = PathBuf::from(&root_hint);
    let agents_root = fs_detect::detect_agents_root(&root);

    // `AGENTS.md` names the repos, so dò `repositoryRoot` theo chính danh
    // sách đó thay vì đoán qua `.git`. Tìm file ở cả `root_hint` lẫn
    // `agentsRoot` vừa dò được — file không nằm cố định một chỗ.
    // `agentsRoot` trước `root_hint`: `find_agents_md` cũng thử thư mục CHA
    // của mỗi root, mà cha của `root_hint` rất hay là chính repo kit — file
    // `AGENTS.md` mẫu ở đó có bảng Repos toàn dòng placeholder và sẽ nuốt
    // mất bảng thật của project.
    let mut lookup: Vec<&Path> = Vec::new();
    if let Some(detected) = agents_root.as_deref() {
        lookup.push(detected);
    }
    lookup.push(&root);
    let declared_repos = find_agents_md(&lookup)
        .map(|(_, content)| agents_reader::declared_repo_paths(&content))
        .unwrap_or_default();

    let docs_root = fs_detect::detect_docs_root(&root);

    DetectedPaths {
        repository_root: fs_detect::detect_repository_root_by_declared_repos(
            &root,
            &declared_repos,
            docs_root.as_deref(),
        )
        .map(|p| path_to_string(&p)),
        agents_root: agents_root.as_deref().map(path_to_string),
        docs_root: docs_root.as_deref().map(path_to_string),
    }
}

/// Creates a project in the selected parent directory using the standard
/// layout, then opens it through the same scaffold path as an existing project.
#[tauri::command]
pub fn create_project(
    app: AppHandle,
    state: State<AppState>,
    parent_path: String,
    name: String,
) -> AppResult<ProjectSummary> {
    let name = validate_new_project_name(&name)?;
    let parent = PathBuf::from(parent_path.trim());
    if !parent.is_dir() {
        return Err(AppError::Invalid {
            message: format!("Thư mục lưu project không tồn tại: {}", parent.display()),
        });
    }
    let parent = dunce::canonicalize(&parent).map_err(|err| AppError::Invalid {
        message: format!("Không đọc được thư mục lưu project: {err}"),
    })?;
    let destination = parent.join(&name);
    if destination.exists() {
        return Err(AppError::Invalid {
            message: format!(
                "Project đã tồn tại tại {} — chọn tên hoặc thư mục khác",
                destination.display()
            ),
        });
    }

    let paths = new_project_paths(&destination);
    open_project_internal(
        app,
        state,
        paths.agents_root,
        paths.docs_root,
        paths.repository_root,
        name,
        true,
    )
}

/// Tries `AGENTS.md` at each root and its immediate parent — the file's
/// location is not fixed across projects (see plan risk #2; ESKITCHEN has
/// it directly under `agentsRoot`, but nothing guarantees that in general).
fn find_agents_md(roots: &[&Path]) -> Option<(PathBuf, String)> {
    let mut candidates: Vec<PathBuf> = Vec::new();
    for root in roots {
        candidates.push(root.join(AGENTS_MD_FILENAME));
        if let Some(parent) = root.parent() {
            candidates.push(parent.join(AGENTS_MD_FILENAME));
        }
    }
    candidates.into_iter().find_map(|candidate| {
        std::fs::read_to_string(&candidate)
            .ok()
            .map(|content| (candidate, content))
    })
}

fn load_or_reset_config(
    orchestrator_root: &Path,
    agents_found: &[String],
    warnings: &mut Vec<String>,
) -> AppResult<ProjectConfig> {
    let path = orchestrator_dir::config_json_path(orchestrator_root);
    if !path.exists() {
        return Ok(ProjectConfig::with_defaults(agents_found));
    }

    let raw = std::fs::read_to_string(&path)?;
    match serde_json::from_str::<ProjectConfig>(&raw) {
        Ok(mut config) => {
            config.reconcile(agents_found);
            Ok(config)
        }
        Err(_) => {
            // AF-6 / AC-E1-23: corrupted config.json — back it up, never lose
            // the project from recent, never crash.
            let backup_path = path.with_file_name("config.json.bak");
            std::fs::rename(&path, &backup_path)?;
            warnings.push(format!(
                "config.json bị hỏng, đã backup thành {} và tạo lại mặc định",
                backup_path.display()
            ));
            Ok(ProjectConfig::with_defaults(agents_found))
        }
    }
}

/// Đảm bảo cả 3 root tồn tại, trả về mô tả những root mà hàm này vừa TẠO.
///
/// Trước đây root chưa tồn tại là lỗi cứng, trong khi app lại sẵn sàng ghi
/// hàng trăm file kit VÀO TRONG chính các root đó (`kit_template`,
/// `ensure_skeleton`). Mâu thuẫn đó bắt người dùng phải `mkdir docs`,
/// `mkdir repos` bên ngoài app trước khi mở được project mới.
///
/// Cố ý KHÔNG tự sửa một path đang là file: đó là lỗi thật, đoán ý người
/// dùng ở đây chỉ làm hỏng thêm.
fn prepare_roots(roots: &[(&str, &Path)], create_missing: bool) -> AppResult<Vec<String>> {
    let mut created = Vec::new();

    for (field, path) in roots {
        if path.as_os_str().is_empty() {
            return Err(AppError::Invalid {
                message: format!("{field} chưa được điền"),
            });
        }
        if path.is_dir() {
            continue;
        }
        if path.exists() {
            return Err(AppError::Invalid {
                message: format!(
                    "{field} đang trỏ tới một file, không phải thư mục: {}",
                    path.display()
                ),
            });
        }
        if !create_missing {
            return Err(AppError::Invalid {
                message: format!("{field} không tồn tại: {}", path.display()),
            });
        }
        std::fs::create_dir_all(path).map_err(|err| AppError::Invalid {
            message: format!("Không tạo được {field} ({}): {err}", path.display()),
        })?;
        created.push(format!("{field} ({})", path.display()));
    }

    Ok(created)
}

fn build_ecosystem_with_warnings(
    agents_root: &Path,
    docs_root: &Path,
    repository_root: &Path,
    warnings: &mut Vec<String>,
) -> Vec<EcosystemRepo> {
    let Some((_path, content)) = find_agents_md(&[agents_root, docs_root, repository_root]) else {
        warnings.push(format!(
            "Không tìm thấy {AGENTS_MD_FILENAME} ở agentsRoot, docsRoot, repositoryRoot (hoặc thư mục cha của chúng)"
        ));
        return Vec::new();
    };

    let mut candidate_bases: Vec<&Path> = vec![repository_root, agents_root, docs_root];
    if let Some(parent) = repository_root.parent() {
        candidate_bases.push(parent);
    }

    match agents_reader::build_ecosystem(&content, &candidate_bases) {
        // Bảng parse được nhưng mọi dòng còn là placeholder. Trước đây
        // nhánh này im hoàn toàn, nên project chưa init trông y hệt project
        // đã init mà app đọc hụt.
        Ok(Some(repos)) if repos.is_empty() => {
            warnings.push(format!(
                "Bảng ## Repos trong {AGENTS_MD_FILENAME} chưa có dòng repo nào được điền — chạy /init-kit trong Claude Code tại agentsRoot"
            ));
            Vec::new()
        }
        Ok(Some(repos)) => {
            // Repo khai trong bảng mà không thấy trên đĩa từng im lặng hoàn
            // toàn cho tới lúc bấm Run agent tương ứng. Nguyên nhân thường
            // gặp nhất là `repositoryRoot` trỏ nhầm, nên nêu luôn nó ra.
            let missing: Vec<&str> = repos
                .iter()
                .filter(|repo| !repo.cloned)
                .map(|repo| repo.declared_path.as_str())
                .collect();
            if !missing.is_empty() {
                warnings.push(format!(
                    "Không tìm thấy trên đĩa {} repo khai trong {AGENTS_MD_FILENAME}: {}. Kiểm tra repositoryRoot ({}) hoặc clone các repo này về — agent backend/frontend/mobile tương ứng sẽ không chạy được.",
                    missing.len(),
                    missing.join(", "),
                    repository_root.display(),
                ));
            }
            // Ô "Vai trò" đọc không ra thì repo vẫn hiện trong bảng
            // Ecosystem, nhưng mọi agent nhắm vào vai trò đó bị chặn — nói
            // ngay lúc mở project, đừng để tới lúc bấm Run mới lộ.
            let unreadable: Vec<String> = repos
                .iter()
                .filter(|repo| repo.role_key.is_none())
                .map(|repo| format!("{} (vai trò: \"{}\")", repo.name, repo.role))
                .collect();
            if !unreadable.is_empty() {
                warnings.push(format!(
                    "Không đọc được vai trò của {} repo trong {AGENTS_MD_FILENAME}: {}. Ô \"Vai trò\" phải là đúng một từ backend/frontend/mobile/other — agent tương ứng sẽ không chạy được cho tới khi sửa.",
                    unreadable.len(),
                    unreadable.join(", "),
                ));
            }
            repos
        }
        Ok(None) => {
            warnings.push(format!(
                "Không tìm thấy bảng ## Repos hợp lệ trong {AGENTS_MD_FILENAME}"
            ));
            Vec::new()
        }
        Err(_) => Vec::new(),
    }
}

#[tauri::command]
pub fn open_project(
    app: AppHandle,
    state: State<AppState>,
    agents_root: String,
    docs_root: String,
    repository_root: String,
    label: String,
) -> AppResult<ProjectSummary> {
    open_project_internal(
        app,
        state,
        agents_root,
        docs_root,
        repository_root,
        label,
        true,
    )
}

/// Opens a recent project without recreating roots that were deleted or
/// renamed. Missing paths must return to the launcher so the user can repair
/// the saved entry instead of receiving a fresh empty project.
#[tauri::command]
pub fn open_existing_project(
    app: AppHandle,
    state: State<AppState>,
    agents_root: String,
    docs_root: String,
    repository_root: String,
    label: String,
) -> AppResult<ProjectSummary> {
    open_project_internal(
        app,
        state,
        agents_root,
        docs_root,
        repository_root,
        label,
        false,
    )
}

fn open_project_internal(
    app: AppHandle,
    state: State<AppState>,
    agents_root: String,
    docs_root: String,
    repository_root: String,
    label: String,
    create_missing: bool,
) -> AppResult<ProjectSummary> {
    let label = label.trim().to_string();
    if label.is_empty() {
        return Err(AppError::Invalid {
            message: "Tên project chưa được điền".to_string(),
        });
    }
    let agents_root_path = PathBuf::from(&agents_root);
    let docs_root_path = PathBuf::from(&docs_root);
    let repository_root_path = PathBuf::from(&repository_root);

    // Claimed for this whole function's duration (dropped on every return
    // path) so two concurrent open calls can't both pass the `is_some()`
    // check below before either sets `current_project` — see
    // `AppState::try_claim_opening`.
    let Some(_opening_guard) = state.try_claim_opening() else {
        return Err(AppError::Invalid {
            message: "Một project khác đang được mở — vui lòng đợi rồi thử lại.".to_string(),
        });
    };

    if state.current_project.lock().unwrap().is_some() {
        return Err(AppError::Invalid {
            message: "Đã có project đang mở — hãy đóng project trước khi mở project khác"
                .to_string(),
        });
    }

    let created_roots = prepare_roots(
        &[
            ("agentsRoot", &agents_root_path),
            ("docsRoot", &docs_root_path),
            ("repositoryRoot", &repository_root_path),
        ],
        create_missing,
    )?;

    let mut warnings = Vec::new();

    // Bỏ luật "root phải tồn tại" cũng là bỏ luôn lớp chặn gõ sai đường
    // dẫn: `/Users/x/Wrok/...` giờ tạo ra thư mục rác thay vì báo lỗi.
    // Cảnh báo nêu đích danh thứ vừa tạo là thứ duy nhất bù lại chỗ đó.
    if !created_roots.is_empty() {
        warnings.push(format!(
            "Đã tạo thư mục chưa có: {}. Nếu đây không phải chỗ bạn định trỏ tới, đóng project rồi mở lại với đường dẫn đúng.",
            created_roots.join(", ")
        ));
    }

    // Dựng khung kit NGAY khi mở, trước khi tính `read_only` và trước khi
    // đọc agent/Ecosystem — cả ba đều phải nhìn thấy trạng thái sau khi
    // dựng, nếu không project vừa được dựng xong vẫn bị báo read-only.
    //
    // `match` chứ không `?`: không ghi được `.claude/` (thư mục chỉ đọc,
    // hết quota) mà lại không mở nổi project để xem chuyện gì xảy ra thì là
    // bước lùi. Cảnh báo + nút "Bổ sung khung kit" trên Launcher là đường thử lại.
    match kit_template::materialize_for_project(
        &agents_root_path,
        &docs_root_path,
        Some(&label),
    ) {
        Ok(report) if !report.created.is_empty() || !report.updated.is_empty() => warnings.push(format!(
            "Đã dựng khung kit cho project: tạo mới {} mục, cập nhật {} template trong .claude/ và <docsRoot>/features/ (không ghi đè file custom).",
            report.created.len(),
            report.updated.len()
        )),
        Ok(_) => {}
        Err(err) => warnings.push(format!(
            "Không dựng được khung kit: {err}. Project vẫn mở được — dùng nút \"Bổ sung khung kit\" để thử lại."
        )),
    }

    let read_only = !agents_reader::has_claude_agents_dir(&agents_root_path);
    if read_only {
        warnings.push(
            "Không tìm thấy .claude/agents/ tại agentsRoot — project mở ở chế độ read-only"
                .to_string(),
        );
    }

    let agents_found = agents_reader::discover_agents(&agents_root_path).unwrap_or_default();

    let ecosystem = build_ecosystem_with_warnings(
        &agents_root_path,
        &docs_root_path,
        &repository_root_path,
        &mut warnings,
    );
    let (init_status, init_reasons) = agents_reader::read_init_status(&agents_root_path);
    if init_status == ProjectInitStatus::NeedsInit {
        warnings.push(
            "Project chưa init: chạy /init-kit trong Claude Code tại agentsRoot rồi kiểm tra lại."
                .to_string(),
        );
    }

    // .orchestrator/ lives under agentsRoot: it's the closest thing to a
    // stable "this is the kit-managed project" anchor across the 3
    // independent roots (see A1 — there is no single project root anymore).
    orchestrator_dir::ensure_skeleton(&agents_root_path)?;

    // The self-ignore above only helps a directory git has not seen yet.
    // Anything already in the index keeps being committed, transcripts and
    // all, so say so — and leave the `git rm` to the user, since rewriting
    // someone's index unasked is not this app's call.
    if crate::gitutil::git_source::has_tracked_entries_under(&orchestrator_dir::orchestrator_dir(
        &agents_root_path,
    )) {
        warnings.push(
            "Thư mục .orchestrator/ đang được git theo dõi — nó chứa transcript agent (gồm nguyên văn nội dung file agent đã đọc/ghi) và bản sao input. Chạy `git rm -r --cached .orchestrator` rồi commit để gỡ khỏi repo."
                .to_string(),
        );
    }

    // Legacy data from builds that still had `pm-agent` and Push to
    // Backlog. Runs BEFORE `load_pipeline_def` / `load_or_reset_config`:
    // those two read the very files this cleans, and `reconcile()` would
    // otherwise tombstone `pm-agent` as `stale` instead of dropping it.
    if let Some(message) = crate::store::legacy_cleanup::purge(&agents_root_path).warning() {
        warnings.push(message);
    }

    // Migrate `pipeline.json` before anything reads it — a file written by
    // an older build keeps its stale stage topology otherwise (it still
    // parses), which is how a project ended up with no Trigger gate and
    // every `depends_on` empty.
    if let Ok(load) = crate::commands::pipeline::load_pipeline_def(&agents_root_path) {
        if let Some(backup) = load.migrated_backup {
            warnings.push(format!(
                "pipeline.json thuộc phiên bản cũ, đã cập nhật lên template hiện tại (bản cũ giữ tại {}). Các stage/gate mới sẽ xuất hiện trên Board.",
                backup.display()
            ));
        }
    }

    let config = load_or_reset_config(&agents_root_path, &agents_found, &mut warnings)?;
    // Before anything can spawn the CLI: a path typed in Settings must win
    // over discovery from this moment on, not from the next app start.
    cli_path::set_override(config.claude_cli_path.as_deref());
    write_json_atomic(
        &orchestrator_dir::config_json_path(&agents_root_path),
        &config,
    )?;

    // AC-E6-04/10 — runs the previous app instance left in flight: dead
    // processes become `interrupted` right here (the Board then shows them
    // via normal state derivation); still-live orphans are only *counted*
    // in a warning — the Board queries `list_orphans` for the actionable
    // banner. Idempotent, safe on every (re)open.
    let (interrupted, orphans) = crate::agentrun::recovery::scan_stale_runs(
        &agents_root_path,
        crate::agentrun::recovery::pid_is_live_agent,
        // Opening a project is the one moment nothing of ours can be
        // running yet — every marker found here belongs to a past instance.
        |_, _| false,
    );
    for slot in &interrupted {
        warnings.push(format!(
            "Agent '{}' (feature '{}') bị gián đoạn ở phiên trước — mở node để Resume hoặc Re-run.",
            slot.slot, slot.feature
        ));
    }
    if !orphans.is_empty() {
        warnings.push(format!(
            "{} process agent từ phiên trước vẫn đang chạy — xem cảnh báo trên Pipeline Board để gắn lại hoặc kill.",
            orphans.len()
        ));
    }

    let paths = ProjectPaths {
        agents_root,
        docs_root,
        repository_root,
    };

    *state.current_project.lock().unwrap() = Some(paths.clone());
    *state.current_project_label.lock().unwrap() = Some(label.clone());
    *state.ecosystem.lock().unwrap() = ecosystem.clone();

    upsert_recent_project(&app, &paths, &label)?;

    Ok(ProjectSummary {
        missing_kit: kit_template::missing_groups(&agents_root_path, &docs_root_path),
        paths,
        label,
        read_only,
        ecosystem,
        agents_found,
        warnings,
        init_status,
        init_reasons,
    })
}

/// Dựng phần khung kit còn thiếu cho project đang mở (AC: mở project mới
/// mà chưa có `.claude/` thì mọi node đều `AgentMissing` và không có cách
/// nào thoát từ trong app).
///
/// Trả `ScaffoldReport` thay vì `ProjectSummary`: frontend gọi lại
/// `open_project` sẵn có để làm mới `read_only`/`agents_found`/`ecosystem`.
/// Bóc tách thân `open_project` (còn `upsert_recent_project`,
/// `scan_stale_runs`, `cli_path::set_override`) rủi ro hơn giá trị nó mang
/// lại.
#[tauri::command]
pub fn scaffold_kit(state: State<AppState>) -> AppResult<kit_template::ScaffoldReport> {
    let paths = state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)?;
    let label = state.current_project_label.lock().unwrap().clone();
    kit_template::materialize_for_project(
        Path::new(&paths.agents_root),
        Path::new(&paths.docs_root),
        label.as_deref(),
    )
}

/// Re-reads project files after the user completes the external Claude Code
/// `/init-kit` handoff. Unlike `open_project`, this does not rewrite recent
/// project metadata or recreate runtime config; it only refreshes inspection
/// state and the cached Ecosystem.
#[tauri::command]
pub fn refresh_project(state: State<AppState>) -> AppResult<ProjectSummary> {
    let paths = state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)?;
    let label = state
        .current_project_label
        .lock()
        .unwrap()
        .clone()
        .unwrap_or_else(|| "Project".to_string());
    let agents_root = Path::new(&paths.agents_root);
    let docs_root = Path::new(&paths.docs_root);
    let repository_root = Path::new(&paths.repository_root);
    let mut warnings = Vec::new();
    let read_only = !agents_reader::has_claude_agents_dir(agents_root);
    let agents_found = agents_reader::discover_agents(agents_root).unwrap_or_default();
    let ecosystem =
        build_ecosystem_with_warnings(agents_root, docs_root, repository_root, &mut warnings);
    let (init_status, init_reasons) = agents_reader::read_init_status(agents_root);
    if init_status == ProjectInitStatus::NeedsInit {
        warnings.push(
            "Project chưa init: chạy /init-kit trong Claude Code tại agentsRoot rồi kiểm tra lại."
                .to_string(),
        );
    }
    *state.ecosystem.lock().unwrap() = ecosystem.clone();

    Ok(ProjectSummary {
        missing_kit: kit_template::missing_groups(agents_root, docs_root),
        paths,
        label,
        read_only,
        ecosystem,
        agents_found,
        warnings,
        init_status,
        init_reasons,
    })
}

/// Lets the frontend reconcile its in-memory screen after a webview reload.
/// The backend project state intentionally lives longer than React state, so
/// the launcher must not offer a second open while one is already active.
#[tauri::command]
pub fn has_open_project(state: State<AppState>) -> bool {
    state.current_project.lock().unwrap().is_some()
}

/// Tính lại bảng Ecosystem từ `AGENTS.md` + tình trạng thật trên đĩa, rồi
/// cập nhật bản cache trong `AppState`.
///
/// `open_project` trước đây là nơi DUY NHẤT ghi vào cache đó, nên clone một
/// repo về trong lúc app đang mở không có tác dụng gì cho tới lần mở lại
/// project. Chi phí: đọc 1 file `AGENTS.md` + vài lần `is_dir` — không đáng
/// kể so với `compute_and_persist` mà cùng lệnh đó vẫn đang chạy.
pub fn recompute_ecosystem(state: &AppState) -> Vec<EcosystemRepo> {
    let Some(paths) = state.current_project.lock().unwrap().clone() else {
        return Vec::new();
    };
    let mut ignored_warnings = Vec::new();
    let repos = build_ecosystem_with_warnings(
        Path::new(&paths.agents_root),
        Path::new(&paths.docs_root),
        Path::new(&paths.repository_root),
        &mut ignored_warnings,
    );
    *state.ecosystem.lock().unwrap() = repos.clone();
    repos
}

/// One agent run still alive in the project about to be closed.
#[derive(Debug, Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RunningSlot {
    pub feature: String,
    pub slot: String,
}

/// What is still running right now — used by the switch-project dialog to
/// name what would be killed instead of asking a vague "are you sure".
#[tauri::command]
pub fn list_running_slots(state: State<AppState>) -> Vec<RunningSlot> {
    state
        .agent_runs
        .keys()
        .into_iter()
        .map(|key| RunningSlot {
            feature: key.feature,
            slot: key.slot,
        })
        .collect()
}

/// Releases the currently open project so another one can be opened.
///
/// Everything project-scoped in `AppState` is cleared — the watcher, the
/// roots, the Ecosystem, and any pending spawn reservations — so the next
/// `open_project` starts from nothing rather than inheriting state that
/// belongs to a different directory. See `AppState::close` for why a
/// spawn racing this close can never land in `agent_runs` afterward.
#[tauri::command]
pub fn close_project(state: State<AppState>, force: bool) -> AppResult<()> {
    state.close(force)
}

fn read_recent_projects(app: &AppHandle) -> AppResult<Vec<RecentProjectEntry>> {
    let store = app.store(SETTINGS_STORE)?;
    let list = store
        .get(RECENT_PROJECTS_KEY)
        .and_then(|value| serde_json::from_value::<Vec<RecentProjectEntry>>(value).ok())
        .unwrap_or_default();
    Ok(list)
}

fn write_recent_projects(app: &AppHandle, list: &[RecentProjectEntry]) -> AppResult<()> {
    let store = app.store(SETTINGS_STORE)?;
    store.set(RECENT_PROJECTS_KEY, serde_json::to_value(list)?);
    store.save()?;
    Ok(())
}

fn same_project(a: &RecentProjectEntry, paths: &ProjectPaths) -> bool {
    a.agents_root == paths.agents_root
        && a.docs_root == paths.docs_root
        && a.repository_root == paths.repository_root
}

fn upsert_recent_project(app: &AppHandle, paths: &ProjectPaths, label: &str) -> AppResult<()> {
    let mut list = read_recent_projects(app)?;
    let now = chrono::Utc::now().to_rfc3339();

    list.retain(|entry| !same_project(entry, paths));
    list.insert(
        0,
        RecentProjectEntry {
            label: label.to_string(),
            agents_root: paths.agents_root.clone(),
            docs_root: paths.docs_root.clone(),
            repository_root: paths.repository_root.clone(),
            last_opened_at: now,
        },
    );

    write_recent_projects(app, &list)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// `project-ai-kit/example-project/` — a synthetic (not real-client)
    /// fixture deliberately built with the same messiness T1.7's plan calls
    /// for real project data to have: `repositoryRoot` is a sibling, not a
    /// descendant, of `agentsRoot`/`docsRoot`; one Ecosystem repo is
    /// declared but not cloned; `.claude/agents/` is missing an agent the
    /// pipeline definition still references. Exercises `find_agents_md` +
    /// `build_ecosystem_with_warnings` against real (if synthetic) file
    /// content instead of a hand-built string.
    fn fixture_root() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../example-project")
            .canonicalize()
            .expect("example-project fixture must exist — see repo root")
    }

    /// Regression cho đúng sự cố đã gặp: `repos/` của project ví dụ không
    /// chứa git repo nào, nên heuristic `.git` cũ bó tay và người dùng để
    /// `repositoryRoot` trỏ nhầm sang `agentsRoot` — agent backend bị chặn
    /// với thông báo "example-api chưa được clone".
    #[test]
    fn detect_project_paths_finds_the_repos_dir_of_example_project() {
        let root = fixture_root();
        let detected = detect_project_paths(path_to_string(&root));

        assert_eq!(
            detected.repository_root,
            Some(path_to_string(&root.join("repos"))),
        );
        assert_eq!(
            detected.agents_root,
            Some(path_to_string(&root.join("kit-repo"))),
        );
    }

    /// Và giá trị dò được đó phải làm cho cả 2 repo có thật hiện là "đã
    /// clone" — tức nút Run của backend mở khoá.
    #[test]
    fn the_detected_repository_root_resolves_example_project_repos_as_cloned() {
        let root = fixture_root();
        let repository_root = PathBuf::from(
            detect_project_paths(path_to_string(&root))
                .repository_root
                .unwrap(),
        );

        let mut warnings = Vec::new();
        let ecosystem = build_ecosystem_with_warnings(
            &root.join("kit-repo"),
            &root.join("docs"),
            &repository_root,
            &mut warnings,
        );

        let cloned: std::collections::HashMap<&str, bool> = ecosystem
            .iter()
            .map(|r| (r.name.as_str(), r.cloned))
            .collect();
        assert!(cloned["example-api"]);
        assert!(cloned["example-web"]);
        assert!(!cloned["example-mobile"]);
    }

    // --- prepare_roots: app tự tạo root còn thiếu thay vì từ chối mở ---

    #[test]
    fn prepare_roots_creates_missing_directories_including_nested_ones() {
        let tmp = tempfile::tempdir().unwrap();
        let nested = tmp.path().join("a/b/docs");

        let created = prepare_roots(&[("docsRoot", &nested)], true).unwrap();

        assert!(nested.is_dir());
        assert_eq!(created.len(), 1);
        assert!(created[0].starts_with("docsRoot ("));
    }

    /// Cảnh báo chỉ được nói về thứ app vừa động vào — root đã có sẵn mà
    /// bị liệt kê thì người dùng sẽ tưởng app nghịch vào project của mình.
    #[test]
    fn prepare_roots_reports_only_what_it_created() {
        let tmp = tempfile::tempdir().unwrap();
        let existing = tmp.path().join("already-here");
        std::fs::create_dir_all(&existing).unwrap();
        let fresh = tmp.path().join("brand-new");

        let created =
            prepare_roots(&[("agentsRoot", &existing), ("docsRoot", &fresh)], true).unwrap();

        assert_eq!(created.len(), 1);
        assert!(created[0].starts_with("docsRoot ("));
    }

    #[test]
    fn prepare_roots_rejects_an_empty_path() {
        let empty = PathBuf::new();
        let err = prepare_roots(&[("docsRoot", &empty)], true).unwrap_err();
        assert!(format!("{err:?}").contains("docsRoot"));
    }

    /// Path đang là file là lỗi thật — không được tự sửa.
    #[test]
    fn prepare_roots_rejects_a_path_that_exists_as_a_file() {
        let tmp = tempfile::tempdir().unwrap();
        let as_file = tmp.path().join("docs");
        std::fs::write(&as_file, "").unwrap();

        let err = prepare_roots(&[("docsRoot", &as_file)], true).unwrap_err();
        assert!(format!("{err:?}").contains("docsRoot"));
        assert!(as_file.is_file(), "không được đụng vào file của người dùng");
    }

    /// Mở lại cùng project không được báo "vừa tạo" thêm lần nào nữa.
    #[test]
    fn prepare_roots_is_idempotent() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path().join("docs");

        assert_eq!(
            prepare_roots(&[("docsRoot", &root)], true).unwrap().len(),
            1
        );
        assert!(prepare_roots(&[("docsRoot", &root)], true)
            .unwrap()
            .is_empty());
    }

    #[test]
    fn find_agents_md_locates_it_under_agents_root_of_example_project() {
        let root = fixture_root();
        let agents_root = root.join("kit-repo");
        let docs_root = root.join("docs");
        let repository_root = root.join("repos");

        let (path, content) =
            find_agents_md(&[&agents_root, &docs_root, &repository_root]).expect("must be found");

        assert_eq!(path, agents_root.join("AGENTS.md"));
        assert!(content.contains("example-api"));
    }

    #[test]
    fn build_ecosystem_matches_expected_clone_state_for_example_project() {
        let root = fixture_root();
        let agents_root = root.join("kit-repo");
        let docs_root = root.join("docs");
        let repository_root = root.join("repos");

        let mut warnings = Vec::new();
        let ecosystem = build_ecosystem_with_warnings(
            &agents_root,
            &docs_root,
            &repository_root,
            &mut warnings,
        );

        // `example-mobile` được khai nhưng không có trên đĩa — im lặng ở đây
        // chính là lý do người dùng chỉ phát hiện ra khi bấm Run.
        assert_eq!(warnings.len(), 1, "warnings: {warnings:?}");
        assert!(warnings[0].contains("example-mobile"));
        assert!(warnings[0].contains("repositoryRoot"));
        assert_eq!(ecosystem.len(), 3);

        let cloned_by_name: std::collections::HashMap<&str, bool> = ecosystem
            .iter()
            .map(|r| (r.name.as_str(), r.cloned))
            .collect();
        // README.md documents example-api/example-web as present under
        // repos/ and example-mobile as deliberately absent.
        assert!(cloned_by_name["example-api"]);
        assert!(cloned_by_name["example-web"]);
        assert!(!cloned_by_name["example-mobile"]);
    }

    #[test]
    fn discover_agents_finds_every_agent_the_fixture_ships() {
        // B17 is closed: `design-analyst-agent.md` now exists in the kit and
        // was copied into the fixture, so the design-analyst node is a
        // runnable slot rather than the permanently-skipped one it used to
        // be. This asserts the fixture stays in step with the real kit —
        // if they drift, the design-analyst path silently stops being
        // testable end to end.
        let root = fixture_root();
        let agents = agents_reader::discover_agents(&root.join("kit-repo")).expect("dir exists");
        assert_eq!(agents.len(), 12);
        assert!(agents.iter().any(|a| a == "design-analyst-agent"));
    }

    #[test]
    fn new_project_name_accepts_normal_folder_names() {
        for name in ["shop-admin", "Project 2026", "dự án mới"] {
            assert_eq!(validate_new_project_name(name).unwrap(), name);
        }
    }

    #[test]
    fn new_project_name_rejects_path_traversal_and_invalid_components() {
        for name in ["", ".", "..", "nested/project", "nested\\project", "CON"] {
            assert!(
                validate_new_project_name(name).is_err(),
                "name should be rejected: {name:?}"
            );
        }
    }

    #[test]
    fn new_project_paths_use_the_standard_layout() {
        let destination = Path::new("/tmp/shop-admin");
        let paths = new_project_paths(destination);

        assert_eq!(paths.agents_root, "/tmp/shop-admin");
        assert_eq!(paths.docs_root, "/tmp/shop-admin/docs");
        assert_eq!(paths.repository_root, "/tmp/shop-admin/repos");
    }
}

#[tauri::command]
pub fn list_recent_projects(app: AppHandle) -> AppResult<Vec<RecentProjectEntry>> {
    let mut list = read_recent_projects(&app)?;
    list.sort_by(|a, b| b.last_opened_at.cmp(&a.last_opened_at));
    Ok(list)
}

#[tauri::command]
pub fn remove_recent_project(
    app: AppHandle,
    agents_root: String,
    docs_root: String,
    repository_root: String,
) -> AppResult<()> {
    let target = ProjectPaths {
        agents_root,
        docs_root,
        repository_root,
    };
    let mut list = read_recent_projects(&app)?;
    list.retain(|entry| !same_project(entry, &target));
    write_recent_projects(&app, &list)
}
