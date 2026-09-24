---
description: Add Jest service specs and Supertest endpoint specs for a feature, fix, or module.
---

# Test Generation

## Trigger

Use when adding backend tests for a feature, bug fix, module, service, controller, endpoint, or migration-adjacent behavior.

## Delegation

Run each step named below through that subagent with the Agent tool (`subagent_type`), and wait for its result before the next step. Do not read the agent file and play the role yourself - the point of the split is that each agent gets a clean context and its own tool limits.

## Steps

1. **Read behavior** - the `backend-tester` subagent reads acceptance criteria, API contract, and existing tests.
2. **List cases** - Cover success, validation failure, authorization failure, missing records, transaction failure, and regression paths where relevant.
3. **Write tests** - Apply the `nestjs-testing` skill using existing project patterns.
4. **Run focused tests** - Run the smallest command that exercises the new tests.
5. **Run relevant suite** - Run the module or project test command that catches regressions.
6. **Patch gaps** - Add missing cases for meaningful uncovered branches.

## Definition Of Done

- Each acceptance criterion has test coverage.
- Important error paths are covered.
- Bug fixes have regression coverage or a documented micro-fix reason.
- Tests are deterministic and pass.
- Test style matches the project.
