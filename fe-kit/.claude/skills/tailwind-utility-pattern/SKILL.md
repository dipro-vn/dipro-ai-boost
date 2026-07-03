---
name: tailwind-utility-pattern
description: 
---

# Utility Pattern

**Category:** tailwind · **Status:** 🟢 Active

## When to use
Khi style bằng Tailwind theo tư duy utility-first, compose class ngay trên markup.

## Steps
1. Style trực tiếp bằng utility class trên element; tránh viết file CSS rời cho từng case.
2. Compose nhiều utility nhỏ (`flex items-center gap-2`) thay vì một class custom mơ hồ.
3. Dùng token có sẵn (`p-4`, `text-sm`, `rounded-md`) thay vì giá trị tùy ý `[12px]`.
4. Chỉ tách abstraction (component/`@apply`) khi pattern lặp nhiều lần.
5. Giữ logic trạng thái qua variant (`hover:`, `disabled:`) thay vì JS toggle class thủ công.

## Template
```tsx
<button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2
  text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
  Save
</button>
```

## Example
**Good:** compose utility từ token, dùng variant cho state, không CSS rời.
**Avoid:** giá trị tùy ý `[13px]` khắp nơi, viết CSS riêng cho việc utility làm được, class custom rỗng nghĩa.

## Checklist
- [ ] Utility-first, không CSS rời thừa
- [ ] Dùng token thay vì giá trị tùy ý
- [ ] State qua variant thay vì toggle JS
