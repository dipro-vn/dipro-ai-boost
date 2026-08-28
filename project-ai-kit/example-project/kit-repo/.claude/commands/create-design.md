---
description: Tạo DESIGN.md per repo từ SPEC.md theo Tech Lead Design workflow. Dùng: /create-design <path/to/SPEC.md>
---

Đọc `.claude/agents/techlead-design-agent.md` rồi đóng vai **Tech Lead (Design)** để tạo DESIGN.md từ SPEC: **$ARGUMENTS**

Toàn bộ workflow (Bước 1→4), bảng map nghiệp vụ → repo, ràng buộc `tilth_deps` blast radius, và cấu trúc DESIGN nằm trong `techlead-design-agent.md` — tuân thủ đầy đủ.

Nếu `$ARGUMENTS` rỗng hoặc không trỏ tới SPEC.md hợp lệ, hỏi user trước khi bắt đầu.
