---
description: Luồng 1 — khảo sát hệ thống có sẵn, 1 lệnh 2 giai đoạn: Giai đoạn 1 đọc source code ra output nhanh (Overview · API · DB · Figma · Basic Design · chạy local) → dừng cho xem trước → Giai đoạn 2 AI Playwright kiểm tra trên website, thêm Design System + Bug list
model: opus
---

Hãy là **System Analyst**. Đọc `.claude/agents/system-analyst.md` và chạy **Luồng 1** (§3): **1 lệnh, 2 giai đoạn** — Giai đoạn 1 đọc source code cho ra output nhanh, **dừng để người dùng xem trước**, rồi Giai đoạn 2 (AI Playwright) khi người dùng đồng ý.

Đối tượng / gợi ý ban đầu của user: $ARGUMENTS

**Giai đoạn 1 — đọc source code (BE · FE · Mobile), không mở website:**
0. `ensure-env.py --flow 1` (tự cài thư viện thiếu) → `version-tool.py context --outputs outputs --flow 1`. Có baseline → hỏi **G-R**; `suggest.flow1_phase = 2` (Giai đoạn 1 đã xong lần trước) → hỏi "chạy tiếp Giai đoạn 2 hay sửa Giai đoạn 1 theo góp ý trước" → chạy tiếp thì nhảy tới Giai đoạn 2
1. Preflight Giai đoạn 1 (`preflight-questions.md` §0 · §0b, `preflight-memory.py missing --phase 1`): tên / phạm vi · **web hay app** · source code · DB · Figma · ngôn ngữ. **Chưa hỏi tài khoản website / 4 câu an toàn**
2. `scan-sensitive.py` (exit 3 → **cảnh báo + DỪNG**) → đọc code (Pha A) → `extract-design-tokens.py --code-only` → **Discovery Brief** + Quyết định lớn, DỪNG chờ confirm → `version-tool.py next --outputs outputs --slug <slug> --create` (ghi đè ver chưa khoá: `version-tool.py snapshot` trước)
3. Inventory từ code → gate V1 · V2
4. Sinh O2 → O3 → O5 → O4 → O8 (mỗi output qua gate, `FAIL = 0`; V-BD `--phase 1`). O5: `scan-sensitive.py --high-list` → bộ trích AST `ast/extract-screen.mjs` (thiếu S1 → không trích; không phải React JSX → báo chưa hỗ trợ) → LLM viết spec theo nghiệp vụ → `build-basic-design.py --spec … --ast-spec …`
5. Viết `business.json` → vẽ luồng nghiệp vụ bằng skill **archify** (workflow, `finalize` PASS) → xuất PNG → O1 `render-overview-docx.py --flow-image <png>` → gate V3
6. Self-test · `detect-pii.js --scan` · `build-version-index.py --skip "O6=chờ Giai đoạn 2" --skip "O7=chờ Giai đoạn 2"` · run-log

**Điểm dừng:**
7. Báo cáo Giai đoạn 1 (§8 của agent: đường dẫn + bảng output + **danh sách 7 việc giai đoạn 2 sẽ làm**, đúng mẫu "Báo cáo ở điểm dừng") → `AskUserQuestion`: **"Giai đoạn 1 đã chạy xong — bạn xem trước các output trên. Chạy tiếp Giai đoạn 2?"** `[A] Chạy tiếp ngay` · `[B] Dừng để tôi review — lần sau gọi /analyze-system sẽ chạy tiếp` · `[C] Không chạy Giai đoạn 2`. App → không hỏi, báo "Phần mềm là app nên không có Giai đoạn 2", đóng. **Không tự sang Giai đoạn 2 khi chưa có câu trả lời.**

**Giai đoạn 2 — AI Playwright trên website (chạy lâu, ít token):**
8. Preflight Giai đoạn 2 (`preflight-memory.py missing --phase 2`): website (URL · môi trường) · tài khoản + quyền · mức thao tác · vùng cấm · dữ liệu thật · Bug list — **4 câu an toàn luôn hỏi lại** → `ensure-env.py --flow 1 --browser`
9. `version-tool.py snapshot --ver <ver>` → `login-site.js` / `crawl-site.js` (seed từ route FE của Giai đoạn 1; đăng nhập lỗi → nhờ đăng nhập tay `--manual`)
10. Đối chiếu inventory với màn hình thật — chỉ bổ sung phần code không cho biết; khác code → Open Question → gate V1 · V2 (`--crawled`)
11. O5: chụp màn hình, đánh số item, chèn vào từng sheet (V-BD) · cập nhật O2 / O3 / O4 nếu đổi · O6 Design System (tuỳ chọn, V-DS) · O7 Bug list (V8)
12. Render lại O1 → self-test · `detect-pii.js --scan` · `build-version-index.py` (bỏ `--skip` O6 / O7) · run-log → báo cáo cuối **"Giai đoạn 2 đã chạy xong"** + bảng output + phần đã đổi so với Giai đoạn 1
