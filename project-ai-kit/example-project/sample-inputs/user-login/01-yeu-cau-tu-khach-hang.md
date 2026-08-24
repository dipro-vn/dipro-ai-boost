# Yêu cầu từ khách hàng — làm lại màn đăng nhập

*(Ghi âm cuộc gọi với chị Hương — Product Owner, 12/08/2026, Linh tóm tắt lại)*

## Bối cảnh

Hệ thống hiện tại đăng nhập bằng **mã nhân viên + mật khẩu**, mã do bộ phận hành chính cấp
dạng `NV0173`. Dùng nội bộ thì được, nhưng tháng tới mở cho khách hàng doanh nghiệp bên ngoài
đăng nhập thì không ổn: họ không có "mã nhân viên", và bắt họ nhớ một dãy số vô nghĩa thì chắc
chắn sẽ có người quên.

Chị Hương muốn **chuyển sang đăng nhập bằng email + mật khẩu**.

## Vấn đề đang gặp với màn đăng nhập cũ

1. **Bị dò mật khẩu.** Tháng trước log ghi nhận một IP thử hơn 4.000 lần trong một đêm vào vài
   mã nhân viên. Không có cơ chế nào chặn. May là không ai bị vào.
2. **Không biết ai đang đăng nhập ở đâu.** Có lần một tài khoản bị dùng ở hai nơi cùng lúc,
   không có cách nào kiểm tra hay ngắt phiên.
3. **Quên mật khẩu phải gọi hành chính.** Bạn hành chính đặt lại tay rồi đọc mật khẩu mới qua
   điện thoại. Chị Hương nói thẳng là "cách này vừa mất thời gian vừa không an toàn".

## Mong muốn

- Đăng nhập bằng email + mật khẩu.
- **Chặn dò mật khẩu** — sai nhiều lần thì khoá lại một lúc. Chị Hương nhắc lại nhiều lần điểm
  này, coi đây là phần quan trọng nhất.
- Có "Quên mật khẩu" tự phục vụ, không phải gọi ai.
- Giữ đăng nhập lâu, đừng bắt đăng nhập lại mỗi ngày. Nhân viên kho dùng máy tính bảng cả ngày,
  cứ vài tiếng bắt đăng nhập lại là họ sẽ chửi.

## Không muốn

- **Không dùng OTP/SMS cho đăng nhập thường.** Chị Hương nói "tốn tiền tin nhắn mà nhân viên
  kho thì hay để điện thoại ngoài tủ đồ". Nếu sau này cần 2FA thì bàn riêng, không phải đợt này.
- Không bắt đổi mật khẩu định kỳ 3 tháng như hệ thống cũ — "chỉ tổ khiến mọi người ghi mật khẩu
  ra giấy dán lên màn hình".

## Thời gian

Cần lên production **trước 15/09** để kịp mở cho nhóm khách hàng doanh nghiệp đầu tiên.
