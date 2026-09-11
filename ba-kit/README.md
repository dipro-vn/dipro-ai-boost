# BA AI Kit

Bộ công cụ AI hỗ trợ **Business Analyst** — nhận input requirement dạng bất kỳ (docx / md / xlsx / pdf / meeting note / user chat), tự động tạo **SPEC.md + Figma flow + HTML prototype** để bàn giao stakeholder hoặc chuyển tiếp Tech Lead / Designer.

## Danh sách tool

| # | Tool | Mục đích | Nền tảng | Hướng dẫn sử dụng |
|---|------|----------|----------|-------------------|
| 1 | [Requirement to Flow](./requirement-to-flow/) | Từ requirement bất kỳ → SPEC.md + 3 Figma frames (Flow / Screen Flow / Screens+Items) + HTML Prototype | Claude Code + Figma MCP | [README chi tiết](./requirement-to-flow/README.md) |

---
## Tool `requirement-to-flow` tạo ra **3 Figma frame + 1 HTML prototype + 1 SPEC.md** trong 1 lần chạy. Ảnh dưới đây là sample thật từ 1 feature (In-App VoIP Call).

### Output 1 — Flow Tổng Quan

Business Logic Flow (Actor → Trigger → Function → Technology → Outcome) + Sitemap WBS Tree + Technology Stack table. Dùng để stakeholder / Tech Lead nắm bức tranh tổng quan trong 1 nhìn.

![Output 1 — Flow Tổng Quan](./requirement-to-flow/sample/output1_sample.jpg)

---

### Output 2 — Screen Flow

Chia flow thành N group theo business logic, kèm bảng Index screens. Dùng để Designer nắm được trình tự màn hình + Tech Lead cắt task theo group.

![Output 2 — Screen Flow](./requirement-to-flow/sample/output2_sample.jpg)

---

### Output 3 — Screens + Items + Error Scenarios

Mockup từng screen kèm bảng ITEMS (component / behavior) + ERROR SCENARIOS (non-happy case). Dùng làm input cho Designer làm high-fi UI và QC viết test case.

![Output 3 — Screens + Items](./requirement-to-flow/sample/output3_sample.png)

---