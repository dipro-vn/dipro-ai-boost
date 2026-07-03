---
name: testing-jest-coverage-analysis
description: 
---

# Coverage Analysis

**Category:** testing-jest · **Status:** 🟢 Active

## When to use
Khi đọc báo cáo coverage, vá nhánh thiếu, tránh chạy theo % một cách mù quáng.

## Steps
1. Chạy `jest --coverage`, đọc cột Branch/Function chứ không chỉ % Lines.
2. Mở HTML report, tìm dòng/nhánh đỏ chưa được test (if/else, ternary, optional chain).
3. Ưu tiên vá nhánh ở logic quan trọng (tính toán, phân quyền, lỗi) hơn code tầm thường.
4. Coverage cao không đảm bảo đúng — assert phải kiểm tra hành vi, không chỉ chạy qua dòng.
5. Đặt ngưỡng `coverageThreshold` hợp lý, loại trừ file generated/config.

## Template
```js
// jest.config.js
module.exports = {
  collectCoverage: true,
  coveragePathIgnorePatterns: ['/node_modules/', '\\.generated\\.'],
  coverageThreshold: {
    global: { branches: 80, functions: 80, lines: 80 },
  },
};
```

## Example
**Good:** nhắm nhánh đỏ ở logic quan trọng, assert hành vi, ngưỡng theo branch.
**Avoid:** thêm test rỗng chỉ để tăng %, bỏ qua branch, đặt threshold 100% cứng nhắc.

## Checklist
- [ ] Đọc Branch/Function, không chỉ Lines
- [ ] Vá nhánh ở logic quan trọng trước
- [ ] Assert kiểm tra hành vi thật
- [ ] Threshold hợp lý, loại trừ file generated
