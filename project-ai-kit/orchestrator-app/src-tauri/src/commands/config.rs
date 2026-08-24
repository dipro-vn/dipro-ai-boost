//! Settings screen's data commands (AC-E1-08..15) — thin read/write over
//! the `ProjectConfig` model `open_project` already reconciles + persists.

use std::path::Path;

use tauri::State;

use crate::agentrun::cli_path;
use crate::agents_reader;
use crate::app_state::AppState;
use crate::domain::config_file::ProjectConfig;
use crate::domain::project::ProjectPaths;
use crate::error::{AppError, AppResult};
use crate::store::atomic_write::write_json_atomic;
use crate::store::mcp_config::{self, McpServer};
use crate::store::mcp_status::{self, McpStatusEntry};
use crate::store::orchestrator_dir;

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

/// Reads `config.json` as-is — deliberately does NOT re-reconcile against
/// `.claude/agents/` (that happens once per `open_project`; re-running it
/// here would clear the one-cycle "mới" badges AC-E1-13 needs the Settings
/// screen to show). Missing/corrupt file → defaults from the currently
/// discovered agents, without overwriting anything on disk.
#[tauri::command]
pub fn get_config(state: State<AppState>) -> AppResult<ProjectConfig> {
    let project = current_project(&state)?;
    let agents_root = Path::new(&project.agents_root);
    let path = orchestrator_dir::config_json_path(agents_root);

    if let Some(config) = std::fs::read_to_string(&path)
        .ok()
        .and_then(|raw| serde_json::from_str::<ProjectConfig>(&raw).ok())
    {
        cli_path::set_override(config.claude_cli_path.as_deref());
        return Ok(config);
    }

    let discovered = agents_reader::discover_agents(agents_root).unwrap_or_default();
    Ok(ProjectConfig::with_defaults(&discovered))
}

/// AC-E1-11 — persists edits atomically; survives app restart. Changes
/// apply to the NEXT spawn only (`load_agent_config` re-reads per run —
/// AC-E1-24), never to an agent already running.
#[tauri::command]
pub fn set_config(state: State<AppState>, config: ProjectConfig) -> AppResult<()> {
    let project = current_project(&state)?;
    let path = orchestrator_dir::config_json_path(Path::new(&project.agents_root));
    // AC-E1-24 applies to models, not to this: a corrected CLI path has to
    // take effect on the very next Run, otherwise the user cannot recover
    // from a bad auto-detection without restarting the app.
    cli_path::set_override(config.claude_cli_path.as_deref());
    write_json_atomic(&path, &config)
}

/// AC-E1-25..27 — the project's own MCP servers, read-only. Env values are
/// never included (see `store::mcp_config`'s security note).
#[tauri::command]
pub fn get_mcp_servers(state: State<AppState>) -> AppResult<Vec<McpServer>> {
    let project = current_project(&state)?;
    Ok(mcp_config::read_mcp_servers(Path::new(
        &project.agents_root,
    )))
}

/// Live connection status of every MCP server the spawned agents can
/// actually reach — user-level config plus every `.mcp.json` up the tree
/// from the project, health-checked by `claude mcp list` itself.
///
/// `async` and off-thread on purpose: the health checks are network calls
/// (~8s observed), and a sync command would freeze the window for that
/// whole time.
#[tauri::command]
pub async fn get_mcp_status(state: State<'_, AppState>) -> AppResult<Vec<McpStatusEntry>> {
    let project = current_project(&state)?;
    let agents_root = std::path::PathBuf::from(project.agents_root);

    tauri::async_runtime::spawn_blocking(move || mcp_status::fetch_mcp_status(&agents_root))
        .await
        .map_err(|err| AppError::Invalid {
            message: format!("Không hoàn tất kiểm tra MCP: {err}"),
        })?
        .map_err(|message| AppError::Invalid { message })
}
