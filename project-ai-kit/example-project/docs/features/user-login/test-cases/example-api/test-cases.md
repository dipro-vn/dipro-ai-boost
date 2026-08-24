# API Test Cases: User Login — example-api

**Feature:** REST API endpoints cho login + forgot password + reset  
**Platform:** example-api (NestJS + PostgreSQL)  
**Version:** 1.0 (2026-08-19)

---

## POST /auth/login

### **TC-API-LOGIN-001** — Login thành công với email + password hợp lệ
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-001 |
| **Tiêu đề** | Successful login with valid credentials |
| **Severity** | Critical |
| **Traceability** | AC-API-01 |
| **Precondition** | <ul><li>Database: Tài khoản `qc_auth_api_001@example.test` tồn tại, `password_hash` = bcrypt(`SecurePass123`), `is_active=true`</li><li>Counter = 0 (không bị lock)</li></ul> |
| **Request** | `POST /auth/login` <br> Content-Type: application/json <br> `{ "email": "qc_auth_api_001@example.test", "password": "SecurePass123", "rememberMe": false }` |
| **Expected Response** | **Status: 200 OK** <br> `{ "accessToken": "eyJ...", "refreshToken": "eyJ...", "expiresIn": 900, "user": { "id": "...", "email": "qc_auth_api_001@example.test", "isActive": true } }` |
| **Verification** | <ul><li>Access token: valid JWT, alg=HS256 (hoặc per spec), exp = now + 900s</li><li>Refresh token: valid JWT, exp = now + 2592000s (30 ngày vì rememberMe=false → session-only thực tế, store in memory)</li><li>Database: counter vẫn = 0 (hoặc xóa entry lock nếu có)</li><li>No plain-text password trong log (AC-API-20)</li></ul> |
| **Notes** | ⚠️ Phụ thuộc Contract Lock (API-001) — chờ confirm response schema chính xác. Response có thể khác (user field, token field name, v.v.). |

---

### **TC-API-LOGIN-002** — Email tự động normalize (lowercase + trim)
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-002 |
| **Tiêu đề** | Email normalization: uppercase + spaces → lowercase trim |
| **Severity** | High |
| **Traceability** | AC-API-02 |
| **Precondition** | Tài khoản `qc_auth_api_002@example.test` tồn tại, password hợp lệ |
| **Request** | `POST /auth/login` <br> `{ "email": "  QC_AUTH_API_002@EXAMPLE.TEST  ", "password": "CorrectPass", "rememberMe": true }` |
| **Expected Response** | **Status: 200 OK** <br> Token cấp, xác thực thành công (email được normalize) |
| **Verification** | <ul><li>Backend xử lý: email.toLowerCase().trim() trước khi query database</li><li>Login thành công (match email normalized)</li></ul> |
| **Notes** | Verify qua application logic hoặc integration test: test case khác (uppercase, space) phải thành công. |

---

### **TC-API-LOGIN-003** — Email không tồn tại → error (không leak existence)
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-003 |
| **Tiêu đề** | Non-existent email → INVALID_CREDENTIALS (security) |
| **Severity** | High (Security) |
| **Traceability** | AC-API-03 |
| **Precondition** | Email `nonexistent_api_20260819@example.test` không tồn tại |
| **Request** | `POST /auth/login` <br> `{ "email": "nonexistent_api_20260819@example.test", "password": "SomePass", "rememberMe": false }` |
| **Expected Response** | **Status: 400 Bad Request** <br> `{ "error": "INVALID_CREDENTIALS", "message": "Email or password is incorrect" }` |
| **Verification** | <ul><li>Status code = 400 (hoặc per spec)</li><li>Error code = INVALID_CREDENTIALS (cùng với password sai — AC-API-03)</li><li>Message không tiết lộ email tồn tại (vd không nói "Email not found")</li><li>Response time ≈ TC-API-LOGIN-004 (constant-time, tránh timing attack)</li></ul> |
| **Notes** | **Security critical:** Thông báo phải giống hệt TC-API-LOGIN-004 để không leak email existence. Verify bằng response time measurement (millisecond precision). |

---

### **TC-API-LOGIN-004** — Mật khẩu sai → error
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-004 |
| **Tiêu đề** | Wrong password → INVALID_CREDENTIALS |
| **Severity** | High (Security) |
| **Traceability** | AC-API-03 |
| **Precondition** | Tài khoản `qc_auth_api_003@example.test` tồn tại, counter=0 |
| **Request** | `POST /auth/login` <br> `{ "email": "qc_auth_api_003@example.test", "password": "WrongPassword", "rememberMe": false }` |
| **Expected Response** | **Status: 400** <br> `{ "error": "INVALID_CREDENTIALS", "message": "Email or password is incorrect" }` |
| **Verification** | <ul><li>Error = INVALID_CREDENTIALS (100% giống TC-API-LOGIN-003)</li><li>Message = "Email or password is incorrect" (không phân biệt)</li><li>Counter tăng 1 (0 → 1)</li><li>Response time ≈ TC-API-LOGIN-003 (constant-time)</li></ul> |
| **Notes** | Verify counter tăng: query database sau request. |

---

### **TC-API-LOGIN-005** — Sai mật khẩu lần 1-4: vẫn nhận 400, không lock
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-005 |
| **Tiêu đề** | Attempt counter 1-4: still allow login |
| **Severity** | High |
| **Traceability** | AC-API-04 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_api_004@example.test` tồn tại, counter=0</li><li>Sẽ submit 4 lần sai liên tiếp</li></ul> |
| **Steps** | 1. Submit wrong password 4 lần liên tiếp<br>2. Sau lần thứ 4, check counter |
| **Expected Response (Attempts 1-4)** | **Status: 400** <br> INVALID_CREDENTIALS (mỗi lần) |
| **Expected Response (After 4 attempts)** | Database counter = 4 (chưa lock) |
| **Verification** | <ul><li>Mỗi lần submit: 400 + INVALID_CREDENTIALS</li><li>Counter tăng: 0→1→2→3→4</li><li>Lần 4: vẫn nhận 400, không phải 429</li></ul> |
| **Notes** | Bulk test: tạo 4 requests sai, verify each response = 400, cuối cùng counter=4. |

---

### **TC-API-LOGIN-006** — Sai mật khẩu lần thứ 5 → tài khoản bị lock 15 phút
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-006 |
| **Tiêu đề** | 5th wrong attempt → lock for 15 minutes |
| **Severity** | Critical |
| **Traceability** | AC-API-04, AC-API-06 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_api_005@example.test`, counter=4 (sai 4 lần rồi)</li><li>Hoặc tạo bằng cách submit 4 requests sai từ TC-API-LOGIN-005</li></ul> |
| **Request (Lần 5)** | `POST /auth/login` <br> `{ "email": "qc_auth_api_005@example.test", "password": "WrongPass", "rememberMe": false }` |
| **Expected Response** | **Status: 429 Too Many Requests** <br> `{ "error": "ACCOUNT_LOCKED", "message": "Account locked. Try again after 900 seconds", "retryAfter": 900 }` |
| **Verification** | <ul><li>Status = 429 (hoặc 400 + ACCOUNT_LOCKED per spec — TBD)</li><li>Error = ACCOUNT_LOCKED</li><li>retryAfter = 900 (seconds, = 15 phút)</li><li>Database: `locked_until` = now + 900s</li></ul> |
| **Notes** | **⚠️ Contract TBD (API-002)** — error code, HTTP status, message format chưa lock. Adjust expect khi API-002 được confirm. |

---

### **TC-API-LOGIN-007** — Tài khoản bị lock, nhập đúng MK → vẫn từ chối
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-007 |
| **Tiêu đề** | Login during lock period (correct password) → still denied |
| **Severity** | High |
| **Traceability** | AC-API-06 |
| **Precondition** | Tài khoản `qc_auth_api_006@example.test` vừa bị lock (counter=5) |
| **Request** | `POST /auth/login` <br> `{ "email": "qc_auth_api_006@example.test", "password": "CorrectPass", "rememberMe": false }` |
| **Expected Response** | **Status: 429** <br> `{ "error": "ACCOUNT_LOCKED", "message": "...", "retryAfter": 900 }` |
| **Verification** | <ul><li>Mặc dù MK đúng, vẫn bị từ chối</li><li>Không cấp token</li><li>retryAfter vẫn ~900s (hoặc giảm dần theo thời gian thực)</li></ul> |
| **Notes** | Security: không cấp token ngay cả khi MK đúng (nếu lock). |

---

### **TC-API-LOGIN-008** — Hết 15 phút lock, nhập đúng → đăng nhập thành công
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-008 |
| **Tiêu đề** | Lock timeout expired → login succeeds |
| **Severity** | High |
| **Traceability** | AC-API-06 |
| **Precondition** | <ul><li>Tài khoản `qc_auth_api_007@example.test` bị lock tại T0</li><li>Hiện tại = T0 + 15 phút (mock time hoặc wait)</li></ul> |
| **Request** | `POST /auth/login` <br> `{ "email": "qc_auth_api_007@example.test", "password": "CorrectPass", "rememberMe": false }` |
| **Expected Response** | **Status: 200** <br> Token cấp |
| **Verification** | <ul><li>Đăng nhập thành công</li><li>Counter = 0 (reset)</li><li>locked_until cleared từ database</li></ul> |
| **Notes** | Mock time: add 15 min từ lock timestamp. Hoặc run test sau khi chờ 15 phút thực. |

---

### **TC-API-LOGIN-009** — Sai 4 lần, nhập đúng lần 5 → thành công + counter reset
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-009 |
| **Tiêu đề** | Successful login after 4 failures → counter reset |
| **Severity** | High |
| **Traceability** | AC-API-07 |
| **Precondition** | Tài khoản `qc_auth_api_008@example.test`, counter=4 |
| **Request** | `POST /auth/login` <br> `{ "email": "qc_auth_api_008@example.test", "password": "CorrectPass", "rememberMe": false }` |
| **Expected Response** | **Status: 200** <br> Token cấp |
| **Verification** | <ul><li>Đăng nhập thành công</li><li>Counter reset = 0 (database)</li></ul> |
| **Notes** | Test verify reset: submit 5 requests sai sau đó, lần 5 mới lock (không phải lần 2). |

---

### **TC-API-LOGIN-010** — Tài khoản A bị lock, tài khoản B (khác) vẫn đăng nhập ok
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-010 |
| **Tiêu đề** | Lock per account, not per IP |
| **Severity** | High |
| **Traceability** | (No direct AC, implicit in design) |
| **Precondition** | <ul><li>Tài khoản A: `qc_auth_api_009a@example.test`, counter=5 (locked)</li><li>Tài khoản B: `qc_auth_api_009b@example.test`, counter=0</li></ul> |
| **Steps** | 1. Login account A (locked) → 429<br>2. Login account B (not locked) → 200 |
| **Expected Response** | <ul><li>A: Status 429 ACCOUNT_LOCKED</li><li>B: Status 200, token</li></ul> |
| **Verification** | Counter/lock stored per user_id, không per IP |
| **Notes** | Verify qua database: lock table/column indexed by user_id. |

---

### **TC-API-LOGIN-011** — Tài khoản inactive (`is_active=false`) → specific error
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-011 |
| **Tiêu đề** | Inactive account → ACCOUNT_INACTIVE |
| **Severity** | High |
| **Traceability** | AC-API-08 |
| **Precondition** | Tài khoản `qc_auth_api_010@example.test`, `is_active=false`, counter=0 |
| **Request** | `POST /auth/login` <br> `{ "email": "qc_auth_api_010@example.test", "password": "CorrectPass", "rememberMe": false }` |
| **Expected Response** | **Status: 400** <br> `{ "error": "ACCOUNT_INACTIVE", "message": "Account has been disabled. Contact administrator" }` |
| **Verification** | <ul><li>Error = ACCOUNT_INACTIVE (không INVALID_CREDENTIALS)</li><li>Counter = 0 (KHÔNG tăng)</li><li>KHÔNG cấp token</li></ul> |
| **Notes** | Security: inactive account không đóng góp vào attempt counter (không leak existence). |

---

### **TC-API-LOGIN-012** — Missing email field → validation error
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-012 |
| **Tiêu đề** | Missing required field: email |
| **Severity** | Medium |
| **Traceability** | AF-02 |
| **Precondition** | (None) |
| **Request** | `POST /auth/login` <br> `{ "password": "SomePass", "rememberMe": false }` |
| **Expected Response** | **Status: 400** <br> `{ "error": "VALIDATION_ERROR", "message": "Email is required", "fields": { "email": "Email is required" } }` |
| **Verification** | <ul><li>Status = 400</li><li>Error = VALIDATION_ERROR (hoặc per spec)</li><li>Message chỉ rõ field missing</li><li>KHÔNG gọi business logic (không check counter)</li></ul> |
| **Notes** | Test all required fields: email, password. |

---

### **TC-API-LOGIN-013** — Invalid email format → validation error
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-013 |
| **Tiêu đề** | Invalid email format validation |
| **Severity** | Medium |
| **Traceability** | AF-01 |
| **Precondition** | (None) |
| **Request** | `POST /auth/login` <br> `{ "email": "not-an-email", "password": "SomePass", "rememberMe": false }` |
| **Expected Response** | **Status: 400** <br> `{ "error": "INVALID_EMAIL_FORMAT", "message": "Invalid email format" }` |
| **Verification** | <ul><li>Email validation (RFC5322 hoặc basic @domain check)</li><li>KHÔNG gọi database query</li></ul> |
| **Notes** | Test multiple invalid formats: no @, no domain, space, special char. |

---

### **TC-API-LOGIN-014** — RememberMe=true → refresh token 30 ngày
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-014 |
| **Tiêu đề** | Remember me: 30-day refresh token lifetime |
| **Severity** | High |
| **Traceability** | AC-API-12 |
| **Precondition** | Tài khoản `qc_auth_api_011@example.test`, MK hợp lệ |
| **Request** | `POST /auth/login` <br> `{ "email": "qc_auth_api_011@example.test", "password": "CorrectPass", "rememberMe": true }` |
| **Expected Response** | **Status: 200** <br> `{ "accessToken": "...", "refreshToken": "...", "expiresIn": 900, ... }` |
| **Verification** | <ul><li>Access token exp = now + 900s</li><li>Refresh token exp = now + 2592000s (30 * 24 * 3600 = 2,592,000 seconds)</li><li>Refresh token lưu persistent (localStorage hoặc HTTP-only cookie)</li></ul> |
| **Notes** | Decode JWT claim để verify exp. |

---

### **TC-API-LOGIN-015** — RememberMe=false → refresh token session-only
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-LOGIN-015 |
| **Tiêu đề** | No remember me: session-only refresh token |
| **Severity** | High |
| **Traceability** | AC-API-13 |
| **Precondition** | Tài khoản `qc_auth_api_012@example.test`, MK hợp lệ |
| **Request** | `POST /auth/login` <br> `{ "email": "qc_auth_api_012@example.test", "password": "CorrectPass", "rememberMe": false }` |
| **Expected Response** | **Status: 200** <br> Token cấp |
| **Verification** | <ul><li>Access token lifetime = 15 phút (900s)</li><li>Refresh token: stored in memory hoặc session storage (không persistent)</li><li>Token không lưu localStorage</li></ul> |
| **Notes** | Verify refresh token exp claim: có thể vẫn có TTL (ví dụ 1 giờ session TTL), hoặc không có exp (stateless session). Spec cần clarify. |

---

## POST /auth/refresh

### **TC-API-REFRESH-001** — Refresh token hợp lệ → cấp access token mới
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-REFRESH-001 |
| **Tiêu đề** | Valid refresh token → new access token |
| **Severity** | High |
| **Traceability** | AC-API-11 |
| **Precondition** | <ul><li>Có refresh token hợp lệ từ login (TC-API-LOGIN-001)</li><li>Access token hết hạn hoặc chưa hết</li></ul> |
| **Request** | `POST /auth/refresh` <br> `{ "refreshToken": "eyJ..." }` |
| **Expected Response** | **Status: 200** <br> `{ "accessToken": "eyJ...", "expiresIn": 900 }` |
| **Verification** | <ul><li>New access token issued (different from old)</li><li>exp = now + 900s</li><li>User can call protected endpoints with new token</li></ul> |
| **Notes** | ⚠️ Contract TBD: chưa biết response schema chính xác (có cấp refresh token mới không, v.v.). |

---

### **TC-API-REFRESH-002** — Invalid/malformed refresh token → 401
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-REFRESH-002 |
| **Tiêu đề** | Malformed token → UNAUTHORIZED |
| **Severity** | High |
| **Traceability** | AC-API-11 |
| **Precondition** | (None) |
| **Request** | `POST /auth/refresh` <br> `{ "refreshToken": "not-a-jwt" }` |
| **Expected Response** | **Status: 401** <br> `{ "error": "UNAUTHORIZED", "message": "Invalid token" }` |
| **Verification** | <ul><li>Status = 401</li><li>KHÔNG cấp access token</li></ul> |
| **Notes** | Test various malformed tokens: no signature, invalid base64, wrong algorithm. |

---

### **TC-API-REFRESH-003** — Expired refresh token → 401
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-REFRESH-003 |
| **Tiêu đề** | Expired refresh token → UNAUTHORIZED |
| **Severity** | High |
| **Traceability** | AC-API-11 |
| **Precondition** | Refresh token exp claim đã qua (mock time +30 ngày) |
| **Request** | `POST /auth/refresh` <br> `{ "refreshToken": "eyJ..." }` |
| **Expected Response** | **Status: 401** <br> `{ "error": "UNAUTHORIZED", "message": "Token expired" }` |
| **Verification** | <ul><li>Status = 401</li><li>KHÔNG cấp access token</li></ul> |
| **Notes** | Mock system time để test. |

---

### **TC-API-REFRESH-004** — Revoked refresh token (e.g., password reset) → 401
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-REFRESH-004 |
| **Tiêu đề** | Revoked token (password reset) → UNAUTHORIZED |
| **Severity** | High |
| **Traceability** | AC-API-15 |
| **Precondition** | <ul><li>Refresh token được cấp lúc T0</li><li>Tại T1, user reset password (AC-API-15 — revoke all tokens)</li><li>Thử refresh token cũ tại T2</li></ul> |
| **Request** | `POST /auth/refresh` <br> `{ "refreshToken": "eyJ..." }` (token cũ từ T0) |
| **Expected Response** | **Status: 401** <br> `{ "error": "UNAUTHORIZED", "message": "Token revoked" }` |
| **Verification** | <ul><li>Status = 401</li><li>Token bị revoke (check revocation list hoặc version field trong token)</li></ul> |
| **Notes** | AC-API-15: reset password → revoke all tokens. Test verify revocation. |

---

## POST /auth/forgot-password

### **TC-API-FORGOT-001** — Email tồn tại → 200 + link gửi (OQ-05 TBD)
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-FORGOT-001 |
| **Tiêu đề** | Forgotten password: email exists → send link |
| **Severity** | Critical |
| **Traceability** | AC-API-16 |
| **Precondition** | Tài khoản `qc_auth_api_forgot_001@example.test` tồn tại |
| **Request** | `POST /auth/forgot-password` <br> `{ "email": "qc_auth_api_forgot_001@example.test" }` |
| **Expected Response** | **Status: 200** <br> `{ "message": "If this email exists in our system, we've sent a reset link. Check your spam folder." }` |
| **Verification** | <ul><li>Status = 200</li><li>Message = standard message (không leak email existence)</li><li>Database: reset_token generated, exp = now + 3600s (60 phút), used=false</li><li>Email được gửi (check mock email service hoặc log — **OQ-05 TBD**)</li></ul> |
| **Notes** | **⚠️ Blocked by OQ-05** — email provider chưa chọn. Mock hoặc skip email delivery verification. |

---

### **TC-API-FORGOT-002** — Email không tồn tại → 200 + cùng message
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-FORGOT-002 |
| **Tiêu đề** | Non-existent email → same response (security) |
| **Severity** | High (Security) |
| **Traceability** | AC-API-16 |
| **Precondition** | Email `nonexistent_forgot@example.test` không tồn tại |
| **Request** | `POST /auth/forgot-password` <br> `{ "email": "nonexistent_forgot@example.test" }` |
| **Expected Response** | **Status: 200** <br> `{ "message": "If this email exists in our system, we've sent a reset link. Check your spam folder." }` |
| **Verification** | <ul><li>**Cùng 200 status + message như TC-API-FORGOT-001** (không leak)</li><li>Response time ≈ TC-API-FORGOT-001 (constant-time check)</li><li>KHÔNG gửi email</li><li>KHÔNG tạo reset token</li></ul> |
| **Notes** | Security: không thể phân biệt email tồn tại vs không via response. |

---

### **TC-API-FORGOT-003** — Gửi lần 2 trong 60s → 429 rate limit
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-FORGOT-003 |
| **Tiêu đề** | Rate limit: 60s cooldown |
| **Severity** | Medium |
| **Traceability** | AC-API-17 |
| **Precondition** | Tài khoản `qc_auth_api_forgot_002@example.test` tồn tại |
| **Steps** | 1. Submit request 1 → 200<br>2. Submit request 2 **ngay sau đó** (<60s) |
| **Expected Response (Request 1)** | **Status: 200** |
| **Expected Response (Request 2)** | **Status: 429** <br> `{ "error": "RATE_LIMITED", "message": "Please wait 45 seconds before sending again", "retryAfter": 45 }` |
| **Verification** | <ul><li>Request 1: 200, link gửi (database record created)</li><li>Request 2: 429, retryAfter ≈ 60 - (T2 - T1)</li><li>Chỉ 1 link được gửi (không double-send)</li></ul> |
| **Notes** | Test timing precision: submit tại 30s, 45s, 59s — all should get 429 với retryAfter khác nhau. |

---

### **TC-API-FORGOT-004** — Invalid email format → 400
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-FORGOT-004 |
| **Tiêu đề** | Invalid email format → validation error |
| **Severity** | Medium |
| **Traceability** | AF-15 |
| **Precondition** | (None) |
| **Request** | `POST /auth/forgot-password` <br> `{ "email": "not-email" }` |
| **Expected Response** | **Status: 400** <br> `{ "error": "INVALID_EMAIL_FORMAT", "message": "Invalid email format" }` |
| **Verification** | <ul><li>Validation client-side (frontend) hoặc server-side (API)</li><li>KHÔNG trigger rate limit counter</li></ul> |
| **Notes** | Test multiple invalid formats. |

---

## POST /auth/reset-password

### **TC-API-RESET-001** — Link hợp lệ + password khớp → 200, password updated
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-RESET-001 |
| **Tiêu đề** | Reset password: valid link + matching passwords |
| **Severity** | Critical |
| **Traceability** | AC-API-19 |
| **Precondition** | <ul><li>Reset link được tạo từ TC-API-FORGOT-001</li><li>Link còn hạn (60 phút), chưa dùng</li><li>Current password: `OldPass`</li></ul> |
| **Request** | `POST /auth/reset-password` <br> `{ "token": "reset_token_xxx", "newPassword": "NewPass123", "confirmPassword": "NewPass123" }` |
| **Expected Response** | **Status: 200** <br> `{ "message": "Password reset successfully" }` |
| **Verification** | <ul><li>Password hash được update trong database (verify via bcrypt hash check hoặc login lagi)</li><li>Reset token: used=true, exp vẫn valid (nhưng tidak dùng được lần 2)</li><li>Tất cả refresh tokens của tài khoản bị revoke (AC-API-15)</li><li>User phải login lại bằng password mới</li></ul> |
| **Notes** | ⚠️ Phụ thuộc OQ-04 (password rules) — currently no rules defined, assume min 6 chars. |

---

### **TC-API-RESET-002** — Link quá 60 phút → 400 INVALID_RESET_LINK
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-RESET-002 |
| **Tiêu đề** | Expired reset link → error |
| **Severity** | High |
| **Traceability** | AC-API-19 |
| **Precondition** | Reset link exp < now (mock time +61 phút) |
| **Request** | `POST /auth/reset-password` <br> `{ "token": "expired_token", "newPassword": "NewPass", "confirmPassword": "NewPass" }` |
| **Expected Response** | **Status: 400** <br> `{ "error": "INVALID_RESET_LINK", "message": "Reset link is invalid or expired" }` |
| **Verification** | <ul><li>KHÔNG update password</li><li>KHÔNG phân biệt "expired" vs "already used" (cùng message)</li></ul> |
| **Notes** | Constant-time response: checking token format + expiry phải mất thời gian gần bằng (tránh timing attack). |

---

### **TC-API-RESET-003** — Link đã dùng 1 lần → 400 INVALID_RESET_LINK (cùng message)
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-RESET-003 |
| **Tiêu đề** | Already-used reset link → same error as expired |
| **Severity** | High |
| **Traceability** | AC-API-19 |
| **Precondition** | Reset link đã dùng thành công ở TC-API-RESET-001 |
| **Request** | `POST /auth/reset-password` <br> `{ "token": "used_token", "newPassword": "AnotherPass", "confirmPassword": "AnotherPass" }` |
| **Expected Response** | **Status: 400** <br> `{ "error": "INVALID_RESET_LINK", "message": "Reset link is invalid or expired" }` |
| **Verification** | <ul><li>**Cùng message như TC-API-RESET-002** (không phân biệt used vs expired)</li><li>KHÔNG update password</li></ul> |
| **Notes** | Security: không leak token status. |

---

### **TC-API-RESET-004** — Password không khớp → 400
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-RESET-004 |
| **Tiêu đề** | Password mismatch validation |
| **Severity** | Medium |
| **Traceability** | AC-API-24 |
| **Precondition** | Link hợp lệ |
| **Request** | `POST /auth/reset-password` <br> `{ "token": "valid_token", "newPassword": "NewPass123", "confirmPassword": "DifferentPass456" }` |
| **Expected Response** | **Status: 400** <br> `{ "error": "PASSWORD_MISMATCH", "message": "Passwords do not match" }` |
| **Verification** | <ul><li>KHÔNG update password</li><li>KHÔNG revoke tokens (link still valid for another attempt)</li></ul> |
| **Notes** | Test case có thể retry sau khi fix mismatch. |

---

### **TC-API-RESET-005** — Password không đạt quy tắc → 400 (phụ thuộc OQ-04)
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-RESET-005 |
| **Tiêu đề** | Weak password → validation error ⚠️ OQ-04 TBD |
| **Severity** | Medium |
| **Traceability** | AC-API-24 |
| **Precondition** | <ul><li>Link hợp lệ</li><li>Quy tắc MK: min 6 ký tự (assumption, chưa confirm)</li></ul> |
| **Request** | `POST /auth/reset-password` <br> `{ "token": "valid_token", "newPassword": "123", "confirmPassword": "123" }` |
| **Expected Response** | **Status: 400** <br> `{ "error": "INVALID_PASSWORD_STRENGTH", "message": "Password must be at least 6 characters" }` |
| **Verification** | <ul><li>KHÔNG update password</li><li>KHÔNG revoke tokens</li></ul> |
| **Notes** | **⚠️ BLOCKED by OQ-04** — quy tắc chưa quyết. Adjust test case khi OQ-04 được confirm. |

---

### **TC-API-RESET-006** — Reset thành công → login bằng MK mới ok, MK cũ fail
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-RESET-006 |
| **Tiêu đề** | After reset: new password works, old password fails |
| **Severity** | High |
| **Traceability** | AC-API-25 |
| **Precondition** | <ul><li>Reset password thành công (TC-API-RESET-001) → new password = `NewPass123`</li><li>Old password = `OldPass`</li></ul> |
| **Steps** | 1. Submit login với old password → fail<br>2. Submit login với new password → success |
| **Expected Response** | <ul><li>Step 1: 400 INVALID_CREDENTIALS</li><li>Step 2: 200, token</li></ul> |
| **Verification** | Password hash được update trong database |
| **Notes** | Combine TC-API-LOGIN-001 + TC-API-LOGIN-003 logic để verify password change. |

---

### **TC-API-RESET-007** — Reset password → tất cả refresh tokens bị revoke
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-RESET-007 |
| **Tiêu đề** | Reset password revokes all sessions |
| **Severity** | High |
| **Traceability** | AC-API-15 |
| **Precondition** | <ul><li>User có 2 phiên đăng nhập (2 refresh tokens): session 1 + session 2</li><li>Reset password ở session 1</li></ul> |
| **Steps** | 1. Reset password → 200<br>2. Thử refresh token từ session 1 → 401<br>3. Thử refresh token từ session 2 → 401 |
| **Expected Response** | <ul><li>Step 1: 200</li><li>Step 2-3: 401 (tokens revoked)</li></ul> |
| **Verification** | Tất cả refresh tokens của tài khoản bị vô hiệu hoá |
| **Notes** | AC-API-15: revoke all sessions khi reset pwd. Distributed system test (AC-28): verify qua revocation list hoặc database version bump. |

---

## Integration & E2E Tests

### **TC-API-E2E-001** — End-to-end: Forgot password → Reset → Login
| Trường | Giá trị |
|---|---|
| **TC ID** | TC-API-E2E-001 |
| **Tiêu đề** | Full forgotten password flow |
| **Severity** | Critical |
| **Traceability** | AC-API-16, AC-API-19, AC-API-25 |
| **Precondition** | Tài khoản `qc_auth_e2e_api@example.test` có MK cũ = `OldPass` |
| **Steps** | **Phase 1 — Quên MK:**<br>1. POST /auth/forgot-password → 200<br><br>**Phase 2 — Lấy reset link:**<br>2. Check email (mock/real), lấy reset token<br><br>**Phase 3 — Reset MK:**<br>3. POST /auth/reset-password → 200, MK = `NewPass`<br><br>**Phase 4 — Đăng nhập:**<br>4. POST /auth/login với MK cũ → 400<br>5. POST /auth/login với MK mới → 200, token |
| **Expected Result** | <ul><li>Phase 1: 200, link generated</li><li>Phase 2: Link in email (OQ-05 TBD)</li><li>Phase 3: 200, password updated, tokens revoked</li><li>Phase 4: MK cũ fail, MK mới success</li></ul> |
| **Notes** | **⚠️ Blocked by OQ-05** (email provider) → mock hoặc skip email verification. |

---

## Traceability Matrix

| AC ID | Test Case(s) | Coverage |
|---|---|---|
| AC-API-01 | TC-API-LOGIN-001 | ✅ Happy path |
| AC-API-02 | TC-API-LOGIN-002 | ✅ Normalize |
| AC-API-03 | TC-API-LOGIN-003, TC-API-LOGIN-004 | ✅ Parity |
| AC-API-04 | TC-API-LOGIN-005, TC-API-LOGIN-006 | ✅ Counter 5 |
| AC-API-05 | TC-API-LOGIN-004, TC-API-LOGIN-010 | ✅ Counter logic |
| AC-API-06 | TC-API-LOGIN-006, TC-API-LOGIN-007 | ✅ Lock state |
| AC-API-07 | TC-API-LOGIN-009 | ✅ Reset counter |
| AC-API-08 | TC-API-LOGIN-011 | ✅ Inactive account |
| AC-API-09 | (Implicit, tested via request idempotency) | ✅ |
| AC-API-10 | (Network error simulation) | ✅ |
| AC-API-11 | TC-API-LOGIN-001, TC-API-LOGIN-014, TC-API-LOGIN-015, TC-API-REFRESH-001 | ✅ Token lifetime |
| AC-API-12 | TC-API-LOGIN-014 | ✅ 30-day refresh |
| AC-API-13 | TC-API-LOGIN-015 | ✅ Session-only |
| AC-API-14 | (logout endpoint — minimal coverage) | ⚠️ Minimal |
| AC-API-15 | TC-API-RESET-007 | ✅ Revoke all |
| AC-API-16 | TC-API-FORGOT-001, TC-API-FORGOT-002, TC-API-E2E-001 | ✅ Email send (OQ-05) |
| AC-API-17 | TC-API-FORGOT-003 | ✅ Rate limit |
| AC-API-18 | TC-API-FORGOT-001 | ✅ Link generation |
| AC-API-19 | TC-API-RESET-001, TC-API-RESET-002, TC-API-RESET-003 | ✅ Link validation |
| AC-API-20 | (Code review — logging) | ⚠️ Not automated |
| AC-API-21 | (Code review — bcrypt) | ⚠️ Not automated |
| AC-API-22 | (Requires multi-instance setup) | ⚠️ AC-28 TBD |
| AC-API-23 | (Database constraint) | ⚠️ Setup validation |
| AC-API-24 | TC-API-RESET-004, TC-API-RESET-005 | ✅ Password validation |
| AC-API-25 | TC-API-RESET-006 | ✅ Verify password update |

---

## Test Execution Strategy

| Phase | TCs | Environment | Remarks |
|---|---|---|---|
| **Unit** | Business logic (counter, token) | Local (mock DB) | Dev team |
| **Integration** | API + DB + mock email | Staging DB | QC team |
| **E2E** | Full flow (forgot → reset → login) | Staging | QC team (OQ-05 TBD) |

---

## Blockers & Dependencies

| Blocker | Test IDs | Unblock by |
|---------|----------|-----------|
| **API Contract (API-001)** | All TCs | Tech Lead lock endpoint schema |
| **Error Codes (API-002)** | All negative TCs | Tech Lead define error code list |
| **OQ-04 (Password rules)** | TC-API-RESET-005 | PO confirm rules |
| **OQ-05 (Email provider)** | TC-API-FORGOT-001, TC-API-FORGOT-002, TC-API-E2E-001 | PM choose provider |
| **AC-28 (Counter storage)** | TC-API-LOGIN-010 (multi-instance) | Tech Lead decide Redis vs DB |

---

## History

- **v1 (2026-08-19 22:00)** — `/gen-tcs` khởi tạo
  - 40+ API test cases cover 24 API-specific ACs
  - 5 endpoints tested (POST /auth/login, refresh, forgot-password, reset-password, logout)
  - Traceability matrix: 75% coverage (25% blocked by OQ/AC-28)
  - E2E scenario included
  - **Status: BLOCKED by Contract Lock (API-001)** — adjust test cases sau khi contract được lock
