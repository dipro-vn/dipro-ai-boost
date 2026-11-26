---
description: Chỉ chạy O5 Basic Design cho 1 site hoặc danh sách màn cụ thể — nhanh, ít token, không phải chạy cả /analyze-system 2 giai đoạn. Dùng khi đã có inventory/baseline + chỉ cần sửa O5. Feedback 22/11/2026 P1-6.
model: opus
---

Hãy là **System Analyst** (agent `basic-design`, nhỏ hơn `system-analyst`). Đọc `.claude/agents/basic-design.md` rồi chạy luồng ngắn này.

Đối tượng: `$ARGUMENTS` (dự kiến `<URL hoặc repo> <danh sách màn>` hoặc rỗng — hỏi lại).

**KHÔNG nạp:** skill `ba-figma-output` (55KB) · `ba-flow-journey` (16KB) · `flow-2-change-request.md` · figma MCP. Chỉ nạp: `sys-agent/outputs/o5-basic-design.md` + `sys-agent/basic-design/workbook-structure.md` + `sys-agent/preflight-questions.md`.

---

**Luồng ngắn — 1 lệnh, không có 2 giai đoạn:**

0. `ensure-env.py --flow 1` (không `--figma`, không `--browser` nếu input là repo code). → `version-tool.py context --outputs outputs`. Chưa có baseline → DỪNG, đề nghị `/analyze-system` trước.

1. **Preflight ngắn** — hỏi đúng 2-3 câu bằng `AskUserQuestion`:
   - Site (URL hoặc đường dẫn repo FE)
   - Danh sách màn (Screen ID hoặc URL) — rỗng = tất cả màn của site
   - **4 câu an toàn** (P1-env · P2b · P3 · P11) luôn hỏi lại nếu input là URL website

2. `scan-sensitive.py` (exit 3 → DỪNG).

3. **Nạp inventory baseline** mới nhất của site này (`_internal/inventory.xlsx` từ `outputs/<baseline>/`). Thiếu → DỪNG.

4. **Sinh skeleton** (feedback 22/11/2026 P1-4):
   ```
   build-bd-skeleton.py --ast-spec … --crawl recon/crawl/<WEB-xx>/ \
                        --fe-api-calls … --inventory … \
                        --site <WEB-xx> --out _internal/bd/skeleton-<WEB-xx>.json
   ```

5. **LLM điền spec ngắn** — chỉ diffs (purpose / access / p / q / group / common_step1 6 dòng / errors). **KHÔNG viết lại toàn bộ item** (đã có trong skeleton). Lưu → `_internal/bd/spec-<WEB-xx>.json`.

6. **Build workbook** — `build-basic-design.py --skeleton … --spec … --phase 2` (nếu có crawl) hoặc `--phase 1` (code-only).

7. **Gate V-BD** — 24 check cũ + 7 check mới P2 chất lượng (feedback 22/11/2026 lỗi #1-#9). FAIL → fix spec hoặc skeleton → rerun bước 6.

8. **Sub-agent `basic-design-reviewer`** chạy 1 vòng (hoặc 2 nếu vòng 1 FIX).

9. **Bỏ (vì scope nhỏ):** inventory đầy đủ · self-test · snapshot history · build README · chạy O1 Overview · gate V9. Chỉ chạy `detect-pii.js --scan` cho workbook mới + append run-log 1 dòng.

**Flag `--light` cho `/analyze-system`:**

User gọi `/analyze-system --light` với scope ≤5 màn → `analyze-system.md` bỏ các bước thủ tục như `/basic-design`: không inventory đầy đủ, không snapshot history, không build README. Giống `/basic-design` nhưng vẫn chạy toàn bộ O1-O8 (chỉ bỏ thủ tục phụ).

---

**Báo cáo cuối:**
- Workbook đã sinh: `outputs/<baseline>/05_Basic_Design/BasicDesign_<WEB-xx>_ver<N>.xlsx`
- Số màn làm · số item · ô 要確認 · số Q · số lỗi gate P2 (nếu có)
- Reviewer verdict + feedback cụ thể
