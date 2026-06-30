---
name: bug_reporter
description: Skill chuẩn hóa bug reports — phân loại bug type/severity/priority, sinh steps to reproduce rõ ràng, format sẵn sàng paste vào Backlog.
---

# Bug Reporter

## Description

Skill này giúp QC viết bug reports **chuẩn, đủ thông tin, không mơ hồ** — đảm bảo DEV hiểu được ngay mà không cần hỏi lại.

---

## When to Use

- Sinh bug report từ mô tả lỗi của QC
- Chuẩn hóa bug report đang viết dở
- Phân loại severity/priority cho bug
- **Không dùng** skill này để sinh test cases → dùng `rbt_manual_testing`

---

## Bug Report Fields (Bắt buộc)

| Field | Mô tả |
|-------|-------|
| **Bug ID** | Format: `BUG-[MODULE]-[SỐ]` (VD: `BUG-LOGIN-001`) |
| **Tiêu đề** | Ngắn gọn, rõ impact: `[Màn hình] [Hành động] → [Kết quả sai]` |
| **Bug Type** | Xem bảng phân loại Bug Type bên dưới |
| **Environment** | OS, Browser/App version, URL/Build, Test account |
| **Severity** | Xem bảng phân loại bên dưới |
| **Priority** | Xem bảng phân loại bên dưới |
| **Steps to Reproduce** | Đánh số, đủ precondition, test data cụ thể |
| **Expected Result** | Kết quả đúng theo spec/requirements |
| **Actual Result** | Kết quả thực tế quan sát được |
| **Reproducibility** | Always / Intermittent (x/y lần) / Only once |
| **Evidence** | Screenshot, video, console log (nếu có) |
| **Root Cause Hint** | Gợi ý nơi có thể xảy ra lỗi (optional) |

---

## Phân Loại Bug Type

| # | Bug Type | Tiêu chí phân loại |
|---|----------|-------------------|
| 1 | **UI Bug** | Sai font, màu sắc, layout, căn lề, padding/margin, responsive không đúng, không khớp Figma/Spec. Không ảnh hưởng logic |
| 2 | **Functional Bug** | Chức năng không hoạt động đúng yêu cầu, sai logic nghiệp vụ, sai flow, lỗi lưu/cập nhật/hiển thị data |
| 3 | **Validation Bug** | Sai format input, sai required/optional, thiếu hoặc sai error message, sai min/max length, chấp nhận data không hợp lệ |
| 4 | **Performance Bug** | Phản hồi chậm, tốn thời gian tải, bị treo khi thao tác — thường kèm ngưỡng cụ thể (VD: >3s, >10s) |
| 5 | **Compatibility Bug** | Giao diện hoặc chức năng không đúng trên một số browser, OS, hoặc thiết bị cụ thể |
| 6 | **Security Bug** | Lỗ hổng cho phép truy cập trái phép, thay đổi data không qua xác thực, lộ thông tin nhạy cảm |
| 7 | **REQ Bug** | Thiếu mô tả validation, thiếu màn hình, thiếu logic/công thức/trạng thái trong requirement — lỗi thuộc về spec, không phải code |
| 8 | **Design Bug** | Design chưa đồng bộ (cùng template nhưng nhiều nơi khác nhau), thiếu states (hover, loading, empty, error, disabled), thiếu flow/animation |

> **Phân biệt UI Bug vs Design Bug:** UI Bug = implement sai so với design đã có. Design Bug = design thiếu/sai từ đầu, chưa có gì để implement theo.

> **Phân biệt Functional Bug vs Validation Bug:** Validation Bug = lỗi tại lớp kiểm tra đầu vào (input field). Functional Bug = lỗi ở logic xử lý sau khi data đã pass validation.

---

## Phân Loại Severity

| Severity | Tiêu chí | Ví dụ |
|----------|----------|-------|
| **Critical** | Crash app, mất data, không thể tiếp tục sử dụng | App crash khi submit form, payment bị trừ tiền 2 lần |
| **Major** | Tính năng chính không hoạt động, không có workaround | Không thể đăng nhập, không lưu được dữ liệu |
| **Minor** | Tính năng bị ảnh hưởng nhưng có workaround | Dropdown không sort đúng, filter sai một case |
| **Trivial** | Lỗi UI/UX, không ảnh hưởng logic | Typo, màu sắc sai, icon lệch |

---

## Phân Loại Priority

| Priority | Tiêu chí |
|----------|----------|
| **P1 (Urgent)** | Blocker — cần fix trước khi release |
| **P2 (High)** | Ảnh hưởng user thường xuyên, cần fix trong sprint này |
| **P3 (Medium)** | Cần fix nhưng có thể defer sang sprint sau |
| **P4 (Low)** | Nice-to-have, cosmetic, không ảnh hưởng nghiệp vụ |

> **Lưu ý:** Severity và Priority độc lập. Trivial bug có thể là P1 (VD: typo trên nút "Xác nhận thanh toán").

---

## Steps to Reproduce — Quy tắc viết

```
❌ Sai:
1. Mở trang
2. Nhập thông tin
3. Nhấn Submit → lỗi

✅ Đúng:
Precondition: Đăng nhập tài khoản admin@test.com, đang ở trang /users/create

1. Điền field "Email" với giá trị: test@gmail.com
2. Điền field "Tên" với giá trị: Nguyễn Văn A
3. Để trống field "Số điện thoại"
4. Nhấn nút "Tạo tài khoản"
```

**Nguyên tắc:**
- Precondition phải đủ để DEV reproduce ngay lần đầu
- Test data phải cụ thể — không dùng "nhập email hợp lệ"
- Mỗi step là 1 action duy nhất
- Step cuối là action trigger lỗi

---

## Output Format

```markdown
## [BUG-MODULE-001] Tiêu đề ngắn gọn

| Field | Nội dung |
|-------|---------|
| **Bug Type** | Functional Bug |
| **Severity** | Major |
| **Priority** | P2 |
| **Environment** | Chrome 124, macOS 14, https://staging.app.com, account: test@admin.com |
| **Reproducibility** | Always |

### Steps to Reproduce
**Precondition:** [trạng thái ban đầu]

1. [action 1]
2. [action 2]
3. [action trigger lỗi]

### Expected Result
[Kết quả đúng theo spec]

### Actual Result
[Kết quả thực tế]

### Evidence
[Screenshot / Video / Console log]
```

---

## Anti-Patterns

- ❌ Steps mơ hồ ("nhập thông tin", "thực hiện thao tác")
- ❌ Không có precondition → DEV không reproduce được
- ❌ Gộp nhiều bugs vào 1 report
- ❌ Expected Result copy nguyên văn spec mà không diễn giải
- ❌ Actual Result chỉ ghi "lỗi" — phải mô tả chính xác điều gì xảy ra
- ❌ Nhầm lẫn Severity với Priority
