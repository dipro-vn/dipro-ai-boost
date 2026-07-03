---
name: prisma-migration
description: 
---

# Prisma Migration

**Category:** prisma · **Status:** 🟢 Active

## When to use
Khi tạo/chạy migration: `migrate dev`, `migrate deploy`, đặt tên, tránh mất data.

## Steps
1. Sửa schema trước, rồi `prisma migrate dev --name <ý-nghĩa>` để sinh SQL ở local.
2. Đặt tên migration mô tả thay đổi: `add_post_status`, `rename_user_email`.
3. Review file SQL sinh ra trước khi commit; soi câu lệnh DROP/ALTER có thể mất data.
4. Đổi tên/đổi type không phá data: thêm cột mới → backfill → bỏ cột cũ (nhiều bước).
5. Production dùng `migrate deploy` (không `dev`); không bao giờ chạy `migrate reset` trên prod.

## Template
```bash
# local: tạo + apply migration
npx prisma migrate dev --name add_post_status

# review SQL trong prisma/migrations/<ts>_add_post_status/migration.sql

# production / CI
npx prisma migrate deploy
```

## Example
**Good:** tên rõ nghĩa, review SQL, đổi schema phá hỏng chia thành nhiều migration backfill.
**Avoid:** `--name update`, đổi type trực tiếp làm mất data, `migrate reset` trên prod.

## Checklist
- [ ] Tên migration mô tả thay đổi
- [ ] Đã review SQL sinh ra
- [ ] Thay đổi phá data được tách bước + backfill
- [ ] Prod dùng `migrate deploy`, không `reset`
