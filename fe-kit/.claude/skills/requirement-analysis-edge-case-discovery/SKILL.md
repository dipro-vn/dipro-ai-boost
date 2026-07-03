---
name: requirement-analysis-edge-case-discovery
description: 
---

# Edge Case Discovery

**Category:** requirement-analysis · **Status:** 🟢 Active

## When to use
Khi rà soát một feature để tìm các trường hợp biên dễ bị bỏ sót.

## Steps
1. Dữ liệu: empty, null/undefined, 0, chuỗi rất dài, ký tự đặc biệt/emoji.
2. Số lượng: 0 phần tử, 1 phần tử, rất nhiều (phân trang, scroll).
3. Biên giá trị: min/max, vượt ngưỡng, số âm, ngày quá khứ/tương lai.
4. Mạng/hệ thống: timeout, mất kết nối, request trùng, response chậm.
5. Quyền & phiên: chưa đăng nhập, hết hạn token, không đủ quyền.
6. Concurrency: hai tab cùng sửa, double-click, race condition.

## Template
```md
## Edge cases — <feature>
| Nhóm | Case | Hành vi mong đợi |
|------|------|------------------|
| Data | list rỗng | hiển thị empty state |
| Biên | nhập > max | chặn + báo lỗi |
| Mạng | API timeout | retry / thông báo |
| Quyền | token hết hạn | điều hướng login |
```

## Example
**Good:** Có empty state, chặn quá max, xử lý token hết hạn, chống double-submit.
**Avoid:** Chỉ test happy path; bỏ qua list rỗng và lỗi mạng.

## Checklist
- [ ] Phủ empty/null/0 và dữ liệu cực trị
- [ ] Phủ min/max và vượt ngưỡng
- [ ] Phủ lỗi mạng/timeout/retry
- [ ] Phủ quyền, phiên và concurrency
