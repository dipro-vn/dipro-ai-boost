use std::path::{Path, PathBuf};
use std::sync::atomic::Ordering;
use std::time::Duration;

use notify::{RecommendedWatcher, RecursiveMode};
use notify_debouncer_full::{new_debouncer, DebounceEventResult, Debouncer, RecommendedCache};
use serde::Serialize;
use tauri::{AppHandle, Emitter, Manager};

use crate::app_state::AppState;
use crate::domain::state_file::FeatureState;
use crate::pipeline_state::compute_and_persist;
use crate::store::orchestrator_dir;

pub type ActiveDebouncer = Debouncer<RecommendedWatcher, RecommendedCache>;

/// NFR: "Watcher debounce 500ms" (`OVERVIEW.md` §7).
const DEBOUNCE_MS: u64 = 500;

pub const EVENT_STATE_CHANGED: &str = "pipeline://state-changed";
pub const EVENT_WATCH_ERROR: &str = "pipeline://watch-error";

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct StateChangedPayload {
    feature: String,
    state: FeatureState,
    /// AC-E3-06 / AC-E6-08 — non-fatal warnings surfaced alongside the state
    /// (e.g. a tracked artifact vanished, `state.json` was corrupt and got
    /// backed up). Empty in the common case.
    warnings: Vec<String>,
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct WatchErrorPayload {
    path: String,
    message: String,
}

/// `pub(crate)` rather than private: `commands::agentrun::run_to_completion`
/// reuses this directly after a run finishes, so the Board gets
/// `EVENT_STATE_CHANGED` even for outcomes (waiting-input, failed, timeout)
/// where nothing inside `feature_dir` actually changed on disk — those
/// wouldn't trigger the file watcher's own debounce callback on their own.
pub(crate) fn recompute_and_emit(
    app: &AppHandle,
    agents_root: &Path,
    docs_root: &Path,
    feature: &str,
) {
    let ecosystem = app.state::<AppState>().ecosystem.lock().unwrap().clone();
    match compute_and_persist(agents_root, docs_root, feature, &ecosystem) {
        Ok((mut state, warnings)) => {
            crate::commands::pipeline::mark_running_on_old_contract(
                &app.state::<AppState>(),
                feature,
                &mut state,
            );
            let _ = app.emit(
                EVENT_STATE_CHANGED,
                StateChangedPayload {
                    feature: feature.to_string(),
                    state,
                    warnings,
                },
            );
        }
        Err(err) => {
            let _ = app.emit(
                EVENT_WATCH_ERROR,
                WatchErrorPayload {
                    path: docs_root
                        .join("features")
                        .join(feature)
                        .display()
                        .to_string(),
                    message: err.to_string(),
                },
            );
        }
    }
}

/// Starts watching one feature's directory (plus `.ai-boost/runs/` for
/// QA/QC report conventions — AC-E3-05). The returned `Debouncer` must be
/// kept alive in `AppState`; dropping it stops the watch (see its `Drop`
/// impl). Deliberately does NOT watch `.ai-boost/contract.lock` /
/// the rest of `.ai-boost/` — recursively watching that directory
/// would self-trigger on our own `state.json` writes, since both live
/// side-by-side. Revisit properly once MVP3 needs Contract Lock inference.
///
/// Reads `AppState.watch_generation` at call time and closes over that
/// snapshot — see `spawn_reconnect_if_needed` for why this matters for
/// AC-E3-07's reconnect-with-backoff.
pub fn start(
    app: AppHandle,
    agents_root: PathBuf,
    docs_root: PathBuf,
    feature: String,
) -> notify::Result<ActiveDebouncer> {
    // Compute once immediately so the frontend has something to render
    // before the first file-system event ever fires — also doubles as the
    // "reconnected" signal after AC-E3-07's retry loop re-arms a watch: it
    // re-emits `EVENT_STATE_CHANGED`, which the Board already treats as
    // clearing any stale watch-error banner, so no separate event is needed.
    recompute_and_emit(&app, &agents_root, &docs_root, &feature);

    let generation = app
        .state::<AppState>()
        .watch_generation
        .load(Ordering::SeqCst);

    let cb_app = app.clone();
    let cb_agents_root = agents_root.clone();
    let cb_docs_root = docs_root.clone();
    let cb_feature = feature.clone();

    let mut debouncer = new_debouncer(
        Duration::from_millis(DEBOUNCE_MS),
        None,
        move |result: DebounceEventResult| match result {
            // Full-rescan-on-settle (see `inference::stage_rules` docs) —
            // deliberately ignores which specific paths changed.
            Ok(_events) => {
                recompute_and_emit(&cb_app, &cb_agents_root, &cb_docs_root, &cb_feature);
            }
            Err(errors) => {
                for error in &errors {
                    let _ = cb_app.emit(
                        EVENT_WATCH_ERROR,
                        WatchErrorPayload {
                            path: error
                                .paths
                                .first()
                                .map(|p| p.display().to_string())
                                .unwrap_or_default(),
                            message: error.to_string(),
                        },
                    );
                }
                spawn_reconnect_if_needed(
                    cb_app.clone(),
                    cb_agents_root.clone(),
                    cb_docs_root.clone(),
                    cb_feature.clone(),
                    generation,
                );
            }
        },
    )?;

    let feature_dir = docs_root.join("features").join(&feature);
    if feature_dir.is_dir() {
        debouncer.watch(&feature_dir, RecursiveMode::Recursive)?;
    }

    let runs_dir = orchestrator_dir::runs_dir(&agents_root);
    if runs_dir.is_dir() {
        debouncer.watch(&runs_dir, RecursiveMode::Recursive)?;
    }

    Ok(debouncer)
}

/// AC-E3-07 — kicks off a background reconnect-with-backoff attempt, unless
/// one is already running or this watch has since been superseded (the user
/// called `stop_watching`/`start_watching` again, bumping
/// `watch_generation`). Never called directly by anything except the
/// debouncer's own error callback above.
fn spawn_reconnect_if_needed(
    app: AppHandle,
    agents_root: PathBuf,
    docs_root: PathBuf,
    feature: String,
    generation: u64,
) {
    let state = app.state::<AppState>();
    if state.watch_generation.load(Ordering::SeqCst) != generation {
        return;
    }
    if state.watch_reconnecting.swap(true, Ordering::SeqCst) {
        return;
    }
    std::thread::spawn(move || {
        reconnect_with_backoff(app, agents_root, docs_root, feature, generation);
    });
}

/// Polls (with exponential backoff, capped) until `feature_dir` is
/// accessible again, then re-arms a fresh watch on it — `start()` itself
/// only *skips* watching a missing directory rather than treating that as
/// success, so this must check `is_dir()` itself rather than just retrying
/// `start()` blindly. Runs until it succeeds or `generation` goes stale;
/// never gives up on its own (AC-E3-07 does not bound how long the
/// directory may stay unavailable), and never panics on repeated failure.
fn reconnect_with_backoff(
    app: AppHandle,
    agents_root: PathBuf,
    docs_root: PathBuf,
    feature: String,
    generation: u64,
) {
    const INITIAL_BACKOFF: Duration = Duration::from_secs(2);
    const MAX_BACKOFF: Duration = Duration::from_secs(30);
    let feature_dir = docs_root.join("features").join(&feature);
    let mut backoff = INITIAL_BACKOFF;

    loop {
        std::thread::sleep(backoff);

        let state = app.state::<AppState>();
        if state.watch_generation.load(Ordering::SeqCst) != generation {
            state.watch_reconnecting.store(false, Ordering::SeqCst);
            return;
        }

        if feature_dir.is_dir() {
            if let Ok(new_debouncer) = start(
                app.clone(),
                agents_root.clone(),
                docs_root.clone(),
                feature.clone(),
            ) {
                let state = app.state::<AppState>();
                // Re-check after `start()` (which itself did I/O) in case
                // the user switched away while it was running — never apply
                // a reconnect result for a watch that's no longer current.
                if state.watch_generation.load(Ordering::SeqCst) == generation {
                    *state.watcher.lock().unwrap() = Some(new_debouncer);
                }
                state.watch_reconnecting.store(false, Ordering::SeqCst);
                return;
            }
        }

        backoff = std::cmp::min(backoff * 2, MAX_BACKOFF);
    }
}
