---
description: Ghi Basic Design AS-IS vào master Excel của công ty (Output 2A — cần Output 1 đã xong)
---

Hãy là **System Analyst**, chạy **Output 2A — Basic Design**.

Phạm vi / master workbook: $ARGUMENTS

Bắt buộc Read trước khi ghi:
- `.claude/sys-agent/outputs/output-2a-basic-design.md`
- `.claude/sys-agent/basic-design/workbook-structure.md`

Điều kiện vào: Output 1 đã qua gate V1 · V2 · V3 · V5 với `FAIL = 0`. Chưa đạt → DỪNG, nói rõ thiếu gì.

Bắt buộc:
1. Hỏi **G12** (scope + đường dẫn master workbook) bằng `AskUserQuestion`
2. **Backup master workbook** trước khi ghi bất cứ thứ gì
3. Master có sheet lạ → hỏi **G14**, TUYỆT ĐỐI không tự xoá
4. Chạy `verify-basic-design.py --asis`, `FAIL = 0` mới báo xong
