# Example Project

Mô tả: Hệ thống quản lý đơn hàng / kho hàng cho nhân viên nội bộ và khách hàng doanh nghiệp với chức năng đăng nhập qua email, quản lý tài khoản, quên mật khẩu.

## Actors
- **Nhân viên nội bộ** (180 tài khoản hiện có): Dùng máy tính bảng, nhạy cảm với việc bị bắt đăng nhập lại quá thường xuyên.
- **Người dùng doanh nghiệp** (Khách hàng): Nhóm mới, mở từ tháng 09/2026, không có mã nhân viên.
- **Hệ thống gửi email**: Gửi link đặt lại mật khẩu (nhà cung cấp chưa được chọn).

## Platform chính
- **example-web** (Web UI cho nhân viên nội bộ và khách hàng)
- **example-api** (REST API backend xử lý xác thực, phiên, mật khẩu)
- **example-mobile** (Mobile app — chưa có tính năng đăng nhập riêng)

## Business Rules toàn cục
- **Bảo mật**: Không log mật khẩu, token, PII — đặc biệt ở mức debug.
- **Định danh đăng nhập**: Email (duy nhất toàn hệ thống) thay mã nhân viên cũ.
- **Khoá tài khoản**: Theo account, KHÔNG theo IP (khách hàng dùng chung IP văn phòng).
- **Email hiện tại**: Nằm ở bảng `employee_profiles`, không unique — cần migrate để làm định danh duy nhất.
- **Mật khẩu**: Hash bcrypt (không migrate hash khi đổi cơ chế đăng nhập).

## Quy ước
- **Output language**: Tiếng Việt
- **Test data**: Email test dùng format `qc_<module>_<timestamp>@example.test` — không dùng email/SĐT thật.
- **Feature code**: `user-login` (cross-repo: example-api + example-web)
