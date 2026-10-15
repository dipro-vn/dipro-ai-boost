---
description: Sinh Test Case chi tiết (bao gồm Test Scenario) từ plan-tcs.md + analysis.md. Nếu module chưa có cả 2 file này, hỏi user chọn Full Mode (chain /analyze-req → /plan-tcs → gen) hoặc Quick Mode (sinh nhanh trực tiếp từ spec). Thiếu 1 trong 2 file thì tự chạy bước còn thiếu (chỉ dừng ở checkpoint Summary + System Model của analyze-req; plan chạy không dừng).
skills:
  - rbt_manual_testing
  - testing_dimensions
  - component_checklist
  - jp_validation
---

Thực hiện **Section 4: Test Case Generation** từ skill `rbt_manual_testing`.

## Bước 0 — Kiểm tra `analysis.md` và `plan-tcs.md`

Kiểm tra `testing/[module]/analysis.md` và `testing/[module]/plan-tcs.md` có tồn tại không:

**Thiếu cả 2** → **không tự chạy**. Dùng `AskUserQuestion` hỏi user chọn chế độ (Full đặt đầu, ghi `(Recommended)`):

- Câu hỏi: `Module chưa có analysis.md/plan-tcs.md, bạn muốn gen-tcs ở chế độ nào?`
- **Full mode** — chạy full luồng từ phân tích requirement đến gen TC (`/analyze-req` → `/plan-tcs` → sinh TC). Ưu: có Q&A chỉ ra điểm spec chưa cover, Traceability về AC, độ phủ chặt, ít TC đoán mò. Nhược: lâu hơn, token nhiều hơn, có checkpoint dừng để confirm Summary + System Model.
- **Quick mode** — sinh nhanh TC trực tiếp từ spec. Ưu: nhanh, ít token, bộ TC gọn, hợp module nhỏ hoặc bản nháp. Nhược: không có Q&A nên điểm spec mơ hồ không bị phát hiện, Expected suy luận gắn `[ASSUMED]`, Traceability dùng REQ-xx thay AC-xx.

Chọn **Full** → tiếp tục theo luồng "Thiếu 1 trong 2" bên dưới (chạy tuần tự `/analyze-req` → `/plan-tcs` → Bước 1). Chọn **Quick** → làm theo mục **Quick Mode** (bên dưới phần "Sinh Test Case chi tiết"), bỏ qua Bước 0 còn lại và Bước 1.

**Không có lựa chọn của user** (không tương tác, user bỏ qua, hoặc trả lời không rõ chọn chế độ nào) → **dừng, không tự chọn chế độ, không tạo file nào**, in đúng một dòng: `Module chưa có analysis.md/plan-tcs.md. Chạy lại /gen-tcs và chọn Full hoặc Quick.`

**Thiếu 1 trong 2** → thông báo ngắn rồi **tự động chạy tuần tự** các bước còn thiếu — không cần hỏi user có muốn chạy không, vì đây là bước bắt buộc để thực hiện đúng yêu cầu user vừa đưa ra:

> ℹ️ Module này chưa có `analysis.md`/`plan-tcs.md`. Tôi sẽ tự chạy `/analyze-req` → `/plan-tcs` trước, sau đó tiếp tục `/gen-tcs`.

- Thiếu `analysis.md` → thực hiện **Section 2: Requirement Analysis** (skill `rbt_manual_testing`) — vẫn dừng đúng tại checkpoint Summary + System Model confirm như khi chạy `/analyze-req` độc lập.
- Sau khi có `analysis.md` (vừa tạo hoặc đã có sẵn) mà thiếu `plan-tcs.md` → thực hiện **Section 3: TC Implementation Plan**, lưu `plan-tcs.md` và **không dừng hỏi** (không có checkpoint "Bạn muốn điều chỉnh gì không?").
- Ngay sau đó tiếp tục Bước 1 bên dưới. Đầu output in **tóm tắt plan không chặn** (xem bên dưới).

**Có sẵn cả 2** → tiếp tục Bước 1 luôn, không chạy lại.

**Tóm tắt plan (in ở đầu output, không chờ user trả lời):**

```
📋 Plan: [N] Screen: [Screen 1] (suy luận từ spec / theo design), [Screen 2] ...
- Permission Matrix: [số hàng] hàng ([số ô ?] ô chưa rõ)
- Luồng E2E chính: [N] luồng — [tên luồng 1], [tên luồng 2] ...
Nếu cấu trúc sai, dừng lại và chạy `/plan-tcs` để chỉnh `plan-tcs.md` trước.
```

Plan chỉ có Screen suy luận từ text (không có design) → ghi rõ "suy luận từ spec" cho từng Screen để người dùng thấy ngay phần dễ sai nhất.

---

## Bước 1 — Kiểm tra TBD ACs (severity-gated)

Đọc `testing/[module]/analysis.md`, kiểm tra cột Status trong bảng Acceptance Criteria. Với mỗi AC status TBD, tra Severity của Q-MOD-XXX liên quan trong bảng Q&A — Cần quyết định (nếu không xác định được Q&A liên quan hoặc severity không rõ, coi như **High** để an toàn). AC phụ thuộc **DIF-XX** (bảng Lệch spec↔design) chưa được chọn A/B coi như mức **Low**. AC status `Assumed` (gắn ASM-XX) sinh TC bình thường, không cần tag.

**Không có AC nào status TBD** → tiếp tục bình thường.

**Có AC TBD nhưng Q&A liên quan chỉ ở mức Medium/Low** → sinh **đúng 1 TC đại diện cho mỗi AC** (happy path theo `Phương án đề xuất` của Q&A), tag `[UNCONFIRMED]` ở đầu Test Scenario. **Không** khai triển Decision Table/State Transition/Boundary Tier, negative hay edge case cho AC này — chỉ khai triển sau khi Q&A được trả lời và `analysis.md` cập nhật (chạy lại `/gen-tcs` cho AC đó). Không hỏi user.

> **Phạm vi của quy tắc TC đại diện:** chỉ áp dụng cho **phần hành vi mà Q&A chưa trả lời**. Kiểm tra cơ bản **không phụ thuộc** câu trả lời vẫn sinh bình thường theo Field-Level Validation / Component Checklist, kể cả khi field liên quan có AC TBD. Ví dụ Weight có AC TBD về đơn vị và khoảng giá trị (Q&A chưa trả lời): vẫn sinh TC Weight để trống, bằng 0, số âm, có chữ (sai với mọi phương án trả lời); chỉ riêng biên cụ thể (giá trị tối đa, đơn vị) mới thuộc 1 TC đại diện `[UNCONFIRMED]`. Tương tự, mặt "bắt buộc nhập" của mọi field trong AC Confirmed/Assumed (VD AC "tạo đơn với đủ field") phải có TC cho từng field, không bị gộp vào TC đại diện của AC TBD.

**Có AC TBD với Q&A liên quan ở mức High** (nghiệp vụ liên quan tiền/bảo mật/phân quyền) → **không dừng hỏi user**. Rủi ro càng cao càng phải phủ sâu, nên sinh đầy đủ **happy, negative, exception/edge** cho AC đó, tag `[UNCONFIRMED]` ở đầu Test Scenario và ghi mã Q&A vào Traceability ID (VD `AC-13, Q-LDM-005`) để lọc và sửa nhanh khi Q&A được trả lời. Cách sinh phụ thuộc loại "chưa trả lời":

| Loại | Dấu hiệu | Xử lý |
|---|---|---|
| **1 — Spec chưa chọn hành vi** | Q&A có `Phương án đề xuất` A/B rõ (VD ai nhập actual weight, ở bước nào) | Sinh đủ happy + negative + edge **theo phương án đề xuất**. Expected nêu hành vi của phương án đó, ghi rõ `theo đề xuất Q-XXX-NNN` ở Expected hoặc Test Data. Áp dụng Technique (Decision Table/State Transition/Boundary Tier) như AC Confirmed. |
| **2 — Spec thiếu giá trị / công thức** | Q&A hỏi về giá trị cụ thể không thể suy ra (đơn giá, bậc phí, ngưỡng, bảng ghép) | **Không tự đặt giá trị.** Chỉ sinh TC kiểm tra **quan hệ** không cần giá trị (VD Express Fee chỉ có khi Service Type là Express; phí tính lại khi actual weight lớn hơn registered; giữ nguyên khi nhỏ hơn hoặc bằng). Phần cần giá trị (biên bậc phí, tổng tiền cụ thể) **không sinh TC**. |

Cuối output (sau Self-check), thêm mục:

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

1. Đọc `plan-tcs.md` — dùng làm khung cấu trúc (Screen → Component → Risk Level/Ghi chú phụ thuộc, **Strategy Summary** của từng Screen là đầu vào bắt buộc: phạm vi không test, tổ hợp ưu tiên, cách xử lý TBD, lưu ý kiểm thử không hiển nhiên; và **Permission Matrix** nếu có — mỗi ô ❌ phải có TC phủ, xem Pattern 1 trong skill).
2. Đọc `analysis.md` — lấy nội dung AC/Q&A để viết Steps/Expected Result.
3. Xác định platform: `analysis.md` Summary → nếu trống, `CLAUDE.md` → đọc `.claude/skills/testing_dimensions/SKILL.md` section tương ứng. **Cả hai trống (hoặc còn `[...]`) → hỏi user một lần** (Web / Mobile / Desktop...) trước khi sinh TC, không tự mặc định. Multi-language và tính năng đặc thù (push, offline...) suy ra từ spec/AC, không nhắc thì không áp, không hỏi. Xác định **Locale** cùng nguồn (`analysis.md` Summary → `CLAUDE.md`): nếu `Locale: JP` → đọc `.claude/skills/jp_validation/SKILL.md` và áp **cho mọi field nhập liệu**, không phụ thuộc spec có nhắc 全角/半角 hay không (spec có ghi lớp ký tự thì theo spec, không thì dùng bảng mặc định theo loại field, tag `[ASSUMED]`).
4. Với mỗi Screen trong `plan-tcs.md` (theo đúng thứ tự xuất hiện trong file):
   - Sinh **đúng 1 TC UI** cho Screen đó (đặt đầu bảng): `Check giao diện màn hình [tên Screen] thống nhất với design`, Expected Results = đúng một dòng `UI thống nhất với design` (không thêm tên frame, không mô tả chi tiết; chưa có design vẫn ghi như vậy). Theo "UI Policy" trong skill `rbt_manual_testing`.
   - Với mỗi Component (theo đúng thứ tự trong plan):
     - Nhận diện pattern từ AC (và lưu ý trong Strategy Summary) → dựng đầy đủ Decision Table/State Transition/Boundary Tier tương ứng (tham chiếu sub-section "Complex Logic Patterns" trong skill `rbt_manual_testing`), show inline trước khi expand ra TC.
     - **Không** sinh TC visual theo state/component. Popup/dialog/toast/submenu hiện sau action → verify trong Expected Result của TC action đó. Thuộc tính UI chỉ có TC riêng khi là giá trị nghiệp vụ (màu/label theo status, format theo spec) — xem "UI Policy".
     - Nếu là input field: sinh **Field-Level Validation TCs riêng cho từng trường** (Bảng Field-Level Validation trong skill) — không gộp nhiều field vào 1 TC. Nếu `Locale: JP`: sinh theo **Bộ khung TC cho mỗi field text** trong `jp_validation` (thay cho phần ký tự/độ dài của bảng Field-Level, không sinh trùng).
     - Áp **Component Checklist** từ `.claude/skills/component_checklist/SKILL.md` theo **Component Type** đã gắn trong `plan-tcs.md` — tra trực tiếp Section A/B/C, không đoán qua keyword AC text.
     - Nếu cột "Ghi chú phụ thuộc" của component không phải "—": sinh thêm TC cho tương tác cross-component đó (gắn vào Logic của component này).
5. Áp dụng kỹ thuật thiết kế phù hợp: Equivalence Partitioning (EP) kết hợp Boundary Value Analysis (BVA) theo **Pattern 4** trong skill `rbt_manual_testing` cho mọi field có giới hạn độ dài/giá trị (dựng bảng lớp và giá trị inline trước khi sinh TC). Khi expand ra TC, tuân thủ **"Quy tắc gộp TC"** trong skill `rbt_manual_testing`: TC cùng Steps chỉ khác data và cùng loại kết quả → gộp 1 TC nhiều dòng Test Data; Boundary chỉ lấy giá trị sát biên mỗi phía.
6. Áp dụng Platform Dimensions từ `.claude/skills/testing_dimensions/SKILL.md` **một lần cho cả module** (sau khi sinh xong tất cả Screen), gom vào nhóm Function Name `Platform – [tên platform]`, mỗi dimension tối đa 1 TC đại diện, chỉ chọn dimension module thật sự có rủi ro. Không lặp theo Screen/Component.
7. Tuân thủ **Rule ngôn ngữ Test Scenario** (xem sub-section bên dưới).
8. Mỗi **Screen điều hướng chính** (List, Detail...) là 1 heading `## [tên Screen]` duy nhất, với **một bảng TC** ngay bên dưới — `/export-xlsx` dựa vào heading `##` để tách sheet. Popup/dialog/submenu thuộc Screen nào thì TC nằm trong bảng của Screen đó (phân biệt bằng cột Function Name), **không** tạo heading riêng. Không tạo heading theo nhóm tính năng hay theo lượt sinh; ID đánh số liên tục trong toàn module.
9. Sau khi sinh xong tất cả Screen và Platform Dimensions, sinh mục **`## High Risk & E2E`** ở cuối file theo "Mục High Risk & E2E" trong skill `rbt_manual_testing`: **Bảng 1** nhóm TC high risk cần ưu tiên chạy (suy ra từ Risk Level trong `plan-tcs.md`, ô ❌ Permission Matrix, Q&A High, trạng thái không đảo ngược, toàn vẹn dữ liệu) và **Bảng 2** test E2E cần đảm bảo work trước (lấy từ mục "Luồng E2E chính" trong `plan-tcs.md`, chỉ tham chiếu TC có sẵn). Hai bảng luôn được sinh lại sau mỗi lần sinh hoặc sinh lại TC của bất kỳ Screen nào (vì ID có thể đổi).
10. Lưu output ra `testing/[module]/test-cases.md`.

> Nếu nhiều Screen, sinh từng Screen một theo đúng thứ tự trong `plan-tcs.md`, hỏi user để tiếp tục. Nếu một Screen quá lớn phải sinh nhiều lượt, các lượt sau **nối tiếp vào cùng bảng/heading** của Screen đó.

---

## Quick Mode

Chỉ vào đây khi module thiếu cả `analysis.md` và `plan-tcs.md` **và** user chọn Quick ở Bước 0. Không chạy `/analyze-req`, `/plan-tcs`, không có Question Gate/Q&A, bỏ Bước 1 (không có AC TBD). Đánh đổi: spec mơ hồ không được phát hiện, nên Expected dựa trên suy luận phải tag `[ASSUMED]`.

**Đầu vào:** spec/requirement của module (Backlog, Drive, Docs, .md, Figma) cộng `CLAUDE.md`. Chưa có spec nào để đọc → dừng và hỏi user spec ở đâu.

**Trước khi ghi file:** nếu `testing/[module]/test-cases.md` đã tồn tại, hỏi user xác nhận ghi đè (nêu rõ file hiện tại là bản Full hay Quick theo dòng `Mode:` ở đầu file; bản Full thì cảnh báo mạnh hơn). Không đồng ý → dừng, không ghi.

**Cách sinh:**
1. Đọc spec, xác định platform và Locale (nguồn: spec → `CLAUDE.md`). `Locale: JP` → áp `jp_validation` cho mọi field nhập liệu như Full.
2. Rút danh sách yêu cầu từ spec, đánh mã `REQ-01`, `REQ-02`... theo thứ tự xuất hiện (dùng ở cột Traceability ID thay AC-xx). Giả định tự đặt ghi `ASM-xx`, tag `[ASSUMED]`.
3. **Chỉ 1 sheet TC cho cả module**: toàn bộ TC nằm trong **một** heading `## [tên module]` với một bảng TC duy nhất (không tách heading theo nhóm tính năng hay theo frame, vì `/export-xlsx` tách sheet theo heading `##`). Phân biệt các nhóm tính năng/popup/dialog bằng cột Function Name; ID đánh số liên tục. Mục `## High Risk & E2E` vẫn là sheet riêng (bước 6). Spec có phân quyền thì mỗi ô bị cấm vẫn phải có ≥1 TC.
4. Với mỗi nhóm áp **cùng bộ luật như Full**: Field-Level Validation riêng từng field, `component_checklist` (tự nhận Component Type từ spec), EP/BVA theo Pattern 4, "Quy tắc gộp TC", UI Policy (1 TC UI cho mỗi nhóm có màn hình), Platform Dimensions một lần cho cả module, "Rule ngôn ngữ Test Scenario" và TC Gate. Technique (Decision Table/State Transition/Boundary Tier) **không** sinh TC riêng cho từng hàng, mà gộp thành nhiều dòng Test Data trong TC.
5. Spec im lặng hoặc mơ hồ → **không đoán Expected**: theo TC Gate, bỏ TC đó và ghi vào mục "Hành vi spec chưa nêu" cuối output.
6. Cuối file vẫn có `## High Risk & E2E` (Bảng 1, Bảng 2) theo skill `rbt_manual_testing`: Bảng 1 suy từ yêu cầu về tiền/bảo mật/phân quyền/dữ liệu không đảo ngược trong spec; Bảng 2 từ các luồng chính trong spec (3-6 luồng).
7. Chạy Self-Check như Full, **trừ** các tiêu chí cần file không tồn tại: C1 đối chiếu REQ-xx thay AC, S1 và P1(a) không áp dụng, Q2 chỉ đối chiếu các yêu cầu rủi ro cao rút từ spec.

**Dòng đầu file `test-cases.md` (bắt buộc):**

```
> Mode: Quick — chưa qua /analyze-req; Traceability dùng REQ-xx/ASM-xx; Expected tag [ASSUMED] là suy luận, chưa PM/BA xác nhận.
```

**Cuối output, in thêm:**

```
⚠️ Bản Quick, chưa qua analyze-req: chưa có Q&A để phát hiện điểm spec mơ hồ. Module rủi ro cao (tiền/bảo mật/phân quyền) nên chạy /analyze-req rồi /gen-tcs (Full).
```

Muốn nâng lên Full: chạy `/analyze-req` rồi `/gen-tcs` (có đủ `analysis.md`, `plan-tcs.md` thì chạy thẳng, ghi đè bản Quick sau khi user xác nhận).

---

## TC Gate (cho TC sinh từ Checklist, Field-Level, Dimensions, Technique)

Mỗi TC ứng viên phải qua 2 cổng trước khi vào bảng. Cổng này lọc TC "sinh theo loại component" mà không có căn cứ hoặc Expected không đo được.

| Cổng | Câu hỏi | Nếu không đạt |
|---|---|---|
| **G1 — Nguồn** | TC có ít nhất một nguồn hợp lệ không? Nguồn hợp lệ: AC/Q&A/design trong `analysis.md`; ASM-XX đã ghi; Business Rules trong `CLAUDE.md`; hoặc **bộ chuẩn của kit** có Expected không cần spec (Field-Level cơ bản như bắt buộc nhập, không thực thi script/SQL, double-submit không tạo 2 bản ghi; `jp_validation` khi Locale = JP) | Không sinh TC |
| **G2 — Expected đo được** | Nêu được kết quả cụ thể, quan sát được (message, state, giá trị hiển thị) không? | Không sinh TC |

- Expected dựa trên **bộ chuẩn của kit** hoặc **ASM** (không có câu chữ trong spec) → tag `[ASSUMED]`.
- Dòng checklist ghi "(theo spec)" mà spec im lặng và không có nguồn G1 → **không sinh TC**, không đoán Expected. Ghi vào mục cuối output (xem dưới) để QC hỏi PM/BA hoặc bổ sung `analysis.md`.
- Không dùng Gate để loại TC của AC đã Confirmed/Assumed hoặc ô ❌ Permission Matrix.

Mục cuối output (cùng chỗ với cảnh báo AC High), chỉ in khi có mục để liệt kê:

```
ℹ️ Hành vi spec chưa nêu, chưa sinh TC (cần PM/BA hoặc bổ sung analysis.md):
- [Component/dòng checklist]: [hành vi chưa rõ] (VD "Weight Fee tính tròn lên hay làm tròn xuống")
```

## Rule ngôn ngữ Test Scenario

- Luôn bắt đầu bằng **"Check"**, theo sau là **câu tự nhiên hoàn chỉnh, đọc như người nói** — không phải cụm từ khóa rút gọn.
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
| C1 | **AC Coverage** — mỗi AC có ≥1 TC positive | Dò cột Traceability ID, đối chiếu với `analysis.md` |
| C2 | **Test Data cụ thể khi có ghi** — không có placeholder (chỉ áp cho ô đã ghi; ô không cần thì để trống) | Grep "email hợp lệ", "số điện thoại đúng", "nhập đúng", "bất kỳ" trong cột Test Data |
| C3 | **Expected Result đo được** — không mơ hồ | Grep "hiển thị đúng", "load nhanh", "thành công", "phản hồi nhanh" trong cột Expected Results. "Hiển thị đúng" chỉ được chấp nhận khi nêu rõ đối tượng và đối chiếu được với Test Data hoặc Steps (VD "Hiển thị đúng dữ liệu đã nhập như Test Data"); dạng trơn ("hiển thị đúng", "hiển thị đúng thông tin") thì viết lại |
| M1 | **TC Independence** — không TC nào refer đến TC khác | Grep mã module của chính file (VD `APB-\d{3}`, lấy từ tiền tố cột ID) cùng "xem TC", "kết quả bước trước" trong cột Steps/Precondition |
| M2 | **Negative Coverage** — mỗi happy path AC có ≥1 TC negative (**trừ** AC `[UNCONFIRMED]` mức Medium/Low chỉ có 1 TC đại diện; AC High vẫn phải có negative) | Gom TC theo Traceability ID; TC là **negative** khi Expected báo lỗi, từ chối, chặn hoặc không thực hiện được hành động (hoặc Category `Negative`/`Security`). Không đếm theo Category vì TC mức component chỉ có UI/Validate/Behavior/Logic |
| Q1 | **ID trong mục High Risk & E2E còn tồn tại** — mọi ID ở Bảng 1 và Bảng 2 có trong bảng TC; ID không bị lặp ở Bảng 1 | Đối chiếu từng ID với cột ID của bảng TC |
| Q2 | **Bảng 1 phủ rủi ro** — gồm mọi ô ❌ của Permission Matrix, mọi TC của AC High, và không vượt khoảng 30% tổng số TC | Đối chiếu Permission Matrix, bảng AC (Status/Q&A High) với cột TC của Bảng 1 |
| Q3 | **Bảng 2 phủ luồng chính** — có đủ các luồng ở mục "Luồng E2E chính" của plan (3-6 luồng), mỗi bước có TC hoặc ghi `thiếu TC`, có cột "Nếu fail thì" | Đối chiếu mục Luồng E2E chính của `plan-tcs.md` với Bảng 2 |
| L1 | **Ngôn ngữ TS** — không còn ký hiệu rút gọn | Grep `→`, `->`, dấu `:` nén ý trong cột Test Scenario |
| S1 | **Plan nhất quán với analysis và đã dùng Strategy** — Screen trong `plan-tcs.md` khớp Screen Inventory của `analysis.md` (nếu có); mọi hàng ma trận của `analysis.md` có trong plan (xem P1a); TC không sinh cho phần Strategy ghi "không test" | Đối chiếu `plan-tcs.md` với `analysis.md` và các bullet Strategy Summary |
| L3 | **Precondition và Test Data chỉ khi cần** — Precondition để trống nếu Steps tự đủ; không có "đăng nhập", email/tài khoản, tên định danh (`Hospital A`, `M1`); mỗi điều kiện một dòng, ngắn, tham chiếu `như Test Data` khi đã có dữ liệu cụ thể. Test Data không chứa email/tài khoản, không chứa mô tả trạng thái (thuộc Precondition), không ghi `—` | Rà hai cột: grep `@`, `đăng nhập`, `Đăng nhập`, `—`; Test Data có dòng `Trạng thái:` thì chuyển sang Precondition; TC UI/mở màn hình không cần Precondition |
| L2 | **Test Data một field một dòng** — không nối nhiều field bằng `;` hoặc `,` trên một dòng | Rà cột Test Data: mỗi field/giá trị phải nằm sau `<br>` riêng (xem "Trình bày cột Test Data" trong skill) |
| P1 | **Permission Coverage** — (a) mỗi hàng ma trận Actor × Action trong `analysis.md` có mặt trong Permission Matrix của `plan-tcs.md` (nếu thiếu thì bổ sung hàng vào plan trước); (b) mỗi ô ❌ — kể cả hàng sở hữu `[Action] — của người khác` — có ≥1 dòng Test Data trong một TC; (c) ô ? có Q&A thì có 1 TC `[UNCONFIRMED]` (chỉ check khi module có phân quyền) | Đối chiếu ma trận `analysis.md` → `plan-tcs.md` → cột Test Data/Steps của TC Security/Negative |

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

**Sau khi gộp/xoá:** chạy lại C1, M2, P1 để chắc chắn không làm mất độ phủ AC, negative hay ô ❌.

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

File đã lưu tại testing/[module]/test-cases.md
```

Nếu không phát hiện issue nào: `✅ Self-check: 0 issues. File đã lưu tại testing/[module]/test-cases.md`

---

## Output

`testing/[module]/test-cases.md`

Bảng TC format: `ID | Function Name | Category | Traceability ID | Test Scenario | Precondition | Steps | Expected Results | Test Data` — **không có** cột Risk Level và Priority; ưu tiên chạy nằm ở mục `## High Risk & E2E` (xem bên dưới).

- **Function Name:** Sub-module/Component từ `plan-tcs.md` (VD "Email field", "Submit button"). Nếu TC ở mức flow (không gắn 1 component cụ thể), dùng tên flow (VD "Login Flow").
- **Category:** cấp con dưới Function Name — "UI"/"Validate"/"Behavior"/"Logic" (component-level) hoặc "Happy Path"/"Negative"/"Security" (flow-level).
- **Traceability ID:** AC tương ứng từ `analysis.md` (VD `AC-05`), hoặc Q&A ID (VD `Q-LOG-001`), hoặc `N/A` nếu không có nguồn rõ ràng — tên cột dùng chung cho mọi loại ID team quy ước để trace ngược, không giới hạn chỉ AC.

> Khi export ra `.xlsx` qua `/export-xlsx`: Sheet name = tên Screen (heading `##` trong `test-cases.md`, lấy theo tên Screen trong `plan-tcs.md`).
>
> Khi requirements thay đổi sau khi đã có `test-cases.md`: cập nhật `plan-tcs.md` trước (nếu cấu trúc Screen/Component đổi), rồi chạy lại `/gen-tcs` cho Screen bị ảnh hưởng.
