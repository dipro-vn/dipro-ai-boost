# Designer Pre-flight — Design System Sources Check

> **Scope:** Câu 0.6 trong workflow `designer-agent` (Bước 3 — Component Discovery). Chi tiết template A/B/C/D cho 2 gate kiểm tra design system sources trước khi vẽ.
> **Dùng ở:** `designer-agent.md` (Câu 0.6). Agent body chỉ giữ tóm tắt gate + reference file này khi cần copy template.
> **Nguyên tắc:** Thiếu 1 trong 2 gate → DỪNG, hỏi user "đọc ở đâu". KHÔNG silent-fallback tự dùng kit default hoặc tự vẽ rectangle.

---

## Gate A — Design System Rule (token doc)

File quy định color/typography/spacing/radius/effect token của dự án.

**Verify:**

```
Read: .claude/rules/design_rule.md
→ Section 1 (Color Primitives), Section 4 (Typography), Section 5 (Border Radius),
  Section 6 (Spacing), Section 8 (Effects) đã có value cụ thể chưa?
→ Section 10 (Per-Site Layout Rules) đã có sub-section cho repo target chưa?
→ Section 11 (Figma → Token Quick Lookup per repo) đã điền hex → token mapping chưa?
```

**Trigger hỏi user (khi design token rỗng / placeholder / chỉ có kit default chung — chưa customize cho dự án cụ thể):**

```
⚠️ Design System Rule chưa đầy đủ cho dự án <name>

File `.claude/rules/design_rule.md` hiện chỉ có kit default — chưa có:
  - Per-Site Layout Rules cho repo <target-repo>
  - Figma → Token mapping (hex primary button, sidebar color của repo)
  - [liệt kê cụ thể section nào thiếu]

Đọc design token ở đâu? — chọn 1:
  [A] User cung cấp Figma URL của page "Design Tokens" / "Foundations" trong Figma file dự án
      → Designer sẽ đọc qua get_variable_defs + get_design_context, extract token,
        rồi cập nhật `design_rule.md` sections 10-11 trước khi vẽ.
  [B] User cung cấp doc token khác (Notion, Zeplin, spec .md riêng) — paste URL/path
  [C] User cho phép Designer dùng token của kit default (Section 1-8) tạm thời + note "TBD design lock"
  [D] User cho phép Designer đề xuất token mới dựa trên reference screen mẫu (Câu 1) — chờ user duyệt
```

---

## Gate B — Figma Component Library page

Page trong `FIGMA_OUTPUT_URL` chứa components dùng chung (Sidebar, Header, Table, Button, Input...).

**Verify:**

```
mcp__claude_ai_Figma__get_metadata(fileKey: <FIGMA_OUTPUT_URL fileKey>)
→ List pages trong file, tìm page tên "Component Library" / "Components" / "UI Kit" / "Design System"

mcp__claude_ai_Figma__search_design_system(query: "Sidebar")  ← smoke test có return component không
```

**Trigger hỏi user (khi không có page component library match HOẶC `search_design_system` trả về rỗng cho các component cơ bản):**

```
⚠️ Component Library chưa có trong Figma file <FIGMA_OUTPUT_URL>

get_metadata result: <list pages hiện có — vd chỉ có page "Screens", chưa có "Components">
search_design_system("Sidebar"): <0 results / N results>

Đọc component library ở đâu? — chọn 1:
  [A] User cung cấp URL Figma file khác chứa Component Library (published library)
      → Designer sẽ import qua get_libraries + importComponentByKeyAsync
  [B] User chỉ ra page trong CÙNG file này (đổi tên page hoặc paste URL page cụ thể)
  [C] User cho phép Designer tạo page "Component Library" mới trong file + đề xuất basic components
      (Sidebar, Header, Button, Input, Table, Badge, Pagination, Modal)
      → chờ user duyệt design từng component TRƯỚC KHI vẽ screens
  [D] User cho phép Designer skip component library, tự dùng primitives (createRectangle + text)
      — CHẤP NHẬN downgrade từ HIGH-FIDELITY xuống MID-FIDELITY (ghi note vào Bước 6 output)
```

---

## Enforcement

- Cả 2 gate (A + B) phải PASS trước khi sang Câu 1
- KHÔNG được silent-fallback: gặp thiếu → tự dùng kit default / tự vẽ rectangle → vi phạm rule "KHÔNG tự ý generate khi thiếu component"
- User chọn option → lưu decision vào note đầu Bước 6 handover để Design Lead review sau
- Nếu user chọn [A] hoặc [B] cho Gate A → Designer sync design token về `design_rule.md` sections 10-11 (Edit tool) TRƯỚC KHI vẽ screen đầu tiên — không để token drift giữa Figma và docs
