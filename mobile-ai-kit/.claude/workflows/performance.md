# Performance / Optimization Workflow

> Bước "tìm file liên quan" đã thực hiện ở bước 1 của [Workflow dispatcher](../CLAUDE.md#6-workflow-theo-loại-task).

1. **Đo baseline TRƯỚC khi sửa**: xác định chỉ số cần tối ưu (thời gian render, bundle size, memory, số lần rebuild, thời gian gọi API...) và ghi lại con số hiện tại. Không tối ưu khi chưa có baseline để so sánh.
2. Bỏ qua bước lấy spec/notebookLM và design/figma — trừ khi optimization kéo theo đổi UI/UX.
3. Xác định mức độ theo [Planning Spec](../rules/planning-spec.md):
   - Optimization cục bộ, 1 file, không đổi kiến trúc (vd thêm `const`, `useMemo`, `useCallback`) → code ngay.
   - Đổi kiến trúc/state management, đụng nhiều module → BẮT BUỘC lên plan + chờ tôi approve.
4. Chọn skill theo [Skill Selection Spec](../rules/skill-selection-spec.md) nếu cần.
5. Tối ưu, KHÔNG đổi behavior/output hiện có (theo mục 3 — Surgical Changes của [CLAUDE.md](../CLAUDE.md)).
6. Đo lại chỉ số SAU khi sửa, so sánh với baseline ở bước 1. Nếu không cải thiện rõ ràng, báo lại thay vì giữ thay đổi.
7. Chạy lint/format/test. Pass → chỉ báo "✅ Pass" (không in log chi tiết). Có lỗi → chỉ in phần liên quan kèm hướng xử lý.
8. Sync lại source-map tool đã dùng (`codegraph sync` hoặc `/understand`), bỏ qua nếu dự án chưa setup.
9. Impact assessment kèm số liệu trước/sau (before → after) để tôi đánh giá.
