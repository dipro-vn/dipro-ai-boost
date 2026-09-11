# Ba Agent — Figma Outputs Shared Rules

> Rules dùng chung cho Output 1 / 2 / 3. BẮT BUỘC đọc trước khi vẽ bất kỳ output nào.

---

## ⚠️ Sequential Rule cho Output 1 → 2 → 3 (BẮT BUỘC — không parallel)

Output 1, 2, 3 PHẢI vẽ theo thứ tự tuần tự, KHÔNG được vẽ song song:

1. **Output 1** — Flow Tổng Quan phải vẽ XONG trước (đây là source of truth về số business flows N)
2. **Output 2** — Screen Flow dựa vào Output 1: PHẢI vẽ N screen-flows tương ứng với N business flows từ Output 1 (VD Output 1 có 5 flows → Output 2 có 5 screen-flows). Bảng SCREEN INDEX tổng hợp vẫn giữ.
3. **Output 3** — Screens + Items PHẢI group theo cùng N business flows đó (VD 5 groups, mỗi group chứa mockup rows của screens thuộc flow đó)

Cross-verification bắt buộc:
- Số business flows Output 1 = số screen-flow groups Output 2 = số groups Output 3
- Nếu không khớp → refactor để khớp, KHÔNG bỏ qua

---

## ⚠️ Gate Rules — BẮT BUỘC hỏi user giữa các output (không được chạy liền tù tì)

> **Nguyên tắc:** BA không được tự động chạy tất cả Output 1→2→3 liền không hỏi. Sau mỗi output PHẢI có gate để user review + quyết định tiếp. Chi phí gate = 1-2 câu hỏi; chi phí không gate = user phát hiện Output 2 sai định hướng khi đã vẽ xong Output 3 → refactor toàn bộ.

### Gate A — Sau Output 1 (BẮT BUỘC — mọi SCOPE_TYPE)

Sau khi vẽ Output 1 xong + PASS visual verify (Bước 5.5 mini-check), BA PHẢI DỪNG và hiển thị block dưới đây trước khi bắt đầu Output 2:

```
✅ Output 1 — Flow Tổng Quan đã vẽ xong: <Figma node URL>

Screenshot verify: <✅ N business flows rõ ràng, gap 100px đủ, không đè>
Số business flows detected: N = <số>

3 outputs BA sẽ tạo (giải thích ngắn):
  📊 Output 1 (VỪA XONG) — Flow Tổng Quan
     Mục đích: cho stakeholder thấy Actor → Trigger → Function → Technology → Outcome + Sitemap WBS
     Ai dùng: PM/Tech Lead review scope, chốt tech stack

  🔀 Output 2 (KẾ TIẾP) — Screen Flow
     Mục đích: mỗi business flow → luồng đi qua các screens (Happy + Non-Happy) + Bảng Index tổng
     Ai dùng: Designer / Dev / QC — biết cần vẽ / build / test những màn nào

  🖼 Output 3 — Screens + Items + Error Scenarios
     Mục đích: mỗi screen → mockup phone + bảng liệt kê chi tiết items UI + error scenarios
     Ai dùng: Designer làm HiFi, Dev build UI, QC viết test case

Bạn muốn:
  [1] Tiếp tục Output 2 → Output 3 (default)
  [2] Chỉnh Output 1 trước (paste comment cụ thể)
  [3] Dừng ở Output 1, không cần Output 2/3
```

Chờ user chọn. KHÔNG được tự chạy tiếp Output 2 khi chưa có confirm.

### Gate B1 — Sau Output 1, chỉ khi SCOPE_TYPE = `[B]/[C]` multi-flow (BẮT BUỘC)

Nếu `SCOPE_TYPE` (từ Câu 0.4 Bước 2b) = `[B]` (cụm) hoặc `[C]` (toàn hệ thống) VÀ Output 1 detect N > 1 business flows → sau Gate A user chọn [1] tiếp tục → BA hỏi thêm:

```
⚠️ Feature này có N = <số> business flows (scope: <B - cụm / C - toàn hệ thống>).

Output 2 vẽ scope nào?
  [A] TOÀN BỘ N flows (recommended nếu deliverable cần đủ scope cho stakeholder)
      Effort: ~<N × 15> phút, Figma frame chiều dài ~<N × 800>px

  [B] CHỈ 1 flow cụ thể — user chỉ định flow name (VD "Flow 2 — Scout")
      Lưu ý: các flow còn lại → note trong bảng status "⚠️ Partial — user chọn vẽ 1 flow"

  [C] BATCH — vẽ M flows / lượt (M < N), user review từng batch trước khi vẽ tiếp
```

Chờ user chọn. KHÔNG được tự vẽ toàn bộ hoặc tự chọn 1 flow.

### Gate B2 — Sau Output 2 (BẮT BUỘC — mọi SCOPE_TYPE)

Sau khi vẽ Output 2 xong + verify, BA PHẢI DỪNG hỏi:

```
✅ Output 2 — Screen Flow đã vẽ xong: <Figma node URL>

Screenshot verify: <✅ N screen-flow groups + Bảng Index đủ N screens>
Số screens tổng detected trong Bảng Index: M = <số>

Bạn muốn:
  [1] Tiếp tục Output 3 (mockup + items + error scenarios cho từng screen)
      Effort: ~<M × 5> phút vẽ, Figma frame chiều dài ~<M × 400>px
  [2] Chỉnh Output 2 trước (paste comment)
  [3] Dừng ở Output 2, không cần Output 3 (VD: chỉ cần flow overview cho stakeholder meeting)
```

**Thêm question nếu SCOPE_TYPE = `[B]/[C]` VÀ Output 2 có N groups:**

```
Nếu chọn [1] Tiếp tục Output 3:

Output 3 vẽ scope nào?
  [A] TOÀN BỘ N flows (mọi group Output 2 → tương ứng group Output 3)
  [B] CHỈ 1 flow cụ thể — user chỉ định flow name
  [C] BATCH — vẽ M screens / lượt, user review từng batch
```

Chờ user chọn. KHÔNG được tự vẽ Output 3 khi chưa có confirm scope.

---

### Gate flow summary

```
Vẽ Output 1
   ↓
Gate A (giải thích 3 outputs + xin phép Output 2)  ← MỌI SCOPE
   ↓ user chọn [1]
Gate B1 (nếu multi-flow) — Output 2 toàn bộ hay 1 flow?
   ↓ user chọn scope
Vẽ Output 2
   ↓
Gate B2 (xin phép Output 3 + scope nếu multi-flow)
   ↓ user chọn [1] + scope
Vẽ Output 3
   ↓
Bước 5.5 Visual Recheck → Bước 5.6 Self-Feedback → Output 4 HTML → Report final
```

**Anti-pattern NGHIÊM CẤM:**
- ❌ Vẽ liền Output 1 → 2 → 3 không dừng gate nào
- ❌ Tự đoán "user chắc muốn toàn bộ" khi SCOPE multi-flow → vẽ hết N flows không hỏi
- ❌ Skip Gate B2 khi user "trông có vẻ" đã ok Output 2

---

## Bước 5 preamble — Figma Design Output (BẮT BUỘC sau Bước 4.6)

> Dùng **Figma Design file** (`/design/` URL) từ `FIGMA_OUTPUT_URL` đã hỏi ở Bước 2b.
> Tất cả outputs trên **page do user cung cấp**. KHÔNG tạo page mới.

**Load skill bắt buộc trước khi code:**
```
skill: ba-figma-output   ← đọc TOÀN BỘ trước khi viết use_figma call nào
skill: figma:figma-use   ← đọc trước use_figma (rule quan trọng về font, textAutoResize, page switching)
```

**Figma Design = default cho tất cả outputs** vì:
- Pixel-perfect layout, đều tay, professional hơn FigJam
- HiFi phone screens (dark/light) trông thật hơn FigJam shapes
- Spec table text readable hơn FigJam stickies

**FigJam chỉ dùng khi:** user explicitly yêu cầu brainstorm/workshop real-time.

---

## Reference examples — BẮT BUỘC xem trước khi vẽ

BA phải xem 3 example images trong `.claude/skills/ba-figma-output/examples/`:

| File | Xem để hiểu |
|---|---|
| `example_output_1.png` | **Sitemap kiểu WBS tree** — actor icon + hành động, có illustration (icon người/xe/laptop...) |
| `example_output_2_screen_flow.png` | **Screen flow dạng vertical + numbered badges** — icon xanh/hồng/cam theo loại screen, decision diamond, có bảng text bên cạnh |
| `example_output_3.png` | **Mô tả màn hình** — mỗi item trên UI đều đánh số + text bên cạnh (Title / Mô tả / Mục đích) — KHÔNG lược bỏ item nào |

Load bằng `Read` tool trước khi bắt đầu Output tương ứng.

---

## API khác nhau giữa 2 tool (BẮT BUỘC đọc trước khi code)

| Tính năng | FigJam (`/board/`) | Figma Design (`/design/`) |
|---|---|---|
| Node có text tích hợp | `figma.createShapeWithText()` | Tạo riêng: `createRectangle()` + `createText()` |
| Arrow / Connector thật | `figma.createConnector()` | Không có — dùng `createVector()` hoặc `createRectangle()` |
| Post-it note | `figma.createSticky()` | Không có |
| Nhóm vùng làm việc | `figma.createSection()` | `figma.createSection()` (cùng API) |
| Tạo page mới | ❌ `figma.createPage()` không hoạt động | ✅ Hoạt động |
| `get_metadata` tool | ❌ Không hỗ trợ FigJam | ✅ Hoạt động |

**Detect loại file từ URL:**
- `figma.com/board/...` → FigJam → dùng `createShapeWithText` + `createConnector`
- `figma.com/design/...` → Figma Design → dùng `createRectangle` + `createText` + `createVector`

---

## Visual conventions — NHẤT QUÁN giữa cả 2 tool

Màu sắc và ý nghĩa KHÔNG thay đổi dù dùng FigJam hay Design:

| Element | Màu fill | Màu stroke | Ý nghĩa |
|---|---|---|---|
| Actor / người dùng | `#E8F4FD` (Actor A — Caller) · `#EDFDF0` (Actor B — Receiver) | `#0969DA` · `#1A7F37` | Ai thực hiện |
| Trigger / Action | `#E8F4FD` | `#0969DA` | Điều gì kích hoạt |
| Function / System | `#FFF9EB` | `#F4860C` | Xử lý gì |
| Technology / SDK | `#FFF9EB` | `#F4860C` | Công nghệ nào |
| Outcome / Result | `#F6F8FA` | `#D0D7DE` | Kết quả |
| Error / Non-happy | `#FFF6F5` | `#CF222E` | Lỗi, edge case |
| Popup / Modal | `#FBEEFF` | `#6639BA` | Overlay |
| Arrow happy path | — | `#0969DA` | Luồng chính |
| Arrow error | — | `#CF222E` (dashed) | Luồng lỗi |
| Arrow cross-actor | — | `#6639BA` | Kết nối 2 actor |

---

## Post-Delivery requirement — Update SPEC.md ## BA Deliverables (BẮT BUỘC — entry point cho downstream)

> **Nguyên tắc:** SPEC.md là **single source of truth** cho Tech Lead / Designer / QC downstream. Toàn bộ 5 outputs của BA PHẢI được liệt kê trong SPEC.md để downstream agents đọc SPEC là có đủ context — không phải tìm kiếm scattered files.

Sau khi hoàn thành 5 outputs, BA agent PHẢI edit `SPEC.md` thêm section **`## BA Deliverables`** **ngay sau section `## Mô tả nghiệp vụ`** (trước `## Actors & Preconditions`). Section này chứa link clickable, stakeholder + downstream agents click từ browser mở thẳng deliverable.

**Format bắt buộc (đủ 5 outputs, không thiếu output nào):**

```markdown
## BA Deliverables

> Toàn bộ output của BA cho feature này. Đây là entry point cho Tech Lead / Designer / QC downstream — mọi agent PHẢI đọc section này trước khi bắt đầu.

### Docs

| # | Output | Path / URL | Note |
|---|---|---|---|
| 0 | **SPEC.md** (file này) | `<DOCS_ROOT>/features/<feature>/SPEC.md` | Chính là file bạn đang đọc |

### Figma outputs (Bước 5 — Design output)

| # | Output | Nội dung | Figma Frame |
|---|---|---|---|
| 1 | **Flow Tổng Quan** | Business Logic Flow + Technology Table + Sitemap WBS | [Mở Figma](<URL frame Output 1>) |
| 2 | **Screen Flow** | N screen-flow groups (matching N business flows) + Bảng Index tổng | [Mở Figma](<URL frame Output 2>) |
| 3 | **Screens + Items** | Grouped by business flow, đủ N screens, Bảng ITEMS + Bảng ERROR SCENARIOS | [Mở Figma](<URL frame Output 3>) |

**Figma file:** [<Tên file>](<URL Figma file gốc>)
**Page:** `<Tên page user cung cấp>`

### Interactive prototype

| # | Output | Path / URL | Cách chạy |
|---|---|---|---|
| 4 | **HTML Prototype** | `<DOCS_ROOT>/features/<feature>/prototype/index.html` | `open <DOCS_ROOT>/features/<feature>/prototype/index.html` — standalone, không cần build |

### Downstream instructions

- **Tech Lead agent** — dùng `## Screens` (list) + `## Screen Details` (per-screen data) + Figma Frame 3 (Items) để thiết kế DB schema, API contract, service layer
- **Designer agent** — dùng Figma Frame 1/2/3 làm reference low-fi → tạo high-fidelity screens, điền cột "Figma Link" trong `## Screens`
- **QC agent** — dùng `## Acceptance Criteria` + `## Alternative Flows & Edge Cases` + HTML Prototype để test manual + Figma Frame 3 để verify Error Scenarios
```

**Cách lấy URL Figma frame:** sau khi `use_figma` tạo node, dùng `figma.currentPage.selection = [node]` hoặc lấy `node.id`, sau đó format URL:
```
https://www.figma.com/design/<FILE_KEY>/<FILE_NAME>?node-id=<NODE_ID_URL_ENCODED>
```
- `FILE_KEY`, `FILE_NAME` lấy từ URL gốc user cung cấp
- `NODE_ID` = `node.id` (dạng `123:456`), encode thành `123-456` trong URL

**Nếu skip Output nào** (VD Figma MCP unavailable → skip Output 1-3):
- Vẫn giữ section `## BA Deliverables` với đủ 5 rows
- Row bị skip: cột `Path / URL` ghi `❌ Skipped — <lý do>`, cột `Note` ghi hướng dẫn user hoàn thành
- KHÔNG được xóa row (downstream cần biết output nào có/không để plan work)
