---
name: backend-query-cache-performance
description: Backend performance guidance for PostgreSQL queries, indexing, pagination, N+1 prevention, Redis cache, and request-path efficiency.
metadata:
  stack: postgresql, redis, performance
---

# Backend Query And Cache Performance

Use this skill when reviewing list endpoints, heavy reads, cache additions, or slow backend behavior.

## Query Review

- Confirm the endpoint filters by tenant, company, user, or ownership scope where needed.
- Confirm list endpoints paginate.
- Check that filter and sort columns have appropriate indexes.
- Check that dynamic sort fields are whitelisted.
- Avoid loading relations implicitly.
- Use joins or batched lookups for relation data.

## N+1 Prevention

Bad pattern:

```typescript
for (const order of orders) {
  order.items = await this.itemsRepository.findByOrderId(order.id);
}
```

Better patterns:

- Join the relation in one query when response size is bounded.
- Fetch related rows with `WHERE order_id IN (...)`.
- Return summary fields instead of full nested data when list endpoints do not need detail data.

## Cache Review

- Cache only data that is safe to reuse for the same scope.
- Include filter dimensions in cache keys.
- Give every key a TTL.
- Invalidate affected keys after writes.
- Keep cached response payloads compatible with DTOs.

## Request-Path Efficiency

- Do not run expensive scans in request handlers.
- Do not perform one external call per row in a list response.
- Move non-critical side effects to an event or queue if the project already has that pattern.

## Checklist

- [ ] List endpoints paginate.
- [ ] Filters and sort columns are indexed.
- [ ] Query avoids N+1 behavior.
- [ ] Cache key includes scope and filters.
- [ ] Cache has TTL.
- [ ] Write paths invalidate cache.
- [ ] Response does not load unnecessary relation data.
