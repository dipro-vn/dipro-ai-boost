/// The 11 sections `ba-agent.md`'s template mandates, verbatim (Vietnamese,
/// exact casing) — see `.claude/agents/ba-agent.md` §Bước 4 and
/// `.claude/ba-agent/spec-template.md` in the kit. Order is the template's
/// own: `missing_sections` reports in this order and the Trigger Gate panel
/// renders that list as-is.
///
/// `BA Deliverables` is in here on purpose. It is the entry point the kit
/// declares for every downstream agent (techlead-design / designer / qc all
/// stop if it is absent), and a run that could not deliver Outputs 1-5
/// still writes the section — with `❌ Skipped` rows — so requiring the
/// heading never blocks a degraded run.
///
/// `UX Review Notes` (Bước 4.5) is deliberately NOT here: the kit lets BA
/// report it to the user instead of writing it into the SPEC.
pub const REQUIRED_SPEC_SECTIONS: &[&str] = &[
    "Mô tả nghiệp vụ",
    "BA Deliverables",
    "Actors & Preconditions",
    "Flow Tổng Quan",
    "Happy Path",
    "Alternative Flows & Edge Cases",
    "Acceptance Criteria",
    "Out of Scope",
    "Screens",
    "Screen Details",
    "Responsive Requirements",
];

/// True if `content` has a level-2 markdown heading (`## <section>`) whose
/// text matches `section` exactly after trimming. Matches only `##`, not
/// `###`+, because that's what the kit's own template uses for every
/// section.
fn has_section_heading(content: &str, section: &str) -> bool {
    content.lines().any(|line| {
        let trimmed = line.trim();
        trimmed
            .strip_prefix("## ")
            .map(|rest| rest.trim() == section)
            .unwrap_or(false)
    })
}

/// Returns the required sections NOT present in `content`, in the order
/// `ba-agent.md`'s template defines them. Empty means the SPEC is complete.
pub fn missing_sections(content: &str) -> Vec<String> {
    REQUIRED_SPEC_SECTIONS
        .iter()
        .filter(|section| !has_section_heading(content, section))
        .map(|s| s.to_string())
        .collect()
}

/// The outputs BA itself declared it could not deliver, read off the
/// `## BA Deliverables` table (rows carrying `❌ Skipped`).
///
/// The app does not go and verify Figma node URLs or an MkDocs port — it
/// cannot, they are external. The kit already made that table the single
/// source of truth for what BA delivered, so this reads BA's own account of
/// it. Returns the output name from each skipped row's first non-empty
/// cell (e.g. `**Flow Tổng Quan**`, stripped of markdown emphasis).
pub fn skipped_deliverables(content: &str) -> Vec<String> {
    let mut in_section = false;
    let mut out = Vec::new();

    for line in content.lines() {
        let trimmed = line.trim();
        if let Some(rest) = trimmed.strip_prefix("## ") {
            // Bất kỳ heading `##` nào cũng kết thúc section — bảng nằm gọn
            // giữa `## BA Deliverables` và section kế tiếp.
            in_section = rest.trim() == "BA Deliverables";
            continue;
        }
        if !in_section || !trimmed.contains("❌ Skipped") {
            continue;
        }
        if let Some(name) = row_label(trimmed) {
            out.push(name);
        }
    }
    out
}

/// Tên output của một row bảng markdown: cell đầu tiên không rỗng và không
/// phải số thứ tự, bỏ `**`/`` ` `` bao quanh.
fn row_label(row: &str) -> Option<String> {
    row.split('|')
        .map(str::trim)
        .filter(|cell| !cell.is_empty())
        .find(|cell| !cell.chars().all(|c| c.is_ascii_digit()))
        .map(|cell| {
            cell.trim_matches(|c| c == '*' || c == '`')
                .trim()
                .to_string()
        })
}

/// A SPEC.md with every required section present, for tests elsewhere in
/// the crate. Built from `REQUIRED_SPEC_SECTIONS` rather than hand-written:
/// five modules used to keep their own copy, and each one had to be found
/// and edited by hand whenever the section list changed.
#[cfg(test)]
pub fn complete_spec_fixture() -> String {
    let mut out = String::from("# SPEC: Something\n");
    for section in REQUIRED_SPEC_SECTIONS {
        out.push_str(&format!("\n## {section}\ntext\n"));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn complete_spec_has_no_missing_sections() {
        assert!(missing_sections(&complete_spec_fixture()).is_empty());
    }

    #[test]
    fn missing_two_sections_are_reported_in_template_order() {
        let content = "## Mô tả nghiệp vụ\ntext\n\n## Happy Path\ntext\n";
        let missing = missing_sections(content);
        assert_eq!(
            missing,
            vec![
                "BA Deliverables",
                "Actors & Preconditions",
                "Flow Tổng Quan",
                "Alternative Flows & Edge Cases",
                "Acceptance Criteria",
                "Out of Scope",
                "Screens",
                "Screen Details",
                "Responsive Requirements",
            ]
        );
    }

    #[test]
    fn empty_content_is_missing_everything() {
        assert_eq!(missing_sections("").len(), REQUIRED_SPEC_SECTIONS.len());
    }

    /// Downstream agent nào cũng dừng nếu SPEC thiếu section này, nên nó
    /// phải nằm trong danh sách bắt buộc — và ngay sau `Mô tả nghiệp vụ`,
    /// đúng vị trí kit yêu cầu BA đặt.
    #[test]
    fn ba_deliverables_is_required_and_comes_second() {
        assert_eq!(REQUIRED_SPEC_SECTIONS[1], "BA Deliverables");
    }

    /// Bước 4.5 cho phép BA báo miệng thay vì ghi vào SPEC — bắt buộc nó ở
    /// đây sẽ làm mọi SPEC hợp lệ bị coi là thiếu.
    #[test]
    fn ux_review_notes_is_not_required() {
        assert!(!REQUIRED_SPEC_SECTIONS.contains(&"UX Review Notes"));
    }

    const DELIVERABLES: &str = r#"# SPEC: Something

## BA Deliverables

| # | Output | Nội dung | Figma Frame |
|---|---|---|---|
| 1 | **Flow Tổng Quan** | Business flow | ❌ Skipped — không có MCP Figma khả dụng |
| 2 | **Screen Flow** | N groups | [Mở Figma](https://figma.com/design/x?node-id=1-2) |
| 3 | **Screens + Items** | Grouped | ❌ Skipped — không có MCP Figma khả dụng |

## Screens
text
"#;

    #[test]
    fn skipped_deliverables_names_only_the_skipped_rows() {
        assert_eq!(
            skipped_deliverables(DELIVERABLES),
            vec!["Flow Tổng Quan", "Screens + Items"]
        );
    }

    #[test]
    fn a_fully_delivered_spec_reports_nothing_skipped() {
        assert!(skipped_deliverables(&complete_spec_fixture()).is_empty());
    }

    /// `❌ Skipped` ở section khác (VD ghi chú trong `## Out of Scope`)
    /// không được tính là output thiếu.
    #[test]
    fn skipped_outside_the_deliverables_section_is_ignored() {
        let content = "## BA Deliverables\n\ntext\n\n## Out of Scope\n| 1 | Foo | ❌ Skipped |\n";
        assert!(skipped_deliverables(content).is_empty());
    }

    #[test]
    fn a_spec_without_the_section_reports_nothing() {
        assert!(skipped_deliverables("## Screens\ntext\n").is_empty());
    }

    #[test]
    fn level_3_heading_does_not_count_as_the_section() {
        // A `###` subsection with the same text must not be mistaken for
        // the real `##` section heading.
        let content = "### Mô tả nghiệp vụ\ntext\n";
        assert!(missing_sections(content).contains(&"Mô tả nghiệp vụ".to_string()));
    }
}
