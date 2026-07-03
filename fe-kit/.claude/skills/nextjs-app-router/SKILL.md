---
name: nextjs-app-router
description: 
---

# App Router

**Category:** nextjs · **Status:** 🟢 Active

## When to use
Khi tổ chức route trong thư mục `app/` với layout, page, loading, error.

## Steps
1. Mỗi route là 1 folder; `page.tsx` render UI, `layout.tsx` bọc layout dùng chung.
2. Thêm `loading.tsx` cho Suspense fallback, `error.tsx` ('use client') cho error boundary.
3. Dùng route group `(group)` để gom route mà không ảnh hưởng URL.
4. `not-found.tsx` cho 404; `template.tsx` khi cần remount mỗi navigation.
5. Giữ layout là Server Component, không đặt state client ở layout gốc.

## Template
```tsx
// app/(dashboard)/users/layout.tsx
export default function Layout({ children }: { children: React.ReactNode }) {
  return <section className="users">{children}</section>;
}
// app/(dashboard)/users/page.tsx
export default async function Page() {
  const users = await getUsers();
  return <UserList users={users} />;
}
```

## Example
**Good:** Tách loading/error riêng từng segment, route group gom layout.
**Avoid:** Nhồi mọi UI vào 1 page, bỏ error boundary, dùng `pages/` lẫn `app/`.

## Checklist
- [ ] page.tsx và layout.tsx đúng vai trò
- [ ] Có loading.tsx / error.tsx khi cần
- [ ] Route group không phá URL
- [ ] Layout giữ ở phía server
