# Context Files — On-Demand Load

> Agent đọc các file này khi cần trong Bước 1 — **không tự động load**. Cột "Ai đọc" chỉ định agent nào cần đọc file đó. Phần lớn các file này **rỗng trong kit gốc**, được điền dần qua `/init-kit` (khung ban đầu) + BA/PM/Tech Lead (nội dung thật theo thời gian).

## Context files

| File | Nội dung | Ai đọc |
|---|---|---|
| `specification.md` | Business context, epics, phase-gate | `ba-agent`, `pm-agent` |
| `technical.md` | Tech stack, CI/CD, known bugs | `techlead-design-agent`, `backend-agent` |
| `backlog-workflow.md` | Quy tắc tạo issue/task, status workflow | `techlead-tasks-agent`, `pm-agent`, `backend-agent`, `frontend-agent`, `mobile-agent` |
| `doc-structure.md` | Cấu trúc SPEC/DESIGN/PLAN theo feature type (single-repo vs cross-repo) | `ba-agent`, `techlead-design-agent`, `techlead-tasks-agent`, `designer-agent` |
| `designer-context.md` | UI components catalog, theme thực tế per repo — auto-extract từ source code khi cần | `designer-agent` (BẮT BUỘC mỗi lần chạy) |
| `business-flows/` (optional) | Business-flow index theo domain — chỉ cần nếu dự án có nhiều domain nghiệp vụ phức tạp, xem pattern trong `business-flows/README.md` | `ba-agent`, `techlead-design-agent`, `pm-agent` |
| `ai-workflow.md` | Kiến trúc AI Agent system | Human reference — đọc khi thêm agent mới |

## Workflows — `.claude/workflows/` (on-demand)

| File | Nội dung | Ai dùng |
|---|---|---|
| `new-feature.md` | BMAD pipeline end-to-end | Human reference — đọc khi cần tra cứu thứ tự pipeline; `pm-agent` đọc khi lập PLAN |
| `bug-fix.md` | Quy trình điều tra và fix bug | `backend-agent` / `frontend-agent` / `mobile-agent` |
| `bmad-plan-phase.js` / `bmad-build-phase.js` | Orchestrator scripts | `/create-feature` command |
