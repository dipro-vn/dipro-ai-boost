//! Reads the few fields the Backlog push needs out of a `task-*.md` file.
//!
//! Two shapes exist in the wild and both must work:
//!
//! - **canonical** (`techlead-tasks-agent.md` Bước 6) — a `## Backlog Info`
//!   list plus a `## Metadata` table: `| Estimate | ~4h |`
//! - **legacy** (the `example-project` fixtures) — bold key/value lines
//!   right under the title: `**Estimate:** 4h`
//!
//! This is READ-ONLY by contract (AC-E5-13): nothing in this module, or in
//! anything it is called from, writes back into a task file. Priority is
//! deliberately NOT read — `pm-agent.md` derives it from the phase
//! (Phase 1 → High, otherwise Normal), and the app must not invent a second
//! source of truth for it (AC-E5-06).

use std::path::Path;

use serde::Serialize;

/// One task file as the Backlog panel shows it before pushing.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TaskMeta {
    /// Path relative to the feature directory, e.g.
    /// `backend-repo/tasks/task-2-1.md` — the same key the mapping file and
    /// the agent's prompt use.
    pub relative_path: String,
    /// First heading, trimmed of its `#` — what the PM recognizes the task by.
    pub title: String,
    /// From `| Phase | 2 — ... |`, `**Phase:** 2 (...)`, or the `task-<phase>-<n>.md`
    /// filename as a last resort.
    pub phase: Option<u32>,
    /// Verbatim estimate text (`4h`, `~2.5h`). AC-E5-12: `None` is what the
    /// UI warns about — Estimated Hours is a required Backlog field per
    /// `backlog-workflow.md` §II.a.
    pub estimate: Option<String>,
}

fn strip_markdown_noise(value: &str) -> String {
    value
        .trim()
        .trim_matches(|c| c == '*' || c == '`')
        .trim()
        .to_string()
}

/// `| Estimate | ~4h |` → `~4h`, matching on the row's label column.
fn table_row_value(line: &str, label: &str) -> Option<String> {
    let cells: Vec<&str> = line.split('|').map(str::trim).collect();
    // A markdown row splits into ["", key, value, ""] once trimmed.
    if cells.len() < 4 {
        return None;
    }
    if !strip_markdown_noise(cells[1]).eq_ignore_ascii_case(label) {
        return None;
    }
    let value = strip_markdown_noise(cells[2]);
    (!value.is_empty() && value != "—" && value != "-").then_some(value)
}

/// `**Estimate:** 4h` / `- **Estimate Hour:** 4h` → `4h`.
fn bold_field_value(line: &str, label: &str) -> Option<String> {
    let line = line.trim().trim_start_matches("- ").trim();
    let (key, value) = line.split_once(':')?;
    if !strip_markdown_noise(key).eq_ignore_ascii_case(label) {
        return None;
    }
    let value = strip_markdown_noise(value);
    (!value.is_empty() && value != "—" && value != "-").then_some(value)
}

fn find_field(content: &str, labels: &[&str]) -> Option<String> {
    for line in content.lines() {
        for label in labels {
            if let Some(value) =
                table_row_value(line, label).or_else(|| bold_field_value(line, label))
            {
                return Some(value);
            }
        }
    }
    None
}

/// Leading integer of a phase value: `2 — Service + API` → 2, `2 (API)` → 2.
fn leading_number(value: &str) -> Option<u32> {
    let digits: String = value
        .trim()
        .chars()
        .take_while(char::is_ascii_digit)
        .collect();
    digits.parse().ok()
}

/// `task-2-1.md` → 2. The filename is the fallback when neither the
/// Metadata table nor a bold line carries the phase.
fn phase_from_file_name(file_name: &str) -> Option<u32> {
    file_name
        .strip_prefix("task-")?
        .split(['-', '.'])
        .next()
        .and_then(|part| part.parse().ok())
}

fn first_heading(content: &str) -> String {
    content
        .lines()
        .find(|line| line.trim_start().starts_with('#'))
        .map(|line| line.trim_start().trim_start_matches('#').trim().to_string())
        .unwrap_or_default()
}

/// Parses one task file's content. `relative_path` and `file_name` are
/// passed in rather than derived, so this stays a pure function.
pub fn parse_task_meta(relative_path: &str, file_name: &str, content: &str) -> TaskMeta {
    let estimate = find_field(content, &["Estimate", "Estimate Hour", "Estimated Hours"]);
    let phase = find_field(content, &["Phase"])
        .as_deref()
        .and_then(leading_number)
        .or_else(|| phase_from_file_name(file_name));

    TaskMeta {
        relative_path: relative_path.to_string(),
        title: first_heading(content),
        phase,
        estimate,
    }
}

/// Every `task-*.md` under a feature directory, newest convention or old,
/// sorted by relative path so the UI order is stable. Reuses
/// `stage_rules::task_files_in_repos` so there is one definition of where
/// task files live.
pub fn collect_task_meta(feature_dir: &Path) -> Vec<TaskMeta> {
    let mut metas: Vec<TaskMeta> = crate::inference::stage_rules::task_files_in_repos(feature_dir)
        .into_iter()
        .filter_map(|path| {
            let content = std::fs::read_to_string(&path).ok()?;
            let relative = path
                .strip_prefix(feature_dir)
                .unwrap_or(&path)
                .to_string_lossy()
                .replace('\\', "/");
            let file_name = path.file_name()?.to_string_lossy().to_string();
            Some(parse_task_meta(&relative, &file_name, &content))
        })
        .collect();
    metas.sort_by(|a, b| a.relative_path.cmp(&b.relative_path));
    metas
}

#[cfg(test)]
mod tests {
    use super::*;

    const CANONICAL: &str = r#"# [BE] [H-03-06] — Integrate worry API

## Backlog Info
- **Issue Type:** Task
- **Category:** Backend_API
- **Estimate Hour:** 8h
- **Status:** Open

## Metadata
| Thuộc tính | Giá trị |
|---|---|
| Phase | 2 — Service + API endpoint |
| Repo | `example-api` |
| Estimate | ~4h |

## Mục tiêu
"#;

    const LEGACY: &str = r#"# Task 2-1: API endpoint POST /auth/login

**Phase:** 2 (API endpoint)
**Repo:** example-api
**Estimate:** 4h

## Yêu cầu implement
"#;

    #[test]
    fn reads_canonical_metadata_table() {
        let meta = parse_task_meta("api/tasks/task-2-1.md", "task-2-1.md", CANONICAL);
        assert_eq!(meta.title, "[BE] [H-03-06] — Integrate worry API");
        assert_eq!(meta.phase, Some(2));
        // `## Backlog Info`'s "Estimate Hour" comes first in the file, so it
        // wins — both forms are accepted either way.
        assert_eq!(meta.estimate.as_deref(), Some("8h"));
    }

    #[test]
    fn reads_legacy_bold_fields() {
        let meta = parse_task_meta("api/tasks/task-2-1.md", "task-2-1.md", LEGACY);
        assert_eq!(meta.title, "Task 2-1: API endpoint POST /auth/login");
        assert_eq!(meta.phase, Some(2));
        assert_eq!(meta.estimate.as_deref(), Some("4h"));
    }

    /// AC-E5-12 — the case the preview has to flag.
    #[test]
    fn missing_estimate_is_none_and_phase_falls_back_to_the_file_name() {
        let content = "# Task 3-2: Something\n\n## Mục tiêu\nlàm gì đó\n";
        let meta = parse_task_meta("web/tasks/task-3-2.md", "task-3-2.md", content);
        assert_eq!(meta.estimate, None);
        assert_eq!(meta.phase, Some(3));
    }

    #[test]
    fn placeholder_estimate_counts_as_missing() {
        let content = "# T\n\n| Phase | 1 |\n| Estimate | — |\n";
        let meta = parse_task_meta("a/tasks/task-1-1.md", "task-1-1.md", content);
        assert_eq!(meta.estimate, None);
    }

    #[test]
    fn collects_and_sorts_task_files_across_repo_subdirs() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        for (repo, file, body) in [
            ("web-repo", "task-3-1.md", LEGACY),
            ("api-repo", "task-2-1.md", CANONICAL),
            ("api-repo", "not-a-task.md", LEGACY),
        ] {
            let dir = feature_dir.join(repo).join("tasks");
            std::fs::create_dir_all(&dir).unwrap();
            std::fs::write(dir.join(file), body).unwrap();
        }

        let metas = collect_task_meta(&feature_dir);
        let paths: Vec<&str> = metas.iter().map(|m| m.relative_path.as_str()).collect();
        assert_eq!(
            paths,
            vec!["api-repo/tasks/task-2-1.md", "web-repo/tasks/task-3-1.md"]
        );
    }
}
