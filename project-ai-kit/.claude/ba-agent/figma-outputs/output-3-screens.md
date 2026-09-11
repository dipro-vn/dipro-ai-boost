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
