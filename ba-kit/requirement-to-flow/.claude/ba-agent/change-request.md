# BA Agent — Nhánh CR (ChangeRequest) của Bước 7

> **Điều kiện vào file này:** Bước 7.2 đã phân loại có item `🔴 CR` **và** user đã confirm phân loại ở Bước 7.3 (`post-meeting-workflow.md`). Chưa confirm → không được làm gì ở đây.
>
> **4 việc bắt buộc, đúng thứ tự:** ① giải trình *vì sao là CR* → ② `AskUserQuestion` về CR → ③ vẽ **CR view mới** (phân định NEW / UPDATE) → ④ `output_cr.md` + lưu version mới.
>
> Mapping Issue Type Backlog: `ChangeRequest` = yêu cầu ngoài Scope đã chốt (ProjectBase). Xem `ba-agent.md` mục Ràng buộc cứng.

---

## §1 — Giải trình "vì sao đây là CR" (BẮT BUỘC in trước khi hỏi)

Mỗi CR phải có 1 block giải trình. Không có bằng chứng trích từ baseline → **không được gọi nó là CR**, quay lại xếp `⚪ CHƯA RÕ`.

```markdown
## CR-<ID> — <tên ngắn>

**Yêu cầu KH:** <nguyên văn, 1-2 dòng>
**Baseline:** v<M>_<DDMMYYYY> · **Nguồn:** `meetings/meeting_note_<DDMMYY>.md`

**Vì sao đây là CR:**
- <Tiêu chí C<x>> — baseline `SPEC.md ## <section>` ghi: "<trích dẫn>" → yêu cầu mới ngược/vượt nội dung này
- <Tiêu chí C<y>> — phát sinh <N> screen mới chưa có trong `## Screens` (v<M>)
- <Tiêu chí C<z>> — kéo theo sửa <artifact> đã giao (Basic Design sheet / prototype)

**KHÔNG phải feedback vì:** <1 dòng — VD "baseline không hề thiếu mục này; đây là thay đổi ý định của KH, không phải BA vẽ sai">
```

Quy tắc giải trình:
- Dùng tiêu chí C1→C6 ở `post-meeting-workflow.md` Bước 7.2 — ghi rõ mã tiêu chí, không giải trình bằng cảm tính.
- Trích dẫn baseline phải là **nội dung thật đọc từ file**, không paraphrase từ ký ức.
- Giọng văn trung tính. ❌ Không viết "KH đổi ý liên tục", "yêu cầu vô lý" — CR là việc bình thường của dự án.
- Nhiều CR trong 1 note → đánh `CR-01`, `CR-02`… mỗi CR 1 block riêng.

---

## §2 — AskUserQuestion về CR (BẮT BUỘC trước khi vẽ)

Gọi `AskUserQuestion` — in text rồi tự vẽ = vi phạm gate. Batch 1 (luôn hỏi):

| Câu | Nội dung | Lựa chọn |
|---|---|---|
| 1 | Giải trình CR ở §1 đúng chưa? | `[Đúng — xử lý như CR]` · `[Không — đây là feedback trong scope]` · `[Cho xem thêm bằng chứng baseline]` |
| 2 | Lần này làm tới đâu? | `[Vẽ CR view + output_cr (đầy đủ)]` · `[Chỉ output_cr để trao đổi KH trước]` · `[Chỉ ghi nhận CR, chưa xử lý]` |
| 3 | CR này **thay thế** hay **thêm song song** phần cũ? | `[Thay thế luồng/màn cũ]` · `[Thêm mới, giữ luồng cũ]` · `[Chưa rõ — cần hỏi KH]` |
| 4 | Ai yêu cầu + mức ưu tiên? | `[KH — must have sprint này]` · `[KH — nice to have, sprint sau]` · `[BrSE/nội bộ đề xuất]` |

Batch 2 (chỉ hỏi khi câu 2 = `[Vẽ CR view + output_cr]`):

| Câu | Nội dung | Lựa chọn |
|---|---|---|
| 5 | Scope CR view vẽ đến mức nào? | `[Flow + Screen Flow + Screens của phần ảnh hưởng]` · `[Chỉ Flow + Screen Flow]` · `[Chỉ bảng CR Change Table, chưa vẽ node]` |
| 6 | Phần **AS-IS** (luồng cũ liên quan) có vẽ kèm để đối chiếu? | `[Có — vẽ mờ làm ngữ cảnh]` · `[Không — chỉ vẽ NEW/UPDATE]` |
| 7 | *(chỉ khi CR chạm Basic Design đã giao)* Xử lý Basic Design? | `[Ghi nhận, chờ KH chốt CR]` · `[Update luôn sau khi vẽ CR]` |

Ràng buộc:
- ❌ TUYỆT ĐỐI không đưa lựa chọn kiểu "tiếp tục có điều kiện" / "vẽ luôn cho nhanh rồi hỏi sau".
- BA **không** tự đưa con số man-day / cost trong bất kỳ câu hỏi nào — estimate là việc của Dev/PM.
- Câu 1 trả lời `[Không — đây là feedback]` → về Bước 7.4 (`post-meeting-workflow.md`), không vẽ CR view.
- Câu 2 trả lời `[Chỉ ghi nhận]` → chỉ làm §1 + ghi vào version mới, bỏ qua §3/§4.

---

## §3 — Vẽ CR view (view MỚI — tuyệt đối không vẽ chồng lên Output 1/2/3)

### 3.1 Vị trí & đặt tên — hard rule

- CR vẽ trong **Section / Frame mới**: `CR-<ID> — <tên ngắn> (baseline v<M> → v<N+1>)`
- Đặt **dưới cùng** vùng làm việc hiện tại, cách bbox thấp nhất của Output 1/2/3 **MIN 400px** theo trục Y.
- ⛔ KHÔNG `remove()` / `resize()` / di chuyển / append node vào Section của Output 1/2/3 đã có. Output cũ là **immutable** (`POLICIES.md §4.6`) — người xem phải so được "trước CR" vs "sau CR".
- ⛔ KHÔNG sửa màu / label node của Output 1/2/3 để "đánh dấu chỗ thay đổi". Việc đánh dấu diễn ra **trong CR view**.
- Nhiều CR → mỗi CR 1 Section riêng, xếp dọc, gap MIN 400px.

Sub-view trong CR Section (theo lựa chọn câu 5 §2):

| Sub-view | Nội dung | Ghi chú |
|---|---|---|
| `CR-1 — Flow thay đổi` | Chỉ nhánh business flow bị CR chạm | Không vẽ lại toàn bộ Output 1 |
| `CR-2 — Screen Flow thay đổi` | Luồng màn của phần ảnh hưởng | Connector vẽ thật (`shared-rules.md`) |
| `CR-3 — Screens mới / cần sửa` | Mockup màn NEW + màn UPDATE | Chỉ màn bị chạm |
| `CR Change Table` | Bảng phân định NEW / UPDATE / DELETE | **BẮT BUỘC, không bỏ** |

### 3.2 Legend phân định — MỌI node phải có đúng 1 badge

| Badge | Ý nghĩa | Fill | Stroke | Bổ sung |
|---|---|---|---|---|
| 🟩 `NEW` | Tạo mới hoàn toàn | `#EDFDF0` | `#1A7F37` solid 2px | — |
| 🟨 `UPD` | Sửa cái đã có | `#FFF9EB` | `#F4860C` **dashed** 2px | Sub-text `<giá trị cũ> → <giá trị mới>` |
| 🟥 `DEL` | Bỏ khỏi luồng | `#FFF6F5` | `#CF222E` dashed 2px | Text gạch ngang |
| ⬜ `AS-IS` | Giữ nguyên, vẽ làm ngữ cảnh | `#F6F8FA` | `#D0D7DE` 1px | opacity 0.6 |

- Node `UPD` / `DEL` / `AS-IS` phải ghi **Screen Code / ID gốc** từ baseline (VD `AX_FEAT_003`) để trace được về SPEC cũ.
- Vẽ 1 **Legend box** ở góc trên trái CR Section với đủ 4 badge trên.
- Màu ngoài bảng này = vi phạm (giữ nhất quán `shared-rules.md` → Visual conventions).

### 3.3 CR Change Table (bắt buộc, đặt bên phải hoặc dưới các sub-view)

| # | Đối tượng | Loại | Baseline ref | Nội dung thay đổi | Artifact cần sửa |
|---|---|---|---|---|---|
| 1 | `AX_FEAT_007` Màn Xác nhận OTP | 🟩 NEW | — (chưa có) | Thêm bước xác thực OTP trước khi submit | SPEC `## Screens`, O2, O3, prototype |
| 2 | `AX_FEAT_003` Màn Đăng ký | 🟨 UPD | `SPEC v<M> ## Screen Details` | Button "Gửi" → điều hướng sang OTP thay vì Kết quả | SPEC, O2, O3 |
| 3 | BR-04 | 🟥 DEL | `SPEC v<M> ## Acceptance Criteria` AC-06 | Bỏ rule auto-approve | SPEC |

### 3.4 Quality Gate CR (chạy trước khi báo xong — FAIL = 0)

| # | Check | PASS |
|---|---|---|
| 1 | Số node có badge `NEW`+`UPD`+`DEL` = số row CR Change Table | Đếm 2 bên khớp |
| 2 | Số node **không** badge trong CR Section | `= 0` |
| 3 | Overlap bbox giữa CR Section và Section Output 1/2/3 | `= 0` (gap ≥ 400px) |
| 4 | Node của Output 1/2/3 bị thay đổi (id / vị trí / màu / text) | `= 0` — so `get_metadata` trước/sau |
| 5 | Mỗi node `UPD`/`DEL` có Screen Code gốc từ baseline | 100% |
| 6 | Legend box đủ 4 badge | Có |
| 7 | Overlap nội bộ CR Section (`recheck.md` Tiêu chí 7) | `overlapCount == 0` |

FAIL > 0 → sửa rồi chạy lại, **không** hạ ngưỡng, không báo Done.

---

## §4 — `output_cr.md` — tài liệu trao đổi KH (BẮT BUỘC cho mọi CR)

Đây là output **hướng ra khách hàng**, không phải log nội bộ. Yêu cầu: **ngắn gọn, gạch đầu dòng, có reference file**.

Đường dẫn: `<output-folder>/versions/v<N+1>_<DDMMYYYY>/output_cr.md` (nhiều CR → `output_cr_<ID>.md` mỗi CR 1 file).

```markdown
# CR-<ID> — <tên ngắn>

> Tài liệu trao đổi với khách hàng: vì sao yêu cầu này là Change Request. Đọc trong 2 phút.

**Nguồn:** <meeting note / mail / chat> ngày <DD/MM/YY> · **Người yêu cầu:** <role> · **Baseline:** v<M>_<DDMMYYYY>

## 1. Yêu cầu của KH
- <1-3 bullet, sát ý KH, không diễn giải thêm>

## 2. Vì sao chúng tôi xem đây là CR
- <lý do 1> — baseline đã chốt tại `SPEC.md ## <section>` (v<M>): "<trích dẫn ngắn>"
- <lý do 2> — nằm trong `## Out of Scope` của v<M>
- <lý do 3> — phát sinh <N> màn mới / đổi <business rule>

## 3. Ảnh hưởng nếu thực hiện
- Scope: +<N> màn mới · <M> màn cần sửa
- Artifact phải cập nhật: <SPEC section · Figma O2/O3 · prototype · Basic Design sheet>
- Effort / schedule: cần Dev estimate — BA không đưa con số

## 4. Phương án đề xuất
- [A] <phương án> — <trade-off 1 dòng>
- [B] <phương án> — <trade-off 1 dòng>
- Khuyến nghị: **[A]** vì <1 dòng>

## 5. Cần KH xác nhận
- [ ] <câu hỏi 1>
- [ ] <câu hỏi 2>

## Reference
| Loại | Đường dẫn / URL |
|---|---|
| Meeting note | `meetings/meeting_note_<DDMMYY>.md` |
| Baseline SPEC | `versions/v<M>_<DDMMYYYY>/SPEC.md` |
| CR view (Figma) | `<node URL>` |
| Triage | `versions/v<N+1>_<DDMMYYYY>/feedback-triage.md` |
```

Ràng buộc `output_cr.md`:
- **≤ 1 trang (~40 dòng)**, toàn bộ là gạch đầu dòng / bảng. Không đoạn văn dài.
- Mục 2 là **quan điểm của mình** — mỗi bullet 1 lý do + 1 reference baseline. Không gộp nhiều lý do vào 1 bullet.
- Reference **chỉ ghi file/URL có thật** đã tạo trong lần chạy này. Không có Figma URL → ghi `chưa vẽ` , KHÔNG bịa link.
- ⛔ Không đưa nội dung nội bộ ra ngoài (`POLICIES.md §3.5`): không nêu tên agent/AI, không log nội bộ, không cost/đơn giá nội bộ.
- ⛔ Không PII (`rules/DATA-PRIVACY.md`): người yêu cầu ghi bằng **role**, không ghi họ tên.
- ⛔ Không tự kết luận "CR này miễn phí" / "CR này tính thêm tiền" — thương thảo là việc của PM/BrSE.

---

## §5 — Lưu version mới (BẮT BUỘC)

Theo `.claude/ba-agent/versioning.md` Rule 2c:

```
versions/v<N+1>_<DDMMYYYY>/
├── SPEC.md               ← chỉ update khi user đã chốt làm CR; chưa chốt thì giữ nguyên baseline + ghi CR vào ## Ambiguities
├── output_cr.md          ← BẮT BUỘC (§4)
├── feedback-triage.md    ← bảng triage 7.2 + §1 giải trình + câu trả lời §2
├── ba-outputs-log.md     ← Trigger = CR · CR view URL · diff so với v<N>
└── prototype/index.html  ← chỉ khi đã vẽ và có thay đổi
```

- Version cũ `v<N>` **giữ nguyên** — đó là bằng chứng "baseline trước CR".
- CR chưa được KH chốt → **KHÔNG** ghi CR vào `## Happy Path` / `## Acceptance Criteria` của SPEC. Ghi vào `## Ambiguities` dạng `CR-<ID>: chờ KH xác nhận` cho tới khi có confirm.
- `ba-outputs-log.md` phải có row `CR view` kèm Figma URL + note `NEW: <n> · UPD: <m> · DEL: <k>`.

---

## Anti-pattern NGHIÊM CẤM (nhánh CR)

- ❌ Vẽ CR chồng vào Output 1/2/3 hiện tại, hoặc sửa node/màu của output cũ để đánh dấu thay đổi
- ❌ CR view không có Legend / không có CR Change Table
- ❌ Node trong CR view không badge NEW/UPD/DEL/AS-IS → người xem không biết chỗ nào tạo mới, chỗ nào sửa cũ
- ❌ Vẽ CR trước khi gọi `AskUserQuestion` §2
- ❌ Gọi là CR mà không trích được bằng chứng baseline (§1)
- ❌ Bỏ `output_cr.md`, hoặc viết `output_cr.md` dài dòng như SPEC
- ❌ Đưa man-day / giá / kết luận thương mại vào `output_cr.md`
- ❌ Ghi CR vào Happy Path / AC của SPEC khi KH chưa chốt
- ❌ Overwrite version cũ thay vì tạo `v<N+1>`
