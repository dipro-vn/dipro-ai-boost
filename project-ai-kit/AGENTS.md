# \<PROJECT_NAME\> — Project Rules for AI Agents

> **Chưa init?** App chỉ tạo khung kit. Mở Claude Code tại `agentsRoot`, nhập `/init-kit` để điền Ecosystem/Actors. Đây là slash command trong Claude Code, không phải lệnh shell. Setup A→Z ở `README.md`.

<ecosystem>

## Repos

| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| _(tên repo)_ | _(đường dẫn tương đối so với Repository root)_ | backend / frontend / mobile / other | _(NestJS / React / Flutter / ...)_ |

Mỗi repo có 1 **Epic code** ngắn (`E01`, `E02`...) tham chiếu xuyên suốt SPEC/DESIGN/task/Screen Code.

Liệt kê **mỗi repo một dòng**, kể cả nhiều repo cùng vai trò — Dipro AI Boost dựng một node Build riêng cho từng dòng, nên gộp lại là mất khả năng chạy/theo dõi riêng.

- **Domain:** _(1-2 câu, điền qua `/init-kit`)_
- **`<DOCS_ROOT>`:** single long-memory chứa SPEC/DESIGN/tasks/test-cases cho mọi feature (ví dụ `<project>-docs/docs/features/`).
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

**Bước 2 song song 3 agent** — 2a Tech Lead Design · 2b QC (pipeline 3 bước) · 2c Designer. **QC chạy 1 lần trong pipeline** — sau SPEC, sinh bộ test case (`qc-agent`). Bước test sau Build do `qc-automation-agent` đảm nhiệm (Playwright E2E).

**QC vs QC-Automation:** qc-agent = manual TC (artifact `.md`, bước 2b); qc-automation-agent = E2E browser (`.spec.ts` + execution report, bước 5). Bổ sung nhau, không thay thế.

> `qa-agent` và bước "QC execution checklist" **không còn nằm trong pipeline** — file agent vẫn giữ trong `.claude/agents/`, chỉ chạy thủ công khi user gọi trực tiếp.

> **Danh sách sub-agents đầy đủ** (vai trò + slash command mapping) → `.claude/commands/README.md` (command → agent) hoặc `ai-agents-workflow.md` §1 (phase-gate table). Skills → `.claude/skills/README.md`. Context/Workflows → `.claude/context/README.md`.

</agent_architecture>

---

<bmad_workflow>

## BMAD Workflow — Phase Skeleton

| Phase | Agent | Command | Output |
|---|---|---|---|
| 0 Setup | `init-agent` | `/init-kit` | `AGENTS.md` + context |
| 1 Discovery | `ba-agent` | `/create-spec` | 6 outputs — `SPEC.md` (11 sections, có `## BA Deliverables`) · 3 Figma frame · `prototype/index.html` · MkDocs site |
| 2 Design (parallel) | `techlead-design-agent` · `qc-agent` · `designer-agent` | `/create-design` · `/test/analyze-req`→`plan-tcs`→`gen-tcs` · `/create-ui-design` | `DESIGN.md` · TC files · Figma URL |
| 3 Planning | `techlead-tasks-agent` | `/create-tasks` | `tasks/task-*.md` |
| 4 Build | `backend-agent` → `frontend-agent` ‖ `mobile-agent` | BE Phase 1→2 (migration + API + Contract) → copy Contract → FE/Mobile Phase 3 (song song, 3 sub-steps) → Phase 4 integration | Code + API Contract table |
| 5 Test | `qc-automation-agent` | `"Hãy là QC Automation…"` | Playwright `.spec.ts` + execution report |

**Contract Lock** trước Phase 3 (Build FE/Mobile): REST + WebSocket + Push — confirm bởi BE+FE+Mobile+PM+QC.

Chi tiết đầy đủ (per-step context, handover, on-demand commands `/test/review-tcs` · `/test/export-xlsx` · `/test/gen-bug-report` · `/test/generate_test_execution_checklist` · `/test/generate_regression_suite`) → `.claude/workflows/new-feature.md`. Bảng agent audit + flowchart per agent → `ai-agents-workflow.md`. Danh sách command đầy đủ → `.claude/commands/README.md`.

</bmad_workflow>

---

<memory_update_gate>

## Memory Update Gate — sau mỗi Dev task

> Dev agent BẮT BUỘC cập nhật overview docs của repo (`<DOCS_ROOT>/<layer>/<repo>/overview/`) khi task thay đổi endpoint/entity/pattern/structure. Bảng mapping chi tiết per-layer → section "Memory Update Gate" trong `.claude/agents/{backend,frontend,mobile}-agent.md`. Sau Dev xong (test + coverage của chính task đó phải xanh) → chuyển task kế.

</memory_update_gate>
