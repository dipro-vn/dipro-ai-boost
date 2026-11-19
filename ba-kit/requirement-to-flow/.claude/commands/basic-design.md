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
6b. **Basic Design Review loop** (bắt buộc sau Quality Gate PASS):
    - Gọi sub-agent `basic-design-reviewer` (`.claude/agents/basic-design-reviewer.md`) qua Agent tool, truyền: `workbook_path`, `spec_path`, `versions_dir`, `round=1`
    - **`overall=PASS`** → sang bước 7
    - **`overall=FIX`** → đọc `versions_dir/basic-design-review-round1.md` → sửa spec JSON theo fix instructions → re-run `build-basic-design.py` → re-run `verify-basic-design.py` PASS → gọi lại sub-agent `round=2`
    - **Round 2 vẫn `FIX`** → gắn cờ `manual-review-needed` vào `versions_dir/run-log.md` (danh sách issue còn lại + lý do), báo user, **không loop vòng 3**
7. **§7** — dừng ở `WAITING FOR BRSE APPROVAL`
8. **§8** — in Runtime response contract 9 field

Nếu `$ARGUMENTS` rỗng → không tự chọn toàn bộ screen; hỏi phạm vi ở Proposal Gate Câu 3.
