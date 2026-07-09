---
name: sourcebase-reuse-first
description: Codebase exploration guidance that requires inspecting existing modules, patterns, DTOs, guards, repositories, tests, and scripts before adding new backend code.
metadata:
  stack: sourcebase, nestjs
---

# Sourcebase Reuse First

Use this skill before adding or changing backend code in an existing project.

## Exploration Order

1. Read `CLAUDE.md` and project docs if present.
2. Check whether a source-map tool is already configured:
   - `.codegraph/` exists: use `.claude/tools/codegraph.md`.
   - `.understand-anything/` exists: use `.claude/tools/understand-anything.md`.
   - Neither exists: use normal file and text search and report that no source-map setup is present.
3. Inspect `package.json` scripts and dependencies.
4. Find nearby modules with similar behavior.
5. Inspect existing controller, service, DTO, entity, migration, and test patterns.
6. Reuse naming, folder structure, exception shape, and response shape.
7. Add a new pattern only when no existing pattern fits.

## Search Targets

Use the fastest available project search. If a source-map tool exists, use it before broad manual search. Otherwise use normal file and text search.

Search for:

- Existing module folders under `src`.
- Existing guards and decorators.
- Existing DTO naming and pagination DTOs.
- Existing exception filters and response interceptors.
- Existing repository or data access providers.
- Existing migration file names and locations.
- Existing Jest and Supertest patterns.

## Reuse Rules

- Prefer established helpers over new abstractions.
- Keep edits close to the feature module.
- Do not rename or reshape unrelated files.
- Do not introduce a new library for behavior already covered by the project.
- Keep command names and scripts aligned with `package.json`.

## Source-Map Sync

After code changes, sync the source-map tool when it is configured:

- CodeGraph: run `codegraph sync` when available, or `codegraph init` if sync is not supported.
- Understand-Anything: run `/understand` to refresh the knowledge graph.

If no source-map tool is configured, skip this step and note that normal file search was used.

## Checklist

- [ ] Similar modules were inspected.
- [ ] Source-map tool was used when `.codegraph/` or `.understand-anything/` exists.
- [ ] Existing DTO and response patterns were followed.
- [ ] Existing test pattern was followed.
- [ ] Existing migration location was used.
- [ ] Source-map tool was synced after code changes when configured.
- [ ] No unrelated cleanup was mixed into the task.
