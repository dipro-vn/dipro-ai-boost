---
name: backend-query-performance
description: Backend performance guidance for PostgreSQL and Prisma queries, indexing, pagination, N+1 prevention, and request-path efficiency.
metadata:
  stack: postgresql, prisma, performance
---

# Backend Query Performance

Use this skill when reviewing list endpoints, heavy reads, or slow backend behavior.

This project has **no cache layer**. Performance work here means query shape, indexes, and
pagination - not caching. Never raise "missing cache" as a finding.

## Query Review

- Confirm the endpoint applies ownership scope where the contract requires it. The only scope column in this project is `Product.userId`; there is no tenant or company dimension.
- Confirm list endpoints paginate with `skip` / `take`, and that the `count` uses the same `where`.
- Check that filter and sort columns have appropriate `@@index` / `@@unique` entries.
- Check that dynamic sort fields are whitelisted through `Prisma.<Model>ScalarFieldEnum`, not taken raw from the DTO.
- Check that `include` / `select` is explicit and returns only what the contract needs.
- Use `include` or batched `in` lookups for relation data.

## N+1 Prevention

Bad pattern:

```typescript
for (const order of orders) {
  order.items = await this.itemsRepository.findAll({ where: { orderId: order.id } });
}
```

Better patterns:

- Load the relation in one query with `include: { items: true }` when response size is bounded.
- Fetch related rows in one batch with `where: { orderId: { in: orderIds } }`, then group in memory.
- Use `select` to return summary fields instead of full nested data when list endpoints do not need detail data.

## Request-Path Efficiency

- Do not run expensive scans in request handlers.
- Do not perform one external call per row in a list response.
- Move non-critical side effects to an event or queue if the project already has that pattern.

## Checklist

- [ ] List endpoints paginate.
- [ ] Filters and sort columns are indexed.
- [ ] Query avoids N+1 behavior.
- [ ] Response does not load unnecessary relation data.
