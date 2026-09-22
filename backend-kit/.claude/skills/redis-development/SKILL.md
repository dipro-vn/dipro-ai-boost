---
name: redis-development
description: Use when adding a cache read, or writing to data that is already cached. Symptoms — a new cache key, a set call without TTL, a write path with no invalidation, cached data that differs per tenant or user, stale data reported after an update.
metadata:
  stack: redis
---

# Redis Development

Use this skill when adding or reviewing Redis cache behavior in a NestJS backend.

## Cache-Aside Pattern

1. Build a deterministic key.
2. Try Redis first.
3. If cache is missing, query PostgreSQL.
4. Store serialized data with TTL.
5. Return the data.

```typescript
const key = `orders:company:${companyId}`;
const cached = await this.safeGet<OrderListItemDto[]>(key);
if (cached) {
  return cached;
}

const rows = await this.orderRepository.findByCompany(companyId);
const items = rows.map(OrderListItemDto.fromEntity); // cache the DTO, never the entity
await this.safeSet(key, items, 300_000); // @nestjs/cache-manager 2+ — TTL in milliseconds
return items;
```

## TTL Units Depend On The Client

Read `package.json` before writing a TTL. The same number means different things:

| Client | Call | TTL unit |
| --- | --- | --- |
| `cache-manager` 4 | `set(key, value, { ttl: 300 })` | seconds |
| `cache-manager` 5+ / `@nestjs/cache-manager` 2+ | `set(key, value, 300_000)` | milliseconds |
| `ioredis` | `set(key, value, 'EX', 300)` | seconds |

A seconds value passed to a milliseconds API expires in under a second; the reverse keeps data for days.

## Redis Down Must Not Mean Service Down

The cache is an optimization. A Redis failure should degrade to a database read, not a 500.

```typescript
private async safeGet<T>(key: string): Promise<T | undefined> {
  try {
    return await this.cache.get<T>(key);
  } catch (error) {
    this.logger.warn({ key, error }, 'Cache read failed, falling back to database');
    return undefined;
  }
}
```

Apply the same wrapper to `set` and `del`. Log at `warn`, once per failure — not `error` on every request.

## Key Naming

- Use `<entity>:<scope>:<id>`.
- Keep keys stable and readable.
- Include tenant, company, or user scope when data is scoped.
- Avoid broad keys that mix unrelated permissions or filters.

Examples:

```text
orders:company:<companyId>
order-detail:order:<orderId>
permissions:user:<userId>
```

## TTL And Invalidation

- Every cache key must have TTL.
- Invalidate after the write **commits** — after `dataSource.transaction(...)` resolves, never inside the callback.
- Invalidate every affected key, not only the object being changed.
- Keep TTL short for user-visible mutable data.
- For a hot key that is expensive to rebuild, add jitter to the TTL (for example ±10%) so many keys do not expire at once, and consider a short lock so only one request rebuilds it.

## Production Safety

- Avoid blocking Redis commands in request paths.
- Avoid scanning all keys in application code.
- Keep serialized payloads small.
- Treat Redis as a cache unless the project explicitly models it as durable state.

## Checklist

- [ ] Key includes the correct data scope.
- [ ] Key has TTL, in the unit the project's client expects.
- [ ] Write paths invalidate affected keys.
- [ ] Cached payload matches the response contract.
- [ ] Cache miss path still works without Redis data.
- [ ] A Redis error falls back to the database instead of failing the request.
- [ ] Invalidation runs after the transaction commits.
- [ ] The cached value is the response DTO, not the entity.
- [ ] No broad key scan is used in request handling.
