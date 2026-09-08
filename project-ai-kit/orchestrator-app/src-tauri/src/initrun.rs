//! Interactive Claude session for the in-app project setup flow.
//!
//! Pipeline agents intentionally run headlessly through `agentrun`. `/init-kit`
//! is different: the canonical init agent must ask the user questions, so it
//! needs a real PTY and raw terminal input/output.

use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

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
    /// When the PTY last produced output, and whether it ever has. Together
    /// they say "Claude has drawn a screen and stopped drawing" — the only
    /// moment it is safe to type into the TUI. See `send_command_when_ready`.
    saw_output: AtomicBool,
    last_output_at: Mutex<Instant>,
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

/// Guarantees the child sees a UTF-8 locale.
///
/// `CommandBuilder::new` seeds the child environment from this process's own,
/// and a macOS `.app` launched from Finder inherits launchd's environment —
/// which has no `LANG` at all (`launchctl getenv LANG` is empty), unlike the
/// login shell that `pnpm tauri dev` runs under. Anything under this PTY that
/// consults the locale would therefore behave one way in development and
/// another in the installed build.
///
/// An existing UTF-8 locale is left alone: a user whose `LANG` is
/// `ja_JP.UTF-8` should keep it. `LC_ALL` is deliberately not set — it
/// overrides every category and is far heavier than this needs to be.
fn ensure_utf8_locale(command: &mut CommandBuilder) {
    let already_utf8 = std::env::var("LC_ALL")
        .or_else(|_| std::env::var("LANG"))
        .is_ok_and(|value| value.to_ascii_uppercase().contains("UTF-8"));
    if !already_utf8 {
        command.env("LANG", "en_US.UTF-8");
    }
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

/// How many trailing bytes of `buf` begin a UTF-8 character whose remaining
/// bytes have not arrived yet — at most 3, since no character is longer than
/// 4 bytes. `0` when the buffer ends on a character boundary, and also `0`
/// for bytes that can never become valid: those must be handed to the lossy
/// decode now rather than held back forever waiting for a continuation that
/// is never coming.
fn incomplete_tail_len(buf: &[u8]) -> usize {
    for back in 1..=buf.len().min(3) {
        let byte = buf[buf.len() - back];
        if byte < 0x80 {
            return 0;
        }
        if byte & 0b1100_0000 == 0b1000_0000 {
            continue;
        }
        let needed = if byte & 0b1110_0000 == 0b1100_0000 {
            2
        } else if byte & 0b1111_0000 == 0b1110_0000 {
            3
        } else if byte & 0b1111_1000 == 0b1111_0000 {
            4
        } else {
            return 0;
        };
        return if back < needed { back } else { 0 };
    }
    0
}

/// Takes everything in `pending` that forms whole characters, leaving a
/// split character's leading bytes behind for the next read to complete.
///
/// A PTY read boundary falls wherever the kernel put it, and a redrawing TUI
/// fills the 8 KiB buffer often enough that landing mid-character is routine.
/// Decoding each read on its own turned the two halves of `ế` (`E1 BA BF`)
/// into two U+FFFD, permanently — Vietnamese output came back as `<?>` even
/// though the bytes were intact.
fn take_decodable(pending: &mut Vec<u8>) -> String {
    let split = pending.len() - incomplete_tail_len(pending);
    let whole: Vec<u8> = pending.drain(..split).collect();
    String::from_utf8_lossy(&whole).into_owned()
}

fn start_reader(app: &AppHandle, session: Arc<InitKitSession>, mut reader: Box<dyn Read + Send>) {
    let app = app.clone();
    let session_id = session.id.clone();
    std::thread::spawn(move || {
        let mut buffer = [0_u8; 8192];
        let mut pending: Vec<u8> = Vec::new();
        loop {
            match reader.read(&mut buffer) {
                Ok(0) => break,
                Ok(count) => {
                    session.saw_output.store(true, Ordering::SeqCst);
                    *session.last_output_at.lock().unwrap() = Instant::now();
                    pending.extend_from_slice(&buffer[..count]);
                    let data = take_decodable(&mut pending);
                    // The whole read was the front of a split character —
                    // nothing to draw yet, and emitting "" would only make
                    // the frontend re-render for no reason.
                    if data.is_empty() {
                        continue;
                    }
                    let _ = app.emit(
                        EVENT_OUTPUT,
                        InitKitOutputPayload {
                            session_id: session_id.clone(),
                            data,
                        },
                    );
                }
                Err(_) => break,
            }
        }
        // Whatever is still held back can never be completed now, but it is
        // real output — show it rather than dropping it silently.
        if !pending.is_empty() {
            let _ = app.emit(
                EVENT_OUTPUT,
                InitKitOutputPayload {
                    session_id: session_id.clone(),
                    data: String::from_utf8_lossy(&pending).into_owned(),
                },
            );
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

/// Whether Claude has already been told this folder is trusted.
///
/// Claude records the answer to its "Quick safety check" prompt as
/// `projects.<cwd>.hasTrustDialogAccepted` in `~/.claude.json`, and writes it
/// the moment the user answers. Reading it is how we know the prompt is no
/// longer sitting in front of the TUI. Anything we cannot read or parse counts
/// as not trusted: waiting costs the user a hint after the deadline, whereas
/// guessing "trusted" types into the prompt and kills the session.
fn folder_trusted(agents_root: &Path) -> bool {
    let Some(home) = cli_path::home_dir() else {
        return false;
    };
    let Ok(raw) = std::fs::read_to_string(home.join(".claude.json")) else {
        return false;
    };
    let Ok(config) = serde_json::from_str::<serde_json::Value>(&raw) else {
        return false;
    };
    let Some(projects) = config.get("projects").and_then(|value| value.as_object()) else {
        return false;
    };
    let canonical = std::fs::canonicalize(agents_root).ok();
    projects.iter().any(|(key, entry)| {
        let key_path = Path::new(key);
        let same_folder = key_path == agents_root
            || canonical.as_deref() == Some(key_path)
            || (canonical.is_some() && std::fs::canonicalize(key_path).ok() == canonical);
        same_folder
            && entry
                .get("hasTrustDialogAccepted")
                .and_then(serde_json::Value::as_bool)
                .unwrap_or(false)
    })
}

/// Types `/init-kit` into the TUI once Claude is actually ready to receive it.
///
/// Writing it straight after spawn is what broke this flow: in a folder Claude
/// has not been trusted with — which a freshly created project always is — the
/// first screen is the trust prompt, whose highlighted default is "No, exit".
/// The `\r` ending the command confirms that default, so Claude exits before
/// the user can type anything and every later keystroke fails with "phiên
/// init-kit không còn hoạt động".
///
/// So wait for two things: the folder is trusted (the prompt has been answered,
/// or never appeared), and the PTY has drawn something and then gone quiet for
/// `SETTLE` (the TUI has finished painting its input box). If neither happens
/// before `DEADLINE`, say so in the terminal and let the user type the command
/// themselves rather than firing it blindly.
fn send_command_when_ready(
    app: &AppHandle,
    session: Arc<InitKitSession>,
    agents_root: PathBuf,
    command: String,
) {
    const DEADLINE: Duration = Duration::from_secs(120);
    const SETTLE: Duration = Duration::from_millis(1200);
    const POLL: Duration = Duration::from_millis(200);

    let app = app.clone();
    std::thread::spawn(move || {
        let started = Instant::now();
        loop {
            if session.stopped.load(Ordering::SeqCst) {
                return;
            }
            let settled = session.saw_output.load(Ordering::SeqCst)
                && session.last_output_at.lock().unwrap().elapsed() >= SETTLE;
            if settled && folder_trusted(&agents_root) {
                break;
            }
            if started.elapsed() >= DEADLINE {
                let _ = app.emit(
                    EVENT_OUTPUT,
                    InitKitOutputPayload {
                        session_id: session.id.clone(),
                        data: "\r\n\x1b[33m[app] Chưa gửi được /init-kit tự động \
                               (Claude chưa sẵn sàng hoặc thư mục chưa được trust). \
                               Bạn hãy tự gõ lệnh /init-kit trong terminal này.\x1b[0m\r\n"
                            .to_string(),
                    },
                );
                return;
            }
            std::thread::sleep(POLL);
        }

        let mut writer = session.writer.lock().unwrap();
        let _ = writer
            .write_all(command.as_bytes())
            .and_then(|_| writer.flush());
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
    ensure_utf8_locale(&mut command);
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
        saw_output: AtomicBool::new(false),
        last_output_at: Mutex::new(Instant::now()),
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
    send_command_when_ready(
        &app,
        session.clone(),
        agents_root,
        format!("/init-kit Tên dự án: {project_name}\r"),
    );

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

#[cfg(test)]
mod tests {
    use super::*;

    /// The bug this guards: a PTY read that ends between the bytes of a
    /// Vietnamese character used to produce U+FFFD on both sides of the
    /// boundary, so typed and echoed accents came back as `<?>`.
    #[test]
    fn a_character_split_across_two_reads_is_rejoined_intact() {
        let bytes = "ế".as_bytes();
        assert_eq!(bytes.len(), 3, "sanity: ế is a 3-byte character");

        let mut pending = Vec::new();
        pending.extend_from_slice(&bytes[..2]);
        assert_eq!(
            take_decodable(&mut pending),
            "",
            "an incomplete character must be held back, not replaced"
        );

        pending.extend_from_slice(&bytes[2..]);
        assert_eq!(take_decodable(&mut pending), "ế");
        assert!(pending.is_empty());
    }

    /// Only the split character waits — everything before it is drawn now,
    /// or the terminal would stutter a whole frame behind.
    #[test]
    fn whole_characters_before_a_split_one_are_emitted_immediately() {
        let mut pending = Vec::new();
        pending.extend_from_slice("Tên dự á".as_bytes());
        pending.extend_from_slice(&"ế".as_bytes()[..1]);

        assert_eq!(take_decodable(&mut pending), "Tên dự á");
        assert_eq!(pending.len(), 1, "the lone lead byte stays behind");
    }

    #[test]
    fn ascii_and_complete_multibyte_pass_straight_through() {
        let mut pending = Vec::new();
        pending.extend_from_slice("/init-kit Tên dự án: x\r".as_bytes());
        assert_eq!(take_decodable(&mut pending), "/init-kit Tên dự án: x\r");
        assert!(pending.is_empty());
    }

    /// Bytes that can never start a valid character must not be held back, or
    /// the reader would stall forever waiting for a continuation that is not
    /// coming — better one U+FFFD than a frozen terminal.
    #[test]
    fn invalid_bytes_are_not_held_back_forever() {
        let mut pending = vec![0xFF, 0xFE];
        let decoded = take_decodable(&mut pending);
        assert!(!decoded.is_empty());
        assert!(pending.is_empty());
    }

    #[test]
    fn incomplete_tail_len_counts_only_a_genuinely_truncated_character() {
        assert_eq!(incomplete_tail_len("abc".as_bytes()), 0);
        assert_eq!(incomplete_tail_len("ế".as_bytes()), 0);
        assert_eq!(incomplete_tail_len(&"ế".as_bytes()[..1]), 1);
        assert_eq!(incomplete_tail_len(&"ế".as_bytes()[..2]), 2);
        // A lead byte more than 3 back cannot still be waiting: no character
        // is longer than 4 bytes.
        assert_eq!(incomplete_tail_len(&[0xE1, 0xBA, 0xBF, 0x61]), 0);
    }
}
