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
4. Inspect existing controller, service, repository, DTO, Prisma model, migration, and test patterns.
5. Reuse naming, folder structure, exception shape, and response shape.
6. Add a new pattern only when no existing pattern fits.

## Search Targets

Use normal file and text search - `Glob` for structure, `Grep` for symbols and usages.

Search for:

- Existing module folders under `src`.
- Existing guards and decorators.
- Existing DTO naming and pagination DTOs.
- Existing exception filters and response interceptors.
- Existing feature repositories wrapping `PrismaService`.
- `prisma/schema.prisma` models and `prisma/migrations/` naming.
- Existing Jest and Supertest patterns.

## Reuse Rules

- Prefer established helpers over new abstractions.
- Keep edits close to the feature module.
- Do not rename or reshape unrelated files.
- Do not introduce a new library for behavior already covered by the project.
- Keep command names and scripts aligned with `package.json`.

## Optional Source-Map Tools

**This project has neither, so skip this section here.** It applies only when the kit is used in a repository that has already set one up.

If `.codegraph/` exists at the project root, read `.claude/tools/codegraph.md` and use CodeGraph before broad manual search, then run `codegraph sync` after code changes. If `.understand-anything/` exists, read `.claude/tools/understand-anything.md` and use `/understand-chat`, then run `/understand` to refresh.

Never install or initialize either tool unless the user asks for setup.

## Checklist

- [ ] Similar modules were inspected.
- [ ] Existing DTO and response patterns were followed.
- [ ] Existing test pattern was followed.
- [ ] Schema changes went through `prisma/schema.prisma` and `prisma migrate dev`.
- [ ] No unrelated cleanup was mixed into the task.
