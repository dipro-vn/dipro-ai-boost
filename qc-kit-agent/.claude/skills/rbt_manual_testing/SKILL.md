---
name: RBT Manual Testing
description: Skill sinh manual test cases theo quy trình AI-RBT — pipeline 3 bước per module (analyze-req → gen-tcs TS → gen-tcs TCs), context-roleplay chạy 1 lần cho project. Dùng kết hợp với requirements_analyzer và testing_dimensions.
---

# RBT Manual Testing

## Description

Skill hỗ trợ sinh manual test cases chất lượng cao theo quy trình Risk-Based Testing (RBT). Được tổ chức thành **5 sections**, tương ứng với pipeline 3 bước per module + 1 bước setup project.

**Pipeline:**
```
/context-roleplay  → /analyze-req  → /decompose-modules  → /gen-tcs
```

**Nguyên tắc cốt lõi:**
- **Human Strategy:** Con người xác định chiến lược, mức độ rủi ro và tiêu chuẩn
- **AI Execution:** AI thực hiện phân tích, viết TCs và rà soát lỗ hổng
- **Human Verification:** Con người kiểm tra lại kết quả trước khi chốt

---

## When to Use

Sử dụng skill này khi:
- Sinh manual test cases từ requirements / user stories
- Phân tích requirements để phát hiện ambiguity và verify AC
- Phân rã hệ thống thành modules / features
- Xây dựng test scenarios có traceability với AC
- Áp dụng Risk-Based Testing (đánh giá rủi ro cho test cases)
- Chuẩn hóa test cases sang bảng Markdown (Backlog/Excel format)

**KHÔNG** sử dụng skill này khi:
- Chỉ cần sinh test data riêng lẻ → dùng `/gen-test-data`
- Cần chuẩn hóa bug report → dùng `/gen-bug-report`

---

# Section 1: Context & Role-play

**Command tương ứng:** `/context-roleplay`

**Mục đích:** Thiết lập vai trò Senior QA Engineer và nạp bối cảnh dự án trước khi phân tích.

**Agent phải:**
1. Thu thập thông tin project (chạy 1 lần duy nhất):
   - Tên project + mô tả hệ thống
   - Actors và vai trò
   - **Platform: Web / Mobile / Desktop / Nhiều platform?**
   - Business rules toàn cục (áp dụng ở mọi module)
2. Filter trước khi ghi — áp rule *"Đây là rule của cả project hay của riêng module này?"* Chỉ ghi thông tin là rule của cả project
3. Lưu ra `context.md` ở **root folder** — được CLAUDE.md auto-load vào mọi session

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

> Giữ ngắn — dưới 20 dòng. Thông tin đặc thù module để trong `## Summary` của `analysis.md`.

---

# Section 2: Requirement Analysis

**Command tương ứng:** `/analyze-req`

**Mục đích:** Phân tích requirements để phát hiện điểm mờ (Q&A) và mapping REQ → AC. Hai việc chạy song song vì Q&A làm AC chất lượng hơn. Output là bộ AC đủ tốt để triển khai Test Scenarios.

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

3. Tổng hợp vào `analysis.md` — 3 sections: Summary, Q&A, AC

**Output file:** `testing/[module]/analysis.md`

```markdown
# Requirements Analysis: [Module Name]

## Summary
[Tên tính năng, mục đích nghiệp vụ, actors, luồng chính, scope, dependencies]

## Q&A — Ambiguities

| ID | Reference | Screen | Question (VN) + Assumption/Đề xuất | Impact | Severity | Status |
|----|-----------|--------|--------------------------------------|--------|----------|--------|
| AMB-01 | REQ-XX | [tên màn hình] | ... Đề xuất: ... | ... | High / Medium / Low | TBD |

> **TBD** = chưa được PM/BA confirm | **Answered** = đã có câu trả lời (dùng `/sync-qa` để update từ file Q&A công ty)

---

## Acceptance Criteria

| REQ ID | AC ID | AC Content | Status |
|--------|-------|------------|--------|
| REQ-01 | AC-01 | ... | Confirmed / Assumed / TBD |

## History
- v1 ([ngày]): /analyze-req — khởi tạo
```

> AC **Status TBD** = AC phụ thuộc vào Q&A chưa được trả lời — `/gen-tcs` sẽ cảnh báo khi gặp AC này.

---

# Section 3: Module Decomposition

**Command tương ứng:** `/decompose-modules`

**Mục đích:** Phân rã tính năng thành các Module / Sub-module nhỏ, xác định risk level để định hướng độ sâu test.

**Agent phải:**
1. Đọc `analysis.md` (Summary section có đủ module context)
2. Phân rã theo 1 trong 2 cách:
   - **Theo UI:** Header, Data Table, Form popup, Sidebar...
   - **Theo luồng:** Flow tạo mới, Flow chỉnh sửa, Flow xóa...
3. Mô tả ngắn gọn chức năng từng Module
4. Đánh giá Risk Level per sub-module:
   - **High:** Nghiệp vụ quan trọng, liên quan tiền/bảo mật/phân quyền
   - **Medium:** Luồng chính nhưng không critical
   - **Low:** UI validation, happy path đơn giản
5. Chỉ ra Dependencies giữa các Module

**Output file:** `testing/[module]/modules.md`

```markdown
# Module Decomposition: [Module Name]

## Module Hierarchy

### [Module A]
- **Mô tả:** ...
- **Risk:** High / Medium / Low
- **Sub-modules:**
  - [Sub-module A1] — Risk: High — [mô tả ngắn]
  - [Sub-module A2] — Risk: Medium — [mô tả ngắn]

### [Module B]
...

## Dependencies
- [Module A] phụ thuộc vào [Module B] vì ...
```

---

# Section 4: Test Scenario Generation

**Command tương ứng:** `/gen-tcs` (Mode A — sinh TS trước để review)

**Mục đích:** Sinh Test Scenarios có traceability với AC, phân loại theo risk level từ modules.md.

**Agent phải:**
1. Đọc `analysis.md` + `modules.md`. Nếu không có (flexible entry), suy luận từ requirements doc trực tiếp.
2. Xác định platform từ `analysis.md` Summary → nếu trống, dùng Platform trong project `context.md` đã auto-load → đọc `.claude/skills/testing_dimensions/SKILL.md` section tương ứng
3. Sinh Test Scenarios bao phủ:
   - Happy Path (luồng chính)
   - Alternate Paths (luồng rẽ nhánh)
   - Exception Paths (lỗi, timeout, mất kết nối...)
   - Security / phân quyền
   - UI Validation
   - Business Logic
   - Data Integrity
   - Platform-specific dimensions (từ testing_dimensions)
4. Đảm bảo mỗi AC có ít nhất 1 Scenario cover — bổ sung nếu thiếu (Gap Analysis)

**Output file:** `testing/[module]/test-scenarios.md`

```markdown
# Test Scenarios: [Module Name]

| TS ID | AC ID | Scenario Description | Risk Level | Category |
|-------|-------|----------------------|------------|----------|
| TS-001 | AC-01 | Check [happy path...] | High | Business Logic |
| TS-002 | AC-01 | Check [negative...] | Medium | Validation |
```

---

# Section 5: Test Case Generation

**Command tương ứng:** `/gen-tcs`

**Mục đích:** Sinh test cases chi tiết từ test-scenarios.md, áp dụng Field-Level Validation, Visual States, và kỹ thuật thiết kế test case.

**Agent phải:**
1. Đọc `test-scenarios.md`. Platform đọc từ `analysis.md` Summary hoặc project `context.md` đã auto-load.
2. Với mỗi scenario, sinh TC đầy đủ fields (xem Output Format)
3. **Validation chuyên biệt từng trường (Field-Level Validation):**
   - Liệt kê **tất cả input fields** trên form/UI đang test
   - Sinh validation TCs **riêng cho TỪNG trường** theo đặc tính riêng
   - Tham chiếu **Bảng Field-Level Validation** ở Reference Library
   - **KHÔNG** gộp validation nhiều trường vào 1 TC
4. **Sinh UI Visual TCs** theo Bảng Field-Level Visual States Validation:
   - 1 TC screen level "Verify UI tổng thể" — đặt **ĐẦU** bảng TC
   - Visual state TCs (6 states: Normal, Focus, Filled, Error, Disabled, Loading) per field — đặt **TRƯỚC** logic TCs của cùng field
5. **Nhận diện và áp dụng Complex Logic Patterns** (xem sub-section bên dưới) — làm TRƯỚC khi sinh TC
6. Áp dụng kỹ thuật thiết kế test case phù hợp:
   - **Equivalence Partitioning (EP)**
   - **Boundary Value Analysis (BVA)**
   - **Decision Table** (khi có ≥2 điều kiện kết hợp)
   - **State Transition** (khi có workflow trạng thái)
7. **Áp dụng Platform Dimensions** từ `testing_dimensions/SKILL.md`
8. Nếu scenarios quá nhiều → sinh từng Module một, hỏi user để tiếp tục

**Output file:** `testing/[module]/test-cases.md`

---

## Complex Logic Patterns

Agent **tự động nhận diện** từ nội dung AC/TS và áp dụng pattern phù hợp **trước khi sinh TC**. Có thể áp nhiều pattern trong 1 lần nếu AC phức tạp.

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
3. Show inline trước khi sinh TC

```
Ví dụ — Workflow phê duyệt:

[Draft] --submit--> [Pending]
[Pending] --approve--> [Approved]
[Pending] --reject--> [Rejected]
[Approved] --cancel--> [Cancelled]

Invalid transitions:
[Draft] --approve--> ❌
[Approved] --submit--> ❌
```

**Sau đó:** test mỗi transition hợp lệ (1 TC) + mỗi invalid transition quan trọng (1 TC).

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

**Screen level (1 TC per module):**
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
| ID | Function Name | Category | Risk Level | AC ID | TS ID | Test Scenario | Precondition | Steps | Expected Results | Test Data | Priority |
```

- **ID:** format `[MODULE]-[SỐ]` (VD: `ORD-001`)
- **AC ID:** AC tương ứng từ `analysis.md` (VD: `AC-05`). Với TCs từ implicit requirement hoặc ambiguity: dùng Q&A ID (VD: `AMB-01`) hoặc để `N/A` nếu không có nguồn rõ ràng.
- **TS ID:** TS tương ứng từ `test-scenarios.md` (VD: `TS-001`). Điền `N/A` nếu dùng Mode B (không có TS artifact).
- **Test Scenario:** bắt đầu bằng "Check..." cho functional TCs; dùng prefix `[UI Visual]` cho visual TCs
- **Steps / Expected Results:** đánh số, dùng `<br>` xuống dòng trong cell — **KHÔNG** dùng `|`, `/`, hay newline thô
- **Priority:** Critical / High / Medium / Low

---

## Integration Testing Patterns

Dùng khi cần test data di chuyển giữa các modules. Tham chiếu bởi `/gen-inter-tcs`.

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
- ❌ Sinh tất cả test cases 1 lần cho hệ thống lớn (phải chia module)
