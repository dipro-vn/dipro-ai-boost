---
name: system-analyst
description: Phân tích ngược hệ thống đã có sẵn (website đang chạy, source code, database, tài liệu khách hàng) thành tài liệu AS-IS có bằng chứng truy vết. Dùng khi nhận dự án LABO/Maintain, cần dựng tài liệu phiên bản đầu tiên, cần baseline để impact-analysis, hoặc cần liệt kê lỗi đang tồn tại trước khi bàn giao.
---

# System Analyst — reverse engineering ra tài liệu

Workflow canonical nằm ở `.claude/agents/system-analyst.md`. Skill này là chỉ mục script.

## Nguyên tắc một dòng

> Mọi câu khẳng định trong tài liệu phải trỏ về một hiện vật chụp được. Không có bằng chứng → `UNKNOWN`, không phải câu văn nghe hợp lý.

## Script

| Script | Việc | Chạy ở bước |
|---|---|---|
| `crawl-site.js` | Crawl website read-only, chụp screenshot, bắt console/network error | 3 |
| `scan-repo.py` | Trích route / job / integration / stack từ source code | 3 |
| `read-schema.py` | Đọc schema từ SQL dump hoặc SQLite + sinh SQL kiểm toàn vẹn | 3 |
| `build-inventory.py` | Sinh inventory workbook rỗng đúng schema (`--bug-list` cho Output 2B) | 4 |
| `inv_schema.py` | Hợp đồng schema dùng chung — sửa cột thì sửa ở đây | — |
| `render-flow.py` | `flow.json` → PNG chèn vào chương 4 | 6 |
| `render-highlevel-docx.py` | inventory + narrative + PNG → docx | 7 |
| `verify-evidence.py` | **Gate V1** — Evidence Ledger | 4 |
| `verify-inventory.py` | **Gate V2** — coverage + truy vết | 5 |
| `verify-high-level.py` | **Gate V3/V4/V6** — tài liệu docx | 7 |
| `verify-flow-png.py` | **Gate V5** — so đồ flow | 6 |
| `verify-basic-design.py` | **Gate V7** — master Excel (`--asis` bật check 16) | 9 |
| `verify-bug-list.py` | **Gate V8** — Bug List | 9 |
| `selftest-gates.py` | **Gate V9** — tiêm lỗi, chứng minh gate không rỗng | 9 |
| `selftest-basic-design.py` | Self-test riêng cho gate Basic Design | 9 |
| `gate_report.py` · `docx_read.py` · `bd_styles.py` | Thư viện dùng chung | — |

## Dependency

```bash
pip install openpyxl python-docx matplotlib
npm i -D playwright && npx playwright install chromium
```

Thiếu dependency → script exit code `2`. Khi đó output tương ứng = `❌ Blocked`, **không** được tự chấm PASS bằng mắt.
