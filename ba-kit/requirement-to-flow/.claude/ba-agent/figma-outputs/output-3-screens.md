# Ba Agent — Output 3: Screens + Items + Error Scenarios

## Output 3 — Screens + Bảng ITEMS + Bảng ERROR SCENARIOS (Grouped theo Business Flow)

> **Reference:** xem `final_output_3.png` — layout DỌC N hàng: mỗi hàng = 1 mockup phone/screen + Bảng ITEMS (Action/Behavior) + Bảng ERROR SCENARIOS.

> **⚠️ Prerequisites:** Output 1 và Output 2 PHẢI vẽ xong trước. Output 3 dùng **cùng N business flow groups** đã định nghĩa ở Output 1 và Output 2.

> **⚠️ LAYOUT MỚI (feedback từ user):** Chia thành N groups theo business flow. Trong mỗi group, layout DỌC N mockup rows như cũ.

> **⚠️ Gate B2 BẮT BUỘC — hỏi user TRƯỚC khi vẽ Output 3 (không skip)**
>
> Khi bắt đầu Output 3, BA PHẢI đã hỏi Gate B2 ở `shared-rules.md` — user đã confirm 2 thứ:
>   1. Có muốn tạo Output 3 không? (nếu KHÔNG → skip Output 3, ghi vào bảng status "❌ Skipped — user quyết không cần")
>   2. Scope Output 3: TOÀN BỘ N flows / CHỈ 1 flow / BATCH M screens
>
> **Ứng xử theo lựa chọn:**
>
> | User chọn ở Gate B2 | Áp dụng vào Output 3 |
> |---|---|
> | `[A] TOÀN BỘ N flows` | Vẽ đủ N groups tương ứng N business flows Output 2. Coverage Rule bên dưới BẮT BUỘC pass. |
> | `[B] CHỈ 1 flow "<Tên flow>"` | Vẽ 1 group cho flow user chỉ định. Các flow còn lại → KHÔNG vẽ. Ghi vào bảng status Output 3: "⚠️ Partial — user chọn vẽ 1/N flows: `<Tên flow>`. Flows còn lại: [list N-1 flows] — chờ user quyết định vẽ tiếp." |
> | `[C] BATCH M screens/lượt` | Vẽ batch đầu tiên gồm M screens (theo thứ tự Happy Path). Sau mỗi batch DỪNG hỏi user "vẽ tiếp batch kế không?" trước khi tiếp tục. |
>
> **NGHIÊM CẤM:**
> - ❌ Tự vẽ toàn bộ N flows khi user chưa confirm scope
> - ❌ Tự chọn 1 flow "quan trọng nhất" thay user
> - ❌ Vẽ Output 3 trước khi hỏi Gate B2 (dù thấy Output 2 chỉ có 1 flow — vẫn phải hỏi "có muốn tạo Output 3 không")

**Bố cục frame Output 3:**

```
┌─── Group 1 — Flow 1: <Tên business flow từ Output 1> ────┐
│                                                           │
│  Row 1: [Mockup] [Bảng ITEMS] [Bảng ERROR SCENARIOS]     │
│  Row 2: [Mockup] [Bảng ITEMS] [Bảng ERROR SCENARIOS]     │
│  Row N: [Mockup] [Bảng ITEMS] [Bảng ERROR SCENARIOS]     │
│                                                           │
└───────────────────────────────────────────────────────────┘
                        gap 150px
┌─── Group 2 — Flow 2 ─────────────────────────────────────┐
│  ...                                                      │
└───────────────────────────────────────────────────────────┘
                        ...
┌─── Group N — Flow N ─────────────────────────────────────┐
│  ...                                                      │
└───────────────────────────────────────────────────────────┘
```

**Rule chính:**
- Số groups = số business flows Output 1 = số screen-flow groups Output 2 (cross-verification)
- Mỗi group đặt vertically stacked, gap MIN 150px giữa 2 groups
- Trong mỗi group: tiêu đề group ở đầu (label + số mockup rows), sau đó các mockup rows theo thứ tự Happy Path của screen-flow tương ứng
- **Format bảng ITEMS + ERROR SCENARIOS giữ nguyên** như spec cũ (feedback từ user: "Format vẫn giữ như cũ")

**⚠️ COVERAGE RULE — BẮT BUỘC (không được tự pragmatic):**

Output 3 PHẢI vẽ **ĐỦ TẤT CẢ** màn hình đã liệt kê trong Output 2 Bảng Index (bao gồm Popup, Toast, Banner, Push nếu chúng xuất hiện dưới dạng screen node riêng trong Index).

- Nếu Output 2 Bảng Index có **N screens** → Output 3 PHẢI có **N mockup rows** (phân bổ trong các groups theo flow chúng thuộc về)
- KHÔNG bỏ qua screen với lý do "Form đơn giản" / "List chuẩn" / "đã hiểu rồi" / "quá nhiều"
- Popup / Modal / Toast: dùng phone/screen mockup theo viewport chuẩn với overlay hiển thị bên trong
- 1 screen có thể xuất hiện trong nhiều groups nếu nó thuộc nhiều flows (VD screen Login xuất hiện trong flow Application + Scout) — vẽ mockup 1 lần ở group đầu tiên, các group sau chỉ reference bằng Screen Code (không vẽ lại)

**Nếu N > 20 (số lượng lớn)** → BẮT BUỘC hỏi user TRƯỚC KHI vẽ theo template:

```
⚠️ Output 3 sẽ vẽ N màn hình (từ Output 2 Bảng Index).
   Ước lượng effort: ~<N × 5> phút vẽ, Figma file lớn.

   Chọn 1:
   [A] Vẽ đủ N màn hình (recommended — chuẩn Definition of Done)
   [B] Vẽ theo phases: batch 20 màn hình / lượt, user review từng batch
   [C] Vẽ M màn hình đại diện (M < N) — user chỉ định danh sách cụ thể + đồng ý ⚠️ Partial trong bảng status cuối
```

Chỉ khi user explicitly chọn [B] hoặc [C] mới được vẽ ít hơn N. Mặc định = [A]. **KHÔNG được tự quyết định vẽ ít**.

**Layout chính xác (viewport theo `TARGET_PLATFORM` — hỏi ở Bước 2b):**
- Frame width **1500px** (Mobile / Web app / Tablet) hoặc **2560px** (Website desktop) tuỳ platform
- Mỗi hàng: `ROW_HEIGHT` dynamic (cao đủ chứa items table + errors table)
- Phone/Screen mockup viewport:
  - Mobile app / Web app: `375×812` (x=40..415)
  - Website desktop: `1440×1024` (đặt hàng ngang cạnh tables, hoặc row cao hơn)
  - iPad/Tablet: `1024×768`
- Tables: đặt bên phải mockup, width ~990 (Mobile/Web app/Tablet) hoặc ~1000 (Website)
  - Bảng ITEMS ở TRÊN
  - Gap 20px
  - Bảng ERROR SCENARIOS ở DƯỚI
- Number badges đặt TRÊN mỗi item trong phone

**Bảng ITEMS (bảng 1):**
- 4 cột: `# | Title (Tên item) | Mô tả | Action / Behavior`
- Column offsets: 8 · 40 · 220 · 430
- Row height dynamic: 48 (nếu no action) / 68 (medium) / 88 (long)
- Fill WHITE, stroke DIV, cornerRadius 8

**Bảng ERROR SCENARIOS (bảng 2 — BẮT BUỘC dưới Items):**
- Fill `cv(255,251,251)` (hồng nhạt), stroke RED, cornerRadius 8
- 4 cột: `# | Trigger (nguyên nhân) | Hiển thị | Message + Action tiếp theo`
- Column offsets: 8 · 40 · 240 · 370
- Row height: 68 hoặc 88 nếu msgAction > 100 chars
- Cột "Hiển thị" dùng enum: Toast · Modal · Popup · Banner · Tooltip · Empty state · Push notification · Auto dismiss

**Cột Action / Behavior format:**
- Không có action → `"—"` (visual only)
- Có action → `"TAP → <đích>. Happy: <mô tả>. Error nếu <trigger> → <hiển thị>"`

**Cột Message + Action tiếp theo format:**
- `"Text: '<message>' + Nút [<action>] <mô tả>"`
- `"Text: '<message>'. Action: auto <chuyển đâu>, log '<status>'"`

**KHÔNG ghi thông số design** (px, hex color, font size, border-radius) — đó là việc của Designer-agent.
**Chỉ tập trung:** liệt kê ĐẦY ĐỦ item + tương tác + luồng lỗi.

**⚠️ NGUYÊN TẮC CỐT LÕI: KHÔNG LƯỢC BỎ ITEM NÀO**

Trên màn hình có bao nhiêu item hiển thị thì liệt kê hết bấy nhiêu:
- Nút / Button
- Input / Textbox / Dropdown
- Label / Text hiển thị
- List item / Row
- Icon / Badge / Status dot
- Tab / Filter
- Avatar / Image
- Divider / Section header
- FAB / Menu / Sidebar item
- Modal trigger / Popup trigger

**Format bảng bên cạnh mỗi màn hình:**

```markdown
### <Screen Code>  ·  <Screen Name>

**Mục đích màn hình:** <1 câu>

**Danh sách items:**

| # | Title (Tên item) | Mô tả | Mục đích |
|---|---|---|---|
| ① | Nút "Gọi ngay" | Nút chính màu xanh ở dưới cùng | Kích hoạt cuộc gọi tới Actor B (Receiver) |
| ② | Avatar company | Ảnh tròn với chữ đầu tên cty | Nhận biết trực quan công ty đang xem |
| ③ | Badge trạng thái | Pill hiển thị Online/Offline/Busy | Cho biết CA có sẵn sàng nhận gọi không |
| ④ | Row "Địa chỉ" | Label + giá trị | Hiển thị địa chỉ công ty |
| ⑤ | Row "Đơn hàng active" | Label + số đơn với badge | Hiển thị số đơn đang xử lý |
| ⑥ | Row "Điện thoại" | Label + số điện thoại | Hiển thị số ĐT liên hệ |
| ⑦ | Section header "Cuộc gọi gần đây" | Text bold + link "Xem tất cả" | Chuyển hướng nhanh tới Call History |
| ⑧ | Call history item (×3) | Icon + tên + duration + timestamp | Xem 3 cuộc gọi gần nhất |
| ⑨ | Nút back ← | Icon mũi tên top-left | Quay lại Company List |

**Logic màn hình:**

- **Happy Case:**
  1. User vào từ Company List → thấy full thông tin
  2. Đọc trạng thái → quyết định gọi
  3. Tap [Gọi ngay] → Outgoing Call

- **Buttons / Actions:**
  - [Gọi ngay] → AX_FEAT_003 (disabled khi Offline/Busy + tooltip)
  - [Xem tất cả →] → AX_FEAT_006
  - [←] → AX_FEAT_001

- **⚠ Non-Happy:**
  - CA Offline → Nút disabled + tooltip "Không online"
  - CA Busy → Nút disabled + tooltip "Đang trong cuộc gọi khác"
```

**⚠️ QUY TẮC XÁC ĐỊNH ITEM:**

Xem mockup HiFi (do Designer tạo) hoặc SPEC.md `## Screen Details`, đánh số **TẤT CẢ** element user thấy được:
- Nếu trên màn hình có 5 nút → phải liệt kê 5 nút, không lược
- Nếu list có template row (repeat) → liệt kê 1 row + ghi chú "×N"
- Divider và section header → **CÓ đếm** (giúp Designer/Dev không quên)
- Whitespace decorative → không đếm

**Ví dụ ĐÚNG:** 12 items → bảng có 12 dòng.
**Ví dụ SAI:** Màn hình có 15 items nhưng bảng chỉ ghi 5 → **thiếu**, phải bổ sung.

---

## ⚠️ 4 phép kiểm "đủ item hay chưa" (BẮT BUỘC — chống thiếu từ gốc)

> **Lỗ hổng đã xác định khi audit:** `recheck.md` Tiêu chí 5 chỉ đối chiếu **NỘI BỘ** (badge trên mockup vs row trong bảng của chính nó). Nếu BA liệt kê thiếu ngay từ đầu thì cả hai cùng thiếu như nhau → **vẫn PASS**. Bắt buộc phải có ít nhất 1 phép đối chiếu với nguồn NGOÀI.

### Phép 1 — Đối chiếu chéo với SPEC (phép kiểm NGOÀI, bắt buộc)

> `số item bảng ITEMS` **≥** `số row bảng Components trong SPEC ## Screen Details` của chính screen đó

- Thiếu → **FAIL**, phải bổ sung trước khi báo xong
- Thừa là **bình thường và đúng** — Output 3 chi tiết hơn SPEC (divider, section header, badge, status dot mà SPEC không liệt kê)

### Phép 2 — Rà theo VÙNG, không rà theo LOẠI (zone sweep)

> Checklist 10 loại ở trên rà theo **loại**; phép này rà theo **không gian**. Con người và LLM đều quét màn hình theo vùng — rà theo loại rất dễ sót nguyên một vùng (hay sót nhất: overlay và trạng thái phụ).

| # | Vùng | Phải kiểm |
|---|---|---|
| 1 | Status bar / Header | back, title, action bên phải |
| 2 | Navigation | tab bar, drawer, breadcrumb, stepper |
| 3 | Body — nội dung chính | list / form / detail content |
| 4 | Body — trạng thái phụ | empty state, loading skeleton, inline error |
| 5 | Footer / CTA | nút chính, nút phụ, disclaimer |
| 6 | Overlay | modal, toast, tooltip, bottom-sheet, snackbar |

Mỗi vùng PHẢI có ≥1 dòng trong bảng ITEMS **hoặc** ghi rõ `N/A — <lý do>`.

### Phép 3 — Ngưỡng cảnh báo tối thiểu theo Screen Type

> KHÔNG fail cứng (có màn thật sự đơn giản) — nhưng BẮT BUỘC in cảnh báo và hỏi user. Cùng tinh thần "smoke detector" như Test E (Cardinality Budget) ở Output 1.

| Screen Type | Số item tối thiểu hợp lý |
|---|---|
| `Form` | ≥ số field + submit + validation message + back (thường ≥ 6) |
| `List` | ≥ 6 (header · search/filter · sort · row template · empty state · pagination) |
| `Detail` | ≥ 5 |
| `Dashboard` | ≥ 6 |
| `Modal` | ≥ 3 (title · body · ≥1 action) |
| `Wizard` | ≥ (số bước × 3) + progress indicator |

Dưới ngưỡng → in: `⚠️ <Screen Code> chỉ có N item — dưới ngưỡng tối thiểu của type <T>. Xác nhận màn này thật sự đơn giản, hay tôi đang liệt kê thiếu?`

### Phép 4 — Đảo chiều check Navigation Mapping

> `số item có cột Action ≠ "—"` **=** `số row Navigation Mapping có From = screen đó`

Rule hiện có chỉ nói "mọi item phải có ≥1 row" (chiều xuôi). Phép đếm ngược này bắt được trường hợp bảng Navigation Mapping bị bỏ sót dòng.

### Câu hỏi bắt buộc trong Self-Feedback Output 3 — *implied items*

> Mượn từ skill **Business Analyst Reviewer** (marketplace): *"Are there implied requirements not captured?"*

Sau khi liệt kê xong, BA PHẢI tự hỏi và trả lời trong self-feedback:

```
Item nào là IMPLIED — user chắc chắn cần nhưng requirement không bao giờ viết ra — mà tôi chưa liệt kê?
Nhóm hay thiếu nhất: nút back · loading indicator · empty state · pull-to-refresh ·
confirm khi thoát form đang nhập dở · disabled state của CTA · error inline dưới field
```

Đây đúng là nhóm item mà Dev luôn phải hỏi lại khi build nếu BA bỏ sót.

**Ví dụ ĐÚNG (logic-focused):**
```
BUTTONS:
• [Gọi ngay] → AX_FEAT_003 (Outgoing Call)
• [Gọi ngay] disabled khi: Actor B (Receiver) đang Offline hoặc Busy
  → tooltip: "Actor B (Receiver) hiện không thể nhận cuộc gọi"
```

**Ví dụ SAI (design-focused — KHÔNG làm):**
```
❌ Nút [Gọi ngay]: 48px cao, bo góc 6px, nền #0969da, text Bold 16px
❌ Toast: nền #fff6f5, border 1px #ffbbb9, Regular 13px #cf222e
```

**BA KHÔNG tạo:** px, hex color, font-size, border-radius, component instances → đó là Designer-agent.

---

## Bổ sung 2 bảng mới cạnh Bảng ITEMS + ERROR SCENARIOS (BẮT BUỘC)

> 2 bảng dưới đây bổ sung **CẠNH** bảng ITEMS/ERROR SCENARIOS hiện tại (đặt DƯỚI, cùng width). KHÔNG thay mockup phone. Mục đích: cho TL Design + QC + FE Dev đủ thông tin về states và navigation trace-back.

### Bảng 3 — SCREEN STATES (8 state chuẩn)

> Bắt buộc list mọi state screen có thể ở, không được silent-skip. State nào chưa có evidence → đánh dấu `UNKNOWN`.

| State ID | Trigger | Visible / disabled items | System behavior | Exit condition |
|---|---|---|---|---|
| S01-default | Load lần đầu, đủ điều kiện | Tất cả items enabled | — | Tap CTA |
| S02-loading | Đang fetch data | Skeleton loader thay content; CTA disabled | GET /api/... | Response về |
| S03-success | Action success | Toast success + navigate | Redirect S1 kế | Auto 2s |
| S04-empty | Data trống | Empty illustration + "Chưa có..." | — | Tap "Tạo mới" |
| S05-validation-error | Form field invalid | Inline error dưới field; CTA disabled | — | User sửa field |
| S06-system-error | API 500 / network | Banner đỏ + "Thử lại"; CTA disabled | Log Sentry | Tap Retry |
| S07-disabled | Precondition không đủ (VD: chưa verify email) | CTA disabled + tooltip lý do | — | User đi verify |
| S08-permission-denied | User không đủ role | Overlay + "Không có quyền" | Log audit | Back |

**Rule bắt buộc:**
- 8 state là **checklist tối đa** — nếu screen không có state nào (VD Detail read-only chỉ có S01 + S06) → xóa row không dùng, ghi note `Chỉ có 2/8 states`
- State chưa có evidence từ SPEC/user → đánh `UNKNOWN` vào cột System behavior, KHÔNG tự invent
- Row S05/S06 phải link về Exception Matrix ID trong Output 2 (VD "xem EX-01, EX-03")

### Bảng 4 — NAVIGATION MAPPING (trace về Flow Manifest + Source Register)

> Bảng này cho phép QC + FE Dev trace từng action trên screen về đúng transition trong Flow Output 2 VÀ về requirement gốc trong Source Register (SPEC.md). Chống drift 2 chiều: giữa screen action ↔ flow diagram, và giữa screen action ↔ requirement.

| User/System action | From | Condition | To | Manifest transition ID | Source RQ-ID |
|---|---|---|---|---|---|
| Tap [Gọi ngay] | AX_FEAT_002 | CA Online | AX_FEAT_003 | CALL_D01_ONLINE | RQ-012 |
| Tap [Gọi ngay] | AX_FEAT_002 | CA Offline | (disabled) | — | RQ-015 |
| Tap [Gọi ngay] | AX_FEAT_002 | CA Busy | Tooltip "Đang bận" | — | RQ-016 |
| Tap [Xem tất cả →] | AX_FEAT_002 | — | AX_FEAT_006 | HISTORY_NAV | RQ-020 |
| Tap [←] | AX_FEAT_002 | — | AX_FEAT_001 | BACK_NAV | — (UI convention) |
| System push arrival | AX_FEAT_003 | Actor B pick up | AX_FEAT_004 | CALL_D02_PICKUP | RQ-013 |
| System timeout 30s | AX_FEAT_003 | Actor B không pick | AX_FEAT_005 (missed) | CALL_D02_TIMEOUT | RQ-014 |

**Rule bắt buộc:**
- Mọi button / interactive element trong Bảng ITEMS PHẢI có ≥ 1 row trong Navigation Mapping (kể cả action = `—` cho disabled state)
- Cột "Manifest transition ID" trace về Flow diagram Output 2 — format `<FLOW>_<DECISION>_<CONDITION>` (VD `CALL_D01_ONLINE`). Nếu Output 2 chưa có transition ID → BA phải quay lại Output 2 thêm ID.
- **Cột "Source RQ-ID"** trace về row trong `## Source Register` (SPEC.md):
  - Row có business logic → PHẢI có RQ-ID (VD `RQ-012`) — nếu không có → row Source Register thiếu, BA phải bổ sung trước
  - Row là UI convention thuần túy (back button, close icon) → để `— (UI convention)` explicit, không được để trống
  - Row có RQ-ID classification `UNKNOWN` / `PROPOSAL` trong Source Register → thêm badge `⚠ UNKNOWN` / `⚠ PROPOSAL` sau ID (VD `RQ-021 ⚠ UNKNOWN`)
- Row không có Manifest transition (VD tooltip disabled) → cột ID để `—`, nhưng phải có row để explicit "không navigate đi đâu"

**Cross-verification khi Quality Gate O3:**
- 100% Source RQ-ID phải tồn tại trong `## Source Register` — grep check
- Row có Source RQ-ID `UNKNOWN` → phải có tương ứng entry trong Exception Matrix Output 2 (không được silent skip)

**Downstream impact:**
- FE Dev đọc bảng này biết đúng route + condition
- QC đọc bảng này viết test case cho từng transition
- TL Design verify không có action nào bị orphan (button không dẫn đi đâu mà không có lý do rõ ràng)
