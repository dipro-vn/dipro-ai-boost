# Default Workflow — Loại task khác

> Dùng khi task không thuộc Fix Bug / Investigate / New Feature / Refactor / Performance.
> Bước "tìm file liên quan" đã thực hiện ở bước 1 của [Workflow dispatcher](../CLAUDE.md#6-workflow-theo-loại-task).

1. Lấy spec từ [notebookLM](../CLAUDE.md#tool-notebooklm), nếu không có, hỏi tôi.
2. Nếu có yêu cầu implement/integration, check design từ [figma](../CLAUDE.md#tool-figma), nếu không có, hỏi tôi.
3. Xác định mức độ task theo [Planning Spec](../rules/planning-spec.md). Trung bình trở lên → BẮT BUỘC lên plan + chờ tôi approve trước khi code.
4. Chọn skill theo [Skill Selection Spec](../rules/skill-selection-spec.md), sau đó code theo [Coding Convention](../CLAUDE.md#reference-1).
5. Chạy lint/format/test. Pass → chỉ báo "✅ Pass" (không in log chi tiết). Có lỗi → chỉ in phần liên quan kèm hướng xử lý.
6. Sync lại source-map tool đã dùng (`codegraph sync` hoặc `/understand`), bỏ qua nếu dự án chưa setup.
7. Impact assessment, gửi cho tôi.
8. Track tiến độ bằng tag `[x]` done / `[ ]` pending.

Confirm có cần viết unit test cho task này không — nếu có, thực hiện sau bước 8.
