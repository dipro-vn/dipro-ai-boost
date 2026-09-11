# Task Template — Frontend / Mobile (Phase 3)

> **Scope:** Áp dụng cho task Phase 3 — repo có vai trò `frontend` hoặc `mobile`.
> **Dùng ở:** `techlead-tasks-agent` (Bước 6b). Khi Write file `task-3-y.md` trong repo FE/Mobile → Read template này rồi fill placeholder theo Design-Technical.md + Figma URL.
> **Task BE (Phase 1/2/4):** dùng `task-template-be.md` thay vào — KHÔNG dùng template này.

> **3 sub-step BẮT BUỘC** — đảm bảo FE ráp được API vào UI khi chạy localhost.

---

## Template markdown

```markdown
# [FE] [Category] — <Mô tả ngắn gọn>

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
| Phase | 3 — Frontend / Mobile |
| Repo | `<repo-name>` |
| Depends on | task-2-X ← BE API phải xong trước |
| Song song với | task-3-Y (FE khác nếu có) / task-3-Z (Mobile) |
| Estimate | ~Xh |

## Mục tiêu
[1-2 câu: task này implement screen nào, kết quả khi chạy FE-localhost + BE-localhost sẽ thấy gì]

## Context (đọc trước khi code) — Link output các agent thượng nguồn

### 📘 BA-Agent output (đọc đầu tiên — logic + prototype)
- **SPEC.md:** `<DOCS_ROOT>/features/<feature>/SPEC.md`
- **BA Deliverables** (section trong SPEC.md — chứa đủ 5 outputs):
  - Figma Frame 2 — Screen Flow: `<figma-url-frame-2>`
  - HTML Prototype: `<DOCS_ROOT>/features/<feature>/prototype/index.html` _(mở để verify UX trước khi code)_

### 🎨 Designer-Agent output (Giao diện final UI/UX)
- **Screen Code:** `<XX_FEAT_001>` _(lấy từ SPEC.md `## Screens`)_
- **Figma URL (high-fi):** `<path_figma>` _(BẮT BUỘC đọc qua Figma MCP trước khi code)_

### 🏗️ Tech Lead output (technical spec)
- **Design-Technical.md (FE):** `<DOCS_ROOT>/features/<feature>/<fe-repo>/Design-Technical.md`
- **BE task liên quan:** `<task-2-X.md>` ← đọc section **API Definition** để lấy endpoint (CONTRACT LOCK)

### 📂 File liên quan trong codebase
- `<path/to/existing-service>` — xem pattern service file hiện có
- `<path/to/existing-hook>` — xem pattern useQuery hook hiện có

## API Definition (copy từ BE task-2-X)

> Copy từ section **API Definition** trong task BE tương ứng — không tự đoán endpoint.

| Method | Endpoint | Request | Response |
|---|---|---|---|
| GET | `/api/<resource>` | `?page=1&limit=10` | `{ items: [], total }` |
| POST | `/api/<resource>` | `{ field: type }` | `{ id, field }` |

**Base URL:** `import.meta.env.VITE_API_URL` (không hard-code)

## Yêu cầu implement

### Step 1 — Tạo API service file

**File:** `src/services/<feature>Api.ts`

```typescript
// Gọi đúng endpoint trong API Definition bên trên
export const <feature>Api = {
  getList: (params: ListParams): Promise<ListResponse> =>
    apiClient.get('/api/<resource>', { params }),
  create: (data: CreateDto): Promise<XxxResponse> =>
    apiClient.post('/api/<resource>', data),
};
```

### Step 2 — Tạo TanStack Query hooks

**File:** `src/hooks/use<Feature>.ts`

```typescript
export const use<Feature>List = (params: ListParams) =>
  useQuery({
    queryKey: ['<feature>', params],
    queryFn: () => <feature>Api.getList(params),
  });

export const useCreate<Feature> = () =>
  useMutation({
    mutationFn: <feature>Api.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['<feature>'] }),
  });
```

### Step 3 — Implement UI Component (wire hooks vào giao diện)

**File:** `src/pages/<Feature>Page.tsx` hoặc `src/components/<Feature>/<Component>.tsx`

```typescript
// Wire hooks vào component — loading / error / data states đủ cả
const { data, isLoading } = use<Feature>List(params);
const { mutate: create<Feature>, isPending } = useCreate<Feature>();
// Mọi data hiển thị phải đến từ hook — không hard-code, không mock
```

## Unit Tests (BẮT BUỘC)

### Test file: `src/services/<feature>Api.test.ts`

```typescript
// Test service functions với mock HTTP client (msw)
```

### Test file: `src/hooks/use<Feature>.test.ts`

```typescript
// Test hook với QueryClientWrapper + msw mock server
```

**Coverage target:**
| File | Target |
|---|---|
| `<feature>Api.ts` | ≥ 70% |
| `use<Feature>.ts` | ≥ 70% |
| `<Feature>Page.tsx` (critical path) | ≥ 70% |

**Verify:** `npm run test -- --coverage`

## Kiểm tra Integration (BẮT BUỘC trước Request Review)

- [ ] Chạy BE-localhost + FE-localhost kết nối nhau
- [ ] Screen `<XX_FEAT_001>` load được data thật từ API (không mock)
- [ ] Các nút bấm / form submit gọi đúng endpoint trong API Definition
- [ ] Loading state hiển thị khi đang fetch
- [ ] Error state hiển thị khi API lỗi

## Non-Regression Table
| Tính năng | File liên quan | Cách verify |
|---|---|---|
| <feature khác dùng cùng service/hook> | `<path>` | <bước test> |

## Không được làm
- Không hard-code URL endpoint — luôn dùng `import.meta.env.VITE_API_URL`
- Không mock data trong production code (chỉ mock trong test)
- Không tự thay đổi API Definition — nếu BE endpoint sai thì báo BE fix trước
- Không sửa file ngoài scope (entity, migration, BE service)

## Definition of Done
- [ ] Step 1: Service file tạo xong, gọi đúng endpoint
- [ ] Step 2: Hooks tạo xong, wrap đúng service functions
- [ ] Step 3: UI component wire hooks, hiển thị data / loading / error
- [ ] Build pass (`npm run build`)
- [ ] Lint pass (`npm run lint`)
- [ ] Type-check pass (`npm run type-check`)
- [ ] Unit Tests pass — coverage đạt target
- [ ] **Integration check pass** — localhost kết nối BE, data hiển thị đúng
- [ ] Non-Regression verify đủ
- [ ] Actual Hour cập nhật
- [ ] Status → `Done` (Assignee) → sau đó chuyển `Reviewing` + tạo subtask cho reviewer nếu cần (§I.6 backlog-workflow.md)
```

---

## Unit Test frameworks per stack (FE / Mobile)

| Vai trò | Framework | Pattern |
|---|---|---|
| `frontend` (React) | Jest + React Testing Library | `jest.fn()`, `msw` |
| `mobile` (Flutter) | Flutter test (`flutter_test`) | `MockClient`, `ProviderContainer` |

**Coverage targets (tối thiểu):**

| Module | Line Coverage |
|---|---|
| React Component (critical path) | ≥ 70% |
| Flutter Provider / Service | ≥ 75% |

**Verify commands:**
```bash
# React
npm run test -- --coverage <file>

# Flutter
flutter test <file>
```
