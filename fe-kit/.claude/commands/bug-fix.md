# Bug Fix

**Type:** Workflow

## Trigger

Có báo lỗi/issue mô tả hành vi sai cần sửa.

## Steps

0. **Chuẩn bị Context** - Đọc `CLAUDE.md` và các file liên quan trong `.claude/docs/` trước khi thay đổi.
1. **Tái hiện** — dựng lại lỗi theo bước; nếu thiếu thông tin, `.claude/agents/frontend-analyst` dùng `.claude/skills/requirement-analysis-*/SKILL.md` làm rõ hành vi mong đợi.
2. **Khoanh vùng** — tìm nguyên nhân gốc (root cause), không vá triệu chứng; xác định phạm vi ảnh hưởng.
3. **Fix** — `.claude/agents/frontend-developer` sửa tối thiểu, đúng root cause, giữ type-safe và quy ước.
4. **Regression test** — `.claude/agents/frontend-tester` thêm test tái hiện bug dùng `.claude/skills/testing-jest-*/SKILL.md`, chạy lại suite liên quan.
5. **Review** — `.claude/agents/frontend-reviewer` chạy `.claude/commands/code-review.md`, xác nhận không phát sinh hồi quy.

## Definition of Done

- Lỗi không còn tái hiện; nguyên nhân gốc được xử lý.
- Có regression test cho đúng bug, đều xanh.
- Không phát sinh hồi quy ở vùng liên quan.
- Review pass, không còn blocker.
