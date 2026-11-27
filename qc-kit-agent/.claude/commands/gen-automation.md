---
description: Sinh & chạy Playwright automation script từ file test case (`[module]-testcases-vN.md`) có sẵn, dùng Playwright MCP để recon DOM thật. Auto-heal lỗi phía script (tối đa 2 vòng), assertion fail được báo là nghi bug. Bắt buộc phải có test-cases.md trước khi chạy.
skills:
  - automation_engineer
---

Thực hiện đầy đủ **Section 1–6** từ skill `automation_engineer`.

## Bước 0 — Kiểm tra file test case (bắt buộc)

Lấy file TC mới nhất: `python3 -I .claude/scripts/module_files.py latest testing/[module] testcases` (tên theo "Quy ước file và version" trong skill `rbt_manual_testing`: `[module]-testcases-vN.md`; tên cũ `test-cases.md` tính là v1). Nêu version đang dùng trong tóm tắt. Mọi chỗ dưới đây viết `test-cases.md` là tên gọi tắt của file này.

Chạy thêm `module_files.py latest testing/[module] testcases xlsx`: nếu xlsx có version **lớn hơn** md thì in cảnh báo một dòng `xlsx đang chạy là vX nhưng md mới nhất chỉ là vY, md có thể đã cũ` rồi vẫn dùng md (hoặc dừng nếu user muốn đồng bộ md trước bằng /update-tcs).

Không lấy được file nào nghĩa là module chưa có test case:

**Không có** → dừng lại, thông báo:

> ⚠️ Module này chưa có file test case. Chạy `/gen-tcs` trước để sinh test case, sau đó quay lại `/gen-automation`.

**Có** → tiếp tục Bước 1.

## Bước 1 — Setup & Scaffold

Thực hiện **Section 1** từ skill `automation_engineer`:
- Kiểm tra `automation/package.json` — nếu chưa có, scaffold project Playwright TypeScript tối thiểu (xác nhận base URL với user trước).
- Nếu đã có, bỏ qua, sang Bước 2.

## Bước 2 — Chọn phạm vi TC

Thực hiện **Section 2**:
- Liệt kê TC từ `test-cases.md`, đề xuất phạm vi mặc định theo mục `## High Risk & E2E`: TC của Bảng 2 (E2E) trước, rồi Bảng 1 (nhóm high risk) nếu có.
- **Hỏi user xác nhận danh sách TC** trước khi sang Bước 3 — đây là checkpoint bắt buộc duy nhất.

## Bước 3 — MCP Recon

Thực hiện **Section 3**: mở Playwright MCP, đi qua từng bước của TC đã chọn trên browser thật, thu thập + verify locator. Ghi bảng Locator Collection. Không đoán locator.

## Bước 4 — Sinh code

Thực hiện **Section 4**: sinh Page Object (`automation/pages/<module>/`) + Test (`automation/tests/<module>/`) từ Locator Collection, gắn TC ID (cột `ID`) vào tên test và ghi kèm Traceability ID trong comment.

## Bước 5 — Run & Auto-heal

Thực hiện **Section 5**: chạy `npx playwright test`; TC fail được phân loại — lỗi phía script thì tự sửa tối đa 2 vòng, chỉ chạy lại TC fail (`--last-failed`). **Assertion fail không heal**, ghi nhận là nghi bug. Không hỏi user trừ CAPTCHA-2FA / không phân biệt được lỗi script hay nghi bug.

## Bước 6 — Report

Thực hiện **Section 6**: cập nhật `automation/task.md`, sinh `testing/[module]/[module]-automation-report-vN.md` (N = version của file TC đang chạy; lấy đường dẫn bằng `module_files.py path testing/[module] automation-report N`; chạy lại cùng N thì ghi đè, TC lên version mới thì giữ report cũ) (PASS / Nghi bug / Không chạy được, ID `BUG-<TC ID>`), tóm tắt trong chat.

## Output

`automation/` project (mới hoặc mở rộng), Page Object + Test classes, `testing/[module]/[module]-automation-report-vN.md`, `automation/task.md`.
