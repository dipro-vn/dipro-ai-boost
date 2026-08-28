---
description: Setup kit AI agent cho dự án mới — hỏi thông tin dự án rồi điền AGENTS.md + context templates. Dùng: /init-kit
---

Đọc `.claude/agents/init-agent.md` rồi đóng vai **Kit Setup Assistant** để init kit cho dự án hiện tại.

Toàn bộ workflow (Bước 1→3), checklist câu hỏi bắt buộc, và danh sách file cần sinh nằm trong `init-agent.md` — tuân thủ đầy đủ, không bỏ qua bước hỏi user.

Nếu `$ARGUMENTS` có nội dung (vd user đã mô tả sẵn dự án), dùng làm ngữ cảnh trả lời trước cho các câu hỏi liên quan thay vì hỏi lại.
