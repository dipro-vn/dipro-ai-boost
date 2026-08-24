# PLAN: User Login

> **Nguồn:** `SPEC.md`, `example-api/DESIGN.md`, `example-web/DESIGN.md`, task files trong `*/tasks/`
>
> **Phạm vi:** brownfield — thay màn đăng nhập cũ, sống chung với bảng `users` sẵn có.

---

## 1. Phân rã theo phase

| Phase | Repo | Task | Estimate |
|---|---|---|---|
| 1 — Database | `example-api` | `task-1-1` Migration lockout + password_reset_tokens | 3h |
| 2 — Service + API | `example-api` | `task-2-1` AuthService login + lockout | 6h |
| 2 — Service + API | `example-api` | `task-2-2` 5 endpoint + error code enum | 5h |
| 3 — Frontend | `example-web` | `task-3-1` authSlice + authApi + useAuth | 5h |
| 3 — Frontend | `example-web` | `task-3-2` LoginPage + ProtectedRoute | 6h |

**Tổng:** 25h.

---

## 2. Contract Lock

Chốt sau `task-2-2`, trước khi `example-web` vào Phase 3.

| Bên | Vai trò |
|---|---|
| `example-api` | Chủ contract — 5 endpoint, DTO, error code |
| `example-web` | Consumer — không tự đoán response shape |

Không có WebSocket và push notification trong feature này.

---

## 3. Đường găng

`task-1-1` → `task-2-1` → `task-2-2` → `task-3-1` → `task-3-2`.

Chuỗi hoàn toàn tuần tự: `example-web` không có việc nào chạy song song được với backend, vì cả state layer lẫn UI đều phụ thuộc contract. `example-mobile` nằm ngoài phạm vi (ghi rõ trong SPEC).

---

## 4. Rủi ro

| Rủi ro | Ảnh hưởng | Xử lý |
|---|---|---|
| OQ-05 chưa chốt nhà cung cấp email | Chặn kiểm thử luồng quên mật khẩu đầu-cuối | FE mock trước; chốt trước khi QC chạy bộ TC reset password |
| `users.email` chưa unique ở dữ liệu cũ | Migration `task-1-1` có thể fail lúc tạo index | Kiểm tra và dọn bản ghi trùng trước khi chạy migration lên staging |
| Đổi lock state khi chạy nhiều instance | Đếm sai số lần đăng nhập sai (AC-28) | QueryBuilder thay vì read-modify-write, đã ghi trong `task-2-1` |

---

## 5. Bàn giao

Dev xong → `qa-agent` verify theo AC → QC chạy `test-cases/` đã có sẵn cho `example-api` và `example-web`.
