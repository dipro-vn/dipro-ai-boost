//! AC-E1-25..27 — reads the PROJECT'S OWN MCP server configuration
//! (`<agents_root>/.mcp.json` and/or `<agents_root>/.claude/settings.json`,
//! both keyed `mcpServers` — shapes verified against the kit's real
//! `.claude/settings.json`, not assumed) and reports it read-only.
//!
//! SECURITY: an MCP entry's `env` block can contain real credentials (the
//! kit's own `backlog` server declares `BACKLOG_API_KEY` there). Nothing
//! from `env` is ever included in the output — `detail` carries only the
//! command+args or the URL.

use std::path::Path;

use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum McpServerKind {
    Stdio,
    Http,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct McpServer {
    pub name: String,
    pub kind: McpServerKind,
    /// Human-readable identification only: `command arg1 arg2...` for
    /// stdio, the URL for http. NEVER env values.
    pub detail: String,
    /// AC-E1-26/B18 — detected by the project's actual configuration
    /// (name/command/url containing "figma", case-insensitive), never by
    /// assuming a fixed server name.
    pub figma_candidate: bool,
}

/// An MCP server's name as it appears inside a tool id
/// (`mcp__<prefix>__<tool>`), which is what an agent file's `tools:`
/// allowlist has to spell out.
///
/// The rule is the CLI's own: every character outside `A-Za-z0-9_-` becomes
/// `_`. So `claude.ai Figma` → `claude_ai_Figma` while `figma-bridge` is
/// already its own prefix. Exists because the app has to compare the
/// server a project actually configured against the literal names the kit's
/// agent files declare — a mismatch there blocks every tool call of that
/// server, silently.
pub fn mcp_tool_prefix(server_name: &str) -> String {
    server_name
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '_' || c == '-' {
                c
            } else {
                '_'
            }
        })
        .collect()
}

fn parse_servers(raw: &str) -> Vec<McpServer> {
    let Ok(value) = serde_json::from_str::<serde_json::Value>(raw) else {
        return Vec::new();
    };
    let Some(servers) = value.get("mcpServers").and_then(|v| v.as_object()) else {
        return Vec::new();
    };

    servers
        .iter()
        .filter_map(|(name, entry)| {
            let (kind, detail) = if let Some(url) = entry.get("url").and_then(|v| v.as_str()) {
                (McpServerKind::Http, url.to_string())
            } else {
                // Unrecognized entry shape (no url, no command) — skip,
                // don't fail the whole list.
                let command = entry.get("command").and_then(|v| v.as_str())?;
                let args = entry
                    .get("args")
                    .and_then(|v| v.as_array())
                    .map(|arr| {
                        arr.iter()
                            .filter_map(|a| a.as_str())
                            .collect::<Vec<_>>()
                            .join(" ")
                    })
                    .unwrap_or_default();
                let detail = if args.is_empty() {
                    command.to_string()
                } else {
                    format!("{command} {args}")
                };
                (McpServerKind::Stdio, detail)
            };

            let haystack = format!("{name} {detail}").to_lowercase();
            Some(McpServer {
                name: name.clone(),
                kind,
                detail,
                figma_candidate: haystack.contains("figma"),
            })
        })
        .collect()
}

/// How far up from `agents_root` to look. The `claude` CLI walks all the
/// way to the filesystem root; this stops at a fixed depth so a project
/// nested under a home directory can't start picking up unrelated files
/// from `~` or `/`.
const MAX_ANCESTOR_DEPTH: usize = 4;

/// Merges `.mcp.json` and `.claude/settings.json` (AC-E1-25), starting at
/// `agents_root` and **walking up its ancestors** — the same resolution
/// `claude` itself does, and the same walk-up shape
/// `commands::project::find_agents_md` already uses.
///
/// The walk matters: a workspace commonly declares its MCP servers once at
/// the top (`<workspace>/.mcp.json`) while `agentsRoot` points at a repo
/// inside it. Looking only at `agentsRoot` reported "no MCP servers" for
/// exactly that layout, which then blocked `design-analyst` for a project
/// whose Figma server was configured perfectly well one directory up.
///
/// Nearest file wins on a name collision, and within one directory
/// `.mcp.json` beats `.claude/settings.json` (the more project-local file).
pub fn read_mcp_servers(agents_root: &Path) -> Vec<McpServer> {
    let mut servers: Vec<McpServer> = Vec::new();
    let mut seen: std::collections::HashSet<String> = std::collections::HashSet::new();

    let mut dirs: Vec<&Path> = Vec::new();
    let mut current = Some(agents_root);
    while let Some(dir) = current {
        dirs.push(dir);
        if dirs.len() > MAX_ANCESTOR_DEPTH {
            break;
        }
        current = dir.parent();
    }

    for dir in dirs {
        for path in [
            dir.join(".mcp.json"),
            dir.join(".claude").join("settings.json"),
        ] {
            let Ok(raw) = std::fs::read_to_string(&path) else {
                continue;
            };
            for server in parse_servers(&raw) {
                if seen.insert(server.name.clone()) {
                    servers.push(server);
                }
            }
        }
    }

    servers
}

#[cfg(test)]
mod tests {
    /// The exact normalization the CLI documents for `mcp__<server>__<tool>`
    /// ids. Getting this wrong means comparing a project's server against an
    /// agent's `tools:` list and silently concluding "not declared".
    #[test]
    fn mcp_tool_prefix_matches_the_documented_normalization() {
        use super::mcp_tool_prefix;
        // Dots and spaces become `_`; the connector's real name.
        assert_eq!(mcp_tool_prefix("claude.ai Figma"), "claude_ai_Figma");
        // Hyphens and underscores survive — already valid in a tool id.
        assert_eq!(mcp_tool_prefix("figma-bridge"), "figma-bridge");
        assert_eq!(mcp_tool_prefix("figma_bridge"), "figma_bridge");
        assert_eq!(mcp_tool_prefix("figma"), "figma");
        // Case is preserved, only invalid characters are replaced.
        assert_eq!(mcp_tool_prefix("Figma/Dev Mode"), "Figma_Dev_Mode");
    }

    use super::*;

    /// Mirrors the kit's real `.claude/settings.json` shape (stdio with
    /// args+env, http with type+url).
    const REAL_SHAPE: &str = r#"{
        "mcpServers": {
            "tilth": { "command": "tilth", "args": ["--mcp"] },
            "figma": { "type": "http", "url": "http://127.0.0.1:3845/mcp" },
            "backlog": {
                "command": "npx",
                "args": ["-y", "@nulab/backlog-mcp-server"],
                "env": { "BACKLOG_DOMAIN": "", "BACKLOG_API_KEY": "sk-secret-value" }
            }
        }
    }"#;

    #[test]
    fn parses_stdio_and_http_shapes_and_detects_figma() {
        let servers = parse_servers(REAL_SHAPE);
        assert_eq!(servers.len(), 3);

        let figma = servers.iter().find(|s| s.name == "figma").unwrap();
        assert_eq!(figma.kind, McpServerKind::Http);
        assert!(figma.figma_candidate);
        assert_eq!(figma.detail, "http://127.0.0.1:3845/mcp");

        let tilth = servers.iter().find(|s| s.name == "tilth").unwrap();
        assert_eq!(tilth.kind, McpServerKind::Stdio);
        assert!(!tilth.figma_candidate);
        assert_eq!(tilth.detail, "tilth --mcp");
    }

    #[test]
    fn env_values_never_leak_into_output() {
        let servers = parse_servers(REAL_SHAPE);
        let serialized = serde_json::to_string(&servers).unwrap();
        assert!(!serialized.contains("sk-secret-value"));
        assert!(!serialized.contains("BACKLOG_API_KEY"));
    }

    #[test]
    fn figma_detected_by_command_or_url_not_just_name() {
        let by_url =
            r#"{"mcpServers":{"design-server":{"type":"http","url":"https://mcp.figma.com/x"}}}"#;
        let servers = parse_servers(by_url);
        assert!(servers[0].figma_candidate);
    }

    #[test]
    fn garbage_or_missing_files_yield_empty_not_error() {
        assert!(parse_servers("not json").is_empty());
        assert!(parse_servers(r#"{"other": 1}"#).is_empty());
        let tmp = tempfile::tempdir().unwrap();
        assert!(read_mcp_servers(tmp.path()).is_empty());
    }

    #[test]
    fn merge_prefers_mcp_json_on_name_collision() {
        let tmp = tempfile::tempdir().unwrap();
        std::fs::write(
            tmp.path().join(".mcp.json"),
            r#"{"mcpServers":{"figma":{"type":"http","url":"http://from-mcp-json/mcp"}}}"#,
        )
        .unwrap();
        std::fs::create_dir_all(tmp.path().join(".claude")).unwrap();
        std::fs::write(
            tmp.path().join(".claude/settings.json"),
            r#"{"mcpServers":{"figma":{"type":"http","url":"http://from-settings/mcp"},"tilth":{"command":"tilth"}}}"#,
        )
        .unwrap();

        let servers = read_mcp_servers(tmp.path());
        assert_eq!(servers.len(), 2);
        let figma = servers.iter().find(|s| s.name == "figma").unwrap();
        assert_eq!(figma.detail, "http://from-mcp-json/mcp");
    }

    /// The reported bug: `.mcp.json` sitting one directory ABOVE
    /// `agentsRoot` (the common workspace layout) was invisible, so the app
    /// insisted the project had no Figma MCP and blocked design-analyst.
    #[test]
    fn finds_mcp_json_declared_in_an_ancestor_of_agents_root() {
        let tmp = tempfile::tempdir().unwrap();
        let workspace = tmp.path();
        let agents_root = workspace.join("kit-repo");
        std::fs::create_dir_all(&agents_root).unwrap();
        std::fs::write(
            workspace.join(".mcp.json"),
            r#"{"mcpServers":{"figma-bridge":{"command":"npx","args":["-y","mcp-figma-bridge"]}}}"#,
        )
        .unwrap();

        let servers = read_mcp_servers(&agents_root);

        assert_eq!(servers.len(), 1);
        assert_eq!(servers[0].name, "figma-bridge");
        assert!(
            servers[0].figma_candidate,
            "and it still counts as a Figma server"
        );
    }

    /// Nearest declaration wins, so a project can override a workspace-wide
    /// server without editing the shared file.
    #[test]
    fn a_nearer_declaration_shadows_the_same_name_higher_up() {
        let tmp = tempfile::tempdir().unwrap();
        let workspace = tmp.path();
        let agents_root = workspace.join("kit-repo");
        std::fs::create_dir_all(&agents_root).unwrap();
        std::fs::write(
            workspace.join(".mcp.json"),
            r#"{"mcpServers":{"shared":{"command":"outer"},"only-outer":{"command":"outer2"}}}"#,
        )
        .unwrap();
        std::fs::write(
            agents_root.join(".mcp.json"),
            r#"{"mcpServers":{"shared":{"command":"inner"}}}"#,
        )
        .unwrap();

        let servers = read_mcp_servers(&agents_root);

        let shared = servers.iter().find(|s| s.name == "shared").unwrap();
        assert!(
            shared.detail.contains("inner"),
            "nearest wins: {}",
            shared.detail
        );
        assert!(
            servers.iter().any(|s| s.name == "only-outer"),
            "ancestors still contribute"
        );
    }

    /// The walk must not climb forever — a deeply nested project would
    /// otherwise start reading unrelated files from the home directory.
    #[test]
    fn the_ancestor_walk_is_depth_limited() {
        let tmp = tempfile::tempdir().unwrap();
        let deep = tmp.path().join("a/b/c/d/e/f");
        std::fs::create_dir_all(&deep).unwrap();
        std::fs::write(
            tmp.path().join(".mcp.json"),
            r#"{"mcpServers":{"too-far":{"command":"x"}}}"#,
        )
        .unwrap();

        assert!(read_mcp_servers(&deep).is_empty());
    }
}
