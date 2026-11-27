# Tiêu chí review TCs (v3)

Nguồn chuẩn duy nhất cho `/review-tcs`. Cách chạy (thứ tự bước, chia agent, format file) nằm ở `.claude/commands/review-tcs.md`.

---

## 1. Mindset

Câu hỏi gốc của review: **"Có chỗ nào có thể bị lọt bug không?"**

1. **Con mắt thứ hai, đánh giá kết quả.** Review không kiểm "gen có chạy đúng skill không". Skill chỉ là nguồn tham chiếu cho chuẩn chất lượng.
2. **Độc lập với gen.** Reviewer tự đối chiếu với spec gốc, không tin hoàn toàn vào `analysis.md` hay danh sách scenario mà gen đã sinh.
3. **Hỏi "bug nào lọt qua được bộ TC này?"** thay vì "TC này vi phạm quy tắc nào?".
4. **Tier theo hậu quả và mức rủi ro của AC**, không theo loại lỗi (xem 5.4).
5. **Mỗi finding có bằng chứng, lý do cần fix và đề xuất cụ thể.**
6. **Review không tự sửa TC.** Người được review quyết định.
7. **Thiếu input thì không đoán.** Ghi vào "Chưa kiểm tra được".

**Phân vai gen và review:** tiêu chí nào kiểm được cơ học trên chính input/output của gen thì nằm trong Self-check của `gen-tcs`. Review giữ các kiểm tra cần nguồn ngoài (spec gốc), phán đoán nội dung, hoặc nhìn cả bộ TC. Hai skill dùng chung định nghĩa chuẩn nhưng khác nguồn đối chiếu (xem 5.7).

**Phân vai máy, AI và người:** script `.claude/scripts/review_checks.py` chạy trước phần máy kiểm được (mục 5.8). AI chạy toàn bộ 17 mục, dùng kết quả script thay vì tự dò lại. Người review cuối chỉ cần duyệt các finding loại *Cần người xác nhận*, mục "Chưa kiểm tra được" và các finding Critical loại *AI phán đoán*.

---

## 2. Đầu vào và chế độ review

| Chế độ | Input | Ghi chú |
|---|---|---|
| Full | File TC + `analysis.md` + spec gốc (+ diagram, design nếu có) | Review đủ 8 nhóm |
| Quick | File TC + spec | Không có `analysis.md` và Q&A; REQ-xx thay AC-xx |

- Thiếu spec: vẫn review phần còn lại. 02.1, 01.2 và mục 5.2 ghi "Chưa kiểm tra được". Báo rõ "AC lấy từ `analysis.md`, chưa đối chiếu spec gốc".
- Thiếu `analysis.md` (còn spec): chạy chế độ Quick.
- **BLOCKED** chỉ khi không có nguồn chuẩn nào (cả `analysis.md` lẫn spec) hoặc không có file TC. Thiếu một input phụ không làm BLOCKED toàn bộ.
- **Nguồn REQ-xx ở bản Quick:** review lấy danh sách REQ-xx mà gen đã tách làm gốc để khỏi lệch đánh số. Sau đó review tự đọc spec và báo thêm yêu cầu spec có mà gen không tách (finding thuộc REV-01.1).
- **Mức rủi ro AC ở bản Quick:** bản Quick không có risk level, trong khi tier (5.4), Bảng 1 (REV-07) và quy tắc negative đều dựa vào AC High. Reviewer tự gán High / Medium / Low cho từng REQ hoặc AC theo định nghĩa ở 5.4 và **in bảng gán ở đầu phụ lục** để người duyệt. Các finding phụ thuộc cách gán này ghi loại *Cần người xác nhận*.
- **Module** = một file TC. File gộp nhiều feature thì luồng giữa các feature trong file xét ở REV-01.1 và 01.2.

---

## 3. Bộ tiêu chí: 8 nhóm, 17 mục con

Mã REV là đề xuất. "Mức kiểm": **TC** = đánh giá từng TC, **Bộ** = đánh giá cả bộ TC. "Gen tự kiểm?" tính theo `gen-tcs.md`. "Góc nhìn": A = Tính đúng đắn, B = Khả năng phát hiện bug, C = Khả năng thực thi và duy trì (xem 5.5).

| Mã | Tiêu chí | Mức kiểm | Góc nhìn | Gen tự kiểm? | Tier mặc định (chỉ để tham khảo, tier thật theo 5.4) |
|---|---|---|---|---|---|
| **Nhóm 01 — Độ phủ kiểm thử** | | | | | |
| REV-01.1 | AC Coverage theo vế | Bộ | B | Có (C1) | Critical |
| REV-01.2 | Phủ kịch bản ngoài AC | Bộ | B | Không | Major |
| REV-01.3 | Kỹ thuật thiết kế test (gồm diagram) | Bộ | B | Một phần (E1, D1) | Major |
| REV-01.4 | Negative (gồm phân quyền theo từng ô ❌) | Bộ | B | Có (M2, P1) | Major |
| REV-01.5 | Platform và Environment | Bộ | B | Một phần | Minor |
| REV-01.6 | Component và Domain | Bộ | B | Một phần | Minor |
| **Nhóm 02 — Đúng theo yêu cầu** | | | | | |
| REV-02.1 | Expected đúng spec | TC | A | Một phần | Critical |
| REV-02.2 | Nhất quán với `analysis.md` | Bộ | A | Có | Major |
| **Nhóm 03 — Steps và Expected** | | | | | |
| REV-03.1 | Steps tái hiện được | TC | C | Không | Critical |
| REV-03.2 | Expected kiểm chứng được | TC | A | Có (C3) | Critical |
| **Nhóm 04 — Chất lượng thiết kế TC** | | | | | |
| REV-04.1 | Một TC một mục tiêu chính | TC | C | Có (O1) | Major |
| REV-04.2 | Không trùng lặp, không thừa | Bộ | C | Có (R1–R4) | Minor / Suggestion |
| **Nhóm 05 — Dữ liệu và điều kiện tiên quyết** | | | | | |
| REV-05.1 | Test Data cụ thể | TC | C | Có (C2) | Critical |
| REV-05.2 | Precondition dựng lại được | TC | C | Một phần (L3) | Major |
| **Nhóm 06 — Độc lập và dễ bảo trì** | | | | | |
| REV-06 | TC Independence | Bộ | C | Có (M1 mở rộng) | Major |
| **Nhóm 07 — Truy vết và quản lý** | | | | | |
| REV-07 | Bảng High Risk & E2E | Bộ | B | Có (Q1–Q3) | Major |
| **Nhóm 08 — Rõ ràng, nhất quán** | | | | | |
| REV-08 | Format và quy ước nhất quán | TC | C | Có | Minor |

**Thứ tự ưu tiên kiểm:** đi từ nhóm 01 đến nhóm 08.

---

## 4. Chi tiết từng mục

### REV-01.1 AC Coverage theo vế
- **Câu hỏi:** từng vế của mỗi AC có TC mà Steps thực hiện vế đó và Expected kiểm chứng vế đó không?
- **Đối chiếu với:** danh sách AC (đã đối chiếu spec); bản Quick: REQ-xx (xem mục 2).
- **Cách kiểm:** (1) tách AC thành vế theo quy tắc ở mục 5.3; (2) với mỗi vế, tìm TC trong Traceability ID; (3) đánh giá **Steps** và **Expected** riêng; (4) gán trạng thái (mục 5.3); (5) chiều ngược: liệt kê TC không trace AC nào và phân loại: *Risk-based* (có căn cứ ở REV-01.2), *Technical/Platform* (kỹ thuật hoặc môi trường), *Unjustified* (không có căn cứ, không rõ mục tiêu), *Chưa xác định*. Thiếu Traceability ID không tự động là finding; chỉ *Unjustified* mới cần xem xét finding (thuộc REV-04.2 phần thừa).
- **Report:** chỉ in vế Partial, Not Covered, Chưa kiểm tra được kèm bằng chứng. Vế Covered chỉ in số đếm theo AC (xem 5.6).
- **Đạt khi:** mọi vế Covered, với Covered = Steps thực hiện vế **và** Expected kiểm chứng vế. Một AC có thể được phủ bởi nhiều TC kết hợp.
- **Lưu ý:** đọc theo nghĩa, không dò từ khoá.

### REV-01.2 Phủ kịch bản ngoài AC
- **Câu hỏi:** có kịch bản liên quan hành vi hoặc rủi ro của chức năng mà không AC nào nêu và chưa có TC không?
- **Đối chiếu với:** spec và quy trình nghiệp vụ; reviewer tự dựng danh sách.
- **Cách kiểm:** hai bước. (1) Xác định kịch bản có liên quan đến hành vi, kiến trúc, rủi ro của chức năng không (thứ tự thao tác, đồng thời như 2 người hoặc 2 tab, gián đoạn, dữ liệu rỗng hoặc lớn). (2) Nếu liên quan, xác định có cần TC không; nếu không cần thì ghi lý do.
- **Đạt khi:** mọi kịch bản liên quan có TC hoặc có lý do không cần. Thiếu TC không tự động là lỗi nếu không có căn cứ rủi ro.
- **"Dữ liệu lớn":** lấy theo giới hạn có trong spec (phân trang, số bản ghi tối đa, dung lượng file). Spec không nêu thì không tự đặt ngưỡng, ghi vào danh sách cần hỏi PM/BA.

### REV-01.3 Kỹ thuật thiết kế test
- **Câu hỏi:** bộ TC có phủ đủ theo các kỹ thuật phù hợp với constraint và logic thật của requirement không?
- **Đối chiếu với:** constraint, bảng quyết định, sơ đồ trạng thái dựng từ spec; diagram lifecycle và workflow (nếu có).
- **Cách kiểm:** reviewer xác định kỹ thuật phù hợp rồi đánh giá theo kỹ thuật đã chọn (không bắt buộc áp dụng mọi kỹ thuật):
  - **EP:** đủ lớp hợp lệ và không hợp lệ có thật (rỗng, sai kiểu, âm, quá dài...).
  - **BVA:** các biên có thật. Chỉ có "≥ 18" thì chỉ có biên dưới.
  - **Decision Table** (gồm vai trò × chức năng): các rule và kết quả có ý nghĩa, không đòi mọi tổ hợp.
  - **State Transition:** chuyển hợp lệ có TC; chuyển bị cấm có TC negative khi có rủi ro. Khi có diagram: mỗi chuyển trạng thái (kể cả tới trạng thái cuối và đường lùi) và mỗi nhánh có nhãn của workflow có TC.
- **Diagram lệch text:** phần có trong diagram mà spec/`analysis.md` không nêu thì không đòi TC; ghi finding loại *Cần người xác nhận*.
- **Đạt khi:** mỗi kỹ thuật được áp dụng đều đạt. Kỹ thuật không áp dụng ghi lý do.

### REV-01.4 Negative
- **Câu hỏi:** mỗi AC có TC negative không, và các nhóm rủi ro có căn cứ có bị bỏ sót không?
- **Đối chiếu với:** danh sách AC, spec, Permission Matrix.
- **Cách kiểm:** ba lớp.
  1. **Theo từng AC** (khớp quy ước gen): mỗi AC happy path có ≥1 TC negative của chính AC đó. Negative của AC này không thay được cho AC khác.
  2. **Phân quyền theo từng ô:** mỗi ô ❌ của Permission Matrix (kể cả hàng "thao tác trên dữ liệu của người khác") có ≥1 TC hoặc ≥1 dòng Test Data. Không đếm chung theo nhóm. Không có ma trận: xử lý như REV-07.
  3. **Theo nhóm rủi ro còn lại**, để không sót loại negative quan trọng: input validation, vi phạm business rule, trạng thái không hợp lệ, xử lý ngoại lệ, toàn vẹn dữ liệu. Mỗi nhóm áp dụng có ≥1 TC negative.
- **TC negative** là TC có Expected báo lỗi, từ chối, chặn hoặc không thực hiện được. AC không có đối lập negative có ý nghĩa (ví dụ chỉ hiển thị dữ liệu) thì ghi "không áp dụng" kèm lý do. AC mà nội dung tự thân là nhánh lỗi (ví dụ "đăng nhập thất bại thì báo lỗi") tính là đã có negative. Danh sách ứng viên K8 của script chỉ dò theo từ khoá nên có thể sót; AI vẫn tự xét từng AC.
- **Đạt khi:**
  - AC đã xác nhận: có ≥1 TC negative của chính AC đó, hoặc ghi "không áp dụng" kèm lý do.
  - AC High: không được miễn negative.
  - Mọi ô ❌ có ít nhất 1 TC hoặc 1 dòng Test Data.
  - Mỗi nhóm rủi ro áp dụng có ≥1 TC negative.
- **Ngoại lệ (chỉ bản Full):** AC `[UNCONFIRMED]` Medium/Low chỉ cần 1 TC đại diện theo thiết kế của gen. **TC đại diện này không được tính là coverage đã xác nhận**; report ghi riêng. Bản Quick không có trạng thái `[UNCONFIRMED]` nên không có ngoại lệ này.

### REV-01.5 Platform và Environment
- **Câu hỏi:** có dimension theo môi trường nào bị thiếu không?
- **Đối chiếu với:** Platform và Locale (Summary của `analysis.md` hoặc `CLAUDE.md`), skill `testing_dimensions`.
- **Cách kiểm:** lấy dimension của platform (Web: Back, F5, nhiều tab, hết phiên; Mobile: gesture, offline...). Chỉ chọn dimension có rủi ro thật với module.
- **Đạt khi:** mỗi dimension áp dụng có TC hoặc có lý do không áp dụng.

### REV-01.6 Component và Domain
- **Câu hỏi:** quy tắc theo loại component hoặc domain có được phủ không?
- **Đối chiếu với:** skill `component_checklist`, `jp_validation` (khi Locale = JP).
- **Cách kiểm:** Locale = JP thì xác định loại từng field nhập liệu (họ tên, furigana, địa chỉ, số điện thoại, mã bưu điện, email, free-text...) và kiểm các quy tắc `jp_validation` tương ứng loại đó; không áp quy tắc không liên quan đến loại dữ liệu của field. Có form hoặc layout thì kiểm `component_checklist` theo Component Type.
- **Đạt khi:** mỗi quy tắc áp dụng có TC hoặc có lý do không áp dụng.
- **Tier:** không tự nâng lên Major chỉ vì Locale = JP; tier theo hậu quả từng finding (lỗi format Furigana khác lỗi không nhập được tên người Nhật).

### REV-02.1 Expected đúng spec
- **Câu hỏi:** Expected của mỗi TC có khớp spec gốc không?
- **Đối chiếu với:** spec gốc (và AC).
- **Cách kiểm:** với mỗi TC, tìm câu trong spec làm căn cứ cho Expected. Phân loại: **Explicit** (spec ghi trực tiếp), **Derived** (suy ra hợp lý từ rule đã xác nhận), **Unconfirmed** (dựa giả định chưa xác nhận), **Contradiction** (mâu thuẫn spec). Với Contradiction phải trích nguyên câu spec làm bằng chứng; không trích được thì không kết luận Contradiction.
- **Bộ TC lớn:** áp quy tắc lấy mẫu ở 5.6.
- **Report:** chỉ in Unconfirmed và Contradiction; không cần đếm Explicit/Derived.
- **Đạt khi:** không có Contradiction. Unconfirmed được liệt kê riêng để hỏi PM/BA.
- **Unconfirmed chưa gắn nhãn:** TC khẳng định hành vi mà spec còn ghi "to be confirmed / to be decided / TBD" (bản Quick), hoặc AC còn TBD (bản Full), nhưng không gắn `[ASSUMED]` / `[UNCONFIRMED]` là finding Minor (ứng viên K9 của script).
- **Nghi spec có lỗi:** chỗ spec có vẻ gõ nhầm hoặc tự mâu thuẫn không phải lỗi của TC; đưa vào danh sách hỏi PM/BA với nhãn "Nghi lỗi spec".
- **Khi thiếu nguồn:** ghi "Chưa kiểm tra được: không có spec gốc".
- **Gợi ý tier:** Contradiction là Critical. Unconfirmed không phải lỗi, chỉ là danh sách cần xác nhận.

### REV-02.2 Nhất quán với `analysis.md` (bản Full)
- **Câu hỏi:** TC có khớp trạng thái Q&A hiện tại không?
- **Đối chiếu với:** `analysis.md` (AC `[UNCONFIRMED]`, mã Q&A, ASM, DIF).
- **Cách kiểm:** liệt kê AC `[UNCONFIRMED]` và mã Q&A. AC đã được trả lời thì không còn ngoại lệ. AC còn mở thì TC không được khẳng định Expected. Đối chiếu thêm ASM và DIF: TC không được dùng quyết định đã bị thay thế hoặc chưa xác nhận như thể đó là behavior chính thức.
- **Đạt khi:** TC khớp trạng thái Q&A, ASM, DIF hiện tại.

### REV-03.1 Steps tái hiện được
- **Câu hỏi:** tester chưa biết hệ thống có chạy được TC mà không phải đoán không?
- **Đối chiếu với:** chính TC (và môi trường test nếu có).
- **Cách kiểm:** đọc Steps như tester mới. Mỗi bước là hành động đủ rõ, có đối tượng và điều kiện cụ thể (không bắt buộc một thao tác vật lý mỗi bước). Dữ liệu lấy từ Test Data. Đánh giá tĩnh vẫn phát hiện được Steps mơ hồ, ví dụ "Nhập thông tin hợp lệ" mà Test Data không chỉ rõ thông tin nào. Chỉ ghi "Chưa kiểm tra được" với khía cạnh cần chạy thật mới xác minh (ví dụ tên nút có đúng trên môi trường); không dùng để bỏ qua đánh giá độ rõ của Steps.
- **Đọc hết mọi TC**, không lấy mẫu.
- **Đạt khi:** không bước nào phải đoán; Steps và Expected khớp nhau.

### REV-03.2 Expected kiểm chứng được
- **Câu hỏi:** Expected có quan sát và xác định được pass/fail khách quan không?
- **Cách kiểm:** tìm cụm mơ hồ ("hiển thị đúng", "thành công", "nhanh"). "Hiển thị đúng" chỉ chấp nhận khi nêu rõ đối tượng và đối chiếu được với Test Data hoặc Steps. Expected có thể kiểm chứng qua UI, thông báo, trạng thái, dữ liệu, hành vi phân quyền; không nhất thiết là giá trị cố định.
- **Ngoại lệ:** TC UI tổng thể có Expected "UI thống nhất với design" theo UI Policy của skill `rbt_manual_testing` không tính là mơ hồ.
- **Đạt khi:** mọi Expected có thể xác minh được.

### REV-04.1 Một TC một mục tiêu chính
- **Câu hỏi:** TC có gom nhiều mục tiêu không liên quan không?
- **Đối chiếu với:** chính TC.
- **Cách kiểm:** đọc tiêu đề, Steps, Expected. Nhiều Steps và nhiều Expected được phép khi cùng phục vụ một mục tiêu. Đánh giá theo sự liên quan giữa các hành vi, không đặt ngưỡng số Expected.
- **Đạt khi:** mỗi TC có một mục tiêu chính.

### REV-04.2 Không trùng lặp, không thừa
- **Câu hỏi:** (a) có TC nào trùng mục tiêu, hành động, dữ liệu và kết quả với TC khác không? (b) có TC nào không bắt được bug nào mà TC khác chưa bắt không?
- **Đối chiếu với:** chính bộ TC.
- **Cách kiểm:** (a) nhóm TC theo Traceability ID, so Steps, Test Data, Expected. TC khác role, state, biên hoặc requirement không bị coi là trùng dù Steps gần giống. (b) với TC bị nghi thừa (gồm TC *Unjustified* từ REV-01.1), thử nêu một lỗi cụ thể chỉ TC này phát hiện được; không nêu được thì là thừa.
- **Tier:** (a) trùng thật sự là Minor; (b) thừa là Suggestion. Không bao giờ đề xuất xoá TC của AC High, ô ❌ hoặc bộ chuẩn Field-Level chỉ vì nghi thừa.
- **Đạt khi:** không có cặp TC trùng thật sự.

### REV-05.1 Test Data cụ thể
- **Câu hỏi:** Test Data có đủ cụ thể để tái hiện không?
- **Cách kiểm:** tìm placeholder ("hợp lệ", "đúng", "bất kỳ", "tùy ý").
- **Ranh giới với REV-03.1:** REV-03.1 lo khả năng thực hiện Steps, REV-05.1 lo độ cụ thể của dữ liệu. Cùng một nguyên nhân (ví dụ Steps "Nhập thông tin hợp lệ" và Test Data "Thông tin hợp lệ") thì gộp thành một finding, dẫn cả hai mã.
- **Đạt khi:** ô đã ghi là giá trị cụ thể. Giữ quy ước manual testing; chỉ cho phép biến tham số hoá nếu team thống nhất dùng Data Matrix riêng.
- **Hợp lệ:** biến ghi lại giá trị quan sát lúc chạy khi Steps nói rõ cách đọc giá trị đó; nhãn mô tả lớp dữ liệu đi kèm giá trị cụ thể (ví dụ "Field còn lại (hợp lệ): Câu hỏi: ...").

### REV-05.2 Precondition dựng lại được (mới)
- **Câu hỏi:** tester có tự chuẩn bị được trạng thái ban đầu từ Precondition không?
- **Cách kiểm:** đọc Precondition như tester mới. Lỗi khi: (1) mô tả quá chung, không biết dựng thế nào (ví dụ "Có đơn hàng" trong khi TC cần đơn ở trạng thái cụ thể); (2) thiếu điều kiện mà Steps/Expected ngầm cần (ví dụ Expected "hiển thị 3 bản ghi" nhưng Precondition không nói có 3 bản ghi); (3) trỏ tới mã TC khác thay vì mô tả trạng thái (finding thuộc REV-06). Precondition để trống là hợp lệ khi Steps tự đủ.
- **Ranh giới với REV-05.1:** trạng thái dữ liệu thuộc Precondition, giá trị nhập thuộc Test Data.
- **Đạt khi:** mọi trạng thái mà Steps và Expected cần đều được mô tả đủ để dựng lại.

### REV-06 TC Independence
- **Câu hỏi:** TC có chạy được với precondition ghi rõ, không dựa vào thứ tự chạy hay trạng thái ẩn không?
- **Cách kiểm:** (1) tìm tham chiếu tới TC khác ("xem TC", "như TC", "các TC sau", "bước trước", mã TC) trong Precondition, Steps, Expected và Test Data (script K3); (2) nhóm TC theo Test Data trùng, kiểm cặp TC cùng sửa trạng thái dữ liệu gây ảnh hưởng nhau. Phân biệt ba trường hợp:
  - *Hidden dependency*: TC cần trạng thái do TC khác tạo ra mà không khai báo. **Là finding.**
  - *Shared mutable data*: nhiều TC dùng chung dữ liệu có thể bị đổi (ví dụ TC A đổi đơn sang Cancelled rồi TC B cần đơn chưa Cancelled). **Chỉ là finding khi thực sự ảnh hưởng kết quả.** Dùng chung Test Data không tự động là xung đột.
  - *Explicit precondition*: Precondition **mô tả trạng thái** cần có (ví dụ "Đơn ở trạng thái Waiting"). **Hợp lệ.** Precondition **trỏ tới mã TC** (ví dụ "Đã chạy TC-003") **không** được coi là khai báo rõ, vẫn là finding.
- **Đạt khi:** không TC nào trỏ tới mã TC khác; không cặp TC nào làm lệch dữ liệu của nhau khi chạy liên tiếp.

### REV-07 Bảng High Risk & E2E (mức bộ TC)
- **Câu hỏi:** hai bảng có đúng và đủ để quyết định thứ tự chạy không?
- **Đối chiếu với:** Permission Matrix, luồng E2E chính.
- **Khi không có Permission Matrix:** spec có phân quyền nhưng không có ma trận → "Chưa kiểm tra được"; chức năng không có phân quyền → "Không áp dụng". Không tự suy toàn bộ permission từ tên role.
- **Cách kiểm:** (1) mọi ID còn tồn tại trong bảng TC; (2) Bảng 1 phủ mọi ô ❌ (nếu có ma trận) và TC của AC High; (3) Bảng 2 phủ luồng chính, mỗi bước có TC hoặc ghi `thiếu TC`.
- **Đạt khi:** cả 3 kiểm đều đạt.
- **Ngưỡng của gen** (~30% tổng TC cho Bảng 1, 3–6 luồng cho Bảng 2): review chỉ cảnh báo Minor khi vượt, không kết luận không đạt.
- **Không đòi** cột "TC phủ từng bước" ghép từng bước với từng TC: mẫu trong skill `rbt_manual_testing` ghi danh sách TC liền nhau. Chỉ báo khi có bước rõ ràng không có TC nào phủ.

### REV-08 Format và quy ước nhất quán
- **Câu hỏi:** các TC có cùng quy ước không?
- **Cách kiểm:** so tên cột, định dạng, dấu câu giữa các TC.
- **Đạt khi:** mọi TC cùng một quy ước.
- **Lưu ý tier:** lỗi format làm `/export-xlsx` hỏng hoặc mất dữ liệu (sai tên cột, vỡ bảng) tính theo hậu quả, có thể là Major.

---

## 5. Quy tắc chung

### 5.1 Nguồn chuẩn
Spec gốc là nguồn chuẩn khi đối chiếu. `analysis.md` do AI dựng từ spec nên có thể sót hoặc hiểu sai.

### 5.2 AC lệch spec
Review đối chiếu mọi AC với spec, kể cả AC trông rõ ràng. Chỗ lệch được liệt kê trong mục riêng của report (AC, `analysis.md` ghi gì, spec ghi gì, TC đang theo bên nào, ai xác nhận). Review không dừng để hỏi.

| Loại lệch | Mức |
|---|---|
| Lệch lớn: đổi hành vi, điều kiện, phân quyền, số liệu | Critical |
| Lệch nhỏ: wording, nhãn, định dạng | Minor |
| Đã ghi nhận qua Q&A đã trả lời, ASM, DIF | Không tính finding |

Phần liên quan AC lệch lớn ghi "cần xác nhận". Dùng chung phân loại nhỏ/lớn với `gen-tcs` (Bước 1). Không chắc nhỏ hay lớn thì coi là lớn.

### 5.3 Vế và Covered
- **Vế:** một hành động, điều kiện hoặc kết quả của AC có thể kiểm chứng độc lập (pass hoặc fail riêng). Từ nối ("rồi", "sau đó", "và") là dấu hiệu để xem xét tách vế, không phải điều kiện tách bắt buộc. Ví dụ "nhập họ và tên" là một vế; "hệ thống lưu dữ liệu và gửi email xác nhận" là hai vế vì mỗi hành vi pass/fail riêng. Các giá trị cùng nhập trong một hành động là một vế nếu không cần kiểm chứng độc lập. Một điều kiện là một vế riêng. Một kết quả quan sát được là một vế riêng.
- Ví dụ: "Patient chọn phòng khám, ngày, khung giờ còn trống rồi đặt lịch thành công" → vế 1: chọn phòng khám, ngày, khung giờ; vế 2: khung giờ còn trống; vế 3: đặt lịch thành công.
- **Covered** khi Steps thực hiện vế đó **và** Expected kiểm chứng vế đó.

| Trạng thái | Nghĩa |
|---|---|
| Covered | Steps và Expected đều xác minh vế |
| Partial | Chỉ có Steps hoặc chỉ có Expected, hoặc kiểm một phần |
| Not Covered | Không có TC phù hợp |
| Chưa kiểm tra được | Thiếu thông tin để xác định (AC lệch spec, thiếu spec...) |

### 5.4 Tier và verdict

| Tier | Ý nghĩa |
|---|---|
| Critical | Sai hoặc thiếu hành vi quan trọng; có nguy cơ xác nhận sai chức năng hoặc làm tester chạy sai |
| Major | Thiếu coverage hoặc sai logic có ảnh hưởng đáng kể |
| Minor | Vấn đề rõ ràng, nhất quán, bảo trì; không ảnh hưởng đáng kể đến khả năng xác minh |
| Suggestion | Cải thiện chất lượng, không bắt buộc sửa |

**Cách xác định tier của một finding:** xét hai yếu tố.
1. **Hậu quả:** nếu bỏ qua finding này thì điều gì xảy ra (lọt bug, tester chạy sai, chỉ khó đọc).
2. **Mức rủi ro của phần bị ảnh hưởng:** AC High (tiền, bảo mật, phân quyền, dữ liệu) > Medium > Low.

| Hậu quả \ Rủi ro AC | High | Medium | Low |
|---|---|---|---|
| Có thể lọt bug hoặc xác nhận sai chức năng | Critical | Major | Minor |
| Tester phải đoán hoặc không chạy được như đã viết | Major | Major | Minor |
| Chỉ ảnh hưởng thứ tự chạy, ưu tiên (Bảng 1, Bảng 2) | Minor | Minor | Minor |
| Chỉ ảnh hưởng đọc hiểu, bảo trì | Minor | Minor | Minor |

Bảng trên là gợi ý mặc định; reviewer được lệch một bậc nếu ghi lý do. Loại kiểm (5.5) không quyết định tier.

| Tier | Bắt buộc sửa trước khi chấp nhận bộ TC? |
|---|---|
| Critical, Major | Có |
| Minor | Không bắt buộc, ghi nhận riêng (team quyết) |
| Suggestion | Không |

| Verdict | Điều kiện |
|---|---|
| PASS | Không có Critical, Major và mọi mục áp dụng đều đã kiểm được |
| PASS có điều kiện | Không có Critical, Major nhưng còn mục "Chưa kiểm tra được" hoặc "Kiểm một phần" (thiếu spec, thiếu Permission Matrix, AC còn TBD...). Report nêu rõ phần nào chưa kiểm và ai bổ sung |
| NEEDS FIX | Có ≥1 Critical hoặc Major |
| BLOCKED | Không có nguồn chuẩn nào hoặc không có file TC |

Cạnh verdict luôn in **độ phủ của review**: `Đã kiểm X/17 mục · Kiểm một phần P · Không áp dụng Y · Chưa kiểm tra được Z`. "Kiểm một phần" là mục đã kiểm nhưng còn phần không kết luận được (ví dụ vế AC còn TBD, mức rủi ro AC do reviewer tự gán).

### 5.5 Finding và report
- Mỗi finding gồm: mã tiêu chí, TC hoặc AC liên quan, bằng chứng, **lý do cần fix**, đề xuất cụ thể, và **loại kiểm**: *Máy kiểm được* (format, tham chiếu TC, placeholder, trùng mẫu), *AI phán đoán* (logic Expected, coverage theo nghĩa, kịch bản ngoài AC), hoặc *Cần người xác nhận* (behavior chưa xác nhận, AC lệch spec, diagram lệch text, ngoại lệ nghiệp vụ). Finding *AI phán đoán* ghi thêm **độ chắc chắn** (cao / trung bình / thấp). *AI phán đoán* vẫn có thể là Critical hoặc Major nếu có bằng chứng và lý do.
- Report giữ riêng kết quả ba góc nhìn bên cạnh verdict chung: **(A) Tính đúng đắn** (02.1, 02.2, 03.2), **(B) Khả năng phát hiện bug** (01.1–01.6, 07), **(C) Khả năng thực thi và duy trì** (03.1, 04, 05.1, 05.2, 06, 08). Không gộp thành một điểm chất lượng.
- **Một nguyên nhân gốc, một finding.** Khi cùng một lỗi bị nhiều tiêu chí báo thì chỉ tạo một finding, ghi tiêu chí chính và dẫn các mã còn lại.

| Chồng lấn | Tiêu chí chính | Ghi chú |
|---|---|---|
| 01.2 và 01.5 (nhiều tab, đồng thời) | 01.2 | 01.5 chỉ tham chiếu |
| 01.3 (EP lớp không hợp lệ) và 01.4 (input validation) | 01.3 | |
| 01.3 (BVA), 01.6 (`component_checklist`, `jp_validation`) về biên độ dài | 01.3 | 01.6 chỉ báo phần riêng của component hoặc JP (ví dụ đa byte) |
| 01.1 (vế là nhánh lỗi) và 01.4 | 01.1 | |
| 01.1 Partial (Expected không kiểm vế) và 03.2 (Expected mơ hồ) | 03.2 | Sửa Expected cho đo được thường xử lý luôn phần Partial; 01.1 chỉ tham chiếu |
| 02.1 Contradiction và 03.2 | 02.1 | Expected sai nặng hơn Expected mơ hồ |
| 01.3 State Transition (chuyển bị cấm) và 01.4 (trạng thái không hợp lệ) | 01.3 | |
| 01.4 (ô ❌) và 07 (Bảng 1 phủ ô ❌) | Mỗi tiêu chí kiểm phần của mình | 01.4 kiểm có TC; 07 kiểm TC đó có trong bảng |
| 07 (AC High trong bảng) và 01.4 (AC High có negative) | Mỗi tiêu chí kiểm phần của mình | |
| 05.2 (Precondition trỏ mã TC) và 06 | 06 | |
| Mục 5.2 (AC lệch spec) và 02.1 (Expected mâu thuẫn spec) | Mục 5.2 | Gốc là AC sai |
| 03.1 và 05.1 | Theo nguyên nhân | Đã có quy tắc ở REV-05.1 |
| 03.1 và 05.2 (không nói cách dựng hoặc kiểm trạng thái backend) | 03.1 | |
| 01.2 (kịch bản ngoài AC) và 01.4 (negative còn thiếu) | 01.2 | |
| 01.3 BVA và 01.1 Partial | 01.3 | |

Cặp chồng không có trong bảng: chọn tiêu chí ở góc nhìn gần hậu quả nhất (B, rồi A, rồi C).

- Finding vi phạm quy tắc mà gen đã có thì gắn nhãn **"lỗi lọt qua gen"** để team cải tiến gen.
- Report có mục **"Chưa kiểm tra được"**: liệt kê tiêu chí hoặc phần nội dung không đủ input để kết luận, kèm ai có thể bổ sung.
- Mục không áp dụng ghi "Không áp dụng" kèm lý do.
- Review không tự sửa TC.

### 5.6 Report, bộ TC lớn và review lại
- **Report chia theo người đọc** (format cụ thể ở `/review-tcs`):
  - **Report chính** (member sửa TC, lead): verdict, tóm tắt 3 dòng, việc cần làm **gom theo TC**, mỗi việc 1 dòng (tier · TC · vấn đề · sửa thế nào · mã finding). Tách hai nhóm "Sửa TC có sẵn" và "Thêm TC mới". Minor cùng kiểu gộp một dòng. Mục tiêu ≤ 50 dòng.
  - **Câu hỏi PM/BA:** mỗi câu 1 dòng kèm TC bị ảnh hưởng.
  - **Phụ lục** (file riêng): bằng chứng, trích spec, lý do, loại kiểm, tier đã dùng, vế ngoại lệ, trạng thái 17 mục, bảng gán rủi ro (bản Quick), các ứng viên của script bị loại kèm lý do.
- **Chỉ in ngoại lệ.** Phần đạt chỉ in số đếm.
- **Lấy mẫu** chỉ áp cho REV-02.1 và chỉ khi bộ TC trên 150 TC: kiểm toàn bộ TC của AC High, ô ❌; phần còn lại lấy max(30%, 1 TC mỗi AC). REV-03.1 luôn đọc hết. Lỗi thấy ở TC ngoài mẫu vẫn báo, gắn nhãn "ngoài mẫu".
- **Review lại sau khi fix:** chỉ kiểm TC đã sửa, TC mới thêm và các finding cũ. Chạy lại script và các mục mức Bộ có thể bị ảnh hưởng (01.1, 01.4, 04.2, 06, 07).

### 5.7 Định nghĩa dùng chung
Các định nghĩa "Vế", "Covered", "TC negative", "lệch nhỏ/lớn", "TC đại diện `[UNCONFIRMED]`" chỉ đặt ở **một nơi**: skill `rbt_manual_testing`. `gen-tcs.md` và `review-tcs.md` chỉ dẫn tới đó, không chép lại. Mục đích: sửa một chỗ thì cả gen và review cùng đổi (hiện C1, M1 đang lệch giữa hai command vì chép riêng).


### 5.8 Kiểm máy (script)

`python3 -I .claude/scripts/review_checks.py <testcases.md> --spec <spec> [--analysis <analysis>] --json <out.json>`

| Kiểm | Nội dung | Mục REV | Loại |
|---|---|---|---|
| K1 | Cấu trúc bảng (9 cột, cho phép thêm Notes), ID đúng mẫu, không trùng, không nhảy số | 08 | Chắc chắn |
| K2 | Ô bắt buộc trống; Category ngoài danh sách chuẩn | 08 | Chắc chắn |
| K3 | Tham chiếu TC khác trong Precondition, Steps, Expected, Test Data | 06 | Chắc chắn |
| K4 | Traceability sai mẫu; REQ thiếu AC (trừ TC UI); trace tới AC không có trong nguồn | 08, 01.1 | Chắc chắn |
| K5 | Bảng 1/2: ID tồn tại, không lặp ở Bảng 1, tỷ lệ Bảng 1, số luồng Bảng 2, cột "Nếu fail thì" | 07 | Chắc chắn |
| K6 | Vị trí tag `[ASSUMED]` / `[UNCONFIRMED]` không thống nhất | 08 | Chắc chắn |
| K7 | AC chưa có TC nào trace (mức AC, chưa đến vế) | 01.1 | Ứng viên |
| K8 | AC có TC nhưng không TC nào có dấu hiệu negative | 01.4 | Ứng viên |
| K9 | AC còn TBD trong nguồn mà TC không gắn tag | 02.1 | Ứng viên |
| K10 | Placeholder trong phần giá trị của Test Data, Steps | 05.1 | Ứng viên |
| K11 | Cụm mơ hồ trong Expected; "Kiểm tra backend" trong Steps | 03.2, 03.1 | Ứng viên |
| K12 | Expected nhắc "Bước n" mà Steps không có bước đó | 03.1 | Chắc chắn |
| K13 | Precondition trống (trừ TC UI) | 05.2 | Ứng viên |
| K14 | Function Name viết nhiều kiểu cho cùng một tên (trừ TC UI) | 08 | Ứng viên |
| K15 | Cặp TC (không phải UI) giống nhau ≥ 90% | 04.2 | Ứng viên |

- **Chắc chắn:** là finding, AI không dò lại; AI chỉ gán tier, viết đề xuất và gộp vào finding cùng nguyên nhân.
- **Ứng viên:** AI xác nhận từng dòng. Dòng bị loại ghi lý do ngắn trong phụ lục.
- Script không thay phần phán đoán của bất kỳ mục nào. Đặc biệt K7, K8 chỉ là điểm xuất phát cho 01.1 và 01.4.
- Bản Quick: script chỉ trích được AC khi spec viết theo mẫu `F<n>` và `- AC<n>:`. Không trích được thì K4 (tồn tại), K7, K8, K9 bị bỏ và ghi rõ ở đầu kết quả; AI tự làm các phần này.
