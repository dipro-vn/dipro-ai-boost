# Fix Bug Workflow

> Bước "tìm file liên quan" đã thực hiện ở bước 1 của [Workflow dispatcher](../CLAUDE.md#6-workflow-theo-loại-task).

1. **Reproduce**: viết test (hoặc nêu rõ bước tái hiện thủ công nếu chưa test được) để xác nhận bug tồn tại trước khi sửa (theo mục 4 — Thực thi hướng mục tiêu của [CLAUDE.md](../CLAUDE.md)).
2. **Xác định root cause**: dùng source-map tool đã chọn để trace luồng code liên quan. Không đoán/patch triệu chứng khi chưa rõ nguyên nhân (theo [RELIABILITY.md](../rules/RELIABILITY.md)).
3. Bỏ qua bước lấy spec/notebookLM và design/figma — trừ khi bug liên quan trực tiếp tới UI/spec, khi đó check theo bước 1-2 của [default.md](default.md).
4. Xác định mức độ theo [Planning Spec](../rules/planning-spec.md):
   - Root cause rõ, sửa 1 file, không đổi contract → code ngay.
   - Chưa rõ root cause, hoặc fix đụng ≥ 2 file/module → BẮT BUỘC lên plan + chờ tôi approve trước khi sửa.
5. Chọn skill theo [Skill Selection Spec](../rules/skill-selection-spec.md) nếu cần.
6. Fix bug, đảm bảo test ở bước 1 pass và không phá test khác hiện có.
7. Chạy lint/format/test. Pass → chỉ báo "✅ Pass" (không in log chi tiết). Có lỗi → chỉ in phần liên quan kèm hướng xử lý.
8. Sync lại source-map tool đã dùng (`codegraph sync` hoặc `/understand`), bỏ qua nếu dự án chưa setup.
9. Impact assessment — chú trọng: fix này có gây side effect ở chỗ nào khác không (theo mục 3 — Surgical Changes của [CLAUDE.md](../CLAUDE.md)).
10. Ghi rõ **root cause** (why, không chỉ what) trong commit/PR description.
