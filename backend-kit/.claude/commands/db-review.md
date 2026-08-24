---
description: Review database-facing backend changes — entities, migrations, queries, indexes, transactions, cache.
argument-hint: [module, migration, or endpoint]
---

# Database Review

**Request:** $ARGUMENTS

## Trigger

Use when reviewing database-facing backend changes: entities, migrations, repositories, QueryBuilder logic, indexes, transactions, list endpoints, and Redis cache interaction.

## Steps

1. **Read the query path** - Identify endpoint, service method, repository call, entity, migration, and cache keys.
2. **Schema review** - Apply the `postgresql` skill.
3. **Performance review** - Apply the `backend-query-cache-performance` skill.
4. **Cache review** - Apply the `redis-development` skill if Redis is involved.
5. **Safety review** - Confirm ownership scope, transactions, soft delete behavior, and broad update/delete filters.
6. **Report findings** - Classify blocker, should fix, and suggestion items.

## Definition Of Done

- Schema conventions are checked.
- Query and index fit are checked.
- N+1 risk is checked.
- Transaction boundaries are checked.
- Cache TTL and invalidation are checked where relevant.
- Findings include concrete fix directions.
