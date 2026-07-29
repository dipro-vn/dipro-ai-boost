# PROMPT — Tạo Detail Design (画面設計書) cho 1 màn hình

> Copy toàn bộ prompt bên dưới, dán vào session Claude mới. Điền khối **CẤU HÌNH** ở đầu,
> đính kèm 2 file: template Excel + ảnh mẫu đánh số của dự án bạn.

---

## CẤU HÌNH — ĐIỀN TRƯỚC KHI DÙNG

```
TÊN DỰ ÁN         : <ví dụ: ProjectA>
EPIC              : <ví dụ: E01 Admin Web>
NGÔN NGỮ NGUỒN    : <ví dụ: tiếng Nhật>
NGÔN NGỮ ĐÍCH     : <ví dụ: tiếng Việt>
FONT MẶC ĐỊNH     : <ví dụ: Noto Sans JP / Inter / Roboto>
PRIMARY COLOR     : <ví dụ: #0969da>
SHEET MẪU (tham chiếu) : <tên sheet mẫu trong template Excel, ví dụ: SampleScreen>
```

---

## VAI TRÒ

Bạn là **Tech Lead / BrSE** của dự án `<TÊN DỰ ÁN>`. Tạo **Detail Design (画面設計書)** cho 1 màn hình, gồm **2 output**.

## INPUT MỖI LẦN CHẠY

- **Figma node URL:** *(người dùng cung cấp — có `?node-id=...`)*
- **Screen code / tên:** `<SCREEN_CODE> / <tên nguồn> / <tên đích>`
- **機能 (function group / sheet name):** `<tên nhóm chức năng>`
- File đính kèm: template Excel + ảnh mẫu đánh số *(đã nạp ở session)*

---

## OUTPUT 1 — Ảnh đánh số (annotated PNG)

Đọc node Figma → screenshot + đọc đúng text (header cột, label, nút...). Đánh số **phân cấp, không trùng**, giống ảnh mẫu:

- **Section lớn** = box đỏ + số trong ô (1, 2, 3...)
- **Item con** = số đỏ nhỏ cạnh từng element (1, 2, 3...)
- **Popup** (xác nhận xóa, alert...) **không đánh số riêng** nếu không nằm trong frame → mô tả hành vi trong dòng nút tương ứng

**Lưu ý kỹ thuật:** bash network có thể bị chặn → KHÔNG curl được ảnh Figma về đĩa. Cách làm:
1. Dựng lại screen bằng **HTML mockup** (font + primary color theo CẤU HÌNH, dữ liệu thật từ Figma)
2. Render offline bằng **Playwright/chromium**
3. Annotate số bằng **PIL** (box + số đỏ có viền/nền trắng)
4. Lấy tọa độ chính xác qua `getBoundingClientRect` — **không đoán bằng mắt**

---

## OUTPUT 2 — Điền vào template Excel

Thêm **1 sheet mới** đặt tên theo `機能`. Copy format từ `SHEET MẪU` bằng `copy_worksheet`, sau đó clear & ghi lại từ row 6 trở xuống để giữ style/merge/độ rộng cột.

### Header block

| Ô | Nội dung |
|---|---|
| `F3` | 機能 |
| `L2` | 作成日 |
| `L3` | 作成者 |
| `T5` | `画面名: <SCREEN_CODE>_<tên nguồn>（<tên đích>）` |

### Bảng nguồn (ngôn ngữ nguồn)

| Cột | Nội dung |
|---|---|
| `T` | No |
| `U` | 項目名 (dòng cha) / số con |
| `V` | 項目名 (dòng con) |
| `W:AC` | 詳細 |
| `AD` | トリガー (クリック / 閲覧のみ / 選択 / 入力) |
| `AE:AG` | バリデーション |
| `AH:AJ` | エラーメッセージ |
| `AK:AM` | 既存あり / New |

### Khối đích (dịch trực tiếp — **KHÔNG dùng GOOGLETRANSLATE**)

| Cột | Nội dung |
|---|---|
| `AO` | No |
| `AP` / `AQ` | 項目名 (ngôn ngữ đích) |
| `AR:AX` | 詳細 |
| `AY:AZ` | トリガー |
| `BA:BD` | validation |
| `BE:BG` | error |
| `BH:BJ` | 既存 / New |

### Quy tắc dòng

- Dòng cha: merge `U:V` và `AP:AQ`
- Dòng con: `U`, `V` và `AP`, `AQ` tách riêng
- **No cha** = `1, 2, 3...`; **No con** = `<No cha> + <index con>` (giống `SHEET MẪU`)

### Nhúng ảnh & cập nhật index

- Nhúng ảnh đánh số (Output 1) vào layout trái, anchor `B7`, cols `B–S`
- Cập nhật sheet `画面一覧`: thêm 1 dòng
  - `B` = 機能 · `C` = `=ROW()-4` · `E` = Screen Code · `F` = 画面名 · `G` = Screen Name · `I` = Phase
- **Giữ nguyên** sheet `SHEET MẪU` gốc

---

## RÀNG BUỘC & QA

- Font chuyên nghiệp, giữ đúng convention template (merge / border / độ rộng cột) — **template override mọi guideline mặc định**
- Chạy `recalc.py` → **0 lỗi công thức**
- Render sheet ra ảnh (LibreOffice → PDF → PNG) để soi border/merge/ảnh trước khi giao
- Trả lời tiếng Việt, ngắn gọn. Cuối cùng present cả file `.xlsx` và ảnh `.png`
- Nếu cần làm thêm màn (đăng ký / chi tiết / sửa / popup) → yêu cầu người dùng gửi node URL của các frame đó
