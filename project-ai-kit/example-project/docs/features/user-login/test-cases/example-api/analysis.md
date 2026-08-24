# Requirements Analysis: User Login — example-api (REST API)

## Summary

**Tính năng:** REST API endpoints cho luồng đăng nhập + quên mật khẩu

**Mục đích nghiệp vụ:**
- Hỗ trợ Web UI (example-web) + Mobile app (future)
- Xác thực email + password + phiên quản lý
- Chống dò mật khẩu (counter per account)
- Token-based authentication (JWT hoặc tương đương)

**Endpoints cần (từ SPEC.md § Phạm vi, chưa chốt chi tiết):**
1. `POST /auth/login` — Đăng nhập email + password
2. `POST /auth/refresh` — Làm mới access token (dùng refresh token)
3. `POST /auth/logout` — Logout (revoke session)
4. `POST /auth/forgot-password` — Yêu cầu reset link (gửi email)
5. `POST /auth/reset-password` — Đặt lại mật khẩu qua link
6. `POST /auth/verify-reset-link` — Kiểm tra link còn hạn (optional)

**API Contract:** ⚠️ **CHƯA LOCK** — SPEC ghi "CẦN Contract Lock trước Phase 3"

**Actors:**
- Client: example-web (FE), example-mobile (sau này)
- Service: Email provider (OQ-05 chưa quyết)
- Database: PostgreSQL (email unique, counter per account)

**Luồng chính:**
1. **Login:** Email + pwd → validate → cấp access token (15p) + refresh token (30d hoặc session)
2. **Forgot:** Email → generate link (60p, 1 lần dùng) → gửi email → user mở link → reset pwd
3. **Refresh:** Old access token + refresh token → cấp access token mới
4. **Logout:** Revoke refresh token (optional)

**Scope:**
- ✅ Email lowercase + trim (backend)
- ✅ Counter sai mật khẩu (per account, persistent — Redis hoặc DB)
- ✅ Khoá 15 phút khi counter=5
- ✅ Reset link generation + expiry (60p)
- ✅ Token management (15p access, 30d refresh)
- ✅ Session revocation (đổi/reset pwd)
- ✅ Error handling (4xx, 5xx)
- ❌ OTP/SMS, 2FA, IP-based block, device management, multi-tenancy

**Phụ thuộc:**
- API Contract chưa lock (request/response schema, error codes)
- Email provider chưa chọn (OQ-05)
- Database schema migration (email unique — OQ-01)
- Counter storage strategy: Redis vs PostgreSQL (AC-28 TBD)

---

## Q&A — Ambiguities

| ID | Reference | Endpoint | Câu hỏi + Đề xuất | Ảnh hưởng | Severity | Status |
|----|-----------|----------|---|---|---|---|
| **OQ-01** | Precondition, Email unique | POST /auth/login | **Migrate 180 tài khoản → email duy nhất?** <br> Cách migrate email từ `employee_profiles` → `users.email` | Chặn Phase 1 | High | TBD |
| **OQ-04** | Password validation | POST /auth/reset-password | **Quy tắc MK mới?** (độ dài, loại ký tự) | Error validation logic | High | TBD |
| **OQ-05** | HP-B, Link gửi | POST /auth/forgot-password | **Nhà cung cấp email?** | Chặn end-to-end test, không test email delivery | High | TBD |
| **API-001** | Contract | All | **Request/response schema chưa định** (JSON format, field name, data type) | Chặn API test, FE integration | Critical | **TBD** |
| **API-002** | Error handling | All | **Error codes chưa định** (401, 400, 429 cho rate limit, v.v.) | Test case negative không biết expect gì | Critical | **TBD** |
| **API-003** | Counter storage | POST /auth/login | **Counter sai MK lưu ở đâu?** (Redis hoặc DB) | AC-28 implementation | High | TBD |
| **API-004** | Token format | POST /auth/login | **Access token format?** (JWT, opaque, v.v.) Refresh token lưu ở đâu? | Test payload parsing | High | TBD |
| **API-005** | Rate limit | POST /auth/forgot-password | **60s cooldown enforce ở BE hay FE?** Nếu BE, API return 429 hay 400? | Error code test | Medium | TBD |
| **API-006** | Session revocation | POST /auth/reset-password | **Revoke all refresh tokens: sync qua các instance hay async?** Ảnh hưởng race condition | Distributed system test | Medium | TBD |

> **Status:** **TBD** = chưa được lock, chặn contract

---

## Acceptance Criteria (API-specific)

| AC ID | AC Content | Traceability | Status | Notes |
|-------|-----------|---|---|---|
| **AC-API-01** | POST /auth/login → email + pwd đúng + active + không lock → return access + refresh token | BR-01, AC-01 | **TBD** | Phụ thuộc API-001 (contract) |
| **AC-API-02** | Email input: lowercase + trim (backend xử lý) | BR-02, AC-02 | **TBD** | Request payload handling |
| **AC-API-03** | Email sai hoặc pwd sai → return **cùng một error message + code** (không phân biệt) | BR-11, AC-03 | **TBD** | Security: constant-time response |
| **AC-API-04** | Sai mật khẩu 5 lần → status code 429 (Too Many Requests) hoặc 400 + specific message? | BR-02, AC-04 | **TBD** | Phụ thuộc API-002 (error code) |
| **AC-API-05** | Counter sai tăng chỉ khi email tồn tại (không tăng nếu email sai) | AC-04 | **TBD** | Database logic |
| **AC-API-06** | Tài khoản locked → return error (kèm số phút còn lại nếu cần) | AC-06, BR-05 | **TBD** | Response format TBD |
| **AC-API-07** | Counter reset = 0 khi login thành công | BR-03, AC-07 | **TBD** | Database transaction |
| **AC-API-08** | is_active = false → specific error message (không tăng counter) | AC-09, BR-12 | **TBD** | Condition check order |
| **AC-API-09** | Mỗi request gọi 1 lần (idempotent nếu cần, hoặc check duplicate client-side) | AC-10 | **TBD** | Request handling strategy |
| **AC-API-10** | Network error (5xx) → return proper status (500, 503) | AC-11 | **TBD** | Error handling |
| **AC-API-11** | Access token lifetime = 15 phút (verify via exp claim trong JWT) | BR-06, AC-12 | **TBD** | Token config |
| **AC-API-12** | Refresh token lifetime = 30 ngày (nếu remember-me=true) | BR-06, AC-13 | **TBD** | Token config |
| **AC-API-13** | Refresh token session-only (không persistent) nếu remember-me=false | BR-07, AC-14 | **TBD** | Storage strategy |
| **AC-API-14** | POST /auth/logout → revoke refresh token | BR-08, AC-15 | **TBD** | Session management |
| **AC-API-15** | POST /auth/reset-password → revoke **all** refresh tokens của tài khoản | BR-08, AC-15 | **TBD** | Distributed system (AC-28) |
| **AC-API-16** | POST /auth/forgot-password → gửi email link (chỉ nếu email tồn tại, không leak) | BR-10, AC-17, AC-18 | **TBD** | Email provider (OQ-05) |
| **AC-API-17** | Gửi lại link trong 60s → return 429 (rate limit) | BR-13, AC-19 | **TBD** | Rate limit enforcement |
| **AC-API-18** | Reset link hạn 60 phút, dùng 1 lần | BR-09, AC-20 | **TBD** | Token generation + validation |
| **AC-API-19** | POST /auth/reset-password → verify link (đúng format, chưa expire, chưa dùng) | AC-21, AC-22 | **TBD** | Link validation logic |
| **AC-API-20** | Không log mật khẩu, access token, refresh token ở mọi mức | BR-15, AC-26 | **TBD** | Code review (logging config) |
| **AC-API-21** | Mật khẩu lưu bcrypt, không migrate hash | AC-27 | **TBD** | Code review |
| **AC-API-22** | Counter sync qua nhiều API instance (Redis hoặc DB lock) | AC-28 | **TBD** | Implementation (AC-003) |
| **AC-API-23** | Email unique: không tồn tại 2 tài khoản active cùng email | AC-30 | **TBD** | Database unique constraint |
| **AC-API-24** | Response format consistent (JSON, error structure, HTTP status code) | N/A | **TBD** | Contract (API-001) |

---

## Endpoints (dự kiến, chưa lock)

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| `POST` | `/auth/login` | Đăng nhập email + pwd | **TBD** |
| `POST` | `/auth/refresh` | Làm mới access token | **TBD** |
| `POST` | `/auth/logout` | Logout | **TBD** |
| `POST` | `/auth/forgot-password` | Gửi reset link | **TBD** |
| `POST` | `/auth/reset-password` | Đặt lại mật khẩu | **TBD** |
| `GET` | `/auth/me` (optional) | Lấy thông tin người dùng hiện tại | **TBD** |

---

## Error Codes (dự kiến, chưa lock)

| HTTP | Code | Message | Scenario |
|------|------|---------|----------|
| **200** | OK | Login successful, token returned | Happy path login |
| **400** | INVALID_CREDENTIALS | Email or password is incorrect | Email/pwd sai |
| **400** | ACCOUNT_LOCKED | Account locked for 15 minutes | Counter = 5 |
| **400** | ACCOUNT_INACTIVE | Account has been disabled | is_active = false |
| **400** | INVALID_EMAIL_FORMAT | Email format is invalid | Validation error |
| **400** | INVALID_RESET_LINK | Reset link is invalid or expired | Link hết hạn/used |
| **400** | PASSWORD_MISMATCH | Passwords do not match | Confirm MK != new MK |
| **400** | INVALID_PASSWORD_STRENGTH | Password does not meet requirements | MK không đạt quy tắc (OQ-04) |
| **401** | UNAUTHORIZED | Invalid or expired token | Token hết hạn, không refresh được |
| **403** | FORBIDDEN | Access denied | Permission check (future) |
| **429** | TOO_MANY_REQUESTS | Rate limit exceeded. Try again after 60 seconds | Forgot-password cooldown |
| **500** | INTERNAL_SERVER_ERROR | Server error | Lỗi server |

> **⚠️ TBD** — Error code chưa quyết (API-002), có thể thay đổi

---

## Technology Stack (từ stack-constraints.md)

| Layer | Tech |
|---|---|
| **API Framework** | NestJS |
| **Database** | PostgreSQL + TypeORM |
| **Auth Method** | JWT (hoặc tương đương) |
| **Password Hash** | bcrypt (không thay đổi) |
| **Email Service** | ⚠️ OQ-05 chưa chọn |
| **Session Storage** | ? Redis hoặc PostgreSQL (OQ-03 TBD) |

---

## Dependencies & Blockers

| Blocker | Impact | Unblock by |
|---------|--------|-----------|
| **Contract không lock** | FE/API integration test bị chặn | Tech Lead lock contract (request/response schema, error codes) |
| **OQ-01 — Email migration** | Database setup chưa xong | DBA hoặc BA confirm migration strategy |
| **OQ-05 — Email provider** | Email delivery test chưa thực hiện được | PM/Tech Lead chọn email provider |
| **AC-28 — Counter storage** | Implementation chưa rõ (Redis vs DB) | Tech Lead quyết kỹ thuật |
| **OQ-04 — Password rules** | Validation logic TBD | PO/Tech Lead confirm quy tắc |

---

## Notes cho `/plan-tcs`

1. Phân rã từng endpoint thành:
   - Happy path (200)
   - Negative path (400, 401, 429, 500)
   - Edge cases (boundary, race condition)
2. Test strategy: API unit test (mock DB) + integration test (real DB + mock email)
3. Counter sync test: simulate multiple instances (AC-28)
4. Token validation: verify JWT claims, lifetime, format
5. Rate limit test: timing precision (60s exact)
6. Email delivery: mock hoặc manual verification (OQ-05)

---

## History

- **v1 (2026-08-19 20:30)** — `/analyze-req` khởi tạo từ SPEC.md
  - 24 ACs API-specific mapped
  - 6 Endpoints listed (contract TBD)
  - 11 Error codes proposed (TBD)
  - 5 major blockers identified (Contract, OQ-01, OQ-04, OQ-05, AC-28)
  - **Status: BLOCKED** — chờ Contract Lock trước khi test
