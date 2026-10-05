---
description: Luồng 2 — phân tích ảnh hưởng của 1 Change Request lên hệ thống hiện tại (dựa trên baseline mới nhất). Dùng: /change-request <file trong inputs/cr/ | link | dán nội dung>
---

Hãy là **System Analyst**. Đọc `.claude/agents/system-analyst.md` §4 và **`.claude/sys-agent/flow-2-change-request.md`**, rồi chạy **Luồng 2 — Change Request**.

Yêu cầu thay đổi: $ARGUMENTS

`$ARGUMENTS` rỗng → hỏi user đưa CR theo 1 trong 3 cách: bỏ file vào `inputs/cr/` · dán nội dung · gửi link.

Bắt buộc, không rút gọn:
0. `ensure-env.py --flow 2` — **tự cài** thư viện còn thiếu; user không phải cài gì
1. `version-tool.py latest-baseline --outputs outputs` + `list --outputs outputs` — **chưa có baseline → DỪNG**, đề nghị chạy `/analyze-system`
2. Lưu CR nguyên văn (đã che dữ liệu cá nhân) · tách thành item · phân loại CR / BUG / QUESTION / CHƯA RÕ bằng bằng chứng baseline
3. Hỏi **CR-0** xác nhận baseline + mã CR; chỗ mơ hồ hỏi **CR-1** — không tự chọn đáp án
4. `version-tool.py next --outputs outputs --cr-id CR-<id> --slug <tên-ngắn> --create` → **giải trình vì sao là CR** (C1–C6, trích baseline) → phân tích đủ **6 trục** System · DB · Business · Screen · Third-party · Mockup (NEW / UPD / DEL / IMPACT, vì sao phải sửa, mã đơn giá + số lượng; trục không ảnh hưởng ghi lý do) → `_internal/cr.json` → `build-cr-impact.py`
5. `verify-cr-impact.py --cr-json … --baseline <baseline>` — `FAIL = 0`. **MD do script tính** — không gõ tay
6. Figma (hỏi **CR-2**): chọn vẽ → `ensure-env.py --flow 2 --figma` (tự thêm Figma MCP; `NEED_AUTH` → nhờ user `/mcp` → Authenticate) → section CR **mới**, chỉ hạng mục Impact + hàng xóm 1 bước, badge NEW/UPD/DEL/IMPACT/AS-IS — **không vẽ đè, không sửa node cũ**; `verify-cr-figma.py` — `FAIL = 0`
7. `detect-pii.js --scan` · `build-version-index.py` · run-log
8. Báo cáo: folder version mới, baseline đã dùng, số hạng mục theo trục × loại, **tổng MD** (đơn giá DRAFT/APPROVED), xung đột, câu hỏi cần KH trả lời, link Figma
