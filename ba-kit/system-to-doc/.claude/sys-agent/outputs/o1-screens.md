# O1 — Danh sách màn hình theo website (Basic Design)

> **Câu hỏi O1 phải trả lời được:** mỗi website có **tổng bao nhiêu màn hình** · mỗi màn có **item gì** · item **xử lý thế nào** · **lỗi** thì hiện gì · các màn **liên kết với nhau** thế nào.
>
> Định dạng: template công ty `templates/sample_basic_design.xlsx`. **1 workbook / website**: `01_Screens/BasicDesign_<WEB-xx>_ver<N>.xlsx`.
>
> **BẮT BUỘC Read trước khi ghi:** `../basic-design/workbook-structure.md` (map cell: 5 sheet, metadata `A1:F6`, bảng item `H9:R19`, 8 nhóm nội dung, bảng ERROR SCENARIOS).

---

## 1. Mỗi câu hỏi nằm ở đâu trong workbook

| Câu hỏi | Nơi trả lời | Nguồn dữ liệu |
|---|---|---|
| Website có bao nhiêu màn | Sheet `Screen Index` (1 dòng / màn) — tổng ở dòng cuối | `02_Screen` lọc theo `Site` |
| Mỗi màn có item gì | Bảng item `H–O` (tên JP/VN, type, required, maxlength, default) | `pages.json.items` của crawl + `04_DB_Columns.Max Length` + validation trong code |
| Item xử lý thế nào | Cột `P`/`Q` — trạng thái ban đầu, hành vi khi nhấn, validation, API gọi tới (`API-xxx`) | quan sát UI + `07_API` + `code-ref` |
| Lỗi hiện gì | Bảng `ERROR SCENARIOS` dưới bảng item + sheet `Screen Error message` / `Common mesage` | message trong code (validation / i18n) · quan sát UI khi được phép submit |
| Màn liên kết thế nào | `P`/`Q`: `→ SC-xxx` ở hành vi chuyển màn · ô **Cách access** (`A6`/`B6`): "Từ SC-xxx (menu …)" · Figma O5 Screen Flow | `02_Screen.Entry From` · link trong `pages.json` |

---

## 2. Nguồn — bắc cầu từ inventory (kit này không có SPEC.md)

| Template cần | Kit này dùng |
|---|---|
| Danh sách màn | `02_Screen` (lọc `Site = WEB-xx`) |
| URL `D1` | `02_Screen.URL / Route` |
| Ảnh UI `A9+` | `05_Evidence` loại `screenshot` khớp URL của màn (P11 = dữ liệu thật → **không chèn ảnh**, ghi `NO IMAGE — text only`) |
| `F5 Source Flow Version` | `ver<N> — AS-IS baseline` |
| `F4 Status` | `DRAFT` (mô tả hiện trạng, chưa ai duyệt) |
| Item | `pages.json.items` (label, type, required, maxlength — **không bao giờ có giá trị đã nhập**) |
| Maxlength thật | ưu tiên validation trong code (`code-ref`) > `maxlength` của DOM > `04_DB_Columns.Max Length` (ghi rõ nguồn ở cột `R`) |

---

## 3. Quy tắc AS-IS khi điền

| | Kit forward (TO-BE) | Kit này (AS-IS) |
|---|---|---|
| Cột `P`/`Q` | Hành vi **mong muốn** | Hành vi **quan sát được** / đọc được trong code |
| Cột `R` | Câu hỏi cho BrSE | **Bắt buộc `EV-xxxx`** cho mọi mô tả hành vi — gate check 16 |
| Ô không có dữ liệu | chưa quyết | `UNKNOWN — chưa quan sát được` |

Viết `P`/`Q`:
```
・<mô tả item>
・初期表示 / Trạng thái ban đầu: <...>
・押下時の挙動 / Hành vi khi nhấn:
  1. <đã quan sát> → gọi API-012 → chuyển SC-015
  2. <chưa bấm được> → UNKNOWN — chưa quan sát được (P3 READ-ONLY)
・Validation: <rule> → E_SC014_001   (chỉ khi có code-ref hoặc đã thử nhập thật)
```
Cột `R`: `EV-0031; EV-0102` hoặc `⚠ UNKNOWN — bị chặn theo P3 (Q-007)`.

❌ Cấm ghi validation khi bằng chứng duy nhất là ảnh chụp.
❌ Cấm ghi message lỗi "nghe hợp lý" — message phải lấy nguyên văn từ code/i18n hoặc màn hình.

---

## 4. Quy trình (mỗi website)

| # | Bước | Điều kiện chuyển tiếp |
|---|---|---|
| 1 | Copy `templates/sample_basic_design.xlsx` → `01_Screens/BasicDesign_<WEB-xx>_ver<N>.xlsx`; giữ thêm 1 bản gốc ở `_internal/bd_before_<WEB-xx>.xlsx` làm `--before` cho gate | 2 file tồn tại |
| 2 | Đọc lại 5 sheet bằng `openpyxl` | `Sample` có, `F6 = TEMPLATE_SCREEN` |
| 3 | Lập **Screen Creation Plan** từ `02_Screen` của site | Mọi màn có `Status` |
| 4 | Duplicate `Sample` → 1 sheet / màn (tên sheet = Screen ID) | `Sample` không bị chạm |
| 5 | Neutralize: xoá banner `A8:F8`, `F6 → WORKING_SCREEN`, điền `F1..F5` | — |
| 6 | Metadata → ảnh (`A9+`, ≤ 840×900 px, map ảnh theo URL, **cấm** đoán theo nội dung ảnh) → bảng item | Mọi item có `EV` ở `R` hoặc `UNKNOWN` |
| 7 | Catalog message: dùng lại `Common mesage` trước, thêm `Screen Error message` | Mọi code trong `P`/`Q` tồn tại |
| 8 | `Screen Index` (đủ màn, `UI Source`) + `Change History`: thêm dòng **Change ID tiếp theo** sau dòng cuối của template (template có sẵn `CHG-0001…0005` → dòng mới `CHG-0006`, nội dung "AS-IS baseline ver<N>") | gate check 12: ID liên tục |
| 9 | Gate | `FAIL = 0` |

Màn có > 11 item → chèn thêm dòng theo style chuẩn (`workbook-structure.md` §2.8), không đổi layout template.

---

## 5. Gate V-BD

```bash
python3 $S/verify-basic-design.py "$V/01_Screens/BasicDesign_WEB-01_ver<N>.xlsx" \
    --before "$I/bd_before_WEB-01.xlsx" --expect-screens "SC-001,SC-002,..." \
    --asis --out "$I/gates/v-bd-WEB-01.md"
python3 $S/selftest-basic-design.py "$V/01_Screens/BasicDesign_WEB-01_ver<N>.xlsx" --before "$I/bd_before_WEB-01.xlsx" --asis
```
`--expect-screens` = toàn bộ Screen ID của site trong `02_Screen` → gate bắt màn bị bỏ sót. 15 check gốc + **check 16** (`--asis`: mọi mô tả có `EV` hoặc `UNKNOWN`).

---

## 6. Anti-pattern

- ❌ Sửa sheet `Sample` / thêm cột / đổi layout template
- ❌ Gộp nhiều website vào 1 workbook
- ❌ Bỏ màn vì "chưa có ảnh" — tạo sheet, ghi `NO IMAGE — text only`
- ❌ Chèn ảnh đoán theo nội dung nhìn thấy thay vì map bằng URL
- ❌ Chèn screenshot có dữ liệu người dùng thật (P11 `[B]/[C]`)
- ❌ Ghi `→ SC-xxx` mà màn đích không có trong `02_Screen`
