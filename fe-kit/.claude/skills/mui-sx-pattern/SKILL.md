---
name: mui-sx-pattern
description: CHỈ dùng khi dự án dùng Material UI. Style component bằng prop sx — dùng token theme thay vì magic value, responsive value dạng object, khi nào nên tách sang styled. Dùng khi style bất kỳ component MUI nào.
---

# Sx Pattern

**Category:** mui · **Status:** 🟢 Active

## When to use
Khi style component MUI bằng prop `sx`.

## Steps
1. Dùng `sx` cho style cục bộ; tránh inline style và styled trùng lặp.
2. Tham chiếu theme token (`p: 2`, `color: 'text.secondary'`) thay vì giá trị cứng.
3. Responsive bằng object breakpoint (`{ xs: 1, md: 2 }`).
4. Tách sx phức tạp ra biến/const để tái dùng.

## Template
```tsx
<Box sx={{ p: 2, display: 'flex', gap: 1, color: 'text.secondary',
  flexDirection: { xs: 'column', md: 'row' } }}>
  {children}
</Box>
```

## Example
**Good:** dùng token theme, responsive object, tách sx tái dùng.
**Avoid:** hardcode px/màu, lặp sx khắp nơi, trộn sx + style.

## Checklist
- [ ] Dùng theme token thay vì giá trị cứng
- [ ] Responsive bằng breakpoint object
- [ ] Không trộn nhiều cơ chế style
