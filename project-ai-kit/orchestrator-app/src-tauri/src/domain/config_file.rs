use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Model {
    Opus,
    Sonnet,
    Haiku,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum PermissionProfile {
    ReadOnly,
    WriteScoped,
    Full,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "kebab-case")]
pub enum ClaudeAuthMode {
    /// Preserve the credential resolution of the user's Claude CLI install.
    #[default]
    CliDefault,
    /// Use the Claude.ai/Pro/Max/Team/Enterprise login managed by Claude CLI.
    Subscription,
    /// Use the Claude Console login/API billing path managed by Claude CLI.
    Console,
    /// Inject an API key from the OS keychain into the child CLI only.
    ApiKey,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClaudeAuthConfig {
    #[serde(default)]
    pub mode: ClaudeAuthMode,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub credential_ref: Option<String>,
}

impl Default for ClaudeAuthConfig {
    fn default() -> Self {
        Self {
            mode: ClaudeAuthMode::CliDefault,
            credential_ref: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentConfig {
    pub model: Model,
    pub max_turns: u32,
    pub permission: PermissionProfile,
    /// True when this agent file no longer exists under `.claude/agents/`
    /// (AC-E1-14) — kept in config.json, not removed, so the Settings
    /// screen can surface it ("không còn trong kit").
    #[serde(default)]
    pub stale: bool,
    /// True for one reconciliation cycle when the agent was just discovered
    /// in `.claude/agents/` and had no prior entry (AC-E1-13, "đánh dấu mới").
    #[serde(default)]
    pub newly_discovered: bool,
    /// AC-E6-21 — per-agent run timeout, minutes. Serde default keeps a
    /// `config.json` written before this field existed deserializing.
    #[serde(default = "default_timeout_minutes")]
    pub timeout_minutes: u32,
}

fn default_timeout_minutes() -> u32 {
    DEFAULT_TIMEOUT_MINUTES
}

fn default_max_retries() -> u32 {
    crate::domain::run_summary::DEFAULT_MAX_RETRIES
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectConfig {
    pub agents: BTreeMap<String, AgentConfig>,
    /// Authentication selection for Claude processes spawned by this
    /// project. Secrets are never stored here; `credential_ref` points to the
    /// OS keychain when `mode` is `ApiKey`.
    #[serde(default)]
    pub claude_auth: ClaudeAuthConfig,
    /// Presentation-only aliases keyed by pipeline slot id (e.g. `ba`,
    /// `qc-design`). This deliberately does not alter the real agent name
    /// used by readiness or Claude CLI spawning.
    #[serde(default, skip_serializing_if = "BTreeMap::is_empty")]
    pub node_nicknames: BTreeMap<String, String>,
    /// AC-E6-23 — project-wide Retry ceiling (default 2). The frontend's
    /// retry gate reads this via `get_config` instead of a hardcoded copy.
    #[serde(default = "default_max_retries")]
    pub max_retries: u32,
    /// B18/AC-E1-26 — which MCP server (by name, from the project's own
    /// MCP config) serves Figma, chosen by the user when detection is
    /// ambiguous. `None` = auto (single candidate or none).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub figma_mcp_server: Option<String>,
    /// Absolute path to the `claude` binary, for the installs
    /// `agentrun::cli_path`'s discovery cannot guess. `None` = auto-detect,
    /// which is the normal case; a packaged app whose user installed the
    /// CLI somewhere unusual is the reason this escape hatch exists.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub claude_cli_path: Option<String>,
    /// AC-E1-19 — Backlog integration, NON-SECRET half only (the API key
    /// itself lives in the OS keychain, see `store::keychain`). `None` =
    /// not configured, which disables Push to Backlog (AC-E5-01).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub backlog: Option<crate::domain::integrations::BacklogConfig>,
}

/// "Model mặc định (chỉnh được)" table, `orchestrator-project-config/SPEC.md`.
/// `design-analyst-agent` is included even though the file does not exist in
/// the kit yet (B17) — reconciliation will mark it `stale` until it does.
const DEFAULT_MODELS: &[(&str, Model)] = &[
    ("ba-agent", Model::Opus),
    ("techlead-design-agent", Model::Opus),
    ("techlead-tasks-agent", Model::Opus),
    ("pm-agent", Model::Sonnet),
    ("design-analyst-agent", Model::Sonnet),
    ("designer-agent", Model::Sonnet),
    ("qc-agent", Model::Sonnet),
    ("backend-agent", Model::Sonnet),
    ("frontend-agent", Model::Sonnet),
    ("mobile-agent", Model::Sonnet),
    ("qa-agent", Model::Sonnet),
    ("qc-automation-agent", Model::Sonnet),
    ("init-agent", Model::Sonnet),
];

/// "Permission profile" table: Dev agents (BE/FE/Mobile) default to `full`,
/// everything else defaults to `write-scoped` (AC-E1-18: "Dev=full, còn lại
/// =write-scoped").
const FULL_PERMISSION_AGENTS: &[&str] = &["backend-agent", "frontend-agent", "mobile-agent"];

/// SPEC does not give a per-agent default for "Max turns" (it's a Settings
/// table column with no stated values). NOTE (A7): the `claude` CLI has no
/// `--max-turns` flag, so this field is displayed/stored but NOT enforced
/// at spawn time — the Settings UI says so explicitly rather than
/// pretending otherwise.
pub const DEFAULT_MAX_TURNS: u32 = 20;

/// AC-E6-21's stated default (30 minutes) — the same value
/// `agentrun::runner::DEFAULT_TIMEOUT` encoded before it became
/// configurable.
pub const DEFAULT_TIMEOUT_MINUTES: u32 = 30;

pub fn default_model_for(agent_name: &str) -> Model {
    DEFAULT_MODELS
        .iter()
        .find(|(name, _)| *name == agent_name)
        .map(|(_, model)| *model)
        .unwrap_or(Model::Sonnet)
}

pub fn default_permission_for(agent_name: &str) -> PermissionProfile {
    if FULL_PERMISSION_AGENTS.contains(&agent_name) {
        PermissionProfile::Full
    } else {
        PermissionProfile::WriteScoped
    }
}

fn default_agent_config(agent_name: &str, newly_discovered: bool) -> AgentConfig {
    AgentConfig {
        model: default_model_for(agent_name),
        max_turns: DEFAULT_MAX_TURNS,
        permission: default_permission_for(agent_name),
        stale: false,
        newly_discovered,
        timeout_minutes: DEFAULT_TIMEOUT_MINUTES,
    }
}

impl ProjectConfig {
    /// Used the very first time `.orchestrator/config.json` is created for a
    /// project (AC-E1-10/18) — nothing is "newly discovered" here, this IS
    /// the baseline.
    pub fn with_defaults(discovered_agent_names: &[String]) -> Self {
        let agents = discovered_agent_names
            .iter()
            .map(|name| (name.clone(), default_agent_config(name, false)))
            .collect();
        ProjectConfig {
            agents,
            node_nicknames: BTreeMap::new(),
            claude_auth: ClaudeAuthConfig::default(),
            max_retries: default_max_retries(),
            figma_mcp_server: None,
            claude_cli_path: None,
            backlog: None,
        }
    }

    /// Reconciles this config against the agents actually found in
    /// `.claude/agents/` right now: newly discovered agents are added with
    /// defaults (AC-E1-13), agents no longer present are marked `stale`
    /// rather than deleted (AC-E1-14), and previously-stale agents that
    /// reappeared are un-marked.
    pub fn reconcile(&mut self, discovered_agent_names: &[String]) {
        for name in discovered_agent_names {
            match self.agents.get_mut(name) {
                Some(existing) => {
                    existing.stale = false;
                    existing.newly_discovered = false;
                }
                None => {
                    self.agents
                        .insert(name.clone(), default_agent_config(name, true));
                }
            }
        }
        for (name, cfg) in self.agents.iter_mut() {
            if !discovered_agent_names.contains(name) {
                cfg.stale = true;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A `config.json` written before `timeout_minutes`/`max_retries`/
    /// `figma_mcp_server` existed must still deserialize with the defaults
    /// filled in — old projects keep working untouched.
    #[test]
    fn old_config_json_without_new_fields_still_deserializes_with_defaults() {
        let old_shape = r#"{
            "agents": {
                "ba-agent": { "model": "opus", "max_turns": 20, "permission": "write-scoped" }
            }
        }"#;
        let config: ProjectConfig = serde_json::from_str(old_shape).unwrap();
        assert_eq!(config.max_retries, 2);
        assert!(config.figma_mcp_server.is_none());
        assert!(config.claude_cli_path.is_none());
        assert!(config.node_nicknames.is_empty());
        assert_eq!(config.agents["ba-agent"].timeout_minutes, 30);
    }

    #[test]
    fn with_defaults_fills_new_fields() {
        let config = ProjectConfig::with_defaults(&["ba-agent".to_string()]);
        assert_eq!(config.max_retries, 2);
        assert!(config.node_nicknames.is_empty());
        assert_eq!(config.agents["ba-agent"].timeout_minutes, 30);
        assert_eq!(config.agents["ba-agent"].max_turns, DEFAULT_MAX_TURNS);
    }
}
