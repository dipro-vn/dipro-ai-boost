---
description: Produce or review a REST API contract - endpoints, auth, DTOs, pagination, and error bodies.
---

# API Contract

## Trigger

Use when producing or reviewing a REST API contract for backend work.

## Steps

1. **Read requirements** - Identify actors, auth, data ownership, fields, filters, pagination, and errors.
2. **Inspect existing contracts** - Use the `sourcebase-reuse-first` skill to find project response and error shapes.
3. **Draft contract** - Use the `rest-api-contract` skill to document endpoint table, DTOs, and status codes.
4. **Review security** - Use the `backend-security-review` skill to confirm auth and output shaping.
5. **Review database impact** - Use the `postgresql` skill for filters, sorting, pagination, and indexes.
6. **Finalize** - Provide a contract that implementers and API consumers can use without guessing.

## Output Format

```markdown
| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| GET | `/<resource>` | Bearer JWT | `<QueryDto>` | `BasePaginationResponseDto<<ItemDto>>` |

Errors (bodies follow the Error Shape table in the `rest-api-contract` skill):
- 400: validation failed - `{ message: string[], error: 'Bad Request', statusCode: 400 }`
- 401: authentication required
- 403: access denied
- 404: resource not found

Notes:
- Pagination: `totalItems` = rows in this page, `allItems` = grand total
- Breaking changes:
```

## Definition Of Done

- Every endpoint has method, path, auth, request, and response.
- Paths carry no `/api` prefix - see Route Convention in the `rest-api-contract` skill.
- Errors are documented.
- Pagination and sorting are explicit, and `totalItems` / `allItems` are spelled out.
- Breaking changes are called out.
