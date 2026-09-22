---
description: Build a new backend capability end to end — analysis, design, implementation, tests, review.
argument-hint: <feature description>
model: opus
---

# New Feature

**Request:** $ARGUMENTS

## Trigger

Use when building a new backend capability such as an endpoint, service flow, entity, migration, cache behavior, or integration inside the application layer.

## Process Precedence

This command is the process for this task. Its design and approval step is the `backend-clarify-and-approve` skill — do not also run `superpowers:brainstorming`, `superpowers:writing-plans`, or `superpowers:subagent-driven-development`.

## Execution Mode

The approval question of the `backend-clarify-and-approve` skill also picks the execution mode. **Subagents**: dispatch the tester and developer steps as written below. **Inline**: the main agent performs those steps itself, in the same order — test first, then implementation — and still dispatches **backend-reviewer** for the review step.

## Step 0 — Context Brief (main agent, once)

Invoke the `sourcebase-reuse-first` skill **once**, then write a Context Brief. Every subagent receives this brief, so no subagent repeats the exploration. When `.codegraph/` exists, build the code map with one `codegraph_explore` call naming the symbols of the affected flow, and paste its relevant output — subagents then read line ranges, not whole files.

```markdown
Request: <one paragraph>
Acceptance criteria: <given / to be defined>
Code map: <codegraph_explore output for the affected flow — symbols, call path, file:line ranges; "none" if no .codegraph/>
Files to read: <paths of similar modules, DTOs, entities, tests>
Patterns to follow: <guard, pagination DTO, exception shape, response shape, migration location>
Commands: <focused test, full test, lint, typecheck, migration — from CLAUDE.md or package.json>
Size: Small | Standard (reason)
```

Announce the chosen path in one line so the user can override it. If hidden complexity appears later, stop and move to Standard.

## Choose The Path

**Small** — all of these are true:
- At most 3 production files change.
- No migration, no new or changed endpoint contract.
- No change to guards, roles, or ownership rules.
- No new cache key.

Anything else is **Standard**.

## Small Path (no subagents)

0. **Clarify and approve** — apply the `backend-clarify-and-approve` skill: ask blocking questions one at a time, present a short design in chat, and ask the approval question (inline is recommended here). If the user picks subagents, continue from step 4 of the Standard path.
1. Write a failing test, following the `nestjs-testing` skill.
2. Implement the smallest change, following the skills whose trigger applies.
3. Run the focused test file, then lint and typecheck.
4. Self-review the diff against the Definition Of Done below.
5. Finish (see below).

## Standard Path

1. **Requirements** — if acceptance criteria are vague, dispatch **backend-analyst** with the brief. Then apply the `backend-clarify-and-approve` skill: ask the analyst's blocking questions one at a time and record the answers and assumptions.
2. **Approaches** — dispatch **backend-architect** with the brief, the answers, and the assumptions. Present its 2–3 approaches to the user and let them choose.
3. **Design and approval** — present the design for the chosen approach in sections, then ask the approval question, which also picks subagents or inline (per the `backend-clarify-and-approve` skill). No code before approval.
4. **Tests and implementation** — inline: write the tests, then implement. Subagents: in one message, dispatch:
   - **backend-tester** to write tests from the design's contract and acceptance criteria, in test files only.
   - **backend-developer** to implement the design, in production files only.
   Pass both the brief and the approved design.
5. **Verify (main agent)** — run the new tests. When `.codegraph/` exists, pick the relevant suite with `codegraph affected --quiet <changed files>` instead of running the whole module. If a test fails, compare it with the approved design: the implementation deviates → send it back to **backend-developer**; the test misreads the design → send it back to **backend-tester**; the design is ambiguous → ask the user. Then run lint, typecheck, and the relevant test suite **once**.
6. **Review** — dispatch **backend-reviewer** with the brief, the design, the diff, and the verification result. The reviewer does not re-run passing tests.
7. Finish (see below).

## Finish

- If `.codegraph/` exists, run `codegraph sync` once. If `.understand-anything/` exists, tell the user to refresh it; do not run it.
- Invoke the `backend-change-record` skill. Write the record only if the diff matches one of its conditions.

## Definition Of Done

- The user approved the design before implementation.
- Acceptance criteria are implemented.
- Request DTOs validate external input.
- Protected routes use the project guard pattern.
- Responses use DTOs or explicit response objects.
- Migration changes include rollback.
- Query and cache behavior have been reviewed.
- Focused tests and relevant suites pass.
- Review has no blockers.
- A change record exists, or no record condition was matched.
