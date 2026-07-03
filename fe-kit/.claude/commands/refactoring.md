# Refactoring

**Type:** Workflow

## Trigger

Cần cải thiện cấu trúc/độ rõ/hiệu năng của code mà KHÔNG đổi hành vi.

## Steps

0. **Chuẩn bị Context** - Đọc `CLAUDE.md` và các file liên quan trong `.claude/docs/` trước khi thay đổi.
1. **Xác định mục tiêu** — `.claude/agents/frontend-architect` nêu rõ vấn đề và đích đến (tách module, đổi pattern, giảm trùng lặp).
2. **Đảm bảo test** — `.claude/agents/frontend-tester` xác nhận có test bao phủ hành vi hiện tại; nếu thiếu, viết bổ sung trước dùng `.claude/skills/testing-jest-*/SKILL.md`.
3. **Refactor từng bước** — `.claude/agents/frontend-developer` đổi nhỏ, commit nhỏ, chạy test sau mỗi bước dùng `.claude/skills/react-*/SKILL.md`, `.claude/skills/typescript-*/SKILL.md`, `.claude/skills/performance-*/SKILL.md`.
4. **Verify** — chạy đủ test + so sánh hành vi/output; không thay đổi API công khai ngoài dự kiến.
5. **Review** — `.claude/agents/frontend-reviewer` chạy `.claude/commands/code-review.md`, xác nhận behavior bất biến.

## Definition of Done

- Hành vi/đầu ra không đổi (test cũ vẫn xanh).
- Cải thiện được mục tiêu đề ra (rõ hơn/nhanh hơn/ít trùng lặp).
- Không phát sinh API breaking ngoài ý muốn.
- Review pass.
