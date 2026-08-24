# Biên bản họp kỹ thuật — user-login

**Thời gian:** 13/08/2026, 09:30–10:45
**Thành phần:** anh Tuấn (Tech Lead), Linh (BrSE), Mai (QC), anh Dũng (PM)
*(chị Hương không dự — những gì cần chị quyết đã gom ở mục 4)*

---

## 1. Cơ chế chống dò mật khẩu — đã chốt

Chốt **khoá tạm theo tài khoản**: sai **5 lần liên tiếp** thì khoá **15 phút**. Đăng nhập đúng
thì bộ đếm về 0.

Anh Tuấn đề xuất thêm giới hạn theo IP nhưng Mai phản đối: khách hàng doanh nghiệp thường dùng
chung một IP văn phòng, chặn theo IP sẽ khoá nhầm cả công ty. → **chỉ khoá theo tài khoản**.

Thông báo khi bị khoá phải nói rõ còn bao lâu mới thử lại được.

## 2. Phiên đăng nhập — đã chốt

- Access token sống **15 phút**, refresh token sống **30 ngày**.
- Có ô "Ghi nhớ đăng nhập". Không tick thì refresh token chỉ sống trong phiên trình duyệt.
- Đổi mật khẩu thành công thì **thu hồi toàn bộ refresh token** của tài khoản đó — đây là cách
  xử lý tình huống "tài khoản bị dùng ở hai nơi" mà chị Hương nêu.

## 3. Quên mật khẩu — đã chốt

Gửi link đặt lại qua email, link sống **60 phút**, dùng **một lần**. Dùng rồi hoặc hết hạn thì
báo lỗi và mời gửi lại.

Không tiết lộ email có tồn tại hay không — luôn hiện cùng một thông báo "nếu email tồn tại,
chúng tôi đã gửi hướng dẫn".

## 4. Điểm CHƯA CHỐT — cần chị Hương quyết

> Mai tổng hợp cuối buổi. Đã gửi mail cho chị Hương, chưa có phản hồi.

1. **Tài khoản cũ dùng mã nhân viên thì migrate thế nào?** Có ~180 tài khoản nội bộ đang dùng
   `NV0173`. Ba phương án: (a) hành chính nhập email cho từng người; (b) cho đăng nhập bằng cả
   mã cũ lẫn email trong 3 tháng chuyển tiếp; (c) bắt tất cả đặt lại qua "Quên mật khẩu". Anh
   Tuấn nghiêng về (b), Mai lo (b) làm phức tạp phần khoá tài khoản. → **chưa quyết**.

2. **Bị khoá 15 phút rồi vẫn sai tiếp thì sao?** Khoá tiếp 15 phút nữa, hay tăng dần
   (15 → 30 → 60 phút), hay khoá hẳn chờ admin mở? → **chưa quyết**.

3. **Có cần trang xem/ngắt phiên đăng nhập không?** Chị Hương than phiền về việc "một tài khoản
   dùng hai nơi", nhưng không nói rõ muốn tự xem được danh sách thiết bị hay chỉ cần đổi mật
   khẩu là đá hết ra. Phương án 2 rẻ hơn nhiều. → **chưa quyết**.

4. **Nhân viên kho dùng máy tính bảng — refresh token 30 ngày có đủ "lâu" như chị Hương muốn
   không?** Nếu họ muốn "không bao giờ phải đăng nhập lại" thì đó là yêu cầu khác hẳn về bảo
   mật, cần bàn riêng. → **chưa quyết**.

## 5. Việc tiếp theo

- Linh: viết SPEC từ biên bản này, 4 điểm mục 4 để riêng ra.
- Anh Dũng: hối chị Hương trả lời trước thứ Sáu.
