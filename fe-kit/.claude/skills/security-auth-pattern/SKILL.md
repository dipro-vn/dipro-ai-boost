---
name: security-auth-pattern
description: 
---

# Auth Pattern

**Category:** security · **Status:** 🟢 Active

## When to use
Khi thiết kế luồng đăng nhập FE, bảo vệ route theo trạng thái/quyền, và lưu session an toàn.

## Steps
1. Xác định nguồn sự thật: server session (cookie httpOnly) là mặc định an toàn.
2. Bọc route cần bảo vệ bằng guard; redirect về login khi chưa đăng nhập, giữ `returnUrl`.
3. Phân quyền theo role/permission, kiểm tra cả ở FE (ẩn UI) lẫn server (bắt buộc).
4. Không tin trạng thái auth ở client tuyệt đối — server vẫn phải authorize mỗi request.
5. Xử lý hết hạn/đăng xuất: xoá session, vô hiệu cache, chuyển hướng rõ ràng.

## Template
```tsx
function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to={`/login?returnUrl=${pathname}`} replace />;
  return <>{children}</>;
}
```

## Example
**Good:** guard route, server vẫn authorize, lưu session httpOnly.
**Avoid:** chỉ ẩn UI mà không chặn server, lưu cờ `isAdmin` ở localStorage.

## Checklist
- [ ] Route bảo vệ có guard + returnUrl
- [ ] Server authorize mọi request
- [ ] Phân quyền theo role/permission
- [ ] Đăng xuất xoá session + cache
