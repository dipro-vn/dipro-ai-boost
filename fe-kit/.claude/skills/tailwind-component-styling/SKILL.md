---
name: tailwind-component-styling
description: 
---

# Component Styling

**Category:** tailwind · **Status:** 🟢 Active

## When to use
Khi cần trừu tượng hóa class Tailwind lặp lại thành variant tái dùng (`@apply`/`cva`/`clsx`).

## Steps
1. Khi pattern lặp nhiều, gom bằng component + `cva` để quản lý variant, thay vì copy class.
2. Dùng `clsx`/`cn` để ghép class điều kiện sạch sẽ, tránh chuỗi template rối.
3. Dùng `@apply` trong CSS cho primitive lặp lại (vd `.btn`), không lạm dụng cho mọi thứ.
4. Định nghĩa `variants`/`defaultVariants` rõ (size, intent) thay vì truyền class rời.
5. Giữ một nguồn chân lý cho mỗi component để dễ sửa đồng loạt.

## Template
```tsx
const button = cva('inline-flex items-center rounded-md font-medium', {
  variants: {
    intent: { primary: 'bg-blue-600 text-white hover:bg-blue-700',
              ghost: 'bg-transparent hover:bg-gray-100' },
    size: { sm: 'px-3 py-1 text-sm', md: 'px-4 py-2 text-base' },
  },
  defaultVariants: { intent: 'primary', size: 'md' },
});

<button className={cn(button({ intent, size }), className)}>{children}</button>
```

## Example
**Good:** variant qua `cva`, ghép điều kiện bằng `cn/clsx`, một nguồn chân lý.
**Avoid:** copy chuỗi class khắp nơi, nối string `${}` rối, `@apply` cho mọi class.

## Checklist
- [ ] Pattern lặp gom thành variant (`cva`/component)
- [ ] Ghép class điều kiện bằng `clsx/cn`
- [ ] Một nguồn chân lý cho mỗi component
