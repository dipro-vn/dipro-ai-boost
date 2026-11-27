---
name: ui_compare
description: So sánh design Figma (expect) với UI web thật (actual) để ra danh sách nghi bug UI — thừa/thiếu item, vị trí, kích thước, khoảng cách, màu, chữ, viền, bo góc, ảnh/icon — theo từng kích thước màn hình. Đi từ khung tổng thể đến chi tiết từng item. Dùng trong /ui-compare.
---

# UI Compare

Skill này hướng dẫn tìm **điểm khác nhau giữa design Figma và UI web thật**, kể cả lệch vài pixel (margin, padding, width, height...). Kết quả là **danh sách nghi bug** để QC kiểm tra nhanh, không phải kết luận cuối.

Tư tưởng chính:

- **Số đo là chính, ảnh pixel là phụ.** So số đo của từng item đã ghép (rộng, cao, vị trí, đệm, màu, chữ...). Pixelmatch chỉ cắt ảnh từng item để làm bằng chứng và bắt lỗi mà số đo bỏ sót (ảnh, icon, bóng đổ). Không chạy pixelmatch trên cả trang.
- **AI ghép item, script đo và so số.** Ghép Figma ↔ web cần hiểu ngữ nghĩa (dữ liệu mock khác dữ liệu thật, design có chỗ vẽ sai) nên AI làm; script chỉ làm việc cố định.
- **Mọi con số chỉ là nghi bug.** Design có thể sai, dữ liệu có thể khác. QC quyết định cuối.

## Khi nào dùng

- Có link Figma (node cụ thể) và URL web thật của cùng một màn hình, muốn tìm chỗ UI lệch design.
- **Không dùng** để kiểm logic/chức năng (dùng `rbt_manual_testing`, `gen-automation`), và không dùng để chuẩn hoá bug report (dùng `bug_reporter` sau khi QC xác nhận nghi bug).

## Đầu vào

| Thông tin | Ghi chú |
|---|---|
| Tên module | Tên thư mục `testing/[module]/` |
| URL web thật | Trang public, hoặc đã đăng nhập (QC tự đăng nhập, không gửi mật khẩu vào chat) |
| Danh sách `kích thước = node Figma` | Ví dụ `1440=5532:43972`, `375=1234:5678`. Mỗi kích thước ghép với đúng 1 frame Figma |
| (tuỳ chọn) bước thao tác | Mở modal, chọn tab... trước khi so |

Size nào không có frame Figma thì **không có chuẩn để so số**: chỉ kiểm tràn ngang, chữ bị cắt, item đè nhau và ghi rõ "chưa so với design".

## Phạm vi so sánh

| Nhóm | Kiểm gì | Bước so | Pha |
|---|---|---|---|
| Thừa/thiếu item | Khối/item có ở design mà thiếu trên web, và ngược lại | 2, 3 | 1 |
| Vị trí, thứ tự | Item đúng chỗ, đúng thứ tự | 1–3 | 1 |
| Kích thước | Rộng, cao | 4 | 1 |
| Khoảng cách | Đệm trong item, khoảng cách giữa các item | 3, 4 | 1 |
| Màu sắc | Màu chữ, nền, viền, độ mờ | 4 | 1 |
| Chữ | Font, cỡ, độ đậm, chiều cao dòng | 4 | 1 |
| Viền, bo góc, bóng đổ | Độ dày, màu, độ bo, bóng | 4, 5 | 1 |
| Ảnh, icon | Đúng hình, kích thước, không méo | 4, 5 | 1 |
| Chữ cố định | Nhãn, nút, tiêu đề đúng như design (gắn độ chắc chắn thấp nếu design là mock) | 4 | 1 |
| Nhiều kích thước | Mỗi size ghép 1 frame Figma | 0 | 1 (viết sẵn, mới thử 1440) |
| Trạng thái | hover, focus, disabled, lỗi, rỗng | — | 2 (chưa làm) |
| Hiệu ứng chuyển động, app iOS/Android | — | — | Ngoài phạm vi |

Giá trị dữ liệu động (tên, ngày, số liệu) **không so giá trị**; chỉ so kiểu và định dạng.

## Thứ tự so sánh (từ tổng thể đến chi tiết)

| Bước | So gì | Ví dụ |
|---|---|---|
| 0 | Điều kiện chung: kích thước, đã tải xong, font có tải không, trạng thái dữ liệu giống design không | Dev 100 hàng, design 10 hàng → ghi "khác dữ liệu" |
| 1 | Khung tổng thể: sidebar, header, chiều rộng vùng nội dung, lề trang | Sidebar 280 so với 210 |
| 2 | Các khối lớn: thừa/thiếu, thứ tự, khoảng cách dọc giữa các khối | Thiếu khối "絞り込み条件" |
| 3 | Bên trong khối: bố cục hàng/cột, khoảng cách giữa các item | Thanh chuyển trang thụt 15px |
| 4 | Chi tiết từng item: kích thước, đệm, font, màu, bo góc, viền | Nút cao 32 so với 34 |
| 5 | Ảnh pixel của các item đã ghép: bằng chứng, bắt lỗi ảnh/icon/bóng | Ảnh diff nút |

**Quy tắc đi kèm:**

1. **So vị trí tương đối trong khối cha**, không so vị trí tuyệt đối trên trang. Cha lệch bao nhiêu thì báo **một lần** ở bước của cha; item con không báo lại phần lệch kế thừa đó.
2. **Dừng nhánh khi khối không ghép được.** Khối thiếu/thừa thì báo ở bước đó, không so tiếp item bên trong.
3. **Bước 4 vẫn chạy đầy đủ** dù bước trên có lỗi: cha lệch không có nghĩa item con đúng.
4. **Báo cáo xếp theo bước** (khung → khối → bên trong khối → chi tiết); trong mỗi bước xếp theo độ chắc chắn giảm dần.
5. Cặp nào AI không chắc khi ghép thì đánh dấu độ tin cậy ghép "thấp" và không báo bug từ cặp đó (chỉ liệt kê ở mục "Chưa chắc ghép").

## Phân công và dữ liệu trung gian

Mọi file trung gian nằm trong `testing/[module]/uicompare/vN/` (N theo `module_files.py`).

| File | Ai tạo | Nội dung |
|---|---|---|
| `meta-<size>.xml`, `figma-src/*.json`, `figma-src/map-*.json` | AI lưu kết quả Figma MCP; ánh xạ id do script gợi ý, AI duyệt | Dữ liệu thô từ Figma và ánh xạ id bản copy → bản gốc (để truy ngược nguồn) |
| `figma-<size>.json` | Script `figma_meta` (từ các file thô trên) | Cây node Figma đã chuẩn hoá, kèm nguồn (`sources`, `styleFetched`, `sourceOverrides`) |
| `dom-<size>.json` | Script `dom_extract` | Cây phần tử web thật: tag, chữ ngắn, vị trí tuyệt đối, style tính toán (kèm `margin`, `gap`, `display` để nêu nguyên nhân lệch khoảng cách; không so trực tiếp vì Figma không có margin) |
| `pairs-<size>.json` | AI | Danh sách cặp đã ghép Figma ↔ web, kèm bước (level) và độ tin cậy ghép |
| `result-<size>.json` | Script `compare` | Chênh lệch theo cặp, `checks` (11 loại × trạng thái), `elements`, `unmatchedDomCandidates` |
| `coverage-<size>.json`, `coverage-<size>.md` | Script `coverage` | Bảng phạm vi và mức độ kiểm tra, tự đối chiếu số liệu giữa các file |
| `figma-img/*.png`, `pixel-<size>/act-img/*.png`, `pixel-<size>/diff/*.png`, `pixel-<size>/diff-strict/*.png`, `pixel-<size>/pixel.json` | AI tải ảnh Figma; script cắt ảnh web và so | Bằng chứng pixel |

**`figma-<size>.json`:**
```json
{ "frame": {"id": "5532:43972", "name": "...", "width": 1440, "height": 1150},
  "nodes": [ {"id": "5532:57608", "name": "Data → Button", "type": "frame",
              "parent": "5532:57522", "x": 970, "y": 17, "w": 124, "h": 34,
              "text": "スカウトを送信",
              "style": {"color": "#424242", "bg": "#ffffff", "fontSize": 14, "lineHeight": 20,
                        "fontWeight": 500, "padding": [6,12,6,12], "radius": 8,
                        "borderWidth": 1, "borderColor": "#e4e4e7", "opacity": 1} } ] }
```
`x`, `y` là vị trí **tương đối trong node cha**, đúng như Figma trả về. Trường `style` chỉ điền cho node đã ghép (xem "Lấy dữ liệu Figma").

**`pairs-<size>.json`:**
```json
[ {"figma": "5532:57608", "dom": 412, "role": "button", "level": 4,
   "match": "cao", "note": "nút hàng 1"} ]
```
`dom` là số thứ tự phần tử (`i`) trong `dom-<size>.json`. `match` là độ tin cậy ghép: cao / trung bình / thấp. Các trường khác:

| Trường | Dùng khi |
|---|---|
| `"dom": null` | Item có trong design nhưng không thấy trên web → ra mục "thiếu" |
| `"figma": null` | Item có trên web nhưng không có trong design → ra mục "thừa" |
| `"skip": ["cao"]` | Khối có nội dung động (danh sách, bảng: 10 hàng ở design, 100 hàng ở web) → bỏ so chiều cao. Giá trị được: `rộng`, `cao`, `vị trí`, `vị trí dưới`, `style`, `text` |
| `"shiftBy": ["<id Figma>"]` | Phía trên có khối bị thiếu (đã ghép `dom: null`) làm item này lệch dọc → lệch dọc đó ghi vào `inherited`, không thành nghi bug riêng |
| `"checkText": true` | Chữ cố định (nhãn, nút, tiêu đề) cần đối chiếu nguyên văn. Chỉ so khi đánh dấu cờ này. Chữ Figma lấy từ chính node nếu nó là chữ, nếu là khung thì từ **đúng một** node chữ trong cây con chưa có cặp riêng (không có hoặc nhiều hơn một thì `not_comparable`; đã ghép riêng thì `skipped`). Chữ web lấy từ chính phần tử, rỗng thì lấy từ con cháu. **AI phải điền `text` (nội dung thật) cho node chữ Figma cần so**; `name` chỉ là tên node, không bao giờ được dùng thay chữ |
| `"domBox": {"of": <i>, "inset": [trên, phải, dưới, trái]}` hoặc `[x, y, rộng, cao]` | Khối Figma không có thẻ web riêng (ví dụ cột nội dung mà web không bọc bằng một thẻ, hàng điều khiển cuối bảng). Khai khung ảo; để `dom: null`. **Nên dùng dạng `{of, inset}`**: lấy khung của một phần tử web rồi thu vào theo `inset`, nên dịch theo khi bố cục đổi (dạng số cố định bị sai khi bố cục đổi, đã gây báo nhầm trong bộ kiểm thử). Khối vẫn được so kích thước/vị trí, không có style |

`pairs-<size>.json` có thể là mảng cặp (dạng cũ) hoặc `{"pairs": [...], "exclude": [...]}`. `exclude` là danh sách phần tử **chủ động loại khỏi phạm vi so**, mỗi mục bắt buộc có `reason` (thiếu lý do hoặc id không tồn tại thì script báo lỗi, không ghi file): `{"figma": "id"|[ids], "dom": i|[i], "figmaChildrenOf": "id", "domChildrenOf": i, "keep": 3, "scope": "subtree"|"node", "reason": "..."}`. Mặc định loại cả cây con. `domChildrenOf` + `keep: 3` loại các con từ vị trí thứ 4 trở đi (ví dụ chỉ so 3 hàng đầu của danh sách; làm cả hai phía Figma và web). **Không dùng `exclude` cho phần tử chỉ vì ghép không được**: phần tử đó phải ở trạng thái `unmatched_figma` hoặc ứng viên web chưa ghép. Muốn bỏ một thuộc tính của phần tử vẫn được so thì dùng `skip`, không dùng `exclude`.

**Ghép cặp:** theo vai trò cấu trúc (hàng thứ N, cột thứ M, loại: nút, nhãn, ảnh, checkbox, tiêu đề), **không ghép theo chữ** của dữ liệu động. Dùng ảnh chụp cả hai bên để đối chiếu khi cần. Chọn đúng khối cha: vị trí của item được đo trong khối cha gần nhất đã ghép, nên ghép sai khối cha sẽ làm lệch cả nhánh.

## Chạy script

Cài một lần (Node >= 18): `cd .claude/scripts/ui_compare && npm install && npx playwright install chromium`. Script tự tìm Chromium có sẵn trong cache của Playwright nếu bản mặc định không mở được.

| Bước | Lệnh (chạy từ thư mục gốc project; `D` = `testing/[module]/uicompare/vN`; `U` = `.claude/scripts/ui_compare`) |
|---|---|
| Khung cây Figma | AI lưu kết quả `get_metadata` ra `D/meta-<size>.xml`, rồi `node U/figma_meta.mjs --in D/meta-1440.xml --out D/figma-1440.json --source original --file-key <key> --file-name <tên>` (ghi nguồn; `--styled-subtree <id,...>` đánh dấu node đã được AI điền style từ Figma MCP chính thức) |
| Tra cứu DOM (để ghép cặp) | `node U/dom_find.mjs --dom D/dom-1440.json --text "<chữ>"` hoặc `--tag button [--within <i>]` hoặc `--tree <i> --depth 3` hoặc `--box "x,y,w,h"`. Đừng đọc cả `dom-<size>.json` (hàng nghìn phần tử). Tìm theo **chữ** có thể sót (chữ nằm trong phần tử con, có khoảng trắng); đối chiếu với ảnh chụp trước khi kết luận "thiếu" |
| Đo web thật | `node U/dom_extract.mjs --url <URL> --width 1440 --out D/dom-1440.json` (ra thêm ảnh toàn trang `D/dom-1440.png`). Tuỳ chọn: `--height`, `--steps <file.json>` (thao tác trước khi đo), `--storage <file>` (đã đăng nhập), `--wait <ms>` |
| So số liệu | `node U/compare.mjs --figma D/figma-1440.json --dom D/dom-1440.json --pairs D/pairs-1440.json --out D/result-1440.json` (tuỳ chọn: `--tol`, `--color-tol`, `--opacity-tol`) |
| Ảnh bằng chứng | `node U/pixel_diff.mjs --figma ... --dom ... --pairs ... --shot D/dom-1440.png --figma-img D/figma-img --out D/pixel-1440` (tuỳ chọn: `--threshold 0.05`, `--only id1,id2`) |
| Phạm vi và mức độ kiểm tra | `node U/coverage.mjs --result D/result-1440.json --figma D/figma-1440.json --pixel D/pixel-1440/pixel.json --out D/coverage-1440` (ra `.json` và `.md`; tự đối chiếu số liệu giữa các file, mã thoát 3 nếu không khớp) |
| So danh sách chữ (chế độ `--quick`) | `node U/text_diff.mjs --figma D/figma-<size>.json --dom D/dom-<size>.json --out D/text-<size>.json` (ứng viên thiếu/thừa chữ, AI đối chiếu ảnh) |
| Báo cáo HTML | `node U/report_html.mjs --md testing/<module>/<module>-uicompare-vN.md` (ra `.html` cùng tên; `--inline` để nhúng ảnh thành một file gửi đi) |
| Đăng nhập trang cần login | `node U/node_modules/playwright/cli.js open --save-storage=U/.auth/<tên miền>.json <URL>`: QC tự đăng nhập rồi đóng cửa sổ; sau đó đo với `--storage` file đó (không bao giờ đưa mật khẩu vào chat hay file) |

Ảnh Figma lưu ở `D/figma-img/<id, dấu ':' và ';' đổi thành '-'>.png`. Chỉ xuất ảnh cho item nhỏ (nút, nhãn, ô); item quá lớn (> 400.000 pixel) script bỏ qua.

`result-<size>.json` có 4 phần: `findings` (nghi lệch, mỗi dòng có `group`: size / position / style / text / missing / extra), `inherited` (lệch do cha hoặc do khối thiếu, không báo thành bug riêng), `uncertain` (cặp có `match` "thấp") và `ok` (cặp không có nghi lệch; `okComplete` là cặp mà mọi phép áp dụng đều đã so và khớp). Ngoài ra mỗi cặp có `checks` với đủ 11 loại phép kiểm tra (position, size, padding, radius, border, background, text_color, font_size, font_weight, opacity, text_content), mỗi loại một trạng thái: `passed`, `mismatch` (có `inherited` nếu lệch theo cha hoặc khối thiếu), `not_comparable` (thiếu dữ liệu, có lý do), `skipped` (bỏ qua theo `skip`/`checkText`), `not_applicable` (loại này không áp dụng cho node, ví dụ node không phải chữ; không tính vào mẫu số). `elements.figma` đếm mỗi node Figma một trạng thái (matched, uncertain, missing_on_web, text_via_parent, excluded, unmatched_figma) kèm danh sách `unmatchedFigma` và `excluded`; `unmatchedDomCandidates` liệt kê khối web lớn (mặc định từ 100x20) nằm trong phần tử đã ghép nhưng chưa ghép, đã loại lớp bọc trùng khung cha, tổ tiên của phần tử đã ghép và vùng `exclude`, gom theo thẻ và kích thước. Đây chỉ là **ứng viên cần xác minh** (có thể là item thừa, cũng có thể là phần AI chưa ghép), không tự thành nghi bug. `ok` không có nghĩa là đã kiểm đủ: phải đọc `checks`. `meta.summary` đếm theo loại; `meta.consistency` tự kiểm `checks` với `findings`. Vị trí theo chiều dọc được đo bằng **khoảng cách tới khối liền trên** (cùng cha, chồng nhau theo chiều ngang), không đo từ mép trên của cha, để lệch không cộng dồn qua các khối xếp chồng; chiều ngang đo khoảng cách tới cạnh trái hoặc phải của khối cha (cạnh nào sát hơn trong design). AI đọc kết quả này để viết báo cáo theo mẫu bên dưới, gom các lệch cùng nguyên nhân (ví dụ cùng một nút lệch ở 3 hàng, hoặc đệm và chiều cao cùng một nút) thành một nghi bug; **AI chịu trách nhiệm phân loại** (thiếu / thừa / có nhưng sai, kèm nhãn người xử lý; xem mục Phân loại kết quả) và gán độ chắc chắn.

`pixel-<size>/pixel.json`: **mỗi cặp một bản ghi** với `status`: `compared` (đã so; có `strict` = chưa căn và `aligned` = sau khi dò lệch ±4px kèm `offset`, và `figmaImage` ghi nguồn ảnh), `not_comparable` (chưa có ảnh Figma, khối ảo, thiếu phần tử), `skipped` (nằm trong `exclude`, ảnh quá lớn so với giới hạn xử lý), `invalid_capture` (ảnh Figma không phải 1:1 so với node, vùng web nằm ngoài ảnh chụp, ảnh chụp sai tỉ lệ so với viewport). `summary` đếm theo trạng thái. Khi báo cáo, ghi cả `strict` và `aligned` nếu khác nhau; tỉ lệ pixel lệch chỉ là bằng chứng, không dùng để suy ra mức độ nghiêm trọng hay nâng độ chắc chắn.

Nếu trang thật tràn ngang (`page.overflowX` = true trong `dom-<size>.json`) thì ghi rõ trong báo cáo, kể cả khi size đó chưa có frame Figma để so.

## Lấy dữ liệu Figma

Nguồn dữ liệu Figma có hai phần, lưu riêng để truy ngược: **hình học** (vị trí, kích thước, cây cha-con) luôn lấy từ **file gốc**; **style** (màu, viền, bo góc, đệm, chữ) và **nội dung chữ** lấy từ file gốc nếu được, hoặc từ **bản copy** khi không có quyền chạy plugin (xem figma-console bên dưới). Mọi file thô lưu vào `D/` (`meta-<size>.xml`, `figma-src/*.json`) để khi có sai lệch biết dữ liệu nào đến từ file nào.

**1) Khung và hình học (file gốc, Figma MCP chính thức; cần `create_session` trước).** `get_metadata` cho node của size; ghi XML vào `D/meta-<size>.xml` (có thể rất dài, chỉ cần khung, các khối lớn, 3 hàng đầu của danh sách lặp), rồi `figma_meta.mjs --in D/meta-<size>.xml --out D/figma-<size>.json --source original --file-key <key> --file-name <tên>`. Lưu ý khung cả frame lớn chỉ trả sparse; gọi theo khối vừa. Nếu cắt bớt XML, ghi vào báo cáo rằng design có nhiều hàng hơn phần đã lưu.

**1b) Khung, hình học, style và chữ trong một lần (figma-console chạy được trên file gốc).** Nếu plugin figma-console đang mở trên **chính file gốc** (`list_files` thấy file key trùng key trong link), bỏ bước 1 và cả mục 2: gọi `get_design_context node_id="<frame>" depth=12 visible_only=true out="D/figma-src/original-<size>.json"` (thay `D` bằng đường dẫn thật). **Không** truyền `compact`: bản `compact` trả màu dạng chuỗi hex, script không đọc được. `out` để tool tự ghi JSON ra file, AI không chép tay; `visible_only` bỏ lớp ẩn (lớp đánh dấu, bản nháp) để không bị báo nhầm là thiếu trên web. Rồi `node U/figma_meta.mjs --in D/figma-src/original-<size>.json --out D/figma-<size>.json --source original --file-key <key> --file-name <tên>`. JSON này đã có hình học, style và `text`, nên mọi node có style đều `styleFetched: true`; node ẩn (`visible: false`) cũng bị script bỏ nếu còn sót. Không cần connector chính thức, không tốn lượt gọi. File chỉ có quyền xem thì làm như bước 1 và mục 2.

**Lấy toàn bộ chữ của frame (để soát chữ, `checkText`).** figma-console: `find_nodes node_id="<frame>" types=["TEXT"] fields=["characters","fontSize","fontName"] max_results=500` trả mọi node chữ kèm nội dung, cỡ và font trong một lần gọi.

**2) Style và chữ — cách A: connector chính thức.** `get_design_context` ở **cấp khối vừa** (một hàng, một thanh, một ô), `excludeScreenshot: true`: một lần gọi trả style của mọi con. Không gọi từng lá, không gọi cả bảng hay cả trang (sẽ trả sparse). Code trả về là Tailwind: `px-[12px]` = đệm trái/phải 12, `py-[6px]` = đệm trên/dưới 6, `rounded-[8px]` = bo góc 8, `text-[14px]` = cỡ chữ, `opacity-50` = độ mờ 0.5; quy đổi sang `style` trong `figma-<size>.json`. Sau khi điền style cho **cả khối** đã gọi, chạy `figma_meta.mjs --out D/figma-<size>.json --styled-subtree <id khối,...>` để đánh dấu `styleFetched` (chỉ cho khối thật sự đã gọi, vì từ đó thuộc tính vắng được hiểu là giá trị mặc định). **Điền `text` (nội dung thật) cho node chữ cần so (`checkText`)**; `name` không được dùng thay chữ. Giới hạn lượt gọi: tài khoản View seat gói Professional từng chạm giới hạn sau vài chục lần; mỗi màn hình dùng ít lượt nhất (1 metadata, 1 ảnh khung, vài lần theo khối), tái dùng kết quả đã có, và khi bị chặn thì dừng, báo khối nào chưa lấy (không đoán).

**2) Style và chữ — cách B: figma-console (cách 2 trong `README.md`).** Plugin chạy trong Figma Desktop, không giới hạn lượt gọi, trả JSON có sẵn style và chữ (`fills`, `strokes`, `strokeWeight`, `cornerRadius`, `padding`, `opacity`, `fontSize`, `fontName`, `text`), `figma_meta.mjs` tự đổi sang `style`. Plugin chỉ bật được khi QC có quyền sửa file; không có quyền thì copy frame sang file cá nhân (id node đổi). Quy trình với bản copy:
1. `get_design_context` của khối cha (ví dụ `Page`) với `depth` lớn, không `compact`, `visible_only=true`, `out="D/figma-src/copy-<tên>.json"`: tool tự ghi JSON ra file, không chép tay.
2. `figma_meta.mjs --in D/figma-src/copy-<tên>.json --out D/figma-<size>.json --suggest-map D/figma-src/map-<tên>.json --from <id copy> --to <id gốc> --source copy` gợi ý ánh xạ theo cấu trúc (ghép con theo tên và kích thước, bỏ qua node dư ở một phía).
3. Duyệt `map-<tên>.json`: mục `needsReview` và `unmatched` (`missing: "source"` = bản copy thiếu node gốc; `missing: "target"` = bản copy dư node). Lưu bản đã duyệt thành `map-<tên>-approved.json` với `source: "copy"` và `dataTypes: ["style", "text"]` cho mỗi cặp (hình học không được phép lấy từ bản copy).
4. `figma_meta.mjs --in D/figma-src/copy-<tên>.json --out D/figma-<size>.json --merge --source copy --file-key <key bản copy> --file-name <tên> --map D/figma-src/map-<tên>-approved.json`. Script báo lỗi (không ghi file) khi ánh xạ trùng hoặc thiếu node, ghi `sourceMappingWarnings` khi kích thước bản copy lệch bản gốc (đưa vào báo cáo); node gốc không có tương ứng giữ `styleFetched: false`.
5. Nếu đã có style lấy trực tiếp từ file gốc, đối chiếu với style từ bản copy để kiểm bản copy khớp bản gốc, ghi kết quả vào báo cáo.

`styleFetched`: `true` nghĩa là style đã được lấy (thuộc tính vắng = giá trị mặc định: không viền, nền trong suốt, bo góc 0, độ mờ 1); `false` nghĩa là chưa có dữ liệu (các phép về style là `not_comparable`).

**3) Ảnh để so pixel.** Ảnh node xuất kèm bóng đổ hoặc phần con tràn ra ngoài nên có thể lớn hơn node (ví dụ node 124x34 → ảnh 128x38). Ảnh sai tỉ lệ sẽ bị `pixel_diff` đánh dấu `invalid_capture`.
- **figma-console (ưu tiên khi plugin chạy được):** `download_assets` ghi thẳng ra file, nhiều node trong một lần gọi, node lỗi không làm hỏng cả lô:
  `download_assets items=[{node_id:"604:29582", format:"PNG", scale:1, exact_bounds:true, path:"D/figma-img/604-29582.png"}, {node_id:"I4174:36531;462:30466", format:"PNG", scale:1, exact_bounds:true, path:"D/figma-img/I4174-36531-462-30466.png"}, ...]` (thay `D` bằng đường dẫn thật). Bắt buộc `scale: 1` và `exact_bounds: true`: thiếu `exact_bounds` thì Figma cắt ảnh sát nét vẽ (chữ ra ảnh nhỏ hơn khung) và `pixel_diff` báo "không phải ảnh 1:1". Thông báo của tool in cả kích thước ảnh và kích thước node; hai số phải bằng nhau. Claude Code phải được mở ở thư mục gốc project (tool chỉ ghi được file bên trong thư mục đó). `get_screenshot` của figma-console chỉ để xem, không lưu ra file.
- **Connector chính thức (khi không chạy được plugin):** `get_screenshot` với `maxDimension` = `original_width` (không để mặc định, sẽ bị scale), tải về `D/figma-img/<id, dấu ':' và ';' đổi thành '-'>.png`. URL ảnh có hiệu lực ngắn, coi như bí mật.

**Ghi lại kết quả đã lấy** vào `figma-<size>.json`; chạy lại thì dùng lại, không gọi MCP lần nữa cho node đã có. Toạ độ Figma tính từ node cha: khi cần vị trí tuyệt đối phải cộng dồn lên frame gốc.

## Mức lệch được bỏ qua (dung sai) mặc định (đề xuất, chưa hiệu chỉnh trên nhiều màn hình)

| Đại lượng | Coi là khớp khi |
|---|---|
| Vị trí, rộng, cao, đệm, khoảng cách | lệch ≤ 1px |
| Cỡ chữ, độ đậm, chiều cao dòng | khớp đúng |
| Màu (chữ, nền, viền) | mỗi kênh RGB lệch ≤ 2 |
| Độ mờ | lệch ≤ 0.02 |
| Bo góc, độ dày viền | lệch ≤ 1px |
| Pixelmatch (ảnh bằng chứng) | ngưỡng 0.05 (mặc định 0.1 bỏ sót viền xám nhạt trên nền trắng) |

Dung sai chỉnh được qua tham số của `/ui-compare`; ghi dung sai đã dùng vào đầu báo cáo.

## Phân loại kết quả

Mỗi chênh lệch thuộc **một trong ba loại so với design** (trục chính của báo cáo), và có một nhãn **Người xử lý** (trục phụ):

| Loại | Nghĩa | Lấy từ đâu |
|---|---|---|
| **Thiếu so với design** | Design có, web không có | Cặp `dom: null`; node Figma chưa ghép (`elements.unmatchedFigma`) sau khi AI rà từng mục và đối chiếu ảnh |
| **Thừa so với design** | Web có, design không có | Cặp `figma: null`; `unmatchedDomCandidates` sau khi AI rà từng nhóm và đối chiếu ảnh |
| **Có nhưng sai so với design** | Có ở cả hai bên nhưng khác | `findings` (size, position, style, text), gom theo nguyên nhân gốc |

**Thiếu và thừa phải rà, không chép nguyên danh sách của script.** Mỗi mục ghi mức xác nhận: **"đã xác nhận"** (AI đã đối chiếu ảnh hoặc DOM) hay **"ứng viên"** (script liệt kê, chưa xác nhận). Khối do dữ liệu động (số hàng, giá trị trong ô, trạng thái đăng nhập...) **không** tính là thiếu, thừa hay sai: ghi ở mục "Dữ liệu động và trạng thái" cuối báo cáo, không tính vào số đếm.

**Khác biệt không nhìn thấy không phải nghi bug.** Một `finding` thuộc loại này khi đủ cả ba điều kiện: (1) AI đã đối chiếu ảnh chụp hai bên và không thấy khác; (2) nguyên nhân **đã xác minh** là khác cách dựng lớp, ví dụ: đệm hoặc nền đặt ở lớp cha thay vì lớp con, nền trắng so với trong suốt trên trang trắng, bo góc trên khung không có nền và viền, viền trong suốt, lớp bọc trong suốt lệch vài px trong khi phần tử nhìn thấy bên trong đúng vị trí; (3) không có trạng thái nào của chính màn hình này làm nó hiện ra (gõ chữ dài, hover, focus...). Những mục này ghi ở mục riêng "Khác biệt không nhìn thấy" (`KB-xx`), **không tính vào số nghi bug** và không gửi dev sửa. Thiếu một điều kiện (nguyên nhân mới là giả thuyết, hoặc sẽ hiện ra khi người dùng thao tác) thì vẫn là mục `SA-xx`.

**Nhãn Người xử lý:**

| Nhãn | Khi nào |
|---|---|
| **dev** | Có số đo rõ, web khác design, và không có dấu hiệu design cũ hoặc sai |
| **designer** | Design tự mâu thuẫn: item vẽ lùi ra ngoài khung, cùng loại item mà kích thước/đệm khác nhau giữa các hàng, độ rộng tab không đều... |
| **BA** (hoặc designer) | Chữ, nút, link, mục menu, màu chữ khác nhau mà chưa biết bên nào là chuẩn (design có thể cũ, requirement có thể đổi) |
| **QC** | Cần QC xác nhận: dữ liệu, trạng thái, khối chỉ hiện khi có điều kiện |

**Không tự quyết bên nào sai.** Hai bên khác nhau chưa đủ để kết luận web sai hay design sai. Chỉ gắn nhãn **dev** khi không có dấu hiệu nào cho thấy design cũ hoặc tự mâu thuẫn; còn nghi ngờ thì gắn nhãn **designer** hoặc **BA** và viết là "cần xác nhận". Nội dung khác design **không** mặc định là "không phải bug": nếu requirement vẫn theo design thì vẫn là lỗi.

**Giá trị suy ra không phải giá trị thiết kế.** Chiều cao của chữ khi design để chiều cao dòng tự động là kết quả tính, không phải số designer đặt. Khác biệt kiểu này ghi thành "khác biệt cần xác nhận bằng mắt" (nhãn BA/designer hoặc độ chắc chắn thấp), không gọi là bug.

**Độ chắc chắn** của từng nghi bug:
- **Cao:** số đo lệch quá dung sai ở nhiều chỗ cùng loại (ví dụ cả 3 hàng) **hoặc** số đo kèm ảnh diff đã dò lệch cùng chỉ ra. Tỉ lệ pixel lệch **không** dùng để nâng độ chắc chắn và **không** phản ánh mức nghiêm trọng, chỉ là bằng chứng bổ sung.
- **Trung bình:** chỉ có số đo, hoặc cặp ghép có độ tin cậy "trung bình", hoặc có thể do cách co giãn layout.
- **Thấp:** lệch sát dung sai (1–2px), hoặc cặp ghép thấp, hoặc design có thể là mock, hoặc giá trị design là suy ra.
- **Cần xác nhận:** thiếu/thừa khối có thể phụ thuộc dữ liệu hoặc điều kiện hiển thị; mục thiếu/thừa ở mức "ứng viên".

Trong mỗi nghi bug, ghi rõ **nguyên nhân đã xác minh** (đọc được trong CSS hoặc số đo) khác với **giả thuyết** (suy đoán); không viết giả thuyết như sự thật.

Mức độ nghiêm trọng (severity/priority) **không quyết ở đây**. Khách Nhật coi một bug UI nghiêm trọng như bug logic; QC xác nhận rồi mới chuẩn hoá bằng `/gen-bug-report`.

## Mẫu báo cáo cho QC

Viết cho QC đọc: **dễ hiểu, không viết tắt kỹ thuật** (không `px12`, `py6`). Số đo luôn có đơn vị px và nói rõ đo từ đâu tới đâu, cạnh trái hay phải.

**Từ không dùng trong báo cáo** (cả file, kể cả bảng đầu file và mục phạm vi), thay bằng lời thường:

| Không viết | Viết thay |
|---|---|
| dung sai | mức lệch được bỏ qua |
| diff, ảnh diff | ảnh chỗ khác nhau (tô đỏ) |
| pixelmatch, ngưỡng 0.05 | (bỏ, không nhắc) |
| kênh RGB | (bỏ; viết "màu gần như giống hệt") |
| khử răng cưa, anti-alias | mép chữ/mép hình bị nhoè nhẹ khi vẽ |
| căn, offset 0,1 | dịch ảnh 1px xuống dưới thì khớp |
| node, instance, frame | phần tử, khung (trong design) |
| DOM, thẻ bọc, wrapper | phần tử trên web, khung bọc ngoài |
| ghép cặp, cặp ghép | ghép phần tử design với phần tử web |
| bbox, toạ độ trang | khung, vị trí |
| viewport | cửa sổ trình duyệt |
| placeholder | chữ gợi ý trong ô nhập |

**Chỗ cần sửa viết gọn kiểu dev đọc là hiểu: tên thẻ đơn giản + thuộc tính + giá trị**, cả chế độ kỹ và chế độ nhanh. Không viết bộ chọn dài hay chi tiết kỹ thuật thừa:

| Viết thế này | Không viết thế này |
|---|---|
| `a` có `font-weight: 700` (design 400) | Đã xác minh: `a` có `font-weight: 700`; design dùng `Noto Sans JP Regular` |
| `main` có `gap: 32px`, `footer` có `padding-top: 32px` | (kèm phép cộng, lập luận dài trong cùng ô) |
| `placeholder` của `input` ô パスワード | Thuộc tính `placeholder` của `input[type=password]` |
| icon mắt (`svg`) trong ô パスワード | `span[aria-label=表示] svg` |

Quy tắc: chỉ tên thẻ trần (`a`, `input`, `main`, `footer`, `svg`), không ngoặc vuông, không chuỗi bộ chọn lồng nhau; cần chỉ rõ phần tử nào thì thêm tên trên màn hình ("ô パスワード"). Không nhắc "DevTools".

**Mỗi ô, mỗi dòng một ý, tối đa khoảng 20 chữ.** Nói điều QC nhìn thấy trước, số đo sau, và chỉ giữ một cặp số (design so với thực tế). Không nhồi phép tính, lập luận và nghi vấn vào cùng một ô: phép tính và lập luận không nhồi vào ô; nghi vấn viết thành một câu hỏi cho người xử lý. Ví dụ:

- Khó đọc: "Khung 358×21px, cách dòng 新規登録 32px; bên trong không có chữ hay link (khung trống). Từ mép dưới dòng 新規登録 tới mép trên logo chân trang là 76px"
- Viết lại: **Design:** "Có một khung trống cao 21px giữa dòng 新規登録 và logo chân trang." **Thực tế:** "Không có khung này, nên logo gần dòng 新規登録 hơn 12px (64px, design 76px)." **Câu hỏi cho designer:** "Khung trống này để làm gì? Nếu là chỗ cho link điều khoản thì web đang thiếu."

**Ảnh "chỗ khác nhau"** (`pixel-<size>/diff/`) là ảnh web có **khung đỏ** quanh từng vùng khác design. **Ảnh bằng chứng phải là ảnh của chính phần tử trong mục đó**, không phải ảnh cả khối chứa nó: người đọc nhìn ảnh phải thấy ngay điều mục đó nói, không phải tự tìm trong nhiều khung đỏ. Mục nói về link こちら thì ảnh chỉ có link こちら (design cạnh web). Một mục gồm nhiều phần tử cùng lỗi (ví dụ hai link cùng bị đậm) thì dẫn ảnh của một phần tử tiêu biểu. Chưa có ảnh riêng của phần tử thì xuất thêm rồi chạy `pixel_diff.mjs --only <id>`; không xuất được thì để trống cột ảnh, **không** dẫn ảnh cả khối thay thế. Ảnh có khung đỏ không liên quan tới mục (khung quanh phần tử khác) cũng không dẫn.

Mỗi mục đánh số theo loại: `TH-01` (thiếu), `TR-01` (thừa), `SA-01` (có nhưng sai), `KB-01` (khác biệt không nhìn thấy):

```
### SA-02: [tên ngắn, nêu item và hướng lệch]
- **Item:** [tên phần tử trên màn hình + vị trí để QC tìm]
- **Design:** [giá trị trong Figma]
- **Thực tế:** [giá trị trên web]
- **Chênh lệch:** [lệch bao nhiêu, theo hướng nào]
- **Nguyên nhân:** [gọn: thẻ + thuộc tính + giá trị, ví dụ "`a` có `font-weight: 700` (design 400)"; chưa xác minh thì ghi "giả thuyết"]
- **Cách kiểm tra:** [QC nhìn ở đâu trên màn hình, thao tác gì để thấy; ví dụ "gõ mật khẩu dài, xem chữ dừng cách icon mắt bao nhiêu" hoặc "so hai ảnh bên dưới"]
- **Người xử lý:** dev / designer / BA / QC
- **Độ chắc chắn:** cao / trung bình / thấp / cần xác nhận — [lý do ngắn]
- **Ảnh:** [đường dẫn ảnh bằng chứng, nếu có]
```

Mục thiếu/thừa dùng các trường: **Item**, **Ở design** hoặc **Ở web** (vị trí, nội dung), **Mức xác nhận** (đã xác nhận / ứng viên), **Cách kiểm tra**, **Người xử lý**, **Độ chắc chắn**.

Mục `KB-xx` viết gọn, mỗi mục một hàng của một bảng, không dùng mẫu dài ở trên:

```
| Mã | Item | Design | Thực tế | Vì sao không nhìn thấy | Lưu ý |
|---|---|---|---|---|---|
| KB-01 | 2 ô nhập, 2 nút mạng xã hội | không có nền | nền trắng | trang nền trắng | sẽ khác nếu sau này đặt trên nền màu |
```

Cấu trúc file `testing/[module]/[module]-uicompare-vN.md` (kết quả lên trước, phạm vi kiểm thử xuống sau):

1. Đầu file: màn hình, link Figma, URL, kích thước đã so, ngày, **mức lệch được bỏ qua** (không viết "dung sai", "kênh RGB", "pixelmatch"; viết đúng mẫu: "Lệch tới 1px về vị trí, kích thước thì coi là khớp; màu gần như giống hệt thì coi là khớp", đổi số nếu QC truyền `--tol`), công cụ, nguồn style/chữ (file gốc hay bản copy).
2. **Tóm tắt:** câu đầu tiên nêu **số nghi bug** (= TH + TR + SA) và mục đáng xem nhất; rồi bảng số mục theo loại (thiếu, thừa, có nhưng sai; theo người xử lý). Số mục `KB` ghi ở một dòng riêng dưới bảng ("Khác biệt không nhìn thấy: N mục, không tính là nghi bug"), không cộng vào tổng.
3. **Thiếu so với design** (`TH-xx`).
4. **Thừa so với design** (`TR-xx`).
5. **Có nhưng sai so với design** (`SA-xx`), theo thứ tự khung → khối → bên trong khối → chi tiết, chia thành:
   - 5.1 Khung và khối lớn (kích thước, khoảng cách giữa các khối)
   - 5.2 Vị trí và kích thước item
   - 5.3 Style (màu, viền, bo góc, đệm, chữ)
   - 5.4 Nội dung chữ
6. **Khác biệt không nhìn thấy** (`KB-xx`, một bảng; không tính vào số nghi bug). Không có thì bỏ mục này.
7. **Chưa kiểm / chưa chắc ghép** (cặp ghép độ tin cậy thấp, size chưa có frame Figma, trạng thái chưa so, ứng viên chưa xác nhận, node Figma chưa ghép).
8. **Dữ liệu động và trạng thái** (không tính vào số đếm): số hàng, giá trị trong ô, trạng thái đăng nhập...
9. **Phạm vi và mức độ kiểm tra:** chép nguyên **các bảng và các mục "Nguồn dữ liệu design", "Giới hạn", "Đối chiếu số liệu"** của `coverage-<size>.md`, không sửa số. Riêng phần "So pixel": chỉ chép bảng tổng; **không chép** danh sách từng cặp ("chưa căn ... pixel lệch") và từng dòng "Ảnh không hợp lệ". Thay bằng tối đa ba dòng bằng lời cho QC: bao nhiêu cặp không so ảnh được và vì sao (gom theo nguyên nhân), cặp nào có ảnh lệch đáng xem (gọi bằng tên phần tử trên màn hình, không gọi "field", "button"), và dẫn tới `uicompare/vN/coverage-<size>.md` cho ai cần chi tiết.
10. **Đã so và khớp** (liệt kê ngắn; chỉ ghi những thuộc tính thật sự đã so).

## Kiểm thử bộ so sánh

`node U/tests/run_injection_tests.mjs --url <URL> --figma D/figma-<size>.json --pairs D/pairs-<size>.json --pairs-dom D/dom-<size>.json --out <thư mục>` tiêm 6 sai lệch giả lập (menu rộng thêm 10px, nút lệch phải 3px, nút thấp 2px, chữ đổi màu, bo góc thêm 4px, ẩn một thành phần) vào trình duyệt khi đo (không đụng vào site thật), chạy lại `compare` và kiểm: phát hiện đủ không, có báo nhầm phần tử không đổi không, có gom đúng nguyên nhân gốc không. Chạy khi sửa script so sánh. Lần chạy trên Scout: 6/6 phát hiện, 0 báo nhầm; gom nguyên nhân gốc chưa đủ ở các khối chia đều chiều rộng của khối cha (xem `summary.md`). `dom_extract.mjs --eval <file.js>` chạy JS trong trang trước khi đo (dùng cho kiểm thử), mỗi phần tử web có `uid` ổn định khi một phần tử bị ẩn.

## Không làm

- Không sửa design hay code web. Không ghi vào Figma.
- Không kết luận "đúng/sai" thay QC: chỉ liệt kê nghi bug kèm độ chắc chắn.
- Không so giá trị dữ liệu động; không so trạng thái (hover, lỗi, rỗng) ở Pha 1.
- Không đoán số liệu design khi Figma MCP không trả: ghi "chưa lấy được" và dừng so item đó.
