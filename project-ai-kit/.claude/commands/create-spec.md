---
description: Chạy trọn workflow BA (6 outputs) cho feature mới. Dùng: /create-spec <tên feature>
---

Đọc `.claude/agents/ba-agent.md` rồi đóng vai **BA (Business Analyst)** cho feature: **$ARGUMENTS**

Toàn bộ workflow (Bước 1 → 5.6), 12 câu hỏi bắt buộc (Câu 0 platform + Câu 0.5 Figma URL + 10 câu nghiệp vụ), ràng buộc cứng, và cấu trúc SPEC nằm trong `ba-agent.md` — tuân thủ đầy đủ, không bỏ qua bước hỏi user.

Definition of Done là **6 outputs**, không phải riêng SPEC.md:

| # | Output |
|---|---|
| 0 | `SPEC.md` — 11 sections, có `## BA Deliverables` |
| 1-3 | 3 Figma frame — Flow Tổng Quan · Screen Flow · Screens + Items |
| 4 | HTML prototype — `<DOCS_ROOT>/features/<feature>/prototype/index.html` |
| 5 | MkDocs site |

Báo "xong" khi mới có SPEC.md là sai — xem bảng "Definition of Done" và mục "Anti-pattern NGHIÊM CẤM" trong `ba-agent.md`.

Nếu `$ARGUMENTS` rỗng, hỏi user tên feature trước khi bắt đầu.
