# AI Agent Policies — system-to-doc

> Always-loaded qua `CLAUDE.md`. Sửa policy thì chỉ sửa file này.

---

## 1. Năm nguyên tắc cốt lõi

| Policy | Nội dung | Vi phạm dẫn tới |
|---|---|---|
| **Bằng chứng trước, kết luận sau** | Mọi `Confirmed` phải có `EV ID` phân giải được | Tài liệu sai, khách hàng mất niềm tin vào cả bộ |
| **Không đoán mò** | Thiếu thông tin → `UNKNOWN` + Open Question, không viết đại | Giả định biến thành spec |
| **Read-only mặc định** | Không thao tác ghi trên hệ thống thật khi chưa qua Gate G2 | Hỏng dữ liệu production — không hoàn tác được |
| **Stateless** | Mỗi session độc lập; context đọc từ file, trạng thái approve chỉ người xác nhận | Tự cho là đã được duyệt |
| **Gate bằng máy** | Kết luận PASS/FAIL do script, không do cảm nhận | Gate rỗng, báo xong khi chưa xong |

---

## 2. Cái tuyệt đối không được làm với hệ thống của khách

- ❌ Sửa source code của hệ thống đang phân tích — kit này **chỉ đọc**
- ❌ Chạy migration, seed, truncate, hay bất kỳ câu SQL ghi nào
- ❌ Bấm nút xoá / thanh toán / gửi mail hàng loạt khi chưa qua Gate G9
- ❌ Crawl vào vùng user đã khai cấm (`forbidden_zones`)
- ❌ Vượt trần budget (200 URL / 30 phút) mà không báo — hết budget thì **dừng và báo cáo phần đã phủ**

---

## 3. Bảo mật

- ❌ Không đọc / không in ra: `.env`, key store, `.p8`, `.p12`, credential file, token trong URL
- ❌ Không ghi mật khẩu, session token, dữ liệu cá nhân thật của người dùng vào tài liệu hay evidence
- ⚠️ Screenshot có dữ liệu cá nhân thật → che vùng nhạy cảm hoặc dùng tài khoản test
- ❌ Không đẩy evidence (chứa ảnh hệ thống khách) lên dịch vụ ngoài

---

## 4. Trung thực trong báo cáo

| Bắt buộc | Cấm |
|---|---|
| In số thật từ script: `N checks · X PASS · Y FAIL` | Gõ tay con số gate |
| `FAIL > 0` → sửa rồi chạy lại | Hạ ngưỡng gate cho dễ qua |
| Script lỗi → `❌ Blocked` | Tự chấm PASS bằng mắt |
| Phần chưa làm được → ghi rõ và nói vì sao | Im lặng thu hẹp scope |

---

## 5. Ranh giới ba mức kết luận

| Mức | Nghĩa | Điều kiện |
|---|---|---|
| `Confirmed` | Ta đã nhìn thấy nó chạy | ≥ 1 evidence phân giải được |
| `Inferred` / `To verify` | Ta suy ra, chưa xác minh | Bắt buộc kèm Open Question |
| `UNKNOWN` | Ta chưa quan sát được | Ghi rõ vì sao chưa (thiếu role / bị chặn theo G2 / không có DB) |

**`UNKNOWN` không phải thất bại.** Ô trống mới là thất bại — người đọc sẽ tưởng "không áp dụng".
