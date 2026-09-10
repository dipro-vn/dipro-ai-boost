# Ba Agent — SPEC.md Template Guide

> Chi tiết hướng dẫn điền các sections của `SPEC.md` — được reference từ Bước 4 của `ba-agent.md`.

Cấu trúc bắt buộc:

```markdown
# SPEC: <Feature Name>

## Mô tả nghiệp vụ

## BA Deliverables

## Actors & Preconditions

## Flow Tổng Quan

## Happy Path

## Alternative Flows & Edge Cases

## Acceptance Criteria

## Out of Scope

## Screens

## Screen Details

## Responsive Requirements
```

> Copy nguyên văn các dòng `## ` ở trên — **không thêm chú thích vào cuối dòng heading**. Tool kiểm tra SPEC khớp heading chính xác sau khi trim, một chữ dính đuôi là section coi như thiếu.

**⚠️ `## BA Deliverables` — BẮT BUỘC, entry point cho downstream (TL/Designer/QC) — vị trí + nội dung:**

- Đặt NGAY SAU `## Mô tả nghiệp vụ`, TRƯỚC `## Actors & Preconditions`
- Chứa đủ 6 outputs (SPEC.md + 3 Figma Frames + HTML Prototype + MkDocs Site) với path/URL clickable
- Có "Downstream instructions" — chỉ rõ TL Design / Designer / QC dùng phần nào của SPEC + Figma
- Format chi tiết → xem `.claude/ba-agent/figma-outputs/shared-rules.md` section "Post-Delivery requirement"
- Bước 4 của ba-agent tạo skeleton (rows với `<URL>` placeholder). Bước 5 fill Figma URLs. Cuối cùng tất cả 6 rows đều có value hoặc `❌ Skipped — <lý do>`.

---

**Hướng dẫn điền `## Flow Tổng Quan`:**

Mô tả toàn bộ luồng bằng ký hiệu `→` để bất kỳ stakeholder nào đọc xong hình dung được ngay. Bắt buộc bao gồm cả nhánh lỗi / non-happy.

```markdown
## Flow Tổng Quan

<Actor> → <Bước 1> → <Bước 2> → <Bước 3> → <Kết quả>
↓ [Lỗi X]
<Màn hình lỗi / message>
```

Ví dụ:

```
User → Mở App → Login Screen → Nhập credentials → [OK] → Home Screen
                                                 → [Sai pass] → Toast "Sai mật khẩu" → Login Screen
                                                 → [Quên pass] → Forgot Password Screen → Gửi email
```

---

**Hướng dẫn điền `## Screens`:**

Bảng index tổng hợp — liệt kê **tổng số màn hình** ở đầu section, sau đó 1 dòng per screen.

```markdown
## Screens

> Tổng: <N> màn hình

| Screen Code   | Screen         | Actor   | App         | Screen Type | Transition To                            |
| ------------- | -------------- | ------- | ----------- | ----------- | ---------------------------------------- |
| <XX_FEAT_001> | <Tên màn hình> | <Actor> | <Epic code> | <type>      | <Screen Code tiếp theo khi action chính> |
```

Notation chuyển màn hình (ghi vào cột **Transition To**):

- Happy path: `→ XX_FEAT_002`
- Conditional: `[OK] → XX_FEAT_002 / [Lỗi] → Modal lỗi`
- External: `→ Email gửi / → Push notification`

- **Screen Code**: `<Module(2)>_<Feature(4)>_<Seq(3)>` — theo `.claude/context/business-flows/screen-code-rule.md`
  - Module: prefix lấy từ Epic code của từng repo trong bảng Ecosystem (`AGENTS.md`)
  - Feature: 4 chữ hoa viết tắt từ tên feature (ví dụ: `MENU`, `AUTH`, `PAYM`, `DLVR`, `CONT`)
  - Seq: `001`, `002`, `003`... theo thứ tự screen trong feature
  - Unique toàn dự án — không trùng với screen khác
- **Screen Type**: `List` · `Form` · `Detail` · `Dashboard` · `Modal` · `Card-list` · `Chat` · `Wizard` · `Calendar` · `Report` · `Settings`

**Screen Type guide:**

- `List` — bảng dữ liệu có filter/search/pagination
- `Form` — tạo mới hoặc chỉnh sửa record
- `Detail` — xem chi tiết 1 record, read-only hoặc có action buttons
- `Dashboard` — overview với stats, KPIs, summary cards
- `Modal` — popup/dialog overlay (không phải full page)
- `Card-list` — danh sách dạng card (chủ yếu mobile)
- `Chat` — giao diện chat/AI
- `Wizard` — multi-step flow (onboarding, checkout steps)
- `Calendar` — lịch, schedule view
- `Report` — biểu đồ, báo cáo, export
- `Settings` — cài đặt, toggle, configuration

---

**Hướng dẫn điền `## Screen Details`:**

Mỗi screen trong bảng Screens phải có 1 block chi tiết theo format sau. Đây là input chính cho Designer tạo Figma — càng chi tiết Designer càng ít phải hỏi lại.

```markdown
## Screen Details

### <Screen Code> — <Screen Name>

**Happy Case:**

- Layout: <mô tả layout tổng quan — tab/section/panel>
- Components:
  | Vị trí | Component | Nội dung | Action |
  |---|---|---|---|
  | Header | <tên> | <hiển thị gì> | <tap/click đi đâu> |
  | Body | <tên> | <hiển thị gì> | <tap/click đi đâu> |
  | Footer | <tên> | <hiển thị gì> | <tap/click đi đâu> |
- Interactions: Hover → <...> / Swipe → <...> / Long-press → <...>
- Animation đề xuất: <fade-in / slide-up / skeleton loader / none>

**Non-Happy Case:**
| Trigger | Hiển thị | Message |
|---|---|---|
| <điều kiện gây lỗi> | <Toast / Modal / Inline error / Banner> | "<nội dung message>" |
```

Ví dụ:

```markdown
### AU_AUTH_001 — Login Screen

**Happy Case:**

- Layout: Single-column, centered card
- Components:
  | Vị trí | Component | Nội dung | Action |
  |---|---|---|---|
  | Top | Logo | App logo | — |
  | Body | Input | Email field | — |
  | Body | Input | Password field (masked) | — |
  | Body | Link | "Quên mật khẩu?" | → AU_AUTH_003 |
  | Bottom | Button primary | "Đăng nhập" | Submit → AU_AUTH_002 |
- Interactions: Button disabled khi form trống
- Animation đề xuất: Skeleton loader trong 300ms

**Non-Happy Case:**
| Trigger | Hiển thị | Message |
|---|---|---|
| Sai email/password | Toast error | "Email hoặc mật khẩu không đúng" |
| Account locked | Modal | "Tài khoản đã bị khoá. Liên hệ admin." |
| Mất mạng | Banner | "Không có kết nối mạng. Thử lại." |
```

---

**Hướng dẫn điền `## Responsive Requirements`:**

Sử dụng đúng viewport chuẩn theo `TARGET_PLATFORM` (đã hỏi ở Bước 2b Câu hỏi 0):

```markdown
## Responsive Requirements

| Breakpoint             | Screen size (W×H) | Layout changes                                      |
| ---------------------- | ----------------- | --------------------------------------------------- |
| Mobile app             | 375×812           | <mô tả> — dùng khi TARGET_PLATFORM = Mobile app     |
| Web app (mobile-first) | 375×812           | Same as mobile — dùng khi TARGET_PLATFORM = Web app |
| Website (desktop)      | 1440×1024         | Layout chuẩn — dùng khi TARGET_PLATFORM = Website   |
| iPad / Tablet          | 1024×768          | Landscape — dùng khi TARGET_PLATFORM = iPad/Tablet  |

**Quy tắc chung:**

- Navigation: <bottom tab (mobile) / sidebar (desktop) / ...>
- Font scale: <có scale theo viewport không>
- Grid: <breakpoint columns — 1 col mobile / 2 col tablet / 3-4 col desktop>
```

**Quy tắc bắt buộc:**

- Chỉ điền breakpoint tương ứng với `TARGET_PLATFORM` đã chọn, KHÔNG điền tất cả 4 platform nếu dự án chỉ có 1
- Kích thước viewport không được tự đổi (VD không dùng 390×844 hay 1920×1080) — dùng chính xác 4 kích thước chuẩn ở trên
- Nếu feature multi-platform (VD Doctor mobile + Admin website) → điền cả 2 breakpoint và ghi rõ nhóm screen nào dùng platform nào (đối chiếu cột "App" trong `## Screens`)

---

Nếu thiếu thông tin để xác định screens cụ thể → tạo screens hợp lý nhất từ context (đạt ~90% độ chính xác), ghi chú `*` và note cuối bảng.
