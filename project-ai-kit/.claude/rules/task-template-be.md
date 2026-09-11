# Task Template — Backend / Generic

> **Scope:** Áp dụng cho task Phase 1 (DB migration), Phase 2 (Service + API), Phase 4 (Integration test) — repo có vai trò `backend`.
> **Dùng ở:** `techlead-tasks-agent` (Bước 6). Khi Write file `task-x-y.md` trong repo backend → Read template này rồi fill placeholder theo Design-Technical.md.
> **FE/Mobile task Phase 3:** dùng `task-template-fe.md` thay vào — KHÔNG dùng template này.

---

## Template markdown

```markdown
# [ROLE] [Category] — <Mô tả ngắn gọn>

## Backlog Info
- **Issue Type:** Task
- **Category:** <Category theo Ecosystem AGENTS.md>
- **Parent Issue:** <User Story title hoặc Epic ID>
- **Version:** <release/version của dự án>
- **Milestone:** <Released xxx>
- **Estimate Hour:** Xh
- **Actual Hour:** — _(điền khi Resolved)_
- **Status:** Open

## Metadata
| Thuộc tính | Giá trị |
|---|---|
| Phase | X — <tên phase> |
| Repo | `<repo-name>` |
| Depends on | task-Y-Z / none |
| Song song với | task-A-B / none |
| Estimate | ~Xh |

## Mục tiêu
[1-2 câu: task này làm gì và tại sao cần]

## Context (đọc trước khi code) — Link output các agent thượng nguồn

### 📘 BA-Agent output (đọc đầu tiên — logic + prototype)
- **SPEC.md:** `<DOCS_ROOT>/features/<feature>/SPEC.md`
- **BA Deliverables** (section trong SPEC.md — chứa đủ 5 outputs):
  - Figma Frame 1 — Flow Tổng Quan: `<figma-url-frame-1>`
  - Figma Frame 2 — Screen Flow: `<figma-url-frame-2>`
  - Figma Frame 3 — Screens + Items + Error Scenarios: `<figma-url-frame-3>`
  - HTML Prototype: `<DOCS_ROOT>/features/<feature>/prototype/index.html`

### 🎨 Designer-Agent output (Giao diện final UI/UX)
- **Screen Code:** `<XX_FEAT_001>` _(lấy từ SPEC.md `## Screens`)_
- **Figma URL (high-fi):** `<path_figma>` _(lấy từ SPEC.md `## Screens` cột Figma Link — FE/Mobile agent gọi MCP đọc trực tiếp)_

### 🏗️ Tech Lead output (technical spec)
- **Design-Technical.md:** `<DOCS_ROOT>/features/<feature>/<repo>/Design-Technical.md`

### 📂 File liên quan trong codebase
- `<path/to/file>` — xem pattern inject dependency / service structure
- `<path/to/entity>` — xem column conventions

## Yêu cầu implement

### Tạo / Sửa: `<đường dẫn chính xác>`

```typescript
// Pseudocode / code snippet cụ thể
```

## Unit Tests (BẮT BUỘC)

### Test file: `<path>.spec.ts`

```typescript
describe('<ClassName>', () => {
  let service: <ClassName>;
  let mockDep: jest.Mocked<<Dependency>>;

  beforeEach(async () => {
    const module = await Test.createTestingModule({
      providers: [<ClassName>, { provide: <Dependency>, useValue: createMock<<Dependency>>() }],
    }).compile();
    service = module.get<<ClassName>>(<ClassName>);
    mockDep = module.get(<Dependency>);
  });

  it('should <mô tả behavior>', async () => {
    // Arrange → Act → Assert — BẮT BUỘC có ít nhất 1 expect()
  });
});
```

**Coverage target:**
| File | Target |
|---|---|
| `*.service.ts` | ≥ 80% |
| `*.controller.ts` | ≥ 70% |

**Verify:** `npm run test -- <file>`

## API Definition _(chỉ điền cho task Phase 2 — API endpoint; bỏ section này nếu task Phase 1)_

> Điền sau khi implement xong. FE/Mobile sẽ copy bảng này vào task-3-x trước khi bắt đầu code.

| Method | Endpoint | Request | Response |
|---|---|---|---|
| GET | `/api/<resource>` | `?page=1&limit=10` | `{ items: [], total }` |
| POST | `/api/<resource>` | `{ field: type }` | `{ id, field }` |

**Base URL:** `VITE_API_URL` (env var — không hard-code)
**Auth:** Bearer JWT (trừ khi endpoint public)

## Non-Regression Table
| Tính năng | File liên quan | Cách verify |
|---|---|---|
| <feature đang dùng entity/service này> | `<path>` | <bước test> |

## Không được làm
- Không sửa `<file khác>` — ngoài scope, sẽ làm ở task khác
- Không thay đổi response format API đang có — consumer đang dùng
- Không refactor code lân cận dù thấy cần cải thiện

## Definition of Done
- [ ] Build pass (`npm run build`)
- [ ] Lint pass (`npm run lint`)
- [ ] Unit Tests pass — coverage đạt target
- [ ] Non-Regression verify đủ
- [ ] **API Definition điền đủ** _(Phase 2 only)_ — FE/Mobile có thể bắt đầu task-3-x
- [ ] Actual Hour cập nhật
- [ ] Status → `Done` (Assignee) → sau đó chuyển `Reviewing` + tạo subtask cho reviewer nếu cần (§I.6 backlog-workflow.md)
```

---

## Unit Test frameworks per stack (BE)

| Vai trò | Framework | Pattern |
|---|---|---|
| `backend` (NestJS) | Jest + `@nestjs/testing` + `@golevelup/ts-jest` | `createMock<T>()`, `jest.fn()` |

**Coverage targets (tối thiểu):**

| Module | Line Coverage |
|---|---|
| NestJS Service / Business Logic | ≥ 80% |
| NestJS Controller | ≥ 70% |

**Verify commands:**
```bash
npm run test -- <file>
npm run test:cov
```
