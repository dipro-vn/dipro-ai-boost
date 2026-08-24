# Mô tả màn quên mật khẩu / đặt lại mật khẩu

*(Chụp lại từ bản vẽ trên bảng buổi họp — chưa có thiết kế Figma)*

## Màn 1 — Nhập email

Một ô email + nút "Gửi hướng dẫn". Có link quay lại đăng nhập.

Bấm gửi xong **luôn** hiện cùng một thông báo, bất kể email có tồn tại hay không:

> Nếu email này có trong hệ thống, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu. Kiểm tra cả hộp
> thư rác.

Có chống spam: bấm gửi lại phải đợi 60 giây.

## Màn 2 — Đặt mật khẩu mới

Mở từ link trong email. Hai ô: "Mật khẩu mới" và "Nhập lại mật khẩu mới", cùng thanh độ mạnh.

| Tình huống | Hiển thị |
|---|---|
| Link hết hạn (quá 60 phút) | "Link đã hết hạn" + nút gửi lại |
| Link đã dùng rồi | Cùng thông báo như hết hạn — không phân biệt |
| Hai ô mật khẩu không khớp | Báo dưới ô thứ hai |
| Mật khẩu không đạt quy tắc | Báo dưới ô thứ nhất |

## Sau khi đặt lại thành công

Hiện thông báo ngắn rồi đưa về màn đăng nhập, **bắt đăng nhập lại bằng mật khẩu mới** — không tự
động đăng nhập, vì mọi phiên cũ đã bị thu hồi ở bước này.

## Câu hỏi để ngỏ

Quy tắc mật khẩu mới là gì? Buổi họp chốt cơ chế khoá và phiên nhưng **chưa ai nói độ dài tối
thiểu hay yêu cầu ký tự** cho mật khẩu. Hệ thống cũ đang là "tối thiểu 6 ký tự, không yêu cầu
gì thêm" — giữ nguyên hay siết lại?
