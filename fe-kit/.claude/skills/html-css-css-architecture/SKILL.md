---
name: html-css-css-architecture
description: 
---

# CSS Architecture

**Category:** html-css · **Status:** 🟢 Active

## When to use
Khi tổ chức CSS cho dự án lớn, đặt tên class, kiểm soát scope.

## Steps
1. Chọn 1 phương pháp nhất quán: BEM, utility-first, hoặc CSS Modules — không trộn lẫn tùy hứng.
2. BEM: `block__element--modifier`; utility: class nhỏ đơn nhiệm; Modules: scope tự động.
3. Đặt tên theo ý nghĩa, không theo hình thức (`.card__title` thay `.red-text`).
4. Giữ specificity thấp và phẳng; tránh selector lồng sâu (>3 cấp).
5. Tuyệt đối tránh `!important`; nếu cần, sửa nguồn gốc specificity.
6. Tách token (color/space/typography) ra biến CSS dùng chung.

## Template
```css
/* BEM */
.card { padding: var(--space-4); }
.card__title { font-weight: 600; }
.card--featured { border: 2px solid var(--color-accent); }

/* CSS Modules */
.button { background: var(--color-primary); }
/* import styles from './Button.module.css' */
```

## Example
**Good:** BEM nhất quán, specificity phẳng, token hóa, không `!important`.
**Avoid:** `.red-text`, selector `div > ul li a span`, `!important` để đè style.

## Checklist
- [ ] Một phương pháp đặt tên nhất quán toàn dự án
- [ ] Tên class theo ngữ nghĩa, không theo style
- [ ] Specificity thấp, không lồng sâu >3 cấp
- [ ] Không dùng `!important`
