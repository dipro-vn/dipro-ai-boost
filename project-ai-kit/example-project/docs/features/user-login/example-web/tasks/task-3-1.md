# [FE] authSlice + authApi + useAuth

## Backlog Info
- **Category:** Frontend
- **Estimate Hour:** 5h
- **Status:** Open

## Metadata
| Thuộc tính | Giá trị |
|---|---|
| Phase | 3 — Frontend |
| Repo | `example-web` |
| Estimate | ~5h |

## Mục tiêu

Tầng state và data cho auth, theo `example-web/DESIGN.md` §2 → §4.

## Phạm vi

- `authSlice` (Redux Toolkit) giữ client state: user, trạng thái đăng nhập.
- `authApi.ts` bọc 5 endpoint đã chốt ở `task-2-2`.
- Hook `useAuth` + `usePasswordReset`.
- Token theo chiến lược ở DESIGN §8 — không để JWT trần trong `localStorage`.

## Phụ thuộc

Chờ API Contract từ `example-api/tasks/task-2-2.md`.
