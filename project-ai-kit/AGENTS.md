# \<PROJECT_NAME\> — Project Rules for AI Agents

> **Chưa init?** Chạy `/init-kit` để điền Ecosystem/Actors. Setup A→Z ở `README.md`.

<ecosystem>

## Repos

| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| _(tên repo)_ | _(đường dẫn tương đối)_ | backend / frontend / mobile / other | _(NestJS / React / Flutter / ...)_ |

Mỗi repo có 1 **Epic code** ngắn (`E01`, `E02`...) tham chiếu xuyên suốt SPEC/DESIGN/task/Screen Code.

- **Domain:** _(1-2 câu, điền qua `/init-kit`)_
- **`<DOCS_ROOT>`:** single long-memory chứa SPEC/DESIGN/PLAN/tasks/test-cases cho mọi feature (ví dụ `<project>-docs/docs/features/`).
- **E2E Testing (optional):** repo Playwright riêng nếu có.

</ecosystem>

---

<core_rules>

## Nguyên tắc bắt buộc (project-specific)

> AI behavior policy chung + companion rules → `./POLICIES.md`. Section này chỉ liệt kê rules **đặc thù dự án**.

1. _(điền qua `/init-kit` — ví dụ: 2 repo tên gần giống, quy ước đặt tên riêng, business rule hay bị AI đoán sai...)_
2. **Memory Update Gate** sau mỗi Dev task → xem `<memory_update_gate>` bên dưới.

Rules đọc-on-demand khác (context role, doc path, per-layer coding/git/design/tilth) → xem `.claude/rules/` (index đầy đủ ở `POLICIES.md`).

</core_rules>

---

<red_line_rules>

## Cross-repo features (đụng nhiều repo)

_(Điền qua `/init-kit` — feature nào đụng ≥ 2 repo. Ví dụ: Payment (backend + FE/mobile callback), Auth JWT (backend + tất cả client), Real-time WS (server + subscribers).)_

| Tính năng | Repos liên quan |
|---|---|
| _(điền)_ | _(điền)_ |

</red_line_rules>

---

<agent_architecture>

## Agent architecture

**Agent vs Command:** Agent (`.claude/agents/*.md`) = canonical workflow (single source of truth). Command (`.claude/commands/*.md`) = thin entry point 5–8 dòng, trỏ về agent. Sửa quy trình → chỉ sửa file agent. User trigger 2 cách: slash command (`/create-spec login`) hoặc natural language ("hãy là BA, làm SPEC cho login") — cùng load agent.

**Bước 2 song song 3 agent** — 2a Tech Lead · 2b QC (pipeline 3 bước) · 2c Designer. **QC chạy 3 lần** — lần 1 sau SPEC (sinh TC), lần 2 sau dev (execute + bug report), lần 3 song song 7a (Playwright E2E qua `qc-automation-agent`).

**QC vs QA vs QC-Automation:** qc-agent = manual TC (artifact `.md`); qa-agent = post-dev verify unit test + coverage (QA Report/task); qc-automation-agent = E2E browser (`.spec.ts` + execution report). Bổ sung nhau, không thay thế.

> **12 sub-agents đầy đủ** (vai trò + slash command mapping) → `.claude/commands/README.md` (command → agent) hoặc `ai-agents-workflow.md` §1 (phase-gate table). Skills → `.claude/skills/README.md`. Context/Workflows → `.claude/context/README.md`.

</agent_architecture>

---

<bmad_workflow>

## BMAD Workflow — Phase Skeleton

| Phase | Agent | Command | Output |
|---|---|---|---|
| 0 Setup | `init-agent` | `/init-kit` | `AGENTS.md` + context |
| 1 Discovery | `ba-agent` | `/create-spec` | `SPEC.md` |
| 2 Design (parallel) | `techlead-design-agent` · `qc-agent` · `designer-agent` | `/create-design` · `/test/analyze-req`→`plan-tcs`→`gen-tcs` · `/create-ui-design` | `Design-Technical.md` · TC files · Figma URL |
| 3 Planning | `techlead-tasks-agent` · `pm-agent` | `/create-tasks` · `/create-plan` (+ `/create-backlog`) | `tasks/task-*.md` · `PLAN.md` |
| 4 Build | `backend-agent` → `frontend-agent` ‖ `mobile-agent` | BE Phase 1→2 (migration + API + Contract) → copy Contract → FE/Mobile Phase 3 (song song, 3 sub-steps) → Phase 4 integration | Code + API Contract table |
| 5 Verify | `qa-agent` | `"Hãy là QA, verify task: <path>"` | QA Report |
| 6 Test (parallel) | `qc-agent` · `qc-automation-agent` | `/test/generate_test_execution_checklist` (+ `/test/generate_regression_suite`) · `"Hãy là QC Automation…"` | Execution checklist · Playwright `.spec.ts` |

**Contract Lock** trước Phase 3 (Build FE/Mobile): REST + WebSocket + Push — confirm bởi BE+FE+Mobile+PM+QC.

Chi tiết đầy đủ (per-step context, handover, on-demand commands `/test/review-tcs` · `/test/export-xlsx` · `/test/gen-bug-report`) → `.claude/workflows/new-feature.md`. Bảng agent audit + flowchart per agent → `ai-agents-workflow.md`. Danh sách command đầy đủ → `.claude/commands/README.md`.

</bmad_workflow>

---

<memory_update_gate>

## Memory Update Gate — sau mỗi Dev task

> Dev agent BẮT BUỘC cập nhật overview docs của repo (`<DOCS_ROOT>/<layer>/<repo>/overview/`) khi task thay đổi endpoint/entity/pattern/structure. Bảng mapping chi tiết per-layer → section "Memory Update Gate" trong `.claude/agents/{backend,frontend,mobile}-agent.md`. Sau Dev xong → handover `qa-agent`; PASS → task kế, FAIL → dev fix loop.

</memory_update_gate>
