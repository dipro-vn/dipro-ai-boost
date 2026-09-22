---
description: Use when the user reports wrong, broken, slow, or unexpected backend behavior. Triggers — lỗi, bug, không chạy, bị sai, fix, broken, error, 500, バグ, 不具合, エラー. Reproduces with a failing test, fixes the root cause, and reviews.
argument-hint: <bug description>
model: sonnet
---

# Bug Fix

**Request:** $ARGUMENTS

## Trigger

Use when backend behavior is incorrect, unstable, insecure, slow, or inconsistent with the expected API contract.

## Process Precedence

This command is the process for this task. Its design and approval step is the `backend-clarify-and-approve` skill — do not also run `superpowers:brainstorming`, `superpowers:writing-plans`, or `superpowers:subagent-driven-development`.

## Execution Mode

The approval question of the `backend-clarify-and-approve` skill also picks the execution mode. **Subagents**: dispatch the tester and developer steps as written below. **Inline**: the main agent performs those steps itself, in the same order — test first, then implementation — and still dispatches **backend-reviewer** for the review step.

## Step 0 — Context Brief (main agent, once)

Read `CLAUDE.md`, the code on the failing path, and its existing tests. Write a Context Brief (request, files to read, patterns, commands, size) in the format used by `/new-feature`. Pass it to every subagent.

If the expected behavior is not stated and cannot be derived from the contract, tests, or docs, ask the user before reproducing — do not guess which behavior is correct.

## Choose The Path

**Small** — the root cause is in at most 3 production files, and the fix does not change a migration, an endpoint contract, a guard, or a cache key. Anything else is **Standard**.

## Small Path (no subagents)

1. **Reproduce** — write a failing test, following the `nestjs-testing` skill. Micro-fixes may skip this only with a written reason.
2. **Diagnose** — find the root cause, not just the symptom.
2b. **Approve** — apply the `backend-clarify-and-approve` skill: if the expected behavior is unclear, ask first (one question at a time); then state the root cause and the fix in a few sentences and stop until the user approves.
3. **Fix** — make the smallest change that resolves the root cause.
4. **Verify** — run the focused test, then lint and typecheck.
5. Self-review the diff against the Definition Of Done.

## Standard Path

1. **Reproduce** — dispatch **backend-tester** with the brief to write a failing test that proves the bug.
2. **Diagnose (main agent)** — find the root cause and affected scope.
2b. **Approve** — apply the `backend-clarify-and-approve` skill: ask about unclear expected behavior one question at a time, then present the root cause, affected scope, and fix options. Stop until the user approves.
3. **Fix** — dispatch **backend-developer** with the brief, the failing test, and the root cause.
4. **Verify (main agent)** — confirm the failing test now passes, then run the relevant suite **once**.
5. **Review** — dispatch **backend-reviewer** with the brief, the diff, and the verification result.

## Finish

- If `.codegraph/` exists, run `codegraph sync` once. If `.understand-anything/` exists, tell the user to refresh it; do not run it.
- Invoke the `backend-change-record` skill. Write the record only if the diff matches one of its conditions.

## Definition Of Done

- The user approved the root cause and fix before it was applied.
- The bug no longer reproduces.
- A regression test exists or a micro-fix reason is recorded.
- Relevant tests pass.
- The fix stays within root-cause scope.
- Review has no blockers.
- A change record exists, or no record condition was matched.
