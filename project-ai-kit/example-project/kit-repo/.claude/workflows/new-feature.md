# Workflow: New Feature — BMAD Pipeline

Quy trình chuẩn để đưa một feature mới từ yêu cầu đến production.

> **Shortcut:** `/create-feature <feature> [mô tả]` rồi `/create-feature <feature> build` chạy gộp Bước 1→3 và Bước 4→5 bên dưới qua 2 workflow `bmad-plan-phase`/`bmad-build-phase`. Dùng bảng dưới đây khi cần chạy tay từng bước hoặc debug 1 bước cụ thể. Guide chạy automation test (Bước 5, `qc-automation-agent`) → `Automation_Test.md` ở root kit.

---

## Tổng quan pipeline

```
User requirement
      │
      ▼ [ba-agent]
   SPEC.md  ←── /create-spec <feature>
      │
      ▼ [techlead-design-agent + qc-agent + designer-agent song song]
DESIGN.md per repo  ←── /create-design <SPEC.md>
      │
      ▼ [techlead-tasks-agent]
tasks/task-*.md  ←── /create-tasks <feature-folder/>
  Phase 1,2 → template Bước 6 (BE)
  Phase 3   → template Bước 6b (FE/Mobile — có ## API Definition)
      │
      ▼ CONTRACT LOCK ← REST endpoints + WebSocket + Push payload confirm
      │
      ▼ [backend-agent]
  task-1-x (DB migration)
  task-2-x (API endpoint) → output: API Definition table
      │
      ▼ lint + test + coverage của task-2-x xanh
      │
      ▼ copy API Definition vào task-3-x.md + trỏ design-analysis.md
      │
      ┌─────────────────┬──────────────────┐
      │                 │                  │
[frontend-agent]  [frontend-agent]  [mobile-agent]
 task-3-x (repo FE-a) task-3-x (repo FE-b) task-3-x (repo mobile)
 Step1 service     Step1 service    Step1 service
 Step2 hooks       Step2 hooks      Step2 provider
 Step3 wire UI     Step3 wire UI    Step3 wire UI
      │                 │                  │
      └─────────────────┴──────────────────┘
      │
      ▼ Integration check (localhost BE + FE = data thật)
      │
      ▼ [qc-automation-agent]
  E2E automation (Playwright headed) → execution-report.md
      │
      ▼
  Deploy STG → PROD
```

> Chuỗi Build → QC Automation ở trên là logic thật của `.claude/workflows/bmad-build-phase.js`
> (chạy qua `/create-feature <feature> build`) — không phải bước thủ công.

---

## Bước 1 — Phân tích yêu cầu (BA)

**Agent:** `ba-agent`
**Command:** `/create-spec <tên feature>`
**Context cần đọc:**
- `.claude/context/specification.md` — business overview, actors
- `.claude/context/doc-structure.md` — cấu trúc folder
- Các SPEC hiện có trong `<DOCS_ROOT>/features/`

**Output (path duy nhất):** `<DOCS_ROOT>/features/<feature-name>/SPEC.md`

> Single-actor vs cross-repo phân biệt qua section Actors trong SPEC, không qua path.

**Gate:** Không tiếp tục nếu SPEC chưa được PM/BrSE review.

---

## Bước 2 — Thiết kế kỹ thuật (Tech Lead Design)

**Agent:** `techlead-design-agent`
**Command:** `/create-design <path/to/SPEC.md>`
**Context cần đọc:**
- `.claude/context/technical.md` — tech stack, known bugs
- `<DOCS_ROOT>/backend/<backend-repo>/overview/patterns.md`
- `<DOCS_ROOT>/backend/<backend-repo>/overview/erd.md`

**BẮT BUỘC trước khi viết DESIGN:**
```
tilth_deps(path: "<file sẽ thay đổi>")
```

**Output:** `DESIGN.md` per repo (cùng folder với SPEC.md)

---

## Bước 3 — Phân rã tasks (Tech Lead Tasks)

**Agent:** `techlead-tasks-agent`
**Command:** `/create-tasks <path/to/feature-folder/>`
**Phase numbering global:**

| Phase | Nội dung | Repo | Template |
|---|---|---|---|
| 1 | DB migration / schema | repo vai trò backend | Bước 6 (template chung) |
| 2 | Service + API endpoint | repo vai trò backend | Bước 6 (template chung) |
| 3 | Frontend + Mobile (song song) | repo vai trò frontend/mobile | **Bước 6b** (template FE/Mobile) |
| 4 | Integration test | Tất cả | Bước 6 (template chung) |

**Output:** `tasks/task-X-Y.md` per repo

> **Quan trọng:** Task Phase 3 (FE/Mobile) dùng template riêng (Bước 6b trong `techlead-tasks-agent.md`). Template này có sẵn section `## API Definition` chờ BE điền sau khi hoàn thành task-2-X.

---

## CONTRACT LOCK ⚠️ (trước Phase 3)

**Nguồn tham chiếu:** `DESIGN.md ## 3. API Definition` (per repo vai trò backend) — bảng này phải có trước khi sign-off.

Phải confirm đầy đủ trước khi FE/Mobile bắt đầu implement:

- [ ] `DESIGN.md ## 3. API Definition` đã có bảng đủ cột: Method / Endpoint / Auth / Request / Response / Error codes
- [ ] WebSocket events: tên event, payload schema (nếu có)
- [ ] Push notification: payload format, trigger condition (nếu có)
- [ ] FE/Mobile đã đọc và hiểu DESIGN.md — không có câu hỏi chưa giải đáp

**Ai confirm:** Backend dev + Frontend dev + Mobile dev (nếu có) + PM

> Nếu DESIGN.md chưa có `## 3. API Definition` → yêu cầu `techlead-design-agent` bổ sung trước khi lock.

---

## Bước 4 — Implement (Dev)

**Agent theo vai trò repo (xem bảng Ecosystem trong `AGENTS.md`):**
- repo vai trò backend → `backend-agent`
- repo vai trò frontend → `frontend-agent`
- repo vai trò mobile → `mobile-agent`

**Thứ tự bắt buộc:**

```
task-1-x (BE — DB migration)
    ↓
task-2-x (BE — API endpoint)
    ↓ [lint + test + coverage của task-2-x phải xanh trước khi đi tiếp]
    ↓ [output API Definition → copy vào task-3-x trước khi FE bắt đầu]
task-3-x (FE + Mobile, song song):
    Step 1 — Tạo service file  (gọi đúng endpoint trong API Definition)
    Step 2 — Tạo TanStack Query hooks
    Step 3 — Implement UI, wire hooks vào giao diện — đọc design-analysis.md (nếu có) làm nguồn design chính
    ↓ [Integration check: FE-localhost + BE-localhost = data thật trên màn hình]
task-4-x (Integration test)
```

**Sau khi BE xong task-2-x (lint + test + coverage của task đó xanh):**
1. Copy bảng `## API Definition` từ BE output vào section tương ứng trong `task-3-x.md`
2. FE/Mobile task có gọi API → không bắt đầu implement trước khi có API Definition. FE task thuần UI (component, layout, không gọi API) không bị ràng buộc này.
3. Nếu feature có design-analysis.md (output `design-analyst-agent`) → FE/Mobile đọc trước khi implement UI.

> Backend không tự chuyển sang FE/Mobile khi test suite của task-2-x còn đỏ — API Contract chưa ổn định thì FE/Mobile code lại từ đầu.

**Sau mỗi task:** Chạy Memory Update Gate (xem `AGENTS.md`).

---

## Bước 5 — QC Automation

**Agent:** `qc-automation-agent`

Chạy sau khi Build (Bước 4) xong toàn bộ feature: `qc-automation-agent` chạy Playwright
E2E headed mode nếu có repo E2E testing và website DEV đang chạy.

**Output:** E2E automation report (`execution-report.md`)

**Status workflow:**
```
Dev: Open → In Progress → Request Review
Leader: In Review → Testing Request
QC: Testing Request → Resolved (hoặc Reopen nếu fail)
PM/Leader: Resolved → Closed
```

> On-demand (không thuộc pipeline): `/test/generate_test_execution_checklist` sinh
> checklist thủ công trước release, `/test/generate_regression_suite` sinh regression
> suite sau code change — gọi khi cần, không chạy tự động.

---

## Bước 6 — Deploy

1. Deploy STG → smoke test
2. Confirm với PM/client
3. Deploy PROD

**Không deploy thẳng PROD** khi chưa qua STG.

---

## Checklist trước khi đóng feature

- [ ] Tất cả tasks status = Resolved/Closed
- [ ] Test suite + coverage target của mọi task đều xanh
- [ ] E2E automation report đã có (Bước 5)
- [ ] Memory Update Gate đã chạy (api-catalog, erd cập nhật nếu cần)
- [ ] PR approved và merged
- [ ] STG deploy pass
- [ ] PROD deploy pass
