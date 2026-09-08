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
    ContractLockRecord, ContractLockSkip, ContractLockState, ContractLockStatus, FileViolation,
    LockedFileRef, ViolationKind,
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
        .any(|repo| repo.role_key.as_deref() == Some(role))
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

fn not_applicable(
    applicable_roles: Vec<String>,
    reason: String,
    manually_skipped: bool,
) -> ContractLockState {
    ContractLockState {
        status: ContractLockStatus::NotApplicable,
        checked_design_md_paths: vec![],
        missing_columns: vec![],
        manually_skipped,
        not_applicable_reason: Some(reason),
        applicable_roles,
        candidate_files: vec![],
        current_lock: None,
        violated_files: vec![],
        running_on_old_contract: false,
    }
}

fn not_ready(
    applicable_roles: Vec<String>,
    checked_design_md_paths: Vec<String>,
) -> ContractLockState {
    ContractLockState {
        status: ContractLockStatus::NotReady,
        checked_design_md_paths,
        missing_columns: vec![],
        manually_skipped: false,
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
    skip: Option<ContractLockSkip>,
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
            checked_design_md_paths: vec![],
            missing_columns: vec![],
            manually_skipped: false,
            not_applicable_reason: None,
            applicable_roles: applicable,
            candidate_files: vec![],
            current_lock: Some(lock),
            violated_files: violations,
            running_on_old_contract: false,
        };
    }

    // AC-E4-11b — the PM's explicit override, checked right after an actual
    // lock (which outranks it: once locked there is nothing to skip) and
    // before every inferred rule, so it can rescue a feature the rules below
    // would dead-end at `NotReady`.
    if let Some(skip) = skip {
        return not_applicable(
            applicable,
            format!(
                "{} đánh dấu không cần Contract Lock: {}",
                skip.skipped_by, skip.reason
            ),
            true,
        );
    }

    // AC-E4-11 — takes priority over the table search: a single-repo
    // feature doesn't need Contract Lock regardless of what DESIGN.md
    // contains.
    if stage_rules::repo_subdirs(feature_dir).len() <= 1 {
        return not_applicable(
            applicable,
            "Feature chỉ chạm 1 repo — Contract Lock không áp dụng.".to_string(),
            false,
        );
    }

    // AC-E4-11a — what this gate freezes is the API contract BETWEEN a
    // backend and something that consumes it. With only one of those two
    // sides in the feature's scope there is no contract to freeze, and no
    // `DESIGN.md` will ever carry an API Definition table either: the kit's
    // `techlead-design-agent` writes that table only into the backend
    // repo's DESIGN.md. Without this branch such a feature sat at
    // `NotReady` forever with no button anywhere to move it — the exact
    // trap AC-E4-11 already fixed once for single-repo features.
    //
    // Only trusted when EVERY subfolder resolved to a declared repo — see
    // `feature_scope_roles`.
    let (scope_roles, unmatched) = stage_rules::feature_scope_roles(feature_dir, ecosystem);
    if unmatched.is_empty() {
        let has_backend = scope_roles.iter().any(|role| role == "backend");
        let has_consumer = scope_roles
            .iter()
            .any(|role| role == "frontend" || role == "mobile");
        if !has_backend || !has_consumer {
            let repos: Vec<String> = stage_rules::repo_subdirs(feature_dir)
                .iter()
                .filter_map(|dir| dir.file_name().and_then(|n| n.to_str()))
                .map(|name| name.to_string())
                .collect();
            let missing_side = if has_backend {
                "không repo nào tiêu thụ API (frontend/mobile)"
            } else {
                "không repo nào vai trò backend"
            };
            return not_applicable(
                applicable,
                format!(
                    "Feature chỉ chạm {} — {} nên không có API contract để khoá.",
                    repos.join(", "),
                    missing_side
                ),
                false,
            );
        }
    }

    let files = api_definition::design_md_files_with_api_table(feature_dir);
    if files.is_empty() {
        // AC-E4-08a — name every DESIGN.md the search actually looked at
        // (one per repo subdir), not just "no table found" in the abstract.
        let checked_design_md_paths = stage_rules::repo_subdirs(feature_dir)
            .into_iter()
            .map(|dir| dir.join("DESIGN.md").display().to_string())
            .collect();
        return not_ready(applicable, checked_design_md_paths); // AC-E4-08
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
        checked_design_md_paths: vec![],
        missing_columns,
        manually_skipped: false,
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
            // Derived exactly as the parser does, so a fixture can never
            // claim a role the real pipeline wouldn't read off that cell.
            role_key: crate::agents_reader::canonical_role(role).map(str::to_string),
            stack: "x".to_string(),
            cloned: true,
            resolved_path: Some("/tmp/repo".to_string()),
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
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None, None);
        assert_eq!(state.status, ContractLockStatus::NotApplicable);
        assert!(state.not_applicable_reason.is_some());
    }

    fn named_repo(name: &str, role: &str) -> EcosystemRepo {
        EcosystemRepo {
            name: name.to_string(),
            declared_path: format!("repos/{name}"),
            role: role.to_string(),
            // Derived exactly as the parser does, so a fixture can never
            // claim a role the real pipeline wouldn't read off that cell.
            role_key: crate::agents_reader::canonical_role(role).map(str::to_string),
            stack: "x".to_string(),
            cloned: true,
            resolved_path: Some("/tmp/repo".to_string()),
        }
    }

    /// The reported bug: a feature spanning web + mobile has no backend, so
    /// `techlead-design-agent` never writes an API Definition table for it
    /// — under the old repo-count rule it sat at `NotReady` with no button
    /// anywhere, blocking all of stage ⑤+ forever.
    #[test]
    fn a_feature_with_no_backend_in_scope_is_not_applicable() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("shop-web").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );
        write(
            &feature_dir.join("shop-app").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );

        let ecosystem = vec![
            named_repo("shop-api", "backend"),
            named_repo("shop-web", "frontend"),
            named_repo("shop-app", "mobile"),
        ];
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None, None);
        assert_eq!(state.status, ContractLockStatus::NotApplicable);
        assert!(!state.manually_skipped);
        let reason = state.not_applicable_reason.unwrap();
        assert!(reason.contains("backend"), "{reason}");
        assert!(reason.contains("shop-web"), "{reason}");
    }

    /// The mirror case — backend touched but nothing consuming it. There is
    /// still no two-sided contract to freeze.
    #[test]
    fn a_feature_with_no_api_consumer_in_scope_is_not_applicable() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(&feature_dir.join("shop-api").join("DESIGN.md"), DESIGN_WITH_TABLE);
        write(&feature_dir.join("shop-jobs").join("DESIGN.md"), DESIGN_WITH_TABLE);

        let ecosystem = vec![
            named_repo("shop-api", "backend"),
            named_repo("shop-jobs", "backend"),
            named_repo("shop-web", "frontend"),
        ];
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None, None);
        assert_eq!(state.status, ContractLockStatus::NotApplicable);
        assert!(state
            .not_applicable_reason
            .unwrap()
            .contains("frontend/mobile"));
    }

    /// The gate must NOT weaken for a real backend↔frontend feature — this
    /// is the case it exists for.
    #[test]
    fn a_backend_plus_frontend_feature_still_goes_through_the_table_check() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("shop-api").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );
        write(
            &feature_dir.join("shop-web").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );

        let ecosystem = vec![
            named_repo("shop-api", "backend"),
            named_repo("shop-web", "frontend"),
        ];
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None, None);
        assert_eq!(state.status, ContractLockStatus::NotReady);
    }

    /// `AGENTS.md` writes repo names in backticks often enough that this
    /// matters: with the decoration left on, `EcosystemRepo.name` never
    /// matched a feature's repo subfolder, so every feature on such a
    /// project fell into the "unmatched" chock below and Contract Lock
    /// stayed blocking regardless of scope.
    #[test]
    fn repo_names_written_in_markdown_still_match_a_feature_subdir() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("shop-web").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );
        write(
            &feature_dir.join("shop-app").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );

        let ecosystem = crate::agents_reader::build_ecosystem(
            "## Repos\n\n| Repo | Đường dẫn | Vai trò | Stack |\n|---|---|---|---|\n             | `shop-api` | `repos/shop-api` | backend — API chính | NestJS |\n             | `shop-web` | `repos/shop-web` | frontend — web admin | React |\n             | `shop-app` | `repos/shop-app` | mobile | Flutter |\n",
            &[tmp.path()],
        )
        .unwrap()
        .unwrap();

        // Scope is frontend + mobile, no backend -> genuinely not applicable,
        // rather than "couldn't match the folders" (which would keep it
        // blocking).
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None, None);
        assert_eq!(state.status, ContractLockStatus::NotApplicable);
        assert!(state
            .not_applicable_reason
            .unwrap()
            .contains("backend"));
    }

    /// The safety chock. An unrecognised subfolder means the Ecosystem
    /// table could not be trusted to say what is or isn't a backend —
    /// falling back to "no backend found, skip the gate" there would
    /// silently disable Contract Lock for every feature in a project whose
    /// `AGENTS.md` isn't filled in.
    #[test]
    fn an_unrecognised_repo_subdir_never_switches_the_gate_off() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("shop-web").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );
        write(
            &feature_dir.join("mystery-repo").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );

        // `mystery-repo` is not in the Ecosystem: roles are unknowable.
        let ecosystem = vec![named_repo("shop-web", "frontend")];
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None, None);
        assert_eq!(state.status, ContractLockStatus::NotReady);

        // Same feature with an empty Ecosystem — the "AGENTS.md not filled
        // in" case — must behave identically.
        let state = infer_contract_lock_state(&feature_dir, &[], None, None);
        assert_eq!(state.status, ContractLockStatus::NotReady);
    }

    fn skip_record() -> ContractLockSkip {
        ContractLockSkip {
            skipped_by: "PM Test".to_string(),
            reason: "Feature không thêm endpoint nào".to_string(),
            skipped_at: "2026-08-26T00:00:00Z".to_string(),
        }
    }

    /// AC-E4-11b — the manual escape hatch for a real backend↔frontend
    /// feature that defines no new endpoint.
    #[test]
    fn a_manual_skip_clears_a_gate_the_rules_would_leave_not_ready() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        write(
            &feature_dir.join("shop-api").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );
        write(
            &feature_dir.join("shop-web").join("DESIGN.md"),
            "## 1. Tổng quan\nx\n",
        );
        let ecosystem = vec![
            named_repo("shop-api", "backend"),
            named_repo("shop-web", "frontend"),
        ];

        assert_eq!(
            infer_contract_lock_state(&feature_dir, &ecosystem, None, None).status,
            ContractLockStatus::NotReady
        );

        let state =
            infer_contract_lock_state(&feature_dir, &ecosystem, None, Some(skip_record()));
        assert_eq!(state.status, ContractLockStatus::NotApplicable);
        // The undo button hangs off this flag — an inferred NotApplicable
        // must never offer it.
        assert!(state.manually_skipped);
        let reason = state.not_applicable_reason.unwrap();
        assert!(reason.contains("PM Test"), "{reason}");
        assert!(reason.contains("không thêm endpoint"), "{reason}");
    }

    /// An actual lock outranks a stale skip: once files are frozen their
    /// checksums still have to be honoured, skip or no skip.
    #[test]
    fn an_existing_lock_outranks_a_skip() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        let design = feature_dir.join("shop-api").join("DESIGN.md");
        write(&design, DESIGN_WITH_TABLE);

        let previous = ContractLockRecord {
            locked_at: "2026-08-17T00:00:00Z".to_string(),
            approved_by: "PM Test".to_string(),
            confirmed_roles: vec!["BE".to_string()],
            files: vec![crate::domain::contract_lock::LockedFile {
                path: design.display().to_string(),
                checksum_sha256: sha256_hex(DESIGN_WITH_TABLE),
                content: DESIGN_WITH_TABLE.to_string(),
            }],
        };

        let state = infer_contract_lock_state(
            &feature_dir,
            &[],
            Some(previous),
            Some(skip_record()),
        );
        assert_eq!(state.status, ContractLockStatus::Locked);
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
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None, None);
        assert_eq!(state.status, ContractLockStatus::NotReady);
        // AC-E4-08a — names every DESIGN.md it looked at, not just "none found".
        assert_eq!(state.checked_design_md_paths.len(), 2);
        assert!(state
            .checked_design_md_paths
            .iter()
            .any(|p| p.ends_with("api/DESIGN.md") || p.ends_with("api\\DESIGN.md")));
        assert!(state
            .checked_design_md_paths
            .iter()
            .any(|p| p.ends_with("web/DESIGN.md") || p.ends_with("web\\DESIGN.md")));
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
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None, None);
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
        let state = infer_contract_lock_state(&feature_dir, &ecosystem, None, None);
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

        let state = infer_contract_lock_state(&feature_dir, &[], Some(previous), None);
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
        let state = infer_contract_lock_state(&feature_dir, &[], Some(previous), None);

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
        let state = infer_contract_lock_state(&feature_dir, &[], Some(previous), None);

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
        let violated = infer_contract_lock_state(&feature_dir, &[], Some(previous.clone()), None);
        assert_eq!(violated.status, ContractLockStatus::Violated);

        write(&design_md, "original content"); // AC-E4-26 — revert exactly
        let healed = infer_contract_lock_state(&feature_dir, &[], Some(previous), None);
        assert_eq!(healed.status, ContractLockStatus::Locked);
        assert!(healed.violated_files.is_empty());
    }
}
