---
description: Use when the user asks to review a backend change set, branch, or PR before merge. Triggers — review, xem lại code, check PR, レビュー.
argument-hint: [branch, PR, or paths]
model: sonnet
---

# Code Review

**Request:** $ARGUMENTS

## Trigger

Use when reviewing a backend change set before merge.

## Steps

1. **Understand intent (main agent)** — read the requirement, acceptance criteria, API contract, and diff. List which areas the diff touches: controllers/DTOs, auth and ownership, input and output, database, cache, errors and logs, tests.
2. **Review** — for a small diff (at most 3 files), review directly. Otherwise dispatch **backend-reviewer** once with the diff, the intent, and the list of touched areas. Either way, apply only the skills for the touched areas:
   - Controllers, services, DTOs — the `nestjs-best-practices` skill.
   - Routes, guards, owned data — the `backend-auth-authorization` skill. Confirm every read and write is scoped to the caller's tenant or ownership, inside the query.
   - External input, output shaping, logging — the `backend-security-review` skill.
   - Entities, migrations, queries, transactions — the `postgresql` skill.
   - List endpoints, heavy reads, cache — the `backend-query-cache-performance` skill and the `redis-development` skill.
   - Exceptions, error responses, logs — the `backend-error-logging` skill.
   - Tests — the `nestjs-testing` skill.
3. **Findings** — report blocker, should fix, and suggestion items with reason and fix direction. State which areas were out of scope for this diff.
4. **Re-check** — after changes, re-check every blocker and agreed should-fix item.

## Definition Of Done

- All blockers are resolved.
- Every read and write is scoped to the caller's tenant or ownership.
- Relevant security, database, cache, error handling, and test risks were reviewed.
- Findings are specific and actionable.
- The change is ready for merge from a backend review perspective.
