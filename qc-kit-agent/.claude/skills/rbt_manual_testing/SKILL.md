---
name: rbt_manual_testing
description: Skill sinh manual test cases theo quy trình AI-RBT — pipeline 2 bước per module (analyze-req → gen-tcs), CLAUDE.md điền tay 1 lần cho project. Dùng kết hợp với requirements_analyzer và testing_dimensions.
---

# RBT Manual Testing

## Description

Skill hỗ trợ sinh manual test cases chất lượng cao theo quy trình Risk-Based Testing (RBT). Được tổ chức thành **4 sections**: 1 bước setup project (không cần command), `/analyze-req` (Section 2), bước dựng cấu trúc test nằm bên trong `/gen-tcs` (Section 3, không có command riêng), và `/gen-tcs` (Section 4).

**Pipeline:**
```
CLAUDE.md (điền tay 1 lần) → /analyze-req → /gen-tcs
```

**Nguyên tắc cốt lõi:**
- **Human Strategy:** Con người xác định chiến lược, mức độ rủi ro và tiêu chuẩn — thể hiện ở Q&A của `/analyze-req` (PM/BA quyết định), ở Summary + System Model mà user đọc trong `analysis.md`, và ở tóm tắt cấu trúc Screen/Component mà `/gen-tcs` in ở đầu output
- **AI Execution:** AI thực hiện phân tích, viết TCs và rà soát lỗ hổng
- **Human Verification:** Con người kiểm tra lại kết quả trước khi chốt

---

## When to Use

Sử dụng skill này khi:
- Sinh manual test cases từ requirements / user stories
- Phân tích requirements để phát hiện ambiguity và verify AC
- Dựng cấu trúc test (phân rã Screen/Component, risk level) có traceability với AC
- Áp dụng Risk-Based Testing (đánh giá rủi ro cho test cases)
- Chuẩn hóa test cases sang bảng Markdown (Backlog/Excel format)

**KHÔNG** sử dụng skill này khi:
- Cần chuẩn hóa bug report → dùng `/gen-bug-report`

---

# Quy ước file và version

Mọi file của một module nằm trong `testing/[module]/`. **Tên module = tên thư mục** (không dùng Mã module):

| File | Tên |
|---|---|
| Phân tích requirement | `[module]-analysis-vN.md` |
| Test case (bản markdown) | `[module]-testcases-vN.md` |
| Test case (bản Excel) | `[module]-testcases-vN.xlsx` (cùng tên với `.md`, chỉ đổi đuôi) |
| Review (`/review-tcs`) | `[module]-review-vN.md`, N = version TC được review |
| Phụ lục review (`/review-tcs`) | `[module]-review-detail-vN.md`, cùng N với file review |
| Automation report (`/gen-automation`) | `[module]-automation-report-vN.md`, N = version TC được chạy |
| Bản chụp spec (`/update-tcs`) | `[module]-spec-vN.md`, N = version mới mà lần update đó tạo ra |

Review, automation report và spec **không quyết định version của module**: `next-version` chỉ tính analysis và testcases. Chúng đi theo version của file TC liên quan.

**Số `N` là số lần spec đổi** (spec v1, v2, v3...). `analysis-vN` và `testcases-vN` cùng N nghĩa là cùng một bản spec. Module không có analysis (Quick) thì chỉ có `testcases-vN`. N có thể nhảy cách (VD có `analysis-v1` và `analysis-v3`) nếu một lần spec đổi mà analysis không được cập nhật.

**Khi nào tạo version mới:**

| Tình huống | Việc làm |
|---|---|
| Module chưa có file nào, chạy `/analyze-req` hoặc `/gen-tcs` | Tạo `v1` |
| Spec đổi, chạy `/update-tcs` | Tạo file mới với N = (version lớn nhất của module) + 1, cho cả analysis (nếu có) và testcases. File cũ giữ nguyên. **Ngoại lệ:** analysis mới nhất đã có version lớn hơn file TC đầu vào (analysis được cập nhật trước) thì TC mới lấy đúng số của analysis đó, không tạo thêm analysis |
| `/update-tcs` chạy trên xlsx | Ghi xlsx `vN+1` và, nếu module có md TC, ghi thêm md `vN+1` (md chỉ phản ánh thay đổi do spec, không gồm sửa tay trong xlsx). Chạy trên md: ghi md `vN+1` rồi export xlsx tự động nếu xlsx đích chưa tồn tại |
| `/gen-tcs` Full sinh lại hoặc sinh tiếp TC, spec không đổi | Giữ nguyên Function Name, ghi vào `testcases-vN` hiện tại (N của analysis), không tạo version mới. Đích là bản Quick thì hỏi 3 lựa chọn (xem `/gen-tcs` Bước 0) |
| `/gen-tcs` Quick, đích đã tồn tại | Hỏi xác nhận rồi ghi đè `testcases-vN` hiện tại (N của testcases mới nhất). Không tạo version mới |
| `/gen-tcs` hoặc `/update-tcs` (chạy trên md) lưu xong file md | Tự export xlsx cùng tên nếu xlsx đích chưa tồn tại; đã tồn tại thì bỏ qua, không ghi đè |
| `/gen-tcs` bổ sung giả định nhỏ vào analysis (VD ASM mới) | Sửa tại chỗ analysis hiện tại và ghi một dòng `History`. Không tạo version mới |
| `/analyze-req` chạy lại khi module đã có analysis | Hỏi user: ghi đè version mới nhất hay tạo version mới (spec đã đổi) |
| `/analyze-req` khi module đã có testcases vN nhưng chưa có analysis (Quick lên Full) | Hỏi spec đã đổi chưa: đã đổi thì ghi `analysis-v(N+1)`, chưa đổi thì ghi `analysis-vN` |

**Đọc file:** không nêu version thì dùng **version lớn nhất**. Trong tài liệu kit, `analysis.md` và `test-cases.md` là **tên gọi tắt** của file mới nhất theo quy ước này, không phải tên file thật.

**Tên cũ:** `analysis.md`, `test-cases.md`, `test-cases.xlsx` (module làm trước quy ước này) vẫn đọc được và tính là v1. Cùng N thì tên mới được ưu tiên. File tên cũ không bị đổi tên tự động.

**Không đếm version bằng tay.** Dùng `.claude/scripts/module_files.py` (xem docstring đầu file):

```
python3 -I .claude/scripts/module_files.py latest testing/[module] analysis|testcases [md|xlsx]
python3 -I .claude/scripts/module_files.py next-version testing/[module]
python3 -I .claude/scripts/module_files.py check testing/[module]   # cảnh báo md/xlsx lệch version, tên sai quy ước
python3 -I .claude/scripts/module_files.py path testing/[module] analysis|testcases N [md|xlsx]
```

`History` trong `analysis` dùng chính số N của file (`v1`, `v2`...), không dùng nhãn lẻ như `v1.1`.

---

# Section 1: Context Setup

**Không có command riêng** — `CLAUDE.md` ở root project là file điền tay 1 lần, Claude Code tự nạp mỗi session.

**Cách dùng:**
- Kit có sẵn `CLAUDE.md` skeleton (placeholder `[...]`). Copy ra root project rồi điền: Project Name, Actors, Platform, Locale, Business Rules toàn cục.
- Project **đã có** `CLAUDE.md` → không ghi đè, dán các mục của skeleton vào cuối file hiện có.
- Mục để trống hoặc còn `[...]` thì agent bỏ qua.

> Giữ ngắn — dưới 20 dòng (file được nạp mỗi session). Thông tin đặc thù module để trong `## Summary` của `analysis.md`. Filter trước khi ghi: *"Đây là rule của cả project hay của riêng module này?"* — chỉ ghi thông tin là rule của cả project.

---

# Section 2: Requirement Analysis

**Command tương ứng:** `/analyze-req`

**Mục đích:** Giúp con người phát hiện **lỗ hổng mà spec/design không nói tới**, và mapping REQ → AC. Chất lượng đo bằng độ trúng của câu hỏi (câu trả lời làm đổi bao nhiêu TC), không đo bằng số câu hỏi. Output là bộ AC + Screen Inventory đủ tốt để `/gen-tcs` sinh TC.

> **Nguồn chính cho quy trình, Question Gate, format và output là [`/analyze-req`](../../commands/analyze-req.md) + [`requirements_analyzer`](../requirements_analyzer/SKILL.md).** Section này chỉ tóm tắt — khi có khác biệt, theo hai file đó.

**Agent phải:**
1. Đọc **toàn bộ** requirements doc trước (chưa sinh câu hỏi) — project context lấy từ CLAUDE.md (Claude Code tự nạp). Nếu có design: đọc theo `Design Integration` trong `requirements_analyzer`, lưu danh sách frame/screen đã confirm.
2. **Dựng System Model** (thực thể & định danh, vòng đời/state, actor × action, luồng dữ liệu, giả định môi trường ngầm) cùng Summary → ghi vào `analysis.md` (mục Summary, System Model), không show inline và không chờ xác nhận.
3. **Tìm lỗ hổng trên mô hình** bằng 8 Lens (L1-L8, ưu tiên L1-L5: state, định danh, thao tác hàng loạt, lỗi từng phần, môi trường) → sinh danh sách ứng viên câu hỏi.
4. Cho từng ứng viên đi qua **Question Gate** (G1-G4) → phân loại: **Q&A** (cần quyết định, Severity High/Medium) / **ASM** (assumption có căn cứ) / **DIF** (lệch spec↔design, chọn A/B) / loại bỏ. Mỗi Q&A có Reference (chỉ mã REQ), Screen, ô **Câu hỏi** gộp 3 phần (REQ dẫn chứng → Câu hỏi → Phương án đề xuất A/B kèm `→ Đề xuất` và nguồn căn cứ), "Nếu đoán sai", Severity, Status; một câu = một quyết định.
5. **Impact Analysis** *(chỉ khi có dependency có căn cứ)*: liệt kê hành vi hiện có của module khác có thể vỡ (IMP-XX: điểm chạm, hành vi cần kiểm lại, rủi ro, căn cứ) — chưa sinh test scenario ở bước này.
6. **Song song — Mapping REQ → AC:** xác định Happy / Alternate / Exception Paths, map thành AC, Status `Confirmed` / `Assumed` (gắn ASM-XX) / `TBD` (gắn Q-MOD-XXX).
7. Tổng hợp vào `analysis.md`: Summary, System Model, Q&A — Cần quyết định, Lệch spec↔design, Assumptions, Impact Analysis (nếu có dependency), Acceptance Criteria, Screen Inventory (nếu có design), History.

**Output file:** `testing/[module]/[module]-analysis-vN.md` (xem "Quy ước file và version") — template đầy đủ xem trong `/analyze-req`.

> AC **Status TBD** = AC phụ thuộc Q&A chưa được trả lời — `/gen-tcs` sẽ cảnh báo theo Severity của Q&A liên quan (DIF chưa chọn coi như mức Low).

---

# Section 3: Dựng cấu trúc test (bước nội bộ của /gen-tcs)

**Không có command riêng** — `/gen-tcs` tự làm bước này ngay trước khi sinh TC và **không lưu thành file** (cấu trúc dựng từ `analysis.md`; file `plan-tcs.md` cũ nếu còn thì bỏ qua).

**Mục đích:** xác định cấu trúc phân rã Screen/Component + Risk Level trước khi sinh TC. Kết quả là đầu vào cho bước sinh TC trong cùng một lần chạy, không phải bản ghi lâu dài. Nơi lưu lâu dài: Screen và Function Name nằm trong bảng của `test-cases.md`; Permission Matrix nằm trong `analysis.md`; luồng E2E nằm trong Bảng 2 của `## High Risk & E2E`.

**Agent phải:**
1. Đọc `analysis.md` (Summary + AC + Screen Inventory nếu có) + `CLAUDE.md` (platform)
2. **Xác định Screen (đơn vị màn hình)** — tổng quát, không giới hạn CRUD List/Create/Edit/Detail. 1 Screen = 1 **màn hình điều hướng chính** user đi tới được (VD List, Detail, Create/Edit). **Form wizard nhiều step = 1 Screen** (lấy cả form làm đơn vị, mỗi step là nhóm Component/Function Name trong cùng sheet, không tách step thành Screen) — mỗi Screen = 1 sheet trong file `.xlsx`. **Popup, dialog, modal, submenu, bottom sheet, toast, tab con KHÔNG phải Screen riêng**: chúng thuộc Screen đã mở ra chúng, được liệt kê là Component (Component Type = Dialog/Popup...) của Screen đó và TC nằm cùng sheet. Overlay dùng chung ở nhiều Screen → gắn vào Screen mở nó đầu tiên, các Screen còn lại chỉ test phần khác biệt.
   - Có Screen Inventory → dùng làm nguồn, nhưng frame của popup/dialog/submenu gộp vào Screen cha.
   - Không có → suy luận từ Summary/luồng trong AC, tự flag rõ "Phân rã dựa trên suy luận từ text, chưa có design xác nhận."
3. Với mỗi Screen:
   a. Ghi nhận **UI chung (layout tổng thể)** — 1 dòng mô tả ngắn ở cấp Screen.
   b. Liệt kê **từng Component theo đúng thứ tự xuất hiện trên UI**. Có design → thứ tự đọc trên frame (trên xuống dưới, trái sang phải; popup/dialog ngay sau component mở ra nó); chỉ có spec → thứ tự spec mô tả (field theo danh sách trong spec, rồi action theo thứ tự luồng), ghi rõ "thứ tự suy luận từ spec". Screen: có design → thứ tự frame trong luồng điều hướng; chỉ có spec → theo luồng chính. Spec và design khác thứ tự → theo design, ghi vào DIF.
4. **Gợi ý theo loại Screen** (để nhớ những nhóm TC hay bị sót — **không phải danh sách phạm vi**; không loại được bộ chuẩn Field-Level, `component_checklist`, ô ❌ Permission Matrix và TC của AC High):
   - **List/Search:** test độc lập từng chức năng (Search, mỗi Filter, Sort, Pagination, Row/Bulk action), chỉ chọn 1-2 tổ hợp rủi ro cao để test kết hợp, không test mọi tổ hợp; boundary data 0 record, 1 record, vừa đủ 1 trang, nhiều trang; danh sách cập nhật đúng sau Create/Update/Delete.
   - **Form (Create/Edit):** field-level trước, cross-field sau; Create khác Edit thì tách; Cancel/dirty state/double-submit.
   - **Detail/View:** data mapping đúng nguồn và định dạng; record không tồn tại hoặc đã xóa báo lỗi rõ ràng, không crash.
   - **Khác** (Dashboard, Wizard, Settings...): liệt kê các nhóm chức năng độc lập, test từng nhóm trước, chỉ kết hợp những nhóm có rủi ro nghiệp vụ cao.
   - Phạm vi **không test** chỉ được quyết định khi có căn cứ cụ thể trong `analysis.md` (VD spec không mô tả Search/Filter), ghi kèm lý do vào tóm tắt cấu trúc.
5. Với mỗi Component, xác định:
   - **Component Type** (Textbox/Dropdown/Checkbox/Radio/Table/Dialog/Button/File Upload/...) — dùng để tra thẳng `.claude/skills/component_checklist/SKILL.md`, không đoán qua keyword.
   - **Risk Level** (High/Medium/Low) — High: nghiệp vụ quan trọng/tiền/bảo mật/phân quyền; Medium: luồng chính không critical; Low: UI validation/happy path đơn giản. Dùng làm đầu vào cho Bảng 1 "High Risk & E2E", không xuất thành cột.
5b. **Permission Matrix:** nếu Screen có action phân quyền, chép đủ mọi hàng Actor × Action từ `analysis.md` vào Screen chứa action đó (không bỏ hàng, kể cả hàng chỉ có ô ❌ hoặc ?; hàng không gắn Screen nào thì đặt vào Screen đầu tiên liên quan), thêm hàng riêng `[Action] — của người khác` cho action giới hạn theo sở hữu (đơn của mình, đơn được gán cho mình); ô ? ghi mã Q&A. Đối chiếu: số hàng của `analysis.md` = số hàng ma trận đã dựng (chưa tính hàng sở hữu).
6. **Rule tương tác chéo component:** khi xác định Logic của 1 component, luôn tự hỏi "component này có phụ thuộc/ảnh hưởng component nào khác trên cùng màn hình không?" — nếu có, sinh thêm TC cho tương tác đó, gắn vào component chịu trách nhiệm chính, không tạo category riêng.
7. **Xác định Assumption môi trường test** — liệt kê ngắn các điều kiện hạ tầng/bên ngoài mà TC sẽ ngầm dựa vào để chạy được (VD: API bên thứ 3 available lúc test, cronjob/background job chạy đúng chu kỳ thật, không bị mock/stub). Đây KHÔNG phải câu hỏi cho PM/BA (khác Q-MOD-XXX) — chỉ là lưu ý cho người chạy test. Để trống nếu module không phụ thuộc hạ tầng ngoài.
7b. **Luồng E2E chính:** từ luồng chính và các nhánh có ý nghĩa nghiệp vụ trong `analysis.md` (vòng đời, nhánh lỗi/hủy, luồng qua nhiều actor/thiết bị), liệt kê 3-6 luồng E2E (luồng chính trước) — làm nguồn cho Bảng 2 của mục `## High Risk & E2E`. Không gộp biến thể dữ liệu thành luồng riêng.

**Kết quả:** không lưu file. `/gen-tcs` in tóm tắt cấu trúc không chặn ở đầu output (định dạng xem Bước 0 trong `/gen-tcs`).

> **Lưu ý:** Khi user gọi `/gen-tcs` mà module chưa có `analysis.md` → hỏi user chọn Full (chạy `/analyze-req` rồi sinh TC) hoặc Quick (sinh thẳng từ spec, xem "Quick Mode" trong `/gen-tcs`). Có `analysis.md` thì chạy thẳng. Mọi bước đều chạy liền mạch, không dừng hỏi.

---

# Section 4: Test Case Generation

**Command tương ứng:** `/gen-tcs`

**Mục đích:** Sinh Test Case chi tiết (bao gồm Test Scenario) từ `analysis.md` (cùng cấu trúc test dựng ở Section 3), áp dụng Field-Level Validation, UI Policy (không sinh TC visual theo từng state), và kỹ thuật thiết kế test case.

**Agent phải:**
1. Dựng cấu trúc test theo Section 3 từ `analysis.md` — nếu thiếu `analysis.md`, xử lý theo Bước 0 trong `/gen-tcs`: hỏi user chọn Full/Quick (Quick sinh thẳng từ spec, không có `analysis.md` nên không áp bước 2 về AC TBD; luật còn lại giữ như Full, chi tiết trong "Quick Mode" của `/gen-tcs`); Full thì tự chạy `/analyze-req` không dừng hỏi. Cấu trúc này quyết định thứ tự Screen/Component và Risk Level; `analysis.md` quyết định *sinh cái gì* và *sâu tới đâu*.
2. Đọc `analysis.md` (nội dung AC đầy đủ + Q&A status) — quyết định *nội dung* Steps/Expected Result. Kiểm tra TBD ACs theo severity của Q&A liên quan trước khi tiếp tục: Medium/Low → sinh 1 TC đại diện mỗi AC, tag `[UNCONFIRMED]`, không khai triển kỹ thuật/negative/edge **của phần Q&A chưa trả lời** (kiểm tra cơ bản không phụ thuộc câu trả lời, VD bắt buộc nhập/sai kiểu dữ liệu/số âm, vẫn sinh bình thường — xem `/gen-tcs` Bước 1), không hỏi; High → **không dừng hỏi**, sinh đầy đủ happy/negative/edge theo phương án đề xuất của Q&A, tag `[UNCONFIRMED]` + mã Q&A (nếu Q&A thiếu giá trị/công thức thì chỉ sinh TC quan hệ, phần cần giá trị ghi vào mục cảnh báo cuối output; xem Bước 1 trong `/gen-tcs`).
3. Xác định platform: đọc `analysis.md` Summary → nếu trống, dùng Platform trong `CLAUDE.md` → đọc `.claude/skills/testing_dimensions/SKILL.md` section tương ứng.
4. Với mỗi Screen trong cấu trúc đã dựng (đúng thứ tự):
   a. Sinh **đúng 1 TC "Verify UI tổng thể"** cho Screen (đặt đầu bảng của sheet đó), Expected Result = `UI thống nhất với design` — xem "UI Policy" ở Reference Library. Đây là TC UI duy nhất của Screen.
   b. Với mỗi Component (đúng thứ tự trong cấu trúc):
      - Nhận diện pattern từ AC → **dựng đầy đủ** Decision Table/State Transition/Boundary Tier tương ứng (xem sub-section "Complex Logic Patterns"), show inline trước khi expand ra TC.
      - **KHÔNG** sinh TC visual riêng theo state (Normal/Focus/Error/Disabled/Loading) — theo "UI Policy". Hành vi của state (Disabled không tap được, Error hiện đúng message...) được verify trong TC Logic/Validate của action gây ra state đó.
      - Nếu là input field: sinh **Field-Level Validation TCs riêng cho từng trường** (Bảng Field-Level Validation) — không gộp nhiều field vào 1 TC.
      - Áp `.claude/skills/component_checklist/SKILL.md` theo **Component Type** đã xác định ở Section 3 (Section A/B/C — tra trực tiếp, không đoán qua keyword AC text).
      - Khi xét Logic: áp dụng rule tương tác chéo component (Section 3, bước 6) — nếu component phụ thuộc component khác, sinh thêm TC cho tương tác đó.
5. Áp dụng kỹ thuật thiết kế phù hợp: Equivalence Partitioning (EP), Boundary Value Analysis (BVA).
6. Áp dụng Platform Dimensions từ `.claude/skills/testing_dimensions/SKILL.md` **một lần cho cả module** (không lặp theo Screen/Component) — xem "Platform Dimensions: áp theo module" ở Reference Library.
7. Lưu output ra `testing/[module]/[module]-testcases-vN.md` (xem "Quy ước file và version").

> Nếu scope lớn (nhiều Screen), sinh từng Screen một theo thứ tự đã dựng, hỏi user để tiếp tục. Khi sinh lại hoặc sinh tiếp một Screen đã có trong `test-cases.md`, lấy Function Name từ bảng hiện có để tên không đổi giữa các lần chạy.

## Rule ngôn ngữ Test Scenario

- Luôn bắt đầu bằng **"Check"**, theo sau là **câu tự nhiên hoàn chỉnh, đọc như người nói** — không phải cụm từ khóa rút gọn. Tag `[UNCONFIRMED]` (nếu có) đứng ngay trước chữ "Check" (`[UNCONFIRMED] Check ...`) và không tính là vi phạm.
- **Cấm:** ký hiệu mũi tên (`→`, `->`), gạch chéo nén ý thay cho "hoặc" (VD `A/B`), dấu hai chấm nén nhiều ý (VD `Login: email sai`), viết tắt không giải thích.
- Ví dụ:
  - ❌ Sai: `Login → Dashboard (email/pass hợp lệ)`
  - ✅ Đúng: `Check đăng nhập thành công với email và password hợp lệ`

**Output file:** `testing/[module]/[module]-testcases-vN.md`

---

## Complex Logic Patterns

Agent **tự động nhận diện** từ nội dung AC và áp dụng pattern phù hợp **trước khi sinh TC**. Có thể áp nhiều pattern trong 1 lần nếu AC phức tạp. Với lưu ý kiểm thử không hiển nhiên của component đang xử lý (VD biên làm tròn), tự dựng bảng/diagram đầy đủ ở đây.

### Pattern 1: Decision Table

**Trigger:** AC có ≥2 điều kiện kết hợp tạo ra kết quả khác nhau.
Dấu hiệu: "nếu... thì", "khi... và", multiple conditions, **phân quyền theo role**, role-based behavior.

> **Permission/Auth là use case phổ biến nhất của pattern này.** Bất cứ khi nào AC mô tả "role X được làm Y trên resource Z" → bắt buộc dựng Decision Table trước khi sinh TC.

**Agent làm:**
1. Liệt kê tất cả điều kiện (conditions)
2. Dựng bảng tổ hợp → kết quả
3. Show inline cho user thấy trước khi expand ra TC

```
Ví dụ 1 — Permission: Role × Action × Resource

| Role    | Action | Resource      | Kết quả     |
|---------|--------|---------------|-------------|
| Admin   | Edit   | Own record    | ✅ Allowed  |
| Admin   | Edit   | Other record  | ✅ Allowed  |
| Editor  | Edit   | Own record    | ✅ Allowed  |
| Editor  | Edit   | Other record  | ❌ Denied   |
| Viewer  | Edit   | Any record    | ❌ Denied   |

Ví dụ 2 — Business logic: Role × Trạng thái đơn hàng

| Role    | Trạng thái | Có thể hủy? |
|---------|------------|-------------|
| Admin   | Pending    | ✅ Có       |
| Admin   | Shipped    | ❌ Không    |
| User    | Pending    | ✅ Có       |
| User    | Shipped    | ❌ Không    |
```

**Sau đó:** gộp các row theo **kết quả**, không phải 1 row = 1 TC:
- Các row cho **cùng kết quả và cùng cách verify** → 1 TC, liệt kê từng tổ hợp ở Test Data, Expected nêu kết quả chung.
- Row cho **kết quả khác** hoặc **side-effect khác** → TC riêng.
- Row **rủi ro cao** (tiền/bảo mật/phân quyền) hoặc có Q&A riêng → giữ TC riêng.
- Với Permission table: vẫn phải có cả allowed (positive) lẫn denied (negative). Trong **cùng một action**, các role cùng bị denied với cùng cách verify có thể là các dòng Test Data của 1 TC; **không gộp xuyên action** (mỗi action giữ TC riêng).
- **Phủ ma trận:** mỗi ô ❌ trong Permission Matrix (dựng ở Section 3 từ `analysis.md`) phải có ít nhất 1 dòng Test Data trong một TC — không chọn tuỳ ý "vài role". Gồm cả hàng sở hữu (`[Action] — của người khác`): VD Driver khác thực hiện Pickup/Delivered/Failure trên đơn của Driver được gán. Ô ? có Q&A chưa trả lời → **luôn** có 1 TC đại diện `[UNCONFIRMED]` theo phương án đề xuất của Q&A đó; nếu Q&A chỉ hỏi về hành vi gần kề (VD hỏi quyền hủy đơn nhưng ô ? là quyền tạo đơn), suy ra từ phương án của Q&A và ghi rõ trong Expected là suy luận từ Q-XXX-NNN; không khai triển thêm. Chỉ khi ô ? không có Q&A nào liên quan mới không sinh TC (ghi vào mục "Hành vi spec chưa nêu").

---

### Pattern 2: State Transition

**Trigger:** AC có workflow trạng thái, object chuyển qua nhiều states.
Dấu hiệu: "trạng thái", "chuyển sang", "flow", tên states rõ ràng (Draft, Pending, Approved...).

**Agent làm:**
1. Vẽ state diagram dạng text
2. Xác định transitions hợp lệ và không hợp lệ
3. **Xác định back transition** — tự hỏi: có transition nào đi NGƯỢC lại state trước đó không (khác invalid transition — đây là đường lùi CÓ CHỦ ĐÍCH trong thiết kế, VD "mở lại", "hủy duyệt", "yêu cầu sửa lại")? Nếu có, đánh dấu riêng — side-effect của đi lùi thường khác đi tiến (thu hồi quyền đã cấp, xóa timestamp đã đóng dấu, báo lại người liên quan...), không thể coi là "test lại y hệt transition tiến theo chiều ngược".
4. Show inline trước khi sinh TC

```
Ví dụ — Workflow phê duyệt:

[Draft] --submit--> [Pending]
[Pending] --approve--> [Approved]
[Pending] --reject--> [Rejected]
[Approved] --cancel--> [Cancelled]

Back transitions (đi lùi có chủ đích, khác invalid):
[Approved] --reopen--> [Pending]

Invalid transitions:
[Draft] --approve--> ❌
[Approved] --submit--> ❌
```

**Sau đó:** test mỗi transition hợp lệ (1 TC) + mỗi invalid transition quan trọng (1 TC) + mỗi back transition (1 TC riêng — verify cả state cuối đúng chưa lẫn side-effect đi kèm, không gộp chung với transition tiến).

---

### Pattern 3: Boundary Tier

**Trigger:** AC có ngưỡng phân loại tạo ra hành vi khác nhau theo dải giá trị, **kể cả ngưỡng nghiệp vụ không gắn với field** (giới hạn số lượng như "tối đa 5 đơn", thời gian chờ như "quá 30 phút", số lần thử như "lần thứ 3 thì hủy").
Dấu hiệu: "từ X đến Y", %, tier/level/rank, ngưỡng số cụ thể, "tối đa", "quá", "từ lần thứ N".

**Agent làm:**
1. List đủ các tier và boundary values của từng tier
2. Show inline trước khi sinh TC

```
Ví dụ — Phí vận chuyển theo giá trị đơn hàng:

Tier 1 (0đ - 99,999đ):     test 0, 1, 99,998, 99,999
Tier 2 (100,000đ - 499,999đ): test 100,000, 100,001, 499,998, 499,999
Tier 3 (500,000đ+):         test 500,000, 500,001, giá trị rất lớn
```

**Sau đó:** chọn giá trị đại diện, không test mọi giá trị:
- Mỗi **biên** chỉ lấy giá trị sát biên mỗi phía (VD biên 120s → 119s, 121s; giá trị 120s nếu spec nói rõ biên thuộc phía nào). Không thêm giá trị xa biên nếu cùng một lớp tương đương.
- Các giá trị **cùng Steps, chỉ khác data, cùng loại kết quả** (VD ghép 1 file / 2 file / 3 file đều cho "thời lượng bằng tổng") → **1 TC**, Test Data liệt kê từng dòng, Expected ghi tương ứng từng dòng.
- Giá trị cho **kết quả khác** (hợp lệ vs lỗi, thuộc tier khác) → TC riêng.
- **Ngưỡng nghiệp vụ luôn phủ cả hai phía** (áp cho AC Confirmed/Assumed và AC High; AC TBD mức Medium/Low vẫn chỉ 1 TC đại diện theo `/gen-tcs` Bước 1): phía "còn được" sát ngưỡng và phía "bị chặn/đổi hành vi" sát ngưỡng (VD giới hạn 5 đơn: Driver đang có 4 đơn vẫn nhận được đơn thứ 5, Driver đang có 5 đơn bị chặn; cảnh báo 30 phút: assign ở phút 29 không cảnh báo, phút 31 có cảnh báo). Không chỉ test phía bị chặn.

### Pattern 4: Length / Value (EP + BVA)

**Trigger:** field có giới hạn độ dài hoặc giá trị (min/max ký tự, khoảng số, tiền, ngày, số lượng).

**Cách kết hợp:** EP chia miền thành các lớp (mỗi lớp cùng một hành vi) → BVA chọn giá trị sát biên của các lớp → gộp các giá trị cùng kết quả thành 1 TC nhiều dòng Test Data (xem "Quy tắc gộp TC").

**Agent làm:**
1. Liệt kê các lớp EP của field: trống, không hợp lệ phía dưới, hợp lệ, không hợp lệ phía trên (+ lớp khác theo loại: âm, 0, thập phân, không phải số, sai định dạng).
2. Chọn giá trị BVA cho mỗi biên: **min−1, min, max, max+1** (mức mặc định) và **1 giá trị đại diện giữa** lớp hợp lệ. Chỉ thêm min+1 và max−1 cho field rủi ro High (tiền, phân quyền).
3. Show bảng lớp và giá trị inline trước khi sinh TC.

```
Ví dụ — Login ID 8 đến 32 ký tự:

| Lớp (EP)                    | Giá trị (BVA)                   | Kết quả                 |
|-----------------------------|---------------------------------|-------------------------|
| Trống                       | 0 ký tự                         | Lỗi bắt buộc (TC riêng) |
| Không hợp lệ — ngắn         | 7 ký tự (min−1)                 | Lỗi độ dài              |
| Hợp lệ                      | 8 (min), 20 (giữa), 32 (max)    | Chấp nhận               |
| Không hợp lệ — dài          | 33 ký tự (max+1)                | Lỗi độ dài              |
```

**Sau đó:** gộp theo kết quả:
- Các giá trị hợp lệ (min, giữa, max) → **1 TC** "chấp nhận", mỗi dòng Test Data là một giá trị cụ thể (không ghi "nhập 20 ký tự", phải ghi chuỗi thật).
- Các giá trị không hợp lệ cùng thông báo lỗi (min−1, max+1) → **1 TC**. Nếu thông báo lỗi khác nhau theo phía → tách 2 TC.
- Trống → TC bắt buộc nhập riêng.

**Đơn vị đếm:** nếu field nhận ký tự đa byte (hệ thống Nhật, tiếng Việt có dấu), mỗi biên max và max+1 chạy thêm 1 dòng với ký tự 全角/đa byte (và surrogate pair nếu field cho phép) để bắt lỗi đếm byte thay vì ký tự.

**Không có min/max trong AC:** không có biên để áp BVA → coi là AC TBD (xem `/gen-tcs` Bước 1), không tự đặt giá trị.

---

# Reference Library

## Platform Context Detection

Trước khi sinh TCs, agent **bắt buộc** xác định 3 điều sau — **suy ra từ file, không hỏi user** (trừ trường hợp ở dưới):
```
1. Platform: Web / Mobile / Desktop / Nhiều platform?
   → analysis.md Summary (Platform) → CLAUDE.md (Platform chính) → Quick Mode: spec.
   → Cả hai nguồn đều trống hoặc còn [...] : hỏi user MỘT lần trước khi sinh TC.
2. Multi-language: spec/CLAUDE.md (Locale) có nhắc đa ngôn ngữ không?
   → Không có dấu hiệu: không áp section Multi-Language, không hỏi.
3. Tính năng đặc thù (push notification, offline mode, v.v.): spec/AC có nhắc không?
   → Không nhắc: không áp dimension đó, không hỏi.
```

Sau khi xác định:
- Đọc `.claude/skills/testing_dimensions/SKILL.md` — section tương ứng với platform
- Áp thêm các dimension đó vào bộ TCs đang sinh (lớp bổ sung, không thay thế base TCs)
- Cross-platform: chỉ áp các section **có liên quan** đến feature đang test

### Platform Dimensions: áp theo module

- Áp **một lần cho cả module**, không lặp lại ở từng Screen/Component. Gom các TC này vào một nhóm Function Name riêng (VD `Platform – Mobile`), đặt cuối bảng TC của module.
- Chỉ chọn dimension mà module **thật sự có rủi ro** (VD module có tác vụ tải/ghép dài → background/kill app/mất mạng **khi đang chạy tác vụ đó**; module chỉ xem danh sách → không cần "có cuộc gọi đến", "xoay màn hình" cho từng màn).
- Mỗi dimension tối đa **1 TC đại diện** (chọn màn/tác vụ rủi ro nhất làm ví dụ). Chỉ thêm TC thứ hai khi hai ngữ cảnh có hành vi **khác nhau theo spec** (VD kill app khi đang Save khác kill app khi đang xem list vì có dữ liệu dở dang).

---

## Bảng Field-Level Validation

Khi form/UI có các input fields, agent **BẮT BUỘC** phải liệt kê từng trường và sinh validation TCs riêng theo loại:

| Loại Field | Validation cần test |
|---|---|
| **Text (Name, Address...)** | Required/Optional · Min length · Max length · Chỉ khoảng trắng (whitespace-only) · Ký tự đặc biệt (`<>&"'`) · XSS injection (`<script>alert(1)</script>`) · SQL injection (`' OR 1=1--`) · Unicode/Emoji · Leading/trailing spaces |
| **Email** | Format hợp lệ (`tester+format@dipro.vn`) · Thiếu `@` · Thiếu domain · Domain không hợp lệ · Nhiều `@` · Ký tự đặc biệt trước `@` · Max length · Case sensitivity · Email đã tồn tại (nếu unique) |
| **Phone** | Chỉ chấp nhận số · Prefix hợp lệ (ví dụ: `+84`, `0`) · Min/Max length · Chữ cái xen lẫn · Dấu `-`, `.`, khoảng trắng · Mã vùng không hợp lệ |
| **Date / DateTime** | Format đúng (dd/MM/yyyy, ISO...) · Ngày không tồn tại (`31/02`, `30/02`) · Năm nhuận (`29/02/2024`) · Ngày quá khứ / tương lai (tùy business rule) · Giá trị min/max date · Timezone (nếu áp dụng) |
| **Number / Currency** | Min/Max value · Số âm · Số 0 · Số thập phân · Ký tự không phải số · Overflow (số cực lớn) · Leading zeros · Định dạng currency (dấu phẩy, dấu chấm) |
| **Dropdown / Select** | Giá trị mặc định · Tất cả options hợp lệ · Option bị disabled · Thay đổi selection · Required validation (chưa chọn) |
| **Checkbox / Radio** | Trạng thái mặc định · Check/Uncheck · Required validation · Nhóm radio (chỉ chọn 1) |
| **File Upload** | File type hợp lệ/không hợp lệ · Max size · File rỗng (0 KB) · Tên file có ký tự đặc biệt · Multiple files (nếu cho phép) · Kéo thả vs nút chọn |
| **Password** | Min/Max length · Yêu cầu ký tự đặc biệt · Yêu cầu chữ hoa/thường · Yêu cầu số · Copy-paste bị chặn? · Hiện/ẩn password · Confirm password khớp/không khớp |
| **Textarea** | Max length · Line breaks · HTML tags · Resize (nếu UI cho phép) · Character counter (nếu có) |

> **Min/Max length và khoảng giá trị:** áp **Pattern 4 (EP + BVA)** trong Complex Logic Patterns, không sinh mỗi giá trị một TC.

> **Nguyên tắc:** Mỗi trường có đặc tính riêng → validation riêng. Agent PHẢI phân tích từng field trước khi sinh TCs, không được dùng chung 1 bộ validation cho tất cả fields.

---

## UI Policy (thay cho Visual States)

**Không sinh TC visual theo từng component/state.** Lý do: lỗi hiển thị thuần tuý được bắt bằng 1 lần đối chiếu design; sinh TC riêng cho từng state làm bộ TC phình ra mà ít phát hiện thêm lỗi.

**Mỗi Screen có đúng 1 TC UI:**
- Test Scenario: `Check giao diện màn hình [tên Screen] thống nhất với design`
- Expected Result: đúng một dòng `UI thống nhất với design`. Không thêm tên frame, không liệt kê chi tiết hiển thị, kể cả khi chưa có design.
- Đặt **ĐẦU** bảng TC của Screen. Không gắn tag `[UI Visual]`.

**Một thuộc tính UI chỉ được sinh TC riêng khi nó là giá trị nghiệp vụ hoặc thay đổi theo action/data** — và khi đó nó là TC Logic/Behavior, không phải TC UI:
- Màu/label/icon theo từng trạng thái dữ liệu (VD badge status, tag màu) → verify qua TC của rule status đó.
- Quy tắc truncate, format ngày/số/tiền do spec quy định → TC Data Display/Logic.
- Popup/dialog/toast/submenu hiện ra sau một action → verify nội dung và vị trí xuất hiện **ngay trong Expected Result của TC action đó**, không tách TC "Check hiển thị popup" riêng.
- Trạng thái Disabled/Error/Loading → verify trong TC của điều kiện gây ra nó (VD "Check nút Save bị disable khi chưa chọn item": Expected nêu rõ không tap được).

**Không sinh:** TC riêng cho placeholder/font/màu/border/focus/cursor/spacing của từng component.

## Vế của AC và điều kiện "Covered" (dùng chung `/gen-tcs` và `/review-tcs`)

**Vế** là một hành động, điều kiện hoặc kết quả của AC mà có thể kiểm chứng (pass/fail) độc lập với các vế khác. Cách tách:

- Từ nối ("rồi", "sau đó", "và") là dấu hiệu để xem xét tách vế, không bắt buộc tách. "Nhập họ và tên" → một vế; "hệ thống lưu dữ liệu và gửi email xác nhận" → hai vế vì mỗi hành vi pass/fail riêng.
- Một điều kiện ("khung giờ còn trống", "khi đã đăng nhập") → một vế riêng.
- Một kết quả quan sát được ("thành công", "hiển thị thông báo X", "không tạo bản ghi") → một vế riêng.
- Các giá trị cùng nhập trong một bước ("chọn phòng khám, ngày, khung giờ") → một vế.

VD AC "Patient chọn phòng khám, ngày, khung giờ còn trống rồi đặt lịch thành công" → vế 1: chọn phòng khám, ngày, khung giờ; vế 2: khung giờ được chọn còn trống; vế 3: đặt lịch thành công.

Một vế chỉ được tính **Covered** khi đồng thời: (1) Steps của một TC thực hiện hành động hoặc tạo điều kiện của vế đó; (2) Expected Result của TC đó kiểm chứng được kết quả mà vế đó yêu cầu. Chỉ có một trong hai là **Partial**, chưa tính là phủ. Một AC có thể được phủ bởi nhiều TC kết hợp; không bắt buộc một TC phủ mọi vế. Đọc theo nghĩa, không đối chiếu bằng từ khoá.

## Quy tắc gộp TC (chống phình số lượng)

Trước khi lưu, rà từng nhóm TC cùng Function Name:

| Tình huống | Xử lý |
|---|---|
| Cùng Steps, chỉ khác Test Data, cùng loại kết quả | Gộp **1 TC**, Test Data liệt kê từng dòng, Expected ghi tương ứng từng dòng |
| Cùng hành động nhưng kết quả khác (thành công vs lỗi, tier khác) | Tách TC riêng |
| TC chỉ khác nhau ở việc đổi nhãn/tên đối tượng (Front/Rear/Both, Folder A/B) mà luồng và rule giống nhau | Gộp, hoặc chọn 1 đại diện + 1 đối tượng có rule khác biệt |
| Hai TC cho cùng một rule ở hai Screen/popup khác nhau, cùng component dùng chung | Chỉ test 1 lần ở nơi rủi ro cao nhất, các nơi còn lại bỏ hoặc ghi chú |

Không gộp nếu: kết quả hoặc side-effect khác, rủi ro High, hoặc TC gắn Q&A riêng. Không gộp **nhiều field** vào 1 TC validation (xem Anti-Patterns) — quy tắc gộp chỉ áp cho cùng field/cùng hành vi khác data.

---

## Quy tắc Precondition

**Chỉ ghi Precondition khi cần thiết.** Precondition là trạng thái hệ thống hoặc dữ liệu phải có **trước** khi chạy Steps mà chính Steps không tự tạo. Không cần thì **để trống ô**, không ghi `—`.

**Không ghi:**
- Đăng nhập, "đang ở màn hình X" (Steps bắt đầu bằng việc mở màn hình). Chỉ nhắc vai trò khi **vai trò là điểm khác biệt của TC** (VD TC phân quyền), và ghi ở mức vai trò (VD: `Đăng nhập với role Hospital`), nằm trong Steps nếu là một hành động.
- Email, username, mật khẩu, mã tài khoản cụ thể. Tài khoản thuộc môi trường test, không phải nội dung của TC.
- Thông tin dùng chung cho cả sheet (tài khoản, môi trường, dữ liệu nền chung): thuộc dòng `Assumption môi trường test` ở đầu `test-cases.md`, không lặp vào từng TC.
- Tên riêng, mã định danh chỉ để gọi đối tượng (`Hospital A`, `Thao Pham`, `M1`) khi không cần phân biệt. Dùng danh từ chung (`Hospital`, `doctor`, `matching`); chỉ dùng "khác" khi TC cần hai đối tượng (`Hospital khác`).

**Cách viết:** mô tả **chung và ngắn gọn**, **mỗi điều kiện một dòng** (xuống dòng bằng `<br>`). Khi điều kiện đã có dữ liệu cụ thể ở cột Test Data thì tham chiếu `như Test Data`, không lặp lại giá trị.

```
❌ Sai: Đăng nhập hospital_a@example.jp (A総合病院); Hospital A đã review Thao Pham với comment theo Test Data
✅ Đúng: Hospital đã review doctor với comment như Test Data

❌ Sai: Đăng nhập hospital user hospital_a@example.jp   (TC chỉ kiểm tra giao diện màn hình)
✅ Đúng: (để trống)

✅ Đúng (nhiều điều kiện):
Doctor có matching đã contracted<br>Matching chưa được review
```

---

## Quy tắc Test Data

```
❌ Sai: "Nhập mã số hợp lệ"
✅ Đúng: "Nhập mã: KH-2026-0012"

❌ Sai: "Nhập email hợp lệ"
✅ Đúng: "Nhập email: tester+khachhang01@dipro.vn"

❌ Sai: "Nhập giá trị vượt giới hạn"
✅ Đúng: "Nhập 256 ký tự vào trường Name (max: 255)"
```

### Khi nào ghi Test Data

**Chỉ ghi Test Data khi cần thiết và phục vụ được TC.** Test Data là **giá trị đầu vào cụ thể** mà tester nhập hoặc chọn, hoặc dữ liệu nền mà **giá trị cụ thể quyết định kết quả** (VD comment dài đúng 1000 ký tự, bốn điểm sao để điểm trung bình ra 4.0). Không cần thì **để trống ô**, không ghi `—`.

**Không ghi:**
- Email, username, tài khoản đăng nhập (trừ khi email là giá trị đầu vào cần kiểm tra, VD TC validate field email hoặc TC đăng ký tài khoản).
- **Khi email là giá trị đầu vào thật** (đăng ký, nhập vào field email, gửi mail): dùng định dạng `tester+<mô tả ngắn>@dipro.vn` (VD `tester+hospital01@dipro.vn`, `tester+duplicate@dipro.vn`), mỗi TC cần email khác nhau thì đổi phần `<mô tả ngắn>`. Không dùng `example.com`, `domain.com` hay email giả khác.
- Tên người hoặc đối tượng chỉ để định danh (`Thao Pham`, `Matching M1`, `A総合病院`) khi giá trị đó không ảnh hưởng kết quả.
- **Mô tả trạng thái** (`Trạng thái: contracted`, `Review: chưa có`, `Matching M2 đang thương lượng`): đó là **Precondition**, không phải Test Data.
- Thông tin đã có ở Steps hoặc Precondition.

```
❌ Sai (HRD-003): Matching M2:<br>- Doctor: Hanh Tran<br>- 案件: test H spot<br>- Trạng thái: đang thương lượng
✅ Đúng: Precondition = "Doctor có matching đang thương lượng"; Test Data để trống

❌ Sai (HRD-052): Dòng 1: Hospital B (hospital_b@example.jp) xem tab 評価
✅ Đúng: Comment: 対応が丁寧で安心して依頼できました。
```

### Trình bày cột Test Data

**Mỗi field (hoặc mỗi giá trị) một dòng**, xuống dòng bằng `<br>`. Không nối nhiều field trên cùng một dòng bằng `;` hoặc `,`.

- Nhóm dữ liệu dùng chung (các field còn lại hợp lệ) ghi trước, mỗi field một dòng, dưới tiêu đề `Field còn lại (hợp lệ):`.
- Dữ liệu kiểm tra ghi sau, dưới tiêu đề `Dữ liệu kiểm tra:`. Nhiều dòng data thì mỗi dòng bắt đầu bằng `Dòng n:`; nếu một dòng data gồm nhiều field thì mỗi field một dòng con bắt đầu bằng `- `.
- Giá trị rỗng ghi `(để trống)`, khoảng trắng ghi rõ số lượng (`3 dấu cách`, `全角 space ×8`).
- Ký tự `<`, `>`, `&` trong chuỗi test (XSS, injection) viết **nguyên dạng** hoặc dạng entity (`&lt;` `&gt;` `&amp;`) đều được — khi export `.xlsx`, script tự đổi entity về ký tự thật.

```
❌ Sai: Field còn lại: Delivery Address = 25 Nguyen Hue, Quan 1, TP.HCM; Recipient = Nguyen Van An; Package Type = Parcel; Weight = 5; Service Type = Standard; Requested Delivery Date = 2026-10-10 Dòng 1: Pickup Address = (để trống) Dòng 2: Pickup Address = 3 dấu cách

✅ Đúng:
Field còn lại (hợp lệ):<br>Delivery Address: 25 Nguyen Hue, Quan 1, TP.HCM<br>Recipient: Nguyen Van An<br>Package Type: Parcel<br>Weight: 5<br>Service Type: Standard<br>Requested Delivery Date: 2026-10-10<br>Dữ liệu kiểm tra:<br>Dòng 1: Pickup Address = (để trống)<br>Dòng 2: Pickup Address = 3 dấu cách
```

---

## Output Format

```
| ID | Function Name | Category | Traceability ID | Test Scenario | Precondition | Steps | Expected Results | Test Data |
```

- **ID:** format `[MODULE]-[SỐ]` (VD: `ORD-001`) — `[MODULE]` dùng đúng **Mã module** trong Summary của `analysis.md` (cùng mã với ID Q&A `Q-ORD-001`)
- **Function Name:** Component dựng ở Section 3. **Quy ước đặt tên, giữ cố định giữa các lần sinh:** field nhập liệu dùng tên field đúng như trong spec/`analysis.md`, không thêm hậu tố "field" (VD "Weight", "Pickup Address"); nút `[Tên] button`; popup `[Tên] dialog`; bảng `[Tên] table`; TC UI của Screen `Màn hình [tên Screen]`; TC phân quyền `Permission – [Action]`; mỗi loại notification/sự kiện riêng `Notification – [sự kiện]`; TC nền tảng `Platform – [platform]`. TC mức flow (không gắn 1 component cụ thể) dùng tên flow (VD "Login Flow").
- **Category:** cấp con dưới Function Name — "UI"/"Validate"/"Behavior"/"Logic" (component-level) hoặc "Happy Path"/"Negative"/"Security" (flow-level).
- **Traceability ID:** ID nguồn gốc TC trace ngược tới — AC tương ứng từ `analysis.md` (VD: `AC-05`), hoặc Q&A ID nếu từ ambiguity (VD: `Q-LOG-001`), hoặc `N/A` nếu không có nguồn rõ ràng. Tên cột dùng chung cho mọi loại ID team quy ước (REQ ID, AC ID, Q&A ID, hoặc ID khác theo bảng quy ước riêng của team) — không giới hạn chỉ AC.
- **Test Scenario:** bắt đầu bằng "Check..." — xem "Rule ngôn ngữ Test Scenario" ở Section 4.
- **Precondition / Test Data:** chỉ ghi khi cần thiết, không cần thì để trống ô — xem "Quy tắc Precondition" và "Khi nào ghi Test Data". Steps không ghi email/tài khoản cụ thể, dùng vai trò (VD: `Đăng nhập bằng tài khoản Hospital khác`).
- **Steps / Expected Results:** đánh số, dùng `<br>` xuống dòng trong cell — **KHÔNG** dùng `|`, `/`, hay newline thô.

Khi export ra `.xlsx` qua `/export-xlsx`: **Sheet name = tên Screen** (heading `##` trong `test-cases.md`, lấy theo tên Screen đã dựng ở Section 3). Mỗi Screen điều hướng chính đúng **1 heading `##` duy nhất** — dù sinh TC chia làm nhiều lượt, kết quả vẫn gộp về cùng 1 heading/bảng. Nhóm theo chức năng bên trong sheet dùng cột Function Name, không tách heading.


## Mục High Risk & E2E (thay cho cột Risk Level và Priority)

Bảng TC **không có** cột Risk Level và Priority. Thay vào đó cuối `test-cases.md` có mục `## High Risk & E2E` gồm 2 bảng, export thành **một sheet gần cuối workbook** (tên sheet `High Risk & E2E`, đứng ngay trước sheet `Screen name_evidence`). Hai bảng ngăn cách bằng dòng nhãn đậm (**không** dùng heading `###`, vì `/export-xlsx` tách mỗi heading thành một sheet). Không thêm cột "nhóm chạy" vào bảng TC; QC lọc bằng danh sách ID trong hai bảng.

**Thứ tự chạy:** Bảng 2 (E2E) trước làm cổng, sau đó Bảng 1 theo thứ tự dòng, cuối cùng các TC còn lại.

### Bảng 1 — Nhóm TC high risk cần ưu tiên chạy

```
**Bảng 1 — Nhóm TC high risk cần ưu tiên chạy**

| # | Module (màn hình – function) | TC | Lý do | Ghi chú |
|---|---|---|---|---|
| 1 | Order List – Assign Driver, Retry | LDM-033, 034 | **Phân quyền:** Customer và Driver không được Assign Driver, Retry | |
| 2 | Order Detail – Delivery Fee | LDM-040, 041 | **Tiền:** phí tính lại sai khi actual weight đổi | LDM-041 `[UNCONFIRMED]` (Q-LDM-001, 005) |
```

- **#:** số thứ tự dòng, bắt đầu từ 1, tăng dần theo thứ tự dòng trong bảng (cũng là thứ tự chạy).
- **Module:** `Màn hình – Function Name` (màn hình = tên sheet TC).
- **TC:** liệt kê ID, dùng khoảng (`049–054`) khi liên tiếp. **Mỗi TC xuất hiện đúng một lần** trong cả bảng (nhóm theo lý do chính).
- **Lý do:** bắt đầu bằng nhãn nhóm đậm rồi giải thích. Các dòng **sắp xếp theo nhãn**, nhóm hậu quả nặng nhất lên trên, cùng nhãn nằm liền nhau.
- **Ghi chú:** mã Q&A, điều kiện chạy (VD "nên chạy sau khi PM trả lời Q-LDM-006"), TC `[UNCONFIRMED]`. Để trống nếu không có.
- **TC được chọn khi thuộc ít nhất một nhóm:**

| Nhóm | Nguồn xác định |
|---|---|
| **Phân quyền / bảo mật** | Các ô ❌ trong Permission Matrix (cả hàng sở hữu), TC Category Security |
| **Tiền** | Component Risk High liên quan phí/thanh toán; Q&A High về tiền |
| **Vòng đời và trạng thái không đảo ngược** | State Transition; trạng thái cuối (Cancelled, Completed); hủy sau mốc không hủy được |
| **Toàn vẹn dữ liệu và đồng thời** | Double-submit, hai người cùng thao tác, vượt capacity/giới hạn |
| **AC `[UNCONFIRMED]` mức High** | Q&A High chưa trả lời — ghi vào Ghi chú |
| **Ký tự và encoding** (chỉ khi `Locale: JP`) | Nhập sai lớp ký tự gây lỗi lưu hoặc hiển thị ở field quan trọng |

- Tối đa khoảng **5-6 nhóm lý do**; mục tiêu chiếm khoảng **20-30% tổng số TC**. Không lấy mọi TC thuộc component Risk High (tránh quay lại tình trạng một nửa bộ TC).
- Risk Level của component (Section 3) chỉ là **đầu vào** để suy ra bảng này, không xuất thành cột.

### Bảng 2 — Test E2E cần đảm bảo work trước

```
**Bảng 2 — Test E2E cần đảm bảo work trước**

| # | Luồng E2E | Các bước | TC phủ từng bước | Dữ liệu và thiết lập | Nếu fail thì |
|---|---|---|---|---|---|
| 1 | Tạo đơn đến Delivered | Customer tạo đơn → Operator assign → Driver Accept → Pickup → In Transit → Delivered | LDM-015, 021, 038 | 1 Customer, 1 Operator, 1 Driver Active (Web và Mobile) | Dừng chạy Order List, Order Detail, Driver Order, Notification |
```

- **Luồng E2E = một đường đi khác nhau qua vòng đời nghiệp vụ**, không phải biến thể dữ liệu: luồng chính (happy path) luôn có; thêm nhánh có ý nghĩa nghiệp vụ (thất bại rồi Retry, Cancelled, hủy); thêm luồng đi qua nhiều actor/thiết bị. Lấy từ các luồng E2E chính dựng ở Section 3.
- **Chỉ tham chiếu TC có sẵn**, không tạo TC mới Category E2E. Bước nào chưa có TC ghi `thiếu TC` (đây là kiểm tra độ phủ luồng chính).
- **Số luồng 3-6.** Vượt quá thì gộp (có thể đang tách theo biến thể dữ liệu).
- **Luồng #1 là cổng chính**; các luồng sau chạy sau khi #1 đạt. Cột **Nếu fail thì** nêu rõ nên dừng chạy phần nào.
- Luồng phụ thuộc điểm `[UNCONFIRMED]`: vẫn liệt kê, ghi chú trong "Dữ liệu và thiết lập" hoặc "Nếu fail thì" rằng cần Q&A trả lời trước khi tin kết quả.

---

## Anti-Patterns (NGHIÊM CẤM)

- ❌ **Sinh TC thừa hoặc trùng**: cùng Steps chỉ khác data/đối tượng mà không gộp; cùng kịch bản do nhiều tầng sinh; TC mà Expected đã được verify ở TC khác — xem R1-R4 trong Self-Check của `/gen-tcs`
- ❌ **Sinh TC từ dòng checklist khi spec im lặng và không có nguồn** (AC/ASM/`CLAUDE.md`/bộ chuẩn của kit) hoặc Expected không đo được — xem "TC Gate" trong `/gen-tcs`
- ❌ **Gộp/xoá TC phủ ô ❌ của Permission Matrix, AC High hoặc TC gắn Q&A riêng** khi rà thừa
- ❌ Sinh test data chung chung / placeholder
- ❌ Chỉ có Happy Path, thiếu Negative/Boundary cases
- ❌ Test Steps mơ hồ, không ghi rõ dữ liệu nhập
- ❌ Gộp validation nhiều trường vào 1 test case → mỗi trường phải có TC validation riêng
- ❌ Dùng chung 1 bộ validation cho tất cả fields (Email ≠ Phone ≠ Date ≠ Text)
- ❌ Bỏ qua security validation (XSS, SQL injection) cho text/textarea fields
- ❌ Không liệt kê danh sách fields trước khi sinh validation TCs
- ❌ **Sinh TC visual theo từng component/state** (Normal, Focus, Error, Disabled, Loading) — chỉ có 1 TC UI cho mỗi Screen, xem "UI Policy"
- ❌ **Lặp Platform Dimensions** (background, kill app, xoay màn hình, cuộc gọi...) ở từng Screen/Component — áp một lần cho cả module
- ❌ Sinh TCs khi chưa xác định được platform (Summary và `CLAUDE.md` đều trống mà không hỏi user)
- ❌ Bỏ qua `testing_dimensions` khi đã biết platform
- ❌ Rút gọn hoặc bỏ sót test case khi mapping sang bảng
- ❌ Sinh tất cả test cases 1 lần cho hệ thống lớn (phải chia theo Screen)
- ❌ **Viết Test Scenario dạng ký hiệu rút gọn** (mũi tên, gạch chéo nén ý, dấu hai chấm nén nhiều ý) thay vì câu tự nhiên hoàn chỉnh
- ❌ **Sinh TC mà không lưu Summary + System Model vào `analysis.md`** khi `/gen-tcs` auto-chain `/analyze-req` — file phải có đủ để user đọc lại. (`/gen-tcs` luôn in tóm tắt cấu trúc ở đầu output.)
- ❌ **Đoán Component Type qua keyword AC text** khi đã xác định Component Type ở Section 3 — phải tra trực tiếp
