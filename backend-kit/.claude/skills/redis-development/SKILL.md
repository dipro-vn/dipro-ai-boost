---
name: redis-development
description: Redis guidance for cache-aside reads, key naming, TTL, invalidation, connection behavior, and safe production use.
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
const cached = await this.cache.get(key);
if (cached) {
  return JSON.parse(cached) as OrderResponseDto[];
}

const orders = await this.orderRepository.findByCompany(companyId);
await this.cache.set(key, JSON.stringify(orders), { ttl: 300 });
return orders;
```

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
- Invalidate cache immediately after successful writes.
- Invalidate every affected key, not only the object being changed.
- Keep TTL short for user-visible mutable data.

## Production Safety

- Avoid blocking Redis commands in request paths.
- Avoid scanning all keys in application code.
- Keep serialized payloads small.
- Treat Redis as a cache unless the project explicitly models it as durable state.

## Checklist

- [ ] Key includes the correct data scope.
- [ ] Key has TTL.
- [ ] Write paths invalidate affected keys.
- [ ] Cached payload matches the response contract.
- [ ] Cache miss path still works without Redis data.
- [ ] No broad key scan is used in request handling.
