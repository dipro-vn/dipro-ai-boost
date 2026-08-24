# Requirements Analysis: Auth (User Login)

## Summary

**Tính năng:** Chuyển cơ chế đăng nhập từ mã nhân viên (`NVxxxx`) sang **email + mật khẩu**, bổ sung chống dò mật khẩu (khoá tài khoản), quản lý phiên (access/refresh token), và tự phục vụ quên mật khẩu qua email.

**Mục đích nghiệp vụ:**
1. Chống dò mật khẩu (ưu tiên cao nhất theo PO) — khoá tài khoản sau 5 lần sai liên tiếp.
2. Kiểm soát phiên đăng nhập — đổi mật khẩu = thu hồi toàn bộ refresh token.
3. Tự phục vụ quên mật khẩu qua email, không cần hành chính can thiệp thủ công.

**Actors:**
- Nhân viên nội bộ (~180 tài khoản `NVxxxx` hiện có, dùng cả máy tính bảng đời cũ)
- Người dùng doanh nghiệp (khách hàng mới, mở từ 09/2026, không có mã nhân viên)
- Hệ thống gửi email (nhà cung cấp **chưa chọn** — OQ-05)

**Scope:** Cross-repo — `example-api` (backend) + `example-web` (frontend). **KHÔNG** thuộc scope: `example-mobile`.

**Screens (3 màn — theo `## Screens` trong SPEC.md, module prefix `WB_AUTH`):**
| Screen Code | Tên | Mô tả ngắn |
|---|---|---|
| `WB_AUTH_001` | Đăng nhập | Form Email + Password + checkbox "Ghi nhớ đăng nhập" |
| `WB_AUTH_002` | Quên mật khẩu — nhập email | Form 1 ô Email + nút "Gửi hướng dẫn" (cooldown 60s) |
| `WB_AUTH_003` | Đặt mật khẩu mới | 2 ô mật khẩu + thanh độ mạnh, mở từ link email |

> **Chưa có Figma link cho cả 3 màn** (`SPEC.md ## Screens` cột Figma Link = "chưa có"; `DESIGN.md (example-web)` cũng ghi "Chờ Design Figma"). TC ở bước `/gen-tcs` sẽ dựa hoàn toàn trên AC + mô tả text — **TC base only, refine sau khi Designer xong**.

**Happy Path:**
- HP-A: Đăng nhập thành công → cấp access token (15p) + refresh token (30 ngày nếu tick "Ghi nhớ", session-only nếu không) → vào trang chủ / trang trước đó.
- HP-B: Quên mật khẩu → nhận email link (60p, dùng 1 lần) → đặt mật khẩu mới → thu hồi hết refresh token → quay về màn login, phải đăng nhập lại bằng mật khẩu mới.

**Dependencies:**
- `DESIGN.md` (example-api) — đã lock được cấu trúc 5 endpoint (login/refresh/logout/forgot-password/reset-password) + error code enum, nhưng **chưa Contract Lock chính thức** (còn phụ thuộc OQ-01/04/05/06).
- `DESIGN.md` (example-web) — đã có state shape Redux + API service layer + error handling map.
- Bảng `users` hiện có (giữ nguyên `employee_code`, `password_hash`, `is_active` — AC-29), hash bcrypt giữ nguyên (AC-27).

**Out of Scope (không sinh TC cho các mục này):** OTP/SMS đăng nhập thường, 2FA, đổi mật khẩu định kỳ 3 tháng, khoá theo IP, đăng nhập `example-mobile`, trang quản lý/ngắt phiên theo thiết bị, SSO/mạng xã hội, đăng ký tự phục vụ, màn đổi mật khẩu khi đang đăng nhập.

---

## Q&A — Ambiguities

| ID | Reference | Screen | Question (VN) + Assumption/Đề xuất | Impact | Severity | Status |
|----|-----------|--------|--------------------------------------|--------|----------|--------|
| AMB-01 | OQ-01, BR-01 | `WB_AUTH_001` | Migrate 180 tài khoản `NVxxxx` sang email thế nào — (a) hành chính nhập tay, (b) dual-auth 3 tháng, (c) bắt buộc reset qua "Quên mật khẩu"? Đề xuất: chờ PO quyết trước khi viết TC cho AC-30 (email unique) và AC-04 (bộ đếm sai) vì phương án (b) phát sinh nhánh flow đăng nhập bằng mã cũ. | Chặn TC cho AC-30, có thể đổi cả AC-04 nếu chọn (b) | High | TBD |
| AMB-02 | OQ-02, AF-07 | `WB_AUTH_001` | Hết 15 phút khoá mà vẫn sai tiếp thì xử lý sao — (a) khoá tiếp 15p, (b) tăng dần 15→30→60p, (c) khoá hẳn chờ admin? `DESIGN.md (example-api)` đang đặt **placeholder (a)** nhưng SPEC ghi rõ đây là điểm PO chưa chốt. Đề xuất: giữ placeholder (a) để viết TC nháp, đánh dấu rõ "cần review lại nếu PO chọn phương án khác". | Chặn TC chính thức cho AF-07 | Medium | TBD |
| AMB-03 | OQ-03, Out-of-scope #6 | — | Có cần trang xem/ngắt phiên theo thiết bị không? SPEC đã mặc định phương án (b) — chỉ dựa BR-08 (đổi MK = thu hồi hết phiên), đưa vào Out of Scope. Đề xuất: không sinh TC cho trang quản lý thiết bị đợt này (theo giả định SPEC). | Không chặn TC vì đã có giả định rõ trong SPEC | Low | Assumed (theo SPEC) |
| AMB-04 | OQ-04, AF-21 | `WB_AUTH_003` | Quy tắc mật khẩu mới là gì — giữ nguyên tối thiểu 6 ký tự (hệ thống cũ) hay siết lại (độ dài, loại ký tự)? `DESIGN.md (example-web)` đang dùng **placeholder 6+ ký tự, không ràng buộc loại ký tự**, thanh độ mạnh tính theo độ dài + có chữ hoa/số/ký tự đặc biệt/chữ thường (%). Đề xuất: dùng placeholder này để viết TC Boundary/Field-Validation nháp cho ô mật khẩu, đánh dấu rõ cần review lại khi PO/Tech Lead chốt. | Chặn TC Field-Level Validation đầy đủ cho ô "Mật khẩu mới" + TC cho Password Strength Bar | High | TBD |
| AMB-05 | OQ-05, HP-B bước 4, AC-18 | `WB_AUTH_002` | Nhà cung cấp gửi email chưa chọn. Không có nhà cung cấp thật → không test được E2E "nhận email chứa link" (AC-18) cho tới khi có mock/service thật. Đề xuất: TC cho AC-18 sẽ ghi rõ "cần môi trường có email service (thật hoặc mock) mới verify được", không tự giả định đã có. | Chặn verify đầy đủ AC-18; các TC khác của luồng forgot-password (validate email, cooldown, thông báo chung) không bị chặn | Medium | TBD |
| AMB-06 | OQ-06, AF-17 | `WB_AUTH_003` | Yêu cầu link đặt lại mới khi link cũ chưa hết hạn — link cũ có bị vô hiệu không? `DESIGN.md (example-api)` đang đặt **placeholder (a) vô hiệu link cũ, chỉ link mới nhất dùng được**. Đề xuất: dùng placeholder này để viết TC bảo mật nháp cho AF-17, đánh dấu rõ cần review lại. | Chặn TC chính thức cho AF-17 | Medium | TBD |
| AMB-07 | AC-06, BR-05 vs `DESIGN.md (example-web)` §useAuth | `WB_AUTH_001` | **Inconsistency phát hiện khi cross-check 2 DESIGN.md:** SPEC (BR-05, AC-06) yêu cầu thông báo khoá hiển thị **số phút còn lại**, khớp với response BE `remaining_minutes` (đơn vị phút). Nhưng `example-web/DESIGN.md` hook `useAuth` lại build message `"Tài khoản bị khoá. Vui lòng thử lại sau ${lockState.remainingSeconds} giây."` — đơn vị **giây**, không phải phút. Đề xuất: FE nên hiển thị theo phút (khớp SPEC) hoặc SPEC cần làm rõ nếu muốn hiển thị giây — cần Tech Lead/PM xác nhận đơn vị hiển thị chính thức trước khi viết TC assert chính xác text. | Ảnh hưởng TC assert nội dung thông báo khoá (AC-06, AF-04, AF-05) — không rõ nên assert "phút" hay "giây" | Medium | TBD |

> **TBD** = chưa được PM/BA confirm | **Answered** = đã có câu trả lời | **Assumed** = SPEC đã tự đặt giả định rõ ràng, không cần hỏi lại

---

## Acceptance Criteria

### Đăng nhập (`WB_AUTH_001`)

| REQ ID (BR/AF nguồn) | AC ID | AC Content | Status |
|---|---|---|---|
| BR-01, BR-12, BR-02 | AC-01 | Email hợp lệ + mật khẩu đúng + `is_active=true` + không bị khoá → đăng nhập thành công, vào trang chủ | Confirmed |
| BR-01 | AC-02 | Email có hoa/khoảng trắng thừa (`  User@Example.com  `) vẫn đăng nhập được như `user@example.com` | Confirmed |
| BR-11, BR-10 | AC-03 | Sai email hoặc sai mật khẩu → thông báo giống hệt nhau, không lộ tồn tại email | Confirmed |
| BR-02 | AC-04 | Sai lần 1→4 vẫn thử tiếp; sai lần 5 → khoá 15 phút | Assumed (phụ thuộc AMB-01 nếu chọn dual-auth) |
| BR-02, BR-04 | AC-05 | Đang bị khoá, nhập đúng mật khẩu vẫn bị từ chối, không cấp token | Confirmed |
| BR-05 | AC-06 | Thông báo khoá hiển thị số phút còn lại, giảm dần theo thời gian thực | Confirmed nội dung nghiệp vụ / **TBD đơn vị hiển thị** (xem AMB-07) |
| BR-03 | AC-07 | Sai 4 lần rồi đúng lần 5 → thành công; sai tiếp 4 lần sau đó không bị khoá (đếm đã reset) | Confirmed |
| BR-04 | AC-08 | Tài khoản A bị khoá không ảnh hưởng tài khoản B dù cùng IP | Confirmed |
| BR-12 | AC-09 | `is_active=false` → thông báo vô hiệu hoá, không cấp token, không tăng bộ đếm khoá | Confirmed |
| AF-10 | AC-10 | Bấm nút/Enter nhiều lần liên tiếp → chỉ 1 request được gửi, bộ đếm sai tăng tối đa 1 | Confirmed |
| AF-09 | AC-11 | Server 5xx/mất mạng → banner đỏ, email đã gõ vẫn còn trong ô | Confirmed |

### Phiên đăng nhập

| REQ ID (BR/AF nguồn) | AC ID | AC Content | Status |
|---|---|---|---|
| BR-06 | AC-12 | Access token hết hạn sau đúng 15 phút; refresh token còn hạn → tự làm mới, không gián đoạn | Confirmed |
| BR-06, BR-07 | AC-13 | Tick "Ghi nhớ đăng nhập" → đóng/mở lại trình duyệt trong 30 ngày vẫn còn đăng nhập | Confirmed |
| BR-07 | AC-14 | Không tick "Ghi nhớ" → đóng trình duyệt rồi mở lại phải đăng nhập lại | Confirmed |
| BR-08 | AC-15 | Đăng nhập 2 trình duyệt, đổi MK ở trình duyệt 1 → trình duyệt 2 bị đá về login ở thao tác kế tiếp | Confirmed |
| HP-A bước 7 | AC-16 | Bị đá ra từ trang cụ thể → sau đăng nhập lại, quay về đúng trang đó | Confirmed |

### Quên / đặt lại mật khẩu

| REQ ID (BR/AF nguồn) | AC ID | AC Content | Status |
|---|---|---|---|
| BR-10 | AC-17 | Email tồn tại và không tồn tại → thông báo trên màn giống hệt nhau | Confirmed |
| BR-09, OQ-05 | AC-18 | Email tồn tại → nhận được email chứa link đặt lại | **TBD** (xem AMB-05 — cần email service thật/mock để verify E2E) |
| BR-13 | AC-19 | Gửi "Gửi hướng dẫn" lần 2 trong 60 giây → bị chặn, hiển thị thời gian chờ | Confirmed |
| BR-09 | AC-20 | Link mở trong 60 phút và chưa dùng → vào được màn đặt mật khẩu mới | Confirmed |
| BR-09 | AC-21 | Link mở sau 60 phút → "Link đã hết hạn" + nút gửi lại | Confirmed |
| BR-09, AF-19 | AC-22 | Link đã dùng 1 lần → mở lại hiển thị đúng thông báo như hết hạn | Confirmed |
| AF-20 | AC-23 | Hai ô mật khẩu không khớp → lỗi dưới ô thứ hai, không gọi API | Confirmed |
| BR-14 | AC-24 | Đặt lại thành công → thông báo ngắn, về màn đăng nhập, không tự động đăng nhập | Confirmed |
| BR-08, BR-14 | AC-25 | Đăng nhập bằng MK cũ sau khi đã reset → thất bại; MK mới → thành công | Confirmed |
| OQ-04, AF-21 | *(chưa có AC số riêng)* | Mật khẩu mới không đạt quy tắc → lỗi dưới ô thứ nhất | **TBD** (xem AMB-04 — chưa có quy tắc chính thức) |
| OQ-06, AF-17 | *(chưa có AC số riêng)* | Yêu cầu link mới khi link cũ chưa hết hạn | **TBD** (xem AMB-06) |

### Bảo mật & vận hành

| REQ ID (BR/AF nguồn) | AC ID | AC Content | Status |
|---|---|---|---|
| BR-15 | AC-26 | Không có password/access token/refresh token trong log ở mọi mức, kể cả debug | Confirmed |
| Precondition (bcrypt) | AC-27 | Mật khẩu lưu dạng hash bcrypt; 180 tài khoản hiện có không phải đặt lại MK do đổi thuật toán | Confirmed |
| Tech note (multi-instance) | AC-28 | Bộ đếm sai hoạt động đúng khi API chạy nhiều instance song song (3 lần qua instance 1 + 2 lần qua instance 2 → khoá) | Confirmed |
| Precondition (schema) | AC-29 | Không cột nào của bảng `users` bị đổi tên/xoá (`employee_code`, `password_hash`, `is_active`) | Confirmed |
| BR-01, OQ-01 | AC-30 | Email đăng nhập duy nhất — không có 2 tài khoản active cùng email | **TBD** (xem AMB-01 — phụ thuộc phương án migration 180 tài khoản) |

---

## History
- v1 (18/08/2026): `/analyze-req` — khởi tạo, phát hiện 7 AMB (6 từ SPEC Open Questions + 1 mới từ cross-check 2 DESIGN.md về đơn vị hiển thị thời gian khoá tài khoản)
