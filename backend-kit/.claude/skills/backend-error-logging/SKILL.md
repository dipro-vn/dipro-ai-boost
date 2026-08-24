---
name: backend-error-logging
description: Use when choosing which exception to throw, shaping an error response, or deciding what to log. Symptoms — a caught error that returns 200, a try/catch that swallows the cause, a 500 where the client should see 400, an error message exposing a stack trace or SQL, a log line with no request context, the same failure logged at every layer.
metadata:
  stack: nestjs, logging, error-handling
---

# Backend Error Handling And Logging

Use this skill when deciding how a failure leaves the service — as a status code, a
response body, and a log line.

Scope boundary: the `backend-security-review` skill owns whether a log is *safe*
(no credentials, no tokens). This skill owns whether an error and its log are
*correct and useful*.

## Pick The Status Code From The Cause

| Cause | Exception | Status |
| --- | --- | --- |
| Input failed validation | `BadRequestException` | 400 |
| No or invalid credentials | `UnauthorizedException` | 401 |
| Authenticated but not allowed | `ForbiddenException` | 403 |
| Record absent, or not visible to this caller | `NotFoundException` | 404 |
| Unique or state conflict | `ConflictException` | 409 |
| Valid shape, impossible business state | `UnprocessableEntityException` | 422 |
| Anything unhandled | let it become 500 | 500 |

Return `404`, not `403`, when the caller may not know the record exists — a `403`
confirms the ID is real and leaks the existence of another tenant's data.

## Rules

- Throw at the point of detection. Do not return `null` and let a caller guess.
- Never catch an error only to log it and rethrow — that produces one failure logged
  three times with no added information.
- Catch only to add context or convert the type. Always preserve the cause.
- Never let a caught error produce a success response.
- An error message may name the field and the rule. It may not carry a stack trace,
  a SQL fragment, a file path, or a driver message.

```typescript
// Convert an infrastructure error into a domain error, keeping the cause.
try {
  await this.repo.insert(row);
} catch (error) {
  if (error instanceof QueryFailedError && error.driverError?.code === '23505') {
    throw new ConflictException('An order with this reference already exists');
  }
  throw error; // unknown failure stays unhandled — do not flatten it into 400
}
```

## Log Levels

| Level | Use for | Example |
| --- | --- | --- |
| `debug` | Local diagnosis only | Query parameters |
| `log` / `info` | Notable business events | Order created |
| `warn` | Expected failures worth counting | Validation rejected, quota hit |
| `error` | The service is at fault | Unhandled exception, database unreachable |

An expected business failure is not an `error`. Logging every 404 at error level
turns the error channel into noise and hides the failures that matter.

## Every Log Line Needs Context

A log without identifiers cannot be traced back to a request. Include the request or
correlation ID, the route, and the business identifiers a human would search for.

```typescript
this.logger.warn(
  { requestId, route: 'POST /api/orders', companyId, orderRef },
  'Order rejected: duplicate reference',
);
```

Log the error object itself, not `error.message` — the stack is what makes an `error`
line actionable.

## Checklist

- [ ] Status code matches the cause, not the layer that caught it.
- [ ] Hidden records return 404 rather than 403.
- [ ] No catch block swallows a failure or returns success.
- [ ] Converted errors keep the original cause.
- [ ] Error messages carry no stack trace, SQL, or driver text.
- [ ] Expected business failures are `warn`, not `error`.
- [ ] The same failure is logged once, at the boundary that handles it.
- [ ] Log lines carry request ID, route, and business identifiers.
