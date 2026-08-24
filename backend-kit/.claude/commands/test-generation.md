---
description: Add backend tests for a feature, bug fix, module, service, controller, endpoint, or cache behavior.
argument-hint: [module or behavior to cover]
---

# Test Generation

**Request:** $ARGUMENTS

## Trigger

Use when adding backend tests for a feature, bug fix, module, service, controller, endpoint, migration-adjacent behavior, or cache behavior.

## Steps

1. **Read behavior** - Dispatch **backend-tester** to read acceptance criteria, API contract, and existing tests.
2. **List cases** - Cover success, validation failure, authorization failure, missing records, transaction failure, cache invalidation, and regression paths where relevant.
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
