---
description: Luồng 1 — khảo sát hệ thống có sẵn (website / source / DB / Figma) và dựng bộ tài liệu baseline có version
---

Hãy là **System Analyst**. Đọc `.claude/agents/system-analyst.md` và chạy **Luồng 1 — Baseline** đúng 9 bước.

Đối tượng / gợi ý ban đầu của user: $ARGUMENTS

Bắt buộc, không rút gọn:
0. `ensure-env.py --flow 1` — **tự cài** thư viện còn thiếu; user không phải cài gì. Sau Discovery Brief chạy lại với `--browser` (có website) / `--figma` (vẽ O5) — xem §4 *Môi trường* của agent
1. `version-tool.py context --outputs outputs --flow 1` — **agent tự đọc version mới nhất** (baseline mới nhất · CR mở sau baseline · feedback chưa xử lý) và Read các file trong `read`; user **không** phải chỉ version, không phải mở `run-log.md`. Có baseline → hỏi **G-R** với mode đề xuất `suggest.flow1_mode` (Delta / Toàn bộ / Chỉ đọc / Đây là CR → Luồng 2) — xem `sys-agent/versioning.md` §6–7
2. Hỏi đủ **P0 → P11** bằng `AskUserQuestion` theo `.claude/sys-agent/preflight-questions.md` — **không đoán** URL, tài khoản, quyền, đường dẫn repo. Thứ gì user không có → ghi lại, chạy tiếp phần khác
3. In **Discovery Brief**, DỪNG chờ confirm → `version-tool.py next --outputs outputs --slug <slug> --create`
4. `scan-sensitive.py --path … --out <ver>/_internal/gates/sensitive.md` trên mọi repo / dump / file input — exit 3 → **cảnh báo + DỪNG**, hỏi cách khắc phục
5. Recon **read-only** (trừ khi P3 cho phép khác) → inventory → gate V1 · V2
6. Sinh O2 → O3 → O1 → O4 → O7 → O5 (mỗi output qua gate của nó, `FAIL = 0`)
7. Sinh O6 docx tổng hợp → gate V3 · V5
8. Self-test · `detect-pii.js --scan` · `build-version-index.py` · run-log (ghi **Feedback đã xử lý** = các version trong `pending_feedback` đã làm theo)
9. Báo cáo cuối theo §8 của agent: **đường dẫn folder version + bảng từng output (file · số lượng · gate) + output không chạy và lý do**
