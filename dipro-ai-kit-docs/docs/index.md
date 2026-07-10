# Dipro AI Kit

> **Bộ công cụ AI agents chuẩn hóa** toàn bộ vòng đời phát triển phần mềm tại Dipro — từ phân tích yêu cầu đến deploy.

---

## Dipro AI Kit là gì?

**Dipro AI Kit** là một **monorepo** chứa **6 kit chuyên biệt** dành cho từng vai trò và tầng công nghệ trong quy trình phát triển phần mềm. Mỗi kit là một bộ cấu hình **Claude Code** reusable gồm agents, commands, skills, workflows, rules, và tools đã được chuẩn hóa.

```
dipro-ai-kit/
├── project-ai-kit/    → Orchestration toàn bộ dự án (BMAD)
├── backend-kit/       → NestJS Backend chuyên biệt
├── fe-kit/            → React Frontend chuyên biệt
├── mobile-ai-kit/     → Flutter + React Native chuyên biệt
├── brse-ai-kit/       → Basic Design từ Figma
└── qc-kit-agent/      → QC Testing (manual + automation)
```

---

## Tại sao cần Dipro AI Kit?

| Vấn đề | Giải pháp của Kit |
|--------|------------------|
| AI đoán mò tech stack, không nhất quán | Stack constraints cố định per kit |
| Mỗi dev dùng AI theo cách khác nhau | Agents & commands chuẩn hóa |
| AI leak code/secret ra ngoài | Security rules + forbidden file list |
| QC sinh test case không theo quy trình | RBT pipeline 5 bước |
| BA/Dev/QC không có quy trình rõ ràng | BMAD 8-phase workflow |
| Tài liệu không đồng bộ với code | Memory Update Gate bắt buộc |

---

## Các Kit & Vai trò

| Kit | Dành cho ai | Khi nào dùng |
|-----|------------|--------------|
| [project-ai-kit](kits/project-ai-kit.md) | Toàn team | Bắt đầu dự án / feature mới |
| [backend-kit](kits/backend-kit.md) | Backend Dev | Phát triển NestJS API |
| [fe-kit](kits/fe-kit.md) | Frontend Dev | Phát triển React Web |
| [mobile-ai-kit](kits/mobile-ai-kit.md) | Mobile Dev | Phát triển Flutter / React Native |
| [brse-ai-kit](kits/brse-ai-kit.md) | BrSE | Tạo Basic Design từ Figma |
| [qc-kit-agent](kits/qc-kit-agent.md) | QC Engineer | Sinh & quản lý test cases |

---

## Bắt đầu nhanh

=== "Dự án mới"

    ```bash
    mkdir my-project && cd my-project
    git init
    cp -r /path/to/project-ai-kit/.claude .
    cp /path/to/project-ai-kit/{CLAUDE.md,POLICIES.md,AGENTS.md} .
    
    claude          # Mở Claude Code session
    /init-kit       # Setup dự án
    /create-spec "Tính năng đăng nhập"  # Bắt đầu feature
    ```

=== "Backend NestJS"

    ```bash
    cp -r /path/to/backend-kit/.claude my-project/.claude
    cd my-project
    
    claude
    /new-feature "Thêm order search endpoint"
    ```

=== "Frontend React"

    ```bash
    cp -r /path/to/fe-kit/.claude my-project/.claude
    cd my-project
    
    claude
    /new-feature "Thêm trang quản lý đơn hàng"
    ```

=== "Mobile Flutter/RN"

    ```bash
    git submodule add git@github.com:dipro-vn/dipro-ai-kit.git tools/dipro-ai-kit
    ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/CLAUDE.md .claude/CLAUDE.md
    
    claude
    # Mô tả task → workflow tự chọn
    ```

---

## Nguyên tắc cốt lõi

!!! info "5 Nguyên tắc không thể vi phạm"

    1. **Không đoán mò** — Thiếu thông tin → hỏi user, không tự giả định
    2. **Đọc trước, hành động sau** — Luôn đọc docs liên quan trước khi generate
    3. **Stateless** — Mọi context đọc từ file `.md`, không nhớ session trước
    4. **Tool-first** — Dùng `tilth_*` / Grep/Glob thay grep/cat/find thủ công
    5. **Blast radius check** — Chạy `tilth_deps` trước khi đổi bất kỳ public interface

!!! warning "Phân quyền nghiêm ngặt"

    **Chỉ Dev** được phép sửa source code. BA, Tech Lead, PM, QC, QA, Designer **không được chạm** vào source code.

---

## Xem thêm

- [Kiến trúc Monorepo](overview/architecture.md) — Cấu trúc chi tiết từng kit
- [BMAD Workflow](overview/bmad-workflow.md) — 8 phases từ Spec đến Deploy
- [So sánh tất cả Kits](kits/index.md) — Chọn kit phù hợp cho task
- [Bảo mật & Chính sách](reference/security.md) — Security rules bắt buộc
