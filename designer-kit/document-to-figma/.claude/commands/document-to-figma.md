---
description: Chuyển tài liệu (prototype HTML / SPEC / ảnh…) thành Figma HIGH-FIDELITY theo design system của dự án. Dùng: /document-to-figma [document-path] [figma-output-url]
---

Đọc `.claude/agents/designer-agent.md` rồi đóng vai **Designer**.

Arguments: **$ARGUMENTS**
1. `document-path` _(tuỳ chọn)_ — file / folder tài liệu: `.html` `.md` `.docx` `.xlsx` `.pdf` ảnh (mặc định tìm trong `input/`)
2. `figma-output-url` _(tuỳ chọn)_ — link Figma đầu ra

Bắt buộc chạy Bước 0 theo thứ tự: **G1 design system** → **G2 tài liệu & phạm vi** → **G3 link Figma đầu ra** → platform → ngôn ngữ tên → LEARNING SUMMARY. Chỉ hỏi (bằng `AskUserQuestion`) phần chưa có trong arguments. Gate nào không đạt → dừng, không vẽ.
