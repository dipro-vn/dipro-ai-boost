//! AC-E4-30..32 — Memory Update Gate (SOFT). After a dev agent
//! (backend/frontend/mobile) finishes a run, checks whether the repo's
//! overview docs (`<docs_root>/<layer>/<repo>/overview/`) were touched
//! during that run. Never blocks anything — produces at most a warning
//! string the caller appends to the run's `last_message`.

use std::path::Path;
use std::time::SystemTime;

use crate::domain::project::EcosystemRepo;

/// The files the kit's dev agents are required to keep updated (per the
/// Memory Update Gate section in `.claude/agents/{backend,frontend,mobile}-agent.md`).
const OVERVIEW_FILES: &[&str] = &["api-catalog.md", "erd.md", "patterns.md", "structure.md"];

fn dir_touched_since(dir: &Path, since: SystemTime) -> bool {
    std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .filter_map(|entry| entry.ok())
        .any(|entry| {
            entry
                .metadata()
                .and_then(|m| m.modified())
                .map(|mtime| mtime >= since)
                .unwrap_or(false)
        })
}

/// `slot_role` is the repo role the slot targets (`"backend"`/`"frontend"`/
/// `"mobile"` — callers pass `slot_repo_role`'s result; `None` for non-dev
/// slots never reaches here). `started_at_rfc3339` is the run's start time.
///
/// Returns `Some(warning)` only when at least one matching repo HAS an
/// overview directory and NONE of its files were modified during the run
/// (AC-E4-31). Repos without an overview directory are `không áp dụng` —
/// silently skipped, no noise (AC-E4-32).
pub fn memory_update_warning(
    docs_root: &Path,
    ecosystem: &[EcosystemRepo],
    slot_role: &str,
    started_at_rfc3339: &str,
) -> Option<String> {
    let started_at: SystemTime = chrono::DateTime::parse_from_rfc3339(started_at_rfc3339)
        .ok()?
        .into();

    let stale_dirs: Vec<String> = ecosystem
        .iter()
        .filter(|repo| repo.role_key.as_deref() == Some(slot_role))
        .filter_map(|repo| {
            let overview_dir = docs_root.join(slot_role).join(&repo.name).join("overview");
            if !overview_dir.is_dir() {
                return None; // AC-E4-32 — không áp dụng, no warning noise
            }
            if dir_touched_since(&overview_dir, started_at) {
                return None; // AC-E4-30 — updated as required
            }
            Some(overview_dir.display().to_string())
        })
        .collect();

    if stale_dirs.is_empty() {
        return None;
    }

    Some(format!(
        "⚠ Memory Update Gate: không thấy overview docs nào được cập nhật trong lượt chạy này — lẽ ra nên cập nhật {} tại: {}. Pipeline vẫn chạy tiếp (gate mềm, không chặn).",
        OVERVIEW_FILES.join(", "),
        stale_dirs.join("; ")
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn repo(name: &str, role: &str) -> EcosystemRepo {
        EcosystemRepo {
            name: name.to_string(),
            declared_path: format!("repos/{name}"),
            role: role.to_string(),
            // Derived exactly as the parser does, so a fixture can never
            // claim a role the real pipeline wouldn't read off that cell.
            role_key: crate::agents_reader::canonical_role(role).map(str::to_string),
            stack: "x".to_string(),
            cloned: true,
        }
    }

    #[test]
    fn no_overview_dir_is_not_applicable_no_warning() {
        let tmp = tempfile::tempdir().unwrap();
        let ecosystem = vec![repo("api", "backend")];
        let warning =
            memory_update_warning(tmp.path(), &ecosystem, "backend", "2026-08-17T00:00:00Z");
        assert!(warning.is_none()); // AC-E4-32
    }

    #[test]
    fn untouched_overview_dir_warns_with_expected_files_and_path() {
        let tmp = tempfile::tempdir().unwrap();
        let overview = tmp.path().join("backend/api/overview");
        std::fs::create_dir_all(&overview).unwrap();
        std::fs::write(overview.join("api-catalog.md"), "old").unwrap();

        // A start time in the future of the file's mtime → nothing touched
        // during the run.
        let future = chrono::Utc::now() + chrono::Duration::hours(1);
        let ecosystem = vec![repo("api", "backend")];
        let warning =
            memory_update_warning(tmp.path(), &ecosystem, "backend", &future.to_rfc3339())
                .expect("warning expected");
        assert!(warning.contains("api-catalog.md")); // AC-E4-31: named files
        assert!(warning.contains("backend/api/overview"));
        assert!(warning.contains("không chặn")); // soft gate
    }

    #[test]
    fn touched_overview_file_suppresses_the_warning() {
        let tmp = tempfile::tempdir().unwrap();
        let overview = tmp.path().join("backend/api/overview");
        std::fs::create_dir_all(&overview).unwrap();

        // Run "started" an hour ago; file written now → touched during run.
        let past = chrono::Utc::now() - chrono::Duration::hours(1);
        std::fs::write(overview.join("erd.md"), "updated").unwrap();

        let ecosystem = vec![repo("api", "backend")];
        let warning = memory_update_warning(tmp.path(), &ecosystem, "backend", &past.to_rfc3339());
        assert!(warning.is_none()); // AC-E4-30 satisfied
    }
}
