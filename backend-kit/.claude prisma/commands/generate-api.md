---
description: Scaffold a NestJS REST resource, or extend an existing module with new endpoint behavior.
argument-hint: <resource-name>
---

# Generate API

## Trigger

Use when scaffolding a NestJS REST resource or extending an existing module with new endpoint behavior.

## Input

The resource name is `$1`. Use it verbatim for the folder name, file prefixes, and route path.

If `$1` is empty, ask which resource to scaffold and stop until answered - do not guess a name.

## Delegation

Run each step named below through that subagent with the Agent tool (`subagent_type`), and wait for its result before the next step. Do not read the agent file and play the role yourself - the point of the split is that each agent gets a clean context and its own tool limits.

## Steps

1. **Inspect existing patterns** - Use the `sourcebase-reuse-first` skill to find the modules closest to `$1`, plus their controllers, services, repositories, DTOs, Prisma models, migrations, and tests.
2. **Define contract** - Use the `rest-api-contract` skill to list method, path (`/$1`, `/$1/:id`), auth, request DTO, response DTO, errors, and pagination.
3. **Design module** - the `backend-architect` subagent decides whether `$1` needs a new feature module at `src/modules/$1/` or belongs to an existing module.
4. **Implement scaffold** - the `backend-developer` subagent creates only the files the accepted `$1` contract needs.
5. **Add tests** - the `backend-tester` subagent adds service and endpoint tests for `$1`.
6. **Review** - the `backend-reviewer` subagent checks validation, authorization, raw model exposure, database rules, and query safety.

## Scaffold Checklist

- [ ] `src/modules/$1/` follows the existing feature-module pattern: `$1.module.ts`, `$1.controller.ts`, `$1.service.ts`, `$1.repository.ts`, `dto/`, `$1.service.spec.ts`.
- [ ] `@Controller('$1')` mounts at `/$1` - no `/api` prefix.
- [ ] Handlers carry `@UseGuards(JwtAuthGuard)` plus a `@Roles(...)` list naming every role allowed to pass.
- [ ] Request DTOs use the `dto.decorators.ts` wrappers plus `@ApiProperty` / `@ApiPropertyOptional`; list DTOs extend `BasePaginationDto`.
- [ ] Every response DTO field carries `@ResField`, and the DTO is applied through `TransformInterceptor`.
- [ ] New Prisma models use `Int @id @default(autoincrement())`, `createdAt`/`updatedAt`, and `deletedAt` when soft delete applies.
- [ ] Schema changes go through `prisma migrate dev`, with the reverse migration documented.
- [ ] Tests cover success and key failures.
