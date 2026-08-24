# Ràng buộc kỹ thuật — ghi chú của anh Tuấn (Tech Lead)

*(Gửi cho Linh sau buổi kickoff, để đưa vào SPEC phần preconditions)*

## Tái dùng từ feature `user-login` đã làm

Feature `user-login` đã lên production tháng 6, đăng ký phải dùng lại đúng những thứ đó, **không
được dựng song song một hệ auth thứ hai**:

- Bảng `users` đã có sẵn (`example-api`). Đăng ký là **thêm bản ghi vào bảng này**, không tạo bảng
  người dùng mới.
- JWT access token + refresh token đã có. Sau khi đăng ký + xác thực xong thì cấp token bằng đúng
  cơ chế đang dùng, không tự phát minh.
- Mật khẩu đang hash bằng bcrypt. Giữ nguyên, không đổi thuật toán.

## Repo liên quan

| Repo | Vai trò trong feature này |
|---|---|
| `example-api` | Endpoint đăng ký, sinh + kiểm mã OTP, gửi email |
| `example-web` | Màn đăng ký + màn nhập mã xác thực |
| `example-mobile` | Màn đăng ký + màn nhập mã xác thực (bản mobile) |

> Lưu ý: repo `example-mobile` hiện **chưa được clone về máy** — cần xử lý trước khi giao task mobile.

## Ràng buộc bắt buộc

- Database: PostgreSQL + TypeORM (theo `stack-constraints.md` của kit, không thương lượng).
- Không lưu mật khẩu dạng plaintext ở bất kỳ đâu, kể cả log.
- Không log mã OTP ra console/log file.
- Endpoint đăng ký và endpoint gửi lại mã **phải có rate limit** — nếu không sẽ bị lạm dụng để
  spam email người khác. Đề xuất: giới hạn theo IP và theo địa chỉ email.
- Mã OTP lưu dạng hash, không lưu thẳng số vào DB.

## Chưa chốt phía kỹ thuật

- **Nhà cung cấp gửi email chưa chọn.** Đang cân nhắc AWS SES (đã dùng cho email hệ thống khác)
  hoặc SendGrid. Ảnh hưởng tới thời gian gửi mã — chị Hương yêu cầu "gần như tức thì" nhưng chưa
  đo được. Tôi sẽ xác nhận trong tuần này.
- Chưa rõ có cần hỗ trợ đa ngôn ngữ cho nội dung email không (hiện hệ thống chỉ có tiếng Việt).

## Ước lượng sơ bộ

Backend ~3 ngày, web ~2 ngày, mobile ~2 ngày, chưa tính test và tích hợp. Kịp deadline 25/09 nếu
chốt được 4 điểm còn treo trong biên bản họp trước cuối tuần này.
