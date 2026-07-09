---
name: nestjs-best-practices
description: NestJS backend guidance for feature modules, controllers, services, DTOs, guards, error handling, TypeORM integration, Redis cache use, and tests.
metadata:
  stack: nestjs, typescript, rest, jwt, typeorm, postgresql, redis
---

# NestJS Best Practices

Use this skill when writing, reviewing, or refactoring NestJS backend code.

## Architecture

- Organize code by feature module. A module owns its controller, service, DTOs, entity, tests, and cache behavior.
- Prefer small services with one clear responsibility over broad service classes.
- Use constructor injection. Do not instantiate providers manually inside services.
- Avoid circular module dependencies. Extract shared behavior into a small provider only when two or more modules need it.
- Do not let controllers contain business logic. Controllers parse input, apply guards, call services, and return response DTOs.
- Do not return raw entities from controllers.

## Controllers

- Use REST routes with stable resource names.
- Protect non-public routes with the project guard pattern.
- Validate query, params, and body through DTO classes.
- Keep pagination and filtering explicit in request DTOs.
- Return response DTOs or plain objects shaped by the project contract.

## Services

- Keep write flows transactional when they touch multiple tables.
- Keep read flows explicit about relations to avoid N+1 behavior.
- Throw NestJS exceptions such as `NotFoundException`, `BadRequestException`, and `ForbiddenException`.
- Keep external side effects behind injectable providers so tests can replace them.
- Invalidate Redis cache immediately after successful writes.

## DTOs And Validation

- Request DTOs use `class-validator` decorators.
- Use `@IsUUID()` for UUID fields and `@IsEnum()` for enumerated values.
- Prefer explicit optional fields with `@IsOptional()`.
- Do not accept raw `orderBy` or `sort` fields without whitelisting.
- Response DTOs must omit sensitive fields and expose only contract fields.

## TypeORM Integration

- Use repositories or project-specific data access providers.
- Do not use implicit eager relations for feature reads.
- Use QueryBuilder when filtering, sorting, paginating, or joining.
- Keep TypeORM `synchronize` disabled outside throwaway local experiments.

## Redis

- Use cache-aside for read-heavy resources.
- Give every cache key a TTL.
- Use predictable key names: `<entity>:<scope>:<id>`.
- Delete or refresh cache keys after writes.

## Testing

- Unit test service logic with Nest testing utilities.
- Use Supertest for endpoint behavior.
- Test guards, validation errors, missing records, and write failures where relevant.
- Bug fixes require a regression test that fails before the fix.

## Checklist

- [ ] Feature module follows existing project structure.
- [ ] Controller has no business logic.
- [ ] Request DTOs validate all external input.
- [ ] Response does not expose raw entity data.
- [ ] Dynamic sort fields are whitelisted.
- [ ] Multi-table writes run in a transaction.
- [ ] Redis cache has TTL and invalidation.
- [ ] Tests cover success and important failure cases.
