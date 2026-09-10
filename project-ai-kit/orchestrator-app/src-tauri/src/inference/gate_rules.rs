//! AC-E4-01/02/07 — the Trigger gate's open condition and checklist,
//! computed purely from disk like the rest of `inference` (see
//! `stage_rules`'s own docs on that philosophy), plus one deliberate
//! exception: **approval is sticky**. `stage_rules::infer_feature_state`
//! never consults prior state, but a gate is a recorded human decision, not
//! a derived fact — once a PM has approved, re-running inference on a
//! `SPEC.md` that changed again afterward must NOT silently revoke that
//! approval. v1 does not support re-opening an approved gate; that would
//! need its own explicit action, out of scope for this pass.

use std::path::Path;

use crate::domain::gate_state::{GateState, GateStatus};
use crate::inference::spec_sections;

/// `previous` is whatever was persisted in `state.json` for this gate on
/// the last recompute (`None` if never computed before, e.g. a brand new
/// feature).
pub fn infer_trigger_gate_state(feature_dir: &Path, previous: Option<&GateState>) -> GateState {
    if let Some(prev) = previous {
        if prev.status == GateStatus::Approved {
            return prev.clone();
        }
    }

    let spec_path = feature_dir.join("SPEC.md");
    let missing_sections = match std::fs::read_to_string(&spec_path) {
        Ok(content) => spec_sections::missing_sections(&content),
        // No SPEC.md at all yet — every section is "missing".
        Err(_) => spec_sections::REQUIRED_SPEC_SECTIONS
            .iter()
            .map(|s| s.to_string())
            .collect(),
    };

    GateState {
        status: if missing_sections.is_empty() {
            GateStatus::PendingReview
        } else {
            GateStatus::NotReady
        },
        approved_by: None,
        approved_at: None,
        missing_sections,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn write(path: &Path, content: &str) {
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, content).unwrap();
    }

    #[test]
    fn no_spec_md_is_not_ready_with_all_sections_missing() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();

        let gate = infer_trigger_gate_state(&feature_dir, None);
        assert_eq!(gate.status, GateStatus::NotReady);
        assert_eq!(
            gate.missing_sections.len(),
            spec_sections::REQUIRED_SPEC_SECTIONS.len()
        );
    }

    #[test]
    fn incomplete_spec_md_is_not_ready() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(&feature_dir.join("SPEC.md"), "## Mô tả nghiệp vụ\nx\n");

        let gate = infer_trigger_gate_state(&feature_dir, None);
        assert_eq!(gate.status, GateStatus::NotReady);
        assert!(!gate.missing_sections.is_empty());
    }

    #[test]
    fn complete_spec_md_is_pending_review() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("SPEC.md"),
            &crate::inference::spec_sections::complete_spec_fixture(),
        );

        let gate = infer_trigger_gate_state(&feature_dir, None);
        assert_eq!(gate.status, GateStatus::PendingReview);
        assert!(gate.missing_sections.is_empty());
    }

    #[test]
    fn approved_gate_is_sticky_even_if_spec_md_changes_again() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("SPEC.md"),
            &crate::inference::spec_sections::complete_spec_fixture(),
        );

        let approved = GateState {
            status: GateStatus::Approved,
            approved_by: Some("PM Test".to_string()),
            approved_at: Some("2026-08-17T00:00:00Z".to_string()),
            missing_sections: vec![],
        };

        // SPEC.md becomes incomplete again after approval — must not revert.
        write(&feature_dir.join("SPEC.md"), "## Mô tả nghiệp vụ\nx\n");
        let gate = infer_trigger_gate_state(&feature_dir, Some(&approved));
        assert_eq!(gate.status, GateStatus::Approved);
        assert_eq!(gate.approved_by.as_deref(), Some("PM Test"));
    }
}
