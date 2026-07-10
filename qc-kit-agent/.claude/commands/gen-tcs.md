---
description: Sinh Test Case chi tiết (bao gồm Test Scenario) từ plan-tcs.md + analysis.md. Nếu module chưa có 2 file này, tự động chain /analyze-req → /plan-tcs trước (vẫn giữ checkpoint).
skills:
  - rbt_manual_testing
  - testing_dimensions
  - component_checklist
---

Thực hiện **Section 4: Test Case Generation** từ skill `rbt_manual_testing`.

## Bước 0 — Kiểm tra `analysis.md` và `plan-tcs.md`

Kiểm tra `testing/[module]/analysis.md` và `testing/[module]/plan-tcs.md` có tồn tại không:

**Thiếu 1 trong 2 (hoặc cả 2)** → thông báo ngắn rồi **tự động chạy tuần tự** các bước còn thiếu — không cần hỏi user có muốn chạy không, vì đây là bước bắt buộc để thực hiện đúng yêu cầu user vừa đưa ra:

> ℹ️ Module này chưa có `analysis.md`/`plan-tcs.md`. Tôi sẽ tự chạy `/analyze-req` → `/plan-tcs` trước, sau đó tiếp tục `/gen-tcs`.

- Thiếu `analysis.md` → thực hiện **Section 2: Requirement Analysis** (skill `rbt_manual_testing`) — vẫn dừng đúng tại checkpoint Requirements Summary confirm và Q&A ambiguities như khi chạy `/analyze-req` độc lập.
- Sau khi có `analysis.md` (vừa tạo hoặc đã có sẵn) mà thiếu `plan-tcs.md` → thực hiện **Section 3: TC Implementation Plan** — vẫn dừng đúng tại checkpoint "Bạn muốn điều chỉnh gì không?" như khi chạy `/plan-tcs` độc lập.
- Sau khi user confirm `plan-tcs.md` → tiếp tục Bước 1 bên dưới.

**Có sẵn cả 2** → tiếp tục Bước 1 luôn, không chạy lại.

---

## Bước 1 — Kiểm tra TBD ACs (severity-gated)

Đọc `testing/[module]/analysis.md`, kiểm tra cột Status trong bảng Acceptance Criteria. Với mỗi AC status TBD, tra Severity của AMB-XX liên quan trong bảng Q&A (nếu không xác định được AMB liên quan hoặc severity không rõ, coi như **High** để an toàn).

**Không có AC nào status TBD** → tiếp tục bình thường.

**Có AC TBD nhưng AMB liên quan chỉ ở mức Medium/Low** → tự động sinh TC bình thường, tag `[UNCONFIRMED]` ở đầu Test Scenario của các TC thuộc AC đó. Không hỏi user.

**Có AC TBD với AMB liên quan ở mức High** (nghiệp vụ liên quan tiền/bảo mật/phân quyền) → dừng lại, thông báo và hỏi user:

> ⚠️ Có **X AC** chưa được confirm (status: TBD), trong đó **Y AC** liên quan ambiguity mức **High** (AMB-XX). TCs sinh từ các AC này có thể sai lệch nghiêm trọng nếu PM/BA thay đổi requirement sau.
>
> Bạn muốn xử lý thế nào?
> **A.** Chỉ sinh TCs cho AC Confirmed/Assumed — bỏ qua các AC TBD mức High
> **B.** Vẫn sinh TCs cho AC TBD mức High — tag `[UNCONFIRMED]` như các AC mức Medium/Low
> **C.** Dừng lại để resolve TBD mức High trước (chạy lại sau khi PM confirm)

> *AC TBD mức Medium/Low luôn được tag `[UNCONFIRMED]` tự động dù chọn phương án nào ở trên — câu hỏi trên chỉ áp dụng riêng cho AC TBD mức High.*

---

## Sinh Test Case chi tiết

1. Đọc `plan-tcs.md` — dùng làm khung cấu trúc (Screen → Component → Risk Level/Technique Flag/Ghi chú phụ thuộc).
2. Đọc `analysis.md` — lấy nội dung AC/Q&A để viết Steps/Expected Result.
3. Xác định platform: `analysis.md` Summary → nếu trống, `context.md` đã auto-load → đọc `.claude/skills/testing_dimensions/SKILL.md` section tương ứng.
4. Với mỗi Screen trong `plan-tcs.md` (theo đúng thứ tự xuất hiện trong file):
   - Sinh **1 TC "Verify UI tổng thể"** đầu tiên cho Screen đó (đặt đầu bảng), dựa trên mô tả "UI chung" trong plan.
   - Với mỗi Component (theo đúng thứ tự trong plan):
     - Nếu có **Technique Flag** → dựng đầy đủ Decision Table/State Transition/Boundary Tier tương ứng (tham chiếu sub-section "Complex Logic Patterns" trong skill `rbt_manual_testing`), show inline trước khi expand ra TC.
     - Sinh **Visual TCs** cho 6 states (Bảng Visual States trong skill) — đặt **TRƯỚC** logic TCs của cùng component.
     - Nếu là input field: sinh **Field-Level Validation TCs riêng cho từng trường** (Bảng Field-Level Validation trong skill) — không gộp nhiều field vào 1 TC.
     - Áp **Component Checklist** từ `.claude/skills/component_checklist/SKILL.md` theo **Component Type** đã gắn trong `plan-tcs.md` — tra trực tiếp Section A/B/C, không đoán qua keyword AC text.
     - Nếu cột "Ghi chú phụ thuộc" của component không phải "—": sinh thêm TC cho tương tác cross-component đó (gắn vào Logic của component này).
5. Áp dụng kỹ thuật thiết kế phù hợp: Equivalence Partitioning (EP), Boundary Value Analysis (BVA).
6. Áp dụng Platform Dimensions từ `.claude/skills/testing_dimensions/SKILL.md`.
7. Tuân thủ **Rule ngôn ngữ Test Scenario** (xem sub-section bên dưới).
8. Mỗi Screen là 1 heading `## [tên Screen]` riêng, với bảng TC của Screen đó ngay bên dưới — `/export-xlsx` dựa vào heading `##` để tách sheet-per-Screen.
9. Lưu output ra `testing/[module]/test-cases.md`.

> Nếu nhiều Screen, sinh từng Screen một theo đúng thứ tự trong `plan-tcs.md`, hỏi user để tiếp tục.

---

## Rule ngôn ngữ Test Scenario

- Luôn bắt đầu bằng **"Check"**, theo sau là **câu tự nhiên hoàn chỉnh, đọc như người nói** — không phải cụm từ khóa rút gọn.
- **Cấm:** ký hiệu mũi tên (`→`, `->`), gạch chéo nén ý thay cho "hoặc" (VD `A/B`), dấu hai chấm nén nhiều ý (VD `Login: email sai`), viết tắt không giải thích.
- Ví dụ:
  - ❌ Sai: `Login → Dashboard (email/pass hợp lệ)`
  - ✅ Đúng: `Check đăng nhập thành công với email và password hợp lệ`
- Visual TCs vẫn giữ prefix `[UI Visual]` trước câu "Check...".

---

## Self-Check trước khi lưu file

Sau khi draft xong toàn bộ TCs, thực hiện quick pass **trước khi lưu ra file**. Không hỏi user — tự phát hiện và tự fix.

### Checklist (theo thứ tự ưu tiên)

| # | Tiêu chí | Cách check |
|---|----------|-----------|
| C1 | **AC Coverage** — mỗi AC có ≥1 TC positive | Dò cột Traceability ID, đối chiếu với `analysis.md` |
| C2 | **Test Data cụ thể** — không có placeholder | Grep "email hợp lệ", "số điện thoại đúng", "nhập đúng", "bất kỳ" trong cột Test Data |
| C3 | **Expected Result đo được** — không mơ hồ | Grep "hiển thị đúng", "load nhanh", "thành công", "phản hồi nhanh" trong cột Expected Results |
| M1 | **TC Independence** — không TC nào refer đến TC khác | Grep "TC-" hoặc "xem TC" trong cột Steps/Precondition |
| M2 | **Negative Coverage** — mỗi happy path AC có ≥1 TC negative | Đếm TC per Traceability ID theo Category |
| M4 | **Risk Alignment** — Happy Path không set Priority thấp hơn edge case cùng AC | Đối chiếu cột Risk Level + Priority theo nhóm Traceability ID |
| L1 | **Ngôn ngữ TS** — không còn ký hiệu rút gọn | Grep `→`, `->`, dấu `:` nén ý trong cột Test Scenario |

> Mã C1-C3/M1-M2/M4 dùng chung với `/review-tcs` (M3 — Boundary Completeness — chỉ có ở `/review-tcs`, không check ở đây vì cần đối chiếu sâu constraint trong AC). L1 là tiêu chí riêng của self-check lúc sinh TC, không có ở `/review-tcs`.

### Khi phát hiện issue: tự fix luôn, ghi nhận để báo cáo.

### Summary format (hiển thị sau khi lưu file)

```
✅ Self-check hoàn thành. Đã fix: [X] issues.
- C1: Thêm TC cho AC-03 (thiếu positive case)
- C2: Cập nhật test data TC-007, TC-012 (thay placeholder bằng giá trị cụ thể)
- M2: Thêm TC negative cho AC-05
- L1: Viết lại Test Scenario TC-014 sang câu tự nhiên

File đã lưu tại testing/[module]/test-cases.md
```

Nếu không phát hiện issue nào: `✅ Self-check: 0 issues. File đã lưu tại testing/[module]/test-cases.md`

---

## Output

`testing/[module]/test-cases.md`

Bảng TC format: `ID | Function Name | Category | Risk Level | Traceability ID | Test Scenario | Precondition | Steps | Expected Results | Test Data | Priority`

- **Function Name:** Sub-module/Component từ `plan-tcs.md` (VD "Email field", "Submit button"). Nếu TC ở mức flow (không gắn 1 component cụ thể), dùng tên flow (VD "Login Flow").
- **Category:** cấp con dưới Function Name — "UI"/"Validate"/"Behavior"/"Logic" (component-level) hoặc "Happy Path"/"Negative"/"Security" (flow-level).
- **Traceability ID:** AC tương ứng từ `analysis.md` (VD `AC-05`), hoặc Q&A ID (VD `AMB-01`), hoặc `N/A` nếu không có nguồn rõ ràng — tên cột dùng chung cho mọi loại ID team quy ước để trace ngược, không giới hạn chỉ AC.

> Khi export ra `.xlsx` qua `/export-xlsx`: Sheet name = tên Screen (heading `##` trong `test-cases.md`, lấy theo tên Screen trong `plan-tcs.md`).
>
> Khi requirements thay đổi sau khi đã có `test-cases.md`: cập nhật `plan-tcs.md` trước (nếu cấu trúc Screen/Component đổi), rồi chạy lại `/gen-tcs` cho Screen bị ảnh hưởng.
