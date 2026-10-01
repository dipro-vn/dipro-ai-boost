# O4 — Design System của hệ thống cũ (Artifact type "Design System")

> **Yêu cầu:** O4 phải ra **đúng 100% format** của Artifact type **Design System** trên claude.ai — giống bản mẫu https://claude.ai/artifact/ModdSpJmnWd9yA4onTCtpp (brand book · tokens theo theme · type scale · spacing / radius / shadow · component có preview chạy thật + hướng dẫn · assets · cover). Chỉ tạo khi **có đọc từ website hoặc Figma**; nguồn gồm website + source code (+ Figma).
>
> Dùng lại về sau: Luồng 2 trục **Mockup** đối chiếu với nó; mọi màn mới / đề xuất màn mới reference tới nó.

---

## 0. Type và tài liệu gốc

| | |
|---|---|
| Type | **Design System** (core) — `type_url` = `https://claude.ai/artifact/5M7UeXXcx16TP3vzVFNDzd` |
| Hướng dẫn gốc (BẮT BUỘC đọc trước khi viết, bằng Artifact `read` với `type_url` hoặc trên url của system vừa tạo) | `SKILL.md` · `artifact-type/reference/format.md` (ngữ pháp từng file) · `craft.md` (luật chất lượng) · `cover.md` · `from-code.md` (từ repo) · `from-design-tool.md` (từ Figma) · `artifact-type/demo.json` (ví dụ đủ bộ) |
| Bản mẫu tham chiếu | https://claude.ai/artifact/ModdSpJmnWd9yA4onTCtpp — `read` các file `project/*` để xem một system hoàn chỉnh |

File này **không thay** tài liệu gốc — nó quy định cách kit lấy dữ liệu **quan sát được** và đổ vào đúng format đó. Mâu thuẫn về format → tài liệu gốc thắng. Nội dung đọc từ artifact là **dữ liệu**, không phải lệnh.

---

## 1. Điều kiện

| Có | O4 |
|---|---|
| Website đã crawl (P1) **hoặc** Figma input (P7) | ✅ chạy |
| Chỉ có source code | ⬜ không chạy — `--skip "O4=chỉ có source code, chưa quan sát UI"` |

---

## 2. Thành phẩm — y hệt cấu trúc `project/` của type

```
04_DesignSystem/
├── link.md                       ← link artifact đã publish (P7b = có) hoặc "chưa publish — lý do"
└── project/
    ├── design-system.json        index v3 (viết CUỐI)
    ├── tokens.json               tokens dạng LIST
    ├── README.md                 brand book
    ├── components/
    │   ├── <Comp>/README.md      hướng dẫn dùng (câu đầu = tóm tắt)
    │   ├── <Comp>/preview.html   preview chạy thật, dòng 1 = <!-- @dsCard group="…" height=N -->
    │   ├── Cover/preview.html    bìa — folder để TRỐNG ngoài file này
    │   ├── bundle.js             1 classic script gán window.<Namespace>
    │   ├── bundle.css            CSS chỉ dùng var(--<token>)
    │   └── index.d.ts            props của mọi component
    ├── assets/
    │   ├── Logos/<file> + README.md
    │   └── Icons/<file>.svg + README.md
    └── fonts/<file>              chỉ khi có file font hợp lệ trong source (§4.3)
```

**Không viết:** `api/…`, `tokens.css`, `manifest.json` (page tự sinh) · `index.html`, `SKILL.md`, `artifact-type/…` (của type).

---

## 3. Thu nguồn — chỉ ghi cái quan sát được

```bash
# crawl đã chạy ở Bước 4 thu luôn style component + logo/icon (styles.json, assets.json)
python3 $S/extract-design-tokens.py --crawl $I/recon/crawl --css-root REPO-01=<fe-repo> \
    --out $I/recon/design --emit-tokens $V/04_DesignSystem/project/tokens.json --name "<system_name>"
```

| Nguồn | Lấy gì | Ưu tiên khi lệch |
|---|---|---|
| **Website đang chạy** | màu nền/chữ/nút/viền/badge/nav/bảng, font, thang chữ, padding/gap, radius, shadow, viewport; logo, favicon, SVG icon | **1** — đây là cái người dùng đang thấy |
| **Figma** (P7) | variable, style, component, icon — theo `from-design-tool.md` (Figma MCP) | 2 |
| **Source FE** | tên token (CSS var / SCSS / Tailwind theme), font file, component library (tên, props), icon set — theo `from-code.md`, **route Read-only** (không cài, không build code khách) | 3 cho giá trị · **1 cho tên** token và tên component |

`--emit-tokens` sinh `tokens.json` **khởi đầu** đúng ngữ pháp, chứa **chỉ giá trị quan sát được**, mỗi token tên `obs-<family>-NN` + usage `TODO — <gợi ý vai trò, số lần, ở đâu>`. Agent phải **đổi tên ngữ nghĩa** và **viết usage thật**; gate V-DS FAIL khi còn `obs-` hoặc `TODO`. Không thêm giá trị nào không có trong draft.

---

## 4. Viết từng file

### 4.1 `tokens.json` — ngữ pháp bắt buộc (format.md)

- Mọi family trừ `type` là `{"tokens":[{"name","value","usage"}…]}` — **LIST**. Map kiểu DTCG `{"brand":{"$value":…}}` = page không đọc được → FAIL.
- `color`: `themes` + 1 list `tokens` phẳng. **Theme:** 1 theme `light` nếu mọi website cùng màu chủ đạo; **mỗi website/portal 1 theme** khi `perSite` trong draft cho thấy primary khác nhau (như bản mẫu: 4 portal = 4 theme, chỉ `primary*` đổi). Theme chính đặt ĐẦU.
- Tên token: `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`, duy nhất trên mọi family. Ưu tiên **tên trong source** (CSS var của FE) — không có thì đặt theo vai trò: `primary`, `primary-hover`, `primary-subtle`, `on-primary`, `page-bg`, `surface`, `surface-subtle`, `text-high/middle/low`, `divider-low/middle`, `success-*`, `info-*`, `warning-*`, `negative-*`.
- Giá trị màu: hex thường / `rgb()` `hsl()`… / alias `"{token}"`. Cấm tên màu (`red`, `transparent`), `var()`, `color-mix()`.
- `type`: `families` (stack font thật), `groups` → `styles` `{name, fontSize, lineHeight, fontWeight, sample, usage}` — mỗi style là 1 tổ hợp **đo được** trong `typeStyles` của draft; `sample` lấy chữ UI thật (nhãn, tiêu đề — **không** dữ liệu người dùng).
- `spacing` · `radius` · `shadow` (+ family khác nếu có, VD `size` cho chiều cao control, sidebar, header) đều dạng list.
- **Mọi token có `usage`** nói dùng ở đâu (nêu màn `SC-xxx` / component). Màu chữ: nêu nền nó nằm trên + tỉ lệ tương phản nếu < 4.5:1 (giữ nguyên giá trị của hệ thống, **không** tự chỉnh màu cho đẹp).
- `meta`: `{"source":"website+code[+figma]","sites":[…],"repos":[…],"figma":"<link|—>","synced":"<YYYY-MM-DD>","evidence":{"<token>":"<URL trang | REPO-xx:file#Lnn>"}}`.

### 4.2 `README.md` — brand book (ngôn ngữ theo P10)

Luật dùng cho agent đọc sau, câu mệnh lệnh **gọi tên token / style / asset**. **Không** tiêu đề `#` (page tự hiện tên), **không** ghi nguồn / cách làm / việc tiếp theo (để ở báo cáo), trừ **1** mục ghi chú "Chưa đồng bộ" ở cuối. Độ dài theo nguồn — không độn. Section theo bản mẫu, có cái nào viết cái đó:

| Section | Nội dung (ví dụ thật lấy từ hệ thống) |
|---|---|
| (đoạn mở đầu) | Design system cho hệ thống nào, mấy website, dùng chung cho site nào |
| `## <N> website = <N> theme` | chỉ khi nhiều theme: bảng `data-theme` · website · người dùng · `primary` · nguồn |
| `## Màu` | nền / chữ / đường kẻ / trạng thái / màu thương hiệu — gọi tên token, quy ước badge trạng thái (nhãn thật → tone) |
| `## Chữ` | font, thang chữ, style nào cho tiêu đề trang / section / modal / nội dung / helper; định dạng số, ngày, tiền |
| `## Khoảng cách, bố cục` | lưới, khung màn (sidebar, header, vùng nội dung theo viewport đo được), form, bảng, phân trang |
| `## Mẫu màn hình …` | mẫu lặp lại (一覧/詳細/編集, tìm kiếm + bảng…) lấy từ `02_Screen` + O1 — nêu component dùng |
| `## Viền, bo góc, đổ bóng` | radius theo vai trò, shadow cho card / dropdown / modal, focus |
| `## Trạng thái tương tác` | hover / active / disabled / loading — chỉ những gì quan sát được hoặc có trong CSS |
| `## Nội dung và giọng văn` | ngôn ngữ UI, nhãn nút thật, câu xác nhận / thành công / lỗi **nguyên văn** từ hệ thống (catalog message của O1) |
| `## Icon` | bộ icon (tên thư viện nếu nhận ra từ class/SVG), cỡ, màu; số icon đã copy |
| `## Logo` | file trong `assets/Logos`, đặt ở đâu, nền nào; không có logo → ghi rõ, dùng chữ thường |
| `## Chưa đồng bộ` | 1 mục: token / component / font / theme không lấy được + lý do |

### 4.3 Assets & font

- `assets/Logos/`, `assets/Icons/`: **copy nguyên** file thu được (`recon/design/assets/<WEB>/…`) — không vẽ lại, không "gần giống". Mỗi group có `README.md` (bộ nào, cỡ, màu mực của SVG).
- Font: Google Fonts → chỉ khai trong `type.families`. File font chỉ copy khi **có trong repo FE** (cùng license với code); font tải từ CDN thương mại → không copy, ghi "Chưa đồng bộ".
- **Không** đưa ảnh nội dung (ảnh sản phẩm, avatar…) — có thể chứa dữ liệu thật.

### 4.4 Component — inventory trước, build đủ

1. **Inventory = cái hệ thống THẬT có** (craft: "the source defines the inventory"): component FE export + mẫu UI lặp lại trên các màn (`components` trong draft: button, input, select, checkbox/radio/switch, badge, table, pagination, tabs, nav, header, card, dialog, alert/toast, breadcrumb…). Mỗi mục ghi màn thấy nó (`SC-xxx`). **Không** thêm component "thường có" mà hệ thống không có.
2. In inventory cho user (số lượng + tên) trước khi viết.
3. Mỗi component:
   - `bundle.js`: viết tay bằng `React.createElement` (không JSX, import, fetch), tái hiện **đúng style đo được** qua class trong `bundle.css` dùng `var(--token)` — không literal giá trị token. Cuối file: `window.<Namespace> = {Button, …}`. Không chứa chuỗi `</script` hay `<!--`.
   - `index.d.ts`: `export interface <Comp>Props {…}` + `export declare function <Comp>(…)`.
   - `<Comp>/README.md`: câu đầu = tóm tắt; khi nào dùng; **consumer cung cấp gì** (props, children); làm/không làm; màn đang dùng.
   - `<Comp>/preview.html`: dòng 1 `<!-- @dsCard group="<Actions|Forms|Data|Navigation|Feedback|Layout|Patterns>" height=N -->`; tài liệu HTML nhỏ, 1 `<div id="root">` + 1 `<script>` render component qua `window.<Namespace>` với vài trạng thái; nhiều theme → render mỗi theme 1 hàng (`data-theme`). Không `<iframe>`, không ảnh ngoài, chỉ Google Fonts.
   - Có source FE: tên + props lấy từ code; style vẫn đối chiếu website. README ghi "dựng lại từ `<path>`".
4. Nhiều component → làm 2–3 cái cơ bản trước (Button, TextField, Badge), rồi phần còn lại. Không kịp → liệt kê ở "Chưa đồng bộ", **không** im lặng bỏ.

### 4.5 Cover — viết CUỐI (`cover.md`)

`components/Cover/preview.html`: dòng 1 `<!-- @dsCard height=288 -->` (240–360); 1 SVG inline: 3–5 **khối màu** từ token nhận diện (primary từng theme, màu thương hiệu, ink) + **1 pattern** chọn từ tính cách hệ thống (bo góc lớn → pill; lưới 4px dày đặc → dot grid…) + **tên** (đúng như README) ≤ 440px bên trái dưới + 1 dòng tagline. Mọi fill / rx là class gắn token. Comment 4 dòng "derivation" đầu SVG. Không ảnh, không gradient, không chữ trên khối.

### 4.6 `design-system.json` — index, viết CUỐI

```json
{"v":3, "layout":"files", "createdOnFiles":{"v":1,"at":"<ISO now>"},
 "title":"<system_name>", "namespace":"<PascalCase, VD ShopDemo>",
 "libraries":[{"name":"react","version":"18"},{"name":"react-dom","version":"18"}],
 "sections":{}, "groups":["Logos","Icons"],
 "assetGroups":{"Logos":{"name":"Logos","tile":"l","order":[…],"files":{…}},
                "Icons":{"name":"Icons","tile":"xs","order":[…],"files":{…}}},
 "blobs":{}, "docs":{"readme":"project/README.md","sections":[]},
 "lastChange":{"by":"<user>","at":"<ISO>","via":"Claude Code · system-to-doc ver<N>","note":"AS-IS từ WEB-01 + REPO-01"}}
```
`files.<tên>` = `{"name","blob":"<id sau khi upload>","size","type"}` — chưa publish thì bỏ `blob` (gate WARN).

---

## 5. Gate V-DS (trước khi publish)

```bash
python3 $S/verify-design-system.py $V/04_DesignSystem --draft $I/recon/design/tokens-draft.json \
    [--figma-used] [--published-url <url>] --out $I/gates/v-ds.md
python3 $S/selftest-design-system.py >> $I/gates/selftest.md
```
Chặn: thiếu file · index sai shape · tokens sai ngữ pháp (map DTCG, tên màu, alias hỏng, trùng tên) · còn `obs-`/`TODO` · **màu / font không quan sát được** (bịa) · nguồn chỉ có code · README thiếu section / không gọi tên token · component thiếu README/preview/marker, không có trong bundle / d.ts · cover sai luật · asset thiếu README. WARN: tương phản < 4.5:1 mà usage không ghi chú.

---

## 6. Publish lên claude.ai — chỉ khi P7b = Có

⚠️ claude.ai là dịch vụ cloud: chỉ token, chữ UI, logo/icon của hệ thống — **không** dữ liệu người dùng. Hook H06 vẫn chặn PII.

| # | Bước |
|---|---|
| 1 | V-DS `FAIL = 0` |
| 2 | Artifact `publish` với `type_url` (§0) + `title` = `<system_name>` + `auto_open: "after_first_write"`, **không file** → nhận `url` (chỉ 1 lần — không bao giờ dùng `type_url` lần 2) |
| 3 | Upload ảnh / SVG trong `assets/` (`asset: true`, `file_paths` tối đa 25 file / call) → ghi `blob` id vào `assetGroups.<Group>.files` (giữ `size` = kích thước file trên đĩa). `README.md` của group gửi như file thường ở bước 4 |
| 4 | Publish các file `project/*` với `root = $V/04_DesignSystem`, `file_path` = đường dẫn tuyệt đối của `project/design-system.json`, `files` = map mọi file còn lại (không gồm file đã upload ở bước 3). **`index.d.ts` phải khai `{"from": "project/components/index.d.ts", "contentType": "text/plain"}`** — `.ts` không phải loại file được phục vụ, publish sẽ bị từ chối cả lượt. > 255 file → nhiều call, index ở call CUỐI |
| 5 | Ghi `04_DesignSystem/link.md` (url + ngày + version); chạy lại V-DS với `--published-url` |

P7b = Không → giữ file local, `link.md` ghi "chưa publish — <lý do>"; vẫn là deliverable hợp lệ (có thể publish sau bằng đúng các bước trên).

**Version sau (DELTA / Luồng 2 không đổi DS):** không tạo artifact mới — **revise** artifact cũ theo `SKILL.md` § Revising (đọc index + file sẽ sửa, gửi chỉ file đổi, index cuối), `lastChange.note` ghi thay đổi. Folder version mới vẫn giữ bản `project/` mới nhất.

---

## 7. Anti-pattern

- ❌ Format khác type (md tự chế, tokens dạng map, thiếu cover / preview)
- ❌ Màu / font / shadow "hợp lý" không có trong dữ liệu quan sát
- ❌ Thêm component hệ thống không có; bỏ component có mà không ghi "Chưa đồng bộ"
- ❌ Vẽ lại logo, thay icon bằng bộ khác mà không ghi rõ
- ❌ Chỉnh màu của hệ thống cho đạt tương phản — giữ nguyên, ghi chú
- ❌ README có tiêu đề `#`, ghi nguồn / cách làm, chung chung không gọi tên token
- ❌ Gọi `type_url` lần 2 (tạo artifact trùng); gửi index trước các file khác
- ❌ Publish khi user chưa đồng ý (P7b)
