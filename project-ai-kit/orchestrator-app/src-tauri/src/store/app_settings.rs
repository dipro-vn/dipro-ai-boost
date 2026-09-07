//! Migration for app-level settings when the Tauri identifier changes.
//!
//! The store plugin resolves `settings.json` below the app data directory. A
//! product identifier change therefore creates a new directory unless the old
//! settings are copied first. Project-local `.orchestrator/` data is unrelated
//! and must never be moved by this module.

use std::path::{Path, PathBuf};

use serde_json::Value;
use tauri::{AppHandle, Manager, Runtime};

use crate::error::{AppError, AppResult};
use crate::store::atomic_write::write_json_atomic;

const SETTINGS_FILE: &str = "settings.json";
const LEGACY_IDENTIFIER: &str = "com.dipro.orchestrator-app";

fn settings_path(app_data_dir: &Path) -> PathBuf {
    app_data_dir.join(SETTINGS_FILE)
}

fn merge_missing_values(current: &mut Value, legacy: Value) -> bool {
    let (Value::Object(current), Value::Object(legacy)) = (current, legacy) else {
        return false;
    };

    let mut changed = false;
    for (key, value) in legacy {
        if !current.contains_key(&key) {
            current.insert(key, value);
            changed = true;
        }
    }
    changed
}

fn read_object(path: &Path) -> AppResult<Value> {
    let raw = std::fs::read_to_string(path)?;
    let value: Value = serde_json::from_str(&raw).map_err(|err| AppError::Invalid {
        message: format!("Không đọc được settings cũ: {err}"),
    })?;
    if !value.is_object() {
        return Err(AppError::Invalid {
            message: "settings cũ không có định dạng JSON object".to_string(),
        });
    }
    Ok(value)
}

/// Copies only missing settings from the old identifier's app-data directory.
/// The old file is retained so a failed or repeated migration is safe.
pub fn migrate<R: Runtime>(app: &AppHandle<R>) -> AppResult<bool> {
    let current_dir = app.path().app_data_dir().map_err(|err| AppError::Invalid {
        message: format!("Không xác định được thư mục settings của app: {err}"),
    })?;
    let Some(parent) = current_dir.parent() else {
        return Ok(false);
    };
    let legacy_path = settings_path(&parent.join(LEGACY_IDENTIFIER));
    if !legacy_path.is_file() {
        return Ok(false);
    }

    let legacy = read_object(&legacy_path)?;
    let current_path = settings_path(&current_dir);
    if !current_path.is_file() {
        write_json_atomic(&current_path, &legacy)?;
        return Ok(true);
    }

    let mut current = read_object(&current_path)?;
    if merge_missing_values(&mut current, legacy) {
        write_json_atomic(&current_path, &current)?;
        Ok(true)
    } else {
        Ok(false)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn merge_preserves_current_values_and_adds_legacy_values() {
        let mut current = serde_json::json!({
            "theme": "dark",
            "recentProjects": [{"label": "new"}]
        });
        let legacy = serde_json::json!({
            "theme": "light",
            "recentProjects": [{"label": "old"}],
            "oldSetting": true
        });

        assert!(merge_missing_values(&mut current, legacy));
        assert_eq!(current["theme"], "dark");
        assert_eq!(current["recentProjects"][0]["label"], "new");
        assert_eq!(current["oldSetting"], true);
    }

    #[test]
    fn merge_is_a_noop_for_non_objects() {
        let mut current = Value::String("current".to_string());
        assert!(!merge_missing_values(
            &mut current,
            Value::Object(serde_json::Map::new())
        ));
    }

    #[test]
    fn settings_path_uses_the_app_data_directory() {
        assert_eq!(
            settings_path(Path::new("/app-data")),
            Path::new("/app-data/settings.json")
        );
    }
}
