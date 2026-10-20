# Văn phong cho output gửi khách hàng

> Lý do có file này: feedback (20/10/2026) — chữ trong output của kit khó hiểu, trừu tượng, không giải thích được cho khách. Cùng chuẩn với `system-to-doc/.claude/sys-agent/writing-style.md` (chuẩn tham chiếu: cột 改修内容 của bản 見積書 FINAL team gửi khách). Agent **đọc file này trước khi viết** mọi chữ khách đọc.

## 1. Áp dụng cho

| Output | Người đọc | Phần áp dụng |
|---|---|---|
| Output OQ — `OQ-REGISTER.md` + `open_questions.xlsx` (`open-questions.md`) | Khách hàng / BrSE | Cột Câu hỏi · Vì sao cần trả lời · Phương án BA đề xuất · Lựa chọn gợi ý |
| `output_cr.md` (`change-request.md` §4) | Khách hàng | Toàn bộ, trừ bảng Reference |
| Giải trình "vì sao là CR" (`change-request.md` §1) khi chuyển cho khách | Khách hàng | Toàn bộ |
| Figma Output 1 / 2 / 3 / CR view khi `OUTPUT_AUDIENCE` = BrSE / Khách hàng cuối (Câu 0.11) | Khách hàng / BrSE | Bước trong lane use case, mô tả node, cột Mô tả / Action của bảng ITEMS, message lỗi |

Không áp dụng cho phần **nội bộ** (`SPEC.md` `## Source Register`, cột `Liên quan` / trace của OQ, tên layer Figma, bảng Reference của `output_cr.md`, `feedback-triage.md`, run-log) — ở đó được dùng mã.

Ngôn ngữ theo `OUTPUT_LANG` (Câu 0.11). Bản tiếng Nhật dùng nhãn 【想定する対応内容】 / 【提案する対応方法】 / 【見積もり前提・確認事項】 / 【見積もり前提・対象外】; bản tiếng Việt dùng nhãn tương ứng ở quy tắc 2 và 8.

## 2. Mười quy tắc

| # | Quy tắc | Sai (trừu tượng) | Đúng (cụ thể) |
|---|---|---|---|
| 1 | **Viết theo điều người dùng thấy và làm**, không theo đối tượng kỹ thuật | "Sửa API lọc theo limited_public" | "Trang danh sách sản phẩm không hiện sản phẩm giới hạn" |
| 2 | **Mỗi mục có cấu trúc**: mở bằng nhãn rồi gạch đầu dòng | Một câu dài nhiều ý | **Nội dung dự kiến:** + `•` mỗi ý 1 dòng (JP: `【想定する対応内容】` + `・`) |
| 3 | **Câu đầy đủ, động từ rõ**: "thêm / hiển thị / gửi mail / không cho chọn…" | "Giới hạn ON / OFF" | "Thêm mục “Hiển thị giới hạn” vào form sản phẩm: Tắt = bán bình thường, Bật = chỉ hiện ở trang giới hạn." |
| 4 | **Tên màn, nút, mục đúng như trên màn hình**, đặt trong “ ” (JP: 「」) | "AX_ORD_004", "component BookingVacancies" | "trang “Chi tiết cửa hàng”", "nút “Xem 1 tháng”" |
| 5 | **Không mã nội bộ** trong chữ khách đọc: `FR-` / `OQ-` / `CR-` (trừ tiêu đề) / mã màn `AX_…` / `IMP-` / `API-` / `CQ-`, tên bảng / cột / hàm, "Output 2", "Flow 3" | "FR-12 · AX_ORD_004", "chặn vẽ Output 2" | Viết thành câu: "màn duyệt đơn", "chưa vẽ được bước duyệt đơn" |
| 6 | **Không viết tắt nội bộ**: KH, MD, BrSE, UPD, NEW, AC… | "KH chọn", "chặn chốt AC" | "khách hàng chọn", "chưa chốt được tiêu chí nghiệm thu" |
| 7 | **Luồng nhiều bước viết thành các bước đánh số** | "admin duyệt rồi gửi mail" | "1. … 2. … 3. …" |
| 8 | **Giả định / phương án đề xuất phải nói rõ** bằng nhãn riêng | Để lẫn trong nội dung | **Đề xuất:** (đề xuất của mình) · **Tiền đề · cần xác nhận:** (giả định đang dùng, chờ khách xác nhận) · **Không làm:** (ngoài phạm vi) |
| 9 | **Một ngôn ngữ mỗi bản**: bản Việt dịch đầy đủ; tên màn tiếng Nhật thì dịch nghĩa (có thể kèm tên Nhật trong ngoặc ở lần đầu) | "Trang 限定公開 · 店舗詳細" | "Trang giới hạn · Trang chi tiết cửa hàng (店舗詳細)" |
| 10 | **Câu hỏi gửi khách chỉ hỏi nghiệp vụ** — điều khách quyết định được (quy tắc, phạm vi, vận hành). Chi tiết giao diện nhỏ, kỹ thuật, môi trường → nội bộ tự quyết hoặc chuyển Tech Lead (`open-questions.md` §1). Điều nguồn đã trả lời → ghi thành tiền đề, không hỏi | "Có cần giữ trạng thái mở khi quay lại không?" | "Đơn đã huỷ có được đặt lại cùng suất đó không?" |

## 3. Mẫu một câu hỏi gửi khách (OQ)

| Cột | Viết thế nào |
|---|---|
| Nhóm nghiệp vụ | Theo bảng `open-questions.md` §1 (Quyền & phê duyệt · Business rule…), không dùng mã |
| Câu hỏi | 1 câu bối cảnh nếu cần + câu hỏi có lựa chọn rõ ("A hay B?"), không mã, không tên kỹ thuật |
| Vì sao cần trả lời | Ảnh hưởng khách hiểu được: "chưa vẽ được bước duyệt đơn", "chưa chốt được màn thanh toán" — không "chặn Output 2" |
| Phương án BA đề xuất | Phương án đang dùng nếu khách không có ý kiến, viết thành câu đầy đủ |
| Lựa chọn gợi ý | `A) … · B) … · C) …` — mỗi lựa chọn 1 hệ quả ngắn nếu khác biệt lớn |
| Liên quan | **Cột trace nội bộ** — được ghi `FR No.` · flow · mã màn |

## 4. Máy kiểm

- `export-open-questions.py` check **"Van phong gui khach"**: mã nội bộ (`FR-` / `OQ-` / `IMP-` / `API-` / `CQ-` / mã màn `XX_YYY_NNN`) trong Câu hỏi / Vì sao / Đề xuất / Lựa chọn → **FAIL**; viết tắt nội bộ (KH, BrSE, MD, AC, UPD) hoặc "Output N" → **WARN**.
- `output_cr.md` và chữ trên Figma không có script → agent rà theo bảng §2 ở bước Self-Feedback (`self-feedback.md`).

Gate chỉ bắt được phần có hình dạng. Quy tắc 1, 3, 10 vẫn cần agent tự rà trước khi bàn giao.
