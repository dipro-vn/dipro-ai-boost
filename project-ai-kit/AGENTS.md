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

> AI behavior policy chung → `./POLICIES.md`. Đây chỉ liệt kê rules **đặc thù dự án**.

1. _(điền qua `/init-kit` — ví dụ: 2 repo tên gần giống, quy ước đặt tên riêng, business rule hay bị AI đoán sai...)_
2. **Context files đọc đúng role** — xem `.claude/context/README.md` cột "Ai đọc".
3. **Doc location single path:** `<DOCS_ROOT>/features/<feature>/`.
4. **Memory Update Gate** sau mỗi dev task (xem `<memory_update_gate>` bên dưới).

Per-layer rules → `.claude/rules/`: `stack-constraints` · `security-rules` · `SECURITY` · `POLICY` · `RELIABILITY` · `git-workflow` · `coding-style` · `project-structure` · `design_rule`

</core_rules>

---

<tilth_rules>

## Source code analysis — dùng tilth

```
tilth_search(query)   → tìm symbol/usage
tilth_read(paths)     → đọc file
tilth_files(pattern)  → list file
tilth_deps(path)      → blast radius — BẮT BUỘC trước khi đổi public interface
```

**Thứ tự:** đọc docs → `tilth_search` xác nhận → generate. Nếu không có tilth MCP: dùng `Grep`/`Read`/`Glob` chuẩn.

</tilth_rules>

---

<red_line_rules>

## Cross-repo features (đụng nhiều repo)

Điền qua `/init-kit` hoặc bổ sung khi phát hiện. Ví dụ:

| Tính năng | Repos liên quan |
|---|---|
| Payment integration | backend + mobile/frontend nhận callback |
| Real-time / WebSocket | backend (socket server) + repo nào subscribe |
| Auth flow JWT | backend (issue+verify) + tất cả FE/Mobile (lưu token) |

</red_line_rules>

---

<agent_architecture>

## Agent architecture

**Agent vs Command:** Agent (`.claude/agents/*.md`) = canonical workflow (single source of truth). Command (`.claude/commands/*.md`) = thin entry point 5–8 dòng, trỏ về agent. Sửa quy trình → chỉ sửa file agent. User trigger 2 cách: slash command (`/create-spec login`) hoặc natural language ("hãy là BA, làm SPEC cho login") — cùng load agent.

**Bước 2 song song 3 agent** — 2a Tech Lead Design · 2b QC (pipeline 4 bước) · 2c Designer. **QC chạy 3 lần** — lần 1 sau SPEC (sinh TC), lần 2 sau dev (execute + bug report), lần 3 song song 7a (Playwright E2E qua `qc-automation-agent`).

### Sub-agents — `.claude/agents/`

| Agent | Vai trò | Slash command |
|---|---|---|
| `init-agent` | Kit Setup (1 lần) | `/init-kit` |
| `ba-agent` | Business Analyst — SPEC.md | `/create-spec` |
| `techlead-design-agent` | Tech Lead Design — DESIGN.md per repo | `/create-design` |
| `techlead-tasks-agent` | Tech Lead Tasks — phân rã task | `/create-tasks` |
| `pm-agent` | Project Manager — PLAN.md, timeline | `/create-plan`, `/create-backlog` |
| `backend-agent` | Backend Dev — API/service/entity/migration | `/generate-api`, `/review-code` |
| `frontend-agent` | Frontend Dev — component/hook/store | `/create-component`, `/review-code` |
| `mobile-agent` | Mobile Dev — screen/API call | `/review-code` |
| `qc-agent` | QC Manual — pipeline 4 bước + regression/execution/exploratory | `/test/analyze-req` → `plan-tcs` → `gen-tcs` → `review-tcs` · `/test/export-xlsx` · `/test/gen-bug-report` · ... |
| `designer-agent` | UI Designer — Figma screens + URL vào SPEC | `/create-ui-design` |
| `qa-agent` | QA Engineer — test suite + coverage + AC validate | `"Hãy là QA, verify task: <path>"` |
| `qc-automation-agent` | E2E Playwright headed mode | `"Hãy là QC Automation, test feature: <path>, Figma: <url>"` |

> **QC vs QA vs QC-Automation:** qc-agent = manual TC (artifact `.md`); qa-agent = post-dev verify unit test + coverage (QA Report/task); qc-automation-agent = E2E browser (`.spec.ts` + execution report). Bổ sung nhau, không thay thế.

**Chi tiết:**
- Commands đầy đủ → `.claude/commands/README.md`
- Skills đầy đủ → `.claude/skills/README.md`
- Context files + Workflows → `.claude/context/README.md`

</agent_architecture>

---

<bmad_workflow>

## BMAD Workflow

| Bước | Command | Output | Agent | Phase |
|---|---|---|---|---|
| 0 | `/init-kit` | `AGENTS.md` + context templates | `init-agent` | Setup |
| 1 | `/create-spec <feature>` | `SPEC.md` | `ba-agent` | Discovery |
| 2a | `/create-design <SPEC.md>` | `DESIGN.md` per repo | `techlead-design-agent` | Design |
| 2b | `/test/analyze-req` → `plan-tcs` → `gen-tcs` (parallel với 2a, 2c) | `test-cases/<module>/{analysis,plan-tcs,test-cases}.md` | `qc-agent` | Design |
| 2c | `/create-ui-design <SPEC.md>` (parallel) | Figma frames + URL → SPEC ## Screens | `designer-agent` | Design |
| 3 | `/create-tasks <feature/>` | `tasks/task-*.md` | `techlead-tasks-agent` | Planning |
| 4 | `/create-plan <feature/>` | `PLAN.md` | `pm-agent` | Planning |
| 4b | `/create-backlog <feature/>` (optional) | Backlog issues | `pm-agent` | Planning |
| 5a | Implement BE task Phase 1→2 | Code + **API Contract table** | `backend-agent` | Build |
| 5b | Copy API Contract → task-3-x.md | Manual step | — | Build |
| 5c | Implement FE task Phase 3 (service→hooks→UI) | Code + integration check | `frontend-agent` | Build |
| 5d | Implement Mobile task Phase 3 (parallel 5c) | Code + integration check | `mobile-agent` | Build |
| 5e | task-4-x integration test | BE+FE+Mobile end-to-end | Dev agents | Integration |
| 6 | `"Hãy là QA, verify task: <path>"` | QA Report | `qa-agent` | Verify |
| 7a | `/test/generate_test_execution_checklist` | Execution checklist + bug reports | `qc-agent` | Test |
| 7b | `/test/generate_regression_suite` (optional) | Regression suite | `qc-agent` | Test |
| 7c | `"Hãy là QC Automation, test feature: <path>, Figma: <url>"` (parallel 7a) | Playwright `.spec.ts` + report | `qc-automation-agent` | Test |

> **On-demand (ngoài pipeline):** `/test/review-tcs` (deep review khi ≥2 QC) · `/test/export-xlsx <path> web\|app` (khi cần bàn giao Excel client/release) · `/test/gen-bug-report` (chuẩn hóa bug).

**Phase order:** 1 (DB migration) → 2 (API + Contract) → **copy Contract vào FE task** → 3 (FE+Mobile parallel, 3 sub-steps) → 4 (Integration).

**Contract Lock** trước Phase 3: REST + WebSocket + Push — confirm bởi BE+FE+Mobile+PM+QC.

Chi tiết pipeline / handover / API Contract handoff → `.claude/workflows/new-feature.md`.

</bmad_workflow>

---

<memory_update_gate>

## Memory Update Gate — sau mỗi Dev task

> Overview docs vừa là **input** (Bước 1 của Dev/Tech Lead đọc để không code trùng) vừa là **output** (ghi lại thay đổi tại đây). Sửa gate này → cập nhật danh sách load ở dev agents tương ứng.

| Thay đổi | File cập nhật |
|---|---|
| Endpoint mới / đổi method/path/response | `<DOCS_ROOT>/backend/<repo>/overview/api-catalog.md` |
| Entity mới / đổi column/relation | `<DOCS_ROOT>/backend/<repo>/overview/erd.md` |
| Pattern mới BE codebase | `<DOCS_ROOT>/backend/<repo>/overview/patterns.md` |
| Pattern mới FE codebase | `<DOCS_ROOT>/frontend/<repo>/overview/patterns.md` |
| Cấu trúc module / thư mục lớn | `<DOCS_ROOT>/<layer>/<repo>/overview/structure.md` |
| Không có gì | Bỏ qua |

**Sau dev xong:** dev handover `qa-agent`. QA PASS → move sang task kế; QA FAIL → dev fix rồi loop. Template output ở dev agents.

</memory_update_gate>
