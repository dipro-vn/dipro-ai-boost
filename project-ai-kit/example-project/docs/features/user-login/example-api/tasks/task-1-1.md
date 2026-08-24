# [BE] Migration — cột lockout cho `users` + bảng `password_reset_tokens`

## Backlog Info
- **Category:** Backend_Migration
- **Estimate Hour:** 3h
- **Status:** Open

## Metadata
| Thuộc tính | Giá trị |
|---|---|
| Phase | 1 — Database |
| Repo | `example-api` |
| Estimate | ~3h |

## Mục tiêu

Chuẩn bị schema cho luồng đăng nhập có khoá tài khoản và đặt lại mật khẩu, theo `example-api/DESIGN.md` §2.

## Phạm vi

- Thêm `failed_login_attempts` (int, default 0) và `locked_until` (timestamptz, nullable) vào bảng `users`.
- Đặt unique index trên `users.email` — DESIGN §2 ghi rõ cột này chưa unique ở schema cũ.
- Tạo bảng `password_reset_tokens` (`token_hash`, `user_id`, `expires_at`, `used_at`).

## Acceptance Criteria liên quan

AC-01, AC-28 (lock state phải nhất quán khi chạy nhiều instance).

## Ghi chú

Migration phải reversible — `down()` bắt buộc có, không drop cột chứa dữ liệu thật.
