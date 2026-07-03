---
name: prisma-indexing
description: 
---

# Prisma Indexing

**Category:** prisma · **Status:** 🟢 Active

## When to use
Khi thêm `@@index`/`@unique` cho cột hay dùng để query/sort/join.

## Steps
1. Đánh index cho cột xuất hiện trong `where`, `orderBy`, hoặc khóa ngoại join.
2. Dùng `@unique`/`@@unique` cho ràng buộc duy nhất (email, slug, cặp cột).
3. Composite index khi query lọc nhiều cột cùng lúc; thứ tự cột theo độ chọn lọc.
4. Đừng đánh index tràn lan: mỗi index tốn ghi + bộ nhớ, chỉ thêm khi có truy vấn thật.
5. Kiểm chứng bằng `EXPLAIN` nếu nghi query chậm.

## Template
```prisma
model Post {
  id       String @id @default(cuid())
  slug     String @unique
  authorId String
  status   String

  @@index([authorId])
  @@index([status, createdAt])
  @@unique([authorId, slug])
}
```

## Example
**Good:** index cho FK + cột filter/sort thường dùng, composite đúng thứ tự, unique cho slug.
**Avoid:** index mọi cột, thiếu index trên FK gây full scan, unique nhầm chỗ.

## Checklist
- [ ] Cột where/orderBy/FK có index
- [ ] Ràng buộc duy nhất dùng @unique/@@unique
- [ ] Composite index đúng thứ tự cột
- [ ] Không index thừa, đã cân nhắc chi phí ghi
