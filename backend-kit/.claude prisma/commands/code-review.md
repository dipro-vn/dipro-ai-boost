---
description: Review a backend change set before merge across architecture, security, database, queries, and tests.
---

# Code Review

## Trigger

Use when reviewing a backend change set before merge.

## Delegation

Run each step named below through that subagent with the Agent tool (`subagent_type`), and wait for its result before the next step. Do not read the agent file and play the role yourself - the point of the split is that each agent gets a clean context and its own tool limits.

## Steps

1. **Understand intent** - Read the requirement, acceptance criteria, API contract, and diff.
2. **Architecture review** - the `backend-reviewer` subagent checks module boundaries, provider usage, service responsibilities, and response DTOs.
3. **Security review** - Apply the `backend-security-review` skill.
4. **Database review** - Apply the `postgresql` skill for Prisma models, migrations, transactions, and queries.
5. **Performance review** - Apply the `backend-query-performance` skill.
6. **Test review** - Apply the `nestjs-testing` skill.
7. **Findings** - Report blocker, should fix, and suggestion items with reason and fix direction.
8. **Re-check** - After changes, re-check every blocker and agreed should-fix item.

## Definition Of Done

- All blockers are resolved.
- Relevant security, database, query, and test risks were reviewed.
- Findings are specific and actionable.
- The change is ready for merge from a backend review perspective.
