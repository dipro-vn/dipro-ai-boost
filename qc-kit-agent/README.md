# QC Kit Agent

Bộ commands & skills hỗ trợ QC sinh manual test cases theo quy trình Risk-Based Testing (RBT) và sinh automation script Playwright từ test cases đã có.

---

## Pipeline sinh Test Cases

```
/analyze-req → /plan-tcs → /gen-tcs → /review-tcs → /export-xlsx
```

| Command | Input | Khi nào dùng | Output |
|---------|-------|-------------|--------|
| `/analyze-req` | Requirements doc (spec/Google Drive/Docs/Figma) | Có spec mới — phân tích điểm mờ (Q&A) và mapping REQ→AC | `testing/[module]/analysis.md` gồm list Q&A kèm Summary về module |
| `/plan-tcs` | `analysis.md` | Bắt buộc trước `/gen-tcs` — xác định chiến lược theo Screen archetype, phân rã Screen/Component, gắn Component Type/Risk Level, Permission Matrix, Luồng E2E chính. Là bước tiền xử lý của `/gen-tcs`, chạy riêng khi muốn duyệt cấu trúc | `testing/[module]/plan-tcs.md` |
| `/gen-tcs` | `plan-tcs.md` + `analysis.md` | Sinh Test Case chi tiết (có self-check). Thiếu cả `analysis.md` và `plan-tcs.md` → hỏi chọn **Full** (chain `/analyze-req` → `/plan-tcs` → sinh TC) hoặc **Quick** (sinh nhanh trực tiếp từ spec, không có Q&A, Expected suy luận tag `[ASSUMED]`, cả module 1 sheet TC). Thiếu 1 trong 2 → tự chạy bước còn thiếu (chỉ dừng ở checkpoint của `/analyze-req`; `/plan-tcs` chạy không dừng, `/gen-tcs` in tóm tắt plan ở đầu output). Bảng TC không có cột Risk Level/Priority; cuối file có mục `## High Risk & E2E` (Bảng 1 nhóm TC high risk, Bảng 2 test E2E), export thành 1 sheet cuối workbook. | `testing/[module]/test-cases.md` |
| `/review-tcs` | `test-cases.md` | Muốn review chéo bộ TC (với DA có >= 2 QC) | `testing/[module]/review_report.md` |
| `/export-xlsx` | file `.md` (thường là `test-cases.md`) | Xuất `test-cases.md` ra `.xlsx` theo template Web/App của công ty (vẫn giữ nguyên công thức) | `testing/[module]/test-cases.xlsx` |

> **Lưu ý:** Figma MCP phải được cài global và reachable trước khi chạy lần đầu. Có một số cách kết nối với Figma, xem hướng dẫn bên dưới:

> 1. **figma mcp (official của Figma)**: https://docs.google.com/document/d/1GD_92bQ_xSd9sHDYXUaPLSskrSEAFcH1k_5GdvevqZA/edit?tab=t.0
→ cách này có thể phát sinh tình huống `rate limit` làm AI không thể đọc tiếp figma, khi đó tham khảo cách 2

> 2. **figma-mcp-console (by AnNTH_Dev)**: https://docs.google.com/document/d/1FPcs9NQxqdfylFR-kHUukXyErDv_pKKYeQC66GSWOaQ/edit?tab=t.0#heading=h.iqfvo6v5ltbf

---

## Automation

`/gen-automation` — Sinh & chạy Playwright automation script thật từ `test-cases.md` (dùng Playwright MCP để recon DOM thật), chạy test, tự sửa lỗi phía script (auto-heal tối đa 2 vòng, chỉ chạy lại TC fail); assertion fail được báo là nghi bug, không sửa. Bắt buộc phải có `test-cases.md` trước khi chạy.

| Command | Input | Khi nào dùng | Output |
|---------|-------|-------------|--------|
| `/gen-automation` | `test-cases.md` | Đã có `test-cases.md`, muốn sinh automation script chạy thật | `automation/` (pages/tests/utils) + `testing/[module]/automation-report.md` (PASS / Nghi bug / Không chạy được) |

> **Lưu ý:** Playwright MCP server (`@playwright/mcp`) phải được cài global và reachable trước khi chạy lần đầu.
> Xem hướng dẫn cài đặt `playwright mcp` tại đây: https://docs.google.com/document/d/11qEffhyYP7zXdnWDAwqLTGgewIwZbxAfCwu6bFTxWPA/edit?tab=t.0

---

## Bug Report

`/gen-bug-report` — Độc lập, không nằm trong pipeline TC.

Dùng khi QC tìm được bug và muốn chuẩn hóa report trước khi submit lên Backlog. Input là mô tả lỗi tự nhiên, output là bug report đầy đủ fields (Bug Type, Severity, Priority, Steps to Reproduce).

---

## Skills đi kèm

| Skill | Dùng bởi |
|-------|---------|
| `rbt_manual_testing` | `/analyze-req`, `/plan-tcs`, `/gen-tcs`, `/review-tcs` |
| `requirements_analyzer` | `/analyze-req` |
| `screen_strategy` | `/plan-tcs` (không dùng độc lập) |
| `testing_dimensions` | `/gen-tcs` |
| `component_checklist` | `/gen-tcs` |
| `jp_validation` | `/gen-tcs` (khi `Locale: JP`) — bộ validate chuẩn Nhật: lớp ký tự 全角/半角, kana, kanji, độ dài đa byte |
| `automation_engineer` | `/gen-automation` |
| `bug_reporter` | `/gen-bug-report` |

---

## Cấu trúc kit

```
qc-kit-agent/
├── .claude/
│   ├── commands/
│   │   ├── analyze-req.md
│   │   ├── plan-tcs.md
│   │   ├── gen-tcs.md
│   │   ├── review-tcs.md
│   │   ├── gen-automation.md
│   │   ├── export-xlsx.md
│   │   └── gen-bug-report.md
│   ├── scripts/
│   │   └── md_to_xlsx.py
│   └── skills/
│       ├── rbt_manual_testing/SKILL.md
│       ├── requirements_analyzer/SKILL.md
│       ├── screen_strategy/SKILL.md
│       ├── testing_dimensions/SKILL.md
│       ├── component_checklist/SKILL.md
│       ├── jp_validation/SKILL.md
│       ├── automation_engineer/SKILL.md
│       └── bug_reporter/SKILL.md
├── template/
│   ├── [Tên dự án]_[Tên module]_Testcase_ForWeb_V3.0.xlsx
│   └── [Tên dự án]_[Tên module]_Testcase_ForApp_V3.0.xlsx
└── CLAUDE.md                # skeleton project context — điền 1 lần
```

---

## Cài đặt vào project

Copy 3 thứ từ kit ra **root project**: `.claude`, `template`, `CLAUDE.md`.

- Giữ `CLAUDE.md` dưới 20 dòng; chỉ ghi thông tin áp dụng cho cả project.
- Trong **root project** tạo thêm folder `testing`
- Tiếp tục tạo folder con `module` trong `testing`
  → xem cấu trúc folder dự án mẫu như dưới

---

## Cấu trúc folder dự án

```
project-example/
├── .claude/                 # commands, scripts, skills copy từ kit
│   ├── commands/
│   ├── scripts/
│   └── skills/
├── template/                # template xlsx Web/App
│   ├── [Tên dự án]_[Tên module]_Testcase_ForWeb_V3.0.xlsx
│   └── [Tên dự án]_[Tên module]_Testcase_ForApp_V3.0.xlsx
├── testing/                 # member tự tạo
│   ├── [module-example]/
│   │   ├── spec.md          # member tự thêm: spec của module
│   │   ├── [...]            # member tự thêm: các documents khác của module
│   │   ├── analysis.md      # output của /analyze-req
│   │   ├── plan-tcs.md      # output của /plan-tcs
│   │   └── test-cases.md    # output của /gen-tcs
│   ├── [module-A]/
│   └── [module-B]/
└── CLAUDE.md                # thông tin chung của project — điền 1 lần
```
