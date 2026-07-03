# Refactor / Migrate Workflow — Không đổi behavior

> Bước "tìm file liên quan" đã thực hiện ở bước 1 của [Workflow dispatcher](../CLAUDE.md#6-workflow-theo-loại-task).

1. Refactor/migrate mặc định luôn ở mức **trung bình trở lên** — BẮT BUỘC lên plan + chờ tôi approve rõ ràng trước khi sửa, theo [Planning Spec](../rules/planning-spec.md). Plan phải nêu rõ: phạm vi refactor, cam kết KHÔNG đổi behavior nào, cách verify (test trước/sau).
2. Bỏ qua bước lấy spec/notebookLM và design/figma — trừ khi refactor kéo theo đổi UI.
3. Đảm bảo có test bao phủ hành vi hiện tại TRƯỚC khi refactor. Nếu chưa có, báo cho tôi trước — không tự ý viết thêm test ngoài phạm vi plan đã approve.
4. Chỉ refactor đúng phạm vi đã approve (theo mục 3 — Surgical Changes của [CLAUDE.md](../CLAUDE.md)). Không "tiện tay" dọn code không liên quan — thấy dead code/code xấu ngoài phạm vi thì ghi chú lại, không tự xóa/sửa.
5. Chọn skill theo [Skill Selection Spec](../rules/skill-selection-spec.md) nếu cần.
6. Chạy lại toàn bộ test liên quan — phải pass cả trước và sau refactor với cùng kết quả hành vi.
7. Chạy lint/format. Pass → chỉ báo "✅ Pass" (không in log chi tiết). Có lỗi → chỉ in phần liên quan kèm hướng xử lý.
8. Sync lại source-map tool đã dùng (`codegraph sync` hoặc `/understand`), bỏ qua nếu dự án chưa setup.
9. Impact assessment — liệt kê rõ những nơi gọi tới code vừa refactor để tôi biết phạm vi ảnh hưởng thực tế.
