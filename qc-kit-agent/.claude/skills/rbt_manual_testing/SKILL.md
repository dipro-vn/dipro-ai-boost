---
name: RBT Manual Testing
description: Skill sinh manual test cases theo quy trình AI-RBT — pipeline 3 bước per module (analyze-req → plan-tcs → gen-tcs), context.md điền tay 1 lần cho project. Dùng kết hợp với requirements_analyzer và testing_dimensions.
---

# RBT Manual Testing

## Description

Skill hỗ trợ sinh manual test cases chất lượng cao theo quy trình Risk-Based Testing (RBT). Được tổ chức thành **4 sections**, tương ứng pipeline 3 bước per module + 1 bước setup project (không cần command).

**Pipeline:**
```
context.md (điền tay 1 lần) → /analyze-req → /plan-tcs → /gen-tcs
```

**Nguyên tắc cốt lõi:**
- **Human Strategy:** Con người xác định chiến lược, mức độ rủi ro và tiêu chuẩn — thể hiện rõ nhất ở bước `/plan-tcs`, nơi user duyệt cấu trúc Screen/Component trước khi AI sinh hàng loạt TC
- **AI Execution:** AI thực hiện phân tích, viết TCs và rà soát lỗ hổng
- **Human Verification:** Con người kiểm tra lại kết quả trước khi chốt

---

## When to Use

Sử dụng skill này khi:
- Sinh manual test cases từ requirements / user stories
- Phân tích requirements để phát hiện ambiguity và verify AC
- Lên plan triển khai test (phân rã Screen/Component, risk level) có traceability với AC
- Áp dụng Risk-Based Testing (đánh giá rủi ro cho test cases)
- Chuẩn hóa test cases sang bảng Markdown (Backlog/Excel format)

**KHÔNG** sử dụng skill này khi:
- Cần chuẩn hóa bug report → dùng `/gen-bug-report`

---

# Section 1: Context Setup

**Không có command riêng** — `context.md` là file điền tay.

**Khi nào cần:**
- **Project-base** (context.md do PM's agent flow tạo và maintain): QC không cần làm gì — context.md đã tồn tại, được CLAUDE.md auto-load.
- **Labo / Maintain** (dùng kit rời, chưa có context.md): QC tự tạo file `context.md` ở **root project**, copy template bên dưới và điền tay.

**Output file:** `context.md` (root project)

```markdown
# [Project Name]
Mô tả: [Hệ thống làm gì, đối tượng dùng là ai]

## Actors
- [Actor 1]: [vai trò]
- [Actor 2]: [vai trò]

## Platform chính
- [Web / Mobile / API]

## Business Rules toàn cục
- [Rule áp dụng ở mọi module — để trống nếu không có]

## Quy ước
- Output language: Tiếng Việt
```

> Giữ ngắn — dưới 20 dòng. Thông tin đặc thù module để trong `## Summary` của `analysis.md`. Filter trước khi ghi: *"Đây là rule của cả project hay của riêng module này?"* — chỉ ghi thông tin là rule của cả project.

---

# Section 2: Requirement Analysis

**Command tương ứng:** `/analyze-req`

**Mục đích:** Phân tích requirements để phát hiện điểm mờ (Q&A) và mapping REQ → AC. Hai việc chạy song song vì Q&A làm AC chất lượng hơn. Output là bộ AC + Screen Inventory đủ tốt để lên `/plan-tcs`.

**Agent phải:**
1. Đọc requirements doc — project context đã được auto-load qua CLAUDE.md
2. **Song song thực hiện:**

   **A — Phát hiện Ambiguities:**
   - Yêu cầu thiếu sót (độ dài field, timeout, hành vi mất kết nối...)
   - Yêu cầu mâu thuẫn hoặc chưa rõ ràng
   - Nếu có design input (Figma link / screenshot / PDF): đọc design → cross-check theo bảng trong `requirements_analyzer/SKILL.md` (screen inventory, UI states, field names, annotations) → thêm AMB items cho mỗi inconsistency phát hiện
   - Sinh danh sách câu hỏi AMB-XX kèm assumption nếu không được trả lời

   **B — Mapping REQ → AC:**
   - Xác định các luồng: Happy Path, Alternate Paths, Exception Paths
   - Map từng requirement thành Acceptance Criteria có thể kiểm chứng
   - Đánh dấu AC nào cần clarify từ Q&A (Status: TBD)

3. Nếu có design input đã cross-check: lưu lại danh sách frame/screen đã confirm vào section **Screen Inventory** — để `/plan-tcs` dùng trực tiếp, không đọc lại Figma hay đoán cấu trúc từ text.
4. Tổng hợp vào `analysis.md` — 4 sections: Summary, Q&A, AC, Screen Inventory (nếu có)

**Output file:** `testing/[module]/analysis.md`

```markdown
# Requirements Analysis: [Module Name]

## Summary
[Tên tính năng, mục đích nghiệp vụ, actors, luồng chính, scope, dependencies]

## Q&A — Ambiguities

| ID | Reference | Screen | Question (VN) + Assumption/Đề xuất | Impact | Severity | Status |
|----|-----------|--------|--------------------------------------|--------|----------|--------|
| AMB-01 | REQ-XX | [tên màn hình] | ... Đề xuất: ... | ... | High / Medium / Low | TBD |

> **TBD** = chưa được PM/BA confirm | **Answered** = đã có câu trả lời

---

## Acceptance Criteria

| REQ ID | AC ID | AC Content | Status |
|--------|-------|------------|--------|
| REQ-01 | AC-01 | ... | Confirmed / Assumed / TBD |

## Screen Inventory
*(chỉ có nếu đã cross-check với design — Figma/screenshot/PDF)*

| Screen/Frame | Nguồn (Figma frame name) | Ghi chú |
|---|---|---|
| [Tên screen] | [Frame name trong Figma] | ... |

## History
- v1 ([ngày]): /analyze-req — khởi tạo
```

> AC **Status TBD** = AC phụ thuộc vào Q&A chưa được trả lời — `/gen-tcs` sẽ cảnh báo khi gặp AC này.

---

# Section 3: TC Implementation Plan

**Command tương ứng:** `/plan-tcs`

**Mục đích:** Xác định chiến lược test ở cấp module — cấu trúc phân rã Screen/Component + risk level + technique hint — trước khi sinh TC. Đây là bước **bắt buộc**, thể hiện nguyên tắc Human Strategy.

**Agent phải:**
1. Đọc `analysis.md` (Summary + AC + Screen Inventory nếu có) + `context.md` (platform, auto-load)
2. **Xác định Screen (đơn vị màn hình)** — tổng quát, không giới hạn CRUD List/Create/Edit/Detail. 1 Screen = 1 đơn vị điều hướng riêng biệt user thực sự thấy (1 URL riêng, 1 dialog full-screen, 1 step trong wizard, 1 tab riêng).
   - Có Screen Inventory → dùng trực tiếp.
   - Không có → suy luận từ Summary/luồng trong AC, tự flag rõ "Phân rã dựa trên suy luận từ text, chưa có design xác nhận."
3. Với mỗi Screen:
   a. Ghi nhận **UI chung (layout tổng thể)** — 1 dòng mô tả ngắn ở cấp Screen.
   b. Liệt kê **từng Component theo đúng thứ tự xuất hiện trên UI**.
4. Với mỗi Component, xác định:
   - **Component Type** (Textbox/Dropdown/Checkbox/Radio/Table/Dialog/Button/File Upload/...) — dùng để tra thẳng `component_checklist/SKILL.md` ở bước `/gen-tcs`, không đoán qua keyword.
   - **Risk Level** (High/Medium/Low) — High: nghiệp vụ quan trọng/tiền/bảo mật/phân quyền; Medium: luồng chính không critical; Low: UI validation/happy path đơn giản.
   - **Technique Flag** (nhẹ, optional) — note ngắn nếu AC có dấu hiệu cần Decision Table/State Transition/Boundary Tier. **Không dựng bảng/diagram đầy đủ ở bước này.**
5. **Rule tương tác chéo component:** khi xác định Logic của 1 component, luôn tự hỏi "component này có phụ thuộc/ảnh hưởng component nào khác trên cùng màn hình không?" — ghi vào cột "Ghi chú phụ thuộc" của component chịu trách nhiệm chính, không tạo category riêng.
6. **Xác định Assumption môi trường test** — liệt kê ngắn các điều kiện hạ tầng/bên ngoài mà TC ở bước `/gen-tcs` sẽ ngầm dựa vào để chạy được (VD: API bên thứ 3 available lúc test, cronjob/background job chạy đúng chu kỳ thật, không bị mock/stub). Đây KHÔNG phải câu hỏi cho PM/BA (khác AMB-XX) — chỉ là lưu ý cho người chạy test. Để trống nếu module không phụ thuộc hạ tầng ngoài.
7. Lưu ra `testing/[module]/plan-tcs.md`, show cho user confirm.

**Output file:** `testing/[module]/plan-tcs.md`

```markdown
# TC Implementation Plan: [Module Name]

## [Screen 1 Name]
- **UI chung:** [mô tả ngắn layout tổng thể]

| Component | Component Type | Risk Level | Technique Flag | Ghi chú phụ thuộc |
|---|---|---|---|---|
| [Tên component] | [Loại] | High/Medium/Low | [tên pattern nếu có, — nếu không] | [phụ thuộc component nào, — nếu không] |

## [Screen 2 Name]
...

## Ghi chú tổng quát
- **Assumption môi trường test:** [điều kiện hạ tầng/bên ngoài TC sẽ dựa vào — để trống nếu không có]
```

> **Lưu ý:** `/gen-tcs` sẽ từ chối chạy nếu module chưa có `plan-tcs.md`.

---

# Section 4: Test Case Generation

**Command tương ứng:** `/gen-tcs`

**Mục đích:** Sinh Test Case chi tiết (bao gồm Test Scenario — không còn artifact riêng) từ `plan-tcs.md` + `analysis.md`, áp dụng Field-Level Validation, Visual States, và kỹ thuật thiết kế test case.

**Agent phải:**
1. Đọc `plan-tcs.md` (bắt buộc — nếu chưa có, dừng lại yêu cầu chạy `/plan-tcs` trước). File này quyết định *sinh cái gì* và *sâu tới đâu*.
2. Đọc `analysis.md` (nội dung AC đầy đủ + Q&A status) — quyết định *nội dung* Steps/Expected Result. Kiểm tra TBD ACs trước khi tiếp tục.
3. Xác định platform: đọc `analysis.md` Summary → nếu trống, dùng Platform trong `context.md` đã auto-load → đọc `testing_dimensions/SKILL.md` section tương ứng.
4. Với mỗi Screen trong `plan-tcs.md` (đúng thứ tự):
   a. Sinh **1 TC "Verify UI tổng thể"** trước tiên (đặt đầu bảng của sheet đó), dựa trên mô tả "UI chung" trong plan.
   b. Với mỗi Component (đúng thứ tự trong `plan-tcs.md`):
      - Nếu có Technique Flag → **dựng đầy đủ** Decision Table/State Transition/Boundary Tier tương ứng (xem sub-section "Complex Logic Patterns"), show inline trước khi expand ra TC.
      - Sinh **Visual TCs** theo 6 states (Bảng Visual States) — đặt **TRƯỚC** logic TCs của cùng component.
      - Nếu là input field: sinh **Field-Level Validation TCs riêng cho từng trường** (Bảng Field-Level Validation) — không gộp nhiều field vào 1 TC.
      - Áp `component_checklist/SKILL.md` theo **Component Type** đã gắn trong `plan-tcs.md` (Section A/B/C — tra trực tiếp, không đoán qua keyword AC text).
      - Khi xét Logic: áp dụng cột "Ghi chú phụ thuộc" từ `plan-tcs.md` — nếu component phụ thuộc component khác, sinh thêm TC cho tương tác đó.
5. Áp dụng kỹ thuật thiết kế phù hợp: Equivalence Partitioning (EP), Boundary Value Analysis (BVA).
6. Áp dụng Platform Dimensions từ `testing_dimensions/SKILL.md`.
7. Lưu output ra `testing/[module]/test-cases.md`.

> Nếu scope lớn (nhiều Screen), sinh từng Screen một theo thứ tự trong `plan-tcs.md`, hỏi user để tiếp tục.

## Rule ngôn ngữ Test Scenario

- Luôn bắt đầu bằng **"Check"**, theo sau là **câu tự nhiên hoàn chỉnh, đọc như người nói** — không phải cụm từ khóa rút gọn.
- **Cấm:** ký hiệu mũi tên (`→`, `->`), gạch chéo nén ý thay cho "hoặc" (VD `A/B`), dấu hai chấm nén nhiều ý (VD `Login: email sai`), viết tắt không giải thích.
- Ví dụ:
  - ❌ Sai: `Login → Dashboard (email/pass hợp lệ)`
  - ✅ Đúng: `Check đăng nhập thành công với email và password hợp lệ`
- Visual TCs vẫn giữ prefix `[UI Visual]` trước câu "Check...".

**Output file:** `testing/[module]/test-cases.md`

---

## Complex Logic Patterns

Agent **tự động nhận diện** từ nội dung AC và áp dụng pattern phù hợp **trước khi sinh TC**. Có thể áp nhiều pattern trong 1 lần nếu AC phức tạp. Nếu `plan-tcs.md` đã có Technique Flag cho component đang xử lý, dùng đó làm gợi ý — nhưng vẫn phải tự dựng bảng/diagram đầy đủ ở đây (Technique Flag chỉ là note ngắn, không phải bảng hoàn chỉnh).

### Pattern 1: Decision Table

**Trigger:** AC có ≥2 điều kiện kết hợp tạo ra kết quả khác nhau.
Dấu hiệu: "nếu... thì", "khi... và", multiple conditions, **phân quyền theo role**, role-based behavior.

> **Permission/Auth là use case phổ biến nhất của pattern này.** Bất cứ khi nào AC mô tả "role X được làm Y trên resource Z" → bắt buộc dựng Decision Table trước khi sinh TC.

**Agent làm:**
1. Liệt kê tất cả điều kiện (conditions)
2. Dựng bảng tổ hợp → kết quả
3. Show inline cho user thấy trước khi expand ra TC

```
Ví dụ 1 — Permission: Role × Action × Resource

| Role    | Action | Resource      | Kết quả     |
|---------|--------|---------------|-------------|
| Admin   | Edit   | Own record    | ✅ Allowed  |
| Admin   | Edit   | Other record  | ✅ Allowed  |
| Editor  | Edit   | Own record    | ✅ Allowed  |
| Editor  | Edit   | Other record  | ❌ Denied   |
| Viewer  | Edit   | Any record    | ❌ Denied   |

Ví dụ 2 — Business logic: Role × Trạng thái đơn hàng

| Role    | Trạng thái | Có thể hủy? |
|---------|------------|-------------|
| Admin   | Pending    | ✅ Có       |
| Admin   | Shipped    | ❌ Không    |
| User    | Pending    | ✅ Có       |
| User    | Shipped    | ❌ Không    |
```

**Sau đó:** mỗi row = ít nhất 1 TC riêng. Với Permission table: test cả allowed (positive) lẫn denied (negative) — không chỉ test happy path.

---

### Pattern 2: State Transition

**Trigger:** AC có workflow trạng thái, object chuyển qua nhiều states.
Dấu hiệu: "trạng thái", "chuyển sang", "flow", tên states rõ ràng (Draft, Pending, Approved...).

**Agent làm:**
1. Vẽ state diagram dạng text
2. Xác định transitions hợp lệ và không hợp lệ
3. **Xác định back transition** — tự hỏi: có transition nào đi NGƯỢC lại state trước đó không (khác invalid transition — đây là đường lùi CÓ CHỦ ĐÍCH trong thiết kế, VD "mở lại", "hủy duyệt", "yêu cầu sửa lại")? Nếu có, đánh dấu riêng — side-effect của đi lùi thường khác đi tiến (thu hồi quyền đã cấp, xóa timestamp đã đóng dấu, báo lại người liên quan...), không thể coi là "test lại y hệt transition tiến theo chiều ngược".
4. Show inline trước khi sinh TC

```
Ví dụ — Workflow phê duyệt:

[Draft] --submit--> [Pending]
[Pending] --approve--> [Approved]
[Pending] --reject--> [Rejected]
[Approved] --cancel--> [Cancelled]

Back transitions (đi lùi có chủ đích, khác invalid):
[Approved] --reopen--> [Pending]

Invalid transitions:
[Draft] --approve--> ❌
[Approved] --submit--> ❌
```

**Sau đó:** test mỗi transition hợp lệ (1 TC) + mỗi invalid transition quan trọng (1 TC) + mỗi back transition (1 TC riêng — verify cả state cuối đúng chưa lẫn side-effect đi kèm, không gộp chung với transition tiến).

---

### Pattern 3: Boundary Tier

**Trigger:** AC có ngưỡng phân loại tạo ra hành vi khác nhau theo dải giá trị.
Dấu hiệu: "từ X đến Y", %, tier/level/rank, ngưỡng số cụ thể.

**Agent làm:**
1. List đủ các tier và boundary values của từng tier
2. Show inline trước khi sinh TC

```
Ví dụ — Phí vận chuyển theo giá trị đơn hàng:

Tier 1 (0đ - 99,999đ):     test 0, 1, 99,998, 99,999
Tier 2 (100,000đ - 499,999đ): test 100,000, 100,001, 499,998, 499,999
Tier 3 (500,000đ+):         test 500,000, 500,001, giá trị rất lớn
```

**Sau đó:** mỗi boundary value = 1 TC riêng (không gộp).

---

# Reference Library

## Platform Context Detection

Trước khi sinh TCs, agent **bắt buộc** xác định platform:
```
1. Feature này chạy trên platform nào? (Web / Mobile / Desktop / Nhiều platform?)
2. App có hỗ trợ multi-language không?
3. Có tính năng đặc thù nào không? (push notification, offline mode, v.v.)
```

Sau khi xác định:
- Đọc `.claude/skills/testing_dimensions/SKILL.md` — section tương ứng với platform
- Áp thêm các dimension đó vào bộ TCs đang sinh (lớp bổ sung, không thay thế base TCs)
- Cross-platform: chỉ áp các section **có liên quan** đến feature đang test

---

## Bảng Field-Level Validation

Khi form/UI có các input fields, agent **BẮT BUỘC** phải liệt kê từng trường và sinh validation TCs riêng theo loại:

| Loại Field | Validation cần test |
|---|---|
| **Text (Name, Address...)** | Required/Optional · Min length · Max length · Chỉ khoảng trắng (whitespace-only) · Ký tự đặc biệt (`<>&"'`) · XSS injection (`<script>alert(1)</script>`) · SQL injection (`' OR 1=1--`) · Unicode/Emoji · Leading/trailing spaces |
| **Email** | Format hợp lệ (`user@domain.com`) · Thiếu `@` · Thiếu domain · Domain không hợp lệ · Nhiều `@` · Ký tự đặc biệt trước `@` · Max length · Case sensitivity · Email đã tồn tại (nếu unique) |
| **Phone** | Chỉ chấp nhận số · Prefix hợp lệ (ví dụ: `+84`, `0`) · Min/Max length · Chữ cái xen lẫn · Dấu `-`, `.`, khoảng trắng · Mã vùng không hợp lệ |
| **Date / DateTime** | Format đúng (dd/MM/yyyy, ISO...) · Ngày không tồn tại (`31/02`, `30/02`) · Năm nhuận (`29/02/2024`) · Ngày quá khứ / tương lai (tùy business rule) · Giá trị min/max date · Timezone (nếu áp dụng) |
| **Number / Currency** | Min/Max value · Số âm · Số 0 · Số thập phân · Ký tự không phải số · Overflow (số cực lớn) · Leading zeros · Định dạng currency (dấu phẩy, dấu chấm) |
| **Dropdown / Select** | Giá trị mặc định · Tất cả options hợp lệ · Option bị disabled · Thay đổi selection · Required validation (chưa chọn) |
| **Checkbox / Radio** | Trạng thái mặc định · Check/Uncheck · Required validation · Nhóm radio (chỉ chọn 1) |
| **File Upload** | File type hợp lệ/không hợp lệ · Max size · File rỗng (0 KB) · Tên file có ký tự đặc biệt · Multiple files (nếu cho phép) · Kéo thả vs nút chọn |
| **Password** | Min/Max length · Yêu cầu ký tự đặc biệt · Yêu cầu chữ hoa/thường · Yêu cầu số · Copy-paste bị chặn? · Hiện/ẩn password · Confirm password khớp/không khớp |
| **Textarea** | Max length · Line breaks · HTML tags · Resize (nếu UI cho phép) · Character counter (nếu có) |

> **Nguyên tắc:** Mỗi trường có đặc tính riêng → validation riêng. Agent PHẢI phân tích từng field trước khi sinh TCs, không được dùng chung 1 bộ validation cho tất cả fields.

---

## Bảng Field-Level Visual States Validation

Sau khi sinh logic/validate TCs cho mỗi field, agent PHẢI sinh thêm visual TCs theo trạng thái hiển thị — đặt **TRƯỚC** logic TCs của cùng field:

| Loại State | Visual cần test |
|---|---|
| **Normal (default)** | Placeholder text đúng · Font/color đúng · Border/background đúng · Label đúng · Required (*) có/không |
| **Focus** | Border/outline highlight khi click vào field · Cursor đúng loại |
| **Filled/Valid** | Text hiển thị đúng · Không bị cắt (truncate) · Color đúng |
| **Error** | Border đỏ · Error message hiển thị đúng vị trí (dưới field) · Icon lỗi (nếu có) |
| **Disabled** | Màu grayed out · Cursor not-allowed · Không tương tác được |
| **Loading** | Spinner/skeleton hiển thị (nếu áp dụng) · Field disabled trong khi load |

> **Tất cả 6 states đều bắt buộc** — sinh TC cho từng state, không bỏ qua state nào dù field đơn giản.

**Screen level (1 TC per Screen):**
- TC "Verify UI tổng thể": layout đúng, spacing đúng, không bị vỡ giao diện — đặt **ĐẦU** bảng TC

> **Nguyên tắc:** Nếu có design input (Figma link / screenshot / PDF): Expected Result của Visual TC = "UI hiển thị đúng theo [tên frame/screen] trong design" — đối với Figma, đính kèm screenshot frame làm reference. Nếu không có design: expected result là "thống nhất với design [tên component]".

---

## Quy tắc Test Data

```
❌ Sai: "Nhập mã số hợp lệ"
✅ Đúng: "Nhập mã: KH-2026-0012"

❌ Sai: "Nhập email hợp lệ"
✅ Đúng: "Nhập email: test_khachhang_01@domain.com"

❌ Sai: "Nhập giá trị vượt giới hạn"
✅ Đúng: "Nhập 256 ký tự vào trường Name (max: 255)"
```

---

## Output Format

```
| ID | Function Name | Category | Risk Level | Traceability ID | Test Scenario | Precondition | Steps | Expected Results | Test Data | Priority |
```

- **ID:** format `[MODULE]-[SỐ]` (VD: `ORD-001`)
- **Function Name:** Sub-module/Component từ `plan-tcs.md` (VD: "Email field", "Submit button"). Nếu TC ở mức flow (không gắn 1 component cụ thể), dùng tên flow (VD "Login Flow").
- **Category:** cấp con dưới Function Name — "UI"/"Validate"/"Behavior"/"Logic" (component-level) hoặc "Happy Path"/"Negative"/"Security" (flow-level).
- **Traceability ID:** ID nguồn gốc TC trace ngược tới — AC tương ứng từ `analysis.md` (VD: `AC-05`), hoặc Q&A ID nếu từ ambiguity (VD: `AMB-01`), hoặc `N/A` nếu không có nguồn rõ ràng. Tên cột dùng chung cho mọi loại ID team quy ước (REQ ID, AC ID, Q&A ID, hoặc ID khác theo bảng quy ước riêng của team) — không giới hạn chỉ AC.
- **Test Scenario:** bắt đầu bằng "Check..." — xem "Rule ngôn ngữ Test Scenario" ở Section 4. Prefix `[UI Visual]` cho visual TCs.
- **Steps / Expected Results:** đánh số, dùng `<br>` xuống dòng trong cell — **KHÔNG** dùng `|`, `/`, hay newline thô.
- **Priority:** Critical / High / Medium / Low

Khi export ra `.xlsx` qua `/export-xlsx`: **Sheet name = tên Screen** (heading `##` trong `test-cases.md`, lấy theo tên Screen trong `plan-tcs.md`).

---

## Integration Testing Patterns

Dùng khi cần test data di chuyển giữa các modules — áp thủ công vào `/gen-tcs` cho các Component/Screen liên quan đến integration point (không có command riêng).

### 4 loại TC cần cover per integration point

| Loại | Khi nào áp dụng | Test gì |
|------|----------------|---------|
| **Data pass-through** | Luôn áp dụng | Module A tạo/sửa data → Module B hiển thị đúng, không mất field, không bị transform ngoài ý muốn |
| **Data transformation** | Chỉ khi có transformation | Kết quả sau khi transform đúng công thức (VD: amount × tax rate, format date, convert currency) |
| **Invalid/missing data at boundary** | Luôn áp dụng | Module A gửi data sai/thiếu required field → Module B hiển thị error đúng, không crash, không lưu data bẩn |
| **Data consistency sau lỗi** | Khi luồng có ≥2 bước ghi dữ liệu | Nếu bước giữa luồng fail → data ở bước trước có bị dirty/orphan không; rollback có hoạt động không |

### Độ sâu theo risk level

| Risk | Loại TC bắt buộc |
|------|-----------------|
| **High** | Tất cả 4 loại + edge cases (null, empty string, boundary values) |
| **Medium** | Data pass-through + Invalid/missing data |
| **Low** | Data pass-through only |

### Bảng TC format cho integration TCs

```
| ID | Integration Point | TC Type | Risk | Precondition | Steps | Expected Result | Test Data | Priority |
```

- **ID:** format `INT_[FEATURE]_[SỐ]` (VD: `INT_ORDER_001`)
- **Integration Point:** `[Module A] → [Module B]` (VD: `Tạo đơn hàng → Lịch sử đơn hàng`)
- **TC Type:** `pass-through` / `transformation` / `invalid-boundary` / `consistency`

---

## Anti-Patterns (NGHIÊM CẤM)

- ❌ Sinh test data chung chung / placeholder
- ❌ Chỉ có Happy Path, thiếu Negative/Boundary cases
- ❌ Test Steps mơ hồ, không ghi rõ dữ liệu nhập
- ❌ Gộp validation nhiều trường vào 1 test case → mỗi trường phải có TC validation riêng
- ❌ Dùng chung 1 bộ validation cho tất cả fields (Email ≠ Phone ≠ Date ≠ Text)
- ❌ Bỏ qua security validation (XSS, SQL injection) cho text/textarea fields
- ❌ Không liệt kê danh sách fields trước khi sinh validation TCs
- ❌ Bỏ qua visual TCs — mỗi field phải có TC cho các state: Normal, Error, Disabled (nếu applicable)
- ❌ Expected result visual chung chung không rõ state nào đang test
- ❌ Không hỏi platform trước khi sinh TCs
- ❌ Bỏ qua `testing_dimensions` khi đã biết platform
- ❌ Rút gọn hoặc bỏ sót test case khi mapping sang bảng
- ❌ Sinh tất cả test cases 1 lần cho hệ thống lớn (phải chia theo Screen)
- ❌ **Viết Test Scenario dạng ký hiệu rút gọn** (mũi tên, gạch chéo nén ý, dấu hai chấm nén nhiều ý) thay vì câu tự nhiên hoàn chỉnh
- ❌ **Chạy `/gen-tcs` khi chưa có `plan-tcs.md`** cho module đó
- ❌ **Đoán Component Type qua keyword AC text** khi `plan-tcs.md` đã có sẵn Component Type — phải tra trực tiếp
