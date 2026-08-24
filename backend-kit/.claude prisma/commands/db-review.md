---
description: Review database-facing changes - Prisma models, migrations, indexes, query paths, and transactions.
---

# Database Review

## Trigger

Use when reviewing database-facing backend changes: Prisma models, migrations, repositories, query logic, indexes, transactions, and list endpoints.

## Steps

1. **Read the query path** - Identify endpoint, service method, repository call, Prisma model, and migration.
2. **Schema review** - Apply the `postgresql` skill.
3. **Performance review** - Apply the `backend-query-performance` skill.
4. **Safety review** - Confirm ownership scope, transactions, soft delete middleware coverage, raw-query safety, and broad `updateMany` / `deleteMany` filters.
5. **Report findings** - Classify blocker, should fix, and suggestion items.

## Definition Of Done

- Schema conventions are checked.
- Query and index fit are checked.
- N+1 risk is checked.
- Transaction boundaries are checked.
- Findings include concrete fix directions.
