//! Backlog credentials: test, save, inspect, clear (AC-E1-19..22).
//!
//! The API key is a parameter here and a keychain entry there — it is never
//! a struct field that gets serialized, never part of `ProjectConfig`, and
//! never returned to the frontend once saved. `get_backlog_status` exists
//! precisely so the UI can render the section without ever asking for the
//! secret back.

use std::path::Path;

use tauri::State;

use crate::app_state::AppState;
use crate::domain::config_file::ProjectConfig;
use crate::domain::integrations::{
    BacklogConfig, BacklogIssueStatus, BacklogStatus, BacklogStatusCache,
};
use crate::domain::project::ProjectPaths;
use crate::error::{AppError, AppResult};
use crate::integrations::backlog_api::{self, FetchOutcome};
use crate::store::atomic_write::write_json_atomic;
use crate::store::{keychain, orchestrator_dir};

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

fn read_config(agents_root: &Path) -> AppResult<ProjectConfig> {
    let path = orchestrator_dir::config_json_path(agents_root);
    let raw = std::fs::read_to_string(&path).map_err(|_| AppError::Invalid {
        message: "Chưa có config.json cho project này".to_string(),
    })?;
    serde_json::from_str(&raw).map_err(|err| AppError::Invalid {
        message: format!("config.json không đọc được: {err}"),
    })
}

/// Shared by `test_backlog_connection` and `save_backlog_credentials` — one
/// definition of "does this credential actually work", so saving can never
/// use a weaker check than the button the user pressed (AC-E1-21).
async fn verify_credentials(domain: &str, api_key: &str) -> AppResult<String> {
    if domain.trim().is_empty() || api_key.trim().is_empty() {
        return Err(AppError::Invalid {
            message: "Cần nhập cả domain và API key".to_string(),
        });
    }
    let url = backlog_api::build_api_url(domain, "users/myself", api_key);
    match backlog_api::get_json(&url).await {
        FetchOutcome::Ok(body) => {
            backlog_api::parse_myself(&body).ok_or_else(|| AppError::Invalid {
                message: "Backlog trả về phản hồi không nhận dạng được (thiếu tên user)"
                    .to_string(),
            })
        }
        FetchOutcome::NotFound => Err(AppError::Invalid {
            message: "HTTP 404: domain đúng dạng nhưng không có API v2 ở đó — kiểm tra lại domain"
                .to_string(),
        }),
        FetchOutcome::Failed(message) => Err(AppError::Invalid { message }),
    }
}

/// AC-E1-20 — "Kiểm tra kết nối". Writes nothing anywhere; on failure the
/// verbatim Backlog error (minus the key itself) is what comes back
/// (AC-E1-21).
#[tauri::command]
pub async fn test_backlog_connection(domain: String, api_key: String) -> AppResult<String> {
    verify_credentials(&domain, &api_key).await
}

/// AC-E1-21 — the connection test runs HERE, in the backend, before
/// anything is persisted. A frontend that "forgot" to test first still
/// cannot store a broken (or unverified) credential.
#[tauri::command]
pub async fn save_backlog_credentials(
    state: State<'_, AppState>,
    domain: String,
    project_key: String,
    api_key: String,
) -> AppResult<String> {
    if project_key.trim().is_empty() {
        return Err(AppError::Invalid {
            message: "Cần nhập project key (vd PROJ)".to_string(),
        });
    }
    let project = current_project(&state)?;
    let agents_root = std::path::PathBuf::from(&project.agents_root);

    // AC-E1-22 — no keychain, no save. There is no file fallback by design.
    if let Err(err) = keychain::keychain_availability() {
        return Err(AppError::Invalid {
            message: format!(
                "OS keychain không truy cập được ({err}) — app không ghi API key ra file, hãy bật keychain rồi thử lại"
            ),
        });
    }

    let display_name = verify_credentials(&domain, &api_key).await?;

    let domain = domain
        .trim()
        .trim_end_matches('/')
        .trim_start_matches("https://")
        .trim_start_matches("http://")
        .to_string();
    keychain::save_api_key(&domain, api_key.trim())?;

    let mut config = read_config(&agents_root)?;
    config.backlog = Some(BacklogConfig {
        domain: domain.clone(),
        project_key: project_key.trim().to_string(),
        credential_ref: domain,
    });
    write_json_atomic(&orchestrator_dir::config_json_path(&agents_root), &config)?;

    Ok(display_name)
}

/// Everything the Settings screen needs, and nothing more — no API key.
#[tauri::command]
pub fn get_backlog_status(state: State<AppState>) -> AppResult<BacklogStatus> {
    let project = current_project(&state)?;
    let config = read_config(Path::new(&project.agents_root)).ok();
    let backlog = config.and_then(|config| config.backlog);
    let keychain_error = keychain::keychain_availability().err();

    Ok(BacklogStatus {
        // AC-E5-01 — Push to Backlog is enabled off exactly this flag: the
        // non-secret config exists AND the key is still in the keychain.
        configured: backlog
            .as_ref()
            .map(|cfg| {
                keychain_error.is_none()
                    && keychain::read_api_key(&cfg.credential_ref)
                        .ok()
                        .flatten()
                        .is_some()
            })
            .unwrap_or(false),
        domain: backlog
            .as_ref()
            .map(|cfg| cfg.domain.clone())
            .unwrap_or_default(),
        project_key: backlog
            .as_ref()
            .map(|cfg| cfg.project_key.clone())
            .unwrap_or_default(),
        keychain_available: keychain_error.is_none(),
        keychain_error,
    })
}

/// Removes the key from the keychain and the non-secret half from
/// `config.json` — used when switching spaces or revoking a key.
#[tauri::command]
pub fn clear_backlog_credentials(state: State<AppState>) -> AppResult<()> {
    let project = current_project(&state)?;
    let agents_root = Path::new(&project.agents_root);
    let mut config = read_config(agents_root)?;

    if let Some(backlog) = config.backlog.take() {
        keychain::delete_api_key(&backlog.credential_ref)?;
    }
    write_json_atomic(&orchestrator_dir::config_json_path(agents_root), &config)
}

/// AC-E5-14..18 — pulls the current status of every mapped issue.
///
/// Read-only by construction: the only HTTP verb this app ever sends to
/// Backlog is GET. A refresh that fails leaves the previous cache in place
/// and says when it was taken (AC-E5-16) instead of blanking the table.
#[tauri::command]
pub async fn refresh_backlog_status(
    state: State<'_, AppState>,
    feature: String,
) -> AppResult<BacklogStatusCache> {
    let project = current_project(&state)?;
    let agents_root = std::path::PathBuf::from(&project.agents_root);
    let docs_root = std::path::PathBuf::from(&project.docs_root);

    let (mapping, _) = crate::store::backlog_map::read_mapping(&agents_root, &feature);
    let previous = read_status_cache(&agents_root, &feature);

    if mapping.issues.is_empty() {
        return Ok(BacklogStatusCache {
            fetched_at: chrono::Utc::now().to_rfc3339(),
            issues: Vec::new(),
            task_hashes: previous.map(|cache| cache.task_hashes).unwrap_or_default(),
            stale: false,
            error: None,
        });
    }

    let (backlog, api_key) = match saved_credentials(&agents_root) {
        Ok(credentials) => credentials,
        Err(err) => return Ok(stale_cache(previous, err.to_string())),
    };

    let mut issues = Vec::with_capacity(mapping.issues.len());
    for link in &mapping.issues {
        let url = backlog_api::build_api_url(
            &backlog.domain,
            &format!("issues/{}", link.issue_key),
            &api_key,
        );
        match backlog_api::get_json(&url).await {
            FetchOutcome::Ok(body) => issues.push(BacklogIssueStatus {
                issue_key: link.issue_key.clone(),
                task_file: link.task_file.clone(),
                status_name: backlog_api::parse_issue_status(&body),
                not_found: false,
            }),
            // AC-E5-17 — deleted on Backlog: flagged, never recreated.
            FetchOutcome::NotFound => issues.push(BacklogIssueStatus {
                issue_key: link.issue_key.clone(),
                task_file: link.task_file.clone(),
                status_name: None,
                not_found: true,
            }),
            // AC-E5-16 — one transport failure invalidates the whole
            // refresh; keep the previous numbers rather than showing a
            // half-updated table.
            FetchOutcome::Failed(message) => return Ok(stale_cache(previous, message)),
        }
    }

    // AC-E5-18 — hash task files as they were at this refresh. A later
    // refresh comparing against these detects "task file changed after the
    // issue was created"; the app only reports it, never edits the issue.
    let feature_dir = docs_root.join("features").join(&feature);
    let task_hashes = mapping
        .issues
        .iter()
        .filter_map(|link| {
            let content = std::fs::read_to_string(feature_dir.join(&link.task_file)).ok()?;
            Some((
                link.task_file.clone(),
                crate::inference::contract_lock_rules::sha256_hex(&content),
            ))
        })
        .collect();

    let cache = BacklogStatusCache {
        fetched_at: chrono::Utc::now().to_rfc3339(),
        issues,
        task_hashes,
        stale: false,
        error: None,
    };
    let _ = write_json_atomic(
        &orchestrator_dir::backlog_status_cache_path(&agents_root, &feature),
        &cache,
    );
    Ok(cache)
}

/// The last cache as-is, without hitting the network — what the Backlog
/// screen renders on mount before its first refresh.
#[tauri::command]
pub fn get_backlog_status_cache(
    state: State<AppState>,
    feature: String,
) -> AppResult<Option<BacklogStatusCache>> {
    let project = current_project(&state)?;
    Ok(read_status_cache(Path::new(&project.agents_root), &feature))
}

fn read_status_cache(agents_root: &Path, feature: &str) -> Option<BacklogStatusCache> {
    let raw = std::fs::read_to_string(orchestrator_dir::backlog_status_cache_path(
        agents_root,
        feature,
    ))
    .ok()?;
    serde_json::from_str(&raw).ok()
}

/// AC-E5-16 — previous numbers, marked stale, with the reason attached.
fn stale_cache(previous: Option<BacklogStatusCache>, error: String) -> BacklogStatusCache {
    match previous {
        Some(cache) => BacklogStatusCache {
            stale: true,
            error: Some(error),
            ..cache
        },
        None => BacklogStatusCache {
            fetched_at: String::new(),
            issues: Vec::new(),
            task_hashes: std::collections::BTreeMap::new(),
            stale: true,
            error: Some(error),
        },
    }
}

/// Reads the saved key for outbound calls. Never exposed as a command —
/// only `commands::integrations` and the status-refresh path may call it.
pub(crate) fn saved_credentials(agents_root: &Path) -> AppResult<(BacklogConfig, String)> {
    let config = read_config(agents_root)?;
    let backlog = config.backlog.ok_or_else(|| AppError::Invalid {
        message: "Chưa cấu hình Backlog — vào Settings › Integrations để nhập domain và API key"
            .to_string(),
    })?;
    let api_key =
        keychain::read_api_key(&backlog.credential_ref)?.ok_or_else(|| AppError::Invalid {
            message: "Không tìm thấy API key trong OS keychain — hãy nhập lại trong Settings"
                .to_string(),
        })?;
    Ok((backlog, api_key))
}
