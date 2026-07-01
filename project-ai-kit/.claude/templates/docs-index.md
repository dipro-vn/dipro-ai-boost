# <TEN_DU_AN> — Documentation

BMAD feature docs — SPEC → DESIGN → PLAN → tasks. Long-memory của dự án, sinh ra bởi các AI agent (BA/Tech Lead/PM/Dev) theo pipeline trong `AGENTS.md`.

## Cấu trúc

```
features/<feature-name>/
├── SPEC.md              ← BA — nghiệp vụ, actors, flow, AC, Screens
├── PLAN.md               ← PM — kế hoạch, timeline, dependencies
└── <repo>/
    ├── DESIGN.md         ← Tech Lead — thiết kế kỹ thuật per repo
    └── tasks/task-*.md   ← Task chi tiết cho Dev implement
```

Dùng menu bên trái (tự sinh theo thư mục, không cần sửa `mkdocs.yml` khi thêm feature mới) để duyệt từng feature.
