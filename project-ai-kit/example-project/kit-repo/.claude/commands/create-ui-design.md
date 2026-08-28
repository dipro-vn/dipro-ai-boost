---
description: Tạo UI-SPEC.md + Figma screens từ SPEC.md theo Designer workflow. Dùng: /create-ui-design <path/to/SPEC.md>
---

Đọc `.claude/agents/designer-agent.md` rồi đóng vai **Designer** để tạo UI-SPEC.md + Figma screens từ SPEC: **$ARGUMENTS**

Toàn bộ workflow (Bước 1→8), Figma output location, Screen Code naming convention, token mapping, và ràng buộc nằm trong `designer-agent.md` và `.claude/skills/figma-design/SKILL.md` — tuân thủ đầy đủ.

Nếu `$ARGUMENTS` rỗng hoặc không trỏ tới SPEC.md hợp lệ, hỏi user trước khi bắt đầu.
