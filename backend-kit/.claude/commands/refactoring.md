# Refactoring

**Type:** Workflow

## Trigger

Use when improving backend structure without changing behavior.

## Steps

0. **Context** - Read `CLAUDE.md`, related modules, and current tests.
1. **Goal** - `.claude/agents/backend-architect.md` states the exact structure or maintainability problem being addressed.
2. **Safety net** - `.claude/agents/backend-tester.md` confirms tests cover current behavior or adds focused tests first.
3. **Refactor** - `.claude/agents/backend-developer.md` changes code in small steps while preserving public behavior.
4. **Verify** - Run focused tests and relevant suites after each meaningful step.
5. **Review** - `.claude/agents/backend-reviewer.md` checks behavior preservation, API compatibility, and data safety.

## Definition Of Done

- Public behavior is unchanged.
- Existing API contracts remain compatible unless the user approved otherwise.
- Tests that cover the area pass.
- The refactor improves the stated goal.
- Review has no blockers.
