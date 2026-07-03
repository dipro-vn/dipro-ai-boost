---
name: nextjs-data-fetching
description: 
---

# Data Fetching

**Category:** nextjs · **Status:** 🟢 Active

## When to use
Khi fetch data phía server trong App Router với kiểm soát cache/revalidate.

## Steps
1. Fetch trực tiếp trong Server Component bằng async/await, server-first.
2. Cấu hình cache: `fetch(url, { cache: 'force-cache' | 'no-store' })`.
3. Dùng ISR: `next: { revalidate: 60 }` để làm mới định kỳ.
4. Chạy song song các fetch độc lập bằng `Promise.all` để tránh waterfall.
5. Dùng `<Suspense>` + loading để stream phần chậm, không block cả trang.

## Template
```tsx
export default async function Page() {
  const [user, posts] = await Promise.all([
    fetch(`${API}/user`, { next: { revalidate: 60 } }).then((r) => r.json()),
    fetch(`${API}/posts`, { cache: 'no-store' }).then((r) => r.json()),
  ]);
  return <Dashboard user={user} posts={posts} />;
}
```

## Example
**Good:** Promise.all song song, revalidate hợp lý, no-store cho data động.
**Avoid:** await tuần tự gây waterfall, fetch ở client khi server làm được.

## Checklist
- [ ] Fetch server-first
- [ ] Cache/revalidate đặt đúng
- [ ] Promise.all cho fetch độc lập
- [ ] Suspense cho phần chậm
