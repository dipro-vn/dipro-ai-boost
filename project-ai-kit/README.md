# project-ai-kit — Template BMAD Agent Kit

> Bộ khung multi-agent AI (BA → Tech Lead → PM → Dev → QC → QA → Designer) theo mô hình BMAD. Pull kit này vào 1 dự án mới, bỏ repo source code vào đúng chỗ, chạy 1 lệnh setup, là có ngay bộ agent/command/skill hoạt động cho toàn bộ vòng đời feature (SPEC → DESIGN → task → implement → QA → deploy).

**Stack mặc định kit:** NestJS + PostgreSQL (backend) · React 19 + Redux Toolkit v2 + TanStack Query v5 (web frontend) · Flutter + Riverpod (mobile) · REST API. Dự án dùng đúng stack này sẽ tận dụng được gần như toàn bộ skill kỹ thuật có sẵn mà không cần sửa gì. Dự án dùng stack khác vẫn dùng được phần workflow/persona (BA/Tech Lead/PM/QC/QA), nhưng nên thay các skill trong `.claude/skills/{nestjs-best-practices,react-expert,flutter-review,postgresql,redis-development}/` bằng skill tương ứng với stack thật.

---

## Quy trình từ A → Z

### Bước 1 — Chuẩn bị thư mục dự án mới

```bash
mkdir <ten-du-an> && cd <ten-du-an>
git init   # nếu chưa có git repo
```

### Bước 2 — Copy kit vào dự án

```bash
# Từ thư mục chứa project-ai-kit (đổi <path-to-kit> cho đúng)
cp -r <path-to-kit>/project-ai-kit/.claude ./.claude
cp <path-to-kit>/project-ai-kit/CLAUDE.md <path-to-kit>/project-ai-kit/POLICIES.md <path-to-kit>/project-ai-kit/AGENTS.md ./
```

Sau bước này, dự án mới có:

```
<ten-du-an>/
├── CLAUDE.md          ← always-loaded, chỉ import 2 file dưới
├── POLICIES.md         ← AI behavior policy chung (không sửa trừ khi cần đổi rule tổ chức)
├── AGENTS.md           ← project rules — CHƯA điền, sẽ điền ở Bước 4
└── .claude/
    ├── agents/ commands/ skills/ context/ rules/ workflows/ settings.json
```

### Bước 3 — Bỏ repo source code vào

Kit **không giả định số lượng hay tên repo cố định** — 1 repo (monorepo) hay N repo (backend + nhiều web + mobile) đều được. Có 2 cách tổ chức, chọn 1:

**Cách A — Nhiều repo con nằm cùng cấp trong dự án** (khuyến nghị nếu có backend + nhiều frontend + mobile):

```
<ten-du-an>/
├── CLAUDE.md / POLICIES.md / AGENTS.md / .claude/    ← kit (Bước 2)
├── <ten-du-an>-repository/       ← thư mục chứa toàn bộ source code
│   ├── <backend-repo>/           ← git clone repo backend vào đây
│   ├── <web-repo-a>/             ← git clone repo web #1 vào đây
│   ├── <web-repo-b>/             ← git clone repo web #2 vào đây (nếu có)
│   └── <mobile-repo>/            ← git clone repo mobile vào đây (nếu có)
└── <ten-du-an>-docs/             ← (optional) repo docs riêng, xem Bước 4 câu 2
    └── docs/features/
```

**Cách B — Kit nằm ngay trong 1 repo duy nhất** (phù hợp dự án nhỏ/monorepo):

```
<ten-du-an>/                       ← chính là git repo source code
├── CLAUDE.md / POLICIES.md / AGENTS.md / .claude/    ← kit (Bước 2)
├── src/ ...                       ← source code dự án
└── docs/features/                 ← docs ngay trong repo, không cần repo riêng
```

`git clone` (hoặc `git submodule add`) từng repo vào đúng vị trí đã chọn — dùng đường dẫn tương đối này khi trả lời câu hỏi ở Bước 4.

### Bước 4 — Chạy setup 1 lần: `/init-kit`

Mở Claude Code tại thư mục `<ten-du-an>`, chạy:

```
/init-kit
```

(hoặc nói tự nhiên: "hãy chạy init kit cho dự án này")

`init-agent` sẽ hỏi ~8 câu — **trả lời dựa trên cấu trúc thư mục đã tạo ở Bước 3**:

1. Tên dự án + mô tả domain nghiệp vụ 1-2 câu
2. Docs root — path thật tới nơi chứa SPEC/DESIGN/PLAN (ví dụ `<ten-du-an>-docs/docs` nếu dùng Cách A, hoặc `docs` nếu dùng Cách B)
3. Danh sách repo: tên, **đường dẫn tương đối thật** (ví dụ `<ten-du-an>-repository/<backend-repo>`), vai trò (`backend`/`frontend`/`mobile`/`other`), stack (Enter để dùng mặc định kit)
4. Epic code cho mỗi repo (tự đặt hoặc để agent tự đánh số)
5. Danh sách actor/persona nghiệp vụ (ai dùng hệ thống, dùng repo nào)
6. Payment/integration đặc thù (nếu có)
7. Cặp repo/khái niệm dễ nhầm lẫn cần lưu ý
8. Feature cross-repo nào chắc chắn sẽ có (optional)

Agent tự điền `AGENTS.md`, `.claude/context/specification.md`, `.claude/context/technical.md`, `.claude/rules/project-structure.md`, `.claude/rules/stack-constraints.md`.

Yêu cầu môi trường (tuỳ chọn nhưng khuyến nghị — đã khai trong `.claude/settings.json`):
- **tilth MCP** — code intelligence (search/read/deps) thay cho grep/cat/find thủ công. Không có tilth thì sửa `agents/*.md` sang `Read`/`Glob`/`Grep` chuẩn.
- **Figma MCP** — cần cho `designer-agent`, `qc-automation-agent`.
- **Backlog MCP** (`@nulab/backlog-mcp-server`) — cần cho `pm-agent` nếu track issue trên Backlog; điền `BACKLOG_DOMAIN`/`BACKLOG_API_KEY` vào `.claude/settings.json`. Không dùng thì bỏ qua.

### Bước 5 — Kiểm tra lại kết quả init

Mở `AGENTS.md` → xác nhận bảng Ecosystem/Actors đã điền đúng đường dẫn repo thật (Bước 3). Sai chỗ nào thì sửa tay hoặc chạy lại `/init-kit` để bổ sung.

### Bước 5b — (optional) Setup MkDocs site để duyệt docs

Kit có sẵn template MkDocs để render `<DOCS_ROOT>/features/<feature>/` (SPEC/DESIGN/PLAN/tasks) thành 1 site duyệt được bằng browser — không cần sửa `mkdocs.yml` mỗi khi thêm feature mới (nav tự sinh từ cấu trúc thư mục qua plugin `awesome-pages`).

```bash
# Copy 2 file template vào ĐÚNG cấp với docs_dir (thư mục chứa "docs/"):
# - Cách A (docs repo riêng): root <ten-du-an>-docs/
# - Cách B (docs ngay trong repo): root <ten-du-an>/
cp .claude/templates/mkdocs.yml <đích>/mkdocs.yml
mkdir -p <đích>/docs
cp .claude/templates/docs-index.md <đích>/docs/index.md
```

`/init-kit` (Bước 4) tự điền `<TEN_DU_AN>` trong `mkdocs.yml`/`docs/index.md` nếu 2 file này đã tồn tại tại thời điểm chạy — nếu chưa, tự sửa placeholder `<TEN_DU_AN>` bằng tay.

Cài dependency và chạy site:

```bash
pip install -r .claude/templates/mkdocs-requirements.txt
mkdocs serve   # mở http://localhost:8000
```

### Bước 6 — Bắt đầu vòng đời feature đầu tiên

```
/create-spec <tên feature>
```

hoặc: "hãy là BA, làm SPEC cho \<feature\>". Từ đây pipeline BMAD tự dẫn dắt qua "Bước tiếp theo" ở cuối mỗi output — không cần nhớ thứ tự lệnh:

```
/create-spec        (BA)         → SPEC.md
/create-design       (Tech Lead)  → DESIGN.md per repo         ┐ chạy song song
/create-ui-design     (Designer)   → Figma frames + URL         ┤ (2b, 2c)
/test/generate_manual_testcases_rbt (QC) → test cases           ┘
/create-tasks        (Tech Lead)  → tasks/task-*.md
/create-plan         (PM)         → PLAN.md
"Hãy là Backend/Frontend/Mobile Developer, implement task: <task-x-y.md>"
"Hãy là QA, verify task: <task-x-y.md>"
/test/generate_test_execution_checklist (QC) → trước khi deploy
```

Chi tiết đầy đủ pipeline (thứ tự, Contract Lock, Memory Update Gate) → `AGENTS.md` section `<bmad_workflow>` và `.claude/workflows/new-feature.md`.

---

## Cấu trúc kit

```
project-ai-kit/
├── CLAUDE.md, POLICIES.md, AGENTS.md   ← root docs, always-loaded qua CLAUDE.md
└── .claude/
    ├── agents/       ← 12 persona (BMAD core + init-agent)
    ├── commands/     ← slash command, thin entry point → agent tương ứng
    ├── skills/       ← technical + process skills, load on-demand
    ├── context/      ← business/technical memory — phần lớn RỖNG, điền dần qua BA/PM/init-agent
    ├── rules/        ← coding-style, security, git-workflow, stack-constraints...
    ├── workflows/    ← BMAD pipeline reference, db-connect templates
    └── templates/    ← mkdocs.yml + docs-index.md + mkdocs-requirements.txt (Bước 5b, optional)
```

**Nguyên tắc cốt lõi** (chi tiết trong `POLICIES.md`): không đoán mò · đọc trước hành động sau · stateless (mọi context đọc từ `.md`) · tool-first (tilth thay grep/cat/find) · blast radius check trước khi đổi public interface · phân quyền persona nghiêm ngặt (chỉ Dev sửa source code).

## Khi dự án phát triển

- Phát hiện gotcha mới (2 repo dễ nhầm, convention riêng...) → thêm vào `AGENTS.md` section `<core_rules>` / `<red_line_rules>`.
- Pattern code mới → cập nhật `<DOCS_ROOT>/<layer>/<repo>/overview/patterns.md` theo Memory Update Gate (xem `AGENTS.md`).
- Thêm repo mới vào dự án → chạy lại `/init-kit`, chọn "thêm repo mới" khi được hỏi.
- Feature/domain nghiệp vụ phức tạp cần business-flow index riêng → tham khảo pattern ở `.claude/context/business-flows/README.md` (optional, chỉ cần khi dự án có nhiều domain nghiệp vụ tách biệt).
</content>
