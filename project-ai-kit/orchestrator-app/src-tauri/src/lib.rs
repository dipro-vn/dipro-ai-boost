mod agentrun;
mod agents_reader;
mod app_state;
mod auth;
mod commands;
mod domain;
mod error;
mod fs_detect;
mod fswatch;
mod gitutil;
mod inference;
mod integrations;
mod pipeline_state;
mod store;

use app_state::AppState;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            commands::theme::get_theme,
            commands::theme::set_theme,
            commands::project::detect_project_paths,
            commands::project::open_project,
            commands::project::scaffold_kit,
            commands::project::list_recent_projects,
            commands::project::remove_recent_project,
            commands::pipeline::list_features,
            commands::pipeline::get_pipeline_definition,
            commands::pipeline::get_pipeline_state,
            commands::pipeline::get_node_detail,
            commands::pipeline::start_watching,
            commands::pipeline::stop_watching,
            commands::pipeline::list_contract_locks,
            commands::pipeline::list_contract_violations,
            commands::artifact::read_artifact,
            commands::artifact::list_artifact_versions,
            commands::artifact::diff_artifact,
            commands::agentrun::kill_run,
            commands::agentrun::start_run,
            commands::agentrun::send_clarification_answer,
            commands::agentrun::get_run_summary,
            commands::agentrun::read_run_log,
            commands::agentrun::approve_trigger_gate,
            commands::agentrun::lock_contract,
            commands::agentrun::skip_run,
            commands::agentrun::resume_run,
            commands::agentrun::get_slot_readiness,
            commands::agentrun::run_slot,
            commands::agentrun::list_orphans,
            commands::agentrun::resolve_orphan,
            commands::project::list_running_slots,
            commands::project::close_project,
            commands::explorer::get_explorer_roots,
            commands::explorer::list_directory,
            commands::explorer::create_explorer_file,
            commands::explorer::create_explorer_folder,
            commands::explorer::preview_delete_explorer_entry,
            commands::explorer::delete_explorer_entry,
            commands::pipeline::create_feature,
            commands::pipeline::preview_delete_feature,
            commands::pipeline::delete_feature,
            commands::import::preview_import,
            commands::import::import_folder,
            commands::config::get_config,
            commands::config::set_config,
            commands::config::get_mcp_servers,
            commands::config::get_mcp_status,
            commands::auth::get_claude_auth_status,
            commands::auth::set_claude_auth_mode,
            commands::auth::save_claude_api_key,
            commands::auth::clear_claude_api_key,
            commands::auth::start_claude_login,
            commands::auth::logout_claude,
            commands::reports::list_run_history,
            commands::reports::export_cost_csv,
            commands::reports::clear_run_logs,
            commands::integrations::test_backlog_connection,
            commands::integrations::save_backlog_credentials,
            commands::integrations::get_backlog_status,
            commands::integrations::clear_backlog_credentials,
            commands::backlog::get_backlog_push_view,
            commands::backlog::push_to_backlog,
            commands::backlog::hash_task_file,
            commands::integrations::refresh_backlog_status,
            commands::integrations::get_backlog_status_cache,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
