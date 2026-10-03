> **SOURCE:** `designer-kit/prototype-to-figma/.claude/designer-agent/design-system-format.md` — copy self-contained cho kit system-to-doc; **đây là chuẩn chung** của design system giữa 2 kit. Sửa chuẩn thì sửa CẢ HAI nơi + `skills/system-analyst/scripts/ds_roles.py` (danh sách token vai trò / component bắt buộc mà gate V-DS kiểm). Ở kit này: thư mục là `04_DesignSystem/` (thay `design-system/`), cách lấy dữ liệu từ hệ thống đang chạy ở `../outputs/o4-design-system.md`.

# Định dạng Design System (chuẩn bắt buộc)

> Đọc ở **Bước 0.1** cùng `design-system-intake.md`. Mọi design system của kit — dù phân tích từ link Figma, file tài liệu, màn Figma mẫu, codebase hay artifact có sẵn — **đều phải ra đúng định dạng của Artifact type "Design System"** trên claude.ai (ví dụ chuẩn: ES Kitchen — `https://claude.ai/artifact/ModdSpJmnWd9yA4onTCtpp`).
>
> Nguồn quy định gốc là `SKILL.md` + `artifact-type/reference/*.md` của type "Design System" (`Artifact list scope:"types"` → "Design System" → `read` các file đó trên `type_url`). File này tóm tắt chuẩn đó **và thêm quy ước của kit** (tên token vai trò, mục README, checklist D1–D8). Hai bên lệch nhau → theo type, ghi chú vào `design-system/STATUS.md`.

---

## 1. Cây thư mục

```
design-system/
├── STATUS.md                         ← của KIT (không publish): trạng thái, nguồn, link artifact, platform, mâu thuẫn, changelog
└── project/                          ← = project/ của artifact, publish nguyên cây
    ├── design-system.json            ← index (ghi CUỐI CÙNG)
    ├── tokens.json                   ← toàn bộ token (ghi nguyên file)
    ├── README.md                     ← brand book = luật sử dụng cho agent
    ├── components/
    │   ├── Cover/preview.html        ← bìa (ghi sau cùng, KHÔNG có README.md bên cạnh)
    │   ├── <Comp>/README.md          ← guideline từng component
    │   ├── <Comp>/preview.html       ← preview chạy thật
    │   ├── bundle.js                 ← 1 classic script gán window.<Namespace>
    │   ├── bundle.css                ← style component, chỉ dùng var(--token)
    │   └── index.d.ts                ← props (tài liệu)
    ├── assets/
    │   ├── Logos/README.md + file logo (upload)
    │   └── Icons/README.md + file SVG (upload)
    └── fonts/<file>.woff2            ← chỉ khi có file font thật (Google Fonts thì không cần)
```

- **Không bao giờ ghi** `tokens.css`, `manifest.json`, `api/**` (trang tự sinh).
- Tên file/folder: không `..`, không bắt đầu bằng `/` hoặc `.`, không `package.json` / `CLAUDE.md` / `AGENTS.md`.
- Logo, icon, ảnh, SVG, PDF dưới `assets/` = **asset upload** (`Artifact publish asset:true`) + bản ghi trong `design-system.json` → `assetGroups`. File text (`README.md`, `.json`) dưới `assets/` = file thường.

## 2. `design-system.json` — index

```json
{
  "v": 3,
  "layout": "files",
  "createdOnFiles": { "v": 1, "at": "<ISO-8601 lúc tạo>" },
  "title": "<Tên dự án>",
  "namespace": "<TenDuAnPascalCase>",
  "libraries": [ { "name": "react", "version": "18" }, { "name": "react-dom", "version": "18" } ],
  "sections": {},
  "groups": ["Logos", "Icons"],
  "assetGroups": {
    "Logos": { "name": "Logos", "tile": "l",  "order": ["<logo>.png"], "files": { "<logo>.png": { "name": "<logo>.png", "blob": "<id>", "size": 0, "type": "image/png" } } },
    "Icons": { "name": "Icons", "tile": "xs", "order": ["<Icon>.svg"], "files": { "<Icon>.svg": { "name": "<Icon>.svg", "blob": "<id>", "size": 0, "type": "image/svg+xml" } } }
  },
  "blobs": {},
  "docs": { "readme": "project/README.md", "sections": [] },
  "lastChange": { "by": "<tên user>", "at": "<ISO-8601>", "via": "Claude · prototype-to-figma", "note": "<1 dòng>" }
}
```

- `title` = tên design system. `namespace` = global của `bundle.js` (`window.<namespace>`).
- `blob` = id trong `/_blob/<id>` mà lệnh upload trả về; `size` byte; `type` media type.
- Sửa lần sau: **đọc lại index ngay trước khi ghi**, giữ mọi key cũ, chỉ đổi `lastChange` + key liên quan.

## 3. `tokens.json`

### 3.1 Hình dạng (sai hình dạng → trang hiển thị trống)

```json
{
  "name": "<Tên dự án>",
  "version": 1,
  "meta": { "source": "figma | docs | code | screens | website", "file": "<link / tên file>", "frames": ["<link frame>"], "components": { "Button": "<node id>" }, "componentKeys": { "Button": "<component key Figma>" }, "synced": "YYYY-MM-DD" },
  "color":   { "themes": [ { "id": "<theme-id>", "name": "<Tên hiển thị>" } ],
               "tokens": [ { "name": "primary", "value": { "<theme-id>": "#0969DA" }, "usage": "…" } ] },
  "type":    { "fonts": [], "families": { "sans": "\"Noto Sans JP\", system-ui, sans-serif", "mono": "…" },
               "groups": [ { "name": "Heading", "family": "sans", "styles": [ { "name": "char-6-bold", "fontSize": "24px", "lineHeight": "36px", "fontWeight": 700, "sample": "…", "usage": "…" } ] } ] },
  "spacing": { "tokens": [ { "name": "space-16", "value": "16px", "usage": "…" } ] },
  "radius":  { "tokens": [ { "name": "radius-md", "value": "6px", "usage": "…" } ] },
  "shadow":  { "tokens": [ { "name": "shadow-float", "value": "0 2px 4px -2px rgba(0,0,0,0.10)", "usage": "…" } ] },
  "size":    { "tokens": [ { "name": "header-height", "value": "54px", "usage": "…" } ] }
}
```

- `meta.source`: `figma` (Figma library / variable) · `screens` (đo trên màn Figma mẫu) · `docs` · `code` · `website` (đo trên website đang chạy — kit `ba-kit/system-to-doc`); nhiều nguồn nối bằng `+` (vd. `website+code`).
- Mọi family trừ `type` là **danh sách** `{"tokens":[{name,value,usage}]}`. **Cấm** dạng map DTCG (`{"color":{"brand":{"$value":…}}}`) — chuyển thành danh sách trước khi ghi.
- `color.tokens` là **một danh sách phẳng**; giá trị theo theme `{ "<theme-id>": "#hex" }`; chuỗi đơn = theme đầu; theme thiếu giá trị thừa hưởng theme đầu → đặt theme chính lên đầu.
- Giá trị màu hợp lệ: `#rgb` `#rrggbb` (`#rrggbbaa`), `rgb()/rgba()/hsl()/oklch()` với số thuần, hoặc alias `"{ten-token-khac}"` của token có thật. **Cấm**: tên màu (`red`, `transparent`), `var()`, `color-mix()`.
- Tên token: `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$` (không dấu cách, không `/` — Figma `blue/500` → `blue-500`), **duy nhất** trên mọi family trừ `type`.
- Độ dài `px|rem|em|%`; `lineHeight` có thể không đơn vị; `fontWeight` số.
- **Mọi token có `usage`** nói dùng ở đâu; token chữ ghi rõ nền nó đặt lên (để kiểm 4.5:1).
- `type.fonts` để `[]` khi dùng Google Fonts / không có file font; khai họ font ở `type.families`.
- Giới hạn: ≤ 8 theme, ≤ 600 màu, ≤ 12 type group / ≤ 80 style, ≤ 60 token mỗi family khác.

### 3.2 Theme

- 1 theme / portal hoặc site có màu chủ đạo khác nhau (vd. `system-admin`, `company-admin`, `carrier`, `supplier`). Chỉ 1 brand → 1 theme `light`. Có dark mode trong nguồn → thêm theme `dark`.
- Chỉ token đổi theo theme mới có giá trị dạng object; neutral / status / type / spacing / radius giữ chung.

### 3.3 Tên token vai trò BẮT BUỘC (quy ước kit — để bước vẽ Figma bind được)

Đặt **tên vai trò dưới đây** cho token; tên gốc trong nguồn (`blue/500`, `Sparkle action`…) ghi trong `usage`. Thang gốc của nguồn (`blue-50…900`) giữ thêm nếu có.

| D# | Family | Token bắt buộc |
|---|---|---|
| D1 | color | `primary-50…900` (thang theo theme) · `primary` · `primary-hover` · `primary-active` · `primary-subtle` · `primary-text` (khi primary là chữ / nét mảnh) · `on-primary` · `brand-*` (màu logo, nếu có) |
| D2 | color | `neutral-50…900` · `white` · `page-bg` · `surface` · `surface-subtle` · `surface-disabled` · `text-high` · `text-middle` · `text-low` · `divider-low` · `divider-middle` · `divider-high` · `overlay-scrim` |
| D3 | color | `success-50/100/500/700` · `info-50/100/500/700` · `warning-50/100/400/800` · `negative-50/100/500/600` · `focus-ring` |
| D4 | type | `families.sans` (+ `mono` nếu có ID / mã) · group `Heading`, `Text` (+ `Mono`) · style đặt theo thang nguồn (vd. `char-1…12`, `-bold`), ≥ 4 bậc, mỗi style có `sample` + `usage` |
| D5 | spacing · radius · shadow | `space-<px>` (thang 4px) · `radius-none/xs/sm/md/lg/xl/full` · `shadow-flat/raise/stick/float/popout/focus` |
| D7 | size | `viewport-<platform>` (vd. `viewport-web` 1440px; chiều cao ghi trong usage) · `header-height` · `sidebar-width` / `sidebar-collapsed` hoặc `tabbar-height` · `nav-item-height` · `control-sm/md/lg` · `table-header-height` · `table-row-height` · `modal-width` · `content-max` |

Nguồn không có giá trị cho token bắt buộc → **không bịa**: bỏ token đó, ghi `TBD` vào `STATUS.md` (§ Thiếu).

## 4. `README.md` — brand book

- Viết **tiếng Việt** (giữ nguyên nhãn UI gốc, vd. tiếng Nhật trong 「」), câu mệnh lệnh, **gọi tên token / style / component** trong backtick. Ví dụ: "Nền ứng dụng `page-bg`. Card, header, modal dùng `surface`."
- **Không** có tiêu đề `#` đầu file (trang đã có tên), **không** ghi nguồn gốc / build note / next step (để vào `STATUS.md`). Ngoại lệ: 1 câu mở đầu nói design system dựa trên thư viện / file nào và phục vụ những portal nào.
- Thứ tự mục (bỏ mục nguồn không có, không độn):

| # | Mục `##` | Nội dung |
|---|---|---|
| 0 | _(đoạn mở đầu)_ | Dựa trên thư viện / file nào; một bộ component phục vụ những portal nào; cái gì đổi theo portal |
| 1 | `<N> portal = <N> theme` | Cách chọn theme (`data-theme`) · bảng `data-theme · Portal · Người dùng · primary · Nguồn` · luật dùng token vai trò · cảnh báo tương phản |
| 2 | `Màu` | Nền / surface · chữ high/middle/low và nền được phép · divider · status (bước nền / bước chữ) · `brand-*` chỉ dùng cho thương hiệu · bảng badge trạng thái (`Nhãn · Tone · Ghi chú`) |
| 3 | `Chữ` | Font + lúc dùng mono · thang chữ và style cho từng vai trò (tiêu đề trang, section, modal, body, nhãn, helper) · định dạng số tiền / ngày / số lượng, căn phải, `tabular-nums` |
| 4 | `Khoảng cách, bố cục` | Lưới · khung màn hình (viewport, sidebar / header / tab bar, padding vùng nội dung, khoảng cách card) · form · bảng · vùng tìm kiếm |
| 5 | `Mẫu màn hình <loại>` | Mẫu màn lặp lại (vd. CRUD 一覧 / 詳細 / 編集 / 新規登録): nút nào, tiêu đề nào, hộp xác nhận, toast |
| 6 | `Viền, bo góc, đổ bóng` | radius theo vai trò · shadow theo lớp · focus ring · chi tiết trang trí đặc trưng |
| 7 | `Trạng thái tương tác` | solid / outline / ghost / danger: default → hover → active → disabled · loading · ẩn hay disable khi không có quyền |
| 8 | `Nội dung và giọng văn` | Ngôn ngữ UI, kiểu nhãn, mẫu câu xác nhận / thành công / lỗi (trích nguyên văn), thuật ngữ thống nhất, emoji hay không |
| 9 | `Icon` | Bộ icon, độ đậm, kích thước theo ngữ cảnh, component `Icon`, `aria-label` |
| 10 | `Logo` | File, kích thước, vị trí đặt, nền được phép, điều cấm |
| 11+ | `Màn <nghiệp vụ>` | Bảng `Mục đích · Component` cho nhóm màn đặc thù (tuỳ dự án) |

## 5. Component

- **Danh mục = đúng những gì nguồn định nghĩa** (không thêm "cho đủ bộ"; thêm thì ghi lý do). Tối thiểu cần cho bước vẽ: `Button` · `TextField` · `Select` · `Checkbox` · `Radio` · `Switch` · `Badge` · `Tabs` · `Table` · `Pagination` · `Modal` · `Toast` · `InlineMessage` · `PageHeader` · `Breadcrumb` · `SideNav` / `TabBar` · `AppHeader` · `AppShell` · `Icon`. Thiếu trong nguồn → ghi `STATUS.md` § Thiếu.
- `components/<Comp>/README.md`:
  - Câu đầu = tóm tắt (kiểu × tông × cỡ, có số px). Không lặp `# <Comp>`.
  - `- **Consumer cung cấp**: …` (props / children / dữ liệu).
  - Các gạch đầu dòng: khi dùng / không dùng, luật theo theme, quyền, a11y. Nhiều hành vi → bảng.
- `components/<Comp>/preview.html`:
  - **Dòng 1** bắt buộc: `<!-- @dsCard group="<Nhóm>" height=<px> -->` (nhóm: `Actions`, `Forms`, `Data`, `Navigation`, `Feedback`, `Layout`, `Patterns`, …).
  - Tài liệu HTML nhỏ: 1 `<div id="root">` + 1 `<script>` render qua `window.<Namespace>.<Comp>` bằng `React.createElement`; chỉ dùng `var(--token)`; font qua Google Fonts. Nhiều theme → render mỗi theme 1 hàng bằng `data-theme`.
  - Cấm `<iframe>`, `fetch` ra ngoài, `<script src>` tương đối.
- `components/bundle.js`: **1 classic script** viết tay, mỗi component là hàm dùng `window.React.createElement` (không JSX, `import`, network, không chuỗi `</script`), cuối file `window.<Namespace> = { Button, … }`. Dòng 1 tuỳ chọn: `/* @ds-bundle: {"format":4,"namespace":"<Namespace>","components":[{"name":"Button"}, …]} */`.
- `components/bundle.css`: class component chỉ dùng `var(--<token>)`, không hex trần, không Tailwind.
- `components/index.d.ts`: dòng đầu là chú thích namespace + cách đổi theme; mỗi component `export interface <Comp>Props {…}` + `export declare function <Comp>(…)`; `IconName` là union tên icon.

## 6. Cover — `components/Cover/preview.html`

- Dòng 1 `<!-- @dsCard height=300 -->` (240–360). Khung 960 × height, không responsive, không animation.
- 1 SVG inline + tên hệ thống (≤ 120px, đáy trái, trên nền `page-bg`) + 1 dòng tagline 13–14px `text-middle`.
- Khối màu lớn (3–5 khối, các màu nhận diện: `primary` từng theme, `brand-*`) + **1 pattern** chọn theo tính chất hệ thống; mọi fill / `rx` là class bind token. Mọi khối nằm bên phải x = 480.
- Chú thích 4 dòng trên SVG: `blocks:` · `arrangement:` · `pattern:` · `scales:` — mỗi dòng có tên token.
- Folder `Cover/` **không** có `README.md` (có thì nó thành component thường).

## 7. Asset

- `assets/Logos/README.md`: mô tả logo (màu = tên token + hex), định dạng & kích thước gốc, vị trí đặt + chiều cao, nền được phép, điều cấm. File logo **copy nguyên từ nguồn**, không vẽ lại. Không có logo → không tạo nhóm Logos, README ghi "dùng tên bằng chữ".
- `assets/Icons/README.md`: bộ icon, độ đậm, khung, màu mực của SVG, dùng component `Icon` (`currentColor`) trong code.
- `tile`: Logos `"l"`, Icons `"xs"`.

## 8. `STATUS.md` (của kit, không publish)

```markdown
# Design System — <Tên dự án>

- Trạng thái: DRAFT | APPROVED YYYY-MM-DD | TBD: D#…
- Artifact: https://claude.ai/artifact/<id>
- Nguồn: <link Figma · tài liệu · N màn đã phân tích · codebase>

## Platform
| Platform | Theme (`data-theme`) | Viewport | Khung màn | Screen prefix |
|---|---|---|---|---|

## Thứ tự ưu tiên nguồn
1. Màu / size đo trên màn Figma đã duyệt · code
2. Variable / style trong Figma library
3. Tài liệu guideline

## Thiếu (TBD)
| D# | Token / component | Ghi chú |
|---|---|---|

## Mâu thuẫn cần xác nhận
| # | Nội dung | Quyết định tạm |
|---|---|---|

## Changelog
| Ngày | Thay đổi |
|---|---|
```

## 9. Checklist chất lượng (trước khi xin duyệt)

- [ ] `tokens.json` đúng hình dạng danh sách, không map DTCG, không tên trùng, mọi token có `usage`
- [ ] Đủ token vai trò bắt buộc (§3.3) hoặc đã ghi TBD
- [ ] Giá trị **chính xác** từ nguồn (5px giữ 5px, không làm tròn); code > variable > screenshot; không bịa
- [ ] Chữ đạt 4.5:1 trên nền ghi trong `usage` ở **mọi theme** (3:1 cho chữ ≥ 24px / đậm ≥ 19px, viền control, focus ring, icon); cặp màu gốc không đạt → giữ nguyên, ghi cảnh báo trong `usage` + README
- [ ] README đủ mục §4, gọi tên token, có ví dụ thật của dự án
- [ ] Mỗi component có `README.md` + `preview.html` (dòng 1 marker) và nằm trong `bundle.js` + `index.d.ts`
- [ ] Logo / icon copy nguyên từ nguồn; mỗi nhóm asset có README
- [ ] Cover đã ghi, folder Cover không có README
- [ ] Không AI trope: gradient xanh-tím, emoji trang trí, card viền trái màu, số liệu độn
- [ ] Không dữ liệu thật của khách hàng trong sample / preview
