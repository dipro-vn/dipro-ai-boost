---
description: Tạo SPEC.md cho feature mới theo BA workflow. Dùng: /create-spec <tên feature>
---

Đọc `.claude/agents/ba-agent.md` rồi đóng vai **BA (Business Analyst)** để tạo SPEC.md cho feature: **$ARGUMENTS**

Toàn bộ workflow (Bước 1→4), 10 câu hỏi bắt buộc, ràng buộc cứng, và cấu trúc SPEC nằm trong `ba-agent.md` — tuân thủ đầy đủ, không bỏ qua bước hỏi user.

Nếu `$ARGUMENTS` rỗng, hỏi user tên feature trước khi bắt đầu.
