/// The 7 sections `ba-agent.md`'s template mandates, verbatim (Vietnamese,
/// exact casing) — see `.claude/agents/ba-agent.md` §Bước 4 in the kit.
pub const REQUIRED_SPEC_SECTIONS: &[&str] = &[
    "Mô tả nghiệp vụ",
    "Actors & Preconditions",
    "Happy Path",
    "Alternative Flows & Edge Cases",
    "Acceptance Criteria",
    "Out of Scope",
    "Screens",
];

/// True if `content` has a level-2 markdown heading (`## <section>`) whose
/// text matches `section` exactly after trimming. Matches only `##`, not
/// `###`+, because that's what the kit's own template uses for all 7
/// sections.
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

#[cfg(test)]
mod tests {
    use super::*;

    const COMPLETE_SPEC: &str = r#"# SPEC: Something

## Mô tả nghiệp vụ
text

## Actors & Preconditions
text

## Happy Path
text

## Alternative Flows & Edge Cases
text

## Acceptance Criteria
text

## Out of Scope
text

## Screens
text
"#;

    #[test]
    fn complete_spec_has_no_missing_sections() {
        assert!(missing_sections(COMPLETE_SPEC).is_empty());
    }

    #[test]
    fn missing_two_sections_are_reported_in_template_order() {
        let content = "## Mô tả nghiệp vụ\ntext\n\n## Happy Path\ntext\n";
        let missing = missing_sections(content);
        assert_eq!(
            missing,
            vec![
                "Actors & Preconditions",
                "Alternative Flows & Edge Cases",
                "Acceptance Criteria",
                "Out of Scope",
                "Screens",
            ]
        );
    }

    #[test]
    fn empty_content_is_missing_everything() {
        assert_eq!(missing_sections("").len(), 7);
    }

    #[test]
    fn level_3_heading_does_not_count_as_the_section() {
        // A `###` subsection with the same text must not be mistaken for
        // the real `##` section heading.
        let content = "### Mô tả nghiệp vụ\ntext\n";
        assert!(missing_sections(content).contains(&"Mô tả nghiệp vụ".to_string()));
    }
}
