use std::collections::HashSet;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Mutex;

use crate::agentrun::cli_path;
use crate::agentrun::process_registry::{ProcessRegistry, RunKey};
use crate::domain::project::{EcosystemRepo, ProjectPaths};
use crate::error::{AppError, AppResult};
use crate::fswatch::watcher::ActiveDebouncer;

/// Tauri-managed runtime state: which project (if any) is currently open,
/// the active file-system watcher (if any), and any agent processes
/// currently running. Read/written by every command that needs to resolve
/// the current project's roots, start/stop watching, or spawn/kill agents.
#[derive(Default)]
pub struct AppState {
    pub current_project: Mutex<Option<ProjectPaths>>,
    /// Display/project name supplied in the launcher. Needed when the user
    /// asks the app to scaffold again after the external `/init-kit` handoff.
    pub current_project_label: Mutex<Option<String>>,
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
    /// Bumped by `close()` before it does anything else. A spawn captures
    /// this value synchronously (in the command handler, before its
    /// background thread starts any slow pre-spawn I/O), then
    /// `ProcessRegistry::insert_if_current` re-checks it atomically with
    /// the actual registration into `agent_runs`. A mismatch means the
    /// project closed in between, so the run kills the child it just
    /// spawned instead of registering it — this is what closes the TOCTOU
    /// between `close()` and an in-flight spawn (a `close()` that finds
    /// `agent_runs` empty used to be able to race a spawn that lands its
    /// process a moment later, orphaning it against a project the app no
    /// longer considers open).
    pub spawn_admission: Mutex<u64>,
    /// Claimed for the duration of `open_project_internal`'s check-then-set
    /// of `current_project` — closes the TOCTOU where two concurrent
    /// `open_project`/`open_existing_project` calls could both pass the
    /// "nothing open yet" check before either sets `current_project`.
    pub opening_claim: AtomicBool,
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

    /// Releases the currently open project so another one can be opened.
    ///
    /// Refuses while any agent is running unless `force`, because `RunKey`
    /// (feature + slot) carries no project id: leaving a run tracked while a
    /// different project is open means the new project's Board could match
    /// that key, show a foreign run as its own, and Kill the wrong process.
    /// `force` kills them first rather than leaving that hazard behind.
    ///
    /// `spawn_admission` is bumped before `kill_all` runs (not held across
    /// it): the bump and each spawn's own check+insert in
    /// `ProcessRegistry::insert_if_current` share one mutex, so every spawn
    /// either finishes registering strictly before this bump (in which case
    /// `kill_all` — running right after — still finds and kills it) or reads
    /// the bumped epoch and aborts on its own instead of registering. No
    /// spawn can land in `agent_runs` after this method returns.
    pub fn close(&self, force: bool) -> AppResult<()> {
        let running = self.agent_runs.keys();
        if !running.is_empty() && !force {
            let names: Vec<String> = running
                .iter()
                .map(|key| format!("{}/{}", key.feature, key.slot))
                .collect();
            return Err(AppError::Invalid {
                message: format!(
                    "Đang có {} agent chạy ({}) — dừng (Kill) trước, hoặc xác nhận đóng để kill hết",
                    running.len(),
                    names.join(", ")
                ),
            });
        }

        {
            *self.spawn_admission.lock().unwrap() += 1;
        }
        self.agent_runs.kill_all();

        // Same order `stop_watching` uses: bump the generation first so an
        // in-flight reconnect gives up instead of resurrecting a watch on a
        // project that is no longer open.
        self.watch_generation.fetch_add(1, Ordering::SeqCst);
        *self.watcher.lock().unwrap() = None;
        *self.current_project.lock().unwrap() = None;
        *self.current_project_label.lock().unwrap() = None;
        self.ecosystem.lock().unwrap().clear();
        self.pending_spawns.lock().unwrap().clear();
        cli_path::set_override(None);
        Ok(())
    }

    /// Claims `opening_claim` for the caller, or returns `None` if another
    /// open is already in progress. The returned guard releases the claim
    /// on drop (every exit path of `open_project_internal`), which is what
    /// makes the check-then-set of `current_project` in that function
    /// atomic with respect to a second concurrent `open_project`/
    /// `open_existing_project` call.
    pub fn try_claim_opening(&self) -> Option<OpeningGuard<'_>> {
        if self.opening_claim.swap(true, Ordering::SeqCst) {
            None
        } else {
            Some(OpeningGuard {
                flag: &self.opening_claim,
            })
        }
    }
}

pub struct OpeningGuard<'a> {
    flag: &'a AtomicBool,
}

impl Drop for OpeningGuard<'_> {
    fn drop(&mut self) {
        self.flag.store(false, Ordering::SeqCst);
    }
}

#[cfg(test)]
mod tests {
    use std::sync::Arc;

    use super::*;
    use crate::agentrun::process_registry::spawn_sleeper;

    /// Proves the actual guarantee Race A depends on: a spawn that captured
    /// its `expected_epoch` before `close()` ran, but whose child hasn't
    /// registered yet, must never land in `agent_runs` once `close()` has
    /// returned.
    #[test]
    fn close_refuses_to_orphan_a_spawn_reserved_before_it_ran() {
        let state = AppState::default();
        let epoch = *state.spawn_admission.lock().unwrap();

        state.close(false).unwrap();

        let key = RunKey {
            feature: "f1".to_string(),
            slot: "ba".to_string(),
        };
        let child = Arc::new(Mutex::new(spawn_sleeper()));
        let registered = state.agent_runs.insert_if_current(
            &state.spawn_admission,
            epoch,
            key.clone(),
            child.clone(),
        );

        assert!(!registered);
        assert!(state.agent_runs.get(&key).is_none());
        child.lock().unwrap().kill().unwrap();
    }

    /// The other half of Race A: a spawn that wins the race (registers
    /// before `close()` bumps the epoch) must still be killed by `close()`,
    /// not left running against a project the app no longer considers open.
    #[test]
    fn close_kills_a_process_that_wins_the_race_and_registers_first() {
        let state = AppState::default();
        let epoch = *state.spawn_admission.lock().unwrap();
        let key = RunKey {
            feature: "f1".to_string(),
            slot: "ba".to_string(),
        };
        let child = Arc::new(Mutex::new(spawn_sleeper()));
        let registered = state.agent_runs.insert_if_current(
            &state.spawn_admission,
            epoch,
            key.clone(),
            child.clone(),
        );
        assert!(registered);

        state.close(true).unwrap();

        assert!(state.agent_runs.get(&key).is_none());
        // Really dead, not just dropped from the map — `wait()` must return
        // promptly (mirrors `process_registry.rs`'s own `kill` assertion).
        let status = child.lock().unwrap().wait().unwrap();
        assert!(!status.success());
    }

    #[test]
    fn try_claim_opening_lets_only_one_claimant_through_at_a_time() {
        let state = AppState::default();

        let first = state.try_claim_opening();
        assert!(first.is_some());
        assert!(
            state.try_claim_opening().is_none(),
            "a second concurrent open must be refused while the first is in progress"
        );

        drop(first);
        assert!(
            state.try_claim_opening().is_some(),
            "releasing the guard must free the claim for the next open"
        );
    }
}
