use std::path::{Path, PathBuf};
use std::sync::{Mutex, MutexGuard, OnceLock};

use crate::error::{AppError, AppResult};

pub const ORCHESTRATOR_DIR_NAME: &str = ".orchestrator";

pub fn orchestrator_dir(project_root: &Path) -> PathBuf {
    project_root.join(ORCHESTRATOR_DIR_NAME)
}

pub fn config_json_path(project_root: &Path) -> PathBuf {
    orchestrator_dir(project_root).join("config.json")
}

pub fn pipeline_json_path(project_root: &Path) -> PathBuf {
    orchestrator_dir(project_root).join("pipeline.json")
}

/// Serializes the *whole* read-modify-write of `state.json`, which
/// `write_json_atomic` cannot: that guarantees no reader ever sees a torn
/// file, but says nothing about two threads each reading, then each writing
/// what they read. The loser's write silently drops the winner's update.
///
/// That is not hypothetical — three call sites reach `compute_and_persist`
/// from different threads (the watcher's debounce callback, a run finishing
/// in `run_to_completion`, and the `get_pipeline_state` IPC), and
/// `approve_trigger_gate` does its own read-modify-write on top. A Trigger
/// gate approval lives ONLY in this file, so a dropped update is a user's
/// approval vanishing with no trace.
///
/// One global lock rather than one per project: writes are short, and
/// nothing here is hot enough to justify keying it.
///
/// Poisoning is recovered from rather than propagated — the mutex guards
/// ordering, not data, so there is no invariant a panicking thread could
/// have left broken.
///
/// NOT reentrant. `approve_trigger_gate` calls `compute_and_persist` (which
/// takes this lock) before doing its own read-modify-write, so it must take
/// the lock only AFTER that call returns.
pub fn lock_state_file() -> MutexGuard<'static, ()> {
    static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    LOCK.get_or_init(|| Mutex::new(()))
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

pub fn state_json_path(project_root: &Path) -> PathBuf {
    orchestrator_dir(project_root).join("state.json")
}

pub fn snapshots_dir(project_root: &Path) -> PathBuf {
    orchestrator_dir(project_root).join("snapshots")
}

pub fn runs_dir(project_root: &Path) -> PathBuf {
    orchestrator_dir(project_root).join("runs")
}

/// Deliberately a SEPARATE tree from `runs_dir` — that one is a flat,
/// app-defined namespace of report conventions (AC-E3-05, `<run-id>/<file>`,
/// not partitioned by feature). Agent-run bookkeeping (T2.3) needs to be
/// keyed by `(feature, slot)` specifically, so it gets its own directory
/// rather than overloading `runs_dir`'s existing shape.
pub fn agent_runs_dir(project_root: &Path) -> PathBuf {
    orchestrator_dir(project_root).join("agent-runs")
}

fn agent_run_dir(project_root: &Path, feature: &str, slot: &str) -> PathBuf {
    agent_runs_dir(project_root).join(feature).join(slot)
}

/// The latest run's outcome/cost/session/timing for one `(feature, slot)` —
/// re-read on every `pipeline_state::compute_and_persist` so it survives
/// the same "always recompute from disk" model the rest of inference uses,
/// rather than living only in memory.
pub fn agent_run_summary_path(project_root: &Path, feature: &str, slot: &str) -> PathBuf {
    agent_run_dir(project_root, feature, slot).join("last-run.json")
}

/// Raw `stream-json` lines for the latest run of one `(feature, slot)` —
/// kept for later inspection (Log Console re-opening a finished run).
pub fn agent_run_log_path(project_root: &Path, feature: &str, slot: &str) -> PathBuf {
    agent_run_dir(project_root, feature, slot).join("log.jsonl")
}

/// In-flight marker for one `(feature, slot)` run — see
/// `domain::running_marker::RunningMarker`. Exists only while a run is
/// live; found at startup, it means the previous app instance died mid-run
/// (AC-E6-04/10).
pub fn agent_run_marker_path(project_root: &Path, feature: &str, slot: &str) -> PathBuf {
    agent_run_dir(project_root, feature, slot).join("running.json")
}

/// One directory per feature, holding one immutable timestamped JSON file
/// per Lock/Re-lock (AC-E4-19 — history retained, never overwritten) —
/// mirrors `snapshots_dir`'s timestamped-immutable-file convention. Not
/// created by `ensure_skeleton`, same reasoning as `inputs_dir`: only
/// comes into existence the first time a feature is actually locked.
pub fn contract_lock_dir(project_root: &Path, feature: &str) -> PathBuf {
    orchestrator_dir(project_root)
        .join("contract-locks")
        .join(feature)
}

/// One immutable timestamped JSON file per detected violation (AC-E4-26 —
/// history retained even after a violation self-heals). Nested under
/// `contract_lock_dir` rather than a sibling, since a violation only ever
/// makes sense relative to that feature's lock history.
pub fn contract_lock_violations_dir(project_root: &Path, feature: &str) -> PathBuf {
    contract_lock_dir(project_root, feature).join("violations")
}

/// Per-feature Backlog integration state (AC-E5-09/16): the
/// `task file ↔ issue key` mapping the push agent writes, and the status
/// cache the refresh keeps. Lazily created on first push, like
/// `contract_lock_dir`.
pub fn backlog_dir(project_root: &Path, feature: &str) -> PathBuf {
    orchestrator_dir(project_root).join("backlog").join(feature)
}

pub fn backlog_mapping_path(project_root: &Path, feature: &str) -> PathBuf {
    backlog_dir(project_root, feature).join("mapping.json")
}

/// Last successful status pull — kept so a failed refresh can still show
/// the previous numbers with an "as of" label instead of blanking out
/// (AC-E5-16).
pub fn backlog_status_cache_path(project_root: &Path, feature: &str) -> PathBuf {
    backlog_dir(project_root, feature).join("status-cache.json")
}

/// One immutable timestamped JSON file per agent run, cross-feature
/// (AC-E6-12..18) — see `store::run_history`. Separate from `agent-runs/`
/// (latest-run bookkeeping) so deleting logs there never touches cost
/// history here (AC-E6-28).
pub fn run_history_dir(project_root: &Path) -> PathBuf {
    orchestrator_dir(project_root).join("run-history")
}

/// Import Input's copy destination base (AC-E2-23) — `<inputs_dir>/<run-id>/`.
/// Not created by `ensure_skeleton`: unlike `snapshots`/`runs`/`agent-runs`,
/// which every project needs from the moment it's opened, this only comes
/// into existence the first time a folder is actually imported.
pub fn inputs_dir(project_root: &Path) -> PathBuf {
    orchestrator_dir(project_root).join("inputs")
}

/// Keeps `.orchestrator/` out of the user's git history, by ignoring itself
/// rather than by editing the project's own `.gitignore` — that file belongs
/// to the user and this app has no business rewriting it.
///
/// This is not tidiness, it is the whole point: `agent-runs/<f>/<slot>/log.jsonl`
/// stores the raw `stream-json` of every run verbatim, and those lines carry
/// `ToolCall.input` and `ToolResult.content` — i.e. the full text of every file
/// the agent wrote and read. Left un-ignored, one `git add .` commits the
/// project's own source into history, which is exactly what the kit's
/// `POLICY.md` §NO_CODE_EXFILTRATION forbids. `inputs/` (copies of imported
/// folders) and `config.json` (Backlog wiring) live here too.
/// Leading whitespace is significant in a `.gitignore` pattern — git does
/// not trim it — so this is a raw literal starting at column 0 rather than
/// an indented, continued string.
const SELF_IGNORE: &str = r"# Máy tự sinh — thư mục này chứa transcript agent (gồm nguyên văn nội dung
# file agent đã đọc/ghi) và bản sao thư mục input. Không được commit.
*
";

/// Creates `.orchestrator/{snapshots,runs,agent-runs}` under `project_root`
/// if missing, plus the self-ignoring `.gitignore` above. `config.json`/
/// `pipeline.json`/`state.json` are written separately by their own owners
/// (config_file, pipeline_def, fswatch) — this only guarantees the directory
/// skeleton exists.
pub fn ensure_skeleton(project_root: &Path) -> AppResult<()> {
    std::fs::create_dir_all(orchestrator_dir(project_root))?;
    std::fs::create_dir_all(snapshots_dir(project_root))?;
    std::fs::create_dir_all(runs_dir(project_root))?;
    std::fs::create_dir_all(agent_runs_dir(project_root))?;

    // Never overwritten: a user who edited it (say, to un-ignore one report)
    // meant it. Only the absence of the file is ours to fix.
    let gitignore = orchestrator_dir(project_root).join(".gitignore");
    if !gitignore.exists() {
        std::fs::write(&gitignore, SELF_IGNORE)?;
    }
    Ok(())
}

/// Canonicalizes `path` and asserts it falls within `allowed_root`. Every
/// function in this codebase that reads or writes a file supplied (even
/// indirectly) by the frontend MUST call this first — it is the single
/// enforcement point for "the app never touches anything outside project
/// roots it was explicitly given, plus its own `.orchestrator/`".
///
/// Uses `dunce::canonicalize` rather than `std::fs::canonicalize` — the
/// stdlib version prefixes Windows paths with `\\?\`, which breaks a naive
/// string-prefix comparison and can turn this guard into a silent no-op on
/// Windows. This bug would never surface on the macOS dev machine this was
/// written on, only on Windows CI/users — see plan risk #4.
pub fn assert_within(path: &Path, allowed_root: &Path) -> AppResult<PathBuf> {
    let canonical_path = dunce::canonicalize(path)?;
    let canonical_root = dunce::canonicalize(allowed_root)?;
    if canonical_path.starts_with(&canonical_root) {
        Ok(canonical_path)
    } else {
        Err(AppError::PathOutsideRoot {
            path: canonical_path.display().to_string(),
        })
    }
}

/// `read_artifact` has 3 independent legitimate roots to allow (agentsRoot,
/// docsRoot, repositoryRoot — there is no single "project root" since A1),
/// so it needs "within ANY of these", not just one. Succeeds on the first
/// root that accepts the path; if none do, returns the error from the
/// first attempt (arbitrary but stable — good enough for an error message,
/// the caller doesn't need to know all 3 failed for the same reason).
pub fn assert_within_any(path: &Path, allowed_roots: &[&Path]) -> AppResult<PathBuf> {
    let mut first_err = None;
    for root in allowed_roots {
        match assert_within(path, root) {
            Ok(canonical) => return Ok(canonical),
            Err(err) => {
                if first_err.is_none() {
                    first_err = Some(err);
                }
            }
        }
    }
    Err(first_err.unwrap_or(AppError::PathOutsideRoot {
        path: path.display().to_string(),
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The `log.jsonl` files under here hold whole source files verbatim, so
    /// "not committed" has to be true from the very first run — not something
    /// the user is expected to remember.
    #[test]
    fn ensure_skeleton_makes_the_directory_ignore_itself() {
        let tmp = tempfile::tempdir().unwrap();
        ensure_skeleton(tmp.path()).unwrap();

        let gitignore = orchestrator_dir(tmp.path()).join(".gitignore");
        let contents = std::fs::read_to_string(&gitignore).unwrap();
        // Compared WITHOUT trimming on purpose: git treats leading spaces as
        // part of the pattern, so an indented `*` silently ignores nothing.
        assert!(
            contents.lines().any(|line| line == "*"),
            "the ignore rule must be exactly `*`, unindented, got: {contents:?}"
        );
        assert!(
            contents.lines().all(|line| !line.starts_with(' ')),
            "no pattern line may be indented: {contents:?}"
        );
    }

    #[test]
    fn ensure_skeleton_never_overwrites_a_gitignore_the_user_edited() {
        let tmp = tempfile::tempdir().unwrap();
        ensure_skeleton(tmp.path()).unwrap();

        let gitignore = orchestrator_dir(tmp.path()).join(".gitignore");
        std::fs::write(&gitignore, "*\n!runs/\n").unwrap();
        ensure_skeleton(tmp.path()).unwrap();

        assert_eq!(std::fs::read_to_string(&gitignore).unwrap(), "*\n!runs/\n");
    }

    #[test]
    fn assert_within_accepts_path_inside_root() {
        let tmp = tempfile::tempdir().unwrap();
        let file = tmp.path().join("SPEC.md");
        std::fs::write(&file, "content").unwrap();

        assert!(assert_within(&file, tmp.path()).is_ok());
    }

    #[test]
    fn assert_within_rejects_path_outside_root() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path().join("allowed");
        let outside = tmp.path().join("not-allowed");
        std::fs::create_dir_all(&root).unwrap();
        std::fs::create_dir_all(&outside).unwrap();
        let file = outside.join("secret.md");
        std::fs::write(&file, "content").unwrap();

        assert!(assert_within(&file, &root).is_err());
    }

    #[test]
    fn assert_within_rejects_traversal_out_of_root() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path().join("allowed");
        std::fs::create_dir_all(&root).unwrap();
        let outside_file = tmp.path().join("outside.md");
        std::fs::write(&outside_file, "content").unwrap();

        // `../outside.md` from inside `root` resolves outside of it.
        let traversal_path = root.join("../outside.md");
        assert!(assert_within(&traversal_path, &root).is_err());
    }

    #[test]
    fn assert_within_any_succeeds_if_any_root_matches() {
        let tmp = tempfile::tempdir().unwrap();
        let root_a = tmp.path().join("a");
        let root_b = tmp.path().join("b");
        std::fs::create_dir_all(&root_a).unwrap();
        std::fs::create_dir_all(&root_b).unwrap();
        let file_in_b = root_b.join("SPEC.md");
        std::fs::write(&file_in_b, "content").unwrap();

        assert!(assert_within_any(&file_in_b, &[&root_a, &root_b]).is_ok());
    }

    #[test]
    fn assert_within_any_rejects_when_no_root_matches() {
        let tmp = tempfile::tempdir().unwrap();
        let root_a = tmp.path().join("a");
        let root_b = tmp.path().join("b");
        let elsewhere = tmp.path().join("elsewhere");
        std::fs::create_dir_all(&root_a).unwrap();
        std::fs::create_dir_all(&root_b).unwrap();
        std::fs::create_dir_all(&elsewhere).unwrap();
        let file = elsewhere.join("SPEC.md");
        std::fs::write(&file, "content").unwrap();

        assert!(assert_within_any(&file, &[&root_a, &root_b]).is_err());
    }
}
