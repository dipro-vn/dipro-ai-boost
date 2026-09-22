---
name: backend-security-review
description: Use when writing or reviewing an endpoint that touches protected data, accepts external input, or writes to the database. Symptoms — a new route, a changed guard, an entity returned from a controller, an ID taken from the request, dynamic orderBy, a file upload, a new log statement.
metadata:
  stack: backend-security, nestjs
---

# Backend Security Review

Use this skill when reviewing backend code or designing endpoints that handle protected data.

## Auth And Authorization

- Protected endpoints must use the project guard pattern.
- Role or ownership checks must happen before returning data.
- Tenant, company, or user scope must be applied in database queries.
- Do not trust IDs from the request without checking access rights.

## Input Validation

- All body, query, and params input must go through DTO validation.
- Use UUID validation for IDs.
- Whitelist dynamic sort and filter fields.
- Validate file metadata and size before processing uploads.
- Enforce a maximum page size in the DTO (`@Max(100)` on `limit`). An unbounded `limit` lets one request read the whole table.

### Mass Assignment

The global `ValidationPipe` must strip fields the DTO does not declare:

```typescript
app.useGlobalPipes(
  new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true }),
);
```

Without `whitelist`, a client can send `companyId`, `role`, or `isAdmin` in the body and a spread into the entity (`repo.save({ ...dto })`) writes it. Map DTO fields to the entity explicitly, and set scope and ownership fields from the token, never from the body.

## Output Shaping

- Do not return raw entities from controllers.
- Do not expose internal fields, audit data, or credential material.
- Use response DTOs for stable contracts.
- Keep error messages useful but not revealing of internal implementation details.

## Logging

- Logs may include request IDs, route names, and business identifiers.
- Logs must not include credential material, session headers, or full request bodies with sensitive fields.
- Log expected business failures at a lower level than system failures.

## Abuse And Secrets

- Rate-limit login, OTP, password reset, export, and other expensive or guessable endpoints — with `@nestjs/throttler` or the project's existing mechanism.
- Read secrets and connection strings from configuration, never from code or committed files.
- Do not read `.env` files during a task; ask for the variable name instead.

## Data Safety

- Use transactions for multi-table writes.
- Check ownership before updates and deletes.
- Prefer soft delete when the project uses soft delete for the entity.
- Avoid broad update/delete operations without explicit filters.

## Checklist

- [ ] Guards are present where required.
- [ ] Ownership or role checks are explicit.
- [ ] DTO validation covers external input.
- [ ] `ValidationPipe` uses `whitelist` and `forbidNonWhitelisted`; no DTO is spread into an entity.
- [ ] List endpoints cap `limit`.
- [ ] Sensitive or expensive endpoints are rate-limited.
- [ ] Query sort fields are whitelisted.
- [ ] Responses are shaped through DTOs.
- [ ] Logs avoid credential material.
- [ ] Writes cannot affect records outside the intended scope.
