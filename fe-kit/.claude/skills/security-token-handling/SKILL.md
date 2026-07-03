---
name: security-token-handling
description: 
---

# Token Handling

**Category:** security · **Status:** 🟢 Active

## When to use
Khi quản lý access/refresh token: nơi lưu, làm mới, và xử lý hết hạn an toàn.

## Steps
1. Ưu tiên cookie `httpOnly` + `Secure` + `SameSite` cho token (chống XSS đọc trộm).
2. Nếu buộc dùng storage, chỉ giữ access token ngắn hạn trong memory; tránh localStorage cho token nhạy cảm.
3. Refresh token nên ở httpOnly cookie; access token hết hạn thì gọi refresh tự động.
4. Chặn race condition khi refresh: gom request đang chờ vào một lần refresh.
5. Khi refresh thất bại/hết hạn: xoá phiên, đăng xuất, redirect login.

## Template
```ts
let refreshing: Promise<string> | null = null;
async function getToken() {
  if (isExpired(token)) {
    refreshing ??= refresh().finally(() => (refreshing = null));
    token = await refreshing;
  }
  return token;
}
```

## Example
**Good:** refresh trong httpOnly cookie, access token in-memory, gom refresh.
**Avoid:** lưu refresh token ở localStorage, refresh song song nhiều lần.

## Checklist
- [ ] Token ưu tiên httpOnly cookie
- [ ] Không localStorage cho token nhạy cảm
- [ ] Refresh tự động + chống race
- [ ] Hết hạn thì xoá phiên, redirect
