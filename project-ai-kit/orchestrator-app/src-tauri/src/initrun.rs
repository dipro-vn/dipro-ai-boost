//! Interactive Claude session for the in-app project setup flow.
//!
//! Pipeline agents intentionally run headlessly through `agentrun`. `/init-kit`
//! is different: the canonical init agent must ask the user questions, so it
//! needs a real PTY and raw terminal input/output.

use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

use portable_pty::{native_pty_system, Child, ChildKiller, CommandBuilder, MasterPty, PtySize};
use tauri::{AppHandle, Emitter, Manager, State};

use crate::agentrun::cli_path;
use crate::agentrun::process_group::{self, Signal};
use crate::app_state::AppState;
use crate::auth;
use crate::domain::config_file::ClaudeAuthMode;
use crate::domain::project::ProjectPaths;
use crate::error::{AppError, AppResult};

pub const EVENT_OUTPUT: &str = "init-kit://output";
pub const EVENT_FINISHED: &str = "init-kit://finished";

static NEXT_SESSION_ID: AtomicU64 = AtomicU64::new(1);

#[derive(Clone, Debug, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct InitKitSessionInfo {
    pub session_id: String,
    pub project_name: String,
}

#[derive(Clone, Debug, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct InitKitStatus {
    pub running: bool,
    pub session_id: Option<String>,
    pub project_name: Option<String>,
}

#[derive(Clone, Debug, serde::Serialize)]
#[serde(rename_all = "camelCase")]
struct InitKitOutputPayload {
    session_id: String,
    data: String,
}

#[derive(Clone, Debug, serde::Serialize)]
#[serde(rename_all = "camelCase")]
struct InitKitFinishedPayload {
    session_id: String,
    exit_code: Option<u32>,
    stopped: bool,
}

/// Handles one live PTY. The writer and master are locked independently so a
/// terminal keystroke cannot race a resize request.
pub struct InitKitSession {
    pub id: String,
    pub project_name: String,
    writer: Mutex<Box<dyn Write + Send>>,
    master: Mutex<Box<dyn MasterPty + Send>>,
    child: Mutex<Box<dyn Child + Send + Sync>>,
    killer: Mutex<Box<dyn ChildKiller + Send + Sync>>,
    stopped: AtomicBool,
}

struct InitStartingGuard<'a>(&'a AtomicBool);

impl Drop for InitStartingGuard<'_> {
    fn drop(&mut self) {
        self.0.store(false, Ordering::SeqCst);
    }
}

impl InitKitSession {
    fn stop(&self) {
        self.stopped.store(true, Ordering::SeqCst);
        #[cfg(unix)]
        if let Some(pid) = self
            .master
            .lock()
            .unwrap()
            .process_group_leader()
            .and_then(|pid| u32::try_from(pid).ok())
        {
            process_group::signal_group(pid, Signal::Kill);
        }
        let _ = self.killer.lock().unwrap().kill();
    }
}

fn current_project(state: &State<AppState>) -> AppResult<ProjectPaths> {
    state
        .current_project
        .lock()
        .unwrap()
        .clone()
        .ok_or(AppError::NoProjectOpen)
}

fn configure_auth(command: &mut CommandBuilder, resolved: &auth::ResolvedClaudeAuth) {
    const OVERRIDES: [&str; 8] = [
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CODE_API_KEY_HELPER",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "ANTHROPIC_PROFILE",
    ];

    if resolved.mode != ClaudeAuthMode::CliDefault {
        for name in OVERRIDES {
            command.env_remove(name);
        }
    }
    if let Some(key) = resolved.api_key.as_deref() {
        command.env("ANTHROPIC_API_KEY", key);
    }
}

fn start_reader(app: &AppHandle, session: Arc<InitKitSession>, mut reader: Box<dyn Read + Send>) {
    let app = app.clone();
    let session_id = session.id.clone();
    std::thread::spawn(move || {
        let mut buffer = [0_u8; 8192];
        loop {
            match reader.read(&mut buffer) {
                Ok(0) => break,
                Ok(count) => {
                    let _ = app.emit(
                        EVENT_OUTPUT,
                        InitKitOutputPayload {
                            session_id: session_id.clone(),
                            data: String::from_utf8_lossy(&buffer[..count]).into_owned(),
                        },
                    );
                }
                Err(_) => break,
            }
        }

        let exit_code = session
            .child
            .lock()
            .unwrap()
            .wait()
            .ok()
            .map(|status| status.exit_code());
        let stopped = session.stopped.load(Ordering::SeqCst);
        let _ = app.emit(
            EVENT_FINISHED,
            InitKitFinishedPayload {
                session_id: session_id.clone(),
                exit_code,
                stopped,
            },
        );

        let state = app.state::<AppState>();
        let mut current = state.init_session.lock().unwrap();
        if current
            .as_ref()
            .is_some_and(|active| active.id == session_id)
        {
            current.take();
        }
    });
}

pub fn stop_session(slot: &Mutex<Option<Arc<InitKitSession>>>) -> bool {
    let session = slot.lock().unwrap().take();
    if let Some(session) = session {
        session.stop();
        true
    } else {
        false
    }
}

#[tauri::command]
pub fn init_kit_status(state: State<AppState>) -> InitKitStatus {
    let session = state.init_session.lock().unwrap().clone();
    let running = session.is_some() || state.init_starting.load(Ordering::SeqCst);
    InitKitStatus {
        running,
        session_id: session.as_ref().map(|session| session.id.clone()),
        project_name: session.map(|session| session.project_name.clone()),
    }
}

#[tauri::command]
pub fn start_init_kit(
    app: AppHandle,
    state: State<AppState>,
    project_name: String,
) -> AppResult<InitKitSessionInfo> {
    if !crate::agentrun::spawn::is_claude_cli_available() {
        return Err(AppError::Invalid {
            message: cli_path::not_found_message(),
        });
    }
    let project = current_project(&state)?;
    let expected_epoch = *state.spawn_admission.lock().unwrap();
    let project_name = project_name.trim().to_string();
    if project_name.is_empty() {
        return Err(AppError::Invalid {
            message: "Tên project chưa được điền".to_string(),
        });
    }
    if state.init_starting.swap(true, Ordering::SeqCst) {
        return Err(AppError::Invalid {
            message: "Project này đã có phiên init-kit đang chạy".to_string(),
        });
    }
    let _starting_guard = InitStartingGuard(&state.init_starting);
    if state.init_session.lock().unwrap().is_some() {
        return Err(AppError::Invalid {
            message: "Project này đã có phiên init-kit đang chạy".to_string(),
        });
    }

    let agents_root = PathBuf::from(project.agents_root);
    let resolved_auth = auth::resolve_for_spawn(&agents_root)?;
    let pty = native_pty_system();
    let pair = pty
        .openpty(PtySize {
            rows: 30,
            cols: 120,
            pixel_width: 0,
            pixel_height: 0,
        })
        .map_err(|err| AppError::Invalid {
            message: format!("Không mở được terminal init-kit: {err}"),
        })?;

    let mut command = CommandBuilder::new(cli_path::program());
    command.cwd(Path::new(&agents_root));
    command.env("TERM", "xterm-256color");
    configure_auth(&mut command, &resolved_auth);
    let child = pair
        .slave
        .spawn_command(command)
        .map_err(|err| AppError::Invalid {
            message: format!("Không khởi chạy được Claude CLI: {err}"),
        })?;
    drop(pair.slave);

    let reader = match pair.master.try_clone_reader() {
        Ok(reader) => reader,
        Err(err) => {
            let mut child = child;
            let _ = child.kill();
            return Err(AppError::Invalid {
                message: format!("Không đọc được terminal init-kit: {err}"),
            });
        }
    };
    let writer = match pair.master.take_writer() {
        Ok(writer) => writer,
        Err(err) => {
            let mut child = child;
            let _ = child.kill();
            return Err(AppError::Invalid {
                message: format!("Không ghi được terminal init-kit: {err}"),
            });
        }
    };
    let killer = child.clone_killer();
    let session = Arc::new(InitKitSession {
        id: format!("init-{}", NEXT_SESSION_ID.fetch_add(1, Ordering::Relaxed)),
        project_name: project_name.clone(),
        writer: Mutex::new(writer),
        master: Mutex::new(pair.master),
        child: Mutex::new(child),
        killer: Mutex::new(killer),
        stopped: AtomicBool::new(false),
    });

    let admitted = {
        let epoch = state.spawn_admission.lock().unwrap();
        if *epoch != expected_epoch {
            false
        } else {
            *state.init_session.lock().unwrap() = Some(session.clone());
            true
        }
    };
    if !admitted {
        session.stop();
        return Err(AppError::Invalid {
            message: "Project đã đóng khi terminal init-kit đang khởi động".to_string(),
        });
    }
    start_reader(&app, session.clone(), reader);

    let command = format!("/init-kit Tên dự án: {}\r", project_name);
    let write_result = {
        let mut writer = session.writer.lock().unwrap();
        writer
            .write_all(command.as_bytes())
            .and_then(|_| writer.flush())
    };
    if let Err(err) = write_result {
        stop_session(&state.init_session);
        return Err(AppError::Invalid {
            message: format!("Không gửi được lệnh /init-kit vào terminal: {err}"),
        });
    }

    Ok(InitKitSessionInfo {
        session_id: session.id.clone(),
        project_name,
    })
}

#[tauri::command]
pub fn send_init_kit_input(
    state: State<AppState>,
    session_id: String,
    data: String,
) -> AppResult<()> {
    let session = state
        .init_session
        .lock()
        .unwrap()
        .clone()
        .filter(|session| session.id == session_id)
        .ok_or_else(|| AppError::Invalid {
            message: "Phiên init-kit không còn hoạt động".to_string(),
        })?;
    let mut writer = session.writer.lock().unwrap();
    writer.write_all(data.as_bytes())?;
    writer.flush()?;
    Ok(())
}

#[tauri::command]
pub fn resize_init_kit(
    state: State<AppState>,
    session_id: String,
    cols: u16,
    rows: u16,
) -> AppResult<()> {
    if cols == 0 || rows == 0 || cols > 500 || rows > 200 {
        return Err(AppError::Invalid {
            message: "Kích thước terminal không hợp lệ".to_string(),
        });
    }
    let session = state
        .init_session
        .lock()
        .unwrap()
        .clone()
        .filter(|session| session.id == session_id)
        .ok_or_else(|| AppError::Invalid {
            message: "Phiên init-kit không còn hoạt động".to_string(),
        })?;
    let result = session
        .master
        .lock()
        .unwrap()
        .resize(PtySize {
            rows,
            cols,
            pixel_width: 0,
            pixel_height: 0,
        })
        .map_err(|err| AppError::Invalid {
            message: format!("Không đổi được kích thước terminal: {err}"),
        });
    result
}

#[tauri::command]
pub fn stop_init_kit(state: State<AppState>, session_id: String) -> AppResult<()> {
    let active_id = state
        .init_session
        .lock()
        .unwrap()
        .as_ref()
        .map(|session| session.id.clone());
    if active_id.as_deref() != Some(session_id.as_str()) {
        return Err(AppError::Invalid {
            message: "Phiên init-kit không còn hoạt động".to_string(),
        });
    }
    stop_session(&state.init_session);
    Ok(())
}
