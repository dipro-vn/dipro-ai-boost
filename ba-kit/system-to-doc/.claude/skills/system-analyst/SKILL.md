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
| `ensure-env.py` | **Tự chuẩn bị môi trường** — thư viện Python · `--browser` Playwright + Chromium · `--figma` Figma MCP. Thiếu → tự cài. Exit 2 = BLOCKED |
| `scan-sensitive.py` | **S1** — quét secret / dữ liệu thật trong repo, dump, file input **trước khi đọc**. Exit 3 = DỪNG |
| `login-site.js` | Tạo phiên đăng nhập `.auth/<WEB>.json` (user tự gõ `--manual`, hoặc env var `--form`). Không lưu mật khẩu |
| `crawl-site.js` | Crawl 1 website read-only (chặn ghi ở tầng network, không theo link logout/xoá): screenshot, item, style, lỗi UI |
| `scan-repo.py` | 1 repo: API, batch, route FE, lời gọi API từ FE, bảng DB được dùng, integration, evidence code-ref, `api-seed.csv` |
| `read-schema.py` | Dump schema-only / SQLite metadata → bảng, cột, max length, format, constraint. Dump có dữ liệu → exit 3 |
| `extract-design-tokens.py` | Tổng hợp màu / font / spacing / component quan sát được (website + CSS) → `tokens-draft.json`; `--emit-root` tự quyết 1 DS nhiều theme hay 1 DS / website và sinh `tokens.json` + `STATUS.md` khởi đầu đúng chuẩn chung |

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
| `build-cr-impact.py` | Luồng 2 — `CR-<id>_Impact.xlsx` 7 sheet (Summary · Estimation · Screen · API · Database · Figma · Q&A) từ `cr.json` |
| `extract-estimation-template.py` | Bóc 見積書 của công ty → `templates/template_estimation.xlsx` (khung + hệ số công đoạn từ công thức) cho sheet Estimation |
| `render-cr-figma.py` | Luồng 2 — sinh JS vẽ view CR (CR-1 Flow = Output 1 · CR-2 Screen Flow = Output 2 · Change Table thống kê · CR-3 màn đề xuất từ token Design System) + JS đọc ngược |
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
| V-CR | `verify-cr-impact.py` | Luồng 2 — xlsx 7 sheet |
| V-CR-FIGMA | `verify-cr-figma.py` | Luồng 2 — view CR (format Output 1/2, thống kê, mũi tên, màn đề xuất bám DS) |
| V9 | `selftest-gates.py` · `selftest-docs.py` · `selftest-basic-design.py` · `selftest-cr-impact.py` · `selftest-design-system.py` | gate không rỗng |

Tên file báo cáo gate quyết định nó được tính cho output nào trong README version: `_internal/gates/v1.md` `v2.md` `v-bd-<WEB>.md` `v-api.md` `v-db.md` `v-ds.md` `v3.md` `v5.md` `v8.md` `v-cr.md` `v-cr-figma.md`.

Thư viện dùng chung: `gate_report.py` · `docx_read.py` · `bd_styles.py` · `ds_roles.py` (token vai trò D1–D7 + component tối thiểu của chuẩn design system chung — sửa cùng `sys-agent/design-system/design-system-format.md`).

## Dependency — kit tự cài, user không cài tay

```bash
python3 $S/ensure-env.py --flow 1 [--browser] [--figma] [--out <ver>/_internal/gates/env.md]   # Luồng 1
python3 $S/ensure-env.py --flow 2 [--figma]                                                     # Luồng 2
```

Cần: Python `openpyxl` `python-docx` `matplotlib` (Luồng 2 chỉ `openpyxl`) · Playwright + Chromium (crawl website) · Figma MCP (vẽ O5 / view CR).
Script báo "Thieu … Chay: pip install …" → chạy `ensure-env.py`, **không** chuyển lời nhắc đó cho user.
`ensure-env.py` exit `2` (BLOCKED) → output tương ứng `❌ Blocked`, **không** tự chấm PASS.
