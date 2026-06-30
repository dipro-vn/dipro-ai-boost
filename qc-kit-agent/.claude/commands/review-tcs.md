---
description: Deep review test cases — sinh review_report.md với issues phân tier và action đề xuất cụ thể. Không tự sửa TCs.
skills:
  - rbt_manual_testing
---

## Mục đích

Review chéo bộ TCs đã sinh — phát hiện issues, đề xuất action cụ thể, để người được review tự quyết định fix.

**KHÔNG tự sửa TCs.** Chỉ output report.

---

## Bước 1 — Thu thập artifacts

Đọc các file sau (nếu có):

| File | Bắt buộc? | Dùng để |
|------|-----------|---------|
| `testing/[module]/test-cases.md` | ✅ | Input chính để review |
| `testing/[module]/analysis.md` | Nên có | Verify AC coverage + Platform fit (từ Summary) |
| `testing/[module]/test-scenarios.md` | Tùy | Verify TS→TC traceability |

**Nếu không tìm thấy file:** Hỏi user cung cấp path hoặc paste nội dung.

---

## Bước 2 — Deep Review theo 8 tiêu chí

Đánh giá toàn bộ TCs theo 8 tiêu chí dưới đây. Mỗi issue tìm được → ghi nhận đầy đủ: TC ID, tiêu chí vi phạm, mô tả cụ thể, action đề xuất.

### Tier Critical — Phải fix trước khi handoff QC

| # | Tiêu chí | Cách check | Ví dụ vi phạm |
|---|----------|-----------|--------------|
| C1 | **AC Coverage** — mỗi AC có ≥1 TC positive | Dò cột AC ID, đối chiếu danh sách ACs trong `analysis.md` | AC-05 không có TC nào |
| C2 | **Test Data cụ thể** — không có placeholder | Grep "email hợp lệ", "số bất kỳ", "nhập đúng", "password hợp lệ" trong cột Test Data | TC-007: Test Data = "mật khẩu hợp lệ" |
| C3 | **Expected Result đo được** — không mơ hồ | Grep "hiển thị đúng", "load nhanh", "thành công", "phản hồi nhanh" trong cột Expected Results | TC-012: Expected = "Hệ thống phản hồi nhanh" |

### Tier Major — Nên fix trước khi handoff QC

| # | Tiêu chí | Cách check | Ví dụ vi phạm |
|---|----------|-----------|--------------|
| M1 | **TC Independence** — không TC nào phụ thuộc TC khác | Grep "TC-", "xem TC", "kết quả bước trước" trong cột Steps/Precondition | TC-015: Precondition "Đã thực hiện TC-003" |
| M2 | **Negative Coverage** — mỗi happy path AC có ≥1 TC negative | Đếm TC per AC ID theo Category; flag AC chỉ có Positive | AC-02 chỉ có Positive TCs, không có Negative |
| M3 | **Boundary Completeness** — fields có constraint phải có TC cho min/max/out-of-range | Tìm ACs có rule "từ X đến Y", "tối đa N ký tự", "≥ 0" | AC có "tối đa 255 ký tự" nhưng thiếu TC cho 256 ký tự |
| M4 | **Risk Alignment** — feature critical không set Priority thấp | Đối chiếu Risk Level + Priority theo nhóm AC ID | Happy path tính năng thanh toán set Priority = Thấp |

### Tier Minor — Cải thiện chất lượng

| # | Tiêu chí | Cách check | Ví dụ vi phạm |
|---|----------|-----------|--------------|
| N1 | **Format Consistency** — cùng column naming, cùng convention xuyên suốt file | So sánh header + cách điền value giữa các TCs | TC-001 dùng "Expected:" nhưng TC-010 dùng "Kết quả mong đợi:" |
| N2 | **Platform Fit** — TCs có dimension phù hợp platform | Đọc Platform từ `analysis.md` Summary (hoặc project `context.md` nếu Summary trống) → đối chiếu vs TCs | Test mobile nhưng không có TC nào test gesture, scroll, offline mode |

---

## Bước 3 — Tổng hợp và lưu report

Lưu ra `testing/[module]/review_report.md` theo format sau:

---

```markdown
# TC Review Report — [Module Name]

**Reviewer:** Claude AI
**Reviewed:** `testing/[module]/test-cases.md`
**Ngày review:** [date]
**Tổng TCs:** X

---

## Tổng quan

| Tier | Số issues |
|------|-----------|
| 🔴 Critical | A |
| 🟠 Major | B |
| 🟡 Minor | C |
| **Tổng** | **A+B+C** |

**Verdict:** PASS / NEEDS FIX
> PASS = không có Critical, không có Major
> NEEDS FIX = có ≥1 Critical hoặc Major

---

## Issues chi tiết

### 🔴 Critical

| # | TC / AC | Tiêu chí | Mô tả issue | Action đề xuất |
|---|---------|----------|-------------|----------------|
| 1 | TC-007 | C2 — Test Data | Test Data = "mật khẩu hợp lệ" — placeholder, không reproduce được | Thay bằng: `P@ssw0rd123` |
| 2 | AC-05 | C1 — AC Coverage | AC-05 không có TC nào trong file | Thêm ≥1 TC positive cover AC-05 |

### 🟠 Major

| # | TC / AC | Tiêu chí | Mô tả issue | Action đề xuất |
|---|---------|----------|-------------|----------------|
| 1 | AC-02 | M2 — Negative Coverage | AC-02 chỉ có Positive TCs, thiếu negative | Thêm TC: nhập [field] = null / sai format / vượt max length |

### 🟡 Minor

| # | TC / AC | Tiêu chí | Mô tả issue | Action đề xuất |
|---|---------|----------|-------------|----------------|
| 1 | TC-010 | N1 — Format | Cột Expected Results dùng "Kết quả mong đợi:" — không nhất quán với các TC khác | Đổi thành "Expected Results:" |

---

## Checklist cho người được review

**Cần fix trước khi handoff (Critical):**
- [ ] [action cụ thể từ bảng Critical]

**Nên fix trước khi handoff (Major):**
- [ ] [action cụ thể từ bảng Major]

**Có thể fix sau (Minor):**
- [ ] [action cụ thể từ bảng Minor]
```

---

## Kết thúc

Sau khi lưu file, thông báo ngắn gọn:

```
✅ Review hoàn thành. Report đã lưu tại testing/[module]/review_report.md

Verdict: NEEDS FIX
🔴 Critical: A  |  🟠 Major: B  |  🟡 Minor: C
```
