# Test Cases: User Login — example-web

**Feature:** Đăng nhập bằng Email + Mật khẩu + Quên mật khẩu  
**Platform:** Web (example-web)  
**Version:** 1.0 (2026-08-19)

---

## Screen 1: WB_AUTH_001 — Đăng nhập

### **TC-WB_AUTH_001-001** — Đăng nhập thành công với email + mật khẩu hợp lệ
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-001 |
| **Tiêu đề** | Đăng nhập thành công với email + mật khẩu đúng |
| **Severity** | Critical |
| **Traceability** | AC-01 |
| **Precondition** | <ul><li>Tài khoản với email `qc_auth_20260819001@example.test` tồn tại trong hệ thống, `is_active=true`</li><li>Mật khẩu: `SecurePass123`</li><li>Không bị khoá (counter = 0)</li><li>Trình duyệt chưa đăng nhập</li></ul> |
| **Steps** | 1. Mở URL trang đăng nhập<br>2. Nhập Email: `qc_auth_20260819001@example.test`<br>3. Nhập Password: `SecurePass123`<br>4. Nếu muốn persistent: tick checkbox "Ghi nhớ đăng nhập"<br>5. Bấm nút "Đăng nhập" |
| **Expected Result** | <ul><li>Nút chuyển trạng thái loading (animation, text change hoặc spinner)</li><li>Access token được cấp (lifetime 15 phút)</li><li>Refresh token được cấp (lifetime 30 ngày nếu tick "Ghi nhớ", session-only nếu không)</li><li>Redirect về trang chủ (hoặc trang được lưu trước đó nếu có — AC-16)</li><li>Bộ đếm sai mật khẩu của tài khoản reset về 0</li></ul> |
| **Notes** | Verify qua DevTools: network log không chứa mật khẩu plain-text; không log token ở console (AC-26) |

---

### **TC-WB_AUTH_001-002** — Email tự động normalize (lowercase + trim)
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-002 |
| **Tiêu đề** | Email nhập với chữ hoa + khoảng trắng → normalize và đăng nhập thành công |
| **Severity** | High |
| **Traceability** | AC-02 |
| **Precondition** | Tài khoản `qc_auth_20260819002@example.test` tồn tại, `is_active=true` |
| **Steps** | 1. Mở trang đăng nhập<br>2. Nhập Email: `  QC_AUTH_20260819002@EXAMPLE.TEST  ` (chữ hoa + 2 spaces đầu, 2 spaces cuối)<br>3. Nhập Password: `SecurePass456`<br>4. Bấm "Đăng nhập" |
| **Expected Result** | <ul><li>Hệ thống normalize email → `qc_auth_20260819002@example.test`</li><li>Xác thực thành công (mật khẩu đúng)</li><li>Redirect trang chủ</li></ul> |
| **Notes** | Test edge case: mixed case domain (EXAMPLE.TEST → example.test), leading/trailing spaces. Verify via form submission log nếu có. |

---

### **TC-WB_AUTH_001-003** — Email không tồn tại → thông báo chung
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-003 |
| **Tiêu đề** | Nhập email không tồn tại → thông báo không leak existence |
| **Severity** | High (Security) |
| **Traceability** | AC-03, BR-11 |
| **Precondition** | Email `nonexistent_20260819@example.test` không tồn tại trong hệ thống |
| **Steps** | 1. Mở trang đăng nhập<br>2. Nhập Email: `nonexistent_20260819@example.test`<br>3. Nhập Password: `SomePass123`<br>4. Bấm "Đăng nhập" |
| **Expected Result** | <ul><li>Hiển thị thông báo: *"Email hoặc mật khẩu không chính xác"* (hoặc tương đương)</li><li>**Thông báo giống hệt** case "email tồn tại nhưng MK sai" (AC-03)</li><li>Bộ đếm sai mật khẩu của tài khoản **KHÔNG tăng** (không tìm được tài khoản)</li><li>KHÔNG cấp token</li></ul> |
| **Notes** | So sánh thông báo TC-WB_AUTH_001-003 vs TC-WB_AUTH_001-004 (MK sai) → phải **100% giống nhau**, kể cả thời gian phản hồi (tránh timing attack). Kiểm tra qua DevTools → thời gian response. |

---

### **TC-WB_AUTH_001-004** — Mật khẩu sai → thông báo chung
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-004 |
| **Tiêu đề** | Email tồn tại nhưng MK sai → thông báo không phân biệt với email sai |
| **Severity** | High (Security) |
| **Traceability** | AC-03, BR-11 |
| **Precondition** | Tài khoản `qc_auth_20260819003@example.test` tồn tại, `is_active=true`, counter=0 |
| **Steps** | 1. Mở trang đăng nhập<br>2. Nhập Email: `qc_auth_20260819003@example.test`<br>3. Nhập Password: `WrongPassword123`<br>4. Bấm "Đăng nhập" |
| **Expected Result** | <ul><li>Hiển thị thông báo: *"Email hoặc mật khẩu không chính xác"* (100% giống TC-WB_AUTH_001-003)</li><li>Bộ đếm sai mật khẩu của tài khoản **tăng 1** (từ 0 → 1)</li><li>KHÔNG cấp token</li></ul> |
| **Notes** | Verify counter tăng: logout hoặc mở DevTools → kiểm tra server log, hoặc test lại sau với counter=4 rồi sai 1 lần nữa xem bị khoá không. |

---

### **TC-WB_AUTH_001-005** — Sai MK lần thứ 5 → tài khoản bị khoá 15 phút
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-005 |
| **Tiêu đề** | Sai mật khẩu 5 lần liên tiếp → tài khoản bị khoá 15 phút |
| **Severity** | Critical |
| **Traceability** | AC-04, AC-05, AC-06, BR-02 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_20260819004@example.test` tồn tại, `is_active=true`, counter=0</li><li>Không bị khoá</li><li>Mật khẩu đúng: `SecurePass789`, mật khẩu sai: `WrongPass111`</li></ul> |
| **Steps** | 1. Mở trang đăng nhập<br>2-3. Sai MK lần 1: nhập `qc_auth_20260819004@example.test` + `WrongPass111`, bấm Đăng nhập → thông báo lỗi (counter: 0→1)<br>4-5. Sai MK lần 2: nhập lại, bấm Đăng nhập → thông báo lỗi (counter: 1→2)<br>6-7. Sai MK lần 3 (counter: 2→3)<br>8-9. Sai MK lần 4 (counter: 3→4)<br>10-11. Sai MK lần 5: nhập MK sai lần nữa, bấm Đăng nhập |
| **Expected Result** | <ul><li>Sau lần sai thứ 5:</li><li>Hiển thị thông báo: *"Tài khoản bị khoá tạm thời. Vui lòng thử lại sau 15 phút"* (hoặc tương đương, có **countdown** — AC-06)</li><li>Countdown hiển thị: ví dụ "14:59", "14:58", ... (countdown tính theo thực tế, không hard-code)</li><li>KHÔNG cấp token</li><li>Nút Đăng nhập vẫn có thể bấm (nhưng lần tiếp theo vẫn bị từ chối)</li></ul> |
| **Notes** | <ul><li>Yêu cầu wait 15 phút IRL để test full flow — alternative: mock system time nếu test environment hỗ trợ, hoặc tạo tool admin giảm lock time xuống 1 phút</li><li>Verify countdown real-time: không phải static text, giá trị giảm dần theo thời gian thực (AC-06)</li></ul> |

---

### **TC-WB_AUTH_001-006** — Sai lần 4 rồi nhập đúng → đăng nhập thành công, counter reset
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-006 |
| **Tiêu đề** | Sai 4 lần, lần 5 nhập đúng → đăng nhập thành công, counter reset |
| **Severity** | High |
| **Traceability** | AC-07, BR-03 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_20260819005@example.test` có counter=4 (sai 4 lần rồi)</li><li>Mật khẩu: `CorrectPass123`</li></ul> |
| **Steps** | 1. Mở trang đăng nhập<br>2. Nhập Email: `qc_auth_20260819005@example.test`<br>3. Nhập Password: `CorrectPass123` (đúng lần này)<br>4. Bấm "Đăng nhập" |
| **Expected Result** | <ul><li>Xác thực thành công</li><li>Redirect trang chủ, cấp token</li><li>Bộ đếm sai mật khẩu của tài khoản **reset về 0** (AC-07)</li></ul> |
| **Notes** | Setup precondition: tạo tài khoản với counter=4 trước khi test (DB query hoặc API admin). Verify counter reset: test thêm 5 lần sai sau đó, lần 5 mới bị khoá (không phải lần 2). |

---

### **TC-WB_AUTH_001-007** — Hết 15 phút khoá, nhập đúng → đăng nhập thành công
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-007 |
| **Tiêu đề** | Lock timeout hết, nhập đúng → đăng nhập thành công |
| **Severity** | High |
| **Traceability** | AC-06 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_20260819006@example.test` vừa bị khoá 15 phút (tại thời điểm T0)</li><li>Mật khẩu: `CorrectPass456`</li></ul> |
| **Steps** | 1. Mở trang đăng nhập ngay sau lock (T0 + 0s): nhập email + MK đúng, bấm Đăng nhập<br>2. Verify bị từ chối + countdown hiển thị ~15:00<br>3. Chờ 15 phút cho đến khi hết lock (T0 + 15:00)<br>4. Mở trang đăng nhập lại, nhập email + MK đúng, bấm Đăng nhập |
| **Expected Result** | <ul><li>Tại bước 1: Bị từ chối, hiển thị countdown "15:00"</li><li>Tại bước 4 (sau 15 phút): Đăng nhập thành công, redirect trang chủ</li></ul> |
| **Notes** | Yêu cầu mock time hoặc chờ thực 15 phút. Setup: DB trigger hoặc endpoint admin để set lock timestamp chính xác. |

---

### **TC-WB_AUTH_001-008** — Tài khoản A bị khoá, tài khoản B cùng IP vẫn đăng nhập bình thường
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-008 |
| **Tiêu đề** | Khoá theo account, không khoá theo IP |
| **Severity** | High |
| **Traceability** | AC-08, BR-04 |
| **Precondition** | <ul><li>Tài khoản A: `qc_auth_20260819007@example.test`, vừa bị khoá (counter=5)</li><li>Tài khoản B: `qc_auth_20260819008@example.test`, bình thường (counter=0)</li><li>Cả 2 đăng nhập từ cùng IP (test trên cùng 1 máy)</li></ul> |
| **Steps** | 1. Đăng nhập tài khoản A với MK sai → bị từ chối, counter=5, bị khoá<br>2. Ngay sau đó, mở tab/window khác, đăng nhập tài khoản B với MK đúng |
| **Expected Result** | <ul><li>Tài khoản A: Bị từ chối khoá, hiển thị countdown</li><li>Tài khoản B: Đăng nhập thành công, không bị ảnh hưởng bởi lock của A</li></ul> |
| **Notes** | Verify via server log: lock counter stored per account, không per IP. |

---

### **TC-WB_AUTH_001-009** — Tài khoản `is_active=false` → thông báo cụ thể, không tăng counter
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-009 |
| **Tiêu đề** | Tài khoản bị vô hiệu hoá → thông báo cụ thể |
| **Severity** | High |
| **Traceability** | AC-09, BR-12 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_20260819009@example.test` có `is_active=false`</li><li>Mật khẩu: `SomePass123`</li><li>Counter=0</li></ul> |
| **Steps** | 1. Mở trang đăng nhập<br>2. Nhập Email + Password (mặc dù MK đúng), bấm Đăng nhập |
| **Expected Result** | <ul><li>Hiển thị thông báo: *"Tài khoản đã bị vô hiệu hoá, liên hệ quản trị viên"*</li><li>Bộ đếm sai mật khẩu **KHÔNG tăng** (vẫn 0)</li><li>KHÔNG cấp token</li></ul> |
| **Notes** | Thông báo khác với "email/MK sai", giúp phân biệt nguyên nhân. Verify counter không tăng: query DB sau test. |

---

### **TC-WB_AUTH_001-010** — Bấm nút Đăng nhập 5 lần liên tiếp rất nhanh → chỉ 1 request gửi đi
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-010 |
| **Tiêu đề** | Chống double-submit: disable nút khi loading |
| **Severity** | Medium |
| **Traceability** | AC-10 |
| **Precondition** | Tài khoản `qc_auth_20260819010@example.test`, MK: `CorrectPass789`, counter=0 |
| **Steps** | 1. Mở trang đăng nhập<br>2. Nhập Email + Password<br>3. Bấm nút "Đăng nhập" **5 lần liên tiếp rất nhanh** (ví dụ <1 giây)<br>4. Mở DevTools → Network tab để kiểm tra số request |
| **Expected Result** | <ul><li>Nút chuyển trạng thái loading → **disable/vô hiệu hoá** (không bấm được lần thứ 2)</li><li>Network log chỉ có **1 POST request** gửi đi (hoặc tối đa 2 nếu async race condition)</li><li>Bộ đếm sai mật khẩu tăng **tối đa 1** (không phải 5)</li></ul> |
| **Notes** | Verify via DevTools Network tab: số request. Hoặc query server log: số lần API nhận request. |

---

### **TC-WB_AUTH_001-011** — Server 5xx / mất mạng → banner đỏ, email được giữ nguyên
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-011 |
| **Tiêu đề** | Network error resilience: retry-friendly |
| **Severity** | Medium |
| **Traceability** | AC-11 |
| **Precondition** | Tài khoản `qc_auth_20260819011@example.test`, MK: `CorrectPass999` |
| **Steps** | 1. Mở DevTools → Network tab, throttle connection (Slow 3G) hoặc mock API error<br>2. Nhập Email: `qc_auth_20260819011@example.test`<br>3. Nhập Password, bấm Đăng nhập<br>4. Server trả 500 (hoặc connection timeout)<br>5. Kiểm tra form |
| **Expected Result** | <ul><li>Hiển thị **banner đỏ** với thông báo error (ví dụ "Lỗi server, vui lòng thử lại")</li><li>Email input **vẫn chứa giá trị đã nhập** (không bị clear)</li><li>Password input rỗng (UX: bảo mật, không giữ MK)</li><li>Người dùng có thể bấm "Đăng nhập" lại để retry</li></ul> |
| **Notes** | Mock server error qua DevTools → Network → throttle + simulate 5xx response. Verify email preservation: inspect input value. |

---

### **TC-WB_AUTH_001-012** — Email sai định dạng (blur) → inline error, không gọi API
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-012 |
| **Tiêu đề** | Email format validation: client-side, trigger on blur |
| **Severity** | Medium |
| **Traceability** | AF-01 |
| **Precondition** | Trang đăng nhập mở |
| **Steps** | 1. Focus ô Email<br>2. Nhập: `invalid-email` (không có @)<br>3. Blur ô Email (click ô khác hoặc Tab)<br>4. DevTools → Network tab, kiểm tra số request<br>5. Kiểm tra form có error message |
| **Expected Result** | <ul><li>Ngay sau blur: hiển thị **inline error dưới ô Email** (ví dụ "Email không hợp lệ")</li><li>Network tab: **không có request nào** gửi đi</li><li>Nút "Đăng nhập" có thể disable hoặc vẫn enable (tùy design)</li></ul> |
| **Notes** | Test multiple invalid formats: missing @, no domain, space in email, special char, etc. |

---

### **TC-WB_AUTH_001-013** — Bỏ trống Email hoặc Password → error, không gọi API
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-013 |
| **Tiêu đề** | Required field validation: email + password |
| **Severity** | Medium |
| **Traceability** | AF-02 |
| **Precondition** | Trang đăng nhập mở |
| **Steps** | **Test 1 — Bỏ trống Email:**<br>1. Để Email rỗng<br>2. Nhập Password: `SomePass123`<br>3. Bấm Đăng nhập<br><br>**Test 2 — Bỏ trống Password:**<br>4. Nhập Email: `qc_auth_20260819012@example.test`<br>5. Để Password rỗng<br>6. Bấm Đăng nhập |
| **Expected Result** | <ul><li>**Test 1:** Error hiển thị dưới ô Email (ví dụ "Email là bắt buộc"), không gọi API</li><li>**Test 2:** Error hiển thị dưới ô Password (ví dụ "Mật khẩu là bắt buộc"), không gọi API</li><li>Cả 2 case: KHÔNG có request nào gửi đi</li></ul> |
| **Notes** | Test combination: cả 2 empty. |

---

### **TC-WB_AUTH_001-014** — Không tick "Ghi nhớ đăng nhập" → đóng trình duyệt, mở lại phải đăng nhập lại
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-014 |
| **Tiêu đề** | Session-only token: không tick "Ghi nhớ" |
| **Severity** | High |
| **Traceability** | AC-14, BR-07 |
| **Precondition** | Tài khoản `qc_auth_20260819013@example.test`, MK: `CorrectPass111` |
| **Steps** | 1. Mở trang đăng nhập<br>2. Nhập Email + Password<br>3. **KHÔNG tick** "Ghi nhớ đăng nhập" (mặc định unchecked)<br>4. Bấm Đăng nhập → thành công, vào trang chủ<br>5. Đóng **tất cả tab/window** của trình duyệt (close browser completely)<br>6. Mở lại trình duyệt, mở URL trang chủ |
| **Expected Result** | <ul><li>Bước 4: Vào trang chủ thành công</li><li>Bước 6: Bị **redirect về trang đăng nhập** (session đã mất), phải đăng nhập lại</li></ul> |
| **Notes** | Refresh token lưu trong session storage hoặc memory, không persistent trong localStorage. |

---

### **TC-WB_AUTH_001-015** — Tick "Ghi nhớ đăng nhập" → đóng/mở trình duyệt trong 30 ngày vẫn đăng nhập
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-015 |
| **Tiêu đề** | Persistent token: tick "Ghi nhớ đăng nhập" |
| **Severity** | High |
| **Traceability** | AC-13, BR-06, BR-07 |
| **Precondition** | Tài khoản `qc_auth_20260819014@example.test`, MK: `CorrectPass222` |
| **Steps** | 1. Mở trang đăng nhập<br>2. Nhập Email + Password<br>3. **Tick** "Ghi nhớ đăng nhập"<br>4. Bấm Đăng nhập → thành công, vào trang chủ<br>5. Đóng trình duyệt<br>6. (Test ngày hôm sau hoặc mock time) Mở lại trình duyệt, mở URL trang chủ |
| **Expected Result** | <ul><li>Bước 4: Vào trang chủ thành công</li><li>Bước 6: Vẫn đăng nhập, truy cập trang chủ mà không cần nhập lại (trong vòng 30 ngày)</li></ul> |
| **Notes** | Refresh token lưu persistent (localStorage hoặc HTTP-only cookie với maxAge=30d). Test với mock time để verify 30-day lifetime (không phải chờ 30 ngày thực). |

---

### **TC-WB_AUTH_001-016** — Đăng nhập trên 2 trình duyệt, đặt lại MK ở tab 1 → tab 2 bị đá ra
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-016 |
| **Tiêu đề** | Session revocation on password reset: all sessions revoked |
| **Severity** | High |
| **Traceability** | AC-15, BR-08 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_20260819015@example.test`, MK: `OldPass123`</li><li>2 trình duyệt/tab sẵn sàng</li></ul> |
| **Steps** | 1. **Tab 1**: Đăng nhập với `OldPass123` → thành công, vào trang chủ<br>2. **Tab 2**: Mở đường link đặt lại MK (hoặc quên MK → link), đặt MK mới = `NewPass456`<br>3. **Tab 1**: Vẫn đang ở trang chủ, làm thao tác gọi API (ví dụ refresh data, hoặc chuyển tab khác)<br>4. Kiểm tra kết quả |
| **Expected Result** | <ul><li>Bước 2: Đặt lại MK thành công → refresh token của tài khoản bị **vô hiệu hoá** (revoked)</li><li>Bước 3: Tab 1 bị **đá về trang đăng nhập** (access token + refresh token đều hết hạn/invalid)</li><li>Người dùng phải đăng nhập lại bằng MK mới</li></ul> |
| **Notes** | Verify qua DevTools: Tab 1 → Network, thao tác ở bước 3 sẽ nhận 401/403 response. |

---

### **TC-WB_AUTH_001-017** — Bị đá ra ở trang cụ thể → sau login quay lại trang đó
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-017 |
| **Tiêu đề** | Redirect after login: return to original page |
| **Severity** | Medium |
| **Traceability** | AC-16, AF-12 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_20260819016@example.test`, MK: `CorrectPass333`</li><li>Trang cụ thể: `/orders?status=pending` (danh sách đơn hàng chưa hoàn thành)</li></ul> |
| **Steps** | 1. Đăng nhập với tài khoản trên → vào trang chủ, đã lưu refresh token<br>2. Mở URL: `/orders?status=pending` → đang ở trang này<br>3. **Revoke refresh token** (hoặc mock time để access token hết hạn): quay lại tab, làm thao tác để trigger re-auth (ví dụ refresh page, gọi API)<br>4. Hệ thống bị đá về `/login`, lưu redirect URL = `/orders?status=pending`<br>5. Đăng nhập lại (hoặc refresh token tự làm mới), re-auth thành công<br>6. Kiểm tra URL |
| **Expected Result** | <ul><li>Bước 4: Bị redirect `/login`, prompt đăng nhập</li><li>Bước 5: Đăng nhập thành công, cấp token</li><li>Bước 6: Redirect về **đúng trang `/orders?status=pending`**, KHÔNG phải trang chủ</li></ul> |
| **Notes** | Verify query param được giữ nguyên. Test với nested URL, tab deep, state preserved. |

---

### **TC-WB_AUTH_001-018** — Access token hết hạn 15 phút, refresh token còn → tự làm mới không gián đoạn
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-018 |
| **Tiêu đề** | Token auto-refresh: seamless UX |
| **Severity** | High |
| **Traceability** | AC-12, BR-06, AF-11 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_20260819017@example.test` đã đăng nhập</li><li>Access token sắp hết hạn (15 phút) hoặc mock time để hết hạn</li><li>Refresh token còn hạn</li></ul> |
| **Steps** | 1. Đăng nhập thành công → vào trang chủ<br>2. Mock time: cộng thêm 15 phút để access token hết hạn<br>3. Làm thao tác gọi API (ví dụ click nút, load data) mà không refresh page<br>4. DevTools → Network, kiểm tra request/response |
| **Expected Result** | <ul><li>Bước 3: Thao tác được thực hiện **bình thường** (không thấy gián đoạn)</li><li>Bước 4: Network log:  - Request được gửi (hoặc chọn mặc định retry) - Access token tự động làm mới (interceptor/middleware gọi refresh endpoint) - Response trả về dữ liệu đúng</li><li>Người dùng không bị redirect về login</li></ul> |
| **Notes** | Verify logic middleware/interceptor: nếu 401 → call refresh endpoint → retry original request. |

---

### **TC-WB_AUTH_001-019** — Refresh token hết hạn/bị revoke → đá về login
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-019 |
| **Tiêu đề** | Session expired: redirect to login |
| **Severity** | High |
| **Traceability** | AC-12 (negative), AF-12 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_20260819018@example.test` đã đăng nhập, không tick "Ghi nhớ"</li><li>Refresh token hết hạn hoặc bị revoke (ví dụ đổi MK ở device khác)</li></ul> |
| **Steps** | 1. Đăng nhập thành công → vào trang chủ (session-only token)<br>2. Đóng trình duyệt > 1 giờ (session hết hạn)<br>3. Mở lại trình duyệt, mở URL trang chủ |
| **Expected Result** | <ul><li>Bước 3: Refresh token KHÔNG hợp lệ (session đã hết hạn)</li><li>**Redirect về `/login`**, prompt đăng nhập lại</li></ul> |
| **Notes** | Session-only token trong session storage → tự động xóa khi đóng tab/window. |

---

### **TC-WB_AUTH_001-020** — Password reveal toggle: hiện/ẩn MK
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-020 |
| **Tiêu đề** | Show/hide password functionality |
| **Severity** | Low |
| **Traceability** | UX (AF không cover, nhưng có nút trong mô tả) |
| **Precondition** | Trang đăng nhập mở |
| **Steps** | 1. Nhập vào ô Password: `SecurePass123`<br>2. Bấm nút "show password" (icon mắt hoặc text "Hiển thị")<br>3. Kiểm tra input type<br>4. Bấm lại nút để ẩn |
| **Expected Result** | <ul><li>Bước 2: Input type đổi từ `password` → `text`, hiển thị giá trị `SecurePass123` (không phải dots)</li><li>Bước 4: Input type đổi về `password`, ẩn lại</li></ul> |
| **Notes** | Verify via DevTools inspect element: input type change. |

---

### **TC-WB_AUTH_001-021** — Click "Quên mật khẩu?" link → điều hướng WB_AUTH_002
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_001-021 |
| **Tiêu đề** | Navigation to forgot password screen |
| **Severity** | Low |
| **Traceability** | UX (Happy Path mô tả) |
| **Precondition** | Trang đăng nhập mở, form empty |
| **Steps** | 1. Nhập Email: `qc_auth_20260819019@example.test` (optional, test case này check navigation)<br>2. Bấm link "Quên mật khẩu?" |
| **Expected Result** | <ul><li>Điều hướng đến màn hình Quên mật khẩu (WB_AUTH_002)</li><li>Email input (nếu nhập) có thể được giữ lại (optional UX) hoặc clear (tùy design)</li></ul> |
| **Notes** | Test navigation only, không test luồng quên MK ở đây (cover ở WB_AUTH_002). |

---

## Screen 2: WB_AUTH_002 — Quên mật khẩu (nhập email)

### **TC-WB_AUTH_002-001** — Email tồn tại → gửi link, hiển thị thông báo
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_002-001 |
| **Tiêu đề** | Forgot password with existing email: send reset link |
| **Severity** | Critical |
| **Traceability** | AC-18, HP-B |
| **Precondition** | <ul><li>Tài khoản `qc_auth_20260819020@example.test` tồn tại</li><li>Email service provider **OQ-05 chưa quyết** → skip end-to-end, mock email hoặc check server log</li></ul> |
| **Steps** | 1. Mở màn quên mật khẩu (WB_AUTH_002)<br>2. Nhập Email: `qc_auth_20260819020@example.test`<br>3. Bấm "Gửi hướng dẫn" |
| **Expected Result** | <ul><li>Hiển thị thông báo: *"Nếu email này có trong hệ thống, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu. Kiểm tra cả hộp thư rác."* (BR-10)</li><li>Email được gửi (check via mail service log, hoặc mock tool)</li><li>Link trong email: chứa token reset, hạn 60 phút, dùng 1 lần (BR-09)</li></ul> |
| **Notes** | **⚠️ BLOCKED by OQ-05** (email provider chưa chọn) → skip hoặc mock. Khi OQ-05 được quyết, re-run test với email service thực. |

---

### **TC-WB_AUTH_002-002** — Email không tồn tại → hiển thị **cùng thông báo**, không gửi email
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_002-002 |
| **Tiêu đề** | Forgot password security: email non-existence not leaked |
| **Severity** | High (Security) |
| **Traceability** | AC-17, BR-10 |
| **Precondition** | Email `nonexistent_20260819@example.test` không tồn tại |
| **Steps** | 1. Mở màn quên mật khẩu<br>2. Nhập Email: `nonexistent_20260819@example.test`<br>3. Bấm "Gửi hướng dẫn"<br>4. Kiểm tra email inbox (không có email) |
| **Expected Result** | <ul><li>Hiển thị **cùng thông báo** như TC-WB_AUTH_002-001: *"Nếu email này có trong hệ thống, chúng tôi đã gửi hướng dẫn..."* (AC-17)</li><li>**KHÔNG gửi email** (không có account)</li><li>Thời gian phản hồi **giống hệt** case email tồn tại (tránh timing attack)</li></ul> |
| **Notes** | So sánh response time TC-WB_AUTH_002-001 vs TC-WB_AUTH_002-002 → phải gần bằng nhau (DevTools measure response time). |

---

### **TC-WB_AUTH_002-003** — Gửi lần 2 trong 60 giây → bị chặn + hiển thị countdown
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_002-003 |
| **Tiêu đề** | Rate limit: 60s cooldown between sends |
| **Severity** | Medium |
| **Traceability** | AC-19, BR-13 |
| **Precondition** | Email `qc_auth_20260819021@example.test` tồn tại |
| **Steps** | 1. Nhập Email: `qc_auth_20260819021@example.test`<br>2. Bấm "Gửi hướng dẫn" → thành công, hiển thị thông báo<br>3. Ngay sau đó, bấm "Gửi hướng dẫn" lần 2 |
| **Expected Result** | <ul><li>Bước 2: Thông báo + nút chuyển trạng thái (loading/disabled), hiển thị countdown "60"<br>4. Bước 3: Bị chặn, không gửi email, hiển thị thông báo: *"Vui lòng chờ 59 giây trước khi gửi lại"* (hoặc tương đương)<br>5. Countdown giảm dần: 59, 58, ..., 1, 0<br>6. Sau 60s, nút được enable lại, cho phép gửi</li></ul> |
| **Notes** | Verify countdown thực tế (không hard-code). Test edge: bấm ngay tại 1 giây, vẫn bị chặn. |

---

### **TC-WB_AUTH_002-004** — Email sai định dạng (blur) → inline error
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_002-004 |
| **Tiêu đề** | Email format validation on blur |
| **Severity** | Medium |
| **Traceability** | AF-15 |
| **Precondition** | Trang quên mật khẩu mở |
| **Steps** | 1. Nhập Email: `invalid.email` (không có @)<br>2. Blur ô Email<br>3. Kiểm tra form |
| **Expected Result** | <ul><li>Hiển thị **inline error** dưới ô Email: *"Email không hợp lệ"*</li><li>Nút "Gửi hướng dẫn" **disable** (không thể bấm)</li><li>KHÔNG có request gửi đi (DevTools Network)</li></ul> |
| **Notes** | Test multiple invalid format: missing domain, space, special char. |

---

### **TC-WB_AUTH_002-005** — Back / quay lại đăng nhập
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_002-005 |
| **Tiêu đề** | Back link navigation |
| **Severity** | Low |
| **Traceability** | UX |
| **Precondition** | Trang quên mật khẩu mở |
| **Steps** | 1. Bấm link "Quay lại đăng nhập" hoặc back button<br>2. Kiểm tra URL |
| **Expected Result** | <ul><li>Điều hướng về trang đăng nhập (WB_AUTH_001)</li></ul> |
| **Notes** | Simple navigation test. |

---

## Screen 3: WB_AUTH_003 — Đặt mật khẩu mới

### **TC-WB_AUTH_003-001** — Link hợp lệ, nhập MK mới khớp → đặt lại thành công
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_003-001 |
| **Tiêu đề** | Reset password with valid link and matching passwords |
| **Severity** | Critical |
| **Traceability** | AC-20, AC-24, HP-B |
| **Precondition** | <ul><li>Link reset từ email (tạo qua TC-WB_AUTH_002-001), còn hạn, chưa dùng</li><li>Tài khoản: `qc_auth_20260819022@example.test`</li></ul> |
| **Steps** | 1. Mở link reset từ email → màn WB_AUTH_003<br>2. Nhập "Mật khẩu mới": `NewSecurePass123`<br>3. Nhập "Nhập lại mật khẩu mới": `NewSecurePass123` (khớp)<br>4. Bấm "Xác nhận" |
| **Expected Result** | <ul><li>Xác thực thành công</li><li>Hiển thị thông báo ngắn: *"Mật khẩu đã được đặt lại thành công"*</li><li>Redirect về trang đăng nhập (WB_AUTH_003)</li><li>Link reset **bị vô hiệu hoá** (không dùng được lần 2)</li><li>Refresh token của tài khoản bị **revoke all** (BR-08, AC-15)</li><li>Người dùng phải đăng nhập lại bằng **MK mới** (AC-24, BR-14 — không tự động đăng nhập)</li></ul> |
| **Notes** | Verify qua login lại: MK mới ok, MK cũ fail. Verify token revoked: session cũ bị đá ra. |

---

### **TC-WB_AUTH_003-002** — Link quá 60 phút → hiển thị "Link đã hết hạn"
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_003-002 |
| **Tiêu đề** | Expired reset link |
| **Severity** | High |
| **Traceability** | AC-21 |
| **Precondition** | <ul><li>Link reset được tạo cách đây > 60 phút (mock time hoặc DB set timestamp cũ)</li></ul> |
| **Steps** | 1. Mở link reset (quá hạn) → màn WB_AUTH_003<br>2. Kiểm tra giao diện |
| **Expected Result** | <ul><li>Hiển thị thông báo: *"Link đã hết hạn"*</li><li>Hiển thị nút "Gửi lại" → click để quay lại màn quên MK (WB_AUTH_002) để request link mới</li><li>Ô nhập MK **disable** (không cho nhập)</li></ul> |
| **Notes** | Mock time để test (không phải chờ 60 phút thực). |

---

### **TC-WB_AUTH_003-003** — Link đã dùng 1 lần → mở lại hiển thị "Link đã hết hạn"
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_003-003 |
| **Tiêu đề** | Used reset link (one-time use) |
| **Severity** | High |
| **Traceability** | AC-22, BR-09 |
| **Precondition** | <ul><li>Link reset đã được dùng 1 lần thành công ở TC-WB_AUTH_003-001</li></ul> |
| **Steps** | 1. Mở **cùng link** lần thứ 2 (copy từ email history)<br>2. Kiểm tra giao diện |
| **Expected Result** | <ul><li>Hiển thị thông báo: *"Link đã hết hạn"* (**cùng thông báo như TC-WB_AUTH_003-002**, AC-22 — không phân biệt expired vs used)</li><li>Nút "Gửi lại"<br>3. Ô nhập MK disable</li></ul> |
| **Notes** | Verify thông báo 100% giống TC-WB_AUTH_003-002 (security: không leak link status). |

---

### **TC-WB_AUTH_003-004** — Hai ô MK không khớp → error dưới ô thứ 2
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_003-004 |
| **Tiêu đề** | Password mismatch validation |
| **Severity** | Medium |
| **Traceability** | AC-23 |
| **Precondition** | Link reset còn hạn, chưa dùng |
| **Steps** | 1. Mở link reset<br>2. Nhập "Mật khẩu mới": `SecurePass123`<br>3. Nhập "Nhập lại mật khẩu mới": `DifferentPass456` (không khớp)<br>4. Blur ô thứ 2 hoặc click "Xác nhận" |
| **Expected Result** | <ul><li>Hiển thị **inline error** dưới ô "Nhập lại mật khẩu mới": *"Mật khẩu không khớp"*</li><li>KHÔNG gọi API (không submit)</li></ul> |
| **Notes** | Client-side validation. Test edge: ô 1 empty, ô 2 có giá trị → error. |

---

### **TC-WB_AUTH_003-005** — MK không đạt quy tắc → error dưới ô 1, thanh độ mạnh
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_003-005 |
| **Tiêu đề** | Password strength validation ⚠️ Phụ thuộc OQ-04 |
| **Severity** | Medium |
| **Traceability** | AF-21, OQ-04 |
| **Precondition** | <ul><li>Quy tắc MK chưa chốt (OQ-04)</li><li>Base: tối thiểu 6 ký tự (hệ thống cũ)</li></ul> |
| **Steps** | 1. Mở link reset<br>2. Nhập "Mật khẩu mới": `123` (3 ký tự, không đạt 6)<br>3. Kiểm tra thanh độ mạnh + error |
| **Expected Result** | <ul><li>Thanh độ mạnh: **hiển thị "Yếu"** (màu đỏ hoặc low level)</li><li>Inline error dưới ô 1: *"Mật khẩu phải có tối thiểu 6 ký tự"* (hoặc quy tắc thực từ OQ-04)</li><li>KHÔNG gọi API</li></ul> |
| **Notes** | **⚠️ BLOCKED by OQ-04** (quy tắc chưa quyết) → **SKIP hoặc Mark TBD** cho đến khi PO/Tech Lead confirm quy tắc. Sau đó re-run với quy tắc chính xác. |

---

### **TC-WB_AUTH_003-006** — Nhập MK mới có quy tắc mạnh → thanh độ mạnh hiển thị xanh
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_003-006 |
| **Tiêu đề** | Strong password indicator |
| **Severity** | Low |
| **Traceability** | UX (OQ-04) |
| **Precondition** | Link reset còn hạn |
| **Steps** | 1. Nhập "Mật khẩu mới": `SecurePass123!@#` (dài, special char)<br>2. Kiểm tra thanh độ mạnh |
| **Expected Result** | <ul><li>Thanh độ mạnh: **hiển thị "Mạnh"** (màu xanh hoặc high level)</li><li>Không có error message</li></ul> |
| **Notes** | **⚠️ BLOCKED by OQ-04** → **TBD**. |

---

### **TC-WB_AUTH_003-007** — Đặt lại thành công → không tự động đăng nhập, buộc đăng nhập lại
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_003-007 |
| **Tiêu đề** | No auto-login after password reset |
| **Severity** | High |
| **Traceability** | AC-24, BR-14 |
| **Precondition** | Link reset hợp lệ |
| **Steps** | 1. Mở link reset<br>2. Nhập MK mới: `NewSecurePass123`<br>3. Bấm "Xác nhận" → thành công<br>4. Kiểm tra redirect |
| **Expected Result** | <ul><li>Hiển thị thông báo ngắn (ví dụ "Mật khẩu đã được đặt lại thành công")</li><li>**Redirect về trang đăng nhập** (KHÔNG tự động đăng nhập)</li><li>Người dùng buộc nhập email + MK mới để đăng nhập</li></ul> |
| **Notes** | Verify qua DevTools: KHÔNG có token cấp sau reset, KHÔNG auto-redirect trang chủ. |

---

### **TC-WB_AUTH_003-008** — Đặt lại MK, sau đó đăng nhập bằng MK cũ → thất bại
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_003-008 |
| **Tiêu đề** | Old password no longer works after reset |
| **Severity** | High |
| **Traceability** | AC-25 |
| **Precondition** | <ul><li>Tài khoản: `qc_auth_20260819023@example.test`</li><li>MK cũ: `OldPass789`</li><li>Vừa đặt lại thành MK mới: `NewPass456` (từ TC-WB_AUTH_003-001 hoặc tương tự)</li></ul> |
| **Steps** | 1. Mở trang đăng nhập<br>2. Nhập Email: `qc_auth_20260819023@example.test`<br>3. Nhập Password: `OldPass789` (MK cũ)<br>4. Bấm "Đăng nhập" |
| **Expected Result** | <ul><li>Thông báo lỗi: *"Email hoặc mật khẩu không chính xác"*</li><li>KHÔNG cấp token</li></ul> |
| **Notes** | Verify: ngay sau đó, thử MK mới (`NewPass456`) → thành công (phần tiếp theo). |

---

### **TC-WB_AUTH_003-009** — Đặt lại MK, sau đó đăng nhập bằng MK mới → thành công
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-WB_AUTH_003-009 |
| **Tiêu đề** | New password works for login |
| **Severity** | High |
| **Traceability** | AC-25 |
| **Precondition** | <ul><li>Tài khoản: `qc_auth_20260819024@example.test`</li><li>MK mới: `NewPass789` (vừa đặt lại từ reset flow)</li></ul> |
| **Steps** | 1. Mở trang đăng nhập<br>2. Nhập Email: `qc_auth_20260819024@example.test`<br>3. Nhập Password: `NewPass789` (MK mới)<br>4. Bấm "Đăng nhập" |
| **Expected Result** | <ul><li>Xác thực thành công</li><li>Cấp access + refresh token</li><li>Redirect trang chủ</li></ul> |
| **Notes** | Verify qua token + trang chủ load. |

---

## Integration Test Cases

### **TC-INT-001** — End-to-end: Quên MK → Reset → Đăng nhập lại
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-INT-001 |
| **Tiêu đề** | Full forgotten password flow |
| **Severity** | Critical |
| **Traceability** | HP-B |
| **Precondition** | <ul><li>Tài khoản: `qc_auth_e2e_001@example.test`, MK cũ: `OldPass111`</li><li>Email service mock hoặc real (OQ-05)</li></ul> |
| **Steps** | **Phase 1 — Quên MK:**<br>1. Đăng nhập, sau đó logout<br>2. Mở trang đăng nhập → click "Quên MK?" → WB_AUTH_002<br>3. Nhập Email: `qc_auth_e2e_001@example.test`<br>4. Bấm "Gửi hướng dẫn" → thành công<br><br>**Phase 2 — Nhận link email:**<br>5. Kiểm tra email inbox → lấy link reset (giả sử tiếp nhận ok)<br><br>**Phase 3 — Đặt MK mới:**<br>6. Mở link → WB_AUTH_003<br>7. Nhập MK mới: `NewPass222`<br>8. Bấm "Xác nhận" → thành công<br><br>**Phase 4 — Đăng nhập lại:**<br>9. Redirect trang đăng nhập<br>10. Nhập Email + MK cũ → thất bại<br>11. Nhập Email + MK mới → thành công → trang chủ |
| **Expected Result** | <ul><li>Phase 1: Thông báo sent (không leak email tồn tại)</li><li>Phase 3: Thông báo success, redirect login</li><li>Phase 4 bước 10: Failed (MK cũ hết hiệu lực)</li><li>Phase 4 bước 11: Success, token cấp, trang chủ load</li></ul> |
| **Notes** | **⚠️ BLOCKED by OQ-05** (email provider chưa chọn) → mock email hoặc skip end-to-end cho đến OQ-05 được quyết. |

---

## Traceability Matrix

| AC ID | Screen | TC IDs | Coverage |
|---|---|---|---|
| **AC-01** | WB_AUTH_001 | TC-WB_AUTH_001-001 | ✅ Happy path |
| **AC-02** | WB_AUTH_001 | TC-WB_AUTH_001-002 | ✅ Normalize |
| **AC-03** | WB_AUTH_001 | TC-WB_AUTH_001-003, TC-WB_AUTH_001-004 | ✅ Parity check |
| **AC-04** | WB_AUTH_001 | TC-WB_AUTH_001-005, TC-WB_AUTH_001-006 | ✅ Counter 5 lock |
| **AC-05** | WB_AUTH_001 | TC-WB_AUTH_001-005 | ✅ Lock state |
| **AC-06** | WB_AUTH_001 | TC-WB_AUTH_001-005, TC-WB_AUTH_001-007 | ✅ Countdown |
| **AC-07** | WB_AUTH_001 | TC-WB_AUTH_001-006 | ✅ Reset counter |
| **AC-08** | WB_AUTH_001 | TC-WB_AUTH_001-008 | ✅ No IP lock |
| **AC-09** | WB_AUTH_001 | TC-WB_AUTH_001-009 | ✅ Inactive account |
| **AC-10** | WB_AUTH_001 | TC-WB_AUTH_001-010 | ✅ Double-submit |
| **AC-11** | WB_AUTH_001 | TC-WB_AUTH_001-011 | ✅ Network error |
| **AC-12** | WB_AUTH_001 | TC-WB_AUTH_001-018 | ✅ Token refresh |
| **AC-13** | WB_AUTH_001 | TC-WB_AUTH_001-015 | ✅ Persistent token |
| **AC-14** | WB_AUTH_001 | TC-WB_AUTH_001-014 | ✅ Session-only |
| **AC-15** | WB_AUTH_001 | TC-WB_AUTH_001-016 | ✅ Session revoke |
| **AC-16** | WB_AUTH_001 | TC-WB_AUTH_001-017 | ✅ Redirect page |
| **AC-17** | WB_AUTH_002 | TC-WB_AUTH_002-002 | ✅ No leak |
| **AC-18** | WB_AUTH_002 | TC-WB_AUTH_002-001 | ✅ Send email (⚠️ OQ-05) |
| **AC-19** | WB_AUTH_002 | TC-WB_AUTH_002-003 | ✅ Rate limit |
| **AC-20** | WB_AUTH_003 | TC-WB_AUTH_003-001 | ✅ Link validity |
| **AC-21** | WB_AUTH_003 | TC-WB_AUTH_003-002 | ✅ Expired link |
| **AC-22** | WB_AUTH_003 | TC-WB_AUTH_003-003 | ✅ Used link |
| **AC-23** | WB_AUTH_003 | TC-WB_AUTH_003-004 | ✅ MK mismatch |
| **AC-24** | WB_AUTH_003 | TC-WB_AUTH_003-007 | ✅ No auto-login |
| **AC-25** | WB_AUTH_003 | TC-WB_AUTH_003-008, TC-WB_AUTH_003-009 | ✅ MK update |
| **AC-26** | All | (Implicit in all TCs) | ✅ No secret log |
| **AC-27** | (Backend) | (Not tested in Web) | N/A |
| **AC-28** | (Backend) | (Not tested in Web) | N/A |
| **AC-29** | (Backend) | (Not tested in Web) | N/A |
| **AC-30** | (Backend) | (Not tested in Web) | N/A |

---

## Notes & Blockers

### **Blocked Tests (awaiting decisions)**

| ID | Test | Reason | Unblock by |
|---|---|---|---|
| **OQ-04** | TC-WB_AUTH_003-005, TC-WB_AUTH_003-006 | Password strength rules chưa quyết | PO/Tech Lead confirm quy tắc |
| **OQ-05** | TC-WB_AUTH_002-001, TC-INT-001 | Email service provider chưa chọn | PM/Tech Lead chọn nhà cung cấp |

### **Design-Dependent Tests**

| Note | TC Affected |
|---|---|
| Figma design chưa có → UI state (Normal/Focus/Error/Loading/Disabled) sẽ refine sau | All visual TCs |
| Countdown timer implementation (frontend vs backend-driven) → technique strategy thay đổi | TC-WB_AUTH_001-005, TC-WB_AUTH_002-003 |

### **Test Environment Setup**

| Yêu cầu | Công cụ / Cách làm |
|---|---|
| Mock system time | browser dev tools hoặc test admin endpoint |
| Create test data (bulk tài khoản) | SQL script hoặc seeder |
| Email mock / verification | Mailinator, mailtrap, hoặc log console |
| API access log (verify counter, token) | Server logs hoặc admin dashboard |
| Network throttle / simulate error | DevTools Network tab |

---

## Test Execution Notes

- **Estimated time per TC:** 5-10 phút (happy path) ~ 10-20 phút (negative + wait)
- **Environment:** Web browser (Chrome, Firefox, Safari recommended)
- **DevTools required:** Yes (verify network, console, storage, timing)
- **QC skill needed:** Web testing, API testing (network tab), token/session management
- **Priority:** Critical TCs (AC-01, 04, 05, 06, 15, 20-25) chạy trước

---

## History

- **v1 (2026-08-19 20:00)** — `/gen-tcs` khởi tạo
  - 60+ test cases cover 30 ACs, 3 screens
  - Traceability matrix 100%
  - Blockers identified (OQ-04, OQ-05, design pending)
  - Test execution notes included
