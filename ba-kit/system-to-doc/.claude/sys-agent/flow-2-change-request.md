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
> Kết quả: folder version MỚI với **1 file `CR-<id>_Impact.xlsx` (2 sheet)**. **Không sửa baseline, không vẽ đè Figma cũ.**

---

## 0. Điều kiện vào

| Cần | Kiểm bằng | Thiếu thì |
|---|---|---|
| Baseline | `version-tool.py latest-baseline --outputs outputs` | ⛔ DỪNG — đề nghị chạy Luồng 1 (ít nhất phần site/repo liên quan CR) |
| `_internal/inventory.xlsx` của baseline | file tồn tại, gate V2 của baseline PASS | ⛔ DỪNG — baseline hỏng thì impact sai |
| Bảng đơn giá MD | `.claude/config/md-unit-rates.json` | Vẫn chạy; `status ≠ APPROVED` → Summary ghi rõ **"Ước lượng sơ bộ — chưa được PM/Tech Lead duyệt"** |
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
| 5 | Phân tích 6 trục (§4) → ghi `<ver>/_internal/cr.json` → `build-cr-impact.py` → `CR-<id>_Impact.xlsx` | 🔴 **V-CR** |
| 6 | Figma view CR (§5) | 🟡 **CR-2** · 🔴 **V-CR-FIGMA** |
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
| **CR** | Thoả ≥ 1 tiêu chí C1–C6 (§3.2) | Giải trình (§3.3) + vào sheet Impact |
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
              "rate_code","qty","md_note","evidence","question"}]}
```

```bash
python3 $S/build-cr-impact.py --cr-json $V/_internal/cr.json --rates .claude/config/md-unit-rates.json \
    --out $V/CR-<id>_Impact.xlsx
python3 $S/verify-cr-impact.py $V/CR-<id>_Impact.xlsx --cr-json $V/_internal/cr.json \
    --baseline outputs/<baseline-folder> [--other-cr outputs/<CR khác đang mở>/_internal/cr.json] \
    --out $V/_internal/gates/v-cr.md
```

### 4.3 Workbook — đúng **2 sheet**

| Sheet | Nội dung (script sinh, agent không gõ tay) |
|---|---|
| **`Summary`** | ① Khối đầu: CR · tiêu đề · baseline · nguồn · ngày · người yêu cầu (vai trò) · mức ảnh hưởng chung · đề xuất. ② **Vì sao đây là Change Request** (bảng §3.3). ③ **Tổng MD** — ma trận Trục × Loại + tổng, dòng đơn giá (`DRAFT` → cảnh báo "ước lượng sơ bộ"). ④ Trục không ảnh hưởng + lý do. ⑤ Câu hỏi cần khách trả lời. ⑥ Không thuộc CR (BUG / QUESTION) — nếu có |
| **`Impact`** | 1 dòng / hạng mục: `No · Impact ID · Trục · Loại · Baseline Ref · Hạng mục · Nội dung thay đổi · Vì sao phải sửa · Ảnh hưởng tới hiện tại · Xung đột · Chi tiết xung đột · Rủi ro · Mã đơn giá · Số lượng · MD · Ghi chú MD · Evidence · Câu hỏi` + dòng **Tổng MD** |

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

Gate V-CR chặn mọi vi phạm trên + **MD / tổng trong xlsx khác đơn giá × số lượng** (sửa tay). WARN: đơn giá chưa `APPROVED`; CR khác đang mở cũng sửa cùng thứ (phải nêu ở mục đề xuất).

---

## 5. Figma — view CR mới, chỉ phần liên quan trực tiếp

### CR-2 (AskUserQuestion)
```
Vẽ view CR lên Figma?
  [A] Có — cùng file flow của baseline: <figma_output_url của baseline>
  [B] Có — file/page khác (Other: link)
  [C] Không vẽ lần này
```

### Luật vẽ (khung kỹ thuật copy từ requirement-to-flow — `skills/ba-figma-output/SKILL.md` + `sys-agent/figma/`)

- **Section mới** `CR-<id> — <tiêu đề> (baseline ver<K>)`, cách bbox thấp nhất của mọi node hiện có **≥ 400 px** (đo bằng `get_metadata`). Nhiều CR → mỗi CR 1 section, cách nhau ≥ 400 px.
- **Không** remove / move / resize / recolor / relabel node nào của Output 1/2 hay CR trước.
- **Phạm vi — POLICY:** chỉ vẽ (a) hạng mục có dòng trong sheet Impact (`NEW` / `UPD` / `DEL` / `IMPACT`) và (b) hàng xóm **đúng 1 bước** của chúng để thấy chỗ nối (`AS-IS`). Không vẽ lại toàn hệ thống, không vẽ "cho đẹp". **Máy kiểm** bằng V-CR-FIGMA.
- **Tô màu — mỗi node đúng 1 badge, tên node `<BADGE> · <REF> · <nhãn>`** (`REF` = Baseline Ref của dòng Impact; hạng mục `NEW` chưa có trong baseline → dùng Impact ID, VD `NEW · IMP-004 · Ô mã giảm giá`). Mỗi node gắn thêm `setSharedPluginData("cr", "kind", "screen|flow|table-row|other")` để script đọc ngược phân loại được:

| Badge | Màu (fill / stroke) | Dùng cho |
|---|---|---|
| `NEW` | `#EDFDF0` / `#1A7F37` | thêm mới |
| `UPD` | `#FFF9EB` / `#F4860C` nét đứt, ghi "cũ → mới" | sửa |
| `DEL` | `#FFF6F5` / `#CF222E` nét đứt, gạch ngang | xoá |
| `IMPACT` | `#FBEEFF` / `#6639BA` nét đứt, ghi "bị ảnh hưởng qua <API-xxx / table:…>" | không sửa nhưng **bị kéo theo**, cần kiểm lại |
| `AS-IS` | `#F6F8FA` / `#D0D7DE`, opacity 0.6 | hàng xóm không đổi, chỉ để thấy chỗ nối |

- Sub-view: **CR-1 Flow** (đoạn luồng bị đổi) · **CR-2 Screen Flow** (màn bị đổi + hàng xóm) · **CR Change Table** (bắt buộc: Impact ID · badge · Baseline Ref · nội dung · MD).
- Mockup màn `NEW` / `UPD` (khi user yêu cầu): dùng **token / type style / component Design System của baseline** đúng tên trong README của nó.
- **Kiểm sau khi vẽ — không bằng mắt:**
```bash
# 1. use_figma đọc ngược section CR → $V/_internal/cr-figma-nodes.json (snippet trong docstring verify-cr-figma.py)
# 2. bbox không chồng node cũ: script Tiêu chí 7 trong sys-agent/figma/recheck.md
python3 $S/verify-cr-figma.py --nodes $V/_internal/cr-figma-nodes.json --cr-json $V/_internal/cr.json \
    --baseline outputs/<baseline-folder> --out $V/_internal/gates/v-cr-figma.md
```
  V-CR-FIGMA chặn: node ngoài phạm vi (không phải hạng mục Impact, không phải hàng xóm 1 bước) · badge khác `Loại` của dòng Impact · màn / chức năng bị đổi mà không vẽ · số dòng CR Change Table ≠ số hạng mục đã vẽ.
- Ghi link node vào `<ver>/05_Figma/figma-links.md`.

---

## 6. Thành phẩm folder CR

```
ver<N>_<DDMMYY>_CR-<id>-<slug>/
├── README.md                  mục lục (build-version-index)
├── run-log.md                 baseline: ver<K>_…
├── input/                     CR nguyên văn
├── CR-<id>_Impact.xlsx        2 sheet: Summary · Impact   ← gửi khách được
├── 05_Figma/figma-links.md    (nếu vẽ)
└── _internal/  cr.json · cr-figma-nodes.json · gates/
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
