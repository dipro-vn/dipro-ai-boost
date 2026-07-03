---
name: prisma-schema-design
description: 
---

# Prisma Schema Design

**Category:** prisma · **Status:** 🟢 Active

## When to use
Khi thiết kế hoặc sửa Prisma schema: model, relation, field type, naming.

## Steps
1. Model = danh từ số ít, PascalCase (`User`); field camelCase; map sang DB bằng `@@map`/`@map` nếu cần snake_case.
2. Chọn type sát domain: `String`, `Int`, `Decimal` (tiền), `DateTime`, `enum` thay cho chuỗi tự do.
3. Khai báo relation 2 chiều, dùng `@relation` với `fields`/`references` rõ ràng.
4. Mặc định hợp lý: `@id @default(cuid())`, `createdAt @default(now())`, `updatedAt @updatedAt`.
5. Nullable chỉ khi thật sự optional; còn lại để bắt buộc + default.

## Template
```prisma
model Post {
  id        String   @id @default(cuid())
  title     String
  status    PostStatus @default(DRAFT)
  authorId  String
  author    User     @relation(fields: [authorId], references: [id])
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@map("posts")
}

enum PostStatus { DRAFT PUBLISHED }
```

## Example
**Good:** type đúng domain, relation 2 chiều, default chuẩn, enum thay magic string.
**Avoid:** lạm dụng `String` cho mọi thứ, relation 1 chiều mơ hồ, thiếu createdAt/updatedAt.

## Checklist
- [ ] Naming nhất quán (model số ít PascalCase, field camelCase)
- [ ] Type sát domain, dùng enum khi hữu hạn
- [ ] Relation 2 chiều rõ fields/references
- [ ] Có id/createdAt/updatedAt và default hợp lý
