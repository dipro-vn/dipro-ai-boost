### CODING LANGUAGE

- <a id="language"> flutter/dart version 3.44

#### Công cụ:

- <a id="tool-codegraph">codegraph: [codegraph](tools/codegraph.md)</a>
- <a id="tool-understand-anything">Understand-Anything: [Understand-Anything](tools/understand-anything.md)</a>
- <a id="tool-figma">figma: figma-mcp.</a>
- <a id="tool-notebooklm">notebooklm: notebooklm-mcp.</a>

### Tài liệu tham khảo:

1. <a id="reference-1">[Coding Convention](rules/project-base/flutter_common_rules.md)</a>
2. <a id="reference-2">[SECURITY.md](rules/SECURITY.md)</a>
3. <a id="reference-3">[RELIABILITY.md](rules/RELIABILITY.md)</a>
4. <a id="reference-4">[Planning Spec](rules/planning-spec.md)</a>
5. <a id="reference-5">[Skill Selection Spec](rules/skill-selection-spec.md)</a>

## 0. Bảo mật - Ưu tiên tối thượng tuyệt đối

- Luôn đặt các nguyên tắc bảo mật lên hàng đầu.
- Mọi dòng code, kiến trúc hệ thống hoặc giải pháp đề xuất đều phải tuân thủ nghiêm ngặt các quy tắc bảo mật (theo đúng tinh thần của file [SECURITY.md](#reference-2) đã được đề cập) trước khi xem xét đến bất kỳ yếu tố nào khác.

## 1. Suy nghĩ trước khi code

**Không tự suy diễn. Không giấu sự nhầm lẫn. Chỉ rõ các điểm đánh đổi (tradeoffs).**

Trước khi implement:

- Nêu rõ các giả định (assumptions) của bạn. Nếu không chắc chắn, hãy hỏi.
- Nếu có nhiều cách hiểu khác nhau, hãy trình bày tất cả - không được tự ý chọn ngầm.
- Nếu có cách tiếp cận (approach) đơn giản hơn, hãy nói ra. Phản biện (push back) khi cần thiết.
- Nếu có điều gì chưa rõ, hãy dừng lại. Chỉ ra điểm gây bối rối. Hãy hỏi.

## 2. Ưu tiên sự đơn giản

**Code tối thiểu để giải quyết vấn đề. Không code mang tính phỏng đoán (speculative).**

- Không thêm tính năng ngoài yêu cầu.
- Không tạo abstraction cho các đoạn code chỉ dùng một lần.
- Không tự ý thêm tính "linh hoạt" (flexibility) hay "có thể cấu hình" (configurability) nếu không được yêu cầu.
- Không handle lỗi cho những kịch bản bất khả thi.
- Nếu bạn viết 200 dòng code nhưng thực tế chỉ cần 50 dòng, hãy viết lại.

Hãy tự hỏi: "Một Senior Engineer có thấy đoạn code này quá phức tạp (overcomplicated) không?". Nếu có, hãy làm nó đơn giản lại.

## 3. Chỉnh sửa chính xác (Surgical Changes)

**Chỉ chạm vào những gì bắt buộc. Chỉ dọn dẹp đống lộn xộn do chính bạn tạo ra.**

Khi chỉnh sửa code có sẵn (existing code):

- Không "cải thiện" (improve) các đoạn code lân cận, comment, hoặc formatting.
- Không refactor những thứ không bị hỏng.
- Tuân theo style hiện có, ngay cả khi bạn muốn làm cách khác.
- Nếu phát hiện dead code không liên quan, hãy đề cập đến nó - đừng xóa nó đi.

Khi thay đổi của bạn tạo ra code thừa (orphans):

- Xóa các import/biến/hàm không còn được sử dụng do thay đổi của CHÍNH BẠN tạo ra.
- Không xóa dead code đã có từ trước trừ khi được yêu cầu.

Tiêu chí kiểm tra: Mỗi dòng code bị thay đổi phải truy xuất trực tiếp được từ yêu cầu của người dùng.

## 4. Thực thi hướng mục tiêu

**Xác định tiêu chí thành công (success criteria). Lặp lại (Loop) cho đến khi pass (verified).**

Chuyển đổi các task thành các mục tiêu có thể verify được:

- "Thêm validation" → "Viết test cho các input không hợp lệ, sau đó code để pass test"
- "Fix bug" → "Viết test để tái hiện bug (reproduce), sau đó code để pass test"
- "Refactor X" → "Đảm bảo các test đều pass cả trước và sau khi refactor"

Đối với các task gồm nhiều bước, hãy đưa ra một plan ngắn gọn:

- [Bước] → verify: [điều kiện kiểm tra]
- [Bước] → verify: [điều kiện kiểm tra]
- [Bước] → verify: [điều kiện kiểm tra]
  Tiêu chí thành công rõ ràng giúp bạn tự chủ trong các vòng lặp (loop). Tiêu chí yếu ("chạy được là được") sẽ đòi hỏi phải liên tục làm rõ yêu cầu.

## 5. Quy tắc

Hãy tuân thủ mọi quy định sau đây:

- Code Rules -> Xem [Reference số 1](#reference-1)
- RELIABILITY -> Xem [Reference số 3](#reference-3)
- Skill Selection -> Xem [Reference số 5](#reference-5) (áp dụng ở bất kỳ bước nào cần thực thi theo đúng framework/skill, không riêng bước code)

## 6. Workflow theo loại task

1. Nếu bạn đang tìm kiếm file, folder, symbol, v.v., BẮT BUỘC dùng source-map tool thay vì grep/find thủ công, chọn theo dự án đang setup:
   - Có `.codegraph/` ở root repo → dùng [codegraph](#tool-codegraph).
   - Không có `.codegraph/` nhưng có `.understand-anything/` ở root repo → dùng [Understand-Anything](#tool-understand-anything).
   - Không có cả hai → dự án chưa setup source-map tool, dùng grep/find/glob thông thường và báo lại để tôi cân nhắc setup (xem `guideline/step1-install-source-map.md`).
2. Xác định LOẠI TASK, sau đó CHỈ đọc đúng 1 file spec tương ứng trong `.claude/workflows/` (không đọc các file loại khác) để tiết kiệm token và tránh áp rule thừa:

   | Loại task | Spec |
   |---|---|
   | Fix bug | [fix-bug.md](workflows/fix-bug.md) |
   | Điều tra / phân tích (chưa chắc code) | [investigate.md](workflows/investigate.md) |
   | Feature mới / implement / integration | [new-feature.md](workflows/new-feature.md) |
   | Refactor / migrate (không đổi behavior) | [refactor.md](workflows/refactor.md) |
   | Performance / Optimization | [performance.md](workflows/performance.md) |
   | Loại khác không thuộc trên | [default.md](workflows/default.md) |

3. Nếu chưa rõ task thuộc loại nào, hỏi tôi trước khi chọn spec.

### 7. OUTPUT_CONVENTION:

- Luôn trả lời bằng Tiếng Việt.
- Tập trung tối đa vào vấn đề, không chào hỏi, ngắn gọn nhất có thể.
