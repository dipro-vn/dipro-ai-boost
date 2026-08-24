use serde::{Deserialize, Serialize};

/// The NON-SECRET half of the Backlog integration — this is what lands in
/// `config.json` (AC-E1-19: opening that file in a text editor must show
/// only a reference name, never the API key itself, which lives in the OS
/// keychain under `credential_ref`).
///
/// Field naming follows `ProjectConfig`'s snake_case (it is the one domain
/// type in this codebase without `rename_all = "camelCase"` — see the
/// warning above `ProjectConfig` in `config_file.rs` and its TS mirror).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BacklogConfig {
    /// Full host, e.g. `example.backlog.com` — matches the kit MCP server's
    /// `BACKLOG_DOMAIN` shape rather than the bare space name, since Nulab
    /// also serves `.backlog.jp` / `.backlog.tool`.
    pub domain: String,
    /// Project key as shown in issue keys, e.g. `PROJ` in `PROJ-123`.
    pub project_key: String,
    /// Keychain account name the API key is stored under — a POINTER, not
    /// the secret. Always equals `domain` today; kept explicit so a future
    /// multi-account setup doesn't have to change the file format.
    pub credential_ref: String,
}

/// What the Settings screen needs to render the Backlog section. Contains
/// no secret: the API key is never returned to the frontend once saved.
#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BacklogStatus {
    pub configured: bool,
    pub domain: String,
    pub project_key: String,
    /// AC-E1-22 — false disables the whole integration section in the UI.
    pub keychain_available: bool,
    /// Present when `keychain_available` is false: why it failed, verbatim.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub keychain_error: Option<String>,
}

/// One mapped issue's last known state (AC-E5-14/17).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BacklogIssueStatus {
    pub issue_key: String,
    /// Path relative to the feature dir — joins back to `TaskMeta`.
    pub task_file: String,
    /// Verbatim Backlog status name (`Open`, `In-Progress`, …). `None` when
    /// the issue is gone or the payload lacked a status.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub status_name: Option<String>,
    /// AC-E5-17 — the issue no longer exists on Backlog. The app flags it
    /// and stops there; it never recreates anything.
    #[serde(default)]
    pub not_found: bool,
}

/// Persisted result of the last status pull, plus the task-file hashes that
/// drive drift detection (AC-E5-18).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BacklogStatusCache {
    /// RFC3339 of the last SUCCESSFUL pull — the "số liệu lúc …" label.
    pub fetched_at: String,
    pub issues: Vec<BacklogIssueStatus>,
    /// `task file → sha256` at the time of that pull.
    #[serde(default)]
    pub task_hashes: std::collections::BTreeMap<String, String>,
    /// AC-E5-16 — true when this is the previous cache being shown because
    /// the latest refresh failed. Only ever written to disk as `false` (the
    /// cache file is written on success alone), but it must stay
    /// serializable: the frontend reads it off the command's return value.
    #[serde(default)]
    pub stale: bool,
    /// Why the refresh failed, when `stale` is true.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    /// AC-E1-19 — the serialized form must never carry anything that could
    /// be mistaken for a secret field.
    #[test]
    fn backlog_config_json_holds_only_a_reference_not_a_key() {
        let config = BacklogConfig {
            domain: "example.backlog.com".to_string(),
            project_key: "PROJ".to_string(),
            credential_ref: "example.backlog.com".to_string(),
        };
        let json = serde_json::to_string(&config).unwrap();
        assert!(json.contains("credential_ref"));
        assert!(!json.contains("api_key"));
        assert!(!json.contains("apiKey"));
    }
}
