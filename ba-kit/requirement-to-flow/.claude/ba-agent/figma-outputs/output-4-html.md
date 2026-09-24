# Ba Agent — Output 4: HTML Prototype

## Output 4 — HTML Prototype (Local)

> Dựng prototype chạy được trên browser để stakeholder confirm UI trước khi Designer vẽ Figma HiFi.

**Tạo file:** `<output-folder>/prototype/index.html`

---

## Yêu cầu chung (mọi platform)

> Thước đo duy nhất: **stakeholder mở ra bấm thử được**, không phải "đọc được".
> Prototype đủ màn / đủ item / 0 link gãy mà không bấm được thì vẫn là **FAIL**.

- **Standalone** — 1 file HTML duy nhất, không cần build, mở thẳng bằng `open index.html`
- **All screens** — mỗi screen là 1 div, **toggle `display`** để chuyển màn. Tại một thời
  điểm chỉ **1 màn** hiển thị. Tài liệu cuộn dọc liệt kê lần lượt các màn → **không phải
  prototype**, gate sẽ FAIL
- **UI thật, không phải bảng mô tả** — item `Input` phải là ô nhập thật, `Bảng` phải là
  bảng dữ liệu thật, `Button primary` phải là nút bấm được (xem Rule P7)
- **Interactive** — buttons/taps navigate đúng luồng Happy Case (xem Rule P4)
- **Dev Nav bar** — thanh navigation cho phép jump thẳng vào bất kỳ screen nào khi review
- **Error states** — simulate toast/modal/banner/inline cho non-happy case (xem Rule P8)
- **Timers** — nếu feature có countdown/timer, implement đúng
- **Prototype Contract** — expose `window.__PROTO__` + `window.go()` + `window.fireErr()`
  để chạy được Quality Gate (`output-4-verify.md`). Thiếu → không approve được

---

## ⚠️ 8 rules cứng khi build prototype (BẮT BUỘC — không được vi phạm)

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

### Rule P4 — Điều hướng phải giải theo đúng thứ tự ưu tiên

Cột `Action` trong `## Screen Details` **không phải lúc nào cũng chứa mã màn đích**.
Rất hay gặp kiểu ghi bằng lời: `→ màn mặc định theo role`, `→ file download`,
`[Trả lại] → Thông báo tới cơ sở`. Nếu chỉ đọc cột Action thì nút sẽ không có đích, hoặc
tệ hơn: **bắt nhầm mã của nhánh NG** vì đó là mã duy nhất trong chuỗi.

**Thứ tự giải đích cho 1 phần tử điều hướng:**

1. Mã màn trong cột `Action` của chính item đó
2. Nếu Action ghi đích bằng lời (có `→` nhưng không có mã) → lấy từ **cột `Transition`**
   của màn trong `## Screens`. Cột Transition **luôn liệt kê nhánh happy trước**
3. Vẫn không có → trang chủ của site đó

**Nút `Button primary` = nhánh HAPPY.** Khi Action có nhánh điều kiện mà chỉ nhánh NG kèm
mã, nút primary PHẢI lấy mã happy từ Transition:

```
SPEC:
  Action     : [IP trong whitelist] → màn mặc định theo role / [Ngoài] → OP_AUTH_003
  Transition : [IP trong whitelist] → OP_ORDR_001             / [Ngoài] → OP_AUTH_003

❌ SAI  : nút "Đăng nhập" → OP_AUTH_003   (mã duy nhất trong Action = nhánh NG)
✅ ĐÚNG : nút "Đăng nhập" → OP_ORDR_001   (nhánh happy, lấy từ Transition)
```

**Bắt buộc render dải "Transition theo SPEC"** ở cuối mỗi màn: biến từng nhánh của cột
Transition thành 1 nút bấm được. Nhánh nào SPEC chưa ghi mã màn → hiện ô xám không bấm
được, để BA nhìn thấy ngay chỗ SPEC còn thiếu. Đây **không phải logic mới** (không vi phạm
Rule P1) — nó chỉ là Navigation Mapping của Output 3 làm cho bấm được.

---

### Rule P5 — Không màn nào cụt đường, không màn nào không tới được

- **Cụt đường**: màn không có phần tử điều hướng nào đi ra. Nguy hiểm nhất ở màn ẩn
  sidebar (đăng nhập, màn lỗi full screen) — user vào là kẹt, phải F5.
  → Màn nào không có lối ra: tự thêm nút **Về trang chủ**
- **Không tới được**: BFS từ menu chính phải chạm được 100% màn. Màn nào không tới được
  → thiếu link ở đâu đó, hoặc màn đó chưa được index trong Output 2

Cả hai đều là phép **đồ thị**, nhìn từng màn riêng lẻ không phát hiện được — gate tự chạy.

---

### Rule P6 — Nhiều website → chia tab, mỗi tab 1 website

SPEC có nhiều hệ thống dùng chung (VD web khách hàng + web vận hành, phân biệt bằng
prefix mã màn `CF_` / `OP_`) → **1 file HTML, nhiều tab ở thanh trên cùng**, mỗi tab là
1 website hoàn chỉnh: app bar riêng, màu riêng, sidebar menu riêng theo module của site đó.

- Đổi tab → vào màn đầu tiên của site đó (thường là đăng nhập)
- Điều hướng cross-site tự đổi tab, không được để lạc
- **Màn đứng riêng (`solo`)**: đăng nhập, quên mật khẩu, màn lỗi full screen → **ẩn
  sidebar + breadcrumb**, dựng card căn giữa. Nhưng vẫn phải tuân Rule P5

Khác với "Multi-platform feature" bên dưới (mobile + website = **file** riêng): cùng
platform mà khác hệ thống thì dùng **tab**, không tách file.

---

### Rule P7 — Item `Title` là loại widget, phải render thành UI thật

Cột `Title` trong bảng item của `## Screen Details` chính là **tên loại widget**. Map sang
HTML thật, KHÔNG in ra dạng dòng mô tả:

| `Title` trong SPEC | Render thành |
|---|---|
| `Input`, `Input text`, `Input password`, `Search` | `<input>` có label, placeholder lấy từ Mô tả |
| `Input OTP` | dãy 6 ô 1 ký tự |
| `Textarea`, `Rich text` | `<textarea>` |
| `Dropdown`, `Multi-select`, `Month picker` | `<select>`, option lấy từ Mô tả |
| `Checkbox`, `Radio`, `Toggle`, `Radio card` | control thật, có trạng thái bấm được |
| `Date picker`, `Date range`, `Time range` | `<input type=date/time>` |
| `Bảng *`, `Table` | bảng dữ liệu — **tên cột tách từ Mô tả theo dấu `·`** |
| `Filter`, `Search + Filter` | thanh lọc: input + select + nút Lọc |
| `Pagination` | thanh phân trang |
| `Tab`, `Segmented control`, `Filter chip` | tab/segment/chip bấm được |
| `Stat card ×N` | N thẻ số liệu (giá trị **phải là số/tiền**, không phải chuỗi văn bản) |
| `Line chart`, `Stacked bar` | SVG biểu đồ |
| `Timeline`, `Stepper` | dòng thời gian / thanh bước |
| `Ô ngày × N`, `Ô ma trận`, `Calendar` | lưới ngày × dòng, ô nhập được |
| `Upload`, `Dropzone` | vùng kéo thả |
| `Callout`, `Highlight`, `Badge` | hộp thông báo / nhãn màu |
| `Button primary/secondary/danger`, `Link`, `Icon *` | nút / link, gắn đích theo Rule P4 |
| `Logo`, `Breadcrumb`, `Icon`, `Meta` | **bỏ qua** — đã có sẵn trong app shell |

**Mô tả của item là nguồn dữ liệu.** `Ngày · bữa · món · số suất · thành tiền` → đúng 5 cột
đó, đúng thứ tự đó. Đừng bịa tên cột khác.

Title lạ không khớp bảng trên → render 1 khối `card` có tiêu đề + nội dung, **không lặp lại
mô tả 2 lần**. Nếu tỉ lệ rơi vào nhánh này > 15% số item → bảng map còn thiếu, phải bổ sung.

---

### Rule P8 — Error phải bắn thử được, và dữ liệu giả phải được nói rõ

**Bắn thử error:** mỗi màn có 1 cách trigger từng dòng trong bảng Non-Happy (dropdown ở
thanh Dev, hoặc bấm vào dòng trong panel Spec). Mỗi `Hiển thị` ra đúng hình dạng của nó:

| `Hiển thị` | Prototype phải làm gì |
|---|---|
| `Toast` | toast góc màn hình, tự tắt |
| `Modal` · `Popup` | overlay có nút đóng |
| `Banner` · `Empty state` · `Chặn UI` | dải thông báo chèn đầu vùng nội dung |
| `Inline error` · `Tooltip` | viền đỏ + dòng lỗi dưới field |
| `Button disabled` | disable nút primary kèm tooltip lý do |
| `Full screen` | điều hướng sang màn lỗi `*_ERRS_*` tương ứng |

**Dữ liệu giả:** prototype phải điền dữ liệu mẫu hợp lý theo tên cột (ngày ra ngày, tiền ra
tiền, trạng thái ra badge) — bảng rỗng thì stakeholder không hình dung được. Nhưng PHẢI ghi
rõ **"dữ liệu hiển thị là dữ liệu giả, chỉ để xem bố cục"** trong `## BA Deliverables`,
tránh bị hiểu là số liệu nghiệp vụ thật.

---

### Cách làm khuyến nghị: sinh prototype bằng script, không gõ tay

Với feature ≥ 20 màn, gõ tay HTML vừa lâu vừa trôi khỏi SPEC. Cách đã kiểm chứng trên
130 màn: viết script đọc `SPEC.md` rồi sinh `index.html`.

```
SPEC.md ──> sinh prototype ──> chạy Quality Gate ──> chèn report vào HTML + SPEC
            (parse + map widget)   (Playwright)
```

Lợi ích: prototype **nhất quán với SPEC theo cấu trúc** (không thể lệch), sửa SPEC là build
lại trong vài giây, và diff được giữa các version.

⚠️ Bước sinh file **ghi đè** `index.html` → phải chạy gate **sau** bước sinh, và chèn report
**sau cùng**, nếu không mất comment report. Ghi rõ thứ tự này vào script build.

Bản tham chiếu đầy đủ (parser + bảng map widget + sinh dữ liệu giả + gate):
`docs/features/carepro-system/prototype/_build/` trong dự án CarePro.

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
- Nếu project đã có convention layout mobile (VD `<output-folder>/design/mobile-layout.md`) → Read + follow
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
open <output-folder>/prototype/index.html
```

Nếu multi-platform → mở lần lượt file mobile/website:
```bash
open <output-folder>/prototype/mobile.html
open <output-folder>/prototype/website.html
```

---

## Quality Gate BẮT BUỘC — chạy Playwright trước khi báo Done

> Cách cũ "BA test manual từng element rồi gõ bảng PASS/FAIL" **đã bỏ**. Bảng gõ tay không
> phải bằng chứng — nó từng cho lọt prototype không bấm được và nút trỏ tới màn không tồn tại.

**Chi tiết đầy đủ: `Read('.claude/ba-agent/figma-outputs/output-4-verify.md')`**

```bash
node .claude/skills/business-analyst/scripts/verify-prototype.js \
     <output-folder>/prototype/index.html \
     --out  <output-folder>/prototype/test-report.md \
     --json <output-folder>/prototype/test-report.json
```

Gate chạy 8 nhóm phép kiểm trên Chromium thật: `STATIC` · `SHAPE` · `NAV` · `REACH` ·
`ERR` · `P2` · `RESP` · `RUNTIME`. Nó click thật **từng** phần tử điều hướng và bắn thật
**từng** error trong SPEC.

**Điều kiện approve:**

```
Tổng: N tests
  ✅ PASS   : X
  ❌ FAIL   : 0   ← BẮT BUỘC. Còn 1 FAIL là KHÔNG được báo Output 4 Done.
  ⚠ SKIPPED: Y   ← chỉ cho màn UNKNOWN/INFERENCE (Rule P2)
```

Exit code `1` = có FAIL. Sửa prototype rồi chạy lại — không được ghi chú "sẽ sửa sau",
không được hạ ngưỡng gate cho qua.

Kết quả đưa vào 2 nơi: comment cuối `index.html`, và `SPEC.md` → `## BA Deliverables`
(summary + bảng Happy Path; bảng error chi tiết để trong comment HTML, dẫn link).

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
