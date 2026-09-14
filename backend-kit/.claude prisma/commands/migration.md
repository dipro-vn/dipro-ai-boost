---
description: Add, edit, or review a Prisma schema change and the migration it generates.
---

# Migration

## Trigger

Use when adding, editing, or reviewing Prisma schema changes and the migrations they generate.

## Delegation

Run each step named below through that subagent with the Agent tool (`subagent_type`), and wait for its result before the next step. Do not read the agent file and play the role yourself - the point of the split is that each agent gets a clean context and its own tool limits.

## Steps

1. **Inspect current schema pattern** - Use the `sourcebase-reuse-first` skill to read `prisma/schema.prisma`, existing migrations in `prisma/migrations/`, naming conventions, and `package.json` scripts.
2. **Design schema change** - Use the `postgresql` skill to define models, fields, indexes, relations, `onDelete` behavior, soft delete, and the reverse migration.
3. **Edit the schema** - the `backend-developer` subagent edits `prisma/schema.prisma` only. Never hand-write SQL into an existing migration folder.
4. **Generate the migration** - Run `npx prisma migrate dev --name <change_name>`, then review the generated `migration.sql` before committing it.
5. **Regenerate the client** - Run `npx prisma generate` so `Prisma.*` types and scalar field enums match the schema.
6. **Update dependent code** - Align repositories, DTOs, response DTOs, and `SOFT_DELETE_MODEL_NAMES` (`src/services/prisma/prisma.config.ts`) with the new schema.
7. **Verify** - Run `npm run build` and the affected tests.
8. **Review** - the `backend-reviewer` subagent checks the reverse plan, index coverage, data safety, and query impact.

## Rollback Rule

Prisma migrations are **forward-only**. There is no `down()`.

- Rollback means a new forward migration that reverses the change. Write down that reverse migration in the plan **before** applying a destructive change.
- Split destructive changes (drop column, drop table, narrow a type, add `NOT NULL` to a populated table) into: add new shape → backfill → remove old shape in a later migration.
- `prisma migrate reset` drops all data. It is for local development only, never for shared or production databases.
- Never edit or delete a migration that has already been applied outside your machine.

## Definition Of Done

- `prisma/schema.prisma` is the only source of the schema change.
- Generated `migration.sql` has been read and is correct.
- A reverse migration is written down, or the change is documented as non-destructive.
- `npx prisma generate` has been run and the build passes.
- Indexes cover expected query paths.
- Soft delete, timestamp, and relation conventions are followed.
- New soft-delete models are registered in `SOFT_DELETE_MODEL_NAMES`.
- Affected tests pass.
