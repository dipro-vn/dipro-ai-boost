---
description: Lập danh sách lỗi đang tồn tại trong hệ thống để báo khách hàng (Output 2B)
---

Hãy là **System Analyst**, chạy **Output 2B — Bug List**.

Phạm vi: $ARGUMENTS

Bắt buộc Read trước: `.claude/sys-agent/outputs/output-2b-bug-list.md`

Đây là tài liệu **đi ra ngoài công ty** — ngưỡng bằng chứng cao nhất trong kit:
1. Hỏi **G13** (phạm vi quét + gửi khách hay nội bộ review trước) bằng `AskUserQuestion`
2. Mỗi bug phải có **≥ 2 bước tái hiện đánh số** + `EV ID` phân giải được
3. `Reproduced = No` → sheet `Suspected`, **không** lọt sheet gửi khách
4. Nghi vấn `Security` không có PoC → sheet `Observations`, **không** gọi là bug
5. Chạy `verify-bug-list.py`, `FAIL = 0` mới báo xong
6. `g13_recipient = Nội bộ review trước` → DỪNG chờ người duyệt, không tự gửi
