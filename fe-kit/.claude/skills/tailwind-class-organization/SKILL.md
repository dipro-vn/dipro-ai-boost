---
name: tailwind-class-organization
description: 
---

# Class Organization

**Category:** tailwind · **Status:** 🟢 Active

## When to use
Khi chuỗi class Tailwind dài và cần thứ tự nhất quán, dễ đọc, dễ review.

## Steps
1. Bật `prettier-plugin-tailwindcss` để tự sắp xếp class theo thứ tự chuẩn.
2. Giữ nhóm logic theo trình tự: layout → spacing → kích thước → typography → màu → state.
3. Khi class quá dài, tách dòng hoặc trừu tượng hóa bằng `cva`/component thay vì 1 chuỗi khổng lồ.
4. Tránh trùng/đè utility cùng nhóm (vd hai padding khác nhau) gây khó đoán kết quả.
5. Đặt variant (`hover:`, `md:`) cạnh utility gốc của chúng cho dễ theo dõi.

## Template
```tsx
// thứ tự: layout → box → spacing → typography → color → state
<div className="flex items-center gap-3 rounded-lg p-4 text-sm
  text-gray-800 bg-white hover:bg-gray-50 md:p-6">
  {children}
</div>
```

## Example
**Good:** plugin tự sort, nhóm logic rõ, tách/abstract khi quá dài.
**Avoid:** thứ tự ngẫu nhiên, utility trùng đè nhau, chuỗi 30+ class trên 1 dòng không tách.

## Checklist
- [ ] Bật prettier-plugin-tailwindcss
- [ ] Class theo nhóm logic nhất quán
- [ ] Tách/abstract khi chuỗi quá dài
