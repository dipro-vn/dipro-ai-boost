# Project Structure

## Repos (Red Line Rules)

_(điền qua `/init-kit` — đồng bộ với bảng Ecosystem trong `AGENTS.md`)_

| Repo | Epic | Trách nhiệm | Không được làm |
|---|---|---|---|
| _(tên repo)_ | _(epic code)_ | _(mô tả)_ | _(business logic của repo khác)_ |

> Luôn xác nhận đúng repo trước khi code — nhầm domain giữa 2 repo tương tự là lỗi phổ biến nhất trong dự án nhiều repo.

## NestJS Module Structure

```
src/modules/<feature>/
├── <feature>.module.ts
├── <feature>.controller.ts     ← HTTP layer only
├── <feature>.service.ts        ← Business logic
├── entities/<feature>.entity.ts
├── dto/
│   ├── create-<feature>.dto.ts
│   └── list-<feature>.dto.ts
└── <feature>.service.spec.ts
```

## React Project Structure

```
src/
├── pages/          ← Route-level components (1 file = 1 route)
├── components/     ← Shared, reusable UI components
├── hooks/          ← Custom hooks (use<Feature>.ts)
├── store/          ← Redux slices (client state only)
├── services/       ← API call functions
└── utils/          ← Pure utility functions
```

## Doc Structure (BMAD)

> Path duy nhất cho mọi feature — `<DOCS_ROOT>/features/<feature-name>/`. Single-actor (1 repo) hay cross-repo (N repos) chỉ khác nhau ở số subfolder repo bên trong.

```
<DOCS_ROOT>/features/<feature>/
├── SPEC.md                  ← BA (11 sections, ## BA Deliverables liệt kê cả 6 output)
├── prototype/index.html     ← BA (Output 4 — mở bằng `open`, không cần build)
├── <backend-repo>/
│   ├── DESIGN.md            ← Tech Lead
│   └── tasks/task-X-Y.md
├── <web-repo-a>/            ← nếu repo này liên quan
│   ├── DESIGN.md
│   └── tasks/task-X-Y.md
├── <web-repo-b>/            ← nếu repo này liên quan
└── <mobile-repo>/           ← nếu Mobile liên quan
```

## Tilth — Code Analysis Tool

Luôn dùng tilth MCP thay vì bash grep/find/cat:
- `tilth_search` → tìm symbol, definition, usage
- `tilth_read` → đọc file với smart outline
- `tilth_files` → list file theo pattern
- `tilth_deps` → blast radius trước khi đổi interface public

## AI Agent Policy — BẮT BUỘC

**Không tự suy nghĩ, không tự đoán, không search bừa:**

1. **Đọc đúng file được chỉ định** — mỗi agent/command có danh sách file phải đọc ở Bước 1. Không bỏ qua, không đọc thêm file ngoài danh sách đó trừ khi có lý do rõ ràng từ task.

2. **Không tự suy nghĩ khi thiếu thông tin** — nếu context chưa đủ để ra quyết định, hỏi user. Không tự điền giả định vào SPEC/DESIGN/task.

3. **Không search toàn bộ codebase** — chỉ `tilth_search` khi cần xác nhận symbol/file cụ thể liên quan đến task. Không scan rộng để "khám phá" codebase.

4. **Context files chỉ đọc khi đúng role** — xem cột "Ai đọc" trong bảng Context của AGENTS.md. Agent không liên quan không cần đọc.

5. **Không generate code khi chưa đọc đủ context** — thứ tự bắt buộc: đọc docs → xác nhận source → mới generate.
