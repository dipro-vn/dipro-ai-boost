# Mobile AI Kit

Bộ cấu hình Claude Code (rules, workflows, skills, MCP) dùng chung cho các dự án **Flutter** và **React Native** của team.

- **Repo:** `dipro-vn/dipro-ai-kit`
- **Branch của kit này:** `main`

> **Lưu ý cấu trúc:** `dipro-ai-kit` là **monorepo** chứa 3 kit ngang cấp — `mobile-ai-kit/` (kit này), `project-ai-kit/`, `qc-kit-agent/`. Khi thêm cả repo qua git submodule, bạn nhận về cả 3 — nội dung kit mobile thực sự nằm **lồng thêm 1 cấp** trong thư mục submodule (`tools/dipro-ai-kit/mobile-ai-kit/...`), không nằm ngay tại root submodule. Các lệnh bên dưới đã tính sẵn cấp này — đừng bỏ bớt.

Kit được phân phối vào project đích qua **git submodule**, sau đó **symlink** các file cấu hình vào `.claude/` thật của project để Claude Code đọc được. Ưu điểm của symlink: khi kit cập nhật (rule mới, workflow mới...), mọi project dùng chung chỉ cần `git submodule update` là nhận được ngay, không phải copy tay từng project.

---

## 0. Yêu cầu trước khi bắt đầu

- Đã cài [Claude Code](https://claude.com/claude-code).
- Có quyền truy cập SSH vào `git@github.com:dipro-vn/dipro-ai-kit.git` (repo private).
- Project đích đã là 1 git repo (đã `git init` + có commit đầu tiên).

---

## 1. Thêm kit vào project qua git submodule

Chạy tại root của project đích (Flutter hoặc React Native):

```bash
git submodule add -b main git@github.com:dipro-vn/dipro-ai-kit.git tools/dipro-ai-kit
git submodule update --init --remote tools/dipro-ai-kit
```

Submodule được đặt tại `tools/dipro-ai-kit` (tách biệt với `.claude/` thật của project) để tránh xung đột với config cá nhân (`.claude/settings.local.json`) đã có sẵn trong project. Đặt tên theo đúng tên repo (`dipro-ai-kit`) vì submodule chứa cả monorepo, không chỉ riêng mobile kit.

Vì `dipro-ai-kit` là monorepo (xem lưu ý ở đầu file), sau lệnh trên cây thư mục sẽ là:

```
tools/dipro-ai-kit/             # root submodule = toàn bộ repo dipro-ai-kit
├── mobile-ai-kit/              # ← kit thật sự dùng ở các bước dưới
├── project-ai-kit/             # kit khác trong repo, không dùng ở đây
└── qc-kit-agent/                # kit khác trong repo, không dùng ở đây
```

Commit `.gitmodules` và pointer của submodule:

```bash
git add .gitmodules tools/dipro-ai-kit
git commit -m "chore: add dipro-ai-kit submodule"
```

---

## 2. Symlink cấu hình vào `.claude/` của project

Các file/thư mục dưới đây nên **luôn đồng bộ** với kit (không customize riêng) → symlink thẳng vào submodule:

```bash
mkdir -p .claude
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/CLAUDE.md .claude/CLAUDE.md
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/settings.json .claude/settings.json
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/rules .claude/rules
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/workflows .claude/workflows
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/tools .claude/tools
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.mcp.json .mcp.json
```

Commit các symlink này (git lưu symlink như file thường, không lưu nội dung target):

```bash
git add .claude/CLAUDE.md .claude/settings.json .claude/rules .claude/workflows .claude/tools .mcp.json
git commit -m "chore: link mobile-ai-kit config into .claude/"
```

**Không symlink** — giữ là file thật, riêng của từng máy/dev:

- `.claude/settings.local.json` — config cá nhân, thêm vào `.gitignore` của project (giống kit gốc).
- Các secret: `.env*`, keystore, `google-services.json`... — không bao giờ đưa vào kit hay commit (xem [`SECURITY.md`](.claude/rules/SECURITY.md)).

### Cần customize riêng cho project? (CLAUDE.md, rules)

Guideline của kit (mục 3 bên dưới) cho phép — thậm chí khuyến khích — sửa `CLAUDE.md` hoặc bớt/thêm rule tuỳ đặc thù project. Vì các file này đang là **symlink**, sửa trực tiếp nghĩa là sửa vào submodule (ảnh hưởng chung mọi project khác dùng kit). Nếu cần customize riêng cho project:

```bash
# Ví dụ: tách CLAUDE.md ra khỏi symlink để sửa riêng cho project này
unlink .claude/CLAUDE.md
cp tools/dipro-ai-kit/mobile-ai-kit/.claude/CLAUDE.md .claude/CLAUDE.md
```

File sau khi tách sẽ **không tự nhận update** từ kit nữa — chỉ tách khi thực sự cần diverge.

---

## 3. Setup theo guideline của kit

Sau khi symlink xong, làm theo đúng thứ tự 3 bước trong `tools/dipro-ai-kit/mobile-ai-kit/guideline/`:

1. [`step1-install-source-map.md`](guideline/step1-install-source-map.md) — cài source-map tool (Codegraph hoặc Understand-Anything) để AI hiểu source code.
2. [`step2-setup-mcp.md`](guideline/step2-setup-mcp.md) — cấu hình MCP (Figma, NotebookLM). Điền `FIGMA_API_KEY` thật vào `.mcp.json` — **không commit key thật lên git** (nếu cần override riêng, dùng `.claude/settings.local.json` hoặc biến môi trường, không sửa trực tiếp file symlink).
3. [`step3-custom.md`](guideline/step3-custom.md) — thêm skill phù hợp dự án (`npx skills add ...`) và điều chỉnh rule/workflow nếu cần (xem cách tách symlink ở mục 2).

---

## 4. Cập nhật kit khi có phiên bản mới

```bash
git submodule update --remote --merge tools/dipro-ai-kit
git add tools/dipro-ai-kit
git commit -m "chore: update dipro-ai-kit submodule"
```

Vì `.claude/CLAUDE.md`, `.claude/rules`, `.claude/workflows` là symlink trỏ vào submodule, project sẽ tự nhận thay đổi ngay sau lệnh trên — trừ những file đã bị `unlink` để customize riêng (mục 2).

---

## 5. Kiểm tra tích hợp thành công

- [ ] `ls -la .claude/` — các symlink trỏ đúng vào `tools/dipro-ai-kit/mobile-ai-kit/...`, không bị broken.
- [ ] Mở Claude Code tại root project, kiểm tra Claude đọc được `CLAUDE.md` (Claude tự áp workflow/rule tương ứng khi giao task).
- [ ] `.claude/settings.local.json` đã có trong `.gitignore` của project.
- [ ] Đã điền `FIGMA_API_KEY` thật (không commit) nếu dùng MCP Figma.
- [ ] Đã chạy source-map tool (`codegraph init` hoặc `/understand`) theo bước 1.

---

## Cấu trúc kit (tham khảo)

`tools/dipro-ai-kit/` (root submodule) là cả repo `dipro-ai-kit` — kit mobile nằm ở thư mục con `mobile-ai-kit/` bên trong:

```
tools/dipro-ai-kit/               # root submodule = repo dipro-ai-kit (monorepo)
├── mobile-ai-kit/                # ← kit này, mọi path ở các mục trên đều trỏ vào đây
│   ├── .claude/
│   │   ├── CLAUDE.md          # entrypoint: security, workflow dispatcher, code rules
│   │   ├── settings.json      # permission allow/ask/deny + hooks (format-on-save, codegraph hook)
│   │   ├── rules/              # SECURITY.md, POLICY.md, RELIABILITY.md, planning-spec, skill-selection-spec, project-base/*
│   │   ├── workflows/          # fix-bug, new-feature, refactor, performance, investigate, default
│   │   └── tools/               # docs cho codegraph, understand-anything
│   ├── .agents/skills/          # skill đã cài sẵn (find-skills, flutter-expert, ...)
│   ├── guideline/                # step1 → step3, hướng dẫn setup
│   ├── docs/                      # ADR, tài liệu kiến trúc kit
│   ├── .mcp.json                  # cấu hình MCP: figma-mcp, notebooklm-mcp, codegraph
│   └── skills-lock.json            # lock file các skill đã cài
├── project-ai-kit/                # kit khác trong cùng repo — không dùng cho setup mobile
└── qc-kit-agent/                   # kit khác trong cùng repo — không dùng cho setup mobile
```
