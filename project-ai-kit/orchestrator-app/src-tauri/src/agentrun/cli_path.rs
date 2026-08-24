//! Resolves the `claude` binary this app spawns agents with.
//!
//! `Command::new("claude")` only finds the CLI when the app inherits a
//! shell's `PATH`. A macOS `.app` launched from Finder does not: it gets a
//! minimal `/usr/bin:/bin:/usr/sbin:/sbin`, where a CLI installed to
//! `~/.local/bin` (the default) is invisible. Every run would then fail
//! with "không tìm thấy CLI" in a packaged build while working fine under
//! `pnpm tauri dev` — the dev shell's PATH masks the bug entirely.
//!
//! On Windows the same call fails for a second reason: an npm-installed
//! CLI is a `claude.cmd` shim, and `CreateProcess` only ever appends
//! `.exe`. Resolving to a full path with its real extension fixes both.
//!
//! Resolution order — first hit wins:
//!   1. the path the user typed in Settings (`ProjectConfig::claude_cli_path`)
//!   2. `PATH`, honouring `PATHEXT` on Windows
//!   3. the known install locations
//!   4. the user's login shell, asked for its own `PATH` (unix only)
//!
//! Steps 2–4 are cached for the process lifetime: step 4 spawns a shell,
//! and this is on the critical path of every run.

use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::{Mutex, OnceLock};
use std::time::{Duration, Instant};

const BIN: &str = "claude";

/// A login shell that never returns must not wedge every command that
/// needs the CLI — same poll-with-deadline shape `store::mcp_status` uses.
const SHELL_QUERY_TIMEOUT: Duration = Duration::from_secs(3);

fn override_slot() -> &'static Mutex<Option<PathBuf>> {
    static SLOT: OnceLock<Mutex<Option<PathBuf>>> = OnceLock::new();
    SLOT.get_or_init(|| Mutex::new(None))
}

fn discovered_slot() -> &'static OnceLock<Option<PathBuf>> {
    static SLOT: OnceLock<Option<PathBuf>> = OnceLock::new();
    &SLOT
}

/// Records the Settings override. Called wherever `ProjectConfig` is read
/// into memory (`open_project`, `set_config`) so a path typed in Settings
/// takes effect without restarting the app. Empty string clears it.
pub fn set_override(path: Option<&str>) {
    let resolved = path
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(PathBuf::from);
    *override_slot()
        .lock()
        .unwrap_or_else(|err| err.into_inner()) = resolved;
}

/// The resolved binary, or `None` when the CLI cannot be found anywhere.
/// `None` is what the Settings screen turns into "chỉ đường dẫn thủ công".
pub fn resolve() -> Option<PathBuf> {
    if let Some(configured) = override_slot()
        .lock()
        .unwrap_or_else(|err| err.into_inner())
        .clone()
    {
        // A path the user typed is authoritative even if it no longer
        // exists: silently falling back to a different binary than the one
        // they pinned would be worse than failing with their own value.
        return Some(configured);
    }
    discovered_slot().get_or_init(discover).clone()
}

/// The program to hand `Command::new`. Falls back to the bare name so a
/// failed discovery still produces the familiar "not found" error rather
/// than a panic — callers that want to *report* the failure use
/// `resolve()` instead.
pub fn program() -> PathBuf {
    resolve().unwrap_or_else(|| PathBuf::from(BIN))
}

/// Every `claude` invocation in the app goes through here.
pub fn command() -> Command {
    let mut cmd = Command::new(program());
    crate::agentrun::procutil::hide_console(&mut cmd);
    cmd
}

/// The message every "cannot run without the CLI" path shows. Names the
/// escape hatch, because the common cause in a packaged build is not a
/// missing install but a `PATH` the app never inherited — telling the user
/// to "check PATH" sends them to fix something that is already correct in
/// their terminal.
pub fn not_found_message() -> String {
    "Không tìm thấy Claude Code CLI (`claude`). App bundle không kế thừa PATH của terminal — \
vào Settings → Authentication để nhập đường dẫn tuyệt đối tới `claude` (ví dụ \
`~/.local/bin/claude`, xem bằng lệnh `which claude`)."
        .to_string()
}

/// File names to look for. Windows shims carry an extension and
/// `CreateProcess` will not guess it for us.
fn candidate_names() -> Vec<String> {
    if cfg!(windows) {
        let pathext =
            std::env::var("PATHEXT").unwrap_or_else(|_| ".COM;.EXE;.BAT;.CMD".to_string());
        let mut names: Vec<String> = pathext
            .split(';')
            .map(str::trim)
            .filter(|ext| !ext.is_empty())
            .map(|ext| format!("{BIN}{}", ext.to_ascii_lowercase()))
            .collect();
        // A bare name still wins when something did install a real .exe
        // under it; keep it last so an explicit extension is preferred.
        names.push(BIN.to_string());
        names
    } else {
        vec![BIN.to_string()]
    }
}

/// Install locations to probe when `PATH` does not carry the CLI — which
/// is the normal case for a Finder-launched bundle.
fn known_dirs() -> Vec<PathBuf> {
    let mut dirs = Vec::new();
    if let Some(home) = home_dir() {
        dirs.push(home.join(".local").join("bin"));
        dirs.push(home.join(".claude").join("local"));
        dirs.push(home.join(".bun").join("bin"));
        dirs.push(home.join(".volta").join("bin"));
        dirs.push(home.join(".npm-global").join("bin"));
        if cfg!(windows) {
            dirs.push(home.join("AppData").join("Roaming").join("npm"));
        }
    }
    if !cfg!(windows) {
        dirs.push(PathBuf::from("/opt/homebrew/bin"));
        dirs.push(PathBuf::from("/usr/local/bin"));
        dirs.push(PathBuf::from("/usr/bin"));
    }
    dirs
}

fn home_dir() -> Option<PathBuf> {
    std::env::var_os(if cfg!(windows) { "USERPROFILE" } else { "HOME" })
        .map(PathBuf::from)
        .filter(|path| !path.as_os_str().is_empty())
}

/// Pure so the search order is testable without touching the filesystem.
fn first_match(
    dirs: &[PathBuf],
    names: &[String],
    exists: &dyn Fn(&Path) -> bool,
) -> Option<PathBuf> {
    for dir in dirs {
        for name in names {
            let candidate = dir.join(name);
            if exists(&candidate) {
                return Some(candidate);
            }
        }
    }
    None
}

fn is_executable_file(path: &Path) -> bool {
    // `is_file` follows symlinks, which is what `~/.local/bin/claude`
    // is — a link into the versioned install dir.
    path.is_file()
}

/// Search order, split out from the environment so a test can reproduce
/// the Finder-launch case (minimal `PATH`, CLI in `~/.local/bin`) without
/// touching the real one.
fn discover_from(
    path_dirs: &[PathBuf],
    known: &[PathBuf],
    names: &[String],
    exists: &dyn Fn(&Path) -> bool,
) -> Option<PathBuf> {
    first_match(path_dirs, names, exists).or_else(|| first_match(known, names, exists))
}

fn discover() -> Option<PathBuf> {
    let names = candidate_names();
    let path_dirs: Vec<PathBuf> = std::env::var_os("PATH")
        .map(|value| std::env::split_paths(&value).collect())
        .unwrap_or_default();

    discover_from(&path_dirs, &known_dirs(), &names, &is_executable_file)
        .or_else(login_shell_lookup)
}

/// Last resort: ask the user's login shell where the CLI is. Covers the
/// installs that live somewhere `known_dirs` does not guess (custom npm
/// prefix, asdf/mise shims, ...).
#[cfg(not(windows))]
fn login_shell_lookup() -> Option<PathBuf> {
    let shell = std::env::var("SHELL").ok().filter(|s| !s.is_empty())?;
    let mut child = Command::new(shell)
        .arg("-lc")
        .arg(format!("command -v {BIN}"))
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .ok()?;

    let start = Instant::now();
    loop {
        match child.try_wait() {
            Ok(Some(_)) => break,
            Ok(None) => {}
            Err(_) => return None,
        }
        if start.elapsed() >= SHELL_QUERY_TIMEOUT {
            let _ = child.kill();
            return None;
        }
        std::thread::sleep(Duration::from_millis(50));
    }

    let output = child.wait_with_output().ok()?;
    if !output.status.success() {
        return None;
    }
    let path = PathBuf::from(String::from_utf8_lossy(&output.stdout).trim().to_string());
    if path.as_os_str().is_empty() || !is_executable_file(&path) {
        return None;
    }
    Some(path)
}

#[cfg(windows)]
fn login_shell_lookup() -> Option<PathBuf> {
    // No login-shell equivalent worth spawning here: `PATH` plus
    // `known_dirs` already covers the npm/global install shapes, and
    // `where.exe` reads the same `PATH` step 2 just searched.
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    /// One test, not two: `set_override` writes a process-global that the
    /// test harness would otherwise let two threads race over.
    #[test]
    fn override_wins_over_discovery_and_blank_clears_it() {
        set_override(Some("/custom/bin/claude"));
        assert_eq!(resolve(), Some(PathBuf::from("/custom/bin/claude")));

        set_override(Some("   "));
        assert_eq!(override_slot().lock().unwrap().clone(), None);

        set_override(None);
    }

    #[test]
    fn first_match_scans_dirs_in_order_then_names() {
        let dirs = vec![PathBuf::from("/a"), PathBuf::from("/b")];
        let names = vec!["claude.exe".to_string(), "claude".to_string()];
        // Only /b/claude exists: the whole of /a must be rejected first,
        // and within /b the .exe name must be tried before the bare one.
        let exists = |path: &Path| path == Path::new("/b/claude");
        assert_eq!(
            first_match(&dirs, &names, &exists),
            Some(PathBuf::from("/b/claude"))
        );
    }

    #[test]
    fn first_match_is_none_when_nothing_exists() {
        let dirs = vec![PathBuf::from("/a")];
        let names = vec!["claude".to_string()];
        assert_eq!(first_match(&dirs, &names, &|_| false), None);
    }

    #[cfg(not(windows))]
    #[test]
    fn unix_looks_for_the_bare_name_only() {
        assert_eq!(candidate_names(), vec!["claude".to_string()]);
    }

    #[cfg(windows)]
    #[test]
    fn windows_looks_for_shim_extensions() {
        let names = candidate_names();
        // The npm shim is `claude.cmd`; without this the packaged app
        // cannot spawn the CLI at all.
        assert!(names.iter().any(|name| name == "claude.cmd"));
        assert_eq!(names.last().map(String::as_str), Some("claude"));
    }

    /// The bug this module exists for: a Finder-launched `.app` inherits
    /// `/usr/bin:/bin:/usr/sbin:/sbin`, where the CLI installed to
    /// `~/.local/bin` is invisible. Discovery must still find it.
    #[test]
    fn finds_the_cli_when_path_is_the_minimal_finder_set() {
        let path_dirs: Vec<PathBuf> = ["/usr/bin", "/bin", "/usr/sbin", "/sbin"]
            .iter()
            .map(PathBuf::from)
            .collect();
        let known = vec![PathBuf::from("/home/u/.local/bin")];
        let names = vec![BIN.to_string()];
        let installed = Path::new("/home/u/.local/bin/claude");

        assert_eq!(
            discover_from(&path_dirs, &known, &names, &|path| path == installed),
            Some(installed.to_path_buf()),
        );
    }

    /// PATH still wins when it does carry the CLI — `pnpm tauri dev` must
    /// keep using whatever the developer's shell resolves.
    #[test]
    fn path_takes_precedence_over_known_dirs() {
        let path_dirs = vec![PathBuf::from("/opt/dev/bin")];
        let known = vec![PathBuf::from("/home/u/.local/bin")];
        let names = vec![BIN.to_string()];

        assert_eq!(
            discover_from(&path_dirs, &known, &names, &|_| true),
            Some(PathBuf::from("/opt/dev/bin/claude")),
        );
    }

    /// End-to-end against the real filesystem, and the reason this module
    /// exists — so it is `#[ignore]`d by default (it needs a real install)
    /// and run deliberately:
    ///
    /// ```text
    /// env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin \
    ///   cargo test resolves_a_real_claude_under_a_finder_path -- --ignored
    /// ```
    ///
    /// That environment is what a Finder-launched `.app` gets. Before this
    /// module, resolution under it failed and no agent could ever start.
    #[test]
    #[ignore = "needs a real Claude CLI installed on the machine"]
    fn resolves_a_real_claude_under_a_finder_path() {
        let resolved = resolve().expect("Claude CLI must be discoverable without a shell PATH");
        assert!(
            resolved.is_file(),
            "resolved path must exist: {}",
            resolved.display()
        );
    }

    #[test]
    fn known_dirs_include_the_default_install_location() {
        if let Some(home) = home_dir() {
            assert!(known_dirs().contains(&home.join(".local").join("bin")));
        }
    }
}
