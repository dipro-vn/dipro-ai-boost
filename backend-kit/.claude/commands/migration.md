---
description: Add or review a TypeORM migration and keep the entity aligned with the schema change.
argument-hint: <schema change description>
---

# Migration

**Request:** $ARGUMENTS

## Trigger

Use when adding, editing, or reviewing TypeORM migrations and related entities.

## Steps

1. **Inspect current schema pattern** - Use the `sourcebase-reuse-first` skill to find migration location, naming, entity conventions, and script commands.
2. **Design schema change** - Use the `postgresql` skill to define tables, columns, indexes, relations, soft delete, and rollback.
3. **Implement migration** - Dispatch **backend-developer** to write `up()` and `down()` using project conventions.
4. **Update entity** - Keep entity names, column names, relation names, and types aligned with the migration.
5. **Verify** - Run the project migration or test command available for schema checks.
6. **Review** - Dispatch **backend-reviewer** to check rollback, index coverage, data safety, and query impact.

## Definition Of Done

- Migration has both `up()` and `down()`.
- Entity and migration match.
- Indexes cover expected query paths.
- Soft delete and timestamp conventions are followed.
- Rollback is meaningful.
- Verification command has been run or the missing command is documented.
