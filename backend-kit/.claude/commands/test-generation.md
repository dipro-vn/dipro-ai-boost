---
description: Use when the user asks to add or improve backend tests or coverage for existing behavior. Triggers — viết test, thêm test, coverage, unit test, e2e, テスト追加.
argument-hint: [module or behavior to cover]
model: sonnet
---

# Test Generation

**Request:** $ARGUMENTS

## Trigger

Use when adding backend tests for a feature, bug fix, module, service, controller, endpoint, migration-adjacent behavior, or cache behavior.

## Steps

If you are already running as **backend-tester**, do these steps directly. Otherwise do them in the main agent for one module, or dispatch **backend-tester** once when several modules need coverage.

1. **Read behavior** — read acceptance criteria, API contract, the code under test, and one existing test in the same module to copy its style.
2. **List cases** — cover success, validation failure, authorization failure, missing records, transaction failure, cache invalidation, and regression paths where relevant.
3. **Write tests** — apply the `nestjs-testing` skill using existing project patterns.
4. **Run focused tests** — run only the files you wrote (`npx jest <path>`), and fix until they pass.
5. **Run relevant suite once** — run the module's suite a single time at the end to catch regressions.
6. **Patch gaps** — add missing cases for meaningful uncovered branches.

## Definition Of Done

- Each acceptance criterion has test coverage.
- Important error paths are covered.
- Bug fixes have regression coverage or a documented micro-fix reason.
- Tests are deterministic and pass.
- Test style matches the project.
