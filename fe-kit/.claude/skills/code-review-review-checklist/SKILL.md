---
name: code-review-review-checklist
description: 
---

# Review Checklist

**Category:** code-review · **Status:** 🟢 Active

## When to use
Khi review PR chung: đảm bảo đúng, rõ ràng, an toàn, có test.

## Steps
1. Đúng: code làm đúng yêu cầu, phủ edge case, xử lý lỗi.
2. Rõ: tên biến/hàm dễ hiểu, không lặp, complexity hợp lý, không code chết.
3. An toàn: validate input, không lộ secret, xử lý quyền (xem security-review).
4. Test: có test cho thay đổi, phủ nhánh chính, chạy pass.
5. Phạm vi: PR nhỏ, đúng mục tiêu, không lẫn refactor không liên quan.

## Template
```md
## Review
- [ ] Đúng yêu cầu + edge case + lỗi
- [ ] Tên/cấu trúc rõ, không trùng lặp
- [ ] Input validate, không lộ secret
- [ ] Có test, pass CI
- [ ] PR nhỏ, đúng scope

Nhận xét: <blocking> / <nit> / <gợi ý>
```

## Example
**Good:** comment phân loại blocking vs nit, chỉ rõ vị trí + lý do + đề xuất.
**Avoid:** review "LGTM" không đọc, bắt bẻ style chủ quan, trộn nhiều mối quan tâm.

## Checklist
- [ ] Đúng + edge case + lỗi
- [ ] Rõ ràng, không trùng lặp
- [ ] An toàn (input, secret, quyền)
- [ ] Có test & pass CI
