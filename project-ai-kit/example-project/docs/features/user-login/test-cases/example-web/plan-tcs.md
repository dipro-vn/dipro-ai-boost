# Test Case Implementation Plan: User Login — example-web

**Input:** `analysis.md` (30 ACs, 6 OQs, 3 Screens)  
**Output:** Screen decomposition + Archetype + Strategy + Component Risk

---

## Screen Decomposition & Strategy

### **Screen 1: WB_AUTH_001 — Đăng nhập**

**Archetype:** Form (single-step login form)

**UI Components (phân rã từ mô tả SPEC):**
1. **Logo/Header** — Brand image
2. **Email Input** — Textbox, normalize (lowercase+trim), email format validation
3. **Password Input** — Textbox + password reveal toggle
4. **Remember Me Checkbox** — Checkbox "Ghi nhớ đăng nhập" (mặc định unchecked)
5. **Submit Button** — Primary button "Đăng nhập", loading state, disabled state
6. **Forgot Password Link** — Text link "Quên mật khẩu?"
7. **Form Error Banner** — Top alert (email sai hoặc MK sai — thông báo chung)
8. **Field Error (Email)** — Inline error dưới ô email (format error)
9. **Locked Account Message** — Specific error khi tài khoản bị khoá 15p (+ countdown)
10. **Server Error Banner** — Red banner khi 5xx/network error

**Strategy Summary:**

| Chỉ tiêu | Mô tả |
|---|---|
| **Happy Path** | Email hợp lệ + MK đúng + không bị khoá → đăng nhập thành công (AC-01, AC-02) |
| **Boundary: Login Lockout** | Sai MK 5 lần liên tiếp → khoá 15p (AC-04, AC-06); sai lần 5 vs 4: edge (AC-04); hết 15p nhập đúng → ok (AC-06); tiếp tục sai → ? (OQ-02 TBD) |
| **Email Security** | Sai email vs sai MK → cùng thông báo, KHÔNG leak (AC-03, BR-11) |
| **Account States** | `is_active=false` → specific message (AC-09); bị khoá → countdown (AC-06) |
| **Session State** | Tick "Ghi nhớ" → 30 ngày (AC-13); không tick → session-only (AC-14) |
| **Network Resilience** | 5xx/network error → banner, email preserved (AC-11) |
| **Client-side Validation** | Email format → error dưới ô (AF-01), không gọi API (AF-02 — bỏ trống) |
| **Normalization** | Email tự lowercase+trim (AC-02) — verify edge cases: double-space, mixed-case domain |
| **Double Submit** | Nút disable khi loading, chỉ 1 request gửi (AC-10) |
| **Redirect on Session Expiry** | Bị đá ra ở trang cụ thể → nhớ URL, sau login quay lại (AC-16) |

**Component Risk Assessment:**

| Component | Type | Risk | Rationale | TC Technique |
|---|---|---|---|---|
| Email Input | Textbox | **High** | Normalize (lowercase+trim) — edge case: unicode, mixed case | Boundary: normal, mixed-case, leading/trailing spaces, unicode, max-length |
| Password Input | Textbox | **High** | Sai 5 lần → khoá, core security feature | State machine: attempt counter 1→4→5; equivalence class (sai string khác nhau) |
| Remember Me | Checkbox | **Medium** | 2 state: 30 ngày vs session-only, ảnh hưởng token lifetime | Condition: checked vs unchecked, close browser test |
| Submit Button | Button | **High** | Loading state, disable, double-submit prevention | State: normal → loading → done; interaction: rapid clicks |
| Form Error Banner | Alert | **High** | Email sai vs MK sai = cùng thông báo (security) | Equivalence: email-error vs password-error, message parity |
| Forgot Password Link | Link | **Medium** | Navigation to WB_AUTH_002 | Positive: click works; precondition: form not submitted |
| Field Error (Email) | Inline error | **Medium** | Format validation (blur trigger) | Boundary: valid email, invalid format, edge case (+ vs .) |
| Locked Account Message | Modal/Alert | **High** | Countdown 15p real-time, không reload page | Real-time: verify countdown accuracy, across refresh |
| Password Reveal Toggle | Button/Icon | **Low** | UX: show/hide password | Positive: toggle works, password visible when toggled |
| Server Error Banner | Alert | **Medium** | 5xx/network → retry possible | Error: simulate 5xx, network timeout, verify email preserved |

---

### **Screen 2: WB_AUTH_002 — Quên mật khẩu (nhập email)**

**Archetype:** Form (single-field prompt)

**UI Components:**
1. **Back Button / Header** — Link/button quay lại đăng nhập
2. **Email Input** — Textbox, email format validation
3. **Submit Button** — "Gửi hướng dẫn", loading state, disabled state
4. **Countdown Timer** — 60s cooldown sau khi gửi (show remaining time)
5. **Success Message** — Thông báo khi gửi (luôn hiển thị, bất kể email tồn tại hay không)
6. **Field Error (Email)** — Inline error dưới ô email (format)
7. **Server Error Banner** — 5xx/network error

**Strategy Summary:**

| Chỉ tiêu | Mô tả |
|---|---|
| **Happy Path** | Email tồn tại → gửi email link (AC-18 phụ thuộc OQ-05) |
| **Security: Email Leak** | Email không tồn tại → **cùng thông báo như tồn tại** (AC-17, BR-10 — không gửi email) |
| **Rate Limit** | Gửi lần 2 trong 60s → bị chặn, hiển thị cooldown (AC-19, BR-13) |
| **Client-side Validation** | Email format → error dưới ô, không gọi API (AF-15) |
| **Email Normalization** | Normalize (lowercase+trim) như screen WB_AUTH_001 (AC-02) |
| **Link Validity** | Email link hợp lệ 60 phút, 1 lần dùng (AC-20) |

**Component Risk Assessment:**

| Component | Type | Risk | Rationale | TC Technique |
|---|---|---|---|---|
| Email Input | Textbox | **High** | Security: không leak email tồn tại, cần normalize | Equivalence: exists vs not-exists (thông báo giống); boundary: format |
| Submit Button | Button | **High** | Cooldown 60s, state transition | State: normal → loading → cooldown active → cooldown done |
| Countdown Timer | Timer | **Medium** | Real-time countdown, phải đồng bộ server time | Real-time: accuracy, across refresh, edge (59s, 60s, 61s) |
| Success Message | Alert | **High** | LUÔN hiển thị (email tồn tại hoặc không) — không query result leakage | Equivalence: email-exists vs not-exists → cùng message |
| Field Error (Email) | Inline error | **Low** | Format validation | Boundary: valid email, invalid format |
| Back Button | Link | **Low** | Navigate back | Positive: click works |

---

### **Screen 3: WB_AUTH_003 — Đặt mật khẩu mới**

**Archetype:** Form (multi-field password reset)

**UI Components:**
1. **Back Button / Close** — Optional, hoặc auto-redirect nếu link hết hạn
2. **New Password Input** — Textbox, password reveal toggle
3. **Confirm Password Input** — Textbox, password reveal toggle
4. **Password Strength Meter** — Progress bar (độ mạnh, color indicator)
5. **Password Hint Text** — Helper text mô tả quy tắc mật khẩu (phụ thuộc OQ-04)
6. **Submit Button** — "Đặt mật khẩu", loading state
7. **Link Validity Alert** — Nếu link hết hạn/đã dùng → thông báo + nút "Gửi lại"
8. **Success Message** — Thông báo ngắn "Đặt mật khẩu thành công"
9. **Field Error (Confirm)** — Inline error "Mật khẩu không khớp" dưới ô thứ 2
10. **Field Error (Password Strength)** — Inline error dưới ô 1 nếu MK không đạt quy tắc (phụ thuộc OQ-04)

**Strategy Summary:**

| Chỉ tiêu | Mô tả |
|---|---|
| **Happy Path** | Link hợp lệ → nhập MK mới (khớp) → đặt lại thành công → về màn đăng nhập (AC-20, AC-24) |
| **Link Validity** | Link 60p, 1 lần dùng → hết hạn/đã dùng = cùng thông báo (AC-21, AC-22) |
| **Password Rules** | Quy tắc MK chưa chốt (OQ-04) — base: tối thiểu 6 ký tự (hệ thống cũ) |
| **Match Validation** | 2 ô không khớp → lỗi dưới ô 2, không gọi API (AC-23) |
| **Session Revocation** | Đặt lại MK → thu hồi toàn bộ refresh token của tài khoản (AC-15, BR-08) |
| **No Auto-login** | Thành công → KHÔNG tự động đăng nhập, buộc đăng nhập lại bằng MK mới (AC-24, BR-14) |
| **Strength Meter** | Hiển thị độ mạnh MK, color indicator (phụ thuộc OQ-04 định quy tắc) |
| **Normalization** | Không normalize MK (khác email) — giữ nguyên case, space |

**Component Risk Assessment:**

| Component | Type | Risk | Rationale | TC Technique |
|---|---|---|---|---|
| Password Input 1 | Textbox | **High** | Quy tắc chưa chốt (OQ-04), cần test độ mạnh | Boundary: min-length (6 vs 7 nếu siết), special char, unicode |
| Password Input 2 | Textbox | **High** | Match validation, error dưới ô này | Equivalence: match vs not-match; boundary: empty, short, long |
| Password Strength Meter | Progress | **Medium** | Visual feedback, phụ thuộc quy tắc | State: empty → weak → fair → strong (phụ thuộc OQ-04) |
| Submit Button | Button | **High** | Loading state, success → no auto-login | State: normal → loading → done; redirect to login |
| Link Validity Alert | Modal/Alert | **High** | Hết hạn vs đã dùng = cùng thông báo (security) | Equivalence: expired vs used → cùng message; retry link generation |
| Confirm Password Input | Textbox | **High** | Match logic, non-matching handling | Equivalence: match vs not-match; boundary: empty, null, special char |
| Success Message | Alert | **Medium** | Thông báo ngắn, redirect | Positive: message shown, auto-redirect to login within X sec |
| Password Reveal Toggles | Button/Icon | **Low** | Show/hide password | Positive: toggle works for each field |

---

## Traceability: Screens ↔ ACs

| Screen | Key ACs | Technique |
|---|---|---|
| **WB_AUTH_001** | AC-01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16 | Boundary (attempt counter 1-5), Equivalence (email/pwd error), State Machine (lock/unlock), Real-time (countdown), Load (network resilience) |
| **WB_AUTH_002** | AC-17, 18, 19, 20 | Equivalence (email exists/not), Boundary (60s cooldown), Real-time (countdown), Rate limit |
| **WB_AUTH_003** | AC-20, 21, 22, 23, 24, 25 | Equivalence (link expired/used, pwd match/mismatch), Boundary (password rules - OQ-04), Real-time (link lifetime) |

---

## Risk-Based Testing Priority

### **Critical Path (Must-test):**
1. ✅ Login success happy path (AC-01, 02)
2. ✅ Login attempt counter & lockout (AC-04, 05, 06, 07)
3. ✅ Email vs password error parity (AC-03)
4. ✅ Remember me token lifetime (AC-13, 14)
5. ✅ Forgot password → link generation & validity (AC-20, 21, 22)
6. ✅ Session revocation on password reset (AC-15)

### **High-Risk Scenarios (Should-test):**
- Normalization edge cases: unicode, mixed-case domains
- Real-time countdown accuracy across browser refresh
- Network resilience: 5xx, timeout, email preservation
- Multi-device session revocation (AC-15)
- Account disabled state (AC-09)

### **Medium/Low Risk (Nice-to-test):**
- Password reveal toggle UX
- Link "Quên mật khẩu?" navigation
- Server error recovery

---

## Implementation Notes for `/gen-tcs`

| Note | Ảnh hưởng |
|---|---|
| **OQ-04 — Password Rules** | Thanh độ mạnh + quy tắc validation → SKIP test WB_AUTH_003 field strength cho đến khi PO confirm |
| **OQ-05 — Email Provider** | Link generation → mock email service hoặc skip end-to-end test cho đến khi provider được chọn |
| **Design pending** | Figma chưa có → các TC về UI state (Normal/Focus/Error/Loading/Disabled) sẽ có note "refine sau khi design" |
| **Countdown Timer** | Frontend vs Backend clock — cần verify implementation để chọn test technique (mock time vs real time) |
| **AC-28 (TBD)** | Counter sync across multiple API instances → phụ thuộc backend storage (Redis vs PostgreSQL) — skip cho đến xác định implementation |

---

## History

- **v1 (2026-08-19 19:30)** — `/plan-tcs` khởi tạo
  - 3 screens × 30+ components decomposed
  - Risk assessment + strategy per screen
  - Traceability AC ↔ Technique
  - Implementation blockers identified (OQ-04, OQ-05, design pending)
