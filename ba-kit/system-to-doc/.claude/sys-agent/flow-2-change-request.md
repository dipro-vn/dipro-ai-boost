# Luồng 2 — Change Request trên hệ thống hiện tại

> **Mục đích:** khi khách gửi 1 yêu cầu thay đổi (CR), trả lời được 6 câu hỏi **dựa trên baseline đã có bằng chứng**, kèm **giải trình vì sao là CR** và **tổng MD**:
>
> | Trục | Câu hỏi phải trả lời |
> |---|---|
> | **System** | CR tác động tới hệ thống hiện tại thế nào (site / repo / module / API / batch nào) |
> | **DB** | Thêm gì? Có xung đột với cái cũ không? |
> | **Business** | Nghiệp vụ sửa gì? Ảnh hưởng tới nghiệp vụ hiện tại không? |
> | **Screen** | Thêm / sửa / xoá màn nào? Ảnh hưởng tới các màn hiện tại không? |
> | **ThirdParty** | Có thêm liên kết nào? Ảnh hưởng liên kết hiện tại không? |
> | **Mockup** | Màn mới / sửa có nhất quán với Design System hệ thống cũ không? |
>
> Kết quả: folder version MỚI với **1 file `CR-<id>_Impact.xlsx` (7 sheet: Summary · Estimation · Screen · API · Database · Figma · Q&A)** + view CR trên Figma theo **format Output 1 / Output 2** + màn đề xuất bám Design System. **Không sửa baseline, không vẽ đè Figma cũ.**

---

## 0. Điều kiện vào

| Cần | Kiểm bằng | Thiếu thì |
|---|---|---|
| Môi trường | `ensure-env.py --flow 2` (+ `--figma` khi CR-2 chọn vẽ) — **tự cài**, user không cài tay | `BLOCKED` → xlsx = `❌ Blocked`; Figma `NEED_AUTH` → nhờ user `/mcp` → Authenticate, chưa xong thì bỏ view CR, chạy tiếp |
| Baseline | `version-tool.py latest-baseline --outputs outputs` | ⛔ DỪNG — đề nghị chạy Luồng 1 (ít nhất phần site/repo liên quan CR) |
| `_internal/inventory.xlsx` của baseline | file tồn tại, gate V2 của baseline PASS | ⛔ DỪNG — baseline hỏng thì impact sai |
| Bảng đơn giá MD | `.claude/config/md-unit-rates.json` | Vẫn chạy; `status ≠ APPROVED` → Summary ghi rõ **"Ước lượng sơ bộ — chưa được PM/Tech Lead duyệt"** |
| Template estimation | `templates/template_estimation.xlsx` (bóc từ 見積書 công ty bằng `extract-estimation-template.py`) | ⛔ build từ chối — bóc template trước (§4.5) |
| Nội dung CR | §1 | Hỏi user |

---

## 1. Nhận CR — 3 cách user đưa vào

| Cách | User làm gì | Agent làm gì |
|---|---|---|
| **File** (khuyến nghị) | Bỏ file vào `inputs/cr/` (`.docx` `.pdf` `.xlsx` `.md` `.png` ảnh chụp email/mockup) rồi gõ `/change-request inputs/cr/<file>` | `scan-sensitive.py --path inputs/cr/<file> --out inputs/cr/.sensitive.md` trước → đọc → copy file vào `<ver>/input/` |
| **Dán trực tiếp** trong Claude Code | `/change-request` + dán nội dung yêu cầu | Lưu nguyên văn vào `<ver>/input/cr-request.md` (đã che PII nếu có) |
| **Link** (Backlog / Google Drive / Figma) | `/change-request <link>` | Có connector (Backlog MCP, Drive MCP, Figma MCP) → đọc qua connector. Không có → nhờ user tải file về `inputs/cr/` hoặc dán nội dung. Lưu link + nội dung vào `<ver>/input/link.md`. **Không** tự fetch URL lạ |

⛔ CR chứa tên / email / SĐT khách hàng thật, dữ liệu giao dịch → thay bằng vai trò / dữ liệu mẫu trước khi lưu (`DATA-PRIVACY.md` §4). Hook H06 chặn nếu quên.

---

## 2. Quy trình

| Bước | Việc | Gate |
|---|---|---|
| 0 | Nhận CR (§1), tách thành **danh sách item** `CR-001.1, .2…` | — |
| 1 | `latest-baseline` + `list --outputs outputs` → in tình hình baseline + CR đang mở | 🟡 **CR-0** |
| 2 | **Phân loại + giải trình** từng item (§3) | — |
| 3 | Item mơ hồ → hỏi | 🟡 **CR-1** |
| 4 | `version-tool.py next --outputs outputs --cr-id CR-<id> --slug <slug> --create` | — |
| 5 | Phân tích 6 trục (§4) → ghi `<ver>/_internal/cr.json` → `build-cr-impact.py` → `CR-<id>_Impact.xlsx` (7 sheet) | 🔴 **V-CR** |
| 6 | Figma view CR (§5 + `figma/cr-view.md`): CR-1 Flow (Output 1) · CR-2 Screen Flow (Output 2) · CR Change Table (thống kê) · CR-3 màn đề xuất (đọc Design System trước) | 🟡 **CR-2 · CR-3 · CR-3b** · 🔴 **V-CR-FIGMA** |
| 7 | `detect-pii.js --scan <ver>` · `build-version-index.py <ver>` · run-log · report | 🔴 H06 |

### CR-0 — xác nhận baseline (AskUserQuestion)
```
CR: "<tiêu đề>" — <n> item. Đối chiếu với baseline ver<K>_<...> (<ngày>): <a> site · <m> màn · <p> API · <t> bảng.
CR đang mở sau baseline: <CR-xxx (ver..), ...> hoặc "không có".
  [A] Đúng baseline này, mã CR = CR-<id>  (Other: đổi mã/tiêu đề)
  [B] Hệ thống đã đổi so với baseline — chạy Luồng 1 DELTA trước
  [C] Dùng baseline khác — chỉ định
```

### CR-1 — làm rõ (chỉ khi cần, ≤ 4 câu / lượt)
Hỏi đúng chỗ thiếu. User không trả lời được → câu hỏi `CQ-xxx` trong `cr.json`, dòng impact liên quan `Xung đột = UNKNOWN`, **không** tự chọn đáp án.

---

## 3. Phân loại + giải trình "vì sao đây là CR"

### 3.1 Nhãn

| Nhãn | Dấu hiệu (đối chiếu baseline) | Xử lý |
|---|---|---|
| **CR** | Thoả ≥ 1 tiêu chí C1–C6 (§3.2) | Giải trình (§3.3) + hạng mục impact (§4) |
| **BUG** | Khách mô tả hành vi *đúng như baseline đã ghi là phải có* (`Confirmed` / tài liệu đã duyệt) nhưng hệ thống chạy sai | Không phải CR → `not_cr`, đề nghị đưa vào bug list |
| **QUESTION** | Hỏi hệ thống đang làm gì | Trả lời từ baseline (ID + evidence) → `not_cr`; baseline không có → CQ |
| **CHƯA RÕ** | Vùng baseline `UNKNOWN` / `To verify` | Hỏi CR-1, **không** tự chọn nhãn |

### 3.2 Tiêu chí CR (định nghĩa ở `inv_schema.CR_CRITERIA` — chỉnh từ C1–C6 của requirement-to-flow cho chiều AS-IS)

| Mã | Tiêu chí |
|---|---|
| **C1** | Chức năng / màn / API / bảng **mới**, chưa có trong hệ thống hiện tại |
| **C2** | Đổi hành vi đang chạy đã `Confirmed` trong baseline (khách đổi ý, không phải hệ thống lỗi) |
| **C3** | Thêm / bỏ màn, actor, chức năng, liên kết bên thứ 3 |
| **C4** | Đổi business rule / validation đang chạy |
| **C5** | Đổi nền tảng / thiết bị / yêu cầu phi chức năng (hiệu năng, bảo mật, trình duyệt) |
| **C6** | Kéo theo đổi schema DB, API contract hoặc tài liệu đã bàn giao |

### 3.3 Giải trình — viết cho khách, **trọng tâm, không lan man**

Mỗi item CR = 1 dòng `justification` trong `cr.json` → sheet **Summary** mục "Vì sao đây là Change Request":

| Trường | Viết gì | Ví dụ |
|---|---|---|
| `request` | 1–2 dòng yêu cầu khách | "Thêm ô nhập mã giảm giá ở màn xác nhận đơn" |
| `baseline_ref` + `baseline_quote` | ID baseline + **nội dung thật đang ghi** (đọc từ file, không nhớ) | `SC-014` — "Màn xác nhận đơn có 6 item, không có ô mã giảm giá" |
| `criteria` | Mã tiêu chí | `C1`, `C6` |
| `why` | ≤ 2 câu vì sao vượt hệ thống hiện tại | "Hệ thống chưa có khái niệm mã giảm giá; cần bảng mới và đổi API tạo đơn." |
| `not_feedback` | 1 câu vì sao không phải lỗi hệ thống | "Màn đang chạy đúng như thiết kế hiện tại." |

Giọng trung tính. ❌ Không "khách đổi ý liên tục", "yêu cầu vô lý". ❌ Không giải trình bằng cảm tính — không trích được baseline thì **không được gọi là CR**, chuyển CHƯA RÕ.

---

## 4. Phân tích impact — `CR-<id>_Impact.xlsx`

### 4.1 Cách lần ra ảnh hưởng (không phải cảm giác)

1. **Điểm chạm trực tiếp:** từ nội dung CR, tìm ID trong baseline inventory (`02_Screen`, `01_Function`, `07_API`, `03/04_DB`, `09_Integration`, `10_Site`) và Design System (`04_DesignSystem/…/project/README.md` trước, rồi `tokens.json`, `components/<Comp>/README.md`; đã publish → `read` artifact theo dòng `- Artifact:` trong `STATUS.md`).
2. **Lan 1–2 bước** theo liên kết đã có trong inventory:
```
Screen ──Function IDs──▶ Function ──Screen IDs/Related Tables──▶ Table
   │                                                              ▲
   └──(07_API.Called By Screens)──▶ API ──Related Tables──────────┘
Table ──(07_API.Related Tables ngược)──▶ API khác ──▶ Screen khác   ← "ảnh hưởng tới cái hiện tại"
Integration ──Used By──▶ Function / API
Screen ──Entry From──▶ màn dẫn tới nó
```
3. Thứ **bị sửa** → `NEW` / `UPD` / `DEL`. Thứ **không sửa nhưng bị kéo theo** (màn khác gọi cùng API vừa đổi, báo cáo đọc bảng vừa đổi…) → **`IMPACT`** (kiểm lại / chỉnh nhỏ) — ghi rõ **qua liên kết nào**.
4. Liên kết trong baseline là `Inferred` / `To verify` → `Xung đột = UNKNOWN` + câu hỏi.

### 4.2 Nguồn dữ liệu: `<ver>/_internal/cr.json` (agent viết) → script render xlsx

```json
{"meta": {"cr_id","cr_title","baseline_version","cr_version","source_type":"FILE|CHAT|LINK","source_ref",
          "received_date","requested_by":"<vai trò>","overall_risk":"High|Medium|Low","recommendation"},
 "justification": [ … §3.3 … ],
 "not_cr": [{"item","label":"BUG|QUESTION","reason","baseline_ref"}],
 "no_impact_axes": [{"axis":"ThirdParty","reason":"Không thêm / đổi liên kết nào — CR chỉ chạm màn và DB nội bộ"}],
 "questions": [{"id":"CQ-001","question","why","axis","owner","status"}],
 "impacts": [{"id":"IMP-001","axis","change_type":"NEW|UPD|DEL|IMPACT","baseline_ref","item","change",
              "why_change","impact_on_current","conflict":"Yes|No|UNKNOWN","conflict_detail","risk",
              "rate_code","qty","md_note","evidence","question",
              "cr_item":"CR-001.3","option":false}]}
```

```bash
python3 $S/build-cr-impact.py --cr-json $V/_internal/cr.json --rates .claude/config/md-unit-rates.json \
    --out $V/CR-<id>_Impact.xlsx          # [--template templates/template_estimation.xlsx]
python3 $S/verify-cr-impact.py $V/CR-<id>_Impact.xlsx --cr-json $V/_internal/cr.json \
    --baseline outputs/<baseline-folder> [--other-cr outputs/<CR khác đang mở>/_internal/cr.json] \
    --out $V/_internal/gates/v-cr.md
```

### 4.3 Workbook — đúng **7 sheet** (thứ tự cố định, `inv_schema.CR_SHEETS`)

| Sheet | Nội dung (script sinh, agent không gõ tay) |
|---|---|
| **`Summary`** | **Chỉ cơ bản**: khối đầu (CR · baseline · nguồn · ngày · người yêu cầu (vai trò) · mức ảnh hưởng) · **1. Công số thay đổi**: 実装 MD (= tổng đơn giá × số lượng), 総工数 人日 + 人月 (**công thức link** `='Estimation'!P<合計>`), tách 最小改修案 / 拡張案 (theo cờ `option`), link **→ sheet Estimation**, dòng đơn giá (DRAFT → cảnh báo) · **2. Số đối tượng thay đổi**: Màn hình · API · Batch · Bảng DB · Cột DB · Rule nghiệp vụ · Liên kết bên thứ 3 · Mockup · Token DS × `NEW / UPD / DEL / IMPACT / Tổng / 実装 MD` · **3. Link** tới từng sheet chi tiết |
| **`Estimation`** | Copy nguyên khung `templates/template_estimation.xlsx` (letterhead, 御見積書, ■件名/■見積日, header 2 dòng, validation). 1 section `◆ CR-001.x — <yêu cầu>` / item justification, 1 dòng / hạng mục: `No.` = Impact ID · 項目(大) = trục (loại) · 項目(中) = Baseline Ref · 項目(小) = hạng mục · 改修内容 · QA/Note (CQ chờ, xung đột, ghi chú MD) · Tái sử dụng / Phát triển mới (NEW → phát triển mới) · option (= `option`) · **実装 = MD** · 要件定義 / UI・UX / テスト / 管理 / 小計 = **công thức hệ số của template** · cột Q = căn cứ (mã đơn giá × SL) · 合計 人日 + 人月 · ◆前提条件 |
| **`Screen`** · **`API`** · **`Database`** · **`Figma`** | Hạng mục trục Screen · System · DB · Mockup — 1 dòng / hạng mục: `No · Impact ID · Trục · Loại · Baseline Ref · Hạng mục · Nội dung thay đổi · Vì sao phải sửa · Ảnh hưởng tới hiện tại · Xung đột · Chi tiết xung đột · Rủi ro · Mã đơn giá · Số lượng · MD · Ghi chú MD · Evidence · Câu hỏi` + dòng **Tổng MD**. Trục không có hạng mục → 1 dòng lý do (`no_impact_axes`) |
| **`Q&A`** | Mức ảnh hưởng + đề xuất · **Vì sao đây là Change Request** (bảng §3.3) · **Câu hỏi cần khách trả lời** (CQ) · Trục không ảnh hưởng · Không thuộc CR (BUG / QUESTION) |

Trục **Business** + **ThirdParty** không có sheet riêng (luồng nghiệp vụ đã thể hiện ở Figma CR-1) — vẫn đủ dòng trong **Estimation** và trong thống kê Summary.

### 4.4 Luật

| Mục | Bắt buộc |
|---|---|
| 6 trục | Mỗi trục có ≥ 1 dòng impact **hoặc** nằm trong `no_impact_axes` với lý do ≥ 15 ký tự — sếp cần đủ 6 câu trả lời |
| `Vì sao phải sửa` | Mọi dòng — gắn với yêu cầu CR nào, vì sao hạng mục này phải đổi |
| **MD** | Agent **chỉ chọn** `rate_code` (dòng bảng đơn giá đúng trục + loại) và `qty`; **MD = đơn giá × số lượng do script tính**. Agent không gõ số MD. Hạng mục không khớp dòng nào → báo PM bổ sung bảng, không tự chế |
| `Baseline Ref` | Phân giải được trong baseline: `SC-` · `F-` · `API-` · `EXT-` · `WEB-` · `table:<t>` · `column:<t>.<c>` · `DS:<token>` / `DS:WEB-01:<token>` · `DS-component:<Comp>` · `—` (chỉ cho `NEW`) |
| `UPD` / `DEL` / `IMPACT` | Ref phải có thật trong baseline. `DEL` màn → liệt kê màn dẫn tới nó |
| DB | Cột `NEW` trùng tên cột đã có → `Xung đột = Yes`. Đổi kiểu / NOT NULL / FK trên cột đang được API khác dùng → `Rủi ro ≥ Medium` + các dòng `IMPACT` cho API / màn bị kéo theo |
| ThirdParty | Liên kết mới → loại, chiều, **tên** config key cần thêm (không giá trị) |
| Mockup | Màn `NEW` / `UPD` trỏ ≥ 1 `DS:` / `DS-component:` dùng lại. Cần màu / component chưa có (hoặc đang TBD trong `STATUS.md`) → dòng `UI-TOKEN-NEW` + CQ cho designer, **không** tự chế |
| `Xung đột = Yes` / `Rủi ro = High` | Có chi tiết + (câu hỏi hoặc ghi chú hướng xử lý) |
| Evidence | Trích đoạn CR (`input/<file> §2`) hoặc file baseline (`ver1/_internal/inventory.xlsx 07_API API-022`) |
| `cr_item` | Mọi hạng mục gắn 1 item justification (`CR-001.3`) → section của Estimation; mọi item CR có ≥ 1 hạng mục |
| `option` | `true` = hạng mục thuộc 拡張案 (phương án mở rộng) → cột option + tách 最小改修案 / 拡張案 trên Summary. Không đoán: KH chưa nói rõ phương án → hỏi CR-1 |

Gate V-CR chặn mọi vi phạm trên + **MD / tổng trong xlsx khác đơn giá × số lượng** (sửa tay) + Summary gõ số thay vì link Estimation + công thức Estimation khác hệ số template + bảng số đối tượng lệch + Q&A thiếu giải trình / CQ. WARN: đơn giá chưa `APPROVED`; CR khác đang mở cũng sửa cùng thứ (phải nêu ở mục đề xuất).

### 4.5 Template estimation — bóc 1 lần từ 見積書 của công ty

```bash
python3 $S/extract-estimation-template.py --src "<見積書 đã gửi KH>.xlsx" --sheet "見積書(VN)" \
    --out templates/template_estimation.xlsx
```
Giữ letterhead / logo / header / validation / ◆前提条件; bỏ dữ liệu dự án (khách, tên dự án, ngày, từng dòng, số tiền) → placeholder. **Hệ số công đoạn đọc từ công thức** dòng hạng mục đầu của file nguồn (VD 要件定義 = 実装 × 0.2 · UI/UX × 0.2 · テスト × 0.5 · 管理 = tổng × 0.2 · 人月 = 人日 / 20) → sheet ẩn `_meta`. Đổi hệ số = sửa / bóc lại template, **không sửa code**. Kit **không tính tiền** (ô 合計金額 để trống — việc của PM).

---

## 5. Figma — view CR mới, đúng format Output 1 / Output 2 (chi tiết: `figma/cr-view.md`)

### CR-2 / CR-3 / CR-3b (AskUserQuestion — wording ở `figma/cr-view.md` §3)
- **CR-2** vẽ hay không, file nào. **CR-3** phạm vi màn đề xuất (NEW / NEW + UPD / chọn màn / không). **CR-3b** khi màn cần component Design System site chưa có (mượn site khác hay UI-TOKEN-NEW + CQ). Không tự chọn thay user.

### Luật vẽ (tóm tắt — đầy đủ ở `figma/cr-view.md`)
- **Section mới** `CR-<id> — <tiêu đề> (baseline ver<K> → ver<N>)`, cách bbox thấp nhất của mọi node hiện có **≥ 400 px**. **Không** remove / move / resize / recolor / relabel node của Output 1/2 hay CR trước.
- **CR-1 Flow** = Output 1 Phần A (lane `FL-xx` bị chạm: ACTOR → TRIGGER → FUNCTION → TECHNOLOGY → OUTCOME · EDGE) + Phần B Technology. **CR-2 Screen Flow** = Output 2 (Group · Start · Screen · Decision · System · NG inline · Terminal · Edge/Exceptional · ④ Screen Index). Mọi node nối bằng **mũi tên thật**.
- **Phạm vi — POLICY:** chỉ hạng mục có dòng Impact + hàng xóm **đúng 1 bước** / lane `FL-xx` baseline làm ngữ cảnh (`AS-IS`).
- **CR Change Table = THỐNG KÊ**: số đối tượng NEW / UPD / DEL / IMPACT (Màn hình · API · Bảng DB · Cột DB · …) + 実装 MD · 総工数 人日 · 人月 · 最小改修案 / 拡張案. **Không** liệt kê lại từng hạng mục (đã có trong xlsx).
- **CR-3 màn đề xuất**: **đọc Design System trước** (README → tokens.json → component README → STATUS.md, khai vào `screens.ds_read`) → chỉ token / component của DS; thiếu → theo CR-3b. Máy kiểm màu ⊆ token.
- Mỗi node đúng 1 badge, tên `<BADGE> · <REF> · <nhãn>`, `setSharedPluginData("crkit", "kind", …)` (Figma bắt buộc namespace ≥ 3 ký tự).
- **Không tự viết JS vẽ**: agent viết `_internal/cr-figma.json` → `render-cr-figma.py` sinh JS → `use_figma` → `99-readback.js` → `verify-cr-figma.py` `FAIL = 0`.
- Ghi link node vào `<ver>/05_Figma/figma-links.md`.

---

## 6. Thành phẩm folder CR

```
ver<N>_<DDMMYY>_CR-<id>-<slug>/
├── README.md                  mục lục (build-version-index)
├── run-log.md                 baseline: ver<K>_…
├── input/                     CR nguyên văn
├── CR-<id>_Impact.xlsx        7 sheet: Summary · Estimation · Screen · API · Database · Figma · Q&A   ← gửi khách được
├── 05_Figma/figma-links.md    (nếu vẽ)
└── _internal/  cr.json · cr-figma.json · figma-js/ · cr-figma-nodes.json · gates/
```

---

## 7. Anti-pattern

- ❌ Phân tích impact khi chưa xác định baseline / dùng trí nhớ thay vì đọc inventory
- ❌ Gọi là CR mà không trích được baseline; giải trình lan man, cảm tính
- ❌ Gõ tay số MD hoặc sửa MD trong xlsx — chỉ chọn mã đơn giá + số lượng
- ❌ Ghi `UPD SC-099` mà baseline không có `SC-099`
- ❌ Bỏ trống trục "không liên quan" thay vì ghi vào `no_impact_axes` + lý do
- ❌ Vẽ `AS-IS` xám cho thứ thật ra bị ảnh hưởng — phải là `IMPACT`
- ❌ Vẽ ngoài phạm vi CR, vẽ lại toàn bộ flow, sửa / di chuyển node Figma cũ
- ❌ Tự chế màu / component mới cho mockup mà không ghi dòng `UI-TOKEN-NEW` + CQ
- ❌ Lưu tên / email người gửi CR — dùng vai trò
- ❌ Vẽ view CR theo bố cục tự chế (lưới thẻ không mũi tên) thay vì khung Output 1 / Output 2 — lỗi đã xảy ra ở CR-001
- ❌ CR Change Table liệt kê lại từng hạng mục — chỉ thống kê
- ❌ Vẽ màn đề xuất trước khi đọc Design System / dùng màu, component không có trong DS mà không hỏi CR-3b
- ❌ Gõ số công số vào Summary thay vì link sheet Estimation; sửa hệ số công đoạn trong code thay vì template
