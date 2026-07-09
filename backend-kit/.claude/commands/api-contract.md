# API Contract

**Type:** Workflow

## Trigger

Use when producing or reviewing a REST API contract for backend work.

## Steps

1. **Read requirements** - Identify actors, auth, data ownership, fields, filters, pagination, and errors.
2. **Inspect existing contracts** - Use `.claude/skills/sourcebase-reuse-first/SKILL.md` to find project response and error shapes.
3. **Draft contract** - Use `.claude/skills/rest-api-contract/SKILL.md` to document endpoint table, DTOs, status codes, and cache notes.
4. **Review security** - Use `.claude/skills/backend-security-review/SKILL.md` to confirm auth and output shaping.
5. **Review database impact** - Use `.claude/skills/postgresql/SKILL.md` for filters, sorting, pagination, and indexes.
6. **Finalize** - Provide a contract that implementers and API consumers can use without guessing.

## Output Format

```markdown
| Method | Path | Auth | Request | Response |
| --- | --- | --- | --- | --- |
| GET | `/api/<resource>` | Bearer JWT | `<QueryDto>` | `<ResponseDto>` |

Errors:
- 400: validation failed
- 401: authentication required
- 403: access denied
- 404: resource not found

Notes:
- Pagination:
- Cache:
- Breaking changes:
```

## Definition Of Done

- Every endpoint has method, path, auth, request, and response.
- Errors are documented.
- Pagination and sorting are explicit.
- Cache behavior is documented if relevant.
- Breaking changes are called out.
