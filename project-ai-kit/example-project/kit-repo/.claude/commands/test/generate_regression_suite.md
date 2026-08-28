---
description: Xác định bộ TC cần chạy lại khi có code change — map thay đổi vào modules bị ảnh hưởng, phân loại direct/indirect impact, output regression suite có ưu tiên.
skills:
  - rbt_manual_testing
---

> **Canonical workflow:** `.claude/agents/qc-agent.md`.
> **BẮT BUỘC:** Nạp skill `rbt_manual_testing` để hiểu cách đánh giá risk.

# /test/generate_regression_suite

## Khi nào dùng

- Sau mỗi sprint có code change → xác định scope regression
- Hotfix cần verify không break tính năng khác
- Refactor → chọn safety net TCs
- **Không dùng** khi cần full regression → `/test/generate_test_execution_checklist`

## Input

| Input | Bắt buộc | Mô tả |
|---|---|---|
| Bộ TC hiện tại | ✅ | Path `tc_*.md` của feature |
| Danh sách thay đổi | ✅ | Từ PR description, task file Non-Regression table, hoặc commit log |
| Module map | ⚠️ Nên có | Dependencies giữa modules |

## Output path

`docs/features/<feature>/test-cases/regression_<release>.md`

## Các bước

### Bước 1 — Phân tích scope thay đổi

| Loại | Ví dụ | Mức ảnh hưởng |
|---|---|---|
| New feature | Thêm export PDF Order | Direct + module dùng chung Order data |
| Bug fix | Fix validation email | Direct module đó |
| Refactor | Tách OrderService → OrderQueryService + OrderCommandService | Tất cả module gọi OrderService |
| Config change | Tăng timeout API gọi payment gateway | Tất cả flow payment |
| DB migration | Thêm cột `delivery_window` vào `orders` | Tất cả TC liên quan Order |

### Bước 2 — Map thay đổi → Modules

- **Direct impact:** module được sửa trực tiếp
- **Indirect impact:** module phụ thuộc (shared component, API, data, Redis cache)

```markdown
| Thay đổi | Direct | Indirect |
|---|---|---|
| Fix login validation | Auth | Dashboard, Profile |
| Thêm field "Delivery Window" vào Order | Order Create/Edit | Order Report, Driver app screen Order Detail |
```

### Bước 3 — Chọn TC

| Ưu tiên | Loại TC |
|---|---|
| 1 — Bắt buộc | TC liên quan **trực tiếp** thay đổi |
| 2 — Bắt buộc | Happy Path của module Direct |
| 3 — Nên có | Smoke test của module Indirect |
| 4 — Optional | Edge cases của module Direct |

### Bước 4 — Output

```markdown
## Regression Suite — <Release name>

### Scope thay đổi
[2-3 dòng tóm tắt]

### Modules bị ảnh hưởng
- 🔴 Direct: <Module A, B>
- 🟡 Indirect: <Module C, D>

### Regression TCs (<N> TCs — est. <X>h)
| STT | TC ID | Module | Title | Impact | Priority | Kết quả |
|---|---|---|---|---|---|---|
| 1 | TC_001 | Login | Đăng nhập thành công | Direct | Critical | ⬜ |

### TC không cần chạy lại
- <Module X> — isolated, không dùng shared component
```

## Quy tắc

- ❌ KHÔNG bỏ qua Indirect — bug regression thường ở đây
- ❌ KHÔNG chọn TC theo tên module — verify dependency thực tế (qua `tilth_deps` nếu cần)
- ✅ Regression nên chiếm 20-40% bộ TC. >60% → dùng full regression
