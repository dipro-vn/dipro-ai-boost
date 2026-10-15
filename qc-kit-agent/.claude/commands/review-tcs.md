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
| `testing/[module]/analysis.md` | Nên có (bản Full) | Verify AC coverage + Platform fit (từ Summary). Bản Quick không có file này, xem "Xác định chế độ" bên dưới |
| `testing/[module]/plan-tcs.md` | Tùy (bản Full) | Verify Sheet/Function Name/Category đúng theo cấu trúc Screen/Component đã plan, verify Luồng E2E chính khớp Bảng 2. Bản Quick không có file này |

**Nếu không tìm thấy file:** Hỏi user cung cấp path hoặc paste nội dung.

### Xác định chế độ: Full hay Quick

Đọc dòng đầu của `test-cases.md`:

- Có dòng `> Mode: Quick ...` → **bản Quick** (sinh thẳng từ spec bởi `/gen-tcs`, không có `analysis.md`/`plan-tcs.md`). Áp "Quy tắc cho bản Quick" bên dưới.
- Không có → **bản Full**, review như mô tả ở các bước sau.

**Bản Quick — nguồn đối chiếu thay thế:**

| Cần | Lấy từ |
|---|---|
| Danh sách yêu cầu (thay AC của `analysis.md`) | `REQ-xx` trong cột Traceability ID của `test-cases.md`, đối chiếu với spec ở dòng `**Nguồn:**` đầu file. Không đọc được spec → hỏi user path, không tự đoán |
| Platform (thay Summary của `analysis.md`) | Dòng `**Platform:**` đầu `test-cases.md`, sau đó `CLAUDE.md` |
| Luồng E2E và ô phân quyền (thay `plan-tcs.md`) | Spec; Bảng 1/Bảng 2 trong `## High Risk & E2E` của chính file TC |

Bản Quick **không có Q&A**: Expected tag `[ASSUMED]` là suy luận chưa PM/BA xác nhận, review chỉ kiểm độ đo được, không kiểm đúng/sai nghiệp vụ.

---

## Bước 2 — Deep Review theo 8 tiêu chí

Đánh giá toàn bộ TCs theo 8 tiêu chí dưới đây. Mỗi issue tìm được → ghi nhận đầy đủ: TC ID, tiêu chí vi phạm, mô tả cụ thể, action đề xuất.

### Tier Critical — Phải fix trước khi handoff QC

| # | Tiêu chí | Cách check | Ví dụ vi phạm |
|---|----------|-----------|--------------|
| C1 | **AC Coverage** — mỗi AC có ≥1 TC positive | Dò cột Traceability ID, đối chiếu danh sách ACs trong `analysis.md` | AC-05 không có TC nào |
| C2 | **Test Data cụ thể** — không có placeholder | Grep "email hợp lệ", "số bất kỳ", "nhập đúng", "password hợp lệ" trong cột Test Data | TC-007: Test Data = "mật khẩu hợp lệ" |
| C3 | **Expected Result đo được** — không mơ hồ | Grep "hiển thị đúng", "load nhanh", "thành công", "phản hồi nhanh" trong cột Expected Results. "Hiển thị đúng" chỉ được chấp nhận khi nêu rõ đối tượng và đối chiếu được với Test Data hoặc Steps (VD "Hiển thị đúng dữ liệu đã nhập như Test Data"); dạng trơn thì báo lỗi | TC-012: Expected = "Hệ thống phản hồi nhanh" |

### Tier Major — Nên fix trước khi handoff QC

| # | Tiêu chí | Cách check | Ví dụ vi phạm |
|---|----------|-----------|--------------|
| M1 | **TC Independence** — không TC nào phụ thuộc TC khác | Grep mã module của chính file (VD `APB-\d{3}`, lấy từ tiền tố cột ID), "xem TC", "kết quả bước trước" trong cột Steps/Precondition | APB-015: Precondition "Đã thực hiện APB-003" |
| M2 | **Negative Coverage** — mỗi happy path AC có ≥1 TC negative (**trừ** AC `[UNCONFIRMED]` mà Q&A liên quan ở mức Medium/Low — tra Severity trong `analysis.md` — chỉ có 1 TC đại diện theo thiết kế của `/gen-tcs`; AC High vẫn phải có negative. Khi Q&A đã trả lời và `analysis.md` đã cập nhật thì AC không còn ngoại lệ) | Gom TC theo Traceability ID; TC là **negative** khi Expected báo lỗi, từ chối, chặn hoặc không thực hiện được hành động (hoặc Category `Negative`/`Security`). Không đếm theo Category vì TC mức component chỉ có UI/Validate/Behavior/Logic. Flag AC chỉ có Positive | AC-02 chỉ có Positive TCs, không có Negative |
| M3 | **Boundary Completeness** — fields có constraint phải có TC cho min/max/out-of-range | Tìm ACs có rule "từ X đến Y", "tối đa N ký tự", "≥ 0" | AC có "tối đa 255 ký tự" nhưng thiếu TC cho 256 ký tự |
| M4 | **Bảng High Risk & E2E đúng và đủ** — mục `## High Risk & E2E` có Bảng 1 (nhóm TC high risk) và Bảng 2 (E2E); mọi ID tồn tại, Bảng 1 phủ ô ❌ Permission Matrix + TC của AC High, Bảng 2 phủ luồng chính | Đối chiếu ID trong hai bảng với bảng TC, Permission Matrix và Luồng E2E chính của plan | Bảng 1 thiếu TC phân quyền của ô ❌; Bảng 2 có ID không còn trong bảng TC |

> Mã C1-C3/M1-M2 dùng chung với self-check của `/gen-tcs` (M4 tương ứng Q1-Q3 của `/gen-tcs`). M3 (Boundary Completeness) chỉ có ở `/review-tcs` — cần đối chiếu sâu constraint trong AC nên không chạy tự động lúc sinh TC.

### Quy tắc cho bản Quick

Chỉ áp khi `test-cases.md` có dòng `> Mode: Quick`. Các tiêu chí còn lại (C2, C3, M1, M3, N1) chạy như bản Full.

| # | Điều chỉnh cho bản Quick |
|---|---|
| C1 | Đối chiếu theo **`REQ-xx`** rút từ spec (thay AC-xx): mỗi yêu cầu trong spec có ≥1 TC positive. Yêu cầu nào spec nêu mà không có TC → Critical, trừ khi đã nằm trong mục "Hành vi spec chưa nêu" của output Quick (spec im lặng thì không tính là thiếu) |
| M2 | Đếm TC per `REQ-xx` theo Category như bản Full; TC chỉ có Expected tag `[ASSUMED]` vẫn tính bình thường |
| M3 | Constraint lấy từ spec thay vì AC |
| M4 | Chỉ kiểm: mọi ID ở Bảng 1/Bảng 2 còn tồn tại trong bảng TC; Bảng 2 có 3-6 luồng, mỗi bước có TC hoặc ghi `thiếu TC`, có cột "Nếu fail thì"; Bảng 1 phủ các ô bị cấm/TC phân quyền **rút từ spec** và không vượt khoảng 30% tổng TC. Không đối chiếu Permission Matrix/Luồng E2E của `plan-tcs.md` vì không có file này |
| N2 | Platform lấy theo bảng "nguồn đối chiếu thay thế" ở Bước 1 |
| **Không áp** | Kiểm `[UNCONFIRMED]`/mã Q&A và nhất quán plan ↔ analysis (không có các file này) |

**Không đánh Critical/Major cho việc bản Quick thiếu Q&A hay thiếu plan** — đó là đặc điểm của chế độ, không phải lỗi của bộ TC. Lưu ý này được ghi trong report (xem "Mode" ở Bước 3).

### Tier Minor — Cải thiện chất lượng

| # | Tiêu chí | Cách check | Ví dụ vi phạm |
|---|----------|-----------|--------------|
| N1 | **Format Consistency** — cùng column naming, cùng convention xuyên suốt file | So sánh header + cách điền value giữa các TCs | TC-001 dùng "Expected:" nhưng TC-010 dùng "Kết quả mong đợi:" |
| N2 | **Platform Fit** — TCs có dimension phù hợp platform | Đọc Platform từ `analysis.md` Summary (hoặc project `CLAUDE.md` nếu Summary trống) → đối chiếu vs TCs | Test mobile nhưng không có TC nào test gesture, scroll, offline mode |

---

## Bước 3 — Tổng hợp và lưu report

Lưu ra `testing/[module]/review_report.md` theo format sau:

---

```markdown
# TC Review Report — [Module Name]

**Reviewer:** Claude AI
**Reviewed:** `testing/[module]/test-cases.md`
**Mode:** Full | Quick *(Quick: C1/M2/M3 đối chiếu `REQ-xx` theo spec, chưa có Q&A; M4 chỉ kiểm ID và luồng E2E, không đối chiếu plan; Expected `[ASSUMED]` chưa PM/BA xác nhận)*
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
