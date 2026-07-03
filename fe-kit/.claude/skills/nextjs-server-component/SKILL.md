---
name: nextjs-server-component
description: 
---

# Server Component

**Category:** nextjs · **Status:** 🟢 Active

## When to use
Khi render UI không cần tương tác client; mặc định mọi component trong `app/` là RSC.

## Steps
1. Không thêm `'use client'`; component chạy trên server.
2. Fetch data trực tiếp bằng async/await, gọi DB/API ngay trong component.
3. Không dùng hook (useState/useEffect) hay browser API (window/localStorage).
4. Truyền data xuống Client Component qua props (phải serializable).
5. Đặt secret/key ở server, không lộ ra bundle client.

## Template
```tsx
// Server Component (mặc định)
export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await db.product.findById(params.id);
  return (
    <article>
      <h1>{product.name}</h1>
      <AddToCartButton productId={product.id} /> {/* Client Component */}
    </article>
  );
}
```

## Example
**Good:** Fetch trực tiếp, render markup, đẩy phần tương tác ra client con.
**Avoid:** Thêm 'use client' không cần, dùng useEffect để fetch, đọc window.

## Checklist
- [ ] Không có hook/browser API
- [ ] Fetch data async trực tiếp
- [ ] Props truyền xuống client serializable
- [ ] Secret giữ ở server
