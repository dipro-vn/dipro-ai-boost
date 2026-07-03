# New Feature Workflow — Feature mới / Implement / Integration

> Bước "tìm file liên quan" đã thực hiện ở bước 1 của [Workflow dispatcher](../CLAUDE.md#6-workflow-theo-loại-task).

1. Lấy spec từ [notebookLM](../CLAUDE.md#tool-notebooklm) — BẮT BUỘC có spec trước khi code feature mới; nếu không có, hỏi tôi.
2. Check design từ [figma](../CLAUDE.md#tool-figma) nếu feature có UI; nếu không có, hỏi tôi.
3. Feature mới mặc định luôn ở mức **trung bình trở lên** — BẮT BUỘC lên plan chi tiết + chờ tôi approve rõ ràng trước khi code, theo [Planning Spec](../rules/planning-spec.md).
4. Chọn skill theo [Skill Selection Spec](../rules/skill-selection-spec.md) (xác định framework, dùng skill có sẵn hoặc tìm qua find-skills + chờ tôi confirm trước khi cài).
5. Code theo spec, design và plan đã approve, tuân thủ [Coding Convention](../CLAUDE.md#reference-1).
6. Chạy lint/format/test. Pass → chỉ báo "✅ Pass" (không in log chi tiết). Có lỗi → chỉ in phần liên quan kèm hướng xử lý.
7. Sync lại source-map tool đã dùng (`codegraph sync` hoặc `/understand`), bỏ qua nếu dự án chưa setup.
8. Impact assessment, gửi cho tôi.
9. Track tiến độ bằng tag `[x]` done / `[ ]` pending.

Confirm có cần viết unit test cho task này không — nếu có, thực hiện sau bước 9.
