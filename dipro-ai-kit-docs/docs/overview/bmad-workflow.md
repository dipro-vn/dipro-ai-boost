# BMAD Workflow — Flow tổng thể

**BMAD** (BA → Make → Apply → Deploy) là quy trình 8 phase kiểm soát toàn bộ vòng đời feature, từ khi nhận requirement đến khi deploy production.

---

## Sơ đồ tổng thể

```mermaid
flowchart TB

    subgraph S1["① INPUT & ANALYSIS"]
        INPUT["📥 Input\nPDF · Figma · Backlog · Meeting"]
        BA["🟦 BA Agent"]
        SPEC["📄 SPEC.md"]
        INPUT --> BA --> SPEC
    end

    subgraph S2["② DESIGN (song song)"]
        TLD["🟦 Tech Lead Design"]
        DES["🟨 Designer Agent"]
        QCPIPE["🟪 QC Agent\nanalyze-req → plan-tcs → gen-tcs"]

        DESIGN["📄 DESIGN.md per repo"]
        FIGMA["🎨 Figma URL"]
        TC["📄 test-cases/<module>/"]

        SPEC --> TLD --> DESIGN
        SPEC --> DES --> FIGMA
        SPEC --> QCPIPE --> TC
    end

    subgraph S3["③ PLANNING"]
        TASK["🟦 Tech Lead Tasks"]
        PM["🟦 PM Agent"]
        TASKDOC["📄 tasks/task-*.md"]
        PLAN["📄 PLAN.md"]

        DESIGN --> TASK --> TASKDOC --> PM --> PLAN
    end

    subgraph S4["④ CONTRACT LOCK 🔒"]
        LOCK{"BE + FE + Mobile + PM + QC\nREST + WebSocket + Push"}
    end

    PLAN --> LOCK

    subgraph S5["⑤ BUILD"]
        BE["🟩 Backend\nPhase 1 (DB) → 2 (API)"]
        FE["🟩 Frontend\nPhase 3"]
        MOB["🟩 Mobile\nPhase 3"]

        LOCK --> BE
        BE -->|"copy API Contract"| FE
        BE -->|"copy API Contract"| MOB
    end

    subgraph S6["⑥ QA VERIFY"]
        QA["🟪 QA Agent\nper task"]
        REPORT["📊 QA Report PASS/FAIL"]
        BE --> QA --> REPORT
        FE --> QA
        MOB --> QA
    end

    subgraph S7["⑦ TESTING (song song)"]
        MANUAL["🟪 QC Manual\nexecution + bug report"]
        AUTO["🟪 QC Automation\nPlaywright E2E"]

        REPORT --> MANUAL
        REPORT --> AUTO
    end

    subgraph S8["⑧ DEPLOY 🚀"]
        DEPLOY["STG → PROD"]
    end

    MANUAL --> DEPLOY
    AUTO --> DEPLOY
```

---

## Chi tiết 8 Phases

### Phase 0 — Setup `/init-kit`

**Mục tiêu:** Điền thông tin dự án vào `AGENTS.md` một lần duy nhất.

```bash
claude
/init-kit
```

Agent sẽ hỏi 8 câu:

| Câu hỏi | Ví dụ |
|---------|-------|
| Tên dự án + domain | `ecommerce-japan`, quản lý bán hàng B2B |
| Docs root path | `my-project-docs/docs` |
| Danh sách repo + path + vai trò | backend, frontend, mobile |
| Epic code per repo | E01, E02, E03 |
| Actors/personas | Admin, Customer, Driver |
| Payment gateway | elepay, Alipay |
| Cặp repo dễ nhầm | web-admin vs web-shop |
| Cross-repo features | Payment, Auth JWT |

**Output:** `AGENTS.md` được điền đầy đủ

---

### Phase 1 — Discovery `/create-spec`

**Agent:** BA Agent  
**Input:** Requirement (tự nhiên / Figma URL / Backlog ticket / PDF)  
**Output:** `<DOCS_ROOT>/features/<feature>/SPEC.md`

**SPEC.md bao gồm:**
- Background & Objective
- In Scope / Out of Scope
- Actors & Flows
- Acceptance Criteria (per actor)
- Data Model sơ bộ
- Q&A / Ambiguities

---

### Phase 2 — Design (3 agent chạy song song)

#### 2a. Tech Lead Design `/create-design`

**Output:** `<DOCS_ROOT>/features/<feature>/<repo>/DESIGN.md`

Bao gồm: Architecture decision, API endpoints, Database schema, Component breakdown, Cross-repo dependencies.

#### 2b. QC Pipeline `/test/analyze-req` → `/test/plan-tcs` → `/test/gen-tcs`

**Output:** `<DOCS_ROOT>/features/<feature>/test-cases/<module>/`
- `analysis.md` — Extracted ACs + ambiguities
- `plan-tcs.md` — Strategy per screen, risk levels
- `test-cases.md` — Full manual test cases

#### 2c. Designer `/create-ui-design`

**Output:** Figma frames + URL → điền vào `SPEC.md ## Screens`

---

### Phase 3 — Planning

#### Tech Lead Tasks `/create-tasks`

**Output:** `<DOCS_ROOT>/features/<feature>/<repo>/tasks/task-X-Y.md`

Mỗi task file chứa: Goal, Scope, File list, Steps, Estimate, Dependencies, Definition of Done.

#### PM `/create-plan` + `/create-backlog`

**Output:** `<DOCS_ROOT>/features/<feature>/PLAN.md` + Backlog issues

---

### Phase 4 — Contract Lock 🔒

**Gate bắt buộc** trước khi FE/Mobile bắt đầu build.

!!! danger "Không được skip"
    Tất cả BE + FE + Mobile + PM + QC phải confirm:
    - REST API Contract (method, path, request/response)
    - WebSocket events (nếu có)
    - Push notification payloads (nếu có)

---

### Phase 5 — Build

**Thứ tự bắt buộc:**

```
BE Phase 1 (Migration + Entity)
    ↓
BE Phase 2 (Controller + Service + API Contract table)
    ↓ copy API Contract
FE Phase 3  ──┐  (chạy song song)
Mobile Phase 3─┘
```

!!! info "Memory Update Gate"
    Sau mỗi Dev task, **bắt buộc** cập nhật overview docs tại `<DOCS_ROOT>/<layer>/<repo>/overview/` khi thay đổi endpoint/entity/pattern.

---

### Phase 6 — QA Verify (per task)

**Agent:** QA Agent  
**Trigger:** `"Hãy là QA, verify task: <path/to/task.md>"`

**QA Report:**
- Unit test coverage check
- AC checklist
- PASS → chuyển sang task tiếp
- FAIL → Dev fix loop

---

### Phase 7 — Testing (2 luồng song song)

#### 7a. QC Manual

```bash
/test/generate_test_execution_checklist
/test/gen-bug-report "Mô tả lỗi"
```

#### 7b. QC Automation (Playwright E2E)

```bash
/gen-automation  # từ test-cases.md → Playwright scripts
```

Auto-heal loop: chạy → lỗi → sửa (tối đa 5 vòng)

---

### Phase 8 — Deploy

STG → PROD, sau khi tất cả test PASS.

---

## On-demand Commands

| Command | Khi nào dùng |
|---------|-------------|
| `/test/review-tcs` | Có ≥2 QC review chéo (8 tiêu chí) |
| `/test/export-xlsx <path> web\|app` | Bàn giao Excel cho client |
| `/test/generate_regression_suite` | Sau code change lớn |
| `/create-feature <feature> [build]` | Shortcut chạy toàn pipeline |

---

## Phân quyền theo Phase

| Action | BA | TL | PM | QC | QA | Designer | Dev |
|--------|:--:|:--:|:--:|:--:|:--:|:--------:|:---:|
| Sửa `.md` | ✅ | ✅ | ✅ | ✅ | ✅* | ✅** | ✅ |
| Sửa source code | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Chạy test | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Git commit | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌*** |
| Git push | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

> \* QA chỉ sửa QA Report  
> \*\* Designer chỉ điền Figma link vào `SPEC.md ## Screens`  
> \*\*\* Dev commit chỉ khi user yêu cầu rõ ràng
