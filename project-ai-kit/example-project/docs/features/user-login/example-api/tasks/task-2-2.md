# [BE] 5 endpoint auth + error code enum

## Backlog Info
- **Category:** Backend_API
- **Estimate Hour:** 5h
- **Status:** Open

## Metadata
| Thuộc tính | Giá trị |
|---|---|
| Phase | 2 — Service + API endpoint |
| Repo | `example-api` |
| Estimate | ~5h |

## Mục tiêu

Expose `AuthService` qua REST, chốt contract cho FE/Mobile — `example-api/DESIGN.md` §3 và §5.

## Phạm vi

- `POST /api/auth/login`, `/refresh`, `/logout`, `/forgot-password`, `/reset-password`.
- DTO có `class-validator` cho mọi input.
- Bổ sung error code enum mới trong `src/common/enums/error-codes.enum.ts`.
- Rate limiting trên `/login` và `/forgot-password`.

## Acceptance Criteria liên quan

AC-13 → AC-30.

## Ghi chú

Đây là task khoá API Contract — FE và Mobile chờ contract này trước khi vào Phase 3.
