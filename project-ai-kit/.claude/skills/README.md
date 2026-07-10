# Skills Registry

> Skills được load on-demand trong từng agent. File này là registry tra cứu — không phải always-loaded.
> Cột "Repo" ghi theo **vai trò** (xem bảng Ecosystem trong `AGENTS.md`), không phải tên repo cụ thể — kit này generic cho mọi dự án dùng cùng stack.

| Skill | Repo | Dùng khi |
|---|---|---|
| `nestjs-best-practices/` | backend | Viết/review NestJS |
| `postgresql/` | backend | Schema, migration, query |
| `redis-development/` | backend | Redis cache pattern |
| `react-expert/` | frontend (all FE repos) | React 19 hooks/component patterns |
| `frontend-review/` | frontend (all FE repos) | Code review React 19 / TanStack v5 / RTK v2 / AntD v6 |
| `flutter-review/` | mobile | Code review Flutter |
| `business-analyst/` | — | Discovery, SPEC template |
| `solution-architect/` | — | Kiến trúc cross-cutting |
| `rbt_manual_testing/` | — | Master skill cho `qc-agent` — 4 sections pipeline (context → analyze-req → plan-tcs → gen-tcs) + Complex Logic Patterns (Decision Table / State Transition / Boundary Tier) |
| `requirements_analyzer/` | — | Phân tích requirements đa nguồn (Google Drive, Figma, .md, Backlog) — dùng bởi `/test/analyze-req` + Figma 2-phase quy trình |
| `bug_reporter/` | — | Chuẩn hóa bug report — 8 Bug Types + severity/priority/repro steps — dùng bởi `/test/gen-bug-report` |
| `component_checklist/` | — | Checklist component-level (Form/Layout/Data Display) — dùng bởi `/test/gen-tcs` sau khi có Component Type từ `plan-tcs.md` |
| `testing_dimensions/` | — | Checklist testing theo platform (Web/Mobile/Desktop/Batch/Cross-platform) — dùng bởi `/test/gen-tcs` |
| `screen_strategy/` | — | Chiến lược test theo Screen archetype (List/Search, Form, Detail/View, Fallback) — dùng on-demand trong `/test/plan-tcs` khi cần viết Strategy Summary cho Screen |
| `automation_engineer/` | — | Playwright automation từ manual test cases (6 sections: Scaffold → Chọn TC → MCP Recon → Sinh code → Auto-heal → Report) — dùng bởi `/test/gen-automation` |
| `figma-design/` | frontend (all FE repos) + mobile | Figma MCP tools (read + write), token mapping Figma → design tokens dự án |
| `task-decomposition/` | — | Phân rã task từ DESIGN.md — dùng bởi `techlead-tasks-agent` |
| `project-planning/` | — | Risk, dependency, critical path — dùng bởi `pm-agent` |

> `init-agent` không nằm trong `skills/` (nó là agent, xem `.claude/agents/init-agent.md`) — không liệt kê trong bảng này.
