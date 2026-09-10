//! Live MCP connection status, from `claude mcp list`.
//!
//! Distinct from `store::mcp_config`, which only parses the project's own
//! config files. Two reasons this exists:
//!
//! 1. It reports what is **actually reachable**, not merely declared — the
//!    CLI health-checks every server before answering.
//! 2. The CLI resolves the whole config chain (user-level config plus every
//!    `.mcp.json` up the directory tree), whereas `mcp_config` deliberately
//!    looks only at `agentsRoot` and therefore misses servers declared
//!    above it.
//!
//! The app itself never speaks MCP — the `claude` processes it spawns do —
//! so "connected" here means "connected for the agents this app runs",
//! which is exactly the thing worth showing.

use std::path::Path;
use std::process::Stdio;
use std::time::{Duration, Instant};

use serde::Serialize;

use crate::agentrun::cli_path;

/// `<name>: <detail>` — the first `": "` is the name boundary; a URL
/// inside the detail has no space after its colon, so it never matches.
const NAME_SEPARATOR: &str = ": ";

/// Health checks are network calls; 8s was typical on the dev machine, so
/// this is deliberately generous. Exceeding it is reported, never silently
/// treated as "no servers".
const LIST_TIMEOUT: Duration = Duration::from_secs(45);

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum McpConnectionStatus {
    Connected,
    /// Reachable but the user has to log in (OAuth-style servers).
    NeedsAuth,
    /// Anything else the CLI reported — `raw` carries its exact words.
    Failed,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct McpStatusEntry {
    pub name: String,
    /// Command or URL, as the CLI printed it (secrets masked — see
    /// [`redact_inline_secrets`]).
    pub detail: String,
    pub status: McpConnectionStatus,
    /// The CLI's own status words, kept so a failure reason is never lost
    /// in translation.
    pub raw_status: String,
}

/// Masks `KEY=value`-shaped fragments. `claude mcp list` has not been
/// observed printing env values, but a server added with `-e API_KEY=...`
/// could put one in the command line, and this module's output goes
/// straight to the screen.
pub fn redact_inline_secrets(detail: &str) -> String {
    detail
        .split_whitespace()
        .map(|token| match token.split_once('=') {
            Some((key, value)) if !value.is_empty() && is_secret_key(key) => {
                format!("{key}=***")
            }
            _ => token.to_string(),
        })
        .collect::<Vec<_>>()
        .join(" ")
}

fn is_secret_key(key: &str) -> bool {
    let key = key.trim_start_matches('-').to_ascii_uppercase();
    ["KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL"]
        .iter()
        .any(|needle| key.contains(needle))
}

/// Parses `claude mcp list`'s output.
///
/// Each server is one `<name>: <detail> - <status>` line, with a
/// "Checking MCP server health…" banner and blank lines around it. Split
/// from the RIGHT on `" - "` because a detail can itself contain that
/// sequence (URLs and command flags do).
pub fn parse_mcp_list(stdout: &str) -> Vec<McpStatusEntry> {
    stdout
        .lines()
        .filter_map(|line| {
            let line = line.trim();
            if line.is_empty() || !line.contains(NAME_SEPARATOR) {
                return None;
            }
            let (name, rest) = line.split_once(NAME_SEPARATOR)?;
            let (detail, raw_status) = rest.rsplit_once(" - ")?;
            let name = name.trim();
            let raw_status = raw_status.trim();
            if name.is_empty() || raw_status.is_empty() {
                return None;
            }

            let lowered = raw_status.to_ascii_lowercase();
            let status = if lowered.contains("connected") {
                McpConnectionStatus::Connected
            } else if lowered.contains("auth") {
                McpConnectionStatus::NeedsAuth
            } else {
                McpConnectionStatus::Failed
            };

            Some(McpStatusEntry {
                name: name.to_string(),
                detail: redact_inline_secrets(detail.trim()),
                status,
                raw_status: raw_status.to_string(),
            })
        })
        .collect()
}

/// Runs `claude mcp list` from `cwd`, which is what makes the answer
/// project-aware: the CLI merges the user-level config with every
/// `.mcp.json` found from that directory upward.
///
/// Blocking (the health checks take seconds) — callers must keep it off the
/// UI thread.
pub fn fetch_mcp_status(cwd: &Path) -> Result<Vec<McpStatusEntry>, String> {
    let mut child = cli_path::command()
        .arg("mcp")
        .arg("list")
        .current_dir(cwd)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|err| format!("Không chạy được `claude mcp list`: {err}"))?;

    // Same poll-with-deadline shape `agentrun::runner` uses, for the same
    // reason: a hung health check must not wedge the caller forever.
    let start = Instant::now();
    loop {
        match child.try_wait() {
            Ok(Some(_)) => break,
            Ok(None) => {}
            Err(err) => return Err(format!("Lỗi khi chờ `claude mcp list`: {err}")),
        }
        if start.elapsed() >= LIST_TIMEOUT {
            let _ = child.kill();
            return Err(format!(
                "`claude mcp list` quá {} giây chưa trả lời — có thể một MCP server đang treo",
                LIST_TIMEOUT.as_secs()
            ));
        }
        std::thread::sleep(Duration::from_millis(100));
    }

    let output = child
        .wait_with_output()
        .map_err(|err| format!("Không đọc được kết quả `claude mcp list`: {err}"))?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    let entries = parse_mcp_list(&stdout);

    if entries.is_empty() && !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(redact_inline_secrets(stderr.trim()));
    }
    Ok(entries)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Verbatim output from a real `claude mcp list` run.
    const REAL_OUTPUT: &str = "Checking MCP server health…\n\n\
claude.ai Zapier: https://mcp.zapier.com/api/v1/connect - ! Needs authentication\n\
claude.ai Slack: https://mcp.slack.com/mcp - ✔ Connected\n\
claude.ai Figma: https://mcp.figma.com/mcp - ✔ Connected\n\
figma-mcp-go: npx -y @vkhanhqui/figma-mcp-go@latest - ✔ Connected\n\
backlog: npx -y backlog-mcp-server - ✔ Connected\n";

    /// The gate that decides whether `ba-agent` may run reads exactly these
    /// two parsed fields. Asserting the role here closes the loop from the
    /// CLI's own text to the decision, without spawning a process — and
    /// pins that a connected Figma Desktop server is still not enough.
    #[test]
    fn figma_role_of_the_parsed_entries_separates_write_from_read_only() {
        use crate::store::mcp_config::{figma_role, FigmaRole};

        let entries = parse_mcp_list(REAL_OUTPUT);
        let role = |name: &str| {
            let e = entries.iter().find(|e| e.name == name).unwrap();
            figma_role(&e.name, &e.detail)
        };

        assert_eq!(role("claude.ai Figma"), FigmaRole::WriteCapable);
        assert_eq!(role("figma-mcp-go"), FigmaRole::ReadOnly);
        assert_eq!(role("claude.ai Slack"), FigmaRole::NotFigma);

        let desktop = parse_mcp_list("figma: http://127.0.0.1:3845/mcp - ✔ Connected\n");
        assert_eq!(
            figma_role(&desktop[0].name, &desktop[0].detail),
            FigmaRole::ReadOnly,
            "Figma Desktop connected vẫn không vẽ được canvas"
        );
    }

    #[test]
    fn parses_real_cli_output_including_the_health_banner() {
        let entries = parse_mcp_list(REAL_OUTPUT);
        assert_eq!(
            entries.len(),
            5,
            "the banner and blank line must be skipped"
        );

        assert_eq!(entries[0].name, "claude.ai Zapier");
        assert_eq!(entries[0].status, McpConnectionStatus::NeedsAuth);
        assert_eq!(entries[0].raw_status, "! Needs authentication");

        assert_eq!(entries[1].name, "claude.ai Slack");
        assert_eq!(entries[1].detail, "https://mcp.slack.com/mcp");
        assert_eq!(entries[1].status, McpConnectionStatus::Connected);

        assert_eq!(entries[2].name, "claude.ai Figma");
        assert_eq!(entries[2].detail, "https://mcp.figma.com/mcp");

        assert_eq!(entries[3].detail, "npx -y @vkhanhqui/figma-mcp-go@latest");
        assert_eq!(entries[4].name, "backlog");
    }

    /// A detail containing `" - "` must not be mangled — that's why the
    /// status is split from the right.
    #[test]
    fn a_detail_containing_the_separator_is_kept_whole() {
        let entries = parse_mcp_list("weird: npx run -- a - b --flag - ✔ Connected\n");
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].detail, "npx run -- a - b --flag");
        assert_eq!(entries[0].status, McpConnectionStatus::Connected);
    }

    #[test]
    fn an_unrecognised_status_is_reported_as_failed_with_its_own_words() {
        let entries = parse_mcp_list("broken: npx thing - ✗ Connection refused\n");
        assert_eq!(entries[0].status, McpConnectionStatus::Failed);
        assert_eq!(entries[0].raw_status, "✗ Connection refused");
    }

    /// The whole point of this module is being safe to put on screen.
    #[test]
    fn inline_secrets_are_masked_in_the_detail() {
        let entries =
            parse_mcp_list("srv: npx -e BACKLOG_API_KEY=supersecret -e PORT=1 x - ✔ Connected\n");
        assert!(!entries[0].detail.contains("supersecret"));
        assert!(entries[0].detail.contains("BACKLOG_API_KEY=***"));
        // Non-secret env stays readable.
        assert!(entries[0].detail.contains("PORT=1"));
    }

    #[test]
    fn masks_every_secret_shaped_key_but_leaves_ordinary_text_alone() {
        for (input, must_hide) in [
            ("API_TOKEN=abc", "abc"),
            ("--password=hunter2", "hunter2"),
            ("MY_SECRET=zzz", "zzz"),
            ("CREDENTIALS_FILE=/x/y", "/x/y"),
        ] {
            let redacted = redact_inline_secrets(input);
            assert!(!redacted.contains(must_hide), "leaked: {redacted}");
        }
        assert_eq!(
            redact_inline_secrets("npx -y server@1.2.3"),
            "npx -y server@1.2.3"
        );
    }

    #[test]
    fn empty_or_noise_only_output_yields_nothing_rather_than_junk_rows() {
        assert!(parse_mcp_list("").is_empty());
        assert!(parse_mcp_list("Checking MCP server health…\n\n").is_empty());
        assert!(parse_mcp_list("No MCP servers configured\n").is_empty());
    }
}
