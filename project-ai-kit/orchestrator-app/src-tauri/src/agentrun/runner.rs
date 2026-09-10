//! Ties `spawn`, `stream_parser`, and `process_registry` together: spawns
//! one agent run, reads its stdout line-by-line as it arrives, parses each
//! line, and streams a `StreamEvent` per line over a channel in realtime
//! (AC-E2-07 — "không phải chờ agent kết thúc mới thấy").
//!
//! [`run_and_stream`] takes an `mpsc::Sender` instead of an `AppHandle`
//! directly, deliberately — it has no Tauri dependency, so it can be
//! exercised in a plain `#[test]` against the real `claude` CLI without a
//! running app. [`spawn_event_forwarder`] is the glue that forwards a
//! channel's events to `app.emit`, used by `commands::agentrun::start_run`
//! and `send_clarification_answer`.

use std::fs::File;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, ChildStderr, ChildStdout};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{Receiver, Sender};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use tauri::{AppHandle, Emitter};

use crate::agentrun::process_group::{self, Signal};
use crate::agentrun::process_registry::{ProcessRegistry, RunKey};
use crate::agentrun::spawn::{build_command, SpawnParams};
use crate::agentrun::stream_parser::{parse_line, StreamEvent};
use crate::domain::running_marker::RunningMarker;
use crate::error::{AppError, AppResult};
use crate::store::atomic_write::write_json_atomic;

pub const EVENT_LOG_LINE: &str = "agentrun://log-line";

/// Thời gian chờ stdout đóng nốt SAU KHI tiến trình đã thoát. Hết hạn thì
/// đi tiếp với những gì đã đọc được — thà log thiếu vài dòng cuối còn hơn
/// treo cả console và không bao giờ báo run kết thúc.
const READER_GRACE: Duration = Duration::from_secs(3);

// AC-E2-10's 30-minute default now lives in
// `config_file::DEFAULT_TIMEOUT_MINUTES` — the actual timeout is read from
// each agent's `AgentConfig.timeout_minutes` per spawn (AC-E6-21).

#[derive(Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
struct LogLinePayload {
    feature: String,
    slot: String,
    event: StreamEvent,
}

/// `run_and_stream`'s outcome — deliberately does NOT interpret the exit
/// status into done/failed/waiting-input; that classification belongs to
/// `agentrun::run_log` (T2.3), which needs feature-dir/artifact context
/// this module has no reason to know about.
#[derive(Debug)]
pub struct RunResult {
    pub events: Vec<StreamEvent>,
    /// Raw `stream-json` lines, in order — the FALLBACK copy, only
    /// populated when no live log file could be opened (see
    /// `log_already_on_disk`). Keeping every line here unconditionally made
    /// peak memory scale with the run: an agent that writes a few large
    /// files produces a log held once in this Vec and again in the single
    /// `String` the old `finalize_run` joined it into.
    pub raw_lines: Vec<String>,
    /// The live log file received every line as it arrived, so the run's
    /// log is already complete on disk and `finalize_run` has nothing left
    /// to write. `false` means the file could not be opened (no durability
    /// configured, or the open failed) and `raw_lines` is the only copy.
    pub log_already_on_disk: bool,
    /// The process was killed for exceeding `timeout` rather than exiting
    /// on its own (AC-E2-10).
    pub timed_out: bool,
    /// The child's exit code, when it exited on its own (`None` if it was
    /// killed for a timeout, or the OS never reports one). AC-E6-27 —
    /// distinguishing a startup failure from a mid-run crash needs more
    /// signal than "no `result` line", and this is part of it.
    pub exit_code: Option<i32>,
    /// Everything the process wrote to stderr, captured whether or not it
    /// ever produced a single `stream-json` line — AC-E6-27's main signal
    /// for a startup failure (bad model, missing permission), since a
    /// process that never got a session going has no `stream-json` content
    /// to explain why.
    pub stderr: String,
    /// `false` khi stdout chưa kịp EOF trong cửa sổ ân hạn — tức còn tiến
    /// trình khác (MCP server) giữ pipe. Người gọi dùng nó để biết
    /// `event_tx` vẫn còn sống trong thread bị bỏ mặc, nên KHÔNG được
    /// `join()` forwarder.
    pub stdout_drained: bool,
}

/// What happened when `run_and_stream` tried to register its spawned child.
/// `AbortedProjectClosed` means the project closed (`AppState::close`
/// bumped `spawn_admission`) between this run's caller capturing its
/// `expected_epoch` and the child landing in `ProcessRegistry` — the child
/// was already killed before this variant is returned, so the caller never
/// needs to touch it again.
#[derive(Debug)]
pub enum SpawnOutcome {
    Ran(RunResult),
    AbortedProjectClosed,
}

/// Crash-durability hooks for one run (AC-E6-04/07/10) — `None` keeps
/// `run_and_stream` pure for tests. With it, the child's PID lands in
/// `marker_path` right after spawn (orphan detection) and every raw stdout
/// line is appended to `log_path` as it arrives, so a run cut short by the
/// app dying still leaves its log behind.
pub struct RunDurability {
    pub marker_path: PathBuf,
    /// The marker already written (pid `None`) by the caller pre-spawn —
    /// rewritten here with the real PID so the caller needs no read-back.
    pub marker: RunningMarker,
    pub log_path: PathBuf,
}

/// Blocking — spawns the process, registers it in `registry` (so Kill can
/// find it), drains stdout on a background thread (sending one event per
/// parsed `StreamEvent` to `event_tx` as lines arrive, and stderr on
/// another so neither pipe can fill up and block the child — the same
/// class of bug the T2.1 spike test guards against for stdout), and
/// returns once the process exits or `timeout` elapses, whichever first.
///
/// `admission`/`expected_epoch` close the TOCTOU between `AppState::close`
/// and this spawn: registration only happens via
/// `ProcessRegistry::insert_if_current`, which refuses (and this function
/// kills the child it just spawned) if the project closed after the caller
/// captured `expected_epoch` — see that method's doc comment for the
/// ordering argument.
#[allow(clippy::too_many_arguments)]
pub fn run_and_stream(
    registry: &ProcessRegistry,
    key: RunKey,
    params: &SpawnParams,
    event_tx: Sender<StreamEvent>,
    timeout: Duration,
    durability: Option<RunDurability>,
    admission: &Mutex<u64>,
    expected_epoch: u64,
) -> AppResult<SpawnOutcome> {
    let mut cmd = build_command(params);
    let mut child = cmd.spawn()?;

    let stdout = child.stdout.take().ok_or_else(|| AppError::Invalid {
        message: "spawned claude process has no stdout pipe".to_string(),
    })?;
    let stderr = child.stderr.take();

    // AC-E6-10 — the PID must be on disk before anything else happens: an
    // app crash from here on leaves enough to find (or rule out) an orphan.
    // AC-E6-07 — the log file is opened append-mode and flushed per line.
    // This is the ONE deliberate exception to the `write_text_atomic`-only
    // store convention: rewriting the whole log atomically per line would
    // be O(n²) I/O, and `run_log::parse_line` already tolerates a torn
    // final line. `finalize_run` still writes the full log atomically at
    // the end, normalizing whatever this left behind.
    let live_log = durability.and_then(|d| {
        let marker = RunningMarker {
            pid: Some(child.id()),
            ..d.marker
        };
        let _ = write_json_atomic(&d.marker_path, &marker);
        std::fs::OpenOptions::new()
            .create(true)
            .write(true)
            .truncate(true)
            .open(&d.log_path)
            .ok()
    });

    let child = Arc::new(Mutex::new(child));
    if !registry.insert_if_current(admission, expected_epoch, key.clone(), child.clone()) {
        // The project closed while this run was still doing pre-spawn I/O.
        // The child exists but was never tracked — kill it directly with
        // the registry's own group-then-process pattern (`ProcessRegistry::
        // kill` does the same two steps) since it was never inserted for
        // `ProcessRegistry::kill` to find.
        let mut guard = child.lock().unwrap();
        process_group::signal_group(guard.id(), Signal::Kill);
        let _ = guard.kill();
        drop(guard);
        return Ok(SpawnOutcome::AbortedProjectClosed);
    }

    let result = stream_child_output(
        &child,
        stdout,
        stderr,
        event_tx,
        timeout,
        READER_GRACE,
        live_log,
    );
    registry.remove(&key);
    result.map(SpawnOutcome::Ran)
}

/// Những gì thread đọc stdout đã góp được cho tới lúc này.
///
/// Cố ý là bộ đệm CHIA SẺ chứ không phải giá trị trả về của thread: nếu
/// chờ hết hạn mà vẫn phải `join()` mới lấy được dữ liệu thì coi như mất
/// sạch event, và `finalize_run` sẽ phân loại một run thành công thành
/// `failed`. Chia sẻ thì lấy được mọi thứ đã nhận, gồm cả event `result`.
#[derive(Default)]
struct Collected {
    events: Vec<StreamEvent>,
    raw_lines: Vec<String>,
}

/// Chờ `flag` bật, tối đa tới `deadline`. `true` = kịp, `false` = hết hạn.
fn wait_for(flag: &AtomicBool, deadline: Instant) -> bool {
    while !flag.load(Ordering::SeqCst) {
        if Instant::now() >= deadline {
            return false;
        }
        std::thread::sleep(Duration::from_millis(20));
    }
    true
}

/// Phần lõi của `run_and_stream`, tách ra vì nó nhận `Child` đã spawn nên
/// test bơm được tiến trình bất kỳ (`run_and_stream` luôn dựng lệnh
/// `claude` từ `SpawnParams`).
fn stream_child_output(
    child: &Arc<Mutex<Child>>,
    stdout: ChildStdout,
    stderr: Option<ChildStderr>,
    event_tx: Sender<StreamEvent>,
    timeout: Duration,
    reader_grace: Duration,
    mut live_log: Option<File>,
) -> AppResult<RunResult> {
    let log_already_on_disk = live_log.is_some();
    let collected = Arc::new(Mutex::new(Collected::default()));
    let reader_done = Arc::new(AtomicBool::new(false));
    {
        let collected = collected.clone();
        let reader_done = reader_done.clone();
        std::thread::spawn(move || {
            for line in BufReader::new(stdout).lines() {
                let Ok(line) = line else { break };
                if !line.trim().is_empty() {
                    match live_log.as_mut() {
                        // Already durable per line: keeping a second copy in
                        // memory buys nothing and costs the whole log.
                        Some(file) => {
                            let _ = writeln!(file, "{line}");
                            let _ = file.flush();
                        }
                        None => collected.lock().unwrap().raw_lines.push(line.clone()),
                    }
                }
                for event in parse_line(&line) {
                    let _ = event_tx.send(event.clone());
                    collected.lock().unwrap().events.push(event);
                }
            }
            reader_done.store(true, Ordering::SeqCst);
        });
    }

    let stderr_buf = Arc::new(Mutex::new(String::new()));
    // Không có stderr thì coi như đã xong ngay.
    let stderr_done = Arc::new(AtomicBool::new(stderr.is_none()));
    if let Some(stderr) = stderr {
        let stderr_buf = stderr_buf.clone();
        let stderr_done = stderr_done.clone();
        std::thread::spawn(move || {
            use std::io::Read;
            let mut buf = String::new();
            let _ = BufReader::new(stderr).read_to_string(&mut buf);
            *stderr_buf.lock().unwrap() = buf;
            stderr_done.store(true, Ordering::SeqCst);
        });
    }

    // Polls rather than a blocking `wait()` so the lock is only held
    // momentarily each iteration — a blocking `wait()` would hold the
    // Mutex for the entire run and deadlock against a concurrent Kill,
    // which needs the same lock to call `Child::kill`.
    // PGID bằng PID của tiến trình con (`build_command` gọi
    // `process_group(0)`). Lấy trước vòng chờ, khi con chắc chắn chưa bị
    // thu hoạch.
    let pgid = child.lock().unwrap().id();

    let start = Instant::now();
    let mut timed_out = false;
    let mut exit_status = None;
    loop {
        if let Some(status) = child.lock().unwrap().try_wait()? {
            exit_status = Some(status);
            break;
        }
        if start.elapsed() >= timeout {
            // Cả nhóm, không riêng CLI: hết giờ mà chỉ giết tiến trình cha
            // thì MCP server con vẫn sống và vẫn giữ pipe.
            process_group::signal_group(pgid, Signal::Kill);
            let _ = child.lock().unwrap().kill();
            timed_out = true;
            break;
        }
        std::thread::sleep(Duration::from_millis(100));
    }

    // Tiến trình đã thoát, nhưng stdout chỉ EOF khi MỌI tiến trình giữ đầu
    // ghi đóng lại — MCP server do CLI sinh ra thừa kế pipe này và có thể
    // sống lâu hơn nó. `join()` vô hạn ở đây từng làm console treo vĩnh
    // viễn: không ai emit nổi sự kiện kết thúc.
    //
    // Kết thúc cả nhóm TRƯỚC rồi mới chờ: MCP server chết thì pipe đóng
    // gần như tức thì, nên đường thường vẫn drain sạch (`stdout_drained`
    // giữ nguyên `true`) và người gọi vẫn join được forwarder như cũ. Chờ
    // có hạn chỉ còn là lưới an toàn cho tiến trình phớt lờ cả SIGKILL.
    process_group::signal_group(pgid, Signal::Terminate);

    let mut stdout_drained = wait_for(&reader_done, Instant::now() + reader_grace);
    if !stdout_drained {
        process_group::signal_group(pgid, Signal::Kill);
        stdout_drained = wait_for(&reader_done, Instant::now() + reader_grace);
    }
    let _ = wait_for(&stderr_done, Instant::now() + reader_grace);

    let Collected { events, raw_lines } = std::mem::take(&mut *collected.lock().unwrap());
    let stderr = stderr_buf.lock().unwrap().clone();

    Ok(RunResult {
        events,
        raw_lines,
        log_already_on_disk,
        timed_out,
        exit_code: exit_status.and_then(|s| s.code()),
        stderr,
        stdout_drained,
    })
}

/// Forwards every event received on `rx` to `agentrun://log-line` until the
/// sender is dropped (i.e. the run in `run_and_stream` finished). Runs on
/// its own thread so the caller can start it before or concurrently with
/// `run_and_stream` without blocking either side.
pub fn spawn_event_forwarder(
    app: AppHandle,
    feature: String,
    slot: String,
    rx: Receiver<StreamEvent>,
) -> std::thread::JoinHandle<()> {
    std::thread::spawn(move || {
        for event in rx {
            let _ = app.emit(
                EVENT_LOG_LINE,
                LogLinePayload {
                    feature: feature.clone(),
                    slot: slot.clone(),
                    event,
                },
            );
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::agentrun::spawn::is_claude_cli_available;
    use crate::domain::config_file::{AgentConfig, Model, PermissionProfile};

    /// Dựng một tiến trình rồi đưa thẳng vào lõi `stream_child_output` —
    /// `run_and_stream` luôn dựng lệnh `claude` nên không nhét được lệnh
    /// giả vào.
    fn stream(script: &str, grace: Duration) -> RunResult {
        stream_with(script, grace, false)
    }

    /// `own_group = true` mô phỏng đúng cách `build_command` spawn agent
    /// thật (`process_group(0)`); `false` giữ tiến trình trong nhóm của
    /// test runner, tức nhóm KHÔNG diệt được.
    fn stream_with(script: &str, grace: Duration, own_group: bool) -> RunResult {
        let mut cmd = std::process::Command::new("sh");
        cmd.arg("-c")
            .arg(script)
            .stdin(std::process::Stdio::null())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped());
        #[cfg(unix)]
        if own_group {
            use std::os::unix::process::CommandExt;
            cmd.process_group(0);
        }
        let mut child = cmd.spawn().unwrap();
        let stdout = child.stdout.take().unwrap();
        let stderr = child.stderr.take();
        let (tx, _rx) = std::sync::mpsc::channel();

        stream_child_output(
            &Arc::new(Mutex::new(child)),
            stdout,
            stderr,
            tx,
            Duration::from_secs(60),
            grace,
            None,
        )
        .unwrap()
    }

    /// Cùng kịch bản treo, nhưng tiến trình nằm trong process group riêng
    /// đúng như agent thật. Kết thúc nhóm phải giết luôn `sleep 30`, pipe
    /// đóng, và run drain sạch — tức MCP server không còn tồn đọng sau khi
    /// run xong.
    #[cfg(unix)]
    #[test]
    fn killing_the_process_group_reaps_a_grandchild_that_would_hold_stdout() {
        let start = Instant::now();
        let result = stream_with(
            "sleep 30 & echo hello; exit 0",
            Duration::from_secs(5),
            true,
        );

        assert!(
            result.stdout_drained,
            "cháu đã bị nhóm giết nên stdout phải EOF trong cửa sổ ân hạn"
        );
        assert!(
            start.elapsed() < Duration::from_secs(5),
            "không được chờ hết ân hạn: nhóm chết thì pipe đóng gần như tức thì"
        );
        assert!(result.raw_lines.iter().any(|line| line == "hello"));
    }

    /// Đúng lỗi đã gặp: Claude CLI thoát nhưng MCP server con thừa kế
    /// stdout và còn sống, nên pipe không bao giờ EOF. `sleep 30 &` mô
    /// phỏng chính xác vai trò đó.
    ///
    /// Trước khi sửa, `reader.join()` treo tới khi `sleep` kết thúc — kéo
    /// theo console run agent không bao giờ tắt.
    #[test]
    fn a_lingering_grandchild_holding_stdout_does_not_hang_the_run() {
        let grace = Duration::from_millis(300);
        let start = Instant::now();
        let result = stream("sleep 30 & echo hello; exit 0", grace);
        let elapsed = start.elapsed();

        assert!(
            elapsed < Duration::from_secs(5),
            "phải trả về trong cửa sổ ân hạn, thực tế mất {elapsed:?}"
        );
        assert!(
            !result.stdout_drained,
            "pipe vẫn bị cháu giữ nên không thể coi là đã đóng sạch"
        );
        assert!(
            result.raw_lines.iter().any(|line| line == "hello"),
            "dữ liệu nhận trước khi hết hạn không được mất: {:?}",
            result.raw_lines
        );
    }

    /// Đường thường không được đổi hành vi: thoát sạch thì vẫn đọc hết.
    #[test]
    fn a_clean_exit_still_drains_stdout_fully() {
        let result = stream("echo one; echo two", Duration::from_secs(5));

        assert!(result.stdout_drained);
        assert_eq!(result.raw_lines, vec!["one".to_string(), "two".to_string()]);
        assert_eq!(result.exit_code, Some(0));
    }

    /// Real end-to-end run through the whole `agentrun` stack built so far:
    /// spawn -> registry -> stdout drained line-by-line -> parsed -> sent
    /// over the channel in realtime -> collected. Cheap (haiku, no tools,
    /// trivial prompt), consistent with the cost posture agreed for MVP2.
    #[test]
    fn run_and_stream_emits_session_started_and_run_finished_for_a_real_call() {
        if !is_claude_cli_available() {
            eprintln!("skipping live spike: `claude` CLI not usable in this environment");
            return;
        }

        let registry = ProcessRegistry::default();
        let key = RunKey {
            feature: "test-feature".to_string(),
            slot: "ba".to_string(),
        };
        let cfg = AgentConfig {
            model: Model::Haiku,
            max_turns: 20,
            timeout_minutes: 30,
            permission: PermissionProfile::ReadOnly,
            stale: false,
            newly_discovered: false,
        };
        let tmp = crate::agentrun::test_support::agent_project_dir("test-agent");
        // No tools, trivial prompt — a fraction of a cent, no budget cap
        // needed (unlike T2.1's spike, which used a Write tool call).
        let params = SpawnParams {
            agent_name: "test-agent",
            prompt: "Reply with exactly the word: pong",
            cwd: tmp.path(),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: crate::agentrun::spawn::SpawnAuth::CliDefault,
            allowed_tools: &[],
        };
        let (tx, rx) = std::sync::mpsc::channel();

        // AC-E6-07/10 — durability: PID lands in the marker at spawn, every
        // raw line is on disk before the run even returns (deleting the
        // marker afterwards is `finalize_run`'s job, not this function's).
        let marker_path = tmp.path().join("running.json");
        let log_path = tmp.path().join("log.jsonl");
        let durability = RunDurability {
            marker_path: marker_path.clone(),
            marker: crate::domain::running_marker::RunningMarker {
                pid: None,
                started_at: "2026-08-17T00:00:00Z".to_string(),
                attempt: 1,
                prompt: Some("Reply with exactly the word: pong".to_string()),
            },
            log_path: log_path.clone(),
        };

        let admission = Mutex::new(0u64);
        let result = match run_and_stream(
            &registry,
            key.clone(),
            &params,
            tx,
            Duration::from_secs(60),
            Some(durability),
            &admission,
            0,
        )
        .unwrap()
        {
            SpawnOutcome::Ran(result) => result,
            SpawnOutcome::AbortedProjectClosed => panic!("admission epoch matches — must run"),
        };

        // Nothing left registered once the run is over.
        assert!(registry.get(&key).is_none());
        assert!(!result.timed_out);

        let marker: crate::domain::running_marker::RunningMarker =
            serde_json::from_str(&std::fs::read_to_string(&marker_path).unwrap()).unwrap();
        assert!(marker.pid.is_some());

        // Durability was configured, so the log is complete on disk and the
        // in-memory copy is deliberately NOT kept — holding both made peak
        // memory scale with the run. `finalize_run` reads the flag to know
        // it has nothing left to write.
        let log_on_disk = std::fs::read_to_string(&log_path).unwrap();
        assert!(result.log_already_on_disk);
        assert!(
            result.raw_lines.is_empty(),
            "lines must not be buffered twice when the live log has them"
        );
        assert!(
            !log_on_disk.trim().is_empty(),
            "the live log is now the ONLY copy — it must actually have the run in it"
        );
        // The file is a faithful record of what was streamed: re-parsing it
        // yields the same events. Compared by count, not line count — one
        // raw line can carry several content blocks and so several events.
        let reparsed: Vec<StreamEvent> = log_on_disk
            .lines()
            .filter(|line| !line.trim().is_empty())
            .flat_map(parse_line)
            .collect();
        assert_eq!(reparsed.len(), result.events.len());

        assert!(result
            .events
            .iter()
            .any(|e| matches!(e, StreamEvent::SessionStarted { .. })));
        assert!(result
            .events
            .iter()
            .any(|e| matches!(e, StreamEvent::RunFinished { .. })));

        // Everything sent over the channel must also be in the returned
        // history, in the same order — the channel is the realtime path,
        // the return value is the durable one, they must agree.
        let forwarded: Vec<StreamEvent> = rx.try_iter().collect();
        assert_eq!(forwarded, result.events);
    }

    /// A process that never exits on its own gets killed once `timeout`
    /// elapses, rather than hanging `run_and_stream` forever — the actual
    /// mechanism AC-E2-10 depends on. Exercises `run_and_stream`'s own
    /// timeout branch directly (not a reimplementation): a real `claude`
    /// call with a timeout far shorter than any real response can arrive
    /// in gets killed before it can do meaningful work, so cost is
    /// negligible-to-zero regardless of model.
    #[test]
    fn timeout_kills_a_process_that_never_exits_in_time() {
        if !is_claude_cli_available() {
            eprintln!("skipping live spike: `claude` CLI not usable in this environment");
            return;
        }

        let registry = ProcessRegistry::default();
        let key = RunKey {
            feature: "test-feature".to_string(),
            slot: "ba".to_string(),
        };
        let cfg = AgentConfig {
            model: Model::Haiku,
            max_turns: 20,
            timeout_minutes: 30,
            permission: PermissionProfile::ReadOnly,
            stale: false,
            newly_discovered: false,
        };
        let tmp = crate::agentrun::test_support::agent_project_dir("test-agent");
        let params = SpawnParams {
            agent_name: "test-agent",
            prompt: "Reply with exactly the word: pong",
            cwd: tmp.path(),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: crate::agentrun::spawn::SpawnAuth::CliDefault,
            allowed_tools: &[],
        };
        let (tx, _rx) = std::sync::mpsc::channel();

        let admission = Mutex::new(0u64);
        let result = match run_and_stream(
            &registry,
            key.clone(),
            &params,
            tx,
            Duration::from_millis(1),
            None,
            &admission,
            0,
        )
        .unwrap()
        {
            SpawnOutcome::Ran(result) => result,
            SpawnOutcome::AbortedProjectClosed => panic!("admission epoch matches — must run"),
        };

        assert!(result.timed_out);
        assert!(registry.get(&key).is_none());
    }

    #[test]
    fn run_and_stream_aborts_and_kills_the_child_when_the_epoch_is_stale() {
        if !is_claude_cli_available() {
            eprintln!("skipping live spike: `claude` CLI not usable in this environment");
            return;
        }

        let registry = ProcessRegistry::default();
        let key = RunKey {
            feature: "test-feature".to_string(),
            slot: "ba".to_string(),
        };
        let cfg = AgentConfig {
            model: Model::Haiku,
            max_turns: 20,
            timeout_minutes: 30,
            permission: PermissionProfile::ReadOnly,
            stale: false,
            newly_discovered: false,
        };
        let tmp = crate::agentrun::test_support::agent_project_dir("test-agent");
        let params = SpawnParams {
            agent_name: "test-agent",
            prompt: "Reply with exactly the word: pong",
            cwd: tmp.path(),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: crate::agentrun::spawn::SpawnAuth::CliDefault,
            allowed_tools: &[],
        };
        let (tx, _rx) = std::sync::mpsc::channel();

        // Simulates `AppState::close` having bumped the epoch after this
        // caller captured `expected_epoch = 0`.
        let admission = Mutex::new(1u64);
        let outcome = run_and_stream(
            &registry,
            key.clone(),
            &params,
            tx,
            Duration::from_secs(60),
            None,
            &admission,
            0,
        )
        .unwrap();

        assert!(matches!(outcome, SpawnOutcome::AbortedProjectClosed));
        assert!(registry.get(&key).is_none());
    }
}
