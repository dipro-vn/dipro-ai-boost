# Ràng buộc kỹ thuật — ghi chú của anh Tuấn (Tech Lead)

## Hiện trạng cần biết trước khi thiết kế

Bảng `users` trong `example-api` đã có sẵn và đang được dùng bởi các module khác — **không được
đổi tên hay xoá cột đang có**. Cột hiện tại liên quan tới đăng nhập:

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `employee_code` | varchar(10) | Mã nhân viên, đang là định danh đăng nhập |
| `password_hash` | varchar | Đang hash bằng bcrypt cost 10 |
| `is_active` | boolean | Tài khoản bị vô hiệu thì không cho đăng nhập |

Email hiện **chưa có cột riêng** — đang nằm trong bảng `employee_profiles`, và **không unique**.
Đây là điểm phải xử lý: đăng nhập bằng email thì email bắt buộc phải unique.

## Ràng buộc bắt buộc

- Database: PostgreSQL + TypeORM (theo `stack-constraints.md`, không thương lượng).
- Giữ **bcrypt** cho mật khẩu — không đổi thuật toán, vì đổi thì 180 tài khoản hiện tại phải
  đặt lại mật khẩu hết.
- Không log mật khẩu, không log token, kể cả ở mức debug.
- Không tiết lộ qua thông báo lỗi rằng email có tồn tại hay không (tránh dò danh sách khách hàng).
- Bộ đếm sai mật khẩu phải chịu được nhiều instance API chạy song song — đếm trong bộ nhớ của
  một process là **không đủ**.

## Repo liên quan

| Repo | Vai trò |
|---|---|
| `example-api` | Endpoint đăng nhập, refresh token, quên/đặt lại mật khẩu, cơ chế khoá |
| `example-web` | Màn đăng nhập, màn quên mật khẩu, màn đặt lại mật khẩu |

> `example-mobile` **không** thuộc phạm vi đợt này — app mobile hiện chưa có màn đăng nhập riêng.

## Chưa chốt phía kỹ thuật

- **Lưu bộ đếm sai mật khẩu ở đâu?** Redis (nhanh, tự hết hạn, nhưng dự án chưa có Redis) hay
  cột trong Postgres (không thêm hạ tầng, nhưng ghi nhiều). Tôi nghiêng về Postgres cho đợt này
  để khỏi thêm hạ tầng mới, cần xác nhận với anh Dũng về hiệu năng.
- Nhà cung cấp gửi email cho luồng quên mật khẩu chưa chọn (giống vướng mắc của feature khác).

## Ước lượng sơ bộ

Backend ~4 ngày (gồm migration email unique), web ~2,5 ngày. Chưa tính test và tích hợp.
