# BA Agent — Tách User Story & Spike

> **Scope:** quy tắc tách **User Story** (`user-stories.md`) quá lớn, và xử lý Story chưa ước lượng được.
> **Dùng ở:** Bước 5.9 (Output US). Đọc cùng `user-stories.md`.

---

## 0. Ranh giới — KHÔNG nhầm với granularity của Flow / Screen

| | Áp dụng cho | Quy tắc ở đâu |
|---|---|---|
| Gộp/tách **Flow** (Output 1) | Business flow | `granularity-principles.md` — Test G/A/B/F/E |
| Gộp/tách **Screen** (SPEC `## Screens`) | Screen Code | `spec-template.md` — Test C/D |
| Tách **User Story** | Dòng trong danh sách User Story | **File này** |

- ⛔ **Số User Story KHÔNG BAO GIỜ là đầu vào** của Test G/A/B/F/E. Tách Story thành nhiều **không** có nghĩa tách Flow thành nhiều, và **không** được dùng để phình N ở Output 1.
- ⛔ **Số User Story KHÔNG phải mốc "đã đủ".** Mốc duy nhất vẫn là FR Register (`granularity-principles.md` § GATE FR COVERAGE). Story chỉ trace về FR, không thay thế FR.
- Tách Story **không sửa** Output 1/2/3 và **không** vẽ lên Sitemap.

---

## 1. Dấu hiệu cần tách (Smell)

| # | Dấu hiệu | Ngưỡng |
|---|---|---|
| 1 | Tiêu đề chứa "**và**" nối 2 mục tiêu khác nhau ("Đăng ký **và** thanh toán") | có |
| 2 | Có ≥ 2 persona khác nhau cùng đóng vai chính trong 1 Story | ≥ 2 |
| 3 | Gói cả Create + Read + Update + Delete | ≥ 3 thao tác |
| 4 | Số AC `[Happy]`+`[Edge]`+`[Negative]` **của riêng Story đó** (sau khi đã dùng `Examples`) | > 8 |
| 5 | `INVEST — Small` đánh `⚠️` | do BA đánh giá |
| 6 | Trải qua > 1 Screen Type khác hẳn (VD vừa Form vừa Report) | ≥ 2 |

> Ngưỡng #4 tính **theo từng Story**, **không** theo từng màn. Một màn có nhiều dòng Non-Happy không phải lý do tách — gom bằng `Examples` (`ac-standard.md` §5) trước.

Tách thừa cũng là lỗi: Story nhỏ tới mức không có giá trị độc lập (không có `So that` riêng) → **gộp lại**.

## 2. Mẫu tách

| Mẫu | Khi nào dùng | Ví dụ (trung tính) |
|---|---|---|
| **Theo thao tác** (CRUD) | Story gói nhiều thao tác trên cùng thực thể | "Quản lý đơn nghỉ" → Tạo · Xem danh sách · Sửa · Huỷ |
| **Theo persona** | Mỗi actor có quyền/kết quả khác | "Duyệt đơn" → Quản lý trực tiếp duyệt · HR xác nhận |
| **Theo business rule** | Đường chính + quy tắc phức tạp | "Gửi đơn" → Gửi hợp lệ · Kiểm tra hạn mức · Đơn trùng ngày |
| **Theo bước workflow** | Chuỗi có thứ tự, mỗi bước có giá trị | Đăng ký → Xác thực → Kích hoạt |
| **Theo platform** | Cùng chức năng, khác nền tảng đã chốt ở preflight (Câu 0) | Web / Mobile |

Chọn mẫu theo **ý nghĩa nghiệp vụ**, không theo số dòng của tài liệu nguồn (đúng tinh thần `granularity-principles.md`).

## 3. Sau khi tách

- Story con có **ID mới liên tiếp** (`US-LEAV-004`, `-005`…); Story gốc **không** bị xoá số — ghi `Ghi chú: đã tách → US-LEAV-004,005` và đặt `Spike`/`INVEST` phù hợp, hoặc bỏ dòng và ghi ở Diff của `ba-outputs-log.md`.
- Mỗi Story con **phải còn** `FR No.` (trace) và **AC ref** riêng. Không có AC nào để trỏ → Story đó chưa chín.
- Tổng tập `FR No.` của các Story con ⊇ tập của Story gốc (không để mất FR).

## 4. Spike — Story chưa ước lượng được

Dấu hiệu `INVEST — Estimable = ⚠️`:
- Nguồn không đủ để Dev biết làm cỡ nào (kích thước dữ liệu, quy tắc tính, tích hợp bên ngoài chưa rõ)
- Còn OQ mức `Blocker`/`High` gắn với Story đó

Cách xử lý (BA **chỉ đánh dấu**, không ước lượng):

1. Đặt `Estimable = ⚠️` và cột `Spike = Có` cho Story đó.
2. Ghi vào `Ghi chú` **cái gì chưa biết** (câu hỏi cụ thể) — hoặc trỏ `OQ-yy` nếu đã có.
3. Nếu cần nghiên cứu kỹ thuật → Tech Lead/Dev tự mở Spike Story (task kỹ thuật **không thuộc BA**). BA chỉ ghi `Spike = Có`.

⛔ **BA KHÔNG** viết con số man-day/point/giờ vào bất cứ đâu (`change-request.md` đã cấm; cột `Estimate (Dev điền)` trong xlsx để **trống** cho Dev).
⛔ **BA KHÔNG** tự đề xuất giải pháp kỹ thuật cho Spike.

## 5. Anti-pattern

- ❌ Tách Story rồi "tiện thể" tách Flow ở Output 1 cho khớp
- ❌ Dùng số Story làm mốc đã đủ chức năng
- ❌ Tách theo tầng kỹ thuật (UI Story / API Story / DB Story) — mỗi Story phải là **lát cắt dọc có giá trị nghiệp vụ**
- ❌ Ghi estimate vào Story / Spike
- ❌ Tách mà làm mất `FR No.` hoặc AC ref
- ❌ Dùng "AC > 8" làm cớ tách khi chưa thử gom bằng `Examples`
