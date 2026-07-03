---
name: requirement-analysis-impact-analysis
description: 
---

# Impact Analysis

**Category:** requirement-analysis · **Status:** 🟢 Active

## When to use
Khi đánh giá một thay đổi ảnh hưởng tới đâu trước khi triển khai.

## Steps
1. Xác định điểm thay đổi gốc: file/module/API/schema nào bị sửa.
2. Truy ngược consumer: ai gọi hàm/API, ai import component, ai đọc field đó.
3. Phân loại ảnh hưởng: breaking vs backward-compatible.
4. Soát hợp đồng dữ liệu: type, API contract, DB migration, cache.
5. Soát mặt UI/UX: màn hình dùng chung, state, i18n, quyền.
6. Liệt kê test cần chạy lại và rủi ro regression; đề xuất cách giảm thiểu.

## Template
```md
## Impact — <thay đổi>
- Điểm thay đổi: <module/API>
- Consumer ảnh hưởng:
  - <A> — breaking? <yes/no>
- Hợp đồng dữ liệu: <type/API/migration>
- UI ảnh hưởng: <màn hình>
- Test cần chạy lại: <…>
- Rủi ro & giảm thiểu: <…>
```

## Example
**Good:** Liệt kê consumer của API đổi field, đánh dấu breaking, kèm migration plan.
**Avoid:** Đổi response API mà không kiểm component/màn hình nào đang đọc field cũ.

## Checklist
- [ ] Xác định rõ điểm thay đổi gốc
- [ ] Liệt kê consumer và đánh dấu breaking
- [ ] Soát type/API contract/migration
- [ ] Liệt kê test regression và rủi ro
