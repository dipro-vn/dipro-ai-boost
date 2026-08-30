//! Cost & Reports commands (AC-E6-12..18, 28) — read-only aggregation over
//! `store::run_history` plus CSV export and log cleanup.

use std::path::Path;

use tauri::State;

use crate::app_state::AppState;
use crate::domain::pipeline_def::PipelineDef;
use crate::domain::project::ProjectPaths;
use crate::domain::run_history::RunHistoryRecord;
use crate::error::{AppError, AppResult};
use crate::store::orchestrator_dir;
use crate::store::run_history;

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

#[tauri::command]
pub fn list_run_history(state: State<AppState>) -> AppResult<Vec<RunHistoryRecord>> {
    let project = current_project(&state)?;
    Ok(run_history::list_records(
        &orchestrator_dir::run_history_dir(Path::new(&project.agents_root)),
    ))
}

/// RFC-4180-style escaping: quote when the value contains a comma, quote,
/// or newline; double embedded quotes.
fn csv_field(value: &str) -> String {
    if value.contains(',') || value.contains('"') || value.contains('\n') {
        format!("\"{}\"", value.replace('"', "\"\""))
    } else {
        value.to_string()
    }
}

/// Slot id → (stage label, agent name) from the project's own
/// `pipeline.json` — a slot no longer declared there falls back to its raw
/// id rather than being dropped from the export.
fn slot_lookup(def: &PipelineDef, slot_id: &str) -> (String, String) {
    for stage in &def.stages {
        if let Some(agent) = stage.agents.iter().find(|a| a.id == slot_id) {
            return (stage.label.clone(), agent.agent_name.clone());
        }
    }
    (String::new(), slot_id.to_string())
}

pub(crate) fn build_csv(records: &[RunHistoryRecord], def: &PipelineDef) -> String {
    let mut out = String::from(
        "feature,stage,slot,agent,model,outcome,cost_usd,started_at,ended_at,attempt\n",
    );
    for r in records {
        let (stage, agent) = slot_lookup(def, &r.slot);
        let outcome = serde_json::to_value(r.outcome)
            .ok()
            .and_then(|v| v.as_str().map(str::to_owned))
            .unwrap_or_default();
        let cost = r
            .cost_usd
            .map(|c| format!("{c}"))
            // AC-E6-13 — missing stays EMPTY in the export, never 0.
            .unwrap_or_default();
        out.push_str(&format!(
            "{},{},{},{},{},{},{},{},{},{}\n",
            csv_field(&r.feature),
            csv_field(&stage),
            csv_field(&r.slot),
            csv_field(&agent),
            csv_field(r.model.as_deref().unwrap_or("")),
            csv_field(&outcome),
            cost,
            csv_field(&r.started_at),
            csv_field(&r.ended_at),
            r.attempt,
        ));
    }
    out
}

/// AC-E6-15/16 — `path` comes from the OS save dialog the user just picked
/// (user-directed write, like any Save As). Empty history → error, never an
/// empty file.
#[tauri::command]
pub fn export_cost_csv(state: State<AppState>, path: String) -> AppResult<()> {
    let project = current_project(&state)?;
    let agents_root = Path::new(&project.agents_root);

    let records = run_history::list_records(&orchestrator_dir::run_history_dir(agents_root));
    if records.is_empty() {
        return Err(AppError::Invalid {
            message: "Chưa có lượt chạy nào để xuất — không tạo file rỗng".to_string(),
        });
    }

    let def = crate::commands::pipeline::read_or_init_pipeline_def(agents_root)?;
    let csv = build_csv(&records, &def);
    crate::store::atomic_write::write_text_atomic(Path::new(&path), &csv)
}

/// AC-E6-28 — deletes every `log.jsonl` under `agent-runs/`; returns how
/// many were removed. Never touches `run-history/`, so aggregated cost is
/// unaffected by design (separate directories).
#[tauri::command]
pub fn clear_run_logs(state: State<AppState>) -> AppResult<u32> {
    let project = current_project(&state)?;
    let agent_runs = orchestrator_dir::agent_runs_dir(Path::new(&project.agents_root));

    let mut removed = 0u32;
    for feature_entry in std::fs::read_dir(&agent_runs)
        .into_iter()
        .flatten()
        .flatten()
    {
        for slot_entry in std::fs::read_dir(feature_entry.path())
            .into_iter()
            .flatten()
            .flatten()
        {
            let log_path = slot_entry.path().join("log.jsonl");
            if log_path.is_file() && std::fs::remove_file(&log_path).is_ok() {
                removed += 1;
            }
        }
    }
    Ok(removed)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::run_summary::RunOutcome;

    fn record(feature: &str, slot: &str, cost: Option<f64>) -> RunHistoryRecord {
        RunHistoryRecord {
            feature: feature.to_string(),
            slot: slot.to_string(),
            model: Some("claude-haiku-4-5".to_string()),
            outcome: RunOutcome::Done,
            cost_usd: cost,
            started_at: "t0".to_string(),
            ended_at: "t1".to_string(),
            attempt: 1,
        }
    }

    #[test]
    fn csv_has_header_stage_mapping_and_empty_cost_for_missing() {
        let def = PipelineDef::default();
        let csv = build_csv(
            &[
                record("feat-a", "ba", Some(0.05)),
                record("feat-a", "qc-automation", None),
            ],
            &def,
        );
        let lines: Vec<&str> = csv.lines().collect();
        assert_eq!(lines.len(), 3);
        assert!(lines[0].starts_with("feature,stage,slot,agent,model,outcome,cost_usd"));
        assert!(lines[1].contains("ba-agent"));
        assert!(lines[1].contains("0.05"));
        // AC-E6-13 — missing cost is an EMPTY field (",," around it), not 0.
        assert!(lines[2].contains("qc-automation-agent"));
        assert!(lines[2].contains(",done,,"));
    }

    #[test]
    fn csv_escapes_commas_and_quotes() {
        assert_eq!(csv_field("plain"), "plain");
        assert_eq!(csv_field("a,b"), "\"a,b\"");
        assert_eq!(csv_field("say \"hi\""), "\"say \"\"hi\"\"\"");
    }

    #[test]
    fn unknown_slot_falls_back_to_raw_id() {
        let def = PipelineDef::default();
        let (stage, agent) = slot_lookup(&def, "mystery-slot");
        assert_eq!(stage, "");
        assert_eq!(agent, "mystery-slot");
    }
}
