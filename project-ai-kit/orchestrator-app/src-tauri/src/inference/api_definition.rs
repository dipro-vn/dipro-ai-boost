//! Parses the "API Definition" markdown table that `techlead-design-agent`
//! puts in every `DESIGN.md` it writes — `## 3. API Definition`, 6 required
//! columns: `Method | Endpoint | Auth | Request | Response | Error codes`.
//! This is AC-E4-08/10/16/17's "contract" source — the whole `DESIGN.md`
//! file gets locked (whole-file SHA-256, per AC-E4-17), not just this table;
//! this module only cares about the table for the gate's OPEN condition and
//! column-completeness warning.
//!
//! The table is NOT the first thing under the heading. The agent's own
//! template (`.claude/agents/techlead-design-agent.md` §Bước 4, `## 3. API
//! Definition`) puts a `> **Nguồn gốc cho CONTRACT LOCK...**` blockquote and
//! a `### Endpoint mới / thay đổi` sub-heading between the heading and the
//! table, and real DESIGN.md files add prose, DTO code fences, and further
//! tables (`| Code | Message | Điều kiện |` for error responses) around it.
//! So the whole section — heading until the next same-or-higher-level
//! heading — is scanned for tables, code fences are skipped (a `|` inside a
//! fenced example is not a table), and the table carrying both `Method` and
//! `Endpoint` wins. When the section has tables but none of them is the
//! contract table, the first one is returned anyway so AC-E4-10 can name the
//! missing columns instead of the gate silently reporting `NotReady`.
//!
//! WebSocket events / Push notification payload (mentioned in the SPEC's
//! `OR_GATE_002` description) are NOT modeled here — verified they exist
//! only as free-text bullets under `## 5. Interface với repo khác`, never
//! as a structured table in the real template, so there is nothing
//! parseable to extract for them. They're still covered by the whole-file
//! checksum/lock, just not displayed as structured data.

use std::path::{Path, PathBuf};

use crate::agents_reader::{find_column, is_table_separator_row, split_table_row};
use crate::inference::stage_rules;

pub const REQUIRED_COLUMNS: &[&str] = &[
    "Method",
    "Endpoint",
    "Auth",
    "Request",
    "Response",
    "Error codes",
];

/// `Some(n)` for an ATX heading line, where `n` is its level. Tolerant of
/// leading whitespace; `####` counts as 4 even without the trailing space
/// some strict parsers require, since section *boundaries* are all this is
/// used for.
fn heading_level(line: &str) -> Option<usize> {
    let trimmed = line.trim_start();
    let hashes = trimmed.chars().take_while(|c| *c == '#').count();
    (hashes > 0).then_some(hashes)
}

fn is_code_fence(line: &str) -> bool {
    let trimmed = line.trim_start();
    trimmed.starts_with("```") || trimmed.starts_with("~~~")
}

/// One contiguous run of `|`-prefixed lines, as header + rows. `None` when
/// the run is too short to be a table (no header + separator).
fn parse_table(run: &[&str]) -> Option<(Vec<String>, Vec<Vec<String>>)> {
    if run.len() < 2 {
        return None;
    }
    let headers = split_table_row(run[0]);
    let rows: Vec<Vec<String>> = run
        .iter()
        .skip(1)
        .filter(|line| !is_table_separator_row(line))
        .map(|line| split_table_row(line))
        .collect();
    Some((headers, rows))
}

/// Every markdown table in `lines`, in document order. Contiguous runs of
/// `|`-prefixed lines outside code fences are one table each.
fn tables_in(lines: &[&str]) -> Vec<(Vec<String>, Vec<Vec<String>>)> {
    let mut tables = Vec::new();
    let mut run: Vec<&str> = Vec::new();
    let mut in_fence = false;

    for line in lines {
        let is_row = !in_fence && !is_code_fence(line) && line.trim_start().starts_with('|');
        if is_row {
            run.push(line);
            continue;
        }
        tables.extend(parse_table(&run));
        run.clear();
        if is_code_fence(line) {
            in_fence = !in_fence;
        }
    }
    tables.extend(parse_table(&run));

    tables
}

/// Finds the contract table inside the `## ... API Definition` section
/// (heading matched case-insensitively as a substring — tolerant of a
/// leading section number like `## 3. API Definition`, since nothing pins
/// the section numbering). `None` if there is no such heading, or the
/// section contains no table at all.
pub fn find_table_in_design_md(content: &str) -> Option<(Vec<String>, Vec<Vec<String>>)> {
    let lines: Vec<&str> = content.lines().collect();

    let heading_idx = lines.iter().position(|line| {
        let trimmed = line.trim();
        trimmed.starts_with("##") && trimmed.to_lowercase().contains("api definition")
    })?;
    let section_level = heading_level(lines[heading_idx])?;

    // Sub-headings (`###`, `####`) stay inside the section — only a
    // same-or-higher-level heading ends it.
    let section_end = lines
        .iter()
        .enumerate()
        .skip(heading_idx + 1)
        .find(|(_, line)| heading_level(line).is_some_and(|level| level <= section_level))
        .map_or(lines.len(), |(idx, _)| idx);

    let tables = tables_in(&lines[heading_idx + 1..section_end]);

    tables
        .iter()
        .find(|(headers, _)| {
            find_column(headers, &["method"]).is_some()
                && find_column(headers, &["endpoint"]).is_some()
        })
        .or_else(|| tables.first())
        .cloned()
}

/// AC-E4-10 — which `REQUIRED_COLUMNS` are missing from `headers`
/// (case-insensitive substring match, same tolerance `find_column`
/// already uses elsewhere). Empty means the table has everything required.
pub fn missing_required_columns(headers: &[String]) -> Vec<String> {
    REQUIRED_COLUMNS
        .iter()
        .filter(|col| find_column(headers, &[&col.to_lowercase()]).is_none())
        .map(|s| s.to_string())
        .collect()
}

/// Every `DESIGN.md` (across every repo for this feature) that has a
/// recognizable API Definition table — the single source of truth both
/// the gate's open condition (AC-E4-08) and lock creation (AC-E4-16/17)
/// use, so they can never disagree about which files are in scope.
pub fn design_md_files_with_api_table(feature_dir: &Path) -> Vec<PathBuf> {
    stage_rules::files_in_repos(feature_dir, "DESIGN.md")
        .into_iter()
        .filter(|path| {
            std::fs::read_to_string(path)
                .map(|content| find_table_in_design_md(&content).is_some())
                .unwrap_or(false)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The layout `techlead-design-agent.md` §Bước 4 actually emits:
    /// heading → blockquote → `###` sub-heading → table → DTO code fences.
    const TEMPLATE_DESIGN_MD: &str = r#"# DESIGN: User Login — example-api

## 1. Tổng quan thay đổi

Thiết kế API xác thực đăng nhập cho `example-api`.

## 2. Database Changes

Không thay đổi schema — dùng bảng `users` có sẵn.

## 3. API Definition
> **Nguồn gốc cho CONTRACT LOCK và task-3-x FE/Mobile.** Điền đủ bảng này.

### Endpoint mới / thay đổi

| Method | Endpoint | Auth | Request | Response | Error codes |
|---|---|---|---|---|---|
| POST | `/api/auth/login` | Không | `{email, password}` | `{accessToken, refreshToken}` | 401, 429 |
| POST | `/api/auth/logout` | JWT | `{}` | `204` | 401 |

**Request DTO chi tiết** (validation rules):
```
email: string — required, email format
```

## 4. Service Layer

`AuthService.login(email, password)` — verify password hash (bcrypt), tạo JWT.
"#;

    #[test]
    fn finds_the_table_through_blockquote_and_sub_heading() {
        let (headers, rows) = find_table_in_design_md(TEMPLATE_DESIGN_MD).expect("table found");
        assert_eq!(
            headers,
            vec![
                "Method",
                "Endpoint",
                "Auth",
                "Request",
                "Response",
                "Error codes"
            ]
        );
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0][0], "POST");
        assert!(missing_required_columns(&headers).is_empty());
    }

    #[test]
    fn table_immediately_after_the_heading_still_works() {
        let content = "## 3. API Definition\n\n| Method | Endpoint |\n|---|---|\n| POST | `/x` |\n";
        let (headers, rows) = find_table_in_design_md(content).expect("table found");
        assert_eq!(headers, vec!["Method", "Endpoint"]);
        assert_eq!(rows.len(), 1);
    }

    #[test]
    fn contract_table_wins_over_an_earlier_unrelated_table_in_the_section() {
        let content = "## 3. API Definition\n\n\
**Error responses:**\n\n\
| Code | Message | Điều kiện |\n|---|---|---|\n| 401 | INVALID | sai mật khẩu |\n\n\
### Endpoint mới\n\n\
| Method | Endpoint | Auth | Request | Response | Error codes |\n|---|---|---|---|---|---|\n\
| POST | `/x` | JWT | `{}` | `{}` | 400 |\n";
        let (headers, _rows) = find_table_in_design_md(content).expect("table found");
        assert_eq!(headers[0], "Method");
        assert!(missing_required_columns(&headers).is_empty());
    }

    #[test]
    fn unrelated_table_only_is_returned_so_missing_columns_get_named() {
        // AC-E4-10 path — gate opens with a warning rather than reporting
        // the misleading "no API Definition table anywhere" NotReady.
        let content = "## 3. API Definition\n\n\
**Error responses:**\n\n\
| Code | Message | Điều kiện |\n|---|---|---|\n| 401 | INVALID | sai mật khẩu |\n";
        let (headers, _rows) = find_table_in_design_md(content).expect("table found");
        assert_eq!(headers, vec!["Code", "Message", "Điều kiện"]);
        assert_eq!(
            missing_required_columns(&headers),
            REQUIRED_COLUMNS.to_vec()
        );
    }

    #[test]
    fn a_table_inside_a_code_fence_is_not_a_table() {
        let content =
            "## 3. API Definition\n\n```md\n| Method | Endpoint |\n|---|---|\n| POST | `/x` |\n```\n";
        assert!(find_table_in_design_md(content).is_none());
    }

    #[test]
    fn a_table_in_the_next_section_does_not_count() {
        let content = "## 3. API Definition\n\nChưa có bảng.\n\n\
## 4. Service Layer\n\n| Method | Endpoint |\n|---|---|\n| POST | `/x` |\n";
        assert!(find_table_in_design_md(content).is_none());
    }

    #[test]
    fn no_heading_at_all_returns_none() {
        assert!(find_table_in_design_md("## 1. Tổng quan\nx\n").is_none());
    }

    #[test]
    fn heading_without_a_table_returns_none() {
        assert!(find_table_in_design_md("## 3. API Definition\n\nKhông có bảng.\n").is_none());
    }

    #[test]
    fn missing_columns_are_reported_by_name() {
        let headers = vec!["Method".to_string(), "Endpoint".to_string()];
        let missing = missing_required_columns(&headers);
        assert_eq!(missing, vec!["Auth", "Request", "Response", "Error codes"]);
    }

    #[test]
    fn design_md_files_with_api_table_only_returns_files_with_a_real_table() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        let repo_with_table = feature_dir.join("api-repo");
        let repo_without_table = feature_dir.join("web-repo");
        std::fs::create_dir_all(&repo_with_table).unwrap();
        std::fs::create_dir_all(&repo_without_table).unwrap();
        std::fs::write(repo_with_table.join("DESIGN.md"), TEMPLATE_DESIGN_MD).unwrap();
        std::fs::write(
            repo_without_table.join("DESIGN.md"),
            "## 1. Tổng quan\nKhông có API.\n",
        )
        .unwrap();

        let found = design_md_files_with_api_table(&feature_dir);
        assert_eq!(found, vec![repo_with_table.join("DESIGN.md")]);
    }

    #[test]
    fn tmp_verify_real_example_project_file() {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../../example-project/docs/features/user-login/example-api/DESIGN.md");
        let content = std::fs::read_to_string(&path).expect("read real DESIGN.md");
        let (headers, rows) = find_table_in_design_md(&content).expect("table found in real file");
        println!("HEADERS: {headers:?}");
        println!("ROWS: {}", rows.len());
        println!("MISSING: {:?}", missing_required_columns(&headers));
        assert!(missing_required_columns(&headers).is_empty());
        assert_eq!(rows.len(), 5);
    }
}
