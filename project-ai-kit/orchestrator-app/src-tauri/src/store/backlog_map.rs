//! `task file ↔ issue key` mapping (AC-E5-09) — written by `pm-agent`
//! during a push (one entry appended per created issue, so an interrupted
//! batch keeps everything it already created — AC-E5-10) and read back here
//! to drive "what still needs pushing" (AC-E5-11) and the status refresh.
//!
//! Reading is deliberately forgiving, like `store::contract_lock`: a file
//! the agent left half-written must degrade to "no mapping yet" plus a
//! warning, never to an error that blocks the screen.

use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::store::orchestrator_dir;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BacklogIssueLink {
    /// Path relative to the feature dir — same key `task_meta::TaskMeta`
    /// uses, so the two join without normalization.
    pub task_file: String,
    pub issue_key: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub phase: Option<u32>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BacklogMapping {
    #[serde(default)]
    pub issues: Vec<BacklogIssueLink>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pushed_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parent_issue: Option<String>,
}

/// `(mapping, warning)` — the warning is `Some` when a file exists but
/// could not be parsed, so the UI can say so instead of silently pretending
/// nothing was ever pushed (which would risk duplicate issues).
pub fn read_mapping(agents_root: &Path, feature: &str) -> (BacklogMapping, Option<String>) {
    let path = orchestrator_dir::backlog_mapping_path(agents_root, feature);
    let Ok(raw) = std::fs::read_to_string(&path) else {
        return (BacklogMapping::default(), None);
    };
    match serde_json::from_str::<BacklogMapping>(&raw) {
        Ok(mapping) => (mapping, None),
        Err(err) => (
            BacklogMapping::default(),
            Some(format!(
                "Không đọc được {} ({err}) — app coi như chưa có issue nào; kiểm tra file trước khi đẩy lại để tránh tạo trùng.",
                path.display()
            )),
        ),
    }
}

/// Creates the directory the agent is told to write its mapping into, so a
/// failed `mkdir` never gets blamed on the agent.
pub fn ensure_mapping_dir(agents_root: &Path, feature: &str) -> std::io::Result<()> {
    std::fs::create_dir_all(orchestrator_dir::backlog_dir(agents_root, feature))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn missing_file_is_an_empty_mapping_without_a_warning() {
        let tmp = tempfile::tempdir().unwrap();
        let (mapping, warning) = read_mapping(tmp.path(), "feature-a");
        assert!(mapping.issues.is_empty());
        assert!(warning.is_none());
    }

    #[test]
    fn reads_what_the_agent_wrote() {
        let tmp = tempfile::tempdir().unwrap();
        ensure_mapping_dir(tmp.path(), "feature-a").unwrap();
        std::fs::write(
            orchestrator_dir::backlog_mapping_path(tmp.path(), "feature-a"),
            r#"{"issues":[{"taskFile":"api/tasks/task-1-1.md","issueKey":"PROJ-11","phase":1}],"pushedAt":"2026-08-18T00:00:00Z","parentIssue":"PROJ-1"}"#,
        )
        .unwrap();

        let (mapping, warning) = read_mapping(tmp.path(), "feature-a");
        assert!(warning.is_none());
        assert_eq!(mapping.issues.len(), 1);
        assert_eq!(mapping.issues[0].issue_key, "PROJ-11");
        assert_eq!(mapping.parent_issue.as_deref(), Some("PROJ-1"));
    }

    /// A half-written file must warn rather than look like "nothing pushed".
    #[test]
    fn corrupt_file_warns_instead_of_silently_reporting_nothing() {
        let tmp = tempfile::tempdir().unwrap();
        ensure_mapping_dir(tmp.path(), "feature-a").unwrap();
        std::fs::write(
            orchestrator_dir::backlog_mapping_path(tmp.path(), "feature-a"),
            r#"{"issues":[{"taskFile":"a.md","#,
        )
        .unwrap();

        let (mapping, warning) = read_mapping(tmp.path(), "feature-a");
        assert!(mapping.issues.is_empty());
        assert!(warning.unwrap().contains("tạo trùng"));
    }

    /// Old files without the optional fields still load (the agent writes
    /// incrementally and may not have filled them in yet).
    #[test]
    fn tolerates_missing_optional_fields() {
        let mapping: BacklogMapping =
            serde_json::from_str(r#"{"issues":[{"taskFile":"a.md","issueKey":"P-1"}]}"#).unwrap();
        assert_eq!(mapping.issues[0].phase, None);
        assert!(mapping.pushed_at.is_none());
    }
}
