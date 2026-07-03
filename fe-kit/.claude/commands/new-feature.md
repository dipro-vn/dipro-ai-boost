# New Feature

**Type:** Workflow

## Trigger

Có story/issue mô tả tính năng mới cần xây từ đầu.

## Before Starting

Hỏi tối đa 10 câu để làm rõ: user flow, data structure, UI/UX expectations, styling library, technical constraints. Đề xuất plan và chờ xác nhận trước khi viết bất kỳ code nào.

## Steps

0. **Context** — Đọc `CLAUDE.md` và `.claude/docs/` trước khi thay đổi bất kỳ file nào.
1. **Phân tích** — `.claude/agents/frontend-analyst` dùng `.claude/skills/requirement-analysis-*/SKILL.md`, `.claude/skills/ui-analysis-*/SKILL.md` làm rõ AC, edge case, trạng thái UI.
2. **Thiết kế** — `.claude/agents/frontend-architect` dùng `.claude/skills/react-*/SKILL.md`, `.claude/skills/nextjs-*/SKILL.md`, `.claude/skills/typescript-*/SKILL.md`, `.claude/skills/sourcebase-knowledge-*/SKILL.md` chọn pattern, cấu trúc, contract/type.
3. **Implement** — `.claude/agents/frontend-developer` dùng `.claude/skills/form-*/SKILL.md`, `.claude/skills/react-query-*/SKILL.md`, `.claude/skills/mui-*/SKILL.md` hoặc `.claude/skills/tailwind-*/SKILL.md` hiện thực, phủ loading/empty/error.
4. **Test** — `.claude/agents/frontend-tester` chạy `.claude/commands/test-generation.md` cho AC và edge case.
5. **Review** — `.claude/agents/frontend-reviewer` chạy `.claude/commands/code-review.md` dùng `.claude/skills/security-*/SKILL.md`, `.claude/skills/performance-*/SKILL.md`; sửa theo phản hồi rồi re-check.

## Definition of Done

- Đáp ứng mọi acceptance criteria, có xử lý loading/empty/error.
- Type-safe, theo quy ước team, không secret hard-code.
- Test phủ happy path + edge case chính, đều xanh.
- Review pass, không còn blocker.
