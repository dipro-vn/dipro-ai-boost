---
name: mui-accessibility
description: 
---

# Accessibility

**Category:** mui · **Status:** 🟢 Active

## When to use
Khi cần đảm bảo component MUI tiếp cận được: label, ARIA, focus, độ tương phản màu.

## Steps
1. Mọi input có label rõ (`label` của TextField, hoặc `aria-label` cho icon button).
2. Nút chỉ-icon phải có `aria-label` mô tả hành động.
3. Đảm bảo bẫy focus & trả focus đúng với `Dialog`/`Menu` (MUI lo sẵn nếu dùng đúng).
4. Dùng màu từ theme palette để giữ tương phản đạt WCAG; không tô màu nhạt khó đọc.
5. Kiểm tra điều hướng bằng bàn phím (Tab/Enter/Esc) hoạt động.

## Template
```tsx
<IconButton aria-label="delete item" onClick={onDelete}>
  <DeleteIcon />
</IconButton>

<TextField label="Full name" id="name" required
  aria-describedby="name-help" helperText="As on your ID" />

<Dialog open={open} onClose={onClose} aria-labelledby="dlg-title">
  <DialogTitle id="dlg-title">Settings</DialogTitle>
</Dialog>
```

## Example
**Good:** icon button có `aria-label`, input có label, Dialog gắn `aria-labelledby`, màu từ theme.
**Avoid:** icon button trống aria, placeholder thay label, màu hardcode tương phản thấp.

## Checklist
- [ ] Mọi input/icon button có label hoặc `aria-label`
- [ ] Focus & điều hướng bàn phím hoạt động
- [ ] Màu theo theme đạt tương phản
