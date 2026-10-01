# Skill: figma-design

> Kiến thức dùng chung cho `designer-agent`: đọc / ghi Figma qua MCP, map giá trị Figma → design system dự án, kiểm tra chất lượng.

## 1. Đọc Figma (gọi song song cho 1 node)

```
get_metadata(fileKey, nodeId)        → cây layer, kích thước
get_design_context(fileKey, nodeId)  → layout + màu + code tham khảo
get_variable_defs(fileKey, nodeId)   → token (màu, chữ, spacing, radius, shadow)
get_screenshot(fileKey, nodeId)      → ảnh PNG
```
- `fileKey`, `nodeId` lấy từ URL `figma.com/design/<fileKey>/…?node-id=<a-b>` (→ `a:b`). Không hard-code.
- Output quá lớn → `get_metadata` trước, rồi đọc từng node con.
- Trước `get_design_context` load skill Figma `figma-design-to-code` nếu tool yêu cầu.

## 2. Ghi Figma

- **Bắt buộc** load skill `figma-use` trước mọi `use_figma`; `figma-generate-design` khi dựng màn từ mô tả.
- Component: `importComponentByKeyAsync` / `importComponentSetByKeyAsync` (library) hoặc `findOne` (local). Không vẽ rectangle thay component.
- Màu: `setBoundVariableForPaint`; chữ: text style của design system; spacing: `setBoundVariable`.
- Load font trước khi đổi `characters`: `await figma.loadFontAsync(node.fontName)`.
- Đặt Section mới ở vùng trống; không đè frame có sẵn.

## 3. Map giá trị Figma → design system

| Giá trị Figma | Map sang (`design-system/`) |
|---|---|
| Màu hex | `foundation.md` D1–D3 / `tokens.json color` |
| Font size / weight / line-height | `foundation.md` D4 |
| Padding / gap | spacing scale D5 |
| Radius / shadow | D5 |
| Component instance | `components.md` D6 |

- Variable name và màu hiển thị có thể lệch → **tin màu đo trên màn đã duyệt**, ghi mâu thuẫn.
- Không tự bịa token; thiếu → hỏi user (design-system-intake §5).

## 4. Kiểm tra chất lượng (trước khi báo xong)

- [ ] `get_screenshot` từng frame, đối chiếu prototype
- [ ] Đúng viewport, primary, font của platform
- [ ] Component là instance; không rectangle thay component
- [ ] Không chồng đè (quét toạ độ, không nhìn bằng mắt)
- [ ] Label đa ngôn ngữ không bị cắt
- [ ] Không dữ liệu thật của khách hàng

## 5. Nhiều luồng

Prototype có nhiều luồng → đọc `multi-flow.md` (group frame theo luồng, khoảng cách tối thiểu giữa group).
