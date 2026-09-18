# Ba Agent — Nguyên tắc Granularity (Flow & Screen)

> **Nguyên tắc gốc, áp dụng cho MỌI quyết định "tách hay gộp" trong BA workflow** (Output 1 business flow, SPEC `## Screens`, Output 2 screen flow):
>
> **Độ chi tiết của output PHẢI đến từ phán đoán nghiệp vụ/UX độc lập, KHÔNG được kế thừa tự động từ cách tài liệu nguồn (Estimate/PRD/meeting note) tình cờ liệt kê.**
>
> Lỗ hổng đã xảy ra thực tế 2 lần trong cùng 1 lần chạy: (1) N business flow ở Output 1 được suy thẳng từ số nhóm 中分類 trong Excel, không qua kiểm tra nghiệp vụ nào; (2) Screen Code ở SPEC/Output 2 được tách y hệt số dòng Estimate, dù định nghĩa `Wizard` trong `spec-template.md` vốn đã có ý định gộp nhiều bước lại. Cả 2 đều vì agent để tài liệu nguồn quyết định granularity thay vì tự áp test.

---

## Tầng Flow (Output 1) — chi tiết đầy đủ tại `figma-outputs/output-1-flow.md` § "Xác định N"

5 test theo thứ tự chạy (**G chạy ĐẦU TIÊN** — cơ học, lọc sạch case hiển nhiên trước khi tới các test định tính):

| Test | Câu hỏi | Nguồn |
|---|---|---|
| **G — Merge-by-outcome** | 2 ứng viên có trùng CẢ `(Actor, Outcome cuối)` không? Trùng → GỘP ngay, không tranh luận | Phép gom cơ học — giảm chủ quan cho A/B/F |
| **A — Capability grouping** | PM mô tả sản phẩm 1 câu, 2 ứng viên có rơi vào cùng cụm từ không? | Single Responsibility (DDD) |
| **B — Independent-outcome** | Bỏ ứng viên B đi, A còn là hành trình hoàn chỉnh không? B có outcome riêng không? | Tự suy theo mục đích Output 1 |
| **F — Ubiquitous Language & Ownership** (tie-breaker khi A mơ hồ) | 2 ứng viên chung thuật ngữ + chung actor sở hữu? | Bounded Context (DDD — Eric Evans / Martin Fowler) |
| **E — Cardinality Budget** (sanity-check cuối) | N sau khi gộp có > 8-10 không? | User Story Mapping backbone (Jeff Patton) |

## Tầng Screen (SPEC `## Screens` + Output 2) — chi tiết đầy đủ tại `spec-template.md` § "Xác định độ chi tiết 1 Screen"

2 test:

| Test | Câu hỏi | Áp dụng |
|---|---|---|
| **C — Distinct Layout/Purpose** | Cấu trúc layout/kiểu tương tác có khác hẳn nhau không (không chỉ khác nội dung)? | Quyết định tách Screen Code hay không |
| **D — Wizard-step reachability** | State có cần deep-link/điều hướng riêng không, hay chỉ là bước tạm trong 1 lựa chọn? | Quyết định gộp thành step của `Wizard` hay tách riêng |

---

## Quy trình chung bắt buộc (áp dụng cả 2 tầng)

1. Lập **bảng ứng viên thô ĐẦY ĐỦ** từ nguồn (tầng Flow = *Flow Candidate Matrix*) — KHÔNG coi số dòng/nhóm của nguồn là câu trả lời cuối
2. Chạy đủ test tương ứng tầng (Flow: **G → A → B → F → E** · Screen: C → D) trên **mọi cặp cùng Actor HOẶC cùng Outcome** — không chỉ cặp "có vẻ liên quan"
3. In **Merge Log** — mỗi quyết định gộp/tách = 1 dòng, ghi rõ test nào quyết định. **Không có Merge Log → không được vẽ**
4. Verify rule **"gộp = đổi tầng hiển thị, KHÔNG phải xoá thông tin"**: mọi candidate bị gộp phải xuất hiện lại ở Sitemap WBS (Phần C Output 1) hoặc dưới dạng Trigger box phụ / step của `Wizard`
5. **Trình danh sách đã gộp/tách kèm lý do cho user xác nhận** trước khi vẽ Figma (Output 1 xác nhận N flow, SPEC Screens xác nhận trước Output 2/3) — không tự tiện chốt rồi vẽ luôn
6. Nếu số lượng sau khi gộp vẫn lớn bất thường (N flow vượt ngưỡng của `FLOW_GRANULARITY` ở Câu 0.9, hoặc 1 flow có quá nhiều Screen Code biến thể) → phải nêu rõ lý do cụ thể khi trình user, không giấu

## Anti-pattern

- ❌ Đếm N flow/N screen bằng cách đếm số dòng/section trong tài liệu nguồn
- ❌ Vẽ Figma (tốn nhiều Figma tool call) trước khi user xác nhận danh sách flow/screen đã gộp
- ❌ Tách N Screen Code cho N bước của cùng 1 Wizard chỉ vì nguồn liệt kê N dòng
- ❌ Chấp nhận N flow > 10 mà không tự vấn lại hoặc không giải thích lý do cho user
- ❌ Chỉ chạy test cho các cặp "có vẻ liên quan" — phải chạy cho MỌI cặp cùng Actor HOẶC cùng Outcome
- ❌ Coi "gộp" là xoá bớt thông tin — gộp ở tầng flow thì candidate PHẢI xuất hiện lại ở Sitemap / Trigger phụ / step của `Wizard`
- ❌ Kết luận "đã đủ flow/screen/item" bằng cảm tính — mọi kết luận "đủ" phải có phép đếm đối chiếu với nguồn NGOÀI (SPEC, Flow Candidate Matrix, Non-Happy Coverage Matrix)
