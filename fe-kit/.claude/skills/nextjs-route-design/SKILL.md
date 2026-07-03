---
name: nextjs-route-design
description: 
---

# Route Design

**Category:** nextjs · **Status:** 🟢 Active

## When to use
Khi thiết kế cấu trúc route/folder cho feature, gồm dynamic và advanced routing.

## Steps
1. Map URL theo domain: `app/users/[id]/page.tsx` cho dynamic segment.
2. Dùng `[...slug]` catch-all, `[[...slug]]` optional khi cần.
3. Route group `(marketing)` để gom theo mục đích, không đổi URL.
4. Parallel routes `@slot` cho nhiều vùng song song; intercepting `(.)` cho modal.
5. Đặt private folder `_components`, `_lib` để tránh thành route.

## Template
```
app/
  (shop)/
    products/
      [id]/page.tsx        // /products/123
      page.tsx             // /products
  @modal/
    (.)products/[id]/page.tsx  // intercept modal
  _components/             // không phải route
```

## Example
**Good:** Dynamic [id], route group gom layout, private folder cho helper.
**Avoid:** Lồng folder vô nghĩa, dùng query param thay cho dynamic segment hợp lý.

## Checklist
- [ ] Dynamic segment đặt đúng `[param]`
- [ ] Route group dùng khi gom layout
- [ ] Parallel/intercepting chỉ khi thực sự cần
- [ ] Private folder `_x` cho non-route
