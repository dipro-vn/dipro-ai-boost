---
name: form-error-display
description: 
---

# Error Display

**Category:** form · **Status:** 🟢 Active

## When to use
Khi hiển thị lỗi form: lỗi field, lỗi tổng (form-level), đảm bảo a11y.

## Steps
1. Hiện lỗi field ngay dưới input với message từ `errors[field].message`.
2. Gắn `aria-invalid` và `aria-describedby` trỏ tới element message để screen reader đọc.
3. Lỗi tổng (server/submit) hiển thị ở đầu form, có `role="alert"`.
4. Message rõ ràng, hành động được; tránh thuật ngữ kỹ thuật.
5. Focus vào field lỗi đầu tiên khi submit fail để dễ sửa.

## Template
```tsx
<input
  {...register('email')}
  aria-invalid={!!errors.email}
  aria-describedby={errors.email ? 'email-err' : undefined}
/>
{errors.email && <p id="email-err" role="alert">{errors.email.message}</p>}
```

## Example
**Good:** message dưới field, aria-invalid/describedby, role=alert cho lỗi tổng.
**Avoid:** Chỉ đổi viền đỏ không có text, message mơ hồ ("Lỗi"), bỏ a11y.

## Checklist
- [ ] Lỗi field hiển thị kèm message rõ
- [ ] aria-invalid + aria-describedby
- [ ] Lỗi tổng có role="alert"
- [ ] Focus field lỗi đầu tiên khi fail
