---
name: jp_validation
description: Bộ validate chuẩn cho hệ thống Nhật — lớp ký tự (全角/半角, kana, kanji...), độ dài đa byte, khoảng trắng, dán, tự chuyển đổi. Luôn áp cho field nhập liệu khi Locale = JP, không phụ thuộc spec có nhắc hay không. Dùng trong /gen-tcs cùng component_checklist.
---

# JP Validation

## Cách dùng

Skill này **không dùng độc lập** — `/gen-tcs` đọc khi `Locale = JP`, áp **lớp bổ sung** lên TC của field nhập liệu (Textbox, Textarea, Password, field số/ngày/tiền) cùng với `component_checklist` (Section A) và Bảng Field-Level Validation.

**Khi nào áp dụng:** `Locale: JP` trong `CLAUDE.md`, hoặc `Locale: JP` trong Summary của `analysis.md` (user xác nhận ở checkpoint Summary). **Luôn áp**, không cần spec nhắc tới 全角/半角.

**Quy trình cho mỗi field:**
1. Xác định **loại field** (氏名, フリガナ, 電話番号, ID, password...).
2. Xác định **lớp ký tự được phép**:
   - Spec/AC có ghi → dùng đúng theo spec.
   - Spec im lặng → dùng **bảng mặc định theo loại field** bên dưới, TC gắn tag `[ASSUMED]`. Không hỏi Q&A, QC rà ở bước review TC.
3. Sinh TC theo **Bộ khung TC cho mỗi field** bên dưới. Áp Pattern 4 (EP + BVA) của `rbt_manual_testing` cho độ dài.
4. **Message lỗi**: lấy đúng text trong spec. Spec chưa có text → ghi `Hiển thị error msg` kèm `(text theo spec)`, không bịa nội dung message.

---

## Lớp ký tự và Test Data mẫu

Mỗi dòng Test Data phải là **chuỗi thật** (không ghi "nhập kanji"). Chọn chuỗi đủ dài để **thỏa min length của field** — nếu không, lỗi độ dài sẽ che lỗi ký tự và không biết lỗi do nguyên nhân nào.

| Lớp | Test Data mẫu |
|---|---|
| 半角英字 | `abcXYZ` |
| 半角数字 | `0123456789` |
| 半角記号 | `-_@.!#$` |
| 全角英数字 | `ＡＢＣｘｙｚ１２３` |
| 全角記号 | `！？＠＿－、。` |
| 半角カナ | `ｱｲｳｴｵｶﾞﾊﾟ` (ガ, パ gồm 2 mã ký tự) |
| 全角カタカナ | `カタカナガパ` |
| ひらがな | `ひらがなぐぱ` |
| 漢字 (thường dùng) | `漢字山田太郎` |
| 漢字 (dị thể, ngoài JIS cơ bản) | `髙橋`, `﨑`, `𠮷野家` (𠮷 là surrogate pair) |
| Ký tự phụ thuộc môi trường | `①㈱㌔Ⅲ` |
| Gạch / trường âm dễ nhầm | `ー`, `－` (全角), `-` (半角), `‐` (hyphen U+2010) |
| Dấu sóng dễ nhầm | `〜` (U+301C), `～` (U+FF5E), `~` |
| Dấu đục rời | `か` + `゛` (khác `が` một ký tự) |
| Khoảng trắng 半角 | ` ` (U+0020) |
| Khoảng trắng 全角 | `　` (U+3000) |
| Emoji | `😀` |
| Unicode ngoài Nhật (tiếng Việt có dấu) | `tiếng việt` |
| Ký tự điều khiển khi dán | xuống dòng, tab (copy từ Excel/Word) |

---

## Bảng mặc định theo loại field (khi spec im lặng)

Tag `[ASSUMED]` trên TC. QC chỉnh bảng này nếu dự án khác.

| Loại field | Lớp được phép | Lớp bị từ chối |
|---|---|---|
| 氏名 (tên) | 全角 漢字, ひらがな, カタカナ | 半角カナ, 全角英数字 (nếu tên không cho), emoji, ký tự điều khiển |
| フリガナ | 全角カタカナ (nếu có tự đổi ひらがな → カタカナ thì kiểm tra thêm) | 半角カナ, 漢字, 半角英数 |
| 電話番号 | 半角数字 và `-` | 全角数字 (hoặc tự chuyển sang 半角, theo spec), chữ, ký tự khác |
| 郵便番号 | 半角数字 và `-` | 全角数字, `－` `ー`, chữ |
| メールアドレス | 半角英数字 và ký tự đặc biệt chuẩn | `＠` 全角, 全角英数字, khoảng trắng, kana, kanji |
| 住所 | 全角 漢字・かな, 半角/全角 số nhà, gạch | emoji, ký tự điều khiển |
| ID, password | 半角英数字 và ký tự đặc biệt theo spec | 全角 mọi loại, kana, kanji, ký tự ngoài tập cho phép |
| Field số, tiền, ngày | 半角数字 (theo spec cho dấu `,` `.` `¥`) | 全角数字 (hoặc tự chuyển, theo spec), chữ |
| Field text tự do | Theo spec; không có → mọi ký tự hiển thị được | Ký tự điều khiển, emoji nếu hệ thống không hỗ trợ |

Field không có trong bảng: dùng lớp gần nhất, tag `[ASSUMED]`.

---

## Bộ khung TC cho mỗi field text

Mỗi field **TC riêng** (không gộp giữa các field). Trong một field, gộp theo kết quả bằng nhiều dòng Test Data. Tối đa khoảng 7 TC cho một field text:

| # | TC | Dòng Test Data | Ghi chú |
|---|---|---|---|
| 1 | **Bắt buộc nhập** (nếu field bắt buộc) | Trống; chỉ 半角 space; chỉ 全角 space | Cùng message lỗi → 1 TC |
| 2 | **Chấp nhận các lớp được phép** | Mỗi lớp được phép một dòng | Expected: hiển thị đúng dữ liệu đã nhập, không báo lỗi |
| 3 | **Từ chối các lớp không được phép** | Mỗi lớp bị từ chối một dòng; chuỗi đủ dài để thỏa min length | Expected: error msg theo spec. Khác message giữa các lớp → tách TC |
| 4 | **Độ dài** (Pattern 4) | min−1, max+1 (lỗi); min, giữa, max (chấp nhận); thêm dòng 全角/đa byte ở max và max+1 nếu field cho phép | Nhận ký tự đa byte: bắt lỗi đếm byte thay vì ký tự |
| 5 | **Khoảng trắng đầu/cuối và giữa** | ` abc`, `abc `, `　abc`, `ab c` | Expected theo lớp được phép (space không thuộc tập → lỗi) hoặc trim, theo spec |
| 6 | **Dán (copy/paste)** | Dán từ ô khác trong app; dán chuỗi có xuống dòng/tab từ Excel | Chuỗi dán xử lý giống gõ tay |
| 7 | **Tự chuyển đổi** (chỉ khi spec/mặc định có) | `ｱｲｳ` → `アイウ`, `１２３` → `123`, `あいう` → `アイウ` | Có tự chuyển hay báo lỗi, đúng tại thời điểm nào (khi nhập/khi blur/khi submit) |

**Áp một lần cho cả module (không lặp theo field):** thời điểm validate khi dùng IME (lỗi không hiện khi đang gõ chưa xác nhận 変換, hiện đúng lúc blur hoặc 確定). Đặt trong nhóm `Platform – [Web/Mobile]`.

**Field password** thêm: ký tự bị che, icon hiện/ẩn, copy/paste khi đang che, theo `component_checklist` (Mask field). Lớp ký tự password thường chặt hơn 氏名, dùng bảng mặc định "ID, password".

---

## Ví dụ chuẩn: Login ID (8-32 ký tự, 半角英数字 và `-` `_` `@`)

Mẫu tham khảo từ QC Login (`ONSEN`), đã sửa các lỗi: Test Scenario khớp Expected, Test Data là chuỗi thật, chuỗi test ký tự đủ dài để thỏa min length, độ dài gộp theo kết quả.

| Function Name | Test Scenario | Steps | Test Data | Expected Results |
|---|---|---|---|---|
| ログインID Textbox | Check báo lỗi khi để trống hoặc chỉ nhập khoảng trắng | 1. Nhập giá trị theo Test Data vào ログインID<br>2. Bỏ focus | Dòng 1: (trống)<br>Dòng 2: 半角 space ×8<br>Dòng 3: 全角 space ×8 | Hiển thị error msg: ログインIDが必須項目です。 |
| ログインID Textbox | Check chấp nhận ký tự được phép | 1. Nhập giá trị theo Test Data<br>2. Bỏ focus | Dòng 1: `abcEFghi`<br>Dòng 2: `12345678`<br>Dòng 3: `aB_@-678` | Hiển thị đúng dữ liệu đã nhập; không báo lỗi |
| ログインID Textbox | Check báo lỗi khi nhập ký tự không được phép | 1. Nhập giá trị theo Test Data<br>2. Bỏ focus | Dòng 1: `ひらひらひらひらひら`<br>Dòng 2: `カタカタカタカタ`<br>Dòng 3: `漢字漢字漢字漢字`<br>Dòng 4: `ｱｲｳｴｵｶｷｸｹｺ`<br>Dòng 5: `ＡＢＣＤＥＦＧＨ`<br>Dòng 6: `tiếng việt`<br>Dòng 7: `-^09ư-^09ư` | Hiển thị error msg: 入力に誤りがあります。半角英字・数字および「-」「_」「@」のみ使用できます。 |
| ログインID Textbox | Check báo lỗi khi độ dài ngoài khoảng 8 đến 32 ký tự | 1. Nhập giá trị theo Test Data<br>2. Bỏ focus | Dòng 1: `abc123-` (7)<br>Dòng 2: `abcdefghij1234567890abcdefghij123` (33) | Hiển thị error msg: 入力に誤りがあります。〇〇桁〜〇〇桁まで入力してください。 (text số theo spec) |
| ログインID Textbox | Check chấp nhận độ dài trong khoảng 8 đến 32 ký tự | 1. Nhập giá trị theo Test Data<br>2. Bỏ focus | Dòng 1: `abc123--` (8)<br>Dòng 2: `abcdefghij1234567890` (20)<br>Dòng 3: `abcdefghij1234567890abcdefghij12` (32) | Hiển thị đúng dữ liệu đã nhập; không báo lỗi |
| ログインID Textbox | Check xử lý khoảng trắng ở đầu, cuối và giữa chuỗi | 1. Nhập giá trị theo Test Data<br>2. Bỏ focus | Dòng 1: ` abcdefgh`<br>Dòng 2: `abcdefgh `<br>Dòng 3: `　abcdefgh`<br>Dòng 4: `abcd efgh` | Hiển thị error msg ký tự không hợp lệ (space không thuộc tập cho phép) `[ASSUMED]` |
| ログインID Textbox | Check dán nội dung từ ô khác | 1. Copy `abcEFghi` từ ô khác<br>2. Dán vào ログインID<br>3. Dán chuỗi nhiều dòng `abcd` + xuống dòng + `efgh` từ Excel | Dòng 1: `abcEFghi`<br>Dòng 2: `abcd⏎efgh` | Dòng 1 dán được và hiển thị đúng<br>Dòng 2 xử lý như nhập ký tự không được phép |

Với Password dùng cùng khung (min 10, max 64); thêm Eye icon và copy/paste khi che theo `component_checklist`.

---

## Phạm vi chưa có (để sau)

- Xuất/nhập CSV và mã hóa (Shift_JIS, UTF-8 BOM, 文字化け, ký tự ngoài Shift_JIS).
- Tìm kiếm: coi 全角 và 半角, ひらがな và カタカナ là như nhau không; thứ tự sắp xếp 50 âm.
- 和暦 (令和) cho field ngày.
