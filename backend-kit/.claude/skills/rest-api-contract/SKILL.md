---
name: rest-api-contract
description: Guidance for producing REST API contracts with method, path, auth, request, response, pagination, errors, and handoff notes.
metadata:
  stack: rest, openapi, nestjs
---

# REST API Contract

Use this skill when designing, reviewing, or documenting backend API changes.

## Contract Format

Document every endpoint in a table:

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| GET | `/api/orders` | Bearer JWT | `ListOrdersQueryDto` | `PaginatedResponse<OrderListItemDto>` |
| POST | `/api/orders` | Bearer JWT | `CreateOrderDto` | `OrderDetailDto` |

## Required Details

- HTTP method and stable path.
- Auth requirement.
- Request DTO and important validation rules.
- Response DTO with field names and types.
- Pagination shape for list endpoints.
- Error shape and important status codes.
- Cache behavior if the endpoint uses Redis.

## Pagination Shape

Use one project-wide shape. If the project has no shape yet, prefer:

```typescript
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}
```

## Error Shape

Follow the existing project exception filter. If none exists, document this minimum shape:

```typescript
interface ApiErrorResponse {
  statusCode: number;
  message: string | string[];
  error: string;
}
```

## Contract Checklist

- [ ] Every changed endpoint is listed.
- [ ] Request and response DTO names are exact.
- [ ] Pagination shape is explicit.
- [ ] Validation errors and missing-resource errors are covered.
- [ ] Auth requirement is clear.
- [ ] Cache behavior and invalidation are noted when relevant.
- [ ] Breaking changes are called out.
