# [BE] AuthService — login, đếm lần sai, khoá 15 phút

## Backlog Info
- **Category:** Backend_API
- **Estimate Hour:** 6h
- **Status:** Open

## Metadata
| Thuộc tính | Giá trị |
|---|---|
| Phase | 2 — Service + API endpoint |
| Repo | `example-api` |
| Estimate | ~6h |

## Mục tiêu

Business logic đăng nhập trong `AuthService`, theo `example-api/DESIGN.md` §4 và luồng HP-A §6.

## Phạm vi

- `login(email, password, rememberMe)` — verify bcrypt, phát access + refresh token.
- Tăng `failed_login_attempts` khi sai; đạt ngưỡng thì set `locked_until`.
- AF-07: hết hạn khoá mà vẫn sai tiếp → khoá lại, không cộng dồn vô hạn.
- Cập nhật lock state bằng QueryBuilder để an toàn khi chạy nhiều instance (AC-28).

## Acceptance Criteria liên quan

AC-01 → AC-12, AF-07.

## Phụ thuộc

`task-1-1` phải xong trước (cần cột mới).
