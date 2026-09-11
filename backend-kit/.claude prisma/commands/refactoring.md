---
description: Improve backend structure without changing behavior, behind a test safety net.
---

# Refactoring

## Trigger

Use when improving backend structure without changing behavior.

## Delegation

Run each step named below through that subagent with the Agent tool (`subagent_type`), and wait for its result before the next step. Do not read the agent file and play the role yourself - the point of the split is that each agent gets a clean context and its own tool limits.

## Steps

0. **Context** - Read `CLAUDE.md`, related modules, and current tests.
1. **Goal** - the `backend-architect` subagent states the exact structure or maintainability problem being addressed.
2. **Safety net** - the `backend-tester` subagent confirms tests cover current behavior or adds focused tests first.
3. **Refactor** - the `backend-developer` subagent changes code in small steps while preserving public behavior.
4. **Verify** - Run focused tests and relevant suites after each meaningful step.
5. **Review** - the `backend-reviewer` subagent checks behavior preservation, API compatibility, and data safety.

## Definition Of Done

- Public behavior is unchanged.
- Existing API contracts remain compatible unless the user approved otherwise.
- Tests that cover the area pass.
- The refactor improves the stated goal.
- Review has no blockers.
