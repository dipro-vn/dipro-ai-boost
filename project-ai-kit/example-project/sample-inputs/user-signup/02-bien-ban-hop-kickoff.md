# Biên bản họp kickoff — user-signup

**Thời gian:** 15/08/2026, 14:00–15:10
**Thành phần:** chị Hương (PO khách hàng), anh Dũng (PM), Linh (BrSE), anh Tuấn (Tech Lead), Mai (QC)

---

## 1. Thống nhất phạm vi đợt này

Chốt làm **đăng ký bằng email + mật khẩu, có xác thực email**. Đăng nhập bằng Google **tách ra
đợt sau** — anh Tuấn nói phải đăng ký OAuth client với Google, xin domain verification, không kịp
trước 25/09.

Chị Hương đồng ý.

## 2. Luồng xác thực email — đã chốt

Thảo luận 2 phương án:

- **PA1 — link xác thực trong email:** user bấm vào link, hệ thống xác thực rồi chuyển về web.
- **PA2 — mã OTP 6 số:** user nhập mã vào màn hình đang mở.

Chọn **PA2 (mã OTP 6 số)**. Lý do: trên mobile, bấm link trong app email sẽ mở trình duyệt ngoài,
không quay lại được app — trải nghiệm gãy. Nhập mã thì cả web và mobile đều dùng chung một luồng.

Chi tiết đã chốt:

- Mã gồm **6 chữ số**, hết hạn sau **10 phút**.
- Cho phép **gửi lại mã**, nhưng phải đợi **60 giây** giữa 2 lần gửi.
- Nhập sai quá **5 lần** thì khoá mã đó, bắt gửi lại mã mới.

## 3. Quy tắc mật khẩu — đã chốt

Tối thiểu **8 ký tự**, phải có **ít nhất 1 chữ cái và 1 chữ số**. Không bắt buộc ký tự đặc biệt
(anh Tuấn: bắt ký tự đặc biệt làm user hay quên mật khẩu, tăng tải cho support mà không tăng bảo
mật đáng kể).

Có hiển thị thanh độ mạnh mật khẩu như chị Hương yêu cầu — nhưng chỉ để tham khảo, không chặn.

## 4. Điểm CHƯA CHỐT — cần làm rõ trước khi thiết kế

> Mai (QC) nêu ra, cuối buổi vẫn chưa quyết được vì chị Hương cần hỏi lại bên vận hành:

1. **Email đã đăng ký rồi mà đăng ký lại thì sao?** Báo "email đã tồn tại" thì lộ thông tin ai đã
   là khách hàng của mình (bên vận hành có lo ngại về việc này). Còn báo chung chung thì user
   không hiểu vì sao không vào được. → chưa quyết.

2. **Chưa xác thực email thì có đăng nhập được không?** Anh Dũng đề xuất cho vào nhưng hạn chế
   chức năng; chị Hương nghiêng về chặn hẳn cho đơn giản. → chưa quyết.

3. **Tài khoản đăng ký mà không bao giờ xác thực thì xử lý ra sao?** Để mãi trong database hay
   dọn sau N ngày? Nếu dọn thì bao lâu? → chưa quyết, chị Hương sẽ hỏi bên vận hành.

4. **Có cần đăng ký bằng số điện thoại không?** Chị Hương nói "một số khách hàng lớn tuổi không
   dùng email thành thạo". Chưa quyết — nếu có thì phát sinh chi phí SMS gateway.

## 5. Việc tiếp theo

- Linh: viết SPEC dựa trên biên bản này, phần chưa chốt để riêng ra hỏi lại.
- Chị Hương: hỏi bên vận hành 4 điểm ở mục 4, phản hồi trong tuần.
- Anh Tuấn: xác nhận lại nhà cung cấp gửi email.
