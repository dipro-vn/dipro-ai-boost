# DESIGN: User Login — example-web (Frontend)

> **Nguồn:** SPEC.md § Actors, Happy Path, Alternative Flows, Screens table
>
> **Phụ thuộc:** `example-api/DESIGN.md` (API Contract)
>
> **Status:** Chờ Design Figma (Screens table cột "Figma Link" chưa có), Code Contract Lock trước Phase 3

---

## 1. Tổng quan thay đổi

### Phạm vi ảnh hưởng

| Layer | Module/File | Loại thay đổi |
|---|---|---|
| Pages | `src/pages/auth/LoginPage.tsx` | Tạo mới |
| Pages | `src/pages/auth/ForgotPasswordPage.tsx` | Tạo mới |
| Pages | `src/pages/auth/ResetPasswordPage.tsx` | Tạo mới |
| Components | `src/components/auth/EmailField.tsx` | Tạo mới |
| Components | `src/components/auth/PasswordStrengthBar.tsx` | Tạo mới |
| Hooks | `src/hooks/useAuth.ts` | Tạo/sửa (login, logout, refresh) |
| Hooks | `src/hooks/usePasswordReset.ts` | Tạo mới (forgot-password, reset-password flow) |
| Store | `src/store/auth/authSlice.ts` | Sửa (thêm user email, token state, lock state) |
| Services | `src/services/authApi.ts` | Tạo mới (5 endpoints: login, refresh, logout, forgot, reset) |
| Utils | `src/utils/tokenStorage.ts` | Tạo/sửa (lưu access/refresh token correctly) |
| Router | `src/router/ProtectedRoute.tsx` | Sửa (handle refresh token, 401 → redirect login + remember intended URL) |
| Router | `src/router/AuthLayout.tsx` | Tạo mới (layout cho auth pages) |

### Dependency mới

- **react-hook-form** (đã có trong codebase) — form management
- **yup** (đã có) — validation schema
- **react-query** (TanStack Query v5) — API calls + caching
- **redux-persist** (optional) — persist auth state (nếu `remember_me = true`)

---

## 2. State Management (Redux)

### authSlice

**File:** `src/store/auth/authSlice.ts`

**State shape:**

```typescript
interface AuthState {
  // Token
  accessToken: string | null;
  refreshToken: string | null;
  refreshTokenExpiresAt: number | null;  // Unix timestamp (ms)
  refreshTokenExpiresIn: number | null;  // Seconds from now (for progress/countdown)

  // User info
  user: {
    id: string;
    email: string;
    employee_code?: string | null;
    is_active: boolean;
  } | null;

  // Session
  isAuthenticated: boolean;
  isLoading: boolean;

  // Error
  error: {
    code: string;  // Error code từ API (INVALID_CREDENTIALS, ACCOUNT_LOCKED, ...)
    message: string;
  } | null;

  // Lock state (display khi tài khoản bị khoá)
  lockState: {
    isLocked: boolean;
    remainingSeconds: number;
    lockedUntil: number;  // Unix timestamp (ms)
  } | null;

  // Intended URL (remember khi redirect login)
  intendedUrl: string | null;
}
```

**Initial state:**

```typescript
const initialState: AuthState = {
  accessToken: null,
  refreshToken: null,
  refreshTokenExpiresAt: null,
  refreshTokenExpiresIn: null,
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  lockState: null,
  intendedUrl: null,
};
```

**Actions & Reducers:**

```typescript
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    // Login success
    setAuthTokens: (state, action) => {
      state.accessToken = action.payload.access_token;
      state.refreshToken = action.payload.refresh_token;
      state.refreshTokenExpiresAt = action.payload.refresh_token_expires_at;
      state.user = action.payload.user;
      state.isAuthenticated = true;
      state.error = null;
      state.lockState = null;
    },

    // Login fail
    setAuthError: (state, action) => {
      state.error = action.payload;  // { code, message }
      state.isAuthenticated = false;
      // Nếu code = ACCOUNT_LOCKED
      if (action.payload.code === 'ACCOUNT_LOCKED') {
        state.lockState = action.payload.lockState;  // { isLocked, remainingSeconds, lockedUntil }
      }
    },

    // Refresh token
    refreshAccessToken: (state, action) => {
      state.accessToken = action.payload.access_token;
      state.error = null;
    },

    // Logout
    clearAuth: (state) => {
      state.accessToken = null;
      state.refreshToken = null;
      state.user = null;
      state.isAuthenticated = false;
      state.error = null;
      state.lockState = null;
    },

    // Remember intended URL
    setIntendedUrl: (state, action) => {
      state.intendedUrl = action.payload;
    },

    // Refresh countdown (update remaining seconds)
    updateLockCountdown: (state, action) => {
      if (state.lockState) {
        state.lockState.remainingSeconds = action.payload;
      }
    },

    // Set loading
    setLoading: (state, action) => {
      state.isLoading = action.payload;
    },
  },
});
```

**Persistence:** 
- Nếu `remember_me = true` → lưu `accessToken`, `refreshToken`, `user` vào localStorage (redux-persist)
- Nếu `remember_me = false` → lưu vào session storage hoặc memory (không persistent)

---

## 3. API Service Layer

### authApi.ts

**File:** `src/services/authApi.ts`

```typescript
import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';
const api = axios.create({ baseURL: API_BASE_URL });

// Interceptor: Thêm JWT vào header
api.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('accessToken') || sessionStorage.getItem('accessToken');
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Interceptor: Handle 401 → refresh token
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refreshToken') || sessionStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const { data } = await api.post('/api/auth/refresh', { refresh_token: refreshToken });
          localStorage.setItem('accessToken', data.access_token);
          // Retry original request
          return api(error.config);
        } catch (refreshError) {
          // Refresh failed → redirect login
          window.location.href = '/auth/login';
        }
      } else {
        window.location.href = '/auth/login';
      }
    }
    return Promise.reject(error);
  }
);

// ============ Auth API Functions ============

export const authApi = {
  /**
   * POST /api/auth/login
   * Request: { email, password, remember_me? }
   * Response: { access_token, refresh_token, refresh_token_expires_at, user }
   * Errors: 400, 401, 429, 403, 500
   */
  login: async (email: string, password: string, rememberMe: boolean = false) => {
    return api.post('/api/auth/login', {
      email: email.toLowerCase().trim(),
      password,
      remember_me: rememberMe,
    });
  },

  /**
   * POST /api/auth/refresh
   * Request: { refresh_token }
   * Response: { access_token }
   */
  refresh: async (refreshToken: string) => {
    return api.post('/api/auth/refresh', { refresh_token: refreshToken });
  },

  /**
   * POST /api/auth/logout
   * Response: { message }
   */
  logout: async () => {
    return api.post('/api/auth/logout');
  },

  /**
   * POST /api/auth/forgot-password
   * Request: { email }
   * Response: { message } (always same message - BR-10)
   * Errors: 400, 429
   */
  forgotPassword: async (email: string) => {
    return api.post('/api/auth/forgot-password', {
      email: email.toLowerCase().trim(),
    });
  },

  /**
   * POST /api/auth/reset-password
   * Request: { token, new_password, new_password_confirm }
   * Response: { message }
   * Errors: 400, 403
   */
  resetPassword: async (token: string, newPassword: string, newPasswordConfirm: string) => {
    return api.post('/api/auth/reset-password', {
      token,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    });
  },
};
```

---

## 4. Custom Hooks

### useAuth

**File:** `src/hooks/useAuth.ts`

```typescript
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { useCallback } from 'react';
import { authApi } from '@/services/authApi';
import {
  setAuthTokens,
  setAuthError,
  clearAuth,
  setIntendedUrl,
  setLoading,
} from '@/store/auth/authSlice';

export const useAuth = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    isLoading,
    error,
    lockState,
    intendedUrl,
  } = useSelector((state: RootState) => state.auth);

  // Login function
  const login = useCallback(
    async (email: string, password: string, rememberMe: boolean = false) => {
      dispatch(setLoading(true));
      try {
        const { data } = await authApi.login(email, password, rememberMe);
        
        // Store tokens
        const storage = rememberMe ? localStorage : sessionStorage;
        storage.setItem('accessToken', data.access_token);
        storage.setItem('refreshToken', data.refresh_token);

        // Update Redux state
        dispatch(
          setAuthTokens({
            access_token: data.access_token,
            refresh_token: data.refresh_token,
            refresh_token_expires_at: data.refresh_token_expires_at,
            user: data.user,
          })
        );

        // Redirect to intended URL or home
        const redirectUrl = intendedUrl || '/';
        navigate(redirectUrl);
        dispatch(setIntendedUrl(null));
      } catch (err: any) {
        const errorCode = err.response?.data?.error || 'UNKNOWN_ERROR';
        let errorMessage = 'Đăng nhập thất bại. Vui lòng thử lại.';

        if (errorCode === 'INVALID_CREDENTIALS') {
          errorMessage = 'Email hoặc mật khẩu không đúng.';
        } else if (errorCode === 'ACCOUNT_LOCKED') {
          const lockState = {
            isLocked: true,
            remainingSeconds: err.response?.data?.remaining_minutes * 60,
            lockedUntil: err.response?.data?.locked_until,
          };
          errorMessage = `Tài khoản bị khoá. Vui lòng thử lại sau ${lockState.remainingSeconds} giây.`;
          dispatch(
            setAuthError({
              code: errorCode,
              message: errorMessage,
              lockState,
            })
          );
          dispatch(setLoading(false));
          return;
        } else if (errorCode === 'ACCOUNT_INACTIVE') {
          errorMessage = 'Tài khoản đã bị vô hiệu hoá. Liên hệ quản trị viên.';
        } else if (err.response?.status === 500) {
          errorMessage = 'Lỗi máy chủ. Vui lòng thử lại sau.';
        }

        dispatch(
          setAuthError({
            code: errorCode,
            message: errorMessage,
          })
        );
      } finally {
        dispatch(setLoading(false));
      }
    },
    [dispatch, navigate, intendedUrl]
  );

  // Logout function
  const logout = useCallback(async () => {
    dispatch(setLoading(true));
    try {
      await authApi.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      sessionStorage.removeItem('accessToken');
      sessionStorage.removeItem('refreshToken');
      dispatch(clearAuth());
      navigate('/auth/login');
      dispatch(setLoading(false));
    }
  }, [dispatch, navigate]);

  // Remember intended URL (call khi user truy cập protected route mà chưa auth)
  const rememberIntendedUrl = useCallback(
    (url: string) => {
      dispatch(setIntendedUrl(url));
    },
    [dispatch]
  );

  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    isLoading,
    error,
    lockState,
    intendedUrl,
    login,
    logout,
    rememberIntendedUrl,
  };
};
```

### usePasswordReset

**File:** `src/hooks/usePasswordReset.ts`

```typescript
import { useState, useCallback } from 'react';
import { authApi } from '@/services/authApi';

interface PasswordResetState {
  isLoading: boolean;
  error: { code: string; message: string } | null;
  success: string | null;
  remainingCooldown: number;  // Giây chờ trước khi gửi lại (BR-13)
}

export const usePasswordReset = () => {
  const [forgotPasswordState, setForgotPasswordState] = useState<PasswordResetState>({
    isLoading: false,
    error: null,
    success: null,
    remainingCooldown: 0,
  });

  const [resetPasswordState, setResetPasswordState] = useState<PasswordResetState>({
    isLoading: false,
    error: null,
    success: null,
    remainingCooldown: 0,
  });

  // Forgot password
  const forgotPassword = useCallback(async (email: string) => {
    setForgotPasswordState({ isLoading: true, error: null, success: null, remainingCooldown: 0 });
    try {
      const { data } = await authApi.forgotPassword(email);
      // LUÔN thành công với cùng thông báo (BR-10)
      setForgotPasswordState({
        isLoading: false,
        error: null,
        success: data.message,
        remainingCooldown: 60,  // BR-13: bắt đầu cooldown 60 giây
      });
      // Auto-decrement cooldown
      const interval = setInterval(() => {
        setForgotPasswordState((prev) => ({
          ...prev,
          remainingCooldown: Math.max(0, prev.remainingCooldown - 1),
        }));
      }, 1000);
      return () => clearInterval(interval);
    } catch (err: any) {
      const errorCode = err.response?.data?.error || 'UNKNOWN_ERROR';
      let errorMessage = 'Gửi hướng dẫn thất bại. Vui lòng thử lại.';

      if (errorCode === 'INVALID_EMAIL_FORMAT') {
        errorMessage = 'Email không đúng định dạng.';
      } else if (errorCode === 'TOO_MANY_REQUESTS') {
        const remaining = err.response?.data?.retry_after || 60;
        errorMessage = `Vui lòng chờ ${remaining} giây trước khi gửi lại.`;
        setForgotPasswordState({
          isLoading: false,
          error: { code: errorCode, message: errorMessage },
          success: null,
          remainingCooldown: remaining,
        });
        return;
      }

      setForgotPasswordState({
        isLoading: false,
        error: { code: errorCode, message: errorMessage },
        success: null,
        remainingCooldown: 0,
      });
    }
  }, []);

  // Reset password
  const resetPassword = useCallback(
    async (token: string, newPassword: string, newPasswordConfirm: string) => {
      setResetPasswordState({ isLoading: true, error: null, success: null, remainingCooldown: 0 });
      try {
        const { data } = await authApi.resetPassword(token, newPassword, newPasswordConfirm);
        setResetPasswordState({
          isLoading: false,
          error: null,
          success: data.message,
          remainingCooldown: 0,
        });
      } catch (err: any) {
        const errorCode = err.response?.data?.error || 'UNKNOWN_ERROR';
        let errorMessage = 'Đặt lại mật khẩu thất bại. Vui lòng thử lại.';

        if (errorCode === 'INVALID_TOKEN' || errorCode === 'TOKEN_EXPIRED') {
          errorMessage = 'Link đã hết hạn. Vui lòng gửi lại yêu cầu.';
        } else if (errorCode === 'TOKEN_ALREADY_USED') {
          errorMessage = 'Link đã hết hạn. Vui lòng gửi lại yêu cầu.';  // AF-19 = AF-22
        } else if (errorCode === 'PASSWORDS_DONT_MATCH') {
          errorMessage = 'Hai ô mật khẩu không khớp.';
        } else if (errorCode === 'INVALID_PASSWORD') {
          errorMessage = 'Mật khẩu không đạt yêu cầu. Vui lòng kiểm tra lại.';
        }

        setResetPasswordState({
          isLoading: false,
          error: { code: errorCode, message: errorMessage },
          success: null,
          remainingCooldown: 0,
        });
      }
    },
    []
  );

  return {
    forgotPasswordState,
    forgotPassword,
    resetPasswordState,
    resetPassword,
  };
};
```

---

## 5. UI Components

### LoginPage

**File:** `src/pages/auth/LoginPage.tsx`

**Props:** None (top-level page)

**Features:**
- Form: Email + Password + Checkbox "Ghi nhớ đăng nhập"
- Client-side validation (email format, required fields)
- Error banner ở đầu form
- Inline error dưới email field (nếu sai format)
- Loading state (nút bị disable, spinner)
- Link "Quên mật khẩu?" ở dưới form
- Xử lý AF-10 (duplicate submit): nút vô hiệu hoá lúc loading
- Xử lý AF-09 (server error): giữ lại email đã gõ, hiển thị banner lỗi đỏ

**Form DTO:**

```typescript
interface LoginFormValues {
  email: string;
  password: string;
  rememberMe: boolean;
}

const loginSchema = yup.object({
  email: yup
    .string()
    .email('Email không đúng định dạng')
    .required('Email là bắt buộc')
    .lowercase()
    .trim(),
  password: yup.string().required('Mật khẩu là bắt buộc'),
  rememberMe: yup.boolean(),
});
```

**Layout:**
```
┌─────────────────────────────┐
│      Logo / Title           │
├─────────────────────────────┤
│ [Error banner nếu có]       │
│                             │
│ Email: [input] [error]      │
│ Password: [input] [show/hide]
│ □ Ghi nhớ đăng nhập         │
│                             │
│ [Nút Đăng nhập - chiều ngang]
│                             │
│ Quên mật khẩu?              │
└─────────────────────────────┘
```

**Design tokens (từ `.claude/rules/design_rule.md`):**
- Button primary: `colors.semantics.company.500`
- Error text: `colors.semantics.negative.500`
- Border input: `colors.components.divider.middle`
- Font body: `font.text md.regular`
- Padding: `spacing.padding.16`

---

### ForgotPasswordPage

**File:** `src/pages/auth/ForgotPasswordPage.tsx`

**Features:**
- Form: Email input + "Gửi hướng dẫn" button
- Luôn hiển thị **cùng thông báo** sau gửi (BR-10)
- Nút "Gửi" có đếm ngược 60 giây sau lần gửi đầu (BR-13, AF-16)
- Link quay lại đăng nhập

**Form DTO:**

```typescript
interface ForgotPasswordFormValues {
  email: string;
}

const forgotPasswordSchema = yup.object({
  email: yup
    .string()
    .email('Email không đúng định dạng')
    .required('Email là bắt buộc'),
});
```

**Layout:**
```
┌─────────────────────────────┐
│      Logo / Title           │
├─────────────────────────────┤
│ Quên mật khẩu               │
│ Nhập email để nhận link...  │
│                             │
│ Email: [input]              │
│                             │
│ [Nút "Gửi hướng dẫn"]       │
│ (Disabled + countdown       │
│  nếu gửi rồi)              │
│                             │
│ [Success message]           │
│ (nếu gửi xong)             │
│                             │
│ Quay lại đăng nhập          │
└─────────────────────────────┘
```

---

### ResetPasswordPage

**File:** `src/pages/auth/ResetPasswordPage.tsx`

**Props:**
- `token` (từ URL query param)

**Features:**
- 2 ô mật khẩu: "Mật khẩu mới" + "Nhập lại mật khẩu mới"
- Thanh độ mạnh mật khẩu (placeholder: base trên độ dài + ký tự loại — OQ-04 chưa chốt)
- Validation:
  - 2 ô phải khớp (AF-20)
  - Mật khẩu phải đạt quy tắc (AF-21 — OQ-04 placeholder)
- Xử lý link hết hạn / đã dùng: **cùng thông báo** + nút gửi lại (AF-18, AF-19)
- Success: hiển thị thông báo ngắn, redirect login (BR-14)

**Form DTO:**

```typescript
interface ResetPasswordFormValues {
  newPassword: string;
  newPasswordConfirm: string;
}

const resetPasswordSchema = yup.object({
  newPassword: yup
    .string()
    .min(6, 'Mật khẩu tối thiểu 6 ký tự')  // OQ-04 placeholder
    .required('Mật khẩu là bắt buộc'),
  newPasswordConfirm: yup
    .string()
    .oneOf([yup.ref('newPassword')], 'Hai ô mật khẩu không khớp')
    .required('Vui lòng xác nhận mật khẩu'),
});
```

**Password Strength Bar:**
```typescript
// Component: PasswordStrengthBar
// Props: password: string
// Output: 
//   - Length: strength 0–25%
//   - Has uppercase: +20%
//   - Has number: +20%
//   - Has special char: +20%
//   - Has lowercase: +15%

// Display:
// ▓░░░░ 20% - Yếu
// ▓▓▓░░ 60% - Bình thường
// ▓▓▓▓▓ 100% - Mạnh
```

**Layout:**
```
┌─────────────────────────────┐
│      Logo / Title           │
├─────────────────────────────┤
│ Đặt mật khẩu mới            │
│ [Error banner nếu có]       │
│                             │
│ Mật khẩu mới: [input]       │
│ Nhập lại:     [input]       │
│               [error]       │
│                             │
│ [Strength bar]              │
│ Gợi ý: tối thiểu ...        │
│                             │
│ [Nút "Xác nhận"]            │
│                             │
│ Gửi lại link (nếu hết hạn)  │
└─────────────────────────────┘
```

---

## 6. Router & Protection

### ProtectedRoute

**File:** `src/router/ProtectedRoute.tsx`

```typescript
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, rememberIntendedUrl } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    // Remember current URL để quay lại sau khi đăng nhập
    rememberIntendedUrl(location.pathname + location.search);
    return <Navigate to="/auth/login" replace />;
  }

  return <>{children}</>;
};
```

**JWT Interceptor (ở authApi.ts):**
- Tự động thêm `Authorization: Bearer <token>` vào request
- Catch 401 → cố gắng refresh token
- Nếu refresh fail → redirect `/auth/login` + lưu intended URL
- AC-12: Người dùng không thấy gián đoạn (tự refresh)
- AF-11, AF-12: xử lý refresh fail

---

## 7. Routing Map

```typescript
// Router config
const authRoutes = [
  { path: '/auth/login', element: <LoginPage /> },
  { path: '/auth/forgot-password', element: <ForgotPasswordPage /> },
  { path: '/auth/reset-password', element: <ResetPasswordPage /> },
];

const protectedRoutes = [
  { path: '/', element: <ProtectedRoute><HomePage /></ProtectedRoute> },
  { path: '/dashboard', element: <ProtectedRoute><DashboardPage /></ProtectedRoute> },
  // ... other routes
];
```

---

## 8. Token Storage Strategy

### Session vs Persistent

**Nếu `remember_me = true`:**
- Lưu tokens vào `localStorage`
- Persistent qua browser restart
- 30 days expiry (BR-06)

**Nếu `remember_me = false`:**
- Lưu tokens vào `sessionStorage` hoặc variable in-memory
- Mất khi đóng tab/trình duyệt (BR-07)
- Session-only, không persistent

**Implementation:**
```typescript
const login = async (...) => {
  const storage = rememberMe ? localStorage : sessionStorage;
  storage.setItem('accessToken', data.access_token);
  storage.setItem('refreshToken', data.refresh_token);
};

const getAccessToken = () => {
  return localStorage.getItem('accessToken') || sessionStorage.getItem('accessToken');
};
```

### Not localStorage directly for JWT (XSS concern)

**Best practice:** Nếu project yêu cầu XSS protection → dùng httpOnly cookie + SameSite.
**Trong SPEC này:** Không mention XSS → giữ nguyên localStorage (đơn giản, tương thích).

---

## 9. Luồng chi tiết (Happy Path)

### HP-A — Đăng nhập (FE side)

```
User: Mở /auth/login
  ↓
LoginPage render: form trống (hoặc remember email nếu có localStorage)
  ↓
User: Nhập email + password, tick "Ghi nhớ"
  ↓
User: Bấm Đăng nhập
  ↓
FE: Client-side validate
  - Email format? Email required? Password required?
  - Nếu fail → hiển thị error inline dưới ô tương ứng, KHÔNG gọi API
  ↓
FE: Nút vô hiệu hoá (AF-10), loading spinner
  ↓
FE: POST /api/auth/login { email, password, remember_me }
  ↓
FE: Nhận response 200 { access_token, refresh_token, refresh_token_expires_at, user }
  ↓
FE: Lưu tokens vào localStorage (vì remember_me=true)
  ↓
FE: Update Redux auth state
  ↓
FE: Redirect intendedUrl hoặc home "/"
  ↓
Done: User ở trang chủ
```

### HP-B — Quên mật khẩu (FE side)

```
User: Click "Quên mật khẩu?" ở màn login
  ↓
FE: Chuyển /auth/forgot-password
  ↓
ForgotPasswordPage render: form email + nút gửi
  ↓
User: Nhập email, bấm "Gửi hướng dẫn"
  ↓
FE: Validate email format
  ↓
FE: POST /api/auth/forgot-password { email }
  ↓
FE: Response 200 { message: "Nếu email này có..." }
  ↓
FE: Hiển thị thông báo success (LUÔN cùng thông báo — BR-10)
  ↓
FE: Nút gửi lại bị disable, bắt đầu countdown 60 giây (BR-13, AF-16)
  ↓
BE: (nếu email tồn tại) Gửi email chứa reset link (OQ-05 TBD)
  ↓
User: Mở email, click link reset
  ↓
FE: Extract token từ URL param, mở /auth/reset-password?token={token}
  ↓
ResetPasswordPage render: 2 ô mật khẩu + strength bar
  ↓
User: Nhập "MK mới" x2, bấm xác nhận
  ↓
FE: Validate (khớp, độ mạnh)
  ↓
FE: POST /api/auth/reset-password { token, new_password, new_password_confirm }
  ↓
FE: Response 200 { message: "Mật khẩu đã được đặt lại..." }
  ↓
FE: Hiển thị thông báo success (ngắn)
  ↓
FE: Redirect /auth/login (BR-14 — không tự động đăng nhập)
  ↓
User: Đăng nhập lại bằng MK mới
  ↓
Done
```

---

## 10. Error Handling Map

| Scenario | API Response | FE Display | Component |
|---|---|---|---|
| **Login: email sai hoặc MK sai** | 401 INVALID_CREDENTIALS | Error banner: "Email hoặc mật khẩu không đúng" | LoginPage banner |
| **Login: email format sai** | 400 INVALID_EMAIL_FORMAT | Inline error dưới email field (blur event) | EmailField |
| **Login: MK bỏ trống** | 400 MISSING_REQUIRED_FIELD | Inline error dưới password field | LoginPage |
| **Login: tài khoản bị khoá** | 429 ACCOUNT_LOCKED + remaining_minutes | Error banner + countdown "còn XX phút" | LoginPage banner |
| **Login: tài khoản vô hiệu** | 403 ACCOUNT_INACTIVE | Error banner: "Tài khoản đã bị vô hiệu hoá..." | LoginPage banner |
| **Login: server error** | 500 SERVER_ERROR | Red banner: "Lỗi máy chủ. Vui lòng thử lại." Email vẫn giữ | LoginPage banner |
| **Forgot: email format sai** | 400 INVALID_EMAIL_FORMAT | Inline error dưới email | EmailField |
| **Forgot: gửi quá nhanh** | 429 TOO_MANY_REQUESTS | Error: "Vui lòng chờ XX giây" + disable nút | ForgotPasswordPage |
| **Forgot: server error** | 500 | Error banner (tương tự login) | ForgotPasswordPage |
| **Reset: link hết hạn** | 400 TOKEN_EXPIRED | "Link đã hết hạn. [Gửi lại]" + link forgot-password | ResetPasswordPage |
| **Reset: link đã dùng** | 400 TOKEN_ALREADY_USED | Same as TOKEN_EXPIRED (AF-19 = AF-22) | ResetPasswordPage |
| **Reset: 2 ô MK không khớp** | (client-side) | Inline error dưới ô thứ 2 | ResetPasswordPage |
| **Reset: MK không đạt quy tắc** | 400 INVALID_PASSWORD | Inline error dưới ô MK 1 | ResetPasswordPage |
| **Logout success** | 200 | (silent) Redirect /auth/login | (logout action) |
| **API: access token hết hạn** | 401 INVALID_REFRESH_TOKEN | (silent retry) Nếu refresh cũng fail → redirect login | (interceptor) |

---

## 11. Non-Regression Risks

| Tính năng hiện có | File liên quan | Rủi ro | Giải pháp |
|---|---|---|---|
| Router protection (ProtectedRoute cũ) | `src/router/ProtectedRoute.tsx` | Nếu cũ check `user.employee_code` → bị break bởi email auth | Cập nhật check `isAuthenticated` thay vì `employee_code` |
| Token storage (localStorage) | `src/utils/tokenStorage.ts` | Nếu có component khác dùng `localStorage.getItem('token')` → cần đổi thành `accessToken`/`refreshToken` key | Scan codebase, rename key consistent |
| Redux auth state | `src/store/auth/authSlice.ts` | Nếu component khác subscribe `user.employee_code` → giờ có thể NULL → cần xử lý | Default nó thành optional field (`employee_code?: string`) |
| Form validation (email) | Mọi form dùng email | Nếu form email validation dùng quy tắc cũ (không lowercase trim) → mất sync với BE | Dùng shared validation schema (email.ts util) |
| API interceptor | `src/services/authApi.ts` | Nếu có API call khác không qua authApi → không có interceptor 401 refresh | Xác nhận toàn bộ API call qua authApi, không dùng axios trực tiếp |

---

## 12. Design System Integration

### Colors (từ `.claude/rules/design_rule.md`)

- **Button Primary:** `colors.semantics.company.500` (#0969da)
- **Button Hover:** `colors.semantics.company.600` (#0550ae)
- **Button Disabled:** `colors.semantics.neutral.300` (#afb8c1)
- **Error:** `colors.semantics.negative.500` (#cf222e)
- **Success:** `colors.semantics.success.500` (#1a7f37)
- **Warning:** `colors.semantics.warning.500` (#eab308)
- **Border:** `colors.components.divider.middle` (#d0d7de)
- **Text primary:** `colors.components.text.high` (#24292f)
- **Text secondary:** `colors.components.text.middle` (#424a53)
- **Text disabled:** `colors.components.text.low` (#6e7781)
- **Background:** `colors.semantics.neutral.50` (#f6f8fa)

### Typography

- **Form label:** `font.text sm.medium` (14px, medium)
- **Error text:** `font.text xs.regular` (12px)
- **Button text:** `font.text md.medium` (16px, medium)
- **Page title:** `font.display xs.bold` (24px, bold)

### Spacing

- **Form gap:** `spacing.padding.12` hoặc `16`
- **Button height:** `spacing.padding.48` (standard ~48px)
- **Modal padding:** `spacing.padding.24` hoặc `32`

### Border Radius

- **Input:** `borders.semantics.border-radius.action` (6px)
- **Button:** `borders.semantics.border-radius.action` (6px)
- **Modal:** `borders.semantics.border-radius.modal` (12px)

---

## 13. Checklist Pre-Contract-Lock

**Trước Phase 3, FE team cần confirm:**

- [ ] API endpoints (5 routes) + error codes từ BE locked
- [ ] DTO request/response shape finalized
- [ ] Email service endpoint / mock định rõ (OQ-05)
- [ ] Password validation rules finalized (OQ-04)
- [ ] Design Figma cho 3 screens (WB_AUTH_001/002/003) completed — điền Figma URL vào SPEC.md
- [ ] Design tokens mapping hoàn tất (colors, fonts, spacing, border-radius)
- [ ] Token storage strategy confirm (localStorage vs sessionStorage)
- [ ] Redirect logic (intended URL) tested
- [ ] 401 → refresh → retry flow tested

---

## Tham chiếu

- **SPEC:** `/docs/features/user-login/SPEC.md`
- **Backend Contract:** `example-api/DESIGN.md`
- **Stack:** React 19 / Vite / Redux Toolkit v2 / TanStack Query v5 / react-hook-form + yup
- **Design System:** `.claude/rules/design_rule.md`
- **Security:** Không lưu password/token trong localStorage nếu XSS is concern (SPEC không mention)
