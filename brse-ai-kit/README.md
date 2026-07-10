# BRSE AI Kit

Bộ công cụ AI hỗ trợ BrSE tạo tài liệu **Basic Design** nhanh hơn từ màn hình Figma.

---

## Tổng quan

Kit gồm **2 tính năng**:

| # | Tính năng | Mô tả |
|---|-----------|-------|
| 1 | **Figma Plugin** (chính) | Đọc frame Figma → Đánh số UI element → Tạo spec + xuất Excel Basic Design |
| 2 | **Claude Desktop** (phụ) | Từ ảnh/frame đã đánh số → Claude đọc Figma và tạo tài liệu Basic Design đầy đủ |

---

## Tính năng 1 — Figma Plugin (Basic Design Numbering)

### Flow tổng quát

```
Figma Frame
    │
    ▼
[Plugin: Chọn Frame]
    │
    ├─── Chế độ Manual ──► Nhập prompt (vd: "1: 氏名, 2: パスワード")
    │                           │
    └─── Chế độ Auto AI ─► Claude đọc frame, tự đề xuất số
                                │
                          [Preview → Confirm]
                                │
                          [Vẽ badge đỏ + số lên Canvas]
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
          [Tạo spec bằng AI]        [Tạo draft local]
          Claude viết spec           Fallback (không cần API key)
          JP + VN, theo section
                    │
            ┌───────┴───────┐
            ▼               ▼
      Xuất Excel BD     Xuất CSV
      (.xls + ảnh)      (UTF-8 BOM)
```

### Cài đặt Plugin

1. Mở **Figma Desktop** (bắt buộc dùng Figma Desktop, không phải web)
2. Vào `Plugins → Development → Import plugin from manifest...`
3. Trỏ vào file `figma-plugin/manifest.json`
5. Reload plugin sau khi sửa code

![Hướng dẫn setup Figma Plugin](guidelines/Hướng%20dẫn%20setup%20Figma%20Plugin.png)

### Cách sử dụng

#### Chế độ Manual (nhập prompt)

1. Chọn Frame trên canvas Figma
2. Mở plugin → Nhập Anthropic API key
3. Nhập prompt dạng:
   ```
   1: 氏名
   2: パスワード
   3: ログインボタン
   ```
4. Bấm **Phân tích & xem trước** → Kiểm tra preview
5. Bấm **Vẽ số lên canvas**

#### Chế độ Auto AI

1. Chọn Frame → Nhập API key (bắt buộc)
2. Chọn **「Tự động — AI đọc frame và đánh số item」**
3. Bấm **Quét & xem trước (Auto AI)** — Claude tự phân tích frame
4. Tick/bỏ tick từng dòng trong preview
5. Bấm **Vẽ số lên canvas**

#### Tạo spec Basic Design

![Hướng dẫn sử dụng Figma plugin](guidelines/Hướng%20dẫn%20sử%20dụng%20Figma%20plugin.png)

Sau khi đã vẽ số lên canvas:

1. Bấm **「Tạo spec bằng AI」** → Claude viết spec tiếng Nhật + Việt
2. Chỉnh sửa trong modal (項目名, 記述, DB field, …)
3. Bấm **Xuất Excel Basic Design** để ra file `.xls` (ảnh frame + bảng spec)
4. Hoặc bấm **Xuất CSV** nếu chỉ cần dữ liệu thô


---

## Tính năng 2 — Claude Desktop tạo Basic Design

Dùng khi đã có **ảnh màn hình đã đánh số** (từ Plugin hoặc chụp tay) và muốn Claude sinh tài liệu Basic Design đầy đủ.

### Flow

```
Figma (đã đánh số bằng plugin)
    │
    ▼
[Claude Desktop — Tạo Project + Upload Skills]
    │
    ├── Project Instructions: Introductions.md
    └── Project Knowledge: Validation.md
                           Content rule.md
                           Error message.md
                           Format rule.md
                           Master Basic Design Excel
    │
    ▼
[Kết nối Figma Connector trong Claude Desktop]
    │
    ▼
[Dán URL Figma vào chat]
    │
    ▼
[Claude tự động đọc → phân tích → sinh tài liệu]
    │
    ▼
File Basic Design (lưu vào Project Folder)
```

![Hướng dẫn sử dụng Claude tạo BD](guidelines/Hướng%20dẫn%20sửu%20dụng%20claude%20tạo%20BD.png)

### Cài đặt Claude Desktop

#### Bước 1 — Tạo Project Folder

Tạo thư mục trên máy để lưu Basic Design, ví dụ:
```
{Dipro Project}Basic_design/
```

#### Bước 2 — Tạo Project trên Claude Desktop

1. Mở **Claude Desktop** → **New Project**
2. **Add Folder** → chọn thư mục vừa tạo
3. **Create Project**

#### Bước 3 — Cấu hình Instructions

Vào **Project Instructions**, dán nội dung từ file:
- [`Introductions.md`](https://drive.google.com/file/d/16bfYjlGQ1-KnYE2CSw1TyhdJQo7lYaLw/view?usp=drive_link)

#### Bước 4 — Upload bộ Skills

Vào **Project Knowledge**, upload các file:

| File | Mục đích |
|------|----------|
| [`Validation.md`](https://drive.google.com/file/d/1pMZmHQ9VPN6KfRVijygBqm2Kbdc3BUhY/view?usp=drive_link) | Quy tắc validation |
| [`Content rule.md`](https://drive.google.com/file/d/1Pwp-Xo2r78GNYZD8gDu7a73rwYSH89wT/view?usp=drive_link) | Quy tắc nội dung |
| [`Error message.md`](https://drive.google.com/file/d/17w6G3VmBxAv08ZEDgDdfo9c1TeTc9LmA/view?usp=drive_link) | Chuẩn Error Message |
| [`Format rule.md`](https://drive.google.com/file/d/1MltzQeJBRPQcKMOyNXPVaTNeRuU7vuch/view?usp=drive_link) | Định dạng tài liệu |
| [`Master Basic Design Excel`](https://docs.google.com/spreadsheets/d/1F6MMqQusChPndg_vet7V4cbZh9a_7qfi/edit?usp=sharing) | File mẫu BD |

#### Bước 5 — Kết nối Figma Connector

Ở ô chat: nhấn **+** → **Connectors** → **Add Connector** → tìm **Figma** → **Add Figma**

#### Bước 6 — Tạo Basic Design

Dán URL màn hình Figma đã đánh số vào chat:
```
https://www.figma.com/design/xxxxxxxxxxxxxxxx
```

Claude sẽ tự động đọc frame, nhận biết marker số, và sinh tài liệu Basic Design với đầy đủ các phần:

1. Overview
2. Business Overview
3. Screen Overview
4. Layout
5. Item List
6. Input Items
7. Validation
8. Error Message
9. Business Rules
10. Processing Flow
11. Notes

> ⚠️ Chỉ dùng **Claude Desktop**, không phải Claude Web.

---

## Cấu trúc thư mục

```
brse-ai-kit/
├── figma-plugin/               # Figma Plugin source
│   ├── manifest.json           # Cấu hình plugin
│   ├── dist/code.js            # Plugin logic (build output)
│   ├── src/ui.html             # Giao diện plugin
│   ├── README.md               # Hướng dẫn plugin chi tiết
│   ├── AI_WORKFLOW.md          # Sơ đồ flow AI chi tiết
│   └── guidelines/             # Ảnh hướng dẫn setup + sử dụng
├── guidelines/
│   ├── Hướng dẫn sử dụng Claude tạo BasicDesign.md   # Hướng dẫn tính năng 2
│   ├── Hướng dẫn sửu dụng claude tạo BD.png          # Ảnh minh họa
│   ├── Hướng dẫn setup Figma Plugin.png              # Ảnh setup plugin
│   └── Hướng dẫn sử dụng Figma plugin.png           # Ảnh dùng plugin
└── templates/
    ├── WORKFLOW_GUIDE.html                            # Tài liệu workflow tổng quan
    └── 【Project name】Master_Basic_desing_xlsx_V1.0.xlsx  # File mẫu Basic Design
```

---

## Yêu cầu

| Thành phần | Yêu cầu |
|------------|---------|
| Figma | Desktop app (không phải web) |
| Claude | API key từ console.anthropic.com |
| Node.js | Để build plugin (nếu sửa code) |
| Claude Desktop | Cho tính năng 2 (tạo BD từ Claude) |
