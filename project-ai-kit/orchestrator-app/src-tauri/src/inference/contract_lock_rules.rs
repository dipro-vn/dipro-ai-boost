//! AC-E4-08..29 (Contract Lock) — open condition, role applicability,
//! pre-lock file/checksum preview, and (Phase 2b) violation detection,
//! computed purely from disk + the project's Ecosystem, like the rest of
//! `inference`.
//!
//! Once locked, every locked file's checksum is re-verified on every call
//! (AC-E4-21/22) — reverting a file back to its locked content therefore
//! clears a violation on its own the very next recompute (AC-E4-26), no
//! special-casing needed. `running_on_old_contract` (AC-E4-24) is the one
//! field this module can never fill in — it needs `AppState.agent_runs`,
//! which lives outside `inference`'s pure-from-disk world — callers
//! (`pipeline_state::compute_and_persist`'s callers, which do have
//! `AppState`) set it afterward.

use std::path::Path;

use sha2::{Digest, Sha256};

use crate::domain::contract_lock::{
    ContractLockRecord, ContractLockState, ContractLockStatus, FileViolation, LockedFileRef,
    ViolationKind,
};
use crate::domain::project::EcosystemRepo;
use crate::inference::api_definition;
use crate::inference::stage_rules;

/// `pub(crate)` — also used by `commands::agentrun::lock_contract` so the
/// checksum it writes into a `LockedFile` can never disagree with the
/// preview `candidate_files` already showed the user before Lock was
/// clicked.
pub(crate) fn sha256_hex(content: &str) -> String {
    let digest = Sha256::digest(content.as_bytes());
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn role_applies(ecosystem: &[EcosystemRepo], role: &str) -> bool {
    ecosystem
        .iter()
        .any(|repo| repo.role.eq_ignore_ascii_case(role))
}

/// AC-E4-14 — PM and QC always apply; BE/FE/Mobile only if the Ecosystem
/// has a repo of that role (same role-matching principle already used by
/// `commands::agentrun::resolve_repo_readiness` for AC-E2-11/12).
fn applicable_roles(ecosystem: &[EcosystemRepo]) -> Vec<String> {
    let mut roles = Vec::new();
    if role_applies(ecosystem, "backend") {
        roles.push("BE".to_string());
    }
    if role_applies(ecosystem, "frontend") {
        roles.push("FE".to_string());
    }
    if role_applies(ecosystem, "mobile") {
        roles.push("Mobile".to_string());
    }
    roles.push("PM".to_string());
    roles.push("QC".to_string());
    roles
}

fn not_ready(applicable_roles: Vec<String>, plan_md_missing: bool) -> ContractLockState {
    ContractLockState {
        status: ContractLockStatus::NotReady,
        missing_columns: vec![],
        plan_md_missing,
        not_applicable_reason: None,
        applicable_roles,
        candidate_files: vec![],
        current_lock: None,
        violated_files: vec![],
        running_on_old_contract: false,
    }
}

/// AC-E4-21/22 — re-verifies every locked file's checksum against what's
/// on disk right now. `Deleted` when the file can't be read at all (gone,
/// or turned into a directory, etc.) — anything else that keeps a file
/// unreadable is treated the same way, since "not readable" and "not
/// there" look identical from here and both need the same "something's
/// wrong with this locked file" response.
fn detect_violations(lock: &ContractLockRecord) -> Vec<FileViolation> {
    lock.files
        .iter()
        .filter_map(|locked| match std::fs::read_to_string(&locked.path) {
            Ok(current) if sha256_hex(&current) == locked.checksum_sha256 => None,
            Ok(_current) => Some(FileViolation {
                path: locked.path.clone(),
                kind: ViolationKind::Modified,
                locked_content: locked.content.clone(),
            }),
            Err(_) => Some(FileViolation {
                path: locked.path.clone(),
                kind: ViolationKind::Deleted,
                locked_content: locked.content.clone(),
            }),
        })
        .collect()
}

pub fn infer_contract_lock_state(
    feature_dir: &Path,
    ecosystem: &[EcosystemRepo],
    previous_lock: Option<ContractLockRecord>,
) -> ContractLockState {
    let applicable = applicable_roles(ecosystem);

    // Checked before anything else, same priority as the Trigger gate's
    // sticky-once-approved check — but unlike that one, this re-verifies
    // rather than blindly trusting the lock still holds.
    if let Some(lock) = previous_lock {
        let violations = detect_violations(&lock);
        let status = if violations.is_empty() {
            ContractLockStatus::Locked
        } else {
            ContractLockStatus::Violated
        };
        return ContractLockState {
            status,
            missing_columns: vec![],
            plan_md_missing: false,
            not_applicable_reason: None,
            applicable_roles: applicable,
            candidate_files: vec![],
            current_lock: Some(lock),
            violated_files: violations,
            running_on_old_contract: false,
        };
    }

    // AC-E4-11 — takes priority over the table search: a single-repo
    // feature doesn't need Contract Lock regardless of what DESIGN.md
    // contains.
    if stage_rules::repo_subdirs(feature_dir).len() <= 1 {
        return ContractLockState {
            status: ContractLockStatus::NotApplicable,
            missing_columns: vec![],
            plan_md_missing: false,
            not_applicable_reason: Some(
                "Feature chỉ chạm 1 repo — Contract Lock không áp dụng.".to_string(),
            ),
            applicable_roles: applicable,
            candidate_files: vec![],
            current_lock: None,
            violated_files: vec![],
            running_on_old_contract: false,
        };
    }

    let plan_md_missing = !feature_dir.join("PLAN.md").is_file(); // AC-E4-09, warning only

    let files = api_definition::design_md_files_with_api_table(feature_dir);
    if files.is_empty() {
        return not_ready(applicable, plan_md_missing); // AC-E4-08
    }

    let mut missing_columns = Vec::new();
    let mut candidate_files = Vec::new();
    for path in &files {
        let Ok(content) = std::fs::read_to_string(path) else {
            continue;
        };
        if let Some((headers, _rows)) = api_definition::find_table_in_design_md(&content) {
            for col in api_definition::missing_required_columns(&headers) {
                if !missing_columns.contains(&col) {
                    missing_columns.push(col); // AC-E4-10
                }
            }
        }
        candidate_files.push(LockedFileRef {
            path: path.display().to_string(),
            checksum_sha256: sha256_hex(&content), // AC-E4-16
        });
    }

    ContractLockState {
        status: ContractLockStatus::PendingReview,
        missing_columns,
        plan_md_missing,
        not_applicable_reason: None,
        applicable_roles: applicable,
        candidate_files,
        current_lock: None,
        violated_files: vec![],
        running_on_old_contract: false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn repo(role: &str) -> EcosystemRepo {
        EcosystemRepo {
            name: format!("{role}-repo"),
            declared_path: format!("repos/{role}-repo"),
            role: role.to_string(),
            stack: "x".to_string(),
            cloned: true,
        }
    }

    fn write(path: &Path, content: &str) {
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, content).unwrap();
    }

    const DESIGN_WITH_TABLE: &str = "## 3. API Definition\n\n| Method | Endpoint | Auth | Request | Response | Error codes |\n|---|---|---|---|---|---|\n| POST | `/x` | JWT | `{}` | `{}` | 400 |\n";

    #[test]
    fn single_repo_feature_is_not_applicable_even_with_a_table() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("api").join("DESIGN.md"),
            DESIGN_WITH_TABLE,
        );

        let ecosystem = vec![repo("backend")];
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None);
        assert_eq!(state.status, ContractLockStatus::NotApplicable);
        assert!(state.not_applicable_reason.is_some());
    }

    #[test]
    fn multi_repo_no_table_anywhere_is_not_ready() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("api").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );
        write(
            &feature_dir.join("web").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );

        let ecosystem = vec![repo("backend"), repo("frontend")];
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None);
        assert_eq!(state.status, ContractLockStatus::NotReady);
    }

    #[test]
    fn multi_repo_with_complete_table_is_pending_review() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("api").join("DESIGN.md"),
            DESIGN_WITH_TABLE,
        );
        write(
            &feature_dir.join("web").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );

        let ecosystem = vec![repo("backend"), repo("frontend")];
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None);
        assert_eq!(state.status, ContractLockStatus::PendingReview);
        assert!(state.missing_columns.is_empty());
        assert_eq!(state.candidate_files.len(), 1);
        assert!(!state.candidate_files[0].checksum_sha256.is_empty());
    }

    #[test]
    fn missing_columns_are_reported_but_gate_still_opens() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("api").join("DESIGN.md"),
            "## 3. API Definition\n\n| Method | Endpoint |\n|---|---|\n| POST | `/x` |\n",
        );
        write(
            &feature_dir.join("web").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );

        let ecosystem = vec![repo("backend"), repo("frontend")];
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None);
        assert_eq!(state.status, ContractLockStatus::PendingReview); // AC-E4-10: still opens
        assert!(!state.missing_columns.is_empty());
    }

    #[test]
    fn applicable_roles_always_include_pm_and_qc_and_match_ecosystem() {
        let ecosystem = vec![repo("backend")];
        let roles = applicable_roles(&ecosystem);
        assert_eq!(roles, vec!["BE", "PM", "QC"]);
    }

    #[test]
    fn locked_status_is_sticky_regardless_of_current_disk_state() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature"); // no DESIGN.md at all
        let previous = ContractLockRecord {
            locked_at: "2026-08-17T00:00:00Z".to_string(),
            approved_by: "PM Test".to_string(),
            confirmed_roles: vec!["PM".to_string(), "QC".to_string()],
            files: vec![],
        };

        let state = infer_contract_lock_state(&feature_dir, &[], Some(previous));
        assert_eq!(state.status, ContractLockStatus::Locked);
        assert_eq!(state.current_lock.unwrap().approved_by, "PM Test");
    }

    fn locked_record(path: &Path, content: &str) -> ContractLockRecord {
        ContractLockRecord {
            locked_at: "2026-08-17T00:00:00Z".to_string(),
            approved_by: "PM Test".to_string(),
            confirmed_roles: vec!["PM".to_string(), "QC".to_string()],
            files: vec![crate::domain::contract_lock::LockedFile {
                path: path.display().to_string(),
                checksum_sha256: sha256_hex(content),
                content: content.to_string(),
            }],
        }
    }

    #[test]
    fn edited_locked_file_is_a_modified_violation() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        let design_md = feature_dir.join("api").join("DESIGN.md");
        write(&design_md, "original content");
        let previous = locked_record(&design_md, "original content");

        write(&design_md, "edited content"); // AC-E4-21
        let state = infer_contract_lock_state(&feature_dir, &[], Some(previous));

        assert_eq!(state.status, ContractLockStatus::Violated);
        assert_eq!(state.violated_files.len(), 1);
        assert_eq!(state.violated_files[0].kind, ViolationKind::Modified);
        assert_eq!(state.violated_files[0].locked_content, "original content");
    }

    #[test]
    fn deleted_locked_file_is_a_deleted_violation_naming_the_file() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        let design_md = feature_dir.join("api").join("DESIGN.md");
        write(&design_md, "original content");
        let previous = locked_record(&design_md, "original content");

        std::fs::remove_file(&design_md).unwrap(); // AC-E4-22
        let state = infer_contract_lock_state(&feature_dir, &[], Some(previous));

        assert_eq!(state.status, ContractLockStatus::Violated);
        assert_eq!(state.violated_files[0].kind, ViolationKind::Deleted);
        assert_eq!(
            state.violated_files[0].path,
            design_md.display().to_string()
        );
    }

    #[test]
    fn reverting_content_back_to_the_locked_checksum_self_heals() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        let design_md = feature_dir.join("api").join("DESIGN.md");
        write(&design_md, "original content");
        let previous = locked_record(&design_md, "original content");

        write(&design_md, "edited content");
        let violated = infer_contract_lock_state(&feature_dir, &[], Some(previous.clone()));
        assert_eq!(violated.status, ContractLockStatus::Violated);

        write(&design_md, "original content"); // AC-E4-26 — revert exactly
        let healed = infer_contract_lock_state(&feature_dir, &[], Some(previous));
        assert_eq!(healed.status, ContractLockStatus::Locked);
        assert!(healed.violated_files.is_empty());
    }
}
