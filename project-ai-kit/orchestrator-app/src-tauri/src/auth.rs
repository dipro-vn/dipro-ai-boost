use std::path::Path;

use sha2::{Digest, Sha256};

use crate::agentrun::cli_path;
use crate::domain::config_file::{ClaudeAuthMode, ProjectConfig};
use crate::error::{AppError, AppResult};
use crate::store::atomic_write::write_json_atomic;
use crate::store::keychain;
use crate::store::orchestrator_dir;

pub struct ResolvedClaudeAuth {
    pub mode: ClaudeAuthMode,
    pub api_key: Option<String>,
}

pub fn read_project_config(agents_root: &Path) -> AppResult<ProjectConfig> {
    let path = orchestrator_dir::config_json_path(agents_root);
    if let Some(config) = std::fs::read_to_string(&path)
        .ok()
        .and_then(|raw| serde_json::from_str::<ProjectConfig>(&raw).ok())
    {
        return Ok(config);
    }

    Ok(ProjectConfig::with_defaults(&[]))
}

/// The secret account is deterministic per agentsRoot but does not expose the
/// project path in Keychain account listings.
pub fn claude_api_key_account(agents_root: &Path) -> String {
    let mut hasher = Sha256::new();
    hasher.update(agents_root.to_string_lossy().as_bytes());
    format!("project-{:x}", hasher.finalize())
}

pub fn resolve_for_spawn(agents_root: &Path) -> AppResult<ResolvedClaudeAuth> {
    let config = read_project_config(agents_root)?;
    let mode = config.claude_auth.mode;
    if matches!(mode, ClaudeAuthMode::Subscription | ClaudeAuthMode::Console)
        || (mode == ClaudeAuthMode::CliDefault && !has_environment_credential())
    {
        ensure_cli_login()?;
    }
    let api_key = if mode == ClaudeAuthMode::ApiKey {
        let account = config.claude_auth.credential_ref.as_deref().unwrap_or("");
        let account = if account.is_empty() {
            claude_api_key_account(agents_root)
        } else {
            account.to_string()
        };
        keychain::read_claude_api_key(&account)?.ok_or_else(|| AppError::Invalid {
            message: "Chưa tìm thấy Claude API key trong OS keychain — hãy lưu key trong Settings → Authentication".to_string(),
        })?
    } else {
        String::new()
    };

    Ok(ResolvedClaudeAuth {
        mode,
        api_key: (mode == ClaudeAuthMode::ApiKey).then_some(api_key),
    })
}

fn has_environment_credential() -> bool {
    [
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CODE_API_KEY_HELPER",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "ANTHROPIC_PROFILE",
    ]
    .iter()
    .any(|name| std::env::var_os(name).is_some())
}

pub fn api_key_available(agents_root: &Path) -> AppResult<bool> {
    let config = read_project_config(agents_root)?;
    if config.claude_auth.mode != ClaudeAuthMode::ApiKey {
        return Ok(false);
    }
    let account = config
        .claude_auth
        .credential_ref
        .as_deref()
        .filter(|value| !value.is_empty())
        .map(str::to_string)
        .unwrap_or_else(|| claude_api_key_account(agents_root));
    Ok(keychain::read_claude_api_key(&account)?.is_some())
}

fn ensure_cli_login() -> AppResult<()> {
    let output = cli_path::command()
        .args(["auth", "status"])
        .output()
        .map_err(|err| AppError::Invalid {
            message: format!("Không kiểm tra được Claude CLI login: {err}"),
        })?;
    let logged_in = serde_json::from_slice::<serde_json::Value>(&output.stdout)
        .ok()
        .and_then(|value| value.get("loggedIn").and_then(serde_json::Value::as_bool))
        .unwrap_or(false);
    if !logged_in {
        return Err(AppError::Invalid {
            message: "Claude CLI chưa đăng nhập — vào Settings → Authentication để connect account"
                .to_string(),
        });
    }
    Ok(())
}

pub fn set_mode(agents_root: &Path, mode: ClaudeAuthMode) -> AppResult<ProjectConfig> {
    let mut config = read_project_config(agents_root)?;
    config.claude_auth.mode = mode;
    let path = orchestrator_dir::config_json_path(agents_root);
    write_json_atomic(&path, &config)?;
    Ok(config)
}

pub fn save_api_key(agents_root: &Path, api_key: &str) -> AppResult<ProjectConfig> {
    let trimmed = api_key.trim();
    if trimmed.is_empty() {
        return Err(AppError::Invalid {
            message: "Claude API key không được để trống".to_string(),
        });
    }

    let mut config = read_project_config(agents_root)?;
    let account = config
        .claude_auth
        .credential_ref
        .clone()
        .unwrap_or_else(|| claude_api_key_account(agents_root));
    keychain::save_claude_api_key(&account, trimmed)?;
    config.claude_auth.mode = ClaudeAuthMode::ApiKey;
    config.claude_auth.credential_ref = Some(account);
    let path = orchestrator_dir::config_json_path(agents_root);
    write_json_atomic(&path, &config)?;
    Ok(config)
}

pub fn clear_api_key(agents_root: &Path) -> AppResult<ProjectConfig> {
    let mut config = read_project_config(agents_root)?;
    let account = config
        .claude_auth
        .credential_ref
        .clone()
        .unwrap_or_else(|| claude_api_key_account(agents_root));
    keychain::delete_claude_api_key(&account)?;
    config.claude_auth = Default::default();
    let path = orchestrator_dir::config_json_path(agents_root);
    write_json_atomic(&path, &config)?;
    Ok(config)
}
