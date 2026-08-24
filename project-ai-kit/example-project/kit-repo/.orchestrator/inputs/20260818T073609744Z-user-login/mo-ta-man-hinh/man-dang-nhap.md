# Mô tả màn đăng nhập

*(Chụp lại từ bản vẽ trên bảng buổi họp — chưa có thiết kế Figma)*

## Bố cục

Logo ở trên, form ở giữa, không có ảnh nền hay banner gì (chị Hương: "đơn giản thôi, nhân viên
kho mở bằng máy tính bảng đời cũ, đừng nặng").

## Các trường

| Trường | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| Email | text | Có | Tự động viết thường, cắt khoảng trắng thừa hai đầu |
| Mật khẩu | password | Có | Có nút hiện/ẩn |
| Ghi nhớ đăng nhập | checkbox | Không | Mặc định **không** tick |

Nút **Đăng nhập** chiếm hết chiều ngang form. Dưới cùng có link "Quên mật khẩu?".

## Trạng thái lỗi cần hiển thị

| Tình huống | Hiển thị |
|---|---|
| Email sai định dạng | Báo ngay dưới ô email khi rời khỏi ô |
| Sai email hoặc sai mật khẩu | Cùng một thông báo chung ở đầu form — **không** nói rõ sai cái nào |
| Tài khoản đang bị khoá | Nêu rõ còn bao nhiêu phút mới thử lại được |
| Tài khoản bị vô hiệu hoá | "Tài khoản đã bị vô hiệu hoá, liên hệ quản trị viên" |
| Mất mạng / server lỗi | Banner đỏ đầu form, giữ nguyên email đã gõ |

## Trong lúc gửi

Nút chuyển sang loading và bị vô hiệu hoá. Không cho bấm Enter nhiều lần tạo nhiều request.

## Sau khi thành công

Vào thẳng trang chủ. Nếu trước đó người dùng bị đá ra từ một trang cụ thể thì quay lại đúng
trang đó.
