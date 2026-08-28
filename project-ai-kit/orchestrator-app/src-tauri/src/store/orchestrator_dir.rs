use std::cell::Cell;
use std::path::{Path, PathBuf};
use std::sync::{Mutex, MutexGuard, OnceLock};

use crate::error::{AppError, AppResult};

pub const ORCHESTRATOR_DIR_NAME: &str = ".orchestrator";

/// Feature and slot ids are used as directory components throughout the app.
/// Validate them once at the storage boundary so IPC callers cannot smuggle
/// absolute paths or `..` segments into `.orchestrator`.
pub fn validate_run_ids(feature: &str, slot: &str) -> AppResult<()> {
    validate_run_id(feature, "feature")?;
    validate_run_id(slot, "slot")
}

pub fn validate_feature_id(feature: &str) -> AppResult<()> {
    validate_run_id(feature, "feature")
}

fn validate_run_id(value: &str, kind: &str) -> AppResult<()> {
    if value.is_empty()
        || value.len() > 100
        || !value
            .chars()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-')
        || value.starts_with('-')
        || value.ends_with('-')
        || value.contains("--")
    {
        return Err(AppError::Invalid {
            message: format!("Tên {kind} không hợp lệ"),
        });
    }
    Ok(())
}

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
/// NOT reentrant, and the reentrancy hazard runs in BOTH directions: a
/// caller must neither take this lock before calling something that takes
/// it (`compute_and_persist`), nor still hold it when calling something
/// that does (`fswatch::watcher::recompute_and_emit`). The second half is
/// what `approve_trigger_gate` got wrong: it held the guard across its own
/// `recompute_and_emit`, and since Tauri runs non-async commands on the
/// main thread, the resulting self-deadlock froze the entire window.
///
/// So that a repeat never presents as a silent hang again, re-entry from a
/// thread that already holds the lock **panics** instead of parking
/// forever. A panic inside a Tauri command surfaces as an IPC error the
/// user can see and the app survives; a deadlock on the main thread is
/// unrecoverable. This is a correctness assertion, not a soft check — it is
/// compiled in release too, because that is where the freeze was observed.
pub fn lock_state_file() -> StateFileGuard {
    static LOCK: OnceLock<Mutex<()>> = OnceLock::new();

    HELD_BY_THIS_THREAD.with(|held| {
        assert!(
            !held.get(),
            "lock_state_file() is not reentrant — this thread already holds it. \
             Drop the guard before calling anything that locks state.json \
             (compute_and_persist / recompute_and_emit)."
        );
        held.set(true);
    });

    let guard = LOCK
        .get_or_init(|| Mutex::new(()))
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    StateFileGuard { _guard: guard }
}

thread_local! {
    /// Set for exactly as long as this thread holds `lock_state_file()`'s
    /// mutex — the flag `lock_state_file` asserts on. A `thread_local` (not
    /// a global) because reentrancy is per-thread: another thread blocking
    /// on the same mutex is the normal, correct case.
    static HELD_BY_THIS_THREAD: Cell<bool> = const { Cell::new(false) };
}

/// Guard returned by [`lock_state_file`]. Releasing the mutex and clearing
/// the per-thread held-flag are one operation, so no exit path — including
/// an early `?` or a panic unwind — can leave the flag set on a thread that
/// no longer holds the lock (which would make every later acquisition on
/// that thread panic).
pub struct StateFileGuard {
    _guard: MutexGuard<'static, ()>,
}

impl Drop for StateFileGuard {
    fn drop(&mut self) {
        HELD_BY_THIS_THREAD.with(|held| held.set(false));
    }
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

/// The single canonical shape for `runs_dir`'s app-defined report
/// convention (AC-E3-05) — `<runs_dir>/<run_id>/<filename>`, used by both
/// the writer (`agentrun::run_log::finalize_run`, after a QA/QC-testing/
/// QC-automation run) and every reader (`inference::stage_rules::run_files`
/// and friends). `run_id` is prefixed `<feature>--` so a report from one
/// feature's run can never be read as another feature's — this directory is
/// a single flat namespace shared by every feature in the project (unlike
/// `agent_runs_dir`, which nests by feature/slot on disk), so the feature
/// boundary has to live in the name itself. Keep this and `runs_dir_prefix`
/// in sync — the writer's `run_id` and the reader's filter MUST agree on
/// the exact same prefix or a report becomes permanently invisible.
pub fn runs_dir_run_id(feature: &str, slot: &str) -> String {
    format!("{feature}--{slot}")
}

/// The `run_id` prefix that scopes `runs_dir` entries to one feature — see
/// `runs_dir_run_id`.
pub fn runs_dir_prefix(feature: &str) -> String {
    format!("{feature}--")
}

/// A SEPARATE tree from `runs_dir` — that one is a flat, app-defined
/// namespace of report conventions (AC-E3-05, `<run-id>/<file>`, scoped by
/// prefix rather than nesting — see `runs_dir_run_id`). Agent-run
/// bookkeeping (T2.3) needs to be keyed by `(feature, slot)` specifically,
/// so it gets its own directory rather than overloading `runs_dir`'s
/// existing shape.
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

    /// The bug this guards: `approve_trigger_gate` held the guard across a
    /// call that re-locked, on Tauri's main thread, and the window froze
    /// with no error anywhere. Panicking is strictly better than that.
    #[test]
    #[should_panic(expected = "not reentrant")]
    fn lock_state_file_panics_instead_of_deadlocking_on_reentry() {
        let _first = lock_state_file();
        let _second = lock_state_file();
    }

    /// The other half: the flag must be cleared on drop, or the first
    /// legitimate acquisition would poison every later one on that thread.
    #[test]
    fn lock_state_file_can_be_retaken_after_the_guard_drops() {
        drop(lock_state_file());
        drop(lock_state_file());
        let _held = lock_state_file();
    }

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
