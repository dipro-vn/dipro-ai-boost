---
name: nestjs-best-practices
description: NestJS backend guidance for feature modules, controllers, services, DTOs, guards, error handling, Prisma integration, and tests.
metadata:
  stack: nestjs, typescript, rest, jwt, prisma, postgresql
---

# NestJS Best Practices

Use this skill when writing, reviewing, or refactoring NestJS backend code.

## Architecture

- Organize code by feature module under `src/modules/`. A module owns its controller, service, repository, DTOs, and tests.
- Prefer small services with one clear responsibility over broad service classes.
- Use constructor injection. Do not instantiate providers manually inside services.
- Avoid circular module dependencies. Extract shared behavior into a small provider only when two or more modules need it.
- Do not let controllers contain business logic. Controllers parse input, apply guards, call services, and return response DTOs.
- Do not return raw Prisma model objects from controllers.

## Controllers

- Use REST routes with stable resource names.
- Protect non-public routes with the project guard pattern: `@UseGuards(JwtAuthGuard)` plus `@Roles(ERole.…)`, and `@CurrentUser()` for the authenticated user. Read the Auth And Roles section below before choosing the role list.
- Validate query, params, and body through DTO classes.
- Keep pagination and filtering explicit in request DTOs.
- Return response DTOs or plain objects shaped by the project contract.

## Auth And Roles

`@Roles(...)` is `SetMetadata('roles', roles)`. `JwtAuthGuard` reads it, and `JwtStrategy.validate` enforces it. What you put on the handler decides everything:

| `@Roles` on the handler | Effect |
| --- | --- |
| `@Roles(ERole.PUBLIC)` | Guard returns `true` immediately. No token is parsed, so **`@CurrentUser()` is `undefined`**. |
| `@Roles(ERole.USER)` | Token required and `payload.role` must be exactly `USER`. An `ADMIN` gets 403. |
| `@Roles(ERole.USER, ERole.ADMIN)` | Token required, either role passes. |
| no `@Roles` at all | Token required, any authenticated role passes. |

- **Roles do not inherit.** `ADMIN` is not a superset of `USER`. List every role that should pass, the way `UsersController` does with `@Roles(ERole.USER, ERole.ADMIN)`.
- `@Roles` is read with `reflector.get('roles', context.getHandler())` - **handler metadata only**. Putting `@Roles` on the controller class has no effect.
- The comparison does not happen in the guard. `JwtAuthGuard` copies the roles onto `request.roles`, then `JwtStrategy.validate` checks `roles.includes(payload.role)` and throws `ForbiddenException('You not have permission')`.
- `ERole.PUBLIC` is a guard bypass, not a role. It never appears in a JWT payload and is not in the Prisma `Role` enum, which only has `USER` and `ADMIN`.
- A `PUBLIC` handler cannot do ownership checks - there is no authenticated user. `GET /products` and `GET /products/:id` are public today.

### The authenticated user

`@CurrentUser()` returns `request.user`, which is whatever `JwtStrategy.validate` built:

```typescript
{ id: payload.sub, email, name, role }
```

Controllers annotate it as `{ id: string; role: ERole }`, but `payload.sub` is assigned from the Prisma `User.id`, which is an `Int`. **The declared type is wrong - `id` is a number at runtime.** Coerce before using it in a query or a comparison:

```typescript
this.productsService.create(createProductDto, Number(currentUser.id));
```

## Services

- Keep write flows transactional when they touch multiple tables.
- Keep read flows explicit about relations to avoid N+1 behavior.
- Throw NestJS exceptions such as `NotFoundException`, `BadRequestException`, and `ForbiddenException`.
- Keep external side effects behind injectable providers so tests can replace them.

## DTOs And Validation

This project does **not** put raw `class-validator` decorators on feature DTO fields. `src/shared/decorators/dto.decorators.ts` wraps them, and every DTO in `src/modules` and `src/auth` that declares a validated field uses a wrapper. Follow that instead of reaching for `@IsString()` directly.

The only exceptions are `BasePaginationDto` and `BasePaginationResponseDto`, which predate the wrappers and still use raw decorators, and `UploadImageDto`, which is Swagger-only multipart metadata.

### Request DTOs

Two decorators per field. `@ApiProperty` / `@ApiPropertyOptional` carries the Swagger `example` and `description`; the `*Field` wrapper carries the validation.

```typescript
export class CreateProductDto {
  @ApiProperty({ example: 'Milk Tee', description: 'Product name' })
  @StringField({ optional: false }, { min: 1, max: 100 })
  name: string;

  @ApiPropertyOptional({ example: 'Fresh whole chicken', description: 'Product Description' })
  @StringField({ optional: true })
  description?: string;
}
```

Every wrapper adds `ApiProperty`, then its type validators with a message pulled from `MESSAGES` via `CommonHelpers.formatMessageString`, then `IsOptional()` for `{ optional: true }` or `IsNotEmpty()` otherwise.

| Wrapper | Signature | Adds |
| --- | --- | --- |
| `StringField` | `(options?, length?: { min, max })` | `IsString`, plus `Length` when `length` is passed |
| `NumberField` | `(options? & { min?, maxLength? })` | `IsNumber`, `Min`, `MaxNumberLength` |
| `IntField` | `(options? & { min? })` | `IsInt`, plus `Min(options.min ?? 1)` |
| `EmailField` | `(options?, length?: { min, max })` | `IsEmail`, plus `Length` |
| `BooleanField` | `(options?)` | `IsBoolean` |
| `DateStringField` | `(options?)` | `IsDateString` |
| `EnumField` | `(entity, options?)` | `IsEnum(entity)`, `ApiProperty({ enum: entity })` |
| `ArrayField` | `(entity, options? & { minSize? })` | `IsArray`, `ValidateNested({ each: true })`, `Type(() => entity)`, `ArrayMinSize` |
| `ObjectField` | `(entity, options?)` | `IsObject`, `ApiProperty({ type: () => entity })` |

Traps worth checking before you write a DTO:

- `StringField` and `EmailField` take `length` as a **second positional argument**, not a key inside `options`: `@StringField({ optional: true }, { min: 1, max: 100 })`.
- `IntField` defaults to `Min(1)`, so it rejects `0` unless you pass `{ min: 0 }`.
- The wrappers never add `@Type(() => Number)`. Query params arrive as strings, so a numeric query field still needs it - see `GetListProductsDto`, which pairs `@IntField({ optional: true })` with `@Type(() => Number)`.
- `NumberField` applies `min` and `maxLength` whenever the option is present, `0` included - both guards test `!== undefined`, and `src/shared/decorators/dto.decorators.spec.ts` locks that in. Keep that shape if you add a numeric option; a plain truthiness check silently drops a `0` bound.
- `maxLength` counts **digits only**: the minus sign and the decimal point do not count, a literal `0` counts as one digit, and a non-numeric value is left for `IsNumber` to report.

Other rules:

- Ids are numeric: `ParseIntPipe` on route params, `@Type(() => Number)` in DTOs.
- Extend `BasePaginationDto` for list queries instead of redeclaring `page`, `limit`, `sortBy`, `direction`, and `search`.
- Do not accept raw `orderBy` or `sort` fields. Pass `sortBy` through `CommonHelpers.transformPaginationQuery` with the model's `Prisma.<Model>ScalarFieldEnum`.

### Response DTOs

Response fields use `@ResField(options)`, which is `ApiProperty(options)` plus `Expose()`. There is no validation on a response DTO.

`TransformInterceptor` runs `plainToInstance(dto, data, { excludeExtraneousValues: true })`, so **a field without `@ResField` is silently dropped from the response**. That is what keeps `password` and `refreshToken` out - not a manual `delete`.

```typescript
export class ProductWithUserResponseDto extends ProductResponseDto {
  @ResField({ type: () => UserResponseDto, description: 'Product owner', required: false })
  @Type(() => UserResponseDto)
  user?: UserResponseDto;
}
```

- A forgotten `@ResField` surfaces as a missing field in the API, never as an error. Verify every field the contract promises.
- Nested response objects need `@Type(() => OtherResponseDto)` next to `@ResField({ type: () => OtherResponseDto })`.
- Optional fields pass `required: false` inside the `@ResField` options.
- The interceptor treats a payload as paginated when `data.items` is an array: it maps `items` through the DTO and leaves `totalItems`, `currentPage`, and `allItems` untouched at the top level.

## Prisma Integration

- Keep Prisma calls inside a per-feature repository (`src/modules/<feature>/<feature>.repository.ts`). Services depend on the repository, not on `PrismaService`.
- Follow the existing repository shape: params-object methods (`findAll`, `count`, `findOne`, `create`, `update`, `delete`, `createMany`) typed with generated `Prisma.*` input types.
- `PrismaModule` is `@Global()`, so a feature module does not re-import it. Register the feature repository in the feature module's `providers`.
- Load relations explicitly with `include` or `select`. Never assume implicit relation loading.
- Use `select` to keep sensitive columns out of query results instead of deleting them afterwards.
- Use `this.prisma.$transaction` for multi-table writes, and use the `tx` client inside the callback.
- Soft delete is handled by Prisma middleware for models in `SOFT_DELETE_MODEL_NAMES`. Do not re-implement it per service.
- Password hashing is handled by the `UserListener.onCreated` middleware on `User.create` / `createMany`. Do not hash again in a service. See the Prisma Middleware Stack section of the `postgresql` skill for what the three registered middlewares cover, and what they do not.
- Never build schema changes by hand against the database. Change `prisma/schema.prisma`, then run `npx prisma migrate dev` and `npx prisma generate`.

## Testing

- Unit test service logic with Nest testing utilities.
- Use Supertest for endpoint behavior.
- Test guards, validation errors, missing records, and write failures where relevant.
- Bug fixes require a regression test that fails before the fix.

## Checklist

- [ ] Feature module follows existing project structure.
- [ ] Controller has no business logic.
- [ ] Request DTOs validate all external input through the `dto.decorators.ts` wrappers, not raw `class-validator` decorators.
- [ ] Every response field carries `@ResField`, since `excludeExtraneousValues` drops anything without it.
- [ ] Response does not expose raw Prisma model data or sensitive columns.
- [ ] Dynamic sort fields are whitelisted.
- [ ] Multi-table writes run in a transaction.
- [ ] Tests cover success and important failure cases.
