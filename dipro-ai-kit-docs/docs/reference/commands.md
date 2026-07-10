# Commands & Slash Commands

Tổng hợp tất cả slash commands trong Dipro AI Kit.

---

## project-ai-kit Commands

### Setup & Init

| Command | Mô tả | Phase |
|---------|-------|-------|
| `/init-kit` | Setup dự án lần đầu, điền AGENTS.md | 0 |

### Planning Pipeline

| Command | Agent | Phase | Output |
|---------|-------|-------|--------|
| `/create-spec <requirement>` | BA | 1 | `SPEC.md` |
| `/create-design` | Tech Lead | 2a | `DESIGN.md` per repo |
| `/create-ui-design` | Designer | 2c | Figma URL |
| `/create-tasks` | Tech Lead | 3 | `tasks/task-*.md` |
| `/create-plan` | PM | 3 | `PLAN.md` |
| `/create-backlog` | PM | 3 | Backlog issues |

### Shortcut

| Command | Mô tả |
|---------|-------|
| `/create-feature <feature>` | Chạy BA → Design → Tasks, dừng ở gate |
| `/create-feature <feature> build` | Chạy Dev → QA → QC |

### QC Pipeline

| Command | Input | Output |
|---------|-------|--------|
| `/test/analyze-req [path]` | Spec/Figma/Docs | `analysis.md` |
| `/test/plan-tcs` | `analysis.md` | `plan-tcs.md` |
| `/test/gen-tcs` | `plan-tcs.md` | `test-cases.md` |
| `/test/review-tcs` | `test-cases.md` | `review_report.md` |
| `/test/export-xlsx <path> web\|app` | `test-cases.md` | `test-cases.xlsx` |
| `/test/generate_test_execution_checklist` | `test-cases.md` | Execution checklist |
| `/test/generate_regression_suite` | `test-cases.md` | Regression subset |
| `/test/gen-bug-report` | Mô tả lỗi | Bug report |

---

## backend-kit Commands

| Command | Mô tả |
|---------|-------|
| `/new-feature` | Thêm endpoint/module mới |
| `/bug-fix` | Fix lỗi (test-first mandate) |
| `/code-review` | Review changeset |
| `/test-generation` | Sinh unit test |
| `/generate-api <entity>` | Scaffold module đầy đủ |
| `/api-contract` | Produce REST API Contract |
| `/db-review` | Audit schema, query, index, cache |
| `/migration` | Add/review TypeORM migration |
| `/refactoring` | Cải cấu trúc code |

---

## fe-kit Commands

| Command | Mô tả |
|---------|-------|
| `/new-feature` | Thêm feature/page mới |
| `/bug-fix` | Fix lỗi UI/state |
| `/code-review` | Review component/hook/store |
| `/refactoring` | Cải cấu trúc |
| `/test-generation` | Sinh unit test |

---

## mobile-ai-kit Workflows

Mobile kit dùng **workflows** thay vì slash commands — trigger bằng mô tả task tự nhiên:

| Task type | Workflow file |
|-----------|-------------|
| Fix bug | `workflows/fix-bug.md` |
| Feature mới | `workflows/new-feature.md` |
| Refactor | `workflows/refactor.md` |
| Performance | `workflows/performance.md` |
| Điều tra | `workflows/investigate.md` |
| Khác | `workflows/default.md` |

---

## qc-kit-agent Commands

| Command | Input | Output |
|---------|-------|--------|
| `/analyze-req [path]` | Spec/Figma/Docs | `analysis.md` |
| `/plan-tcs` | `analysis.md` | `plan-tcs.md` |
| `/gen-tcs` | `plan-tcs.md` | `test-cases.md` |
| `/review-tcs` | `test-cases.md` | `review_report.md` |
| `/export-xlsx <path> web\|app` | `test-cases.md` | `.xlsx` |
| `/gen-automation` | `test-cases.md` | Playwright scripts |
| `/gen-bug-report` | Mô tả lỗi | Bug report |

---

## Trigger bằng Natural Language

Ngoài slash commands, có thể trigger agents bằng ngôn ngữ tự nhiên:

```
"Hãy là BA, phân tích requirement sau và viết SPEC: [requirement]"
"Hãy là Tech Lead, viết DESIGN cho tính năng login"
"Hãy là PM, lập kế hoạch sprint cho feature này"
"Hãy là Backend Dev, implement task: [path/to/task.md]"
"Hãy là QA, verify task: [path/to/task.md]"
"Hãy là QC, sinh test cases cho module login"
```

---

## Command Chaining

### Pipeline QC hoàn chỉnh

```bash
/test/analyze-req SPEC.md      # → analysis.md
/test/plan-tcs                 # → plan-tcs.md
/test/gen-tcs                  # → test-cases.md
/test/review-tcs               # → review_report.md (nếu có ≥2 QC)
/test/export-xlsx test-cases/login/test-cases.md web
```

### Parallel trong Phase 2

Chạy trong 3 session riêng biệt (hoặc tab):

```bash
# Session 1: Tech Lead
/create-design

# Session 2: QC (pipeline 3 bước)
/test/analyze-req SPEC.md
/test/plan-tcs
/test/gen-tcs

# Session 3: Designer
/create-ui-design
```
