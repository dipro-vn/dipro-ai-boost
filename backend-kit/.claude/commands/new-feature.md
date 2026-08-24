---
description: Build a new backend capability end to end — analysis, design, implementation, tests, review.
argument-hint: <feature description>
---

# New Feature

**Request:** $ARGUMENTS

## Trigger

Use when building a new backend capability such as an endpoint, service flow, entity, migration, cache behavior, or integration inside the application layer.

## Before Starting

Read `CLAUDE.md`, project docs, and nearby modules. Ask only for details that cannot be discovered from the repository or existing requirements.

## Steps

0. **Context** - Invoke the `sourcebase-reuse-first` skill to inspect existing modules, scripts, patterns, DTOs, entities, migrations, and tests.
1. **Analysis** - Dispatch **backend-analyst** to define acceptance criteria, permissions, data rules, errors, and affected contracts.
2. **Design** - Dispatch **backend-architect** to define module boundaries, endpoint contract, DTOs, entity changes, transaction boundaries, cache behavior, and test strategy.
3. **Implementation** - Dispatch **backend-developer** to implement the smallest scoped change with NestJS, TypeORM, PostgreSQL, and Redis guidance.
4. **Tests** - Dispatch **backend-tester** to run `/test-generation` for service, endpoint, and regression coverage.
5. **Review** - Dispatch **backend-reviewer** to run `/code-review` and verify security, data integrity, query performance, cache behavior, and tests.
6. **Record** - Invoke the `backend-change-record` skill. Write the record only if the diff matches one of its conditions.

## Definition Of Done

- Acceptance criteria are implemented.
- Request DTOs validate external input.
- Protected routes use the project guard pattern.
- Responses use DTOs or explicit response objects.
- Migration changes include rollback.
- Query and cache behavior have been reviewed.
- Focused tests and relevant suites pass.
- Review has no blockers.
- A change record exists, or no record condition was matched.
