---
name: html-css-animation-transition
description: 
---

# Animation & Transition

**Category:** html-css · **Status:** 🟢 Active

## When to use
Khi thêm chuyển động, hiệu ứng hover/enter mà vẫn giữ hiệu năng.

## Steps
1. Chỉ animate `transform` và `opacity` (chạy trên GPU, không reflow).
2. Tránh animate `width/height/top/left/margin` — gây layout thrash.
3. Đặt `transition` rõ thuộc tính, không `transition: all`.
4. Thời lượng ngắn (150–300ms) cho UI; dùng `ease-out` cho enter, `ease-in` cho exit.
5. Tôn trọng `prefers-reduced-motion`: tắt/giảm animation khi người dùng yêu cầu.
6. Dùng `will-change` tiết kiệm, chỉ ngay trước animation phức tạp.

## Template
```css
.button {
  transition: transform 200ms ease-out, opacity 200ms ease-out;
}
.button:hover { transform: translateY(-2px); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Example
**Good:** chỉ `transform/opacity`, transition liệt kê rõ, có reduced-motion.
**Avoid:** animate `left/width`, `transition: all`, bỏ qua reduced-motion.

## Checklist
- [ ] Chỉ animate `transform`/`opacity`
- [ ] Không dùng `transition: all`
- [ ] Thời lượng 150–300ms, easing hợp lý
- [ ] Có xử lý `prefers-reduced-motion`
