# Ba Agent — Nguyên tắc Granularity (Flow & Screen)

> **Nguyên tắc gốc, áp dụng cho MỌI quyết định "tách hay gộp" trong BA workflow** (Output 1 business flow, SPEC `## Screens`, Output 2 screen flow):
>
> **Độ chi tiết của output PHẢI đến từ phán đoán nghiệp vụ/UX độc lập, KHÔNG được kế thừa tự động từ cách tài liệu nguồn (Estimate/PRD/meeting note) tình cờ liệt kê.**
>
> Lỗ hổng đã xảy ra thực tế 2 lần trong cùng 1 lần chạy: (1) N business flow ở Output 1 được suy thẳng từ số nhóm 中分類 trong Excel, không qua kiểm tra nghiệp vụ nào; (2) Screen Code ở SPEC/Output 2 được tách y hệt số dòng Estimate, dù định nghĩa `Wizard` trong `spec-template.md` vốn đã có ý định gộp nhiều bước lại. Cả 2 đều vì agent để tài liệu nguồn quyết định granularity thay vì tự áp test.

---

## ⛔ GATE FR COVERAGE — mốc đếm phải là DÒNG CHỨC NĂNG GỐC (BẮT BUỘC, chạy trước mọi phép "đã đủ")

> **Lỗ hổng đã xảy ra thực tế:** input là Estimate 58 dòng chức năng / 7 nhóm lớn / 34 nhóm giữa. Agent lấy **34 nhóm giữa** làm mốc đối chiếu cho rule "gộp = đổi tầng", nên Sitemap 42 hành động cho ra `42 ≥ 34` → **gate PASS**. Ở mức chức năng thật thì `42 < 58` → phải **FAIL**. Hậu quả: 3 chức năng (`#1 ログアウト`, `#33 医師間カルテ共有`, `#38 薬剤相互作用チェック`) biến mất khỏi cả SPEC lẫn 3 Figma output mà không gate nào kêu. User là người phát hiện, không phải agent.
>
> **Bản chất lỗi: gate tự so với chính mình.** Bảng ứng viên thô do chính BA gom từ nguồn — lấy nó làm mốc thì mọi thứ BA bỏ sót lúc gom sẽ biến mất khỏi cả mốc lẫn kết quả, nên hiệu số luôn đẹp.

**Rule:**

1. **Mốc đối chiếu duy nhất hợp lệ = số dòng chức năng nhỏ nhất trong tài liệu nguồn** (Estimate `見積明細` từng dòng · PRD từng requirement · meeting note từng gạch đầu dòng). **KHÔNG được** lấy: số nhóm lớn/nhóm giữa, số flow sau gộp, số candidate trong Flow Candidate Matrix, hay bất kỳ con số nào do BA tự tổng hợp.
2. **Lập `FR Register` ngay ở Bước 0**, TRƯỚC Flow Candidate Matrix — 1 dòng / 1 chức năng nguồn, đánh số `#1..#N` theo đúng thứ tự tài liệu gốc. Đây là baseline bất biến cho toàn bộ lần chạy.
3. **Mọi phép kiểm "đã đủ" phải đối chiếu theo TẬP HỢP, không theo số lượng.** `count(kết quả) ≥ count(nguồn)` là phép kiểm rỗng — phải chứng minh `set(FR nguồn) − set(FR đã xuất hiện) = ∅` và **in ra danh sách thiếu** (kể cả khi rỗng).
4. **Chức năng không sinh màn hình** (batch, cron, job hệ thống, API nội bộ) vẫn PHẢI có 1 dòng trong FR Register, đánh dấu `SYSTEM — không có màn` + trỏ tới node hệ thống ở Output 1/2. **Im lặng bỏ qua = tính là thiếu.**
5. **Cột `FR No.` là bắt buộc** trong bảng `## Screens` của SPEC (xem `spec-template.md`) và trong Sitemap Output 1 (mỗi Hành động gắn tag `#N`). Không có cột này → lần audit sau phải rà tay 58 dòng, chính là tình huống đã xảy ra.

**FR Register — format bắt buộc (đặt trong `## Source Register` hoặc ngay dưới nó):**

```markdown
| FR No. | Chức năng (nguyên văn nguồn) | Nhóm nguồn | Screen Code phủ | Ghi chú |
|---|---|---|---|---|
| #1 | ログアウト | ①共通機能 | CM_AUTH_005 | |
| #24 | 予約リマインド通知（送信） | ③予約管理 | — | SYSTEM — batch, không có màn |
| #33 | 医師間カルテ共有（複数科受診時） | ④診察・カルテ | MR_SHARE_001 | |
```

**Phép kiểm bắt buộc in ra trước khi chốt SPEC và trước khi vẽ Output 1:**

```
FR COVERAGE — nguồn: <file> (<N> dòng chức năng)
  Đã phủ      : <n>/<N>
  SYSTEM-only : #24 (batch reminder)
  THIẾU       : []            ← phải rỗng, và phải in ra kể cả khi rỗng
```

`THIẾU ≠ []` → **KHÔNG được vẽ Figma, KHÔNG được báo hoàn thành.** Hoặc bổ sung Screen Code, hoặc ghi rõ lý do "không sinh màn" vào FR Register.

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
4. Verify rule **"gộp = đổi tầng hiển thị, KHÔNG phải xoá thông tin"**: mọi candidate bị gộp phải xuất hiện lại ở Sitemap WBS (Phần C Output 1) hoặc dưới dạng Trigger box phụ / step của `Wizard` — **đối chiếu với `FR Register` (dòng chức năng gốc), KHÔNG đối chiếu với bảng ứng viên do chính BA gom** (xem § GATE FR COVERAGE ở trên)
5. **Trình danh sách đã gộp/tách kèm lý do cho user xác nhận** trước khi vẽ Figma (Output 1 xác nhận N flow, SPEC Screens xác nhận trước Output 2/3) — không tự tiện chốt rồi vẽ luôn
6. Nếu số lượng sau khi gộp vẫn lớn bất thường (N flow vượt ngưỡng của `FLOW_GRANULARITY` ở Câu 0.9, hoặc 1 flow có quá nhiều Screen Code biến thể) → phải nêu rõ lý do cụ thể khi trình user, không giấu

## Anti-pattern

- ❌ Đếm N flow/N screen bằng cách đếm số dòng/section trong tài liệu nguồn
- ❌ Vẽ Figma (tốn nhiều Figma tool call) trước khi user xác nhận danh sách flow/screen đã gộp
- ❌ Tách N Screen Code cho N bước của cùng 1 Wizard chỉ vì nguồn liệt kê N dòng
- ❌ Chấp nhận N flow > 10 mà không tự vấn lại hoặc không giải thích lý do cho user
- ❌ Chỉ chạy test cho các cặp "có vẻ liên quan" — phải chạy cho MỌI cặp cùng Actor HOẶC cùng Outcome
- ❌ Coi "gộp" là xoá bớt thông tin — gộp ở tầng flow thì candidate PHẢI xuất hiện lại ở Sitemap / Trigger phụ / step của `Wizard`
- ❌ **Lấy số nhóm / số candidate do BA tự gom làm mốc đối chiếu coverage** — gate sẽ tự so với chính mình và luôn PASS. Mốc duy nhất hợp lệ là số dòng chức năng gốc (§ GATE FR COVERAGE)
- ❌ **Kết luận "đủ" bằng phép so số lượng** (`42 ≥ 34`) thay vì phép trừ tập hợp có in danh sách thiếu
- ❌ Bỏ qua chức năng "không có màn hình" (batch/cron) mà không ghi dòng `SYSTEM` trong FR Register
- ❌ Kết luận "đã đủ flow/screen/item" bằng cảm tính — mọi kết luận "đủ" phải có phép đếm đối chiếu với nguồn NGOÀI (SPEC, Flow Candidate Matrix, Non-Happy Coverage Matrix)
