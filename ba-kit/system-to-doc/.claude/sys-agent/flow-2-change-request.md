# Luồng 2 — Change Request trên hệ thống hiện tại

> **Mục đích:** khi khách gửi 1 yêu cầu thay đổi (CR), trả lời được 6 câu hỏi **dựa trên baseline đã có bằng chứng**, không dựa trên trí nhớ hay phỏng đoán:
>
> | Trục | Câu hỏi phải trả lời |
> |---|---|
> | **System** | CR mới tác động tới hệ thống hiện tại thế nào (site / repo / module / batch nào) |
> | **DB** | Thêm gì? Có xung đột với cái cũ không? |
> | **Business** | Nghiệp vụ sửa gì? Ảnh hưởng tới nghiệp vụ hiện tại không? |
> | **Screen** | Thêm / sửa / xoá màn nào? Ảnh hưởng tới các màn hiện tại không? |
> | **Third-party** | Có thêm liên kết nào? Ảnh hưởng liên kết hiện tại không? |
> | **Mockup** | Màn mới/sửa có nhất quán với Design System hệ thống cũ không? |
>
> Kết quả: folder version MỚI. **Không sửa baseline, không vẽ đè Figma cũ.**

---

## 0. Điều kiện vào

| Cần | Kiểm bằng | Thiếu thì |
|---|---|---|
| Baseline | `version-tool.py latest-baseline --outputs outputs` | ⛔ DỪNG — đề nghị chạy Luồng 1 (ít nhất phần site/repo liên quan CR) |
| `_internal/inventory.xlsx` của baseline | file tồn tại, gate V2 của baseline PASS | ⛔ DỪNG — baseline hỏng thì impact sai |
| Nội dung CR | §1 | Hỏi user |

---

## 1. Nhận CR — 3 cách user đưa vào

| Cách | User làm gì | Agent làm gì |
|---|---|---|
| **File** (khuyến nghị) | Bỏ file vào `inputs/cr/` (`.docx` `.pdf` `.xlsx` `.md` `.png` ảnh chụp email/mockup) rồi gõ `/change-request inputs/cr/<file>` | Chạy `scan-sensitive.py --path inputs/cr/<file> --out <ver>/_internal/gates/sensitive.md` trước (chưa có folder version → `--out` tạm `inputs/cr/.sensitive.md`) → đọc → copy file vào `<ver>/input/` |
| **Dán trực tiếp** trong Claude Code | `/change-request` + dán nội dung yêu cầu | Lưu nguyên văn vào `<ver>/input/cr-request.md` (đã che PII nếu có) |
| **Link** (Backlog / Google Drive / Figma) | `/change-request <link>` | Có connector tương ứng (Backlog MCP, Drive MCP, Figma MCP) → đọc qua connector. Không có → nhờ user tải file về `inputs/cr/` hoặc dán nội dung. Lưu link + nội dung vào `<ver>/input/link.md`. **Không** tự fetch URL lạ |

⛔ CR chứa tên/email/SĐT khách hàng thật, dữ liệu giao dịch → thay bằng vai trò / dữ liệu mẫu trước khi lưu (`DATA-PRIVACY.md` §4). Hook H06 sẽ chặn nếu quên.

---

## 2. Quy trình

| Bước | Việc | Gate |
|---|---|---|
| 0 | Nhận CR (§1), tách thành **danh sách item** đánh số `CR-001.1, .2…` | — |
| 1 | `version-tool.py latest-baseline --outputs outputs` + `list --outputs outputs` → in tình hình baseline + CR đang mở | 🟡 **CR-0** |
| 2 | Phân loại từng item (§3) — item không phải CR thì tách ra | — |
| 3 | Item mơ hồ → hỏi | 🟡 **CR-1** |
| 4 | `version-tool.py next --outputs outputs --cr-id CR-<id> --slug <slug> --create` + `build-inventory.py --cr --out <ver>/CR-<id>_Impact.xlsx` | — |
| 5 | Phân tích 6 trục (§4) → ghi workbook | 🔴 **V-CR** |
| 6 | Figma view CR (§5) | 🟡 **CR-2** |
| 7 | `CR-<id>_Summary.md` (§6) + `detect-pii --scan` + `build-version-index.py` + run-log + report | 🔴 H06 |

### CR-0 — xác nhận baseline (AskUserQuestion)
```
CR: "<tiêu đề>" — <n> item. Đối chiếu với baseline ver<K>_<...> (<ngày>): <a> site · <m> màn · <p> API · <t> bảng.
CR đang mở sau baseline: <CR-xxx (ver..), ...> hoặc "không có".
  [A] Đúng baseline này, mã CR = CR-<id>  (Other: đổi mã/tiêu đề)
  [B] Hệ thống đã đổi so với baseline — chạy Luồng 1 DELTA trước
  [C] Dùng baseline khác — chỉ định
```

### CR-1 — làm rõ (chỉ khi cần, tối đa 4 câu/lượt)
Hỏi đúng chỗ thiếu: *"Item .2 'thêm trạng thái tạm hoãn' — áp dụng cho đơn đã thanh toán không?"*. User không trả lời được → ghi vào sheet `07_Questions`, trục liên quan `Conflict = UNKNOWN`, **không** tự chọn đáp án.

---

## 3. Phân loại item — không phải cái gì khách gửi cũng là CR

| Nhãn | Dấu hiệu (đối chiếu baseline) | Xử lý |
|---|---|---|
| **CR** | Thêm mới / đổi hành vi so với cái baseline mô tả `Confirmed` | Vào workbook impact |
| **BUG** | Khách mô tả hành vi *đúng như baseline đã ghi là phải có*, nhưng hệ thống chạy sai | Không phải CR. Ghi 1 dòng ở `CR-<id>_Summary.md` mục "Không thuộc CR", đề nghị đưa vào bug list |
| **QUESTION** | Hỏi hệ thống đang làm gì | Trả lời từ baseline (trích ID + evidence); không có trong baseline → `07_Questions` |
| **CHƯA RÕ** | Baseline không có dữ liệu để phân định (vùng `UNKNOWN`/`To verify`) | Hỏi CR-1, **không** tự chọn nhãn |

Mỗi nhãn phải trích **bằng chứng baseline**: ID (`SC-014`, `API-031`…) + trạng thái của nó.

---

## 4. Phân tích impact — 6 trục

### 4.1 Cách lần ra ảnh hưởng (không phải cảm giác)

1. **Điểm chạm trực tiếp:** từ nội dung CR, tìm ID trong baseline inventory (`02_Screen`, `01_Function`, `07_API`, `03/04_DB`, `09_Integration`, `10_Site`) và Design System (`04_DesignSystem/tokens.json`, `components.md`).
2. **Lan 1–2 bước** theo liên kết đã có trong inventory:

```
Screen ──Function IDs──▶ Function ──Screen IDs/Related Tables──▶ Table
   │                                                              ▲
   └──(07_API.Called By Screens)──▶ API ──Related Tables──────────┘
                                     └──Group / Repo──▶ module / repo / batch
Table ──(07_API.Related Tables ngược)──▶ API khác ──▶ Screen khác   ← "ảnh hưởng tới cái hiện tại"
Integration ──Used By──▶ Function / API
Screen ──Entry From (02_Screen)──▶ màn dẫn tới nó (link, menu, nút quay lại)
```

3. Mỗi thứ tìm được ở bước 2 = 1 dòng `Impact On Current` (thứ hiện tại bị kéo theo), ghi rõ **qua liên kết nào**.
4. Liên kết trong baseline là `Inferred`/`To verify` → impact đó `Conflict = UNKNOWN` + câu hỏi, không khẳng định.

### 4.2 Workbook `CR-<id>_Impact.xlsx`

Sinh rỗng: `build-inventory.py --cr --out <ver>/CR-<id>_Impact.xlsx` (schema: `inv_schema.CR_SHEETS`).

| Sheet | Nội dung |
|---|---|
| `00_Summary` | `cr_id` · `cr_title` · `baseline_version` (= tên folder baseline) · `cr_version` · `source_type` (FILE/CHAT/LINK) · `source_ref` · `received_date` · `requested_by` (**vai trò**, không họ tên) · `summary` · `overall_risk` · `recommendation` |
| `01_System` … `06_Mockup` | 1 dòng = 1 thay đổi hoặc 1 ảnh hưởng |
| `07_Questions` | `CQ-001…` câu hỏi còn treo, gửi KH/Tech Lead |

**Cột mỗi trục:** `Impact ID` (IMP-001, duy nhất toàn file) · `Change Type` (NEW/UPD/DEL/NONE) · `Baseline Ref` · `Item` · `Change Description` · `Impact On Current` · `Conflict` (Yes/No/UNKNOWN) · `Conflict Detail` · `Risk` (High/Medium/Low) · `Evidence` · `Open Q` · `Note`.

**`Baseline Ref`** — phải phân giải được trong baseline (gate kiểm):

| Viết | Trỏ tới |
|---|---|
| `SC-014` · `F-031` · `API-022` · `EXT-003` · `WEB-01` | ID trong inventory |
| `table:orders` · `column:orders.status` | bảng / cột DB |
| `DS:color.status.error` · `DS-component:Button` | token / component trong Design System |
| `—` | chưa có trong baseline (chỉ cho `NEW`) |

**Luật từng trục:**

| Trục | Bắt buộc |
|---|---|
| Mọi trục | ≥ 1 dòng. Không ảnh hưởng → **1 dòng `NONE`** + lý do (≥ 15 ký tự). Bỏ trống = FAIL — sếp cần đủ 6 câu trả lời |
| `02_DB` | Cột `NEW` trùng tên cột đã có → `Conflict = Yes`. Đổi kiểu / thêm NOT NULL / đổi FK trên cột đang được API khác dùng → `Risk ≥ Medium` + liệt kê API/màn bị kéo theo |
| `04_Screen` | `UPD`/`DEL` phải trỏ `SC-` có thật. `DEL` → liệt kê màn đang dẫn tới nó (`Entry From`) |
| `05_ThirdParty` | Liên kết mới → ghi loại, chiều, **tên** config key cần thêm (không giá trị) |
| `06_Mockup` | Màn `NEW`/`UPD` phải trỏ ≥ 1 `DS:`/`DS-component:` dùng lại. Cần màu/component chưa có trong DS → ghi rõ ở Note + CQ để designer quyết, **không** tự chế token |
| `Conflict = Yes` | `Conflict Detail` + (CQ hoặc Note hướng xử lý) |
| `Risk = High` | Open Q hoặc Note nêu biện pháp |
| `Evidence` | Trích đoạn CR (`input/<file> §2`) hoặc file baseline (`ver1/_internal/inventory.xlsx 07_API API-022`) |

Gate:
```bash
python3 $S/verify-cr-impact.py <ver>/CR-<id>_Impact.xlsx --baseline outputs/<baseline-folder> \
    [--other-cr outputs/<ver CR khác đang mở>/CR-xxx_Impact.xlsx] --out <ver>/_internal/gates/v-cr.md
```
`FAIL > 0` → sửa rồi chạy lại. Gate WARN "CR khác cũng sửa cùng thứ" → **phải** nêu trong Summary.

---

## 5. Figma — view CR mới, không vẽ đè

### CR-2 (AskUserQuestion)
```
Vẽ view CR lên Figma?
  [A] Có — cùng file flow của baseline: <figma_output_url của baseline>
  [B] Có — file/page khác (Other: link)
  [C] Không vẽ lần này
```

### Luật vẽ (copy từ kit requirement-to-flow, `change-request.md` §3 — chi tiết kỹ thuật ở `skills/ba-figma-output/SKILL.md` + `sys-agent/figma/`)

- **Section mới** tên `CR-<id> — <tiêu đề> (baseline ver<K>)`, đặt cách bbox thấp nhất của mọi node hiện có **≥ 400 px** (đo bằng `get_metadata`, không ước lượng). Nhiều CR → mỗi CR 1 section, xếp chồng cách nhau ≥ 400 px.
- **Không** remove / move / resize / recolor / relabel bất kỳ node nào của Output 1/2 hay CR trước.
- **Chỉ vẽ phần liên quan CR:** màn/luồng bị chạm trực tiếp + hàng xóm 1 bước (vẽ dạng `AS-IS` mờ để thấy chỗ nối). Không vẽ lại toàn hệ thống.
- Mỗi node mang **đúng 1 badge**:

| Badge | Màu (fill / stroke) | Dùng cho |
|---|---|---|
| `NEW` | `#EDFDF0` / `#1A7F37` | thứ mới |
| `UPD` | `#FFF9EB` / `#F4860C` nét đứt, ghi "cũ → mới" | thứ sửa |
| `DEL` | `#FFF6F5` / `#CF222E` nét đứt, gạch ngang | thứ xoá |
| `AS-IS` | `#F6F8FA` / `#D0D7DE`, opacity 0.6 | hàng xóm không đổi, vẽ để thấy chỗ nối |

- `UPD`/`DEL`/`AS-IS` phải ghi Screen ID / Function ID baseline trên node.
- Sub-view: **CR-1 Flow** (đoạn luồng nghiệp vụ bị đổi) · **CR-2 Screen Flow** (màn bị đổi + hàng xóm) · **CR Change Table** (bắt buộc: Impact ID · badge · Baseline Ref · mô tả).
- Mockup màn `NEW`/`UPD` (khi user yêu cầu): dùng **màu / font / component từ `04_DesignSystem` của baseline** — đây là cách đảm bảo "mockup mới nhất quán với hệ thống cũ".
- Kiểm sau khi vẽ: số badge = số dòng CR Change Table; quét bbox không chồng lên node cũ (script trong `sys-agent/figma/code-patterns.md`), không kết luận bằng mắt.
- Ghi link node vào `<ver>/05_Figma/figma-links.md`.

---

## 6. `CR-<id>_Summary.md` — tài liệu trao đổi với KH (≤ 1 trang)

```markdown
# CR-<id> — <tiêu đề>
Baseline: ver<K>_<...> · Ngày: <DD/MM/YYYY> · Nguồn: <file/chat/link>

## Kết luận
- Mức ảnh hưởng chung: <High/Medium/Low> — <1 câu vì sao>
- Đề xuất: <làm được ngay / cần trả lời câu hỏi trước / cần tách CR>

## Ảnh hưởng (chi tiết: CR-<id>_Impact.xlsx)
| Trục | Thay đổi | Ảnh hưởng tới cái đang có | Xung đột |
|---|---|---|---|
| Hệ thống | ... | ... | ... |
| Database | ... | ... | ... |
| Nghiệp vụ | ... | ... | ... |
| Màn hình | +n mới · n sửa · n xoá | ... | ... |
| Bên thứ 3 | ... | ... | ... |
| Mockup | ... | ... | ... |

## Câu hỏi cần trả lời (CQ)
- CQ-001 ...

## Không thuộc CR
- (BUG / QUESTION tách ra ở §3, nếu có)

Figma: <link view CR> · Chi tiết: CR-<id>_Impact.xlsx
```

Ngắn, gạch đầu dòng, trỏ ID. Không dán lại toàn bộ workbook.

---

## 7. Anti-pattern

- ❌ Phân tích impact khi chưa xác định baseline / dùng trí nhớ thay vì đọc inventory
- ❌ Ghi `UPD SC-099` mà baseline không có `SC-099`
- ❌ Bỏ trống trục "không liên quan" thay vì ghi `NONE` + lý do
- ❌ Tự chọn đáp án cho chỗ CR mơ hồ
- ❌ Sửa file trong folder baseline, hoặc vẽ đè/di chuyển node Figma cũ
- ❌ Vẽ lại toàn bộ flow cho 1 CR nhỏ
- ❌ Tự chế màu/component mới cho mockup mà không đánh dấu "DS chưa có"
- ❌ Lưu tên/email người gửi CR — dùng vai trò
