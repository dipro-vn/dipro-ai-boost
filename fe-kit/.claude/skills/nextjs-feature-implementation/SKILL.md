---
name: nextjs-feature-implementation
description: 
---

# Feature Implementation

**Category:** nextjs · **Status:** 🟢 Active

## When to use
Khi implement một feature Next.js end-to-end trong App Router.

## Steps
1. Thiết kế route/folder, xác định segment dynamic và layout dùng chung.
2. Dựng Server Component fetch data (cache/revalidate), tách phần tương tác ra client.
3. Thêm Server Action cho mutation + validate zod + revalidatePath.
4. Bổ sung loading.tsx, error.tsx, metadata cho segment.
5. Kiểm thử luồng (success/loading/error), dọn type và bundle client.

## Template
```
app/posts/
  page.tsx          // RSC: list, fetch server
  [id]/page.tsx     // RSC: detail
  new/page.tsx      // form -> Server Action
  actions.ts        // 'use server' create/update
  loading.tsx
  error.tsx
```

## Example
**Good:** Server-first, action validate, loading/error/metadata đầy đủ.
**Avoid:** Làm tất cả ở client, quên error boundary, mutation không revalidate.

## Checklist
- [ ] Route/layout thiết kế xong
- [ ] Server fetch + client lá tách bạch
- [ ] Server Action validate + revalidate
- [ ] loading/error/metadata đủ
