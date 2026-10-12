# .auth/ — tài khoản test & phiên đăng nhập

Folder này **không commit**, không bao giờ nằm trong `outputs/`.

## Cách dùng (môi trường TEST: dev / staging)

1. Chạy `/analyze-system` — AI tạo `.auth/credentials.local.env` (giá trị trống), hoặc bạn tự copy:
   ```bash
   cp .auth/credentials.example.env .auth/credentials.local.env
   chmod 600 .auth/credentials.local.env
   ```
2. Mở `credentials.local.env`, điền URL + tài khoản từng role, ghi `WEB-01.ENV=TEST`.
3. Lưu → báo AI "xong". Script `login-site.js` / `crawl-site.js` đọc file trực tiếp để đăng nhập; **AI không đọc file này**.
4. Khảo sát xong: **xoá file** và đổi mật khẩu test.

## Quy tắc

| Quy tắc | Lý do |
|---|---|
| `ENV=TEST` mới dùng được; PRODUCTION / để trống → script từ chối | Không tự động đăng nhập hệ thống thật |
| Tài khoản do KH/PM **cấp cho mục đích khảo sát** | Được phép dùng để quét tự động |
| Mật khẩu **không gõ vào chat** | Chat có thể bị lưu |
| Production / chưa chắc → AI mở trình duyệt, bạn tự đăng nhập; phiên lưu `WEB-xx.json` ở đây | AI không thấy mật khẩu |
