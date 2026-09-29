# Ba Agent — Basic Design Workbook Structure (map thật của master workbook)

> **Nguồn:** đọc trực tiếp từ `sample/sample_basic_design.xlsx` ngày 23/09/2026 bằng `openpyxl`.
> Mọi con số dòng/cột dưới đây là **thật**, không phải mô tả từ tài liệu kiến trúc. Khi master workbook của dự án khác file mẫu, BA **PHẢI đọc lại workbook thật** và cập nhật mapping trước khi ghi — KHÔNG được ghi theo trí nhớ file mẫu.

---

## 1. Sheet inventory (5 sheet)

| # | Sheet | Vai trò | Mutation rule |
|---|---|---|---|
| 1 | `Common mesage` | Catalog message dùng chung cho nhiều màn | **Append-only** + update đúng row. Reuse trước khi tạo mới |
| 2 | `Screen Error message` | Catalog error theo từng màn | **Append** theo block Screen ID + update đúng row |
| 3 | `Sample` | **Template chuẩn** cho 1 Screen Basic Design | ⛔ **IMMUTABLE** — chỉ duplicate. Không điền, không đổi tên, không xóa |
| 4 | `Screen Index` | Bảng tra Screen ID → sheet name + status | Append 1 row / 1 working sheet mới; update status khi đổi |
| 5 | `Change History` | Log mọi thay đổi | **Append-only**. Không sửa, không xóa row cũ |

> ⚠️ **Khác với tài liệu kiến trúc v3.0:** file thật **không có** sheet `Error message` riêng và **không có sheet hidden nào**. Chỉ có `Common mesage` (typo có chủ ý — giữ nguyên) và `Screen Error message`. Nếu tài liệu và workbook mâu thuẫn → **workbook thắng**.

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
| `A4` | `概要` | `B4:D4` (merged) | `■目的` / `■アクセス方法` — block 2 mục |
| `A5` | `Logic chung` | `B5:D5` (merged) | `[GENERAL LOGIC]` |
| `A6` | `Cách access` | `B6:D6` (merged) | `[ACCESS METHOD]` |

**Cột metadata phải (E/F) — BẮT BUỘC điền đủ 6 dòng:**

| Cell | Key | Giá trị ở `Sample` | Giá trị phải điền ở working sheet |
|---|---|---|---|
| `E1`/`F1` | `Screen ID` | `TEMPLATE` | Screen Code từ SPEC `## Screens` (VD `AU_AUTH_001`) |
| `E2`/`F2` | `Flow ID` | `TEMPLATE` | Flow ID từ Output 1/2 |
| `E3`/`F3` | `Version` | `1.1` | `1` cho sheet mới, tăng dần mỗi lần change |
| `E4`/`F4` | `Status` | `TEMPLATE` | `DRAFT` → `WAITING APPROVAL` → `APPROVED` |
| `E5`/`F5` | `Source Flow Version` | `N/A` | Version của Output 2 đã approve (VD `v2_23092026`) |
| `E6`/`F6` | `Sheet Type` | `TEMPLATE_SCREEN` | **`WORKING_SCREEN`** — đổi ngay sau khi duplicate |

> ⛔ Nếu sau khi duplicate mà `F6` vẫn là `TEMPLATE_SCREEN` → Quality Gate O5 **FAIL**. Đây là dấu hiệu agent quên neutralize sheet.

### 2.2 Banner cảnh báo

`A8:F8` (merged) = `AGENT TEMPLATE — Do not edit directly. Duplicate this sheet to create a new Screen Basic Design.`

→ Trên working sheet: **xóa nội dung banner này**, vùng `A9` trở xuống dùng để chèn ảnh UI.

### 2.3 Vùng ảnh UI (cột A–F, từ row 9)

| | `Sample` | `Login_Sample` (reference) |
|---|---|---|
| Vị trí ảnh | trống (chỉ có banner ở `A8:F8`) | 2 ảnh anchor tại `A9` và `A14` |
| Merged cho ảnh | — | `A10:F12`, `A14:F16` |

Quy ước: **ảnh UI nằm cột A–F bên trái, bảng item nằm cột H–R bên phải, cùng dòng**.

**Kích thước vùng ảnh (đo thật):**

| | Giá trị |
|---|---|
| Tổng column width `A`→`F` | 122 ký tự ≈ **854 px** |
| Chiều rộng ảnh tối đa cho phép | **840 px** (chừa lề 14 px) |
| Chiều cao ảnh tối đa | **900 px** |

> ⚠️ **Lỗi có thật trong sheet mẫu gốc:** 2 ảnh của `Login_Sample` đều là `1521 px` chèn vào vùng 854 px → **tràn ~670 px sang cột H–R, đè lên bảng item**. Gate check 13 bắt lỗi này. Quy tắc resize đầy đủ: `output-5-basic-design.md` §1.1d.

### 2.4 Bảng item (cột H–R)

**Header ở `Sample` = row 8. Ở `Login_Sample` = row 9** (lệch 1 dòng vì Login_Sample có spacer row 8 cao 6.0pt).

| Cột | Header | Ghi chú điền |
|---|---|---|
| `H` | `#` | Số thứ tự |
| `I` | `項目名 Item name（JP)` | Tên item tiếng Nhật |
| `J` | `項目名 Item name（VN)` | Tên item tiếng Việt |
| `K` | `種類 (type)` | `Label` · `Textbox` · `Button` · `Hyperlink` · `Icon` · `Dropdown` · `Checkbox` … |
| `L` | `ステータス (status)` | `Enable` · `Disable` · `ー` |
| `M` | `必須 (required)` | `Yes` · `ー` |
| `N` | `最大限 (maxlength)` | số, khoảng (`8〜20`), hoặc `ー` |
| `O` | `初期値 (default)` | giá trị mặc định hoặc `ー` |
| `P` | `記述（日本語）` | Mô tả + validation + hành vi, bullet `・`, sub-list đánh số |
| `Q` | `Description (VN)` | Bản tiếng Việt của `P` — **phải khớp 1-1 về số bullet và số nhánh validation** |
| `R` | `Comment` | Câu hỏi còn treo cho BRSE |

**Số dòng đã format sẵn:** `Sample` có **11 dòng item (row 9 → row 19)** với border + row height đặt sẵn.
Nếu screen có > 11 item → **copy format của 1 row chuẩn xuống**, không được chèn row trần không border.

**Quy ước viết `P` / `Q`:** dùng `・` mở đầu mỗi bullet; nhánh validation đánh số `1.` `2.` `3.`; mọi nhánh lỗi **phải trỏ tới Message Code có thật** trong `Screen Error message` (VD `→ E_L_001`). Trỏ tới code không tồn tại → Quality Gate O5 FAIL.

### 2.5 Layout phải giữ nguyên khi duplicate

- Column widths: `A=9.7` `B=21.2` `C=17.8` `D=40.5` `E=19.0` `F=22.0` `G=9.7` `I=32.2` `J=22.0` `K=14.0` `L=12.5` `N=14.3` `O=12.5` `P=55.0` `R=36.5` `S=8.7`
- Row heights vùng item: row 9=54.8, 10=74.2, 11=204.0, 12=170.2, 13=125.2, 14=70.5, 15=85.5, 16=171.8, 17=83.2, 18=80.2, 19=261.8
- Page setup: **orientation = landscape**
- Merged ranges gốc: `A8:F8`, `B4:D4`, `B5:D5`, `B6:D6`

---

### 2.6 Tám nhóm nội dung bắt buộc → ánh xạ vào cell nào

> Một screen sheet phải chứa đủ 7 nhóm nội dung dưới. **Template thật chỉ có sẵn vùng riêng cho 4 nhóm đầu** — 3 nhóm cuối phải gửi vào cell free-text đang có.
>
> ⛔ **KHÔNG được thêm cột / thêm sheet / đổi layout của template công ty** để "cho đủ chỗ". Template là tài sản dùng chung, đổi nó ảnh hưởng mọi dự án khác.

| # | Nhóm | Vùng trong sheet | Bắt buộc |
|---|---|---|---|
| 1 | **Metadata** | `B1`/`D1` tên + URL · `B2`/`D2` tác giả + ngày tạo · `B3`/`D3` người sửa + ngày sửa · `F1`–`F6` Screen ID / Flow ID / Version / Status / Source Flow Version / Sheet Type | ✅ |
| 2 | **Overview** | `B4` (merged `B4:D4`) block `■目的` + `■アクセス方法` · `B5` Logic chung · `B6` Cách access | ✅ |
| 3 | **UI reference** | Vùng ảnh `A9+`. **Không có ảnh** → `Screen Index` cột `I` = `NO IMAGE — text only` | ✅ (khai báo bắt buộc, ảnh thì không) |
| 4 | **Items** | Bảng `H9:R19` — 11 dòng có sẵn format, mở rộng bằng cách copy format row chuẩn | ✅ |
| 5 | **Behavior** | **Không có vùng riêng** → viết trong cột `P` (JP) / `Q` (VN) của chính item gây ra hành vi: action, state, validation, transition, error reference | ✅ |
| 6 | **Traceability** | **Không có vùng riêng** → thêm block thứ ba vào `B4`:<br>`■トレーサビリティ / Traceability`<br>`FR No. <n> · RQ-<id> · SPEC ## Screen Details <Screen Code>`<br>Cấp flow đã có sẵn ở `F2` (Flow ID) + `F5` (Source Flow Version) | ✅ |
| 7 | **Known gaps** | **Không có vùng riêng** → cấp item: cột `R` (Comment), tiền tố `⚠`<br>cấp screen: `Screen Index` cột `L` (Notes) | ✅ khi có gap |
| 8 | **Error scenarios** | Bảng riêng **dưới bảng item** — xem §2.9 | ✅ khi màn có Non-Happy Case |

**Quy ước viết nhóm 5 Behavior trong `P`/`Q`** (theo đúng `Login_Sample`):

```
・<mô tả item>
・初期表示 / Trạng thái ban đầu: <...>
・押下時の挙動 / Hành vi khi nhấn:
  1. <nhánh 1> → <đích hoặc Message Code>
  2. <nhánh 2> → <đích hoặc Message Code>
```

**Quy ước nhóm 7 Known gaps:** mọi ô không có evidence **để `UNKNOWN`, không để trống và không tự điền**, kèm 1 dòng `⚠ <thứ còn thiếu> — Need Confirm` ở cột `R`. Để trống lặng lẽ = người đọc tưởng "không áp dụng"; tự điền = biến giả định thành spec.

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

### 2.8 Style chuẩn — định nghĩa TƯỜNG MINH, không copy hàng xóm

> ⛔ **Tuyệt đối không lấy style bằng cách copy từ row liền trước.** Khi master workbook sạch (chưa có row dữ liệu nào), cách đó rơi về copy từ **header** — data row thành chữ trắng nền xanh, hoặc mất hết đường kẻ. Đây là lỗi đã xảy ra thật.
>
> Dùng module `.claude/skills/business-analyst/scripts/bd_styles.py`.

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

**7 cột (dùng merge để khớp độ rộng cột có sẵn):**

| Cột | Nội dung | Nguồn |
|---|---|---|
| `H` | `#` | BA tự sinh |
| `I` | Item / vị trí phát sinh | `SPEC ## Screen Details` — item gây ra lỗi |
| `J` | Nhóm (Category) | 4 enum: `🔴 Validation` · `🟡 Business` · `🔵 System` · `🟢 Environment` |
| `K:L` merged | Hiển thị | `SPEC` cột `Hiển thị` — Toast · Modal · Banner · Full screen · Inline · Empty state |
| `M:O` merged | Message Code | Khớp code trong `Screen Error message` / `Common mesage` |
| `P` | Message hiển thị (VN) | `SPEC` cột `Message` — **nguyên văn** |
| `Q:R` merged | **Xử lý tiếp theo** | `SPEC` → hành vi sau lỗi: màn đích, retry, chặn submit… Không rõ → `UNKNOWN — Need Confirm` |

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

- `A1:L1` title. Metadata: `A2`=`Master Version`/`B2` · `D2`=`Template Sheet`/`E2` · `G2`=`Last Standardized`/`H2` · `A3`=`Master Status`/`B3` · `D3`=`Runtime Rule`/`E3` · `G3`=`Maintained By`/`H3`
- **Header = row 5**, data từ row 6

| Cột | Header | Nguồn giá trị |
|---|---|---|
| `A` | `No` | tăng dần |
| `B` | `Screen ID` | = `F1` của working sheet |
| `C` | `Flow ID` | = `F2` |
| `D` | `Screen Name` | = `B1` |
| `E` | `Sheet Name` | tên tab thật |
| `F` | `Sheet Type` | `WORKING_SCREEN` |
| `G` | `Version` | = `F3` |
| `H` | `Status` | = `F4` |
| `I` | `UI Source` | `Output 3 approved` · `Figma <node>` · `Embedded UI images` · **`NO IMAGE — text only`** |
| `J` | `Source Flow Version` | = `F5` |
| `K` | `Last Updated` | ngày ghi |
| `L` | `Notes` | ghi chú / lý do thiếu ảnh |

> **Screen Index là single source of truth để resolve sheet theo Screen ID.** Mọi working sheet mới **bắt buộc** có 1 row ở đây. Thiếu row → Quality Gate O5 FAIL.

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
