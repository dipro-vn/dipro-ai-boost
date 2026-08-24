---
description: Scaffold a NestJS REST resource, or extend an existing module with new endpoint behavior.
argument-hint: <resource-name>
---

# Generate API

**Resource:** $ARGUMENTS

## Trigger

Use when scaffolding a NestJS REST resource or extending an existing module with new endpoint behavior.

## Steps

1. **Inspect existing patterns** - Use the `sourcebase-reuse-first` skill to find similar modules, controllers, services, DTOs, entities, migrations, and tests.
2. **Define contract** - Use the `rest-api-contract` skill to list method, path, auth, request DTO, response DTO, errors, and pagination.
3. **Design module** - Dispatch **backend-architect** to decide whether to create a new feature module or extend an existing one.
4. **Implement scaffold** - Dispatch **backend-developer** to create only the files needed by the accepted contract.
5. **Add tests** - Dispatch **backend-tester** to add service and endpoint tests for the scaffolded behavior.
6. **Review** - Dispatch **backend-reviewer** to check validation, authorization, raw entity exposure, database rules, and query safety.

## Scaffold Checklist

- [ ] Module follows the existing feature-module pattern.
- [ ] Controller path matches project route naming.
- [ ] Request DTOs use validation decorators.
- [ ] Response DTOs are explicit.
- [ ] Entity uses UUID and explicit database names when a table is needed.
- [ ] Migration plan exists when schema changes.
- [ ] Tests cover success and key failures.
