---
description: Luồng 2 — phân tích ảnh hưởng của 1 Change Request lên hệ thống hiện tại (dựa trên baseline mới nhất). Dùng: /change-request <file trong inputs/cr/ | link | dán nội dung>
---

Hãy là **System Analyst**. Đọc `.claude/agents/system-analyst.md` §4 và **`.claude/sys-agent/flow-2-change-request.md`**, rồi chạy **Luồng 2 — Change Request**.

Yêu cầu thay đổi: $ARGUMENTS

`$ARGUMENTS` rỗng → hỏi user đưa CR theo 1 trong 3 cách: bỏ file vào `inputs/cr/` · dán nội dung · gửi link.

Bắt buộc, không rút gọn:
1. `version-tool.py latest-baseline --outputs outputs` + `list --outputs outputs` — **chưa có baseline → DỪNG**, đề nghị chạy `/analyze-system`
2. Lưu CR nguyên văn (đã che dữ liệu cá nhân) · tách thành item · phân loại CR / BUG / QUESTION / CHƯA RÕ bằng bằng chứng baseline
3. Hỏi **CR-0** xác nhận baseline + mã CR; chỗ mơ hồ hỏi **CR-1** — không tự chọn đáp án
4. `version-tool.py next --outputs outputs --cr-id CR-<id> --slug <tên-ngắn> --create` → `build-inventory.py --cr` → phân tích đủ **6 trục**: System · DB · Business · Screen · Third-party · Mockup (trục không ảnh hưởng ghi `NONE` + lý do)
5. `verify-cr-impact.py --baseline <baseline>` — `FAIL = 0`
6. Figma (hỏi **CR-2**): section CR **mới**, chỉ phần CR + hàng xóm 1 bước, badge NEW/UPD/DEL/AS-IS — **không vẽ đè, không sửa node cũ**
7. `CR-<id>_Summary.md` ≤ 1 trang · `detect-pii.js --scan` · `build-version-index.py` · run-log
8. Báo cáo: folder version mới, baseline đã dùng, số thay đổi theo từng trục, xung đột, câu hỏi cần KH trả lời, link Figma
