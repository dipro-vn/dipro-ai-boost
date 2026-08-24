# Mô tả màn nhập mã xác thực

*(Ghi lại từ bản vẽ tay trên bảng buổi kickoff — chưa có thiết kế Figma)*

## Bố cục

Giữa màn hình: dòng chữ "Chúng tôi đã gửi mã tới **&lt;email&gt;**", bên dưới là 6 ô nhập số rời nhau,
mỗi ô một chữ số. Con trỏ tự nhảy sang ô kế tiếp khi gõ. Dán (paste) cả 6 số vào ô đầu thì tự
điền hết các ô còn lại.

## Hành vi

- Nhập đủ 6 số thì **tự động gửi đi**, không cần bấm nút xác nhận.
- Bên dưới có dòng "Không nhận được mã? **Gửi lại**".
- Sau khi bấm Gửi lại, link đổi thành đồng hồ đếm ngược "Gửi lại sau 60 giây", hết giờ mới bấm
  lại được.
- Có link nhỏ "Đổi email khác" quay lại màn đăng ký (trường hợp gõ nhầm email).

## Trạng thái lỗi cần hiển thị

| Tình huống | Hiển thị |
|---|---|
| Mã sai | Viền 6 ô chuyển đỏ, báo "Mã không đúng, còn N lần thử" |
| Mã hết hạn (quá 10 phút) | "Mã đã hết hạn, bấm Gửi lại để nhận mã mới" |
| Sai quá 5 lần | Khoá ô nhập, bắt buộc bấm Gửi lại |
| Mất mạng | Banner đỏ đầu màn, giữ nguyên số đã gõ |

## Sau khi thành công

Hiện thông báo ngắn "Xác thực thành công", rồi vào thẳng trong hệ thống — **không bắt user đăng
nhập lại**, vì họ vừa nhập mật khẩu ở bước trước xong.

## Câu hỏi để ngỏ

Nếu user đóng trình duyệt ở màn này rồi mở lại sau, họ vào lại bằng đường nào? Đăng nhập bằng
email/mật khẩu vừa tạo rồi hệ thống tự đưa về màn nhập mã? Chỗ này liên quan tới điểm chưa chốt
số 2 trong biên bản họp (chưa xác thực thì có đăng nhập được không).
