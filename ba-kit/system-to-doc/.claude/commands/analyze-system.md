---
description: Phân tích hệ thống đã có sẵn (website / source code / DB / file KH) thành tài liệu High Level
---

Hãy là **System Analyst**. Đọc `.claude/agents/system-analyst.md` và chạy đúng quy trình 10 bước để tạo **Output 1 — High Level System Analysis**.

Đối tượng phân tích: $ARGUMENTS

Bắt buộc, không được rút gọn:
1. Bước 0.5 — đọc version trước nếu có (`versions/v*/`), chạy Gate **G-R**
2. Bước 1 — hỏi đủ **G0 → G7** bằng `AskUserQuestion`, không đoán
3. Bước 2 — in **Discovery Brief**, DỪNG chờ confirm
4. Bước 3 — recon ở chế độ **read-only** trừ khi G2 cho phép khác
5. Bước 4–7 — Evidence Ledger → reconcile → flow PNG → render docx + inventory.xlsx
6. Chạy gate **V1 · V2 · V3 · V5 · V9**, `FAIL = 0` mới được báo xong
7. Bước 8 — hỏi **Proposal Gate G11** (Output 2), **1 lần duy nhất**

Không tự chạy Output 2A/2B khi chưa có câu trả lời G11.
