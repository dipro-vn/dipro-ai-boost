---
name: nextjs-metadata
description: 
---

# Metadata

**Category:** nextjs · **Status:** 🟢 Active

## When to use
Khi cấu hình SEO/Open Graph cho route bằng Metadata API trong App Router.

## Steps
1. Export `metadata` (static) cho route cố định title/description.
2. Dùng `generateMetadata` (async) khi metadata phụ thuộc params/data.
3. Khai báo `openGraph` và `twitter` cho social preview.
4. Đặt metadata gốc ở `app/layout.tsx`, override ở segment con.
5. Dùng `title.template` để chuẩn hoá hậu tố title toàn site.

## Template
```ts
import type { Metadata } from 'next';

export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  const post = await getPost(params.id);
  return {
    title: post.title,
    description: post.excerpt,
    openGraph: { title: post.title, images: [post.cover] },
  };
}
```

## Example
**Good:** generateMetadata fetch data, có openGraph, title.template ở layout.
**Avoid:** Nhét <title> thủ công trong JSX, bỏ description/OG.

## Checklist
- [ ] Static vs generateMetadata đúng trường hợp
- [ ] Có title + description
- [ ] openGraph/twitter cho share
- [ ] title.template ở layout gốc
