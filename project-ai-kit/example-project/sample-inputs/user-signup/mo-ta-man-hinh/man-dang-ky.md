# Mô tả màn đăng ký

*(Ghi lại từ bản vẽ tay trên bảng buổi kickoff — chưa có thiết kế Figma)*

## Bố cục

Một form ở giữa màn hình, phía trên có logo, phía dưới form có dòng "Đã có tài khoản? Đăng nhập".

## Các trường

| Trường | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| Email | text | Có | Kiểm định dạng email ngay khi rời khỏi ô |
| Mật khẩu | password | Có | Có nút hiện/ẩn mật khẩu; bên dưới là thanh độ mạnh |
| Nhập lại mật khẩu | password | Có | Phải khớp với ô trên |
| Đồng ý điều khoản | checkbox | Có | Không tick thì nút Đăng ký mờ |

Nút **Đăng ký** nằm cuối form, chiếm hết chiều ngang form.

## Trạng thái lỗi cần hiển thị

- Email sai định dạng → báo ngay dưới ô email, không đợi bấm nút.
- Mật khẩu không đạt quy tắc (dưới 8 ký tự, thiếu chữ hoặc thiếu số) → báo dưới ô mật khẩu.
- Hai ô mật khẩu không khớp → báo dưới ô nhập lại.
- Lỗi từ server (email đã tồn tại, mạng lỗi...) → báo ở đầu form, dạng banner đỏ.

## Trong lúc gửi

Nút Đăng ký chuyển sang trạng thái loading và bị vô hiệu hoá, tránh user bấm nhiều lần tạo trùng
tài khoản.

## Sau khi thành công

Chuyển thẳng sang màn nhập mã xác thực, mang theo email vừa đăng ký để hiển thị (user cần thấy
mình đã nhập đúng email nào).
