<div align="center">
  <img src="https://www.dipro-tech.com/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fimg-dipro-menu2.c404d723.png&w=1536&q=75" alt="DIPRO TECH" width="280" />

  # Dipro AI Boost

  **Bộ cấu hình Claude Code chuẩn hóa — toàn bộ vòng đời phát triển phần mềm tại Dipro Tech**

  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Claude Code](https://img.shields.io/badge/Claude%20Code-CLI-orange.svg)](https://claude.ai/code)
</div>

---

## Tổng quan

**Dipro AI Boost** là monorepo chứa **6 kit chuyên biệt** dành cho từng vai trò trong quy trình phát triển phần mềm. Mỗi kit là tập hợp cấu hình **Claude Code** reusable gồm agents, commands, skills, workflows, và rules đã được chuẩn hóa.

```
dipro-ai-kit/
├── project-ai-kit/    → Orchestration toàn dự án (BMAD workflow)
├── backend-kit/       → NestJS + TypeORM + PostgreSQL
├── fe-kit/            → React 19 + Vite 7 + TanStack Query v5
├── mobile-ai-kit/     → Flutter (Riverpod) + React Native
├── brse-ai-kit/       → Basic Design từ Figma (Figma Plugin)
└── qc-kit-agent/      → QC Testing: manual TC + Playwright E2E
```

---

## Yêu cầu

| Yêu cầu | Phiên bản |
|---------|-----------|
| Node.js | ≥ 18 |
| Claude Code CLI | latest |
| Git | any |
| Python 3 | chỉ cần cho `/export-xlsx` |

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

---

## Các Kit

| Kit | Dành cho | Stack | Hướng dẫn |
|-----|----------|-------|-----------|
| [`project-ai-kit`](project-ai-kit/README.md) | BA · Tech Lead · PM · QC · QA · Designer | Claude Code (multi-agent BMAD) | [README →](project-ai-kit/README.md) |
| [`backend-kit`](backend-kit/README.md) | Backend Developer | NestJS · TypeORM 0.3.x · PostgreSQL · Redis | [README →](backend-kit/README.md) |
| [`fe-kit`](fe-kit/README.md) | Frontend Developer | React 19 · Vite 7 · TanStack Query v5 · Redux Toolkit v2 · Ant Design v6 · TailwindCSS v4 | [README →](fe-kit/README.md) |
| [`mobile-ai-kit`](mobile-ai-kit/README.md) | Mobile Developer | Flutter (Riverpod 3.x · Retrofit+Dio · auto_route) · React Native (RTK Query) | [README →](mobile-ai-kit/README.md) |
| [`brse-ai-kit`](brse-ai-kit/README.md) | BrSE | Figma Plugin + Claude | [README →](brse-ai-kit/README.md) |
| [`qc-kit-agent`](qc-kit-agent/README.md) | QC Engineer | Claude Code · Playwright E2E | [README →](qc-kit-agent/README.md) |

---

## MCP Tools

| Tool | Kit dùng | Chức năng |
|------|---------|-----------|
| `tilth` | project, backend, fe | Code search & analysis |
| Playwright | qc-kit, project-ai-kit | E2E test automation |
| Figma | brse-kit, project-ai-kit | Design reading |
| CodeGraph / Understand-Anything | backend, mobile | Codebase navigation |

---

## Nguyên tắc cốt lõi

1. **Không đoán mò** — Thiếu thông tin → hỏi user, không tự giả định
2. **Đọc trước, hành động sau** — Đọc docs liên quan trước khi generate
3. **Stateless** — Mọi context đọc từ file `.md`, không nhớ session trước
4. **Tool-first** — Dùng `tilth_*` / Grep / Glob thay grep/cat/find thủ công
5. **Blast radius check** — Chạy `tilth_deps` trước khi đổi bất kỳ public interface

> **Phân quyền:** Chỉ **Dev** được phép sửa source code. BA, Tech Lead, PM, QC, QA, Designer **không được chạm** vào source code.

---

## Chọn Kit theo loại dự án

```mermaid
flowchart LR
    Q{"Loại dự án?"}

    Q -->|"Dự án mới\nfull team"| PB["🏗️ Project Base\n─────────────────\nproject-ai-kit ✅\nbackend-kit ✅\nfe-kit ✅\nmobile-ai-kit ✅\nbrse-ai-kit ✅\nqc-kit-agent ✅"]

    Q -->|"POC /\nprototype"| LB["🧪 Labo\n─────────────────\nChọn 1–3 kit\ntheo stack cần dùng"]

    Q -->|"Bug fix /\ncải tiến nhỏ"| MT["🔧 Maintain\n─────────────────\nKit theo repo\n(backend / fe / mobile)\n+ qc-kit-agent nếu\ncần bug report"]

    style PB fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A
    style LB fill:#FEF3C7,stroke:#D97706,color:#78350F
    style MT fill:#DCFCE7,stroke:#16A34A,color:#14532D
```

---

## Tài liệu

Docs đầy đủ được viết bằng MkDocs tại `dipro-ai-kit-docs/`:

```bash
cd dipro-ai-kit-docs
pip install -r requirements.txt
mkdocs serve   # http://localhost:8000
```

Video Demo tham khảo: [Demo](https://drive.google.com/file/d/1tNF06n02QX176GS7vqxYTISAEK496mXc/view)

---

## Các tính năng khác

Tổng hợp các mẹo & workflow ngắn dùng AI trong công việc hằng ngày (nằm ở [`ai-tips/`](ai-tips/)):

| Tính năng | Mô tả | Đề xuất cho role |
|---|---|---|
| [Hướng dẫn tạo Basic-Design](ai-tips/huong-dan-tao-basic-design/H%C6%B0%E1%BB%9Bng%20d%E1%BA%ABn%20t%E1%BA%A1o%20Basic-Design.md) | Sinh 画面設計書 (ảnh đánh số + Excel) từ Figma qua Claude MCP | BrSE · QC |
| [Mẹo Kết nối Figma để tạo code giao diện](ai-tips/generate-code-from-figma/M%E1%BA%B9o%20K%E1%BA%BFt%20n%E1%BB%91i%20v%E1%BB%9Bi%20Figma%20%C4%91%E1%BB%83%20t%E1%BA%A1o%20ra%20code%20giao%20di%E1%BB%87n.md) | Setup MCP Figma + FE agent để generate code component bám cấu trúc repo | FE Developer |
| [Hướng dẫn tạo Daily Report tổng quan](ai-tips/huong-dan-daily-report-tong-quan/H%C6%B0%E1%BB%9Bng%20d%E1%BA%ABn%20t%E1%BA%A1o%20Daily%20Report%20t%E1%BB%95ng%20quan.md) | Sinh 1 ảnh dashboard PMO (KPI + Burn Down/Up) từ dữ liệu task Excel | PM |
| [Mẹo chọn Model AI cho phù hợp](ai-tips/meo-chon-model-ai/M%E1%BA%B9o%20ch%E1%BB%8Dn%20Model%20AI%20cho%20ph%C3%B9%20h%E1%BB%A3p.md) | Chọn Haiku/Sonnet/Opus/Fable theo độ phức tạp — tiết kiệm token | Tất cả |
| [Mẹo thiết lập phiên làm việc cho AI](ai-tips/meo-thiet-lap-phien-lam-viec/M%E1%BA%B9o%20thi%E1%BA%BFt%20l%E1%BA%ADp%20phi%C3%AAn%20l%C3%A0m%20vi%E1%BB%87c%20cho%20AI.md) | Tạo scheduled task 5h sáng để mở thêm 1 phiên Claude/ngày | Tất cả |

---

<div align="center">
  Built with ❤️ by <strong>DIPRO TECH</strong> — <a href="https://www.dipro-tech.com">dipro-tech.com</a>
</div>


