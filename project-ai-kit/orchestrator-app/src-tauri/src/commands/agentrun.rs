use std::path::{Path, PathBuf};

use tauri::{AppHandle, Emitter, Manager, State};

use crate::agentrun::process_registry::RunKey;
use crate::agentrun::readiness::{
    self, resolve_repo_readiness, slot_repo_role, RepoReadiness, SlotReadiness,
};
use crate::agentrun::run_log::{self, RunContext};
use crate::agentrun::runner;
use crate::agentrun::spawn::{self, SpawnParams};
use crate::agentrun::stream_parser::StreamEvent;
use crate::agents_reader;
use crate::app_state::AppState;
use crate::auth;
use crate::domain::config_file::{self, AgentConfig, ProjectConfig};
use crate::domain::contract_lock::{ContractLockRecord, ContractLockStatus, LockedFile};
use crate::domain::gate_state::{GateState, GateStatus};
use crate::domain::pipeline_def::{gate, slot, AgentSlot};
use crate::domain::project::{EcosystemRepo, ProjectInitStatus, ProjectPaths};
use crate::domain::run_summary::{RunOutcome, RunSummary};
use crate::domain::state_file::StateFile;
use crate::error::{AppError, AppResult};
use crate::fswatch::watcher::recompute_and_emit;
use crate::inference::{api_definition, contract_lock_rules, stage_rules};
use crate::pipeline_state::compute_and_persist;
use crate::store::atomic_write::write_json_atomic;
use crate::store::contract_lock as contract_lock_store;
use crate::store::orchestrator_dir;

pub const EVENT_RUN_FINISHED: &str = "agentrun://run-finished";

#[derive(Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
struct RunFinishedPayload {
    feature: String,
    slot: String,
    summary: RunSummary,
}

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

/// Reserves `(feature, slot)` in `pending_spawns` for the run's whole
/// duration and returns the `spawn_admission` epoch to capture *now*, in
/// the synchronous command handler — before this run's background thread
/// starts any pre-spawn I/O — and pass through to `run_to_completion`
/// unchanged (see that function's `spawn_epoch` doc comment for why it must
/// not be re-read later).
///
/// `HashSet::insert`'s return value makes the "already reserved?" check and
/// the reservation itself one atomic step under `pending_spawns`'s lock —
/// this is the double-click guard `PendingSpawnGuard`'s doc comment already
/// described (a second Run click while pre-spawn work is still in flight
/// must not start a second process for the same slot); nothing previously
/// called `.insert()`, so that guard was dead code until now.
fn reserve_spawn(state: &State<AppState>, key: RunKey) -> AppResult<u64> {
    if !state.pending_spawns.lock().unwrap().insert(key) {
        return Err(AppError::Invalid {
            message: "Slot này đang chạy hoặc vừa được yêu cầu chạy".to_string(),
        });
    }
    Ok(*state.spawn_admission.lock().unwrap())
}

pub(crate) fn ensure_project_ready(agents_root: &Path) -> AppResult<()> {
    let (status, reasons) = agents_reader::read_init_status(agents_root);
    if status == ProjectInitStatus::Ready {
        return Ok(());
    }

    let detail = if reasons.is_empty() {
        "chưa hoàn tất init kit".to_string()
    } else {
        reasons.join(", ")
    };
    Err(AppError::Invalid {
        message: format!(
            "Project chưa sẵn sàng chạy agent ({detail}). Chạy /init-kit trong Claude Code tại agentsRoot rồi kiểm tra lại."
        ),
    })
}

/// Falls back to the kit's own defaults (`config_file::default_model_for`/
/// `default_permission_for`) when `config.json` is missing, corrupt, or
/// simply doesn't have an entry yet for this agent — a config problem must
/// never be the reason a run can't start.
fn load_agent_config(agents_root: &Path, agent_name: &str) -> AgentConfig {
    let path = orchestrator_dir::config_json_path(agents_root);
    let from_disk = std::fs::read_to_string(&path)
        .ok()
        .and_then(|raw| serde_json::from_str::<ProjectConfig>(&raw).ok())
        .and_then(|cfg| cfg.agents.get(agent_name).cloned());

    from_disk.unwrap_or_else(|| AgentConfig {
        model: config_file::default_model_for(agent_name),
        max_turns: config_file::DEFAULT_MAX_TURNS,
        permission: config_file::default_permission_for(agent_name),
        stale: false,
        newly_discovered: false,
        timeout_minutes: config_file::DEFAULT_TIMEOUT_MINUTES,
    })
}

/// Whether a slot is ready to spawn, given the project's current Ecosystem —
/// AC-E2-33's config half: a Figma server auto-detected in the project's
/// own files (name/command/url containing "figma" — see
/// `store::mcp_config`, which walks up from `agentsRoot`), or an explicit
/// `ProjectConfig.figma_mcp_server` choice that still exists. Read fresh
/// per spawn, same as everything else. Deterministic and unit-tested.
fn figma_in_project_config(agents_root: &Path) -> bool {
    let servers = crate::store::mcp_config::read_mcp_servers(agents_root);
    if servers.iter().any(|s| s.figma_candidate) {
        return true;
    }
    let chosen = std::fs::read_to_string(orchestrator_dir::config_json_path(agents_root))
        .ok()
        .and_then(|raw| serde_json::from_str::<ProjectConfig>(&raw).ok())
        .and_then(|cfg| cfg.figma_mcp_server);
    match chosen {
        Some(name) => servers.iter().any(|s| s.name == name),
        None => false,
    }
}

fn figma_mcp_available(agents_root: &Path) -> bool {
    if figma_in_project_config(agents_root) {
        return true;
    }

    // Config files aren't the whole picture: a Figma server can come from
    // Claude's user-level configuration (the `claude.ai Figma` connector
    // lives in no project file at all), and the agent we are about to spawn
    // WOULD have it. Asking the CLI costs several seconds, so it is the
    // last resort — reached only when we would otherwise block the run
    // outright, never on the happy path.
    //
    // Not unit-tested on purpose: the answer depends on the machine's own
    // Claude installation. `figma_in_project_config` above carries the
    // deterministic half.
    crate::store::mcp_status::fetch_mcp_status(agents_root)
        .map(|entries| {
            entries.iter().any(|entry| {
                entry.status != crate::store::mcp_status::McpConnectionStatus::Failed
                    && format!("{} {}", entry.name, entry.detail)
                        .to_lowercase()
                        .contains("figma")
            })
        })
        .unwrap_or(false)
}

/// The one place the "app couldn't read your Vai trò cell" wording lives on
/// the Rust side, so the pre-spawn guard and `run_slot` can't drift apart.
/// Quotes each offending row back verbatim — the fix is a one-line edit in
/// `AGENTS.md`, but only if the user is told which line.
fn unreadable_role_message(role: &str, entries: &[readiness::UnreadableRole]) -> String {
    let listed = entries
        .iter()
        .map(|entry| format!("\"{}\" (vai trò: \"{}\")", entry.repo_name, entry.declared_role))
        .collect::<Vec<_>>()
        .join(", ");
    format!(
        "AGENTS.md không khai repo nào vai trò \"{role}\" đọc được. Ô \"Vai trò\" của {listed}          không đọc ra được backend/frontend/mobile — sửa ô đó thành đúng một từ trong bảng Ecosystem."
    )
}

/// AC-E4-23 — reads the real lock-record directory directly (same
/// principle as `pipeline_state::compute_and_persist`'s own contract-lock
/// read: never trust a cache, `read_latest_lock` IS the source of truth),
/// rather than calling the full `compute_and_persist` just for this one
/// boolean.
fn contract_is_violated(
    agents_root: &Path,
    feature_dir: &Path,
    feature: &str,
    ecosystem: &[EcosystemRepo],
) -> bool {
    let dir = orchestrator_dir::contract_lock_dir(agents_root, feature);
    let previous_lock = crate::store::contract_lock::read_latest_lock(&dir);
    let skip = crate::store::contract_lock::read_skip(&dir);
    let state = contract_lock_rules::infer_contract_lock_state(
        feature_dir,
        ecosystem,
        previous_lock,
        skip,
    );
    state.status == crate::domain::contract_lock::ContractLockStatus::Violated
}

/// Persists a `RunSummary` for a slot that was never actually spawned
/// (AC-E2-11/12) and notifies the Board exactly like a real run's
/// completion would — same `EVENT_RUN_FINISHED` emission, same
/// `recompute_and_emit` call, so `blocked`/`skipped` shows up immediately
/// without the frontend needing a separate code path.
fn record_pre_spawn_outcome(
    app: &AppHandle,
    agents_root: &Path,
    feature: &str,
    slot_id: &str,
    outcome: RunOutcome,
    message: String,
) {
    let now = chrono::Utc::now().to_rfc3339();
    let attempt = run_log::next_attempt(agents_root, feature, slot_id);
    let summary = RunSummary {
        outcome,
        session_id: String::new(),
        cost_usd: 0.0,
        started_at: now.clone(),
        ended_at: now,
        last_message: Some(message),
        attempt,
        // Nothing was ever spawned — there is no prompt to replay.
        prompt: None,
    };
    persist_and_notify(app, agents_root, feature, slot_id, summary);
}

/// Ghi `RunSummary`, ghi run-history, rồi báo cho Board.
///
/// Emit nằm NGOÀI điều kiện ghi file thành công: không ghi được summary
/// thì càng phải báo UI, vì im lặng ở đây nghĩa là console run agent kẹt ở
/// trạng thái "đang chạy" vĩnh viễn — đúng lỗi vừa sửa.
fn persist_and_notify(
    app: &AppHandle,
    agents_root: &Path,
    feature: &str,
    slot_id: &str,
    summary: RunSummary,
) {
    let _ = run_log::write_run_summary(agents_root, feature, slot_id, &summary);
    // AC-E6-12..18 — blocked/skipped rows belong in run history too
    // (no model, no cost — nothing ever ran). Best-effort.
    let _ = crate::store::run_history::write_record(
        &orchestrator_dir::run_history_dir(agents_root),
        &crate::domain::run_history::RunHistoryRecord {
            feature: feature.to_string(),
            slot: slot_id.to_string(),
            model: None,
            outcome: summary.outcome,
            cost_usd: None,
            started_at: summary.started_at.clone(),
            ended_at: summary.ended_at.clone(),
            attempt: summary.attempt,
        },
    );
    let _ = app.emit(
        EVENT_RUN_FINISHED,
        RunFinishedPayload {
            feature: feature.to_string(),
            slot: slot_id.to_string(),
            summary,
        },
    );
}

/// Một run đã spawn nhưng không sinh nổi `RunSummary` — vẫn phải báo kết
/// thúc, nếu không console treo mãi. Marker bị xoá để lần khởi động sau
/// không gọi nhầm run này là `interrupted`.
fn record_post_spawn_failure(
    app: &AppHandle,
    agents_root: &Path,
    feature: &str,
    slot_id: &str,
    marker_path: &Path,
    started_at: String,
    message: String,
) {
    let _ = std::fs::remove_file(marker_path);
    persist_and_notify(
        app,
        agents_root,
        feature,
        slot_id,
        RunSummary {
            outcome: RunOutcome::Failed,
            session_id: String::new(),
            cost_usd: 0.0,
            started_at,
            ended_at: chrono::Utc::now().to_rfc3339(),
            last_message: Some(message),
            attempt: run_log::next_attempt(agents_root, feature, slot_id),
            prompt: None,
        },
    );
}

/// Looks up the real `agent_name` for `slot` from `pipeline.json` (falling
/// back to the `<slot>-agent` naming convention if the slot isn't declared
/// there) — most slots follow that convention (`ba` -> `ba-agent`), but
/// `qc-design` maps to `qc-agent`, not `qc-design-agent`, so a fixed format
/// string is wrong for it. Reading the real `PipelineDef` is the only way
/// to get this right for every slot without hardcoding a second copy of
/// the slot->agent-name table here.
fn resolve_agent_name(agents_root: &Path, slot: &str) -> String {
    crate::commands::pipeline::read_or_init_pipeline_def(agents_root)
        .ok()
        .and_then(|def| {
            def.stages
                .into_iter()
                .flat_map(|stage| stage.agents)
                .find(|agent_slot| agent_slot.id == slot)
                .map(|agent_slot| agent_slot.agent_name)
        })
        .unwrap_or_else(|| format!("{slot}-agent"))
}

/// Runs one agent invocation to completion — spawn, stream, classify,
/// persist, and notify the Board. Always called from a background OS
/// thread (see `start_run`/`send_clarification_answer` below) so the Tauri
/// IPC call that triggers it returns immediately; a run can take minutes.
/// Removes this run's `pending_spawns` reservation on every exit path of
/// `run_to_completion` — the reservation must live for the run's whole
/// duration so a second Run click can't start the same slot during the gap
/// before the child process lands in `ProcessRegistry`. Harmless no-op for
/// runs that were never reserved.
struct PendingSpawnGuard {
    app: AppHandle,
    key: RunKey,
}

impl Drop for PendingSpawnGuard {
    fn drop(&mut self) {
        self.app
            .state::<AppState>()
            .pending_spawns
            .lock()
            .unwrap()
            .remove(&self.key);
    }
}

#[allow(clippy::too_many_arguments)]
fn run_to_completion(
    app: AppHandle,
    agents_root: PathBuf,
    docs_root: PathBuf,
    feature: String,
    slot: String,
    prompt: String,
    resume_session_id: Option<String>,
    // Captured synchronously by the caller (before this thread started, and
    // before any pre-spawn I/O) — must NOT be re-read from `AppState` in
    // here, or a close-then-reopen-a-different-project sequence in between
    // would make this run see the new project's epoch and wrongly proceed.
    spawn_epoch: u64,
) {
    let _pending_guard = PendingSpawnGuard {
        app: app.clone(),
        key: RunKey {
            feature: feature.clone(),
            slot: slot.clone(),
        },
    };
    if let Err(err) = ensure_project_ready(&agents_root) {
        record_pre_spawn_outcome(
            &app,
            &agents_root,
            &feature,
            &slot,
            RunOutcome::Blocked,
            err.to_string(),
        );
        recompute_and_emit(&app, &agents_root, &docs_root, &feature);
        return;
    }
    let agent_name = resolve_agent_name(&agents_root, &slot);
    let config = load_agent_config(&agents_root, &agent_name);
    let resolved_auth = match auth::resolve_for_spawn(&agents_root) {
        Ok(auth) => auth,
        Err(err) => {
            record_pre_spawn_outcome(
                &app,
                &agents_root,
                &feature,
                &slot,
                RunOutcome::Failed,
                err.to_string(),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            return;
        }
    };
    let feature_dir = docs_root.join("features").join(&feature);
    let runs_dir = orchestrator_dir::runs_dir(&agents_root);

    // AC-E2-11/12 — resolve before ever spawning; never for a slot that
    // doesn't target a specific repo (MVP2 only ever spawns `ba`, which
    // doesn't, so this is currently a no-op in practice — but must already
    // be correct for whichever future MVP starts backend/frontend/mobile).
    let ecosystem = app.state::<AppState>().ecosystem.lock().unwrap().clone();
    match resolve_repo_readiness(&ecosystem, &slot) {
        RepoReadiness::RepoNotCloned {
            name: repo_name, ..
        } => {
            record_pre_spawn_outcome(
                &app,
                &agents_root,
                &feature,
                &slot,
                RunOutcome::Blocked,
                format!("Repo \"{repo_name}\" chưa được clone — không thể spawn agent nhắm vào repo này."),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            return;
        }
        RepoReadiness::RoleNotInEcosystem => {
            record_pre_spawn_outcome(
                &app,
                &agents_root,
                &feature,
                &slot,
                RunOutcome::Skipped,
                format!(
                    "Project không có repo vai trò \"{}\" — bỏ qua agent này (không áp dụng).",
                    slot_repo_role(&slot).unwrap_or(&slot)
                ),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            return;
        }
        RepoReadiness::RoleUnreadable { entries } => {
            record_pre_spawn_outcome(
                &app,
                &agents_root,
                &feature,
                &slot,
                RunOutcome::Blocked,
                unreadable_role_message(slot_repo_role(&slot).unwrap_or(&slot), &entries),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            return;
        }
        RepoReadiness::Ready => {}
    }

    // AC-E2-33 — design-analyst needs the project's own Figma MCP; without
    // one it blocks with a named reason instead of spawning an agent whose
    // every tool call would fail.
    if slot == slot::DESIGN_ANALYST && !figma_mcp_available(&agents_root) {
        record_pre_spawn_outcome(
            &app,
            &agents_root,
            &feature,
            &slot,
            RunOutcome::Blocked,
            "Không tìm thấy MCP server phục vụ Figma trong cấu hình project — khai báo trong .mcp.json/.claude/settings.json (xem Settings → MCP) rồi thử lại.".to_string(),
        );
        recompute_and_emit(&app, &agents_root, &docs_root, &feature);
        return;
    }

    // AC-E4-23 — a slot that targets a repo (backend/frontend/mobile,
    // stage ⑤+) never spawns while the contract is `Violated`. An
    // already-running process for this `(feature, slot)` is untouched (no
    // kill) — this check only ever runs before a NEW spawn.
    if slot_repo_role(&slot).is_some()
        && contract_is_violated(&agents_root, &feature_dir, &feature, &ecosystem)
    {
        record_pre_spawn_outcome(
            &app,
            &agents_root,
            &feature,
            &slot,
            RunOutcome::Blocked,
            "Contract đang vi phạm — cần Re-lock trước khi tiếp tục.".to_string(),
        );
        recompute_and_emit(&app, &agents_root, &docs_root, &feature);
        return;
    }

    let started_at = chrono::Utc::now().to_rfc3339();
    let key = RunKey {
        feature: feature.clone(),
        slot: slot.clone(),
    };

    let (tx, rx) = std::sync::mpsc::channel();
    let forwarder = runner::spawn_event_forwarder(app.clone(), feature.clone(), slot.clone(), rx);

    // AC-E2-23's Import Input copies the user's chosen folder into
    // `.orchestrator/inputs/<run-id>/` under `agentsRoot` — NOT under
    // `feature_dir` (cwd, under `docsRoot`; see A1: the roots can be three
    // unrelated directories). Without granting this directory too, `ba-agent`
    // (or any future slot that reads user-supplied files this way) hits
    // Claude Code's own path-based permission check reading an absolute path
    // outside both `cwd` and every `--add-dir` — which, with no TTY to answer
    // it, is the "agent asks for permission to read the file" the user hit.
    // Best-effort create: `inputs_dir` is deliberately NOT part of
    // `ensure_skeleton` (only comes to exist once something is imported), so
    // a project that has never imported anything yet would otherwise hand
    // the CLI a `--add-dir` for a directory that isn't there.
    let _ = std::fs::create_dir_all(orchestrator_dir::inputs_dir(&agents_root));
    let extra_add_dirs = vec![orchestrator_dir::inputs_dir(&agents_root)];

    // The kit's hooks (H01/H03/H05) live in `<agentsRoot>/.claude/settings.json`,
    // but cwd below is the feature dir under `docsRoot` — a directory that need
    // not sit under `agentsRoot` at all (A1). Name the file so the hooks apply
    // regardless of how the three roots are arranged. Absent file: skip, a
    // project that hasn't scaffolded the kit still has to run.
    let settings_path = agents_root.join(".claude").join("settings.json");
    let settings_file = settings_path.is_file().then_some(settings_path.as_path());

    let params = SpawnParams {
        agent_name: &agent_name,
        prompt: &prompt,
        cwd: &feature_dir,
        config: &config,
        resume_session_id: resume_session_id.as_deref(),
        settings_file,
        add_dirs: &extra_add_dirs,
        auth: match (resolved_auth.mode, resolved_auth.api_key.as_deref()) {
            (crate::domain::config_file::ClaudeAuthMode::CliDefault, _) => {
                spawn::SpawnAuth::CliDefault
            }
            (crate::domain::config_file::ClaudeAuthMode::Subscription, _) => {
                spawn::SpawnAuth::Subscription
            }
            (crate::domain::config_file::ClaudeAuthMode::Console, _) => spawn::SpawnAuth::Console,
            (crate::domain::config_file::ClaudeAuthMode::ApiKey, Some(key)) => {
                spawn::SpawnAuth::ApiKey(key)
            }
            (crate::domain::config_file::ClaudeAuthMode::ApiKey, None) => {
                // `resolve_for_spawn` rejects this state; keep a safe
                // fallback for exhaustiveness if the resolver changes.
                spawn::SpawnAuth::CliDefault
            }
        },
    };

    let registry = &app.state::<AppState>().agent_runs;
    // AC-E6-21 — per-agent timeout from config (default 30 min), re-read
    // per spawn so Settings changes apply to the next run (AC-E1-24).
    let timeout = std::time::Duration::from_secs(u64::from(config.timeout_minutes) * 60);

    // AC-E6-04/07/10 — durability marker on disk BEFORE the spawn: if the
    // app dies anywhere past this point, the startup scan finds the marker
    // and turns this run into `interrupted` instead of it silently
    // vanishing. Same attempt number `finalize_run` will compute (both
    // read the same untouched `last-run.json`). Removed by `finalize_run`.
    let marker_path =
        crate::store::orchestrator_dir::agent_run_marker_path(&agents_root, &feature, &slot);
    let marker = crate::domain::running_marker::RunningMarker {
        pid: None,
        started_at: started_at.clone(),
        attempt: run_log::next_attempt(&agents_root, &feature, &slot),
        prompt: Some(prompt.clone()),
    };
    if let Some(parent) = marker_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let _ = crate::store::atomic_write::write_json_atomic(&marker_path, &marker);
    // The marker is what makes the node render as "đang chạy"
    // (`apply_agent_run_metadata`), so the Board has to be told about it
    // now — otherwise the node sits on "Chưa bắt đầu" for the whole run and
    // only updates once it finishes.
    recompute_and_emit(&app, &agents_root, &docs_root, &feature);
    let marker_path_for_cleanup = marker_path.clone();
    let durability = runner::RunDurability {
        marker_path,
        marker,
        log_path: crate::store::orchestrator_dir::agent_run_log_path(&agents_root, &feature, &slot),
    };

    let run_result = runner::run_and_stream(
        registry,
        key,
        &params,
        tx,
        timeout,
        Some(durability),
        &app.state::<AppState>().spawn_admission,
        spawn_epoch,
    );
    // The forwarder exits on its own once `tx` (moved into `run_and_stream`)
    // is dropped at the end of that call — join to make sure every event
    // has actually reached the frontend before this thread moves on.
    //
    // CHỈ join khi stdout đã đóng sạch: nếu hết hạn ân hạn, thread đọc bị
    // bỏ mặc vẫn đang giữ `tx`, nên join sẽ treo đúng như lỗi vừa sửa
    // trong `runner`.
    if matches!(
        &run_result,
        Ok(runner::SpawnOutcome::Ran(result)) if result.stdout_drained
    ) {
        let _ = forwarder.join();
    }

    let ended_at = chrono::Utc::now().to_rfc3339();

    // A spawn failure here (e.g. the CLI vanished mid-session) has no
    // `RunResult` to classify — nothing to persist, nothing to notify
    // beyond what already happened (no run was ever registered as active).
    // The durability marker must not linger though, or the next startup
    // would call this never-started run `interrupted`.
    let result = match run_result {
        Ok(runner::SpawnOutcome::Ran(result)) => result,
        // The project closed while this run was still doing pre-spawn I/O
        // (`AppState::close` bumped `spawn_admission` before this thread's
        // `run_and_stream` call registered its child) — `run_and_stream`
        // already killed the child before returning this variant.
        Ok(runner::SpawnOutcome::AbortedProjectClosed) => {
            record_post_spawn_failure(
                &app,
                &agents_root,
                &feature,
                &slot,
                &marker_path_for_cleanup,
                started_at,
                "Project đã đóng khi agent chuẩn bị chạy — huỷ.".to_string(),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            return;
        }
        Err(err) => {
            record_post_spawn_failure(
                &app,
                &agents_root,
                &feature,
                &slot,
                &marker_path_for_cleanup,
                started_at,
                format!("Không chạy được tiến trình agent: {err}"),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            return;
        }
    };

    // AC-E4-30..32 — Memory Update Gate (soft): dev slots only; produces
    // at most an advisory appended to the summary, never blocks anything.
    let memory_warning = slot_repo_role(&slot).and_then(|role| {
        crate::inference::memory_gate::memory_update_warning(
            &docs_root,
            &ecosystem,
            role,
            &started_at,
        )
    });
    // AC-E6-06 — a failed `--resume` must say so: the user chose Resume
    // and needs to know re-running from scratch is the way out, rather
    // than the app silently having started over.
    let resume_failure_note = (resume_session_id.is_some()
        && (result.timed_out || result.exit_code != Some(0)))
    .then(|| {
        "Lần chạy này resume phiên cũ — nếu lỗi do phiên hết hạn hoặc không tồn tại, hãy chạy lại từ đầu (Re-run)."
            .to_string()
    });
    let extra_warning = match (memory_warning, resume_failure_note) {
        (Some(a), Some(b)) => Some(format!("{a}\n{b}")),
        (a, b) => a.or(b),
    };

    let ctx = RunContext {
        agents_root: &agents_root,
        feature: &feature,
        slot: &slot,
        feature_dir: &feature_dir,
        runs_dir: &runs_dir,
        permission: config.permission,
    };
    let summary = match run_log::finalize_run(
        &ctx,
        &result,
        started_at.clone(),
        ended_at,
        &prompt,
        extra_warning,
    ) {
        Ok(summary) => summary,
        Err(err) => {
            record_post_spawn_failure(
                &app,
                &agents_root,
                &feature,
                &slot,
                &marker_path_for_cleanup,
                started_at,
                format!("Agent đã chạy xong nhưng không ghi lại được kết quả: {err}"),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            return;
        }
    };

    let outcome = summary.outcome;
    let _ = app.emit(
        EVENT_RUN_FINISHED,
        RunFinishedPayload {
            feature: feature.clone(),
            slot: slot.clone(),
            summary,
        },
    );

    // `apply_agent_run_metadata` (pipeline_state) reads the marker
    // `finalize_run` just wrote, from `.orchestrator/agent-runs/` — a
    // directory the file watcher (T1.3) does not watch. For a `Done`
    // outcome the watcher would eventually notice the new artifact on its
    // own, but `waiting-input`/`failed`/`timeout` touch nothing inside
    // `feature_dir` at all, so `EVENT_STATE_CHANGED` must be emitted
    // explicitly here rather than relying on the watcher.
    recompute_and_emit(&app, &agents_root, &docs_root, &feature);

    // B22 — nothing is spawned from here any more. The pipeline advances
    // only when the user clicks Run on the next node (`run_slot`), which
    // re-checks `compute_slot_readiness` against the state this run just
    // wrote. `outcome` still drives the emitted event and the node status.
    let _ = outcome;
}

/// Current slot statuses plus the gate ids the user has already cleared —
/// the two inputs `readiness::compute_slot_readiness` needs that live in
/// `FeatureState` rather than in `pipeline.json`.
#[allow(clippy::type_complexity)]
fn statuses_and_passed_gates(
    feature_state: &crate::domain::state_file::FeatureState,
) -> (
    std::collections::BTreeMap<String, crate::domain::node_status::NodeStatus>,
    Vec<String>,
    Vec<String>,
) {
    let statuses = feature_state
        .nodes
        .iter()
        .map(|(id, node)| (id.clone(), node.status))
        .collect();

    let mut passed_gates: Vec<String> = feature_state
        .gates
        .iter()
        .filter(|(_, gate_state)| gate_state.status == GateStatus::Approved)
        .map(|(id, _)| id.clone())
        .collect();
    // The Contract Lock gate isn't in `gates` — it has its own richer state.
    let contract_lock_status = feature_state.contract_lock.as_ref().map(|lock| lock.status);
    if contract_lock_status == Some(ContractLockStatus::Locked) {
        passed_gates.push(gate::CONTRACT_LOCK.to_string());
    }

    // AC-E4-11 — feature chỉ chạm 1 repo KHÔNG CẦN Contract Lock, nhưng
    // stage ⑤ lại `depends_on` chính gate này. Trước đây chỉ `Locked` mới
    // được tính, nên "không áp dụng" hoá ra chặn vĩnh viễn — không có nút
    // Lock nào để bấm ở trạng thái đó, tức backend/frontend/mobile của mọi
    // project single-repo không bao giờ chạy được.
    //
    // Xếp vào `skipped_gates` chứ KHÔNG phải `passed_gates`: gate này không
    // xác nhận điều gì, nên nó trong suốt chứ không mở khoá — readiness phải
    // nhìn xuyên qua nó tới stage ③.
    let mut skipped_gates = Vec::new();
    if contract_lock_status == Some(ContractLockStatus::NotApplicable) {
        skipped_gates.push(gate::CONTRACT_LOCK.to_string());
    }

    (statuses, passed_gates, skipped_gates)
}

/// The auto-spawn prompt per slot — each points the agent at the exact
/// primary input its OWN kit file's `## Bước 1`/`## Quy trình` declares
/// (verified against `.claude/agents/*.md`, not guessed):
/// `techlead-tasks-agent` self-discovers `DESIGN.md`/tasks from the
/// feature folder; `qa-agent` takes task-file paths; the QC pair
/// and everything else start from `SPEC.md` (same wording
/// `approve_trigger_gate` already uses for stage ②).
///
/// `extra_input` is optional slot-specific text the user typed before
/// clicking Run — today only `design-analyst` reads it (the Figma
/// selection URL), which lets that agent finish in ONE run instead of
/// stopping to ask and needing a second resumed run.
fn build_slot_prompt(slot_id: &str, feature_dir: &Path, extra_input: Option<&str>) -> String {
    let spec_path = feature_dir.join("SPEC.md");
    // AC-E2-39 — stage ③ (techlead-tasks) gets the design analysis in
    // its context when stage ②c actually produced one. Appended, never
    // required — a feature without the design-analyst branch still chains.
    let design_analysis = feature_dir.join("design-analysis.md");
    let design_analysis_note = if design_analysis.is_file() {
        format!(
            "\nTham khảo thêm phân tích design tại: {}",
            design_analysis.display()
        )
    } else {
        String::new()
    };
    match slot_id {
        s if s == slot::TECHLEAD_TASKS => format!(
            "Feature folder tại đường dẫn tuyệt đối sau:\n{}\nĐọc các DESIGN.md trong đó và thực hiện đúng quy trình của bạn.{design_analysis_note}",
            feature_dir.display()
        ),
        s if s == slot::FRONTEND || s == slot::MOBILE || s == slot::QA => {
            let mut task_files = stage_rules::task_files_in_repos(feature_dir);
            task_files.sort();
            if task_files.is_empty() {
                format!(
                    "Feature folder tại đường dẫn tuyệt đối sau:\n{}\nThực hiện đúng quy trình của bạn. (Không tìm thấy task-*.md nào trong repo — có thể Tech Lead Tasks chưa chạy cho feature này.)",
                    feature_dir.display()
                )
            } else {
                let task_paths = task_files
                    .iter()
                    .map(|p| p.display().to_string())
                    .collect::<Vec<_>>()
                    .join("\n");
                format!(
                    "Đọc và thực hiện lần lượt các task thuộc phạm vi của bạn trong danh sách sau, theo đúng quy trình của bạn:\n{task_paths}"
                )
            }
        }
        s if s == slot::DESIGN_ANALYST => {
            let figma_url = extra_input.map(str::trim).filter(|url| !url.is_empty());
            // AC-E2-37a — the agent file makes exporting a mandatory step,
            // but that step was silently skipped often enough to be worth
            // naming in the prompt too, with the absolute target path so
            // there is nothing to infer from cwd.
            let export_note = format!(
                "\n\nExport icon/ảnh đọc được từ Figma vào thư mục: {}\nrồi liệt kê ở mục 6 của design-analysis.md. Không export được thì ghi rõ lý do ở mục 6 — đừng dừng lại để hỏi, đừng chặn nhánh.",
                feature_dir.join("design-resources").display()
            );
            match figma_url {
                Some(url) => format!(
                    "Đọc SPEC.md tại đường dẫn tuyệt đối sau và thực hiện đúng quy trình của bạn:\n{}\n(Feature folder: {})\n\nURL Figma (selection) người dùng đã cung cấp — dùng URL này, KHÔNG hỏi lại:\n{url}{export_note}",
                    spec_path.display(),
                    feature_dir.display()
                ),
                // No URL typed: the agent's own Bước 2 takes over and stops
                // to ask, landing the slot in `waiting-input` as before.
                None => format!(
                    "Đọc SPEC.md tại đường dẫn tuyệt đối sau và thực hiện đúng quy trình của bạn:\n{}\n(Feature folder: {}){export_note}",
                    spec_path.display(),
                    feature_dir.display()
                ),
            }
        }
        _ => format!(
            "Đọc SPEC.md tại đường dẫn tuyệt đối sau và thực hiện đúng quy trình của bạn:\n{}",
            spec_path.display()
        ),
    }
}

/// AC-E2-21..24 entry point once Import Input has copied the source folder
/// — starts a fresh `ba-agent` session. AC-E2-28: checked synchronously so
/// a missing CLI never creates an empty run entry.
#[tauri::command]
pub fn start_run(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
    slot: String,
    prompt: String,
) -> AppResult<()> {
    orchestrator_dir::validate_run_ids(&feature, &slot)?;
    if slot != slot::BA {
        return Err(AppError::Invalid {
            message:
                "start_run chỉ dành cho BA và retry được xác thực; dùng run_slot cho slot khác"
                    .to_string(),
        });
    }
    if !spawn::is_claude_cli_available() {
        return Err(AppError::Invalid {
            message: crate::agentrun::cli_path::not_found_message(),
        });
    }
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(project.agents_root);
    let docs_root = PathBuf::from(project.docs_root);
    ensure_project_ready(&agents_root)?;
    auth::resolve_for_spawn(&agents_root)?;

    let spawn_epoch = reserve_spawn(
        &state,
        RunKey {
            feature: feature.clone(),
            slot: slot.clone(),
        },
    )?;
    std::thread::spawn(move || {
        run_to_completion(
            app,
            agents_root,
            docs_root,
            feature,
            slot,
            prompt,
            None,
            spawn_epoch,
        );
    });
    Ok(())
}

/// B22 — every slot's Run button asks this first, so the UI can enable or
/// disable each one and say exactly what is being waited on.
#[tauri::command]
pub fn get_slot_readiness(
    state: State<AppState>,
    feature: String,
) -> AppResult<std::collections::BTreeMap<String, SlotReadiness>> {
    orchestrator_dir::validate_feature_id(&feature)?;
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let docs_root = PathBuf::from(&project.docs_root);
    auth::resolve_for_spawn(&agents_root)?;
    // Tính lại chứ không đọc cache: đây là câu trả lời cho "nút Run có bật
    // được không", nên nó phải phản ánh đĩa lúc này — repo vừa clone xong
    // phải mở khoá được nút mà không cần mở lại project.
    let ecosystem = crate::commands::project::recompute_ecosystem(&state);

    let (feature_state, _) = compute_and_persist(&agents_root, &docs_root, &feature, &ecosystem)?;
    let (statuses, passed_gates, skipped_gates) = statuses_and_passed_gates(&feature_state);
    let def = crate::commands::pipeline::read_or_init_pipeline_def(&agents_root)?;
    let agents_found = agents_reader::discover_agents(&agents_root).unwrap_or_default();
    let slots_without_work = stage_rules::slots_without_work_in_feature(
        &docs_root.join("features").join(&feature),
        &ecosystem,
    );

    Ok(def
        .stages
        .iter()
        .flat_map(|stage| stage.agents.iter())
        .map(|agent_slot| {
            (
                agent_slot.id.clone(),
                readiness::compute_slot_readiness(
                    &def,
                    &statuses,
                    &passed_gates,
                    &skipped_gates,
                    &agents_found,
                    &ecosystem,
                    &slots_without_work,
                    &agent_slot.id,
                ),
            )
        })
        .collect())
}

/// B22 — the only way a pipeline agent starts now: the user clicks Run.
///
/// The prompt is built HERE, not passed in from the frontend, so the UI
/// never has to know which upstream artifacts a slot consumes — that stays
/// one definition (`build_slot_prompt`, plus the two slots with their own
/// builders). `extra_input` is slot-specific free text; today only
/// `design-analyst` uses it, for the Figma selection URL.
#[tauri::command]
pub fn run_slot(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
    slot: String,
    extra_input: Option<String>,
) -> AppResult<()> {
    orchestrator_dir::validate_run_ids(&feature, &slot)?;
    if !spawn::is_claude_cli_available() {
        return Err(AppError::Invalid {
            message: crate::agentrun::cli_path::not_found_message(),
        });
    }
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let docs_root = PathBuf::from(&project.docs_root);
    ensure_project_ready(&agents_root)?;
    // Cùng lý do như `get_slot_readiness` — và `run_to_completion` đọc cache
    // này lại lần nữa ngay trước khi spawn, nên refresh ở đây cũng làm mới
    // luôn cho lớp phòng thủ đó.
    let ecosystem = crate::commands::project::recompute_ecosystem(&state);

    if state.is_running(&feature, &slot) {
        return Err(AppError::Invalid {
            message: "Slot này đang chạy".to_string(),
        });
    }

    let (feature_state, _) = compute_and_persist(&agents_root, &docs_root, &feature, &ecosystem)?;
    let (statuses, passed_gates, skipped_gates) = statuses_and_passed_gates(&feature_state);
    let def = crate::commands::pipeline::read_or_init_pipeline_def(&agents_root)?;
    let agents_found = agents_reader::discover_agents(&agents_root).unwrap_or_default();
    let slots_without_work = stage_rules::slots_without_work_in_feature(
        &docs_root.join("features").join(&feature),
        &ecosystem,
    );

    match readiness::compute_slot_readiness(
        &def,
        &statuses,
        &passed_gates,
        &skipped_gates,
        &agents_found,
        &ecosystem,
        &slots_without_work,
        &slot,
    ) {
        SlotReadiness::Ready => {}
        SlotReadiness::Waiting { blocked_by } => {
            return Err(AppError::Invalid {
                message: format!("Chưa chạy được — đang chờ: {}", blocked_by.join(", ")),
            })
        }
        SlotReadiness::GateNotPassed { gate_label } => {
            return Err(AppError::Invalid {
                message: format!("Chưa chạy được — cần duyệt gate \"{gate_label}\" trước"),
            })
        }
        // Same handling the old chaining engine gave a missing agent file
        // (AC-E2-40): record it as skipped instead of failing to spawn.
        SlotReadiness::AgentMissing { agent_name } => {
            record_pre_spawn_outcome(
                &app,
                &agents_root,
                &feature,
                &slot,
                RunOutcome::Skipped,
                format!(
                    "Agent \"{agent_name}\" chưa tồn tại trong kit (.claude/agents/{agent_name}.md) — bỏ qua."
                ),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            return Ok(());
        }
        // A wrong `repositoryRoot` looks exactly like a missing clone from
        // here, and it is by far the likelier cause — so name the declared
        // path and point at the setting instead of just "chưa clone".
        SlotReadiness::RepoNotCloned {
            repo_name,
            declared_path,
        } => {
            return Err(AppError::Invalid {
                message: format!(
                    "Chưa chạy được — không tìm thấy repo \"{repo_name}\" (AGENTS.md khai đường dẫn \"{declared_path}\"). Kiểm tra repositoryRoot của project, hoặc clone repo về."
                ),
            })
        }
        // Same handling `run_to_completion` gives `RoleNotInEcosystem`:
        // the slot simply doesn't apply to this project.
        SlotReadiness::RepoRoleMissing { role } => {
            record_pre_spawn_outcome(
                &app,
                &agents_root,
                &feature,
                &slot,
                RunOutcome::Skipped,
                format!("Project không có repo vai trò \"{role}\" — bỏ qua agent này (không áp dụng)."),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            return Ok(());
        }
        // NOT `Skipped` like `RepoRoleMissing`: this isn't "the slot doesn't
        // apply", it's "AGENTS.md has a typo". Blocking with the reason
        // keeps the slot runnable the moment the cell is fixed.
        SlotReadiness::RepoRoleUnreadable { role, entries } => {
            return Err(AppError::Invalid {
                message: format!(
                    "Chưa chạy được — {}",
                    unreadable_role_message(&role, &entries)
                ),
            })
        }
        // Same shape as `RepoRoleMissing`: nothing to run, so record it as
        // skipped rather than spawning an agent with no task file to read.
        // Re-checked here, not trusted from the disabled button alone.
        SlotReadiness::NoWorkInFeature { role } => {
            record_pre_spawn_outcome(
                &app,
                &agents_root,
                &feature,
                &slot,
                RunOutcome::Skipped,
                format!(
                    "Feature này không có task nào cho {role} — bỏ qua agent này (không áp dụng)."
                ),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            return Ok(());
        }
        SlotReadiness::UnknownSlot => {
            return Err(AppError::Invalid {
                message: format!("Slot \"{slot}\" không có trong pipeline"),
            })
        }
    }

    let feature_dir = docs_root.join("features").join(&feature);
    let prompt = if slot == slot::BACKEND {
        // Backend reads the task files the Contract Lock froze, exactly as
        // `lock_contract` used to hand it over.
        let locked_designs = crate::store::contract_lock::read_latest_lock(
            &orchestrator_dir::contract_lock_dir(&agents_root, &feature),
        )
        .map(|record| {
            record
                .files
                .iter()
                .map(|file| PathBuf::from(&file.path))
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();
        build_backend_agent_prompt(&feature_dir, &locked_designs)
    } else {
        build_slot_prompt(&slot, &feature_dir, extra_input.as_deref())
    };

    let spawn_epoch = reserve_spawn(
        &state,
        RunKey {
            feature: feature.clone(),
            slot: slot.clone(),
        },
    )?;
    std::thread::spawn(move || {
        run_to_completion(
            app,
            agents_root,
            docs_root,
            feature,
            slot,
            prompt,
            None,
            spawn_epoch,
        );
    });
    Ok(())
}

/// AC-E2-17 — delivers the user's answer into the SAME session as the run
/// that asked (A5: this means spawning a brand new process with
/// `--resume`, not writing into a still-open stdin).
#[tauri::command]
pub fn send_clarification_answer(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
    slot: String,
    answer: String,
) -> AppResult<()> {
    orchestrator_dir::validate_run_ids(&feature, &slot)?;
    if !spawn::is_claude_cli_available() {
        return Err(AppError::Invalid {
            message: crate::agentrun::cli_path::not_found_message(),
        });
    }
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let docs_root = PathBuf::from(project.docs_root);
    ensure_project_ready(&agents_root)?;
    auth::resolve_for_spawn(&agents_root)?;

    let session_id = run_log::read_run_summary(&agents_root, &feature, &slot)
        .map(|s| s.session_id)
        .filter(|s| !s.is_empty())
        .ok_or_else(|| AppError::Invalid {
            message: "Không tìm thấy session trước đó để trả lời tiếp".to_string(),
        })?;

    let spawn_epoch = reserve_spawn(
        &state,
        RunKey {
            feature: feature.clone(),
            slot: slot.clone(),
        },
    )?;
    std::thread::spawn(move || {
        run_to_completion(
            app,
            agents_root,
            docs_root,
            feature,
            slot,
            answer,
            Some(session_id),
            spawn_epoch,
        );
    });
    Ok(())
}

/// Kills the live process for `(feature, slot)`, if any — `false` (not an
/// error) when nothing is currently running there.
#[tauri::command]
pub fn kill_run(state: State<AppState>, feature: String, slot: String) -> AppResult<bool> {
    orchestrator_dir::validate_run_ids(&feature, &slot)?;
    let key = RunKey { feature, slot };
    state.agent_runs.kill(&key)
}

/// The latest persisted run outcome for `(feature, slot)`, if any — used by
/// the frontend to read `attempt` for the Retry-limit check (AC-E2-13)
/// without duplicating or guessing that count client-side. `None` (not an
/// error) when this slot has never been run.
#[tauri::command]
pub fn get_run_summary(
    state: State<AppState>,
    feature: String,
    slot: String,
) -> AppResult<Option<RunSummary>> {
    orchestrator_dir::validate_run_ids(&feature, &slot)?;
    let project = current_project(&state)?;
    Ok(run_log::read_run_summary(
        Path::new(&project.agents_root),
        &feature,
        &slot,
    ))
}

/// AC-E2-20 — re-hydrates the Log Console from `log.jsonl` on disk, so
/// reopening the app (or just re-navigating to a slot) doesn't lose a
/// finished run's history the way pure React state does. Empty (not an
/// error) when this slot has never been run.
#[tauri::command]
pub fn read_run_log(
    state: State<AppState>,
    feature: String,
    slot: String,
) -> AppResult<Vec<StreamEvent>> {
    orchestrator_dir::validate_run_ids(&feature, &slot)?;
    let project = current_project(&state)?;
    run_log::read_run_log(Path::new(&project.agents_root), &feature, &slot)
}

/// AC-E6-25 — marks a slot `skipped (manual)`. `Skipped` counts as
/// stage-complete, so the slots downstream become Ready and their Run
/// buttons light up (B22 — nothing spawns on its own any more). Refuses
/// while the slot has a live process — Skip is for slots that failed or
/// won't be run, not a Kill substitute.
#[tauri::command]
pub fn skip_run(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
    slot: String,
) -> AppResult<()> {
    orchestrator_dir::validate_run_ids(&feature, &slot)?;
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(project.agents_root);
    let docs_root = PathBuf::from(project.docs_root);

    if state.is_running(&feature, &slot) {
        return Err(AppError::Invalid {
            message:
                "Agent đang chạy — dùng Kill trước nếu muốn dừng, Skip chỉ dành cho slot không chạy"
                    .to_string(),
        });
    }

    record_pre_spawn_outcome(
        &app,
        &agents_root,
        &feature,
        &slot,
        RunOutcome::Skipped,
        "Bỏ qua thủ công — skipped (manual).".to_string(),
    );
    recompute_and_emit(&app, &agents_root, &docs_root, &feature);
    Ok(())
}

/// Force-marks a `backend`/`frontend`/`mobile` slot `done`, overriding
/// whatever its own completion heuristic decided. Those 3 slots are the
/// only ones `classify_outcome` (`agentrun::run_log`) infers from the
/// agent's own last message starting with `✅` — a session that actually
/// finished the work but drifted off that convention on a later resumed
/// turn (a clarification reply, a stray "ok" from the user, ...) stays
/// `waiting-input` forever with no automatic way out. This is that way out.
///
/// Kills any live process for the slot first — unlike `skip_run`, which
/// refuses while one is running, Force Done supersedes it outright; the
/// user is telling the app the work is already done, so a stale process
/// still streaming into this slot must not keep writing over that.
///
/// Refuses for any slot other than backend/frontend/mobile: every other
/// slot's `Done` status comes from `RunOutcome::Done` only when
/// `run_log_is_authoritative` (`pipeline_state::apply_agent_run_metadata`)
/// — for those, file-system inference (does the expected artifact exist?)
/// always wins on the next recompute, so persisting `Done` here would
/// silently do nothing.
#[tauri::command]
pub fn force_done_run(app: AppHandle, state: State<AppState>, feature: String, slot: String) -> AppResult<()> {
    orchestrator_dir::validate_run_ids(&feature, &slot)?;
    if slot_repo_role(&slot).is_none() {
        return Err(AppError::Invalid {
            message: format!(
                "Force Done chỉ áp dụng cho slot backend/frontend/mobile — \"{slot}\" không thuộc nhóm này, trạng thái của nó luôn do artifact trên đĩa quyết định, không thể ghi đè thủ công."
            ),
        });
    }

    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let docs_root = PathBuf::from(project.docs_root);

    state.agent_runs.kill(&RunKey {
        feature: feature.clone(),
        slot: slot.clone(),
    })?;

    let previous = run_log::read_run_summary(&agents_root, &feature, &slot);
    let now = chrono::Utc::now().to_rfc3339();
    let attempt = run_log::next_attempt(&agents_root, &feature, &slot);
    let summary = RunSummary {
        outcome: RunOutcome::Done,
        session_id: previous
            .as_ref()
            .map(|p| p.session_id.clone())
            .unwrap_or_default(),
        cost_usd: previous.as_ref().map(|p| p.cost_usd).unwrap_or(0.0),
        started_at: previous
            .as_ref()
            .map(|p| p.started_at.clone())
            .unwrap_or_else(|| now.clone()),
        ended_at: now,
        last_message: None,
        attempt,
        prompt: None,
    };
    persist_and_notify(&app, &agents_root, &feature, &slot, summary);
    recompute_and_emit(&app, &agents_root, &docs_root, &feature);
    Ok(())
}

/// AC-E6-05 — continues an `interrupted` run in its original CLI session
/// (`--resume <session-id>`, same mechanism as clarification answers).
/// AC-E6-06 — a run whose session id never made it to disk gets a clear
/// error pointing at Re-run instead of silently starting a fresh session.
#[tauri::command]
pub fn resume_run(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
    slot: String,
) -> AppResult<()> {
    orchestrator_dir::validate_run_ids(&feature, &slot)?;
    if !spawn::is_claude_cli_available() {
        return Err(AppError::Invalid {
            message: crate::agentrun::cli_path::not_found_message(),
        });
    }
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let docs_root = PathBuf::from(project.docs_root);
    ensure_project_ready(&agents_root)?;
    auth::resolve_for_spawn(&agents_root)?;

    let summary = run_log::read_run_summary(&agents_root, &feature, &slot).ok_or_else(|| {
        AppError::Invalid {
            message: "Không tìm thấy lượt chạy nào cho slot này".to_string(),
        }
    })?;
    if summary.outcome != RunOutcome::Interrupted {
        return Err(AppError::Invalid {
            message:
                "Slot này không ở trạng thái bị gián đoạn — Resume chỉ dành cho run bị cắt ngang"
                    .to_string(),
        });
    }
    if summary.session_id.is_empty() {
        return Err(AppError::Invalid {
            message: "Không có session id để resume — phiên trước bị cắt trước khi CLI kịp báo session id. Hãy dùng Re-run (chạy lại từ đầu).".to_string(),
        });
    }

    let session_id = summary.session_id;
    let spawn_epoch = reserve_spawn(
        &state,
        RunKey {
            feature: feature.clone(),
            slot: slot.clone(),
        },
    )?;
    std::thread::spawn(move || {
        run_to_completion(
            app,
            agents_root,
            docs_root,
            feature,
            slot,
            "Phiên trước bị gián đoạn giữa chừng. Kiểm tra công việc còn dang dở và hoàn tất nốt theo đúng quy trình của bạn.".to_string(),
            Some(session_id),
            spawn_epoch,
        );
    });
    Ok(())
}

/// AC-E6-10 — re-scans `running.json` markers and returns only the ones
/// whose process is still alive. Dead ones are marked `interrupted` as a
/// side effect (same scan `open_project` runs — idempotent), so the Board
/// banner and node states can never disagree about the same marker.
#[tauri::command]
pub fn list_orphans(
    app: AppHandle,
    state: State<AppState>,
) -> AppResult<Vec<crate::agentrun::recovery::OrphanInfo>> {
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let docs_root = PathBuf::from(&project.docs_root);

    let (interrupted, orphans) = crate::agentrun::recovery::scan_stale_runs(
        &agents_root,
        crate::agentrun::recovery::pid_is_live_agent,
        // The Board calls this on every mount, including while our own
        // agents are running — those markers are ours, not orphans.
        |feature, slot| state.is_running(feature, slot),
    );
    for slot in &interrupted {
        recompute_and_emit(&app, &agents_root, &docs_root, &slot.feature);
    }
    Ok(orphans)
}

/// AC-E6-10 — the user's decision about one orphan: `"kill"` terminates it
/// now; `"attach"` watches the PID until the process exits on its own,
/// then rebuilds state from whatever artifacts it wrote. Either way the
/// slot ends `interrupted` (with a message saying which path was taken)
/// and the marker is gone.
#[tauri::command]
pub fn resolve_orphan(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
    slot: String,
    action: String,
) -> AppResult<()> {
    orchestrator_dir::validate_run_ids(&feature, &slot)?;
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(&project.agents_root);
    let docs_root = PathBuf::from(&project.docs_root);

    let marker_path =
        crate::store::orchestrator_dir::agent_run_marker_path(&agents_root, &feature, &slot);
    let marker: crate::domain::running_marker::RunningMarker =
        std::fs::read_to_string(&marker_path)
            .ok()
            .and_then(|raw| serde_json::from_str(&raw).ok())
            .ok_or_else(|| AppError::Invalid {
                message: "Không còn marker cho orphan này — có thể đã được xử lý rồi".to_string(),
            })?;
    let Some(pid) = marker.pid else {
        return Err(AppError::Invalid {
            message: "Marker không có PID — orphan này sẽ được dọn ở lần scan kế".to_string(),
        });
    };

    match action.as_str() {
        "kill" => {
            // Re-verify the PID still belongs to an agent process — guards
            // against PID reuse between the banner render and this click.
            if crate::agentrun::recovery::pid_is_live_agent(pid) {
                let _ = crate::agentrun::procutil::kill_pid(pid);
            }
            crate::agentrun::recovery::mark_interrupted(
                &agents_root,
                &feature,
                &slot,
                &marker,
                "Bị gián đoạn — process mồ côi từ phiên trước đã bị kill theo yêu cầu. Chọn Resume hoặc Re-run.".to_string(),
            );
            recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            Ok(())
        }
        "attach" => {
            std::thread::spawn(move || {
                while crate::agentrun::recovery::pid_is_live_agent(pid) {
                    std::thread::sleep(std::time::Duration::from_secs(2));
                }
                crate::agentrun::recovery::mark_interrupted(
                    &agents_root,
                    &feature,
                    &slot,
                    &marker,
                    "Process mồ côi đã tự kết thúc — trạng thái dựng lại từ artifact trên disk. Nếu chưa đủ, chọn Resume hoặc Re-run.".to_string(),
                );
                recompute_and_emit(&app, &agents_root, &docs_root, &feature);
            });
            Ok(())
        }
        other => Err(AppError::Invalid {
            message: format!("Hành động không hợp lệ: {other} (chỉ nhận \"attach\" hoặc \"kill\")"),
        }),
    }
}

/// Splits stage ②'s declared agent slots into ones ready to spawn (their
/// `.claude/agents/<agent_name>.md` exists in the kit) and ones to skip
/// (it doesn't — e.g. `design-analyst-agent`, not yet authored per B17).
/// Pure and testable without a live Tauri app, unlike the rest of gate
/// approval below.
fn partition_stage_slots_by_agent_availability(
    slots: Vec<AgentSlot>,
    agents_found: &[String],
) -> (Vec<AgentSlot>, Vec<AgentSlot>) {
    slots
        .into_iter()
        .partition(|agent_slot| agents_found.contains(&agent_slot.agent_name))
}

fn stage_two_agent_slots(agents_root: &Path) -> Vec<AgentSlot> {
    crate::commands::pipeline::read_or_init_pipeline_def(agents_root)
        .ok()
        .and_then(|def| {
            def.stages
                .into_iter()
                .find(|stage_def| stage_def.id == "S2_design")
                .map(|stage_def| stage_def.agents)
        })
        .unwrap_or_default()
}

/// AC-E4-01/02/07 — Trigger gate approval. Writes the approval into
/// `state.json` (sticky from then on — see `inference::gate_rules`'s doc
/// comment), then spawns every stage ② slot in parallel: each is an
/// independent `run_to_completion` on its own background thread, same
/// mechanism every other spawn path already uses — "parallel" here is
/// just "more than one such thread at once," no new orchestration
/// primitive. A slot whose agent file doesn't exist in the kit yet is
/// skipped via the same `record_pre_spawn_outcome`/`RunOutcome::Skipped`
/// path AC-E2-12 already built, rather than blocking the other slots.
/// The read-modify-write half of `approve_trigger_gate`, split out so the
/// `lock_state_file()` guard provably ends with this function.
///
/// That scope is the whole point, not tidiness: the guard used to live in
/// `approve_trigger_gate`'s own body and was therefore still held when that
/// function reached `recompute_and_emit` -> `pipeline_state::compute_and_persist`,
/// which takes the SAME non-reentrant mutex on the SAME thread. Tauri runs
/// non-async commands on the main thread, so that self-deadlock froze the
/// whole window while the approval was already on disk (hence "restart and
/// it is approved").
///
/// Re-reads `state.json` fresh rather than reusing the `FeatureState` the
/// caller just computed, so a concurrent write from an unrelated in-flight
/// run is never clobbered. Re-reading alone only narrows the window; the
/// lock closes it.
fn persist_trigger_gate_approval(
    agents_root: &Path,
    feature: &str,
    approved_by: String,
) -> AppResult<()> {
    let _state_guard = orchestrator_dir::lock_state_file();
    let state_path = orchestrator_dir::state_json_path(agents_root);
    let mut file: StateFile = std::fs::read_to_string(&state_path)
        .ok()
        .and_then(|raw| serde_json::from_str(&raw).ok())
        .unwrap_or_default();
    file.features
        .entry(feature.to_string())
        .or_default()
        .gates
        .insert(
            gate::TRIGGER.to_string(),
            GateState {
                status: GateStatus::Approved,
                approved_by: Some(approved_by),
                approved_at: Some(chrono::Utc::now().to_rfc3339()),
                missing_sections: vec![],
            },
        );
    write_json_atomic(&state_path, &file)
}

#[tauri::command]
pub fn approve_trigger_gate(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
    approved_by: String,
) -> AppResult<()> {
    let approved_by = approved_by.trim().to_string();
    if approved_by.is_empty() {
        return Err(AppError::Invalid {
            message: "Cần nhập tên người duyệt trước khi Approve".to_string(),
        });
    }

    let project = current_project(&state)?;
    let agents_root = PathBuf::from(project.agents_root);
    let docs_root = PathBuf::from(project.docs_root);
    let ecosystem = state.ecosystem.lock().unwrap().clone();

    // Recompute fresh first — never trust a possibly-stale on-disk gate
    // status for the guard below.
    let (current_state, _) = compute_and_persist(&agents_root, &docs_root, &feature, &ecosystem)?;
    let is_pending = current_state
        .gates
        .get(gate::TRIGGER)
        .map(|g| g.status == GateStatus::PendingReview)
        .unwrap_or(false);
    if !is_pending {
        return Err(AppError::Invalid {
            message: "Gate không ở trạng thái chờ duyệt — không thể Approve".to_string(),
        });
    }

    persist_trigger_gate_approval(&agents_root, &feature, approved_by)?;

    let stage_two_slots = stage_two_agent_slots(&agents_root);
    let agents_found = agents_reader::discover_agents(&agents_root).unwrap_or_default();
    let (ready, skipped) =
        partition_stage_slots_by_agent_availability(stage_two_slots, &agents_found);

    for agent_slot in skipped {
        record_pre_spawn_outcome(
            &app,
            &agents_root,
            &feature,
            &agent_slot.id,
            RunOutcome::Skipped,
            format!(
                "Agent \"{}\" chưa tồn tại trong kit (.claude/agents/{}.md) — bỏ qua.",
                agent_slot.agent_name, agent_slot.agent_name
            ),
        );
    }

    // B22 — approving the gate no longer launches stage ②. It used to fan
    // out to all three agents at once, which is three paid runs from one
    // click; now the gate just records the approval and those slots become
    // Ready, each with its own Run button.
    let _ = ready;

    recompute_and_emit(&app, &agents_root, &docs_root, &feature);
    Ok(())
}

/// AC-E4-18 — `backend-agent` expects a `task-x-y.md` path as its primary
/// input, not a bare `DESIGN.md` pointer (verified against
/// `.claude/agents/backend-agent.md`'s own `## Quy trình làm việc` — it
/// reads SPEC.md/DESIGN.md paths FROM the task file's `## Context`
/// section, not directly). Finds every `task-*.md` inside the same repo
/// directory as a just-locked `DESIGN.md`, in filename order (Tech Lead
/// Tasks' own `task-<phase>-<seq>.md` convention implies that order).
/// Falls back to pointing at `DESIGN.md` directly (and says so) if no task
/// files are found — never silently pretends they exist.
fn build_backend_agent_prompt(feature_dir: &Path, locked_design_md_paths: &[PathBuf]) -> String {
    let repo_dirs: Vec<&Path> = locked_design_md_paths
        .iter()
        .filter_map(|p| p.parent())
        .collect();
    let mut task_files: Vec<PathBuf> = stage_rules::task_files_in_repos(feature_dir)
        .into_iter()
        .filter(|task_path| repo_dirs.iter().any(|repo| task_path.starts_with(repo)))
        .collect();
    task_files.sort();

    if task_files.is_empty() {
        let design_paths = locked_design_md_paths
            .iter()
            .map(|p| p.display().to_string())
            .collect::<Vec<_>>()
            .join(", ");
        format!(
            "Contract vừa được khoá cho feature này. Đọc DESIGN.md tại {design_paths} và SPEC.md \
             của feature, thực hiện đúng quy trình của bạn. (Không tìm thấy task-*.md nào trong \
             repo — có thể Tech Lead Tasks chưa chạy cho feature này.)"
        )
    } else {
        let task_paths = task_files
            .iter()
            .map(|p| p.display().to_string())
            .collect::<Vec<_>>()
            .join("\n");
        format!(
            "Contract vừa được khoá cho feature này. Đọc và thực hiện lần lượt các task sau theo \
             đúng quy trình của bạn:\n{task_paths}"
        )
    }
}

/// AC-E4-16..18 — validates and persists a Lock, then spawns
/// `backend-agent` (stage ⑤). Server-side re-validates everything the
/// frontend's Lock button already gates on (AC-E4-13) — never trust the
/// client alone for a write like this.
#[tauri::command]
pub fn lock_contract(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
    approved_by: String,
    confirmed_roles: Vec<String>,
) -> AppResult<()> {
    let approved_by = approved_by.trim().to_string();
    if approved_by.is_empty() {
        return Err(AppError::Invalid {
            message: "Cần nhập tên người duyệt trước khi Lock".to_string(),
        });
    }
    if let Some(unknown) = confirmed_roles
        .iter()
        .find(|role| !crate::domain::contract_lock::ALL_ROLES.contains(&role.as_str()))
    {
        return Err(AppError::Invalid {
            message: format!("Vai trò không hợp lệ: \"{unknown}\""),
        });
    }

    let project = current_project(&state)?;
    let agents_root = PathBuf::from(project.agents_root);
    let docs_root = PathBuf::from(project.docs_root);
    let ecosystem = state.ecosystem.lock().unwrap().clone();

    let (current_state, _) = compute_and_persist(&agents_root, &docs_root, &feature, &ecosystem)?;
    let contract_lock = current_state
        .contract_lock
        .ok_or_else(|| AppError::Invalid {
            message: "Không tính được trạng thái Contract Lock".to_string(),
        })?;
    // AC-E4-27 — Re-lock uses this exact same command, just from
    // `Violated` instead of `PendingReview`. Nothing else about the flow
    // changes: role re-confirmation and the file list still come from
    // `design_md_files_with_api_table` fresh, and any slot blocked by
    // `contract_is_violated` (AC-E4-23) becomes spawnable again on its own
    // next attempt once this Lock succeeds — no separate "unblock" step.
    if !matches!(
        contract_lock.status,
        ContractLockStatus::PendingReview | ContractLockStatus::Violated
    ) {
        return Err(AppError::Invalid {
            message: "Gate không ở trạng thái chờ duyệt hoặc vi phạm — không thể Lock".to_string(),
        });
    }

    // AC-E4-13 — server-side enforcement, never trust the client's
    // button-disabled state alone for a write like this.
    let confirmed: std::collections::HashSet<&str> =
        confirmed_roles.iter().map(String::as_str).collect();
    let missing_roles: Vec<&str> = contract_lock
        .applicable_roles
        .iter()
        .map(String::as_str)
        .filter(|role| !confirmed.contains(role))
        .collect();
    if !missing_roles.is_empty() {
        return Err(AppError::Invalid {
            message: format!(
                "Chưa xác nhận đủ vai trò áp dụng được: {}",
                missing_roles.join(", ")
            ),
        });
    }

    let feature_dir = docs_root.join("features").join(&feature);
    let locked_design_md_paths = api_definition::design_md_files_with_api_table(&feature_dir);
    let mut locked_files = Vec::with_capacity(locked_design_md_paths.len());
    for path in &locked_design_md_paths {
        let content = std::fs::read_to_string(path).map_err(|_| AppError::Invalid {
            message: format!("Không đọc được file cần khoá: {}", path.display()),
        })?;
        locked_files.push(LockedFile {
            path: path.display().to_string(),
            checksum_sha256: contract_lock_rules::sha256_hex(&content),
            content,
        });
    }

    let record = ContractLockRecord {
        locked_at: chrono::Utc::now().to_rfc3339(),
        approved_by,
        confirmed_roles,
        files: locked_files,
    };
    let lock_dir = orchestrator_dir::contract_lock_dir(&agents_root, &feature);
    contract_lock_store::write_lock_record(&lock_dir, &record)?;

    // B22 — locking no longer spawns `backend-agent`. The lock is what the
    // gate is for; the run is a separate, deliberate click. `run_slot`
    // rebuilds the very same prompt from this record's locked DESIGN.md
    // paths, so the backend still starts from the frozen contract.
    let _ = &locked_design_md_paths;

    recompute_and_emit(&app, &agents_root, &docs_root, &feature);
    Ok(())
}

/// Recomputes the gate purely from disk, the same way every other
/// contract-lock read in this file does — never trusting the `state.json`
/// cache the frontend happened to be looking at when the button was
/// clicked.
fn current_contract_lock_status(
    agents_root: &Path,
    docs_root: &Path,
    feature: &str,
    ecosystem: &[EcosystemRepo],
) -> ContractLockStatus {
    let feature_dir = docs_root.join("features").join(feature);
    let dir = orchestrator_dir::contract_lock_dir(agents_root, feature);
    contract_lock_rules::infer_contract_lock_state(
        &feature_dir,
        ecosystem,
        contract_lock_store::read_latest_lock(&dir),
        contract_lock_store::read_skip(&dir),
    )
    .status
}

/// AC-E4-11b — lets the PM take a feature past a Contract Lock that
/// inference cannot clear on its own: the feature genuinely spans backend
/// and a consumer, but this change adds no endpoint, so no `DESIGN.md`
/// carries an API Definition table and the gate would sit at `NotReady`
/// forever with nothing to click.
///
/// Deliberately NOT allowed from any other status. From `PendingReview`
/// the correct action is Lock — a skip there would quietly discard the
/// contract the gate exists to freeze; from `Locked`/`Violated` there is a
/// real lock whose checksums still have to be honoured. Re-checked here
/// rather than trusted from the frontend, same as `lock_contract`.
#[tauri::command]
pub fn skip_contract_lock(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
    skipped_by: String,
    reason: String,
) -> AppResult<()> {
    orchestrator_dir::validate_feature_id(&feature)?;
    let skipped_by = skipped_by.trim().to_string();
    let reason = reason.trim().to_string();
    if skipped_by.is_empty() {
        return Err(AppError::Invalid {
            message: "Cần nhập tên người bỏ qua gate".to_string(),
        });
    }
    if reason.is_empty() {
        return Err(AppError::Invalid {
            message: "Cần nhập lý do bỏ qua Contract Lock".to_string(),
        });
    }

    let project = current_project(&state)?;
    let agents_root = PathBuf::from(project.agents_root);
    let docs_root = PathBuf::from(project.docs_root);
    let ecosystem = state.ecosystem.lock().unwrap().clone();

    let status = current_contract_lock_status(&agents_root, &docs_root, &feature, &ecosystem);
    if status != ContractLockStatus::NotReady {
        return Err(AppError::Invalid {
            message:
                "Chỉ bỏ qua được khi gate đang bị chặn vì thiếu bảng API Definition — trạng thái hiện tại không cho phép"
                    .to_string(),
        });
    }

    let dir = orchestrator_dir::contract_lock_dir(&agents_root, &feature);
    std::fs::create_dir_all(&dir)?;
    contract_lock_store::write_skip(
        &dir,
        &crate::domain::contract_lock::ContractLockSkip {
            skipped_by,
            reason,
            skipped_at: chrono::Utc::now().to_rfc3339(),
        },
    )?;

    recompute_and_emit(&app, &agents_root, &docs_root, &feature);
    Ok(())
}

/// AC-E4-11b — takes the skip back, so a mis-click isn't permanent. The
/// gate returns to whatever inference says on its own (normally
/// `NotReady`, i.e. blocking again).
#[tauri::command]
pub fn unskip_contract_lock(
    app: AppHandle,
    state: State<AppState>,
    feature: String,
) -> AppResult<()> {
    orchestrator_dir::validate_feature_id(&feature)?;
    let project = current_project(&state)?;
    let agents_root = PathBuf::from(project.agents_root);
    let docs_root = PathBuf::from(project.docs_root);

    let dir = orchestrator_dir::contract_lock_dir(&agents_root, &feature);
    contract_lock_store::clear_skip(&dir)?;

    recompute_and_emit(&app, &agents_root, &docs_root, &feature);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn contract_lock_state(
        status: ContractLockStatus,
    ) -> crate::domain::contract_lock::ContractLockState {
        crate::domain::contract_lock::ContractLockState {
            status,
            checked_design_md_paths: vec![],
            missing_columns: vec![],
            manually_skipped: false,
            not_applicable_reason: None,
            applicable_roles: vec![],
            candidate_files: vec![],
            current_lock: None,
            violated_files: vec![],
            running_on_old_contract: false,
        }
    }

    fn feature_state_with_lock(
        status: ContractLockStatus,
    ) -> crate::domain::state_file::FeatureState {
        crate::domain::state_file::FeatureState {
            nodes: std::collections::BTreeMap::new(),
            gates: std::collections::BTreeMap::new(),
            contract_lock: Some(contract_lock_state(status)),
            updated_at: String::new(),
        }
    }

    /// Reproduces the freeze: `approve_trigger_gate` writes the approval,
    /// then calls `recompute_and_emit` -> `compute_and_persist`, which
    /// re-locks `state.json`. With the guard still held by the write half,
    /// that second lock never returns — on Tauri's main thread, the window.
    ///
    /// Driven through the same two functions the command calls, in the same
    /// order, so it fails (hangs before the fix, panics with the reentrancy
    /// assert) if anyone ever widens that guard's scope again.
    #[test]
    fn persisting_a_gate_approval_releases_the_state_lock_before_recompute() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let docs_root = tmp.path().join("docs-root");
        std::fs::create_dir_all(docs_root.join("features/login")).unwrap();
        std::fs::create_dir_all(&agents_root).unwrap();

        persist_trigger_gate_approval(&agents_root, "login", "PM Test".to_string()).unwrap();

        // The lock must be free by now — this is what `recompute_and_emit`
        // reaches immediately afterwards in the real command.
        let (state, _) = compute_and_persist(&agents_root, &docs_root, "login", &[]).unwrap();

        let approved = state.gates.get(gate::TRIGGER).unwrap();
        assert_eq!(approved.status, GateStatus::Approved);
        assert_eq!(approved.approved_by.as_deref(), Some("PM Test"));
    }

    fn ecosystem_repo(name: &str, role: &str) -> EcosystemRepo {
        EcosystemRepo {
            name: name.to_string(),
            declared_path: format!("repos/{name}"),
            role: role.to_string(),
            // Derived exactly as the parser does, so a fixture can never
            // claim a role the real pipeline wouldn't read off that cell.
            role_key: crate::agents_reader::canonical_role(role).map(str::to_string),
            stack: "x".to_string(),
            cloned: true,
        }
    }

    /// The guard `skip_contract_lock` runs before writing anything. Driven
    /// through the same helper the command uses, so the two can't drift.
    ///
    /// Skip is only ever legitimate from `NotReady`: from `PendingReview`
    /// there IS a contract and skipping would silently throw it away, which
    /// is precisely what this gate exists to prevent.
    #[test]
    fn contract_lock_skip_is_only_offered_from_the_blocked_state() {
        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let docs_root = tmp.path().join("docs-root");
        let feature_dir = docs_root.join("features").join("login");
        std::fs::create_dir_all(&agents_root).unwrap();
        let ecosystem = vec![
            ecosystem_repo("shop-api", "backend"),
            ecosystem_repo("shop-web", "frontend"),
        ];

        let write = |repo: &str, content: &str| {
            let path = feature_dir.join(repo).join("DESIGN.md");
            std::fs::create_dir_all(path.parent().unwrap()).unwrap();
            std::fs::write(path, content).unwrap();
        };

        // Backend + frontend, no API table anywhere -> blocked, skippable.
        write("shop-api", "## 1. Tổng quan\nx\n");
        write("shop-web", "## 1. Tổng quan\nx\n");
        assert_eq!(
            current_contract_lock_status(&agents_root, &docs_root, "login", &ecosystem),
            ContractLockStatus::NotReady
        );

        // Table appears -> the gate can be opened properly, so skip must be
        // refused from here on.
        write(
            "shop-api",
            "## 3. API Definition\n\n| Method | Endpoint | Auth | Request | Response | Error codes |\n|---|---|---|---|---|---|\n| POST | `/x` | JWT | `{}` | `{}` | 400 |\n",
        );
        assert_eq!(
            current_contract_lock_status(&agents_root, &docs_root, "login", &ecosystem),
            ContractLockStatus::PendingReview
        );
    }

    /// AC-E4-11 — feature 1 repo không cần Contract Lock. Trước đây chỉ
    /// `Locked` mới qua gate, nên `NotApplicable` chặn stage ⑤ vĩnh viễn:
    /// không có nút Lock nào để bấm ở trạng thái đó. Nó thuộc nhóm
    /// "skipped" chứ không phải "passed" — xem `readiness`.
    #[test]
    fn not_applicable_contract_lock_is_skipped_not_passed() {
        let (_, passed_gates, skipped_gates) =
            statuses_and_passed_gates(&feature_state_with_lock(ContractLockStatus::NotApplicable));
        assert!(!passed_gates.contains(&gate::CONTRACT_LOCK.to_string()));
        assert!(skipped_gates.contains(&gate::CONTRACT_LOCK.to_string()));
    }

    #[test]
    fn locked_contract_lock_counts_as_a_passed_gate() {
        let (_, passed_gates, skipped_gates) =
            statuses_and_passed_gates(&feature_state_with_lock(ContractLockStatus::Locked));
        assert!(passed_gates.contains(&gate::CONTRACT_LOCK.to_string()));
        assert!(skipped_gates.is_empty());
    }

    /// Chốt lại giới hạn: một contract đang chờ duyệt hay đang vi phạm vẫn
    /// phải chặn stage ⑤, không rơi vào nhóm nào cả.
    #[test]
    fn a_contract_lock_still_awaiting_review_or_violated_neither_passes_nor_skips() {
        for status in [
            ContractLockStatus::NotReady,
            ContractLockStatus::PendingReview,
            ContractLockStatus::Violated,
        ] {
            let (_, passed_gates, skipped_gates) =
                statuses_and_passed_gates(&feature_state_with_lock(status));
            assert!(
                !passed_gates.contains(&gate::CONTRACT_LOCK.to_string())
                    && !skipped_gates.contains(&gate::CONTRACT_LOCK.to_string()),
                "{status:?} must still block stage ⑤"
            );
        }
    }

    #[test]
    fn resolve_agent_name_uses_real_pipeline_def_not_a_naming_convention_guess() {
        let tmp = tempfile::tempdir().unwrap();
        // qc-design's real agent_name is "qc-agent" — the naming-convention
        // guess `format!("{slot}-agent")` would wrongly produce
        // "qc-design-agent", which doesn't exist in the kit.
        assert_eq!(resolve_agent_name(tmp.path(), slot::QC_DESIGN), "qc-agent");
        assert_eq!(resolve_agent_name(tmp.path(), slot::BA), "ba-agent");
    }

    #[test]
    fn resolve_agent_name_falls_back_to_convention_for_a_slot_not_in_pipeline_def() {
        let tmp = tempfile::tempdir().unwrap();
        assert_eq!(
            resolve_agent_name(tmp.path(), "made-up-slot"),
            "made-up-slot-agent"
        );
    }

    #[test]
    fn partition_stage_slots_by_agent_availability_splits_ready_and_skipped() {
        let slots = vec![
            AgentSlot {
                id: "techlead-design".to_string(),
                agent_name: "techlead-design-agent".to_string(),
                label: None,
                after_slots: vec![],
            },
            AgentSlot {
                id: "design-analyst".to_string(),
                agent_name: "design-analyst-agent".to_string(),
                label: None,
                after_slots: vec![],
            },
            AgentSlot {
                id: "qc-design".to_string(),
                agent_name: "qc-agent".to_string(),
                label: None,
                after_slots: vec![],
            },
        ];
        let agents_found = vec!["techlead-design-agent".to_string(), "qc-agent".to_string()];

        let (ready, skipped) = partition_stage_slots_by_agent_availability(slots, &agents_found);
        assert_eq!(
            ready.iter().map(|s| s.id.as_str()).collect::<Vec<_>>(),
            vec!["techlead-design", "qc-design"]
        );
        assert_eq!(
            skipped.iter().map(|s| s.id.as_str()).collect::<Vec<_>>(),
            vec!["design-analyst"]
        );
    }

    #[test]
    fn backend_agent_prompt_lists_task_files_in_the_locked_repo_in_order() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        let repo_dir = feature_dir.join("api-repo");
        let tasks_dir = repo_dir.join("tasks");
        std::fs::create_dir_all(&tasks_dir).unwrap();
        std::fs::write(tasks_dir.join("task-5-2.md"), "x").unwrap();
        std::fs::write(tasks_dir.join("task-5-1.md"), "x").unwrap();
        // A task file in an unrelated repo must never leak into the prompt.
        let other_repo = feature_dir.join("web-repo");
        std::fs::create_dir_all(other_repo.join("tasks")).unwrap();
        std::fs::write(other_repo.join("tasks/task-5-1.md"), "x").unwrap();

        let design_md = repo_dir.join("DESIGN.md");
        let prompt = build_backend_agent_prompt(&feature_dir, &[design_md]);

        assert!(prompt.contains("task-5-1.md"));
        assert!(prompt.contains("task-5-2.md"));
        assert!(!prompt.contains("web-repo"));
        // Filename order: task-5-1 before task-5-2.
        assert!(prompt.find("task-5-1.md").unwrap() < prompt.find("task-5-2.md").unwrap());
    }

    #[test]
    fn backend_agent_prompt_falls_back_to_design_md_when_no_task_files_exist() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        let design_md = feature_dir.join("api-repo").join("DESIGN.md");
        std::fs::create_dir_all(design_md.parent().unwrap()).unwrap();

        let prompt = build_backend_agent_prompt(&feature_dir, std::slice::from_ref(&design_md));
        assert!(prompt.contains(&design_md.display().to_string()));
        assert!(prompt.contains("Không tìm thấy task-*.md"));
    }

    #[test]
    fn contract_is_violated_true_after_a_locked_file_is_edited() {
        use crate::domain::contract_lock::{ContractLockRecord, LockedFile};

        let tmp = tempfile::tempdir().unwrap();
        let agents_root = tmp.path().join("agents-root");
        let feature_dir = tmp.path().join("docs-root/features/feature-a");
        let design_md = feature_dir.join("api").join("DESIGN.md");
        std::fs::create_dir_all(design_md.parent().unwrap()).unwrap();
        std::fs::write(&design_md, "original").unwrap();

        let lock_dir = orchestrator_dir::contract_lock_dir(&agents_root, "feature-a");
        contract_lock_store::write_lock_record(
            &lock_dir,
            &ContractLockRecord {
                locked_at: "2026-08-17T00:00:00Z".to_string(),
                approved_by: "PM Test".to_string(),
                confirmed_roles: vec!["PM".to_string(), "QC".to_string()],
                files: vec![LockedFile {
                    path: design_md.display().to_string(),
                    checksum_sha256: contract_lock_rules::sha256_hex("original"),
                    content: "original".to_string(),
                }],
            },
        )
        .unwrap();

        assert!(!contract_is_violated(
            &agents_root,
            &feature_dir,
            "feature-a",
            &[]
        ));

        std::fs::write(&design_md, "edited").unwrap();
        assert!(contract_is_violated(
            &agents_root,
            &feature_dir,
            "feature-a",
            &[]
        ));
    }

    #[test]
    fn stage_three_prompts_reference_design_analysis_only_when_it_exists() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();

        // Stage ③ is a single slot since `pm-agent` was removed.
        let without = build_slot_prompt(slot::TECHLEAD_TASKS, &feature_dir, None);
        assert!(!without.contains("design-analysis.md"));

        std::fs::write(feature_dir.join("design-analysis.md"), "# analysis").unwrap();
        let with = build_slot_prompt(slot::TECHLEAD_TASKS, &feature_dir, None);
        assert!(with.contains("design-analysis.md")); // AC-E2-39
    }

    #[test]
    fn figma_in_project_config_detects_candidate_or_explicit_choice() {
        let tmp = tempfile::tempdir().unwrap();
        // No MCP config at all → unavailable (AC-E2-33 blocks).
        assert!(!figma_in_project_config(tmp.path()));

        // A non-figma server alone isn't enough.
        std::fs::create_dir_all(tmp.path().join(".claude")).unwrap();
        std::fs::write(
            tmp.path().join(".claude/settings.json"),
            r#"{"mcpServers":{"tilth":{"command":"tilth","args":["--mcp"]}}}"#,
        )
        .unwrap();
        assert!(!figma_in_project_config(tmp.path()));

        // An explicit user choice pointing at an existing server counts,
        // even when auto-detection finds nothing.
        let config_path = orchestrator_dir::config_json_path(tmp.path());
        std::fs::create_dir_all(config_path.parent().unwrap()).unwrap();
        std::fs::write(
            &config_path,
            r#"{"agents":{},"max_retries":2,"figma_mcp_server":"tilth"}"#,
        )
        .unwrap();
        assert!(figma_in_project_config(tmp.path()));

        // A choice pointing at a server that no longer exists doesn't.
        std::fs::write(
            &config_path,
            r#"{"agents":{},"max_retries":2,"figma_mcp_server":"gone"}"#,
        )
        .unwrap();
        assert!(!figma_in_project_config(tmp.path()));

        // Auto-detected candidate works with no explicit choice.
        std::fs::write(
            tmp.path().join(".claude/settings.json"),
            r#"{"mcpServers":{"figma":{"type":"http","url":"http://127.0.0.1:3845/mcp"}}}"#,
        )
        .unwrap();
        assert!(figma_in_project_config(tmp.path()));
    }

    /// G4/B22 — the Figma URL typed in the UI must reach the agent, so it
    /// can finish in one run instead of stopping to ask and needing a
    /// second resumed run.
    #[test]
    fn design_analyst_prompt_carries_the_figma_url_only_when_one_was_given() {
        let tmp = tempfile::tempdir().unwrap();
        let feature_dir = tmp.path().join("feature");
        std::fs::create_dir_all(&feature_dir).unwrap();

        let with_url = build_slot_prompt(
            slot::DESIGN_ANALYST,
            &feature_dir,
            Some("https://figma.com/design/abc?node-id=1-2"),
        );
        assert!(with_url.contains("https://figma.com/design/abc?node-id=1-2"));
        assert!(with_url.contains("KHÔNG hỏi lại"));
        assert!(with_url.contains("SPEC.md"));
        // AC-E2-37a — the export target is named with an absolute path in
        // both branches, so the agent never has to infer it from cwd.
        assert!(with_url.contains(&feature_dir.join("design-resources").display().to_string()));

        // Blank or absent input must not fabricate a URL — the agent's own
        // Bước 2 takes over and asks.
        for empty in [None, Some(""), Some("   ")] {
            let without = build_slot_prompt(slot::DESIGN_ANALYST, &feature_dir, empty);
            assert!(
                !without.contains("KHÔNG hỏi lại"),
                "empty input leaked a URL branch"
            );
            assert!(without.contains("SPEC.md"));
            assert!(without.contains(&feature_dir.join("design-resources").display().to_string()));
        }
    }
}
