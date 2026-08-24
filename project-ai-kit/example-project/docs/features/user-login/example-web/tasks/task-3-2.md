# [FE] LoginPage, ForgotPassword, ResetPassword + ProtectedRoute

## Backlog Info
- **Category:** Frontend
- **Estimate Hour:** 6h
- **Status:** Open

## Metadata
| Thuộc tính | Giá trị |
|---|---|
| Phase | 3 — Frontend |
| Repo | `example-web` |
| Estimate | ~6h |

## Mục tiêu

Màn hình và điều hướng cho luồng đăng nhập, theo `example-web/DESIGN.md` §5 → §7.

## Phạm vi

- `LoginPage` — form react-hook-form + yup, hiện thông báo khoá tài khoản còn bao nhiêu phút.
- `ForgotPasswordPage`, `ResetPasswordPage`.
- `ProtectedRoute` chặn route cần đăng nhập, redirect kèm `returnTo`.

## Phụ thuộc

`task-3-1` phải xong trước.
