---
name: html-css-accessibility
description: 
---

# Accessibility (HTML/CSS)

**Category:** html-css · **Status:** 🟢 Active

## When to use
Khi xây UI cần đảm bảo a11y nền tảng cho mọi người dùng.

## Steps
1. Ảnh nội dung có `alt` mô tả; ảnh trang trí để `alt=""`.
2. Mọi input gắn `label` (qua `for`/`id` hoặc bọc trong); không dùng placeholder thay label.
3. Đảm bảo focus thấy rõ; không xóa `outline` nếu chưa thay bằng style khác.
4. Tương phản text đạt WCAG AA (≥4.5:1 thường, ≥3:1 cho chữ lớn).
5. Mọi thao tác dùng được bằng bàn phím; thứ tự tab hợp lý (`tabindex` không >0).
6. Dùng HTML ngữ nghĩa trước; chỉ thêm ARIA khi không thẻ gốc nào diễn đạt được.

## Template
```html
<label for="email">Email</label>
<input id="email" type="email" required />

<img src="chart.png" alt="Doanh thu tăng 20% so với quý trước" />
<img src="divider.svg" alt="" />

<button aria-expanded="false" aria-controls="menu">Menu</button>
```
```css
:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
```

## Example
**Good:** input có `label`, focus rõ, contrast AA, ARIA chỉ khi cần.
**Avoid:** `outline: none`, placeholder làm label, `div onclick` không focus được.

## Checklist
- [ ] Ảnh có `alt` phù hợp (rỗng nếu trang trí)
- [ ] Input có `label` liên kết
- [ ] Focus thấy rõ, dùng được bàn phím
- [ ] Tương phản đạt WCAG AA, ARIA chỉ khi cần
