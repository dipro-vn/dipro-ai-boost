# DESIGN: User Login — example-api (Backend)

> **Nguồn:** SPEC.md § Mô tả nghiệp vụ, Quy tắc nghiệp vụ (BR-01 → BR-15), Acceptance Criteria (AC-01 → AC-30), Alternative Flows (AF-01 → AF-23)
>
> **Status:** Ready for Phase 3 Contract Lock (endpoints, DTO, error codes)

---

## 1. Tổng quan thay đổi

### Phạm vi ảnh hưởng

| Layer | Module/File | Loại thay đổi |
|---|---|---|
| Entity | `src/modules/auth/entities/user.entity.ts` | Thêm cột `failed_login_attempts`, `locked_until` + cập nhật email thành unique |
| Entity | `src/modules/auth/entities/password-reset-token.entity.ts` | Thêm mới (token đặt lại mật khẩu) |
| Service | `src/modules/auth/auth.service.ts` | Thêm method: login, verify token, reset password, send reset email |
| Controller | `src/modules/auth/auth.controller.ts` | Thêm 5 endpoint mới (login, refresh, logout, forgot-password, reset-password) |
| Guard | `src/modules/auth/guards/jwt.guard.ts` | Sửa (xử lý refresh token, invalidate on password change) |
| Enum | `src/common/enums/error-codes.enum.ts` | Thêm error code mới cho auth scenarios |
| Module | `src/modules/auth/auth.module.ts` | Wire dependencies (bcrypt, JWT, email service) |

### Dependency mới

- **bcryptjs** — hash/verify mật khẩu (đã được use trong codebase cũ)
- **@nestjs/jwt** — JWT signing + verification (tiêu chuẩn NestJS)
- **nodemailer** hoặc **email service từ nhà cung cấp** (OQ-05 chưa chốt → placeholder để FE/Mobile có thể mock)
- **TypeORM QueryBuilder** — quản lý lock state trên multiple instances (AC-28)

---

## 2. Database Changes

### Entity: User (sửa)

**Tên entity:** `UserEntity`  
**Tên bảng:** `users` (giữ nguyên, KHÔNG đổi tên)

**Cột mới / thay đổi:**

| Cột | Kiểu | Null | Index | Mô tả |
|---|---|---|---|---|
| `id` | UUID | ✗ | PK | Giữ nguyên |
| `employee_code` | VARCHAR(20) | ✓ | Unique (sửa → nullable) | Nhân viên nội bộ; khách doanh nghiệp để NULL |
| `email` | VARCHAR(255) | ✗ | **Unique** (thêm) | Định danh đăng nhập thay thế employee_code (BR-01) |
| `password_hash` | VARCHAR(255) | ✗ | - | Giữ nguyên (không đổi hash algorithm → AC-27) |
| `is_active` | BOOLEAN | ✗ | - | Giữ nguyên; xác thực ở login (BR-12) |
| `failed_login_attempts` | INT | ✗ | - | Bộ đếm sai mật khẩu (mặc định 0) — sử dụng PostgreSQL instead Redis (OQ từ Tech Lead) |
| `locked_until` | TIMESTAMP(3) | ✓ | - | Thời điểm mở khoá tài khoản (hạn 15 phút từ lần sai thứ 5) (BR-02) |
| `last_login_at` | TIMESTAMP(3) | ✓ | - | Audit log (không bắt buộc trong SPEC nhưng hữu ích để debug AC-28) |
| `created_at` | TIMESTAMP(3) | ✗ | - | Giữ nguyên |
| `updated_at` | TIMESTAMP(3) | ✗ | - | Giữ nguyên |

**Migration:**

- **Migration name:** `<timestamp>-add-email-auth-to-users.ts`
- **Steps:**
  1. Thêm cột `email` (VARCHAR 255, UNIQUE, NOT NULL) — cần data migration cho 180 tài khoản cũ (OQ-01 chưa chốt)
  2. Thêm cột `failed_login_attempts` (INT, DEFAULT 0)
  3. Thêm cột `locked_until` (TIMESTAMP NULL)
  4. Sửa cột `employee_code` thành NULL (NULLABLE) nếu tương lai cho phép cả 2 loại định danh
  5. Tạo index unique trên `email`
  6. Tạo index trên `locked_until` (để query nhanh "tài khoản còn bị khoá không" — AC-05)

**Note:** Cột `password_hash` & `employee_code` & `is_active` **KHÔNG được đổi tên hay xóa** (AC-29).

### Entity: PasswordResetToken (mới)

**Tên entity:** `PasswordResetTokenEntity`  
**Tên bảng:** `password_reset_tokens`

**Cột:**

| Cột | Kiểu | Null | Index | Mô tả |
|---|---|---|---|---|
| `id` | UUID | ✗ | PK | |
| `user_id` | UUID | ✗ | FK (`users.id`) | Tài khoản muốn đặt lại MK |
| `token` | VARCHAR(255) | ✗ | **Unique** | Token SHA256(random) — dùng để nhận dạng link đặt lại |
| `expires_at` | TIMESTAMP(3) | ✗ | Index | Hạn 60 phút (BR-09) — delete tự động qua TTL hoặc cleanup job |
| `used_at` | TIMESTAMP(3) | ✓ | - | Khi link đã dùng 1 lần (BR-09, AF-19 = AF-22) |
| `created_at` | TIMESTAMP(3) | ✗ | - | Audit |

**Quan hệ:**
```typescript
@ManyToOne(() => UserEntity, { eager: false })
@JoinColumn({ name: 'user_id' })
user: UserEntity;
```

**Migration:**

- **Migration name:** `<timestamp>-create-password-reset-tokens.ts`
- Tạo bảng mới + FK + indexes

### Redis Cache (không dùng đợt này)

Theo Tech Lead note, dùng PostgreSQL thay vì Redis để:
- Không thêm infra mới
- Đảm bảo AC-28 (multiple instance consistency) via DB row-level locking
- Có audit trail (bộ đếm ghi vào DB, có thể trace logs)

---

## 3. API Definition

> **Source of truth cho Phase 3 Contract Lock** — FE/Mobile sẽ copy đúng DTO/error codes từ bảng này.

### Endpoint mới

| Method | Endpoint | Auth | Request | Response | Error codes |
|---|---|---|---|---|---|
| POST | `/api/auth/login` | Public | `{email, password, remember_me?}` | `{access_token, refresh_token, refresh_token_expires_at, user}` | 400, 401, 403, 429, 500 |
| POST | `/api/auth/refresh` | Public (refresh token) | `{refresh_token}` | `{access_token, refresh_token?}` | 401, 403 |
| POST | `/api/auth/logout` | JWT | `{}` (empty body) | `{message}` | 401 |
| POST | `/api/auth/forgot-password` | Public | `{email}` | `{message}` | 400, 429 |
| POST | `/api/auth/reset-password` | Public (reset token) | `{token, new_password, new_password_confirm}` | `{message}` | 400, 403 |

Chi tiết DTO, validation và business logic flow của từng endpoint ở dưới.

#### **POST** `/api/auth/login`

**Auth:** Public (không cần JWT)

**Request DTO:**

```typescript
class LoginDto {
  email: string;           // required, email format, tự lowercase + trim (BR-01)
  password: string;        // required, min 1 char (validation client-side)
  remember_me?: boolean;   // optional, default false (BR-07)
}
```

**Response DTO (success 200 OK):**

```typescript
class AuthTokenResponse {
  access_token: string;              // JWT exp: 15 min (BR-06)
  refresh_token: string;             // JWT exp: 30 days nếu remember_me=true, else session-only (BR-07)
  refresh_token_expires_at: number;  // Unix timestamp (ms) khi refresh hết hạn
  user: {
    id: string;
    email: string;
    employee_code?: string;          // nullable
    is_active: boolean;
  }
}
```

**Error responses:**

| Code | Message | Điều kiện |
|---|---|---|
| `400` | `{ error: 'INVALID_EMAIL_FORMAT' }` | Email không đúng format (AF-01) |
| `400` | `{ error: 'MISSING_REQUIRED_FIELD' }` | Email hoặc password bỏ trống (AF-02) |
| `401` | `{ error: 'INVALID_CREDENTIALS' }` | Sai email hoặc sai mật khẩu (AF-03, BR-11 — **cùng thông báo**) |
| `429` | `{ error: 'ACCOUNT_LOCKED', locked_until: <unix_ms>, remaining_minutes: <int> }` | Tài khoản bị khoá (AF-04, AF-05, BR-05) |
| `403` | `{ error: 'ACCOUNT_INACTIVE' }` | `is_active = false` (AF-08, BR-12) |
| `500` | `{ error: 'SERVER_ERROR' }` | Lỗi server (AF-09) |

**Validation (client-side để giảm traffic):**
- Email: không để trống, valid email format
- Password: không để trống
- Server-side: xử lý trim + lowercase email trước khi query DB

**Business logic flow:**
1. Email.toLowerCase().trim()
2. Query `UserEntity` by email
3. Nếu email không tồn tại → return 401 INVALID_CREDENTIALS (BR-11 — không leak existence)
4. Nếu `is_active = false` → return 403 ACCOUNT_INACTIVE, **không tăng bộ đếm** (AC-09)
5. Nếu `locked_until > now()` → return 429 ACCOUNT_LOCKED + remaining time (BR-05, AC-06)
6. Verify password hash bằng bcrypt
7. Nếu sai:
   - Tăng `failed_login_attempts` += 1
   - Nếu `failed_login_attempts >= 5` → set `locked_until = now + 15min` (BR-02)
   - Return 401 INVALID_CREDENTIALS
8. Nếu đúng:
   - Reset `failed_login_attempts = 0` (BR-03)
   - Set `last_login_at = now()`
   - Sinh access token (15 min exp)
   - Sinh refresh token:
     - Nếu `remember_me = true` → exp 30 days (BR-06, BR-07)
     - Nếu `remember_me = false` → **không store vào DB**, chỉ ghi trong response (session-only, BR-07)
   - Return 200 + tokens

**AC mapping:**
- AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-11

---

#### **POST** `/api/auth/refresh`

**Auth:** Public (dùng refresh token từ body/cookie, không cần JWT header)

**Request DTO:**

```typescript
class RefreshTokenDto {
  refresh_token: string;  // required
}
```

**Response DTO (success 200 OK):**

```typescript
class RefreshResponse {
  access_token: string;   // JWT exp: 15 min (BR-06)
  refresh_token?: string; // Chỉ sinh lại nếu cũ sắp hết hạn (tuỳ chọn)
}
```

**Error responses:**

| Code | Message | Điều kiện |
|---|---|---|
| `401` | `{ error: 'INVALID_REFRESH_TOKEN' }` | Token không đúng format, không tồn tại, hoặc đã hết hạn |
| `401` | `{ error: 'REFRESH_TOKEN_REVOKED' }` | Token đã bị thu hồi (do đổi MK — BR-08) |
| `403` | `{ error: 'ACCOUNT_INACTIVE' }` | Tài khoản bị vô hiệu hoá sau khi issue refresh token |

**Business logic flow:**
1. Verify refresh token signature (JWT)
2. Nếu hết hạn → 401 INVALID_REFRESH_TOKEN
3. Query `UserEntity` từ JWT claim user_id
4. Nếu tài khoản không tồn tại hoặc `is_active = false` → 403 ACCOUNT_INACTIVE (AF-12 → lấy từ session)
5. Sinh access token mới, return 200

**AC mapping:** AC-12, AC-14, AF-11, AF-12

---

#### **POST** `/api/auth/logout`

**Auth:** JWT (Bearer token)

**Request DTO:** Empty body (hoặc có thể accept optional tham số)

**Response DTO (success 200 OK):**

```typescript
class LogoutResponse {
  message: string;  // "Logged out successfully"
}
```

**Business logic flow:**
1. Extract user ID từ JWT
2. Invalidate refresh token (nếu FE trao refresh token trong body hoặc xóa từ storage)
3. Return 200

**Note:** Phía client sẽ xóa tokens khỏi storage; phía server chỉ cần acknowledge.

---

#### **POST** `/api/auth/forgot-password`

**Auth:** Public

**Request DTO:**

```typescript
class ForgotPasswordDto {
  email: string;  // required, email format
}
```

**Response DTO (success 200 OK):**

```typescript
class ForgotPasswordResponse {
  message: string;  // "Nếu email này có trong hệ thống, chúng tôi đã gửi hướng dẫn đặt lại mật khẩu. Kiểm tra cả hộp thư rác." (BR-10)
}
```

**Error responses:**

| Code | Message | Điều kiện |
|---|---|---|
| `400` | `{ error: 'INVALID_EMAIL_FORMAT' }` | Email không đúng format (AF-15) |
| `429` | `{ error: 'TOO_MANY_REQUESTS' }` | Gửi lại quá nhanh (< 60 giây — BR-13, AF-16) |

**Business logic flow:**
1. Validate email format
2. Kiểm tra rate limit per email (60 giây — BR-13, AF-16) → store vào DB hoặc cache
3. **LUÔN trả response cùng một thông báo** bất kể email tồn tại hay không (BR-10)
4. Nếu email tồn tại:
   - Tạo mới `PasswordResetTokenEntity` với:
     - token = SHA256(random)
     - expires_at = now + 60 min (BR-09)
     - used_at = NULL
   - Xây dựng reset link: `{FRONTEND_URL}/auth/reset-password?token={token}`
   - Gửi email (OQ-05: nhà cung cấp chưa chốt) → nhờ email service (service khác, service này chỉ sinh link)
5. Return 200 cùng thông báo

**AC mapping:** AC-17, AC-18, AC-19

**Note:** Cơ chế rate limit 60 giây (BR-13) có thể store ở:
- Option A: PostgreSQL bảng `email_rate_limit(email, last_sent_at)`
- Option B: In-memory + cleanup (nếu single instance)
- **Recommendation:** Bảng `email_rate_limit` để scale qua nhiều instance

---

#### **POST** `/api/auth/reset-password`

**Auth:** Public (dùng token từ link email)

**Request DTO:**

```typescript
class ResetPasswordDto {
  token: string;              // required, từ link email
  new_password: string;       // required
  new_password_confirm: string; // required
}
```

**Response DTO (success 200 OK):**

```typescript
class ResetPasswordResponse {
  message: string;  // "Mật khẩu đã được đặt lại thành công. Vui lòng đăng nhập lại."
}
```

**Error responses:**

| Code | Message | Điều kiện |
|---|---|---|
| `400` | `{ error: 'INVALID_TOKEN' }` | Token không tồn tại, không đúng format (AF-18, AF-19) |
| `400` | `{ error: 'TOKEN_EXPIRED' }` | Token hết hạn 60 phút (AF-18 — **cùng thông báo như AF-19**) |
| `400` | `{ error: 'TOKEN_ALREADY_USED' }` | Token đã dùng 1 lần (AF-19, BR-09) |
| `400` | `{ error: 'PASSWORDS_DONT_MATCH' }` | 2 ô mật khẩu không khớp (AF-20) |
| `400` | `{ error: 'INVALID_PASSWORD' }` | Mật khẩu không đạt quy tắc (AF-21 — OQ-04 chưa chốt) |
| `400` | `{ error: 'MISSING_REQUIRED_FIELD' }` | Token, new_password, new_password_confirm bỏ trống |
| `403` | `{ error: 'ACCOUNT_INACTIVE' }` | Tài khoản bị vô hiệu hoá |

**Business logic flow:**
1. Query `PasswordResetTokenEntity` by token
2. Nếu không tồn tại → 400 INVALID_TOKEN
3. Nếu `expires_at < now()` → 400 TOKEN_EXPIRED (AF-18, AF-19 cùng thông báo)
4. Nếu `used_at` không NULL → 400 TOKEN_ALREADY_USED (AF-19)
5. Validate `new_password_confirm = new_password` → 400 PASSWORDS_DONT_MATCH (AF-20)
6. Validate mật khẩu theo quy tắc (OQ-04 chưa chốt — giữ tối thiểu 6 ký tự để tương thích codebase cũ, theo SPEC)
7. Query `UserEntity` từ token.user_id
8. Nếu `is_active = false` → 403 ACCOUNT_INACTIVE
9. **Hash mật khẩu mới** bằng bcrypt, cập nhật `user.password_hash`
10. **Set `token.used_at = now()`** để đánh dấu token đã dùng (BR-09)
11. **Thu hồi toàn bộ refresh token của user** (BR-08, AC-15):
    - Xoá/invalidate tất cả refresh token stored của tài khoản này (nếu có bảng riêng)
    - Hoặc: nếu lưu version số trong JWT claim, tăng "token version" để tất cả token cũ không hợp lệ
12. **Không tự động đăng nhập** (BR-14) → return 200 cùng thông báo "vui lòng đăng nhập lại"

**AC mapping:** AC-20, AC-21, AC-22, AC-23, AC-24, AC-25, AF-18, AF-19, AF-20, AF-21, AF-22

---

### Error Code Enum (tạo mới)

```typescript
export enum AuthErrorCode {
  INVALID_EMAIL_FORMAT = 'INVALID_EMAIL_FORMAT',
  MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD',
  INVALID_CREDENTIALS = 'INVALID_CREDENTIALS',
  ACCOUNT_LOCKED = 'ACCOUNT_LOCKED',
  ACCOUNT_INACTIVE = 'ACCOUNT_INACTIVE',
  INVALID_REFRESH_TOKEN = 'INVALID_REFRESH_TOKEN',
  REFRESH_TOKEN_REVOKED = 'REFRESH_TOKEN_REVOKED',
  TOO_MANY_REQUESTS = 'TOO_MANY_REQUESTS',
  INVALID_TOKEN = 'INVALID_TOKEN',
  TOKEN_EXPIRED = 'TOKEN_EXPIRED',
  TOKEN_ALREADY_USED = 'TOKEN_ALREADY_USED',
  PASSWORDS_DONT_MATCH = 'PASSWORDS_DONT_MATCH',
  INVALID_PASSWORD = 'INVALID_PASSWORD',
}
```

---

## 4. Service Layer

### AuthService (tạo/sửa)

**File:** `src/modules/auth/auth.service.ts`

**Method signatures:**

```typescript
export class AuthService {
  // Login
  async login(email: string, password: string, rememberMe: boolean): Promise<AuthTokenResponse>

  // Refresh token
  async refreshToken(refreshToken: string): Promise<{ access_token: string }>

  // Forgot password
  async forgotPassword(email: string): Promise<void>

  // Reset password
  async resetPassword(token: string, newPassword: string): Promise<void>

  // Helper: validate password against rule (OQ-04 chưa chốt)
  private validatePasswordStrength(password: string): boolean

  // Helper: handle failed login (tăng bộ đếm, check lock)
  private handleFailedLoginAttempt(user: UserEntity): Promise<void>

  // Helper: reset login attempts (success)
  private resetLoginAttempts(user: UserEntity): Promise<void>

  // Helper: check account lock status
  private isAccountLocked(user: UserEntity): boolean

  // Helper: revoke refresh tokens (dùng khi đặt lại MK)
  private revokeRefreshTokens(userId: string): Promise<void>
}
```

**Dependency injection:**

```typescript
@Injectable()
export class AuthService {
  constructor(
    private usersRepository: Repository<UserEntity>,
    private passwordResetTokenRepository: Repository<PasswordResetTokenEntity>,
    private jwtService: JwtService,
    private configService: ConfigService,
    private emailService: EmailService,  // OQ-05: TBD nhà cung cấp
  ) {}
}
```

**Key business logic blocks:**

1. **Login flow:**
   - Validate input (email format, required fields)
   - Query user by email.toLowerCase().trim()
   - Check `is_active` → if false, return ACCOUNT_INACTIVE (không tăng bộ đếm)
   - Check `locked_until > now()` → if true, return ACCOUNT_LOCKED + remaining time
   - Verify password (bcrypt compare)
   - If wrong: handleFailedLoginAttempt() → check if >= 5, set locked_until
   - If correct: resetLoginAttempts(), sinh tokens, return

2. **Password reset flow:**
   - Validate token exists, not expired, not used
   - Validate passwords match & strength
   - Hash new password (bcrypt)
   - Update user.password_hash
   - Mark token as used (used_at = now)
   - Revoke all refresh tokens (BR-08)

3. **Rate limiting (BR-13):**
   - Check email_rate_limit table
   - If last_sent_at + 60s > now(), reject
   - Otherwise, update last_sent_at

**No logging of password/token** (AC-26, BR-15):
- Không log `password`, `password_hash`, `access_token`, `refresh_token`
- Chỉ log event (ví dụ: "login attempt", "password reset", "token refresh")

---

### JWT Configuration

**Access Token:**
- Exp: 15 minutes (BR-06)
- Payload: `{ sub: user.id, email: user.email, type: 'access' }`
- Signed with secret từ AWS Parameter Store (không hard-code)

**Refresh Token (nếu remember_me = true):**
- Exp: 30 days (BR-06)
- Payload: `{ sub: user.id, type: 'refresh', version: 1 }`
- Signed with secret từ AWS Parameter Store
- **Version scheme:** Nếu password reset → increment version, tất cả token cũ không hợp lệ (BR-08)

**Session-only Refresh Token (nếu remember_me = false):**
- Không store vào DB
- FE giữ trong memory (session storage hoặc variable, KHÔNG localStorage)
- Hết phiên trình duyệt → mất token (BR-07)

---

## 5. Interface với repo khác (Cross-repo)

### FE (example-web) gọi API

**Base URL:** Từ `VITE_API_URL` env var

**Endpoints gọi:**
- `POST /api/auth/login` — đăng nhập
- `POST /api/auth/refresh` — làm mới access token
- `POST /api/auth/logout` — đăng xuất (tuỳ chọn, có thể không cần từ BE)
- `POST /api/auth/forgot-password` — gửi link reset
- `POST /api/auth/reset-password` — đặt MK mới

**WebSocket:** Không có

**Push Notification:** Không có (đợt này ngoài scope)

---

## 6. Luồng xử lý chi tiết

### HP-A — Đăng nhập thành công

**Sequence (FE → BE):**

```
User: Nhập email + password, click "Đăng nhập"
  ↓
FE: Client-side validate (email format, required)
  ↓
FE: Gửi POST /api/auth/login { email, password, remember_me }
  ↓
BE: Validate input format
  ↓
BE: Query UserEntity by email.toLowerCase().trim()
  ↓
BE: Check is_active = false? → return 403 ACCOUNT_INACTIVE
  ↓
BE: Check locked_until > now()? → return 429 ACCOUNT_LOCKED (AC-06: tính remaining time)
  ↓
BE: bcrypt verify password
  ↓
BE: Password sai? → failed_login_attempts++, check if >= 5 → set locked_until, return 401 INVALID_CREDENTIALS
  ↓
BE: Password đúng? → failed_login_attempts = 0, last_login_at = now(), sinh tokens, return 200 + tokens
  ↓
FE: Lưu access_token + refresh_token (vào localStorage nếu remember_me=true, else memory)
  ↓
FE: Lấy redirect URL (từ query param hoặc localStorage "intended_url"), điều hướng
  ↓
Done: User vào trang chủ / intended page
```

**AC mapping:** AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-11, AC-12, AC-14, AC-16

---

### HP-B — Quên mật khẩu → Đặt lại thành công

**Sequence (FE → BE):**

```
User: Click "Quên mật khẩu?" → Màn quên MK
  ↓
User: Nhập email, click "Gửi hướng dẫn"
  ↓
FE: Client-side validate email format
  ↓
FE: Gửi POST /api/auth/forgot-password { email }
  ↓
BE: Validate email format
  ↓
BE: Check rate limit (last_sent_at + 60s > now?) → return 429 TOO_MANY_REQUESTS (BR-13)
  ↓
BE: LUÔN return 200 + cùng thông báo (BR-10), **bất kể email tồn tại hay không**
  ↓
BE: Nếu email tồn tại:
    - Tạo PasswordResetTokenEntity (token, expires_at = now + 60min, used_at = NULL)
    - Sinh reset link: {FRONTEND_URL}/auth/reset-password?token={token}
    - Gửi email (email service - OQ-05 chưa chốt)
  ↓
FE: Hiển thị thông báo "Nếu email này có..."
  ↓
User: Mở email, click link reset
  ↓
FE: Token trong URL được extract, gửi tới màn "Đặt MK mới"
  ↓
User: Nhập "MK mới" + "Nhập lại MK mới", click xác nhận
  ↓
FE: Client-side validate (2 ô khớp, strength check)
  ↓
FE: Gửi POST /api/auth/reset-password { token, new_password, new_password_confirm }
  ↓
BE: Validate token (exists, not expired, not used)
  ↓
BE: Validate passwords match & strength (OQ-04 chưa chốt, giữ >= 6 ký tự)
  ↓
BE: Query UserEntity từ token.user_id
  ↓
BE: Hash password mới, update user.password_hash
  ↓
BE: Mark token as used (used_at = now)
  ↓
BE: Revoke all refresh tokens (version++, hoặc invalidate stored tokens) (BR-08)
  ↓
BE: Return 200 + thông báo success
  ↓
FE: Hiển thị thông báo short, redirect → Màn đăng nhập
  ↓
User: Đăng nhập lại bằng MK mới (BR-14)
  ↓
Done
```

**AC mapping:** AC-17, AC-18, AC-19, AC-20, AC-21, AC-22, AC-23, AC-24, AC-25, AF-14 → AF-17, AF-18 → AF-23

---

### Edge case: AF-07 (hết 15 phút khoá, vẫn sai tiếp)

**Status:** ⚠️ **CHƯA CHỐT (OQ-02)** — phương án (a) khoá tiếp 15 min, (b) tăng dần, (c) khoá hẳn

**Placeholder:** Giả định phương án (a) — khoá tiếp 15 phút từ lần sai đầu tiên sau mở khoá

```
Hết 15 phút khoá → user sai tiếp lần 1
  ↓
failed_login_attempts = 1 (reset từ 5 về 1)
  ↓
Sai lần 2, 3, 4, 5 liên tiếp
  ↓
locked_until = now + 15min (tính từ lần sai thứ 5)
  ↓
Lặp lại chu kỳ khoá
```

**Thực thi:**
- Mỗi khi check `locked_until > now()`, nếu false (hết hạn) → reset `locked_until = NULL`, `failed_login_attempts = 0`
- Sau đó verify password theo quy tắc bình thường

---

### Edge case: AF-22 (đặt lại MK khi tài khoản bị khoá)

**Status:** ⚠️ **CHƯA CHỐT (OQ-03)** — không có quy tắc rõ

**Placeholder:** Cho phép reset password ngay cả khi locked (vì reset link từ email = bằng chứng sở hữu)

```
User bị khoá 15 phút → nhưng vẫn có thể click link reset password từ email
  ↓
BE reset-password endpoint: không check locked_until, chỉ validate token
  ↓
Reset thành công → locked_until được reset về NULL (hoặc không, quá mờ)
  ↓
Quy tắc chốt: sau khi reset MK, locked_until phải NULL (để user có thể đăng nhập ngay)
```

**Thực thi:**
```typescript
// Ở reset-password service
await this.usersRepository.update(user.id, {
  password_hash: newHashedPassword,
  failed_login_attempts: 0,
  locked_until: null,  // Mở khoá khi reset MK thành công
});
```

---

## 7. Non-Regression Risks

### Tính năng hiện có có thể bị ảnh hưởng

| Tính năng | File liên quan | Rủi ro | Giải pháp |
|---|---|---|---|
| Đăng nhập cũ (mã NV) | BE: AuthService (login endpoint cũ) | Feature mới thay thế hoàn toàn cơ chế đăng nhập → nếu có logic đang rely trên `employee_code` để xác thực sẽ break | Scan codebase để xem có endpoint/service nào khác dùng `employee_code` để auth; nếu có, phải sửa cùng lúc hoặc deprecate song song trong OQ-01 |
| Email migration | DB: users table, email_profiles table | Cột `email` thêm vào users + phải unique → cần migrate từ employee_profiles (OQ-01 chưa chốt, PM/PO quyết) | Cân nhắc migrate khách hàng trước khi deploy feature (hành chính cấp email mới cho nhân viên nội bộ) |
| Session management | FE/BE: JWT guard | Thay đổi refresh token strategy (thêm version/invalidate logic) → có thể affect logout/session timeout hiện có | Verify rằng FE xử lý 401 refresh token expired → redirect login đúng (AF-12) |
| Rate limiting | Nếu có anti-brute-force cũ ở IP level | Feature mới rate-limit per email (60s forgot-password, 5 attempts login) → có thể bị cộng stack với logic IP-level cũ | Scan guard/middleware có IP blocking không; nếu có, evaluate có overlap không |
| Password hash | BE: bcrypt (giữ nguyên) | 180 tài khoản hiện có được hash bằng bcrypt → không migrate (AC-27, SPEC precondition) | Xác nhận bcrypt version trong codebase cũ, dùng cùng library để verify (compatibility) |

### Blast radius từ tilth_deps (khi có code)

_(Chưa chạy tilth vì repo empty — sẽ chạy lại khi dev tạo code.)_

**Kỳ vọng khi dev implement:**
- UserEntity: 0–2 consumer (login/user profile retrieval)
- AuthService login: 1 endpoint consumer (controller)
- JWT guard: N consumer (mọi endpoint cần auth) → đảm bảo không break tính năng cũ

---

## 8. Các quyết định kỹ thuật & Open Questions chưa chốt

### Quyết định đã chốt (Tech Lead Design)

| Quyết định | Giá trị | Lý do |
|---|---|---|
| Lưu bộ đếm failed attempts | PostgreSQL (cột `failed_login_attempts`) | Không thêm infra Redis; multiple instance consistency qua DB |
| Email định danh | Unique constraint trên `users.email` | BR-01 yêu cầu email là định danh duy nhất |
| Hash algorithm | bcrypt (giữ nguyên) | AC-27: không migrate 180 tài khoản |
| Token strategy | JWT (access + refresh) | Chuẩn NestJS, đơn giản, không state |
| Refresh invalidation | JWT version claim hoặc token blacklist | BR-08: đổi MK → revoke hết phiên |
| Password rate limit | 60 giây (BR-13) | PostgreSQL table `email_rate_limit(email, last_sent_at)` |

### Open Questions (PO/PM/Tech Lead quyết định sau Design)

| ID | Câu hỏi | Phương án | Ảnh hưởng | Quyết định của | Status |
|---|---|---|---|---|---|
| **OQ-01** | Migrate 180 tài khoản email từ employee_profiles → users.email làm sao? | (a) Hành chính cấp; (b) Dual-auth 3 tháng; (c) Yêu cầu reset via forgot-password | Chặn Phase 1 migration, AC-30 | PO | TBD |
| **OQ-02** | Hết 15 phút khoá, vẫn sai tiếp? | (a) Khoá 15 min nữa; (b) Tăng dần 15→30→60; (c) Khoá hẳn chờ admin | AF-07 flow | PO | TBD |
| **OQ-03** | Có cần trang xem/ngắt phiên per device? | (a) Có trang; (b) Chỉ dựa BR-08 (đổi MK = revoke tất) | Scope, PLAN timeline | PO | **Giả định (b)** |
| **OQ-04** | Quy tắc mật khẩu mới (độ dài, ký tự đặc biệt)? | Giữ 6 ký tự (cũ) hay siết lại? | AF-21, AC-23, thanh độ mạnh | PO/Tech Lead | TBD (placeholder: 6+ ký tự) |
| **OQ-05** | Nhà cung cấp email? | Nhà cung cấp A/B/C (chưa quyết tại SPEC survey) | HP-B step 4, AC-18, E2E test | Tech Lead/PM | TBD — **Design sẵn sàng mock** |
| **OQ-06** | Link reset được yêu cầu lại có vô hiệu link cũ không? | (a) Vô hiệu link cũ; (b) Cả 2 dùng được | AF-17, test case bảo mật | Tech Lead | TBD (placeholder: **(a) vô hiệu**) |

**Recommendation:** 
- OQ-02, OQ-03, OQ-04 do PO/PM quyết (không phải tech) → **không block Design**
- OQ-05 không block (email service abstract, FE/BE có thể mock)
- OQ-06 có tech implication nhỏ (token storage) → Tech Lead xác nhận lại khi Phase 2 (do được ghi placeholder)

---

## 9. Checklist Pre-Contract-Lock

**Trước Phase 3 (FE/Mobile bắt đầu code)**, Backend team cần confirm:**

- [ ] Database schema (migration) finalized — có review từ QC/PM
- [ ] API endpoints (5 routes) + error codes locked
- [ ] DTO (request/response) finalized
- [ ] Email service placeholder định rõ (mock endpoint hoặc fake SMTP)
- [ ] JWT secret management (AWS Parameter Store) configured
- [ ] bcrypt version aligned với codebase cũ
- [ ] Rate limit table (`email_rate_limit`) hoặc in-memory strategy finalized
- [ ] OQ-01 (email migration plan) finalized — nếu chưa, phải skip phase 1 migration
- [ ] OQ-04 (password rules) finalized — nếu chưa, dùng placeholder 6+ ký tự

---

## Tham chiếu

- **SPEC:** `/docs/features/user-login/SPEC.md`
- **Stack:** PostgreSQL + NestJS + TypeORM (v0.3.x) + bcryptjs + @nestjs/jwt
- **Security rules:** `.claude/rules/security-rules.md` (không log password/token)
- **Design system:** `.claude/rules/design_rule.md` (chưa áp dụng cho backend, chỉ FE/Mobile)
