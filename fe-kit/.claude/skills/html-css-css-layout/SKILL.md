---
name: html-css-css-layout
description: 
---

# CSS Layout

**Category:** html-css · **Status:** 🟢 Active

## When to use
Khi dàn layout: chọn giữa Flexbox và Grid, căn chỉnh phần tử.

## Steps
1. Trục 1 chiều (hàng/cột, nội dung co giãn) → Flexbox; lưới 2 chiều cố định → Grid.
2. Dùng `gap` để tạo khoảng cách, không dùng `margin` thủ công giữa item.
3. Căn chỉnh bằng `justify-content`/`align-items`, tránh `position: absolute` để center.
4. Đặt khoảng cách/kích thước qua biến token (`--space-4`), tránh magic number.
5. Grid: định nghĩa cột bằng `repeat(auto-fit, minmax())` cho lưới tự co.
6. Tránh `width` cố định cho container; ưu tiên `max-width` + `margin-inline: auto`.

## Template
```css
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
}
```

## Example
**Good:** `gap` cho spacing, `auto-fit minmax` cho lưới responsive, token cho khoảng cách.
**Avoid:** `margin-right: 17px` rải rác, center bằng `position: absolute; top: 50%`.

## Checklist
- [ ] Chọn đúng Flex (1D) vs Grid (2D)
- [ ] Dùng `gap` thay margin giữa item
- [ ] Khoảng cách qua token, không magic number
- [ ] Container dùng `max-width` thay `width` cứng
