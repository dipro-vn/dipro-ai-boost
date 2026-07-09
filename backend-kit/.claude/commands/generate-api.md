# Generate API

**Type:** Workflow

## Trigger

Use when scaffolding a NestJS REST resource or extending an existing module with new endpoint behavior.

## Input

`/generate-api <resource-name>`

## Steps

1. **Inspect existing patterns** - Use `.claude/skills/sourcebase-reuse-first/SKILL.md` to find similar modules, controllers, services, DTOs, entities, migrations, and tests.
2. **Define contract** - Use `.claude/skills/rest-api-contract/SKILL.md` to list method, path, auth, request DTO, response DTO, errors, and pagination.
3. **Design module** - `.claude/agents/backend-architect.md` decides whether to create a new feature module or extend an existing one.
4. **Implement scaffold** - `.claude/agents/backend-developer.md` creates only the files needed by the accepted contract.
5. **Add tests** - `.claude/agents/backend-tester.md` adds service and endpoint tests for the scaffolded behavior.
6. **Review** - `.claude/agents/backend-reviewer.md` checks validation, authorization, raw entity exposure, database rules, and query safety.

## Scaffold Checklist

- [ ] Module follows the existing feature-module pattern.
- [ ] Controller path matches project route naming.
- [ ] Request DTOs use validation decorators.
- [ ] Response DTOs are explicit.
- [ ] Entity uses UUID and explicit database names when a table is needed.
- [ ] Migration plan exists when schema changes.
- [ ] Tests cover success and key failures.
