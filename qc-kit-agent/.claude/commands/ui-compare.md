---
description: So sánh design Figma (expect) với UI web thật (actual) theo từng kích thước màn hình, ra danh sách nghi bug UI (thừa/thiếu item, vị trí, kích thước, khoảng cách, màu, chữ, viền, bo góc, ảnh) kèm ảnh bằng chứng. So từ khung tổng thể đến chi tiết. Chạy một mạch, không dừng hỏi giữa chừng. Chỉ web (app để sau); chưa so trạng thái hover/lỗi/rỗng.
skills:
  - ui_compare
---

Thực hiện quy trình trong skill `ui_compare` cho một module. Kết quả là `testing/[module]/[module]-uicompare-vN.md` và các file trung gian trong `testing/[module]/uicompare/vN/`. Mọi dòng trong báo cáo là **nghi bug**, QC xác nhận rồi mới chuyển `/gen-bug-report`.

## Cách dùng

```
/ui-compare <link web> <link Figma> [<link Figma> ...]
/ui-compare <module> --url <URL> --sizes <size>=<node Figma>[,<size>=<node Figma>...] [--steps <file.json | "mô tả bằng lời">] [--storage <file>] [--tol 1] [--color-tol 2] [--quick]
```

Dạng ngắn (dòng đầu) đủ cho trường hợp thường gặp: gửi các link theo **thứ tự nào cũng được**, AI tự suy ra phần còn lại. Dạng đầy đủ dùng khi muốn ghi đè; hai dạng trộn được với nhau, ví dụ `/ui-compare <link web> <link Figma> --steps "bấm tab Đăng ký"`.

| Input | Bắt buộc | Nội dung |
|---|---|---|
| `<module>` | Không | Tên thư mục `testing/[module]/` (chưa có thì tạo). Không truyền thì lấy từ URL, xem "Đọc input" |
| `--url` | Có (hoặc link web trần) | URL trang web thật. Trang cần đăng nhập: không cần chuẩn bị gì, AI mở trình duyệt để QC tự đăng nhập (xem bước 1.2) |
| `--sizes` | Có (hoặc link Figma trần) | Mỗi kích thước ghép với 1 frame Figma. `<node Figma>` là link Figma có `node-id` hoặc id dạng `5532:43972`. Ví dụ `1440=<link>,375=<link>`. Link có dạng `?node-id=5532-43972` thì đổi `-` thành `:` |
| `--steps` | Không | Thao tác trước khi đo (mở tab, bấm nút, điền ô...): file JSON (xem skill), **hoặc mô tả bằng lời trong ngoặc kép**, ví dụ `"bấm tab スポット rồi bấm nút 検索"`; AI tự viết file JSON |
| `--storage` | Không | File trạng thái đăng nhập của Playwright đã có sẵn. Thường không cần: bước 1.2 tự tạo. **Không gửi mật khẩu hay token vào chat** |
| `--quick` | Không | Chế độ nhanh: so ảnh theo khối lớn và so danh sách chữ trước, chỉ đo số ở khối có lệch; báo cáo một trang. Xem mục "Chế độ nhanh". Không có cờ này là chế độ kỹ (đo mọi phần tử) |
| `--tol`, `--color-tol` | Không | Dung sai vị trí/kích thước (mặc định 1px) và màu (mặc định 2/kênh) |

**Đọc input** (trước Bước 0):

- Link có `figma.com` là design; link `http(s)` còn lại là trang web (`--url`). Giữ nguyên URL, kể cả phần `?…`.
- **Module** không truyền: lấy đoạn cuối khác rỗng của đường dẫn URL, bỏ phần `?…`, chữ thường, ký tự ngoài `a-z 0-9 -` đổi thành `-` (ví dụ `/login?next=%2Fsessions` → `login`, `/admin/sessions` → `sessions`). Đường dẫn rỗng (`/`) thì dùng phần đầu tên miền (`company.dev.vivium.jp` → `company`). Ghi tên đã chọn trong tóm tắt cuối.
- **Kích thước** của link Figma không có `<size>=`: sau Bước 0 (đã kết nối Figma), đọc bề rộng frame của node đó (`get_design_context depth=0`, hoặc `get_metadata` của connector chính thức), làm tròn thành số nguyên.
- Hỏi user, không đoán, khi: không có link web, có hơn một link web, không có link Figma, link Figma không có `node-id`, hoặc hai frame ra cùng một kích thước.

Đây là chỗ duy nhất hỏi trước khi chạy; sau đó chạy một mạch, **không dừng duyệt cặp ghép**.

## Bước 0 — Điều kiện (dừng và báo rõ nếu thiếu)

1. **Script:** có `.claude/scripts/ui_compare/node_modules` không (chạy `ls`). Chưa có thì dừng, in lệnh để QC chạy một lần:
   `cd .claude/scripts/ui_compare && npm install && npx playwright install chromium` (cần Node >= 18). **Không tự cài**: cài gói là hành động trên máy QC.
2. **Figma MCP:** (kiểm tra cả khi bắt đầu từng bước cần gọi: plugin figma-console và giới hạn lượt gọi có thể mất giữa chừng)  ưu tiên figma-console nếu đã kết nối (plugin trong Figma Desktop, không giới hạn lượt gọi): gọi `list_files`, thấy file key trùng key trong link là dùng được, **không cần `create_session`**; nhiều file đang mở thì truyền tham số `file` ở mỗi lần gọi. Không có figma-console thì dùng Figma MCP chính thức: gọi `create_session` với file key lấy từ link Figma. Cả hai đều lỗi hoặc chưa kết nối thì dừng, trỏ QC tới hướng dẫn ở `README.md` (cách 1 hoặc cách 2).
3. **Version và thư mục:** tạo `testing/[module]/` nếu chưa có (script `module_files.py` báo lỗi "Không phải thư mục" nếu thư mục chưa tồn tại). `N = max(1, <kết quả next-version> - 1)` với `python3 -I .claude/scripts/module_files.py next-version testing/[module]` (module chưa có file TC/analysis thì N = 1). Thư mục làm việc `D = testing/[module]/uicompare/vN`; tạo nếu chưa có. Đã có file cùng version thì **ghi đè** (đúng quy ước README), nêu việc này một dòng trong tóm tắt.

## Bước 1 — Với từng kích thước trong `--sizes`

Làm đúng thứ tự dưới đây; các lệnh chạy từ thư mục gốc project, `U = .claude/scripts/ui_compare`.

1. **Hình học Figma (file gốc).** Nếu figma-console đang mở trên chính file gốc (`list_files` thấy key trùng): làm theo mục **1b** trong skill (một lần `get_design_context` không `compact`, có `visible_only=true` và `out="D/figma-src/original-<size>.json"` → `figma_meta.mjs --source original`), khi đó bước 5 chỉ còn phần ảnh. Nếu không: `get_metadata` cho node của size đó, ghi XML vào `D/meta-<size>.xml` (chỉ cần khung, các khối lớn và 3 hàng đầu của danh sách lặp; ghi vào báo cáo nếu design có nhiều hàng hơn phần đã lưu), rồi `node U/figma_meta.mjs --in D/meta-<size>.xml --out D/figma-<size>.json --source original --file-key <key trong link Figma> --file-name <tên file>`.
2. **Đo web thật.** `node U/dom_extract.mjs --url <URL> --width <size> --out D/dom-<size>.json` (kèm `--steps`, `--storage` nếu có). Sau lệnh, đọc `page.url` trong `dom-<size>.json`.
   - **Bị chuyển sang trang đăng nhập** (`page.url` khác URL đã nhập): đặt `A = U/.auth/<tên miền của URL>.json`. Nếu `A` đã có và chưa thử lần này thì chạy lại với `--storage A` (phiên cũ có thể còn hạn). Nếu không: chạy **nền** `node U/node_modules/playwright/cli.js open --save-storage=A <URL>` rồi nhắn QC: "Trình duyệt vừa mở: hãy đăng nhập, mở đúng trang cần so, rồi **đóng cửa sổ** đó." Khi lệnh kết thúc (QC đã đóng cửa sổ), đo lại với `--storage A`. Vẫn bị chuyển trang thì dừng, báo QC. **Không bao giờ hỏi, gõ hay ghi mật khẩu**; file `A` chứa cookie đăng nhập, chỉ nằm trong `U/.auth/` (đã gitignore), không chép vào `testing/` hay báo cáo.
   - **`--steps` là lời mô tả:** đo một lần không có bước, tìm phần tử cần bấm/điền bằng `node U/dom_find.mjs` (theo chữ hoặc thẻ), viết `D/steps-<size>.json` (dạng `[{"click":"text=…"}, {"fill":["input[name=…]","…"]}, {"wait":500}]`, ưu tiên selector theo chữ hiển thị hoặc `name`/`id` ổn định), đo lại với `--steps D/steps-<size>.json`, rồi **xem `D/dom-<size>.png`** để chắc đã tới đúng trạng thái QC mô tả; sai thì sửa file bước và đo lại (tối đa 2 lần, vẫn sai thì ghi vào "Chưa kiểm"). Ghi nội dung file bước vào đầu báo cáo.
3. **Nhìn cả hai bên.** Chụp frame Figma bằng `get_screenshot` (để xem; figma-console: `max_dimension` 1024, connector chính thức: `maxDimension` 1024) và đọc ảnh `D/dom-<size>.png`. Dùng hai ảnh này cùng hai file JSON để hiểu cấu trúc trước khi ghép.
4. **Ghép cặp** theo skill; dùng `node U/dom_find.mjs` để tra phần tử web (theo chữ, thẻ, cây con hoặc khung số đo) thay vì đọc cả file JSON, và đối chiếu bằng ảnh trước khi kết luận một khối là "thiếu" (tìm theo chữ có thể sót) (vai trò cấu trúc, không theo chữ của dữ liệu động), ghi `D/pairs-<size>.json` (mảng cặp, hoặc `{pairs, exclude}` khi cần loại phần tử khỏi phạm vi). **`pairs` chỉ đúng với đúng file `dom-<size>.json` đã đo**: nếu đo lại web thì kiểm lại từng cặp (chỉ số phần tử có thể đã đổi, dùng `dom_find.mjs --box`):
   - Ghép đủ **khung (level 1), khối lớn (2), bên trong khối (3)** và các item chi tiết (4) đáng so.
   - Danh sách/bảng lặp: chỉ ghép **tối đa 3 hàng đầu**, ghi `skip: ["cao"]` ở khối chứa, và khai báo phần còn lại trong `exclude` kèm lý do (ví dụ `{"domChildrenOf": <i của khối chứa hàng>, "keep": 3, "reason": "Chỉ so 3 hàng đầu"}`, thêm `figmaChildrenOf` cho phía Figma nếu đã lưu các hàng đó). **Không dùng `exclude` cho phần tử chỉ vì ghép không được.**
   - Chữ cố định cần đối chiếu (nút, nhãn, tiêu đề): ghi `checkText: true`; phải có `text` cho node chữ Figma tương ứng.
   - Khối có ở design mà không có trên web: `dom: null`; khối ở trên bị thiếu làm các khối dưới lệch dọc: gán `shiftBy`.
   - Không chắc cặp nào thì `match: "thấp"`; **không dừng hỏi**, cặp đó vào mục "Chưa chắc ghép" của báo cáo.
5. **Style, chữ và ảnh từ Figma cho các cặp đã ghép** (bỏ qua con của khối không ghép được). Làm đúng theo mục "Lấy dữ liệu Figma" trong skill:
   - **Cách A (connector chính thức):** đọc guidance `figma-design-to-code` (resource `skill://figma/figma-design-to-code/SKILL.md`) trước khi gọi `get_design_context`, nhưng **không sinh code**: chỉ lấy style. Gọi `excludeScreenshot: true` ở **cấp khối vừa**, quy đổi Tailwind sang `style`, điền `text` cho node chữ cần so, rồi `figma_meta.mjs --out D/figma-<size>.json --styled-subtree <id khối đã gọi>`.
   - **Cách B (figma-console, khi hết lượt gọi hoặc không có quyền plugin trong file gốc):** lưu JSON thô vào `D/figma-src/`, gợi ý ánh xạ (`--suggest-map`), duyệt, rồi `--merge --source copy --map ...` với `dataTypes: ["style", "text"]`.
   - Với node nhỏ (nút, nhãn, ô, ảnh; tối đa khoảng 30 node): nếu figma-console chạy được thì một lần `download_assets` cho tất cả, `format: "PNG"`, `scale: 1`, `exact_bounds: true` (ảnh đúng bằng khung node, chữ không bị cắt sát), `path: "D/figma-img/<id, dấu ':' và ';' đổi thành '-'>.png"` (xem mục 3 trong skill). Không thì `get_screenshot` của connector chính thức với `maxDimension = ceil(max(rộng, cao)) + 16` để ra đúng tỉ lệ 1:1, tải về `D/figma-img/<id, dấu ':' và ';' đổi thành '-'>.png` bằng `curl -f -L`. URL ảnh có hiệu lực ngắn, coi như bí mật, không đưa vào báo cáo.
   - Gặp rate limit: dừng gọi thêm, dùng phần đã lấy hoặc chuyển cách B, ghi vào báo cáo "chưa lấy style cho: …". Không đoán style.
   - **Hết lượt gọi hoặc mất kết nối ngay ở bước 1 (khung hình học):** hình học chỉ được lấy từ file gốc, nên nếu chưa có `meta-<size>.xml` thì **dừng và báo QC** (không lấy hình học từ bản copy). Nếu đã có dữ liệu đã lưu từ lần chạy trước (`meta-<size>.xml`, `figma-src/`, `figma-img/`) thì dùng lại và ghi rõ trong báo cáo dữ liệu nào dùng lại, lấy lúc nào.
6. **So số liệu và ảnh.**
   `node U/compare.mjs --figma D/figma-<size>.json --dom D/dom-<size>.json --pairs D/pairs-<size>.json --out D/result-<size>.json` (thêm `--tol`, `--color-tol` nếu QC truyền),
   `node U/pixel_diff.mjs --figma D/figma-<size>.json --dom D/dom-<size>.json --pairs D/pairs-<size>.json --shot D/dom-<size>.png --figma-img D/figma-img --out D/pixel-<size>` (ra `pixel.json`, `act-img/`, `diff/`, `diff-strict/` trong thư mục đó),
   `node U/coverage.mjs --result D/result-<size>.json --figma D/figma-<size>.json --pixel D/pixel-<size>/pixel.json --out D/coverage-<size>` (ra `coverage-<size>.json` và `coverage-<size>.md`; thoát mã 3 nếu số liệu giữa các file không khớp thì dừng và báo QC).

7. **Design có đổi so với mốc không (cả chế độ kỹ và nhanh; chỉ khi dùng figma-console).** Gọi `diff_design node_id="<frame của size>"`, **không** truyền `baseline` và `update`: tool so với mốc mà QC đã lưu bằng nút **Save checkpoint** trong cửa sổ plugin. Ghi đúng một dòng vào bảng đầu báo cáo: "Design so với mốc ngày …: không đổi" hoặc "Design so với mốc ngày …: N thay đổi" kèm tối đa 3 thay đổi đáng chú ý nhất (chữ, thêm, xoá) viết bằng lời thường; chưa có mốc thì ghi "Chưa lưu mốc design (bấm Save checkpoint trong plugin để theo dõi thay đổi)". Lệnh **không** tự lưu hay dời mốc: chỉ QC bấm nút mới đổi. Lỗi ở bước này không chặn việc so UI.

Size nào không có frame Figma (QC không truyền) thì chỉ chạy `dom_extract` và kiểm `page.overflowX`, ghi "chưa so với design".

Lệnh script lỗi: đọc thông báo, sửa nguyên nhân (đường dẫn, id không có trong dữ liệu...) rồi chạy lại một lần; vẫn lỗi thì ghi vào mục "Chưa kiểm" của báo cáo, không bỏ qua im lặng.

## Chế độ nhanh (`--quick`)

Mục tiêu: trả lời nhanh "màn này có lệch gì **nhìn thấy được**", không đo những chỗ ảnh đã khớp. Thay cho Bước 1 và Bước 2 ở chế độ kỹ; Bước 0, Bước 1.7 (design có đổi so với mốc không) và Bước 3 giữ nguyên. Với từng kích thước:

1. **Lấy dữ liệu hai bên** như Bước 1.1 đến 1.3 (hình học Figma, đo web kể cả đăng nhập và `--steps`, nhìn hai ảnh).
2. **Chỉ ghép khung và các khối lớn** (level 1 và 2, thường 4 đến 12 cặp: header, từng khối nội dung, footer), ghi `D/pairs-<size>.json`. Vùng dữ liệu động (tên người dùng, nội dung ô trong bảng, hàng thứ 4 trở đi của danh sách) khai báo trong `exclude` kèm lý do như chế độ kỹ.
3. **Ảnh Figma của từng khối:** một lần `download_assets` (`format: "PNG"`, `scale: 1`, `exact_bounds: true`) cho các khối đã ghép, không xuất khung cả trang.
4. **So:**
   `node U/compare.mjs --figma D/figma-<size>.json --dom D/dom-<size>.json --pairs D/pairs-<size>.json --out D/result-<size>.json` (vị trí, kích thước, khoảng cách giữa các khối),
   `node U/pixel_diff.mjs ... --out D/pixel-<size> --max-area 4000000` (các tham số còn lại như Bước 1.6),
   `node U/text_diff.mjs --figma D/figma-<size>.json --dom D/dom-<size>.json --out D/text-<size>.json` (thêm `--skip-under <id>` cho phần không phải UI web, ví dụ thanh trạng thái điện thoại).
5. **Chọn khối cần xem kỹ.** Một khối là "có lệch" khi: `compare` báo lệch vị trí hoặc kích thước quá dung sai; hoặc `pixel_diff` tìm ra `offset` khác 0; hoặc ảnh `diff/<id>.png` của khối (ảnh web có **khung đỏ** quanh vùng khác design; số khung là `aligned.regions` trong `pixel.json`) có khung đỏ mà khi nhìn vào thấy khác thật (chữ khác, icon khác, thiếu viền...). Nhoè mép chữ đã được script lọc; khung đỏ còn sót quanh chữ giống hệt nhau thì bỏ qua. Tỉ lệ pixel không dùng làm ngưỡng. Với `text-<size>.json`: đối chiếu từng ứng viên với ảnh (chữ gợi ý trong ô nhập và chữ trong ảnh không nằm trong DOM, không tính là thiếu nếu ảnh web có); dữ liệu động không tính.
6. **Chỉ với khối có lệch:** ghép thêm các phần tử bên trong khối đó vào `pairs`, lấy style (`get_design_context` của khối), chạy lại `compare` để nói được lệch bao nhiêu px, ở thuộc tính nào, kèm nguyên nhân đã xác minh, viết gọn. Khối không lệch thì **không đo thêm**. Với mỗi phần tử sẽ thành nghi bug: xuất ảnh Figma của **chính phần tử đó** (`download_assets`, `exact_bounds: true`) rồi chạy lại `pixel_diff.mjs` với `--only <id các phần tử đó>` để có ảnh bằng chứng riêng cho từng mục.
7. **Báo cáo một trang** `testing/[module]/[module]-uicompare-vN.md` (rồi `report_html.mjs` như thường lệ), đúng thứ tự, không thêm mục khác:
   - Bảng đầu file như chế độ kỹ, thêm dòng "Chế độ: nhanh (`--quick`)".
   - **Kết luận** (1 đến 2 câu): số nghi bug và mục đáng sửa nhất, hoặc "không thấy lệch nào nhìn thấy được".
   - **Ảnh hai bên:** ảnh chụp web và ảnh frame Figma.
   - **Bảng nghi bug**, mỗi mục một hàng: `Mã` (`TH`/`TR`/`SA`) | `Ở đâu` (tên phần tử trên màn hình) | `Design` | `Thực tế` | `Sửa ở đâu` (gọn: thẻ + thuộc tính + giá trị, ví dụ "`a` có `font-weight: 700` (design 400)", "`placeholder` của `input` ô パスワード"; không bộ chọn dài như `input[type=password]`, `span[aria-label=…] svg`, xem bảng trong skill; chưa xác minh thì ghi "giả thuyết") | `Người xử lý` | `Ảnh` (ảnh của **chính phần tử bị lệch**, viết dạng `![](uicompare/vN/pixel-<size>/diff/<id phần tử>.png)`; không dùng ảnh cả khối, xem quy tắc ảnh bằng chứng trong skill). Mỗi ô tối đa khoảng 20 chữ, một ý, một cặp số (xem ví dụ viết lại trong skill); phép tính không đưa vào bảng; điều chưa chắc viết thành một câu hỏi cho người xử lý ở dòng riêng dưới bảng (`SA-02, hỏi designer: ...`). Quy tắc phân loại, người xử lý và "không tự quyết bên nào sai" theo skill. Không viết mục `KB`: chỗ không nhìn thấy khác thì không đo.
   - **Chưa so** (tối đa 5 dòng): vùng dữ liệu động đã loại, trạng thái chưa so, kích thước chưa có frame, khối không so ảnh được và vì sao.
   - Dòng cuối: "Chế độ nhanh chỉ bắt lệch nhìn thấy được trên ảnh; lệch 1 đến 2px và màu gần giống có thể lọt. Cần chắc chắn từng px thì chạy lại không có `--quick`."
   Không chạy `coverage.mjs`, không viết mục "Phạm vi và mức độ kiểm tra" và "Đã so và khớp".

## Bước 2 — Phân loại và ghi báo cáo

Đọc `result-<size>.json` và `pixel-<size>/pixel.json`, rồi viết `testing/[module]/[module]-uicompare-vN.md` (đường dẫn lấy bằng `module_files.py path testing/[module] uicompare N`) đúng cấu trúc và mẫu trong skill `ui_compare` (thiếu / thừa / có nhưng sai so với design):

- Mỗi `finding` gom về nguyên nhân gốc (ví dụ đệm trên/dưới lệch cùng nút cao thiếu → một mục), xếp vào **một trong ba loại**: **thiếu** / **thừa** / **có nhưng sai so với design** (riêng khác biệt đã xác minh là không nhìn thấy thì vào mục `KB`, không tính là nghi bug, xem skill), và gán nhãn **Người xử lý** (dev / designer / BA / QC; không tự quyết bên nào sai, xem skill). `inherited` không thành mục riêng, chỉ nhắc ở mục gốc.
- **Rà thiếu và thừa, không chép nguyên danh sách của script:** đi qua `elements.unmatchedFigma` (thiếu) và `unmatchedDomCandidates` (thừa), đối chiếu ảnh và DOM, rồi ghi mỗi mục là "đã xác nhận" hay "ứng viên". Khối do dữ liệu động (số hàng, giá trị trong ô, trạng thái) đưa sang mục "Dữ liệu động và trạng thái", không tính vào số đếm.
- Khi nêu nguyên nhân của lệch khoảng cách hoặc đệm, đọc `margin`, `padding`, `gap` của phần tử web trong `dom-<size>.json` (dùng `dom_find.mjs --tree`) và ghi vào dòng "Nguyên nhân" dạng gọn thẻ + thuộc tính + giá trị (đã xác minh hay giả thuyết), xem bảng "Viết thế này / Không viết thế này" trong skill.
- Gán **độ chắc chắn** theo quy tắc trong skill; ghép `match: "thấp"` thì chỉ liệt kê ở "Chưa chắc ghép".
- Mỗi nghi bug viết theo mẫu **Item / Design / Thực tế / Chênh lệch / Cách kiểm tra / Độ chắc chắn / Ảnh**, ngôn ngữ cho QC đọc: nêu rõ cạnh nào, đo từ đâu, đơn vị px, không dùng viết tắt như `px12`, `py6`. Ảnh dẫn bằng đường dẫn tương đối tới `uicompare/vN/pixel-<size>/` (ảnh diff có ý nghĩa mới dẫn; không dẫn ảnh khi diff chỉ là nhiễu).
- Thứ tự file: tóm tắt số mục, thiếu, thừa, có nhưng sai, khác biệt không nhìn thấy, chưa kiểm, dữ liệu động, rồi **phạm vi và mức độ kiểm tra** (chép các bảng trong `D/coverage-<size>.md`, không tự ước lượng số liệu; phần so pixel chỉ chép bảng tổng và tóm tắt bằng lời, không chép danh sách từng cặp, xem skill), cuối cùng là phần đã so và khớp.
- Đầu file ghi: màn hình, link Figma, URL, kích thước đã so, ngày, mức lệch được bỏ qua (viết bằng lời thường theo mẫu trong skill, không dùng chữ "dung sai", "pixelmatch"), công cụ.
- Nguồn style/chữ (file gốc hay bản copy), cảnh báo ánh xạ (`sourceMappingWarnings`) và kết quả đối chiếu bản copy với bản gốc nếu có: ghi ở đầu file hoặc mục "Chưa kiểm".
- Ứng viên trong `unmatchedDomCandidates` mà AI **chưa** xác nhận được thì liệt kê ở "Chưa kiểm" (mức "ứng viên"), không tự thành mục thừa.
- Mục "Chưa kiểm" luôn có: trạng thái hover/lỗi/rỗng (Pha 2), size không có frame, phần Figma chưa lấy được style, cặp chỉ so 3 hàng đầu, tràn ngang nếu có.

Ghi đè file cùng version nếu đã có. **Không** sửa design, code web hay file ngoài `testing/[module]/`.

**Bản HTML để đọc và gửi:** sau khi ghi xong file `.md`, chạy `node U/report_html.mjs --md <đường dẫn file .md>`: ra file `.html` cùng tên cạnh đó, mỗi ảnh diff đặt cạnh ảnh design và ảnh web (ảnh nhỏ tự phóng to). QC cần gửi một file duy nhất cho dev, PM thì thêm `--inline` (nhúng ảnh vào file).

## Bước 3 — Tóm tắt trong chat

Ngắn gọn: số mục thiếu / thừa / có nhưng sai (và theo kích thước, theo người xử lý), 2–3 nghi bug chắc chắn nhất, số cặp chưa chắc ghép, size nào chưa so, đường dẫn báo cáo (`.md` và `.html`). Nhắc QC: xác nhận các nghi bug rồi chạy `/gen-bug-report` cho những bug thật.

## Output

`testing/[module]/[module]-uicompare-vN.md`, bản đọc `testing/[module]/[module]-uicompare-vN.html`, `testing/[module]/uicompare/vN/` (JSON trung gian, ảnh Figma, ảnh web đã cắt, ảnh diff).
