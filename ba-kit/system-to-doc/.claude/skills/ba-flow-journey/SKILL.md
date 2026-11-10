---
name: ba-flow-journey
description: Vẽ Output 1 của BA kit = **2 frame cạnh nhau**: ① Business Flow Journey (swimlane multi-actor, end-to-end nghiệp vụ khách thấy) + ② Function Flow (use-case lane, map theo module FL-xx của hệ thống). Render song song cả Figma và HTML. Dùng khi BA xây/sửa Output 1.
---

# ba-flow-journey — Output 1 (BF + FF) Skill

> **Scope:** Output 1 của BA kit `requirement-to-flow` giờ gồm **2 frame cạnh nhau**:
> - ① **Business Flow Journey** (BF) — swimlane multi-actor, luồng end-to-end mà **khách nhìn thấy**
> - ② **Function Flow** (FF) — use-case lane theo **module hệ thống** (FL-xx)
>
> Skill này định nghĩa cách vẽ cả 2, cho cả Figma lẫn HTML. Trước khi vẽ Output 1 → **BẮT BUỘC đọc skill này**.
>
> **Reference thật:** Figma `CarePro` node `189:684` (BF) · node `89:52` (FF) · HTML `Pre-Sale/03112026_UnderMT/outputs/01_analysis/business_flows_journey.html`.

---

## 1. Phân biệt BF vs FF — thuật ngữ nghiêm ngặt

| Khái niệm | Business Flow (BF) | Function Flow (FF) |
|---|---|---|
| **Góc nhìn** | Khách / nghiệp vụ end-to-end | Hệ thống / module chức năng |
| **Trigger** | Sự kiện nghiệp vụ (bắt đầu kỳ, chốt đơn...) | User mở màn / action trong hệ thống |
| **Outcome** | Thành quả kinh doanh (thực đơn công khai, hóa đơn gửi) | Trạng thái hệ thống (màn đóng, dữ liệu lưu) |
| **Mã** | `BF-1`..`BF-N` (ít — 3..7 BF cho 1 SPEC) | `FL-01`..`FL-NN` (nhiều — theo module) |
| **Vẽ dạng** | **Swimlane multi-actor** (mỗi actor 1 lane ngang) | **Use-case lane** (1 lane / 1 use case) |
| **Số step mỗi flow** | 4..8 bước (cross-lane) | 3..12 node (Actor, Screen, Decision, Process) |
| **Non-happy** | Nhắc ngắn trong desc hoặc 1 branch nhỏ | Dải riêng dưới happy row |
| **Nguồn** | SPEC `## Business Flows` + Happy Path | SPEC `## Functional Modules` + Screen Register |

**Rule vàng:**
- 1 BF **map được** vào ≥1 FF (BF đi xuyên, FF nhỏ).
- 1 FF **không bắt buộc** thuộc BF nào (có FF service chéo như `FL-01 Xác thực`).
- Khi mô tả cho **khách** → ưu tiên BF.
- Khi mô tả cho **Dev / Tech Lead** → ưu tiên FF.

---

## 2. Data model chung (cả Figma và HTML cùng dùng)

### 2.1 Business Flow data

```ts
type BusinessFlow = {
  code: string;          // "BF-1"
  name: string;          // "Lên thực đơn"
  color: string;         // hex, e.g. "#8b5cf6"
  module: string;        // "FL-03" — module chính mà BF chạm
  actors: Actor[];       // ≥2 actor (nếu <2 → cân nhắc không nên tách thành BF)
  steps: Step[];
};

type Actor = {
  name: string;          // "👤 ES本部 (Admin)" hoặc "⚙ Hệ thống (batch)"
  color: string;         // hex riêng cho actor, khác với màu BF
};

type Step = {
  lane: number;          // index trong actors[]
  title: string;         // BẮT BUỘC có TÊN MÀN HÌNH ĐẦY ĐỦ nếu step = mở màn
                         // Format: "📄 Màn 「<Tên màn>」(<MÃ MÀN>)"
                         //         "⚙ Batch — <mô tả>"
                         //         "🔀 Quyết định: <câu hỏi>"
  desc: string;          // 1-2 câu mô tả hành động + điều kiện
  from: number | null;   // index step trước (null nếu bắt đầu)
};
```

### 2.2 Function Flow data (giữ như Output 1 hiện tại)

Xem `.claude/ba-agent/figma-outputs/output-1-flow.md` — không đổi data model, chỉ đổi vị trí render (frame FF giờ nằm bên **trái**, frame BF nằm bên **phải** hoặc ngược lại tuỳ page).

---

## 3. Palette chuẩn (cả Figma và HTML cùng dùng)

### 3.1 BF color (5 màu đủ cho 5 BF; nếu nhiều hơn → bọc lại từ đầu)

| BF # | Role | Hex | Dùng ở đâu |
|---|---|---|---|
| 1 | purple | `#8b5cf6` | border-left 6px, badge ID, header step box |
| 2 | blue | `#3b82f6` | như trên |
| 3 | amber | `#f59e0b` | như trên |
| 4 | cyan | `#06b6d4` | như trên |
| 5 | pink | `#ec4899` | như trên |

### 3.2 Actor color (độc lập với BF color — thấy ngay actor nào)

| Actor loại | Hex | Icon |
|---|---|---|
| Admin / Operator (ES本部, PM) | `#3b82f6` blue | 👤 |
| User cuối / Cơ sở (FC) | `#10b981` green | 👤 |
| NCC / Supplier (仕入先) | `#f59e0b` amber | 👤 |
| Factory / Xưởng (工場) | `#ef4444` red | 👤 |
| Logistics / Picking (関通) | `#8b5cf6` purple | ⚙ hoặc 👤 |
| Shipping API (Yamato/Sagawa) | `#06b6d4` cyan | ⚙ |
| Billing (Bill One) | `#6b7280` gray | ⚙ |
| Client management (東洋ケア) | `#6366f1` indigo | 👤 |
| Hệ thống / Batch tự động | `#94a3b8` slate | ⚙ |

### 3.3 Icon prefix (BẮT BUỘC trong title)

- `📄` — màn hình (user thao tác trực tiếp)
- `⚙` — batch / API / xử lý tự động
- `🔀` — điểm quyết định

---

## 4. Figma render — spec chi tiết

### 4.1 Vị trí 2 frame trong page Output 1

```
┌──────────────────────┐  ┌──────────────────────────────┐
│ FF Frame (89:52...)  │  │ BF Frame (189:684...)        │
│ Function Flow        │  │ Business Flow Journey        │
│ Use-case lanes       │  │ Swimlane multi-actor         │
│ Width ~2360          │  │ Width ~2800-2900             │
└──────────────────────┘  └──────────────────────────────┘
     x_ff_start               x_bf_start = x_ff_end + 150
```

- Gap giữa 2 frame: **150px**
- Căn **y = cùng mức** cho dễ scan
- Đặt cùng page với Output 1 hiện tại (không tạo page mới)

### 4.2 BF frame layout (swimlane)

```
┌─ Title: "Business Flow Journey — <tên dự án> (N BF · swimlane multi-actor)" ─┐
│ Subtitle: giải thích icon + nguồn SPEC                                        │
├─ BF-1 section (border-left 6px, color BF-1) ─────────────────────────────────┤
│  ┌─────┬──────────────────────────────────────────── Chạm Module: FL-xx ────┐│
│  │ BF-1│                                                                     ││
│  │     │ Tên BF                                                              ││
│  └─────┴─────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────┐                                                             │
│  │ Actor lane 1│  [Step 1]   [Step 2] → [Step 3]                             │
│  └─────────────┘                        ↓                                    │
│  ┌─────────────┐                     [Step 4]   (cross-lane arrow)           │
│  │ Actor lane 2│                                                             │
│  └─────────────┘                                                             │
│  ┌─────────────┐                               [Step 5]                      │
│  │ Actor lane 3│                                                             │
│  └─────────────┘                                                             │
├─ BF-2 section ──────────────────────────────────────────────────────────────┤
│ ...                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Chi tiết dimension:**

| Element | Width × Height | Ghi chú |
|---|---|---|
| Frame | 2850 × dynamic | tính theo `sum(lanes_per_BF)` |
| Title area | full × 90 | |
| BF header | full × 56 | border-left 6px color BF |
| Actor lane | full × 200 | alternating bg `#fafbfc` / `#ffffff` |
| Actor badge | 195 × 150 | opacity 0.12 color, border 1.5 color, text 11px bold CENTER |
| Step box | 310 × 170 | white bg, border 2px color BF, header strip 26px color BF |
| Arrow | weight 2.5, color BF | cross-lane: right→turn→down→right |
| Arrowhead | polygon 10×12, rotate -90 | |

**Step box content (3 dòng):**

1. **Header strip** (26px): `BF-X-N` (step sequence), chữ trắng 11px bold
2. **Title** (body): 12px bold, có icon prefix + tên màn + mã trong ngoặc. VD:
   - `📄 Màn 「Thêm / sửa sản phẩm」(OP_PROD_002)`
   - `⚙ Batch — Gửi mail nhắc 7 ngày & 3 ngày trước hạn chốt`
   - `🔀 Quyết định: lưu nháp hay công khai?`
3. **Desc** (body): 10px regular, 1-2 câu

### 4.3 FF frame layout (giữ nguyên Output 1 hiện tại)

Spec cũ không đổi — xem `.claude/ba-agent/figma-outputs/output-1-flow.md` section "Phần A — Business & Logic Flow".

### 4.4 Code snippets dùng chung

Xem [`examples/figma_render.js`](examples/figma_render.js) — helper function + example cho:
- `createBFFrame(bfs, refNode)` — tạo frame BF
- `drawSwimlane(bf, ...)` — vẽ 1 BF section
- `drawStepBox(x, y, headerStr, title, desc, color, parent)` — step box
- `drawArrow(fromBox, toBox, color, parent)` — mũi tên cross-lane

---

## 5. HTML render — spec chi tiết

### 5.1 Khi nào xuất HTML

- Khi BA cần giao bản **xem web** cho stakeholder không có Figma
- Khi cần embed vào prototype hoặc Notion / Confluence
- Khi vẽ Output 1 để review nhanh (HTML + Figma song song)

### 5.2 Template structure

```html
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>Business Flow Journey — <Tên dự án></title>
  <style>/* tokens dùng chung */</style>
</head>
<body>
  <header class="app-head">
    <h1>🏗️ <Tên dự án> — Business Flow Journey</h1>
    <div class="subtitle">N luồng end-to-end · swimlane multi-actor · nguồn SPEC §BF</div>
  </header>

  <nav class="tabs-nav">
    <!-- 1 tab / BF nếu nhiều, hoặc stack vertical nếu ít -->
  </nav>

  <main>
    <section class="bf-section" data-bf="BF-1">
      <header class="bf-header" style="border-left: 6px solid #8b5cf6;">
        <span class="bf-id" style="background:#8b5cf6;">BF-1</span>
        <div class="bf-names">
          <h3>Lên thực đơn</h3>
          <p class="bf-jp">Chạm Module: FL-03 · N bước</p>
        </div>
      </header>

      <div class="bf-svg-wrap">
        <svg viewBox="0 0 2850 ...">
          <!-- Swimlane bg + actor labels -->
          <!-- Step boxes -->
          <!-- Arrows với marker-end -->
        </svg>
      </div>

      <details class="bf-details">
        <summary>📋 Chi tiết từng bước + Tài nguyên</summary>
        <div class="details-list">
          <div class="detail-row">
            <div class="detail-head">
              <span class="detail-sub">BF-1-1</span>
              <span class="detail-action">Thêm / sửa sản phẩm (OP_PROD_002)</span>
            </div>
            <p class="detail-desc">ES本部 quản lý master SP: SKU + giá + option.</p>
            <div class="detail-chips">
              <span class="chip">📄 OP_PROD_002</span>
              <span class="chip">Actor: ES本部</span>
            </div>
          </div>
          <!-- ... -->
        </div>
      </details>
    </section>

    <!-- BF-2, BF-3, ... -->
  </main>

  <footer class="app-foot">...</footer>
</body>
</html>
```

### 5.3 SVG markup pattern (per BF section)

```svg
<svg viewBox="0 0 <W> <H>" width="<W>">
  <defs>
    <marker id="arrow-BF1" ... refX="9" refY="5" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b5cf6"/>
    </marker>
  </defs>

  <!-- Lane 1 bg + divider -->
  <rect x="0" y="20" width="<W>" height="185" fill="#fafbfc"/>
  <line x1="0" y1="20" x2="<W>" y2="20" stroke="#e2e8f0"/>
  <!-- Actor badge 1 -->
  <rect x="10" y="45" width="195" height="135" rx="10"
        fill="#3b82f6" opacity="0.1" stroke="#3b82f6" stroke-width="1.5"/>
  <text x="102.5" y="112.5" font-size="12.5" font-weight="700"
        fill="#3b82f6" text-anchor="middle">👤 ES本部 (Admin)</text>

  <!-- Lane 2 bg + badge -->
  <rect x="0" y="205" width="<W>" height="185" fill="#ffffff"/>
  <!-- ... -->

  <!-- Arrows (đi trước step boxes để step vẽ đè lên) -->
  <path d="M 530 115 L 555 115 L 555 300 L 570 300"
        stroke="#8b5cf6" stroke-width="2.5" fill="none"
        marker-end="url(#arrow-BF1)"/>

  <!-- Step box 001-1 -->
  <rect x="230" y="35" width="300" height="160" rx="10"
        fill="#ffffff" stroke="#8b5cf6" stroke-width="2"/>
  <rect x="230" y="35" width="300" height="26" rx="10" fill="#8b5cf6"/>
  <text x="242" y="52" font-size="11" font-weight="700" fill="#fff"
        font-family="ui-monospace">BF-1-1</text>
  <text x="242" y="81" font-size="12.5" font-weight="700" fill="#0f172a">
    📄 Màn 「Thêm / sửa sản phẩm」
  </text>
  <text x="242" y="98" font-size="12.5" font-weight="700" fill="#0f172a">
    (OP_PROD_002)
  </text>
  <text x="242" y="123" font-size="10.5" fill="#475569">
    ES本部 quản lý master SP: SKU + giá + option.
  </text>
</svg>
```

### 5.4 CSS tokens

Xem [`examples/html_template.html`](examples/html_template.html) — full template.

---

## 6. Workflow — khi nào vẽ gì

### 6.1 Thứ tự khi làm Output 1 mới

1. **Define BF trước** — xác định N business flow (dùng §1 guide), map sang module FL
2. **Define FF** — các use case theo module (như Output 1 hiện tại)
3. **Vẽ FF frame** (quy trình Figma hiện tại — không đổi)
4. **Vẽ BF frame** cạnh phải FF (dùng data model §2.1)
5. **Nếu cần HTML**: generate song song (same data, 2 output formats)
6. Cross-link: SPEC `## Business Flows` ghi node BF, `## Functional Modules` ghi node FF

### 6.2 Khi BA sửa feedback

- Feedback về **nghiệp vụ end-to-end** (actor không khớp, outcome sai) → sửa **BF frame** + SPEC `## Business Flows`
- Feedback về **màn / action / technology** → sửa **FF frame** + SPEC `## Functional Modules`
- Feedback về **mô tả trong step box** (vd "ghi rõ tên màn hình") → sửa **cả 2** nếu đụng cả 2 frame

---

## 7. Checklist Self-Feedback (bắt buộc)

### BF frame
- [ ] Mỗi BF có **≥2 actor** (nếu chỉ 1 → cân nhắc không phải BF, có thể là FF)
- [ ] Mỗi step có **icon prefix** (📄 / ⚙ / 🔀)
- [ ] Step kiểu màn hình có **TÊN MÀN đầy đủ trong 「 」 + mã màn** trong title
- [ ] Mũi tên cross-lane vẽ **thật** (line + arrowhead polygon) — không chip rời
- [ ] Mỗi BF có **Module FL** gắn ở header ("Chạm Module: FL-XX")
- [ ] Actor badge dùng màu **actor palette §3.2** — không lẫn với màu BF

### FF frame (giữ như Output 1 cũ)
- [ ] 19 lane actor × 8 nghiệp vụ (hoặc theo granularity hiện có)
- [ ] Technology Table bên phải, 194 FR tag trong tên layer
- [ ] Sitemap Site → Actor → nhóm chức năng → màn

### HTML (nếu có)
- [ ] 1 section per BF, có `data-bf` attribute để JS/CSS target
- [ ] SVG arrow dùng `marker-end` (không fake bằng text "→")
- [ ] `<details>` chi tiết step có `<chip>` tài nguyên

---

## 8. Companion files

- `.claude/ba-agent/figma-outputs/output-1-flow.md` — spec chi tiết FF frame (cũ)
- `.claude/ba-agent/figma-outputs/shared-rules.md` — rule chung cho 3 output
- `.claude/ba-agent/figma-outputs/code-patterns.md` — code JS helper
- `.claude/skills/ba-figma-output/SKILL.md` — skill tổng về Figma rendering

Khi vẽ Output 1 — load 2 skill:
1. `ba-figma-output` (rule chung Figma)
2. `ba-flow-journey` (spec BF + FF, file này)
