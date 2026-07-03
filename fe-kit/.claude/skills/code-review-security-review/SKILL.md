---
name: code-review-security-review
description: 
---

# Security Review

**Category:** code-review · **Status:** 🟢 Active

## When to use
Khi review bảo mật: validate input, XSS, token, phân quyền.

## Steps
1. Input: validate + escape mọi dữ liệu từ user/URL/API; không tin client.
2. XSS: tránh `dangerouslySetInnerHTML`; nếu bắt buộc thì sanitize (DOMPurify).
3. Token/secret: không hardcode, không log, không để trong bundle FE; dùng httpOnly cookie cho session.
4. Phân quyền: kiểm tra quyền ở server, không chỉ ẩn nút ở UI; chặn IDOR (truy cập id người khác).
5. Phụ thuộc: tránh lib có lỗ hổng đã biết; cẩn thận URL/redirect mở.

## Template
```tsx
// XSS: sanitize trước khi render HTML thô
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />

// AuthZ: kiểm quyền ở server, không tin FE
if (!can(user, 'post:edit', post)) throw new ForbiddenError();
```

## Example
**Good:** validate server-side, sanitize HTML, secret ngoài bundle, check quyền + chống IDOR.
**Avoid:** tin input client, innerHTML thô, token trong localStorage/log, chỉ ẩn nút mà không chặn API.

## Checklist
- [ ] Input validate + escape (không tin client)
- [ ] Không XSS / đã sanitize HTML thô
- [ ] Secret/token không lộ ra FE/log
- [ ] Phân quyền ở server + chống IDOR
