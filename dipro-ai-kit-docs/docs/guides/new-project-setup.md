# Setup dự án mới

Hướng dẫn chi tiết thiết lập `project-ai-kit` cho một dự án hoàn toàn mới.

---

## Tổng quan các bước

```
Bước 0: Cài Claude Code CLI
Bước 1: Tạo thư mục dự án
Bước 2: Copy kit vào dự án
Bước 3: Clone source repos vào đúng vị trí
Bước 4: Chạy /init-kit (điền thông tin dự án)
Bước 5: Verify kết quả
Bước 5b: (optional) Setup MkDocs site
Bước 6: Bắt đầu feature đầu tiên
```

---

## Bước 0 — Cài Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
claude --version    # Verify
claude             # Đăng nhập lần đầu (mở browser)
```

---

## Bước 1 — Tạo thư mục dự án

```bash
mkdir my-ecommerce && cd my-ecommerce
git init
```

---

## Bước 2 — Copy kit

```bash
cp -r /path/to/dipro-ai-kit/project-ai-kit/.claude .
cp -r /path/to/dipro-ai-kit/project-ai-kit/template .
cp /path/to/dipro-ai-kit/project-ai-kit/{CLAUDE.md,POLICIES.md,AGENTS.md} .
```

Sau bước này:

```
my-ecommerce/
├── CLAUDE.md          ← AI entrypoint
├── POLICIES.md        ← AI behavior rules
├── AGENTS.md          ← Project info (chưa điền)
├── template/          ← Excel QC templates
└── .claude/           ← Agents, commands, skills, rules...
```

---

## Bước 3 — Tổ chức source repos

Có 2 cách tổ chức, chọn 1:

### Cách A — Nhiều repo (khuyến nghị)

```
my-ecommerce/
├── CLAUDE.md / .claude / ...
├── my-ecommerce-repository/
│   ├── backend/          ← git clone repo backend
│   ├── web-admin/        ← git clone repo web admin
│   ├── web-shop/         ← git clone repo web shop
│   └── mobile/           ← git clone repo mobile
└── my-ecommerce-docs/    ← repo docs riêng
    └── docs/features/
```

```bash
mkdir my-ecommerce-repository
cd my-ecommerce-repository
git clone git@github.com:org/backend.git
git clone git@github.com:org/web-admin.git
git clone git@github.com:org/web-shop.git
git clone git@github.com:org/mobile.git
cd ..

mkdir -p my-ecommerce-docs/docs/features
```

### Cách B — Monorepo nhỏ

```
my-ecommerce/
├── CLAUDE.md / .claude / ...
├── src/                  ← Source code
└── docs/features/        ← Docs ngay trong repo
```

---

## Bước 4 — Chạy `/init-kit`

```bash
claude    # Mở session tại my-ecommerce/
/init-kit
```

Agent sẽ hỏi tuần tự. Trả lời dựa trên cấu trúc đã tạo ở Bước 3:

### Câu 1: Tên dự án + domain

```
my-ecommerce — Nền tảng thương mại điện tử B2B kết nối nhà cung cấp với người bán lẻ tại Nhật Bản
```

### Câu 2: Docs root path

```
# Cách A (docs repo riêng)
my-ecommerce-docs/docs

# Cách B (docs trong repo)
docs
```

### Câu 3: Danh sách repos

```
Repo 1:
  Tên: backend
  Path: my-ecommerce-repository/backend
  Vai trò: backend
  Stack: NestJS (Enter để dùng mặc định)

Repo 2:
  Tên: web-admin
  Path: my-ecommerce-repository/web-admin
  Vai trò: frontend
  Stack: React 19 (Enter để dùng mặc định)

Repo 3:
  Tên: mobile
  Path: my-ecommerce-repository/mobile
  Vai trò: mobile
  Stack: Flutter (Enter để dùng mặc định)
```

### Câu 4: Epic codes

```
backend → E01
web-admin → E02
mobile → E03
```

### Câu 5: Actors/personas

```
Admin (quản lý hệ thống, dùng web-admin)
Supplier (nhà cung cấp, dùng web-shop)
Buyer (người mua, dùng mobile)
```

### Câu 6: Payment gateway

```
elepay, Alipay (Nhật Bản)
```

### Câu 7: Cặp dễ nhầm

```
web-admin (quản lý nội bộ) vs web-shop (portal supplier)
Supplier vs Buyer role — 2 role khác nhau hoàn toàn
```

### Câu 8: Cross-repo features

```
Auth JWT (backend + tất cả client)
Payment (backend + mobile callback)
Real-time notification (backend WS + mobile + web)
```

---

## Bước 5 — Verify kết quả

Mở `AGENTS.md` và kiểm tra:

- [ ] Bảng Ecosystem/Repos điền đúng path thật
- [ ] Actors/personas đúng
- [ ] Payment/integration đúng
- [ ] Cross-repo features đúng

Nếu sai → sửa tay hoặc chạy lại `/init-kit`.

---

## Bước 5b — Setup MkDocs (optional)

```bash
# Copy templates
cp .claude/templates/mkdocs.yml my-ecommerce-docs/mkdocs.yml
mkdir -p my-ecommerce-docs/docs
cp .claude/templates/docs-index.md my-ecommerce-docs/docs/index.md

# Sửa placeholder <TEN_DU_AN> nếu /init-kit chưa tự điền
# Cài và chạy
pip install -r .claude/templates/mkdocs-requirements.txt
cd my-ecommerce-docs
mkdocs serve   # http://localhost:8000
```

---

## Bước 6 — Feature đầu tiên

```bash
# Trong session Claude Code
/create-spec "Tính năng đăng nhập bằng email và Google OAuth"
```

BA Agent sẽ tự dẫn dắt qua pipeline. Ở cuối mỗi output có hướng dẫn "Bước tiếp theo":

```
SPEC.md đã sẵn sàng.

Bước tiếp theo (chạy song song):
  /create-design          → Tech Lead viết DESIGN
  /test/analyze-req       → QC phân tích requirement
  /create-ui-design       → Designer tạo Figma frames
```

---

## Checklist setup hoàn chỉnh

- [ ] Claude Code CLI cài đặt + đăng nhập
- [ ] Kit copy vào dự án đúng cấu trúc
- [ ] Source repos ở đúng vị trí
- [ ] `/init-kit` chạy xong, `AGENTS.md` đã có thông tin
- [ ] MkDocs chạy được (nếu dùng)
- [ ] Feature đầu tiên: `/create-spec` chạy thành công
