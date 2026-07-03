# Planning Spec — Quy trình lên plan trước khi code

> Được tham chiếu từ [Workflow dispatcher](../CLAUDE.md#6-workflow-theo-loại-task) và từng file trong `.claude/workflows/` (fix-bug, new-feature, refactor, performance, default).

## 1. Phân loại mức độ task

**Task đơn giản** (code ngay, KHÔNG cần plan/approve):

- Chỉ đụng 1 file, thay đổi cục bộ, không đổi logic nghiệp vụ.
- Fix typo, đổi text/label tĩnh, đổi 1 giá trị config, sửa lỗi lint/format.
- Có thể verify ngay bằng cách đọc lại đoạn vừa sửa.

**Task trung bình trở lên** (BẮT BUỘC lên plan + chờ approve trước khi code) — có ít nhất 1 trong các dấu hiệu sau:

- Đụng ≥ 2 file hoặc ≥ 2 module/feature.
- Thêm mới hoặc sửa logic nghiệp vụ, thêm feature, đổi state management, thêm dependency mới.
- Sửa bug mà chưa xác định rõ root cause ngay từ đầu.
- Thay đổi ảnh hưởng tới API/contract giữa các layer (domain ↔ data ↔ UI).
- Yêu cầu dùng các từ như "implement", "integrate", "refactor", "migrate", "redesign".

Nếu không chắc task thuộc mức nào → Hãy hỏi lại tôi.

## 2. Quy trình lên plan (task trung bình trở lên)

1. **Xác định phạm vi ảnh hưởng**: dùng source-map tool đã chọn ở bước 0 của Workflow ([codegraph](../tools/codegraph.md) hoặc [Understand-Anything](../tools/understand-anything.md)) để tìm toàn bộ file/symbol liên quan trước khi đề xuất plan.
2. **Nêu giả định**: áp dụng mục 1 (Suy nghĩ trước khi code) của [CLAUDE.md](../CLAUDE.md) — nêu rõ assumption, nếu có nhiều cách hiểu thì liệt kê hết, nếu chưa rõ thì hỏi trước khi soạn plan.
3. **Vào Plan Mode**: nếu công cụ hỗ trợ (vd. `EnterPlanMode` trong Claude Code), dùng plan mode native. Nếu công cụ không có plan mode, trình bày plan dưới dạng markdown trong câu trả lời và hỏi rõ "Bạn có approve plan này không?".
4. **Nội dung plan bắt buộc phải có**:
   - Mục tiêu / phạm vi task.
   - Danh sách file/module sẽ bị đụng tới (dựa trên kết quả bước 1).
   - Các bước thực hiện, mỗi bước kèm tiêu chí verify (theo mục 4 — Thực thi hướng mục tiêu của [CLAUDE.md](../CLAUDE.md)).
   - Rủi ro / tradeoff, và những điểm cần xác nhận thêm với người dùng.
   - Có cần viết unit test hay không (nếu có, ghi rõ sẽ test case nào).
5. **Trình bày plan và chờ approve**: gọi `ExitPlanMode` (nếu có) hoặc hỏi trực tiếp. Chỉ được coi là approved khi người dùng xác nhận rõ ràng (đồng ý/OK/approved...) — im lặng hoặc chuyển chủ đề KHÔNG tính là approve.
6. **Chỉ bắt đầu code sau khi plan được approve.**
7. **Nếu trong lúc code phát hiện cần đổi hướng khác plan đã approve** → dừng lại, cập nhật plan, xin approve lại trước khi tiếp tục. Không tự ý mở rộng phạm vi ngoài plan đã duyệt.

## 3. Ngoại lệ

- Task đơn giản theo mục 1 vẫn có thể được nâng lên "trung bình trở lên" nếu người dùng yêu cầu rõ ràng phải lên plan trước.
- Nếu người dùng chủ động giao task kèm plan/spec chi tiết sẵn (vd. copy từ ticket, từ notebookLM) và xác nhận đồng ý thực hiện luôn → có thể bỏ qua bước soạn plan riêng, nhưng vẫn phải xác nhận lại phạm vi trước khi code.
