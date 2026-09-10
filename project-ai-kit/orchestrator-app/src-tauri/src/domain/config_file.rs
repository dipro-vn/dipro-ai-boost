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
}

/// "Model mặc định (chỉnh được)" table, `orchestrator-project-config/SPEC.md`.
/// `design-analyst-agent` is included even though the file does not exist in
/// the kit yet (B17) — reconciliation will mark it `stale` until it does.
const DEFAULT_MODELS: &[(&str, Model)] = &[
    ("ba-agent", Model::Opus),
    ("techlead-design-agent", Model::Opus),
    ("techlead-tasks-agent", Model::Opus),
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

/// "Permission profile" table. AC-E1-18 reads "Dev=full, còn lại
/// =write-scoped", and the three Dev agents are still the reason it exists —
/// but `ba-agent` had to join them.
///
/// BA is the only slot that must BOTH call a write-capable MCP (`use_figma`
/// draws Figma Outputs 1-3) and run arbitrary Bash (`mkdocs build` is its
/// Output 5). Under `write-scoped` → `acceptEdits`, a real run had every one
/// of those refused: 5 `Bash` denials and 2 Figma denials in a single
/// `permission_denials` array, and 3 of its 6 outputs missing. `--allowedTools`
/// (see `agentrun::spawn`) fixes the general write-scoped case, but not the
/// one where a claude.ai connector tool is pinned to "ask" by an org policy —
/// allow rules do not apply to those. `bypassPermissions` is the only
/// configuration ever observed at 0 denials.
const FULL_PERMISSION_AGENTS: &[&str] = &[
    "backend-agent",
    "frontend-agent",
    "mobile-agent",
    "ba-agent",
];

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

/// Agent nào cần nhiều hơn 30 phút mặc định. `ba-agent` giao 6 outputs
/// trong MỘT lượt (SPEC.md + 3 frame Figma + HTML prototype + build MkDocs),
/// kèm vòng visual recheck chụp lại từng frame — 30 phút chỉ đủ cho cái đầu
/// tiên, phần còn lại bị cắt giữa chừng thành `RunOutcome::Timeout`.
const AGENT_TIMEOUT_MINUTES: &[(&str, u32)] = &[("ba-agent", 120)];

pub fn default_timeout_minutes_for(agent_name: &str) -> u32 {
    AGENT_TIMEOUT_MINUTES
        .iter()
        .find(|(name, _)| *name == agent_name)
        .map(|(_, minutes)| *minutes)
        .unwrap_or(DEFAULT_TIMEOUT_MINUTES)
}

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
        timeout_minutes: default_timeout_minutes_for(agent_name),
    }
}

impl ProjectConfig {
    /// Used the very first time `.ai-boost/config.json` is created for a
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
                    // Project tạo từ trước giữ nguyên 30 phút trong
                    // `config.json` mãi mãi, kể cả sau khi agent đó được
                    // nâng default. Chỉ nâng khi giá trị đang là default cũ
                    // — y hệt kỷ luật của `SUPERSEDED_KIT_FILES`: giá trị
                    // user đã tự sửa thì không bao giờ đụng vào.
                    if existing.timeout_minutes == DEFAULT_TIMEOUT_MINUTES {
                        existing.timeout_minutes = default_timeout_minutes_for(name);
                    }
                    // Cùng kỷ luật: `WriteScoped` là giá trị MỌI agent
                    // không-phải-Dev nhận từ `default_permission_for` trước
                    // khi `ba-agent` được thêm vào danh sách, nên nó = "vẫn
                    // đang ở default cũ". `ReadOnly` chỉ đạt được khi user tự
                    // chọn trong Settings → không bao giờ bị đụng.
                    //
                    // Cùng giới hạn đã biết như migration timeout ở trên:
                    // user CỐ Ý chọn `write-scoped` cho ba-agent thì không
                    // phân biệt được với default chưa đụng, và sẽ bị nâng.
                    if existing.permission == PermissionProfile::WriteScoped
                        && default_permission_for(name) == PermissionProfile::Full
                    {
                        existing.permission = PermissionProfile::Full;
                    }
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
        let config =
            ProjectConfig::with_defaults(&["ba-agent".to_string(), "qc-agent".to_string()]);
        assert_eq!(config.max_retries, 2);
        assert!(config.node_nicknames.is_empty());
        assert_eq!(config.agents["ba-agent"].timeout_minutes, 120);
        assert_eq!(
            config.agents["ba-agent"].permission,
            PermissionProfile::Full
        );
        assert_eq!(
            config.agents["qc-agent"].permission,
            PermissionProfile::WriteScoped,
            "chỉ BA lên Full, không phải nâng tất cả"
        );
        assert_eq!(
            config.agents["qc-agent"].timeout_minutes,
            DEFAULT_TIMEOUT_MINUTES
        );
        assert_eq!(config.agents["ba-agent"].max_turns, DEFAULT_MAX_TURNS);
    }

    /// Đường duy nhất để default mới tới được project cũ. `ReadOnly` là lựa
    /// chọn có chủ đích của user, không bao giờ được ghi đè.
    #[test]
    fn reconcile_raises_an_untouched_write_scoped_ba_to_full_but_never_a_read_only_one() {
        let names = vec!["ba-agent".to_string(), "qc-agent".to_string()];

        let mut config = ProjectConfig::with_defaults(&names);
        config.agents.get_mut("ba-agent").unwrap().permission = PermissionProfile::WriteScoped;
        config.reconcile(&names);
        assert_eq!(
            config.agents["ba-agent"].permission,
            PermissionProfile::Full
        );

        config.agents.get_mut("ba-agent").unwrap().permission = PermissionProfile::ReadOnly;
        config.reconcile(&names);
        assert_eq!(
            config.agents["ba-agent"].permission,
            PermissionProfile::ReadOnly,
            "lựa chọn có chủ đích của user không bị nâng"
        );

        assert_eq!(
            config.agents["qc-agent"].permission,
            PermissionProfile::WriteScoped,
            "agent ngoài danh sách Full không bị đụng tới"
        );
    }

    /// Project tạo từ trước giữ `config.json` cũ mãi mãi — `reconcile` là
    /// đường duy nhất để default mới tới được chúng. Nhưng chỉ khi giá trị
    /// còn nguyên default cũ: user đã tự chỉnh thì không được đụng vào.
    #[test]
    fn reconcile_raises_an_untouched_default_timeout_but_never_a_customised_one() {
        let mut config = ProjectConfig::with_defaults(&["ba-agent".to_string()]);
        config.agents.get_mut("ba-agent").unwrap().timeout_minutes = DEFAULT_TIMEOUT_MINUTES;
        config.reconcile(&["ba-agent".to_string()]);
        assert_eq!(config.agents["ba-agent"].timeout_minutes, 120);

        config.agents.get_mut("ba-agent").unwrap().timeout_minutes = 45;
        config.reconcile(&["ba-agent".to_string()]);
        assert_eq!(
            config.agents["ba-agent"].timeout_minutes, 45,
            "giá trị user đã sửa không bao giờ bị ghi đè"
        );
    }
}
