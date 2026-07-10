# Bắt đầu nhanh

---

## Yêu cầu hệ thống

- **Node.js** ≥ 18 (khuyến nghị dùng `nvm`)
- **Claude Code CLI** (hoặc VS Code / JetBrains extension / Claude Desktop app)
- **Git**
- **Python 3** (nếu dùng `/export-xlsx`)

---

## Bước 1: Cài Claude Code CLI

```bash
# Cài global
npm install -g @anthropic-ai/claude-code

# Kiểm tra
claude --version

# Đăng nhập lần đầu (mở browser)
claude
```

---

## Bước 2: Chọn Kit phù hợp

| Bạn là ai? | Kit cần dùng |
|-----------|-------------|
| PM / BA / Tech Lead | project-ai-kit |
| Backend Dev (NestJS) | backend-kit |
| Frontend Dev (React) | fe-kit |
| Mobile Dev (Flutter/RN) | mobile-ai-kit |
| BrSE | brse-ai-kit |
| QC Engineer | qc-kit-agent |
| Toàn team (dự án mới) | project-ai-kit (tất cả kits đều có trong đây) |

---

## Bước 3: Setup kit vào dự án

=== "project-ai-kit (dự án mới)"

    ```bash
    mkdir my-project && cd my-project
    git init

    # Copy kit
    cp -r /path/to/dipro-ai-kit/project-ai-kit/.claude .
    cp -r /path/to/dipro-ai-kit/project-ai-kit/template .
    cp /path/to/dipro-ai-kit/project-ai-kit/{CLAUDE.md,POLICIES.md,AGENTS.md} .

    # Mở Claude Code và chạy setup
    claude
    /init-kit
    ```

=== "backend-kit"

    ```bash
    cd my-nestjs-project
    cp -r /path/to/dipro-ai-kit/backend-kit/.claude .

    claude
    # Bắt đầu với task đầu tiên
    /new-feature "Tên feature cần làm"
    ```

=== "fe-kit"

    ```bash
    cd my-react-project
    cp -r /path/to/dipro-ai-kit/fe-kit/.claude .

    claude
    /new-feature "Trang quản lý đơn hàng"
    ```

=== "mobile-ai-kit"

    ```bash
    cd my-mobile-project

    # Thêm dipro-ai-kit như submodule
    git submodule add -b main git@github.com:dipro-vn/dipro-ai-kit.git tools/dipro-ai-kit
    git submodule update --init --recursive

    # Tạo symlinks
    mkdir -p .claude
    ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/CLAUDE.md .claude/CLAUDE.md
    ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/settings.json .claude/settings.json
    ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/rules .claude/rules
    ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/workflows .claude/workflows

    claude
    # Mô tả task → workflow tự chọn
    ```

=== "qc-kit-agent"

    ```bash
    cd my-project
    cp -r /path/to/dipro-ai-kit/qc-kit-agent/.claude .

    # Cài Python dependencies (cho /export-xlsx)
    pip install openpyxl xlwt

    claude
    /analyze-req docs/features/login/SPEC.md
    ```

---

## Bước 4: Test kit hoạt động

Sau khi setup, mở Claude Code và thử 1 command đơn giản:

```bash
claude

# project-ai-kit
> /create-spec "Tính năng đăng nhập bằng email"

# backend-kit
> /code-review

# fe-kit
> /code-review

# qc-kit
> /analyze-req SPEC.md
```

---

## Lệnh Claude Code cơ bản

| Lệnh | Tác dụng |
|------|---------|
| `claude` | Mở session interactive tại thư mục hiện tại |
| `/<command>` | Chạy slash command — vd: `/init-kit`, `/create-spec` |
| Natural language | Mô tả task tự nhiên — vd: "hãy là BA, viết SPEC cho login" |
| `/help` | Xem help |
| `Ctrl+D` hoặc `/exit` | Thoát session |

---

## Cấu trúc thư mục dự án sau khi setup

```
my-project/
├── CLAUDE.md              ← Kit entrypoint (load policies + agents)
├── POLICIES.md            ← AI behavior rules
├── AGENTS.md              ← Project ecosystem (điền qua /init-kit)
├── template/              ← Excel templates QC
├── .claude/
│   ├── agents/
│   ├── commands/
│   ├── skills/
│   ├── context/
│   ├── rules/
│   ├── scripts/
│   └── workflows/
└── my-project-docs/       ← Docs root (SPEC/DESIGN/PLAN)
    └── docs/
        └── features/
            └── <feature>/
```

---

## Bước tiếp theo

- [Setup dự án mới đầy đủ](new-project-setup.md) — Hướng dẫn chi tiết A-Z
- [Chọn Kit phù hợp](kit-selection.md) — So sánh và chọn đúng kit cho task
- [BMAD Workflow](../overview/bmad-workflow.md) — Hiểu flow 8 phases
