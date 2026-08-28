//! Builds the `claude` CLI invocation for one agent run.
//!
//! Headless spawn has no TTY. Use non-interactive permission modes that keep
//! the CLI from waiting for a prompt: `plan` for read-only agents and
//! `acceptEdits` for write-scoped agents. Only the explicitly full profile
//! uses `bypassPermissions`.
//!
//! `claude --help` (v2.1.232) has no `--max-turns` flag — `AgentConfig`'s
//! `max_turns` field cannot be passed to the CLI (see `ASSUMPTIONS-GAPS.md`
//! A7). It is intentionally NOT used here.

use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use crate::agentrun::cli_path;
use crate::domain::config_file::{AgentConfig, Model, PermissionProfile};

fn model_flag(model: Model) -> &'static str {
    match model {
        Model::Opus => "opus",
        Model::Sonnet => "sonnet",
        Model::Haiku => "haiku",
    }
}

/// `--tools` narrows the **built-in set only** (`claude --help`: "Specify the
/// list of available tools from the built-in set"). It is NOT the per-agent
/// permission layer — that one is the `tools:` allowlist in each
/// `.claude/agents/<name>.md`, which the CLI enforces via `--agent`.
///
/// Because of that, `Bash` was being stripped from every `write-scoped`
/// agent even when the agent's own file declared it: `qc-automation-agent`
/// (whose entire job is running Playwright), `qc-agent`, and
/// `design-analyst-agent` (needs `base64 -d` to write exported PNGs to
/// disk — `mcp-figma-bridge`'s `export_node` only ever returns base64).
/// Granting it here is safe for the agents that do NOT declare it
/// (`ba-agent`, `techlead-*`, `init-agent`): their frontmatter
/// allowlist still blocks the call.
///
/// Pipeline runs spawn with `cwd = feature_dir` (under `docsRoot`, see
/// `commands::agentrun::run_to_completion`), which can be unrelated to
/// `agentsRoot` (A1) — so the kit's `.claude/settings.json` is not
/// reliably discovered from there, and with it the `guard-bash.js`
/// PreToolUse hook (H02/H03/H04). `SpawnParams::settings_file` now names
/// that file explicitly via `--settings`.
///
/// STILL UNVERIFIED, and it matters most for exactly the agents that have
/// `Bash`: Anthropic's docs do not state whether PreToolUse hooks run at
/// all under `-p` headless, nor whether `--permission-mode
/// bypassPermissions` (what the `full` profile passes) skips them. Passing
/// `--settings` is necessary but may not be sufficient. Do not describe
/// these runs as hook-guarded until someone has actually watched
/// `guard-bash.js` block a command in this exact configuration.
fn tools_flag(permission: PermissionProfile) -> &'static str {
    match permission {
        PermissionProfile::ReadOnly => "Read Grep Glob",
        PermissionProfile::WriteScoped => "Read Grep Glob Write Edit Bash",
        PermissionProfile::Full => "default",
    }
}

fn permission_mode(permission: PermissionProfile) -> &'static str {
    match permission {
        PermissionProfile::ReadOnly => "plan",
        PermissionProfile::WriteScoped => "acceptEdits",
        PermissionProfile::Full => "bypassPermissions",
    }
}

pub struct SpawnParams<'a> {
    /// The kit's own agent name (e.g. `"ba-agent"`) — passed as `--agent`
    /// so the CLI loads that agent's real definition from
    /// `.claude/agents/<agent_name>.md` (verified for real: a spawned
    /// `--agent ba-agent` call identified itself as "the Business Analyst
    /// (BA) agent", not assumed from documentation). Plain prompt text
    /// alone would NOT reliably reproduce a specific kit agent's behavior.
    pub agent_name: &'a str,
    pub prompt: &'a str,
    pub cwd: &'a Path,
    pub config: &'a AgentConfig,
    /// `Some` delivers `prompt` into an existing session instead of
    /// starting a new one — this is how a clarification answer is sent.
    /// Each `claude -p` call runs to completion and exits; there is no
    /// long-lived process waiting on stdin to "continue" (A5) — resuming
    /// always means spawning a brand new process.
    pub resume_session_id: Option<&'a str>,
    /// Extra `--add-dir` roots. Pipeline runs leave this empty (their cwd
    /// already is the feature dir); the Backlog push uses it because it
    /// runs from `agentsRoot` — where the project's MCP config lives — and
    /// still needs to read task files under `docsRoot` (A1: the roots can
    /// be three unrelated directories).
    pub add_dirs: &'a [PathBuf],
    /// The kit's `<agentsRoot>/.claude/settings.json`, passed as
    /// `--settings` when it exists.
    ///
    /// Not cosmetic: pipeline runs have `cwd = feature_dir` under
    /// `docsRoot`, which can be a directory entirely unrelated to
    /// `agentsRoot` (A1), so the kit's settings — and with them the
    /// `guard-bash.js` PreToolUse hook — are not necessarily discovered on
    /// their own. Naming the file explicitly makes that deterministic
    /// instead of depending on how the roots happen to nest.
    pub settings_file: Option<&'a Path>,
    /// Authentication environment for this child only. The app never mutates
    /// its own process environment and never puts a secret in CLI arguments.
    pub auth: SpawnAuth<'a>,
}

pub enum SpawnAuth<'a> {
    CliDefault,
    Subscription,
    Console,
    ApiKey(&'a str),
}

fn remove_auth_overrides(cmd: &mut Command) {
    for name in [
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CODE_API_KEY_HELPER",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "ANTHROPIC_PROFILE",
    ] {
        cmd.env_remove(name);
    }
}

/// Does not spawn — callers own when/how the child actually starts (so
/// tests can inspect the built command before running it).
pub fn build_command(params: &SpawnParams) -> Command {
    let mut cmd = cli_path::command();
    cmd.current_dir(params.cwd)
        .arg("-p")
        .arg(params.prompt)
        .arg("--agent")
        .arg(params.agent_name)
        .arg("--output-format")
        .arg("stream-json")
        .arg("--verbose")
        .arg("--model")
        .arg(model_flag(params.config.model))
        .arg("--permission-mode")
        .arg(permission_mode(params.config.permission))
        .arg("--tools")
        .arg(tools_flag(params.config.permission));

    if let Some(settings) = params.settings_file {
        cmd.arg("--settings").arg(settings);
    }

    for dir in params.add_dirs {
        cmd.arg("--add-dir").arg(dir);
    }

    match params.auth {
        SpawnAuth::CliDefault => {}
        SpawnAuth::Subscription | SpawnAuth::Console => remove_auth_overrides(&mut cmd),
        SpawnAuth::ApiKey(api_key) => {
            remove_auth_overrides(&mut cmd);
            cmd.env("ANTHROPIC_API_KEY", api_key);
        }
    }

    if let Some(session_id) = params.resume_session_id {
        cmd.arg("--resume").arg(session_id);
    }

    // stdin is never read (A5: resume via a new process, not stdin input),
    // closing it early is one more guard against ever blocking on input.
    cmd.stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    // Mỗi run một process group riêng (PGID = PID của CLI). MCP server do
    // CLI sinh ra nằm cùng nhóm, nên kết thúc run là kết thúc được cả
    // chúng — `Child::kill()` chỉ với tới tiến trình con trực tiếp, còn MCP
    // server là "cháu". Chúng thừa kế pipe stdout, nên MCP server sống sót
    // đồng nghĩa pipe không bao giờ EOF (xem `agentrun::process_group`).
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        cmd.process_group(0);
    }
    cmd
}

/// AC-E2-28 — checked synchronously before a run is ever started, so a
/// missing CLI never creates an empty run entry.
pub fn is_claude_cli_available() -> bool {
    cli_path::command()
        .arg("--version")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::config_file::AgentConfig;

    fn config(model: Model, permission: PermissionProfile) -> AgentConfig {
        AgentConfig {
            model,
            max_turns: 20,
            timeout_minutes: 30,
            permission,
            stale: false,
            newly_discovered: false,
        }
    }

    fn args_of(cmd: &Command) -> Vec<String> {
        cmd.get_args()
            .map(|a| a.to_string_lossy().into_owned())
            .collect()
    }

    fn env_value(cmd: &Command, name: &str) -> Option<String> {
        cmd.get_envs().find_map(|(key, value)| {
            if key == std::ffi::OsStr::new(name) {
                value.map(|value| value.to_string_lossy().into_owned())
            } else {
                None
            }
        })
    }

    #[test]
    fn permission_mode_matches_profile() {
        for (profile, expected_mode) in [
            (PermissionProfile::ReadOnly, "plan"),
            (PermissionProfile::WriteScoped, "acceptEdits"),
            (PermissionProfile::Full, "bypassPermissions"),
        ] {
            let cfg = config(Model::Sonnet, profile);
            let cmd = build_command(&SpawnParams {
                agent_name: "ba-agent",
                prompt: "hi",
                cwd: Path::new("."),
                config: &cfg,
                resume_session_id: None,
            settings_file: None,
                add_dirs: &[],
                auth: SpawnAuth::CliDefault,
            });
            let args = args_of(&cmd);
            let idx = args.iter().position(|a| a == "--permission-mode").unwrap();
            assert_eq!(args[idx + 1], expected_mode);
        }
    }

    /// The built-in set handed to `write-scoped` agents must include `Bash`:
    /// `qc-automation-agent` runs Playwright with it and
    /// `design-analyst-agent` decodes exported PNGs with it. Per-agent
    /// restriction is the `tools:` frontmatter allowlist, not this flag.
    #[test]
    fn write_scoped_grants_bash_and_write_tools() {
        let cfg = config(Model::Sonnet, PermissionProfile::WriteScoped);
        let cmd = build_command(&SpawnParams {
            agent_name: "ba-agent",
            prompt: "hi",
            cwd: Path::new("."),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: SpawnAuth::CliDefault,
        });
        let args = args_of(&cmd);
        let idx = args.iter().position(|a| a == "--tools").unwrap();
        assert!(args[idx + 1].contains("Bash"));
        assert!(args[idx + 1].contains("Write"));
        assert!(args[idx + 1].contains("Edit"));
    }

    /// Read-only stays read-only — no `Bash`, no `Write`.
    #[test]
    fn read_only_grants_neither_bash_nor_write() {
        let cfg = config(Model::Sonnet, PermissionProfile::ReadOnly);
        let cmd = build_command(&SpawnParams {
            agent_name: "ba-agent",
            prompt: "hi",
            cwd: Path::new("."),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: SpawnAuth::CliDefault,
        });
        let args = args_of(&cmd);
        let idx = args.iter().position(|a| a == "--tools").unwrap();
        assert!(!args[idx + 1].contains("Bash"));
        assert!(!args[idx + 1].contains("Write"));
    }

    #[test]
    fn full_profile_uses_default_tools() {
        let cfg = config(Model::Sonnet, PermissionProfile::Full);
        let cmd = build_command(&SpawnParams {
            agent_name: "ba-agent",
            prompt: "hi",
            cwd: Path::new("."),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: SpawnAuth::CliDefault,
        });
        let args = args_of(&cmd);
        let idx = args.iter().position(|a| a == "--tools").unwrap();
        assert_eq!(args[idx + 1], "default");
    }

    #[test]
    fn api_key_auth_is_injected_as_child_environment_not_cli_args() {
        let cfg = config(Model::Sonnet, PermissionProfile::Full);
        let cmd = build_command(&SpawnParams {
            agent_name: "ba-agent",
            prompt: "hi",
            cwd: Path::new("."),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: SpawnAuth::ApiKey("secret-value"),
        });
        assert_eq!(
            env_value(&cmd, "ANTHROPIC_API_KEY").as_deref(),
            Some("secret-value")
        );
        assert!(!args_of(&cmd).iter().any(|arg| arg.contains("secret-value")));
    }

    #[test]
    fn resume_session_id_appends_resume_flag() {
        let cfg = config(Model::Haiku, PermissionProfile::ReadOnly);
        let cmd = build_command(&SpawnParams {
            agent_name: "ba-agent",
            prompt: "answer",
            cwd: Path::new("."),
            config: &cfg,
            resume_session_id: Some("abc-123"),
            settings_file: None,
            add_dirs: &[],
            auth: SpawnAuth::CliDefault,
        });
        let args = args_of(&cmd);
        let idx = args.iter().position(|a| a == "--resume").unwrap();
        assert_eq!(args[idx + 1], "abc-123");
    }

    /// The kit's `guard-bash.js` hook only applies if the CLI actually loads
    /// `<agentsRoot>/.claude/settings.json`, and pipeline runs have their cwd
    /// under `docsRoot` — which A1 allows to be an unrelated directory. Naming
    /// the file removes that dependency on how the roots happen to nest.
    #[test]
    fn the_kit_settings_file_is_passed_when_it_exists() {
        let cfg = config(Model::Haiku, PermissionProfile::Full);
        let settings = Path::new("/kit/.claude/settings.json");
        let cmd = build_command(&SpawnParams {
            agent_name: "frontend-agent",
            prompt: "go",
            cwd: Path::new("."),
            config: &cfg,
            resume_session_id: None,
            settings_file: Some(settings),
            add_dirs: &[],
            auth: SpawnAuth::CliDefault,
        });
        let args = args_of(&cmd);
        let idx = args
            .iter()
            .position(|a| a == "--settings")
            .expect("--settings must be passed when the kit has a settings file");
        assert_eq!(args[idx + 1], settings.to_string_lossy());
    }

    /// A project that never scaffolded the kit has no such file — handing the
    /// CLI a path to nothing would fail the run over a file that is optional.
    #[test]
    fn no_settings_flag_when_the_project_has_no_kit_settings() {
        let cfg = config(Model::Haiku, PermissionProfile::Full);
        let cmd = build_command(&SpawnParams {
            agent_name: "frontend-agent",
            prompt: "go",
            cwd: Path::new("."),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: SpawnAuth::CliDefault,
        });
        assert!(!args_of(&cmd).iter().any(|a| a == "--settings"));
    }

    #[test]
    fn no_max_turns_flag_is_ever_emitted() {
        // A7: the CLI has no such flag — asserting its absence catches a
        // regression if someone re-adds it from a stale assumption later.
        let cfg = config(Model::Sonnet, PermissionProfile::Full);
        let cmd = build_command(&SpawnParams {
            agent_name: "ba-agent",
            prompt: "hi",
            cwd: Path::new("."),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: SpawnAuth::CliDefault,
        });
        assert!(!args_of(&cmd).iter().any(|a| a.contains("max-turns")));
    }

    /// The in-cwd write smoke test is intentionally opt-in because it spends
    /// Claude API quota. The deterministic command test above is the default
    /// enforcement check.
    #[test]
    #[ignore = "requires a live Claude CLI and API quota"]
    fn bypass_permissions_does_not_hang_when_agent_needs_a_write_tool() {
        if !is_claude_cli_available() {
            eprintln!("skipping live spike: `claude` CLI not usable in this environment");
            return;
        }

        let tmp = crate::agentrun::test_support::agent_project_dir("test-agent");
        let cfg = config(Model::Haiku, PermissionProfile::WriteScoped);
        // An explicit absolute path, not "the current directory" — a real
        // run of this exact test previously observed the model guess `/`
        // (got EROFS) then `/tmp/ok.txt` instead of the real tempdir, which
        // is exactly the kind of ambiguity production prompts (T2.4/T2.5)
        // avoid by always passing `copiedPath` as an explicit absolute path.
        let target = tmp.path().join("ok.txt");
        let prompt = format!(
            "Create a file at exactly this absolute path: {} — containing exactly: done. Then stop, do not explain.",
            target.display()
        );
        let mut cmd = build_command(&SpawnParams {
            agent_name: "test-agent",
            prompt: &prompt,
            cwd: tmp.path(),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: SpawnAuth::CliDefault,
        });
        // A generous cap, not a tight one: a first call in a fresh cwd pays
        // full cache-creation cost (~$0.06 observed for this exact prompt,
        // vs ~$0.01 for a cache-hit follow-up) — the deadline loop below is
        // what actually guards against a hang, this is just a backstop.
        cmd.arg("--max-budget-usd").arg("0.20");

        let mut child = cmd.spawn().expect("failed to spawn claude CLI");

        // Drain stdout concurrently — leaving it unread risks the child
        // blocking on a full pipe buffer, which looks identical to a
        // permission-prompt hang from the outside. Production's reader
        // thread (T2.2) drains it for the same reason.
        let mut stdout = child.stdout.take().expect("piped stdout");
        let drain = std::thread::spawn(move || {
            use std::io::Read;
            let mut buf = String::new();
            let _ = stdout.read_to_string(&mut buf);
            buf
        });

        let deadline = std::time::Duration::from_secs(60);
        let start = std::time::Instant::now();
        let status = loop {
            if let Some(status) = child.try_wait().unwrap() {
                break status;
            }
            if start.elapsed() > deadline {
                let _ = child.kill();
                panic!(
                    "claude did not exit within {deadline:?} — bypassPermissions may be \
                     hanging on an interactive prompt instead of running headlessly"
                );
            }
            std::thread::sleep(std::time::Duration::from_millis(200));
        };
        let stdout_content = drain.join().unwrap();
        if !status.success() {
            // Not fatal by itself — e.g. the CLI's own `--max-budget-usd`
            // guard can end a run with a non-zero exit *after* the write
            // already succeeded. What this test actually cares about is
            // asserted below: no hang, and the write went through.
            eprintln!("claude exited non-zero ({status:?}); stdout was: {stdout_content}");
        }

        assert!(
            target.is_file(),
            "bypassPermissions + WriteScoped tools should let the agent create the file; stdout was: {stdout_content}"
        );
        // `contains`, not exact-match: the model isn't guaranteed to follow
        // "exactly" to the letter (observed "done." with trailing
        // punctuation) — what this test verifies is that the write
        // happened at all, not the model's instruction-following precision.
        assert!(std::fs::read_to_string(&target).unwrap().contains("done"));
    }

    /// SPIKE for AC-E1-16 (giới hạn thư mục ghi khi `WriteScoped`) — verified
    /// for real rather than assumed, same principle as the spike above and
    /// `ASSUMPTIONS-GAPS.md` A5: does `bypassPermissions` (unconditionally
    /// on for every headless spawn — see this module's own top doc comment)
    /// still enforce ANY directory boundary, or does "bypass all permission
    /// checks" really mean all of them, including the cwd/`--add-dir`
    /// boundary a non-bypass session would normally respect? `cwd` is one
    /// fresh tempdir; the write target is a SECOND, wholly unrelated
    /// tempdir — not a subdirectory of `cwd`, not passed via `--add-dir`,
    /// nothing linking the two except this test.
    #[test]
    #[ignore = "requires a live Claude CLI and API quota"]
    fn bypass_permissions_allows_writes_entirely_outside_cwd() {
        if !is_claude_cli_available() {
            eprintln!("skipping live spike: `claude` CLI not usable in this environment");
            return;
        }

        let cwd_tmp = crate::agentrun::test_support::agent_project_dir("test-agent");
        let outside_tmp = tempfile::tempdir().unwrap();
        let outside_target = outside_tmp.path().join("escaped.txt");

        let cfg = config(Model::Haiku, PermissionProfile::WriteScoped);
        let prompt = format!(
            "Create a file at exactly this absolute path: {} — containing exactly: done. Then stop, do not explain.",
            outside_target.display()
        );
        let mut cmd = build_command(&SpawnParams {
            agent_name: "test-agent",
            prompt: &prompt,
            cwd: cwd_tmp.path(),
            config: &cfg,
            resume_session_id: None,
            settings_file: None,
            add_dirs: &[],
            auth: SpawnAuth::CliDefault,
        });
        cmd.arg("--max-budget-usd").arg("0.20");

        let mut child = cmd.spawn().expect("failed to spawn claude CLI");
        let mut stdout = child.stdout.take().expect("piped stdout");
        let drain = std::thread::spawn(move || {
            use std::io::Read;
            let mut buf = String::new();
            let _ = stdout.read_to_string(&mut buf);
            buf
        });

        let deadline = std::time::Duration::from_secs(60);
        let start = std::time::Instant::now();
        let status = loop {
            if let Some(status) = child.try_wait().unwrap() {
                break status;
            }
            if start.elapsed() > deadline {
                let _ = child.kill();
                panic!("claude did not exit within {deadline:?}");
            }
            std::thread::sleep(std::time::Duration::from_millis(200));
        };
        let stdout_content = drain.join().unwrap();
        if !status.success() {
            eprintln!("claude exited non-zero ({status:?}); stdout was: {stdout_content}");
        }

        // This assertion documents the empirical finding, whichever way it
        // comes out: if it FAILS here, that means bypassPermissions genuinely
        // does NOT let a WriteScoped agent escape its cwd, and AC-E1-16 can
        // be satisfied preventively via `--add-dir` (or simply relying on
        // cwd's own default boundary). If it PASSES, bypassPermissions
        // grants unrestricted filesystem write access regardless of
        // `--tools`/`--add-dir`, and AC-E1-16 can only be satisfied
        // detectively (diff what changed after the run, warn if outside
        // scope) — never preventively — under the current headless
        // architecture.
        eprintln!(
            "SPIKE RESULT: outside_target written = {} (path: {})",
            outside_target.is_file(),
            outside_target.display()
        );
        assert!(
            outside_target.is_file(),
            "expected bypassPermissions to allow the write outside cwd — if this fails, \
             directory-scoped enforcement IS possible under bypass mode and AC-E1-16 should \
             be implemented preventively instead of detectively"
        );
    }
}
