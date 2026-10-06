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
4. `version-tool.py next --outputs outputs --cr-id CR-<id> --slug <tên-ngắn> --create` → **giải trình vì sao là CR** (C1–C6, trích baseline) → phân tích đủ **6 trục** System · DB · Business · Screen · Third-party · Mockup (NEW / UPD / DEL / IMPACT, vì sao phải sửa, mã đơn giá + số lượng; trục không ảnh hưởng ghi lý do) → `_internal/cr.json` (mọi hạng mục có `cr_item` + `option` 拡張案) → `build-cr-impact.py` → **7 sheet** Summary (công số + số đối tượng + link) · Estimation (template 見積書) · Screen · API · Database · Figma · Q&A
5. `verify-cr-impact.py --cr-json … --baseline <baseline>` — `FAIL = 0`. **MD do script tính** — không gõ tay
6. Figma (hỏi **CR-2**, **CR-3** phạm vi màn đề xuất, **CR-3b** khi thiếu component DS): chọn vẽ → `ensure-env.py --flow 2 --figma` (tự thêm Figma MCP; `NEED_AUTH` → nhờ user `/mcp` → Authenticate) → đọc `sys-agent/figma/cr-view.md` → **đọc Design System baseline trước** (README · tokens.json · component · STATUS) → viết `_internal/cr-figma.json` → `render-cr-figma.py` → `use_figma` từng file JS: section **mới** — CR-1 Flow **format Output 1** · CR-2 Screen Flow **format Output 2** (mũi tên thật) · CR Change Table **thống kê** (không liệt kê chi tiết) · CR-3 màn đề xuất bằng token DS — **không vẽ đè, không sửa node cũ** → `99-readback.js` → `verify-cr-figma.py --view …` — `FAIL = 0`
7. `detect-pii.js --scan` · `build-version-index.py` · run-log
8. Báo cáo: folder version mới, baseline đã dùng, **số đối tượng thay đổi** (màn / API / bảng …) × NEW/UPD/DEL/IMPACT, **実装 MD + 総工数 人日 + 人月** (最小改修案 / 拡張案) (đơn giá DRAFT/APPROVED), xung đột, câu hỏi cần KH trả lời, link Figma
