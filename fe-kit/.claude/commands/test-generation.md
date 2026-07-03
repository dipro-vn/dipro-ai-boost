# Test Generation

**Type:** Workflow

## Trigger

Cần sinh/bổ sung test cho feature, module, hoặc bug fix.

## Steps

1. **Đọc spec/AC** — `.claude/agents/frontend-tester` nắm hành vi mong đợi từ đặc tả của `.claude/agents/frontend-analyst` dùng `.claude/skills/requirement-analysis-*/SKILL.md`.
2. **Liệt kê case** — phân nhóm happy path, edge case dùng `.claude/skills/requirement-analysis-edge-case-discovery/SKILL.md`, error/empty/loading.
3. **Sinh test** — viết unit/component test với Jest + Testing Library dùng `.claude/skills/testing-jest-*/SKILL.md`, test theo hành vi người dùng.
4. **Đo coverage** — chạy coverage, xác định nhánh/case còn trống.
5. **Vá thiếu** — bổ sung test cho phần chưa phủ; đảm bảo test ổn định, không flaky.

## Definition of Done

- Mỗi AC có ít nhất một test tương ứng.
- Edge case và trạng thái lỗi/empty được phủ.
- Test xanh, không flaky, mock đúng ranh giới.
- Coverage đạt ngưỡng team, không còn nhánh quan trọng bỏ trống.
