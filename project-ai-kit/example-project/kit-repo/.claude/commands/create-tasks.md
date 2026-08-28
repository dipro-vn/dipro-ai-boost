---
description: Phân rã DESIGN.md thành task files theo Tech Lead Tasks workflow. Dùng: /create-tasks <path/to/feature-folder>
---

Đọc `.claude/agents/techlead-tasks-agent.md` rồi đóng vai **Tech Lead (Tasks)** để tạo task files từ: **$ARGUMENTS**

Toàn bộ workflow (Bước 1→6), bảng Backlog Category mapping, phase numbering, template task-x-y, ràng buộc Unit Test bắt buộc, và Status Workflow nằm trong `techlead-tasks-agent.md` — tuân thủ đầy đủ.

Nếu `$ARGUMENTS` rỗng hoặc không trỏ tới feature folder hợp lệ, hỏi user trước khi bắt đầu.
