---
description: Use when the user asks for a new REST resource or a new endpoint on an existing module. Triggers — tạo API, thêm endpoint, CRUD, new route, scaffold, API作成, エンドポイント追加.
argument-hint: <resource-name>
model: sonnet
---

# Generate API

**Resource:** $ARGUMENTS

## Trigger

Use when scaffolding a NestJS REST resource or extending an existing module with new endpoint behavior.

## Process Precedence

This command is the process for this task. Its design and approval step is the `backend-clarify-and-approve` skill — do not also run `superpowers:brainstorming`, `superpowers:writing-plans`, or `superpowers:subagent-driven-development`.

## Execution Mode

The approval question of the `backend-clarify-and-approve` skill also picks the execution mode. **Subagents**: dispatch the tester and developer steps as written below. **Inline**: the main agent performs those steps itself, in the same order — test first, then implementation — and still dispatches **backend-reviewer** for the review step.

## Steps

1. **Context Brief (main agent, once)** — use the `sourcebase-reuse-first` skill to find a similar module to copy, then write a Context Brief in the format used by `/new-feature`.
2. **Define contract and module placement (main agent)** — use the `rest-api-contract` skill to list method, path, auth, request DTO, response DTO, errors, and pagination. Decide new module vs. extend existing by following the closest existing module. Dispatch **backend-architect** only when no existing module is a clear fit.
2b. **Approve** — apply the `backend-clarify-and-approve` skill: ask blocking questions (auth, ownership, filters) one at a time, present the contract and module placement, and stop until the user approves.
3. **Tests and scaffold in parallel** — in one message, dispatch **backend-tester** (test files only) and **backend-developer** (production files only, just the files the contract needs). Pass both the brief and the contract.
4. **Verify (main agent)** — run the new tests. If a test fails, compare it with the approved design: the implementation deviates → send it back to **backend-developer**; the test misreads the design → send it back to **backend-tester**; the design is ambiguous → ask the user. Then run lint, typecheck, and the module's suite **once**.
5. **Review** — dispatch **backend-reviewer** with the brief, the contract, the diff, and the verification result.
6. **Finish** — if `.codegraph/` exists, run `codegraph sync` once. Invoke the `backend-change-record` skill. Write the record only if the diff matches one of its conditions.

## Scaffold Checklist

- [ ] Module follows the existing feature-module pattern.
- [ ] Controller path matches project route naming.
- [ ] Request DTOs use validation decorators.
- [ ] Response DTOs are explicit.
- [ ] Entity uses UUID and explicit database names when a table is needed.
- [ ] Migration plan exists when schema changes.
- [ ] Tests cover success and key failures.
- [ ] Change record written, or skipped because no condition matched.
