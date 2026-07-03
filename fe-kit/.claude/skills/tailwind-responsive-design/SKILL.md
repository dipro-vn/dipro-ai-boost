---
name: tailwind-responsive-design
description: 
---

# Responsive Design

**Category:** tailwind · **Status:** 🟢 Active

## When to use
Khi làm layout responsive bằng Tailwind với prefix breakpoint, theo hướng mobile-first.

## Steps
1. Viết style mặc định cho mobile trước; thêm prefix `sm:`/`md:`/`lg:` cho màn lớn hơn.
2. Hiểu prefix là min-width: `md:flex` áp dụng từ md trở lên.
3. Đổi layout theo breakpoint (`flex-col md:flex-row`, `grid-cols-1 md:grid-cols-3`).
4. Dùng breakpoint chuẩn của config; tránh tự chế giá trị tùy ý lung tung.
5. Test ở các bề rộng để tránh vỡ giữa các mốc.

## Template
```tsx
<div className="flex flex-col gap-4 md:flex-row md:gap-6">
  <aside className="w-full md:w-64">{nav}</aside>
  <main className="flex-1">{content}</main>
</div>

<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">{cards}</div>
```

## Example
**Good:** base = mobile, nâng cấp bằng prefix, đổi cột/hướng theo breakpoint.
**Avoid:** viết desktop trước rồi `max-*` ngược, hardcode width cố định, bỏ qua mobile.

## Checklist
- [ ] Mobile-first, base không prefix
- [ ] Dùng prefix `sm/md/lg` để nâng cấp
- [ ] Layout đổi đúng theo breakpoint
