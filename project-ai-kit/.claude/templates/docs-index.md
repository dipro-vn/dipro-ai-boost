# <TEN_DU_AN> — Documentation

BMAD feature docs — SPEC → DESIGN → tasks. Long-memory của dự án, sinh ra bởi các AI agent (BA/Tech Lead/Dev) theo pipeline trong `AGENTS.md`.

## Cấu trúc

```
features/<feature-name>/
├── SPEC.md              ← BA — nghiệp vụ, actors, flow, AC, Screens
│                          (## BA Deliverables liệt kê cả 6 output của BA)
├── prototype/index.html ← BA — HTML prototype, mở thẳng bằng `open`
└── <repo>/
    ├── Design-Technical.md         ← Tech Lead — thiết kế kỹ thuật per repo
    └── tasks/task-*.md   ← Task chi tiết cho Dev implement
```

Dùng menu bên trái (tự sinh theo thư mục, không cần sửa `mkdocs.yml` khi thêm feature mới) để duyệt từng feature.
