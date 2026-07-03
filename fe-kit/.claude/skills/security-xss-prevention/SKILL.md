---
name: security-xss-prevention
description: 
---

# Xss Prevention

**Category:** security · **Status:** 🟢 Active

## When to use
Khi render nội dung động hoặc HTML do người dùng/đối tác cung cấp.

## Steps
1. Mặc định escape: React đã escape text; KHÔNG dùng `dangerouslySetInnerHTML` trừ khi bắt buộc.
2. Nếu phải render HTML, sanitize bằng DOMPurify trước.
3. Không nhồi dữ liệu vào `href`/`src` chưa kiểm tra (chặn `javascript:`).
4. Validate & encode ở cả input lẫn output.

## Template
```tsx
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />
```

## Example
**Good:** sanitize trước khi set HTML, chặn scheme nguy hiểm.
**Avoid:** set innerHTML thẳng từ API, tin tưởng input client.

## Checklist
- [ ] Không innerHTML thô
- [ ] Sanitize HTML động
- [ ] Kiểm tra href/src scheme
