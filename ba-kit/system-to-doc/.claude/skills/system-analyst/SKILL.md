---
name: system-analyst
description: Phân tích ngược hệ thống đã có sẵn (website đang chạy, source code, database, Figma) thành bộ tài liệu baseline có version — danh sách màn hình, API doc, DB doc, design system, Figma flow, docx tổng hợp, bug list — và phân tích ảnh hưởng của Change Request trên baseline đó. Dùng khi nhận dự án LABO/Maintain.
---

# System Analyst — chỉ mục script

Workflow canonical: `.claude/agents/system-analyst.md`. Skill này chỉ liệt kê script.

> Mọi câu khẳng định trong tài liệu phải trỏ về một hiện vật chụp được. Không có bằng chứng → `UNKNOWN`, không phải câu văn nghe hợp lý.

## Recon (chỉ đọc)

| Script | Việc |
|---|---|
| `scan-sensitive.py` | **S1** — quét secret / dữ liệu thật trong repo, dump, file input **trước khi đọc**. Exit 3 = DỪNG |
| `login-site.js` | Tạo phiên đăng nhập `.auth/<WEB>.json` (user tự gõ `--manual`, hoặc env var `--form`). Không lưu mật khẩu |
| `crawl-site.js` | Crawl 1 website read-only (chặn ghi ở tầng network, không theo link logout/xoá): screenshot, item, style, lỗi UI |
| `scan-repo.py` | 1 repo: API, batch, route FE, lời gọi API từ FE, bảng DB được dùng, integration, evidence code-ref, `api-seed.csv` |
| `read-schema.py` | Dump schema-only / SQLite metadata → bảng, cột, max length, format, constraint. Dump có dữ liệu → exit 3 |
| `extract-design-tokens.py` | Tổng hợp màu / font / spacing / component quan sát được (website + CSS) → `tokens-draft.json`; `--emit-tokens` sinh `tokens.json` khởi đầu đúng format type Design System |

## Inventory + render

| Script | Việc |
|---|---|
| `inv_schema.py` | Hợp đồng schema dùng chung (inventory 12 sheet, bug list, CR impact) — đổi cột chỉ sửa ở đây |
| `build-inventory.py` | Workbook rỗng đúng schema: inventory · `--bug-list` · `--cr` |
| `version-tool.py` | `next` (tên folder version) · `latest-baseline` · `list` (CR đang mở) |
| `build-api-doc.py` | O2 — API Documentation xlsx |
| `render-codemap.py` | O2 — sơ đồ map code FE → API → BE → DB (png + md) |
| `build-db-doc.py` | O3 — Database Documentation xlsx + ERD png |
| `render-flow.py` | Flow tổng quan png (chương 7 của O6) |
| `render-overview-docx.py` | O6 — docx tổng hợp |
| `build-version-index.py` | `README.md` + `index.json` của folder version |
| `build-guide-docx.py` | Sinh lại `docs/Hướng dẫn sử dụng System to Doc.docx` |

## Gate (máy chấm — cấm chấm bằng mắt)

| Gate | Script | Output |
|---|---|---|
| V1 | `verify-evidence.py` | Evidence Ledger |
| V2 | `verify-inventory.py` | inventory |
| V-BD | `verify-basic-design.py --asis` | O1 |
| V-API | `verify-api-doc.py` | O2 |
| V-DB | `verify-db-doc.py` | O3 |
| V-DS | `verify-design-system.py` | O4 (format Artifact type Design System) |
| V3 | `verify-overview.py` | O6 |
| V5 | `verify-flow-png.py` | flow O6 |
| V8 | `verify-bug-list.py` | O7 |
| V-CR | `verify-cr-impact.py` | Luồng 2 |
| V9 | `selftest-gates.py` · `selftest-docs.py` · `selftest-basic-design.py` · `selftest-cr-impact.py` · `selftest-design-system.py` | gate không rỗng |

Tên file báo cáo gate quyết định nó được tính cho output nào trong README version: `_internal/gates/v1.md` `v2.md` `v-bd-<WEB>.md` `v-api.md` `v-db.md` `v-ds.md` `v3.md` `v5.md` `v8.md` `v-cr.md`.

Thư viện dùng chung: `gate_report.py` · `docx_read.py` · `bd_styles.py`.

## Dependency

```bash
pip install openpyxl python-docx matplotlib
npm i -D playwright && npx playwright install chromium
```

Thiếu dependency → script exit `2` → output tương ứng `❌ Blocked`, **không** tự chấm PASS.
