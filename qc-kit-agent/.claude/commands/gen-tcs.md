---
description: Sinh Test Case chi tiết (bao gồm Test Scenario) từ analysis.md; tự dựng cấu trúc Screen/Component bên trong, không cần plan. Nếu module chưa có analysis.md, hỏi user chọn Full Mode (chạy /analyze-req rồi gen) hoặc Quick Mode (sinh nhanh trực tiếp từ spec).
skills:
  - rbt_manual_testing
  - testing_dimensions
  - component_checklist
  - jp_validation
---

Thực hiện **Section 4: Test Case Generation** từ skill `rbt_manual_testing`.

## Bước 0 — Kiểm tra `analysis.md` và dựng cấu trúc

Tên file theo "Quy ước file và version" (skill `rbt_manual_testing`; tên module = tên thư mục). Chạy `python3 -I .claude/scripts/module_files.py latest testing/[module] analysis` để lấy analysis mới nhất (`[module]-analysis-vN.md`, hoặc tên cũ `analysis.md` tính là v1). Mọi chỗ dưới đây viết `analysis.md` là tên gọi tắt của file này.

**File TC đích** (`testing/[module]/[module]-testcases-vN.md`):
- Có analysis vN → đích là `testcases-vN` (cùng N với analysis).
- Không có analysis (Quick) → đích là testcases mới nhất của module (`module_files.py latest testing/[module] testcases`), chưa có thì `testcases-v1`.
- Đích đã tồn tại → chỉ sinh lại hoặc sinh tiếp (giữ Function Name theo bảng hiện có), **không tạo version mới**. Spec đã đổi thì dùng `/update-tcs`, không dùng `/gen-tcs`.
- **Đích là bản Quick** (dòng đầu file là `> Mode: Quick`) mà lần này chạy Full (có analysis) → **dừng và hỏi** bằng `AskUserQuestion` trước khi ghi. Nêu rõ: file hiện tại là bản Quick, có bao nhiêu TC, Traceability `REQ-xx` sẽ đổi sang `AC-xx`, ghi đè không khôi phục được. Lựa chọn:
  1. `Ghi đè, chia Screen theo analysis (Recommended)`: dựng cấu trúc Screen theo analysis như Full thường.
  2. `Ghi đè, giữ cấu trúc Screen cũ`: giữ nguyên số sheet và tên sheet của bản Quick; chỉ đổi Traceability sang `AC-xx` và bổ sung TC theo analysis vào sheet phù hợp.
  3. `Dừng, không ghi`: không tạo hay sửa file nào.
  User chọn **Other** (gõ tự do): đọc nội dung; nói rõ ghi đè và cấu trúc nào (VD "ghi đè nhưng không đổi cấu trúc screen" = lựa chọn 2) thì làm theo; không rõ là ghi đè hay không, hoặc không rõ cấu trúc nào → hỏi lại một lần; vẫn không rõ → dừng, không ghi.
  Ở cả hai lựa chọn ghi đè: **giữ nguyên ID và Function Name** của TC cũ, TC bổ sung đánh số tiếp theo ID lớn nhất. Dòng `Mode: Quick` và các dòng `**Nguồn:**`, `**Platform:**`, `**Yêu cầu (REQ):**` bị bỏ khỏi file mới.
- Khi sinh TC mà phải bổ sung vào analysis (VD thêm ASM-xx, AC mới cho lỗ hổng spec chưa nêu): **sửa tại chỗ** file analysis hiện tại và thêm một dòng `History` dạng `- vN ([ngày]): /gen-tcs — [tóm tắt]` (N = số version của file, không dùng nhãn lẻ như `v1.1`). Không tạo version analysis mới.

Nếu module còn file `plan-tcs.md` (không dùng nữa), **bỏ qua, không đọc**.

**Chưa có `analysis.md`** → **không tự chạy**. Dùng `AskUserQuestion` hỏi user chọn chế độ (Full đặt đầu, ghi `(Recommended)`):

- Câu hỏi: `Module chưa có analysis.md, bạn muốn gen-tcs ở chế độ nào?`
- **Full mode** — phân tích requirement rồi gen TC (`/analyze-req` → sinh TC). Ưu: có Q&A chỉ ra điểm spec chưa cover, Traceability về AC, độ phủ chặt, ít TC đoán mò. Nhược: lâu hơn, token nhiều hơn; Summary, Q&A và Acceptance Criteria nằm ở đầu `analysis.md`; System Model nằm trong phần tham chiếu phía dưới để user đối chiếu khi cần.
- **Quick mode** — sinh nhanh TC trực tiếp từ spec. Ưu: nhanh, ít token, bộ TC gọn, hợp module nhỏ hoặc bản nháp. Nhược: không có Q&A nên điểm spec mơ hồ không bị phát hiện, Expected suy luận gắn `[ASSUMED]`, Traceability dùng REQ-xx thay AC-xx.

Chọn **Full** → thực hiện **Section 2: Requirement Analysis** (skill `rbt_manual_testing`), không dừng hỏi; `analysis.md` được lưu rồi tiếp tục luôn. Chọn **Quick** → làm theo mục **Quick Mode** (bên dưới phần "Sinh Test Case chi tiết"), bỏ qua Bước 0 còn lại và Bước 1.

**Không có lựa chọn của user** (không tương tác, user bỏ qua, hoặc trả lời không rõ chọn chế độ nào) → **dừng, không tự chọn chế độ, không tạo file nào**, in đúng một dòng: `Module chưa có analysis.md. Chạy lại /gen-tcs và chọn Full hoặc Quick.`

**Đã có `analysis.md`** → tiếp tục luôn, không chạy lại `/analyze-req`.

**Dựng cấu trúc test (Full mode):** theo **Section 3** của skill `rbt_manual_testing`, **không lưu thành file**. Gồm Screen, Component theo thứ tự, Component Type, Risk Level, Permission Matrix (chép đủ hàng của `analysis.md` + hàng "của người khác"), rule tương tác chéo, Assumption môi trường test, 3-6 luồng E2E. Cấu trúc này chỉ là khung để sinh TC trong lần chạy này; nếu khi sinh TC thấy cấu trúc sai hoặc thiếu so với `analysis.md` thì sửa luôn, ưu tiên `analysis.md`.

**Tóm tắt cấu trúc (in ở đầu output, không chờ user trả lời):**

```
📋 Cấu trúc: [N] Screen: [Screen 1] (suy luận từ spec / theo design), [Screen 2] ...
- Permission Matrix: [số hàng] hàng ([số ô ?] ô chưa rõ)
- Luồng E2E chính: [N] luồng — [tên luồng 1], [tên luồng 2] ...
- Phạm vi không test (nếu có): [điều không test] — [lý do, AC hoặc Q&A]
Nếu cấu trúc sai (VD chia Screen chưa đúng), báo lại cách chia mong muốn để sinh lại.
```

Chỉ có Screen suy luận từ text (không có design) → ghi rõ "suy luận từ spec" cho từng Screen để người dùng thấy ngay phần dễ sai nhất.

**Assumption môi trường test:** nếu có điều kiện hạ tầng/bên ngoài mà TC ngầm dựa vào, ghi một dòng blockquote ngay dưới tiêu đề file TC: `> **Assumption môi trường test:** ...` (không tạo heading `##`). Không có thì bỏ.

---

## Bước 1 — Kiểm tra TBD ACs (severity-gated)

**Nguồn đọc (Full):** `analysis.md` là nguồn chính; không đọc lại toàn bộ spec gốc. Chỉ tra đúng đoạn spec khi một mục trong analysis mơ hồ hoặc thiếu chi tiết. Analysis thiếu so với spec thì dừng, đề nghị chạy lại `/analyze-req` hoặc `/update-tcs`, không tự bù TC từ spec.

**Khi spec và analysis lệch nhau** (chỉ xét khi đã tra spec như trên):
- **Không tính là lệch** nếu analysis khác spec do quyết định đã ghi lại: Q&A đã trả lời, ASM đã chấp nhận, hoặc DIF đã chọn A/B. Ở các chỗ này analysis đúng, sinh TC bình thường.
- **Lệch nhỏ** (wording, label, định dạng hiển thị, không đổi hành vi hay Expected nghiệp vụ) → vẫn sinh TC theo analysis, gắn tag `[LỆCH SPEC]` ở đầu ô Expected Results, và ghi trong ô đó (hoặc Notes) 1 câu `Spec ghi: [...]`. Liệt kê thêm trong báo cáo cuối: `Spec lệch analysis (nhỏ): [điểm lệch]`.
- **Lệch lớn** (đổi Expected, luồng nghiệp vụ, điều kiện, phân quyền, số liệu) → **không sinh TC cho AC đó**, các AC khác vẫn sinh. Cuối lượt gom mọi chỗ lệch lớn thành **một lần hỏi duy nhất**: mỗi chỗ nêu AC, `Analysis ghi: ...`, `Spec ghi: ...`, để user chọn theo analysis hay theo spec (nếu theo spec thì đề nghị chạy `/update-tcs`). Sau khi user chọn thì sinh TC cho các AC đó.
- Không chắc lệch nhỏ hay lớn → coi là lớn.

Đọc analysis mới nhất (`testing/[module]/[module]-analysis-vN.md`), kiểm tra cột Status trong bảng Acceptance Criteria. Với mỗi AC status TBD, tra Severity của Q-MOD-XXX liên quan trong bảng Q&A — Cần quyết định (nếu không xác định được Q&A liên quan hoặc severity không rõ, coi như **High** để an toàn). AC phụ thuộc **DIF-XX** (bảng Lệch spec↔design) chưa được chọn A/B coi như mức **Low**. AC status `Assumed` (gắn ASM-XX) sinh TC bình thường, không cần tag `[UNCONFIRMED]` (Expected dựa trên ASM vẫn tag `[ASSUMED]` ở đầu ô Expected Results theo TC Gate).

**Không có AC nào status TBD** → tiếp tục bình thường.

**Có AC TBD nhưng Q&A liên quan chỉ ở mức Medium/Low** → sinh **đúng 1 TC đại diện cho mỗi AC** (happy path theo `Phương án đề xuất` của Q&A), tag `[UNCONFIRMED]` ở đầu Test Scenario. **Không** khai triển Decision Table/State Transition/Boundary Tier, negative hay edge case cho AC này — chỉ khai triển sau khi Q&A được trả lời và `analysis.md` cập nhật (chạy lại `/gen-tcs` cho AC đó). Không hỏi user.

> **Phạm vi của quy tắc TC đại diện:** chỉ áp dụng cho **phần hành vi mà Q&A chưa trả lời**. Kiểm tra cơ bản **không phụ thuộc** câu trả lời vẫn sinh bình thường theo Field-Level Validation / Component Checklist, kể cả khi field liên quan có AC TBD. Ví dụ Weight có AC TBD về đơn vị và khoảng giá trị (Q&A chưa trả lời): vẫn sinh TC Weight để trống, bằng 0, số âm, có chữ (sai với mọi phương án trả lời); chỉ riêng biên cụ thể (giá trị tối đa, đơn vị) mới thuộc 1 TC đại diện `[UNCONFIRMED]`. Tương tự, mặt "bắt buộc nhập" của mọi field trong AC Confirmed/Assumed (VD AC "tạo đơn với đủ field") phải có TC cho từng field, không bị gộp vào TC đại diện của AC TBD.

**Có AC TBD với Q&A liên quan ở mức High** (nghiệp vụ liên quan tiền/bảo mật/phân quyền) → **không dừng hỏi user**. Rủi ro càng cao càng phải phủ sâu, nên sinh đầy đủ **happy, negative, exception/edge** cho AC đó, tag `[UNCONFIRMED]` ở đầu Test Scenario và ghi mã Q&A vào Traceability ID (VD `AC-13, Q-LDM-005`) để lọc và sửa nhanh khi Q&A được trả lời. Cách sinh phụ thuộc loại "chưa trả lời":

| Loại | Dấu hiệu | Xử lý |
|---|---|---|
| **1 — Spec chưa chọn hành vi** | Q&A có `Phương án đề xuất` A/B rõ (VD ai nhập actual weight, ở bước nào) | Sinh đủ happy + negative + edge **theo phương án đề xuất**. Expected nêu hành vi của phương án đó, ghi rõ `theo đề xuất Q-XXX-NNN` ở Expected hoặc Test Data. Áp dụng Technique (Decision Table/State Transition/Boundary Tier) như AC Confirmed. |
| **2 — Spec thiếu giá trị / công thức** | Q&A hỏi về giá trị cụ thể không thể suy ra (đơn giá, bậc phí, ngưỡng, bảng ghép) | **Không tự đặt giá trị.** Chỉ sinh TC kiểm tra **quan hệ** không cần giá trị (VD Express Fee chỉ có khi Service Type là Express; phí tính lại khi actual weight lớn hơn registered; giữ nguyên khi nhỏ hơn hoặc bằng). Phần cần giá trị (biên bậc phí, tổng tiền cụ thể) **không sinh TC**. |

Cuối output (sau Self-check), thêm mục (ghi vào cuối `test-cases.md` dưới dạng blockquote ngay sau Bảng 2, **không tạo heading `##`**; `/export-xlsx` đưa phần này vào sheet `High Risk & E2E`; đồng thời nêu ngắn trong chat):

```
⚠️ AC High đang dựa trên giả định (nên PM trả lời trước khi chạy test):
- Q-XXX-NNN — AC-NN: [đã sinh X TC theo phương án đề xuất] / [chỉ sinh TC quan hệ]
Chưa sinh được vì thiếu giá trị từ PM:
- [Nội dung cần giá trị, VD biên bậc Weight Fee, tổng tiền Delivery Fee theo từng Service Type] (Q-XXX-NNN)
```

Khi Q&A được trả lời và `analysis.md` cập nhật: chạy lại `/gen-tcs` cho AC đó để bỏ tag `[UNCONFIRMED]`, sửa Expected theo câu trả lời và sinh phần còn thiếu.

> *Q&A mức Medium/Low vẫn chỉ sinh 1 TC đại diện mỗi AC (xem trên). Chỉ AC TBD mức High mới được phủ đầy đủ.*

---

## Sinh Test Case chi tiết

1. Dựng cấu trúc test theo **Section 3** (Bước 0) — Screen → Component → Component Type/Risk Level, **Permission Matrix** nếu có (mỗi ô ❌ phải có TC phủ, xem Pattern 1 trong skill), rule tương tác chéo, luồng E2E. Không lưu thành file; nếu file TC đã có thì giữ nguyên Screen và Function Name đang dùng (trừ khi đang nâng bản Quick lên Full và user chọn chia Screen theo analysis, xem Bước 0).
2. Đọc `analysis.md` — lấy nội dung AC/Q&A để viết Steps/Expected Result.
   - **Diagram (nếu có):** dòng link ngay đầu `analysis.md` (`> Sơ đồ để dễ hình dung ...`) trỏ tới `diagrams/[module]-state-vN.html` và/hoặc `[module]-flow-vN.html`. Có thì đọc thêm file `.json` cùng tên (lifecycle: `transitions[]`; workflow: `edges[]`) **chỉ để đối chiếu độ phủ** (xem tiêu chí D1). **Text của `analysis.md` là bản chính**: diagram không phải nguồn sinh TC riêng, không có AC/Q&A/ASM tương ứng thì không sinh TC chỉ vì có trong diagram; diagram lệch với text thì theo text. Không có link hoặc không đọc được JSON → bỏ qua, không báo lỗi.
3. Xác định platform: `analysis.md` Summary → nếu trống, `CLAUDE.md` → đọc `.claude/skills/testing_dimensions/SKILL.md` section tương ứng. **Cả hai trống (hoặc còn `[...]`) → hỏi user một lần** (Web / Mobile / Desktop...) trước khi sinh TC, không tự mặc định. Multi-language và tính năng đặc thù (push, offline...) suy ra từ spec/AC, không nhắc thì không áp, không hỏi. Xác định **Locale** cùng nguồn (`analysis.md` Summary → `CLAUDE.md`): nếu `Locale: JP` → đọc `.claude/skills/jp_validation/SKILL.md` và áp **cho mọi field nhập liệu**, không phụ thuộc spec có nhắc 全角/半角 hay không (spec có ghi lớp ký tự thì theo spec, không thì dùng bảng mặc định theo loại field, tag `[ASSUMED]`).
4. Với mỗi Screen trong cấu trúc đã dựng (theo đúng thứ tự):
   - Sinh **đúng 1 TC UI** cho Screen đó (đặt đầu bảng): `Check giao diện màn hình [tên Screen] thống nhất với design`, Expected Results = đúng một dòng `UI thống nhất với design` (không thêm tên frame, không mô tả chi tiết; chưa có design vẫn ghi như vậy). Theo "UI Policy" trong skill `rbt_manual_testing`.
   - Với mỗi Component (theo đúng thứ tự trong cấu trúc):
     - Nhận diện pattern từ AC → dựng đầy đủ Decision Table/State Transition/Boundary Tier tương ứng (tham chiếu sub-section "Complex Logic Patterns" trong skill `rbt_manual_testing`), show inline trước khi expand ra TC. Ngưỡng nghiệp vụ (giới hạn số lượng, thời gian chờ, số lần thử) cũng áp Boundary Tier và phải có TC cả hai phía của ngưỡng (Pattern 3).
     - **Không** sinh TC visual theo state/component. Popup/dialog/toast/submenu hiện sau action → verify trong Expected Result của TC action đó. Thuộc tính UI chỉ có TC riêng khi là giá trị nghiệp vụ (màu/label theo status, format theo spec) — xem "UI Policy".
     - Nếu là input field: sinh **Field-Level Validation TCs riêng cho từng trường** (Bảng Field-Level Validation trong skill) — không gộp nhiều field vào 1 TC. Nếu `Locale: JP`: sinh theo **Bộ khung TC cho mỗi field text** trong `jp_validation` (thay cho phần ký tự/độ dài của bảng Field-Level, không sinh trùng).
     - Áp **Component Checklist** từ `.claude/skills/component_checklist/SKILL.md` theo **Component Type** đã xác định ở Section 3 — tra trực tiếp Section A/B/C, không đoán qua keyword AC text.
     - Nếu component phụ thuộc hoặc ảnh hưởng component khác trên cùng Screen: sinh thêm TC cho tương tác cross-component đó (gắn vào Logic của component này).
5. Áp dụng kỹ thuật thiết kế phù hợp: Equivalence Partitioning (EP) kết hợp Boundary Value Analysis (BVA) theo **Pattern 4** trong skill `rbt_manual_testing` cho mọi field có giới hạn độ dài/giá trị (dựng bảng lớp và giá trị inline trước khi sinh TC). Khi expand ra TC, tuân thủ **"Quy tắc gộp TC"** trong skill `rbt_manual_testing`: TC cùng Steps chỉ khác data và cùng loại kết quả → gộp 1 TC nhiều dòng Test Data; Boundary chỉ lấy giá trị sát biên mỗi phía.
6. Áp dụng Platform Dimensions từ `.claude/skills/testing_dimensions/SKILL.md` **một lần cho cả module** (sau khi sinh xong tất cả Screen), gom vào nhóm Function Name `Platform – [tên platform]`, **đặt ở cuối bảng của Screen cuối cùng, không tạo heading `##` riêng** (heading riêng sẽ thành một sheet thừa khi export), ID nối tiếp, mỗi dimension tối đa 1 TC đại diện, chỉ chọn dimension module thật sự có rủi ro. Không lặp theo Screen/Component.
7. Tuân thủ **Rule ngôn ngữ Test Scenario** (xem sub-section bên dưới).
8. Mỗi **Screen điều hướng chính** (List, Detail...) là 1 heading `## [tên Screen]` duy nhất, với **một bảng TC** ngay bên dưới — `/export-xlsx` dựa vào heading `##` để tách sheet. Popup/dialog/submenu thuộc Screen nào thì TC nằm trong bảng của Screen đó (phân biệt bằng cột Function Name), **không** tạo heading riêng. Không tạo heading theo nhóm tính năng hay theo lượt sinh; ID đánh số liên tục trong toàn module.
9. Sau khi sinh xong tất cả Screen, Platform Dimensions, sinh mục **`## High Risk & E2E`** ở cuối file theo "Mục High Risk & E2E" trong skill `rbt_manual_testing`: **Bảng 1** nhóm TC high risk cần ưu tiên chạy (suy ra từ Risk Level đã xác định, ô ❌ Permission Matrix, Q&A High, trạng thái không đảo ngược, toàn vẹn dữ liệu) và **Bảng 2** test E2E cần đảm bảo work trước (lấy từ các luồng E2E chính đã dựng, chỉ tham chiếu TC có sẵn). Hai bảng luôn được sinh lại sau mỗi lần sinh hoặc sinh lại TC của bất kỳ Screen nào (vì ID có thể đổi).
10. Lưu output ra file TC đích đã xác định ở Bước 0 (`testing/[module]/[module]-testcases-vN.md`).
11. **Export tự động:** sau khi lưu file md, nếu `[module]-testcases-vN.xlsx` **chưa tồn tại** thì chạy luôn `python3 .claude/scripts/md_to_xlsx.py <file md> <web|app>` để có xlsx cùng tên. Chọn template theo Platform: Summary của analysis (Full) → dòng `**Platform:**` đầu file (Quick) → `CLAUDE.md`; có chữ Web thì `web`; App, Mobile, iOS hoặc Android thì `app`; không rõ hoặc nhiều nền tảng thì hỏi user một lần. Xlsx đích **đã tồn tại** (có thể chứa kết quả test) → **không chạy, không hỏi**, chỉ in một dòng `xlsx đã tồn tại, chưa ghi đè: <đường dẫn> (chạy /export-xlsx nếu muốn xuất lại)`. Nêu đường dẫn xlsx trong báo cáo cuối.

> Nếu nhiều Screen, sinh từng Screen một theo đúng thứ tự đã dựng, hỏi user để tiếp tục. Nếu một Screen quá lớn phải sinh nhiều lượt, các lượt sau **nối tiếp vào cùng bảng/heading** của Screen đó. Sinh lại hoặc sinh tiếp một Screen đã có trong `test-cases.md`: lấy Function Name từ bảng hiện có để tên không đổi giữa các lần chạy.

---

## Quick Mode

Chỉ vào đây khi module chưa có `analysis.md` **và** user chọn Quick ở Bước 0. Không chạy `/analyze-req`, không có Question Gate/Q&A, bỏ Bước 1 (không có AC TBD). Đánh đổi: spec mơ hồ không được phát hiện, nên Expected dựa trên suy luận phải tag `[ASSUMED]`.

**Đầu vào:** spec/requirement của module (Backlog, Drive, Docs, .md, Figma) cộng `CLAUDE.md`. Chưa có spec nào để đọc → dừng và hỏi user spec ở đâu.

**Trước khi ghi file:** nếu file TC đích đã tồn tại, hỏi user xác nhận ghi đè (nêu rõ file hiện tại là bản Full hay Quick theo dòng `Mode:` ở đầu file; bản Full thì cảnh báo mạnh hơn). Không đồng ý → dừng, không ghi.

**Cách sinh:**
1. Đọc spec, xác định platform và Locale (nguồn: spec → `CLAUDE.md`). `Locale: JP` → áp `jp_validation` cho mọi field nhập liệu như Full.
2. Rút danh sách yêu cầu từ spec, đánh mã `REQ-01`, `REQ-02`... theo thứ tự xuất hiện (dùng ở cột Traceability ID thay AC-xx). Giả định tự đặt chỉ cần tag `[ASSUMED]` ở đầu ô Expected Results; **không đánh mã `ASM-xx`** (bản Quick không có bảng Assumptions để tra mã).
3. **Chỉ 1 sheet TC cho cả module**: toàn bộ TC nằm trong **một** heading `## [tên sheet]` với một bảng TC duy nhất (tên sheet là tên tính năng đọc được, lấy theo spec, viết tiếng Việt nếu spec tiếng Việt, tối đa 31 ký tự; **không** dùng tên thư mục module) (không tách heading theo nhóm tính năng hay theo frame, vì `/export-xlsx` tách sheet theo heading `##`). Phân biệt các nhóm tính năng/popup/dialog bằng cột Function Name; ID đánh số liên tục. Mục `## High Risk & E2E` vẫn là sheet riêng (bước 6). Spec có phân quyền thì mỗi ô bị cấm vẫn phải có ≥1 TC.
4. Với mỗi nhóm áp **cùng bộ luật như Full**: Field-Level Validation riêng từng field, `component_checklist` (tự nhận Component Type từ spec), EP/BVA theo Pattern 4, "Quy tắc gộp TC", UI Policy (1 TC UI cho mỗi nhóm có màn hình), Platform Dimensions một lần cho cả module, "Rule ngôn ngữ Test Scenario" và TC Gate. Technique (Decision Table/State Transition/Boundary Tier) **không** sinh TC riêng cho từng hàng, mà gộp thành nhiều dòng Test Data trong TC.
5. Spec im lặng hoặc mơ hồ → **không đoán Expected**: theo TC Gate, bỏ TC đó và ghi vào mục "Hành vi spec chưa nêu" cuối output.
6. Cuối file vẫn có `## High Risk & E2E` (Bảng 1, Bảng 2) theo skill `rbt_manual_testing`: Bảng 1 suy từ yêu cầu về tiền/bảo mật/phân quyền/dữ liệu không đảo ngược trong spec; Bảng 2 từ các luồng chính trong spec (3-6 luồng).
7. Chạy Self-Check như Full, **trừ** các tiêu chí cần file không tồn tại: C1 đối chiếu REQ-xx thay AC, S1 và P1(a) không áp dụng, I1 không áp dụng, Q2 chỉ đối chiếu các yêu cầu rủi ro cao rút từ spec.

**Dòng đầu file TC (bắt buộc):**

```
> Mode: Quick — chưa qua /analyze-req; Traceability dùng REQ-xx; Expected tag [ASSUMED] là suy luận, chưa PM/BA xác nhận.
```

Ngay sau dòng đó và tiêu đề `# Test Cases: ...`, ghi thêm các dòng sau (`/review-tcs` đọc để đối chiếu; không vào xlsx):

```
**Nguồn:** `[đường dẫn hoặc link spec]`

**Platform:** [Web | App | ...]

**Yêu cầu (REQ):** REQ-01 [tên yêu cầu] · REQ-02 [tên yêu cầu] · ...
```

Dòng `**Yêu cầu (REQ):**` liệt kê đủ mọi mã `REQ-xx` đã dùng ở cột Traceability ID, mỗi mã kèm tên yêu cầu ngắn, để người đọc biết `REQ-xx` là gì mà không cần mở spec.

**Export tự động:** sau khi lưu file, làm đúng "Export tự động" ở bước 11 của phần Full (Platform lấy từ dòng `**Platform:**` đầu file).

**Cuối output, in thêm:**

```
⚠️ Bản Quick, chưa qua analyze-req: chưa có Q&A để phát hiện điểm spec mơ hồ. Module rủi ro cao (tiền/bảo mật/phân quyền) nên chạy /analyze-req rồi /gen-tcs (Full).
```

Muốn nâng lên Full: chạy `/analyze-req` rồi `/gen-tcs` (có `analysis.md` thì chạy thẳng, ghi đè bản Quick sau khi user xác nhận).

---

## TC Gate (cho TC sinh từ Checklist, Field-Level, Dimensions, Technique)

Mỗi TC ứng viên phải qua 2 cổng trước khi vào bảng. Cổng này lọc TC "sinh theo loại component" mà không có căn cứ hoặc Expected không đo được.

| Cổng | Câu hỏi | Nếu không đạt |
|---|---|---|
| **G1 — Nguồn** | TC có ít nhất một nguồn hợp lệ không? Nguồn hợp lệ: AC/Q&A/design trong `analysis.md`; ASM-XX đã ghi; Business Rules trong `CLAUDE.md`; hoặc **bộ chuẩn của kit** có Expected không cần spec (Field-Level cơ bản như bắt buộc nhập, không thực thi script/SQL, double-submit không tạo 2 bản ghi; `jp_validation` khi Locale = JP) | Không sinh TC |
| **G2 — Expected đo được** | Nêu được kết quả cụ thể, quan sát được (message, state, giá trị hiển thị) không? | Không sinh TC |

- Expected dựa trên **bộ chuẩn của kit** hoặc **ASM** (không có câu chữ trong spec) → tag `[ASSUMED]` **ở đầu ô Expected Results** (một lần cho cả TC, không đặt trong Test Scenario để Scenario luôn bắt đầu bằng "Check"; `[UNCONFIRMED]` vẫn đặt ở đầu Test Scenario). Không gắn `[ASSUMED]` khi Expected có câu chữ trong spec/AC/Q&A để đối chiếu.
- Expected đã sinh theo analysis nhưng spec ghi khác ở điểm lệch nhỏ (xem Bước 1, "Khi spec và analysis lệch nhau") → tag `[LỆCH SPEC]` ở đầu ô Expected Results, kèm `Spec ghi: [...]`. Nếu TC đồng thời cần `[ASSUMED]` thì đặt cả hai, `[LỆCH SPEC]` đứng trước.
- **Bộ chuẩn Field-Level luôn áp dụng** cho mọi field nhập liệu, kể cả khi AC của field đó TBD: bắt buộc nhập, **chỉ khoảng trắng**, ký tự đặc biệt/script/SQL, và với field ngày thì **ngày không tồn tại** (VD 31/02) — theo Bảng Field-Level Validation trong skill. Không được đưa các mục này vào mục "Hành vi spec chưa nêu"; chỉ phần cần giá trị từ spec (độ dài tối đa, định dạng hiển thị, đơn vị) mới ghi vào đó.
- Dòng checklist ghi "(theo spec)" mà spec im lặng và không có nguồn G1 → **không sinh TC**, không đoán Expected. Ghi vào mục cuối output (xem dưới) để QC hỏi PM/BA hoặc bổ sung `analysis.md`.
- Không dùng Gate để loại TC của AC đã Confirmed/Assumed hoặc ô ❌ Permission Matrix.

Mục cuối output (cùng chỗ và cùng cách ghi với cảnh báo AC High), chỉ in khi có mục để liệt kê:

```
ℹ️ Hành vi spec chưa nêu, chưa sinh TC (cần PM/BA hoặc bổ sung analysis.md):
- [Component/dòng checklist]: [hành vi chưa rõ] (VD "Weight Fee tính tròn lên hay làm tròn xuống")
```

## Rule ngôn ngữ Test Scenario

- Luôn bắt đầu bằng **"Check"**, theo sau là **câu tự nhiên hoàn chỉnh, đọc như người nói** — không phải cụm từ khóa rút gọn. Tag `[UNCONFIRMED]` (nếu có) đứng ngay trước chữ "Check" (`[UNCONFIRMED] Check ...`) và không tính là vi phạm.
- **Cấm:** ký hiệu mũi tên (`→`, `->`), gạch chéo nén ý thay cho "hoặc" (VD `A/B`), dấu hai chấm nén nhiều ý (VD `Login: email sai`), viết tắt không giải thích.
- Ví dụ:
  - ❌ Sai: `Login → Dashboard (email/pass hợp lệ)`
  - ✅ Đúng: `Check đăng nhập thành công với email và password hợp lệ`

---

## Self-Check trước khi lưu file

Sau khi draft xong toàn bộ TCs, thực hiện quick pass **trước khi lưu ra file**. Không hỏi user — tự phát hiện và tự fix.

### Checklist (theo thứ tự ưu tiên)

| # | Tiêu chí | Cách check |
|---|----------|-----------|
| C1 | **AC Coverage theo vế** — tách mỗi AC thành các vế (xem "Vế của AC và điều kiện Covered" trong skill `rbt_manual_testing`); mỗi vế có ≥1 TC positive mà Steps thực hiện vế đó và Expected kiểm chứng vế đó. Nhiều TC có thể cùng phủ một AC | Liệt kê vế của từng AC, dò cột Traceability ID, đọc Steps và Expected của từng vế. Vế chỉ có Steps mà Expected không kiểm → bổ sung Expected hoặc thêm TC |
| C2 | **Test Data cụ thể khi có ghi** — không có placeholder (chỉ áp cho ô đã ghi; ô không cần thì để trống) | Grep "email hợp lệ", "số điện thoại đúng", "nhập đúng", "bất kỳ" trong cột Test Data |
| C3 | **Expected Result đo được** — không mơ hồ | Grep "hiển thị đúng", "load nhanh", "thành công", "phản hồi nhanh" trong cột Expected Results. "Hiển thị đúng" chỉ được chấp nhận khi nêu rõ đối tượng và đối chiếu được với Test Data hoặc Steps (VD "Hiển thị đúng dữ liệu đã nhập như Test Data"); dạng trơn ("hiển thị đúng", "hiển thị đúng thông tin") thì viết lại |
| M1 | **TC Independence** — không TC nào refer đến TC khác; các TC dùng cùng giá trị định danh trong Test Data mà cần trạng thái khác nhau thì tách dữ liệu hoặc ghi bước chuẩn bị trong Precondition, để chạy liên tiếp không làm lệch nhau | Grep mã module của chính file (VD `APB-\d{3}`, lấy từ tiền tố cột ID) cùng "xem TC", "kết quả bước trước" trong cột Steps/Precondition; nhóm TC theo giá trị Test Data trùng nhau và so trạng thái yêu cầu |
| M2 | **Negative Coverage** — mỗi happy path AC có ≥1 TC negative (**trừ** AC `[UNCONFIRMED]` mức Medium/Low chỉ có 1 TC đại diện; AC High vẫn phải có negative) | Gom TC theo Traceability ID; TC là **negative** khi Expected báo lỗi, từ chối, chặn hoặc không thực hiện được hành động (hoặc Category `Negative`/`Security`). Không đếm theo Category vì TC mức component chỉ có UI/Validate/Behavior/Logic |
| E1 | **Bảng EP/BVA/Decision Table phủ đủ** — mọi dòng của bảng lớp EP, giá trị BVA và Decision Table đã dựng inline (Bước 4 và 5) có ≥1 TC hoặc ≥1 dòng Test Data (theo "Quy tắc gộp TC") | Đối chiếu từng dòng của các bảng inline với bảng TC |
| O1 | **Một TC một mục tiêu** — Expected chỉ gồm kết quả của một hành vi chính (nhiều kết quả cùng một hành vi thì được, VD báo lỗi và không lưu dữ liệu); Test Scenario không nối hai hành vi bằng "và"; nhiều dòng Test Data cùng Steps vẫn là một mục tiêu | Đọc Test Scenario và Expected của từng TC |
| Q1 | **ID trong mục High Risk & E2E còn tồn tại** — mọi ID ở Bảng 1 và Bảng 2 có trong bảng TC; ID không bị lặp ở Bảng 1 | Đối chiếu từng ID với cột ID của bảng TC |
| Q2 | **Bảng 1 phủ rủi ro** — gồm mọi ô ❌ của Permission Matrix, mọi TC của AC High, và không vượt khoảng 30% tổng số TC | Đối chiếu Permission Matrix, bảng AC (Status/Q&A High) với cột TC của Bảng 1 |
| Q3 | **Bảng 2 phủ luồng chính** — có 3-6 luồng E2E (luồng chính trước, mỗi nhánh có ý nghĩa nghiệp vụ một luồng), mỗi bước có TC hoặc ghi `thiếu TC`, có cột "Nếu fail thì" | Đối chiếu các luồng E2E đã dựng ở Bước 0 với Bảng 2 |
| D1 | **Diagram phủ chuyển trạng thái và luồng** — mỗi `transitions[]` của lifecycle và mỗi `edges[]` có nhãn của workflow trong diagram (bước 2) có ≥1 TC phủ (qua AC/Q&A/ASM tương ứng trong text); chuyển trạng thái đi tới trạng thái cuối hoặc đường lùi cũng phải có TC. Phần trong diagram mà text không nêu → **không sinh TC**, ghi 1 dòng ở báo cáo cuối: `Diagram lệch text: [chuyển trạng thái/cạnh] — kiểm tra lại analysis.md hoặc diagram` (chỉ check khi module có diagram) | Liệt kê `id`/`label` của transitions và edges, đối chiếu với Steps/Expected của TC |
| L1 | **Ngôn ngữ TS** — không còn ký hiệu rút gọn | Grep `→`, `->`, dấu `:` nén ý trong cột Test Scenario |
| S1 | **Cấu trúc nhất quán với analysis** — Screen khớp Screen Inventory của `analysis.md` (nếu có); mọi hàng ma trận của `analysis.md` có trong Permission Matrix đã dựng (xem P1a); mọi Screen/Component có TC; phạm vi "không test" nếu có chỉ dựa trên căn cứ cụ thể trong `analysis.md` và không loại bộ chuẩn Field-Level, ô ❌ Permission Matrix, TC của AC High | Đối chiếu cấu trúc với `analysis.md` và tóm tắt in ở đầu output |
| L3 | **Precondition và Test Data chỉ khi cần** — Precondition để trống nếu Steps tự đủ; không có "đăng nhập", email/tài khoản, tên định danh (`Hospital A`, `M1`); mỗi điều kiện một dòng, ngắn, tham chiếu `như Test Data` khi đã có dữ liệu cụ thể. Test Data không chứa email/tài khoản, không chứa mô tả trạng thái (thuộc Precondition), không ghi `—` | Rà hai cột: grep `@`, `đăng nhập`, `Đăng nhập`, `—`; Test Data có dòng `Trạng thái:` thì chuyển sang Precondition; TC UI/mở màn hình không cần Precondition |
| L2 | **Test Data một field một dòng** — không nối nhiều field bằng `;` hoặc `,` trên một dòng | Rà cột Test Data: mỗi field/giá trị phải nằm sau `<br>` riêng (xem "Trình bày cột Test Data" trong skill) |
| P1 | **Permission Coverage** — (a) mỗi hàng ma trận Actor × Action trong `analysis.md` có mặt trong Permission Matrix đã dựng; (b) mỗi ô ❌ — kể cả hàng sở hữu `[Action] — của người khác` — có ≥1 dòng Test Data trong một TC; (c) ô ? có Q&A thì **luôn** có 1 TC `[UNCONFIRMED]` (kể cả khi Q&A chỉ hỏi hành vi gần kề, xem Pattern 1 trong skill; chỉ khi ô ? không có Q&A nào liên quan mới không sinh) (chỉ check khi module có phân quyền) | Đối chiếu ma trận `analysis.md` → cột Test Data/Steps của TC Security/Negative |

> Mã C1-C3/M1-M2 dùng chung với `/review-tcs` (Q1-Q3 tương ứng M4 của `/review-tcs`) (M3 — Boundary Completeness — chỉ có ở `/review-tcs`, không check ở đây vì cần đối chiếu sâu constraint trong AC). L1, L2, L3, P1, S1 và Q1-Q3 là tiêu chí riêng của self-check lúc sinh TC, không có ở `/review-tcs`.

### Checklist rà thừa/trùng (chạy SAU khi các tiêu chí trên đã bổ sung đủ)

Các tiêu chí trên chỉ thêm TC. Bước này kiểm tra chiều ngược lại: bộ TC có TC nào thừa hoặc trùng không.

| # | Tiêu chí | Cách check | Xử lý |
|---|----------|-----------|-------|
| R1 | **Trùng rule** — hai TC cùng Function Name (hoặc cùng AC) có Steps giống nhau, chỉ khác data hoặc tên đối tượng, cùng loại kết quả | Nhóm TC theo Function Name/Traceability ID, so Steps và Expected | Gộp thành 1 TC nhiều dòng Test Data (VD Retry lần 1 và lần 2; hủy đơn ở Waiting và ở Assigned) |
| R2 | **Trùng giữa các tầng** — cùng một kịch bản do nhiều tầng sinh (Field-Level, Component Checklist, Testing Dimensions, Technique) | Tìm TC có Steps/Expected tương đương nhưng khác Category hoặc khác nguồn | Giữ 1 TC ở nơi sở hữu (Field-Level cho ký tự/độ dài; Checklist cho hành vi component; Dimensions cho nền tảng), xoá bản còn lại |
| R3 | **Bỏ TC này, bug nào lọt?** — với mỗi TC, thử trả lời bằng một lỗi cụ thể mà chỉ TC này phát hiện được | Rà từng TC; TC mà Expected đã được verify trong Expected của TC khác, hoặc không nêu được lỗi nào chỉ nó bắt được | Xoá hoặc gộp vào TC đã verify nội dung đó |
| R4 | **TC không qua TC Gate** — Traceability ID là `N/A` mà không phải TC UI/Platform/bộ chuẩn rõ ràng, hoặc Expected không đo được | Grep `N/A` trong cột Traceability ID; rà cột Expected Results | Gắn nguồn (AC/Q&A/ASM) hoặc xoá; Expected dựa mặc định thì tag `[ASSUMED]` |

**Không được gộp hay xoá khi:**
- TC phủ một ô ❌ của Permission Matrix, hoặc là dòng sở hữu `[Action] — của người khác` (chỉ được gộp thành dòng Test Data trong cùng action, xem P1).
- TC thuộc AC Risk High hoặc gắn Q&A riêng.
- Hai TC thuộc **hai field khác nhau** (mỗi field giữ TC validation riêng, kể cả khi rule giống nhau).
- Kết quả hoặc side-effect của hai TC khác nhau.

**Sau khi gộp/xoá:** chạy lại C1 (theo vế), M2, P1, E1 để chắc chắn không làm mất độ phủ AC, negative hay ô ❌.

### Khi phát hiện issue: tự fix luôn, ghi nhận để báo cáo.

### Summary format (hiển thị sau khi lưu file)

```
✅ Self-check hoàn thành. Đã fix: [X] issues.
- C1: Thêm TC cho AC-03 (thiếu positive case)
- C2: Cập nhật test data TC-007, TC-012 (thay placeholder bằng giá trị cụ thể)
- M2: Thêm TC negative cho AC-05
- L1: Viết lại Test Scenario TC-014 sang câu tự nhiên
- R1: Gộp TC-027 và TC-028 (Retry lần 1, lần 2) thành 1 TC 2 dòng Test Data
- R3: Xoá TC-052 (Expected đã nằm trong TC-030)

File đã lưu tại testing/[module]/[module]-testcases-vN.md
```

Nếu không phát hiện issue nào: `✅ Self-check: 0 issues. File đã lưu tại testing/[module]/[module]-testcases-vN.md`

---

## Output

`testing/[module]/[module]-testcases-vN.md`

Bảng TC format: `ID | Function Name | Category | Traceability ID | Test Scenario | Precondition | Steps | Expected Results | Test Data` — **không có** cột Risk Level và Priority; ưu tiên chạy nằm ở mục `## High Risk & E2E` (xem bên dưới).

- **Function Name:** Component đã dựng ở Section 3, đặt tên theo **quy ước cố định** trong "Output Format" của skill `rbt_manual_testing` (field nhập liệu dùng tên field đúng như spec, không hậu tố "field"; `[Tên] button`, `[Tên] dialog`, `[Tên] table`; `Màn hình [Screen]`; `Permission – [Action]`; `Notification – [sự kiện]`; `Platform – [platform]`). Nếu TC ở mức flow (không gắn 1 component cụ thể), dùng tên flow (VD "Login Flow").
- **Category:** cấp con dưới Function Name — "UI"/"Validate"/"Behavior"/"Logic" (component-level) hoặc "Happy Path"/"Negative"/"Security" (flow-level).
- **Traceability ID:** AC tương ứng từ `analysis.md` (VD `AC-05`), hoặc Q&A ID (VD `Q-LOG-001`), hoặc `N/A` nếu không có nguồn rõ ràng — tên cột dùng chung cho mọi loại ID team quy ước để trace ngược, không giới hạn chỉ AC.

> Khi export ra `.xlsx` qua `/export-xlsx`: Sheet name = tên Screen (heading `##` trong `test-cases.md`).
>
> Khi requirements thay đổi sau khi đã có file TC: chạy `/update-tcs` (tạo version mới, giữ TC không đổi). Chỉ dùng `/gen-tcs` sinh lại một Screen khi **spec không đổi** mà muốn viết lại TC (Function Name lấy từ bảng hiện có).
