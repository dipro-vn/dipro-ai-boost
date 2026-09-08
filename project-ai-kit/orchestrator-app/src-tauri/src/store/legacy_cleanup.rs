//! One-shot, idempotent cleanup of on-disk traces of features the kit no
//! longer has: the `pm` pipeline slot (`pm-agent`) and the whole Backlog
//! integration.
//!
//! Every operation is "remove if present", so running this on every project
//! open is safe — which is exactly what `commands::project` does. The
//! report it returns is what keeps the user-facing warning to the single
//! run that actually removed something.
//!
//! JSON is edited as `serde_json::Value`, never through `ProjectConfig` /
//! `StateFile`. Those structs no longer carry the fields being removed, so
//! a typed round-trip would silently drop them — plus anything else an
//! older or newer build wrote. Working on `Value` removes exactly the keys
//! named here and leaves the rest byte-for-byte.

use std::path::Path;

use crate::store::atomic_write::write_json_atomic;
use crate::store::orchestrator_dir;

/// The removed pipeline slot and the pseudo-slot the Backlog push ran on.
const PM_SLOT: &str = "pm";
const BACKLOG_PUSH_SLOT: &str = "backlog-push";
const PM_AGENT: &str = "pm-agent";

/// What one run actually removed. The all-empty value is the steady state
/// after the first open.
#[derive(Debug, Default, PartialEq, Eq)]
pub struct LegacyCleanupReport {
    /// Features whose `nodes` map still carried a `"pm"` entry.
    pub state_features_cleaned: Vec<String>,
    /// `.ai-boost/agent-runs/<feature>/{pm,backlog-push}/` removed.
    pub run_dirs_removed: Vec<String>,
    /// `.ai-boost/backlog/` removed wholesale.
    pub backlog_dir_removed: bool,
    pub config_pm_agent_removed: bool,
    pub config_pm_nickname_removed: bool,
    pub config_backlog_removed: bool,
    /// The keychain entry `backlog.credential_ref` pointed at.
    pub keychain_entry_removed: bool,
}

impl LegacyCleanupReport {
    pub fn is_empty(&self) -> bool {
        self.state_features_cleaned.is_empty()
            && self.run_dirs_removed.is_empty()
            && !self.backlog_dir_removed
            && !self.config_pm_agent_removed
            && !self.config_pm_nickname_removed
            && !self.config_backlog_removed
            && !self.keychain_entry_removed
    }

    /// One user-facing sentence, or `None` when nothing happened.
    pub fn warning(&self) -> Option<String> {
        if self.is_empty() {
            return None;
        }
        let mut parts: Vec<String> = vec![];
        if !self.state_features_cleaned.is_empty() {
            parts.push(format!(
                "node `pm` ở {} feature",
                self.state_features_cleaned.len()
            ));
        }
        if !self.run_dirs_removed.is_empty() {
            parts.push(format!("{} thư mục log cũ", self.run_dirs_removed.len()));
        }
        if self.backlog_dir_removed {
            parts.push("dữ liệu mapping Backlog".to_string());
        }
        if self.config_pm_agent_removed || self.config_pm_nickname_removed {
            parts.push("cấu hình `pm-agent`".to_string());
        }
        if self.config_backlog_removed {
            parts.push("cấu hình Backlog".to_string());
        }
        if self.keychain_entry_removed {
            parts.push("API key Backlog trong OS keychain".to_string());
        }
        Some(format!(
            "Đã dọn dữ liệu của các tính năng không còn trong kit ({}). `pm-agent` và tính năng đẩy issue lên Backlog đã được gỡ bỏ.",
            parts.join(", ")
        ))
    }
}

/// Never returns `Err`: this is best-effort housekeeping on the
/// open-project path, and a project must open even when a leftover file is
/// unreadable. A file that fails to parse is left exactly as it is — the
/// existing back-up-then-rebuild recovery in `load_or_reset_config` and
/// `pipeline_state::compute_and_persist` is what should see it, not us.
pub fn purge(agents_root: &Path) -> LegacyCleanupReport {
    let mut report = LegacyCleanupReport::default();
    purge_config(agents_root, &mut report);
    purge_state(agents_root, &mut report);
    purge_run_dirs(agents_root, &mut report);

    let backlog_dir = orchestrator_dir::orchestrator_dir(agents_root).join("backlog");
    if backlog_dir.exists() && std::fs::remove_dir_all(&backlog_dir).is_ok() {
        report.backlog_dir_removed = true;
    }

    report
}

fn read_json(path: &Path) -> Option<serde_json::Value> {
    let raw = std::fs::read_to_string(path).ok()?;
    serde_json::from_str(&raw).ok()
}

fn purge_config(agents_root: &Path, report: &mut LegacyCleanupReport) {
    let path = orchestrator_dir::config_json_path(agents_root);
    let Some(mut value) = read_json(&path) else {
        return;
    };
    let Some(root) = value.as_object_mut() else {
        return;
    };

    if let Some(agents) = root.get_mut("agents").and_then(|v| v.as_object_mut()) {
        report.config_pm_agent_removed = agents.remove(PM_AGENT).is_some();
    }
    if let Some(nicknames) = root
        .get_mut("node_nicknames")
        .and_then(|v| v.as_object_mut())
    {
        report.config_pm_nickname_removed = nicknames.remove(PM_SLOT).is_some();
    }

    // Grab the keychain pointer before dropping the block that holds it.
    let credential_ref = root
        .get("backlog")
        .and_then(|b| b.get("credential_ref"))
        .and_then(|c| c.as_str())
        .map(str::to_string);
    report.config_backlog_removed = root.remove("backlog").is_some();

    if report.config_pm_agent_removed
        || report.config_pm_nickname_removed
        || report.config_backlog_removed
    {
        let _ = write_json_atomic(&path, &value);
    }
    if let Some(account) = credential_ref {
        report.keychain_entry_removed =
            crate::store::keychain::delete_legacy_backlog_api_key(&account);
    }
}

fn purge_state(agents_root: &Path, report: &mut LegacyCleanupReport) {
    let _guard = orchestrator_dir::lock_state_file();
    let path = orchestrator_dir::state_json_path(agents_root);
    let Some(mut value) = read_json(&path) else {
        return;
    };
    let Some(features) = value
        .as_object_mut()
        .and_then(|root| root.get_mut("features"))
        .and_then(|v| v.as_object_mut())
    else {
        return;
    };

    for (feature, state) in features.iter_mut() {
        let removed = state
            .as_object_mut()
            .and_then(|s| s.get_mut("nodes"))
            .and_then(|v| v.as_object_mut())
            .is_some_and(|nodes| nodes.remove(PM_SLOT).is_some());
        if removed {
            report.state_features_cleaned.push(feature.clone());
        }
    }

    if !report.state_features_cleaned.is_empty() {
        let _ = write_json_atomic(&path, &value);
    }
}

fn purge_run_dirs(agents_root: &Path, report: &mut LegacyCleanupReport) {
    let Ok(entries) = std::fs::read_dir(orchestrator_dir::agent_runs_dir(agents_root)) else {
        return;
    };
    for entry in entries.flatten() {
        let feature_dir = entry.path();
        if !feature_dir.is_dir() {
            continue;
        }
        for slot in [PM_SLOT, BACKLOG_PUSH_SLOT] {
            let slot_dir = feature_dir.join(slot);
            if slot_dir.exists() && std::fs::remove_dir_all(&slot_dir).is_ok() {
                report
                    .run_dirs_removed
                    .push(format!("{}/{slot}", entry.file_name().to_string_lossy()));
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn write(path: &Path, value: &serde_json::Value) {
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, serde_json::to_string_pretty(value).unwrap()).unwrap();
    }

    fn read(path: &Path) -> serde_json::Value {
        serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap()
    }

    #[test]
    fn purge_is_a_no_op_on_a_project_that_never_had_pm_or_backlog() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();
        write(
            &orchestrator_dir::config_json_path(root),
            &json!({ "agents": { "ba-agent": { "model": "opus" } } }),
        );

        let report = purge(root);

        assert!(report.is_empty());
        assert_eq!(report.warning(), None);
    }

    #[test]
    fn purge_never_errs_when_the_orchestrator_dir_does_not_exist() {
        let tmp = tempfile::tempdir().unwrap();
        assert!(purge(tmp.path()).is_empty());
    }

    #[test]
    fn purge_drops_the_pm_node_from_every_feature_in_state_json() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();
        let state = orchestrator_dir::state_json_path(root);
        write(
            &state,
            &json!({ "features": {
                "a": { "nodes": { "ba": { "status": "done" }, "pm": { "status": "done" } } },
                "b": { "nodes": { "pm": { "status": "idle" } } },
                "c": { "nodes": { "ba": { "status": "idle" } } },
            }}),
        );

        let mut report = purge(root);
        report.state_features_cleaned.sort();

        assert_eq!(report.state_features_cleaned, vec!["a", "b"]);
        let after = read(&state);
        assert!(after["features"]["a"]["nodes"]["pm"].is_null());
        assert!(after["features"]["a"]["nodes"]["ba"].is_object());
        assert!(after["features"]["b"]["nodes"]["pm"].is_null());
    }

    /// The `Value`-not-`StateFile` guarantee: fields the current structs no
    /// longer know about must survive untouched. Guards a "helpful"
    /// refactor to a typed round-trip.
    #[test]
    fn purge_preserves_gates_and_unknown_fields_while_dropping_the_pm_node() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();
        let state = orchestrator_dir::state_json_path(root);
        write(
            &state,
            &json!({ "features": {
                "a": {
                    "nodes": { "pm": { "status": "done" } },
                    "gates": { "S1b_trigger": { "approved": true } },
                    "contractLock": { "status": "pendingReview", "planMdMissing": false },
                    "someFutureField": 42,
                }
            }}),
        );

        purge(root);

        let after = read(&state);
        assert!(after["features"]["a"]["nodes"]["pm"].is_null());
        assert_eq!(
            after["features"]["a"]["gates"]["S1b_trigger"]["approved"],
            true
        );
        assert_eq!(
            after["features"]["a"]["contractLock"]["status"],
            "pendingReview"
        );
        assert_eq!(after["features"]["a"]["someFutureField"], 42);
    }

    #[test]
    fn purge_removes_pm_and_backlog_push_run_dirs_but_keeps_sibling_slots() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();
        let runs = orchestrator_dir::agent_runs_dir(root);
        for slot in ["pm", "backlog-push", "ba"] {
            std::fs::create_dir_all(runs.join("feature-a").join(slot)).unwrap();
            std::fs::write(
                runs.join("feature-a").join(slot).join("last-run.json"),
                "{}",
            )
            .unwrap();
        }

        let report = purge(root);

        assert_eq!(report.run_dirs_removed.len(), 2);
        assert!(!runs.join("feature-a/pm").exists());
        assert!(!runs.join("feature-a/backlog-push").exists());
        assert!(runs.join("feature-a/ba").exists());
    }

    #[test]
    fn purge_drops_pm_agent_backlog_and_the_nickname_while_keeping_unknown_config_fields() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();
        let config = orchestrator_dir::config_json_path(root);
        write(
            &config,
            &json!({
                "agents": { "ba-agent": { "model": "opus" }, "pm-agent": { "model": "sonnet" } },
                "node_nicknames": { "ba": "Núi BA", "pm": "Anh Long PM" },
                "backlog": { "domain": "x.backlog.com", "project_key": "P", "credential_ref": "x.backlog.com" },
                "max_retries": 2,
                "some_future_field": "keep me",
            }),
        );
        std::fs::create_dir_all(
            orchestrator_dir::orchestrator_dir(root)
                .join("backlog")
                .join("feature-a"),
        )
        .unwrap();

        let report = purge(root);

        assert!(report.config_pm_agent_removed);
        assert!(report.config_pm_nickname_removed);
        assert!(report.config_backlog_removed);
        assert!(report.backlog_dir_removed);

        let after = read(&config);
        assert!(after["agents"]["pm-agent"].is_null());
        assert!(after["agents"]["ba-agent"].is_object());
        assert!(after["node_nicknames"]["pm"].is_null());
        assert_eq!(after["node_nicknames"]["ba"], "Núi BA");
        assert!(after["backlog"].is_null());
        assert_eq!(after["max_retries"], 2);
        assert_eq!(after["some_future_field"], "keep me");
    }

    #[test]
    fn running_purge_twice_reports_nothing_the_second_time() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();
        write(
            &orchestrator_dir::config_json_path(root),
            &json!({ "agents": { "pm-agent": { "model": "sonnet" } } }),
        );
        write(
            &orchestrator_dir::state_json_path(root),
            &json!({ "features": { "a": { "nodes": { "pm": { "status": "done" } } } } }),
        );
        std::fs::create_dir_all(orchestrator_dir::agent_runs_dir(root).join("a").join("pm"))
            .unwrap();

        let first = purge(root);
        assert!(!first.is_empty());
        assert!(first.warning().is_some());

        let second = purge(root);
        assert!(second.is_empty(), "{second:?}");
        assert_eq!(second.warning(), None);
    }

    /// A corrupt file is left exactly as-is: the existing
    /// back-up-then-rebuild recovery elsewhere is what should see it.
    #[test]
    fn purge_leaves_corrupt_json_untouched() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path();
        let config = orchestrator_dir::config_json_path(root);
        std::fs::create_dir_all(config.parent().unwrap()).unwrap();
        std::fs::write(&config, "{ not json at all").unwrap();

        let report = purge(root);

        assert!(report.is_empty());
        assert_eq!(
            std::fs::read_to_string(&config).unwrap(),
            "{ not json at all"
        );
    }
}
