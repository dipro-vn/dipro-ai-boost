---
name: backend-change-record
description: Use when a task that changed backend code is finishing, before reporting it done. Symptoms — a migration was added, a request or response shape changed, a new route exists, a cache key was added, something could not be verified, a problem was found and deliberately left alone.
metadata:
  stack: documentation, handoff
---

# Backend Change Record

Use this skill at the end of a task that changed backend code, to record what the
next person needs and cannot recover from the diff.

Save to `docs/backend/changes/YYYY-MM-DD-<topic>.md`. Get the date from
`date +%Y-%m-%d` — never guess it. One file per task, so parallel work does not
conflict.

## Write One Only If The Diff Says So

Check the diff against this table. If nothing matches, skip the record and say so —
a directory full of notes about trivial fixes is a directory nobody reads.

| Condition | Check |
| --- | --- |
| A migration was added or changed | New or edited file under the migrations directory |
| A request or response shape changed | A DTO field added, removed, renamed, or retyped |
| A route was added or removed | A new or deleted controller method |
| A cache key was added or its invalidation changed | New key string, new or changed TTL |
| Something could not be verified | A test or command that did not run |
| A problem was found and left alone | Anything reported as out of scope |

A rename, a comment, a log-message wording change, or a fix with none of the above
needs no record.

## The Document

Seven parts, in this order. A part with nothing to say gets the single word `None.`
— an empty heading tells the reader the question was considered.

```markdown
# <what this task did, in one line>

<Two or three sentences — why this change exists. Link the ticket if there is one.>

## Changed

- `POST /api/orders` — new endpoint, returns `OrderDetailDto`
- `OrderEntity` — added `cancelled_at` (nullable timestamptz)

## Breaking changes

- `GET /api/orders` now returns `{ items, total, page, limit }` instead of an array.
  Consumers reading the bare array break. Frontend notified <date>.

## Migration

`1735000000000-AddOrderCancelledAt` adds one nullable column.
Rollback drops it; no data is recoverable after rollback.

## Cache

`orders:company:<companyId>` invalidated on create, update, and cancel. TTL 300s.

## Verified

- `npm test -- orders` — 14 passed
- Manual check of the cancel flow against local Postgres

## Not verified

- Behaviour under concurrent cancel of the same order. No test exists.

## Found, not fixed

- `ProductsService.findById(id)` takes no `companyId`. No caller today, so not
  exploitable, but any new `GET /api/products/:id` makes it a cross-tenant leak.
```

## What Each Part Is For

**Changed** — the identifiers a person will grep for. Name the route, the DTO, the
column. A line saying "updated the orders module" helps nobody.

**Breaking changes** — the part with a real audience. Say what breaks, for whom, and
whether they were told.

**Not verified** — the honest half of Verified. If tests did not run, this is where
that lives, and it is the most valuable line in the file when something later fails.

**Found, not fixed** — problems noticed while working and deliberately left. This
information exists nowhere else once the task closes.

## Checklist

- [ ] The diff matched at least one condition in the table above.
- [ ] Date came from `date +%Y-%m-%d`.
- [ ] Every changed route, DTO, column, and cache key is named exactly.
- [ ] Breaking changes name the affected consumer.
- [ ] Migration rollback describes what is lost, not only the command.
- [ ] Commands that were run appear under Verified with their result.
- [ ] Anything unrun appears under Not verified.
- [ ] Out-of-scope findings are recorded with their risk.
- [ ] Empty sections say `None.` rather than being deleted.
