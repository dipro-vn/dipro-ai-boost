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
      ▼ copy API Definition vào task-3-x.md
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
      ▼ [qa-agent]
  QA Report  ←── verify AC + non-regression
      │
      ▼
  Deploy STG → PROD
```

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
    ↓ [BE output API Definition → copy vào task-3-x trước khi FE bắt đầu]
task-3-x (FE + Mobile, song song):
    Step 1 — Tạo service file  (gọi đúng endpoint trong API Definition)
    Step 2 — Tạo TanStack Query hooks
    Step 3 — Implement UI, wire hooks vào giao diện
    ↓ [Integration check: FE-localhost + BE-localhost = data thật trên màn hình]
task-4-x (Integration test)
```

**Sau khi BE xong task-2-x:**
1. Copy bảng `## API Definition` từ BE output vào section tương ứng trong `task-3-x.md`
2. FE/Mobile task có gọi API → không bắt đầu implement trước khi có API Definition. FE task thuần UI (component, layout, không gọi API) không bị ràng buộc này.

**Sau mỗi task:** Chạy Memory Update Gate (xem `AGENTS.md`).

---

## Bước 5 — QA Verification

**Agent:** `qa-agent`

Với mỗi task đã implement:
1. Chạy test suite (`npm run test`, `flutter test`)
2. Validate từng AC trong SPEC.md
3. Verify Non-Regression table trong task file

**Status workflow:**
```
Dev: Open → In Progress → Request Review
Leader: In Review → Testing Request
QA: Testing Request → Resolved (hoặc Reopen nếu fail)
PM/Leader: Resolved → Closed
```

---

## Bước 6 — Deploy

1. Deploy STG → smoke test
2. Confirm với PM/client
3. Deploy PROD

**Không deploy thẳng PROD** khi chưa qua STG.

---

## Checklist trước khi đóng feature

- [ ] Tất cả tasks status = Resolved/Closed
- [ ] QA sign-off
- [ ] Memory Update Gate đã chạy (api-catalog, erd cập nhật nếu cần)
- [ ] PR approved và merged
- [ ] STG deploy pass
- [ ] PROD deploy pass
