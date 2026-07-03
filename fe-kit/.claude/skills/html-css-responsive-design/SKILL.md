---
name: html-css-responsive-design
description: 
---

# Responsive Design

**Category:** html-css · **Status:** 🟢 Active

## When to use
Khi cần giao diện thích ứng nhiều kích thước màn hình.

## Steps
1. Viết mobile-first: style mặc định cho mobile, `min-width` media query để mở rộng.
2. Chọn breakpoint theo nội dung (chỗ layout vỡ), không theo tên thiết bị.
3. Dùng `clamp(min, fluid, max)` cho font/spacing để co giãn mượt, giảm media query.
4. Layout fluid bằng `%`, `fr`, `minmax`; tránh chiều rộng pixel cố định.
5. Đặt ảnh `max-width: 100%; height: auto`; dùng `srcset` cho ảnh nặng.
6. Test ở viewport hẹp nhất và rộng nhất, kiểm tra nội dung dài/ngắn.

## Template
```css
:root { --container: min(100% - 2rem, 1200px); }
.title { font-size: clamp(1.5rem, 1rem + 2vw, 2.5rem); }
.layout { width: var(--container); margin-inline: auto; }

@media (min-width: 48rem) {
  .layout { display: grid; grid-template-columns: 1fr 2fr; }
}
```

## Example
**Good:** mobile-first, `clamp()` cho font, breakpoint đặt khi layout vỡ.
**Avoid:** desktop-first `max-width`, `width: 980px` cứng, breakpoint cứng theo iPhone.

## Checklist
- [ ] Style mặc định là mobile, mở rộng bằng `min-width`
- [ ] Dùng `clamp()`/`min()`/`max()` cho giá trị fluid
- [ ] Không width pixel cố định cho container
- [ ] Ảnh `max-width: 100%`, có `srcset` khi cần
