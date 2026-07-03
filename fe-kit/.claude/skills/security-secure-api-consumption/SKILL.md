---
name: security-secure-api-consumption
description: 
---

# Secure Api Consumption

**Category:** security · **Status:** 🟢 Active

## When to use
Khi gọi API từ FE: cấu hình transport, lỗi, secret, CORS và giới hạn tần suất.

## Steps
1. Luôn HTTPS; không gửi dữ liệu nhạy cảm qua query string.
2. KHÔNG để secret/API key bí mật trong bundle FE — gọi qua BFF/route server.
3. Xử lý lỗi rõ ràng: phân biệt 4xx/5xx, không lộ chi tiết nội bộ ra UI.
4. Tôn trọng rate limit: backoff/retry có giới hạn, debounce request người dùng.
5. Cấu hình CORS đúng (allowlist origin); gửi credentials chỉ khi cần.
6. Validate response (xem input-validation) trước khi dùng.

## Template
```ts
const res = await fetch('/api/bff/orders', { credentials: 'include' });
if (!res.ok) throw new ApiError(res.status); // không lộ message nội bộ
const data = OrdersSchema.parse(await res.json());
```

## Example
**Good:** key ở server/BFF, retry có backoff, CORS allowlist.
**Avoid:** nhúng secret vào `NEXT_PUBLIC_*`, retry vô hạn, CORS `*` kèm credentials.

## Checklist
- [ ] HTTPS, không secret trong bundle FE
- [ ] Xử lý lỗi không lộ nội bộ
- [ ] Retry/backoff tôn trọng rate limit
- [ ] CORS allowlist, validate response
