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

## ⚠️ 3 rules cứng khi build prototype (BẮT BUỘC — không được vi phạm)

### Rule P1 — Cấm add business logic mới trong prototype

Prototype là **hiện thực hóa Screen Spec + Flow Manifest đã APPROVED**, không phải nơi BA/dev "sáng tạo" thêm.

- ❌ KHÔNG được implement action / behavior / validation KHÔNG có trong SPEC hoặc Output 3 Screen Spec
- ❌ KHÔNG được thêm màn hình / state / popup không index trong Bảng SCREEN INDEX (Output 2)
- ❌ KHÔNG được đổi Happy Path navigation (VD skip 1 screen "để prototype gọn hơn")
- ✅ Nếu phát hiện thiếu logic khi build → quay lại Output 2/3 sửa spec trước, rồi mới build lại prototype (theo Scoped Update rule `POLICIES.md §4.6`)

**Test check:** mỗi action trong prototype PHẢI trace về 1 row trong Navigation Mapping (Output 3 Bảng 4). Không trace được → vi phạm Rule P1.

### Rule P2 — UNKNOWN exception không tự implement như final behavior

Exception nào trong Output 2 Exception Matrix có classification `UNKNOWN` / `INFERENCE` / `PROPOSAL` (chưa APPROVED bởi BRSE) → KHÔNG được implement với behavior "tự phịa".

- ❌ KHÔNG code fallback / retry / redirect cho UNKNOWN exception theo pattern "chắc là..."
- ✅ Hiển thị **placeholder rõ ràng** trong prototype khi trigger UNKNOWN exception:
  ```
  ⚠ [UNKNOWN BEHAVIOR — chờ BRSE confirm]
     Exception EX-01 chưa có rule. Prototype tạm không xử lý.
     → Xem Output 2 Exception Matrix để track
  ```
- ✅ Interaction Test Report row cho UNKNOWN exception → status `⚠ SKIPPED — waiting BRSE confirm` (không PASS/FAIL)

**Chống hallucination:** user reviewer thấy `⚠ UNKNOWN` sẽ biết đây là gap chưa resolve, không tưởng là feature đã hoàn chỉnh.

### Rule P3 — Partial scope PHẢI có banner cảnh báo ở top HTML

Nếu user chọn Batch M hoặc chỉ 1 flow ở Gate B1/B2 → prototype KHÔNG cover toàn bộ deliverable. BẮT BUỘC hiển thị **banner đỏ cố định** ở top HTML để reviewer không confuse.

**Template banner (chèn vào `<body>` đầu tiên):**

```html
<div style="position:sticky; top:0; z-index:9999; background:#CF222E; color:#fff;
            padding:12px 20px; font-family:sans-serif; font-size:14px;
            text-align:center; border-bottom:2px solid #82071E;">
  ⚠ <strong>PARTIAL SCOPE PROTOTYPE</strong> —
  chỉ cover <strong><!-- Flow X / M-of-N screens --></strong>.
  Đây KHÔNG phải deliverable đầy đủ.
  <br/>
  <span style="opacity:0.85; font-size:13px;">
    Coverage: <!-- 5/12 screens (Flow 2 — Scout only) --> ·
    Full scope xem: <!-- link Output 2 Bảng Index -->
  </span>
</div>
```

**Rule bắt buộc:**
- Nếu `SCOPE_TYPE = [A]` (chức năng đơn lẻ) hoặc user chọn Toàn bộ ở Gate B2 → **KHÔNG chèn banner** (đây là full scope)
- Nếu chọn Batch M hoặc 1 flow → **BẮT BUỘC chèn banner** + điền cụ thể "cover X/Y screens" + link về Output 2 Bảng Index
- Banner phải `position:sticky` — reviewer scroll xuống vẫn thấy, không được hidden

---

## Layout template BẮT BUỘC theo `TARGET_PLATFORM`

> Rule chọn template layout theo Câu 0 Platform ở Bước 2b. KHÔNG tự đổi. Nếu SPEC có nhiều platform → tạo nhiều file HTML tách riêng theo platform (hoặc 1 file với tab switcher).

### Platform: Website (desktop)

**Layout RECOMMENDED DEFAULT — 6 regions** (xem visual reference `.claude/ba-agent/templates/website_template.jpg`):

> **⚠️ Không mặc định cứng — cho phép opt-out có confirm.** Kit hiện tại đề xuất 6-region là default vì phù hợp phần lớn business web app. NHƯNG không phải mọi website đều fit (VD: landing page, marketing site, dashboard full-bleed). Trước khi apply 6-region, BA PHẢI check:
>
> - Nếu SPEC / user đã specify layout convention khác → follow convention đó
> - Nếu screen thuộc loại `Landing / Marketing / Dashboard full-bleed` → hỏi user: "Screen này bạn muốn 6-region layout hay full-bleed / custom layout?"
> - Nếu KHÔNG có convention và user không answer → **apply 6-region default + note trong HTML comment** `<!-- Layout: 6-region default (no explicit convention). Review with Designer trước Phase 3. -->`
> - Chỉ apply 6-region cứng khi user explicit "OK 6-region" hoặc SPEC đã ghi rõ

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

**Ràng buộc khi apply 6-region layout (mặc định recommended, không cứng):**

- Viewport min-width `1440px` (theo `TARGET_PLATFORM = Website desktop`)
- 6 regions SHOULD có mặt (dù nội dung rỗng — VD sidebar right có thể chứa CTA/quick action). Nếu skip region nào → ghi lý do trong HTML comment `<!-- Right sidebar skipped because ... -->`
- **Cho phép opt-out từng region cụ thể** nếu SPEC/user confirm: VD landing page có thể skip LEFT + RIGHT, chỉ giữ HEAD + CONTENT + FOOTER — note lý do trong HTML comment
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

## Interaction Test Report (BẮT BUỘC — chèn cuối file HTML dưới dạng comment + đưa vào BA Deliverables)

> Prototype không chỉ để nhìn — phải chạy được. BA PHẢI test manual từng interactive element sau khi tạo xong HTML rồi ghi kết quả vào bảng dưới. Bảng này chèn dạng `<!-- ... -->` comment cuối file HTML + copy vào SPEC.md `## BA Deliverables` bên dưới row HTML.

**Bảng Interaction Test Report:**

| Test ID | Start screen | Action | Expected destination / state | Actual | PASS / FAIL |
|---|---|---|---|---|---|
| T01 | AX_FEAT_001 | Click row công ty đầu tiên | Navigate AX_FEAT_002 | AX_FEAT_002 hiển thị | ✅ PASS |
| T02 | AX_FEAT_002 | Click [Gọi ngay] khi CA Online | Navigate AX_FEAT_003 modal | AX_FEAT_003 hiển thị + timer chạy | ✅ PASS |
| T03 | AX_FEAT_002 | Click [Gọi ngay] khi CA Offline | Button disabled + tooltip "Không online" | Button không click được, tooltip hiển thị | ✅ PASS |
| T04 | AX_FEAT_003 | Chờ 30s không pick | Navigate AX_FEAT_005 missed | Sau 30s → screen missed | ✅ PASS |
| T05 | AX_FEAT_003 | Click [Cancel] | Popup Confirm Cancel | Popup hiển thị | ✅ PASS |
| T06 | AX_FEAT_003 | Confirm Cancel | Back về AX_FEAT_002 + toast "Đã hủy" | Toast hiển thị + navigate về | ✅ PASS |

**Coverage rule:**
- **Mọi Happy Path transition** trong Output 2 Screen Flow PHẢI có ≥ 1 test row PASS
- **Confirmed NG branch** (từ Exception Matrix Output 2 với classification = `FACT`) PHẢI có test row
- Test cho `UNKNOWN` / `INFERENCE` exception → SKIP test, note `⚠ Not implemented — waiting BRSE confirm`
- **FAIL row NGHIÊM CẤM** — nếu có FAIL, BA phải fix HTML trước khi báo Output 4 ✅ Done

**Count summary bắt buộc in cuối bảng:**

```
Tổng: N tests
  ✅ PASS: X
  ❌ FAIL: 0 (BẮT BUỘC = 0 trước khi Approve)
  ⚠ SKIPPED: Y (waiting BRSE confirm cho UNKNOWN/INFERENCE)
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
