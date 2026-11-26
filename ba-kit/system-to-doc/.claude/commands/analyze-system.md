---
description: Luồng 1 — khảo sát hệ thống có sẵn, 1 lệnh 2 giai đoạn. Giai đoạn 1 chỉ đọc code (offline, nhanh, không hỏi Figma/website); giai đoạn 2 Playwright + Figma (sau điểm dừng, có xác nhận). Feedback 25/11/2026.
model: opus
---

Hãy là **System Analyst**. Đọc `.claude/agents/system-analyst.md` và chạy **Luồng 1** (§3): **1 lệnh, 2 giai đoạn** — G1 chỉ đọc code, **dừng để người dùng xem trước**, rồi G2 (AI Playwright + Figma) khi người dùng đồng ý.

Đối tượng / gợi ý ban đầu của user: $ARGUMENTS

**Flag `--light`** (feedback 22/11/2026 P1-4): scope ≤5 màn → bỏ các bước thủ tục nặng: không snapshot history · không build README chi tiết · dùng skeleton + spec ngắn (feedback 22/11/2026 P1-4) · vẫn chạy O1-O8 đầy đủ. Dùng khi dự án nhỏ hoặc sửa lại 1 góc nhỏ.

**Nếu chỉ cần sửa BD thôi** (không touch output khác): dùng `/basic-design` (feedback 22/11/2026 P1-6) thay vì `/analyze-system` — nhanh hơn, ít token hơn.

---

**Giai đoạn 1 — chỉ đọc source code (offline, nhanh):**

0. `ensure-env.py --flow 1` (tự cài thư viện thiếu) → `version-tool.py context --outputs outputs --flow 1`. Có baseline → hỏi **G-R**; `suggest.flow1_phase = 2` → hỏi "chạy tiếp G2 hay sửa G1 theo góp ý trước" → chạy tiếp thì nhảy tới G2.
1. **Preflight G1** (`preflight-questions.md` §0 · §0b, `preflight-memory.py missing --phase 1`): tên / phạm vi · **web hay app** · source code · DB · ngôn ngữ. **KHÔNG hỏi Figma, không hỏi tài khoản website, không hỏi 4 câu an toàn** — thuộc G2 (feedback 25/11/2026).
2. `scan-sensitive.py` (exit 3 → **cảnh báo + DỪNG**) → đọc code (Pha A) → `extract-design-tokens.py --code-only` → **Discovery Brief** + Quyết định lớn (B1–B5), DỪNG chờ confirm → `version-tool.py next --outputs outputs --slug <slug> --create`.
3. **Inventory** từ code → gate V1 · V2.
4. **Multi-output parallel** — sinh **4 output cùng lúc** (chạy các tool call cùng lượt, không chờ nhau), vì không phụ thuộc nhau sau khi Pha A đã xong:
   - **O2** API Documentation → gate V-API
   - **O3** DB Documentation + ERD → gate V-DB
   - **O8** DevSetup → gate V-DEV
   - **O5** Basic Design **(code-only, chưa có ảnh)** — `ast/extract-screen.mjs` → LLM viết spec → `build-basic-design.py --spec … --ast-spec … --phase 1` → gate **V-BD `--phase 1`** → ◇ sub-agent **basic-design-reviewer vòng 1** (chỉ chạy sau khi V-BD phase 1 PASS cho từng site)

   **KHÔNG sinh O4 Figma ở G1** (dời xuống G2 vì cần link Figma + Figma MCP). FAIL=0 cho mọi gate mới được sang bước 5.
5. **O1 Overview docx** — viết `_internal/business.json` (tổng hợp từ O2/O3/O5 + inventory) → **[BẮT BUỘC, KHÔNG SKIP]** gọi skill **archify** (workflow, chờ `finalize` PASS) → xuất PNG → `render-overview-docx.py --flow-image <png>` → gate V3. ⛔ Không được gọi `render-overview-docx.py` trước khi có PNG từ archify.
6. Self-test · `detect-pii.js --scan` · `build-version-index.py --skip "O4=chờ G2" --skip "O6=chờ G2" --skip "O7=chờ G2"` · run-log.

**Điểm dừng — thông báo cuối G1 (bắt buộc đủ 3 phần):**

7. Gọi `AskUserQuestion` sau khi in báo cáo G1 theo mẫu bên dưới. App → không hỏi, báo "Phần mềm là app nên không có G2", đóng. **Không tự sang G2 khi chưa có câu trả lời.**

   ```
   ✅ Giai đoạn 1 đã chạy xong — các output có thể xem ngay:
      • O1 Overview.docx — tổng quan hệ thống + luồng nghiệp vụ
      • O2 API Doc · O3 DB Doc + ERD · O5 Basic Design (code-only, chưa ảnh) · O8 DevSetup
      Thư mục: outputs/<ver>/

   🧡 Giai đoạn 2 sẽ truy cập **Figma + website** (dịch vụ ngoài công ty) nên chạy LÂU HƠN RẤT NHIỀU so với G1:
      • Chụp ảnh thật của từng màn chèn vào O5 + đánh số item
      • Sinh **O6 Design System** — bộ token màu/font/component quan sát được từ website
         → Lý do quan trọng: Luồng 2 /change-request dùng O6 để vẽ CR-3 màn đề xuất
           bám giao diện website; thiếu O6 thì CR-3 dựng bằng token thủ công, UI xấu
           + khác website thật (feedback 19/11/2026 của khách).
      • Vẽ O4 Figma flow (Output 1 use-case + Output 2 site→flow→màn)
      • (tuỳ chọn) O7 Bug list — hỏi riêng trước khi chạy

   Bạn muốn:
      [A] Chạy tiếp G2 ngay
      [B] Dừng để tôi review — lần sau gọi /analyze-system sẽ tự chạy tiếp từ đây
      [C] Không chạy G2 — baseline chỉ gồm output G1
   ```

---

**Giai đoạn 2 — AI Playwright + Figma (sau điểm dừng, chạy lâu):**

8. **Preflight G2** (`preflight-memory.py missing --phase 2`):
   - Lượt 2 — website (URL · môi trường) · tài khoản + quyền · mức thao tác · vùng cấm
   - **Lượt 4 — Figma** (link file Figma có sẵn để bổ sung DS · link file Figma để vẽ flow) — **mới dời xuống đây từ G1**
   - P9 Bug list · P11 dữ liệu thật
   - **4 câu an toàn luôn hỏi lại** (P1-env · P2b · P3 · P11)
   - → `ensure-env.py --flow 1 --browser` + `ensure-env.py --flow 1 --figma` (nếu Lượt 4 có link)
9. `version-tool.py snapshot --ver <ver>` → `login-site.js` / `crawl-site.js` (seed từ route FE của G1; đăng nhập lỗi → nhờ đăng nhập tay `--manual`).
10. Đối chiếu inventory với màn hình thật — chỉ bổ sung phần code không cho biết; khác code → Open Question → gate V1 · V2 (`--crawled`).
11. **Multi-output parallel** sau crawl — chạy 3 output cùng lúc (không chờ):
    - **O5 chèn ảnh + đánh số** (`build-basic-design.py` + screenshots từ crawl) → gate V-BD → ◇ sub-agent **basic-design-reviewer vòng 2**
    - **O6 Design System** — `extract-design-tokens.py --crawl --emit-root` → gate V-DS (tuỳ chọn, chạy khi B2 = có hoặc Lượt 4 có Figma input)
    - **O7 Bug list** — `build-bug-list.py` → gate V8 (**chỉ chạy khi P9 = có; hỏi trước lần nữa nếu lúc preflight user chọn pending**)

    FAIL=0 cho mọi gate mới được sang bước 12. Cập nhật O2 / O3 nếu reconcile đổi dữ liệu (CONFLICT).
12. **O4 Figma view** (sequential, SAU khi 3 output trên xong vì cần O5/O2/O3) — chọn vẽ (Lượt 4 câu 3 = [A]) → đọc Design System vừa sinh ở O6 → **[PRE-DRAW — BẮT BUỘC, KHÔNG SKIP]**: (1) Read skill `ba-flow-journey` · (2) Read skill `ba-figma-output §1–§5` · (3) Read `examples/final_output_1.png` + `final_output_2.png` · (4) Read `sys-agent/figma/output-1-flow.md` + `output-2-screen-flow.md` · (5) in **NODE PLAN** — phải có: ELLIPSE (Start) · rect Screen · LINE/CONNECTOR · rect Decision · rect dashed NG · rect Terminal ⛔ KHÔNG dùng text frame thuần ⛔ Output 2 ≠ Sitemap (Sitemap = Phần C của Output 1; Output 2 = Screen Flow Merged Branch với Groups + Start/Decision/NG/Terminal + 4 bảng bên phải) → vẽ Output 1 (FF frame Phần A+B+C + BF frame cạnh nhau) + Output 2 qua `use_figma` → readback → gate V-O4 (Tiêu chí 7/9/10/11/12) → ◇ sub-agent **`o4-figma-reviewer` vòng 1** (13 check; FIX → parent sửa use_figma → vòng 2; vòng 2 vẫn FIX → `manual-review-needed` trong run-log, không loop vòng 3).
13. Render lại **O1** (số liệu mới) → self-test · `detect-pii.js --scan` · `build-version-index.py` (bỏ `--skip` O4 / O6 / O7) · run-log → báo cáo cuối **"Giai đoạn 2 đã chạy xong"** + bảng output + phần đã đổi so với G1.
