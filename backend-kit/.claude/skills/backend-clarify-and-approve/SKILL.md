---
name: backend-clarify-and-approve
description: Use when a workflow is about to design or change backend behavior, before any code is written. Symptoms — an analyst returned open questions, the expected behavior of a bug is unclear, a design exists that the user has not seen, a task that looked small turned out to touch a migration, contract, guard, or cache key.
metadata:
  stack: process, requirements
---

# Backend Clarify And Approve

Use this skill in the **main agent** to turn open questions into answers and a design into an approved plan. Subagents cannot talk to the user — only the main agent asks.

<HARD-GATE>
Do not dispatch **backend-developer**, write production code, or write a migration until the user has explicitly approved the intended change. This applies on every path. What scales with task size is the length of the design, never the approval.
</HARD-GATE>

## Stay In One Turn

Ask every question **and the final approval** through the question tool (AskUserQuestion). A tool answer keeps the workflow inside the same turn, so the command's `model:` stays in effect. A plain-text question ends the turn, and the user's reply starts a new turn on the session model — the rest of the workflow would then run on whatever model the session uses.

Fall back to a plain message only when the question tool is unavailable, and say so.

## Process Precedence

When a kit command is running, this skill **is** the design and approval step. Do not also run `superpowers:brainstorming` or `superpowers:writing-plans`, and do not write a second spec under `docs/superpowers/`. TDD rules come from the `nestjs-testing` skill. Running two processes asks the user the same questions twice and doubles the time.

## Announce The Path

Before the first question, state the path in one line so the user can override it — "This looks Small, so I'll show a short design here." The path rules are in the command being run (Small or Standard).

When unsure between two paths, take the heavier one. The ratchet is one-way: if hidden complexity appears mid-task (a migration, a contract change, a guard or ownership rule, a new cache key), stop, say so, and move to the Standard path. Nothing moves down mid-task.

## Asking Questions

- Ask **one question per message**. Wait for the answer before the next one.
- Prefer multiple choice. Put the recommended option first and mark it "(Recommended)". The user can always pick "Other" for a free-text answer.
- Ask only **blocking** questions — ones whose answer changes behavior, permissions, data ownership, or the contract. Examples: who may delete the record, what happens to child rows, whether the field is visible to other tenants.
- Do not ask what the repository can answer. Look it up.
- **Non-blocking** questions get a stated assumption instead, e.g. "Default page size is 20, as in other list endpoints." List every assumption in the design so the user can correct it.

## Presenting The Design

**Small path** — a short design in chat, a few sentences:
- What changes and why.
- Files touched.
- How it is tested.
- Assumptions.

**Standard path**:
1. Present 2–3 approaches with trade-offs. Lead with the recommended one and say why. Remove anything not required (YAGNI).
2. After the user picks one, present the design in sections scaled to complexity: contract (endpoints, DTOs, status codes), data (entities, migration, transaction), authorization, cache, error handling, tests. Ask after each non-trivial section whether it looks right.
3. For a new module or a contract another team consumes, save the approved design to `docs/backend/specs/YYYY-MM-DD-<topic>.md` and ask the user to review the file before implementation.

## Approval

Show the design, then ask one question through the question tool — "Proceed with this design?" — that approves the design **and** picks how it is executed. Put the option recommended for the path first:

| Option | Recommended for | What happens |
| --- | --- | --- |
| **Approve — subagents** | Standard path | Tests and implementation are dispatched to **backend-tester** and **backend-developer** in parallel, each with the Context Brief and the approved design |
| **Approve — inline** | Small path | The main agent does the test and implementation steps itself, in order: failing test first, then the change, then verification |
| **Revise** | — | Revise the design and ask again |

In the option description, give the reason in a few words — for example "several files, tests and code separate cleanly" for subagents, or "changes are tightly coupled" for inline.

Do nothing else until the answer arrives. Starting implementation before the answer skips the gate.

**Either mode keeps the independent review.** After verification, dispatch **backend-reviewer** whether the work ran inline or in subagents — a reviewer that did not write the code catches what the author missed. Only a Small path task may use the self-review described in its command.

**Choosing between them:**

- Subagents — many files, tests and implementation separate cleanly, parallel work saves time, and the developer runs on a cheaper model. Costs a handoff per agent.
- Inline — changes tightly coupled across files, the user wants to watch each step, or the task is short enough that a handoff costs more than it saves. Runs on the command's model and grows the main context.

The answer applies to this task only. Do not carry it over to the next task.
- Each task gets its own approval. Approval of one change does not cover a follow-up change.

## Red Flags

| Thought | Reality |
| --- | --- |
| "It's too small to need approval" | Small means a short design, not no design. |
| "I'll start while they read the design" | The gate is the approval. Stop until you hear yes. |
| "The architect can decide this open question" | Product and data rules come from the user, not a guess. |
| "I'll ask all five questions at once" | One per message. Batched questions get shallow answers. |
| "I'll just ask in plain text" | That ends the turn and drops the command's model. Use the question tool. |
| "Superpowers brainstorming also applies" | One process per task. This skill replaces it inside kit commands. |
| "I'll pick subagents or inline myself" | The user picks, in the approval question. Recommend one; do not decide silently. |
| "It ran inline, so I reviewed it myself" | Standard work still goes to **backend-reviewer**. Self-review is for the Small path only. |
| "It grew, but I'm almost done" | Hidden complexity moves the task to Standard. Stop and say so. |
