//! Reads two things the kit itself defines the shape of:
//!   1. `.claude/agents/*.md` — the list of agent names available.
//!   2. `AGENTS.md`'s `## Repos` table — the Ecosystem list.
//!
//! Parsing is intentionally tolerant (case-insensitive header matching,
//! resilient to extra columns) rather than a strict GFM parser, because the
//! exact table shape after a real project's `/init-kit` run has not been
//! observed byte-for-byte — only the kit's own template
//! (`project-ai-kit/AGENTS.md`) has. See `docs/orchestrator/ASSUMPTIONS-GAPS.md`.

use std::path::Path;

use crate::domain::project::EcosystemRepo;
use crate::error::AppResult;

/// Lists `.claude/agents/*.md` under `agents_root`, returning agent names
/// (filename without extension). Returns `None` if `.claude/agents/` does
/// not exist (AC-E1-05 — caller decides what "not found" means).
pub fn discover_agents(agents_root: &Path) -> Option<Vec<String>> {
    let dir = agents_root.join(".claude").join("agents");
    if !dir.is_dir() {
        return None;
    }
    let mut names: Vec<String> = std::fs::read_dir(&dir)
        .ok()?
        .filter_map(|entry| entry.ok())
        .filter(|entry| entry.path().extension().and_then(|e| e.to_str()) == Some("md"))
        .filter_map(|entry| {
            entry
                .path()
                .file_stem()
                .and_then(|s| s.to_str())
                .map(str::to_owned)
        })
        .collect();
    names.sort();
    Some(names)
}

pub fn has_claude_agents_dir(agents_root: &Path) -> bool {
    agents_root.join(".claude").join("agents").is_dir()
}

/// Looks for a placeholder cell in the kit's convention, e.g. `_(tên repo)_`
/// — an unfilled template row that should not be treated as a real repo.
fn is_placeholder_cell(cell: &str) -> bool {
    let trimmed = cell.trim();
    trimmed.starts_with("_(") && trimmed.ends_with(")_")
}

/// `pub(crate)` — also reused by `inference::api_definition` for parsing
/// the "API Definition" table in `DESIGN.md` (same generic markdown-table
/// shape, different heading to look for).
pub(crate) fn is_table_separator_row(line: &str) -> bool {
    let trimmed = line.trim();
    trimmed.starts_with('|') && trimmed.chars().all(|c| matches!(c, '|' | '-' | ':' | ' '))
}

pub(crate) fn split_table_row(line: &str) -> Vec<String> {
    let trimmed = line.trim().trim_start_matches('|').trim_end_matches('|');
    trimmed
        .split('|')
        .map(|cell| cell.trim().to_string())
        .collect()
}

/// Finds the column index whose header contains any of `keywords`
/// (case-insensitive substring match).
pub(crate) fn find_column(headers: &[String], keywords: &[&str]) -> Option<usize> {
    headers.iter().position(|header| {
        let lower = header.to_lowercase();
        keywords.iter().any(|kw| lower.contains(kw))
    })
}

/// Parses the markdown table under a `## Repos` heading in `AGENTS.md` (or
/// equivalent — matched case-insensitively, tolerant of the section living
/// inside `<ecosystem>` tags per the kit's template). Returns `None` if no
/// such heading/table is found — the caller must not fabricate an empty
/// Ecosystem list vs. "AGENTS.md doesn't have this section" as the same
/// thing (they get different warning messages).
pub fn parse_ecosystem_table(agents_md: &str) -> Option<Vec<(String, String, String, String)>> {
    let lines: Vec<&str> = agents_md.lines().collect();

    let heading_idx = lines.iter().position(|line| {
        let trimmed = line.trim();
        trimmed.starts_with("##") && trimmed.to_lowercase().contains("repos")
    })?;

    // Collect contiguous `|`-prefixed lines after the heading (skipping
    // blank lines before the table starts).
    let mut i = heading_idx + 1;
    while i < lines.len() && lines[i].trim().is_empty() {
        i += 1;
    }
    let table_start = i;
    let mut table_lines: Vec<&str> = Vec::new();
    while i < lines.len() && lines[i].trim_start().starts_with('|') {
        table_lines.push(lines[i]);
        i += 1;
    }
    if table_lines.len() < 2 || table_start >= lines.len() {
        return None; // no header + separator + at least the table shape
    }

    let headers = split_table_row(table_lines[0]);
    let name_idx = find_column(&headers, &["repo"]);
    let path_idx = find_column(&headers, &["đường dẫn", "duong dan", "path"]);
    let role_idx = find_column(&headers, &["vai trò", "vai tro", "role"]);
    let stack_idx = find_column(&headers, &["stack"]);

    let (name_idx, path_idx, role_idx, stack_idx) = match (name_idx, path_idx, role_idx, stack_idx)
    {
        (Some(n), Some(p), Some(r), Some(s)) => (n, p, r, s),
        _ => return None, // table shape doesn't match the kit's convention
    };

    let mut rows = Vec::new();
    for line in table_lines.iter().skip(1) {
        if is_table_separator_row(line) {
            continue;
        }
        let cells = split_table_row(line);
        let get = |idx: usize| cells.get(idx).cloned().unwrap_or_default();
        let name = get(name_idx);
        if name.is_empty() || is_placeholder_cell(&name) {
            continue;
        }
        rows.push((name, get(path_idx), get(role_idx), get(stack_idx)));
    }

    Some(rows)
}

/// Đường dẫn repo khai trong bảng Ecosystem, đã loại ô mẫu chưa điền.
/// Dùng để dò `repositoryRoot`: thư mục nào chứa nhiều repo khai nhất thì
/// gần như chắc chắn là nó — đáng tin hơn heuristic "có con chứa `.git`",
/// vì repo có thể chưa clone, hoặc (như project ví dụ) không phải git repo.
pub fn declared_repo_paths(agents_md: &str) -> Vec<String> {
    parse_ecosystem_table(agents_md)
        .unwrap_or_default()
        .into_iter()
        .map(|(_, declared_path, _, _)| declared_path)
        .filter(|path| !path.is_empty() && !is_placeholder_cell(path))
        .collect()
}

/// Resolves whether a declared repo path exists by trying it against
/// several plausible bases, in order. `AGENTS.md` documents paths as
/// "tương đối" (relative) but does not pin down relative-to-what, and A1
/// showed real projects don't have one consistent root. This never claims
/// "cloned" incorrectly — an absent match always falls through to
/// `cloned: false`, which is the safe direction to be wrong in.
pub fn resolve_repo_cloned(declared_path: &str, candidate_bases: &[&Path]) -> bool {
    let declared = Path::new(declared_path);
    if declared.is_absolute() {
        return declared.is_dir();
    }
    candidate_bases
        .iter()
        .any(|base| base.join(declared).is_dir())
}

pub fn build_ecosystem(
    agents_md: &str,
    candidate_bases: &[&Path],
) -> AppResult<Option<Vec<EcosystemRepo>>> {
    let Some(rows) = parse_ecosystem_table(agents_md) else {
        return Ok(None);
    };
    let repos = rows
        .into_iter()
        .map(|(name, declared_path, role, stack)| EcosystemRepo {
            cloned: resolve_repo_cloned(&declared_path, candidate_bases),
            name,
            declared_path,
            role,
            stack,
        })
        .collect();
    Ok(Some(repos))
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The kit's own unfilled template, verbatim from `project-ai-kit/AGENTS.md`.
    const KIT_TEMPLATE_UNFILLED: &str = r#"
## Repos

| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| _(tên repo)_ | _(đường dẫn tương đối)_ | backend / frontend / mobile / other | _(NestJS / React / Flutter / ...)_ |

Mỗi repo có 1 **Epic code** ngắn tham chiếu xuyên suốt SPEC/DESIGN/task/Screen Code.
"#;

    const FILLED_ECOSYSTEM: &str = r#"
## Repos

| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| es-kitchen-api | es-kitchen-repository/es-kitchen-api | backend | NestJS |
| es-kitchen-web-admin | es-kitchen-repository/es-kitchen-web-admin | frontend | React |
| es-kitchen-webapp-driver | es-kitchen-repository/es-kitchen-webapp-driver | mobile | Flutter |

## Actors
"#;

    #[test]
    fn unfilled_template_yields_no_rows_not_none() {
        // Table shape is valid (headers match), but every row is a
        // placeholder — must be Some(vec![]), NOT None, so the caller can
        // distinguish "no ## Repos section" from "section exists but empty".
        let rows = parse_ecosystem_table(KIT_TEMPLATE_UNFILLED).expect("table shape recognized");
        assert!(rows.is_empty());
    }

    #[test]
    fn missing_repos_heading_yields_none() {
        assert!(parse_ecosystem_table("## Actors\n\nno repos section here").is_none());
    }

    #[test]
    fn filled_table_parses_three_repos_and_stops_at_next_heading() {
        let rows = parse_ecosystem_table(FILLED_ECOSYSTEM).expect("rows found");
        assert_eq!(rows.len(), 3);
        assert_eq!(
            rows[0],
            (
                "es-kitchen-api".to_string(),
                "es-kitchen-repository/es-kitchen-api".to_string(),
                "backend".to_string(),
                "NestJS".to_string(),
            )
        );
        assert_eq!(rows[2].0, "es-kitchen-webapp-driver");
    }

    #[test]
    fn cloned_repo_found_via_repository_root_base() {
        let tmp = tempfile::tempdir().unwrap();
        let repo_dir = tmp.path().join("es-kitchen-api");
        std::fs::create_dir_all(&repo_dir).unwrap();

        assert!(resolve_repo_cloned("es-kitchen-api", &[tmp.path()]));
    }

    #[test]
    fn uncloned_repo_never_falsely_reported_as_cloned() {
        let tmp = tempfile::tempdir().unwrap();
        assert!(!resolve_repo_cloned("does-not-exist", &[tmp.path()]));
    }

    #[test]
    fn discover_agents_returns_none_when_claude_agents_missing() {
        let tmp = tempfile::tempdir().unwrap();
        assert!(discover_agents(tmp.path()).is_none());
        assert!(!has_claude_agents_dir(tmp.path()));
    }

    #[test]
    fn discover_agents_lists_md_files_only_sorted() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_dir = tmp.path().join(".claude").join("agents");
        std::fs::create_dir_all(&agents_dir).unwrap();
        std::fs::write(agents_dir.join("qc-agent.md"), "").unwrap();
        std::fs::write(agents_dir.join("ba-agent.md"), "").unwrap();
        std::fs::write(agents_dir.join("README.md.bak"), "").unwrap(); // not .md

        let agents = discover_agents(tmp.path()).expect("dir exists");
        assert_eq!(agents, vec!["ba-agent", "qc-agent"]);
        assert!(has_claude_agents_dir(tmp.path()));
    }
}
