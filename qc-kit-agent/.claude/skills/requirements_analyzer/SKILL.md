---
name: requirements_analyzer
description: Skill phân tích requirement document có sẵn (Google Drive, Docs, Figma, .md, .doc, Backlog ticket) — hướng dẫn cách đọc, extract AC, và phát hiện ambiguities.
---

# Requirements Analyzer

## Mục tiêu

Hướng dẫn AI cách đọc và phân tích **requirement document có sẵn** (Google Drive, Docs, Figma, .md, .doc, Backlog ticket) — không phải tự sinh requirements từ UI.

---

## Nguyên tắc cốt lõi

- **Đọc kỹ trước khi phân tích** — đọc toàn bộ document, kể cả comments và attachments
- **Không tự đoán business logic** — những gì không được ghi rõ trong document → đưa vào Ambiguities
- **AC do PM tạo** — QC đọc, confirm và map AC vào requirements, không tự sinh AC mới
- **Ưu tiên độ chính xác** — thà hỏi clarify hơn là giả định sai

---

## Kỹ thuật phân tích

### 1. Đọc hiểu scope

- Xác định rõ: tính năng này **thêm mới**, **chỉnh sửa**, hay **xóa** behavior hiện tại?
- Các module/page nào bị ảnh hưởng — trực tiếp và gián tiếp?
- Ai là actor? (user thường, admin, hệ thống tự động?)

### 2. Map AC vào Requirements

Với mỗi REQ trong document:
- Tìm AC tương ứng mà PM đã viết
- Kiểm tra AC đã cover: happy path, negative, edge cases chưa?
- REQ nào thiếu AC → đánh dấu là Ambiguity, không tự bổ sung

### 3. Phát hiện Ambiguities — dấu hiệu cần tìm

| Dấu hiệu | Ví dụ |
|----------|-------|
| Từ khóa mơ hồ | "where applicable", "as needed", "tương tự như", "v.v." |
| Validation thiếu | Không ghi min/max, format, required/optional |
| Behavior edge case chưa mô tả | Mất mạng, dữ liệu trống, concurrent access |
| Inconsistency với mockup | Tên field, format, layout khác nhau |
| Threshold chưa định nghĩa | "tiếp cận deadline" — bao nhiêu ngày? |
| Conflict với requirement cũ | REQ mới mâu thuẫn với behavior hiện tại |

### 4. Phân biệt Business Rules vs UI Rules

- **Business rule:** "Tài khoản bị khóa sau 5 lần sai" → test kỹ, ảnh hưởng nghiệp vụ
- **UI rule:** "Nút Submit disabled khi form chưa đủ dữ liệu" → test validation behavior

### 5. Đọc dependencies

- Tài liệu phụ thuộc → đọc và tóm tắt
- AC từ tài liệu phụ thuộc có thể ảnh hưởng scope của tài liệu chính
- Ghi rõ rule nào đến từ tài liệu nào

---

## Design Integration

*(Áp dụng khi user cung cấp design input: Figma link, screenshot, PDF export design...)*

### Theo dạng input

| Input | Cách đọc |
|-------|---------|
| Screenshot / image | Đọc trực tiếp — cross-check ngay với spec |
| PDF export | Đọc từng trang — cross-check theo từng screen |
| Figma link | Dùng Figma MCP tools — theo quy trình 2 phase bên dưới |

---

### Figma — Quy trình 2 Phase

> Áp dụng khi Figma file có nhiều pages hoặc nhiều frames. Mục tiêu: xác định đúng scope trước khi đọc sâu — tránh bỏ sót screen và tránh đọc nhầm vào archive/draft.

#### Phase 1 — Scope Mapping (có checkpoint)

1. Gọi `get_pages` → list tất cả pages trong file
2. Hỏi user:
   > Figma file có [N] pages: [danh sách tên]. Pages nào liên quan đến feature đang phân tích? *(Bỏ qua Archive, Draft, hoặc pages không liên quan)*
3. Chờ user confirm pages
4. Với các pages được confirm: gọi `scan_nodes_by_types` với type `FRAME` → list top-level frames
5. Hỏi user:
   > Tôi thấy [N] frames: [danh sách tên]. Frames nào là screens của feature này?
6. Chờ user confirm frames → đây là **scope chính thức** cho Phase 2

#### Phase 2 — Deep Read (chỉ trong scope đã confirm)

Với mỗi frame được confirm:

1. Gọi `get_node` để đọc nội dung frame
2. Tìm `COMPONENT_SET` nodes — đây là nơi Figma lưu state variants:
   - Tìm nodes có tên chứa keyword: `State=`, `Status=`, `Type=`, `Variant=`, `Mode=`
   - Ví dụ phổ biến: `State=Error`, `State=Loading`, `State=Disabled`, `Status=Active`
3. Gọi `get_annotations` để đọc annotations và developer notes
4. Cross-check với spec theo bảng bên dưới

---

### Cross-check Checklist

| Thứ cần kiểm tra | Cách làm | Nếu không khớp |
|---|---|---|
| **Screen inventory** | Frames đã confirm vs sections trong spec | Frame có trong design nhưng không có trong spec → thêm AMB item |
| **UI states** | COMPONENT_SET variants vs states được mô tả trong spec | State có trong design (`State=Error`) nhưng spec không mô tả behavior → thêm AMB item |
| **Field names** | Label text trong frame vs tên field trong spec | Naming khác nhau → thêm AMB item, KHÔNG tự chọn cái nào đúng |
| **Business rules ẩn** | Annotations / developer notes trong frame | Annotation chứa rule chưa có trong spec → ghi chú vào AC context |

> Figma Findings chỉ bổ sung thêm AMB items — không thay thế hay override phân tích từ spec text.

---

## Những gì KHÔNG làm

- ❌ Tự sinh AC khi PM chưa viết → đưa vào Ambiguities
- ❌ Tự đoán business logic khi document không nói rõ
- ❌ Bỏ qua comments hoặc notes đính kèm trong document
- ❌ Giả định inconsistency giữa document và mockup là lỗi typo — ghi rõ để confirm
