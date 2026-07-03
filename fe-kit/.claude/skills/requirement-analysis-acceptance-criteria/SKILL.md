---
name: requirement-analysis-acceptance-criteria
description: 
---

# Acceptance Criteria

**Category:** requirement-analysis · **Status:** 🟢 Active

## When to use
Khi viết tiêu chí chấp nhận cho user story để dev/QA cùng hiểu "done".

## Steps
1. Viết theo Given/When/Then: bối cảnh → hành động → kết quả mong đợi.
2. Mỗi AC chỉ kiểm tra một hành vi; tách nếu có nhiều "When".
3. Dùng giá trị cụ thể, đo được; tránh "nhanh", "thân thiện", "hợp lý".
4. Bao phủ cả happy path lẫn nhánh lỗi/biên quan trọng.
5. Diễn đạt ở mức hành vi quan sát được, không ràng buộc cách triển khai.
6. Đảm bảo mỗi AC testable: QA viết được test case từ nó.

## Template
```gherkin
Scenario: Đăng nhập sai mật khẩu
  Given người dùng đang ở trang đăng nhập
  When nhập email đúng và mật khẩu sai rồi bấm "Đăng nhập"
  Then hiển thị lỗi "Email hoặc mật khẩu không đúng"
  And không chuyển trang
```

## Example
**Good:** Given/When/Then rõ, kết quả đo được, có nhánh lỗi.
**Avoid:** "Hệ thống phải đăng nhập tốt và nhanh" — không testable, không đo được.

## Checklist
- [ ] Theo cấu trúc Given/When/Then
- [ ] Mỗi AC một hành vi, đo được
- [ ] Bao phủ happy path và nhánh lỗi/biên
- [ ] QA viết được test case từ AC
