use std::collections::HashSet;
use std::sync::atomic::{AtomicBool, AtomicU64};
use std::sync::Mutex;

use crate::agentrun::process_registry::{ProcessRegistry, RunKey};
use crate::domain::project::{EcosystemRepo, ProjectPaths};
use crate::fswatch::watcher::ActiveDebouncer;

/// Tauri-managed runtime state: which project (if any) is currently open,
/// the active file-system watcher (if any), and any agent processes
/// currently running. Read/written by every command that needs to resolve
/// the current project's roots, start/stop watching, or spawn/kill agents.
#[derive(Default)]
pub struct AppState {
    pub current_project: Mutex<Option<ProjectPaths>>,
    /// `None` when nothing is being watched. Replacing this with a new
    /// value (or `None`) drops the old `Debouncer`, which stops it — see
    /// `fswatch::watcher::start`'s docs.
    pub watcher: Mutex<Option<ActiveDebouncer>>,
    /// Bumped by `start_watching`/`stop_watching` — a reconnect-with-backoff
    /// attempt (AC-E3-07) started under an older generation checks this
    /// before ever replacing `watcher`, so a stale reconnect for a feature
    /// the user already navigated away from (or explicitly stopped
    /// watching) can never clobber a newer watch.
    pub watch_generation: AtomicU64,
    /// Guards against piling up multiple concurrent reconnect-with-backoff
    /// threads for the same watch generation when several watch errors fire
    /// in quick succession.
    pub watch_reconnecting: AtomicBool,
    pub agent_runs: ProcessRegistry,
    /// The Ecosystem repo list computed at `open_project` time — retained
    /// here (rather than only living in that command's one-shot response)
    /// so `commands::agentrun::run_to_completion` can check whether a
    /// target repo is cloned before ever spawning (AC-E2-11/12).
    pub ecosystem: Mutex<Vec<EcosystemRepo>>,
    /// Slots whose `run_to_completion` thread has been spawned but whose
    /// child process hasn't landed in `ProcessRegistry` yet — checked
    /// alongside `agent_runs` so a double-click on Run in that window can't
    /// start the same slot twice. Entries are removed by
    /// `run_to_completion`'s drop-guard on every exit path.
    ///
    /// (The `chaining` mutex that used to serialize auto-chain decisions is
    /// gone with the chaining engine itself — B22.)
    pub pending_spawns: Mutex<HashSet<RunKey>>,
}

impl AppState {
    /// AC-E4-24 — used by both `commands::pipeline::get_pipeline_state` and
    /// `fswatch::watcher::recompute_and_emit` (the only 2 places besides
    /// `commands::agentrun` that have `AppState`) to check whether a slot
    /// has a live process, without either duplicating `RunKey`
    /// construction.
    pub fn is_running(&self, feature: &str, slot: &str) -> bool {
        self.agent_runs
            .get(&RunKey {
                feature: feature.to_string(),
                slot: slot.to_string(),
            })
            .is_some()
    }
}
