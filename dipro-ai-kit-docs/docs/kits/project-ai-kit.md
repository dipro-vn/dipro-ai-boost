# Kit 1: project-ai-kit

> **Multi-Agent Workflow Orchestration** — Bộ khung BMAD điều phối toàn bộ vòng đời feature từ Spec đến Deploy qua 12 sub-agents.

---

## Mục đích

`project-ai-kit` là **kit trung tâm**, orchestrate toàn bộ quy trình phát triển phần mềm:

- BA phân tích requirement → viết SPEC
- Tech Lead design API/DB → viết DESIGN + tạo task
- PM lập kế hoạch sprint
- Designer tạo Figma frames
- Dev (BE/FE/Mobile) implement
- QA verify từng task
- QC sinh test cases + automation E2E

---

## Cài đặt

```bash
mkdir <ten-du-an> && cd <ten-du-an>
git init

# Copy kit vào dự án
cp -r /path/to/project-ai-kit/.claude .
cp -r /path/to/project-ai-kit/template .
cp /path/to/project-ai-kit/{CLAUDE.md,POLICIES.md,AGENTS.md} .

# Mở session và setup
claude
/init-kit
```

---

## Cấu trúc kit

```
project-ai-kit/
├── CLAUDE.md              ← Entrypoint: @POLICIES.md + @AGENTS.md
├── POLICIES.md            ← AI behavior: 5 nguyên tắc + 7 restrictions
├── AGENTS.md              ← Project ecosystem (điền qua /init-kit)
├── ai-agents-workflow.md  ← 12 agents table + phase-gate flowchart
├── Automation_Test.md     ← Setup Playwright E2E riêng
├── template/
│   ├── Web_V3.0.xlsx      ← Excel template TC cho web
│   └── App_V3.0.xlsx      ← Excel template TC cho app
└── .claude/
    ├── agents/            ← 12 sub-agent definitions
    ├── commands/          ← Slash commands
    ├── skills/            ← Technical skills
    ├── context/           ← Business memory (điền dần)
    ├── rules/             ← 8 rule files
    ├── scripts/           ← md_to_xlsx.py
    ├── workflows/         ← BMAD phase workflows
    └── templates/         ← MkDocs templates
```

---

## 12 Sub-Agents

| # | Agent | Trigger | Phase | Output |
|---|-------|---------|-------|--------|
| 1 | `init-agent` | `/init-kit` | 0 | `AGENTS.md` filled |
| 2 | `ba-agent` | `/create-spec` | 1 | `SPEC.md` |
| 3 | `techlead-design-agent` | `/create-design` | 2a | `DESIGN.md` per repo |
| 4 | `designer-agent` | `/create-ui-design` | 2c | Figma URL |
| 5 | `qc-agent` | `/test/analyze-req → gen-tcs` | 2b, 6a | TC files |
| 6 | `techlead-tasks-agent` | `/create-tasks` | 3 | `tasks/task-*.md` |
| 7 | `pm-agent` | `/create-plan` | 3 | `PLAN.md` |
| 8 | `backend-agent` | Natural language | 5 | Code + API Contract |
| 9 | `frontend-agent` | Natural language | 5 | Code |
| 10 | `mobile-agent` | Natural language | 5 | Code |
| 11 | `qa-agent` | `"Hãy là QA, verify task: ..."` | 6 | QA Report |
| 12 | `qc-automation-agent` | `/gen-automation` | 7b | Playwright `.spec.ts` |

---

## Commands chính

### Planning Pipeline

```bash
/init-kit                     # Phase 0: Setup dự án
/create-spec <requirement>    # Phase 1: BA viết SPEC
/create-design                # Phase 2a: Tech Lead Design
/create-ui-design             # Phase 2c: Designer → Figma
/create-tasks                 # Phase 3: Tech Lead phân rã tasks
/create-plan                  # Phase 3: PM lập kế hoạch
/create-backlog               # Phase 3: PM tạo Backlog issues
```

### QC Pipeline

```bash
/test/analyze-req             # Phân tích requirement → analysis.md
/test/plan-tcs                # Lên kế hoạch TC → plan-tcs.md
/test/gen-tcs                 # Sinh test cases → test-cases.md
/test/review-tcs              # Review chéo (≥2 QC)
/test/export-xlsx <path> web|app  # Xuất Excel theo template
/test/generate_test_execution_checklist  # Trước deploy
/test/generate_regression_suite  # Sau code change lớn
/test/gen-bug-report          # Chuẩn hóa bug report
```

### Shortcut

```bash
/create-feature <feature>          # BA → Design → Tasks (dừng ở gate)
/create-feature <feature> build    # Dev → QA → QC
```

---

## Rules files

| File | Nội dung |
|------|---------|
| `POLICIES.md` | 5 nguyên tắc cốt lõi + phân quyền persona |
| `SECURITY.md` | Danh sách file tuyệt đối không đọc/expose |
| `POLICY.md` | 9 sections: IP protection, code exfiltration, secrets |
| `RELIABILITY.md` | No guessing, no hallucination rules |
| `coding-style.md` | NestJS + React + Flutter conventions |
| `security-rules.md` | JWT, sanitize, AWS Parameter Store |
| `git-workflow.md` | Branch naming, commit format, PR checklist |
| `stack-constraints.md` | Version pinning bắt buộc |
| `project-structure.md` | NestJS module structure, React structure, Doc structure |
| `design_rule.md` | Design system tokens (colors, typography, spacing) |

---

## Doc structure (BMAD)

```
<DOCS_ROOT>/features/<feature>/
├── SPEC.md                      ← BA
├── PLAN.md                      ← PM
├── <backend-repo>/
│   ├── DESIGN.md                ← Tech Lead
│   └── tasks/
│       ├── task-1-1.md
│       └── task-1-2.md
├── <web-repo>/
│   ├── DESIGN.md
│   └── tasks/task-2-1.md
└── test-cases/
    └── <module>/
        ├── analysis.md
        ├── plan-tcs.md
        └── test-cases.md
```

---

## MkDocs Integration (optional)

Kit có sẵn templates để render docs thành site:

```bash
cp .claude/templates/mkdocs.yml <DOCS_ROOT>/../mkdocs.yml
cp .claude/templates/docs-index.md <DOCS_ROOT>/index.md

pip install -r .claude/templates/mkdocs-requirements.txt
mkdocs serve   # http://localhost:8000
```

Nav tự sinh từ cấu trúc thư mục qua plugin `awesome-pages` — không cần sửa `mkdocs.yml` khi thêm feature mới.

---

## Stack constraints

```
Database:     PostgreSQL + TypeORM 0.3.x
API:          REST (không GraphQL)
Mobile state: hooks_riverpod 3.x
Web state:    TanStack Query v5 + Redux Toolkit v2
Secrets:      AWS Parameter Store (không .env production)
```
