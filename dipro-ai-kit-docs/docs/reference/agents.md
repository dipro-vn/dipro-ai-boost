# 12 Sub-Agents

Tổng hợp tất cả agents trong `project-ai-kit` với vai trò, quyền hạn và output.

---

## Bảng tổng quan

| # | Agent | File | Phase | Trigger |
|---|-------|------|-------|---------|
| 1 | init-agent | `agents/init-agent.md` | 0 | `/init-kit` |
| 2 | ba-agent | `agents/ba-agent.md` | 1 | `/create-spec` |
| 3 | techlead-design-agent | `agents/techlead-design-agent.md` | 2a | `/create-design` |
| 4 | designer-agent | `agents/designer-agent.md` | 2c | `/create-ui-design` |
| 5 | qc-agent | `agents/qc-agent.md` | 2b, 6a, 7a | `/test/*` |
| 6 | techlead-tasks-agent | `agents/techlead-tasks-agent.md` | 3 | `/create-tasks` |
| 7 | pm-agent | `agents/pm-agent.md` | 3 | `/create-plan` |
| 8 | backend-agent | `agents/backend-agent.md` | 5 | Natural language |
| 9 | frontend-agent | `agents/frontend-agent.md` | 5 | Natural language |
| 10 | mobile-agent | `agents/mobile-agent.md` | 5 | Natural language |
| 11 | qa-agent | `agents/qa-agent.md` | 6 | Natural language |
| 12 | qc-automation-agent | `agents/qc-automation-agent.md` | 7b | `/gen-automation` |

---

## Chi tiết từng Agent

### 1. init-agent

**Vai trò:** Setup dự án lần đầu  
**Trigger:** `/init-kit`  
**Output:** `AGENTS.md` được điền đầy đủ  
**Quyền:** Sửa `.md` files  

Hỏi 8 câu về: tên dự án, docs root, repos, epic codes, actors, payment, cặp dễ nhầm, cross-repo features.

---

### 2. ba-agent (Business Analyst)

**Vai trò:** Phân tích requirement, viết SPEC  
**Trigger:** `/create-spec <requirement>`  
**Output:** `<DOCS_ROOT>/features/<feature>/SPEC.md`  
**Quyền:** Sửa `.md` files ✅ | Source code ❌  

**SPEC.md bao gồm:**
- Background & Objective
- In Scope / Out of Scope  
- Actors & User Stories
- Acceptance Criteria (per AC, per actor)
- Data Model sơ bộ
- Screen list (điền trước, Figma link điền sau bởi Designer)
- Q&A / Ambiguities

**Khi thiếu thông tin:** Hỏi ngay, không tự giả định.

---

### 3. techlead-design-agent (Tech Lead Design)

**Vai trò:** Thiết kế architecture, API, DB  
**Trigger:** `/create-design`  
**Input:** `SPEC.md`  
**Output:** `<DOCS_ROOT>/features/<feature>/<repo>/DESIGN.md`  
**Quyền:** Sửa `.md` files ✅ | Source code ❌  

**DESIGN.md bao gồm:**
- Architecture Decision
- API Endpoints (method, path, auth, request/response)
- Database Schema changes
- Component/Module breakdown
- Cross-repo dependencies
- Implementation phases (Phase 1 → 2 → 3)

---

### 4. designer-agent (UI Designer)

**Vai trò:** Tạo Figma frames  
**Trigger:** `/create-ui-design`  
**Input:** `SPEC.md ## Screens`  
**Output:** Figma URL → điền vào `SPEC.md ## Screens`  
**Quyền:** Sửa `SPEC.md ## Screens` ✅ | Source code ❌  

Dùng Design System tokens từ `.claude/rules/design_rule.md`.

---

### 5. qc-agent (QC Engineer)

**Vai trò:** Sinh manual test cases, thực thi test, viết bug report  
**Trigger:** `/test/analyze-req`, `/test/plan-tcs`, `/test/gen-tcs`...  
**Output:** `analysis.md`, `plan-tcs.md`, `test-cases.md`, `review_report.md`  
**Quyền:** Sửa `.md` files ✅ | Chạy test suite ✅ | Source code ❌  

**Chạy 3 lần:**
1. **Phase 2b** — Sau SPEC, sinh TC
2. **Phase 7a** — Sau dev, thực thi TC + bug report
3. **Phase 7a** — Execution checklist trước deploy

---

### 6. techlead-tasks-agent (Tech Lead Tasks)

**Vai trò:** Phân rã DESIGN thành task files atomic  
**Trigger:** `/create-tasks`  
**Input:** `DESIGN.md` per repo  
**Output:** `tasks/task-X-Y.md` per repo  
**Quyền:** Sửa `.md` files ✅ | Source code ❌  

Mỗi task: Goal, Scope, File list, Steps, Estimate (giờ), Dependencies, Definition of Done.

---

### 7. pm-agent (Project Manager)

**Vai trò:** Lập kế hoạch sprint, tạo Backlog  
**Trigger:** `/create-plan`, `/create-backlog`  
**Input:** `tasks/task-*.md`  
**Output:** `PLAN.md`, Backlog issues  
**Quyền:** Sửa `.md` files ✅ | Source code ❌  

Hỏi trước: deadline, dev available, dependency, deploy window, QA estimate.

---

### 8. backend-agent (Backend Developer)

**Vai trò:** Implement NestJS backend  
**Trigger:** `"Hãy là Backend Dev, implement task: <path>"`  
**Input:** Task file + DESIGN.md + API Contract  
**Output:** Working code + API Contract table cập nhật  
**Quyền:** Sửa source code ✅ (trong scope task) | Commit ❌*  

**Memory Update Gate:** Cập nhật `<DOCS_ROOT>/<layer>/<repo>/overview/` sau mỗi task.

---

### 9. frontend-agent (Frontend Developer)

**Vai trò:** Implement React frontend  
**Trigger:** `"Hãy là Frontend Dev, implement task: <path>"`  
**Input:** Task file + DESIGN.md + API Contract từ BE  
**Output:** Working code  
**Quyền:** Sửa source code ✅ (trong scope task) | Commit ❌*  

**Bắt buộc:** Copy API Contract từ BE trước khi bắt đầu Phase 3.

---

### 10. mobile-agent (Mobile Developer)

**Vai trò:** Implement Flutter/React Native  
**Trigger:** `"Hãy là Mobile Dev, implement task: <path>"`  
**Input:** Task file + DESIGN.md + API Contract từ BE + Figma URL  
**Output:** Working code  
**Quyền:** Sửa source code ✅ (trong scope task) | Commit ❌*  

---

### 11. qa-agent (QA Engineer)

**Vai trò:** Verify từng task sau dev  
**Trigger:** `"Hãy là QA, verify task: <path>"`  
**Input:** Task file + implementation + test cases  
**Output:** QA Report (PASS/FAIL per AC)  
**Quyền:** Sửa `.md` (QA Report) ✅ | Chạy test suite ✅ | Source code ❌  

**PASS** → handover sang task tiếp  
**FAIL** → Dev fix loop

---

### 12. qc-automation-agent (QC Automation)

**Vai trò:** Sinh và chạy Playwright E2E  
**Trigger:** `/gen-automation`  
**Input:** `test-cases.md`  
**Output:** `pages/`, `tests/`, `utils/` Playwright scripts  
**Quyền:** Chạy browser test ✅ | Sửa test scripts ✅ | Source code ❌  

Auto-heal loop: chạy → lỗi → sửa (tối đa 5 vòng).

---

## Agent vs Command

```
Command (.claude/commands/*.md)
    = Thin entry point (5-8 dòng)
    = Trỏ về → Agent

Agent (.claude/agents/*.md)
    = Single Source of Truth
    = Quy trình chi tiết đầy đủ
```

**Sửa quy trình → chỉ sửa file agent. Không sửa command.**

---

> \* Dev commit chỉ khi user yêu cầu rõ ràng trong session.
