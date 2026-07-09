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
```

Expected structure after installation:

```text
your-backend-project/
|-- .claude/
|   |-- agents/
|   |-- commands/
|   |-- skills/
|   `-- tools/
|-- src/
|-- package.json
`-- CLAUDE.md
```

## 3. Add Project Context

Create or update `CLAUDE.md` at the target project root. Keep it short and project-specific:

```text
You are working in a NestJS backend project.

Include:
1. Project overview and domain boundaries
2. Tech stack with versions
3. Install, dev, build, lint, test, and migration commands
4. Module structure and naming conventions
5. Auth, database, cache, and error response conventions
6. Documentation links for API contracts and feature specs
```

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

## 6. Kit Layout

```text
.claude/
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
    |-- backend-query-cache-performance/
    |-- backend-security-review/
    |-- nestjs-best-practices/
    |-- nestjs-testing/
    |-- postgresql/
    |-- redis-development/
    |-- rest-api-contract/
    `-- sourcebase-reuse-first/
```

## 7. Core Rules

- Inspect existing project patterns before adding modules, entities, migrations, or cache keys.
- Use a configured source-map tool before broad manual search when `.codegraph/` or `.understand-anything/` exists.
- Sync the source-map tool after code changes when the tool supports syncing.
- Organize NestJS by feature modules, not technical layers.
- Validate request DTOs with `class-validator`; serialize responses through DTOs.
- Do not return raw entities from controllers.
- Keep TypeORM `synchronize` disabled outside throwaway local experiments.
- Use UUID primary keys, explicit `snake_case` database names, `timestamptz`, and `deleted_at`.
- Every migration needs both `up()` and `down()`.
- Whitelist dynamic sort fields before passing them to QueryBuilder.
- Avoid N+1 queries with joins, batched lookups, or explicit relation loading.
- Use transactions for multi-table writes.
- Redis cache keys must have TTL and must be invalidated after writes.
- Bug fixes need a failing regression test first, except documented micro-fixes.
