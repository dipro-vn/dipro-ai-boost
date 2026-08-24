//! Cross-platform process helpers for the recovery path.
//!
//! `ps` and `kill` do not exist on Windows, so the orphan scan (AC-E6-10)
//! silently reported "no live process" there and its Kill action did
//! nothing — a run left behind by a crash would keep burning tokens with
//! no way to stop it from the UI. Windows uses `tasklist`/`taskkill`
//! instead.
//!
//! The output parsing is separated from the spawning so the format
//! handling is testable on whichever platform CI happens to run.

use std::process::{Command, Stdio};

/// Windows creates a console window for every child process unless told
/// not to. Without this a packaged app flashes a black window on each
/// `claude`, `tasklist` and `taskkill` spawn — several times per run.
#[cfg(windows)]
pub fn hide_console(cmd: &mut Command) {
    use std::os::windows::process::CommandExt;
    // `CREATE_NO_WINDOW` from winbase.h — the only Win32 constant the app
    // needs, so no crate dependency for it.
    const CREATE_NO_WINDOW: u32 = 0x0800_0000;
    cmd.creation_flags(CREATE_NO_WINDOW);
}

#[cfg(not(windows))]
pub fn hide_console(_cmd: &mut Command) {}

/// `ps -p <pid> -o comm=` prints the command name alone, or nothing when
/// the pid is gone.
fn parse_ps_comm(stdout: &str) -> Option<String> {
    let name = stdout.trim();
    if name.is_empty() {
        return None;
    }
    Some(name.to_lowercase())
}

/// `tasklist /FO CSV /NH` prints one quoted CSV row per match — image name
/// first — and an `INFO:` sentence when nothing matched.
fn parse_tasklist_csv(stdout: &str) -> Option<String> {
    let line = stdout
        .lines()
        .map(str::trim)
        .find(|line| !line.is_empty())?;
    let name = line.strip_prefix('"')?.split('"').next()?;
    if name.is_empty() {
        return None;
    }
    Some(name.to_lowercase())
}

/// The running process's command/image name, lowercased. `None` when the
/// pid is not alive (or the query itself failed, which is treated the same
/// way — refusing to act on an unverifiable pid is the safe direction).
pub fn pid_command_name(pid: u32) -> Option<String> {
    let mut cmd = query_command(pid);
    hide_console(&mut cmd);
    let output = cmd.output().ok()?;
    if !output.status.success() {
        return None;
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    if cfg!(windows) {
        parse_tasklist_csv(&stdout)
    } else {
        parse_ps_comm(&stdout)
    }
}

#[cfg(windows)]
fn query_command(pid: u32) -> Command {
    let mut cmd = Command::new("tasklist");
    cmd.args(["/FI", &format!("PID eq {pid}"), "/FO", "CSV", "/NH"]);
    cmd.stdout(Stdio::piped()).stderr(Stdio::null());
    cmd
}

#[cfg(not(windows))]
fn query_command(pid: u32) -> Command {
    let mut cmd = Command::new("ps");
    cmd.args(["-p", &pid.to_string(), "-o", "comm="]);
    cmd.stdout(Stdio::piped()).stderr(Stdio::null());
    cmd
}

/// Best-effort terminate. `taskkill /T` takes the whole tree because a
/// Windows `claude` is a `.cmd` shim whose real work happens in a child
/// process — killing only the shim would leave the agent running.
pub fn kill_pid(pid: u32) -> bool {
    let mut cmd = kill_command(pid);
    hide_console(&mut cmd);
    cmd.status().map(|status| status.success()).unwrap_or(false)
}

#[cfg(windows)]
fn kill_command(pid: u32) -> Command {
    let mut cmd = Command::new("taskkill");
    cmd.args(["/PID", &pid.to_string(), "/T", "/F"]);
    cmd.stdout(Stdio::null()).stderr(Stdio::null());
    cmd
}

#[cfg(not(windows))]
fn kill_command(pid: u32) -> Command {
    let mut cmd = Command::new("kill");
    cmd.arg(pid.to_string());
    cmd.stdout(Stdio::null()).stderr(Stdio::null());
    cmd
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ps_output_is_the_bare_command_name() {
        assert_eq!(parse_ps_comm("claude\n").as_deref(), Some("claude"));
        assert_eq!(parse_ps_comm("  node  \n").as_deref(), Some("node"));
    }

    #[test]
    fn ps_output_is_empty_for_a_dead_pid() {
        assert_eq!(parse_ps_comm(""), None);
        assert_eq!(parse_ps_comm("   \n"), None);
    }

    #[test]
    fn tasklist_csv_row_yields_the_image_name() {
        let row = "\"claude.exe\",\"4242\",\"Console\",\"1\",\"52,880 K\"\r\n";
        assert_eq!(parse_tasklist_csv(row).as_deref(), Some("claude.exe"));
    }

    /// `tasklist` reports a miss as prose on stdout with a success exit
    /// code — parsing it as a row would invent a live process and let the
    /// Kill action fire at a pid that no longer exists.
    #[test]
    fn tasklist_info_line_is_not_a_process() {
        let miss = "INFO: No tasks are running which match the specified criteria.\r\n";
        assert_eq!(parse_tasklist_csv(miss), None);
        assert_eq!(parse_tasklist_csv(""), None);
    }

    /// Deliberately not pid 0: that is Windows' System Idle Process and
    /// `tasklist` really does report it. `u32::MAX` is above every
    /// allocatable pid on both platforms.
    #[test]
    fn a_pid_that_cannot_exist_is_not_reported_as_running() {
        assert_eq!(pid_command_name(u32::MAX), None);
    }

    #[test]
    fn the_current_process_is_reported_as_running() {
        let name = pid_command_name(std::process::id());
        assert!(name.is_some(), "own pid must resolve to a command name");
    }
}
