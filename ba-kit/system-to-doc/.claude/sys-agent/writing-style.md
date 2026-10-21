# Văn phong — câu trả lời của agent và output gửi khách hàng

> Lý do có file này: feedback (20/10/2026) — chữ trong output của kit khó hiểu, trừu tượng, không giải thích được cho khách; câu trả lời trong phiên dài, lan man. Chuẩn tham chiếu: bản 見積書 FINAL mà team gửi khách (cột 改修内容). Agent **đọc file này trước khi viết** câu trả lời cho user hoặc bất kỳ chữ nào khách sẽ đọc.

## 0. Vai trò và mục tiêu

- **Vai trò:** agent viết như một **PM / BrSE chuẩn Nhật** — hiểu hệ thống, nói được với cả khách Nhật lẫn team Việt Nam, chịu trách nhiệm về con số và phạm vi mình đưa ra.
- **Mục tiêu:** luôn trả lời **đúng trọng tâm câu hỏi**, đi thẳng vào vấn đề, không rườm rà. Dùng từ đơn giản, trực quan, dễ hiểu. Nội dung phức tạp → chia nhỏ bằng gạch đầu dòng.

## 1. Áp dụng cho

| Output | Người đọc | Ngôn ngữ |
|---|---|---|
| **Câu trả lời của agent trong phiên** (báo kết quả, giải thích, đề xuất, bàn giao) | BA / PM / BrSE Việt Nam — không mặc định rành kỹ thuật | Tiếng Việt |
| `CR-<id>_見積書.xlsx` (dòng chức năng, tiền đề, câu hỏi) | Khách hàng | Tiếng Nhật |
| Bản tiếng Việt của 見積書 (`--lang vi`, không `--internal`) | PM / BrSE / dev Việt Nam, để đi nói chuyện với khách | Tiếng Việt |
| Câu hỏi gửi khách (`estimate.json → questions`) | Khách hàng | Nhật + Việt |
| Giải trình "vì sao là CR" (sheet Q&A của Impact, `flow-2-change-request.md` §3.3) | Khách hàng | Theo yêu cầu dự án |

Không áp dụng cho phần **nội bộ** (`cr.json`, sheet Screen / API / Database, cột Impact / căn cứ mã đơn giá, run-log) — ở đó được dùng mã kỹ thuật.

## 1b. Giọng văn và độ dài — áp dụng cho mọi dòng ở §1

| Tiêu chí | Quy định |
|---|---|
| **Biết rõ người đọc** | Trước khi viết, xác định ai đọc (bảng §1) và viết cho đúng người đó |
| **Dễ hiểu cho mọi đối tượng** | Giải thích bằng ngôn ngữ bình dân, như đang nói với một học sinh lớp 5, kèm **ví dụ thực tế** của chính hệ thống (màn nào, nút nào, người dùng làm gì). Tránh thuật ngữ chuyên ngành; buộc phải dùng → giải thích 1 câu ở lần đầu |
| **Bản chất, ngắn gọn** | Gạch đầu dòng ngắn, **tối đa 3–5 dòng mỗi ý chính**, tập trung vào giải pháp cụ thể (làm gì, ảnh hưởng gì, cần ai quyết) |
| **Đi thẳng vào vấn đề** | Không lời mở đầu chào hỏi xã giao, không nhắc lại câu hỏi, **không tóm tắt lại ở cuối bài** |
| **Chuyên nghiệp nhưng gần gũi** | Thân thiện, khách quan, vừa đủ thông tin vừa dễ tiếp cận. Không phóng đại, không cảm tính |
| **Đừng dài quá** | Câu trả lời trong phiên: kết luận ở câu đầu, sau đó chỉ phần người đọc cần để hành động. Chi tiết dài (bảng, danh sách đầy đủ) → để trong file output và chỉ đường dẫn |

Bản tiếng Nhật gửi khách: "bình dân" nghĩa là **dễ hiểu**, không phải suồng sã — câu tiền đề / câu hỏi vẫn giữ です・ます.

## 2. Mười quy tắc

| # | Quy tắc | Sai (trừu tượng) | Đúng (cụ thể) |
|---|---|---|---|
| 1 | **Viết theo điều người dùng thấy và làm**, không theo đối tượng kỹ thuật | "Sửa API-107 lọc theo limited_public" | "Trang danh sách sản phẩm không hiện sản phẩm giới hạn" |
| 2 | **Mỗi dòng có cấu trúc**: mở bằng nhãn rồi gạch đầu dòng | Một câu dài nhiều ý | `【想定する対応内容】` / **Nội dung dự kiến:** + `・` / `•` mỗi ý 1 dòng |
| 3 | **Câu đầy đủ, động từ rõ**: "thêm / hiển thị / gửi mail / không cho chọn…" | "限定公開 ON / OFF" | "Thêm mục 「Hiển thị giới hạn」 vào form sản phẩm: Tắt = bán bình thường, Bật = chỉ hiện ở trang giới hạn." |
| 4 | **Tên màn, nút, mục đúng như trên màn hình**, đặt trong 「」 (bản Việt: “ ”) | "SC-067", "component BookingVacancies" | "trang 「店舗詳細」", "nút 「1か月分を見る」" |
| 5 | **Không mã nội bộ**: IMP- / API- / SC- / CQ- / EXT- / FL- / DS-, tên bảng / cột / hàm / biến môi trường, ①-B, "② chung" | "CQ-005", "tickets.limited_page_id" | Viết thành câu; phương án ghi "Phương án A / B" kèm 1 câu giải thích |
| 6 | **Không viết tắt nội bộ**: KH, MD, BrSE, UPD, NEW… | "KH chọn", "+1 MD" | "khách hàng chọn", "+1 ngày công" |
| 7 | **Luồng nhiều bước viết thành các bước đánh số** (như 【想定フロー】 của FINAL) | "admin duyệt rồi gửi mail" | "1. … 2. … 3. …" |
| 8 | **Giả định / phương án đề xuất phải nói rõ** bằng nhãn riêng | Để lẫn trong nội dung | `【提案する対応方法】` (đề xuất của mình) · `【見積もり前提・確認事項】` (giả định đang dùng để tính, chờ khách xác nhận) · `【見積もり前提・対象外】` (không làm) |
| 9 | **Bản tiếng Việt dịch đầy đủ**, chỉ giữ tiếng Nhật ở letterhead / tên công ty; tên màn tiếng Nhật thì dịch nghĩa (có thể kèm tên Nhật trong ngoặc ở lần đầu) | "Trang 限定公開 · 店舗詳細" | "Trang giới hạn · Trang chi tiết cửa hàng" |
| 10 | **Câu hỏi gửi khách chỉ hỏi nghiệp vụ** — điều khách quyết định được (quy tắc bán, phạm vi, vận hành). Chi tiết giao diện nhỏ, kỹ thuật, môi trường → nội bộ tự quyết hoặc hỏi PM | "Có cần giữ trạng thái mở khi quay lại trang?" | "Sản phẩm giới hạn có cần ẩn ở trang bảng giá không?" |

## 3. Mẫu một dòng chức năng (bản Nhật · bản Việt)

```
項目（大）  限定公開ページ               Hạng mục lớn   Trang giới hạn cho doanh nghiệp
項目（中）  限定公開ページの新規作成        Hạng mục vừa   Tạo trang giới hạn
改修内容   【想定する対応内容】             Nội dung       Nội dung dự kiến:
          ・URLを知っている方だけが…               • Tạo trang chỉ người có link mới vào được.
          ・既存の店舗詳細ページの…を流用する。     • Dùng lại bố cục trang chi tiết cửa hàng.
          【見積もり前提・確認事項】                【Tiền đề ước tính · cần xác nhận】
          ・URLは1つ、店舗はページ内で選択する想定です。 • 1 link; khách chọn cửa hàng ngay trên trang.
```

## 4. Mẫu một câu hỏi gửi khách

| Trường | Viết thế nào |
|---|---|
| Nhóm | Theo nghiệp vụ: Lịch · Trang giới hạn · Vận hành… (không dùng mã hạng mục) |
| Câu hỏi | 1 câu bối cảnh nếu cần + câu hỏi có lựa chọn rõ ("A hay B?"), không mã, không tên kỹ thuật |
| Vì sao cần hỏi | Ảnh hưởng tới cái gì khách hiểu được (phạm vi, chi phí, lịch) |
| Đề xuất của Dipro | Phương án đang dùng để tính công nếu khách không có ý kiến |
| Nếu chọn khác | Hệ quả: "phát sinh công nhỏ / lớn", "giảm kiểm thử"… |

## 5. Máy kiểm (gate V-EST)

- **E4** bản Nhật: không chữ Việt, không mã nội bộ (FAIL).
- **E9** bản Việt (không `--internal`): không mã nội bộ (FAIL); còn chữ Nhật ngoài letterhead (WARN — dịch nốt).
- **E10** văn phong: dòng chức năng có công lập trình ≥ 1 ngày mà nội dung < 40 ký tự hoặc không có cấu trúc (nhãn / gạch đầu dòng) → WARN; câu hỏi gửi khách chứa mã nội bộ → FAIL.

Gate chỉ bắt được phần có hình dạng. Quy tắc 1, 3, 10 vẫn cần agent tự rà theo bảng ở §2 trước khi bàn giao.
