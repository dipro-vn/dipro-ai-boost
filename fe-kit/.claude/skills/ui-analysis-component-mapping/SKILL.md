---
name: ui-analysis-component-mapping
description: 
---

# Component Mapping

**Category:** ui-analysis · **Status:** 🟢 Active

## When to use
Khi chuyển một design thành cây component code.

## Steps
1. Tách design thành cây component theo phân cấp visual và trách nhiệm.
2. Ưu tiên tái sử dụng component sẵn có; chỉ tạo mới khi không có sẵn.
3. Map variant trong design (size/state/intent) thành props/variant của code.
4. Tách phần lặp lại thành component con nhận data qua props.
5. Phân biệt presentational (UI thuần) và container (logic/data).
6. Đặt tên component theo vai trò nghiệp vụ, không theo hình thức.

## Template
```md
## Mapping: <màn hình>
| Design block | Component code | Reuse? | Props/variant |
|--------------|----------------|--------|---------------|
| Nút primary | `Button` | reuse | variant="primary", size |
| Thẻ sản phẩm | `ProductCard` | new | product, onSelect |
```
```tsx
<ProductList>
  {items.map((p) => <ProductCard key={p.id} product={p} />)}
</ProductList>
```

## Example
**Good:** Dùng `Button` có sẵn với variant, tách `ProductCard` nhận props, đặt tên theo nghiệp vụ.
**Avoid:** Tạo `BlueBox` mới trùng `Card` sẵn có, nhồi mọi thứ vào 1 component.

## Checklist
- [ ] Ưu tiên reuse component sẵn có
- [ ] Map variant design → props/variant code
- [ ] Tách container vs presentational
- [ ] Tên component theo vai trò nghiệp vụ
