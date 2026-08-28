---
description: Sinh checklist thực thi test có ưu tiên trước release — nhóm TC theo risk, ước lượng thời gian, đánh dấu regression candidates.
skills:
  - rbt_manual_testing
---

> **Canonical workflow:** `.claude/agents/qc-agent.md`.
> **BẮT BUỘC:** Nạp skill `rbt_manual_testing`.

# /test/generate_test_execution_checklist

## Khi nào dùng

- Chuẩn bị sprint release / hotfix / UAT
- Cần phân bổ thời gian test hợp lý trong deadline ngắn
- Xác định TC bắt buộc PASS trước khi ship
- **Không dùng** khi chưa có bộ TC → `/test/generate_manual_testcases_rbt`

## Input

| Input | Bắt buộc | Mô tả |
|---|---|---|
| Bộ TC | ✅ | Path `tc_*.md` |
| Loại release | ✅ | Hotfix / Sprint Release / Major Release / UAT |
| Thời gian có sẵn | ⚠️ Nên có | VD: "2 ngày", "4 tiếng" |
| Tính năng thay đổi | ⚠️ Nên có | Để ưu tiên đúng vùng impact |
| Số QC | ❌ | Để phân chia |

## Output path

`docs/features/<feature>/test-cases/checklist_<release>.md`

## Các bước

### Bước 1 — Phân tích TC + ngữ cảnh

| Loại release | Chiến lược |
|---|---|
| Hotfix | TC trực tiếp liên quan fix + smoke core flows |
| Sprint Release | Full TC tính năng mới + regression module phụ thuộc |
| Major Release | Full regression toàn bộ TC |
| UAT | Happy Path + business-critical scenarios |

Xác nhận context với user → Bước 2.

### Bước 2 — Phân loại 3 nhóm

| Nhóm | Ký hiệu | Tiêu chí |
|---|---|---|
| Must-run | 🔴 | Critical/High, core flows, vùng thay đổi |
| Should-run | 🟡 | Medium, regression module liên quan |
| Nice-to-run | 🟢 | Low, edge case ít gặp, UI cosmetic |

### Bước 3 — Ước lượng thời gian

| Độ phức tạp TC | Time |
|---|---|
| ≤3 steps | 2-3 phút |
| 4-7 steps | 5-10 phút |
| >7 steps, nhiều data | 10-20 phút |

So sánh tổng với thời gian có sẵn.

### Bước 4 — Output

```markdown
## Test Execution Checklist — <Release> — <Ngày>

### Tổng quan
- Tổng TC: N | 🔴 X | 🟡 Y | 🟢 Z
- Time estimate: Must-run Xh | Full Yh
- Time có sẵn: Z giờ

### 🔴 Must-Run (không được bỏ qua)
| STT | TC ID | Module | Title | Priority | Time | Kết quả |

### 🟡 Should-Run
| STT | TC ID | Module | Title | Priority | Time | Kết quả |

### 🟢 Nice-to-Run
| STT | TC ID | Module | Title | Priority | Time | Kết quả |

### Ghi chú
- Thiếu time: bỏ 🟢, cắt 🟡
- Release blocker: tất cả 🔴 phải PASS
```

## Quy tắc

- ❌ KHÔNG bỏ 🔴 dù thiếu time — release blocker
- ✅ Nếu Must-run estimate > time có sẵn → cảnh báo ngay
- ✅ TC cần setup phức tạp → note để QC chuẩn bị trước
