# PM AI Kit

Bộ công cụ AI hỗ trợ Project Manager — tự động hóa báo cáo hiệu suất thành viên từ Backlog.

## Tính năng

### 1. Performance Report
Tự động tổng hợp dữ liệu từ Backlog API → xuất Excel với 5 sheets:
- **Dashboard** — bảng tuần: Total/Done/Remain Task, Total/Done/Remain Bug, Estimate/Actual, Productivity, Effort Load
- **Monthly_Stats** — bảng tháng: cùng cột như Dashboard + Bug_Rate (%)
- **Member_Availability** — số giờ tải/ngày (Mon–Fri) từng member
- **Action_Required** — backlog cần PM sửa (thiếu Estimate / Start / Due)
- **Raw_Data** — toàn bộ dữ liệu thô để verify

Mỗi sheet có bảng **Chú thích** đi kèm giải thích ngưỡng màu.

---

## Tiêu chí đánh giá hiệu suất

### Productivity (%)
```
Productivity = Total Estimate Hours / Total Actual Hours × 100
```

| Productivity | Ý nghĩa |
|---|---|
| **> 100%** | 🟢 Hoàn thành nhanh hơn estimate |
| **80% – 100%** | 🟡 Làm đúng effort dự kiến |
| **< 80%** | 🔴 Tốn nhiều effort hơn estimate — cần review |

### Effort Load (Dashboard — theo tuần)
So sánh **tổng Estimate Hours** vs **Allocation Hours** (chuẩn 100% allocation = **40h/tuần**).

| Ratio (Estimate ÷ Alloc-hours) | Nhãn |
|---|---|
| **< 87.5%** (< 35h với 100% alloc) | 🟡 Còn dư — có thể assign thêm |
| **87.5% – 100%** (35–40h) | 🟢 Đủ |
| **> 100%** (> 40h) | 🔴 Quá tải — cần chia bớt |

### Bug_Rate (Monthly_Stats)
```
Bug_Rate (%) = Total Bug / Total Estimate Hours × 100
```

| Bug_Rate | Ý nghĩa |
|---|---|
| **< 10%** | 🟢 Chất lượng tốt |
| **≥ 10%** | 🔴 Nhiều bug so với effort — cần review chất lượng |

### Task / Bug (theo tuần & tháng)
| Cột | Nguồn |
|---|---|
| Total Task | Σ issues có dueDate trong kỳ (bao gồm bug) |
| Task Done | Task có status ∈ {Resolved, Closed, Done, 完了, 解決済み, 処理済み} |
| Task Remain | Total − Done |
| Total Bug | Subset của Task, `issueType == "Bug"` |
| Bug Done / Remain | Tương tự Task |

---

## Cách dùng

> **Quan trọng:** `pm-ai-kit` phải được mở như một project độc lập trong Claude Code — không mở từ thư mục cha. Slash commands chỉ hoạt động khi Claude Code được khởi động đúng thư mục gốc của kit.

### Bước 1 — Mở Claude Code trong thư mục kit

**CLI:**
```bash
cd pm-ai-kit
claude
```

**IDE (VS Code / JetBrains):** Mở thư mục `pm-ai-kit/` làm workspace.

### Bước 2 — Setup config

Copy template và điền giá trị thật (backlog space, API key, project ID):
```bash
cp performance-report/local.json.example performance-report/local.json
```
File `local.json` đã được `.gitignore` — không commit.

### Bước 3 — Chạy wizard

```
/performance-report
```

Wizard hướng dẫn nhập API key, allocation, thời gian báo cáo → tự chạy script → xuất file `{projectKey}_{YYYYMMDD}_{YYYYMMDD}.xlsx`.

> **Lưu ý:** Thư mục `performance-report/data/` được tạo tự động khi chạy `/performance-report` lần đầu — không cần tạo tay.
