# Ba Agent — SPEC.md Template Guide

> Chi tiết hướng dẫn điền các sections của `SPEC.md` — được reference từ Bước 4 của `ba-agent.md`.

Cấu trúc bắt buộc:
```markdown
# SPEC: <Feature Name>

## Mô tả nghiệp vụ
## BA Deliverables        ← BẮT BUỘC — entry point cho downstream (TL/Designer/QC), format ở figma-outputs/shared-rules.md
## Source Register        ← BẮT BUỘC — classify từng requirement (FACT/PROPOSAL/INFERENCE/UNKNOWN/CONFLICT) + evidence
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

**⚠️ `## Source Register` — vị trí + nội dung (BẮT BUỘC):**

- Đặt NGAY SAU `## BA Deliverables`, TRƯỚC `## Actors & Preconditions`
- Mục đích: **chống hallucination** — mọi kết luận trong SPEC/Flow/Screen PHẢI trace về source. Downstream (TL/QC/Designer) đọc biết chỗ nào là fact vs propose vs inference vs unknown.
- Bảng bắt buộc:

```markdown
## Source Register

> Mọi statement trong SPEC này PHẢI trace về 1 row dưới. `FACT` = user/BRSE đã confirm; `PROPOSAL` = BA đề xuất, chờ approve; `INFERENCE` = BA suy luận từ context, cần verify; `UNKNOWN` = chưa rõ, đưa vào Q&A; `CONFLICT` = ≥2 source mâu thuẫn.

| ID | Statement | Classification | Evidence (file + section/timestamp/user turn) | Confidence | Used in flow? |
|---|---|---|---|---|---|
| RQ-001 | Actor A phải login trước khi tạo order | FACT | user turn 3 ("phải login trước") | High | Yes — Flow Tổng Quan bước 1 |
| RQ-002 | Payment gateway là elepay | PROPOSAL | BA đề xuất dựa POLICIES §5 | Medium | No — chờ BRSE approve |
| RQ-003 | Refund window 7 ngày | INFERENCE | suy từ industry standard, chưa hỏi | Low | No — đưa vào Q&A |
| RQ-004 | Có SMS OTP hay không? | UNKNOWN | user chưa trả lời | — | No — blocking |
| RQ-005 | Meeting note nói "1 ngày" nhưng SPEC cũ nói "3 ngày" | CONFLICT | meeting 12/09 vs SPEC v2 | — | No — cần BRSE quyết |
```

**Rule bắt buộc:**
- Chỉ `FACT` được đưa vào Happy Path / AC như kết luận chính thức
- `PROPOSAL` phải có badge `[PROPOSAL — chờ BRSE approve]` trong SPEC body nơi được reference
- `INFERENCE` phải có badge `[INFERENCE — cần verify]` + list vào `## Alternative Flows & Edge Cases` như giả định
- `UNKNOWN` và `CONFLICT` KHÔNG được nối vào flow bằng giả định — bắt buộc list vào cuối SPEC section `## Open Questions` (tạo thêm nếu chưa có)

**⚠️ `## BA Deliverables` — vị trí + nội dung:**
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

**Xác định độ chi tiết 1 Screen (BẮT BUỘC đọc trước khi điền bảng Screens) — lỗ hổng đã xảy ra thực tế:**

> Tổng quan nguyên tắc granularity chung (cả Flow lẫn Screen) xem `.claude/ba-agent/granularity-principles.md`.

> Agent từng liệt kê Screen Code y hệt số dòng mà tài liệu nguồn (VD Estimate) liệt kê, thay vì tự phán đoán độc lập UI state nào thực sự là 1 màn hình khác biệt. Hệ quả: 4 biến thể checkout được tách thành 4 Screen Code `Wizard` riêng dù định nghĩa `Wizard` bên dưới vốn dành cho "nhiều bước trong 1 màn hình". Không được lặp lại — chạy đủ Test C + Test D dưới đây cho MỌI cặp UI state gần giống nhau trước khi chốt bảng Screens.

1. **Test C — Distinct Layout/Purpose:** 2 UI state là **1 Screen** nếu dùng chung layout khung + chung điểm vào, chỉ khác field hiện/ẩn theo lựa chọn trước đó hoặc khác data hiển thị. Là **2 Screen khác nhau** nếu cấu trúc layout/kiểu tương tác khác hẳn nhau (VD: bản đồ chọn chỗ ngồi vs. form đếm số lượng + toggle thanh toán) — khác biệt phải nằm ở **cấu trúc UI**, không phải chỉ khác nội dung text.
2. **Test D — Wizard-step reachability:** Nếu 1 UI state chỉ tồn tại tạm thời như 1 bước do 1 lựa chọn trước đó dẫn tới, KHÔNG có lý do cần deep-link/điều hướng riêng tới thẳng nó → đó là **1 step của Screen Type = `Wizard`**, KHÔNG tách Screen Code riêng. Chỉ tách Screen Code riêng khi step đó pass được Test C (khác cấu trúc layout hẳn) VÀ có thể được truy cập/tham chiếu độc lập trong luồng khác.

**Khi nào bảng Screens có nhiều Screen Code "biến thể" của cùng 1 hành động (VD 4 kiểu checkout):** mặc định GỘP thành 1 Screen Type=`Wizard` với các bước mô tả trong `## Screen Details` (section riêng cho từng bước dùng heading phụ `#### Bước <n> — <tên>`), TRỪ KHI Test C xác nhận layout khác hẳn — khi đó giữ tách nhưng PHẢI ghi rõ trong Screen Details lý do tách (`> Tách riêng vì Test C: <lý do cấu trúc layout khác>`).

**Bắt buộc trước khi vẽ Output 2/3 (Figma):** trình bảng Screens đã chốt (kèm lý do gộp/tách theo Test C/D cho các case biến thể) cho user xác nhận — tương tự bước xác nhận N-flow ở Output 1 (`output-1-flow.md`). Không vẽ Figma trước khi user confirm bảng Screens.

**Rule phân loại mức hiển thị lỗi → có sinh Screen Code mới hay không (BẮT BUỘC — quyết định số screen Non-Happy):**

> Lỗ hổng đã xác định khi audit: kit có `## Non-Happy Case` và có NG node ở Output 2, nhưng KHÔNG có rule nào nói lỗi nào cần 1 màn hình riêng, lỗi nào chỉ là state của màn hiện tại. Vì vậy số screen Non-Happy lúc thừa lúc thiếu, hoàn toàn cảm tính.

| Cách hiển thị lỗi | Sinh Screen Code mới? | Ghi ở đâu |
|---|---|---|
| Inline error · Toast · Banner · Tooltip | ❌ **Không** — chỉ là **state** của screen hiện tại | Bảng SCREEN STATES ở Output 3 (`S05-validation-error` / `S06-system-error`) |
| Modal · Popup · Bottom-sheet | ⚠️ **Có nếu** modal mang nội dung nghiệp vụ riêng (VD modal huỷ đơn + chọn lý do + xác nhận).<br>**Không nếu** chỉ là alert 1 nút OK | Có → 1 dòng trong `## Screens`, Screen Type = `Modal` |
| Full screen (hết phiên · không có quyền · thanh toán thất bại · maintenance · 404) | ✅ **Bắt buộc** có Screen Code riêng | 1 dòng trong `## Screens` + 1 block `## Screen Details` |

**Checklist 8 nhóm Non-Happy — rà BẮT BUỘC cho MỌI screen có submit / gọi API:**

| # | Nhóm | Ví dụ |
|---|---|---|
| 1 | Validation input | field trống, sai định dạng, quá độ dài |
| 2 | Auth / session / permission | chưa login, hết session, sai role |
| 3 | Network | mất mạng, timeout, kết nối chập chờn |
| 4 | Server error | 500, service unavailable, maintenance |
| 5 | Empty state | không có dữ liệu, kết quả tìm kiếm rỗng |
| 6 | Conflict | double-submit, bản ghi đã bị người khác sửa/xoá |
| 7 | Business rule violation | hết hàng, quá hạn, vượt hạn mức, chưa đủ điều kiện |
| 8 | External integration fail | payment gateway lỗi, SMS/email không gửi được, 3rd-party timeout |

Nhóm nào không áp dụng → ghi `N/A — <lý do>`. Nhóm nào chưa có evidence từ requirement → ghi `UNKNOWN` (sẽ vào Edge/Exceptional Panel ở Output 2), **KHÔNG tự bịa hành vi**.

---

**Hướng dẫn điền `## Screens`:**

Bảng index tổng hợp — liệt kê **tổng số màn hình** ở đầu section, sau đó 1 dòng per screen.

```markdown
## Screens

> Tổng: <N> màn hình

| Screen Code | Screen | Actor | App | Screen Type | Transition To |
|---|---|---|---|---|---|
| <XX_FEAT_001> | <Tên màn hình> | <Actor> | <Epic code> | <type> | <Screen Code tiếp theo khi action chính> |
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
- `Wizard` — multi-step flow (onboarding, checkout steps) — **mặc định 1 Wizard = 1 Screen Code duy nhất chứa nhiều bước**, xem Test D ở trên; không tách Screen Code riêng cho mỗi bước trừ khi pass Test C
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

| Breakpoint | Screen size (W×H) | Layout changes |
|---|---|---|
| Mobile app | 375×812 | <mô tả> — dùng khi TARGET_PLATFORM = Mobile app |
| Web app (mobile-first) | 375×812 | Same as mobile — dùng khi TARGET_PLATFORM = Web app |
| Website (desktop) | 1440×1024 | Layout chuẩn — dùng khi TARGET_PLATFORM = Website |
| iPad / Tablet | 1024×768 | Landscape — dùng khi TARGET_PLATFORM = iPad/Tablet |

**Quy tắc chung:**
- Navigation: <bottom tab (mobile) / sidebar (desktop) / ...>
- Font scale: <có scale theo viewport không>
- Grid: <breakpoint columns — 1 col mobile / 2 col tablet / 3-4 col desktop>
```

**Quy tắc bắt buộc:**
- Chỉ điền breakpoint tương ứng với `TARGET_PLATFORM` đã chọn, KHÔNG điền tất cả 4 platform nếu dự án chỉ có 1
- Kích thước viewport không được tự đổi (VD không dùng 390×844 hay 1920×1080) — dùng chính xác 4 kích thước chuẩn ở trên
- Nếu feature multi-platform (VD User mobile + Admin website) → điền cả 2 breakpoint và ghi rõ nhóm screen nào dùng platform nào (đối chiếu cột "App" trong `## Screens`)

---

Nếu thiếu thông tin để xác định screens cụ thể → tạo screens hợp lý nhất từ context (đạt ~90% độ chính xác), ghi chú `*` và note cuối bảng.
