---
name: requirements_analyzer
description: Skill phân tích requirement document có sẵn (Google Drive, Docs, Figma, .md, .doc, Backlog ticket) — dựng System Model, tìm lỗ hổng bằng lens, lọc câu hỏi qua Question Gate, extract AC.
---

# Requirements Analyzer

## Mục tiêu

Giúp con người **phát hiện những lỗ hổng mà spec/design không nói tới** — không phải đối chiếu lại những gì spec đã viết. Giá trị của bước này đo bằng: *"PM/BA trả lời xong thì bộ test case thay đổi bao nhiêu?"* — không đo bằng số câu hỏi.

Áp dụng cho **requirement document có sẵn** (Google Drive, Docs, Figma, .md, .doc, Backlog ticket) — không tự sinh requirements từ UI.

---

## Nguyên tắc cốt lõi

- **Đọc toàn bộ trước, hỏi sau** — đọc hết spec, comments, attachments rồi mới sinh câu hỏi. Không sinh câu hỏi trong lúc đọc tuần tự từng đoạn (sẽ chỉ bắt được lỗi cục bộ).
- **Hiểu hệ thống trước khi tìm lỗ hổng** — dựng System Model (xem bên dưới), tìm lỗ hổng trên mô hình, không tìm trên từng câu chữ.
- **Hỏi ít nhưng trúng** — chỉ hỏi khi quyết định không thể suy ra. Phần còn lại: đoán có căn cứ và ghi thành Assumption (người chỉ cần phản đối nếu sai), không bắt người trả lời.
- **Mọi câu hỏi phải có dẫn chứng (phần REQ trong ô Câu hỏi)** — trích/mô tả spec/design kèm vị trí, hoặc ghi rõ "Spec không đề cập tới X". Người đọc không phải mở lại spec để hiểu agent đang nói gì.
- **Một câu hỏi = một quyết định** — không gộp nhiều ý; câu gộp luôn bị trả lời thiếu.
- **Không đoán business logic khi không có căn cứ và hậu quả lớn** — đó mới là Q&A. Có căn cứ (spec/design/convention phổ biến) → Assumption.
- **AC:** map từ spec; AC suy luận ghi Status `Assumed`; AC phụ thuộc câu hỏi chưa trả lời ghi `TBD`.

---

## Bước 1 — Dựng System Model

Trước khi tìm lỗ hổng, rút ra từ spec (không bịa thêm) một mô hình gọn:

| Thành phần | Nội dung cần rút ra |
|---|---|
| **Thực thể & định danh** | Đối tượng dữ liệu chính, khoá định danh của từng loại (id/url/tên file...), quan hệ giữa chúng |
| **Vòng đời / State** | Mỗi thực thể có những trạng thái nào, ai/cái gì chuyển, có đường đi ngược không. State của UI (filter, sort, selection) được giữ/mất khi nào |
| **Actor × Action** | Dựng **ma trận** Action × Actor (chỉ khi có phân quyền hoặc điều kiện theo trạng thái; thêm chiều sở hữu nếu có: order của mình / của người khác). Mỗi ô là một trong 3 giá trị: **✅** có căn cứ trong spec · **❌** suy ra được (spec chỉ gán quyền đó cho actor khác) · **?** spec im lặng và không suy ra chắc. Phải rà **từng ô**, không chỉ liệt kê quyền được phép |
| **Luồng dữ liệu** | Dữ liệu đến từ đâu, đi đâu **bên trong module**. Phụ thuộc ngoài (module/hệ thống/thiết bị) ghi ở Summary › Dependencies, không lặp lại ở đây |
| **Giả định môi trường ngầm** | Spec đang ngầm giả định điều gì về dữ liệu bên ngoài, mạng, thiết bị, thời gian |

Mô hình phải gọn (chỉ rút những gì cần cho việc tìm lỗ hổng) và là thứ **con người xác nhận ở checkpoint đầu tiên**. Hiểu sai ở đây rẻ hơn hiểu sai ở 40 câu hỏi sau đó.

### Một thông tin chỉ ghi ở một nơi

Summary và System Model được người dùng đọc cùng lúc ở checkpoint; cùng một ý ghi hai lần chỉ tăng thời gian đọc. Phân vai:

| Phần | Chỉ chứa | Không chứa |
|---|---|---|
| **Summary** (phạm vi) | Mục đích; actor kèm vai trò **một dòng**; **tên** các luồng/màn hình trong scope (mỗi luồng một dòng, không mũi tên, không liệt kê các bước); Out of scope; Dependencies (module, mức ảnh hưởng, điểm chạm) | Quyền theo hành động; các bước trong luồng; quy tắc trạng thái; mô tả thuộc tính thực thể |
| **System Model** (cấu trúc và hành vi) | Thực thể và thuộc tính; vòng đời trạng thái; ma trận Actor × Action; luồng dữ liệu bên trong module; giả định môi trường | Danh sách phụ thuộc ngoài (đã có ở Dependencies); mô tả lại mục đích; lặp lại tên actor/luồng chỉ để giới thiệu |

- Chỗ cần nhắc tới phần kia thì **ghi tham chiếu, không chép lại**, VD `Cột 評価 phụ thuộc trạng thái Matching (xem System Model › Vòng đời)`.
- Một quy tắc nghiệp vụ (VD `contracted` → nút `投稿`) chỉ nằm ở **một** chỗ: nếu là trạng thái/hành vi của thực thể → System Model; Dependencies chỉ ghi tên điểm chạm và tham chiếu tới đó.
- Cùng nguyên tắc với Impact Analysis và Q&A: không chép lại điều đã có ở Dependencies hoặc System Model, chỉ tham chiếu.

### Quy tắc trình bày Summary và System Model

Mục đích: người đọc quét nhanh để xác nhận mô hình, không phải đọc một khối chữ.

- Mỗi mục lớn (Thực thể & định danh, Vòng đời / State, ...) là một bullet làm tiêu đề, **bên dưới mỗi đối tượng/ý/quy tắc độc lập là một dòng con riêng** (bullet lồng nhau).
- **Chỉ viết tiếp trên cùng một dòng khi các vế liên quan trực tiếp** hoặc cần đi cùng nhau mới hiểu, VD: các thuộc tính của cùng một thực thể; một giá trị và điều kiện áp dụng của nó.
- Cấm nhồi nhiều đối tượng độc lập vào một dòng bằng dấu chấm phẩy hoặc dấu chấm. Thấy một dòng chứa 2+ đối tượng khác nhau → tách.
- Chỗ spec không nêu thì ghi ngay trên dòng đó, VD `(spec không nêu)` — đừng dồn thành một đoạn riêng.
- Nguồn gốc (VD module khác, tài liệu khác) ghi ở cuối dòng trong ngoặc.

Ví dụ — **không** viết thế này:

```
- Thực thể & định danh: Delivery Order (Service Type Standard/Express, Requested Delivery Date đã có ở logistics-system; module này thêm flag Scheduled, Delivery Date, Time Slot; Order ID không nêu). Time Slot cố định: 09:00–12:00, 13:00–17:00, 18:00–21:00. Capacity của slot: spec không cho giá trị và không nói tính theo ngày/khu vực/Driver. Driver: capacity (logistics-system: ≤5 active orders).
```

Viết thế này:

```
- **Thực thể & định danh:**
  - Delivery Order:
    - Đã có (logistics-system): Service Type (Standard/Express), Requested Delivery Date
    - Module này thêm: flag Scheduled, Delivery Date, Time Slot
    - Order ID: spec không nêu
  - Time Slot (cố định):
    - 09:00–12:00
    - 13:00–17:00
    - 18:00–21:00
  - Capacity của slot:
    - Spec không cho giá trị
    - Spec không nói tính theo ngày, khu vực hay Driver
  - Driver:
    - Capacity: ≤5 active orders (logistics-system)
```


---

## Bước 2 — Tìm lỗ hổng bằng 8 Lens

Áp từng lens lên System Model. Mỗi lens là một cách đặt câu hỏi *"điều gì có thể xảy ra mà spec không nói tới?"*. Lens không bắt buộc ra câu hỏi — nếu spec đã trả lời thì bỏ qua.

| # | Lens | Câu hỏi dẫn dắt |
|---|---|---|
| L1 | **Vòng đời & State** | Trạng thái nào có thể kẹt? Đường lùi có chủ đích là gì? State UI (filter, sort, selection, scroll) giữ hay mất khi đổi màn, Back, mở lại app? |
| L2 | **Định danh & quan hệ dữ liệu** | Thực thể được nhận diện bằng gì? Hai thực thể khác nhau có thể trùng định danh không? Xoá/sửa/di chuyển ở đây thì dữ liệu gắn kèm (tag, metadata, quan hệ) đi đâu? |
| L3 | **Phạm vi thao tác hàng loạt** | Chọn đối tượng cha thì áp dụng cho con nào? Kết hợp với filter/điều kiện thì áp dụng cho tập nào? Chọn rỗng, chọn tất cả, chọn số lượng rất lớn thì sao? |
| L4 | **Lỗi từng phần & gián đoạn** | Bước 2 trong luồng 3 bước fail thì bước 1 xử lý thế nào? Cancel giữa chừng? Mất kết nối, app xuống background, bị kill, hết pin, hết dung lượng? Dữ liệu dở dang dọn thế nào? Kết quả báo cho user ra sao? |
| L5 | **Môi trường tác động** | Dữ liệu bên ngoài thay đổi khi user đang thao tác (bị ghi đè/xoá bởi nguồn khác)? Nhiều thiết bị/phiên cùng thao tác? Đồng hồ/múi giờ/format thời gian? Quy mô dữ liệu lớn? Quyền OS bị thu hồi giữa chừng? |
| L6 | **Phân quyền & điều kiện kết hợp** | Ma trận role × action × trạng thái đã đủ chưa? Rà từng ô **?** trong ma trận Actor × Action: ô nào có rủi ro Medium trở lên (tiền/dữ liệu/bảo mật/trạng thái đơn) thì đưa qua Question Gate thành câu hỏi (VD "Operator và Driver có được hủy order không?"). Ô ❌ suy ra được thì không hỏi, nhưng phải giữ trong ma trận để `/plan-tcs` và `/gen-tcs` phủ TC. Quyền thay đổi giữa lúc đang thao tác thì sao? |
| L7 | **Phụ thuộc xuyên module** | Module/màn khác sửa dữ liệu mà màn này đọc (xoá, đổi tên, đổi thứ tự) thì màn này phản ứng thế nào? Rule toàn cục nào chi phối? |
| L8 | **Spec tự mâu thuẫn & luồng thiếu** | Hai mục spec nói khác nhau về cùng hành vi? Message/state được định nghĩa nhưng không luồng nào gọi tới? Điểm vào có mà điểm ra không (ngõ cụt)? Trạng thái empty/error/loading có mô tả chưa? |

> Lens L1-L5 là nơi các câu hỏi giá trị cao nhất thường nằm — chúng thường **không có chữ nào trong spec**, vì spec chỉ mô tả luồng thành công. Dành thời gian nhiều nhất cho nhóm này.

---

## Bước 3 — Question Gate (bắt buộc)

Mỗi ứng viên câu hỏi đi qua cổng này. Ghi nhận **kết quả cổng** cho từng ứng viên trước khi quyết định đưa vào đâu.

**Giữ làm Q&A (câu hỏi cần quyết định)** khi và chỉ khi đủ **cả 4**:

| Cổng | Điều kiện |
|---|---|
| G1 | Spec/design **im lặng hoặc tự mâu thuẫn** về điểm này, và bạn có thể trích dẫn bằng chứng |
| G2 | Có **≥2 cách hiểu hợp lý** dẫn tới hành vi hệ thống khác nhau |
| G3 | Câu trả lời **làm đổi Expected Result hoặc luồng** của ít nhất 1 TC (hoặc thiết kế hệ thống) |
| G4 | Agent **không thể suy ra chắc chắn** từ spec/design/context/convention phổ biến |

**Phân loại ứng viên không qua cổng:**

| Trường hợp | Đi đâu |
|---|---|
| Qua G1-G3, rớt G4 vì có căn cứ rõ trong tài liệu (design đã chọn một phía, quy ước phổ biến, câu khác trong spec đã chốt) | **Assumption (ASM)** — 1 dòng, không cần người trả lời |
| Rớt G3 (typo, wording, định dạng hiển thị, không đổi hành vi) và là lệch giữa spec ↔ design | **Bảng Lệch spec↔design (DIF)** — gom, mỗi lỗi 1 dòng, chọn A/B |
| Rớt G3 và không phải lệch spec↔design | **Loại bỏ** |
| Rớt G1 (spec đã trả lời) | **Loại bỏ** |
| Hành vi chuẩn, hiển nhiên (VD: sau khi xoá thành công thì list làm mới) | **Loại bỏ — không ghi** (không đáng một dòng nào, kể cả ASM) |

> **Chú ý:** đề xuất chỉ là *đoán* (không có căn cứ trong tài liệu) **không** làm câu hỏi rớt G4 — những câu này phải giữ lại. Ví dụ thực tế: agent từng đề xuất "phân loại file theo hậu tố tên" nhưng thực tế hệ thống phân loại theo thư mục; hoặc "tag filter lấy mọi tag" nhưng thực tế chỉ lấy 3 tag mới nhất. Cả hai đều là đoán không căn cứ và đều sai.

### Số lượng và ưu tiên

- **Không có số lượng cố định.** Số câu do Question Gate và bước tự phản biện quyết định: module nhiều lỗ hổng thật thì nhiều câu, module sạch thì ít. Không thêm câu cho đủ số, không cắt câu đạt gate chỉ vì dài.
- Xếp theo mức ảnh hưởng (High trước), nhóm theo chủ đề, đánh ★ cho 3 câu quan trọng nhất để người đọc biết bắt đầu từ đâu.
- Nếu danh sách dài bất thường, đó là tín hiệu cần chạy lại 4 bước tự phản biện bên dưới trên từng câu (thường có nhiều câu thực chất là ASM/DIF hoặc câu gộp nhiều quyết định), không phải tín hiệu để cắt bớt theo số.
- **Severity chỉ có 2 mức trong Q&A:**
  - **High** — đoán sai làm sai nghiệp vụ lõi, mất/hỏng dữ liệu, sai tiền/bảo mật/phân quyền, hoặc ảnh hưởng ≥2 màn hình
  - **Medium** — đoán sai làm sai 1 luồng/hành vi chính nhưng không mất dữ liệu
  - Câu "Low" không đáng hỏi → loại bỏ (chỉ chuyển ASM nếu đoán sai có rủi ro Medium trở lên, xem quy tắc "Xoá trước khi ghi")

### Tự phản biện trước khi trả output

1. Với từng Q&A, tự hỏi: **"Nếu PM chỉ trả lời 3 câu hôm nay, câu này có nằm trong 3 câu đó không?"** Xếp 3 câu trả lời "có" lên đầu và đánh dấu ★.
2. Với từng Q&A, tự hỏi: **"PM đọc câu này có cần mở lại spec không?"** Nếu có → viết lại cho phần REQ đủ rõ.
3. Với từng Q&A, tự hỏi: **"Câu trả lời có thể là 'bỏ qua', 'theo design', 'có', 'không cần quan tâm' không?"** Nếu có → câu đó thừa, chuyển ASM (chỉ khi đoán sai có rủi ro Medium trở lên) hoặc loại.
4. Câu nào chứa từ "và", "hoặc", dấu phẩy nối nhiều câu hỏi con → tách hoặc cắt còn quyết định quan trọng nhất.
5. Câu nào đang ghi "không đề xuất": thử lại — nghiêng về phương án nào dựa trên spec, design, convention, hoặc hậu quả nhẹ hơn? Có thì đề xuất. Chỉ giữ "không đề xuất" nếu hai phương án thật sự ngang nhau, kèm lý do cụ thể của câu đó.
6. Với từng dòng ở **Q&A, DIF, ASM và IMP**, tự hỏi: **"Nếu xoá dòng này, người đọc hoặc bộ TC mất gì?"** Không mất gì → xoá.

### Xoá trước khi ghi (ASM, DIF, IMP)

Câu bị loại khỏi Q&A **không** được tự động chuyển sang ASM — nếu không, ASM sẽ thành chỗ đổ rác mà người đọc vẫn phải lướt qua.

- **ASM chỉ ghi khi đoán sai gây rủi ro từ Medium trở lên** (đổi Expected Result của TC quan trọng, hoặc sai một luồng chính). Rủi ro Low, hoặc hành vi hiển nhiên/chuẩn → **không ghi**, không cần đưa vào đâu cả.
- **DIF chỉ ghi lệch có ảnh hưởng tới TC hoặc hiển thị mà người test sẽ kiểm** (default, tên field/label, format, ngôn ngữ, element thiếu). Lỗi chính tả hoặc đánh số mục trong spec mà agent tự bỏ qua được → không ghi.
- **IMP chỉ ghi hành vi có căn cứ và có khả năng vỡ thật** — không liệt kê mọi thứ module kia đang làm.
- Gate này áp dụng cho **mọi dòng ở mọi bảng**, không chỉ Q&A: mỗi dòng phải trả lời được "người đọc dùng dòng này để làm gì?".

---

## Bước 4 — Format câu hỏi

Mỗi câu Q&A là một dòng trong bảng, cột theo mẫu Q&A管理表 của team:

| Cột | Nội dung |
|---|---|
| **ID** | `Q-[MÃ MODULE]-[SỐ 3 CHỮ SỐ]`, VD `Q-LOG-001`. `Q` = Question; mã module = **Mã module** trong Summary (3 chữ cái viết hoa, VD `LOG` = Login). Số tăng dần từ 001 trong từng module. `/gen-tcs` đọc ID này để tra Severity — ID phải sạch, **không** gắn ★ hay ký hiệu khác |
| **Reference** | **Chỉ mã REQ**, VD `REQ-03` (nhiều REQ thì cách nhau dấu phẩy: `REQ-03, REQ-07`). **Không** ghi mô tả requirement, số mục hay trích dẫn vào cột này — mô tả/trích dẫn thuộc phần `* **REQ:**` trong ô Câu hỏi. Bắt buộc, không để trống. Mã REQ phải khớp cột REQ ID trong bảng Acceptance Criteria (quy tắc gán mã bên dưới) |
| **Screen** | Màn hình liên quan (**bắt buộc**) |
| **Câu hỏi** | Gộp 3 phần, mỗi phần **một dòng riêng** (dùng `<br>` xuống dòng trong ô): **REQ** (dẫn chứng mô tả spec/design) → **Câu hỏi** (một quyết định) → **Phương án đề xuất** (luôn có, trừ trường hợp ngoại lệ hiếm — xem bên dưới). Chi tiết bên dưới |
| **Nếu đoán sai** | Hậu quả cụ thể (TC/AC nào sai, hành vi nào sai) |
| **Severity** | High / Medium |
| **Status** | TBD |

Câu nằm trong 3 câu quan trọng nhất (★) thì đặt `★ ` ngay sau nhãn **Câu hỏi:** (VD `* **Câu hỏi:** ★ ...`), không đặt ở cột ID.

### Cấu trúc ô `Câu hỏi`

```
* **REQ:** [trích nguyên văn / mô tả spec hoặc design, kèm vị trí §x — hoặc "Spec không đề cập tới ..."]
* **Câu hỏi:** [câu hỏi — một quyết định, hỏi thẳng]
* **Phương án đề xuất:**
**A.** [phương án A]
**B.** [phương án B]
**C.** [nếu có phương án thứ ba]
**→ Đề xuất:** [A/B] vì [căn cứ] ([nguồn căn cứ])
```

**Quy tắc mã REQ (cột Reference):**
- Spec đã đánh mã requirement → dùng đúng mã đó (không đổi tên, không viết lại).
- Spec không đánh mã → agent gán `REQ-01`, `REQ-02`, ... theo thứ tự requirement trong spec, **gán trước khi sinh câu hỏi**, và dùng đúng các mã này ở cả cột REQ ID của bảng AC, cột Reference của Q&A, và Reference của ASM.
- Câu hỏi thuộc lỗ hổng xuyên nhiều requirement → ghi tất cả REQ liên quan. Chỉ ghi `N/A` khi thật sự không thuộc requirement nào.

**Quy tắc các phần trong ô:**
- **REQ** (trong ô Câu hỏi) là phần để người đọc không phải mở lại spec: trích đủ ngắn gọn nhưng đủ hiểu. Spec im lặng thì ghi rõ "Spec không đề cập tới ...".
- **Câu hỏi** (trong ô) chỉ chứa một quyết định (xem Nguyên tắc cốt lõi).
- **Phương án đề xuất:** mỗi phương án (A, B, C, ...) **một dòng riêng**, chữ cái đầu dòng **in đậm** (`**A.**`, `**B.**`, `**C.**`), không viết dồn thành một đoạn. Dòng kết luận `→` đứng riêng ở cuối.
- **Mặc định là luôn đề xuất một phương án** kèm căn cứ, để người trả lời chỉ cần gật hoặc sửa. Ghi rõ **nguồn căn cứ** trong ngoặc để người đọc biết đề xuất mạnh hay yếu:
  - `(theo spec §x)` / `(theo design [frame])` — có chỉ dẫn trong tài liệu, dù chưa nói thẳng
  - `(theo convention, không từ spec)` — thông lệ phổ biến của loại sản phẩm/nền tảng này
  - `(phương án an toàn hơn nếu đoán sai)` — khi không có căn cứ nào khác, chọn phương án mà hậu quả nhẹ hơn nếu sai (VD: không mất dữ liệu, dễ hoàn tác)
- **Chỉ được ghi "không đề xuất" khi hai phương án thật sự ngang nhau** (cùng hậu quả, không convention nào nghiêng về phía nào, tài liệu không gợi ý) — và phải nêu lý do **cụ thể** của câu hỏi này, VD: `**→ Không đề xuất:** hai phương án có hậu quả ngang nhau, tùy chính sách kinh doanh của khách`. Cấm câu chung chung dùng lại cho nhiều câu hỏi. Đây là ngoại lệ hiếm; nếu nhiều câu cùng ghi "không đề xuất" thì agent đang lười tìm căn cứ.
- Câu hỏi mở không chia được phương án (VD: "giá trị tối đa là bao nhiêu?") → bỏ dòng A/B, ghi `* **Phương án đề xuất:** [giá trị đề xuất] vì [căn cứ] ([nguồn])`.

Ví dụ một ô hoàn chỉnh (viết với `<br>` trong bảng):

```
* **REQ:** System kiểm tra Available Quantity. Nếu đủ: Available → Reserved<br>* **Câu hỏi:** Shipment nhiều Products mà chỉ một Product không đủ Available: từ chối cả Shipment hay tạo Shipment cho các item đủ?<br>* **Phương án đề xuất:**<br>**A.** Từ chối cả Shipment, không Reserved gì cả<br>**B.** Tạo Shipment, chỉ Reserved item đủ, item thiếu bị bỏ/để chờ<br>**→ Đề xuất:** A vì §8 "chỉ Ship khi tất cả items đã Pick" gợi ý Shipment chỉ hình thành khi đủ hàng (theo spec §8, chưa nói thẳng cho trường hợp thiếu Available)
```

Nhóm các câu theo chủ đề (không theo thứ tự đọc spec) để người trả lời giữ được ngữ cảnh.

### Ví dụ câu tốt vs câu thừa (module Media của app dashcam EDR)

| Loại | Câu | Nhận xét |
|---|---|---|
| ❌ Thừa | "Spec ghi 'update popup 8.3' nhưng popup đúng là 9.3.2, có phải typo?" | Agent tự dùng 9.3.2. Nếu cần ghi → DIF, không phải câu hỏi |
| ❌ Thừa | "Sau khi Protect/Delete/Save thành công, list có tự load lại không?" | Hành vi chuẩn → không ghi (kể cả ASM) |
| ❌ Thừa | "Filter mặc định là gì? Spec ghi Internal Storage, design chọn Smartphone. Đề xuất: Smartphone" | Design đã chọn rõ → ASM nếu đoán sai có rủi ro Medium trở lên, hoặc DIF nếu chỉ là lệch spec↔design; còn lại không ghi |
| ❌ Gộp | "Sort 'tăng dần' có nghĩa là mới nhất trên đầu? Sort theo gì? Giữ khi đổi filter? Giữ khi Back? Giữ khi mở lại app?" | 5 quyết định; team chỉ trả lời 1 phần. Tách: câu về **giữ state sort/layout** mới đáng hỏi (L1) |
| ✅ Tốt (L2) | "Phân loại file N/E/M theo thư mục `\Normal\` hay hậu tố `_N/_E/_M`? Nếu mâu thuẫn theo cái nào?" + phần REQ trích FPATH và quy tắc đặt tên | Đề xuất của agent sai trong thực tế → câu hỏi đúng đã đổi cách thiết kế TC |
| ✅ Tốt (L2/L7) | "Tag lưu theo `url` file. File EDR sau khi Save về máy có giữ tag không, xoá file thì tag có bị xoá?" | Vòng đời dữ liệu gắn kèm — spec không nói |
| ✅ Tốt (L3) | "Chọn folder rồi Delete: áp dụng mọi file trong folder hay chỉ file khớp filter đang bật?" | Phạm vi thao tác hàng loạt × filter |
| ✅ Tốt (L4) | "Cancel hoặc fail giữa chừng khi Save nhiều file: file thành công trước đó giữ hay dọn? Popup kết quả hiện số file thành công/thất bại thế nào?" | Lỗi từng phần |

### Ví dụ lỗ hổng điển hình mà list thực tế đã bỏ sót (tham khảo để học cách nghĩ, không sao chép)

- **L5:** Loop recording trên thiết bị ghi đè file cũ chưa bảo vệ **trong khi** user đang chọn/tải/combine → list đã load là snapshot hay live? File biến mất giữa chừng thì sao?
- **L2:** Tag định danh theo `url` — hai thiết bị khác nhau cùng địa chỉ IP, hoặc tên file được tái sử dụng sau khi bị ghi đè → tag gắn nhầm.
- **L4:** App xuống background/bị kill/hết pin giữa lúc Combine — file tạm, file dở xử lý khi mở lại?
- **L5:** Đồng hồ thiết bị sai hoặc bị reset → thứ tự sort, gom folder, tên file lệch.
- **L7:** Tag bị xoá/đổi tên ở màn Setting → filter, file đang gắn tag phản ứng thế nào?

---

## Bước 5 — Dependencies & Impact Analysis

### Đọc dependencies

- Tài liệu phụ thuộc → đọc và tóm tắt
- AC từ tài liệu phụ thuộc có thể ảnh hưởng scope của tài liệu chính
- Ghi rõ rule nào đến từ tài liệu nào

### Dependencies trong Summary (hiển thị ở checkpoint, trước Impact Analysis)

Người dùng xác nhận Summary **trước khi** Impact Analysis được sinh, nên dòng Dependencies phải đủ để họ kiểm tra agent hiểu dependency đúng chưa — không chỉ liệt kê tên.

- Mỗi module một dòng tiêu đề kèm **mức ảnh hưởng**:
  - **trực tiếp** — module kia dùng chung dữ liệu/quy tắc/luồng với module này và thay đổi ở đây tác động thẳng
  - **gián tiếp** — tác động qua một thành phần trung gian (VD qua capacity, assignment, trạng thái dùng chung)
  - **nhẹ** — chỉ chạm ở rìa, hầu như không đổi hành vi của module kia
- Bên dưới là **các điểm chạm cụ thể, mỗi điểm một dòng** (field, công thức, quy tắc, luồng trạng thái dùng chung...), theo quy tắc trình bày ở Bước 1.
- Module đã xét và loại → gom vào **một dòng** `Đã xét, không liên quan: [...]` (không liệt kê từng dòng riêng, tránh nhiễu khi `testing/` có nhiều module). Bỏ dòng này nếu không có module nào bị loại.
- Phân vai để không lặp: Summary nêu **module nào, mức ảnh hưởng, điểm chạm là gì**. Impact Analysis nêu **hành vi cụ thể cần kiểm lại, rủi ro, căn cứ**.

### Impact Analysis (chỉ khi module có dependency **có căn cứ**)

Mục đích: chỉ ra **hành vi đang chạy của module khác có thể vỡ** vì thay đổi của module này, để bước sau (`/plan-tcs`) biết cần regression ở đâu. Đây là **danh sách điểm cần regression, không phải test scenario** — không viết scenario hay TC ở bước này.

**Căn cứ để ghi một dependency** (cần ít nhất một):
- Spec của module này nhắc rõ module/hệ thống khác hoặc dữ liệu dùng chung
- `testing/[module]/analysis.md` của module khác đã có và module này chạm vào điểm mà nó mô tả
- Design cho thấy màn hình/thành phần dùng chung

Không có căn cứ → **không liệt kê** (không đoán mò). Module không có dependency nào → **bỏ hẳn mục Impact Analysis**, không để mục trống.

**Cách làm, với mỗi dependency:**
1. **Điểm chạm:** dữ liệu, luồng hoặc màn hình dùng chung giữa hai module
2. **Hành vi hiện có:** module kia đang làm gì dựa vào điểm chạm (lấy từ `analysis.md` của nó hoặc từ spec)
3. **Thay đổi gây rủi ro:** module này đổi/thêm gì khiến hành vi đó có thể vỡ
4. **Rủi ro:** High / Medium / Low

**Quy tắc:**
- **Mỗi dòng một hành vi cần kiểm lại.** Một module bị chạm ở nhiều điểm → nhiều dòng riêng, không gộp vào một ô.
- **Reference** là mã REQ của module này gây ra thay đổi (cùng quy tắc mã REQ ở Bước 4).
- **Rủi ro:**
  - **High** — liên quan tiền/bảo mật/phân quyền, hoặc mất/hỏng dữ liệu, hoặc luồng lõi của module kia
  - **Medium** — một luồng chính của module kia nhưng không mất dữ liệu
  - **Low** — hiển thị hoặc luồng phụ
- **Phân biệt với Q&A (lens L7):**
  - Hành vi **đã có và đã biết** của module khác → Impact Analysis (IMP)
  - Hành vi spec **chưa nói** khi hai module tác động nhau → câu hỏi, qua Question Gate
  - Một điểm chạm cần cả hai → ghi cả hai; ở dòng IMP ghi thêm `(xem Q-XXX-00N)` ở cột Hành vi, không lặp lại câu hỏi

---

## Design Integration

*(Áp dụng khi user cung cấp design input: Figma link, screenshot, PDF export design...)*

### Theo dạng input

| Input | Cách đọc |
|-------|---------|
| Screenshot / image | Đọc trực tiếp — cross-check ngay với spec |
| PDF export | Đọc từng trang — cross-check theo từng screen |
| Figma link | Dùng Figma MCP tools — theo quy trình 2 phase bên dưới |

### Figma — Quy trình 2 Phase

> Áp dụng khi Figma file có nhiều pages hoặc nhiều frames. Mục tiêu: xác định đúng scope trước khi đọc sâu — tránh bỏ sót screen và tránh đọc nhầm vào archive/draft.

#### Phase 1 — Scope Mapping (có checkpoint)

1. Gọi `get_pages` → list tất cả pages trong file
2. Hỏi user:
   > Figma file có [N] pages: [danh sách tên]. Pages nào liên quan đến feature đang phân tích? *(Bỏ qua Archive, Draft, hoặc pages không liên quan)*
3. Chờ user confirm pages
4. Với các pages được confirm: gọi `scan_nodes_by_types` với type `FRAME` → list top-level frames
5. Hỏi user:
   > Tôi thấy [N] frames: [danh sách tên]. Frames nào là screens của feature này?
6. Chờ user confirm frames → đây là **scope chính thức** cho Phase 2

#### Phase 2 — Deep Read (chỉ trong scope đã confirm)

Với mỗi frame được confirm:

1. Gọi `get_node` để đọc nội dung frame
2. Tìm `COMPONENT_SET` nodes — đây là nơi Figma lưu state variants:
   - Tìm nodes có tên chứa keyword: `State=`, `Status=`, `Type=`, `Variant=`, `Mode=`
   - Ví dụ phổ biến: `State=Error`, `State=Loading`, `State=Disabled`, `Status=Active`
3. Gọi `get_annotations` để đọc annotations và developer notes
4. Cross-check theo bảng bên dưới

### Cross-check — ưu tiên tìm luồng và state thiếu

Design có giá trị nhất ở chỗ nó **cho thấy thứ spec không viết ra**. Ưu tiên theo thứ tự:

| Ưu tiên | Tìm gì | Đi đâu |
|---|---|---|
| 1 | **State/luồng thiếu:** empty state, error state, loading, trạng thái disabled; nút/icon trong design không có hành vi trong spec; màn hình ngõ cụt (vào được mà không thoát được); element trong design không có spec (và ngược lại) | Qua Question Gate → Q&A nếu đổi hành vi |
| 2 | **Business rules ẩn:** annotations/developer notes chứa rule chưa có trong spec | Ghi vào AC context; nếu mâu thuẫn spec → Q&A |
| 3 | **Screen inventory:** frames đã confirm vs sections trong spec | Frame có trong design nhưng không có trong spec → Q&A (qua gate) |
| 4 | **Lệch hiển thị:** tên field/label, format ngày giờ, ngôn ngữ, default value, thứ tự | **Bảng DIF** — gom, mỗi lỗi 1 dòng, không tạo Q&A. KHÔNG tự chọn bên nào đúng |

> Design Findings chỉ bổ sung thêm câu hỏi/DIF — không thay thế hay override phân tích từ spec text.

---

## Những gì KHÔNG làm

- ❌ Sinh câu hỏi trong lúc đọc tuần tự từng đoạn spec mà chưa dựng System Model
- ❌ Hỏi để "xác nhận lại" điều spec/design đã nói rõ
- ❌ Hỏi typo, wording, hoặc lệch hiển thị bằng Q&A (dùng bảng DIF)
- ❌ Gộp nhiều quyết định vào một câu
- ❌ Để trống Reference/Screen/phần REQ
- ❌ Ghi mô tả requirement, số mục hoặc trích dẫn vào cột Reference (cột này chỉ chứa mã REQ)
- ❌ Đưa ra đề xuất mà giấu việc nó chỉ là đoán — luôn ghi nguồn căn cứ
- ❌ Dùng "không đề xuất" làm mặc định cho nhiều câu hỏi
- ❌ Liệt kê dependency khi không có căn cứ (spec, `analysis.md` của module kia, hoặc design) — chỉ đoán
- ❌ Viết test scenario/TC regression trong `analysis.md` (Impact Analysis chỉ liệt kê điểm cần regression)
- ❌ Bỏ qua comments hoặc notes đính kèm trong document
- ❌ Giả định lệch giữa document và mockup là typo — ghi vào DIF để người chọn
- ❌ Giữ câu không qua Question Gate chỉ để danh sách trông đầy đủ
