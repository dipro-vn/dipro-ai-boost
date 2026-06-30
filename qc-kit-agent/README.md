# QC Kit — Integrate v2

Bộ commands & skills hỗ trợ QC sinh manual test cases chất lượng cao theo quy trình Risk-Based Testing (RBT).

---

## Pipeline sinh Test Cases

```
/analyze-req → [/decompose-modules] → /gen-tcs → /review-tcs
                    (optional)
```

| Command | Khi nào dùng | Output |
|---------|-------------|--------|
| `/analyze-req` | Có spec mới — phân tích điểm mờ (Q&A) và mapping REQ→AC | `testing/[module]/analysis.md` |
| `/decompose-modules` | Module phức tạp — cần phân rã và đánh giá risk level | `testing/[module]/modules.md` |
| `/gen-tcs` | Đã có AC — sinh Test Scenarios và Test Cases | `testing/[module]/test-scenarios.md` + `test-cases.md` |
| `/review-tcs` | Muốn review chéo bộ TC trước khi handoff | `testing/[module]/review_report.md` |

---

## Bug Report

`/gen-bug-report` — Độc lập, không nằm trong pipeline TC.

Dùng khi QC tìm được bug và muốn chuẩn hóa report trước khi submit lên Backlog. Input là mô tả lỗi tự nhiên, output là bug report đầy đủ fields (Bug Type, Severity, Priority, Steps to Reproduce).

---

## Skills đi kèm

| Skill | Dùng bởi |
|-------|---------|
| `rbt_manual_testing` | `/analyze-req`, `/decompose-modules`, `/gen-tcs`, `/review-tcs` |
| `requirements_analyzer` | `/analyze-req` |
| `testing_dimensions` | `/gen-tcs` |
| `component_checklist` | `/gen-tcs` |
| `bug_reporter` | `/gen-bug-report` |

---

## Cấu trúc folder

```
qc-kit-integrate-v2/
└── .claude/
    ├── commands/
    │   ├── analyze-req.md
    │   ├── decompose-modules.md
    │   ├── gen-tcs.md
    │   ├── review-tcs.md
    │   └── gen-bug-report.md
    └── skills/
        ├── rbt_manual_testing/SKILL.md
        ├── requirements_analyzer/SKILL.md
        ├── testing_dimensions/SKILL.md
        ├── component_checklist/SKILL.md
        └── bug_reporter/SKILL.md
```
