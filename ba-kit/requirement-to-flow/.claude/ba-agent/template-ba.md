# BA Agent — Template Reference cho Output 1/2/3

> **Purpose:** Template skeleton mô tả cấu trúc chuẩn của Output 1/2/3 dùng làm reference cho MỌI dự án.
> **Dùng ở:** `ba-agent.md` Bước 5 (Figma Design Output). Trước khi vẽ Output 1 lần đầu cho project mới, BA PHẢI `Read` file này để đối chiếu layout + dimension + màu sắc, tránh tự biến tấu.
> **Snapshot images:** `.claude/ba-agent/templates/figma-reference-sample.png` (visual overview 3-output stack — dùng để so sánh cấu trúc, KHÔNG copy nội dung).
> **Nguyên tắc:** File này = layout skeleton. Nội dung cụ thể (screen names, actors, tech table rows) thay theo project — cấu trúc + dimension + màu sắc **giữ nguyên**.

---

## Output 1 — Flow Tổng Quan + Sitemap WBS

**Frame:** `Output 1 — Flow Tổng Quan + Sitemap WBS` · `2280 × 1682px`

**Header (y=24..63):**
- Text 1 (font-size 18px, bold): `Output 1 — Flow Tổng Quan — <Feature Name>`
- Text 2 (font-size 11px, muted `#57606A`): `Phần A: Business & Logic Flow (Actor → Trigger → Function → Technology → Outcome) · Phần B: Sitemap WBS Tree`

**Phần A — 5-column business flow (y=80..~550):**

| Column | X offset | Content |
|---|---|---|
| ACTOR | `x=100` | Ellipse 78px + icon person + text 2 dòng (Tên actor + platform) |
| TRIGGER | `x=290` | Rectangle `150×72` radius 8, fill `#E8F4FD`, stroke `#0969DA` |
| FUNCTION | `x=530` | Rectangle `160×96` radius 8, fill `#FFF9EB`, stroke `#F4860C` |
| TECHNOLOGY | `x=780` | Rectangle `180×96` radius 8, fill `#FFF9EB`, stroke `#F4860C` |
| OUTCOME | `x=1560` | Rectangle `200×72` radius 8, fill `#F6F8FA`, stroke `#D0D7DE` |

- Divider line `y=108`, width 1700, `#D0D7DE`
- Arrows: solid `#0969DA` 2px (happy) / dashed `#CF222E` 2px (error) / solid `#1A7F37` 2px (cross-actor) — có polygon triangle head ở đầu mũi tên (regular-polygon 8×10)
- Label trên arrow: text 11px `#57606A` (VD verb ngắn: "tap", "call API", "notify", "signal")
- Nếu N business flows → stack dọc, gap MIN 100px giữa flows (xem `figma-outputs/output-1-flow.md` Vertical gap rule)

**Phần B — Sitemap WBS Tree (y=560+):**
- Divider line `y=560`, width 1700, `#D0D7DE`
- Section title (y=572, font 14px bold): `SITEMAP — WBS TREE (Actor + Hành động)`
- Sub-title (y=592, font 11px muted): `Level 1: Feature · Level 2: Actor · Level 3: Hành động (verb-first) · Level 4: Screen / Popup`
- Legend box (y=620, `320×50`, radius 6): 4 chip nhỏ giải thích màu Root/Actor/Hành động/Screen
- Tree layout: horizontal or vertical branches (theo số actors) — Root ở giữa hoặc trái, actors đâm ra 2 phía

**Áp dụng khi copy sang project mới:**
- Giữ cột ACTOR/TRIGGER/FUNCTION/TECHNOLOGY/OUTCOME + màu sắc — thay nội dung chip
- Technology table (BẮT BUỘC theo `output-1-flow.md` Phần B) đặt bên phải Flow từ `x=1800..2260`
- Nếu SCOPE_TYPE = `[B]/[C]` (multi-flow) → mỗi flow 1 band, gap MIN 100px

---

## Output 2 — Screen Flow + Bảng SCREEN INDEX

**Frame:** `Output 2 — Screen Flow — <Feature>` · width ~2280px (chiều cao dynamic theo N groups)

**Layout tổng:**

```
┌──────────────────────────────────────┬──────────────────────┐
│ SCREEN-FLOW GROUP 1 (business flow 1)│                      │
│ ┌────────────┬────────────────┐      │                      │
│ │ Happy Case │ Non-Happy Case │      │  BẢNG SCREEN INDEX   │
│ │ ①→②→③...  │ ⚠→Error1...   │      │  (spanning full      │
│ └────────────┴────────────────┘      │   height, bên phải)  │
├──────────────────────────────────────┤                      │
│ SCREEN-FLOW GROUP 2 ...              │                      │
├──────────────────────────────────────┤                      │
│ SCREEN-FLOW GROUP N ...              │                      │
└──────────────────────────────────────┴──────────────────────┘
```

**Screen node** (rectangle `200×56` radius 8):
- Screen thường: fill trắng, stroke `#0969DA` — icon 🖥
- Popup/Modal: fill `#FBEEFF`, stroke `#6639BA` — icon 💬 — nét đứt
- Error/Toast: fill `#FFF6F5`, stroke `#CF222E` — icon ⚠ — nét đứt

**Badges** (ellipse 24px + số): Xanh (Screen) / Tím (Popup) / Đỏ (Error)

**Start/End nodes** (ellipse 32px): Start `#0969DA` ▶ · End `#6E7781` ■

**Decision diamond** (44px): fill `#FFF9EB`, stroke `#F4860C` — label "Yes/No"

**Bảng SCREEN INDEX** (bên phải, DUY NHẤT — không split per group):
- Header row 32px, fill xanh nhạt
- Data row 40-48px, alternating white/BGL
- 3 cột: `# | Màn hình | Loại | Mô tả chức năng`
- Bottom row: `Tổng: N màn hình (trong đó X popup + Y toast)`

**Áp dụng khi copy sang project mới:**
- Số screen-flow groups = số business flows Output 1 (cross-verify)
- Popup/Toast/Banner CŨNG đếm trong Bảng Index — không được lược
- Nếu SCOPE_TYPE = `[B]/[C]` → hỏi Gate B1 trước khi vẽ (vẽ toàn bộ N flows hay chỉ 1)

---

## Output 3 — Screens + Items + Error Scenarios

**Frame:** `Output 3 — Screens + Items — <Feature>` · width 1500px (mobile/webapp) hoặc 2560px (website desktop)

**Layout mỗi row (mockup + tables):**

```
┌──────────────────────────────────────────────────────────────┐
│ Group N — Flow N: <Tên business flow>                        │
│                                                              │
│ Row 1:                                                       │
│  ┌────────────┐  ┌──────────────────────────────────────┐   │
│  │  MOCKUP    │  │ BẢNG ITEMS                           │   │
│  │  phone     │  │ # | Title | Mô tả | Action/Behavior  │   │
│  │  (375×812) │  ├──────────────────────────────────────┤   │
│  │            │  │ BẢNG ERROR SCENARIOS (bg hồng nhạt)  │   │
│  │            │  │ # | Trigger | Hiển thị | Message+Act │   │
│  └────────────┘  └──────────────────────────────────────┘   │
│                                                              │
│ Row 2: ...                                                   │
│ Row N: ...                                                   │
└──────────────────────────────────────────────────────────────┘
                    gap 150px giữa groups
┌──────────────────────────────────────────────────────────────┐
│ Group N+1 ...                                                │
└──────────────────────────────────────────────────────────────┘
```

**Viewport mockup** theo `TARGET_PLATFORM`:

| Platform | Mockup viewport | Frame width |
|---|---|---|
| Mobile app / Web app (PWA) | `375 × 812` | 1500px |
| Website desktop | `1440 × 1024` | 2560px |
| iPad / Tablet | `1024 × 768` | 2000px |

**Bảng ITEMS:**
- 4 cột: `# | Title | Mô tả | Action / Behavior` — column offsets `8 · 40 · 220 · 430`
- Row height dynamic: 48/68/88 tuỳ độ dài action
- Fill trắng, stroke `#D0D7DE`, radius 8

**Bảng ERROR SCENARIOS** (dưới ITEMS, gap 20px):
- Fill `#FFFBFB` (hồng nhạt), stroke `#FFBBB9` red, radius 8
- 4 cột: `# | Trigger | Hiển thị | Message + Action tiếp theo` — offsets `8 · 40 · 240 · 370`
- Cột "Hiển thị" enum: Toast · Modal · Popup · Banner · Tooltip · Empty state · Push notification · Auto dismiss

**Áp dụng khi copy sang project mới:**
- Coverage Rule (BẮT BUỘC): số rows = số screens trong Output 2 Bảng Index (kể cả popup)
- Cross-flow screen: vẽ mockup 1 lần ở group đầu, reference bằng Screen Code ở group sau
- Nếu SCOPE_TYPE = `[B]/[C]` → hỏi Gate B2 trước khi vẽ (vẽ toàn bộ N flows hay chỉ 1)

---

## Checklist khi dùng template này cho project mới

- [ ] Đọc `figma-reference-sample.png` để nhìn visual overview trước khi bắt đầu
- [ ] Xác định N = số business flows từ SPEC → chọn single vs multi-flow layout
- [ ] Copy dimension + màu sắc + font size từ template — KHÔNG tự biến tấu
- [ ] Nội dung (Actor name, Screen Code, Function name, Technology) thay theo project của mình
- [ ] Cross-verify sau khi vẽ xong: Output 1 N flows = Output 2 N groups = Output 3 N groups
- [ ] `get_screenshot` mỗi output → so sánh visual với reference PNG (đúng cột, đúng gap, đúng màu chưa)
