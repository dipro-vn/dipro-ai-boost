---
description: Sinh & chạy Playwright automation script từ test-cases.md có sẵn, dùng Playwright MCP để recon DOM thật. Có vòng lặp auto-heal khi test FAIL. Bắt buộc phải có test-cases.md trước khi chạy.
skills:
  - automation_engineer
---

Thực hiện đầy đủ **Section 1–6** từ skill `automation_engineer`.

## Bước 0 — Kiểm tra `test-cases.md` (bắt buộc)

Kiểm tra `testing/[module]/test-cases.md` có tồn tại không:

**Không có** → dừng lại, thông báo:

> ⚠️ Module này chưa có `test-cases.md`. Chạy `/gen-tcs` trước để sinh test case, sau đó quay lại `/gen-automation`.

**Có** → tiếp tục Bước 1.

## Bước 1 — Setup & Scaffold

Thực hiện **Section 1** từ skill `automation_engineer`:
- Kiểm tra `automation/package.json` — nếu chưa có, scaffold project Playwright TypeScript tối thiểu (xác nhận base URL với user trước).
- Nếu đã có, bỏ qua, sang Bước 2.

## Bước 2 — Chọn phạm vi TC

Thực hiện **Section 2**:
- Liệt kê TC từ `test-cases.md`, đề xuất phạm vi mặc định (Risk cao nhất theo `plan-tcs.md` nếu có).
- **Hỏi user xác nhận danh sách TC** trước khi sang Bước 3 — đây là checkpoint bắt buộc duy nhất.

## Bước 3 — MCP Recon

Thực hiện **Section 3**: mở Playwright MCP, đi qua từng bước của TC đã chọn trên browser thật, thu thập + verify locator. Ghi bảng Locator Collection. Không đoán locator.

## Bước 4 — Sinh code

Thực hiện **Section 4**: sinh Page Object (`automation/pages/<module>/`) + Test (`automation/tests/<module>/`) từ Locator Collection, gắn Traceability ID gốc.

## Bước 5 — Run & Auto-heal

Thực hiện **Section 5**: chạy `npx playwright test`, nếu FAIL thì tự sửa tối đa 5 vòng (không hỏi user, trừ business logic mâu thuẫn / CAPTCHA-2FA / hết 5 vòng). PASS xong verify ổn định 2 lần.

## Bước 6 — Cleanup & Report

Thực hiện **Section 6**: dọn code, cập nhật `automation/task.md`, báo cáo PASS/FAIL/SKIP + Locator Collection cho user.

## Output

`automation/` project (mới hoặc mở rộng), Page Object + Test classes đã chạy PASS, `automation/task.md`, báo cáo kết quả.
