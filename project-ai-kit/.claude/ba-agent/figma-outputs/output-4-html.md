# Ba Agent — Output 4: HTML Prototype

## Output 4 — HTML Prototype (Local)

> Dựng prototype chạy được trên browser để stakeholder confirm UI trước khi Designer vẽ Figma HiFi.

**Tạo file:** `<DOCS_ROOT>/features/<feature>/prototype/index.html`

---

## Yêu cầu chung (mọi platform)

- **Standalone** — 1 file HTML duy nhất, không cần build, mở thẳng bằng `open index.html`
- **All screens** — mỗi screen là 1 div, toggle `display` để chuyển màn hình
- **Interactive** — buttons/taps navigate đúng luồng Happy Case
- **Dev Nav bar** — thanh navigation ở dưới để jump thẳng vào bất kỳ screen nào khi review
- **Error states** — simulate toast/modal cho non-happy cases quan trọng
- **Timers** — nếu feature có countdown/timer, implement đúng

---

## Layout template BẮT BUỘC theo `TARGET_PLATFORM`

> Rule chọn template layout theo Câu 0 Platform ở Bước 2b. KHÔNG tự đổi. Nếu SPEC có nhiều platform → tạo nhiều file HTML tách riêng theo platform (hoặc 1 file với tab switcher).

### Platform: Website (desktop)

**Layout BẮT BUỘC — 6 regions** (xem visual reference `.claude/ba-agent/templates/website_template.jpg`):

```
┌───────────────────────────────────────────────┐
│                    HEAD                       │  ← logo · user menu · notification
├───────────────────────────────────────────────┤
│                  HEAD-LINK                    │  ← breadcrumb / secondary nav / tabs
├───────┬───────────────────────────┬───────────┤
│       │                           │           │
│ LEFT  │         CONTENT           │   RIGHT   │  ← left = sidebar/filter · right = widget/detail-panel/CTA
│       │                           │           │
│       │                           │           │
├───────┴───────────────────────────┴───────────┤
│                   FOOTER                      │  ← copyright · links · version
└───────────────────────────────────────────────┘
```

**Ràng buộc cứng khi vẽ Website prototype:**

- Viewport min-width `1440px` (theo `TARGET_PLATFORM = Website desktop`)
- 6 regions PHẢI có mặt (dù nội dung rỗng — VD sidebar right có thể chứa CTA/quick action). Nếu skip region nào → ghi lý do trong HTML comment `<!-- Right sidebar skipped because ... -->`
- Layout responsive: khi width < 1024px → collapse LEFT thành hamburger, RIGHT ẩn hoặc chuyển xuống dưới CONTENT
- Nav bar dev (ở FOOTER hoặc floating) — cho phép jump thẳng vào screen bất kỳ khi review
- CSS grid template gợi ý:
  ```css
  body { display: grid;
    grid-template-rows: 60px 40px 1fr 40px;
    grid-template-columns: 240px 1fr 320px;
    grid-template-areas:
      "head   head    head"
      "hlink  hlink   hlink"
      "left   content right"
      "footer footer  footer"; }
  ```

**Verify sau khi tạo:** mở file, check đủ 6 regions rõ ràng theo screenshot template + resize browser xuống 1024px xem có responsive không.

### Platform: Mobile app / Web app (mobile-first PWA)

- Viewport width `375px` cố định (giống iPhone 14)
- Layout free-form theo screen — không ràng buộc 6 regions
- BẮT BUỘC có: bottom nav / top nav bar theo pattern feature (ví dụ tabbar 4 icon dưới, hoặc back-button trên)
- Nếu project đã có convention layout mobile (VD `<DOCS_ROOT>/design/mobile-layout.md`) → Read + follow
- Nếu **CHƯA có convention** → hỏi user: **"Mobile prototype này cần layout kiểu nào? Nếu chưa có convention → mô tả pattern (bottom tab / top nav / drawer / full-screen)"**. KHÔNG tự đoán layout.

### Platform: iPad / Tablet

- Viewport `1024×768` (landscape) hoặc `768×1024` (portrait) — hỏi user preference nếu SPEC không nêu
- Split view thường dùng: sidebar 320px + main content — nhưng KHÔNG bắt buộc như website
- Nếu project đã có convention tablet → Read + follow; nếu chưa → hỏi user như Mobile

### Multi-platform feature

- Nếu SPEC có screens thuộc nhiều platform (VD User mobile + Admin website) → tạo file HTML tách:
  ```
  prototype/
    ├── mobile.html   ← screens platform mobile
    ├── website.html  ← screens platform website
    └── index.html    ← landing với 2 button "Xem Mobile" / "Xem Website"
  ```
- Mỗi file follow layout template của platform tương ứng

---

## Sau khi tạo:

```bash
open <DOCS_ROOT>/features/<feature>/prototype/index.html
```

Nếu multi-platform → mở lần lượt file mobile/website:
```bash
open <DOCS_ROOT>/features/<feature>/prototype/mobile.html
open <DOCS_ROOT>/features/<feature>/prototype/website.html
```

---

## Kỹ thuật Figma (cho Output 1-3) — thứ tự KHÔNG được sai

```js
// ✅ ĐÚNG
tx.resize(width, 10);         // 1. resize trước
tx.textAutoResize = "HEIGHT"; // 2. set SAU resize
tx.characters = content;      // 3. text wrap đúng
curY += tx.height + gap;      // 4. tích lũy Y chính xác → không overlap

// ❌ SAI — resize() reset textAutoResize = "NONE"
tx.textAutoResize = "HEIGHT";
tx.resize(width, 10);         // → height = 10 mãi → text chồng nhau
```
