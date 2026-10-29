# O5 — Danh sách màn hình theo website (Basic Design)

> **Câu hỏi O5 phải trả lời được:** mỗi website có **tổng bao nhiêu màn hình** · mỗi màn có **item gì** · item **xử lý thế nào, gọi API nào** · **lỗi** thì hiện gì · các màn **liên kết với nhau** thế nào.
>
> Định dạng: template công ty `templates/sample_basic_design.xlsx` + cột `S` "API gọi" (D2). **1 workbook / website**: `05_Basic_Design/BasicDesign_<WEB-xx>_ver<N>.xlsx`, dựng bằng **`build-basic-design.py`** (không viết script tay mỗi lần).
>
> **BẮT BUỘC Read trước khi ghi:** `../basic-design/workbook-structure.md` (map cell: 5 sheet, metadata `A1:F6`, bảng item `H9:S…`, 8 nhóm nội dung, bảng ERROR SCENARIOS).

---

## 1. Nguồn — code trước, website sau (R3 · D2)

| Thứ tự | Nguồn | Lấy gì |
|---|---|---|
| 1 | **Code** — route FE, component, handler `onClick` / `onSubmit`, server action, validation, i18n message | `recon/code/<REPO>/fe-api-calls.csv` (màn → trigger / nút → API ID, có code-ref) · validation + message nguyên văn → agent ghi vào `_internal/bd/<WEB-xx>.json` (spec) kèm code-ref |
| 2 | **Website** (Playwright) — **chỉ Giai đoạn 2**, bổ sung phần code không cho biết | `recon/crawl/<WEB-xx>/pages.json` (item thật, trạng thái ban đầu) · `evidence/<EV>.png` (ảnh) · `network.json` / `console.json` (4xx/5xx, JS error — bỏ dòng có `noise`) |
| 3 | Inventory | `02_Screen` (danh sách màn, URL, Entry From, Screenshot EV) · `10_Site` (URL site) · `08_API_Fields` (Required, Format / Constraint) + `04_DB_Columns` (Max Length) — tra theo `field` |

**Giai đoạn 1** = chỉ đọc source code (không `--crawl`) · **Giai đoạn 2** = Playwright đã chạy (`--crawl`) → thêm item thật, lỗi trên web, ảnh có đánh số.

| Câu hỏi | Nơi trả lời trong workbook |
|---|---|
| Website có bao nhiêu màn | Sheet `Screen Index` (1 dòng / màn) |
| Mỗi màn có item gì | Bảng item `H–O` (tên JP/VN, type, required, maxlength, default) |
| Item xử lý thế nào | Cột `P`/`Q` — trạng thái ban đầu, hành vi khi nhấn, validation · bằng chứng ở `R` |
| Item gọi API nào | **Cột `S` "API gọi"** — từ `fe-api-calls.csv` (không dùng import graph / `table-refs.json`) |
| Lỗi hiện gì | Bảng `ERROR SCENARIOS` dưới bảng item (cột `S` = nguồn) + sheet `Screen Error message` |
| Màn liên kết thế nào | `B4`/`B6` (Cách access) · `P`/`Q`: "Bấm → chuyển sang màn 「<tên màn>」" (spec `next`) · Figma O4 |

---

## 2. Quy tắc điền (AS-IS)

| Ô | Quy tắc |
|---|---|
| **Tên sheet / `B1` / Screen Name** | Tên màn ngắn, khách đọc được: spec `title`, không có → `Screen Name` ở `02_Screen` đã bỏ mã / route. **Không** `SC-xxx`, route `/…`, camelCase, "chưa có tiêu đề" (check 24). Screen ID ở `F1` + `Screen Index` cột `B` (có hyperlink tới sheet) |
| Tên item `I`/`J`, mô tả `P`/`Q` | Viết theo điều người dùng thấy / làm. **Cấm** `GET/POST… /api/…`, chữ "API", tên hàm (`fetchData`, `onUpdateConfirmed`) — API ở cột `S`, tên hàm / code-ref ở `R` (check 23). Nút chỉ có trong code, không có nhãn → tên = `Cần xác nhận — Q-xxx` |
| Màn có spec `items` | Spec = danh sách item **đầy đủ**: script **không thêm dòng** từ trigger `fe-api-calls.csv` chưa khớp (nhãn "—"). Cột `S`: `api` của item → khớp nhãn (`label` / tên) với `UI Label` → không có: item bấm được = `Cần xác nhận — Q-xxx`, item khác = `ー` |
| `M` required / `N` maxlength của item nhập liệu (textbox, textarea, select, radio, checkbox, date, number, password, email) | Không bao giờ trống (check 22): giá trị từ validation FE / DTO (spec ghi thẳng) hoặc spec `field` → script tra `08_API_Fields` / `04_DB_Columns`, nguồn ghi vào `R`. `ー` chỉ khi không áp dụng (maxlength của select / radio / checkbox / date; required của item Disable). Không có → `Cần xác nhận — Q-xxx` |
| Dòng lỗi (`Screen Error message`, `Common mesage`, `ERROR SCENARIOS`) | Không ô trống (check 20): không áp dụng → `ー`; chưa biết → `Cần xác nhận — Q-xxx` (script tự cấp Q) |
| `E4`/`F4`, cột `Status` của `Screen Index` | **Bỏ** — không ghi DRAFT (check 21) |
| `P`/`Q` | Hành vi **đọc được trong code** hoặc **quan sát được** trên web. Nút không bấm được trên web (READ-ONLY, thiếu quyền, thiếu ID mẫu) → mô tả từ **handler trong code**, code-ref ở `R` |
| `R` | Bắt buộc bằng chứng cho mọi mô tả: `EV-xxxx` hoặc code-ref `REPO-xx:path#Lnn`; không có → `Cần xác nhận — Q-xxx` (gate check 16) |
| `S` "API gọi" | `Mở màn → GET /api/orders (API-012)` · `POST /api/orders (API-015)` · `Không gọi API` · `Không gọi API — chuyển trang` · `Cần xác nhận — Q-xxx` · item không bấm được → `ー` (gate check 17) |
| Ô không có dữ liệu | Không áp dụng → `ー`; chưa có bằng chứng → `Cần xác nhận — Q-xxx` (JP `要確認 — Q-xxx`). **Cấm để trống** (check 19), **cấm lấp bằng nội dung không có căn cứ** (D1) |

Viết `P`/`Q`:
```
・<mô tả item>
・初期表示 / Trạng thái ban đầu: <...>
・押下時の挙動 / Hành vi khi nhấn:
  1. <đọc từ handler / đã quan sát> → lưu dữ liệu → chuyển sang màn 「<tên màn>」
  2. <code không rõ, chưa bấm được> → Cần xác nhận — Q-007
・Validation: <rule> → E_SC014_001   (chỉ khi có code-ref hoặc đã thử nhập thật)
```

**ERROR SCENARIOS** — rà cả hai nguồn, mỗi dòng có nguồn ở cột `S`:
- Code: lỗi validation / message trong code, i18n (`spec.errors[].source` = code-ref, message nguyên văn).
- Web: trang lỗi (`errorPage`), request 4xx/5xx của trang, JS error làm hỏng chức năng — script tự thêm từ `network.json` / `console.json` (bỏ `noise` `read-only-block` / `csp-block`).

❌ Cấm ghi validation khi bằng chứng duy nhất là ảnh chụp.
❌ Cấm ghi message lỗi "nghe hợp lý" — message phải lấy nguyên văn từ code/i18n hoặc màn hình.

---

## 3. Quy trình (mỗi website)

| # | Bước | Điều kiện chuyển tiếp |
|---|---|---|
| 0 | **Bộ trích AST (mức B, giai đoạn 1)** — `ensure-env.py --flow 1` tự cài ts-morph (`scripts/ast/`, `npm ci`). Cần đủ: `fe-screen-files.json` + `fe-api-calls.csv` (recon) + `high-files.txt` (S1: `scan-sensitive.py --high-list … --sensitive-memory …`); thiếu S1 → **không chạy trích**. Chạy `ast/extract-screen.mjs` (lệnh dưới) → `$I/ast/<WEB-xx>/<WEB-xx>.json` (dữ kiện từ code: tiêu đề `<h1>`, ô nhập + nhãn `<Label htmlFor>` + bắt buộc / độ dài từ `isRequired`, `maxLength`, `register`, yup của schema màn dùng qua `yupResolver`; nút + màn chuyển tới qua `router.push(ROUTE.X)`; API ghép `fe-api-calls`; cột bảng; điều kiện hiển thị; thông báo lỗi nguyên văn yup / `setError` / `setErrorDialogMsg` / toast; không có căn cứ → "Cần xác nhận") + `fe-api-calls.ast.csv` (cột UI Label điền từ AST). Chỉ hỗ trợ React JSX (Next.js / React); framework khác → exit 4, báo chưa hỗ trợ, làm bước 1 bằng LLM | AST exit 0 |
| 1 | **LLM** đọc kết quả AST + code của màn → viết `_internal/bd/<WEB-xx>.json` theo nghiệp vụ (tên màn, mục đích, mô tả "bấm → sang màn …", dịch VN, gộp ô cùng nhóm). **Không bịa thêm dữ kiện** — dữ kiện lấy từ AST / code; AST đã có thì không phải đọc lại. Viết thêm phần AST không đọc được (logic trong hàm phức tạp, component chung) (spec, xem docstring `build-basic-design.py` + khung dưới): `title` mỗi màn, item + `P`/`Q`/`R` (+ `field`, `next`) + `errors[]` có `source`. Màn không cần sửa gì thêm → bỏ khỏi spec (script lấy item từ crawl). Nút trên web không khớp nhãn → script tự tra (không cần viết spec cho việc này): nhãn gần đúng → code của màn (`fe-screen-files.json`): `aria-label` / chữ hiển thị / icon `<XxxIcon>` → handler → API (`Trigger` / `Trigger Ref`) hoặc chuyển trang / mở hộp thoại; date picker, ô chọn, phân trang có luật riêng. Nhãn có giá trị động (ngày đã chọn, ngày giờ, số) được chuẩn hoá thành （日付）（時刻）（数値）, ô cùng loại gộp 1 dòng. "Cần xác nhận" chỉ còn khi code không cho biết | Mọi mô tả có code-ref / EV |
| 2 | **Giai đoạn 2** — ảnh **bắt buộc đánh số** (gate V-BD check 13: ảnh chèn mà chưa đánh số → FAIL). `crawl-site.js` ghi vị trí từng ô / nút / link / tiêu đề cột trên ảnh (`items[].box` · `tables[].boxes` · `linkBoxes`, 0..1) → `build-basic-design.py --crawl` **tự ghép** item với vị trí theo nhãn (khớp đúng trước, chứa nhau sau) rồi đánh số theo cột `#`. Item không thấy trên màn → không có số (ghi ở cột R). Có thể ghi đè bằng `mark: [x, y]` (0..1) trong spec → script đánh số theo cột `#` trên `crawl/evidence/<EV>.png` (`annotate-ui-image.py`) → `_internal/bd/annotated/<Screen ID>.png`, mở xem lại. Hoặc tự đánh số rồi khai `image` (+ `"image_numbered": true`). Dùng tạm ảnh cũ chưa đánh số (người dùng đồng ý, P11 = không có dữ liệu thật): `image` = `_internal/evidence/<EV>.png` (tính từ thư mục version) + `image_note` (vd "quét website 02/10/2026") → A9 ghi "ảnh chưa đánh số … giai đoạn 2 thay ảnh mới". Giai đoạn 1 bỏ bước này (A9 = "Chưa có ảnh — bổ sung ở Giai đoạn 2 (Playwright)"). P11 = dữ liệu thật → **không ghi `mark` / `image`** | — |
| 3 | Chạy `build-basic-design.py` (lệnh dưới) với `--spec` (LLM) **và** `--ast-spec` (AST): dữ kiện AST lấp chỗ trống của spec LLM (required / maxlength / màn chuyển tới / API còn trống hoặc "Cần xác nhận") và thêm thông báo lỗi LLM bỏ sót; không thêm dòng item (spec LLM có thể đã gộp). Chỉ có AST (không viết spec LLM) → `--spec <ast json>` là đủ mức B. Script copy template, tạo 1 sheet / màn, `Screen Index`, `Screen Error message`, `Change History` (dòng `CHG-` tiếp theo), gỡ freeze, ghi bản gốc `--before` cho gate | exit 0 |
| 4 | Dán `bd/questions-<WEB-xx>.csv` vào `06_OpenQuestions` (Q-ID cấp từ `--q-start`, chain `next_q`) | Mọi `Cần xác nhận — Q-xxx` có Q thật |
| 5 | Gate V-BD | `FAIL = 0` |

```json
{"screens": {"SC-007": {"title": "予約編集", "purpose": "...", "access": "...", "logic": "...",
  "items": [{"name_jp": "予約日", "name_vn": "Ngày đặt", "type": "Date", "status": "Enable", "required": "Yes",
             "field": "reserveDate", "p": "...", "q": "...", "r": "REPO-01:src/...#L40", "mark": [0.4, 0.3]},
            {"name_jp": "保存", "name_vn": "Lưu", "type": "Button", "label": "保存", "next": "SC-006", "p": "...", "q": "..."}],
  "errors": [{"item", "category", "display", "code", "msg_jp", "msg_vn", "action_jp", "action_vn", "next", "source"}]}}}
```

```bash
# Giai đoạn 1 — bộ trích AST (mọi giá trị trong <> là tham số, không cố định theo máy / dự án)
python3 $S/scan-sensitive.py --path <repo FE> --out $I/gates/sensitive.md --high-list $I/gates/high-files.txt \
    --sensitive-memory outputs/_project/preflight-memory.json
node $S/ast/extract-screen.mjs --frontend <repo FE> --workspace . --site WEB-01 --repo-id REPO-01 \
    --screens "<SC-001=/route,…  — mọi màn của site>" --screen-files $I/recon/code/REPO-01/fe-screen-files.json \
    --api-calls $I/recon/code/REPO-01/fe-api-calls.csv --s1-list $I/gates/high-files.txt --out $I/ast/WEB-01 \
    [--only SC-066,SC-068]   # chỉ trích vài màn · exit 3 thiếu S1 · exit 4 không phải React JSX
# Giai đoạn 1 — dựng (không --crawl)
python3 $S/build-basic-design.py --inventory $I/inventory.xlsx --site WEB-01 --version ver<N> \
    --fe-api-calls $I/ast/WEB-01/fe-api-calls.ast.csv --spec $I/bd/WEB-01.json --ast-spec $I/ast/WEB-01/WEB-01.json --q-start <next_q> \
    --out $V/05_Basic_Design/BasicDesign_WEB-01_ver<N>.xlsx --before $I/bd_before_WEB-01.xlsx
# Giai đoạn 2 — thêm: --crawl $I/recon/crawl/WEB-01
#   [--repo REPO-01=<path>]  # gốc repo để tra handler; mặc định cột Path ở 11_Repo
# stdout: {screens, phase, sheets, items, api_cells, code_matched, field_filled, images, confirm_cells, errors, next_q, ast_fill}
#   ast_fill = {screens lấy nguyên từ AST, filled = số ô AST lấp, errors = số lỗi AST thêm}
#   sheets = Screen ID → tên sheet; field_filled = số item lấy required / maxlength từ inventory; code_matched = số nút tra được
#   từ code; confirm_cells = số ô "Cần xác nhận" (báo trước/sau). "Screenshot EV" nhiều EV → ghép từng EV với pages.json
```

---

## 4. Gate V-BD

```bash
python3 $S/verify-basic-design.py "$V/05_Basic_Design/BasicDesign_WEB-01_ver<N>.xlsx" \
    --before "$I/bd_before_WEB-01.xlsx" --expect-screens "SC-001,SC-002,..." \
    --asis [--phase 1|2] --out "$I/gates/v-bd-WEB-01.md"   # --phase mặc định auto (đọc A9 của workbook)
python3 $S/selftest-basic-design.py        # tự sinh fixture, không cần tham số
```
`--expect-screens` = toàn bộ Screen ID của site trong `02_Screen`. 15 check gốc + `--asis`: **16** mô tả có bằng chứng ở `R` · **17** button / link / form có ô "API gọi" · **18** không còn chữ cũ (D1) · **19** không ô trống cột `I..Q` · **20** không ô trống ở dòng lỗi · **21** không còn Status / DRAFT · **22** item nhập liệu đủ required / maxlength · **23** tên / mô tả item không có API, `/api/…`, tên hàm · **24** tên màn đọc được. Check 10/13 theo Phase: Giai đoạn 1 chưa có ảnh → PASS; Giai đoạn 2 thiếu ảnh → WARN.

---

## 5. Anti-pattern

- ❌ Sửa sheet `Sample` / thêm cột ngoài cột `S` đã chốt / đổi layout template
- ❌ Gộp nhiều website vào 1 workbook
- ❌ Bỏ màn vì "chưa có ảnh" — tạo sheet, ghi `NO IMAGE — …`
- ❌ Đặt tên sheet `SC-xxx` / tên route; đưa API, tên hàm vào tên / mô tả item
- ❌ Bỏ nút vì không bấm được trên web — đọc handler trong code
- ❌ Gán API cho màn bằng import graph tĩnh (ver3 gán sai API-185 cho 11 màn) — chỉ `fe-api-calls.csv`
- ❌ Chèn ảnh đoán theo nội dung thay vì map bằng URL / Screenshot EV; ảnh chưa đánh số
- ❌ Chèn screenshot có dữ liệu người dùng thật (P11 `[B]/[C]`)
- ❌ Ghi `next` tới màn không có trong `02_Screen` (script ghi `Cần xác nhận — Q-xxx`)
