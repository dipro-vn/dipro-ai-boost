---
description: "Optional — Dùng khi module phức tạp: phân rã thành Sub-modules, đánh giá risk level để /gen-tcs test sâu đúng chỗ. Core path 3 bước không cần bước này."
skills:
  - rbt_manual_testing
---

Thực hiện **Section 3: Module Decomposition** từ skill `rbt_manual_testing`.

## Hướng dẫn

1. Đọc `testing/[module]/analysis.md` (Summary section có đủ module context)
2. Phân rã theo UI (Header, Form, Table...) hoặc theo luồng (Flow tạo mới, Flow xóa...) — chọn cách phù hợp với tính năng
3. Đánh giá Risk Level cho từng sub-module (High / Medium / Low)
4. Xác định Dependencies giữa các Module
5. Lưu output ra `testing/[module]/modules.md`

## Input cần thiết

- `testing/[module]/analysis.md`

## Output

`testing/[module]/modules.md`

## Bước tiếp theo

Sau khi có `modules.md`, chạy `/gen-tcs` để sinh Test Scenarios.
