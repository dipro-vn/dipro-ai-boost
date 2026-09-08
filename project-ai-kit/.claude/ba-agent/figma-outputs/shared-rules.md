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
| Actor / người dùng | `#E8F4FD` (Dipro Admin) · `#EDFDF0` (Company Admin) | `#0969DA` · `#1A7F37` | Ai thực hiện |
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

> **Nguyên tắc:** SPEC.md là **single source of truth** cho Tech Lead / Designer / QC downstream. Toàn bộ 6 outputs của BA PHẢI được liệt kê trong SPEC.md để downstream agents đọc SPEC là có đủ context — không phải tìm kiếm scattered files.

Sau khi hoàn thành 6 outputs, BA agent PHẢI edit `SPEC.md` thêm section **`## BA Deliverables`** **ngay sau section `## Mô tả nghiệp vụ`** (trước `## Actors & Preconditions`). MkDocs (Output 5) sẽ render section này thành link clickable, stakeholder + downstream agents click từ browser mở thẳng deliverable.

**Format bắt buộc (đủ 6 outputs, không thiếu output nào):**

```markdown
## BA Deliverables

> Toàn bộ output của BA cho feature này. Đây là entry point cho Tech Lead Design / Designer / QC downstream — mọi agent PHẢI đọc section này trước khi bắt đầu.

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

### Interactive prototype + Documentation site

| # | Output | Path / URL | Cách chạy |
|---|---|---|---|
| 4 | **HTML Prototype** | `<DOCS_ROOT>/features/<feature>/prototype/index.html` | `open <DOCS_ROOT>/features/<feature>/prototype/index.html` — standalone, không cần build |
| 5 | **MkDocs Site** | `http://127.0.0.1:8000` (Nav → Features → <feature> → SPEC) | `cd <PROJECT_ROOT> && mkdocs serve` (auto-refresh khi save SPEC) |

### Downstream instructions

- **Tech Lead Design agent** — dùng `## Screens` (list) + `## Screen Details` (per-screen data) + Figma Frame 3 (Items) để thiết kế DB schema, API contract, service layer
- **Designer agent** — dùng Figma Frame 1/2/3 làm reference low-fi → tạo high-fidelity screens, điền cột "Figma Link" trong `## Screens`
- **QC agent** — dùng `## Acceptance Criteria` + `## Alternative Flows & Edge Cases` + HTML Prototype để test manual + Figma Frame 3 để verify Error Scenarios
```

**Cách lấy URL Figma frame:** sau khi `use_figma` tạo node, dùng `figma.currentPage.selection = [node]` hoặc lấy `node.id`, sau đó format URL:
```
https://www.figma.com/design/<FILE_KEY>/<FILE_NAME>?node-id=<NODE_ID_URL_ENCODED>
```
- `FILE_KEY`, `FILE_NAME` lấy từ URL gốc user cung cấp
- `NODE_ID` = `node.id` (dạng `123:456`), encode thành `123-456` trong URL

**Nếu skip Output nào** (VD Figma MCP unavailable → skip Output 1-3, hoặc mkdocs chưa cài → skip Output 5):
- Vẫn giữ section `## BA Deliverables` với đủ 6 rows
- Row bị skip: cột `Path / URL` ghi `❌ Skipped — <lý do>`, cột `Note` ghi hướng dẫn user hoàn thành
- KHÔNG được xóa row (downstream cần biết output nào có/không để plan work)
