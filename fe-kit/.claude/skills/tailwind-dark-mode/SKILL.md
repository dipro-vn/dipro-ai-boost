---
name: tailwind-dark-mode
description: 
---

# Dark Mode

**Category:** tailwind · **Status:** 🟢 Active

## When to use
Khi hỗ trợ dark mode bằng Tailwind với `dark:` variant và token màu nhất quán.

## Steps
1. Chọn chiến lược trong config: `darkMode: 'class'` (toggle chủ động) hoặc `'media'` (theo OS).
2. Với `class`, thêm/bỏ class `dark` ở `<html>` để bật/tắt; lưu lựa chọn người dùng.
3. Khai báo cặp màu sáng/tối bằng `dark:` (`bg-white dark:bg-gray-900`).
4. Dùng token màu ngữ nghĩa (surface/text/border) thay vì rải hex từng chỗ.
5. Kiểm tra tương phản ở cả hai chế độ, không để chữ chìm nền.

## Template
```js
// tailwind.config.js
module.exports = { darkMode: 'class', /* ... */ };
```
```tsx
<div className="bg-white text-gray-900 border-gray-200
  dark:bg-gray-900 dark:text-gray-100 dark:border-gray-700">
  {children}
</div>
```

## Example
**Good:** chiến lược `class` nhất quán, cặp `dark:` rõ, token ngữ nghĩa, lưu lựa chọn.
**Avoid:** trộn `class` và `media` lẫn lộn, quên `dark:` cho text/border, tương phản kém ở dark.

## Checklist
- [ ] Chọn rõ `class` hay `media`
- [ ] Có cặp `dark:` cho nền/chữ/viền
- [ ] Tương phản đạt ở cả hai chế độ
