---
name: code-review-accessibility-review
description: 
---

# Accessibility Review

**Category:** code-review · **Status:** 🟢 Active

## When to use
Khi review a11y: semantic, label, focus, contrast, điều hướng bàn phím.

## Steps
1. Semantic: dùng `button`/`a`/`nav`/`main`/heading đúng; không `div` onClick cho hành động.
2. Label: input có `label`/`aria-label`; icon-button có tên; ảnh có `alt` ý nghĩa.
3. Focus: thao tác được bằng bàn phím, focus order hợp lý, focus thấy rõ, bẫy focus trong modal.
4. Contrast: chữ/nền đạt WCAG AA (4.5:1 text thường); không chỉ dùng màu để truyền thông tin.
5. ARIA: chỉ thêm khi cần, đúng role/state (`aria-expanded`, `aria-invalid`); ưu tiên HTML semantic.

## Template
```tsx
// đúng: button thật, có nhãn cho icon, trạng thái aria
<button aria-label="Đóng" aria-expanded={open} onClick={close}>
  <XIcon aria-hidden />
</button>
<label htmlFor="email">Email</label>
<input id="email" aria-invalid={!!error} />
```

## Example
**Good:** semantic HTML, label đầy đủ, keyboard + focus rõ, contrast đạt AA.
**Avoid:** div clickable, input không label, modal không bẫy focus, truyền tin chỉ bằng màu.

## Checklist
- [ ] HTML semantic, không div-onClick
- [ ] Input/icon/ảnh có label/alt
- [ ] Keyboard điều hướng được, focus rõ
- [ ] Contrast đạt AA, không chỉ dùng màu
