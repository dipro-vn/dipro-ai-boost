---
description: Luồng 2 — phân tích ảnh hưởng của 1 Change Request lên hệ thống hiện tại (dựa trên baseline mới nhất). Dùng: /change-request <file trong inputs/cr/ | link | dán nội dung>
model: opus
---

Hãy là **System Analyst**. Đọc `.claude/agents/system-analyst.md` §4 và **`.claude/sys-agent/flow-2-change-request.md`**, rồi chạy **Luồng 2 — Change Request**.

Yêu cầu thay đổi: $ARGUMENTS

`$ARGUMENTS` rỗng → hỏi user đưa CR theo 1 trong 3 cách: bỏ file vào `inputs/cr/` · dán nội dung · gửi link.

Bắt buộc, không rút gọn:
0. `ensure-env.py --flow 2` — **tự cài** thư viện còn thiếu; user không phải cài gì
1. `version-tool.py context --outputs outputs --flow 2 [--cr-id CR-<id> nếu CR đã có]` — **agent tự lấy version mới nhất**: baseline mới nhất để đối chiếu, version mới nhất của chính CR này (chạy lại → đọc `cr.json` cũ làm điểm xuất phát), CR khác đang mở, feedback chưa xử lý; Read các file trong `read`. **Chưa có baseline → DỪNG**, đề nghị chạy `/analyze-system`
2. Lưu CR nguyên văn (đã che dữ liệu cá nhân) · tách thành item · phân loại CR / BUG / QUESTION / CHƯA RÕ bằng bằng chứng baseline
3. Hỏi **CR-0** xác nhận baseline + mã CR; chỗ mơ hồ hỏi **CR-1** — không tự chọn đáp án
4. `version-tool.py next --outputs outputs --cr-id CR-<id> --slug <tên-ngắn> --create` (folder `CR-<id>_<DDMMYY>_<slug>`, khoá baseline; CR đã có folder → `reuse:true`, `snapshot` trước khi ghi đè) → **giải trình vì sao là CR** (C1–C6, trích baseline) → phân tích đủ **6 trục** System · DB · Business · Screen · Third-party · Mockup (NEW / UPD / DEL / IMPACT, vì sao phải sửa, mã đơn giá + số lượng; trục không ảnh hưởng ghi lý do) → `_internal/cr.json` (mọi hạng mục có `cr_item` + `option` 拡張案) → `build-cr-impact.py` → **7 sheet** Summary (công số + số đối tượng + link) · Estimation (template 見積書) · Screen · API · Database · Figma · Q&A
5. `verify-cr-impact.py --cr-json … --baseline <baseline>` — `FAIL = 0`. **MD do script tính** — không gõ tay
5b. **見積書** (`sys-agent/estimate-rules.md` + **đọc `sys-agent/writing-style.md` trước khi viết chữ cho khách**; câu hỏi nghiệp vụ gửi khách khai ở `estimate.json → questions`, hỏi **CR-4**: chia Step · phương án đưa vào · ai duyệt bảng công số): `_internal/estimate.json` (dòng = màn × thao tác, ja / vi, phương án thay thế = dòng riêng) → `build-estimate.py` → `CR-<id>_見積書.xlsx` (tiếng Nhật, gửi KH) → `verify-estimate.py` (V-EST) `FAIL = 0` → build lại Impact với `--estimate` + `verify-cr-impact.py --estimate`
6. Figma (hỏi **CR-2**, **CR-3** phạm vi màn đề xuất, **CR-3b** khi thiếu component DS): chọn vẽ → `ensure-env.py --flow 2 --figma` (tự thêm Figma MCP; `NEED_AUTH` → nhờ user `/mcp` → Authenticate) → đọc `sys-agent/figma/cr-view.md` → **đọc Design System baseline trước** (README · tokens.json · component · STATUS) → viết `_internal/cr-figma.json` → `render-cr-figma.py` → `use_figma` từng file JS: section **mới** — CR-1 Flow **format Output 1** · CR-2 Screen Flow **format Output 2** (mũi tên thật) · CR Change Table **thống kê** (không liệt kê chi tiết) · CR-3 màn đề xuất bằng token DS — **không vẽ đè, không sửa node cũ** → `99-readback.js` → `verify-cr-figma.py --view …` — `FAIL = 0`
7. `detect-pii.js --scan` · `build-version-index.py` · run-log (`baseline:` + **Feedback đã xử lý**)
8. Báo cáo: folder version mới, baseline đã dùng, **số đối tượng thay đổi** (màn / API / bảng …) × NEW/UPD/DEL/IMPACT, **実装 MD + 総工数 人日 + 人月** (Step 1 / Step 2 + bảng tổng theo phương án của 見積書) (đơn giá DRAFT/APPROVED), xung đột, câu hỏi cần KH trả lời, link Figma
