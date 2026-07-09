# Bug Fix

**Type:** Workflow

## Trigger

Use when backend behavior is incorrect, unstable, insecure, slow, or inconsistent with the expected API contract.

## Steps

0. **Context** - Read `CLAUDE.md`, related docs, nearby code, and existing tests.
1. **Reproduce** - `.claude/agents/backend-tester.md` writes or identifies a failing test that proves the bug. Micro-fixes may skip this only with a written reason.
2. **Diagnose** - Find the root cause and affected scope. Do not patch only the symptom.
3. **Fix** - `.claude/agents/backend-developer.md` makes the smallest change that resolves the root cause.
4. **Regression** - `.claude/agents/backend-tester.md` verifies the failing test now passes and runs the relevant suite.
5. **Review** - `.claude/agents/backend-reviewer.md` checks for regressions in security, data integrity, query behavior, cache behavior, and contract shape.

## Definition Of Done

- The bug no longer reproduces.
- A regression test exists or a micro-fix reason is recorded.
- Relevant tests pass.
- The fix stays within root-cause scope.
- Review has no blockers.
