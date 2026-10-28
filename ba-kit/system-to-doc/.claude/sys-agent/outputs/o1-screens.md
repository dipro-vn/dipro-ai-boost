# O1 — Danh sách màn hình theo website (Basic Design)

> **Câu hỏi O1 phải trả lời được:** mỗi website có **tổng bao nhiêu màn hình** · mỗi màn có **item gì** · item **xử lý thế nào, gọi API nào** · **lỗi** thì hiện gì · các màn **liên kết với nhau** thế nào.
>
> Định dạng: template công ty `templates/sample_basic_design.xlsx` + cột `S` "API gọi" (D2). **1 workbook / website**: `01_Screens/BasicDesign_<WEB-xx>_ver<N>.xlsx`, dựng bằng **`build-basic-design.py`** (không viết script tay mỗi lần).
>
> **BẮT BUỘC Read trước khi ghi:** `../basic-design/workbook-structure.md` (map cell: 5 sheet, metadata `A1:F6`, bảng item `H9:S…`, 8 nhóm nội dung, bảng ERROR SCENARIOS).

---

## 1. Nguồn — code trước, website sau (R3 · D2)

| Thứ tự | Nguồn | Lấy gì |
|---|---|---|
| 1 | **Code** — route FE, component, handler `onClick` / `onSubmit`, server action, validation, i18n message | `recon/code/<REPO>/fe-api-calls.csv` (màn → trigger / nút → API ID, có code-ref) · validation + message nguyên văn → agent ghi vào `_internal/bd/<WEB-xx>.json` (spec) kèm code-ref |
| 2 | **Website** (Playwright) | `recon/crawl/<WEB-xx>/pages.json` (item thật, trạng thái ban đầu, ảnh) · `network.json` / `console.json` (4xx/5xx, JS error — bỏ dòng có `noise`) |
| 3 | Inventory | `02_Screen` (danh sách màn, URL, Entry From, Screenshot EV) · `10_Site` (URL site) · `07_API` |

| Câu hỏi | Nơi trả lời trong workbook |
|---|---|
| Website có bao nhiêu màn | Sheet `Screen Index` (1 dòng / màn) |
| Mỗi màn có item gì | Bảng item `H–O` (tên JP/VN, type, required, maxlength, default) |
| Item xử lý thế nào | Cột `P`/`Q` — trạng thái ban đầu, hành vi khi nhấn, validation · bằng chứng ở `R` |
| Item gọi API nào | **Cột `S` "API gọi"** — từ `fe-api-calls.csv` (không dùng import graph / `table-refs.json`) |
| Lỗi hiện gì | Bảng `ERROR SCENARIOS` dưới bảng item (cột `S` = nguồn) + sheet `Screen Error message` |
| Màn liên kết thế nào | `B4`/`B6` (Cách access: "Từ SC-xxx") · `P`/`Q`: `→ SC-xxx` · Figma O5 |

---

## 2. Quy tắc điền (AS-IS)

| Ô | Quy tắc |
|---|---|
| `P`/`Q` | Hành vi **đọc được trong code** hoặc **quan sát được** trên web. Nút không bấm được trên web (READ-ONLY, thiếu quyền, thiếu ID mẫu) → mô tả từ **handler trong code**, code-ref ở `R` |
| `R` | Bắt buộc bằng chứng cho mọi mô tả: `EV-xxxx` hoặc code-ref `REPO-xx:path#Lnn`; không có → `Cần xác nhận — Q-xxx` (gate check 16) |
| `S` "API gọi" | `Mở màn → GET /api/orders (API-012)` · `POST /api/orders (API-015)` · `Không gọi API` · `Không gọi API — chuyển trang` · `Cần xác nhận — Q-xxx` · item không bấm được → `ー` (gate check 17) |
| Ô không có dữ liệu | Không áp dụng → `ー`; chưa có bằng chứng → `Cần xác nhận — Q-xxx` (JP `要確認 — Q-xxx`). **Cấm để trống** (check 19), **cấm lấp bằng nội dung không có căn cứ** (D1) |

Viết `P`/`Q`:
```
・<mô tả item>
・初期表示 / Trạng thái ban đầu: <...>
・押下時の挙動 / Hành vi khi nhấn:
  1. <đọc từ handler / đã quan sát> → gọi API-012 → chuyển SC-015
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
| 1 | Đọc code của các màn (handler, validation, i18n) theo `fe-api-calls.csv` → viết `_internal/bd/<WEB-xx>.json` (spec, xem docstring `build-basic-design.py`): item + `P`/`Q`/`R` + `errors[]` có `source`. Màn không cần sửa gì thêm → bỏ khỏi spec (script lấy item từ crawl). Nút trên web không khớp nhãn → script tự tra (không cần viết spec cho việc này): nhãn gần đúng → code của màn (`fe-screen-files.json`): `aria-label` / chữ hiển thị / icon `<XxxIcon>` → handler → API (`Trigger` / `Trigger Ref`) hoặc chuyển trang / mở hộp thoại; date picker, ô chọn, phân trang có luật riêng. Nhãn có giá trị động (ngày đã chọn, ngày giờ, số) được chuẩn hoá thành （日付）（時刻）（数値）, ô cùng loại gộp 1 dòng. "Cần xác nhận" chỉ còn khi code không cho biết | Mọi mô tả có code-ref / EV |
| 2 | Ảnh: đánh số trước khi chèn (`annotate-ui-image.py`, badge đỏ = cột `#`) → `annotated/<Screen ID>.png`, mở xem lại, khai `image` trong spec. P11 = dữ liệu thật → **không chèn ảnh** | — |
| 3 | Chạy `build-basic-design.py` (lệnh dưới) — script copy template, tạo 1 sheet / màn, `Screen Index`, `Screen Error message`, `Change History` (dòng `CHG-` tiếp theo), gỡ freeze, ghi bản gốc `--before` cho gate | exit 0 |
| 4 | Dán `bd/questions-<WEB-xx>.csv` vào `06_OpenQuestions` (Q-ID cấp từ `--q-start`, chain `next_q`) | Mọi `Cần xác nhận — Q-xxx` có Q thật |
| 5 | Gate V-BD | `FAIL = 0` |

```bash
python3 $S/build-basic-design.py --inventory $I/inventory.xlsx --site WEB-01 --version ver<N> \
    --fe-api-calls $I/recon/code/REPO-01/fe-api-calls.csv --crawl $I/recon/crawl/WEB-01 \
    --spec $I/bd/WEB-01.json --q-start <next_q> \
    --out $V/01_Screens/BasicDesign_WEB-01_ver<N>.xlsx --before $I/bd_before_WEB-01.xlsx
#   [--repo REPO-01=<path>]  # gốc repo để tra handler; mặc định cột Path ở 11_Repo
# stdout: {screens, items, api_cells, code_matched, confirm_cells, errors, next_q} — code_matched = số nút tra được
#   từ code; confirm_cells = số ô "Cần xác nhận" (báo trước/sau). "Screenshot EV" nhiều EV → ghép từng EV với pages.json
```

---

## 4. Gate V-BD

```bash
python3 $S/verify-basic-design.py "$V/01_Screens/BasicDesign_WEB-01_ver<N>.xlsx" \
    --before "$I/bd_before_WEB-01.xlsx" --expect-screens "SC-001,SC-002,..." \
    --asis --out "$I/gates/v-bd-WEB-01.md"
python3 $S/selftest-basic-design.py        # tự sinh fixture, không cần tham số
```
`--expect-screens` = toàn bộ Screen ID của site trong `02_Screen`. 15 check gốc + `--asis`: **16** mô tả có bằng chứng ở `R` · **17** button / link / form có ô "API gọi" · **18** không còn chữ cũ (D1) · **19** không ô trống cột `I..Q`.

---

## 5. Anti-pattern

- ❌ Sửa sheet `Sample` / thêm cột ngoài cột `S` đã chốt / đổi layout template
- ❌ Gộp nhiều website vào 1 workbook
- ❌ Bỏ màn vì "chưa có ảnh" — tạo sheet, ghi `NO IMAGE — text only`
- ❌ Bỏ nút vì không bấm được trên web — đọc handler trong code
- ❌ Gán API cho màn bằng import graph tĩnh (ver3 gán sai API-185 cho 11 màn) — chỉ `fe-api-calls.csv`
- ❌ Chèn ảnh đoán theo nội dung thay vì map bằng URL / Screenshot EV; ảnh chưa đánh số
- ❌ Chèn screenshot có dữ liệu người dùng thật (P11 `[B]/[C]`)
- ❌ Ghi `→ SC-xxx` mà màn đích không có trong `02_Screen`
