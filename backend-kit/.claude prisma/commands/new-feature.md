---
description: Build a new backend capability end to end - analysis, design, implementation, tests, review.
---

# New Feature

## Trigger

Use when building a new backend capability such as an endpoint, service flow, Prisma model, migration, or integration inside the application layer.

## Before Starting

Read `CLAUDE.md`, project docs, and nearby modules. Ask only for details that cannot be discovered from the repository or existing requirements.

## Delegation

Run each step named below through that subagent with the Agent tool (`subagent_type`), and wait for its result before the next step. Do not read the agent file and play the role yourself - the point of the split is that each agent gets a clean context and its own tool limits.

## Steps

0. **Context** - Use the `sourcebase-reuse-first` skill to inspect existing modules, scripts, patterns, DTOs, repositories, the Prisma schema, migrations, and tests.
1. **Analysis** - the `backend-analyst` subagent defines acceptance criteria, permissions, data rules, errors, and affected contracts.
2. **Design** - the `backend-architect` subagent defines module boundaries, endpoint contract, DTOs, Prisma schema changes, transaction boundaries, and test strategy.
3. **Implementation** - the `backend-developer` subagent implements the smallest scoped change with NestJS, Prisma, and PostgreSQL guidance.
4. **Tests** - the `backend-tester` subagent runs `/test-generation` for service, endpoint, and regression coverage.
5. **Review** - the `backend-reviewer` subagent runs `/code-review` and verifies security, data integrity, query performance, and tests.

## Definition Of Done

- Acceptance criteria are implemented.
- Request DTOs validate external input.
- Protected routes use the project guard pattern.
- Responses use DTOs or explicit response objects.
- Schema changes go through `prisma migrate dev`, with the reverse migration documented.
- Query behavior has been reviewed.
- Focused tests and relevant suites pass.
- Review has no blockers.
