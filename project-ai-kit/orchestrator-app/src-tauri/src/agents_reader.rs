//! Reads two things the kit itself defines the shape of:
//!   1. `.claude/agents/*.md` — the list of agent names available.
//!   2. `AGENTS.md`'s `## Repos` table — the Ecosystem list.
//!
//! Parsing is intentionally tolerant (case-insensitive header matching,
//! resilient to extra columns) rather than a strict GFM parser, because the
//! exact table shape after a real project's `/init-kit` run has not been
//! observed byte-for-byte — only the kit's own template
//! (`project-ai-kit/AGENTS.md`) has. See `docs/orchestrator/ASSUMPTIONS-GAPS.md`.

use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use crate::domain::project::{EcosystemRepo, ProjectInitStatus};
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

/// The MCP servers an agent file's `tools:` allowlist actually names, as
/// `mcp__<prefix>__…` prefixes (`figma-bridge`, `claude_ai_Figma`, …).
///
/// This matters because `tools:` is an inventory, not a hint: a tool absent
/// from it cannot be called even when its MCP server is connected and
/// healthy (the kit says so itself, in `design-analyst-agent.md`'s "LƯU Ý
/// KHI THÊM MCP FIGMA MỚI" note). So a project configured with a Figma
/// server whose name no agent file spells out gets a spawned agent whose
/// every Figma call fails, with nothing to explain why. Comparing this
/// against `commands::agentrun::resolved_figma_server` turns that into a
/// named reason before the agent is ever started.
///
/// Deliberately a line scan, not a YAML parse — the crate has no YAML
/// dependency and the shape needed is one flat list of scalars. Comment
/// lines are skipped: the kit's agent files carry more comment than list
/// inside `tools:`.
///
/// `None` when there is no `tools:` key to read — a missing file, no
/// frontmatter, or an agent that simply doesn't restrict its tools. That is
/// NOT the same as an empty set: an agent with no `tools:` allowlist is
/// unrestricted and can call any connected server, so callers must not
/// treat it as "declares nothing" and block it.
pub fn declared_mcp_servers(agents_root: &Path, agent_name: &str) -> Option<BTreeSet<String>> {
    let path = agents_root
        .join(".claude")
        .join("agents")
        .join(format!("{agent_name}.md"));
    let raw = std::fs::read_to_string(&path).ok()?;
    mcp_servers_in_tools_block(&raw)
}

/// The `declared_mcp_servers` body, split out so it can be tested against
/// the kit's real agent files via `include_str!` rather than a fixture that
/// might drift from them.
fn mcp_servers_in_tools_block(raw: &str) -> Option<BTreeSet<String>> {
    let mut servers = BTreeSet::new();
    let mut in_frontmatter = false;
    let mut in_tools = false;
    let mut saw_tools_key = false;

    for line in raw.lines() {
        let trimmed = line.trim();
        if trimmed == "---" {
            // Opening fence, then the closing one — nothing past the
            // frontmatter can declare tools.
            if in_frontmatter {
                break;
            }
            in_frontmatter = true;
            continue;
        }
        if !in_frontmatter || trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }

        if let Some(item) = trimmed.strip_prefix("- ") {
            if in_tools {
                if let Some(rest) = item.trim().strip_prefix("mcp__") {
                    if let Some((server, _tool)) = rest.split_once("__") {
                        servers.insert(server.to_string());
                    }
                }
            }
            continue;
        }
        // Any other non-indented key ends the `tools:` list (`skills:`,
        // `model:`, …).
        in_tools = trimmed == "tools:";
        saw_tools_key |= in_tools;
    }

    saw_tools_key.then_some(servers)
}

pub fn has_claude_agents_dir(agents_root: &Path) -> bool {
    agents_root.join(".claude").join("agents").is_dir()
}

/// Determines whether the project has completed the human-driven kit setup.
/// Scaffold files alone are not enough: `AGENTS.md` must contain a real
/// project name/domain and at least one real Ecosystem repo.
pub fn assess_init_status(
    agents_md: Option<&str>,
    has_agents_dir: bool,
) -> (ProjectInitStatus, Vec<String>) {
    if !has_agents_dir {
        return (
            ProjectInitStatus::MissingKit,
            vec!["Thiếu thư mục .claude/agents/".to_string()],
        );
    }

    let Some(content) = agents_md else {
        return (
            ProjectInitStatus::MissingKit,
            vec!["Không tìm thấy AGENTS.md tại agentsRoot".to_string()],
        );
    };

    // Chỉ cần bảng `## Repos` đúng cấu trúc; bảng RỖNG vẫn hợp lệ. Init kit
    // trước rồi clone repo sau là luồng bình thường, và lúc `repos/` còn rỗng
    // thì init-agent giữ nguyên dòng placeholder của kit — `is_placeholder_cell`
    // loại dòng đó nên bảng đọc ra rỗng. Trước đây rỗng bị tính là chưa init,
    // hệ quả là project kiểu đó kẹt ở `NeedsInit` vĩnh viễn và terminal
    // init-kit không bao giờ tự đóng. Board vẫn hiện node Build và tự báo
    // "không áp dụng" khi không có repo, nên chặn ở đây là thừa.
    if parse_ecosystem_table(content).is_none() {
        return (
            ProjectInitStatus::Invalid,
            vec!["AGENTS.md không có bảng ## Repos đúng cấu trúc".to_string()],
        );
    }

    let mut reasons = Vec::new();
    if content.contains("<PROJECT_NAME>") || content.contains("\\<PROJECT_NAME\\>") {
        reasons.push("Chưa điền tên project".to_string());
    }
    let domain_line = content.lines().find(|line| line.contains("**Domain:**"));
    if domain_line.is_none()
        || domain_line.is_some_and(|line| line.contains("1-2 câu") || line.contains("điền qua"))
    {
        reasons.push("Chưa điền domain nghiệp vụ".to_string());
    }
    // `<DOCS_ROOT>` is the bullet's LABEL in the template, not its value:
    // `- **`<DOCS_ROOT>`:** <giá trị>`. A real init fills the value and may
    // keep the label AND the descriptive prose after it, e.g.
    //   - **`<DOCS_ROOT>`:** `docs/` — single long-memory chứa …
    // so neither the literal `<DOCS_ROOT>` nor that prose says anything
    // about whether setup ran. `<memory_update_gate>` also keeps
    // `<DOCS_ROOT>` on purpose, as a generic path pattern.
    //
    // What actually distinguishes unfilled is the VALUE right after `:**`:
    // the template starts it with its own description and still carries the
    // `<project>-docs` example placeholder.
    //
    // A missing bullet is deliberately NOT a reason here (unlike Domain):
    // an init that replaced the label with the real path is also valid, and
    // the repo table + Domain already catch a project that never ran init.
    let docs_root_value = content
        .lines()
        .find(|line| line.trim_start().starts_with("- **") && line.contains("DOCS_ROOT"))
        .and_then(|line| line.split_once(":**"))
        .map(|(_, value)| value.trim());
    if docs_root_value.is_some_and(|value| {
        value.starts_with("single long-memory") || value.contains("<project>-docs")
    }) {
        reasons.push("Chưa điền DOCS_ROOT".to_string());
    }
    if reasons.is_empty() {
        (ProjectInitStatus::Ready, reasons)
    } else {
        (ProjectInitStatus::NeedsInit, reasons)
    }
}

/// Reads the same AGENTS.md locations that project opening accepts, so the
/// spawn guard and Launcher cannot disagree about whether setup is complete.
pub fn read_init_status(agents_root: &Path) -> (ProjectInitStatus, Vec<String>) {
    let mut candidates = vec![agents_root.join("AGENTS.md")];
    if let Some(parent) = agents_root.parent() {
        candidates.push(parent.join("AGENTS.md"));
    }
    let content = candidates
        .into_iter()
        .find_map(|path| std::fs::read_to_string(path).ok());
    assess_init_status(content.as_deref(), has_claude_agents_dir(agents_root))
}

/// Looks for a placeholder cell in the kit's convention, e.g. `_(tên repo)_`
/// — an unfilled template row that should not be treated as a real repo.
fn is_placeholder_cell(cell: &str) -> bool {
    let trimmed = cell.trim();
    trimmed.starts_with("_(") && trimmed.ends_with(")_")
}

/// Strips markdown emphasis from a cell that is an IDENTIFIER (repo name,
/// path) rather than prose. `/init-kit` writes these in backticks often
/// enough that a literal read breaks everything downstream: a
/// `declared_path` of `` `repos/frontend` `` makes `resolve_repo_path`
/// look for a directory whose name contains backticks, so a repo sitting
/// right there on disk reads as "not cloned".
///
/// Not applied to the Stack column (prose, display-only) nor destructively
/// to the Vai trò column — that one keeps its text for display and gets a
/// derived key instead (`canonical_role`).
fn strip_cell_decoration(cell: &str) -> String {
    let mut trimmed = cell.trim();
    loop {
        let stripped = trimmed
            .strip_prefix("**")
            .and_then(|rest| rest.strip_suffix("**"))
            .or_else(|| {
                trimmed
                    .strip_prefix("__")
                    .and_then(|rest| rest.strip_suffix("__"))
            })
            .or_else(|| {
                trimmed
                    .strip_prefix('`')
                    .and_then(|rest| rest.strip_suffix('`'))
            })
            .or_else(|| {
                trimmed
                    .strip_prefix('*')
                    .and_then(|rest| rest.strip_suffix('*'))
            })
            .or_else(|| {
                trimmed
                    .strip_prefix('_')
                    .and_then(|rest| rest.strip_suffix('_'))
            });
        match stripped {
            Some(inner) => trimmed = inner.trim(),
            None => break,
        }
    }
    trimmed.to_string()
}

/// The repo roles the pipeline knows how to target — `slot_repo_role`'s
/// range. `other` is deliberately absent: it is a valid thing to write in
/// `AGENTS.md`, but no slot targets it, so it stays unmatched.
const KNOWN_ROLES: &[&str] = &["backend", "frontend", "mobile"];

/// Reads a repo role out of the free-text "Vai trò" cell.
///
/// That cell is written by hand (and by `/init-kit`, whose instructions
/// never forbade qualifiers), so in the field it is prose, not an enum:
/// `frontend — nơi landing page được implement` has to read as `frontend`.
/// Every consumer used to compare the whole cell with `eq_ignore_ascii_case`,
/// which meant a fully-configured project reported "no repo with role
/// frontend" while `repos/frontend` sat on disk.
///
/// Returns `None` when the cell can't be read confidently. Callers must
/// surface that to the user rather than guessing a role — the app's rule is
/// that `AGENTS.md` is the source of truth and it never fills in a value it
/// only suspects (AC-E1-03).
pub fn canonical_role(role_cell: &str) -> Option<&'static str> {
    // Emphasis is stripped wherever it sits, not just around the whole
    // cell: `**Frontend** (web admin)` has its markers in the middle, so
    // unwrapping alone would leave `**frontend**` and read as unknown.
    // Only ` and * are removed blindly — neither ever occurs inside a word,
    // whereas `_` does, so that one stays with the unwrap-only path.
    let cell = strip_cell_decoration(role_cell)
        .replace(['`', '*'], "")
        .to_lowercase();
    let cell = strip_cell_decoration(&cell);

    // The kit's own placeholder is `backend / frontend / mobile / other`.
    // Taking the leading token there would silently label an undeclared
    // repo `backend`, so a cell that offers several roles counts as
    // unfilled, not as its first option.
    if KNOWN_ROLES
        .iter()
        .filter(|role| contains_word(&cell, role))
        .count()
        > 1
    {
        return None;
    }

    let head = leading_token(&cell);
    KNOWN_ROLES.iter().find(|role| **role == head).copied()
}

/// Whole-word containment, so `frontend` doesn't match inside a longer
/// word. Word chars here are alphanumerics — every separator the role cell
/// realistically uses (space, `/`, `—`, `,`, `(`) is not one.
fn contains_word(haystack: &str, needle: &str) -> bool {
    haystack
        .match_indices(needle)
        .any(|(start, matched)| {
            let before = haystack[..start].chars().next_back();
            let after = haystack[start + matched.len()..].chars().next();
            !before.is_some_and(char::is_alphanumeric)
                && !after.is_some_and(char::is_alphanumeric)
        })
}

/// The cell up to its first separator — what's left is the role itself when
/// the rest of the cell is a human note. A bare `-` is only a separator
/// when it has space around it, so a hyphenated word survives intact
/// (`front-end` stays `front-end`, and therefore stays unrecognized rather
/// than being silently read as `front`).
fn leading_token(cell: &str) -> String {
    let mut cut = cell.len();
    for (idx, ch) in cell.char_indices() {
        let is_separator = matches!(ch, '—' | '–' | '(' | '/' | ',' | ':' | '·' | ';')
            || (ch == '-'
                && cell[..idx].ends_with(' ')
                && cell[idx + ch.len_utf8()..].starts_with(' '));
        if is_separator {
            cut = idx;
            break;
        }
    }
    cell[..cut].trim().to_string()
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
        .map(|path| strip_cell_decoration(&path))
        .filter(|path| !path.is_empty())
        .collect()
}

/// Resolves whether a declared repo path exists by trying it against
/// several plausible bases, in order. `AGENTS.md` documents paths as
/// "tương đối" (relative) but does not pin down relative-to-what, and A1
/// showed real projects don't have one consistent root. This never claims
/// "cloned" incorrectly — an absent match always falls through to
/// `cloned: false`, which is the safe direction to be wrong in.
pub fn resolve_repo_path(declared_path: &str, candidate_bases: &[&Path]) -> Option<PathBuf> {
    let declared = Path::new(declared_path);
    if declared.is_absolute() {
        return declared.is_dir().then(|| declared.to_path_buf());
    }
    candidate_bases
        .iter()
        .map(|base| base.join(declared))
        .find(|candidate| candidate.is_dir())
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
        .map(|(name, declared_path, role, stack)| {
            // Name and path are identifiers: decoration comes off before
            // anything resolves them against disk or against a feature's
            // repo subfolder.
            let name = strip_cell_decoration(&name);
            let declared_path = strip_cell_decoration(&declared_path);
            let resolved = resolve_repo_path(&declared_path, candidate_bases);
            EcosystemRepo {
                cloned: resolved.is_some(),
                resolved_path: resolved.map(|path| path.display().to_string()),
                name,
                declared_path,
                role_key: canonical_role(&role).map(str::to_string),
                role,
                stack,
            }
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

    /// The ESKITCHEN table after its Vai trò cells were reduced to one word
    /// each. Five repos share the role `frontend` — the shape every
    /// role-keyed lookup used to collapse into a single one, and the reason
    /// ⑤ Build now gets one slot per repo instead of one per role.
    const SEVEN_REPOS_FIVE_FRONTEND: &str = r#"
## Repos

| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| es-kitchen-api | es-kitchen-repository/es-kitchen-api | backend | NestJS · TypeScript · PostgreSQL — Core API, Business Logic, Domain Gatekeeper |
| es-kitchen-payment-app | es-kitchen-repository/es-kitchen-payment-app | mobile | Flutter 3.x · Dart · Riverpod — User Mobile App (E01), iOS + Android |
| es-kitchen-web-company | es-kitchen-repository/es-kitchen-web-company | frontend | React 19 · Vite 7 · Redux Toolkit — Company Admin Web (E02), 58 functions |
| es-kitchen-web-admin | es-kitchen-repository/es-kitchen-web-admin | frontend | React 19 · Vite 7 · Redux Toolkit — System Admin Web (E03), 160 functions |
| es-kitchen-web-supplier | es-kitchen-repository/es-kitchen-web-supplier | frontend | React 19 · Vite 7 · Redux Toolkit — Supplier Web (E04), quản lý menu, nhận đơn |
| es-kitchen-web-outsource-web-private | es-kitchen-repository/es-kitchen-web-outsource-web-private | frontend | React 19 · Vite 8 · Redux Toolkit — Outsource / Internal Private Admin Web (E05), operation tool quản lý account & sales |
| es-kitchen-webapp-driver | es-kitchen-repository/es-kitchen-webapp-driver | frontend | React 19 · Vite 7 · Ant Design — Driver Web App (E06), nhận order, cập nhật trạng thái giao hàng |
"#;

    #[test]
    fn five_repos_can_share_the_frontend_role() {
        let repos = build_ecosystem(SEVEN_REPOS_FIVE_FRONTEND, &[Path::new("/nonexistent")])
            .unwrap()
            .expect("table shape recognized");

        assert_eq!(repos.len(), 7);
        // Every cell must read — a repo the app can't classify gets no
        // Build slot at all, which is how ESKITCHEN ended up with the whole
        // stage blocked.
        assert!(repos.iter().all(|repo| repo.role_key.is_some()));
        assert_eq!(
            repos
                .iter()
                .filter(|repo| repo.role_key.as_deref() == Some("frontend"))
                .count(),
            5
        );
        // The description moved to Stack, so it must survive there — losing
        // the Epic codes is what makes E02 and E03 indistinguishable.
        assert!(repos[3].stack.contains("E03"));
    }

    #[test]
    fn unfilled_template_yields_no_rows_not_none() {
        // Table shape is valid (headers match), but every row is a
        // placeholder — must be Some(vec![]), NOT None, so the caller can
        // distinguish "no ## Repos section" from "section exists but empty".
        let rows = parse_ecosystem_table(KIT_TEMPLATE_UNFILLED).expect("table shape recognized");
        assert!(rows.is_empty());
    }

    /// Verbatim row shape from a real `/init-kit` output
    /// (`test-project-automatic`): identifiers in backticks, and a role cell
    /// that is the role plus a human note. Every consumer used to compare
    /// the whole role cell, so this project reported "no repo with role
    /// frontend" while `repos/frontend` sat on disk.
    const REAL_INIT_KIT_OUTPUT: &str = r#"
## Repos

| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| `frontend` | `repos/frontend` | frontend — nơi landing page được implement | React 19 · Vite 8 |
| `backend` | `repos/backend` | backend — **chỉ chứa template residual, ngoài scope landing page** | NestJS 11 |
"#;

    #[test]
    fn a_role_cell_with_a_human_note_still_reads_as_its_role() {
        assert_eq!(
            canonical_role("frontend — nơi landing page được implement"),
            Some("frontend")
        );
        assert_eq!(
            canonical_role("backend — **chỉ chứa template residual**"),
            Some("backend")
        );
        assert_eq!(canonical_role("**Frontend** (web admin)"), Some("frontend"));
        assert_eq!(canonical_role("`mobile`"), Some("mobile"));
        assert_eq!(canonical_role("Backend"), Some("backend"));
        assert_eq!(canonical_role("frontend, chỉ phần public"), Some("frontend"));
    }

    /// The app must say "I can't read this" rather than pick something —
    /// `AGENTS.md` is the source of truth and guessing a role would silently
    /// point an agent at the wrong repo (AC-E1-03).
    #[test]
    fn an_unreadable_role_cell_yields_none_rather_than_a_guess() {
        // The kit's own placeholder: taking the leading token would read it
        // as `backend` and mislabel a repo nobody declared a role for.
        assert_eq!(canonical_role("backend / frontend / mobile / other"), None);
        assert_eq!(canonical_role("FE"), None);
        assert_eq!(canonical_role("web"), None);
        assert_eq!(canonical_role("other"), None);
        assert_eq!(canonical_role(""), None);
        // A hyphenated word must not be cut at its hyphen into `front`.
        assert_eq!(canonical_role("front-end"), None);
    }

    #[test]
    fn identifiers_wrapped_in_markdown_are_read_as_plain_paths() {
        let rows = parse_ecosystem_table(REAL_INIT_KIT_OUTPUT).unwrap();
        assert_eq!(rows.len(), 2);

        let tmp = tempfile::tempdir().unwrap();
        std::fs::create_dir_all(tmp.path().join("repos/frontend")).unwrap();
        std::fs::create_dir_all(tmp.path().join("repos/backend")).unwrap();
        let ecosystem = build_ecosystem(REAL_INIT_KIT_OUTPUT, &[tmp.path()])
            .unwrap()
            .unwrap();

        let frontend = &ecosystem[0];
        assert_eq!(frontend.name, "frontend");
        assert_eq!(frontend.declared_path, "repos/frontend");
        assert_eq!(frontend.role_key.as_deref(), Some("frontend"));
        // Backticks in the path used to make this false, which would have
        // produced a second wrong message ("clone repo về") the moment the
        // role was fixed.
        assert!(frontend.cloned);

        // The note the user wrote is kept — the Launcher's Ecosystem table
        // shows this cell verbatim.
        assert!(frontend.role.contains("nơi landing page"));
    }

    /// The seam this bug lived in: parser tests never asserted on `role`,
    /// and readiness tests built `EcosystemRepo` by hand, so nothing ever
    /// ran `AGENTS.md` text all the way to a Run-button decision.
    #[test]
    fn a_real_init_kit_agents_md_makes_its_dev_slots_runnable() {
        use crate::agentrun::readiness::{resolve_repo_readiness, RepoReadiness};

        let tmp = tempfile::tempdir().unwrap();
        std::fs::create_dir_all(tmp.path().join("repos/frontend")).unwrap();
        std::fs::create_dir_all(tmp.path().join("repos/backend")).unwrap();
        let ecosystem = build_ecosystem(REAL_INIT_KIT_OUTPUT, &[tmp.path()])
            .unwrap()
            .unwrap();

        assert!(matches!(
            resolve_repo_readiness(&ecosystem, "frontend"),
            RepoReadiness::Ready
        ));
        assert!(matches!(
            resolve_repo_readiness(&ecosystem, "backend"),
            RepoReadiness::Ready
        ));
        // This project genuinely has no mobile repo — AC-E2-12 still holds.
        assert!(matches!(
            resolve_repo_readiness(&ecosystem, "mobile"),
            RepoReadiness::RoleNotInEcosystem
        ));
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

        assert!(resolve_repo_path("es-kitchen-api", &[tmp.path()]).is_some());
    }

    #[test]
    fn uncloned_repo_never_falsely_reported_as_cloned() {
        let tmp = tempfile::tempdir().unwrap();
        assert!(resolve_repo_path("does-not-exist", &[tmp.path()]).is_none());
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

    #[test]
    fn unfilled_project_is_marked_needs_init() {
        let content = r#"
# <PROJECT_NAME> — Project Rules for AI Agents
- **Domain:** _(1-2 câu, điền qua `/init-kit`)_
## Repos
| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| _(tên repo)_ | _(đường dẫn tương đối)_ | backend | _(NestJS)_ |
"#;

        let (status, reasons) = assess_init_status(Some(content), true);

        assert_eq!(status, ProjectInitStatus::NeedsInit);
        // Tên project + Domain. Bảng Repos toàn placeholder KHÔNG còn là lý do:
        // init trước, clone repo sau là hợp lệ.
        assert_eq!(reasons.len(), 2, "reasons: {reasons:?}");
    }

    #[test]
    fn filled_project_is_ready() {
        let content = r#"
# Shop — Project Rules for AI Agents
- **Domain:** Nền tảng bán hàng cho cửa hàng nội bộ.
## Repos
| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| shop-api | repos/shop-api | backend | NestJS |
"#;

        let (status, reasons) = assess_init_status(Some(content), true);

        assert_eq!(status, ProjectInitStatus::Ready);
        assert!(reasons.is_empty());
    }

    #[test]
    fn missing_kit_is_not_reported_as_needs_init() {
        let (status, reasons) = assess_init_status(None, false);

        assert_eq!(status, ProjectInitStatus::MissingKit);
        assert!(!reasons.is_empty());
    }

    #[test]
    fn malformed_agents_file_is_invalid() {
        let (status, reasons) = assess_init_status(Some("# Shop"), true);

        assert_eq!(status, ProjectInitStatus::Invalid);
        assert!(!reasons.is_empty());
    }

    /// Reproduces the real flow: app scaffolds the kit (with the project
    /// name rendered in), a human runs `/init-kit`, then the app re-checks.
    /// Parsed against the kit's REAL agent files, not a fixture: the whole
    /// point is to know what those files actually declare, and a fixture
    /// would drift from them the first time someone adds a tool.
    #[test]
    fn declared_mcp_servers_reads_the_kits_own_agent_files() {
        let design_analyst = mcp_servers_in_tools_block(include_str!(
            "../../../.claude/agents/design-analyst-agent.md"
        ))
        .expect("the kit's agents all declare a tools: allowlist");
        assert!(design_analyst.contains("figma-bridge"));
        assert!(design_analyst.contains("claude_ai_Figma"));

        // The two build agents must be able to reach Figma too — stage ⑤
        // re-reads the design the analyst wrote about.
        for (agent, raw) in [
            (
                "frontend-agent",
                include_str!("../../../.claude/agents/frontend-agent.md"),
            ),
            (
                "mobile-agent",
                include_str!("../../../.claude/agents/mobile-agent.md"),
            ),
        ] {
            let declared = mcp_servers_in_tools_block(raw).expect("{agent} declares tools:");
            assert!(
                declared.contains("figma-bridge") && declared.contains("claude_ai_Figma"),
                "{agent} must declare both Figma servers the kit ships"
            );
            assert!(declared.contains("tilth"), "{agent} keeps its tilth tools");
        }

        // The case the spawn check exists for: an agent that declares SOME
        // Figma tools but not the other server's. `qa-agent` has the
        // connector and not the bridge, so "declares MCP tools" can never be
        // read as "can reach any Figma server".
        let qa = mcp_servers_in_tools_block(include_str!("../../../.claude/agents/qa-agent.md"))
            .expect("qa-agent declares tools:");
        assert!(qa.contains("claude_ai_Figma"));
        assert!(!qa.contains("figma-bridge"));
    }

    #[test]
    fn mcp_servers_in_tools_block_ignores_comments_and_stops_at_the_next_key() {
        let raw = "---\nname: x\ntools:\n  # - mcp__commented__out\n  - Read\n  - mcp__figma-bridge__get_colors\nskills:\n  - mcp__not-a-tool__nope\n---\n\n- mcp__body__ignored\n";
        let servers = mcp_servers_in_tools_block(raw).expect("has a tools: key");

        assert_eq!(servers.len(), 1);
        assert!(servers.contains("figma-bridge"));
    }

    /// "No `tools:` key" and "a `tools:` key naming no MCP server" must stay
    /// distinguishable: the first means the agent is unrestricted and can
    /// call any connected server, the second means it genuinely cannot.
    /// Collapsing them would block agents that were never restricted.
    #[test]
    fn a_missing_tools_key_is_none_while_an_mcp_less_list_is_an_empty_set() {
        assert_eq!(mcp_servers_in_tools_block("no frontmatter here"), None);
        assert_eq!(
            mcp_servers_in_tools_block("---\nname: x\nmodel: y\n---\n"),
            None
        );
        assert_eq!(
            mcp_servers_in_tools_block("---\nname: x\ntools:\n  - Read\n  - Bash\n---\n"),
            Some(BTreeSet::new())
        );
    }

    /// The checked-in `example-project` is a REAL inited project. If the
    /// app cannot see it as ready, no user's project can be either.
    #[test]
    fn the_example_project_is_seen_as_inited() {
        let agents_md = include_str!("../../../example-project/kit-repo/AGENTS.md");
        let (status, reasons) = assess_init_status(Some(agents_md), true);
        println!("EXAMPLE = {status:?} reasons={reasons:?}");
        assert_eq!(status, ProjectInitStatus::Ready, "reasons: {reasons:?}");
    }

    #[test]
    fn a_correctly_inited_agents_md_reads_as_ready() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("proj");
        let docs_root = agents_root.join("docs");
        crate::store::kit_template::materialize_for_project(
            &agents_root,
            &docs_root,
            Some("Shop Online"),
        )
        .unwrap();

        let path = agents_root.join("AGENTS.md");
        let scaffolded = std::fs::read_to_string(&path).unwrap();

        // What the app says BEFORE init.
        let (before, before_reasons) =
            assess_init_status(Some(&scaffolded), has_claude_agents_dir(&agents_root));
        println!("BEFORE = {before:?} reasons={before_reasons:?}");

        // Now apply exactly what `init-agent.md` Bước 3.1 instructs.
        let inited = scaffolded
            .replace(
                "| _(tên repo)_ | _(đường dẫn tương đối so với Repository root)_ | backend / frontend / mobile / other | _(NestJS / React / Flutter / ...)_ |",
                "| shop-api | shop-api | backend | NestJS |\n| shop-web-admin | shop-web-admin | frontend | React 19 |",
            )
            .replace(
                "- **Domain:** _(1-2 câu, điền qua `/init-kit`)_",
                "- **Domain:** Nền tảng bán hàng online.",
            )
            .replace("<DOCS_ROOT>", "shop-docs/docs/features");
        std::fs::write(&path, &inited).unwrap();

        let (after, after_reasons) = read_init_status(&agents_root);
        println!("AFTER  = {after:?} reasons={after_reasons:?}");
        assert_eq!(
            after,
            ProjectInitStatus::Ready,
            "reasons: {after_reasons:?}"
        );
    }

    /// Init kit trước, clone repo sau. Khi `repos/` còn rỗng, init-agent giữ
    /// nguyên dòng placeholder của kit — `is_placeholder_cell` loại dòng đó nên
    /// bảng đọc ra rỗng. Trước đây bảng rỗng bị tính là chưa init, và project
    /// kiểu này kẹt `NeedsInit` mãi: terminal init-kit không bao giờ tự đóng vì
    /// vòng poll chờ `Ready` không bao giờ tới.
    #[test]
    fn a_project_with_no_repos_declared_yet_is_ready() {
        let agents_md = "\
# Khkj — Project Rules for AI Agents

## Repos

| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| _(tên repo)_ | _(đường dẫn tương đối so với Repository root)_ | backend / frontend / mobile / other | _(NestJS / React / Flutter / ...)_ |

- **Domain:** Dự án Khkj — dùng để test khung kit AI agent.
";
        let (status, reasons) = assess_init_status(Some(agents_md), true);
        assert_eq!(status, ProjectInitStatus::Ready, "reasons: {reasons:?}");
    }

    /// Nới ở trên chỉ nới chuyện bảng RỖNG. Bảng sai cấu trúc (thiếu cột) vẫn
    /// phải là `Invalid` — không có bảng đúng thì không đọc nổi Ecosystem.
    #[test]
    fn a_repos_table_with_the_wrong_columns_is_still_invalid() {
        let agents_md = "\
## Repos

| Tên | Ghi chú |
|---|---|
| a | b |

- **Domain:** Có domain thật.
";
        let (status, _) = assess_init_status(Some(agents_md), true);
        assert_eq!(status, ProjectInitStatus::Invalid);
    }

    /// The shape a real `/init-kit` run produces: value filled in right
    /// after the label, with the template's descriptive prose kept as a
    /// trailing clause. Regression for a check that grepped the line for
    /// that prose and pinned the project at `NeedsInit` forever.
    #[test]
    fn docs_root_filled_before_the_kept_description_is_ready() {
        let agents_md = "\
## Repos

| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| frontend | repos/frontend | frontend | React |

- **Domain:** Landing page cho thương hiệu outdoor.
- **`<DOCS_ROOT>`:** `docs/` — single long-memory chứa SPEC/DESIGN/tasks/test-cases cho mọi feature (`docs/features/`).

> Dev agent cập nhật overview docs (`<DOCS_ROOT>/<layer>/<repo>/overview/`).
";
        let (status, reasons) = assess_init_status(Some(agents_md), true);
        assert_eq!(status, ProjectInitStatus::Ready, "reasons: {reasons:?}");
    }

    /// The mirror image: the untouched template must still be caught.
    #[test]
    fn docs_root_left_as_the_template_description_is_needs_init() {
        let agents_md = "\
## Repos

| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| frontend | repos/frontend | frontend | React |

- **Domain:** Landing page cho thương hiệu outdoor.
- **`<DOCS_ROOT>`:** single long-memory chứa SPEC/DESIGN/tasks/test-cases cho mọi feature (ví dụ `<project>-docs/docs/features/`).
";
        let (status, reasons) = assess_init_status(Some(agents_md), true);
        assert_eq!(status, ProjectInitStatus::NeedsInit);
        assert!(
            reasons.iter().any(|r| r.contains("DOCS_ROOT")),
            "{reasons:?}"
        );
    }
}
