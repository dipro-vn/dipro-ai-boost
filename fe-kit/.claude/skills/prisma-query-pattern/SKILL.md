---
name: prisma-query-pattern
description: 
---

# Prisma Query Pattern

**Category:** prisma · **Status:** 🟢 Active

## When to use
Khi truy vấn dữ liệu: `findUnique`/`findMany`, `select`/`include`, tránh over-fetch & N+1.

## Steps
1. Dùng `findUnique` cho 1 bản ghi theo khóa; `findMany` cho list có `where`.
2. Chỉ lấy field cần bằng `select`; tránh trả nguyên model khi UI chỉ dùng vài cột.
3. Load quan hệ bằng `include`/nested `select` trong 1 query, không loop query con (N+1).
4. List luôn có `take`/`skip` (phân trang) + `orderBy` xác định.
5. Filter/sort theo cột đã đánh index (xem skill indexing).

## Template
```ts
const posts = await prisma.post.findMany({
  where: { status: 'PUBLISHED' },
  select: { id: true, title: true, author: { select: { name: true } } },
  orderBy: { createdAt: 'desc' },
  take: 20,
});
```

## Example
**Good:** `select` đúng field, `include`/nested gộp 1 query, có phân trang + orderBy.
**Avoid:** lấy toàn bộ model, loop gọi query trong vòng lặp (N+1), findMany không giới hạn.

## Checklist
- [ ] `select` chỉ field cần dùng
- [ ] Quan hệ load bằng include/nested (không N+1)
- [ ] List có take/skip + orderBy
- [ ] Filter/sort theo cột có index
