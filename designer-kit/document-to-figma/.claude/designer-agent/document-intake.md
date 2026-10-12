# G2 — Tài liệu & Phạm vi Intake

> Đọc ở **Bước 0.2**. Hỏi 1 lần `AskUserQuestion` (bỏ câu user đã trả lời trong lệnh).

```json
{
  "questions": [
    {
      "header": "Tài liệu",
      "question": "Tài liệu đầu vào (prototype HTML / SPEC / Basic Design / ảnh…) nằm ở đâu?",
      "multiSelect": false,
      "options": [
        { "label": "Trong input/ (Recommended)", "description": "Agent liệt kê file trong input/ (.html .md .docx .xlsx .pdf ảnh) để bạn xác nhận" },
        { "label": "Đường dẫn khác", "description": "Gõ đường dẫn file / folder ở ô Other" },
        { "label": "Chưa có file", "description": "Dùng link Figma wireframe hoặc ảnh (chọn ở câu dưới)" }
      ]
    },
    {
      "header": "Phạm vi",
      "question": "Bạn muốn phân tích / vẽ gì trong tài liệu này?",
      "multiSelect": false,
      "options": [
        { "label": "Vẽ toàn bộ (Recommended)", "description": "Mọi màn + modal / toast / empty / error có trong tài liệu" },
        { "label": "Chọn một số màn", "description": "Agent liệt kê danh sách màn để bạn chọn" },
        { "label": "Chỉ phân tích", "description": "Xuất danh sách màn + nhận xét UX + điểm cần xác nhận, chưa vẽ Figma" },
        { "label": "Vẽ 1 luồng cụ thể", "description": "Gõ tên luồng ở ô Other (vd: đăng ký → duyệt → thông báo)" }
      ]
    },
    {
      "header": "Tài liệu khác",
      "question": "Có tài liệu nào khác kèm theo không? (chọn nhiều)",
      "multiSelect": true,
      "options": [
        { "label": "SPEC / tài liệu yêu cầu", "description": ".md / .docx / .xlsx / .pdf trong input/ — dùng đúng tên màn, nghiệp vụ" },
        { "label": "Figma wireframe / low-fi", "description": "Link frame đã có — dùng làm tham khảo bố cục" },
        { "label": "Ảnh chụp màn hình", "description": "Ảnh trong input/ — tham khảo UX (không dùng dữ liệu thật)" },
        { "label": "Không có", "description": "Chỉ dùng tài liệu đã chọn ở trên" }
      ]
    }
  ]
}
```

## Xử lý câu trả lời

| Trả lời | Agent làm |
|---|---|
| Trong input/ | `Glob input/**/*` (`.html` `.md` `.docx` `.xlsx` `.pdf` ảnh) → 1 file: xác nhận · nhiều file: hỏi chọn (options = tên file, tối đa 4, còn lại Other) · 0 file: báo và hỏi lại |
| Chọn một số màn | Đọc tài liệu → liệt kê màn → `AskUserQuestion` `multiSelect: true` (nhiều hơn 4 màn: in danh sách đánh số, user gõ số ở Other) |
| Chỉ phân tích | Bỏ Bước 3–5; Bước 6 xuất inventory + nhận xét UX (luồng thiếu, trạng thái thiếu, nhất quán) |
| Vẽ 1 luồng | Lọc màn theo luồng, xác nhận danh sách trước khi vẽ |
| Không có file + Không có tài liệu / ảnh / link Figma nào | **DỪNG** — không có nguồn để vẽ |

- Tài liệu chỉ là **ý đồ UX và nội dung màn** — không copy màu / font / size từ CSS prototype hay style trong tài liệu.
- Tài liệu không phải prototype (SPEC, Basic Design…): màn / trường / trạng thái nào tài liệu không nêu → ghi `[Design]` cần xác nhận, không tự bịa.
- Ảnh / tài liệu có dữ liệu cá nhân thật → không đưa vào Figma, thay bằng dữ liệu mẫu (`.claude/rules/DATA-PRIVACY.md`).
