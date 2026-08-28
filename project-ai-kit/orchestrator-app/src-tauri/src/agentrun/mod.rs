pub mod cli_path;
pub mod import_filter;
pub mod process_group;
pub mod process_registry;
pub mod procutil;
pub mod readiness;
pub mod recovery;
pub mod run_log;
pub mod runner;
pub mod spawn;
pub mod stream_parser;

/// Shared by `spawn`'s and `runner`'s live-call tests — real `claude`
/// spawns need `--agent <name>` to resolve to a `.claude/agents/<name>.md`
/// discoverable from `cwd`. A bare `tempfile::tempdir()` has no such file
/// anywhere in its ancestry, which is exactly what broke these tests once
/// `SpawnParams` started requiring `agent_name` (see A5/spike history) —
/// this gives them a minimal, self-contained project to spawn against
/// instead of depending on the outer kit repo's real `ba-agent.md`.
#[cfg(test)]
pub(crate) mod test_support {
    pub fn agent_project_dir(name: &str) -> tempfile::TempDir {
        let tmp = tempfile::tempdir().unwrap();
        let agent_path = tmp.path().join(".claude/agents").join(format!("{name}.md"));
        std::fs::create_dir_all(agent_path.parent().unwrap()).unwrap();
        std::fs::write(
            &agent_path,
            format!(
                "---\nname: {name}\ndescription: Test fixture agent for orchestrator-app's own tests — not a copy of the kit's real agents.\nmodel: claude-haiku-4-5\ntools:\n  - Read\n  - Write\n---\n\nYou are a minimal test agent. When asked to do something simple and concrete, just do it directly and briefly — no explanation.\n"
            ),
        )
        .unwrap();
        tmp
    }
}
