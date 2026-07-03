---
name: requirement-analysis-requirement-analysis
description: 
---

# Requirement Analysis

**Category:** requirement-analysis · **Status:** 🟢 Active

## When to use
Khi nhận yêu cầu/feature mới còn mơ hồ, trước khi ước lượng hay code.

## Steps
1. Xác định mục tiêu nghiệp vụ: vấn đề gì đang giải, ai hưởng lợi.
2. Liệt kê actor (người dùng/hệ thống) và vai trò của từng actor.
3. Khoanh scope rõ: cái gì IN, cái gì OUT (out-of-scope ghi tường minh).
4. Tách yêu cầu chức năng và phi chức năng (hiệu năng, bảo mật, i18n).
5. Ghi giả định và phụ thuộc; đánh dấu phần chưa chắc chắn.
6. Tổng hợp danh sách câu hỏi mở gửi stakeholder trước khi bắt đầu.

## Template
```md
## Mục tiêu
<vấn đề + giá trị>

## Actor
- <actor>: <vai trò>

## Scope
- IN: …
- OUT: …

## Giả định & Phụ thuộc
- …

## Câu hỏi mở
- [ ] …
```

## Example
**Good:** Scope IN/OUT rõ, có actor, kèm câu hỏi mở về case chưa định nghĩa.
**Avoid:** Nhảy vào code khi yêu cầu còn "làm trang quản lý user" chung chung.

## Checklist
- [ ] Mục tiêu nghiệp vụ rõ ràng
- [ ] Liệt kê đủ actor và vai trò
- [ ] Scope IN/OUT tường minh
- [ ] Có danh sách câu hỏi mở cho stakeholder
