# PM AI Kit — Agents

## Tổng quan

| Tool | Nền tảng | Slash Command / Prompt | Agent |
|------|----------|------------------------|-------|
| Performance Report | Claude Code | `/performance-report` | `performance-report-agent` |
| Task Dashboard | GPT / ChatGPT | `task-dashboard/prompt_task_dashboard.md` | — (prompt-based) |
| Backlog Performance Extension | Chrome | — (UI extension) | — |
| NotebookLM | Google NotebookLM (web) | — (web app) | — |

Chỉ **Performance Report** chạy qua Claude Code với agent + slash command. Các tool còn lại là **prompt template** hoặc **web/browser app** — không có agent riêng trong kit này.

---

## Performance Report Agent

**Mô tả:** Wizard thiết lập và chạy báo cáo hiệu suất thành viên từ Backlog API.

**File liên quan:**
- Script: `performance-report/performance_report.py`
- Prompt logic: `performance-report/prompt_member_performance.md`
- Config: `performance-report/local.json` (không commit)
- Data: `performance-report/data/`

**Trigger:** `/performance-report` hoặc "chạy báo cáo hiệu suất".

**Quy tắc sửa đổi:** khi chỉnh logic mặc định, sửa `prompt_member_performance.md` trước — chỉ sửa `.py` khi user rõ ràng yêu cầu.

---

## Task Dashboard (prompt-based)

**Mô tả:** Prompt cho GPT tạo 1 ảnh dashboard PMO (KPI + Burndown + Burnup + Overdue).

**File liên quan:**
- Prompt: `task-dashboard/prompt_task_dashboard.md`

**Cách dùng:** Xem `task-dashboard/README.md`.
