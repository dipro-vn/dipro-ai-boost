---
description: Export markdown artifact ra file .xlsx. test-cases.md dùng template thật (Web/App, giữ dropdown); các artifact khác (analysis.md, plan-tcs.md...) mỗi ## section thành 1 sheet, table format chuẩn, <br> thành newline thật. Dùng sau khi review xong artifact.
---

Export file `.md` ra `.xlsx` ready import Google Sheets.

## Cách dùng

```
/export-xlsx <đường dẫn file .md> [web|app]
```

Tham số `web`/`app` **chỉ cần khi export `test-cases.md`** (để chọn đúng template).
Các artifact khác (`analysis.md`, `plan-tcs.md`...) không cần và không dùng tham số này.

Ví dụ:
```
/export-xlsx testing/login/test-cases.md web
/export-xlsx testing/login/test-cases.md app
/export-xlsx testing/login/analysis.md
```

## Thực thi

1. Xác định đường dẫn file `.md` từ input của user (tuyệt đối hoặc tương đối từ root project)
2. Kiểm tra file tồn tại
3. **Nếu file là `test-cases.md` và user chưa chỉ định `web`/`app` trong prompt** → hỏi user: "Xuất theo template Web hay App?" trước khi chạy script. Không đoán.
4. Chạy script:

```bash
# Tự động tìm python3 có openpyxl (ưu tiên venv local, sau đó system)
PYTHON=$(python3 -c "import openpyxl, sys; print(sys.executable)" 2>/dev/null || python3 -c "import sys; print(sys.executable)")

# test-cases.md
$PYTHON .claude/scripts/md_to_xlsx.py <file_path> <web|app>

# artifact khác
$PYTHON .claude/scripts/md_to_xlsx.py <file_path>
```

5. Báo kết quả: đường dẫn file `.xlsx` vừa tạo (cùng thư mục với file `.md` input)

## Output format

### `test-cases.md` (dùng template thật `template/*_Testcase_ForWeb|ForApp_V3.0.xlsx`)

- Load nguyên workbook template (Web hoặc App) làm base — giữ nguyên `Test view point`, dropdown/data validation có sẵn
- Mỗi `##` section **có bảng TC** (cột `ID` + `Test Scenario`) → 1 sheet riêng, clone từ sheet `Screen name` gốc (giữ nguyên dropdown), tên sheet lấy theo heading (bỏ số thứ tự đầu, cắt tối đa 31 ký tự). Sheet evidence tương ứng (`<tên sheet>_evidence`) đi kèm ngay sau mỗi sheet TC
- TC data map vào đúng cột theo **tên header** (không theo thứ tự cột)
- Section **không phải bảng TC** (VD `Test Data Reference`, ghi chú...) → vẫn xuất thành sheet (kiểu generic, giống artifact khác) nhưng **chèn ở cuối workbook**, sau tất cả sheet TC — không đưa vào `Summary`
- `Summary!C4, C5, ...`: tự điền tên từng sheet TC theo đúng thứ tự — formula "TCs plan" có sẵn trong template (`COUNTA`/`INDIRECT` theo tên sheet) tự đếm lại, kể cả khi QC sửa TC thủ công sau này. Hyperlink quick-nav ở `C4` (nếu có) được cập nhật trỏ đúng sheet mới
- Dropdown (Result, Bug type, Bug Roots) và công thức "No." chỉ có sẵn tới dòng 97 (fixed range theo template gốc); `Summary` chỉ hỗ trợ tối đa 14 sheet TC (dòng 4–17) — vượt quá sẽ được báo trong output nhưng không tự mở rộng
- Cột OK/NG/Pending và `Test view point` giữ nguyên để QC tự điền khi thực thi — script không tự tính

### Artifact khác (generic)

- Mỗi `##` / `###` heading → 1 sheet riêng (tên sheet = tên heading, tối đa 31 ký tự)
- Free text (Summary, ghi chú...) → hiển thị phía trên bảng trong cùng sheet, font italic
- Bảng markdown → Excel table: header bold nền `#46BDC6`, freeze row 1, wrap text, border
- Column width tự động, capped 55 ký tự

### Chung

- `<br>` trong cell → newline thật (Alt+Enter style)

## Lưu ý

- File `.xlsx` ghi đè nếu đã tồn tại cùng tên
- Nếu script báo lỗi `ModuleNotFoundError: openpyxl`, chạy: `pip install openpyxl` (hoặc dùng venv: `python3 -m venv .venv && .venv/bin/pip install openpyxl`)
