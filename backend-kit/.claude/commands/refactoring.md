---
description: Improve backend structure without changing behavior, with tests as the safety net.
argument-hint: <target module or structural problem>
---

# Refactoring

**Request:** $ARGUMENTS

## Trigger

Use when improving backend structure without changing behavior.

## Steps

0. **Context** - Read `CLAUDE.md`, related modules, and current tests.
1. **Goal** - Dispatch **backend-architect** to state the exact structure or maintainability problem being addressed.
2. **Safety net** - Dispatch **backend-tester** to confirm tests cover current behavior, or add focused tests first.
3. **Refactor** - Dispatch **backend-developer** to change code in small steps while preserving public behavior.
4. **Verify** - Run focused tests and relevant suites after each meaningful step.
5. **Review** - Dispatch **backend-reviewer** to check behavior preservation, API compatibility, and data safety.
6. **Record** - Invoke the `backend-change-record` skill. Write the record only if the diff matches one of its conditions.

## Definition Of Done

- Public behavior is unchanged.
- Existing API contracts remain compatible unless the user approved otherwise.
- Tests that cover the area pass.
- The refactor improves the stated goal.
- Review has no blockers.
- A change record exists, or no record condition was matched.
