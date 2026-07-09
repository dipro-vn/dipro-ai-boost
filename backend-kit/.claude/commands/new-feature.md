# New Feature

**Type:** Workflow

## Trigger

Use when building a new backend capability such as an endpoint, service flow, entity, migration, cache behavior, or integration inside the application layer.

## Before Starting

Read `CLAUDE.md`, project docs, and nearby modules. Ask only for details that cannot be discovered from the repository or existing requirements.

## Steps

0. **Context** - `.claude/skills/sourcebase-reuse-first/SKILL.md` inspects existing modules, scripts, patterns, DTOs, entities, migrations, and tests.
1. **Analysis** - `.claude/agents/backend-analyst.md` defines acceptance criteria, permissions, data rules, errors, and affected contracts.
2. **Design** - `.claude/agents/backend-architect.md` defines module boundaries, endpoint contract, DTOs, entity changes, transaction boundaries, cache behavior, and test strategy.
3. **Implementation** - `.claude/agents/backend-developer.md` implements the smallest scoped change with NestJS, TypeORM, PostgreSQL, and Redis guidance.
4. **Tests** - `.claude/agents/backend-tester.md` runs `.claude/commands/test-generation.md` for service, endpoint, and regression coverage.
5. **Review** - `.claude/agents/backend-reviewer.md` runs `.claude/commands/code-review.md` and verifies security, data integrity, query performance, cache behavior, and tests.

## Definition Of Done

- Acceptance criteria are implemented.
- Request DTOs validate external input.
- Protected routes use the project guard pattern.
- Responses use DTOs or explicit response objects.
- Migration changes include rollback.
- Query and cache behavior have been reviewed.
- Focused tests and relevant suites pass.
- Review has no blockers.
