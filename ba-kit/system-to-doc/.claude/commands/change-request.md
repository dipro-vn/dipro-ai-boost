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
   > ⚠️ **CR-3 MANDATORY — clone màn thật của designer trước, KHÔNG build từ token thủ công** (feedback 19/11/2026):
   > 1. Tìm màn tương ứng trong file Figma (`FINAL UI Admin` · `FINAL UI User` · `UI ADMIN/SUPER ADMIN（デザイナー用）` · `UI Usersite (デザイナー用）`) bằng `get_metadata` hoặc `use_figma` search.
   > 2. `use_figma` → `getNodeByIdAsync(srcId).clone()` → paste vào section CR-3 trên FLOW page.
   > 3. Add annotation overlay **trên clone** (dashed rectangle + number badge + label mô tả thay đổi): NEW = xanh `#1A7F37`, UPD = cam `#F4860C`.
   > 4. Màn chưa có trong designer (hoàn toàn mới) → clone màn cùng loại (admin list / admin form / user page) làm **shell** → annotate toàn bộ content area là "NEW".
   > 5. **Không được** build mockup từ token thủ công nếu có designer frame — sẽ cho ra UI xấu, khác website thật.
   > 6. Gắn plugin data `crkit:src` = node ID nguồn khi clone, hoặc `build_mode=token` + `no_designer_reason=<lý do>` khi dựng token. V-CR-FIGMA check 15 kiểm điều này.
6b_review. **Mockup review loop (sub-agent `mockup-reviewer`)** — sau V-CR-FIGMA PASS, gọi Agent tool với `subagent_type=mockup-reviewer` + input (cr_folder, baseline_folder, figma_file_key, cr_figma_nodes, cr_json, auth_cred). Sub-agent chụp Figma mockup + web thật (Playwright), chấm 5 tiêu chí × 10 màn → `_internal/mockup-review.md`. `overall=FIX` → đọc feedback → sửa `cr-figma.json` các màn FIX → rerun render + use_figma + verify + review vòng 2. Vòng 2 FIX tiếp → gắn cờ `manual-review-needed` trong run-log + báo user, **không review vòng 3**. `overall=PASS` → sang 6c.
6c. **HỎI NGAY sau khi Figma PASS** — `AskUserQuestion` **CR-5** (block CR-5 trong flow): hỏi có build HTML viewer không, ghi rõ mục đích (xem offline, không cần tài khoản Figma) + chi phí (~N giây get_screenshot). User chọn `[A]` → chạy 6a + 6b. `[B]` → skip, ghi run-log, sang bước 7
6a. **Export ảnh CR-3** (chỉ khi CR-5 = `[A]`) — agent loop qua mỗi màn NEW/UPD trong `cr-figma.json`, lookup nodeId trong `cr-figma-nodes.json` (kind='mockup'): `get_screenshot(fileKey, nodeId)` MCP Figma, save base64 → `_internal/screens/<ref>.png`
6b. **Build HTML viewer** — (1) `build-cr-prototype.py --cr-json _internal/cr.json --screens-dir _internal/screens --out CR-<id>_screens.html --figma-url <base>` (2) **BẮT BUỘC** `detect-pii.js --scan CR-<id>_screens.html` — FAIL thì không gửi khách
7. `detect-pii.js --scan` · `build-version-index.py` · run-log (`baseline:` + **Feedback đã xử lý**)
8. Báo cáo: folder version mới, baseline đã dùng, **số đối tượng thay đổi** (màn / API / bảng …) × NEW/UPD/DEL/IMPACT, **実装 MD + 総工数 人日 + 人月** (Step 1 / Step 2 + bảng tổng theo phương án của 見積書) (đơn giá DRAFT/APPROVED), xung đột, câu hỏi cần KH trả lời, link Figma
