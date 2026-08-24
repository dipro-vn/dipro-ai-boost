use std::path::PathBuf;
use std::process::Stdio;

use chrono::Utc;
use tauri::State;

use crate::agentrun::cli_path;
use crate::app_state::AppState;
use crate::auth;
use crate::domain::config_file::{ClaudeAuthMode, ProjectConfig};
use crate::domain::project::ProjectPaths;
use crate::error::{AppError, AppResult};

#[derive(Debug, Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ClaudeAuthStatus {
    pub cli_available: bool,
    pub cli_version: Option<String>,
    /// Which binary was actually resolved (Settings override, `PATH`, a
    /// known install dir, or the login shell). Shown in Settings so a
    /// wrong auto-detection is diagnosable without reading logs.
    pub cli_path: Option<String>,
    pub authenticated: bool,
    pub method: String,
    pub account: Option<String>,
    pub organization: Option<String>,
    pub env_overrides: Vec<String>,
    pub configured_mode: ClaudeAuthMode,
    pub status: String,
    pub checked_at: String,
}

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

fn resolved_cli_path() -> Option<String> {
    cli_path::resolve().map(|path| path.display().to_string())
}

fn cli_version() -> Option<String> {
    cli_path::command()
        .arg("--version")
        .output()
        .ok()
        .filter(|output| output.status.success())
        .map(|output| String::from_utf8_lossy(&output.stdout).trim().to_string())
        .filter(|value| !value.is_empty())
}

fn env_overrides() -> Vec<String> {
    const NAMES: &[&str] = &[
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CODE_API_KEY_HELPER",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "ANTHROPIC_PROFILE",
    ];
    NAMES
        .iter()
        .filter(|name| std::env::var_os(name).is_some())
        .map(|name| (*name).to_string())
        .collect()
}

fn auth_status_from_json(
    value: &serde_json::Value,
) -> (bool, String, Option<String>, Option<String>) {
    let authenticated = value
        .get("loggedIn")
        .and_then(serde_json::Value::as_bool)
        .unwrap_or(false);
    let method = value
        .get("authMethod")
        .and_then(serde_json::Value::as_str)
        .unwrap_or("none")
        .to_string();
    let account = value
        .get("email")
        .or_else(|| value.get("account"))
        .and_then(serde_json::Value::as_str)
        .map(str::to_string);
    let organization = value
        .get("organization")
        .or_else(|| value.get("organizationName"))
        .or_else(|| value.get("orgName"))
        .and_then(serde_json::Value::as_str)
        .map(str::to_string);
    (authenticated, method, account, organization)
}

fn status_kind(
    authenticated: bool,
    method: &str,
    configured_mode: ClaudeAuthMode,
    overrides: &[String],
) -> String {
    if configured_mode == ClaudeAuthMode::ApiKey
        && overrides.iter().any(|v| v == "ANTHROPIC_API_KEY")
    {
        return "api-key".to_string();
    }
    if overrides.iter().any(|v| v == "ANTHROPIC_API_KEY") {
        return "api-key-override".to_string();
    }
    if !authenticated {
        return "not-authenticated".to_string();
    }
    let method_lower = method.to_ascii_lowercase();
    if method_lower.contains("expired") {
        return "expired".to_string();
    }
    if configured_mode == ClaudeAuthMode::Console || method_lower.contains("console") {
        return "console".to_string();
    }
    if method_lower.contains("oauth") || method_lower.contains("claude") {
        return "subscription".to_string();
    }
    "unknown".to_string()
}

#[tauri::command]
pub fn get_claude_auth_status(state: State<AppState>) -> AppResult<ClaudeAuthStatus> {
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let config = auth::read_project_config(&agents_root)?;
    let version = cli_version();
    let overrides = env_overrides();
    let configured_api_key = auth::api_key_available(&agents_root)?;

    let Some(version_value) = version.clone() else {
        return Ok(ClaudeAuthStatus {
            cli_available: false,
            cli_version: None,
            cli_path: resolved_cli_path(),
            authenticated: false,
            method: "cli-not-found".to_string(),
            account: None,
            organization: None,
            env_overrides: overrides,
            configured_mode: config.claude_auth.mode,
            status: "cli-not-found".to_string(),
            checked_at: Utc::now().to_rfc3339(),
        });
    };

    let output = cli_path::command()
        .args(["auth", "status"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|err| AppError::Invalid {
            message: format!("Không kiểm tra được authentication của Claude CLI: {err}"),
        })?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    let parsed = serde_json::from_str::<serde_json::Value>(stdout.trim()).ok();
    let (authenticated, method, account, organization) = parsed
        .as_ref()
        .map(auth_status_from_json)
        .unwrap_or((false, "unknown".to_string(), None, None));
    let status = if configured_api_key {
        "api-key".to_string()
    } else if parsed.is_some() {
        status_kind(authenticated, &method, config.claude_auth.mode, &overrides)
    } else if output.status.success() {
        "unknown".to_string()
    } else {
        "not-authenticated".to_string()
    };

    Ok(ClaudeAuthStatus {
        cli_available: true,
        cli_version: Some(version_value),
        cli_path: resolved_cli_path(),
        authenticated: authenticated || configured_api_key,
        method: if configured_api_key {
            "api-key".to_string()
        } else {
            method
        },
        account,
        organization,
        env_overrides: overrides,
        configured_mode: config.claude_auth.mode,
        status,
        checked_at: Utc::now().to_rfc3339(),
    })
}

#[tauri::command]
pub fn set_claude_auth_mode(
    state: State<AppState>,
    mode: ClaudeAuthMode,
) -> AppResult<ProjectConfig> {
    let project = current_project(&state)?;
    auth::set_mode(PathBuf::from(project.agents_root).as_path(), mode)
}

#[tauri::command]
pub fn save_claude_api_key(state: State<AppState>, api_key: String) -> AppResult<ProjectConfig> {
    let project = current_project(&state)?;
    auth::save_api_key(PathBuf::from(project.agents_root).as_path(), &api_key)
}

#[tauri::command]
pub fn clear_claude_api_key(state: State<AppState>) -> AppResult<ProjectConfig> {
    let project = current_project(&state)?;
    auth::clear_api_key(PathBuf::from(project.agents_root).as_path())
}

/// Starts Claude CLI's own browser login flow. The CLI owns OAuth and its
/// credential storage; the app never receives or persists the OAuth token.
#[tauri::command]
pub fn start_claude_login(state: State<AppState>, mode: ClaudeAuthMode) -> AppResult<()> {
    let project = current_project(&state)?;
    if !matches!(mode, ClaudeAuthMode::Subscription | ClaudeAuthMode::Console) {
        return Err(AppError::Invalid {
            message: "Login flow chỉ hỗ trợ Subscription hoặc Console".to_string(),
        });
    }
    let mut command = cli_path::command();
    command.args(["auth", "login"]);
    if mode == ClaudeAuthMode::Console {
        command.arg("--console");
    }
    command.current_dir(project.agents_root);
    command
        .stdin(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit());
    command.spawn().map_err(|err| AppError::Invalid {
        message: format!("Không mở được Claude login flow: {err}"),
    })?;
    Ok(())
}

#[tauri::command]
pub fn logout_claude(state: State<AppState>) -> AppResult<()> {
    let project = current_project(&state)?;
    cli_path::command()
        .args(["auth", "logout"])
        .current_dir(project.agents_root)
        .stdin(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .spawn()
        .map_err(|err| AppError::Invalid {
            message: format!("Không mở được Claude logout flow: {err}"),
        })?;
    Ok(())
}
