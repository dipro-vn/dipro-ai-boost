# Slash Commands

> **Canonical workflow** nằm trong `.claude/agents/*.md`. Commands là thin entry points — không chứa workflow.

## BMAD Core

| Command | Chức năng | Agent |
|---|---|---|
| `/init-kit` | Setup kit cho dự án mới (chạy 1 lần) | `init-agent.md` |
| `/create-feature <feature> [mô tả]` \| `/create-feature <feature> build` | **Standalone** — chạy toàn bộ BMAD pipeline (không PM): Planning (BA→Design→Tasks) dừng ở gate, sau đó `build` chạy Dev→QA→QC | `bmad-plan-phase` / `bmad-build-phase` workflow |
| `/create-spec <feature>` | Tạo SPEC.md | `ba-agent.md` |
| `/create-design <SPEC.md>` | Tạo DESIGN.md per repo | `techlead-design-agent.md` |
| `/create-ui-design <SPEC.md>` | Tạo Figma screens + URL vào SPEC.md ## Screens | `designer-agent.md` |
| `/create-tasks <feature/>` | Phân rã DESIGN → task files | `techlead-tasks-agent.md` |
| `/create-plan <feature/>` | Tạo PLAN.md | `pm-agent.md` |
| `/create-backlog <feature/>` | Sync task files → Backlog issues | `pm-agent.md` |
| `/review-code [path]` | Review code trên branch | repo-specific |
| `/generate-api <module>` | Scaffold NestJS module | `backend-agent` |
| `/create-component <Name> [variant]` | Scaffold React component | `frontend-agent` |

## QC Automation Testing

| Command | Chức năng | Agent |
|---|---|---|
| `/qc-automation <feature-path> <figma-url> <target-app> <website-url>` | Sinh Playwright `.spec.ts` + chạy E2E test + xuất `execution-report.md` | `qc-automation-agent.md` |

> Prefer trigger tự nhiên: **"Hãy là QC Automation, test feature: `<path>`, Figma: `<url>`, app: `<app>`, website: `<url>`"**

## QC Manual Testing (`/test/*`)

> Canonical workflow: `qc-agent.md`. Master skill: `rbt_manual_testing/SKILL.md` (Sections 1-4 pipeline).

### Pipeline chính — sinh TC cho 1 module (bắt buộc theo thứ tự)

| # | Command | Chức năng | Input → Output | Skill |
|---|---|---|---|---|
| 1 | `/test/analyze-req <feature> <module>` | Phân tích requirements → Q&A + AC + Screen Inventory | SPEC.md → `analysis.md` | `rbt_manual_testing` + `requirements_analyzer` |
| 2 | `/test/plan-tcs <feature> <module>` | TC Implementation Plan (Screen → Component, Risk, Technique) | `analysis.md` → `plan-tcs.md` | `rbt_manual_testing` |
| 3 | `/test/gen-tcs <feature> <module>` | Sinh TC chi tiết (bao gồm Test Scenario + Visual + Validation) | `plan-tcs.md` + `analysis.md` → `test-cases.md` | `rbt_manual_testing` + `testing_dimensions` + `component_checklist` |
| 4 | `/test/review-tcs <feature> <module>` (optional) | Deep review 8 tiêu chí (Critical/Major/Minor) | `test-cases.md` → `review_report.md` | `rbt_manual_testing` |
| 5 | `/test/export-xlsx <path.md> [web\|app]` | Export ra `.xlsx` theo template Web/App (giữ dropdown) | `.md` → `.xlsx` | — (Python script) |

**Output path:** `<DOCS_ROOT>/features/<feature>/test-cases/<module>/{analysis.md,plan-tcs.md,test-cases.md,review_report.md,*.xlsx}`

### Standalone / độc lập

| Command | Chức năng | Skill |
|---|---|---|
| `/test/gen-bug-report` | Chuẩn hóa bug report cho Backlog (severity/priority/repro) | `bug_reporter` |
| `/test/generate_regression_suite` | Chọn TC chạy lại sau code change | `rbt_manual_testing` |
| `/test/generate_test_execution_checklist` | Checklist ưu tiên trước release | `rbt_manual_testing` |

> **thin entry** = command chỉ load agent, không chứa workflow. **standalone** = command có workflow riêng.
>
> **Đã xóa** (superseded by pipeline): `/test/generate_manual_testcases_rbt`, `/test/generate_testcases_from_requirements`, `/test/update_testcases_from_requirements`, `/test/generate_bug_report`. Update SPEC → re-run pipeline (analyze-req sẽ merge vào analysis.md hiện có).
>
> **Đã xóa** (low-value / overlap): `/test/export_to_drive` (dùng `/test/export-xlsx` cho bàn giao Excel), `/test/generate_qc_onboarding_report`, `/test/generate_test_data` (sinh inline trong `/test/gen-tcs` nếu cần).
>
> **Đã xóa** (không align qc-kit-agent + rare use): `/test/generate_cross_module_test_plan` (Pairwise `allpairspy` — nếu cần dùng lại: viết script Python inline hoặc restore từ git history), `/test/generate_exploratory_charter` (contradicts BMAD SPEC-first philosophy).
