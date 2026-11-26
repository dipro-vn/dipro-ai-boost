---
description: Cập nhật bộ TC khi spec thay đổi — nhận file .xlsx đang chạy (member tải về) hoặc `[module]-testcases-vN.md` đang design. Giữ nguyên TC không đổi (cùng kết quả nếu có), sửa/xoá/thêm TC theo spec mới, ghi spec trước/sau vào Notes, ra file version mới + Changelog và cập nhật analysis.md. Không sửa file gốc.
skills:
  - rbt_manual_testing
  - testing_dimensions
  - component_checklist
  - jp_validation
  - archify
---

Cập nhật bộ TC theo spec mới. File gốc **không bị sửa**; kết quả ghi ra file version mới.

Hai loại đầu vào, cùng một quy trình:
- **`.xlsx`** — TC đang chạy, có thể đã fill kết quả (R1, R2...). TC "giữ nguyên" giữ cả kết quả; TC "sửa" bị xoá kết quả.
- **`.md`** (`[module]-testcases-vN.md`) — TC đang design, chưa chạy nên **không có kết quả**. Bước xử lý kết quả bỏ qua; mọi thứ khác giống nhau.

## Cách dùng

```
/update-tcs <file .xlsx hoặc .md> <spec mới> [--note "mô tả thay đổi"] [--module <tên module>]
```

| Input | Bắt buộc | Nội dung |
|---|---|---|
| `<file>` | Có | `.xlsx` TC đang chạy (tải từ Google Sheet, đã/chưa fill kết quả) hoặc `.md` TC đang design |
| `<spec mới>` | Có | Đường dẫn file, link (Drive / Figma / Backlog) hoặc text dán vào |
| `--note` | Không | QC nói thẳng spec đổi gì — chính xác hơn tự suy luận từ diff |
| `--module` | Không | Tên thư mục `testing/[module]/`; thiếu thì suy từ tiền tố ID TC (xem Bước 1) |

Thiếu file TC hoặc spec mới → hỏi user, không đoán. File đuôi khác `.xlsx` / `.md` → dừng, báo lỗi.

## Công cụ

Mọi thao tác đọc/ghi dùng `.claude/scripts/xlsx_tcs.py` (xem docstring đầu file); script chọn xử lý `.xlsx` hay `.md` theo đuôi file. **Không tự sửa file TC bằng cách khác** (sửa tay xlsx dễ làm lệch công thức `No.`, dropdown, ô merge; sửa tay md dễ vỡ bảng và quên mã hoá ký tự đặc biệt).

```
python3 -I .claude/scripts/xlsx_tcs.py read  <file.xlsx|.md> <out.json>
python3 -I .claude/scripts/xlsx_tcs.py write <src.xlsx|.md> <changes.json> <out.xlsx|.md>
```

File tạm (`read.json`, `changes.json`) đặt trong thư mục scratchpad, không để trong `testing/`.

## Bước 1 — Đọc file TC và xác định module, version

1. Chạy `read`. Đọc JSON: mỗi sheet TC (với `.md`: mỗi `## Screen`) có `tcs[]` gồm `fields` (nội dung TC) và `results` (cột kết quả đã fill; luôn rỗng với `.md`). Sheet `kind: "other"` chỉ để tham chiếu (`High Risk & E2E` dùng ở Bước 6; với xlsx bỏ qua `Summary`, `Test view point`). Tên cột `fields` giữ đúng như trong file (md viết `Expected Results`, xlsx viết `Expected results`); `changes.json` không phân biệt hoa thường.
2. In 1 dòng tóm tắt: số sheet TC, số TC; với xlsx thêm số TC đã có kết quả / chưa chạy.
3. **Module và các file hiện có** (tên theo "Quy ước file và version" trong skill `rbt_manual_testing`; tên module = tên thư mục):
   - Module = thư mục `testing/[module]/` chứa file đầu vào, nếu file nằm ở đó; không thì theo `--module`; không có nữa thì lấy tiền tố của cột `ID` (VD `APB-002` → `APB`) rồi quét `testing/*/` tìm analysis mới nhất có `Mã module` khớp. Không tìm ra → coi như **không có analysis** và không có thư mục module (xem Bước 2).
   - Có module → chạy `python3 -I .claude/scripts/module_files.py info testing/[module]` để biết analysis và testcases mới nhất cùng version lớn nhất của module.
4. **Version mới:** `N` = lớn nhất trong (version lớn nhất của module theo `info`, version của file đầu vào theo `module_files.py version <file>` hoặc mục `Changelog` của nó). Version mới = `N+1`. Mọi file mới của lần này đều mang số `N+1`.
   - **Ngoại lệ:** nếu analysis mới nhất của module có version **lớn hơn** version của file TC đầu vào (VD bản Quick `testcases-v1`, rồi `/analyze-req` đã tạo `analysis-v2` cho spec mới), thì version mới của TC = **đúng số version của analysis đó**, **không** cộng thêm và **không** tạo thêm file analysis (analysis đó đã là bản cho spec mới; Bước 3 bỏ qua, chỉ dùng nó làm nguồn đọc).
   - File TC mới: `testing/[module]/[module]-testcases-v[N+1].xlsx|.md` (cùng loại với file đầu vào). Dùng `module_files.py path testing/[module] testcases [N+1] xlsx|md`. File đầu vào không đổi dù nằm ở đâu: member tải xlsx từ Google Sheet về thì file mới vẫn được ghi vào `testing/[module]/`.
   - Không xác định được module (không có thư mục `testing/[module]/`) → ghi cạnh file gốc với tên `[tên file gốc bỏ hậu tố version]-v[N+1].xlsx|.md`.

## Bước 2 — Xác định spec đổi gì

Đọc spec mới (và `--note` nếu có). Tạo **danh sách thay đổi spec** theo đơn vị AC:

- **Có `analysis.md`:** so spec mới với `Acceptance Criteria` hiện có → AC đổi nội dung / AC bị bỏ / AC mới. Đây là nguồn chính.
- **Analysis đã được cập nhật trước** (ngoại lệ ở Bước 1: analysis mới nhất có version lớn hơn file TC): AC hiện có đã là AC của spec mới nên so với spec sẽ không thấy khác biệt. Thay vào đó lấy danh sách thay đổi bằng cách so `Acceptance Criteria` của analysis ngay trước đó (version lớn nhất nhỏ hơn analysis mới nhất, nếu có) với analysis mới nhất; không có analysis cũ hơn thì dựa vào `--note` và nội dung TC.
- **Không có `analysis.md`:** so trực tiếp spec mới với TC và `--note`; Traceability dùng ID trong cột `Traceability ID`. In cảnh báo 1 dòng: `Không có analysis.md — độ chính xác thấp hơn, TC không có Traceability sẽ giữ nguyên và gắn cảnh báo.`
- **TC bản Quick** có Traceability là `REQ-xx`, không khớp `AC-xx` của analysis: không phân loại được theo Traceability → dựa vào `--note` và nội dung TC (như trường hợp không có analysis), ghi cảnh báo 1 dòng. Traceability của TC giữ nguyên `REQ-xx`.
- `--note` mâu thuẫn với kết quả diff → **ưu tiên `--note`**, ghi mâu thuẫn vào Changelog.

Với mỗi thay đổi, ghi rõ **spec v_cũ** và **spec v_mới** bằng 1 câu ngắn. Phần "spec cũ" chỉ lấy từ nguồn thật: AC cũ trong `analysis.md` hoặc `Expected results` của TC cũ. **Không có căn cứ thì bỏ phần cũ, không đoán.**

## Bước 3 — Cập nhật `analysis.md` (nếu module có)

**Bỏ qua bước này** nếu đã áp dụng ngoại lệ ở Bước 1 (analysis mới nhất đã mới hơn file TC): không tạo thêm file analysis, không sửa analysis.

1. Lấy analysis mới nhất (`module_files.py latest testing/[module] analysis`) và tạo file mới `testing/[module]/[module]-analysis-v[N+1].md` từ nội dung của nó. **File cũ giữ nguyên, không sửa.** Từ đây `analysis.md` trong tài liệu này là file mới. Số version của analysis và TC luôn là cùng `N+1`; analysis cũ có thể mang số thấp hơn N.
2. Sửa file analysis mới theo spec mới; đây là **bản hiện hành** (các command khác lấy version lớn nhất nên sẽ đọc file này):
   - `Acceptance Criteria`: sửa AC đổi, đánh dấu AC bị bỏ là `Removed (v[N+1])` (không xoá dòng, để TC cũ còn trace được), thêm AC mới với ID kế tiếp. AC mới thuộc chức năng chưa có REQ → tạo REQ mới **và** thêm tên REQ/luồng mới vào `Summary` (Luồng trong scope) để không có REQ mồ côi.
   - Các mục liên quan (`Summary`, `System Model`, `Q&A`, `Impact Analysis`...) chỉ sửa chỗ spec mới thực sự đụng tới.
   - **Design (nếu analysis cũ có `Screen Inventory`):** `<spec mới>` là link Figma, hoặc `--note` nói design đổi → đọc design theo `## Design Integration` của skill `requirements_analyzer` (Figma 2 phase, có checkpoint chọn page/frame), rồi cập nhật `Screen Inventory` và bảng DIF-xx chỗ design thực sự đổi. Screen mới → thêm vào Inventory (TC UI + TC chức năng thêm ở Bước 4 như AC mới); Screen bị bỏ → đánh dấu `Removed (v[N+1])`, không xoá dòng. Design không đổi hoặc không có Figma thì bỏ qua, không đọc lại.
   - Điểm mơ hồ phát sinh do spec mới → thêm Q&A theo quy tắc Question Gate của `requirements_analyzer`, không tự chốt.
   - `History`: thêm `- v[N+1] ([ngày]): /update-tcs — [tóm tắt thay đổi spec], AC đổi: ...` (số version là `N+1`, khớp tên file).
3. **Diagram (nếu analysis cũ có):** analysis cũ có dòng link diagram ở đầu file (`> Sơ đồ để dễ hình dung ...`) thì vẽ lại cho `v[N+1]` theo bước 5b của `/analyze-req` (skill `archify`, loại `lifecycle` cho State, `workflow` cho Luồng dữ liệu):
   - Copy `diagrams/[module]-state-vN.json` / `[module]-flow-vN.json` thành `v[N+1]`, đổi `meta.output` sang `v[N+1].html`, sửa **chỉ chỗ** mục `Vòng đời / State` và `Luồng dữ liệu` (text) vừa đổi ở bước 2; text không đổi thì giữ nguyên nội dung diagram. Chạy `finalize` như bước 5b (file `v[N+1]` mới nên không có receipt cũ cần xoá).
   - Cập nhật dòng link đầu file analysis mới sang `v[N+1]`. **File diagram `vN` giữ nguyên.**
   - `finalize` fail không sửa được, hoặc thiếu Node/Chrome → **bỏ dòng link** trong analysis mới (không để link trỏ tới diagram cũ lệch spec) và ghi vào báo cáo cuối `Diagram chưa cập nhật`.
   - Analysis cũ không có diagram thì không tạo mới ở đây (chạy `/analyze-req` nếu cần).

## Bước 4 — Phân loại từng TC

Với mỗi TC trong mọi sheet TC, xác định nhóm theo `Traceability ID` và danh sách thay đổi ở Bước 2:

| Nhóm | Điều kiện | Xử lý |
|---|---|---|
| **Giữ nguyên** | AC liên quan không đổi | Không đụng vào, giữ nội dung và kết quả |
| **Sửa** | AC liên quan đổi nội dung, làm Steps / Expected / Test Data không còn đúng | Sửa các cột cần đổi; với xlsx, kết quả bị xoá (script tự làm) vì phải test lại theo spec mới |
| **Xoá** | AC liên quan bị bỏ và TC không còn mục đích | Xoá dòng |
| **Thêm** | AC mới, hoặc ca mới do thay đổi (VD giá trị biên mới) | Thêm TC cuối sheet phù hợp |
| **Chỉ ghi chú** (không rõ liên quan) | `Traceability ID` là `N/A` / không có AC, và không chắc có bị ảnh hưởng | Giữ nguyên nội dung và kết quả, nối cảnh báo vào Notes |

Quy tắc:
- TC có nhiều Traceability ID: chỉ cần 1 AC đổi nội dung là xét "Sửa".
- Chỉ đánh "Sửa" khi nội dung TC **thật sự sai so với spec mới**. Không sửa chỉ vì AC được diễn đạt lại mà ý không đổi.
- Không dừng hỏi user. Chỗ không chắc → nhóm "Chỉ ghi chú". Thà giữ kết quả cũ kèm cảnh báo còn hơn xoá nhầm.
- TC thuộc `High Risk & E2E` xử lý như mọi TC khác (cùng ID).

## Bước 5 — Viết nội dung TC sửa và TC thêm

Tuân theo toàn bộ quy tắc sinh TC của skill `rbt_manual_testing` (Section 4), `testing_dimensions`, `component_checklist`, và `jp_validation` nếu `CLAUDE.md` có `Locale = JP`: văn phong tiếng Việt, Steps/Expected đánh số, Test Data một field một dòng, Precondition và Test Data chỉ ghi khi cần, không tag `[UI Visual]`.

- **TC sửa:** chỉ đổi những cột bị ảnh hưởng, giữ nguyên ID, văn phong, và các cột còn đúng.
- Test Data dài (VD chuỗi 255 ký tự): dùng mô tả (`a` lặp 500 lần) khi bản gốc cũng viết dạng mô tả; nếu bản gốc ghi nguyên chuỗi thì sinh nguyên chuỗi đúng độ dài mới.
- **TC thêm:** ID tiếp nối **số lớn nhất đã dùng trong file** theo tiền tố module (kể cả ID đã xoá trong lần này, không tái sử dụng). Chọn sheet theo Function/Screen gần nhất; không rõ → sheet TC cuối. `Traceability ID` điền AC mới.
- Cột **Notes** (nối vào ghi chú sẵn có của QC, không ghi đè; script tự nối):

| Nhóm | Nội dung Notes |
|---|---|
| Sửa | `[v2] spec v1: <ngắn> → spec v2: <ngắn>` (bỏ phần v1 nếu không có căn cứ) |
| Thêm | `[v2] Mới: <AC ID>` |
| Chỉ ghi chú | `[v2] Cần xem lại: <lý do ngắn, VD không có Traceability, không rõ liên quan thay đổi>` |

Mỗi phần spec v1 / v2 ngắn gọn, một câu, không quá ~120 ký tự. Số `v2` trong tiền tố là version mới.

## Bước 6 — Ghi file và Changelog

1. Tạo `changes.json` theo định dạng ở docstring của `xlsx_tcs.py`: `sheets.<tên sheet>.{delete, update, note, add}`.
2. `High Risk & E2E` (và sheet/mục khác không phải bảng TC) nếu còn nhắc ID TC đã xoá hoặc nội dung cũ (VD "2 review mới nhất"): sửa bằng `cells` (xlsx: toạ độ ô, VD `{"C17": "..."}`) hoặc `text_replace` (md: cặp `[chuỗi cũ, chuỗi mới]` theo section). ID đã xoá thay bằng `[đã xoá v2] <ID>`. Không tự thêm TC mới vào mục này; chỉ nhắc ở "Gợi ý" của báo cáo nếu có TC mới đáng đưa vào.
3. `changelog`: `version`, `date`, `source` (tên file spec / `--note`), `rows` dạng `[ID, Giữ nguyên|Sửa|Xoá|Thêm|Cần xem lại, lý do ngắn, AC liên quan]`. **Không liệt kê TC giữ nguyên từng dòng**, chỉ ghi số lượng ở báo cáo.
4. Chạy `write`. Script in số TC xoá/sửa/ghi chú/thêm và các `CẢNH BÁO` (ID không tìm thấy, cột không tồn tại). Có cảnh báo → sửa `changes.json` rồi chạy lại, không bỏ qua.
5. Chạy lại `read` trên file mới để kiểm tra: số TC = số cũ − xoá + thêm; TC "giữ nguyên" không đổi nội dung (và còn đủ kết quả với xlsx); TC "sửa" không còn kết quả (xlsx). Với `.md` nên chạy thử `/export-xlsx` nếu cần chắc file xuất được.

6. **Lưu bản chụp spec:** nếu có module và `<spec mới>` là file text/markdown hoặc text dán vào, ghi nội dung vào `testing/[module]/[module]-spec-v[N+1].md` (dùng `module_files.py path testing/[module] spec [N+1]`) để sau này đối chiếu spec giữa các version; `--note` ghi kèm ở đầu file. Spec là link (Drive / Figma / Backlog) hoặc file nhị phân (pdf, docx) thì ghi file chỉ gồm link/tên file gốc và ngày lấy, rồi nhắc user tự lưu bản chụp nếu cần. Đã có file cùng tên thì không ghi đè, báo user. Sau khi ghi bản chụp, **cập nhật dòng `> Nguồn spec: ...` ở đầu `analysis-v[N+1].md`** (nếu có) thành `> Nguồn spec: \`<đường dẫn spec gốc>\`; bản hiện hành: \`[module]-spec-v[N+1].md\` ([--note nếu có]).` để người đọc không tưởng spec gốc còn nguyên. Không có bản chụp (spec là link / file nhị phân) thì ghi `bản hiện hành: <link/tên file> (lấy ngày [ngày])`. Không đụng analysis vN cũ.
7. **Đồng bộ file còn lại:**
   - Đầu vào là **`.md`**: sau khi ghi md mới, làm "Export tự động" như `/gen-tcs` (bước 11): xlsx cùng tên chưa tồn tại thì export, đã tồn tại thì bỏ qua và in một dòng.
   - Đầu vào là **`.xlsx`**: nếu module có md TC mới nhất (`module_files.py latest testing/[module] testcases md`) có version nhỏ hơn `N+1`, ghi thêm md `[module]-testcases-v[N+1].md`: chạy `write` trên md đó với cùng thay đổi (ô của `High Risk & E2E` đổi từ `cells` sang `text_replace`). ID có trong `changes.json` mà không có trong md (VD QC tự thêm TC trong xlsx) → ghi cảnh báo vào báo cáo, không dừng. md mới chỉ phản ánh thay đổi do spec, **không gồm sửa tay của QC trong xlsx**; xlsx vẫn là bản đang chạy. Module không có md TC thì bỏ qua.

## Báo cáo cuối (in cho user, không chờ xác nhận)

```
/update-tcs — [module]: v[N] → v[N+1]
Nguồn thay đổi: <spec / --note>
Giữ nguyên: X TC (giữ kết quả)
Sửa:        Y TC → ID... (đã xoá kết quả, cần test lại)
Xoá:        Z TC → ID...
Thêm:       W TC → ID...
Cần xem lại: V TC → ID... (lý do)
File mới: <đường dẫn xlsx|md> (file gốc giữ nguyên)
File đồng bộ: <md v[N+1] nếu đầu vào là xlsx | xlsx nếu đầu vào là md và vừa export | "xlsx đã tồn tại, chưa ghi đè">
Analysis mới: <đường dẫn [module]-analysis-v[N+1].md> (bản cũ giữ nguyên)   (bỏ dòng này nếu không có analysis)
Diagram: <state/flow v[N+1] đã vẽ lại | "chưa cập nhật" nếu lỗi | bỏ dòng này nếu analysis cũ không có diagram>
```

Cuối báo cáo nhắc việc cho QC theo loại file:
- **xlsx:** (1) tải file mới lên Google Sheet và tiếp tục chạy; (2) kiểm tra số liệu sheet `Summary` có khớp số TC mới không (công thức Summary tính lại khi mở file).
- **md:** xlsx đã được export tự động nếu chưa tồn tại; chạy `/export-xlsx` khi cần xuất lại; nếu muốn review lại thì `/review-tcs`.

## Cấm

- Sửa hoặc ghi đè file đầu vào, và mọi file analysis / testcases / diagram của version cũ.
- Xoá kết quả của TC không "Sửa".
- Giữ kết quả cũ trên TC đã sửa.
- Đoán nội dung "spec v1" khi không có căn cứ.
- Dừng hỏi user giữa chừng (trừ khi thiếu input bắt buộc ở đầu command).
- Tái sử dụng ID TC đã bị xoá.
