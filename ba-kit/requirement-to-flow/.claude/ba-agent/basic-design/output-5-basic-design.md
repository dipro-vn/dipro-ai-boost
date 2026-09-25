# Ba Agent — Output 5: Basic Design (master Excel workbook)

> **Output 5 ghi specification vào master Excel Basic Design của công ty** — không tạo file rời, không tạo workbook mới.
> Template tham chiếu: `sample/sample_basic_design.xlsx`. Map cell/cột chính xác: **BẮT BUỘC Read** [`workbook-structure.md`](./workbook-structure.md) trước mọi thao tác ghi.

---

## 0. Tiêu chí — khi nào Output 5 được coi là ĐẠT

> Đọc mục này trước. §1→§9 là cách thực hiện; mục này là thước đo.

**Output 5 ĐẠT khi và chỉ khi đủ cả 3 nhóm:**

| Nhóm | Tiêu chí | Kiểm bằng |
|---|---|---|
| **A. Điều kiện vào** | Output 1 + Output 2 được **người** xác nhận đã chốt · master workbook do user chỉ định · user đã trả lời Proposal Gate | §1 Input Gate + §2 `AskUserQuestion` — không tự suy |
| **B. Nội dung sinh ra** | Mỗi screen trong scope có đúng 1 working sheet, đủ **7 nhóm nội dung** (`workbook-structure.md` §2.6) · mọi item trace về `SPEC ## Screen Details` · mọi Message Code trỏ tới catalog có thật · `Screen Index` + `Change History` được cập nhật | Đọc lại sheet + §6 gate |
| **C. Cái KHÔNG được đụng** | `Sample` nguyên vẹn · sheet ngoài scope nguyên vẹn · không có sheet ví dụ của file mẫu còn sót · có backup trước khi ghi | §6 gate check 1 · 8 · 11 + §4 Bước 0 |

**Thước đo cuối cùng:** `verify-basic-design.py` trả về **`FAIL = 0`**. Không có FAIL = 0 thì Output 5 **không** được báo Done, bất kể sheet trông đẹp thế nào.

**Ba thứ KHÔNG phải tiêu chí đạt** (hay bị nhầm):
- ❌ "Sheet mở ra nhìn giống `Login_Sample`" — giống hình thức không có nghĩa là đúng nội dung
- ❌ "Đã điền hết ô" — điền bằng nội dung tự suy còn tệ hơn để trống có ghi `UNKNOWN`
- ❌ "Gate chỉ còn WARN" — WARN được phép tồn tại, FAIL thì không

---

## 0.1. Output 5 là ON-DEMAND — không bao giờ tự chạy

Khác Output 1–4, **Output 5 KHÔNG nằm trong Definition of Done mặc định**. BA chỉ được chạy khi:

1. Có **trigger** từ user (§0.2), **và**
2. Output 1 **và** Output 2 được user xác nhận đã chốt, **và**
3. BA đã chạy **Proposal Gate** ở §2 bằng `AskUserQuestion` và user trả lời đồng ý.

**Anti-pattern NGHIÊM CẤM:**
- ❌ Tự chạy Output 5 vì "Output 4 xong rồi, còn mỗi Basic Design"
- ❌ Chạy Output 5 khi Output 2 mới ở `QUALITY_PASS` / `WAITING_APPROVAL` (chưa `APPROVED`)
- ❌ Coi im lặng của user là đồng ý
- ❌ Ghi vào workbook trước khi backup (§4 Bước 0)

---

## 0.2. Trigger — Output 5 khởi động bằng cách nào

> Output 5 **không có trigger tự động**. Nó chỉ chạy khi user chủ động yêu cầu, hoặc khi user đồng ý với lời đề nghị của BA.

### Trigger hợp lệ

| Loại | Ví dụ | BA làm gì |
|---|---|---|
| **Slash command** | `/basic-design` · `/basic-design CM_AUTH_001,CM_AUTH_002` | Vào §1 Input Gate → §2 Proposal Gate |
| **Ngôn ngữ tự nhiên — tạo mới** | *"làm Basic Design cho luồng Login"* · *"tạo Basic Design cho module CM"* · *"ghi spec vào file Basic Design"* · *"điền vào master Excel"* | Như trên |
| **Ngôn ngữ tự nhiên — sửa** | *"sửa maxlength của ô email trong Basic Design"* · *"cập nhật Basic Design màn CM_AUTH_003"* | Vào §5 Change Spec workflow (vẫn qua Input Gate + Proposal Gate) |
| **BA đề nghị 1 lần** | Sau khi Output 2 được user xác nhận đã chốt, BA **được phép hỏi 1 lần**: *"Output 1 và Output 2 đã chốt — bạn có muốn tôi làm Basic Design không?"* | ⛔ Hỏi **1 lần duy nhất**. User im lặng hoặc nói "chưa" → không hỏi lại trong session |

### KHÔNG phải trigger

- ❌ Output 4 (HTML Prototype) hoàn thành — O4 không liên quan tới O5
- ❌ Output 3 hoàn thành — ảnh chỉ là input tuỳ chọn
- ❌ `## BA Deliverables` ghi `✅ Done` cho O1/O2 — Done ≠ Approved
- ❌ Trong thư mục dự án có sẵn file `.xlsx` trông giống Basic Design
- ❌ User nói *"làm nốt đi"* / *"tiếp tục"* mà không nêu rõ Basic Design

### Khi trigger mơ hồ

User nói *"làm Basic Design"* nhưng không nêu phạm vi → **không tự chọn toàn bộ**. Đưa câu hỏi phạm vi vào §2 Proposal Gate Câu 3.

---

## 1. Input Gate O5 — kiểm trước khi đề xuất

| Input | Bắt buộc | Điều kiện PASS |
|---|---|---|
| Output 1 — Flow tổng quan | ✅ Có | Quality Gate O1 PASS **và** state = `APPROVED` |
| Output 2 — Screen Flow | ✅ Có | Quality Gate O2 PASS **và** state = `APPROVED` |
| SPEC.md `## Screens` + `## Screen Details` | ✅ Có | Có cột `FR No.`; gate FR Coverage đã in `THIẾU: []` |
| Master workbook | ✅ Có | Đường dẫn do user chỉ định, mở được bằng `openpyxl`, có đủ **5 sheet** theo `workbook-structure.md` §1 |
| **UI source (ảnh)** | ⬜ **KHÔNG bắt buộc** | Xem §1.1 |
| Output 4 — HTML Prototype | ⬜ Không | Chỉ dùng làm evidence bổ sung khi user yêu cầu. **Không** là prerequisite |

**Nếu Output 1 hoặc Output 2 chưa `APPROVED`** → DỪNG, in:

```
❌ Input Gate O5: BLOCKED
  - Output <N>: <state hiện tại> (cần APPROVED)
Basic Design chỉ bắt đầu sau khi Flow tổng quan và Screen Flow được approve.
Bạn muốn tôi quay lại hoàn tất Output <N> trước không?
```

### 1.1 Ảnh UI — optional, nhưng phải khai báo

Basic Design **thường** có ảnh màn hình bên cạnh bảng item, nhưng **không bắt buộc 100%**.

#### a) Ảnh lấy từ đâu — thứ tự ưu tiên

| Ưu tiên | Nguồn | Điều kiện dùng | `Screen Index` cột `UI Source` |
|---|---|---|---|
| 1 | **Output 3** — mockup BA vẽ | Đã `APPROVED`, và node map được với Screen ID | `Output 3 approved — <node URL>` |
| 2 | **Figma Hi-fi của Designer** | User chỉ định node cụ thể | `Figma Hi-fi — <node URL>` |
| 3 | **Screenshot / ảnh user cung cấp** | User đưa file, nói rõ ảnh của màn nào | `Screenshot — <tên file>` |
| 4 | **Màn hình hệ thống đang chạy** (AS-IS) | ⚠️ Chỉ khi user xác nhận TO-BE = AS-IS cho màn đó | `AS-IS screenshot — <nguồn>` + ghi `Need Confirm` ở `Notes` |
| — | **Không có gì** | Luôn hợp lệ | **`NO IMAGE — text only`** |

> Nguồn thấp hơn **không** được override nguồn cao hơn. Có Output 3 approve rồi thì không dùng screenshot AS-IS cho cùng màn đó.

#### b) Map node Figma → Screen ID

Ảnh chỉ được chèn khi **xác định chắc chắn** nó là của Screen ID nào:

| Cách map | Độ tin cậy |
|---|---|
| Tên frame Figma **chứa Screen Code** (VD `CM_AUTH_001 — Login`) | ✅ Dùng được ngay |
| Bảng Navigation Mapping của Output 3 có cột `Screen Code` ↔ số badge trên mockup | ✅ Dùng được |
| Thứ tự mockup trong frame khớp thứ tự `## Screens` | ⚠️ **Không đủ** — phải đối chiếu thêm tên màn |
| Đoán theo nội dung nhìn thấy trên ảnh | ❌ **Cấm** — ghi `NO IMAGE` còn hơn chèn nhầm |

Map không ra → sheet đó `NO IMAGE — text only` + `Notes` ghi `⚠ Output 3 có mockup nhưng không map được Screen ID — Need Confirm`.

#### c) Export và lưu ảnh

**Đường 1 — Figma MCP khả dụng:**
```
get_screenshot(node-id = <node của màn>)  → lưu thành PNG
```

**Đường 2 — Figma MCP KHÔNG khả dụng** (chưa authorize connector, hoặc chạy offline):
> ⛔ **KHÔNG tự bịa ảnh, KHÔNG vẽ placeholder.** BA dừng phần ảnh lại, tạo sheet ở chế độ `NO IMAGE — text only`, và in hướng dẫn cho user:
> 1. Authorize connector Figma, rồi yêu cầu BA chèn ảnh bổ sung, **hoặc**
> 2. Tự export PNG và đặt vào `basic-design/images/` theo quy ước đặt tên dưới

**Quy ước lưu và đặt tên — BẮT BUỘC:**

```
<feature>/basic-design/images/
├── CM_AUTH_001.png              ← 1 màn 1 ảnh
├── CM_AUTH_002_step1.png        ← màn nhiều state: <Screen ID>_<state>.png
├── CM_AUTH_002_step2.png
└── CM_AUTH_002_step3.png
```

- Định dạng: **PNG** (giữ nét chữ trong mockup; JPG làm mờ text nhỏ)
- Tên file = **Screen ID chính xác**, không dấu cách, không tiếng Việt có dấu
- Ảnh không khớp Screen ID nào trong `Screen Index` → **không chèn**, báo user

#### d) Kích thước và cách chèn

> Vùng ảnh `A–F` rộng **~854 px** (tổng column width 122 ký tự). Ảnh rộng hơn sẽ **tràn sang cột H–R và đè lên bảng item**.
>
> ⚠️ File mẫu gốc mắc đúng lỗi này: ảnh `1521 × 1528 px` chèn vào vùng 854 px → tràn ~670 px. **Đừng lặp lại.**

| Quy tắc | Giá trị |
|---|---|
| Chiều rộng hiển thị tối đa | **840 px** (chừa lề 14 px) |
| Chiều cao hiển thị tối đa | **900 px** |
| Scale | Giữ nguyên tỷ lệ. Fit theo chiều rộng trước; nếu cao vượt 900 px thì fit lại theo chiều cao |
| Anchor | Cột **A**, tại row đầu của khối ảnh (`A9` cho ảnh đầu tiên) |
| Merge | `A<r>:F<r+k>` cho vùng ảnh, `k` đủ chứa chiều cao ảnh |
| Row height | Tổng row height của vùng ≥ chiều cao ảnh. Đổi đơn vị: `pt = px × 0.75` |

Ví dụ: mockup mobile `375 × 812` → fit chiều cao 900 px → hiển thị `416 × 900 px` → cần vùng cao `900 × 0.75 = 675 pt`, chia cho 3 row = 225 pt/row.

#### e) Một sheet nhiều ảnh (màn nhiều state)

Màn wizard / nhiều step nằm **cùng 1 sheet** (§3 Granularity). Mỗi state 1 ảnh, xếp **dọc từ trên xuống**:

- Ảnh state 1 anchor `A9`, ảnh state 2 anchor ngay dưới khối state 1, v.v.
- Mỗi ảnh đặt **cạnh đúng nhóm item của state đó** trong bảng `H:R` — item `（Step 1）` nằm ngang hàng ảnh step 1
- Giữa 2 khối ảnh chừa **1 row trống** để không dính nhau

#### f) Cấm

- ❌ Chèn ảnh placeholder tự vẽ, ảnh wireframe tự sinh
- ❌ Chèn ảnh của màn khác cho "đỡ trống"
- ❌ Chèn ảnh từ Output 3 **chưa** approve
- ❌ Chèn ảnh rộng hơn 840 px (đè bảng item — gate check 13 bắt)
- ❌ Chèn ảnh mà không map chắc chắn được Screen ID
- ❌ Suy business rule từ ảnh rồi ghi vào `P`/`Q` như FACT (ảnh là **visual source**, không phải rule source — Rule R8)

> ⚠️ Thiếu ảnh **KHÔNG làm Quality Gate O5 FAIL**. Nhưng **không khai báo** trong `Screen Index` thì FAIL — người đọc sau phải biết sheet này chưa có visual.

#### g) ⛔ Không lấy được ảnh KHÔNG phải lý do hoãn Output 5

Khi Figma không truy cập được (chưa authorize, hết hạn mức, offline) hoặc Output 3 chưa phủ màn đó:

| Sai | Đúng |
|---|---|
| ❌ Dừng Output 5, chờ có ảnh rồi mới tạo | ✅ **Hỏi bằng `AskUserQuestion`: đề xuất tạo sheet trước, bổ sung ảnh sau** |
| ❌ Thu hẹp scope xuống còn mấy màn có ảnh | ✅ Giữ nguyên scope, màn chưa có ảnh ghi `NO IMAGE — text only` |
| ❌ Coi sheet không ảnh là sản phẩm dở dang | ✅ Sheet không ảnh **vẫn đủ giá trị bàn giao** — item, behavior, error, traceability đều đầy đủ |

**Lý do:** nội dung sheet lấy từ `SPEC ## Screen Details`, **không** lấy từ ảnh (Rule R8 — ảnh là visual source, không phải rule source). Thiếu ảnh chỉ làm mất phần minh hoạ, không mất nội dung spec.

Bổ sung ảnh sau là thao tác nhẹ, không phải tạo lại — xem **§1.3**.

### 1.2 Khởi tạo master từ file mẫu — PHẢI loại sheet không thuộc dự án

> Áp dụng khi master workbook của dự án được **tạo ra bằng cách copy file mẫu** (`sample/sample_basic_design.xlsx`) hoặc copy từ master của dự án khác.

File mẫu chứa **sheet ví dụ** để minh hoạ format — `Login_Sample` là một. Copy nguyên cả file sang dự án mới thì các sheet đó trở thành **rác trong master thật**: chúng có `Sheet Type = WORKING_SCREEN`, có Screen ID, nên mọi thống kê / Screen Index / bàn giao đều đếm nhầm chúng là màn của dự án.

**Quy trình bắt buộc — làm TRƯỚC Bước 1 của §4:**

| # | Việc | Chi tiết |
|---|---|---|
| 1 | Liệt kê mọi sheet có `Sheet Type` ≠ rỗng | Đây là toàn bộ screen sheet đang tồn tại |
| 2 | Đối chiếu từng sheet với `## Screens` của SPEC dự án | Screen ID không có trong SPEC = **ứng viên phải xoá** |
| 3 | **Hỏi user** bằng `AskUserQuestion` (xem §2 Câu 4) | ⛔ KHÔNG tự xoá — xoá sheet là thao tác không hoàn tác được |
| 4 | Xoá sheet user đồng ý bỏ + **xoá row tương ứng trong `Screen Index`** | Xoá sheet mà quên row index → gate check 5 FAIL |
| 5 | Ghi `Change History` 1 row `Change Type = MASTER_STANDARDIZATION` | Nêu rõ đã bỏ sheet nào và vì sao |

**Giữ nguyên, KHÔNG bao giờ xoá:**
- `Sample` — template, là nguồn để duplicate
- `Common mesage` · `Screen Error message` · `Screen Index` · `Change History` — sheet hệ thống

**Gate check 11** bắt lỗi này tự động: sheet có tên hoặc Screen ID khớp `sample` / `example` / `demo` / `template` / `mau` / `copy` mà **không** nằm trong `--expect-screens` → **FAIL**.

> Nếu một sheet trông như sheet mẫu nhưng **thực sự** là screen của dự án → thêm Screen ID của nó vào `--expect-screens`. Đó là khai báo có chủ đích, không phải hạ ngưỡng gate.

---

### 1.3 Bổ sung ảnh vào sheet đã tạo — scoped update, KHÔNG tạo lại

> Áp dụng khi sheet đã tồn tại với `UI Source = NO IMAGE — text only` và sau đó lấy được ảnh.

**Đây là scoped update chỉ chạm 2 chỗ.** Không duplicate sheet mới, không đụng bảng item, không đụng catalog.

| # | Việc | Phạm vi |
|---|---|---|
| 0 | Backup master (§4 Bước 0) | Bắt buộc như mọi lần ghi |
| 1 | Resolve sheet theo **Screen ID** qua `Screen Index` | Không dùng tên hiển thị |
| 2 | Chèn ảnh vào `A9+`, resize theo §1.1d | **Chỉ vùng ảnh** |
| 3 | Cập nhật `Screen Index` cột `I` (`UI Source`) + cột `L` (`Notes`) | `NO IMAGE — text only` → nguồn ảnh thật |
| 4 | `F3` Version +1 · `B3`/`D3` người sửa + ngày · `F4` → `WAITING APPROVAL` | Metadata của sheet đó |
| 5 | Append `Change History`, `Change Type = UPDATE_SCREEN` | 1 row |
| 6 | Quality Gate O5 + §6.1 self-test | `FAIL = 0` |

**Không được làm:**
- ❌ Tạo lại sheet từ `Sample` (mất mọi chỉnh sửa/nhận xét đã có)
- ❌ Sửa nội dung bảng item "nhân tiện" — nếu ảnh cho thấy item khác SPEC thì đó là **CONFLICT**, quay lại sửa SPEC trước
- ❌ Quên cập nhật `Screen Index.UI Source` → gate check 10 FAIL

---

## 2. Proposal Gate — BẮT BUỘC hỏi bằng AskUserQuestion trước khi làm

> ⛔ **Đây là gate cứng.** BA **KHÔNG** được tạo/sửa bất kỳ sheet nào trước khi user trả lời. In ra một block text rồi tự đi tiếp = **vi phạm rule này**.
>
> Phải dùng tool **`AskUserQuestion`**, không phải in text rồi tự suy diễn câu trả lời. Lý do: agent **stateless** — không có state machine nào lưu `APPROVED` giữa các session, nên trạng thái Output 1/2 **chỉ con người xác nhận được**.

### Bước A — In bảng tình hình (trước khi hỏi)

```
📋 Đề xuất Output 5 — Basic Design

Sẽ ghi vào: <đường dẫn master workbook>
Screen sheet đang có trong master: <N> (<liệt kê>)
  ⚠️ Không thuộc SPEC dự án: <liệt kê — nếu có, xem §1.2>

Phạm vi đề xuất: <N> screen từ SPEC ## Screens
  • Tạo mới:      <Screen ID chưa có sheet>
  • Update:       <Screen ID đã có sheet>
  • Need Confirm: <Screen ID chưa xác định được boundary>

Nguồn ảnh UI: <Output 3 APPROVED (M/N màn) / Figma <node> / chưa có>
```

### Bước B — Hỏi bằng `AskUserQuestion`

| Câu | Khi nào hỏi | Header | Options |
|---|---|---|---|
| **1. Trạng thái Output 1 & Output 2** | **LUÔN LUÔN** | `O1 & O2` | `[Cả hai đã chốt]` · `[Chưa chốt — dừng lại]` · `[Chỉ O1 chốt, O2 chưa]` |
| **2. Ảnh UI** | **Chỉ khi có/thiếu ảnh cần quyết** | `Ảnh UI` | `[Chèn ảnh lấy được, tạo hết sheet]` · `[Tạo trước — bổ sung ảnh sau]` · `[Tôi export ảnh thủ công trước]` |
| **3. Phạm vi screen** | **LUÔN LUÔN** | `Scope` | `[Toàn bộ N screen]` · `[Chỉ một số — tôi chỉ định]` · `[Chưa làm bây giờ]` |
| **4. Sheet không thuộc dự án** | **Chỉ khi §1.2 phát hiện sheet lạ** | `Sheet lạ` | `[Xoá hết]` · `[Giữ lại — là screen thật]` · `[Cho tôi xem danh sách]` |

**Xử lý câu trả lời Câu 1:**

| User chọn | BA làm gì |
|---|---|
| `Cả hai đã chốt` | Ghi `Source Flow Version` = version Output 2 user xác nhận → đi tiếp |
| `Chưa chốt — dừng lại` | ⛔ **DỪNG.** In: *"Basic Design chỉ bắt đầu sau khi Flow tổng quan và Screen Flow được chốt. Bạn muốn tôi quay lại hoàn tất Output 1/Output 2 trước không?"* — **KHÔNG** tạo sheet nào |
| `Chỉ O1 chốt, O2 chưa` | ⛔ **DỪNG.** Output 2 là nguồn của Screen ID, transition và Screen Index — thiếu nó thì sheet sinh ra không trace về đâu được. In lý do + đề nghị hoàn tất O2 |

**Xử lý câu trả lời Câu 2 (ảnh UI):**

| User chọn | BA làm gì |
|---|---|
| `Chèn ảnh lấy được, tạo hết sheet` | Chèn ảnh cho màn có, `NO IMAGE — text only` cho màn chưa có. **Tạo đủ mọi sheet trong scope** |
| `Tạo trước — bổ sung ảnh sau` | Tạo đủ sheet ở chế độ `NO IMAGE — text only`, rồi chèn ảnh sau theo §1.3 |
| `Tôi export ảnh thủ công trước` | Đưa danh sách file cần export theo quy ước §1.1c rồi chờ. **Chỉ chọn khi user chủ động muốn thế** |

> ⛔ **KHÔNG được đưa lựa chọn "hoãn Output 5 vì chưa có ảnh" vào câu hỏi này.** Ảnh là optional (§1.1); thiếu ảnh không chặn việc tạo sheet. Nội dung sheet lấy từ `SPEC ## Screen Details`, không lấy từ ảnh — thiếu ảnh **không** làm sheet kém giá trị đi.
>
> Output 3 **Partial** (VD phủ 11/56 màn) là trường hợp hay gặp nhất — nêu rõ `M/N` để user biết màn nào sẽ có ảnh, màn nào chưa. Nhưng vẫn **tạo đủ N sheet**.

**Anti-pattern NGHIÊM CẤM ở gate này:**
- ❌ In bảng đề xuất dạng text rồi tự chạy tiếp mà không gọi `AskUserQuestion`
- ❌ Suy `APPROVED` từ việc `## BA Deliverables` ghi `✅ Done` — **Done ≠ Approved**
- ❌ Coi im lặng, "ok", "ừ", "tiếp đi" là đã trả lời đủ 3-4 câu
- ❌ Tự xoá sheet lạ trước khi hỏi Câu 4

---

## 3. Granularity — 1 screen = 1 sheet

Template `Sample` là **screen-level specification**, không phải flow-level.

| Trường hợp | Cách tạo |
|---|---|
| 1 flow có nhiều screen độc lập | Duplicate `Sample` thành **nhiều sheet**, mỗi sheet 1 Screen ID |
| 1 screen có nhiều state / step liên tục (VD Login Step 1 → Step 2) | **1 sheet duy nhất** nếu cùng Screen ID + cùng UI structure — ghi rõ `（Step 1）`/`（Step 2）` trong tên item, đúng như `Login_Sample` |
| Màn lỗi Full screen có Screen Code riêng trong SPEC | Sheet riêng |
| Toast / Inline / Banner | **Không** tạo sheet — mô tả trong cột `P`/`Q` của item liên quan + row ở `Screen Error message` |
| Không xác định được boundary | ⛔ **Không tự quyết** — đưa vào `Need Confirm` ở Proposal Gate, chờ BRSE |

**Tên sheet:** `<Screen ID>_<short name>`, tối đa **31 ký tự** (giới hạn cứng của Excel), không chứa `: \ / ? * [ ]`.
Tên sheet phải **khớp tuyệt đối** với `Screen Index` cột `E`.

> ⚠️ Row seed sẵn trong `Screen Index` của file mẫu ghi `Sheet Name = Login` trong khi tab thật tên `Login_Sample` — **đây là sai lệch có sẵn**. Khi gặp, báo user, không tự sửa tab.

---

## 4. Create New workflow (9 bước)

### Bước 0 — Backup BẮT BUỘC (không có trong tài liệu kiến trúc, bắt buộc ở kit này)

```bash
cp "<master.xlsx>" "<DOCS_ROOT>/features/<feature>/versions/v<N>_<DDMMYYYY>/basic_design_before.xlsx"
```

Lý do: `openpyxl` **không bảo toàn 100%** conditional formatting, một số merged range phức tạp, chart, pivot, macro và ảnh ở vài anchor mode. File Excel là binary — **không có git diff để rollback**. Không backup = không được ghi.

### Bước 1 → 9

| # | Bước | Điều kiện chuyển tiếp |
|---|---|---|
| 1 | Resolve master workbook + đọc lại 5 sheet bằng `openpyxl` | Đúng file, đủ sheet, `Sample` tồn tại và `F6 = TEMPLATE_SCREEN` |
| 2 | Validate Output 1 + Output 2 = `APPROVED` | Cả hai PASS — nếu không, quay về §1 |
| 3 | Resolve UI source theo §1.1 | Mỗi Screen ID có ảnh **hoặc** được đánh dấu `NO IMAGE — text only` |
| 4 | Build **Screen Creation Plan** — bảng 3 nhóm: NEW / EXISTING / NEED CONFIRM | Mọi Screen ID trong scope đã được phân nhóm. `NEED CONFIRM` ≠ rỗng → hỏi user, không tự tạo |
| 5 | Duplicate `Sample` → 1 sheet / screen NEW | `Sample` **không bị chạm** (§6 kiểm bằng script) |
| 6 | Neutralize sheet vừa duplicate | Xóa banner `A8:F8`; đổi `F6` → `WORKING_SCREEN`; điền `F1..F5` |
| 7 | Populate: metadata (rows 1–6) → ảnh (`A9+`, nếu có) → bảng item (`H9:R19`, mở rộng nếu > 11 item) | Mọi item trace về SPEC `## Screen Details`. Không suy rule chỉ từ ảnh |
| 8 | Update catalog: reuse `Common mesage` trước → append `Screen Error message` theo block category | Mọi code trỏ trong cột `P`/`Q` đều tồn tại thật |
| 9 | Append `Screen Index` (1 row/sheet) + `Change History` (1 row/lần chạy) | Không thiếu row nào |

Sau đó → **§6 Quality Gate O5** → **§7 Human Approval Gate O5**.

---

## 5. Change Spec workflow (9 bước)

Khi user yêu cầu sửa spec của screen đã có sheet: **update trực tiếp sheet đang tồn tại**. Không duplicate sheet mới, không regenerate workbook.

| # | Bước | Điều kiện chuyển tiếp |
|---|---|---|
| 0 | Backup như §4 Bước 0 | File backup tồn tại |
| 1 | Parse scope thay đổi: screen / item / validation / state / error row | Scope viết ra được bằng 1 câu |
| 2 | Resolve working sheet **bằng Screen ID** qua `Screen Index`, KHÔNG bằng tên hiển thị | Tìm đúng 1 sheet. Tìm được ≠ 1 → hỏi user |
| 3 | Load dependency trực tiếp: item liên quan, error row liên quan, transition liên quan | Chỉ load đúng phạm vi |
| 4 | Impact analysis theo §5.1 | Phân định rõ in-scope vs out-of-scope |
| 5 | Nếu chạm artifact ngoài scope → **xin approval mở rộng** bằng `AskUserQuestion` | User đồng ý mới đi tiếp. Sau đó **bắt buộc** khai tên sheet đó vào `--approved-scope` khi chạy gate |
| 6 | Chỉ update cell/row bị ảnh hưởng | Style, ảnh, nội dung không liên quan **giữ nguyên** |
| 7 | Update `F3` Version (+1), `B3`/`D3` 更新者/更新日, `F4` Status → `WAITING APPROVAL`; append `Change History` | Đủ 4 mục |
| 8 | Quality Gate O5 — so intended change với **diff thật** của workbook | Diff ⊆ scope đã approve |
| 9 | Human Approval Gate O5 | Sheet về `WAITING APPROVAL` cho change đó |

### 5.1 Impact matrix

| Thay đổi | Update trực tiếp | Downstream có thể ảnh hưởng |
|---|---|---|
| Tên / description của item | Working sheet: row item đó (`I`–`R`) | Thường không ảnh hưởng flow |
| `required` / `maxlength` / validation | Working sheet + `Screen Error message` | HTML Prototype (Output 4) nếu đã tồn tại → mark `STALE` |
| Transition / destination | ⛔ **Không update ngay** nếu khác Output 2 | Phải quay lại Output 2, change + approve ở đúng level rồi mới xuống O5 |
| Thêm screen mới | ⛔ Chỉ sau khi Screen Flow (O2) được approve | Tạo sheet mới từ `Sample`; `Screen Index`; prototype nếu trong scope |
| UI layout / ảnh | Vùng `A9+` + mapping item bị ảnh hưởng | Output 3 hoặc prototype visual |
| Wording của common message | `Common mesage` + mọi sheet reference | ⚠️ Ảnh hưởng **nhiều screen** → **bắt buộc** xin expanded-scope approval |

---

## 6. Quality Gate O5 — chạy script, không tự chấm

```bash
python3 .claude/skills/business-analyst/scripts/verify-basic-design.py \
    "<master.xlsx>" \
    --before "<...>/versions/v<N>_<DDMMYYYY>/basic_design_before.xlsx" \
    --expect-screens "AU_AUTH_001,AU_AUTH_002" \
    --out "<...>/versions/v<N>_<DDMMYYYY>/basic-design-gate.md"
```

**Hai flag khai báo — dùng đúng chỗ, không phải để gỡ FAIL cho nhanh:**

| Flag | Khai cái gì | Khi nào được dùng |
|---|---|---|
| `--expect-screens` | Toàn bộ Screen ID **phải tồn tại** sau lần chạy = screen mới + screen đã có của dự án | Luôn. Chính là Screen Creation Plan ở §4 Bước 4 |
| `--approved-scope` | Tên sheet **ngoài scope** mà user đã đồng ý cho sửa/xoá | ⛔ **Chỉ sau khi có approval thật** (§5 Bước 5 hoặc §1.2 Câu 4). Không có approval mà khai = che lỗi |

> Không khai `--approved-scope` thì mọi thay đổi ngoài scope vẫn **FAIL**. Khai rồi thì nó xuống `WARN` và **được in nguyên văn vào report** — đó là audit trail, không phải cách tắt gate.

Script kiểm 15 điều (`FAIL` = chặn, `WARN` = ghi nhận):

| # | Kiểm | Mức |
|---|---|---|
| 1 | `Sample` không bị sửa / đổi tên / xóa (so byte với bản `--before`) | FAIL |
| 2 | Mọi working sheet mới có `Sheet Type = WORKING_SCREEN` (không sót `TEMPLATE_SCREEN`) | FAIL |
| 3 | Không trùng `Screen ID` giữa các working sheet | FAIL |
| 4 | Mọi working sheet có đủ `F1..F5` (không còn `[PLACEHOLDER]` / `TBD` ở Screen ID) | FAIL |
| 5 | Mọi working sheet có đúng 1 row trong `Screen Index`, tên sheet khớp cột `E` | FAIL |
| 6 | Mọi Message Code được trỏ trong cột `P`/`Q` đều tồn tại trong `Screen Error message` hoặc `Common mesage` | FAIL |
| 7 | `Change History` có ≥ 1 row mới cho lần chạy này | FAIL |
| 8 | Sheet ngoài scope không bị đổi (so với `--before`) — trừ sheet khai ở `--approved-scope` | FAIL · WARN nếu đã khai báo |
| 9 | Screen trong `--expect-screens` đều có sheet; không có sheet thừa ngoài danh sách | FAIL |
| 10 | Working sheet không có ảnh → `Screen Index.UI Source` phải chứa `NO IMAGE` | FAIL nếu không khai báo · WARN nếu khai báo đúng |
| 11 | Không còn sheet ví dụ của file mẫu (`*Sample*` / `*Demo*` / `*Template*`) ngoài Screen Creation Plan | FAIL — xem §1.2 |
| 12 | `Change History` có `Change ID` đúng dạng `CHG-NNNN`, liên tục, không trùng | FAIL |
| 13 | Ảnh UI anchor cột `A`, rộng ≤ 840px, cao ≤ 900px (không đè bảng item) | FAIL · WARN nếu không có ảnh nào — xem §1.1d |
| 14 | Data row có đủ 4 cạnh border và **không** dùng fill của header | FAIL — dùng `bd_styles.py`, xem `workbook-structure.md` §2.8 |
| 15 | Mỗi screen sheet có bảng **ERROR SCENARIOS** dưới bảng item, số row khớp catalog | FAIL — xem `workbook-structure.md` §2.9 |

**Exit code:** `0` = PASS · `1` = có FAIL · `2` = thiếu `openpyxl` (`pip install openpyxl`)

| Kết quả | Hành động |
|---|---|
| `FAIL = 0` | In block PASS → §7 |
| `FAIL > 0` | **Sửa workbook, chạy lại.** Không được báo Done, không được hạ ngưỡng gate |
| Không chạy được script | ⛔ Output 5 = `❌ Blocked` — **KHÔNG** được tự chấm PASS bằng mắt |

**In ra bắt buộc:** `N checks · X PASS · 0 FAIL · Y WARN` — số thật từ script, không gõ tay.

### 6.1 Self-test — chứng minh gate không PASS rỗng

> Gate báo PASS **chưa chứng minh được gì**: một gate hỏng cũng "PASS" mọi thứ. Chạy self-test để xác nhận gate thực sự bắt lỗi.

```bash
python3 .claude/skills/business-analyst/scripts/selftest-basic-design.py \
    "<workbook da PASS>" --before "<backup>"
```

Script lấy workbook đã PASS, **tiêm 8 lỗi đã biết** vào bản copy, rồi xác nhận gate bắt đúng check kỳ vọng:

| Lỗi tiêm | Check phải bắt |
|---|---|
| Xoá đường kẻ data row | 14 |
| Data row tô fill của header | 14 |
| Xoá bảng ERROR SCENARIOS | 15 |
| Ghi bậy vào `Sample` | 1 |
| Phóng to ảnh vượt khung | 13 |
| Change ID nhảy cóc | 12 |
| Xoá row `Screen Index` | 5 |
| Trỏ tới Message Code ma | 6 |

**Khi nào chạy:** sau mỗi lần sửa `verify-basic-design.py`, và khi bàn giao Output 5 cho dự án mới.

> ⚠️ Bộ test này **đã từng tìm ra 2 lỗi thật của gate**:
> - check 14 **crash** (`AttributeError`) khi border side = `None` — gate chết chứ không báo FAIL
> - check 13 đo `im.width` thay vì `anchor.ext` → bỏ sót ảnh bị phóng to trong Excel
>
> Cả hai chỉ lộ ra khi tiêm lỗi, không lộ ra khi chạy trên file đúng.

---

## 7. Human Approval Gate O5

Sau khi Quality Gate PASS, BA **DỪNG HOÀN TOÀN**:

```
✅ Output 5 — Basic Design completed
Quality Gate O5: PASS (N checks · X PASS · 0 FAIL · Y WARN)
Status: WAITING FOR BRSE APPROVAL

Reply:
  - "Approve"           → sheet chuyển APPROVED (BA update F4 + Change History)
  - "Reject: <lý do>"   → BA sửa rồi chờ approve lại
```

**Rule:** approve Output 5 **không** tự động approve lại Output 1/2. Nếu trong lúc làm O5 phát hiện flow conflict → **quay lại artifact gốc** change + approve đúng level, không tự sửa ở tầng Excel.

---

## 8. Runtime response contract — 9 field bắt buộc

Sau mỗi lần create/update Basic Design, BA phải trả về đủ:

```markdown
| Field | Nội dung |
|---|---|
| Requested scope | <flow / screen / spec change đã xử lý> |
| Workbook | <đường dẫn master đã cập nhật> + backup: <đường dẫn backup> |
| Created sheets | <danh sách sheet mới duplicate từ Sample> |
| Updated sheets | <danh sách working sheet đã sửa> |
| Updated catalogs | <số row thêm/sửa ở Common mesage · Screen Error message> |
| Unchanged protected artifacts | Sample + <danh sách sheet ngoài scope không bị chạm> |
| Quality Gate | PASS / FAIL + issue list |
| Open Questions | UNKNOWN · CONFLICT · Need Confirm |
| Approval status | WAITING FOR BRSE APPROVAL / APPROVED |
```

> Field `Unchanged protected artifacts` là bằng chứng scoped update — **lấy từ output script**, không tự khai.

---

## 9. Anti-pattern NGHIÊM CẤM

- ❌ Ghi vào master workbook khi chưa backup
- ❌ Sửa / đổi tên / xóa sheet `Sample`
- ❌ Tạo workbook Basic Design rời bên ngoài master
- ❌ Duplicate `Common mesage` hoặc `Screen Error message` cho từng screen
- ❌ Suy business rule **chỉ** từ ảnh UI rồi ghi vào cột `P`/`Q` như FACT
- ❌ Trỏ tới Message Code chưa tồn tại trong catalog
- ❌ Tự đặt viết tắt màn cho Message Code mà không hỏi BRSE
- ❌ Điền `Description (VN)` lệch số bullet/nhánh so với `記述（日本語）`
- ❌ Tự chấm Quality Gate O5 PASS khi script không chạy được
- ❌ Chèn ảnh placeholder / ảnh màn khác để "cho đủ hình"
- ❌ **Hoãn hoặc thu hẹp scope Output 5 chỉ vì không lấy được ảnh** — ảnh là optional (§1.1g)
- ❌ Đưa lựa chọn "chờ có ảnh rồi làm" vào Proposal Gate Câu 2 như một phương án ngang hàng
- ❌ Sửa transition trong sheet Excel khi Output 2 chưa đổi
