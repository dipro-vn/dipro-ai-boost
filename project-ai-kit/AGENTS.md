# \<PROJECT_NAME\> — Project Rules for AI Agents

> **Kit chưa init.** Bảng Ecosystem/Actors bên dưới còn trống. Chạy `/init-kit` (hoặc "hãy chạy init kit cho dự án này") trước khi dùng các agent khác — `init-agent` sẽ điền các bảng này qua vài câu hỏi. Chi tiết cài đặt → `README.md` ở root kit.

<ecosystem>

## Repos

_(chưa điền — `/init-kit` sẽ hỏi và điền bảng này)_

| Repo | Đường dẫn | Vai trò | Stack |
|---|---|---|---|
| _(tên repo)_ | _(đường dẫn tương đối)_ | backend / frontend / mobile / other | _(NestJS / React / Flutter / ...)_ |

> Mỗi repo tự đặt 1 **Epic code** ngắn (ví dụ `E01`, `E02`...) dùng để tham chiếu xuyên suốt SPEC/DESIGN/task/Screen Code — do team quyết định khi init, không cố định số lượng.

**Domain:** _(1-2 câu mô tả dự án làm gì, cho ai — điền qua `/init-kit`)_

**Docs:** `<DOCS_ROOT>` — single long-memory chứa SPEC, DESIGN, PLAN, tasks, test-cases cho mọi feature (điền path thật qua `/init-kit`, ví dụ `<project>-docs/docs/features/`). Mọi agent bên dưới dùng `<DOCS_ROOT>` để chỉ path này — thay bằng path thật sau khi init.

**E2E Testing (optional):** nếu dự án có repo Playwright riêng (song song với repo source), khai báo path ở đây khi có.

</ecosystem>

---

<core_rules>

## Nguyên tắc bắt buộc (project-specific)

> **AI behavior policy chung** (không đoán mò · stack constraints · permission per persona · ...) → xem `./POLICIES.md` (always-loaded, không sửa ở đây). Dưới đây chỉ liệt kê rules **đặc thù dự án này** mà POLICIES.md không cover.

1. _(điền qua `/init-kit` hoặc bổ sung thủ công — ví dụ: 2 repo tên gần giống dễ nhầm, quy ước đặt tên riêng, business rule hay bị AI đoán sai...)_
2. **Context files đọc đúng theo role** — xem cột "Ai đọc" trong bảng Context (section `<agent_architecture>` bên dưới). Không đọc rộng ra ngoài role.
3. **Doc location single path:** mọi feature docs đặt trong `<DOCS_ROOT>/features/<feature>/`.
4. **Memory Update Gate** sau mỗi dev task (xem section `<memory_update_gate>` bên dưới) — không skip.

Chi tiết per-layer rules → `.claude/rules/`: `stack-constraints.md` · `security-rules.md` · `git-workflow.md` · `coding-style.md` · `project-structure.md`

</core_rules>

---

<tilth_rules>

## Source code analysis — dùng tilth

```bash
tilth_search(query: "OrderService")          # tìm symbol/usage
tilth_read(paths: ["<file>"])                # đọc file
tilth_files(pattern: "**/*.service.ts")      # list file
tilth_deps(path: "<file>")                   # blast radius — BẮT BUỘC trước khi đổi public interface
```

**Thứ tự:** đọc docs liên quan → `tilth_search` xác nhận thực tế → mới generate code.

> Nếu dự án không cài tilth MCP, dùng `Grep`/`Read`/`Glob` chuẩn thay thế — vẫn giữ đúng thứ tự "đọc docs → xác nhận thực tế → generate".

</tilth_rules>

---

<red_line_rules>

## Phân công cross-repo (tính năng chạm nhiều repo)

> Mapping 1 repo → 1 epic: xem bảng **Repos** ở section `<ecosystem>`. Phần dưới chỉ liệt kê các tính năng **đụng nhiều repo cùng lúc** — dev phải đụng vào cả 2 bên. Điền qua `/init-kit` (optional) hoặc bổ sung khi phát hiện trong quá trình dev.

| Tính năng cross-repo | Repos liên quan |
|---|---|
| _(ví dụ: payment integration)_ | _(backend repo)_ + _(mobile/frontend repo nhận callback)_ |
| _(ví dụ: real-time / WebSocket)_ | _(backend repo — socket server)_ + _(repo nào subscribe event đó)_ |
| _(ví dụ: auth flow JWT)_ | _(backend repo — issue + verify)_ + tất cả FE/Mobile (lưu cookie/secure storage) |

</red_line_rules>

---

<agent_architecture>

## Kiến trúc Agent — `.claude/`

### Nguyên tắc — Agent vs Command

- **Agent** (`.claude/agents/*.md`) = **canonical workflow** + persona + ràng buộc + template. Single source of truth cho từng vai trò.
- **Command** (`.claude/commands/*.md`) = **thin entry point** (5–8 dòng). Mỗi command chỉ trỏ về agent tương ứng và truyền `$ARGUMENTS`. Không chứa workflow.
- Khi sửa quy trình BA / Tech Lead / PM → **chỉ sửa file agent**, không sửa command (trừ khi đổi command name hoặc cách parse args).
- User có thể trigger theo 2 cách: gõ slash command (`/create-spec login`) hoặc nói tự nhiên ("hãy là BA, làm SPEC cho login") — cả hai cùng load file agent.
- **Handover hint:** Section "Bước tiếp theo" trong Output của mỗi agent dùng natural language (vd `"Hãy là Tech Lead Design, làm DESIGN.md từ SPEC: <path>"`) — user copy-paste làm prompt turn kế tiếp. Slash command tương ứng vẫn work song song.
- **Handover chain:** chi tiết step-by-step ở bảng **BMAD Workflow** bên dưới. Lưu ý: **Bước 2 gồm 3 agent chạy song song** — 2a Tech Lead Design (DESIGN.md) · 2b QC (test cases) · 2c Designer (Figma frames + URL điền vào SPEC.md ## Screens). **QC chạy 3 lần** — lần 1 sau SPEC (sinh TC manual), lần 2 sau dev xong (execute TC + bug report), lần 3 song song với 7a (chạy Playwright E2E tự động — `qc-automation-agent`).

### Sub-agents — `.claude/agents/`

| Agent | Vai trò | Trigger khi | Slash command |
|---|---|---|---|
| `init-agent.md` | Kit Setup Assistant | **Chạy 1 lần** khi mới pull kit — điền Ecosystem/Actors | `/init-kit` |
| `ba-agent.md` | Business Analyst | Phân tích yêu cầu, tạo SPEC.md | `/create-spec` |
| `techlead-design-agent.md` | Tech Lead Design | Đọc SPEC → tạo DESIGN.md per repo | `/create-design` |
| `techlead-tasks-agent.md` | Tech Lead Tasks | Đọc DESIGN → phân rã task files | `/create-tasks` |
| `pm-agent.md` | Project Manager | Tạo PLAN.md, phase-gate, timeline | `/create-plan` |
| `backend-agent.md` | Backend Developer | Implement/review API, service, entity, migration cho repo vai trò `backend` | `/generate-api`, `/review-code` |
| `frontend-agent.md` | Frontend Developer | Implement/review component, hook, store cho repo vai trò `frontend` | `/create-component`, `/review-code` |
| `mobile-agent.md` | Mobile Developer | Implement/review screen, API call cho repo vai trò `mobile` | `/review-code` |
| `qc-agent.md` | QC Manual Tester | **Sau SPEC, trước/trong khi test** — sinh TC (RBT/QUICK), regression, execution checklist, bug report, test data, exploratory charter | `/test/generate_*` (nhiều command) |
| `designer-agent.md` | UI Designer | **Sau SPEC** — tạo Figma screens, điền Figma URL vào SPEC.md ## Screens | `/create-ui-design` |
| `qa-agent.md` | QA Engineer | **Sau khi dev xong task** — chạy test suite, verify coverage, validate AC, non-regression | `"Hãy là QA, verify task: <path/task-x-y.md>"` |
| `qc-automation-agent.md` | QC Automation Tester | **Sau khi Dev deploy lên DEV** — đọc SPEC.md + Figma URL, sinh Playwright `.spec.ts`, chạy E2E test **có headed mode** | `"Hãy là QC Automation, test feature: <feature-path>, Figma: <url>"` |

> **QC vs QA vs QC-Automation:** `qc-agent` = manual tester sinh/thực thi TC (artifact `.md`); `qa-agent` = post-dev verify unit test + coverage (QA Report per task); `qc-automation-agent` = E2E test tự động trên browser sau khi website chạy (`.spec.ts` + execution report). Ba agent bổ sung nhau, không thay thế.

### Slash Commands — `.claude/commands/`

Danh sách đầy đủ → `.claude/commands/README.md`

### Skills — `.claude/skills/`

Danh sách đầy đủ (skill → repo/vai trò → khi nào dùng) → `.claude/skills/README.md`

### Context — `.claude/context/` (đọc on-demand)

> Agent phải đọc các file này khi cần trong Bước 1 — không tự động load. Cột "Ai đọc" chỉ định agent nào cần đọc file đó. Phần lớn các file này **rỗng trong kit gốc**, được điền dần qua `/init-kit` (khung ban đầu) + BA/PM/Tech Lead (nội dung thật theo thời gian).

| File | Nội dung | Ai đọc |
|---|---|---|
| `specification.md` | Business context, epics, phase-gate | `ba-agent`, `pm-agent` |
| `technical.md` | Tech stack, CI/CD, known bugs | `techlead-design-agent`, `backend-agent` |
| `backlog-workflow.md` | Quy tắc tạo issue/task, status workflow | `techlead-tasks-agent`, `pm-agent`, `backend-agent`, `frontend-agent`, `mobile-agent` |
| `doc-structure.md` | Cấu trúc SPEC/DESIGN/PLAN theo feature type (single-repo vs cross-repo) | `ba-agent`, `techlead-design-agent`, `techlead-tasks-agent`, `designer-agent` |
| `designer-context.md` | UI components catalog, theme thực tế per repo — auto-extract từ source code khi cần | `designer-agent` (BẮT BUỘC mỗi lần chạy) |
| `business-flows/` (optional) | Business-flow index theo domain — chỉ cần nếu dự án có nhiều domain nghiệp vụ phức tạp, xem pattern trong `business-flows/README.md` | `ba-agent`, `techlead-design-agent`, `pm-agent` |
| `ai-workflow.md` | Kiến trúc AI Agent system | Human reference — đọc khi thêm agent mới |

### Workflows — `.claude/workflows/` (đọc on-demand)

| File | Nội dung | Ai dùng |
|---|---|---|
| `new-feature.md` | BMAD pipeline end-to-end | Human reference — đọc khi cần tra cứu thứ tự pipeline; `pm-agent` đọc khi lập PLAN |
| `bug-fix.md` | Quy trình điều tra và fix bug | `backend-agent` / `frontend-agent` / `mobile-agent` |

</agent_architecture>

---

<bmad_workflow>

## BMAD Workflow

| Bước | Command | Output | Agent | Phase |
|---|---|---|---|---|
| 0 | `/init-kit` | `AGENTS.md` điền + context templates | `init-agent` | Setup (1 lần) |
| 1 | `/create-spec <feature>` | `SPEC.md` | `ba-agent` | Discovery |
| 2a | `/create-design <SPEC.md>` | `DESIGN.md` per repo | `techlead-design-agent` | Design |
| 2b | `/test/generate_manual_testcases_rbt` (parallel) | `test-cases/tc_*.md` | `qc-agent` | Design |
| 2c | `/create-ui-design <SPEC.md>` (parallel) | Figma frames + URL điền vào SPEC.md ## Screens | `designer-agent` | Design |
| 3 | `/create-tasks <feature/>` | `tasks/task-*.md` (Phase 1,2: template BE; Phase 3: template FE/Mobile) | `techlead-tasks-agent` | Planning |
| 4 | `/create-plan <feature/>` | `PLAN.md` | `pm-agent` | Planning |
| 4b | (optional) `/create-backlog <feature/>` | Backlog issues (1 per task) | `pm-agent` (Bước 4) | Planning |
| 5a | Implement BE task (Phase 1→2) | Working code + **API Contract table** | `backend-agent` | Build |
| 5b | Copy API Contract → task-3-x.md | Paste vào section `## API Contract` trong task-3-x.md | — (manual step) | Build |
| 5c | Implement FE task (Phase 3): Step1 service file → Step2 hooks → Step3 wire UI | Working code + integration check | `frontend-agent` | Build |
| 5d | Implement Mobile task (Phase 3, song song với 5c) | Working code + integration check | `mobile-agent` | Build |
| 5e | task-4-x Integration test | Verify BE + FE + Mobile hoạt động end-to-end | `backend-agent` + `frontend-agent` + `mobile-agent` | Integration |
| 6 | QA verify per task | QA Report | `qa-agent` — trigger: `"Hãy là QA, verify task: <path>"` | Verify |
| 7a | Sinh/chạy execution checklist | Test execution checklist + Bug reports | `qc-agent` — trigger: `/test/generate_test_execution_checklist` | Test |
| 7b | (optional) `/test/generate_regression_suite` | Regression suite | `qc-agent` | Test |
| 7c | `"Hãy là QC Automation, test feature: <feature-path>, Figma: <figma-url>"` (song song với 7a) | Playwright `.spec.ts` + `execution-report.md` | `qc-automation-agent` — **điều kiện:** website DEV đang chạy, SPEC.md + Figma URL có sẵn | Test |

**Phase order:** Phase 1 (DB migration) → Phase 2 (API + output API Contract) → **copy API Contract vào FE task** → Phase 3 (FE + Mobile song song, mỗi task 3 sub-steps) → Phase 4 (Integration)

**Contract Lock** trước Phase 3: REST API + WebSocket events + Push notification payload (nếu có) — confirm bởi BE + FE + Mobile + PM + QC (để QC chốt TC dựa trên contract).

**API Contract handoff**: Sau khi BE xong task Phase 2, bảng `## API Contract` trong BE output phải được copy vào section tương ứng trong task Phase 3 (FE/Mobile) trước khi FE/Mobile bắt đầu code. FE không tự đoán endpoint.

Chi tiết trigger Designer / QC + thứ tự tham gia → `.claude/workflows/new-feature.md`

</bmad_workflow>

---

<memory_update_gate>

## Memory Update Gate — sau mỗi Dev task

> **Đây là mặt "GHI" của overview docs. Mặt "ĐỌC" là bắt buộc ở Bước 1 của mỗi Dev agent + Bước 3 Tech Lead Design + Bước 1 Tech Lead Tasks** — cùng một bộ file. Overview docs không phải write-only: Tech Lead đọc chúng để thiết kế/chia task không trùng, Dev đọc chúng để code đúng pattern, rồi ghi lại thay đổi tại đây. Nếu sửa gate này (thêm/bớt file) → cập nhật luôn danh sách load ở các agent tương ứng để hai mặt luôn khớp.

| Thay đổi | File cần cập nhật (full path) |
|---|---|
| Endpoint mới / đổi method/path/response | `<DOCS_ROOT>/backend/<backend-repo>/overview/api-catalog.md` |
| Entity mới / đổi column/relation | `<DOCS_ROOT>/backend/<backend-repo>/overview/erd.md` |
| Pattern mới trong BE codebase | `<DOCS_ROOT>/backend/<backend-repo>/overview/patterns.md` |
| Pattern mới trong FE codebase | `<DOCS_ROOT>/frontend/<repo>/overview/patterns.md` |
| Thay đổi cấu trúc module / thư mục lớn | `<DOCS_ROOT>/<layer>/<repo>/overview/structure.md` |
| Không có gì thay đổi | Bỏ qua |

```
✅ task-x-y hoàn thành
Files đã thay đổi:  <path> → <mô tả>
Unit Tests:         ✅ <file>.spec.ts pass, coverage X% (target Y%)
Non-Regression:     ✅ <tính năng X> vẫn hoạt động
Memory Update Gate: ✅/skipped api-catalog / erd / patterns
Bước tiếp theo:     → "Hãy là QA, verify task này: <task-x-y.md>"
                    → sau khi QA PASS: task-x-(y+1)
```

> Dev agent (`backend-agent`, `frontend-agent`, `mobile-agent`) **handover qa-agent** trước khi sang task tiếp theo. `qa-agent` chạy unit test + validate AC + check non-regression. Nếu QA FAIL, dev fix rồi loop lại; nếu QA PASS, dev mới move sang task kế tiếp.

</memory_update_gate>
</content>
