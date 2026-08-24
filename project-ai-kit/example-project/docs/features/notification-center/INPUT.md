# INPUT — notification-center

> **File tạm để unblock BA.** Bạn paste nội dung yêu cầu vào phần ① bên dưới (raw cũng được — không cần format lại).
> Sau khi paste xong, nhắn "đã paste" → tôi đọc file này và viết `SPEC.md`.
> File này **không phải artifact BMAD**, sẽ xoá sau khi SPEC hoàn tất.

---

## ① Nội dung yêu cầu (paste vào đây)

<!-- PASTE BẮT ĐẦU TỪ DÒNG DƯỚI -->



<!-- PASTE KẾT THÚC Ở DÒNG TRÊN -->

---

## ② Trả lời nhanh (tuỳ chọn — bỏ trống cũng được, tôi sẽ hỏi lại nếu ① chưa đủ)

**Scope — chọn 1 (xem giải thích ở chat):**

- [ ] A — In-app inbox (list + badge unread + mark-as-read)
- [ ] B — A + push/real-time (FCM/APNs + WebSocket)
- [ ] C — A + B + preference center (user bật/tắt theo loại & kênh)
- [ ] D — Admin broadcast tool (admin soạn & gửi)
- [ ] Kết hợp: ................................................

**Câu hỏi chi tiết:**

| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Actor nào dùng? (end user mobile / user web / admin) | |
| 2 | Đang thông báo bằng gì hiện nay? Vấn đề gì? | |
| 3 | Bắt buộc login? Phân quyền theo role? | |
| 4 | Nguồn sinh thông báo: system event tự động hay admin soạn tay? Liệt kê 3–5 loại đầu tiên | |
| 5 | Happy path từng bước (sự kiện xảy ra → user đọc được) | |
| 6 | Edge cases quan trọng (user offline, hết hạn, xoá, gửi 10K user, sync unread web↔mobile) | |
| 7 | Acceptance criteria — khi nào coi là done? | |
| 8 | Repo liên quan: `example-api` / `example-web` / `example-mobile` — cái nào? | |
| 9 | Real-time (WebSocket / push) có trong scope lần này không? | |
| 10 | Tích hợp ngoài: FCM / APNs / email provider / SMS? | |

**Epic code (để sinh Screen Code — `AGENTS.md` chưa khai):**

| Repo | Epic code |
|---|---|
| `example-api` | |
| `example-web` | (ví dụ `WB` → `WB_NOTF_001`) |
| `example-mobile` | (ví dụ `MB` → `MB_NOTF_001`) |
