---
name: mui-responsive-layout
description: 
---

# Responsive Layout

**Category:** mui · **Status:** 🟢 Active

## When to use
Khi dựng layout responsive bằng MUI (Grid/Stack) với spacing và breakpoint nhất quán.

## Steps
1. Dùng `Stack` cho layout 1 chiều (gap, hướng), `Grid` cho lưới đa cột.
2. Đặt số cột theo breakpoint (`xs`/`sm`/`md`/`lg`) thay vì width cứng.
3. Dùng `spacing`/`gap` theo đơn vị theme (8px), không pad/margin tùy tiện.
4. Đổi hướng/cột theo breakpoint object (`direction={{ xs: 'column', md: 'row' }}`).
5. Tránh nest layout quá sâu; ưu tiên Stack lồng nhẹ.

## Template
```tsx
<Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
  <Box flex={1}>{left}</Box>
  <Box flex={1}>{right}</Box>
</Stack>

<Grid container spacing={2}>
  <Grid item xs={12} md={6}>{a}</Grid>
  <Grid item xs={12} md={6}>{b}</Grid>
</Grid>
```

## Example
**Good:** cột theo breakpoint, spacing đơn vị theme, đổi hướng responsive bằng object.
**Avoid:** width px cứng, margin tùy tiện thay vì spacing, layout chỉ hợp 1 màn hình.

## Checklist
- [ ] Dùng Grid/Stack thay vì float/width cứng
- [ ] Cột & hướng theo breakpoint
- [ ] Spacing/gap theo đơn vị theme
