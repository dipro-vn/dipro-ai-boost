# Basic Design Numbering — Figma Plugin

Đánh số UI element trên Frame Figma để phục vụ Basic Design (badge đỏ + đường nối).

## Hai chế độ

### 1. Theo mô tả user (Claude / local)

1. Chọn Frame → Lưu API key
2. Nhập prompt (vd. `8.1: 氏名`, `1 クライアント名`)
3. **Phân tích & xem trước** → **Vẽ số lên canvas**

### 2. Tự động — AI đọc frame (Auto Numbering Mode)

1. Chọn Frame → Lưu API key (bắt buộc)
2. Chọn **「Tự động — AI đọc frame và đánh số item」**
3. **Quét & xem trước (Auto AI)** — không cần nhập danh sách thủ công
4. Tick/bỏ tick từng dòng trong preview → **Vẽ số lên canvas**
5. **Tạo spec bằng AI** (hoặc draft local) → chỉnh sửa trong modal → **Download CSV**

### 3. Basic Design Spec + Excel (bổ sung sau đánh số)

1. **Vẽ số lên canvas** (badge phải có trên frame)
2. Bấm **「2. Tạo spec bằng AI」** — Claude viết spec JP + VN, nhóm theo section
3. Chỉnh sửa trong modal (項目名, 記述, DB field, …)
4. **Xuất Excel Basic Design** (`.xls` HTML): ảnh frame có badge bên trái + bảng spec bên phải
5. **Xuất CSV** (UTF-8 BOM) — tùy chọn phụ
6. Không có API key: tick **「Tạo draft local」** để dùng rule fallback

**Hybrid flow:**

```
collectElements()
  → enrichCandidates()      # metadata, table/breadcrumb hints
  → detectTableLikeGroups()
  → preFilterCandidates()   # selectable / contextOnly / ignored
  → Claude chọn nodeId      # chỉ từ selectable
  → preview + confirm
  → drawOverlay()           # tọa độ 100% từ Figma
```

## Cài đặt

1. Figma Desktop → `Plugins → Development → Import plugin from manifest...`
2. API key: https://console.anthropic.com
3. Reload plugin sau khi sửa code

## Cấu trúc

```
├── manifest.json
└── src/
    ├── code.js    # Logic Figma + Auto AI pipeline + Claude
    └── ui.html    # Modal UI
```

## Lưu ý

- Vị trí badge **không** do AI quyết định — luôn tính từ Figma geometry
- Auto mode: bỏ separator, value trong table, text trong input; giữ header/label/button/icon
- Xem `AI_WORKFLOW.md` cho sơ đồ chi tiết
