# Backend AI Kit

Reusable Claude Code configuration for NestJS backend projects. This kit is meant to be copied into a backend repository and used as a focused workflow layer for API, service, database, cache, test, and review work.

## 1. Target Stack

- NestJS with TypeScript
- REST APIs with JWT-based authorization
- PostgreSQL with TypeORM 0.3.x
- Redis for cache-aside use cases
- Jest and Supertest for unit and endpoint tests

This v1 intentionally focuses on application code and database work. It does not include cloud infrastructure, release automation, or multi-language backend guidance.

## 2. Install Into A Project

From this repository, copy the kit into the target backend project:

```bash
cp -r /path/to/dipro-ai-kit/backend-kit/.claude /path/to/your-backend-project/
```

If the target project already has `.claude/`, merge the folders manually:

```bash
cp -r backend-kit/.claude/agents   your-backend-project/.claude/
cp -r backend-kit/.claude/commands your-backend-project/.claude/
cp -r backend-kit/.claude/skills   your-backend-project/.claude/
cp -r backend-kit/.claude/tools    your-backend-project/.claude/
cp backend-kit/.claude/validate-kit.mjs your-backend-project/.claude/
```

Do not overwrite an existing `.claude/settings.json`. Merge the `permissions` block from `backend-kit/.claude/settings.json` into it by hand.

Expected structure after installation:

```text
your-backend-project/
|-- .claude/
|   |-- validate-kit.mjs
|   |-- settings.json
|   |-- agents/
|   |-- commands/
|   |-- skills/
|   `-- tools/
|-- src/
|-- package.json
`-- CLAUDE.md
```

Then run `node .claude/validate-kit.mjs` and restart Claude Code — see section 9.

## 3. Add Project Context

Create `CLAUDE.md` at the target project root from the template, then fill in every `<placeholder>`:

```bash
cp backend-kit/templates/CLAUDE.md.example your-backend-project/CLAUDE.md
```

The template covers the project overview, stack versions, an exact command table, module structure, conventions, doc links, and a **Process Precedence** section. Two fields matter more than they look:

- **Commands table** — agents copy commands from here instead of discovering them, which saves time on every task.
- **Redis client and TTL unit, TypeORM transaction mode** — the skills branch on these; a wrong guess means a TTL off by a factor of 1000 or a migration TypeORM refuses to run.

If the project already has `CLAUDE.md`, copy the sections it lacks.

### Using With Superpowers

If the superpowers plugin is installed, its brainstorming, planning, and TDD skills overlap with this kit's workflows. Running both asks the same questions twice. The **Process Precedence** section of the template tells Claude that inside a kit command the `backend-clarify-and-approve` skill replaces `superpowers:brainstorming`, and that `superpowers:writing-plans` is not run on top. Outside kit commands, superpowers applies as usual.

## 4. Optional Source-Map Setup

Source-map tools help agents understand the backend codebase before editing. They are optional: the kit still works with normal file and text search when no source-map tool is installed.

Setup guide:

```text
backend-kit/guideline/step1-install-source-map.md
```

Choose one:

- CodeGraph for fast source mapping in most NestJS projects.
- Understand-Anything for larger, legacy, or poorly documented projects.

When a target project contains `.codegraph/` or `.understand-anything/`, backend agents should use the matching source-map tool before broad manual search, then verify important findings by reading the source files.

With CodeGraph, every agent looks things up in the same order: the Context Brief, then `codegraph_explore`, then Grep and a targeted Read. The main agent puts one `codegraph_explore` result into the Context Brief as a **code map**, so subagents start from symbols and line ranges instead of reading whole files. The reviewer uses `codegraph impact` / `callers` for the blast radius of a diff, and the verify step uses `codegraph affected` to pick which tests to run.

All five agents list the MCP tool `mcp__codegraph__codegraph_explore` in `tools:`; register the server with `codegraph install --target claude` and confirm with `/mcp`. Without it, agents fall back to Grep and Read.

## 5. Commands

| Task | Command | Use When |
| --- | --- | --- |
| New backend feature | `/new-feature` | Build an endpoint, service, entity, or workflow from requirements |
| Bug fix | `/bug-fix` | Reproduce and fix incorrect backend behavior |
| Code review | `/code-review` | Review a change set before merge |
| Refactoring | `/refactoring` | Improve structure without behavior changes |
| Test generation | `/test-generation` | Add unit, service, or endpoint tests |
| API scaffold | `/generate-api` | Create a NestJS module, controller, service, DTOs, entity, and migration plan |
| Migration work | `/migration` | Add or review a TypeORM migration |
| Database review | `/db-review` | Review schema, query, index, transaction, and cache behavior |
| API contract | `/api-contract` | Produce a handoff-ready REST contract |

Examples:

```text
/new-feature Add order search with pagination, status filter, and role guard.
```

```text
/bug-fix Order list sorting breaks when orderBy is unknown.
```

```text
/generate-api inventory-items
```

### Workflow Overview

Agent models: `backend-architect` and `backend-reviewer` run on `opus` at `high` effort; `backend-analyst`, `backend-developer`, and `backend-tester` run on `sonnet` at `medium` effort.

| Command | Main model | Shortcut | Subagents (full path) |
| --- | --- | --- | --- |
| `/new-feature` | opus | Small path | (analyst) → architect → tester ∥ developer → reviewer |
| `/bug-fix` | sonnet | Small path | tester → developer → reviewer |
| `/generate-api` | sonnet | — | (architect) → tester ∥ developer → reviewer |
| `/refactoring` | opus | — | (architect) → (tester) → (developer) → reviewer |
| `/migration` | sonnet | — | (developer) → reviewer |
| `/code-review` | sonnet | Diff of 3 files or fewer is reviewed directly | reviewer |
| `/test-generation` | sonnet | One module is handled directly | (tester) |
| `/db-review`, `/api-contract` | sonnet | — | none |

`∥` = dispatched in parallel. `( )` = dispatched only when needed.

**Small path:** at most 3 production files, no migration, no contract, guard, or cache-key change. The main agent writes the test, implements, verifies, and self-reviews with no subagents.

**Execution mode:** the design-approval question also asks how to execute, like the superpowers plan handoff — **Approve — subagents** (recommended for Standard: tester ∥ developer) or **Approve — inline** (recommended for Small: the main agent writes the test, then the code). One question, no extra round trip. Standard work goes to `backend-reviewer` in either mode.

**Approval gate:** every code-changing workflow applies the `backend-clarify-and-approve` skill before implementation, modeled on the superpowers brainstorming flow. The main agent asks blocking questions one at a time through the question tool (multiple choice, recommended option first), states non-blocking assumptions, presents a design — a few sentences on the Small path, 2–3 approaches then a sectioned design on the Standard path — and waits for an explicit yes. Subagents never ask the user; the analyst and architect return questions to the main agent. If hidden complexity appears mid-task, the workflow stops and moves to the Standard path.

`/new-feature` in detail (the other workflows follow the same shape):

| Step | Who | Work | Tests |
| --- | --- | --- | --- |
| 0. Context Brief | Main | Explore the codebase once; classify Small or Standard | — |
| 1. Requirements | Analyst (only if requirements are vague) → main asks the user | Draft acceptance criteria; blocking questions asked one at a time; assumptions stated | — |
| 2. Approaches | Architect → main presents | 2–3 approaches with trade-offs; the user chooses | — |
| 3. Design and approval | Main | Sectioned design; **stop until the user approves** and picks subagents or inline | — |
| 4. Tests and implementation | Tester ∥ developer, or main (inline) | Subagents: tester edits test files only, developer edits production files only. Inline: main writes tests, then code | Focused test files |
| 5. Verify | Main | Send failures back to the developer | Lint, typecheck, relevant suite — once |
| 6. Review | Reviewer | Diff only; loads skills only for touched areas | No re-run of passing tests |
| 7. Finish | Main | `codegraph sync` once; change record if a condition matches | — |

## 6. Kit Layout

```text
.claude/
|-- validate-kit.mjs
|-- settings.json
|-- agents/
|   |-- backend-analyst.md
|   |-- backend-architect.md
|   |-- backend-developer.md
|   |-- backend-tester.md
|   `-- backend-reviewer.md
|-- commands/
|   |-- api-contract.md
|   |-- bug-fix.md
|   |-- code-review.md
|   |-- db-review.md
|   |-- generate-api.md
|   |-- migration.md
|   |-- new-feature.md
|   |-- refactoring.md
|   `-- test-generation.md
|-- tools/
|   |-- codegraph.md
|   `-- understand-anything.md
`-- skills/
    |-- backend-auth-authorization/
    |-- backend-clarify-and-approve/
    |-- backend-change-record/
    |-- backend-error-logging/
    |-- backend-query-cache-performance/
    |-- backend-security-review/
    |-- nestjs-best-practices/
    |-- nestjs-testing/
    |-- postgresql/
    |-- redis-development/
    |-- rest-api-contract/
    `-- sourcebase-reuse-first/
```

## 7. Speed

Workflow commands are built to avoid repeated work:

- **Small path.** `/new-feature` and `/bug-fix` classify the task first. A change touching at most 3 production files with no migration, contract, guard, or cache-key change runs in the main agent with no subagents.
- **Context Brief.** The main agent explores the codebase once and passes a code map (from CodeGraph when available), the file list, patterns, and commands to every subagent. Source in the code map counts as read.
- **Parallel work.** Tests and implementation are dispatched together when a design exists; the analyst is skipped when acceptance criteria are already clear.
- **Pinned models and effort.** Every agent and command sets `model:` in its frontmatter, so nothing falls back to the session model (for example Fable). Agents also set `effort:`, so a session running at `xhigh` or `max` does not make every subagent think at that level:

  | Agent | Model | Effort |
  | --- | --- | --- |
  | `backend-analyst` | `sonnet` | `medium` |
  | `backend-architect` | `opus` | `high` |
  | `backend-developer` | `sonnet` | `medium` |
  | `backend-tester` | `sonnet` | `medium` |
  | `backend-reviewer` | `opus` | `high` |

  | Command | Model |
  | --- | --- |
  | `/new-feature`, `/refactoring` | `opus` |
  | all other commands | `sonnet` |

  Commands do not set effort — command frontmatter does not document an `effort` field — so the main agent runs at the session effort. `/effort high` is a good default; `xhigh` and `max` make every workflow noticeably slower. Effort does not adjust itself per task: the model decides how much to think *within* the configured level.

  Change a field to use a different model or effort. Removing it makes that agent or command inherit the session value again.
- **Skills on demand.** Agents load a skill only when the change touches its area.
- **Tests.** Focused test files run during work; the relevant suite runs once before review.
- **Fewer permission prompts.** `.claude/settings.json` pre-allows test, lint, typecheck, build, read-only git, and CodeGraph commands. Migrations and package installs still ask; `git push`, `npm publish`, and reading `.env` files are denied. Adjust the patterns to the project's package manager and script names.
- **One turn per workflow.** Questions and the design approval go through the question tool, so the workflow stays in one turn and keeps the command's model. A plain-text question would end the turn and hand the rest of the work to the session model.

Things you can do in the target project:

- Put the exact test, lint, typecheck, and migration commands in `CLAUDE.md`, so agents do not have to discover them.
- For a one-line change, ask Claude directly instead of running a workflow command.
- Use `/fast` for faster output on long sessions.
- Keep the session at `/effort high` or lower; commands inherit it.

## 8. What The Kit Writes

Commands that change code end with a change record at
`docs/backend/changes/YYYY-MM-DD-<topic>.md`, written only when the diff adds a
migration, alters a request or response shape, adds a route or cache key, leaves
something unverified, or leaves a known problem alone. Trivial changes produce no
file, so the directory stays worth reading.

The record carries what a diff cannot — which consumers a breaking change affects,
what a rollback destroys, which commands were never run, and which problems were
found and deliberately left. Review commands (`/code-review`, `/db-review`,
`/api-contract`, `/test-generation`) write no record; they produce findings, not
changes to hand over.

## 9. Verify The Kit After Installing

The agents, commands, and skills only work if their frontmatter is well formed. A
missing `name`, or a `: ` inside an unquoted description, silently stops a file from
registering — the kit looks installed and does nothing.

```bash
node .claude/validate-kit.mjs
```

It checks required frontmatter fields, `name` against filename and directory, YAML
scalars that would fail to parse, `model:` and `effort:` values, every agent, skill, and command
reference (including references between skills), and that `settings.json` is valid JSON. Exit
code 1 on any problem, so it drops straight into a pre-commit hook or CI step.

Agents are registered as dispatchable subagents, and **the agent registry is read once
at session start**. After installing or editing anything under `.claude/agents/`,
restart Claude Code and confirm with `/agents` that all five appear. Skills and
commands reload without a restart; agents do not.

## 10. Core Rules

- Inspect existing project patterns before adding modules, entities, migrations, or cache keys.
- Use a configured source-map tool before broad manual search when `.codegraph/` or `.understand-anything/` exists.
- Explore the codebase once per task and pass a Context Brief to subagents instead of letting each one re-explore.
- Sync the source-map tool once at the end of a task (CodeGraph only; Understand-Anything is refreshed by the user).
- Organize NestJS by feature modules, not technical layers.
- Validate request DTOs with `class-validator`; serialize responses through DTOs.
- Do not return raw entities from controllers.
- Keep TypeORM `synchronize` disabled outside throwaway local experiments.
- Use UUID primary keys, explicit `snake_case` database names, `timestamptz`, and `deleted_at`.
- Every migration needs both `up()` and `down()`.
- Migrations on large tables avoid long locks: concurrent indexes, nullable-then-backfill, expand and contract.
- Guard concurrent writes to the same row with a version column, a lock, an atomic update, or a unique constraint.
- Whitelist dynamic sort fields before passing them to QueryBuilder.
- Avoid N+1 queries with joins, batched lookups, or explicit relation loading.
- Use transactions for multi-table writes.
- Redis cache keys must have TTL (in the client's unit) and must be invalidated after the write commits. A Redis failure falls back to the database.
- Use `ValidationPipe` with `whitelist` and `forbidNonWhitelisted`; cap `limit` on list endpoints.
- Test tenant scope, QueryBuilder logic, and constraints against a real database, with two tenants.
- Bug fixes need a failing regression test first, except documented micro-fixes.
