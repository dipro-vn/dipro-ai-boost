---
name: backend-auth-authorization
description: Use when adding or changing a protected route, a guard, a role check, or any query that reads or writes records belonging to a user or tenant. Symptoms — a findById that takes only an id, a route with no guard, a role checked in the controller but not the query, an ID read straight from params, a new public endpoint, a service method reachable from more than one caller.
metadata:
  stack: nestjs, jwt, authorization, multi-tenant
---

# Backend Auth And Authorization

Use this skill when deciding who may reach an endpoint, and which rows they may see.

## The Distinction That Causes Most Breaches

**Authentication** proves who the caller is. **Authorization** decides which records
they may touch. A guard delivers the first and none of the second.

```typescript
@UseGuards(JwtAuthGuard)        // proves the caller is a real, logged-in user
@Get(':id')
detail(@Param('id') id: string) {
  return this.service.findById(id);   // still returns ANY company's record
}
```

That endpoint is authenticated and unauthorized. Any logged-in user holding a valid
UUID reads another tenant's data. This is the single most common backend data leak,
and a guard on the route never prevents it.

## Scope Belongs In The Query

The fix is not a check before the query. It is a filter inside it — a check can be
skipped by a new caller, a `WHERE` clause cannot.

```typescript
// The scope is part of the lookup, so no caller can forget it.
async findById(id: string, companyId: string): Promise<OrderEntity> {
  const order = await this.repo.findOne({ where: { id, companyId } });
  if (!order) throw new NotFoundException('Order not found');
  return order;
}
```

Make the scope a **required parameter**. A signature of `findById(id)` on
tenant-owned data is a latent leak waiting for its first caller — the compiler should
refuse to let anyone call it without a scope.

Apply the same rule to writes. An `UPDATE` or `DELETE` filtered only by primary key
lets a caller modify another tenant's row.

## Rules

- Every route is protected unless it is deliberately public. Prefer a global guard
  with an explicit `@Public()` decorator over remembering a guard on each route.
- Take the caller's identity from the validated token, never from the request body,
  a query parameter, or a header the client controls.
- Check roles and permissions in the service, not only the controller — the service
  is what a second caller will reuse.
- Return 404 rather than 403 for a record the caller may not know exists.
- Re-check ownership on every write, including nested resources. Owning the parent
  does not imply owning the child, and the reverse is also false.
- A missing scope is a defect even with no caller today. Fix it where it is defined.

## Testing

Authorization needs its own tests. Coverage of the happy path proves nothing.

- A caller from another tenant receives 404 for a record that exists.
- A caller without the required role receives 403.
- A request with no token, and one with an expired token, receive 401.
- A write scoped to another tenant changes no rows.

## Checklist

- [ ] Every route is guarded, or explicitly marked public.
- [ ] Caller identity comes from the token only.
- [ ] Tenant or owner scope is a required parameter, not an optional one.
- [ ] Scope is applied inside the query, not as a check beside it.
- [ ] Writes and deletes filter on scope as well as primary key.
- [ ] Nested resources verify ownership at each level.
- [ ] Hidden records return 404, not 403.
- [ ] Cross-tenant and missing-role cases have tests.
