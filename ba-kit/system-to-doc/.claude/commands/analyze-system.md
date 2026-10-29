---
description: Luồng 1 — khảo sát hệ thống có sẵn (website / source / DB / Figma) và dựng bộ tài liệu baseline có version
model: opus
---

Hãy là **System Analyst**. Đọc `.claude/agents/system-analyst.md` và chạy **Luồng 1 — Baseline** đúng 9 bước.

Đối tượng / gợi ý ban đầu của user: $ARGUMENTS

Bắt buộc, không rút gọn:
0. `ensure-env.py --flow 1` — **tự cài** thư viện còn thiếu; user không phải cài gì. Sau Discovery Brief chạy lại với `--browser` (có website) / `--figma` (vẽ O5) — xem §4 *Môi trường* của agent
1. `version-tool.py context --outputs outputs --flow 1` — **agent tự đọc version mới nhất** (baseline mới nhất · CR mở sau baseline · feedback chưa xử lý) và Read các file trong `read`; user **không** phải chỉ version, không phải mở `run-log.md`. Có baseline → hỏi **G-R** với mode đề xuất `suggest.flow1_mode` (Delta / Toàn bộ / Chỉ đọc / Đây là CR → Luồng 2) — xem `sys-agent/versioning.md` §6–7
2. `preflight-memory.py missing --outputs outputs` → câu đã có: 1 bảng "Tôi đang dùng các thông tin sau — có gì đổi không?" · 4 câu an toàn luôn hỏi lại gọn · chỉ hỏi câu còn thiếu bằng `AskUserQuestion`, gom theo chủ đề ≤ 4 câu / lượt (quy tắc duy nhất: `.claude/sys-agent/preflight-questions.md` §0) — **không đoán** URL, tài khoản, quyền, đường dẫn repo. Câu không an toàn được chọn "Chưa có — chạy v1 trước, bổ sung sau". Mỗi câu trả lời → `preflight-memory.py set`
2b. Quét nhạy cảm repo → Pha A đọc code → `extract-design-tokens.py --code-only` → đề xuất **Quyết định lớn** (số Design System · output nào làm · repo legacy · phạm vi · đưa sơ đồ DB lên Figma)
3. In **Discovery Brief** (kèm Quyết định lớn), DỪNG chờ confirm → `version-tool.py next --outputs outputs --slug <slug> --create` — chưa có baseline → tạo ver1; baseline chưa khoá → trả về **chính ver đó** (`reuse:true`): ghi vào đó, **`version-tool.py snapshot --ver <ver> [--files …]` trước mỗi lần ghi đè**; exit 3 `locked` → báo user "ver<N> đã khoá vì đã có CR", CR nào đã duyệt + code xong (hỏi `AskUserQuestion`) → `version-tool.py promote --outputs outputs --cr CR-<id> --approved --coded --create` rồi ghi vào ver<N+1>; chưa có → chỉ đọc lại
4. `scan-sensitive.py --path … --out <ver>/_internal/gates/sensitive.md` trên mọi repo / dump / file input — exit 3 → **cảnh báo + DỪNG**, hỏi cách khắc phục
5. Recon **read-only** (trừ khi P3 cho phép khác) → inventory → gate V1 · V2
6. Sinh O3 → O4 → O2 → O6 (tuỳ chọn, không chạy thì bỏ qua) → O7 → O5 → O8 (mỗi output qua gate của nó, `FAIL = 0`)
7. Viết `business.json` → sinh O1 docx tổng hợp (nghiệp vụ chính + bảng tổng; link Figma ERD) → gate V3
8. Self-test · `detect-pii.js --scan` · `build-version-index.py` · run-log (ghi **Feedback đã xử lý** = các version trong `pending_feedback` đã làm theo)
9. Báo cáo cuối theo §8 của agent: **đường dẫn folder version + bảng từng output (file · số lượng · gate) + output không chạy và lý do**
