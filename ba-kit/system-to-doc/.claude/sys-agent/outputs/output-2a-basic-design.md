# Output 2A — Basic Design (ghi vào master Excel công ty)

> **ON-DEMAND.** Chỉ chạy khi Output 1 đã qua mọi gate **và** user đồng ý ở Proposal Gate G11 + G12. Không có Output 2A **không** làm DoD fail.
>
> Phần lớn cơ chế tái dùng nguyên vẹn từ Output 5 của kit `requirement-to-flow`. File này chỉ ghi **khác biệt của chiều ngược** + cách bắc cầu nguồn dữ liệu.
>
> **BẮT BUỘC Read trước khi ghi:** `../basic-design/workbook-structure.md` (map cell chính xác của master workbook: 5 sheet, vùng metadata, bảng item `H9:R19`, 8 nhóm nội dung, bảng ERROR SCENARIOS).

---

## 1. Bắc cầu nguồn dữ liệu — điểm khác biệt cốt lõi

Output 5 của kit forward lấy nguồn từ `SPEC.md`. Kit này **không có SPEC**. Ánh xạ:

| Kit forward cần | Kit này dùng thay |
|---|---|
| `SPEC.md ## Screens` | **Sheet `02_Screen`** của inventory |
| `SPEC.md ## Screen Details` (item, validation, behavior) | Quan sát DOM + `code-ref` validation, mọi dòng gắn `EV ID` |
| Output 2 Screen Flow đã `APPROVED` | `01_Function.Entry / Trigger` + `02_Screen.Entry From` |
| `Source Flow Version` (`F5`) | `O1 v<N> — AS-IS baseline` |
| Ảnh mockup Output 3 | `05_Evidence` loại `screenshot` → file trong `evidence/` |

**Điều kiện vào (Input Gate):**

| Input | Bắt buộc | Điều kiện PASS |
|---|---|---|
| Output 1 | ✅ | Gate V1 · V2 · V3 · V5 đều `FAIL = 0` |
| Sheet `02_Screen` | ✅ | Mỗi Screen ID trong scope có `Status` ≠ rỗng |
| Master workbook | ✅ | User chỉ định đường dẫn, mở được bằng `openpyxl`, đủ 5 sheet |
| Ảnh UI | ⬜ | Không có → `Screen Index.UI Source = NO IMAGE — text only`. **Không phải lý do hoãn** |

---

## 2. Khác biệt AS-IS vs TO-BE khi điền sheet

| | Kit forward (TO-BE) | Kit này (AS-IS) |
|---|---|---|
| Cột `P`/`Q` | Hành vi **mong muốn** | Hành vi **quan sát được** |
| Cột `R` (Comment) | Câu hỏi treo cho BrSE | **Bắt buộc chứa `EV-xxxx`** cho mọi mô tả hành vi — gate check 16 |
| Ô không có dữ liệu | `UNKNOWN` = chưa quyết | `UNKNOWN — chưa quan sát được` = ta chưa nhìn thấy |
| `F5 Source Flow Version` | version Output 2 đã approve | `O1 v<N> — AS-IS baseline` |
| `F4 Status` | `DRAFT` → `WAITING APPROVAL` | `DRAFT` — đây là mô tả hiện trạng, chưa ai duyệt |

**Quy ước viết cột `P`/`Q` (AS-IS):**

```
・<mô tả item quan sát được>
・初期表示 / Trạng thái ban đầu: <...>
・押下時の挙動 / Hành vi khi nhấn:
  1. <nhánh đã bấm thử> → <đích quan sát được>
  2. <nhánh chưa bấm được> → UNKNOWN — chưa quan sát được
```

Cột `R` tương ứng: `EV-0031; EV-0044` — hoặc `⚠ UNKNOWN — thao tác ghi bị chặn theo G2 (Q-007)`.

❌ **Cấm** viết validation vào `P`/`Q` khi bằng chứng duy nhất là ảnh chụp. Validation cần `code-ref` hoặc một lần thử nhập thật.

---

## 3. Quy trình (9 bước — giữ nguyên khung của Output 5)

| # | Bước | Điều kiện chuyển tiếp |
|---|---|---|
| 0 | **Backup master workbook** | File backup tồn tại — chưa backup thì không ghi gì |
| 1 | Đọc lại 5 sheet thật bằng `openpyxl` | `Sample` tồn tại, `F6 = TEMPLATE_SCREEN` |
| 2 | Validate Output 1 đã qua mọi gate | Không PASS → quay lại Output 1 |
| 3 | Resolve ảnh UI từ `05_Evidence` theo Screen ID | Mỗi màn có ảnh **hoặc** khai `NO IMAGE — text only` |
| 4 | Build **Screen Creation Plan**: NEW / EXISTING / NEED CONFIRM | `NEED CONFIRM` ≠ rỗng → hỏi user, không tự tạo |
| 5 | Duplicate `Sample` → 1 sheet / screen NEW | `Sample` không bị chạm |
| 6 | Neutralize: xoá banner `A8:F8`, `F6 → WORKING_SCREEN`, điền `F1..F5` | `F6` còn `TEMPLATE_SCREEN` → gate FAIL |
| 7 | Populate metadata → ảnh (`A9+`, ≤ 840×900 px) → bảng item (`H9:R19`) | Mọi item có `EV` ở cột `R` hoặc ghi `UNKNOWN` |
| 8 | Update catalog message: reuse `Common mesage` trước, append `Screen Error message` | Mọi code trỏ trong `P`/`Q` tồn tại thật |
| 9 | Append `Screen Index` + `Change History` | Không thiếu row |

**Map Screen ID → ảnh:** chỉ dùng `05_Evidence.Locator` (URL) đối chiếu `02_Screen.URL / Route`. ⛔ **Cấm** đoán theo nội dung nhìn thấy trên ảnh — ghi `NO IMAGE` còn hơn chèn nhầm màn.

---

## 4. Quality Gate

```bash
python3 .claude/skills/system-analyst/scripts/verify-basic-design.py \
    "<master.xlsx>" \
    --before "<versions/v<N>_<DDMMYYYY>/basic_design_before.xlsx>" \
    --expect-screens "SC-001,SC-002" \
    --asis \
    --out "gates/v7.md"
```

- 15 check gốc + **check 16** bật bằng `--asis`.
- `--approved-scope` chỉ dùng **sau khi** có approval thật ở Gate G14. Khai mà không có approval = che lỗi.

| # | Check | Mức |
|---|---|---|
| 1 | `Sample` không bị sửa/đổi tên/xoá | FAIL |
| 2 | Mọi working sheet có `Sheet Type = WORKING_SCREEN` | FAIL |
| 3 | Không trùng `Screen ID` | FAIL |
| 4 | Đủ `F1..F5`, không còn placeholder | FAIL |
| 5 | Mỗi working sheet có đúng 1 row `Screen Index` | FAIL |
| 6 | Mọi Message Code trỏ trong `P`/`Q` tồn tại trong catalog | FAIL |
| 7 | `Change History` có row mới | FAIL |
| 8 | Sheet ngoài scope không bị đổi | FAIL · WARN nếu đã khai `--approved-scope` |
| 9 | Khớp Screen Creation Plan | FAIL |
| 10 | Không ảnh → `Screen Index.UI Source` chứa `NO IMAGE` | FAIL |
| 11 | Không còn sheet ví dụ của file mẫu | FAIL |
| 12 | `Change ID` dạng `CHG-NNNN`, liên tục | FAIL |
| 13 | Ảnh anchor cột `A`, ≤ 840×900 px | FAIL |
| 14 | Data row đủ border, không dùng fill của header | FAIL |
| 15 | Có bảng `ERROR SCENARIOS`, số row khớp catalog | FAIL |
| **16** | **AS-IS: mọi mô tả hành vi có `EV-xxxx` ở cột `R` hoặc ghi `UNKNOWN`** | FAIL — **riêng kit này** |

Self-test gate (chứng minh gate không rỗng):
```bash
python3 .claude/skills/system-analyst/scripts/selftest-basic-design.py "<master.xlsx>" --before "<backup>"
```

---

## 5. Anti-pattern

- ❌ Ghi vào master workbook khi chưa backup
- ❌ Sửa hoặc điền vào sheet `Sample` (template dùng chung của công ty)
- ❌ Thêm cột / thêm sheet / đổi layout template để "cho đủ chỗ"
- ❌ Chèn ảnh đoán theo nội dung nhìn thấy thay vì map bằng URL
- ❌ Hoãn Output 2A vì chưa có ảnh — tạo sheet trước, bổ sung ảnh sau
- ❌ Viết validation vào `P`/`Q` khi bằng chứng duy nhất là ảnh
- ❌ Tự xoá sheet lạ trong master mà chưa qua Gate G14
