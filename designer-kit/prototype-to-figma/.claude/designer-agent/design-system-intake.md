# G1 — Design System Intake

> Đọc ở **Bước 0.1**. Mục tiêu: agent chỉ vẽ khi có design system đủ dùng. Không có → DỪNG. Thiếu → xin thêm nguồn (1–5 màn hình / link Figma) để tự phân tích, bổ sung.

---

## 1. Câu DS-1 — Có design system chưa?

```json
{
  "questions": [
    {
      "header": "Design sys",
      "question": "Bạn đã có link / Figma link / file nào quy định design system (màu sắc, font, size, weight, spacing, component…) cho dự án chưa?",
      "multiSelect": true,
      "options": [
        { "label": "Link Figma design system", "description": "Page Foundations / Design Tokens / Component Library — paste link ở ô Other" },
        { "label": "File tài liệu", "description": ".md / .pdf / .docx / .xlsx / ảnh trong input/design-system/ hoặc link artifact / Notion" },
        { "label": "Đã có trong design-system/", "description": "Folder design-system/ của kit đã được dựng từ lần trước" },
        { "label": "Chưa có", "description": "Agent dừng lại — chuẩn bị design system rồi chạy lại" }
      ]
    }
  ]
}
```

- **"Chưa có"** (và không chọn gì khác) → **DỪNG** workflow, in hướng dẫn §4. Không vẽ, không tự dùng màu mặc định.
- Có nguồn → đọc hết nguồn (§2) → chấm checklist (§3).

## 2. Đọc nguồn

| Nguồn | Cách đọc |
|---|---|
| Link Figma | `get_variable_defs` (token màu / chữ / spacing / radius / shadow) · `get_metadata` (page, component) · `get_libraries` + `search_design_system("Button")` (library) · `get_screenshot` |
| File tài liệu | `Read` (md / pdf / ảnh); docx / xlsx dùng skill tương ứng nếu có |
| `design-system/` sẵn có | `Read design-system/README.md` + `tokens.json` (JSON hợp lệ) |

## 3. Checklist — đủ để cấu thành design system

| # | Hạng mục | Tối thiểu cần có |
|---|---|---|
| D1 | Màu thương hiệu / primary | primary + hover/pressed + nền nhạt (subtle); theo từng platform/portal nếu có nhiều theme |
| D2 | Màu nền & chữ | page background · surface · text high / middle / low · divider / border |
| D3 | Màu trạng thái | success · info · warning · error (nền + chữ) |
| D4 | Typography | font family · thang size (≥ 4 bậc) · weight · line-height |
| D5 | Spacing & radius & shadow | thang spacing · radius (button / input / card / modal) · shadow (card / dropdown / modal) |
| D6 | Component library | Figma library có Button, Input, Select, Table/List, Badge/Tag, Modal, Pagination (hoặc tương đương mobile) |
| D7 | Layout / platform | viewport + khung màn (header, sidebar / tab bar, content) cho từng platform |
| D8 | Icon & ngôn ngữ UI | bộ icon · ngôn ngữ hiển thị trên UI |

- **Đủ D1–D8** → dựng `design-system/` (§5) → user duyệt.
- **Thiếu** → Câu DS-2.

## 4. Khi user "Chưa có" — thông điệp dừng

```
⛔ Chưa thể vẽ: dự án chưa có design system.
Designer Agent cần ít nhất 1 trong các nguồn sau để đảm bảo đúng màu / font / component:
  • Link Figma page Foundations / Design Tokens / Component Library
  • Tài liệu design guideline (.md / .pdf / .docx) đặt vào input/design-system/
  • 1–5 màn hình Figma đã được designer duyệt (agent sẽ tự trích xuất design system)
Chuẩn bị xong → chạy lại: /prototype-to-figma
```

## 5. Câu DS-2 — Design system chưa đủ

```json
{
  "questions": [
    {
      "header": "Bổ sung DS",
      "question": "Design system còn thiếu: <liệt kê D#>. Bổ sung bằng cách nào?",
      "multiSelect": false,
      "options": [
        { "label": "Gửi 1–5 màn Figma (Recommended)", "description": "Paste 1–5 link màn hình / frame Figma đã duyệt — agent đọc, phân tích, trích xuất phần còn thiếu" },
        { "label": "Gửi thêm tài liệu", "description": "Đặt file vào input/design-system/ hoặc paste link" },
        { "label": "Dùng tạm phần đã có", "description": "Mục thiếu ghi TBD trong design-system/ và figma-screens.md — cần designer xác nhận sau" },
        { "label": "Dừng lại", "description": "Chuẩn bị design system đầy đủ rồi chạy lại" }
      ]
    }
  ]
}
```

**Phân tích 1–5 màn Figma:** với mỗi link → `get_variable_defs` + `get_design_context` + `get_screenshot`; đo màu thực tế (nav active, nút chính, nền, chữ), font/size/weight, spacing, radius, shadow, khung màn (viewport, header, sidebar/tab bar), component instance dùng (tên + key). Ghi nguồn đo cho từng giá trị. Màu variable và màu hiển thị lệch nhau → **tin màu đo được**, ghi mâu thuẫn vào "Mâu thuẫn cần xác nhận".

## 6. Dựng / bổ sung `design-system/`

Copy template `.claude/designer-agent/design-system-template/` → `design-system/` rồi điền:

```
design-system/
├── README.md        ← nguồn, platform list, trạng thái APPROVED/TBD, changelog, mâu thuẫn
├── foundation.md    ← D1–D5, D8
├── platform-<tên>.md← D7 (1 file / platform)
├── components.md    ← D6 (library, component key, variant)
├── tokens.json      ← bản máy đọc được
└── refs/            ← screenshot các màn đã phân tích (tuỳ chọn)
```

In tóm tắt (màu chính, font, viewport, component library, mục TBD) → `AskUserQuestion`: **Duyệt** · **Sửa**. Chỉ khi **Duyệt** mới sang Bước 0.2. Ghi `APPROVED <ngày>` vào `design-system/README.md`.
