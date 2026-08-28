---
description: Đọc node Figma qua MCP và ghi context ra file figma_<ComponentName>_context.md. Dùng: /read-figma <figma-url> <ComponentName> <feature>
---

Đọc Figma node và tạo context file: **$ARGUMENTS**

## Bước 0 — Parse args + Precondition check

**Args expected** (3 phần, cách nhau bằng space):
1. `<figma-url>` — link node copy từ Figma Dev Mode (chứa `?node-id=`)
2. `<ComponentName>` — PascalCase, sẽ là tên component React (vd: `OrderCard`)
3. `<feature>` — kebab-case, tên feature folder docs (vd: `order-management`)

Nếu thiếu bất kỳ arg nào → **HỎI USER**, không tự đoán.

**Precondition:**
- Figma MCP phải đã connected. Verify bằng cách check có tool `mcp__figma__get_metadata` không. Nếu không có → báo user: *"Figma MCP chưa connect. Mở Figma Desktop → bật local MCP server → restart Claude Code."* và dừng.
- URL phải chứa `?node-id=` hoặc `&node-id=`. Nếu không → báo user copy lại link từ Dev Mode (right-click → Copy link to selection).

## Bước 1 — Đọc node qua MCP (gọi song song)

Gọi 4 tool cùng lúc với cùng URL:

```
mcp__figma__get_metadata(url: "<figma-url>")
mcp__figma__get_design_context(url: "<figma-url>")
mcp__figma__get_variable_defs(url: "<figma-url>")
mcp__figma__get_screenshot(url: "<figma-url>")
```

## Bước 2 — Map tokens Figma → design tokens dự án

Đọc `.claude/rules/design_rule.md` rồi build bảng mapping từ `get_variable_defs` output:

- Color hex → `colors.semantics.*` hoặc `colors.components.*`
- Spacing px → `spacing.padding.<n>`
- Border radius px → `borders.semantics.border-radius.<token>`
- Font size + line-height + weight → `font.text|display <size>.<weight>`

Nếu có token Figma KHÔNG match được token nào trong design system dự án → liệt kê vào section `## Notes` để user/BA confirm.

## Bước 3 — Ghi file context

**Path output (tạo folder nếu chưa có):**
```
docs/features/<feature>/figma/figma_<ComponentName>_context.md
docs/features/<feature>/figma/figma_<ComponentName>.png
```

Nếu feature folder hoàn toàn chưa tồn tại → hỏi user xác nhận trước khi tạo (tránh tạo nhầm feature mới).

**Template file:**

```markdown
# Figma Context — <ComponentName>

- **Figma link:** <figma-url>
- **Node ID:** <id từ metadata>
- **Node name:** <Figma layer name từ metadata>
- **Captured at:** <YYYY-MM-DD>
- **Target component:** <ComponentName>
- **Feature:** <feature>

## Metadata
<output get_metadata — type, size (w×h), children outline tree>

## Design Context
<output get_design_context — layout, spacing, colors, typography raw>

## Tokens Mapping (Figma → Design System dự án)

| Figma token | Figma raw value | Design token dự án |
|---|---|---|
| primary/500 | #0969da | colors.semantics.company.500 |
| spacing/md | 16px | spacing.padding.16 |
| ... | ... | ... |

## Screenshot
![<ComponentName>](./figma_<ComponentName>.png)

## Notes & Ambiguities
- <Tokens không map được → cần BA/Design confirm>
- <States visible: hover/disabled/loading?>
- <Edge cases observed>
```

Screenshot từ `get_screenshot` ghi cùng folder với tên `figma_<ComponentName>.png`.

## Bước 4 — Output cho user

Báo cáo ngắn gọn:

```
✅ Figma context đã ghi:
   - docs/features/<feature>/figma/figma_<ComponentName>_context.md
   - docs/features/<feature>/figma/figma_<ComponentName>.png

📋 Tokens map được: <X>/<Y>
⚠️  Ambiguities cần confirm: <N> (xem section Notes)

Bước tiếp theo:
→ "Hãy là FE AGENT, thực thi code giao diện tại path figma context mới tạo xong: docs/features/<feature>/figma/figma_<ComponentName>_context.md"
```

## Ràng buộc

- ❌ Không generate code component trong command này — chỉ ghi context file.
- ❌ Không tự đoán target repo — để FE agent quyết định ở bước sau dựa trên feature.
- ❌ Không tạo feature folder mới nếu chưa tồn tại — phải hỏi user trước.
- ✅ Nếu file context đã tồn tại (đọc lại node lần 2) → update file cũ, thêm `**Updated at:** <date>` ở header, không tạo file mới.
