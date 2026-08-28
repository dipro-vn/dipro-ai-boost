use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum ProjectInitStatus {
    Ready,
    NeedsInit,
    MissingKit,
    Invalid,
}

/// The 3 independent roots the user provides (AC-E1-02). Deliberately NOT
/// nested under one another in the type system — A1 proved a real project
/// (ESKITCHEN) has `repositoryRoot` as a *sibling* of `agentsRoot`'s parent,
/// not a descendant of it. Never assume a parent/child relationship exists.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProjectPaths {
    pub agents_root: String,
    pub docs_root: String,
    pub repository_root: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DetectedPaths {
    pub agents_root: Option<String>,
    pub docs_root: Option<String>,
    pub repository_root: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EcosystemRepo {
    pub name: String,
    /// Path exactly as written in `AGENTS.md`'s Ecosystem table — shown
    /// verbatim so a mismatch is visible to the user, not silently resolved.
    pub declared_path: String,
    /// Exactly as written in the Vai trò cell — prose and all, because the
    /// Launcher's Ecosystem table shows it verbatim and the human note
    /// people put there ("frontend — nơi landing page được implement") is
    /// worth keeping.
    pub role: String,
    /// The role the pipeline can actually act on, derived from `role` by
    /// `agents_reader::canonical_role`. `None` when the cell couldn't be
    /// read confidently — every role comparison in the app matches on THIS,
    /// never on `role`, so a qualifier in the cell can't hide a repo from
    /// the slot that targets it.
    #[serde(default)]
    pub role_key: Option<String>,
    pub stack: String,
    pub cloned: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProjectSummary {
    pub paths: ProjectPaths,
    pub label: String,
    /// True when `.claude/agents/` could not be found at `agentsRoot`
    /// (AC-E1-05) — the app still opens, agent-running features stay
    /// disabled.
    pub read_only: bool,
    pub ecosystem: Vec<EcosystemRepo>,
    pub agents_found: Vec<String>,
    pub warnings: Vec<String>,
    /// Nhóm khung kit chưa có trên đĩa (`store::kit_template`). Launcher dùng
    /// để hiện nút bổ sung scaffold; không phản ánh semantic `/init-kit`.
    pub missing_kit: Vec<crate::store::kit_template::KitGroup>,
    /// Semantic setup status is separate from `read_only`: a scaffolded
    /// project has agents on disk but still needs `/init-kit` before agents
    /// can be run safely.
    pub init_status: ProjectInitStatus,
    pub init_reasons: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RecentProjectEntry {
    pub label: String,
    pub agents_root: String,
    pub docs_root: String,
    pub repository_root: String,
    /// RFC3339 timestamp, stamped by `open_project` at call time.
    pub last_opened_at: String,
}
