# Skill: figma-design

> Reusable knowledge cho designer-agent và /read-figma command.
> Covers: Figma MCP read tools, write tool pointers, design token mapping, templates, quality checklist.

---

## 1. Figma MCP — Read Tools

Gọi song song cho 1 node:

```
mcp__claude_ai_Figma__get_metadata(fileKey, nodeId)       → structure tree
mcp__claude_ai_Figma__get_design_context(fileKey, nodeId) → layout + colors + code
mcp__claude_ai_Figma__get_variable_defs(fileKey, nodeId)  → design tokens
mcp__claude_ai_Figma__get_screenshot(fileKey, nodeId)     → PNG screenshot
```

**Precondition:** Figma Desktop phải đang mở đúng file của dự án. Verify: tool get_metadata available và không trả về "Invalid tool call".

**File key:** Lấy từ URL Figma của dự án (`figma.com/design/<fileKey>/...`) — không hard-code, mỗi dự án có file key riêng.

---

## 2. Figma MCP — Write Tools

**BẮT BUỘC** load Figma built-in skills trước khi ghi:

```
Skill("figma-use")              ← load trước khi gọi use_figma
Skill("figma-generate-design")  ← load khi tạo screens từ layout description
```

Sau khi load → dùng use_figma theo hướng dẫn từ skill đó.

---

## 3. Scenario Decision Logic

Kiểm tra cột **Figma Link** trong ## Screens của SPEC.md:

```
Figma Link = TBD hoặc trống
  → Scenario A: TẠO MỚI
    1. Load figma-use skill
    2. Load figma-generate-design skill
    3. Tạo frames → đặt trong page "01. Design"
    4. Frame name = Screen Code theo quy ước dự án

Figma Link = URL hợp lệ
  → Scenario B: ĐỌC + ENRICH
    1. Gọi 4 read tools song song
    2. Map giá trị raw (hex, radius, spacing) → design tokens của dự án
    3. Viết context files
```

---

## 4. Token Mapping

Đọc `.claude/rules/design_rule.md` để biết bảng mapping Figma raw value (hex, radius, spacing) → design token của dự án hiện tại (per-site/per-app nếu có nhiều theme).

Nguyên tắc chung khi map:

| Loại giá trị Figma | Map sang |
|---|---|
| Màu hex | `colors.semantics.*` hoặc `colors.primitives.*` theo `design_rule.md` |
| Border radius | `borders.semantics.border-radius.*` |
| Padding/gap | `spacing.padding.*` |
| Font size/weight/line-height | `typography.*` |

Không tự bịa token mới nếu `design_rule.md` chưa định nghĩa — hỏi lại design system owner.

---

## 5. Output Format — Update SPEC.md ## Screens

Designer Agent **KHÔNG tạo file `.md` riêng** (không UI-SPEC, không figma context). Output duy nhất là Figma URL điền vào bảng `## Screens` trong SPEC.md:

```markdown
## Screens

| Screen Code | Screen | Actor | App | Screen Type | Mô tả ngắn | Figma Link |
|---|---|---|---|---|---|---|
| <SCREEN_CODE> | <Screen Name> | <Actor> | <App> | List | ... | [Figma](https://www.figma.com/design/<fileKey>/<project>?node-id=<id>&m=dev) |
```

URL format: `https://www.figma.com/design/<fileKey>/<project-name>?node-id=<frame-id>&m=dev`

> FE/Mobile/QC/QA agents khi cần đọc design sẽ tự gọi MCP `get_design_context` / `get_metadata` / `get_screenshot` từ URL này — không có pre-extracted context file.

---

## 6. Design Quality Checklist

Trước khi declare done per screen:

- [ ] Frame tạo thành công trong Figma page `01. Design`
- [ ] Frame name = Screen Code theo quy ước dự án
- [ ] Color theme đúng per site/app (xem `design_rule.md`)
- [ ] Layout structure đúng (sidebar width / header height per site)
- [ ] Components reuse từ `02. Local Component` page (không vẽ lại từ rectangle)
- [ ] Figma URL đã điền vào cột `Figma Link` của SPEC.md ## Screens
- [ ] Responsive behavior ghi chú nếu có Auto Layout
- [ ] Frame name = Screen Code trong Figma
