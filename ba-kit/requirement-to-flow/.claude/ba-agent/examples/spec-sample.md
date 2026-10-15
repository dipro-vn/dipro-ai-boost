# Ví dụ minh họa — SPEC (trích) + AC + Danh sách User Story

> ⚠️ **VÍ DỤ MINH HỌA — KHÔNG sao chép nội dung vào feature thật.**
> Tên màn hình, con số, message, quy tắc dưới đây là **giả định cho mục đích minh họa**. Feature thật phải lấy từ nguồn người dùng đưa vào (`RELIABILITY.md`).
> Dùng để học **hình dạng** của output: cách trace, cách viết AC, cách dùng `E-nnn`, `Examples`, `PENDING-OQ`, và cách ghi Epic → User Story.
>
> Domain trung tính: *Gửi và theo dõi đơn nghỉ phép*. Mọi dữ liệu theo bộ mẫu `DATA-PRIVACY.md` §4.
> Liên quan: `ac-standard.md` · `user-stories.md` · `story-splitting.md` · `spec-template.md`.

---

## A. Nguồn giả định (FR Register — mô phỏng)

| FR No. | Chức năng nguồn | Screen Code phủ | Ghi chú |
|---|---|---|---|
| #12 | Tạo đơn nghỉ phép | AX_LEAV_002 | |
| #13 | Đính kèm minh chứng (tuỳ chọn) | AX_LEAV_002 | |
| #14 | Xem danh sách đơn đã gửi | AX_LEAV_001 | |
| #15 | Giới hạn số ngày nghỉ mỗi năm | AX_LEAV_002 | Chưa có số cụ thể → OQ-01 |
| #16 | Nhắc quản lý khi đơn chưa được duyệt | — | SYSTEM — job nhắc việc, không có màn |

```
FR COVERAGE — nguồn: <ví dụ> (5 dòng chức năng)
  Đã phủ      : 5/5
  SYSTEM-only : #16
  THIẾU       : []
```

## B. Trích `## Source Register`

| ID | Statement | Classification | Evidence | Confidence | Used in flow? |
|---|---|---|---|---|---|
| RQ-001 | Nhân viên gửi đơn gồm: loại nghỉ, ngày bắt đầu, ngày kết thúc, lý do | FACT | nguồn mục #12 | High | Yes — Flow 1 |
| RQ-002 | Ngày kết thúc không được trước ngày bắt đầu | FACT | nguồn mục #12 | High | Yes — Flow 1 |
| RQ-003 | Đơn có thể nghỉ đúng 1 ngày | FACT | user turn 4 | High | Yes — Flow 1 |
| RQ-004 | Số ngày nghỉ tối đa mỗi năm | UNKNOWN | nguồn chỉ nói "có giới hạn", không nêu số | — | No — OQ-01 |
| RQ-005 | Khoảng thời gian chờ trước khi nhắc quản lý | UNKNOWN | nguồn không nêu | — | No — OQ-02 |

## C. Trích `## Screens`

> **TỔNG: 5 màn hình** = **2 màn chính** + **3 màn lỗi/popup**.
>
> | Loại | Số lượng | Đếm vào tổng? |
> |---|---|---|
> | Màn hình chính | 2 | ✅ |
> | Toast / Modal / Popup / Banner / Full screen / Empty state | 3 | ✅ |
> | Inline error / Button disabled / Tooltip / Chặn UI | 4 | ❌ — chỉ là state |
> | **Tổng error display định nghĩa** | **7** | |

| FR No. | Screen Code | Screen | Actor | App | Screen Type | Transition To |
|---|---|---|---|---|---|---|
| #14 | AX_LEAV_001 | Danh sách đơn nghỉ | Nhân viên | EP-01 | List | `[Nhấn "Tạo đơn"] → AX_LEAV_002` |
| #12,13,15 | AX_LEAV_002 | Tạo đơn nghỉ | Nhân viên | EP-01 | Form | `[Gửi thành công] → AX_LEAV_001` |

> Chức năng #16 là job hệ thống, không có màn → xem System node ở Output 1/2.

## D. Trích `## Screen Details` — chỉ phần Non-Happy (nơi **duy nhất** chứa message)

### AX_LEAV_001 — Danh sách đơn nghỉ

**Non-Happy Case:**
| ID | Nhóm | Trigger | Hiển thị | Message |
|---|---|---|---|---|
| E-001 | 5 Empty | Nhân viên chưa gửi đơn nào | Empty state | "Bạn chưa gửi đơn nghỉ nào" |
| E-002 | 3 Network | Mất mạng khi tải danh sách | Banner | "Không tải được danh sách. Kéo để thử lại." |

### AX_LEAV_002 — Tạo đơn nghỉ

**Non-Happy Case:**
| ID | Nhóm | Trigger | Hiển thị | Message |
|---|---|---|---|---|
| E-003 | 1 Validation | Bỏ trống Loại nghỉ | Inline error | "Vui lòng chọn loại nghỉ" |
| E-004 | 1 Validation | Bỏ trống Ngày bắt đầu | Inline error | "Vui lòng chọn ngày bắt đầu" |
| E-005 | 1 Validation | Bỏ trống Ngày kết thúc | Inline error | "Vui lòng chọn ngày kết thúc" |
| E-006 | 7 Business rule | Ngày kết thúc trước ngày bắt đầu | Inline error | "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu" |
| E-007 | 3 Network | Mất mạng khi nhấn Gửi | Banner | "Không gửi được đơn. Kiểm tra kết nối và thử lại." |
| — | 7 Business rule | Số ngày nghỉ vượt hạn mức năm | UNKNOWN | UNKNOWN — OQ-01 |

> Cột `ID` là **nguồn duy nhất** của `E-nnn`: đánh liên tục toàn SPEC, cố định, không đánh lại số. Dòng `UNKNOWN` **chưa** có ID (ghi `—`); khi OQ-01 được trả lời sẽ nhận `E-008` (số kế tiếp, không chèn vào giữa).

---

## E. `## Acceptance Criteria` (theo `ac-standard.md`)

> Tổng: 10 AC · Happy 2 · Edge 2 · Negative 4 · PENDING-OQ 2

### AC-01 — Gửi đơn nghỉ thành công `[Happy]`
- **Trace:** FR #12 · AX_LEAV_002 · Flow 1
- **Given** nhân viên đã đăng nhập và đang ở màn tạo đơn
- **And** đã chọn Loại nghỉ, Ngày bắt đầu, Ngày kết thúc (sau hoặc bằng ngày bắt đầu) và nhập Lý do
- **When** nhân viên nhấn "Gửi"
- **Then** hệ thống lưu đơn với trạng thái `Chờ duyệt`
- **And** chuyển tới `AX_LEAV_001` và đơn mới xuất hiện đầu danh sách

### AC-02 — Đơn nghỉ đúng 1 ngày được chấp nhận `[Edge]`
- **Trace:** FR #12 · AX_LEAV_002 · Flow 1
- **Given** nhân viên chọn Ngày bắt đầu và Ngày kết thúc là cùng một ngày
- **When** nhân viên nhấn "Gửi"
- **Then** hệ thống lưu đơn, số ngày nghỉ của đơn là 1

### AC-03 — Từ chối gửi khi thiếu trường bắt buộc `[Negative]`
- **Trace:** FR #12 · AX_LEAV_002 · Flow 1
- **Given** nhân viên đang ở màn tạo đơn
- **When** nhân viên nhấn "Gửi" khi bỏ trống `<trường>`
- **Then** hệ thống không lưu đơn và hiển thị `<lỗi>` ngay tại trường đó

| trường | lỗi |
|---|---|
| Loại nghỉ | E-003 |
| Ngày bắt đầu | E-004 |
| Ngày kết thúc | E-005 |

### AC-04 — Từ chối khi ngày kết thúc trước ngày bắt đầu `[Negative]`
- **Trace:** FR #12 · AX_LEAV_002 · Flow 1
- **Given** nhân viên chọn Ngày kết thúc sớm hơn Ngày bắt đầu
- **When** nhân viên nhấn "Gửi"
- **Then** hệ thống không lưu đơn và hiển thị `E-006`

### AC-05 — Mất mạng khi gửi đơn `[Negative]`
- **Trace:** FR #12 · AX_LEAV_002 · Flow 1
- **Given** form đã điền hợp lệ
- **When** nhân viên nhấn "Gửi" trong lúc không có kết nối
- **Then** hệ thống hiển thị `E-007`
- **And** dữ liệu đã nhập trên form vẫn được giữ, không có đơn nào được tạo

### AC-06 — Xem danh sách đơn đã gửi `[Happy]`
- **Trace:** FR #14 · AX_LEAV_001 · Flow 1
- **Given** nhân viên đã gửi ít nhất 1 đơn
- **When** nhân viên mở màn danh sách đơn nghỉ
- **Then** hệ thống hiển thị các đơn của chính nhân viên đó, mỗi đơn kèm trạng thái

### AC-07 — Danh sách rỗng `[Edge]`
- **Trace:** FR #14 · AX_LEAV_001 · Flow 1
- **Given** nhân viên chưa gửi đơn nào
- **When** nhân viên mở màn danh sách đơn nghỉ
- **Then** hệ thống hiển thị `E-001`

### AC-08 — Mất mạng khi tải danh sách `[Negative]`
- **Trace:** FR #14 · AX_LEAV_001 · Flow 1
- **Given** nhân viên mở màn danh sách khi không có kết nối
- **When** hệ thống không tải được dữ liệu
- **Then** hệ thống hiển thị `E-002`

### AC-09 — Giới hạn số ngày nghỉ mỗi năm `[Negative]`
- **PENDING-OQ-01** — chờ KH trả lời: "Mỗi nhân viên được nghỉ tối đa bao nhiêu ngày mỗi năm, theo từng loại nghỉ?"
- **Trace:** FR #15 · AX_LEAV_002 · Flow 1
- _Given/When/Then: chưa viết — UNKNOWN. Không suy diễn con số._

### AC-10 — Nhắc quản lý khi đơn chưa được duyệt `[Happy]`
- **PENDING-OQ-02** — chờ KH trả lời: "Sau bao lâu kể từ lúc gửi mà đơn chưa được duyệt thì hệ thống nhắc quản lý, và nhắc qua kênh nào?"
- **Trace:** FR #16 (SYSTEM) · Flow 1
- _Given/When/Then: chưa viết — UNKNOWN._

**Các điểm đáng chú ý của ví dụ này:**
- AC-03 gom 3 dòng Non-Happy cùng nhóm/cùng cách xử lý bằng **1 AC + Examples**, không viết 3 AC.
- Không AC nào chép message — chỉ `E-nnn`. Sửa wording chỉ ở `## Screen Details`.
- AC-09, AC-10 là **placeholder** vì nguồn không có số / không có quy tắc. Không bịa "tối đa 12 ngày", "sau 24 giờ".
- Dòng `Inline error` (E-003…E-006) chỉ là state, không phải màn hình riêng (đúng bảng thống kê ở §C).

---

## F. `USER-STORIES.md` (theo `user-stories.md`) — Epic → User Story

<!-- BEGIN-REGISTER -->
| Epic | US ID | Tiêu đề | As a | I want to | So that | FR No. | Screen Code | Flow | AC ref | INVEST | Spike | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EP-01 Gửi & theo dõi đơn nghỉ | US-LEAV-001 | Gửi đơn nghỉ phép | nhân viên đã đăng nhập | gửi đơn nghỉ với loại nghỉ và khoảng ngày | quản lý nhận được đơn để xử lý đúng hạn | #12,13 | AX_LEAV_002 | Flow 1 | AC-01,AC-02,AC-03,AC-04,AC-05 | I✅ N✅ V✅ E✅ S✅ T✅ | — | |
| EP-01 Gửi & theo dõi đơn nghỉ | US-LEAV-002 | Xem trạng thái đơn đã gửi | nhân viên đã đăng nhập | xem danh sách đơn của mình kèm trạng thái | biết đơn đã được duyệt hay chưa mà không phải hỏi quản lý | #14 | AX_LEAV_001 | Flow 1 | AC-06,AC-07,AC-08 | I✅ N✅ V✅ E✅ S✅ T✅ | — | |
| EP-02 Chính sách & nhắc việc | US-LEAV-003 | Chặn đơn vượt hạn mức nghỉ năm | quản lý trực tiếp | hệ thống chặn đơn làm tổng số ngày nghỉ vượt hạn mức | không phải duyệt đơn vi phạm chính sách | #15 | AX_LEAV_002 | Flow 1 | PENDING-OQ-01 | I✅ N✅ V✅ E✅ S✅ T⚠️ | — | Chờ OQ-01 (con số hạn mức) |
| EP-02 Chính sách & nhắc việc | US-LEAV-004 | Nhắc quản lý duyệt đơn tồn đọng | quản lý trực tiếp | được nhắc khi có đơn chờ duyệt quá hạn | không để đơn bị bỏ sót | #16 SYSTEM | — | Flow 1 | PENDING-OQ-02 | I✅ N✅ V✅ E⚠️ S✅ T⚠️ | Có | Chờ OQ-02 (thời gian chờ, kênh nhắc) |
<!-- END-REGISTER -->

```
US COUNT: 4 Story · 2 Epic
US COVERAGE — phủ 5/5 · THIẾU: []        (--expect-fr "12-16")
Cần chú ý: Spike = Có → US-LEAV-004 · PENDING-OQ → US-LEAV-003, US-LEAV-004
Estimate / Ưu tiên: để trống — Dev / PO điền
```

**Các điểm đáng chú ý:**
- Chỉ **2 tầng** `Epic → User Story`. Không có Level 1-2-3. Story không xuất hiện trên Sitemap hay bất kỳ frame Figma nào.
- `AC ref` chỉ là ID — nội dung AC nằm ở §E.
- `#16 SYSTEM`: chức năng không có màn vẫn có Story và vẫn được tính vào FR coverage.
- `Spike = Có` chỉ đánh dấu "chưa ước lượng được vì thiếu thông tin" — **không** có con số effort.
- `Epic ≠ Flow`: ở ví dụ này cả hai Epic cùng thuộc `Flow 1`.
