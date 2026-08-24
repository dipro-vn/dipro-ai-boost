# Requirements Analysis: User Login — example-web (Web UI)

## Summary

**Tính năng:** Đăng nhập bằng Email + Mật khẩu (thay thế mã nhân viên cũ) + Quên mật khẩu tự phục vụ

**Mục đích nghiệp vụ:**
- Mở tài khoản cho khách hàng doanh nghiệp từ 09/2026 (không có mã nhân viên) → cần định danh email duy nhất
- Chống dò mật khẩu (ưu tiên cao nhất PO): sai 5 lần → khoá 15 phút/tài khoản
- Cho phép tự phục vụ quên mật khẩu qua email (thay vì gọi hành chính)
- Kiểm soát phiên: đổi/đặt lại mật khẩu → thu hồi toàn bộ refresh token

**Actors:**
- Nhân viên nội bộ (~180 tài khoản, dùng máy tính bảng, nhạy cảm với rebind login)
- Người dùng doanh nghiệp (khách hàng mới)

**Luồng chính:**
1. **HP-A** — Đăng nhập thành công: Email + MK → Access token (15p) + Refresh token (30 ngày hoặc session-only)
2. **HP-B** — Quên mật khẩu: Email → Email link (60p, 1 lần dùng) → Đặt MK mới → Đăng nhập lại

**Scope:**
- ✅ 3 màn hình: Đăng nhập, Quên MK, Đặt MK mới
- ✅ Email lowercase + trim tự động
- ✅ Sai 5 lần → khoá 15 phút, hiển thị countdown
- ✅ Ghi nhớ đăng nhập (30 ngày) vs session-only
- ❌ OTP/SMS, 2FA, IP-based lock, change-password khi online, device management

**Thời gian deadline:** 15/09/2026

**Phụ thuộc:**
- `example-api` (API contract cần lock: endpoints login, refresh, logout, forgot-password, reset-password + error codes)
- Design chưa có (DESIGN.md chưa công bố, Figma chưa có)
- Email service provider chưa chọn (OQ-05)

---

## Q&A — Ambiguities

| ID | Reference | Screen | Câu hỏi + Đề xuất | Ảnh hưởng | Severity | Status |
|----|-----------|--------|---|---|---|---|
| **OQ-01** | BR / Precondition | Tất cả | **Migrate 180 tài khoản từ mã nhân viên → email?** <br> Phương án: (a) Hành chính nhập; (b) Hỗ trợ cả 2 kiểu 3 tháng; (c) Buộc quên MK. <br> **Đề xuất:** Clarify quy trình migrate DB, AC-30 có ảnh hưởng nếu chọn (b). | Chặn Phase 1 (migration) | High | TBD |
| **OQ-02** | AF-07 | WB_AUTH_001 | **Sau 15p khoá, vẫn sai tiếp → khoá lại hay tăng dần?** <br> Phương án: (a) 15p; (b) Tăng 15→30→60; (c) Khoá hẳn chờ admin. <br> **Đề xuất:** Câu này ảnh hưởng UX, cần PO quyết. | AF-07 chưa định hành vi | Medium | TBD |
| **OQ-03** | BR-08, Out of Scope | Tất cả | **Có trang quản lý phiên/thiết bị không?** <br> SPEC hiện giả định chỉ "đổi MK = thu hồi hết refresh token" (rẻ). <br> **Đề xuất:** Giữ SPEC hiện tại (Out of Scope #6), không phát sinh trang admin đợt này. | Ảnh hưởng scope/timeline | Medium | TBD |
| **OQ-04** | AF-21, AC-24 | WB_AUTH_003 | **Quy tắc mật khẩu mới?** (độ dài tối thiểu, loại ký tự?) <br> Hệ thống cũ: tối thiểu 6 ký tự. Siết lại hay giữ? <br> **Đề xuất:** Hỏi PO/Tech Lead, ảnh hưởng thanh độ mạnh ở UI. | AF-21 chưa định hành vi, thanh độ mạnh không design được | High | TBD |
| **OQ-05** | HP-B bước 4 | WB_AUTH_002, WB_AUTH_003 | **Email service provider là gì?** (SendGrid, AWS SES, v.v.) <br> Hiện chưa chọn. <br> **Đề xuất:** Cần Tech Lead/PM xác định, ảnh hưởng contract API + test end-to-end. | Không test được HP-B luồng quên MK end-to-end | High | TBD |
| **OQ-06** | AF-17 | WB_AUTH_002 | **Link mới khi link cũ chưa hết hạn → link cũ bị vô hiệu?** <br> Phương án: (a) Vô hiệu link cũ; (b) Cả 2 cùng dùng được. <br> **Đề xuất:** Ảnh hưởng bảo mật, cần Tech Lead quyết. | AF-17 chưa định hành vi | Medium | TBD |

> **Status:** 
> - **TBD** = chưa được PM/BA/PO confirm — QC không tự chọn phương án
> - **Answered** = đã có câu trả lời, cập nhật AC

---

## Acceptance Criteria

| AC ID | AC Content | Traceability | Status | Notes |
|-------|-----------|---|---|---|
| **AC-01** | Người dùng có email hợp lệ + MK đúng + `is_active = true` + không bị khoá → đăng nhập thành công, vào trang chủ | HP-A | Confirmed | Hạnh phúc lối |
| **AC-02** | Email nhập có chữ hoa hoặc khoảng trắng thừa → vẫn đăng nhập được như email normalized | HP-A, BR-02 | Confirmed | Normalize: lowercase + trim 2 đầu |
| **AC-03** | Nhập sai email HOẶC sai MK → thông báo **giống hệt nhau** ở cả 2 case, KHÔNG tiết lộ email tồn tại | BR-11 | Confirmed | Bảo mật: không phân biệt email sai vs MK sai |
| **AC-04** | Sai MK lần 1→4: vẫn cho thử. Sai lần **5** liên tiếp: tài khoản bị khoá 15 phút, mọi lần thử sau bị từ chối | BR-02 | Confirmed | Key feature: chống dò mật khẩu |
| **AC-05** | Trong lúc bị khoá, nhập **đúng** MK vẫn bị từ chối, KHÔNG cấp token | AF-05 | Confirmed | Security: không double-check khi bị khoá |
| **AC-06** | Thông báo khoá hiển thị **số phút còn lại** và giá trị này giảm dần theo thời gian thực tế | BR-05 | Confirmed | UX: countdown tối ưu UX |
| **AC-07** | Sai 4 lần → nhập đúng lần 5 → đăng nhập thành công, bộ đếm reset về 0. Sau đó sai 4 lần KHÔNG bị khoá | BR-03 | Confirmed | Reset counter khi thành công |
| **AC-08** | Tài khoản A bị khoá thì tài khoản B (dù cùng IP) vẫn đăng nhập bình thường | BR-04 | Confirmed | Không khoá theo IP |
| **AC-09** | Tài khoản `is_active = false` → hiển thị *"Tài khoản đã bị vô hiệu hoá, liên hệ quản trị viên"*, KHÔNG cấp token, KHÔNG tăng bộ đếm khoá | AF-08, BR-12 | Confirmed | UX: thông báo rõ, không làm giả alarm |
| **AC-10** | Bấm nút Đăng nhập 5 lần rất nhanh → chỉ 1 request gửi đi (verify qua network log), bộ đếm sai tăng tối đa 1 | AF-10, BR-02 | Confirmed | UX: disable nút khi loading, chống double-submit |
| **AC-11** | Server 5xx hoặc mất mạng → banner đỏ ở đầu form, email đã gõ **vẫn còn** trong ô | AF-09 | Confirmed | UX: giữ dữ liệu nhập, cho retry |
| **AC-12** | Access token hết hạn 15 phút, refresh token còn hạn → phiên tự làm mới, người dùng không gián đoạn | BR-06, AF-11 | Confirmed | Token lifetime |
| **AC-13** | Tick "Ghi nhớ đăng nhập" → đóng+mở trình duyệt trong 30 ngày vẫn đăng nhập được | BR-06, BR-07, AF-13 | Confirmed | Persistent token |
| **AC-14** | KHÔNG tick "Ghi nhớ đăng nhập" → đóng trình duyệt → mở lại phải đăng nhập lại | BR-07, AF-13 | Confirmed | Session-only token |
| **AC-15** | Đăng nhập trên 2 trình duyệt, đặt lại MK ở trình duyệt 1 → trình duyệt 2 bị đá về màn đăng nhập ở thao tác kế tiếp | BR-08, AF-23 | Confirmed | Revoke all sessions khi reset MK |
| **AC-16** | Bị đá ra khi ở trang cụ thể → sau khi đăng nhập lại, quay về **đúng trang đó** | HP-A, AF-12 | Confirmed | UX: không thoát khỏi workflow |
| **AC-17** | Nhập email tồn tại → thông báo như không tồn tại. Email không tồn tại → **cùng thông báo** | HP-B, BR-10 | Confirmed | Bảo mật: không leak email tồn tại |
| **AC-18** | Email tồn tại → nhận email chứa link đặt lại trong hộp thư | HP-B bước 4 | **TBD** | Phụ thuộc OQ-05 (email provider chưa chọn) |
| **AC-19** | Bấm "Gửi hướng dẫn" lần 2 trong 60s → bị chặn, hiển thị thời gian chờ | BR-13, AF-16 | Confirmed | Chống spam |
| **AC-20** | Link mở trong 60 phút + chưa dùng → vào được màn đặt MK mới | HP-B, BR-09 | Confirmed | Link lifetime |
| **AC-21** | Link mở sau 60 phút → *"Link đã hết hạn"* + nút gửi lại | BR-09, AF-18 | Confirmed | Link expiry UX |
| **AC-22** | Link đã dùng 1 lần → mở lại → **đúng thông báo như hết hạn**, không phân biệt | BR-09, AF-19 | Confirmed | Security: không leak link status |
| **AC-23** | Hai ô MK không khớp → lỗi dưới ô thứ 2, không gọi API | AF-20 | Confirmed | Client-side validation |
| **AC-24** | Đặt lại thành công → thông báo ngắn, chuyển về màn đăng nhập, **KHÔNG** tự động đăng nhập | HP-B bước 7, BR-14 | Confirmed | UX: buộc đăng nhập lại = verify MK mới |
| **AC-25** | Đăng nhập bằng MK cũ sau khi reset → thất bại. MK mới → thành công | HP-B | Confirmed | Verify MK được set |
| **AC-26** | Không có MK, access token, refresh token nào xuất hiện ở log (bao gồm debug) | BR-15 | Confirmed | Bảo mật: không log secret |
| **AC-27** | MK lưu bcrypt, 180 tài khoản hiện có KHÔNG phải reset do đổi thuật toán | AC-27 từ Precondition | Confirmed | Backward compatibility |
| **AC-28** | Bộ đếm sai hoạt động đúng khi API chạy nhiều instance: sai 3 lần instance 1 + 2 lần instance 2 → tài khoản bị khoá | BR-02 | **TBD** | Phụ thuộc implementation backend (Redis vs PostgreSQL) — cần Tech Lead quyết |
| **AC-29** | KHÔNG đổi/xoá cột bảng `users`: `employee_code`, `password_hash`, `is_active` | Precondition | Confirmed | Backward compatibility |
| **AC-30** | Email dùng đăng nhập là **duy nhất**: không tồn tại 2 tài khoản active cùng email | BR-01, Precondition | **TBD** | Phụ thuộc OQ-01 (migration từ mã nhân viên — email hiện không unique) |

> **Status:**
> - **Confirmed** = AC đã được SPEC.md chốt, QC có đủ thông tin để sinh TC
> - **TBD** = AC phụ thuộc OQ chưa được trả lời

---

## Screen Inventory

| Screen Code | Screen Name | Actor | Platform | UI Type | Mô tả ngắn | Figma Frame | Status |
|---|---|---|---|---|---|---|---|
| **WB_AUTH_001** | Đăng nhập | Nhân viên nội bộ, KH doanh nghiệp | example-web | Form | Logo trên, form giữa. Ô Email (tự lowercase+trim), Ô MK (có nút hiện/ẩn), checkbox "Ghi nhớ đăng nhập" (mặc định không tick). Nút Đăng nhập, link "Quên MK?" ở dưới. Lỗi inline ô email + banner lỗi chung ở trên. | _(chưa có)_ | Design pending |
| **WB_AUTH_002** | Quên mật khẩu — nhập email | Nhân viên nội bộ, KH doanh nghiệp | example-web | Form | 1 ô Email + nút "Gửi hướng dẫn". Sau gửi → luôn cùng 1 thông báo. Nút gửi có đếm ngược 60s. Link quay lại đăng nhập. | _(chưa có)_ | Design pending |
| **WB_AUTH_003** | Đặt mật khẩu mới | Nhân viên nội bộ, KH doanh nghiệp | example-web | Form | Mở từ link email. 2 ô "MK mới" + "Nhập lại MK mới", kèm thanh độ mạnh. Xử lý link hết hạn/đã dùng (cùng 1 thông báo + nút gửi lại). Thành công → thông báo ngắn → về màn đăng nhập. | _(chưa có)_ | Design pending |

---

## History

- **v1 (2026-08-19 19:00)** — `/analyze-req` khởi tạo từ SPEC.md
  - 30 ACs confirmed, 6 OQs TBD
  - 3 screens inventory
  - Email service provider (OQ-05), migration strategy (OQ-01), password rules (OQ-04) chưa quyết

---

## Notes cho `/plan-tcs`

1. Phân rã 3 screens → components (Textbox, Button, Checkbox, Countdown timer, Banner, Dialog...)
2. Risk assessment: High (sai 5 lần → khoá = core feature), Medium (token refresh = phiên), Low (UI validation)
3. Chờ design để xác định exact UI states (Normal/Focus/Error/Loading/Disabled)
4. Countdown timer trong AC-06 cần verify được implementation (frontend vs backend-driven clock)
5. Email lowercase + trim: cần test edge cases (double-space, unicode, international domain)
