use tauri::AppHandle;
use tauri_plugin_store::StoreExt;

use crate::error::{AppError, AppResult};

/// Resolved via `BaseDirectory::AppData` by the store plugin — this is
/// app-level storage, NOT part of any project's `.orchestrator/` directory.
/// Theme must persist across projects (AC-E1-31) and never live inside a
/// project folder (AC-E1-32).
const STORE_FILE: &str = "settings.json";
const THEME_KEY: &str = "theme";
const DEFAULT_THEME: &str = "light";

fn is_valid_theme(theme: &str) -> bool {
    theme == "light" || theme == "dark"
}

/// Returns the persisted theme, defaulting to `"light"` (AC-E1-29) when
/// nothing has been saved yet or the stored value is not one of the two
/// sanctioned values.
#[tauri::command]
pub fn get_theme(app: AppHandle) -> AppResult<String> {
    let store = app.store(STORE_FILE)?;
    let theme = store
        .get(THEME_KEY)
        .and_then(|value| value.as_str().map(str::to_owned))
        .filter(|theme| is_valid_theme(theme))
        .unwrap_or_else(|| DEFAULT_THEME.to_string());
    Ok(theme)
}

#[tauri::command]
pub fn set_theme(app: AppHandle, theme: String) -> AppResult<()> {
    if !is_valid_theme(&theme) {
        return Err(AppError::Invalid {
            message: format!("invalid theme \"{theme}\" — must be \"light\" or \"dark\""),
        });
    }
    let store = app.store(STORE_FILE)?;
    store.set(THEME_KEY, theme);
    store.save()?;
    Ok(())
}
