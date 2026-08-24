---
description: Review a backend change set before merge — architecture, security, database, cache, and tests.
argument-hint: [branch, PR, or paths]
---

# Code Review

**Request:** $ARGUMENTS

## Trigger

Use when reviewing a backend change set before merge.

## Steps

1. **Understand intent** - Read the requirement, acceptance criteria, API contract, and diff.
2. **Architecture review** - Dispatch **backend-reviewer** to check module boundaries, provider usage, service responsibilities, and response DTOs.
3. **Authorization review** - Apply the `backend-auth-authorization` skill. Confirm every read and write is scoped to the caller's tenant or ownership, inside the query.
4. **Security review** - Apply the `backend-security-review` skill.
5. **Database review** - Apply the `postgresql` skill for entities, migrations, transactions, and queries.
6. **Cache and performance review** - Apply the `backend-query-cache-performance` skill and the `redis-development` skill where relevant.
7. **Error and logging review** - Apply the `backend-error-logging` skill for status codes, swallowed failures, and log levels.
8. **Test review** - Apply the `nestjs-testing` skill.
9. **Findings** - Report blocker, should fix, and suggestion items with reason and fix direction.
10. **Re-check** - After changes, re-check every blocker and agreed should-fix item.

## Definition Of Done

- All blockers are resolved.
- Every read and write is scoped to the caller's tenant or ownership.
- Relevant security, database, cache, error handling, and test risks were reviewed.
- Findings are specific and actionable.
- The change is ready for merge from a backend review perspective.
