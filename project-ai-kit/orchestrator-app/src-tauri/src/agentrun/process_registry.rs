use std::collections::HashMap;
use std::process::Child;
use std::sync::{Arc, Mutex};

use crate::agentrun::process_group::{self, Signal};
use crate::error::AppResult;

/// At most one live run per `(feature, slot)` at a time in MVP2 — no
/// concurrent multi-stage orchestration yet (that's MVP3).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct RunKey {
    pub feature: String,
    pub slot: String,
}

/// Tracks child processes currently spawned for agent runs. Shared between
/// the reader thread (owns reading stdout as it arrives) and Kill/timeout
/// (need to terminate the same child) — `Child::kill()` takes `&mut self`,
/// hence `Arc<Mutex<Child>>` rather than a bare `Child`.
#[derive(Default)]
pub struct ProcessRegistry {
    inner: Mutex<HashMap<RunKey, Arc<Mutex<Child>>>>,
}

impl ProcessRegistry {
    pub fn insert(&self, key: RunKey, child: Arc<Mutex<Child>>) {
        self.inner.lock().unwrap().insert(key, child);
    }

    pub fn remove(&self, key: &RunKey) {
        self.inner.lock().unwrap().remove(key);
    }

    pub fn get(&self, key: &RunKey) -> Option<Arc<Mutex<Child>>> {
        self.inner.lock().unwrap().get(key).cloned()
    }

    /// Kills the live process for `key`, if any — returns `false` (not an
    /// error) when nothing is running, since the Kill button can race a run
    /// that just finished on its own.
    pub fn kill(&self, key: &RunKey) -> AppResult<bool> {
        let Some(child) = self.get(key) else {
            return Ok(false);
        };
        {
            let mut guard = child.lock().unwrap();
            // Nhóm trước, tiến trình sau: MCP server con phải chết cùng,
            // nếu không chúng giữ pipe stdout và run coi như chưa kết thúc
            // dù CLI đã bị giết.
            process_group::signal_group(guard.id(), Signal::Kill);
            guard.kill()?;
        }
        self.remove(key);
        Ok(true)
    }

    /// Every run currently tracked. `RunKey` carries no project id, so this
    /// is scoped to whichever project is open — which is exactly why
    /// `close_project` has to consult it before letting the user leave.
    pub fn keys(&self) -> Vec<RunKey> {
        self.inner.lock().unwrap().keys().cloned().collect()
    }

    /// Kills everything tracked, returning how many were still alive.
    /// Best-effort per child: one process that refuses to die must not
    /// leave the rest running.
    pub fn kill_all(&self) -> usize {
        let keys = self.keys();
        keys.iter()
            .filter(|key| self.kill(key).unwrap_or(false))
            .count()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::{Command, Stdio};

    /// A plain, portable long-running OS process — process-registry
    /// mechanics don't need the real `claude` CLI to verify. `sleep` isn't
    /// available on Windows and `timeout.exe` refuses to run without a
    /// console handle when stdin is redirected (as it is under CI), so
    /// `ping` is used on both platforms instead — it has neither problem.
    fn spawn_sleeper() -> Child {
        #[cfg(target_os = "windows")]
        let mut cmd = {
            let mut c = Command::new("ping");
            c.args(["-n", "30", "127.0.0.1"]);
            c
        };
        #[cfg(not(target_os = "windows"))]
        let mut cmd = {
            let mut c = Command::new("ping");
            c.args(["-c", "30", "127.0.0.1"]);
            c
        };
        cmd.stdout(Stdio::null()).spawn().unwrap()
    }

    #[test]
    fn kill_terminates_the_tracked_process_and_removes_it() {
        let registry = ProcessRegistry::default();
        let key = RunKey {
            feature: "f1".to_string(),
            slot: "ba".to_string(),
        };
        let child = Arc::new(Mutex::new(spawn_sleeper()));
        registry.insert(key.clone(), child.clone());

        let killed = registry.kill(&key).unwrap();
        assert!(killed);
        assert!(registry.get(&key).is_none());

        // The process really did receive SIGKILL, not just get dropped
        // from the map — wait() must return promptly.
        let status = child.lock().unwrap().wait().unwrap();
        assert!(!status.success());
    }

    #[test]
    fn kill_on_unknown_key_returns_false_not_an_error() {
        let registry = ProcessRegistry::default();
        let key = RunKey {
            feature: "nonexistent".to_string(),
            slot: "ba".to_string(),
        };
        assert!(!registry.kill(&key).unwrap());
    }

    /// `close_project` leans on these two to decide whether the user may
    /// leave a project — `RunKey` has no project id, so a run left tracked
    /// would be mistaken for the next project's own.
    #[test]
    fn keys_lists_every_tracked_run_and_kill_all_clears_them() {
        let registry = ProcessRegistry::default();
        assert!(registry.keys().is_empty());
        assert_eq!(registry.kill_all(), 0, "nothing tracked, nothing killed");

        let keys = [
            RunKey {
                feature: "user-signup".to_string(),
                slot: "ba".to_string(),
            },
            RunKey {
                feature: "user-signup".to_string(),
                slot: "qc-design".to_string(),
            },
        ];
        for key in &keys {
            registry.insert(key.clone(), Arc::new(Mutex::new(spawn_sleeper())));
        }

        let mut listed = registry.keys();
        listed.sort_by(|a, b| a.slot.cmp(&b.slot));
        assert_eq!(listed, vec![keys[0].clone(), keys[1].clone()]);

        assert_eq!(registry.kill_all(), 2);
        assert!(registry.keys().is_empty(), "kill_all must untrack too");
    }
}
