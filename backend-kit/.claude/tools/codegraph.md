# CodeGraph

Use CodeGraph when the target backend repository has a `.codegraph/` directory at the project root.

CodeGraph helps agents answer source questions with symbol-level context and call paths before editing code. It is especially useful for tracing NestJS request flow across controllers, services, repositories, guards, interceptors, and tests.

## When To Use

Use CodeGraph before broad manual search when you need to:

- Locate a module, provider, DTO, entity, migration, or test.
- Trace a request flow from controller to service to data access.
- Understand which files are affected by an interface or contract change.
- Find existing project conventions before generating new code.

## Setup For Agents

The CLI alone is not enough for every agent. `backend-analyst` and `backend-architect` have no Bash, so they reach CodeGraph only through its MCP server. Register it once per machine:

```bash
codegraph install --target claude
```

Then confirm with `/mcp` in Claude Code that `codegraph` is connected. Every kit agent lists `mcp__codegraph__codegraph_explore` in its `tools:`.

## What To Use When

| Need | Call | Who |
| --- | --- | --- |
| Understand a flow, find symbols, see source before an edit | `codegraph_explore` (MCP) or `codegraph explore "<symbols>"` | Everyone — first, before Grep or Read |
| One symbol with its callers and callees | `codegraph node <symbol>` | Agents with Bash |
| Who calls a symbol | `codegraph callers <symbol>` | Reviewer, developer |
| What a change to a symbol affects | `codegraph impact <symbol>` | Reviewer |
| Which tests depend on changed files | `codegraph affected --quiet <files>` | Tester, verify step |
| Refresh the index after code changes | `codegraph sync` | Main agent, once at the end |

`codegraph_explore` returns the verbatim source of the relevant symbols plus the call path between them. Treat that source as already read — re-opening the same files wastes the tokens the tool just saved.

Query with symbol and file names spanning the flow, for example:

```bash
codegraph explore "OrdersController OrdersService OrdersRepository findAll"
```

If `codegraph sync` is unavailable in the installed version, re-run `codegraph init`.

## Rules

- If `.codegraph/` does not exist, skip CodeGraph and use normal file search.
- Do not install or initialize CodeGraph unless the user asks for setup.
- Verify important CodeGraph findings by reading the source file before editing.
- Do not commit generated CodeGraph output unless the project explicitly tracks it.
