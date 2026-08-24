---
name: rest-api-contract
description: Guidance for producing REST API contracts with method, path, auth, request, response, pagination, errors, and handoff notes.
metadata:
  stack: rest, openapi, nestjs
---

# REST API Contract

Use this skill when designing, reviewing, or documenting backend API changes.

## Route Convention

This app has **no global prefix** - `src/main.ts` never calls `setGlobalPrefix`. A route is exactly the `@Controller('<resource>')` path plus the method path:

| Controller | Actual routes |
| --- | --- |
| `@Controller('products')` | `/products`, `/products/:id`, `/products/bulk` |
| `@Controller('users')` | `/users`, `/users/:id`, `/users/bulk` |
| `@Controller('auth')` | `/auth/login`, `/auth/refresh` |
| `@Controller('uploads')` | `/uploads/image` |

Never write `/api/<resource>` in a contract or a test. The only `/api` path in the project is `/api/docs`, mounted by `SwaggerModule.setup` for the docs UI. `/uploads` is also served as static files by `ServeStaticModule`.

## Contract Format

Document every endpoint in a table:

| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| GET | `/orders` | Bearer JWT | `ListOrdersQueryDto` | `BasePaginationResponseDto<OrderListItemDto>` |
| POST | `/orders` | Bearer JWT | `CreateOrderDto` | `OrderDetailDto` |

## Required Details

- HTTP method and stable path.
- Auth requirement.
- Request DTO and important validation rules.
- Response DTO with field names and types. Only fields carrying `@ResField` are serialized - `TransformInterceptor` drops the rest.
- Pagination shape for list endpoints.
- Error shape and important status codes.

## Pagination Shape

List endpoints return `BasePaginationResponseDto<T>` (`src/shared/dtos/base-pagination.response.dto.ts`). Do not invent a `{ items, total, page, limit }` shape.

```typescript
class BasePaginationResponseDto<T> {
  items: T[];         // rows of the current page
  totalItems: number; // rows in THIS page, not the grand total
  currentPage?: number;
  allItems?: number;  // grand total matching the same `where`
}
```

**`totalItems` is the page size and `allItems` is the grand total.** The names read the other way round, so spell out the meaning in every contract. `ProductsService.findAll` and `UsersService.findAll` both build it like this:

```typescript
const [rows, total] = await Promise.all([
  this.repo.findAll({ take, skip, orderBy: sortByField, where }),
  this.repo.count({ where }),
]);

return BasePaginationResponseDto.convertToPaginationResponse(
  [rows, rows.length], // second slot feeds totalItems
  dto.page,            // feeds currentPage
  total,               // feeds allItems
);
```

For Swagger, document the response as `BasePaginationResponseDto.apiOKResponse(<ItemDto>)` - that is what the controllers pass to `@ApiOkResponse`.

## Error Shape

`src/main.ts` registers two global filters. Nest reverses the `useGlobalFilters` order at runtime, so `InvalidFormExceptionFilter` is matched before `AllExceptionsFilter`. There is no single error shape - pick the row that matches what the endpoint throws:

| Thrown | Status | Body |
| --- | --- | --- |
| `HttpException` with a message, e.g. `NotFoundException('Product not found')` | as thrown | `{ message, error, statusCode }` |
| `HttpException` with no message, e.g. `NotFoundException()` | as thrown | `{ message, statusCode }` - no `error` key |
| `ValidationPipe` failure | 400 | `{ message: string[], error: 'Bad Request', statusCode: 400 }` |
| `InvalidFormException(fieldErrors, message)` | 400 | `{ statusCode, errors, message }` - `errors` is `Record<string, string>` |
| Any other `Error` | 500 | `{ message }` only |
| A non-`Error` throw | 500 | `{ message: 'Internal server error' }` |

Rules for contracts:

- `AllExceptionsFilter` returns the `HttpException` body untouched, so the `error` key exists only because Nest adds it when you throw with a message. Always throw with a message.
- The field-error key is `errors` (plural, an object) and only `InvalidFormException` produces it. Do not promise `errors` on ordinary `ValidationPipe` failures, which return `message` as a string array.
- 500 bodies carry no `statusCode` and no `error`. Do not document either.

## Contract Checklist

- [ ] Every changed endpoint is listed.
- [ ] Request and response DTO names are exact.
- [ ] List responses use `BasePaginationResponseDto` and state what `totalItems` and `allItems` mean.
- [ ] Documented error bodies match the Error Shape table, not a generic `{ statusCode, message, error }`.
- [ ] Validation errors and missing-resource errors are covered.
- [ ] Auth requirement is clear.
- [ ] Breaking changes are called out.
