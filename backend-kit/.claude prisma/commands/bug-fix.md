---
description: Reproduce, diagnose, fix, and regression-test a backend bug at its root cause.
---

# Bug Fix

## Trigger

Use when backend behavior is incorrect, unstable, insecure, slow, or inconsistent with the expected API contract.

## Delegation

Run each step named below through that subagent with the Agent tool (`subagent_type`), and wait for its result before the next step. Do not read the agent file and play the role yourself - the point of the split is that each agent gets a clean context and its own tool limits.

## Steps

0. **Context** - Read `CLAUDE.md`, related docs, nearby code, and existing tests.
1. **Reproduce** - the `backend-tester` subagent writes or identifies a failing test that proves the bug. Micro-fixes may skip this only with a written reason.
2. **Diagnose** - Find the root cause and affected scope. Do not patch only the symptom.
3. **Fix** - the `backend-developer` subagent makes the smallest change that resolves the root cause.
4. **Regression** - the `backend-tester` subagent verifies the failing test now passes and runs the relevant suite.
5. **Review** - the `backend-reviewer` subagent checks for regressions in security, data integrity, query behavior, and contract shape.

## Definition Of Done

- The bug no longer reproduces.
- A regression test exists or a micro-fix reason is recorded.
- Relevant tests pass.
- The fix stays within root-cause scope.
- Review has no blockers.
