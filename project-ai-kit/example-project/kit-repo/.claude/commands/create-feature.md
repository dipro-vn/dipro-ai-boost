---
description: Chạy toàn bộ BMAD pipeline để tạo ra 1 feature hoàn chỉnh — từ SPEC đến code đã qua QC Automation. Có 1 gate bắt buộc trước khi động vào code. Dùng: /create-feature <feature> [mô tả] | /create-feature <feature> build
---

Parse `$ARGUMENTS`: token đầu là `<feature>` (kebab-case). Nếu token cuối là đúng chữ `build` → đây là lệnh chạy tiếp sau gate; phần còn lại (nếu có) là `<mô tả>`.

**Nếu KHÔNG có `build` (Planning phase):**
Xác nhận feature chưa có đủ `<DOCS_ROOT>/features/<feature>/SPEC.md` + `DESIGN.md` + `tasks/*.md` (nếu đã có rồi, hỏi lại user có chắc muốn chạy lại Planning phase không — `<DOCS_ROOT>` xem trong AGENTS.md section Ecosystem). Gọi tool Workflow `name: "bmad-plan-phase"`, `args: { feature: "<feature>", description: "<mô tả>" }`.
Sau khi xong: liệt kê file đã tạo (SPEC.md, DESIGN.md từng repo, test-cases, Figma URL, tasks/*.md) và dừng lại — nhắc user:
→ Review xong thì gõ `/create-feature <feature> build` để tiếp tục sang Dev/QC. Đây là gate bắt buộc, KHÔNG tự động chạy tiếp dù không có tham số `build`.

**Nếu CÓ `build` (Build phase):**
Xác nhận feature đã có SPEC.md + DESIGN.md + tasks/*.md (output của lần chạy Planning trước). Nếu thiếu, dừng lại và báo user chạy `/create-feature <feature>` (không kèm `build`) trước.
Nếu đủ điều kiện, gọi tool Workflow `name: "bmad-build-phase"`, `args: { feature: "<feature>" }`.
Sau khi xong: tổng hợp báo cáo Dev + QC theo format Memory Update Gate trong AGENTS.md.

> Nếu dự án chưa chạy `/init-kit`, dừng lại và báo user chạy `/init-kit` trước.
