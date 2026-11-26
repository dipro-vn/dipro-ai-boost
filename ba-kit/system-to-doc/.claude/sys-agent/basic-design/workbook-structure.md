# Ba Agent — Basic Design Workbook Structure (map thật của master workbook)

> **SOURCE:** `ba-kit/requirement-to-flow/.claude/ba-agent/basic-design/workbook-structure.md` @ 447770e — copy self-contained cho kit `system-to-doc`. Khi master workbook cua cong ty doi, sua CA HAI noi.
> **Đã tách khỏi bản gốc requirement-to-flow (D2, 27/10/2026):** bản của kit này thêm cột **`S` "API gọi"** ngay sau cột `R` (bảng item) và cột `S` "Nguồn" (bảng ERROR SCENARIOS), chữ chưa rõ ghi **"Cần xác nhận — Q-xxx"** (bản JP 「要確認 — Q-xxx」). Sheet `Sample` vẫn giữ nguyên (cột `S` chỉ thêm ở working sheet). Không sửa requirement-to-flow. Dựng tự động: `build-basic-design.py` (`../outputs/o5-basic-design.md` §4).
> Khác biệt của kit này (AS-IS thay vì TO-BE, 1 workbook / website) nằm ở `../outputs/o5-basic-design.md`. Ở kit này **"Quality Gate O4" = gate V-BD** (`verify-basic-design.py --asis`).

> **Nguồn:** đọc trực tiếp từ `sample/sample_basic_design.xlsx` ngày 23/09/2026 bằng `openpyxl`.
> Mọi con số dòng/cột dưới đây là **thật**, không phải mô tả từ tài liệu kiến trúc. Khi master workbook của dự án khác file mẫu, BA **PHẢI đọc lại workbook thật** và cập nhật mapping trước khi ghi — KHÔNG được ghi theo trí nhớ file mẫu.

---

## 1. Sheet inventory (6 sheet)

| # | Sheet | Vai trò | Mutation rule |
|---|---|---|---|
| 1 | `Common message` | Catalog message dùng chung cho nhiều màn (feedback 22/11/2026 lỗi #4: sửa chính tả `mesage` → `message`) | **Append-only** + update đúng row. Reuse trước khi tạo mới |
| 2 | `Screen Error message` | Catalog error theo từng màn | **Append** theo block Screen ID + update đúng row |
| 3 | `Sample` | **Template chuẩn** cho 1 Screen Basic Design — **chỉ tồn tại trong template `sample_basic_design.xlsx`** | ⛔ **IMMUTABLE** · builder tự xoá khỏi bản export (feedback 22/11/2026 lỗi #4) |
| 4 | `Screen Index` | Bảng tra Screen ID → tên màn / tên sheet (Screen ID có hyperlink). Bỏ cột `Status` (§5) · bỏ Master Version/Flow ID/Runtime Rule → `_internal/screen-index-meta.json` (feedback 22/11/2026 lỗi #9) | Append 1 row / 1 working sheet mới |
| 5 | `Change History` | Log mọi thay đổi | **Append-only** · builder clean CHG cũ của template trước khi append (feedback 22/11/2026 lỗi #4) |
| 6 | **`確認事項`** (sinh tự động) | Danh sách câu hỏi Q-xxx + hyperlink về ô 要確認 trong sheet màn (feedback 22/11/2026 lỗi #5) | Builder tự sinh ở cuối — xoá & viết lại mỗi lần build |

> ⚠️ **Khác với tài liệu kiến trúc v3.0:** file thật trước đây không có sheet `確認事項` + typo `Common mesage` — nay đã sửa: builder rename `Common mesage` → `Common message` khi build (feedback 22/11/2026 lỗi #4), sinh sheet `確認事項` mới ở cuối. Nếu tài liệu và workbook mâu thuẫn → **workbook thắng**.

### 1.1 Sheet 「確認事項」 — schema (feedback 22/11/2026 lỗi #5)

| Cột | Header | Nội dung |
|---|---|---|
| `A` | Mã Q | `Q-001` ... |
| `B` | Loại | QUESTION_TYPE (từ `inv_schema.py`) |
| `C` | Câu hỏi | Nội dung Q (từ `q.ask(item, reason)`) |
| `D` | Nơi hỏi (click) | Hyperlink về ô `<sheet>!<cell>` nơi ghi 要確認 — Q-xxx |
| `E` | Lý do | Vì sao cần hỏi (reason của `q.ask()`) |
| `F` | Người trả lời | Vai trò (BrSE / PM / khách) |
| `G` | Trạng thái | Open / Answered |

**Nguyên tắc:** mọi ô 要確認 — Q-xxx trong sheet màn PHẢI có 1 dòng Q tương ứng trong sheet 確認事項 (có hyperlink). V-BD check mới (lỗi #5) kiểm điều này.

---

## 2. Sheet `Sample` — template screen (cell map chính xác)

### 2.1 Vùng metadata (rows 1–6)

| Cell | Nội dung | Cell | Nội dung |
|---|---|---|---|
| `A1` | `画面名` | `B1` | `[SCREEN NAME]` |
| | | `D1` | `[SCREEN URL]` |
| `A2` | `作成者` | `B2` | `[CREATED BY]` |
| | | `D2` | `[CREATED DATE]` |
| `A3` | `更新者` | `B3` | `[UPDATED BY]` |
| | | `D3` | `[UPDATED DATE]` |
| `A4` | `概要` | `B4:D4` (merged) | `■目的` / `■アクセス方法` — block 2 mục. Builder dedup header nếu spec đã có (feedback 22/11/2026 lỗi #1) |
| `A5` | `Logic chung + Step 1 共通` | `B5:D5` (merged) | `[GENERAL LOGIC]` + **6 dòng cấp màn**: `■初期表示・データ取得` · `■権限` · `■データ範囲` · `■状態保持` · `■loading / 0件 / エラー` · `■URL tham số sai` (feedback 22/11/2026 P1-5). Thiếu 1 dòng → V-BD check 32 FAIL |
| `A6` | `Cách access` | `B6:D6` (merged) | `[ACCESS METHOD]` |

**Cột metadata phải (E/F) — BẮT BUỘC điền `F1`, `F2`, `F3`, `F5`, `F6`** (`E4`/`F4` để trống ở kit này):

> **Tên sheet = tên màn** khách đọc được (spec `title`, hoặc `Screen Name` ở `02_Screen` đã bỏ mã / route): bỏ `[]:*?/\`, tối đa 31 ký tự, trùng thì thêm ` (2)`. **Không dùng `SC-xxx` làm tên sheet** — Screen ID nằm ở `F1` và `Screen Index` cột `B` (gate check 24). Script khác tìm sheet theo `F1` / `Screen Index`, không theo tên tab.

| Cell | Key | Giá trị ở `Sample` | Giá trị phải điền ở working sheet |
|---|---|---|---|
| `E1`/`F1` | `Screen ID` | `TEMPLATE` | Screen Code từ SPEC `## Screens` (VD `AU_AUTH_001`) |
| `E2`/`F2` | `Flow ID` | `TEMPLATE` | Flow ID từ Output 1/2 |
| `E3`/`F3` | `Version` | `1.1` | `1` cho sheet mới, tăng dần mỗi lần change |
| `E4`/`F4` | ~~`Status`~~ | `TEMPLATE` | **Kit system-to-doc: để trống** (bỏ trạng thái DRAFT theo feedback; gate check 21) |
| `E5`/`F5` | `Source Flow Version` | `N/A` | Version của Output 2 đã approve (VD `v2_23092026`) |
| `E6`/`F6` | `Sheet Type` | `TEMPLATE_SCREEN` | **`WORKING_SCREEN`** — đổi ngay sau khi duplicate |

> ⛔ Nếu sau khi duplicate mà `F6` vẫn là `TEMPLATE_SCREEN` → Quality Gate O4 **FAIL**. Đây là dấu hiệu agent quên neutralize sheet.

### 2.2 Banner cảnh báo

`A8:F8` (merged) = `AGENT TEMPLATE — Do not edit directly. Duplicate this sheet to create a new Screen Basic Design.`

→ Trên working sheet: **xóa nội dung banner này**, vùng `A9` trở xuống dùng để chèn ảnh UI.

### 2.3 Vùng ảnh UI (cột A–F, từ row 9)

| | `Sample` | `Login_Sample` (reference) |
|---|---|---|
| Vị trí ảnh | trống (chỉ có banner ở `A8:F8`) | 2 ảnh anchor tại `A9` và `A14` |
| Merged cho ảnh | — | `A10:F12`, `A14:F16` |

Quy ước: **ảnh UI nằm cột A–F bên trái, bảng item nằm cột H–R bên phải, cùng dòng**.

### 2.3a Đánh số ảnh — bắt buộc trước khi chèn

> Mẫu chuẩn: `BD_01_Login.xlsx` → sheet `DA_AUTHEN_001_Login`.

| Quy tắc | Giá trị |
|---|---|
| Số trên ảnh | = cột `#` (H) của bảng item cùng sheet. Item không hiện trên ảnh → không đặt badge, ghi `R`: `Không hiển thị trên ảnh` |
| Kiểu badge | Tròn đỏ `#C41230`, chữ trắng đậm, viền trắng, đường kính ≈ 4.5% rộng ảnh (≥ 28 px), đặt góc trên-phải trong vùng item, không che nội dung |
| File | Ảnh gốc giữ nguyên; bản đánh số lưu `annotated/<Screen ID>.png` và **chỉ bản này được chèn** |
| Caption | `A9`: `Ảnh <nguồn> #<NN>-<MM> — <Screen ID> · <tên màn> · số đỏ trên ảnh = # trong bảng item`; ảnh anchor từ `A10` |
| Công cụ | `python3 .claude/skills/system-analyst/scripts/annotate-ui-image.py <gốc> <annotated> --marks "1:0.5,0.18;2:0.93,0.22" --expect <N item hiển thị>` — x,y = tâm badge (0–1 theo tỉ lệ ảnh, >1 = px). Chạy xong **mở ảnh xem lại** từng badge |

**Kích thước vùng ảnh (đo thật):**

| | Giá trị |
|---|---|
| Tổng column width `A`→`F` | 122 ký tự ≈ **854 px** |
| Chiều rộng ảnh tối đa cho phép | **840 px** (chừa lề 14 px) |
| Chiều cao ảnh tối đa | **900 px** |

> ⚠️ **Lỗi có thật trong sheet mẫu gốc:** 2 ảnh của `Login_Sample` đều là `1521 px` chèn vào vùng 854 px → **tràn ~670 px sang cột H–R, đè lên bảng item**. Gate check 13 bắt lỗi này. Quy tắc resize: ảnh ≤ 840×900 px, anchor cột `A` (`../outputs/o5-basic-design.md` §4 bước 6).

### 2.4 Bảng item (cột H–R)

**Header ở `Sample` = row 8. Ở `Login_Sample` = row 9** (lệch 1 dòng vì Login_Sample có spacer row 8 cao 6.0pt).

**Feedback 22/11/2026 lỗi #7 — quy định ngôn ngữ theo cột:**

| Cột | Ngôn ngữ | Lý do |
|---|---|---|
| `I` `K` `L` `M` `N` `O` `P` | **JP thuần** | Khách Nhật đọc: tên item, type, status, required, maxlength, default, mô tả nghiệp vụ |
| `J` `Q` | **VN thuần** | Team Việt tham chiếu |
| `R` `S` | **VN** (chú thích nội bộ) | Comment, API gọi — team đọc |
| `H` | số | — |

Builder reject giá trị trộn (VN trong cột JP: 「Cần xác nhận」 trong cột `R` phải là 「要確認」 ở cột `P`; cột `R` ghi VN phải có cặp tương ứng cột `P` JP). V-BD check mới kiểm (feedback 22/11/2026 lỗi #7).

| Cột | Header | Ghi chú điền |
|---|---|---|
| `H` | `#` | Số thứ tự |
| `I` | `項目名 Item name（JP)` | Tên item tiếng Nhật |
| `J` | `項目名 Item name（VN)` | Tên item tiếng Việt |
| `K` | `種類 (type)` | **Enum** (`bd_styles.TYPE_ENUM`): `Label` · `Textbox` · `Textarea` · `Dropdown` · `Checkbox` · `Radio` · `Button` · `Hyperlink` · `Icon` · `DatePicker` · `File` · `Toggle` · `Chip` · `Pagination` · `SearchBox` · `Image` · `Table` · `Tab`. Ngoài enum → V-BD FAIL (feedback 22/11/2026 lỗi #8) |
| `L` | `ステータス (status)` | `Enable` · `Disable` · `ー` |
| `M` | `必須 (required)` | **Enum** (`bd_styles.REQUIRED_ENUM`): `○` (bắt buộc) · `ー` hoặc `—` (tuỳ chọn) · trống. Viết văn dài 「任意（未入力で全件表示）」 → V-BD FAIL, chuyển sang cột `P` (feedback 22/11/2026 lỗi #8) |
| `N` | `最大限 (maxlength)` | số, khoảng (`8〜20`), hoặc `ー` |
| `O` | `初期値 (default)` | giá trị mặc định hoặc `ー` |
| `P` | `記述（日本語）` | Mô tả + validation + hành vi, bullet `・`, sub-list đánh số |
| `Q` | `Description (VN)` | Bản tiếng Việt của `P` — **phải khớp 1-1 về số bullet và số nhánh validation** |
| `R` | `Comment` | Câu hỏi còn treo cho BRSE · kit này: bằng chứng (`EV-xxxx` / code-ref `REPO-xx:path#Lnn`) hoặc `Cần xác nhận — Q-xxx` |
| `S` | `API gọi` *(chỉ kit system-to-doc, D2)* | API sự kiện của item gọi — nguồn `fe-api-calls.csv`: dòng "Mở màn" → `Mở màn → GET /api/orders (API-012)` · nút 「保存」 → `POST /api/orders (API-015)` · link → `Không gọi API — chuyển trang` · không gọi → `Không gọi API` · không có bằng chứng → `Cần xác nhận — Q-xxx` · item không bấm được → `ー`. Item dạng Button / Hyperlink / Form **bắt buộc** có ô này (gate V-BD check 17) |

**Số dòng đã format sẵn:** `Sample` có **11 dòng item (row 9 → row 19)** với border + row height đặt sẵn.
Nếu screen có > 11 item → **copy format của 1 row chuẩn xuống**, không được chèn row trần không border.

**Quy ước viết `P` / `Q`:** dùng `・` mở đầu mỗi bullet; nhánh validation đánh số `1.` `2.` `3.`; mọi nhánh lỗi **phải trỏ tới Message Code có thật** trong `Screen Error message` (VD `→ E_L_001`). Trỏ tới code không tồn tại → Quality Gate O4 FAIL.

### 2.5 Layout phải giữ nguyên khi duplicate

- Column widths: `A=9.7` `B=21.2` `C=17.8` `D=40.5` `E=19.0` `F=22.0` `G=9.7` `I=32.2` `J=22.0` `K=14.0` `L=12.5` `N=14.3` `O=12.5` `P=55.0` `R=36.5` `S=8.7` (working sheet kit này: `S=40` cho cột "API gọi")
- **Không freeze panel** ở mọi sheet (R13) — template có freeze sẵn ở `Screen Index` / `Change History` (`A6`), `build-basic-design.py` gỡ khi sinh file
- Row heights vùng item: row 9=54.8, 10=74.2, 11=204.0, 12=170.2, 13=125.2, 14=70.5, 15=85.5, 16=171.8, 17=83.2, 18=80.2, 19=261.8
- Page setup: **orientation = landscape**
- Merged ranges gốc: `A8:F8`, `B4:D4`, `B5:D5`, `B6:D6`

---

### 2.6 Tám nhóm nội dung bắt buộc → ánh xạ vào cell nào

> Một screen sheet phải chứa đủ 7 nhóm nội dung dưới. **Template thật chỉ có sẵn vùng riêng cho 4 nhóm đầu** — 3 nhóm cuối phải gửi vào cell free-text đang có.
>
> ⛔ **KHÔNG được thêm cột / thêm sheet / đổi layout của template công ty** để "cho đủ chỗ". Template là tài sản dùng chung, đổi nó ảnh hưởng mọi dự án khác. **Ngoại lệ duy nhất đã chốt (D2):** cột `S` "API gọi" / "Nguồn" ở working sheet của kit system-to-doc.

| # | Nhóm | Vùng trong sheet | Bắt buộc |
|---|---|---|---|
| 1 | **Metadata** | `B1`/`D1` tên + URL · `B2`/`D2` tác giả + ngày tạo · `B3`/`D3` người sửa + ngày sửa · `F1`–`F6` Screen ID / Flow ID / Version / (trống) / Source Flow Version / Sheet Type | ✅ |
| 2 | **Overview** | `B4` (merged `B4:D4`) block `■目的` + `■アクセス方法` · `B5` Logic chung · `B6` Cách access | ✅ |
| 3 | **UI reference** | Vùng ảnh `A9+` (`A9` caption, ảnh neo `A10`). **Không có ảnh** → `Screen Index` cột `H` (UI Source) = `NO IMAGE — …`; `A9` = `Chưa có ảnh — bổ sung ở Giai đoạn 2 (Playwright)` (Giai đoạn 1) | ✅ (khai báo bắt buộc, ảnh thì không) |
| 4 | **Items** | Bảng `H9:R19` — 11 dòng có sẵn format, mở rộng bằng cách copy format row chuẩn | ✅ |
| 5 | **Behavior** | **Không có vùng riêng** → viết trong cột `P` (JP) / `Q` (VN) của chính item gây ra hành vi: action, state, validation, transition, error reference | ✅ |
| 6 | **Traceability** | **Không có vùng riêng** → thêm block thứ ba vào `B4`:<br>`■トレーサビリティ / Traceability`<br>`FR No. <n> · RQ-<id> · SPEC ## Screen Details <Screen Code>`<br>Cấp flow đã có sẵn ở `F2` (Flow ID) + `F5` (Source Flow Version) | ✅ |
| 7 | **Known gaps** | **Không có vùng riêng** → cấp item: cột `R` (Comment), tiền tố `⚠`<br>cấp screen: `Screen Index` cột `K` (Notes) | ✅ khi có gap |
| 8 | **Error scenarios** | Bảng riêng **dưới bảng item** — xem §2.9 | ✅ khi màn có Non-Happy Case |

**Quy ước viết nhóm 5 Behavior trong `P`/`Q`** (theo đúng `Login_Sample`):

```
・<mô tả item>
・初期表示 / Trạng thái ban đầu: <...>
・押下時の挙動 / Hành vi khi nhấn:
  1. <nhánh 1> → <đích hoặc Message Code>
  2. <nhánh 2> → <đích hoặc Message Code>
```

**Quy ước nhóm 7 Known gaps:** mọi ô không có evidence **ghi `Cần xác nhận — Q-xxx` (JP `要確認 — Q-xxx`), không để trống và không tự điền**, kèm 1 dòng `⚠ <thứ còn thiếu> — Need Confirm` ở cột `R`. Để trống lặng lẽ = người đọc tưởng "không áp dụng"; tự điền = biến giả định thành spec.

---

### 2.7 Ví dụ 1 item điền đầy đủ (trích từ sheet mẫu trước khi gỡ bỏ)

> Sheet `Login_Sample` từng nằm trong file mẫu để minh hoạ format. Nó **đã được gỡ** (xem §1 ghi chú) vì gây nhầm lẫn khi copy sang master dự án. Toàn bộ đặc tả nó minh hoạ được chốt lại ở §2.1–§2.6; ví dụ cụ thể giữ lại dưới đây.

**Item: ô nhập email của màn Login**

| Cột | Giá trị |
|---|---|
| `I` 項目名 JP | `メールアドレス入力欄` |
| `J` 項目名 VN | `Ô nhập địa chỉ email` |
| `K` 種類 | `Textbox` |
| `L` ステータス | `Enable` |
| `M` 必須 | `Yes` |
| `N` 最大限 | `256` |
| `O` 初期値 | `ー` |

`P` 記述（日本語）:
```
・メールアドレスを入力するためのテキストボックス
・プレースホルダー：「メールアドレス」
・半角英数字・特殊文字（@, _, .）を入力可能
・最大文字数：256文字
・バリデーション：
  1. 未入力の場合 → E_L_001
  2. メール形式が正しくない場合 → E_L_002
  3. 登録されていないメールアドレスの場合 → E_L_003
  4. 256文字を超える場合 → 入力不可（制御により超過入力を防ぐ）
```

`Q` Description (VN):
```
・Textbox nhập địa chỉ email
・Placeholder: 「メールアドレス」
・Cho phép nhập: chữ số, ký tự đặc biệt half-width (@, _, .)
・Maxlength: 256 ký tự
・Validation:
  1. Chưa nhập → E_L_001
  2. Sai định dạng email → E_L_002
  3. Email chưa đăng ký trong hệ thống → E_L_003
  4. Vượt quá 256 ký tự → Không cho nhập thêm (chặn input)
```

**Rút ra từ ví dụ:**
1. Mỗi bullet mở đầu bằng `・`; nhánh validation đánh số `1.` `2.` `3.`
2. Mọi nhánh lỗi trỏ tới **Message Code có thật** trong catalog
3. Nhánh không sinh lỗi (chặn input ở tầng UI) vẫn phải viết ra, không bỏ trống
4. `P` và `Q` **khớp 1-1 về số bullet và số nhánh**

> ⚠️ **Lỗi có thật trong sheet mẫu gốc — đừng lặp lại:** bản gốc ghi nhánh 2 ở cột JP là *「メール形式が正しくない場合、新規アカウント登録画面に遷移」* (sai định dạng → chuyển màn đăng ký) trong khi cột VN ghi *"Sai định dạng email → E_L_002"*, và nhánh 3 thì ngược lại. **Hai cột mô tả hai hành vi khác nhau.** Ví dụ ở trên đã sửa cho khớp. Khi điền, viết xong `Q` thì đọc ngược lại `P` để đối chiếu từng nhánh.

---

### 2.8b Ví dụ P/Q theo từng type — bắt buộc tham khảo trước khi điền

> Mỗi type có trọng tâm mô tả khác nhau. Điền không đúng trọng tâm → gate check 23 FAIL (tên hàm/API trong P/Q) hoặc nội dung không đủ ý nghĩa cho QC.

#### Button / Hyperlink — trọng tâm: hành vi khi nhấn + điều kiện enable

```
P (記述 JP):
・「保存」ボタン — 入力内容を施設情報として保存する
・活性条件：必須項目（施設名・住所）がすべて入力済みの場合のみ活性
・押下時の挙動：
  1. バリデーション通過 → POST /api/facilities → 「施設管理」画面に遷移 (SC-031)
  2. バリデーションエラー → エラーメッセージを表示、画面遷移なし → E_FAC_001
  3. APIエラー（5xx）→ トースト「保存に失敗しました」→ E_FAC_S_001

Q (Description VN):
・Button「保存」— lưu thông tin cơ sở
・Điều kiện active: chỉ active khi tất cả trường bắt buộc (tên cơ sở, địa chỉ) đã nhập
・Hành vi khi nhấn:
  1. Validation pass → POST /api/facilities → chuyển màn「施設管理」(SC-031)
  2. Validation lỗi → hiển thị lỗi, không chuyển màn → E_FAC_001
  3. API lỗi (5xx) → toast「保存に失敗しました」→ E_FAC_S_001
```

**Quy tắc riêng Button/Hyperlink:**
- Luôn ghi điều kiện active / disable (nếu có)
- Mọi nhánh phải đến đích rõ ràng: màn 「tên màn」(SC-xxx) hoặc Message Code
- Cột `S` = tên API được gọi (không ghi vào P/Q)

---

#### Textbox / Textarea / Password / Email / Number — trọng tâm: placeholder + validation từng rule

```
P (記述 JP):
・施設名を入力するテキストボックス
・プレースホルダー：「施設名を入力してください」
・全角・半角文字を入力可能
・最大文字数：100文字（超過時は入力不可）
・バリデーション：
  1. 未入力の場合 → E_FAC_002
  2. 100文字を超える場合 → 入力不可（UIで制御）
  3. 使用不可文字（<, >, "）が含まれる場合 → E_FAC_003

Q (Description VN):
・Textbox nhập tên cơ sở
・Placeholder:「施設名を入力してください」
・Cho phép nhập full-width và half-width
・Maxlength: 100 ký tự (chặn nhập khi vượt)
・Validation:
  1. Chưa nhập → E_FAC_002
  2. Vượt 100 ký tự → không cho nhập thêm (kiểm soát ở UI)
  3. Có ký tự không hợp lệ (<, >, ") → E_FAC_003
```

---

#### Dropdown / Select — trọng tâm: nguồn dữ liệu + option mặc định + hành vi khi chọn

```
P (記述 JP):
・テナントの施設を選択するドロップダウン
・初期表示：「施設を選択してください」（プレースホルダー、未選択状態）
・選択肢：ログイン中のテナントに属する施設一覧（APIで取得）
・選択時：選択した施設IDをフォームにセット、「料金プラン」欄をリセット
・必須項目：未選択のまま送信した場合 → E_FAC_004

Q (Description VN):
・Dropdown chọn cơ sở của tenant
・Ban đầu hiển thị:「施設を選択してください」(placeholder, chưa chọn)
・Danh sách option: các cơ sở thuộc tenant đang đăng nhập (lấy từ API)
・Khi chọn: set facility ID vào form, reset trường「料金プラン」
・Bắt buộc chọn: submit khi chưa chọn → E_FAC_004
```

**Quy tắc riêng Dropdown:**
- Phải ghi rõ nguồn dữ liệu (API, hardcode, hay từ màn trước)
- Ghi rõ option mặc định: placeholder hay option đầu tiên
- Nếu chọn trigger reload dữ liệu khác → ghi rõ field nào bị reset/reload

---

#### Checkbox — trọng tâm: trạng thái mặc định + hành vi khi check/uncheck

```
P (記述 JP):
・利用規約への同意チェックボックス
・初期表示：未チェック
・チェック時：「同意して続ける」ボタンが活性化
・未チェックのまま「同意して続ける」を押下した場合 → E_REG_005

Q (Description VN):
・Checkbox đồng ý điều khoản sử dụng
・Ban đầu: chưa check
・Khi check: button「同意して続ける」chuyển sang active
・Nhấn「同意して続ける」khi chưa check → E_REG_005
```

**Quy tắc riêng Checkbox (nhiều lựa chọn):**
```
P:
・通知を受け取る項目を選択するチェックボックス群
・選択肢：「メール通知」「SMS通知」「プッシュ通知」
・初期表示：「メール通知」のみチェック済み
・複数選択可能、0件選択も可
```

---

#### Radio — trọng tâm: danh sách option + option mặc định + ràng buộc chọn

```
P (記述 JP):
・支払い方法を選択するラジオボタン
・選択肢：「クレジットカード」「銀行振込」「コンビニ払い」
・初期表示：「クレジットカード」が選択済み
・選択変更時：対応する入力フォームが表示/非表示に切り替わる
・必須：未選択では送信不可（UIで制御、エラーメッセージなし）

Q (Description VN):
・Radio button chọn phương thức thanh toán
・Các lựa chọn:「クレジットカード」「銀行振込」「コンビニ払い」
・Ban đầu:「クレジットカード」được chọn
・Khi đổi lựa chọn: form nhập tương ứng hiển thị/ẩn
・Bắt buộc chọn: không submit được khi chưa chọn (kiểm soát ở UI, không có error message)
```

---

#### Table — trọng tâm: cột hiển thị + sort + phân trang + trạng thái 0 item

```
P (記述 JP):
・予約一覧を表示するテーブル
・表示列：No · 氏名 · 予約日時 · ステータス · 操作
・ソート：予約日時 降順（デフォルト）、列ヘッダークリックで昇順/降順切替
・ページネーション：1ページ20件、ページ番号とPrev/Nextボタンを表示
・0件の場合：「予約がありません」を表示、テーブル非表示
・操作列：「詳細」ボタン（全ステータス）、「キャンセル」ボタン（ステータス=確定済みのみ活性）

Q (Description VN):
・Bảng hiển thị danh sách đặt chỗ
・Các cột: No · Họ tên · Thời gian đặt · Trạng thái · Thao tác
・Sort: Thời gian đặt giảm dần (mặc định); click header để đổi chiều
・Phân trang: 20 item/trang, hiển thị số trang và nút Prev/Next
・0 item: hiển thị「予約がありません」, ẩn bảng
・Cột thao tác:「詳細」(mọi status),「キャンセル」(chỉ active khi status = 確定済み)
```

**Quy tắc riêng Table:**
- Liệt kê tên từng cột theo thứ tự từ trái sang phải
- Ghi rõ sort column mặc định và chiều sort
- Ghi rõ số item/trang
- Bắt buộc ghi trạng thái 0 item (empty state)
- Nếu có action column: ghi điều kiện enable/disable từng nút

---

#### Label / Text hiển thị — trọng tâm: nguồn dữ liệu + format

```
P (記述 JP):
・ログイン中のユーザー氏名を表示するラベル
・初期表示：プロフィール情報から取得（GET /api/me のレスポンス `fullName`）
・表示形式：姓 + 半角スペース + 名
・データなし（APIエラー）：「—」を表示

Q (Description VN):
・Label hiển thị họ tên người dùng đang đăng nhập
・Ban đầu: lấy từ thông tin profile (GET /api/me, field `fullName`)
・Định dạng: Họ + dấu cách + Tên
・Không có dữ liệu (API lỗi): hiển thị「—」
```

---

#### Tab — trọng tâm: danh sách tab + tab active mặc định + nội dung mỗi tab

```
P (記述 JP):
・画面内のコンテンツを切り替えるタブコンポーネント
・タブ一覧：「基本情報」「料金設定」「スタッフ管理」
・初期表示：「基本情報」タブがアクティブ
・タブ切替時：URLパラメータ `?tab=` を更新（ブラウザバックで前タブに戻れる）
・各タブの内容：
  - 「基本情報」：施設名・住所・電話番号の入力フォーム
  - 「料金設定」：フリーパス・回数券の料金設定 (SC-029)
  - 「スタッフ管理」：スタッフ一覧・追加・削除 (SC-030)

Q (Description VN):
・Component tab chuyển đổi nội dung trong màn
・Danh sách tab:「基本情報」「料金設定」「スタッフ管理」
・Ban đầu: tab「基本情報」active
・Khi chuyển tab: cập nhật URL param `?tab=` (back browser quay về tab trước)
・Nội dung từng tab:
  - 「基本情報」: form nhập tên, địa chỉ, SĐT cơ sở
  - 「料金設定」: cài đặt giá vé tháng và vé lượt (SC-029)
  - 「スタッフ管理」: danh sách, thêm, xoá staff (SC-030)
```

**Quy tắc riêng Tab:**
- Nếu nội dung tab là màn riêng (SC-xxx) → ghi `(SC-xxx)` sau tên tab
- Ghi rõ tab active mặc định
- Ghi state persistence (URL param / sessionStorage / không giữ)

---

#### DatePicker — trọng tâm: format ngày + range hợp lệ + giá trị mặc định

```
P (記述 JP):
・予約日を選択する日付ピッカー
・表示形式：YYYY/MM/DD
・選択可能範囲：本日以降（過去日は選択不可）
・初期表示：空欄（未選択）
・バリデーション：
  1. 未選択のまま送信 → E_BK_003
  2. 選択可能範囲外の日付（APIで検証）→ E_BK_004

Q (Description VN):
・DatePicker chọn ngày đặt chỗ
・Định dạng: YYYY/MM/DD
・Phạm vi chọn được: từ hôm nay trở đi (không chọn được ngày quá khứ)
・Ban đầu: trống (chưa chọn)
・Validation:
  1. Chưa chọn khi submit → E_BK_003
  2. Ngày ngoài phạm vi (kiểm tra phía API) → E_BK_004
```

---

#### Image / File upload — trọng tâm: loại file + dung lượng + preview

```
P (記述 JP):
・施設のサムネイル画像をアップロードするファイル入力
・対応形式：JPG, PNG, WebP
・最大ファイルサイズ：5MB
・初期表示：アップロード済み画像がある場合はプレビュー表示、なければ「画像を選択」ボタン
・アップロード時：選択直後にプレビューを更新（サーバー送信は「保存」ボタン押下時）
・バリデーション：
  1. 対応形式以外のファイル → E_FAC_010
  2. 5MBを超えるファイル → E_FAC_011

Q (Description VN):
・Input upload ảnh thumbnail cho cơ sở
・Định dạng hỗ trợ: JPG, PNG, WebP
・Dung lượng tối đa: 5MB
・Ban đầu: hiển thị preview ảnh đã upload (nếu có), nếu chưa có → hiển thị button「画像を選択」
・Khi upload: cập nhật preview ngay sau khi chọn (gửi server khi nhấn「保存」)
・Validation:
  1. File không đúng định dạng → E_FAC_010
  2. File vượt 5MB → E_FAC_011
```

---

#### Pagination — trọng tâm: hành vi khi chuyển trang

```
P (記述 JP):
・テーブルのページを切り替えるページネーションコンポーネント
・表示：現在ページ番号・総ページ数・Prev/Nextボタン・最初/最後ページボタン
・1ページあたり：20件
・Prev：1ページ目では非活性
・Next：最終ページでは非活性
・ページ切替時：テーブルデータを再取得（スクロールトップへ）

Q (Description VN):
・Component phân trang cho bảng
・Hiển thị: số trang hiện tại · tổng số trang · nút Prev/Next · nút trang đầu/cuối
・Mỗi trang: 20 item
・Prev: disabled ở trang 1
・Next: disabled ở trang cuối
・Khi chuyển trang: tải lại dữ liệu bảng (scroll về đầu trang)
```

---

#### SearchBox — trọng tâm: trigger tìm kiếm + debounce + empty state

```
P (記述 JP):
・施設名で絞り込む検索ボックス
・プレースホルダー：「施設名で検索」
・入力後300ms（debounce）でテーブルを自動絞り込み（Enterキー不要）
・検索結果0件：「該当する施設がありません」を表示
・クリアボタン（×）：入力をクリアし全件表示に戻る

Q (Description VN):
・Ô tìm kiếm lọc theo tên cơ sở
・Placeholder:「施設名で検索」
・Tự động lọc bảng sau 300ms kể từ lần nhập cuối (debounce, không cần Enter)
・Kết quả 0 item:「該当する施設がありません」
・Nút xoá (×): xoá nội dung, hiển thị lại toàn bộ
```

---

**Bảng tóm tắt trọng tâm theo type:**

| Type | Bắt buộc có trong P/Q | Thường bỏ sót |
|---|---|---|
| Button / Hyperlink | Điều kiện active · hành vi mọi nhánh · đích (màn/toast/error) | Nhánh API lỗi (5xx) |
| Textbox / Textarea | Placeholder · maxlength enforcement · mọi validation rule | Nhánh ký tự không hợp lệ |
| Dropdown | Nguồn dữ liệu · option mặc định · hành vi khi chọn | Trường hợp API load danh sách lỗi |
| Checkbox | Trạng thái mặc định · hành vi check/uncheck | Điều kiện enable nút sau checkbox |
| Radio | Danh sách option · mặc định · hành vi đổi chọn | State persistence khi quay lại |
| Table | Tên cột theo thứ tự · sort mặc định · pagination · 0 item | Điều kiện enable từng action nút |
| Label | Nguồn data (API field) · format · fallback khi không có data | Fallback / loading state |
| Tab | Danh sách tab · tab mặc định · nội dung mỗi tab · state | URL sync |
| DatePicker | Format · phạm vi chọn · mặc định · validation | Range check phía API |
| Image/File | Định dạng · dung lượng · preview · khi nào gửi server | Validation trùng lặp file |
| Pagination | Items/trang · disable Prev/Next · hành vi chuyển trang | Scroll-to-top |
| SearchBox | Trigger (debounce/Enter) · 0 result · clear | Debounce timing |

---

### 2.8 Style chuẩn — định nghĩa TƯỜNG MINH, không copy hàng xóm

> ⛔ **Tuyệt đối không lấy style bằng cách copy từ row liền trước.** Khi master workbook sạch (chưa có row dữ liệu nào), cách đó rơi về copy từ **header** — data row thành chữ trắng nền xanh, hoặc mất hết đường kẻ. Đây là lỗi đã xảy ra thật.
>
> Dùng module `.claude/skills/system-analyst/scripts/bd_styles.py`.

| Loại hàng | Fill | Font | Border | Align | Dùng ở |
|---|---|---|---|---|---|
| **Header** `bd_styles.header()` | `FFDAEEF3` xanh nhạt | Arial, đen, **bold** | thin, 4 cạnh | center / center, wrap | `Common mesage` r3 · `Screen Error message` r3 · header bảng item · header bảng ERROR SCENARIOS |
| **Title** `bd_styles.title()` | `FF1F4E78` xanh đậm | Arial, **trắng**, bold | thin, 4 cạnh | center / center, wrap | `Screen Index` r5 — **chỉ hàng title này**, data row bên dưới KHÔNG dùng |
| **Data** `bd_styles.data()` | `FFFFFFFF` trắng | Arial 11, đen, thường | thin, 4 cạnh | left / center, wrap | Mọi data row của mọi sheet |
| **Data — cột mã** `data(code=True)` | `FFFFFFFF` | Arial 11, `FF1F5C1F` xanh lá, **bold** | thin, 4 cạnh | left / center | Cột `Message Code`, `Ref Code`, `Screen ID` |
| **Data — cột số/enum** `data(center=True)` | `FFFFFFFF` | Arial 11, đen | thin, 4 cạnh | **center** / center | `#`, `type`, `status`, `required`, `maxlength` |
| **Banner** `bd_styles.banner()` | `FFF2F2F2` xám nhạt | Arial, đen, bold | thin, 4 cạnh | left / center | Banner phân nhóm trong `Screen Error message` |
| **Title ERROR** `bd_styles.err_title()` | `FFFCE4E4` hồng nhạt | Arial, `FFC00000` đỏ, bold | thin, 4 cạnh | left / center | Title bảng ERROR SCENARIOS trong screen sheet |

**Quy tắc bắt buộc:**
- Mọi data row **phải có đủ 4 cạnh border**. Thiếu border = gate check 14 FAIL
- Data row **không được mang fill của header** (`FFDAEEF3` / `FF1F4E78`) = gate check 14 FAIL
- Font toàn workbook là **Arial**, không đổi sang font khác

---

### 2.9 Bảng ERROR SCENARIOS — đặt DƯỚI bảng item

> Bảng item (`H9:R…`) chỉ trỏ tới Message Code trong cột `P`/`Q`. Người đọc phải mở sheet `Screen Error message` mới biết lỗi đó hiển thị ra sao và xử lý thế nào. **Bảng này đưa thông tin đó về ngay trong screen sheet.**

**Vị trí:** cách dòng item cuối **1 row trống**, rồi bắt đầu. Vẫn nằm trong cột `H`→`R`.

| Hàng | Nội dung |
|---|---|
| Title (merged `H:R`) | `⚠ ERROR SCENARIOS — <Screen ID>` · style `err_title` |
| Header | 7 cột dưới · style `header` |
| Data | 1 row / 1 error · style `data` |

**7 cột (dùng merge để khớp độ rộng cột có sẵn) + cột `S` Nguồn ở kit này:**

| Cột | Nội dung | Nguồn |
|---|---|---|
| `H` | `#` | BA tự sinh |
| `I` | Item / vị trí phát sinh | `SPEC ## Screen Details` — item gây ra lỗi |
| `J` | Nhóm (Category) | 4 enum: `🔴 Validation` · `🟡 Business` · `🔵 System` · `🟢 Environment` |
| `K:L` merged | Hiển thị | `SPEC` cột `Hiển thị` — Toast · Modal · Banner · Full screen · Inline · Empty state |
| `M:O` merged | Message Code | Khớp code trong `Screen Error message` / `Common mesage` |
| `P` | Message hiển thị (VN) | `SPEC` cột `Message` — **nguyên văn** |
| `Q:R` merged | **Xử lý tiếp theo** | `SPEC` → hành vi sau lỗi: màn đích, retry, chặn submit… Không rõ → `Cần xác nhận — Q-xxx` |
| `S` | **Nguồn** *(chỉ kit system-to-doc)* | code-ref (validation / i18n message) hoặc `EV-xxxx (screenshot) · network.json / console.json` (lỗi thấy khi quét web). Báo động giả của công cụ quét (`noise`) không vào bảng |

**Rule:**
- Số row bảng này **phải bằng** số error của màn đó trong `Screen Error message` — gate check 15 kiểm
- Màn không có Non-Happy Case nào → **không tạo bảng**, không tạo title rỗng
- Cột `Xử lý tiếp theo` là lý do bảng này tồn tại. Để trống = mất giá trị của cả bảng

---

## 3. Sheet `Common mesage`

- Title: `A1:I1` (merged) = `【User】— Error Message / Validation Definition`
- **Header = row 3**, data từ row 4

| Cột | Header |
|---|---|
| `A` | `Ref Code 共通コード` |
| `B` | `Item Name (JP) 項目名（日本語）` |
| `C` | `Item Name (VN) Tên mục (VN)` |
| `D` | `Category カテゴリー` |
| `E` | `Trigger / Check Type チェック種別` |
| `F` | `Error Message (JP) エラーメッセージ（日本語）` |
| `G` | `Error Message (VN) Thông báo lỗi (Tiếng Việt)` |
| `H` | `Applicable Screens 適用画面` |
| `I` | `Remarks 備考` |

**Convention Ref Code:** `COMMON_<NHÓM>_<3 số>` — VD `COMMON_SYS_001`, `COMMON_ENV_001`.

**Category enum (giữ nguyên cả emoji):** `🔴 Validation` · `🟡 Business` · `🔵 System` · `🟢 Environment`

---

## 4. Sheet `Screen Error message`

- Title `A1`, **header = row 3**, data từ row 4
- **Có banner phân nhóm** dạng row merged `A<n>:J<n>` — VD `A4:J4` = `🔴 Validation / バリデーション — Login`. Mỗi Screen ID có 1+ banner theo category. Các banner hiện có ở row: 4, 17, 29, 102, 112, 131, 147, 184.

| Cột | Header |
|---|---|
| `A` | `Message Code` |
| `B` | `Screen ID` |
| `C` | `項目名 Item name (JP)` |
| `D` | `項目名 Item name (VN)` |
| `E` | `カテゴリー Category` |
| `F` | `User Action (JP) ユーザー操作` |
| `G` | `User Action (VN) Hành vi người dùng` |
| `H` | `Error Message (JP)` |
| `I` | `Error Message (VN)` |
| `J` | `備考 Remarks` |

**Ví dụ 1 block đã điền (trích từ catalog mẫu trước khi dọn):**

Banner `A<n>:J<n>` (merged): `🔴 Validation / バリデーション — Login`

| Cột | Giá trị |
|---|---|
| `A` Message Code | `E_L_001` |
| `B` Screen ID | `Login` |
| `C` Item name JP | `メールアドレス` |
| `D` Item name VN | `Địa chỉ email` |
| `E` Category | `🔴 Validation\nバリデーション` |
| `F` User Action JP | `メールアドレス入力欄を空欄のまま「続行」ボタンを押下する` |
| `G` User Action VN | `Để trống ô nhập email rồi nhấn button「続行」` |
| `H` Error Message JP | `メールアドレスを入力してください。` |
| `I` Error Message VN | `Vui lòng nhập địa chỉ email.` |
| `J` Remarks | `必須チェック` |

> Cột `F`/`G` phải mô tả **thao tác cụ thể của người dùng** dẫn tới lỗi, không phải tên lỗi. "Để trống ô email rồi nhấn 続行" đúng; "Lỗi validation email" sai — QC không dựng được test case từ nó.

**Convention Message Code (suy từ dữ liệu thật của màn Login):**

| Nhóm | Pattern | Ví dụ |
|---|---|---|
| Validation / Business | `E_<VIẾT TẮT MÀN>_<3 số>` | `E_L_001` … `E_L_008` |
| System | `E_<MÀN>_S_<3 số>` | `E_L_S_001` |
| Environment | `E_<MÀN>_E_<3 số>` | `E_L_E_001` |

→ Khi thêm màn mới, **hỏi BRSE viết tắt của màn** trước khi tự đặt. Không tự suy từ tên tiếng Anh.

---

## 5. Sheet `Screen Index`

- `A1:K1` title (kit này đã bỏ cột `Status` → template `A1:L1` thu còn `A1:K1`). Metadata: `A2`=`Master Version`/`B2` · `D2`=`Template Sheet`/`E2` · `G2`=`Last Standardized`/`H2` · `A3`=`Master Status`/`B3` · `D3`=`Runtime Rule`/`E3` · `G3`=`Maintained By`/`H3`
- **Header = row 5**, data từ row 6

| Cột | Header | Nguồn giá trị |
|---|---|---|
| `A` | `No` | tăng dần |
| `B` | `Screen ID` | = `F1` của working sheet · **hyperlink tới sheet** |
| `C` | `Flow ID` | = `F2` |
| `D` | `Screen Name` | = `B1` = tên màn (không mã / route — check 24) |
| `E` | `Sheet Name` | tên tab thật (= tên màn) |
| `F` | `Sheet Type` | `WORKING_SCREEN` |
| `G` | `Version` | = `F3` |
| `H` | `UI Source` | `Embedded UI images` · **`NO IMAGE — Giai đoạn 1 (chưa chạy Playwright)`** · `NO IMAGE — <lý do>` |
| `I` | `Source Flow Version` | = `F5` |
| `J` | `Last Updated` | ngày ghi |
| `K` | `Notes` | ghi chú / lý do thiếu ảnh |

> Cột `Status` (cũ `H`) **đã bỏ** ở kit system-to-doc (feedback: không dùng DRAFT). Gate tìm cột theo tên header nên đọc được cả workbook cũ.

> **Screen Index là single source of truth để resolve sheet theo Screen ID.** Mọi working sheet mới **bắt buộc** có 1 row ở đây. Thiếu row → Quality Gate O4 FAIL.

---

## 6. Sheet `Change History`

- `A1:P1` title, `A2:P2` mô tả, **header = row 5**, data từ row 6 (`CHG-0001` là row seed sẵn có)

| Cột | Header |
|---|---|
| `A` | `Change ID` (`CHG-XXXX`, tăng dần) |
| `B` | `Changed Date` |
| `C` | `Changed By` |
| `D` | `Change Type` (`CREATE_SCREEN` · `UPDATE_SCREEN` · `UPDATE_CATALOG` · `MASTER_STANDARDIZATION`) |
| `E` | `Flow ID` |
| `F` | `Screen ID` |
| `G` | `Sheet Name` |
| `H` | `Changed Scope` |
| `I` | `Change Summary` |
| `J` | `Source / Request` |
| `K` | `Previous Version` |
| `L` | `New Version` |
| `M` | `Approval Status` |
| `N` | `Approved By` |
| `O` | `Approved Date` |
| `P` | `Remarks` |

Mỗi lần create/change **PHẢI append đúng 1 row**. Không gộp nhiều thay đổi vào 1 row, không sửa row cũ.
