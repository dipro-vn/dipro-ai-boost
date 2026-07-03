---
name: ui-analysis-figma-analysis
description: 
---

# Figma Analysis

**Category:** ui-analysis · **Status:** 🟢 Active

## When to use
Khi đọc một file/frame Figma trước khi hiện thực hóa thành code.

## Steps
1. Đọc layout tổng: cấu trúc auto-layout, hướng, padding, gap giữa phần tử.
2. Trích token: color, typography, spacing, radius — map sang biến design system.
3. Nhận diện component có thể tái sử dụng và các variant (size, state).
4. Liệt kê state: default, hover, focus, active, disabled, loading, error.
5. Suy ra ý đồ responsive từ constraint/auto-layout (hug, fill, fixed).
6. Ghi chú điểm mơ hồ (thiếu state, spacing lệch) để hỏi designer.

## Template
```md
## Phân tích frame: <tên>
- Layout: <auto-layout, direction, gap, padding>
- Token: color=…, type=…, space=…, radius=…
- Component/variant: <Button: size×state>
- State: default/hover/focus/disabled/loading/error
- Responsive intent: <hug/fill/fixed>
- Câu hỏi designer: <…>
```

## Example
**Good:** Map spacing 16px → `--space-4`, liệt kê đủ state, đánh dấu chỗ thiếu empty state.
**Avoid:** Đọc pixel cứng 16px rồi hardcode, bỏ qua hover/disabled.

## Checklist
- [ ] Trích token thay vì hardcode giá trị
- [ ] Liệt kê đủ state của component
- [ ] Xác định component/variant tái sử dụng
- [ ] Ghi chú ý đồ responsive và câu hỏi designer
