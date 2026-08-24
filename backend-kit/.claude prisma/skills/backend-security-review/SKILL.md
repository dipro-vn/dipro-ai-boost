---
name: backend-security-review
description: Backend security review checklist for auth, authorization, input validation, output shaping, logging, file handling, and configuration hygiene.
metadata:
  stack: backend-security, nestjs
---

# Backend Security Review

Use this skill when reviewing backend code or designing endpoints that handle protected data.

## Auth And Authorization

- Protected endpoints must use the project guard pattern: `@UseGuards(JwtAuthGuard)` plus `@Roles(...)` **on the handler**. `@Roles` on the controller class is read by nobody.
- Treat a missing `@Roles` as a finding: the route then accepts any authenticated role.
- Treat `@Roles(ERole.PUBLIC)` as a finding whenever the handler reads `@CurrentUser()` or returns owner-scoped data. `PUBLIC` bypasses the guard before the token is parsed, so `req.user` is `undefined` and no ownership check is possible.
- Roles do not inherit. `@Roles(ERole.USER)` returns 403 for an `ADMIN`. Confirm the role list matches what the contract intends.
- `currentUser.id` is annotated `string` but is a number at runtime. Coerce with `Number(...)` before using it in a query or comparison.
- Role or ownership checks must happen before returning data.
- Ownership scope must be applied in database queries where the contract requires it. This project has **no tenant or company dimension** - `Product.userId` is the only ownership column.
- Ownership is enforced by loading the row and comparing, not by filtering the query: `product.userId !== Number(currentUser.id) && currentUser.role !== ERole.ADMIN`. That works for single-row reads and writes. It does nothing for a list endpoint, so a list that must be owner-scoped needs `userId` in the `where` instead.
- `GET /products` is deliberately public and unscoped. Do not report that as a leak unless the contract says products are private.
- Do not trust IDs from the request without checking access rights.

## Input Validation

- All body, query, and params input must go through DTO validation, written with the `src/shared/decorators/dto.decorators.ts` wrappers (`StringField`, `NumberField`, `IntField`, `EmailField`, `EnumField`, `ArrayField`, ...). A raw `class-validator` decorator on a feature DTO is a finding.
- Check that a declared bound is the bound you want. `NumberField` enforces `min` and `maxLength` including `0`, and `IntField` defaults to `Min(1)` unless given an explicit `min`. A field that must accept `0` needs `{ min: 0 }` spelled out.
- Numeric query fields need `@Type(() => Number)`; the wrappers do not add it.
- Validate numeric IDs with `ParseIntPipe` on route params.
- Whitelist dynamic sort and filter fields.
- Validate file metadata and size before processing uploads.

## Output Shaping

- Do not return raw Prisma model objects from controllers. Shape responses with a response DTO and `TransformInterceptor`, and keep `password` / `refreshToken` out of `select`.
- `TransformInterceptor` uses `excludeExtraneousValues: true`, so only fields carrying `@ResField` (which adds `Expose()`) reach the client. Adding `@ResField` to a sensitive field is what leaks it - review every new `@ResField` on a user-facing DTO.
- Do not expose internal fields, audit data, or credential material.
- Use response DTOs for stable contracts.
- Keep error messages useful but not revealing of internal implementation details.

## Logging

- Logs may include request IDs, route names, and business identifiers.
- Logs must not include credential material, session headers, or full request bodies with sensitive fields.
- Log expected business failures at a lower level than system failures.

## Data Safety

- Passwords are hashed by the `UserListener.onCreated` Prisma middleware on `User.create` / `createMany`. Calling `AuthHelpers.hash` again on a create path is a finding - the double hash breaks login silently.
- That middleware does **not** cover `update` / `updateMany` / `upsert`. Any new password-changing path must hash explicitly, or it writes plain text.
- Anything else stored hashed (refresh tokens) must be hashed in the service, as `AuthService.login` does.
- Use `$transaction` for multi-table writes.
- Check ownership before updates and deletes.
- Prefer soft delete when the model is registered in `SOFT_DELETE_MODEL_NAMES`.
- Avoid broad `updateMany` / `deleteMany` operations without explicit filters.
- Never interpolate user input into `$queryRawUnsafe` / `$executeRawUnsafe`; use tagged-template `$queryRaw` parameters.
- Remember that raw queries bypass the soft-delete middleware.

## Checklist

- [ ] Guards are present where required, with `@Roles` on the handler.
- [ ] No route is `ERole.PUBLIC` while returning owner-scoped data.
- [ ] The role list covers every role that should pass, since roles do not inherit.
- [ ] Ownership or role checks are explicit.
- [ ] DTO validation covers external input and uses the project wrappers.
- [ ] Numeric bounds match the contract, and any field that must accept `0` declares `{ min: 0 }`.
- [ ] Query sort fields are whitelisted.
- [ ] Responses are shaped through DTOs.
- [ ] Credential material is hashed exactly once - not re-hashed on create, not left plain on update.
- [ ] Logs avoid credential material.
- [ ] Writes cannot affect records outside the intended scope.
