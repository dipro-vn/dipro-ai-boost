---
name: ui-analysis-responsive-analysis
description: 
---

# Responsive Analysis

**Category:** ui-analysis · **Status:** 🟢 Active

## When to use
Khi design chỉ có 1–2 breakpoint mà cần suy ra hành vi responsive đầy đủ.

## Steps
1. Đối chiếu các breakpoint có sẵn để tìm thứ thay đổi: cột, thứ tự, ẩn/hiện.
2. Suy ra hành vi vùng giữa các breakpoint (fluid hay nhảy bậc).
3. Xác định phần tử reflow: grid đổi số cột, nav thành hamburger, sidebar ẩn.
4. Quyết định thứ tự nội dung trên mobile (DOM order ưu tiên).
5. Đặt giả định cho breakpoint thiếu và ghi rõ để xác nhận với designer.
6. Chọn kỹ thuật: `clamp()` cho fluid, `minmax/auto-fit` cho grid co.

## Template
```md
## Responsive intent: <màn hình>
- Mobile (<768): 1 cột, nav→hamburger, sidebar ẩn
- Tablet (768–1024): 2 cột (giả định)
- Desktop (≥1024): 3 cột, sidebar hiện
- Fluid: tiêu đề dùng clamp()
- Giả định cần xác nhận: <…>
```

## Example
**Good:** Suy grid 3 cột desktop → 1 cột mobile bằng `auto-fit minmax`, ghi giả định tablet.
**Avoid:** Chỉ làm đúng 2 mốc trong design, vỡ layout ở vùng giữa.

## Checklist
- [ ] Xác định phần tử reflow giữa các breakpoint
- [ ] Quyết định DOM order cho mobile
- [ ] Đặt và ghi rõ giả định cho breakpoint thiếu
- [ ] Chọn kỹ thuật fluid/grid phù hợp
