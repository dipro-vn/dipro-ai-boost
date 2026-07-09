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
2. Inspect `package.json` scripts and dependencies.
3. Find nearby modules with similar behavior.
4. Inspect existing controller, service, DTO, entity, migration, and test patterns.
5. Reuse naming, folder structure, exception shape, and response shape.
6. Add a new pattern only when no existing pattern fits.

## Search Targets

Use the fastest available project search. If a source-map tool exists, it may be used. Otherwise use normal file and text search.

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

## Checklist

- [ ] Similar modules were inspected.
- [ ] Existing DTO and response patterns were followed.
- [ ] Existing test pattern was followed.
- [ ] Existing migration location was used.
- [ ] No unrelated cleanup was mixed into the task.
