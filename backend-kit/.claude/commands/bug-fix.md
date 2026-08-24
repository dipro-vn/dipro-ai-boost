---
description: Reproduce, diagnose, and fix incorrect backend behavior, with a regression test proving the fix.
argument-hint: <bug description>
---

# Bug Fix

**Request:** $ARGUMENTS

## Trigger

Use when backend behavior is incorrect, unstable, insecure, slow, or inconsistent with the expected API contract.

## Steps

0. **Context** - Read `CLAUDE.md`, related docs, nearby code, and existing tests.
1. **Reproduce** - Dispatch **backend-tester** to write or identify a failing test that proves the bug. Micro-fixes may skip this only with a written reason.
2. **Diagnose** - Find the root cause and affected scope. Do not patch only the symptom.
3. **Fix** - Dispatch **backend-developer** to make the smallest change that resolves the root cause.
4. **Regression** - Dispatch **backend-tester** to verify the failing test now passes and run the relevant suite.
5. **Review** - Dispatch **backend-reviewer** to check for regressions in security, data integrity, query behavior, cache behavior, and contract shape.
6. **Record** - Invoke the `backend-change-record` skill. Write the record only if the diff matches one of its conditions.

## Definition Of Done

- The bug no longer reproduces.
- A regression test exists or a micro-fix reason is recorded.
- Relevant tests pass.
- The fix stays within root-cause scope.
- Review has no blockers.
- A change record exists, or no record condition was matched.
