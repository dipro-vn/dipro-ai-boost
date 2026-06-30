---
description: Bước 3/3 — Sinh Test Cases từ AC hoặc TS. Nếu input là AC, hỏi có muốn review TS trước không. Nếu input là TS, sinh TCs luôn.
skills:
  - rbt_manual_testing
  - testing_dimensions
  - component_checklist
---

Thực hiện **Section 4 + 5** từ skill `rbt_manual_testing` tùy theo input.

## Bước 0 — Module Risk Snapshot (bắt buộc trước khi sinh TCs)

Trước khi làm bất cứ điều gì, xác định cơ sở risk:

**Nếu có `testing/[module]/modules.md`:**
→ Dùng risk level per sub-module từ file đó. Tiếp tục ngay.

**Nếu không có `modules.md`:**
→ Làm **inline decomposition** ngay trong session:
1. Đọc `analysis.md`
2. Liệt kê nhanh các sub-module/luồng chính + risk level (High/Medium/Low) theo nhận định
3. Show cho user dưới dạng bảng ngắn, hỏi:

> Đây là phân rã module tôi xác định được. Bạn muốn điều chỉnh gì không?
> *(Nếu không, tôi sẽ dùng bảng này làm cơ sở risk cho TCs)*

4. User confirm (hoặc chỉnh sửa) → tiếp tục

> **Lưu ý:** Inline decomposition không lưu ra `modules.md`. Nếu bạn cần artifact đầy đủ cho estimate hoặc test plan, chạy `/decompose-modules` trước.

---

## Bước 0.5 — Kiểm tra TBD ACs (nếu có analysis.md)

Trước khi tiếp tục, đọc `testing/[module]/analysis.md` và kiểm tra cột Status:

**Nếu không có AC nào status TBD** → tiếp tục bình thường.

**Nếu có ≥1 AC status TBD** → thông báo và hỏi user:

> ⚠️ Có **X AC** chưa được confirm (status: TBD). TCs sinh từ các AC này có thể sai nếu PM/BA thay đổi requirement sau.
>
> Bạn muốn xử lý thế nào?
> **A.** Chỉ sinh TCs cho AC Confirmed/Assumed — bỏ qua TBD
> **B.** Sinh TCs cho tất cả — tag `[UNCONFIRMED]` vào Test Scenario của TCs từ TBD ACs
> **C.** Dừng lại để resolve TBD trước (chạy lại sau khi PM confirm)

> *Nếu chọn B: TCs từ TBD ACs sẽ có prefix `[UNCONFIRMED]` ở cột Test Scenario để dễ nhận biết và review sau.*

---

## Xác định input và chọn luồng

**Sau Bước 0 và 0.5**, kiểm tra input của user:

### Nếu input là `analysis.md` (hoặc requirements doc chưa có TS)

Hỏi user:

> Bạn muốn sinh theo cách nào?
> **A.** Sinh TS trước → bạn review → chạy lại `/gen-tcs` để sinh TCs chi tiết
> **B.** Sinh TCs luôn (không cần review TS)

**Nếu chọn A — Sinh TS trước:**
1. Đọc `testing/[module]/analysis.md` + risk snapshot từ Bước 0
2. Xác định platform: đọc `analysis.md` Summary → nếu trống, dùng Platform trong project `context.md` đã auto-load → nếu vẫn không rõ, hỏi user → đọc `testing_dimensions/SKILL.md`
3. Sinh Test Scenarios bao phủ: Happy Path, Alternate, Exception, Security, UI Validation, Business Logic, Data Integrity, Platform-specific
4. Gap Analysis: đảm bảo mỗi AC có ít nhất 1 Scenario cover
5. Lưu ra `testing/[module]/test-scenarios.md`
6. Kết thúc với thông báo:

> ✅ Test Scenarios đã được lưu vào `testing/[module]/test-scenarios.md`.
> Bạn có cần chỉnh sửa gì thêm không? Nếu không, hãy gọi lại `/gen-tcs` để sinh Test Cases chi tiết nhé.

**Nếu chọn B — Sinh TCs luôn:**

> ⚠️ **Mode B** không tạo `test-scenarios.md`. Khi requirements thay đổi sau này, khó xác định TC nào bị ảnh hưởng mà không có TS làm anchor. Nên dùng **Mode A** nếu module có nhiều ACs, logic phức tạp, hoặc requirements đang thay đổi thường xuyên.

1. Derive Test Scenarios nội bộ (không lưu file riêng)
2. Tiếp tục sinh TCs theo hướng dẫn bên dưới

---

### Nếu input là `test-scenarios.md`

Sinh TCs luôn, không hỏi thêm.

---

## Sinh Test Cases chi tiết

*(Chạy khi input là TS, hoặc khi user chọn Mode B)*

1. Dùng risk snapshot từ Bước 0 để assign Risk Level cho từng TC
2. **Nhận diện và áp dụng Complex Logic Patterns** trước khi sinh TC (tham chiếu sub-section "Complex Logic Patterns" trong skill `rbt_manual_testing`):
   - AC có ≥2 conditions kết hợp → dựng **Decision Table** inline
   - AC có workflow trạng thái → vẽ **State Transition** diagram inline
   - AC có boundary tiers → list **Boundary Tier** values inline
3. Với mỗi scenario, sinh TC đầy đủ theo Output Format trong Reference Library của skill
4. Áp dụng Field-Level Validation (tham chiếu Bảng Field-Level Validation trong skill)
5. Sinh UI Visual TCs cho 6 states per field (tham chiếu Bảng Visual States trong skill)
6. Áp dụng kỹ thuật thiết kế phù hợp: EP, BVA
7. Áp dụng Platform Dimensions từ `testing_dimensions/SKILL.md`
8. **Áp dụng Component Checklist** từ `component_checklist/SKILL.md`:
   - **Nếu có design input (Figma link / screenshot / PDF):** đọc design → nhận diện component types → áp section tương ứng; lấy field labels thực từ design cho test data; dùng tên frame/screen trong Expected Result của Visual TCs (với Figma: đính kèm screenshot frame)
   - **Nếu không có design:** auto-detect từ AC text theo keywords:
     - Form keywords ("nhập", "upload", "download", "import", "export", "đăng ký", "tạo mới", "cập nhật", "xóa") → áp **Section A**
     - Layout keywords ("dialog", "popup", "breadcrumb", "pager", "tooltip", "hyperlink") → áp **Section B**
     - Data display keywords ("tìm kiếm", "search", "danh sách", "bảng", "paging", "sort", "filter", "lọc") → áp **Section C**
   - Confirm với user: "Tôi sẽ áp component checklist: [A/B/C]. Có cần thêm/bỏ gì không?"
9. Lưu output ra `testing/[module]/test-cases.md`

> Nếu scope lớn, sinh từng Module một và hỏi user để tiếp tục.

---

## Self-Check trước khi lưu file

Sau khi draft xong toàn bộ TCs, thực hiện quick pass **trước khi lưu ra file**. Không hỏi user — tự phát hiện và tự fix.

### Checklist (theo thứ tự ưu tiên)

| # | Tiêu chí | Cách check |
|---|----------|-----------|
| C1 | **AC Coverage** — mỗi AC có ≥1 TC positive | Dò cột AC ID, đối chiếu với `analysis.md` |
| C2 | **Test Data cụ thể** — không có placeholder | Grep "email hợp lệ", "số điện thoại đúng", "nhập đúng", "bất kỳ" trong cột Test Data |
| C3 | **Expected Result đo được** — không mơ hồ | Grep "hiển thị đúng", "load nhanh", "thành công", "phản hồi nhanh" trong cột Expected Results |
| M1 | **TC Independence** — không TC nào refer đến TC khác | Grep "TC-" hoặc "xem TC" trong cột Steps/Precondition |
| M2 | **Negative Coverage** — mỗi happy path AC có ≥1 TC negative | Đếm TC per AC ID theo Category |
| M3 | **Risk Alignment** — Happy Path không set Priority thấp hơn edge case cùng AC | Đối chiếu cột Risk Level + Priority theo nhóm AC ID |

### Khi phát hiện issue: tự fix luôn, ghi nhận để báo cáo.

### Summary format (hiển thị sau khi lưu file)

```
✅ Self-check hoàn thành. Đã fix: [X] issues.
- C1: Thêm TC cho AC-03 (thiếu positive case)
- C2: Cập nhật test data TC-007, TC-012 (thay placeholder bằng giá trị cụ thể)
- M2: Thêm TC negative cho AC-05

File đã lưu tại testing/[module]/test-cases.md
```

Nếu không phát hiện issue nào: `✅ Self-check: 0 issues. File đã lưu tại testing/[module]/test-cases.md`

---

## Output

- Mode A (lần 1): `testing/[module]/test-scenarios.md`
- Mode A (lần 2) hoặc Mode B: `testing/[module]/test-cases.md`

Bảng TC format: `ID | Function Name | Category | Risk Level | AC ID | TS ID | Test Scenario | Precondition | Steps | Expected Results | Test Data | Priority`

- **TS ID:** TS tương ứng từ `test-scenarios.md` (VD: `TS-001`). Điền `N/A` nếu dùng Mode B (không có TS artifact).

> **Khi requirements thay đổi sau khi đã có `test-cases.md`:** Dùng `/update-tcs` để cập nhật delta — không cần chạy lại pipeline từ đầu.
