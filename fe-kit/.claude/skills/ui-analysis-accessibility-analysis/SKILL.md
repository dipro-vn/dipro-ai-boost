---
name: ui-analysis-accessibility-analysis
description: 
---

# Accessibility Analysis

**Category:** ui-analysis · **Status:** 🟢 Active

## When to use
Khi soi một design để phát hiện vấn đề a11y trước khi code.

## Steps
1. Kiểm tương phản text/nền và icon quan trọng đạt WCAG AA.
2. Đo touch target: tối thiểu 44×44px cho phần tử bấm trên mobile.
3. Suy thứ tự đọc/tab hợp lý từ bố cục; cảnh báo nếu order visual lệch DOM.
4. Soát trạng thái focus có được thiết kế không (không chỉ hover).
5. Phát hiện thông tin chỉ truyền bằng màu (cần thêm icon/text).
6. Kiểm label cho input, alt cho ảnh, tên cho icon-button.

## Template
```md
## A11y review: <màn hình>
| Vấn đề | Vị trí | Mức | Đề xuất |
|--------|--------|-----|---------|
| Contrast 3.1:1 | text phụ | AA fail | tăng độ đậm màu |
| Target 32px | icon button | fail | tăng ≥44px |
| Màu báo lỗi | form | fail | thêm icon + text |
```

## Example
**Good:** Phát hiện text xám contrast 3.1:1, target 32px, lỗi chỉ báo bằng màu đỏ.
**Avoid:** Duyệt design chỉ nhìn "đẹp", bỏ qua contrast và target size.

## Checklist
- [ ] Kiểm tương phản đạt WCAG AA
- [ ] Target bấm ≥44×44px
- [ ] Có thiết kế trạng thái focus
- [ ] Không truyền thông tin chỉ bằng màu
