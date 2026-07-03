# Flutter Maintenance — Common Rules

> **Scope:** Áp dụng cho **mọi Flutter project** khi nhận maintain (project từ client hoặc internal handoff).
> **Triết lý:** Ưu tiên **không phá vỡ** những gì đang chạy → **follow convention hiện có** → **chuẩn hóa dần** qua backlog.
> **Baseline file:** Đây là `common rules`. Pattern-specific rules (vd `riverpod-clean-architecture`) sẽ bổ sung, không override phần này.

---

## 0. Nguyên tắc cốt lõi

1. **Đọc trước, sửa sau.** Không chạm code khi chưa hiểu pattern hiện tại.
2. **Không refactor code đang chạy** trừ khi task yêu cầu rõ ràng.
3. **Follow existing convention** > áp convention mới.
4. **Nhất quán** trong 1 project (state management, routing, network) — không mix pattern.
5. **Mọi cleanup / chuẩn hóa** phải có task riêng, không gộp vào feature.

---

## 1. AUDIT_BEFORE_TOUCH — Làm đầu tiên khi nhận project

- Đọc toàn bộ `pubspec.yaml` trước khi chạm bất kỳ package nào.
- Liệt kê: **state management**, **DI framework**, **navigation approach** đang dùng.
- Ghi lại deprecated API / outdated packages (**không fix ngay** — đưa vào backlog).
- Xác định có **flavor / environment config** không (dev / stg / prod).
- Tìm **naming & folder convention** hiện có trong code (không tự đặt mới).
- Chạy thử `flutter analyze` + build 1 lần để nắm baseline error/warning.

---

## 2. DO_NOT_REFACTOR_WORKING_CODE

- Không refactor code đang hoạt động trừ khi task yêu cầu rõ ràng.
- Không đổi state management giữa chừng (vd: không tự chuyển `setState` → Riverpod nếu không có migration plan).
- Không update package version không liên quan tới task đang làm.
- Mọi "cleanup" phải có ticket riêng — **không gộp vào feature task**.

---

## 3. FOLLOW_EXISTING_NAMING

- Nếu project dùng `snake_case` cho file → tiếp tục `snake_case`.
- Nếu widget đặt tên `XxxScreen` → không tự đổi thành `XxxPage`.
- Nếu có prefix widget (`AppButton`, `AppText`) → tiếp tục dùng prefix đó.
- Chỉ áp dụng Dart official naming khi project **chưa có** convention.

**Fallback (Dart official) nếu project chưa có convention:**

| Loại | Convention |
|---|---|
| Files / folders | `snake_case` |
| Classes / enums / typedefs | `PascalCase` |
| Variables / methods / params | `camelCase` |
| Constants | `lowerCamelCase` (không phải `SCREAMING_SNAKE`) |
| Private members | `_camelCase` |

---

## 4. MAINTAIN_FOLDER_STRUCTURE

- Không tự tạo layer mới (`usecase/`, `domain/`) nếu project không có sẵn.
- **Feature-first** → thêm file vào đúng feature folder.
- **Layer-first** → thêm file vào đúng layer folder.
- Không trộn 2 pattern trong cùng project.

**Cách nhận biết:**

- Feature-first: `lib/features/auth/screens/`, `lib/features/home/…`
- Layer-first: `lib/screens/`, `lib/services/`, `lib/models/…`

---

## 5. STATE_MANAGEMENT_CONSISTENCY

- Xác định pattern hiện tại: `setState` / Provider / Bloc / Riverpod / GetX.
- Chỉ dùng đúng pattern đó cho toàn bộ task mới.
- Nếu bắt buộc thêm solution mới → **document lý do + migration plan**.

**Nhận biết nhanh qua `pubspec.yaml`:**

| Package | Pattern |
|---|---|
| `flutter_bloc` / `bloc` | Bloc / Cubit |
| `riverpod` / `flutter_riverpod` | Riverpod |
| `get` | GetX |
| `provider` | Provider |
| (không có gì) | `setState` thuần |

---

## 6. WIDGET_STANDARDS

- Prefer `StatelessWidget` trừ khi cần local state.
- Extract widget khi `build()` vượt ~80 lines.
- **Không** dùng `const` widget nếu project cũ không dùng (tránh lint conflict).
- Tránh nested `Scaffold`.
- Không hardcode màu / font trực tiếp nếu project có `ThemeData`.
- Kiểm tra `lib/widgets/` hoặc `lib/common/` **trước khi tạo widget mới** (tránh duplicate).

---

## 7. NAVIGATION_CONSISTENCY

- Xác định: Navigator 1.0 / GoRouter / AutoRoute / GetX routing.
- Không tự thêm GoRouter vào project đang dùng `Navigator.push()`.
- Route names theo convention đã có (string literal / enum / constant).

**Không được làm:**

- Mix `Navigator.push()` và GoRouter trong cùng project.
- Hardcode route string inline (phải dùng constant / enum).

---

## 8. NETWORK_LAYER

- Không thêm `http` nếu project đang dùng `dio` (và ngược lại).
- Tất cả API call đi qua **repository / service layer** — không gọi thẳng trong widget.
- Error handling nhất quán: chọn 1 (either/result pattern **hoặc** try-catch).
- Base URL / endpoint nằm trong `constants / config` — **không hardcode**.

**Trước khi viết API mới:**

- API này đã có trong existing service chưa?
- Response model đã có chưa (tránh duplicate model)?

---

## 9. ASSETS_AND_L10N

- Không thêm asset vào `pubspec` mà không đặt đúng folder convention.
- Hình ảnh: kiểm tra đã có `1x / 2x / 3x` chưa.
- Nếu project có l10n (`.arb`) → **không hardcode string UI**.
- Nếu project chưa có l10n → không tự thêm, **document lại để backlog**.
- `AppColors / AppStrings / AppDimensions` — nếu có thì dùng, không tự đặt tên khác.

---

## 10. CODE_QUALITY_PRAGMATIC

- Chạy `flutter analyze` trước khi commit → **zero error** (warning có thể pending).
- Không suppress lint (`// ignore:`) trừ khi có comment giải thích.
- Không để `print()` trong production code — dùng `logger` nếu có sẵn.
- TODO phải có format: `// TODO(tên): mô tả` — không để TODO trống.

**Không bắt buộc ngay (đưa vào backlog):**

- 100% test coverage.
- Extract toàn bộ widget thành file riêng.
- Full documentation comment.

---

## 11. MAINTAIN_DOCS

- Fix bug → ghi **root cause** trong commit message / PR description.
- Thêm workaround → comment rõ: `// WORKAROUND: lý do (+ link issue nếu có)`.
- Breaking change khi update package → ghi changelog local.
- README phải có: setup, env vars, flavor/scheme, cách run.

**ADR (Architecture Decision Record)** — nếu có quyết định lớn:

- Ghi: `context / decision / consequences`.
- Đặt trong `docs/adr/` hoặc tương đương.

---

## 12. Priority khi nhận project

| Priority | Action |
|---|---|
| **P0** | Audit: đọc pubspec, chạy thử, xác định pattern |
| **P0** | Không thay đổi gì chưa có task |
| **P1** | Follow naming / folder convention hiện có |
| **P1** | Consistent state management + routing |
| **P2** | Code quality: zero error, no print, no hardcode |
| **P3** | Chuẩn hóa dần qua backlog task |

---

## Checklist nhanh trước mỗi commit

- [ ] `flutter analyze` → zero error
- [ ] Không có `print()` / lint suppress không giải thích
- [ ] Follow đúng naming + folder + state management của project
- [ ] Không refactor / update package ngoài scope task
- [ ] Commit message theo Conventional Commits
- [ ] PR chỉ 1 concern, có mô tả what/why/how-to-test
