# Investigate Workflow — Điều tra / phân tích, chưa chắc code

> Bước "tìm file liên quan" đã thực hiện ở bước 1 của [Workflow dispatcher](../CLAUDE.md#6-workflow-theo-loại-task).
> Task loại này **KHÔNG code** — chỉ đọc, phân tích, báo cáo. Nếu điều tra dẫn tới cần sửa code, dừng lại và hỏi tôi có muốn chuyển sang [fix-bug.md](fix-bug.md) hoặc [new-feature.md](new-feature.md) trước khi code.

1. Dùng source-map tool đã chọn để trace toàn bộ luồng liên quan tới câu hỏi/hiện tượng cần điều tra.
2. Không suy đoán — mọi kết luận phải trace được tới file:line cụ thể (theo [RELIABILITY.md](../rules/RELIABILITY.md)). Nếu thiếu thông tin (log, data thực tế, spec), hỏi tôi thay vì tự giả định.
3. Nếu phát hiện bug trong lúc điều tra, báo ngay, không tự ý sửa.
4. Report: tóm tắt hiện tượng → nguyên nhân (nếu tìm ra) → trích dẫn file:line → đề xuất hướng xử lý (không tự thực hiện).
5. Không cần chạy lint/format/sync source-map vì không đổi code.
