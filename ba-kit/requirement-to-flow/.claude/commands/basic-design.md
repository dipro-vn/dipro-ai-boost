---
description: Tạo hoặc cập nhật Basic Design (Output 5) trên master Excel. Dùng: /basic-design [Screen ID, phân cách dấu phẩy]
---

Đọc `.claude/ba-agent/basic-design/output-5-basic-design.md` và `.claude/ba-agent/basic-design/workbook-structure.md`, rồi thực hiện **Output 5 — Basic Design** cho phạm vi: **$ARGUMENTS**

Bắt buộc theo đúng thứ tự, không được rút gọn:

1. **§1 Input Gate** — kiểm SPEC.md có `## Screens` + `## Screen Details`; xác định master workbook; kiểm Output 3 có ảnh cho màn nào không
2. **§1.2** — nếu master khởi tạo từ file mẫu: liệt kê sheet không thuộc SPEC dự án
3. **§2 Proposal Gate** — **BẮT BUỘC gọi `AskUserQuestion`**, không in text rồi tự chạy tiếp:
   - Câu 1 (luôn): Output 1 & Output 2 đã chốt chưa
   - Câu 2 (khi có Output 3): có chèn ảnh UI không
   - Câu 3 (luôn): phạm vi screen
   - Câu 4 (khi có sheet lạ): xử lý sheet không thuộc dự án
4. **§4 Bước 0** — backup master vào `versions/v<N>_<DDMMYYYY>/basic_design_before.xlsx` **trước khi ghi**
5. **§4 hoặc §5** — Create New hoặc Change Spec
6. **§6 Quality Gate O5** — chạy `verify-basic-design.py`, `FAIL = 0` mới được đi tiếp
7. **§7** — dừng ở `WAITING FOR BRSE APPROVAL`
8. **§8** — in Runtime response contract 9 field

Nếu `$ARGUMENTS` rỗng → không tự chọn toàn bộ screen; hỏi phạm vi ở Proposal Gate Câu 3.
