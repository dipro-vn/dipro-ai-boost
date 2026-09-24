# Inventory Workbook — schema chính xác

> **Artifact nội bộ của agent. KHÔNG phải deliverable cho user, KHÔNG nhắc trong README.**
>
> File: `01_Inventory_<system>_v<N>.xlsx` — sinh cùng lúc với `01_HighLevel_<system>_v<N>.docx`, từ **cùng một nguồn dữ liệu recon**. docx là bản người đọc, file này là bản máy đọc.
>
> Mọi tên sheet / tên cột dưới đây là **hợp đồng cứng** giữa `build-inventory.py`, các gate script, và Output 2A/2B. Đổi tên cột = phải đổi cả 3 nơi.

---

## 0. Vì sao tồn tại

| Mục đích | Cụ thể |
|---|---|
| **Gate script đọc vào** | V1/V2/V4 cần dữ liệu có cấu trúc. Bảng trong docx không có kiểu dữ liệu, không có ID ổn định → không đếm được |
| **Output 2 lấy nguồn ra** | O2A lấy `02_Screen` thay cho `SPEC ## Screens`; O2B lấy `01_Function` + `04_DB_Columns` |
| **Bộ nhớ giữa các lần chạy** | Lần chạy sau đọc version mới nhất để biết đã phủ tới đâu, user đã trả lời gì, câu hỏi nào còn treo |

---

## 1. Bảy sheet

| # | Sheet | Grain | Bắt buộc |
|---|---|---|---|
| 1 | `00_Meta` | 1 file = 1 lần chạy | ✅ |
| 2 | `01_Function` | 1 dòng = 1 chức năng | ✅ |
| 3 | `02_Screen` | 1 dòng = 1 màn hình | ✅ |
| 4 | `03_DB_Tables` | 1 dòng = 1 bảng | ✅ (rỗng + 1 dòng khai báo nếu `G4 = không có DB`) |
| 5 | `04_DB_Columns` | 1 dòng = 1 cột | ✅ (như trên) |
| 6 | `05_Evidence` | 1 dòng = 1 bằng chứng | ✅ |
| 7 | `06_OpenQuestions` | 1 dòng = 1 câu hỏi treo | ✅ |

Header luôn ở **row 1**. Data từ **row 2**. Không merge cell, không sheet ẩn, không công thức.

---

## 2. `00_Meta` — 2 cột `Key` · `Value`

| Key | Ví dụ | Ghi chú |
|---|---|---|
| `system_name` | `EC Portal` | |
| `customer` | `ABC Corp` | |
| `doc_version` | `v2` | khớp tên file |
| `generated_date` | `2026-09-23` | |
| `previous_version` | `v1` hoặc `—` | version đã đọc để resume |
| `run_mode` | `FULL` · `DELTA` · `READ_ONLY_REVIEW` | kết quả Gate G-R |
| `g0_scope` | `Toàn hệ thống` | |
| `g1_websites` | `https://stg.abc.jp` | nhiều site ngăn bằng `;` |
| `g2_crawl_mode` | `READ_ONLY` · `SUBMIT_STAGING` · `SUBMIT_PROD` · `NO_CRAWL` | **mặc định `READ_ONLY`** |
| `g3_accounts` | `admin, user — thiếu role CS` | |
| `g4_db` | `DUMP` · `READONLY_CONN` · `NONE` | `NONE` → chương 3 docx chỉ 1 dòng khai báo |
| `g5_source` | `FULL_REPO` · `PARTIAL` · `NONE` | |
| `g6_detail` | `EXECUTIVE` · `STANDARD` · `DETAILED` | |
| `g7_lang` | `VN` · `JP` · `EN` · `VN+JP` | |
| `g7_audience` | `Nội bộ` · `BrSE` · `Khách hàng` | |
| `env_observed` | `Chrome 129 · 2026-09-23 14:00–15:20` | |
| `crawl_budget_used` | `137/200 URL · 22 phút` | |
| `forbidden_zones` | `/admin/batch/*; nút 削除` | từ Gate G9b |

**Gate V3 đọc sheet này** để biết chương nào **được phép** trống. `g4_db = NONE` mà chương 3 docx có nội dung bảng → FAIL.

---

## 3. `01_Function`

| Cột | Enum / định dạng | Bắt buộc |
|---|---|---|
| `Function ID` | `F-001` — liên tục, không trùng | ✅ |
| `Module` | theo **domain nghiệp vụ**, không theo folder code | ✅ |
| `Function` | động từ + tân ngữ | ✅ |
| `Primary Actor` | lấy từ `g3_accounts` / Actor list | ✅ |
| `Description` | 1–3 câu, mô tả **cái quan sát được** | ✅ |
| `Entry / Trigger` | URL · menu path · cron expr · webhook | ✅ |
| `Screen IDs` | `SC-014,SC-015` hoặc `SYSTEM — no screen` | ✅ |
| `Related Tables` | `orders,order_items` hoặc `—` | ⬜ |
| `Evidence` | `EV-0031;EV-0032` | ✅ khi `Status = Confirmed` |
| `Source` | `UI` · `Code` · `DB` · `Doc` (nối bằng `+`) | ✅ |
| `Status` | `Confirmed` · `To verify` · `Inferred` · `CONFLICT` | ✅ |
| `Open Q` | `Q-003` hoặc `—` | ✅ khi Status ≠ `Confirmed` |
| `Note` | `Carried from v1` khi bê từ version trước | ⬜ |

### Luật gán `Status` — cơ học, không cảm tính

| Điều kiện | Status | Bắt buộc kèm |
|---|---|---|
| Quan sát được trên UI **và** có code tương ứng | `Confirmed` | ≥ 1 EV |
| Chỉ có code, chưa quan sát được trên UI | `To verify` | 1 row `06_OpenQuestions` |
| Chỉ suy từ tên hàm / tên route / tên bảng | `Inferred` | 1 row `06_OpenQuestions` |
| Tài liệu KH nói có, hệ thống không thấy | `CONFLICT` | 1 row `06_OpenQuestions` |

**Chức năng không sinh màn hình** (batch/cron/job) → `Screen IDs = SYSTEM — no screen`. Bỏ im lặng = tính là thiếu coverage.

---

## 4. `02_Screen` — cầu nối sang Basic Design

| Cột | Enum / định dạng | Bắt buộc |
|---|---|---|
| `Screen ID` | `SC-014` | ✅ |
| `URL / Route` | `/orders/:id` | ✅ |
| `Screen Name` | tên **hiển thị thật** trên UI | ✅ |
| `Type` | `List` · `Detail` · `Form` · `Modal` · `Error` · `Other` | ✅ |
| `Actor` | | ✅ |
| `Entry From` | `SC-013` hoặc `—` | ✅ |
| `Function IDs` | `F-011,F-012` | ✅ |
| `Screenshot EV` | `EV-0031` hoặc `NO IMAGE` | ✅ |
| `Item Count` | số item đếm được từ DOM | ✅ |
| `Status` | `Confirmed` · `To verify` · `Inferred` | ✅ |
| `Note` | | ⬜ |

> Output 5 của kit `requirement-to-flow` lấy nguồn từ `SPEC.md ## Screens`. Kit này **không có SPEC** — sheet này thay thế nó. Thiếu sheet này thì O2A không có Screen ID để duplicate, không có URL để điền `D1`, không có ảnh để chèn `A9`.

---

## 5. `03_DB_Tables`

`Table` · `Purpose` · `PK` · `FK` · `Important Columns` · `Est Rows` · `Related Function IDs` · `Evidence` · `Confidence` · `Note`

`Confidence` ∈ `High` · `Medium` · `Low`.

## 6. `04_DB_Columns`

`Table` · `Column` · `Type` · `PK` · `FK` · `Nullable` · `Default` · `Meaning` · `Used By` · `Evidence` · `Confidence`

**Luật `Meaning`:** chỉ được `Confidence = High` khi **có code đọc/ghi cột đó** (`Evidence` phải chứa ≥ 1 EV loại `code-ref`). Tên cột đẹp **không** phải bằng chứng.

**Quan hệ không có FK vật lý** → ghi ở `03_DB_Tables.Note`: `logical FK: orders.user_id → users.id — inferred from EV-0102`. **Không** điền vào cột `FK` như FK thật.

---

## 7. `05_Evidence` — ledger

| Cột | Ví dụ | Bắt buộc |
|---|---|---|
| `EV ID` | `EV-0031` — liên tục, không trùng | ✅ |
| `Type` | `screenshot` · `har` · `console-log` · `code-ref` · `db-query` · `doc-quote` | ✅ |
| `Locator` | `https://stg.abc.jp/orders/88` · `src/order/order.service.ts#L88-L104` · `orders.status` · `仕様書.pdf §3.2 p.12` | ✅ — **phải chính xác tới dòng/trang/cột** |
| `Captured At` | `2026-09-23T14:02+07` | ✅ với `screenshot`/`har`/`console-log` |
| `Actor/Role` | `test_user` · `anonymous` | ✅ với evidence từ website |
| `Artifact` | `evidence/EV-0031.png` — đường dẫn tương đối | ✅ với `screenshot`/`har`/`console-log` |
| `Note` | `màn chi tiết đơn, trạng thái new` | ⬜ |

Chi tiết cách thu thập + quy ước đặt tên file → `evidence-ledger.md`.

---

## 8. `06_OpenQuestions`

`Q ID` (`Q-001`) · `Type` (`Unknown` · `Inference` · `Risk` · `CONFLICT`) · `Item` · `Reason / Evidence` · `Required Action` · `Owner` · `Status` (`Open` · `Answered` · `Closed`) · `Note`

= Appendix A của docx. Gate V2 đối chiếu cơ học: mọi dòng `01_Function` có `Status ≠ Confirmed` **phải** có `Q ID` tương ứng ở đây.

---

## 9. Bug List workbook (O2B) — schema riêng

File `02_BugList_<system>_v<N>.xlsx`, 4 sheet:

| Sheet | Nội dung | Gửi KH? |
|---|---|---|
| `00_Meta` | như trên + `g13_scan_scope`, `g13_recipient` | — |
| `Bugs` | bug đã reproduce được | ✅ |
| `Suspected` | nghi ngờ, chưa reproduce | ❌ nội bộ |
| `Observations` | quan sát cần điều tra (gồm mọi nghi vấn security chưa có PoC) | ❌ nội bộ |

**Cột sheet `Bugs` / `Suspected`:**

`Bug ID` · `Title` · `Screen / Module` · `URL / Route` · `Category` · `Severity` · `Repro Steps` · `Expected` · `Actual` · `Evidence` · `Reproduced` · `Detected By` · `Business Impact` · `Env` · `Pre-existing` · `Report To Customer` · `Status` · `Note`

| Cột | Enum |
|---|---|
| `Category` | `Functional` · `UI/Layout` · `Data` · `Performance` · `Compatibility` · `Security` |
| `Severity` | `S1 Blocker` · `S2 Major` · `S3 Minor` · `S4 Cosmetic` |
| `Reproduced` | `Yes — n/n` · `Intermittent` · `No` |
| `Detected By` | `Playwright` · `Code review` · `DB check` · `Console` |
| `Pre-existing` | `Yes` · `Unknown` |
| `Report To Customer` | `Yes` · `Internal only` |

Ràng buộc gate V8 → `outputs/output-2b-bug-list.md`.
