# BA Agent — Multiple Interpretations Check (Bước 2a)

> **Scope:** Chi tiết logic + template trình bày khi user request có ≥2 cách hiểu.
> **Dùng ở:** `ba-agent.md` Bước 2a — trigger khi request mơ hồ. Agent body chỉ giữ trigger rule + reference file này.

---

## Nguyên tắc

KHÔNG được pick 1 diễn giải im lặng khi user request có ≥2 cách hiểu hợp lý. Chi phí clarify = 2-5 phút; chi phí rework SPEC sai = 2 tuần fan-out toàn bộ pipeline downstream (Design/Tasks/Dev/QA/QC).

## Trigger

Áp dụng khi request của user chứa từ mơ hồ (`export`, `nhanh hơn`, `tối ưu`, `báo cáo`, `quản lý`, `theo dõi`, `tự động`, `thông báo`, `import`, `sync`, `dashboard`...) hoặc chưa rõ scope (`làm feature X` không kèm actor/context).

## Không áp dụng

Request đã kèm đủ context (actor, action cụ thể, output rõ) và chỉ có 1 diễn giải hợp lý — proceed thẳng section 2b, không thêm noise.

---

## Template trình bày

```
"<user request nguyên văn>" có thể hiểu <N> cách khác nhau. Trước khi vào checklist chi tiết,
mình muốn xác nhận scope:

1. **<Diễn giải A ngắn gọn>** — <hệ quả về mặt user thấy gì>
   - Approach: <cách làm 1-2 câu>
   - Effort ước lượng: ~<X> giờ / <Y> ngày
   - Trade-off: <đánh đổi so với option khác>

2. **<Diễn giải B>** — ...
   - Approach: ...
   - Effort: ...
   - Trade-off: ...

3. **<Diễn giải C>** (nếu có) — ...

Context hiện tại của dự án (nếu relevant): <ví dụ: "hệ thống đã có API endpoint list users nhưng
chưa có export">

Bạn muốn hướng nào? (hoặc kết hợp?)
```

---

## Ví dụ minh hoạ

User request: *"Làm chức năng export user data cho admin"*

Diễn giải:

1. **Download file trực tiếp trên browser** — admin bấm button, browser tải CSV ngay
   - Approach: Endpoint `GET /admin/users/export.csv` trả `Content-Disposition: attachment`
   - Effort: ~4 giờ
   - Trade-off: OK cho < 10K users; > 10K sẽ timeout browser

2. **Background job + gửi email link download** — admin bấm, nhận email khi xong
   - Approach: Queue job (BullMQ), lưu file S3, email link expire 24h
   - Effort: ~2 ngày
   - Trade-off: Cần infra queue + email; chịu được data lớn

3. **API endpoint trả JSON có pagination** — cho hệ thống khác consume, không phải cho human
   - Approach: `GET /admin/users?page=1&limit=100` — endpoint bình thường
   - Effort: ~2 giờ
   - Trade-off: Không phải "export" theo nghĩa user thường hiểu

Bạn muốn hướng nào?

---

## Xử lý câu trả lời

- User chọn 1 option → dùng option đó làm baseline cho section 2b (skip câu hỏi đã trả lời qua trade-off)
- User trả lời "kết hợp A+B" hoặc "làm A trước, B sau" → note vào SPEC section `## Out of Scope` (phần chưa làm ngay)
- User trả lời "chưa biết, bạn tư vấn" → recommend option đơn giản nhất kèm lý do, hỏi confirm
