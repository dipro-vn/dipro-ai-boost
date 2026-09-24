---
description: Use when the user asks to restructure backend code without changing behavior. Triggers — refactor, tách, gom, dọn code, clean up, restructure, リファクタ.
argument-hint: <target module or structural problem>
model: opus
---

# Refactoring

**Request:** $ARGUMENTS

## Trigger

Use when improving backend structure without changing behavior.

## Process Precedence

This command is the process for this task. Its design and approval step is the `backend-clarify-and-approve` skill — do not also run `superpowers:brainstorming`, `superpowers:writing-plans`, or `superpowers:subagent-driven-development`.

## Execution Mode

The approval question of the `backend-clarify-and-approve` skill also picks the execution mode. **Subagents**: dispatch the tester and developer steps as written below. **Inline**: the main agent performs those steps itself, in the same order — test first, then implementation — and still dispatches **backend-reviewer** for the review step.

## Steps

0. **Context Brief (main agent, once)** — read `CLAUDE.md`, the target module, and its tests. Write a Context Brief in the format used by `/new-feature`, including the stated goal and the target structure.
1. **Goal** — if the target structure is already stated, skip this step. Otherwise dispatch **backend-architect** with the brief to state the exact problem and the target structure.
1b. **Approve** — apply the `backend-clarify-and-approve` skill: present the target structure, the files that move, and what stays public. Stop until the user approves.
2. **Safety net** — run the module's existing tests. Dispatch **backend-tester** only if the public behavior being moved is not covered.
3. **Refactor** — make small steps while preserving public behavior. Do this directly when it is confined to one module; dispatch **backend-developer** with the brief and target structure when it spans several modules.
4. **Verify** — run the focused tests after each meaningful step, and the relevant suite **once** at the end.
5. **Review** — dispatch **backend-reviewer** with the brief, the diff, and the verification result to check behavior preservation, API compatibility, and data safety.
6. **Finish** — if `.codegraph/` exists, run `codegraph sync` once. Invoke the `backend-change-record` skill. Write the record only if the diff matches one of its conditions.

## Definition Of Done

- Public behavior is unchanged.
- Existing API contracts remain compatible unless the user approved otherwise.
- Tests that cover the area pass.
- The refactor improves the stated goal.
- Review has no blockers.
- A change record exists, or no record condition was matched.
