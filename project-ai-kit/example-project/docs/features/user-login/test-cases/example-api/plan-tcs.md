# Test Case Implementation Plan: User Login — example-api

**Input:** `analysis.md` (24 API-specific ACs, 6 endpoints, error codes)  
**Output:** Endpoint decomposition + Strategy + Test Technique

---

## Endpoint Test Strategy

### **Endpoint 1: POST /auth/login**

**Purpose:** Xác thực email + password, cấp token

**Request Schema (dự kiến):**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "rememberMe": false
}
```

**Response Schema (dự kiến, 200):**
```json
{
  "accessToken": "eyJhbGc...",
  "refreshToken": "eyJhbGc...",
  "expiresIn": 900,
  "user": {
    "id": "123",
    "email": "user@example.com",
    "isActive": true
  }
}
```

**Strategy Summary:**

| Test Dimension | Technique | Coverage |
|---|---|---|
| **Happy Path** | Email + pwd đúng, active, không lock → 200, token cấp | AC-API-01 |
| **Email Normalization** | Request: `  USER@EXAMPLE.COM  ` → backend normalize → xác thực ok | AC-API-02 |
| **Email/Password Security** | Email sai vs pwd sai → **cùng error message + code** (constant-time response) | AC-API-03 |
| **Attempt Counter** | Sai 1-4 lần: 400 + message; lần 5: 429 (locked) | AC-API-04, AC-API-05 |
| **Counter Reset** | Thành công login → counter = 0 | AC-API-07 |
| **Lock State** | Counter = 5 → 429, kèm retry-after (seconds) | AC-API-06 |
| **Inactive Account** | is_active = false → 400 + specific message (không tăng counter) | AC-API-08 |
| **Request Validation** | Missing fields (email, password) → 400 | AF-02 |
| **Email Format** | Invalid email → 400 (email validation) | AF-01 |
| **Token Format** | Response access token = valid JWT (algorithm, claims, signature) | AC-API-24 |
| **Token Lifetime** | Access token exp claim = now + 900s (15 phút) | AC-API-11 |
| **Remember Me** | rememberMe=true → refresh token lifetime = 30d; false → session-only | AC-API-12, AC-API-13 |
| **Idempotency** | Submit cùng request 2 lần → 2 tokens khác nhau (không cache) | AC-API-09 |
| **Network Error** | Server 5xx → return 500 (hoặc 503) | AC-API-10 |

**Risk Level per Field:**

| Field | Type | Risk | Rationale |
|---|---|---|---|
| email | string | **High** | Security: normalization, leak prevention |
| password | string | **High** | Security: counter, attempt limit |
| rememberMe | boolean | **High** | Token lifetime logic affects session |

---

### **Endpoint 2: POST /auth/refresh**

**Purpose:** Làm mới access token (dùng refresh token cũ)

**Request Schema:**
```json
{
  "refreshToken": "eyJhbGc..."
}
```

**Response Schema (200):**
```json
{
  "accessToken": "eyJhbGc...",
  "expiresIn": 900
}
```

**Strategy Summary:**

| Test Dimension | Technique | Coverage |
|---|---|---|
| **Happy Path** | Valid refresh token → 200, new access token | AC-API-11 |
| **Invalid Token** | Malformed JWT → 401 UNAUTHORIZED | AC-API-11 |
| **Expired Token** | Refresh token hết hạn → 401 | AC-API-11 |
| **Revoked Token** | Refresh token bị revoke (đổi pwd) → 401 | AC-API-14, AC-API-15 |
| **Token Rotation** | Cấp access token mới, refresh token **có thay đổi không?** (OQ) | Depends on design |
| **Idempotency** | Submit 2 lần → 2 access token khác nhau (stateless) | Stateless design |

---

### **Endpoint 3: POST /auth/logout**

**Purpose:** Logout (revoke refresh token)

**Request Schema:**
```json
{
  "refreshToken": "eyJhbGc..."
}
```

**Response Schema (200):**
```json
{
  "message": "Logged out successfully"
}
```

**Strategy Summary:**

| Test Dimension | Technique | Coverage |
|---|---|---|
| **Happy Path** | Valid refresh token → 200, token revoked | AC-API-14 |
| **Invalid Token** | Malformed JWT → 401 | AC-API-14 |
| **Already Revoked** | Token đã revoked trước đó → 401 hoặc 200? (design TBD) | Edge case |

---

### **Endpoint 4: POST /auth/forgot-password**

**Purpose:** Gửi reset link (chỉ nếu email tồn tại, không leak)

**Request Schema:**
```json
{
  "email": "user@example.com"
}
```

**Response Schema (200, luôn cùng message):**
```json
{
  "message": "If this email exists, we've sent a reset link. Check your spam folder."
}
```

**Strategy Summary:**

| Test Dimension | Technique | Coverage |
|---|---|---|
| **Happy Path** | Email tồn tại → 200, link được gửi (OQ-05 TBD) | AC-API-16 |
| **Non-existent Email** | Email không tồn tại → **cùng 200 + message** (BR-10) | AC-API-16 (security) |
| **Rate Limit** | 2 lần gửi trong 60s → lần 2: 429 + retry-after | AC-API-17 |
| **Email Format** | Invalid email → 400 | AF-15 |
| **Link Generation** | Email được gửi → link hợp lệ 60p, dùng 1 lần | AC-API-18 |
| **Constant-time Response** | Email-exists vs not-exists → response time gần bằng (tránh timing attack) | Security |
| **Email Delivery** | ⚠️ OQ-05 — mock email hoặc skip end-to-end | Blocker |

---

### **Endpoint 5: POST /auth/reset-password**

**Purpose:** Đặt mật khẩu mới (xác thực link)

**Request Schema:**
```json
{
  "token": "reset_token_xxx",
  "newPassword": "NewPass123",
  "confirmPassword": "NewPass123"
}
```

**Response Schema (200):**
```json
{
  "message": "Password reset successfully"
}
```

**Strategy Summary:**

| Test Dimension | Technique | Coverage |
|---|---|---|
| **Happy Path** | Link valid + pwd khớp + pass rules → 200, pwd updated, all tokens revoked | AC-API-19 |
| **Invalid Link** | Token malformed/invalid → 400 INVALID_RESET_LINK | AC-API-19 |
| **Expired Link** | Token hết hạn (>60 phút) → 400 INVALID_RESET_LINK (không phân biệt expired vs used) | AC-API-19 |
| **Used Link** | Token đã dùng trước đó → 400 INVALID_RESET_LINK (cùng message như expired) | AC-API-19 |
| **Password Mismatch** | newPassword != confirmPassword → 400 | AC-API-24 |
| **Weak Password** | Password không đạt quy tắc (OQ-04 TBD) → 400 INVALID_PASSWORD_STRENGTH | AC-API-24 |
| **Session Revocation** | Refresh token của tài khoản bị vô hiệu → logout all sessions | AC-API-15 |
| **Consistency** | Sau reset, login bằng pwd mới → success; pwd cũ → fail | AC-API-25 |
| **Distributed Lock** | Multiple instances: reset token dùng 1 lần (AC-28 TBD) | Race condition |

**Risk Level:**
- **High:** Token validation, password update transaction, session revocation across instances
- **Medium:** Link expiry handling, password strength validation

---

## Test Scenario Matrix (per Endpoint)

### **Matrix: /auth/login**

| Scenario | Input | Expected HTTP | Expected Error Code | Risk | TC Count |
|----------|-------|---|---|---|---|
| Email đúng + pwd đúng + active + not locked | Standard valid | 200 | N/A | Low | 1 |
| Email normalized (uppercase/space) + pwd đúng | `  USER@EXAMPLE.COM  ` | 200 | N/A | Medium | 1 |
| Email sai hoặc pwd sai | Any | 400 | INVALID_CREDENTIALS | High | 2 |
| Sai pwd lần 1-4 | Counter <5 | 400 | INVALID_CREDENTIALS | High | 4 |
| Sai pwd lần 5 | Counter = 5 | 429 | (locked, retry-after) | High | 1 |
| During lock, nhập đúng | Counter locked | 429 | (locked) | High | 1 |
| After lock expire | Counter unlocked | 200 | N/A | High | 1 |
| Account inactive | is_active=false | 400 | ACCOUNT_INACTIVE | Medium | 1 |
| Missing email | - | 400 | (validation) | Low | 1 |
| Missing password | - | 400 | (validation) | Low | 1 |
| Invalid email format | No @ | 400 | INVALID_EMAIL_FORMAT | Low | 1 |
| **Total** | — | — | — | — | **15** |

---

## Technology & Test Approach

**Framework:** NestJS + TypeORM + PostgreSQL

**Test Layers:**
1. **Unit Test** (Dev) — Business logic (counter logic, token generation)
2. **Integration Test** (QC + Dev) — API endpoint + DB + mock email
3. **E2E Test** (QC) — Full flow: login → token → refresh → logout

**Test Technique Toolset:**

| Technique | Endpoint | Tool |
|---|---|---|
| API call + assertion | All | Postman / REST Client / curl |
| JWT decode + validation | /auth/login, /auth/refresh | jwt.io hoặc JWT library |
| Database state check | All | SQL query (counter, user, session) |
| Time-based test | /auth/forgot-password (60s), /auth/reset-password (60p link) | System time mock hoặc sleep |
| Race condition | /auth/reset-password (token used once across instances) | Load test tool hoặc script parallel request |
| Email mock | POST /auth/forgot-password | Mailinator, mailtrap, hoặc server log |
| Network error simulation | All | Postman mock server hoặc proxy throttle |
| Rate limit test | /auth/forgot-password | Timing script, repeat in <60s |

---

## Risk-Based Testing Priority

### **Critical (Must-test immediately):**
1. ✅ Login happy path (200 token)
2. ✅ Attempt counter (1-5 attempts → lock)
3. ✅ Email/password parity (security)
4. ✅ Reset password flow (token validation)

### **High (Should-test before release):**
- Normalization (email lowercase + trim)
- Account status checks (active, locked, inactive)
- Token validation + lifetime
- Session revocation on password reset

### **Medium (Nice-to-test):**
- Rate limit precision (60s exact)
- Race condition on token single-use
- Network error resilience

---

## Implementation Blockers

| Blocker | Status | Impact |
|---------|--------|--------|
| **Contract Lock** | ⚠️ **TBD** | Cannot finalize request/response schema, error codes |
| **OQ-01 — Email Migration** | **TBD** | Database setup, email unique constraint |
| **OQ-04 — Password Rules** | **TBD** | Password strength validation logic |
| **OQ-05 — Email Provider** | **TBD** | Email delivery test |
| **AC-28 — Counter Storage** | **TBD** | Redis vs DB decision affects test approach |
| **Figma Design** | N/A | Not applicable for API |

---

## History

- **v1 (2026-08-19 21:00)** — `/plan-tcs` khởi tạo
  - 5 endpoints decomposed (6th endpoint not needed for auth only)
  - Test matrix: 15 scenarios for /auth/login
  - Risk assessment per endpoint + field
  - Technology stack + toolset identified
  - Blockers documented (Contract Lock, OQ-01, OQ-04, OQ-05, AC-28)
