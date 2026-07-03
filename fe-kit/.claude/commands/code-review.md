# Code Review

**Type:** Workflow

## Trigger

Có PR/changeset cần review trước khi merge.

## Steps

1. **Checklist** — `.claude/agents/frontend-reviewer` dùng `.claude/skills/code-review-*/SKILL.md`, đối chiếu thay đổi với AC và quy ước team.
2. **Chạy review skills** — soi `.claude/skills/security-*/SKILL.md` và `.claude/skills/performance-*/SKILL.md` ở phần liên quan; kiểm tra xử lý lỗi, edge case, type-safety.
3. **Phản hồi có mức độ** — phân loại blocker / nên sửa / gợi ý, mỗi nhận xét kèm lý do và cách sửa.
4. **Tác giả sửa** — `.claude/agents/frontend-developer` xử lý blocker và các điểm thống nhất.
5. **Re-check** — reviewer kiểm tra lại các điểm đã nêu trước khi approve.

## Definition of Done

- Mọi blocker đã giải quyết.
- Bảo mật/hiệu năng vùng liên quan đã được soi.
- Nhận xét có lý do rõ ràng, đã re-check.
- PR được approve, sẵn sàng merge.
