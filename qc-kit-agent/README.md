# QC Kit Agent

Bộ commands & skills hỗ trợ QC sinh manual test cases theo quy trình Risk-Based Testing (RBT).

---

## Pipeline sinh Test Cases

```
/analyze-req → /plan-tcs → /gen-tcs → /review-tcs → /export-xlsx
```

| Command | Input | Khi nào dùng | Output |
|---------|-------|-------------|--------|
| `/analyze-req` | Requirements doc (spec/Google Drive/Docs/Figma) + design input (optional) | Có spec mới — phân tích điểm mờ (Q&A) và mapping REQ→AC | `testing/[module]/analysis.md` |
| `/plan-tcs` | `analysis.md` | Bắt buộc trước `/gen-tcs` — phân rã Screen/Component, gắn Component Type/Risk Level/Technique Flag | `testing/[module]/plan-tcs.md` |
| `/gen-tcs` | `plan-tcs.md` + `analysis.md` | Đã có `plan-tcs.md` — sinh Test Case chi tiết (có self-check) | `testing/[module]/test-cases.md` |
| `/review-tcs` | `test-cases.md` | Muốn review chéo bộ TC (với DA có >= 2 QC) | `testing/[module]/review_report.md` |
| `/export-xlsx` | file `.md` (thường là `test-cases.md`) | Xuất `test-cases.md` ra `.xlsx` theo template Web/App của công ty (vẫn giữ nguyên công thức) | `testing/[module]/test-cases.xlsx` |

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
| `testing_dimensions` | `/gen-tcs` |
| `component_checklist` | `/gen-tcs` |
| `bug_reporter` | `/gen-bug-report` |

---

## Cấu trúc folder

```
qc-kit-agent/
├── .claude/
│   ├── commands/
│   │   ├── analyze-req.md
│   │   ├── plan-tcs.md
│   │   ├── gen-tcs.md
│   │   ├── review-tcs.md
│   │   ├── export-xlsx.md
│   │   └── gen-bug-report.md
│   ├── scripts/
│   │   └── md_to_xlsx.py
│   └── skills/
│       ├── rbt_manual_testing/SKILL.md
│       ├── requirements_analyzer/SKILL.md
│       ├── testing_dimensions/SKILL.md
│       ├── component_checklist/SKILL.md
│       └── bug_reporter/SKILL.md
└── template/
    ├── [Tên dự án]_[Tên module]_Testcase_ForWeb_V3.0.xlsx
    └── [Tên dự án]_[Tên module]_Testcase_ForApp_V3.0.xlsx
```
