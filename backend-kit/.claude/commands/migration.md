---
description: Use when the user asks to change the database schema — a table, column, index, or constraint — with its TypeORM migration. Triggers — thêm cột, đổi bảng, thêm index, migration, schema, カラム追加, マイグレーション.
argument-hint: <schema change description>
model: sonnet
---

# Migration

**Request:** $ARGUMENTS

## Trigger

Use when adding, editing, or reviewing TypeORM migrations and related entities.

## Process Precedence

This command is the process for this task. Its design and approval step is the `backend-clarify-and-approve` skill — do not also run `superpowers:brainstorming`, `superpowers:writing-plans`, or `superpowers:subagent-driven-development`.

## Execution Mode

The approval question of the `backend-clarify-and-approve` skill also picks the execution mode. **Subagents**: dispatch the tester and developer steps as written below. **Inline**: the main agent performs those steps itself, in the same order — test first, then implementation — and still dispatches **backend-reviewer** for the review step.

## Steps

1. **Context (main agent)** — find the migration location, naming, entity conventions, and migration commands. Read the latest migration and the affected entity; do not scan the whole codebase.
2. **Design schema change** — use the `postgresql` skill to define tables, columns, indexes, relations, soft delete, and rollback. If the table is large or live, follow the skill's large-table rules (concurrent index, nullable then backfill, expand and contract) and ask the user for the approximate row count if it is unknown.
2b. **Approve** — apply the `backend-clarify-and-approve` skill: ask about data that the change could destroy or backfill, present the schema change and its rollback, and stop until the user approves.
3. **Implement** — write `up()` and `down()` and update the entity in the same step, so names and types stay aligned. Do this directly for a single-table change; dispatch **backend-developer** with the design only when several tables or a data backfill are involved.
4. **Verify** — run the project migration command (run, then revert, then run) or the available schema check.
5. **Review** — dispatch **backend-reviewer** to check rollback, index coverage, data safety, and query impact. Pass the migration, the entity diff, and the verification output.
6. **Record** — invoke the `backend-change-record` skill. Write the record only if the diff matches one of its conditions.

## Definition Of Done

- Migration has both `up()` and `down()`.
- Entity and migration match.
- Indexes cover expected query paths.
- Soft delete and timestamp conventions are followed.
- Rollback is meaningful.
- Verification command has been run or the missing command is documented.
- A change record exists, or no record condition was matched.
