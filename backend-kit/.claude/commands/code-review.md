# Code Review

**Type:** Workflow

## Trigger

Use when reviewing a backend change set before merge.

## Steps

1. **Understand intent** - Read the requirement, acceptance criteria, API contract, and diff.
2. **Architecture review** - `.claude/agents/backend-reviewer.md` checks module boundaries, provider usage, service responsibilities, and response DTOs.
3. **Security review** - Apply `.claude/skills/backend-security-review/SKILL.md`.
4. **Database review** - Apply `.claude/skills/postgresql/SKILL.md` for entities, migrations, transactions, and queries.
5. **Cache and performance review** - Apply `.claude/skills/backend-query-cache-performance/SKILL.md` and `.claude/skills/redis-development/SKILL.md` where relevant.
6. **Test review** - Apply `.claude/skills/nestjs-testing/SKILL.md`.
7. **Findings** - Report blocker, should fix, and suggestion items with reason and fix direction.
8. **Re-check** - After changes, re-check every blocker and agreed should-fix item.

## Definition Of Done

- All blockers are resolved.
- Relevant security, database, cache, and test risks were reviewed.
- Findings are specific and actionable.
- The change is ready for merge from a backend review perspective.
