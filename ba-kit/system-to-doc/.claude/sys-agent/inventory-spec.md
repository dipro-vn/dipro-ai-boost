# Inventory Workbook — schema chính xác

> **Artifact nội bộ của agent. KHÔNG phải deliverable cho user, KHÔNG nhắc trong README.**
>
> File: `outputs/ver<N>_<DDMMYY>_<slug>/_internal/inventory.xlsx`. Mọi bảng trong O1–O7 sinh từ file này; Luồng 2 đọc nó làm baseline.
>
> Tên sheet / cột là **hợp đồng cứng**, định nghĩa duy nhất ở `.claude/skills/system-analyst/scripts/inv_schema.py`. Đổi cột → sửa `inv_schema.py` + file này.

---

## 0. Vì sao tồn tại

| Mục đích | Cụ thể |
|---|---|
| **Gate script đọc vào** | V1/V2/V4 cần dữ liệu có cấu trúc. Bảng trong docx không có kiểu dữ liệu, không có ID ổn định → không đếm được |
| **Output lấy nguồn ra** | O1 ← `02_Screen` · O2 ← `07_API` + `08_API_Fields` · O3 ← `03/04` · O6 ← mọi sheet · O7 ← `01/02` |
| **Bộ nhớ giữa các lần chạy** | Luồng 1 DELTA đọc để biết đã phủ tới đâu; **Luồng 2 đọc để tra baseline khi phân tích CR** |

---

## 1. Mười hai sheet

| # | Sheet | Grain | Ghi chú |
|---|---|---|---|
| 1 | `00_Meta` | 1 file = 1 lần chạy | câu trả lời preflight |
| 2 | `01_Function` | 1 dòng = 1 chức năng | |
| 3 | `02_Screen` | 1 dòng = 1 màn hình | → O1 |
| 4 | `03_DB_Tables` | 1 dòng = 1 bảng | rỗng nếu `db_mode = NONE` |
| 5 | `04_DB_Columns` | 1 dòng = 1 cột | như trên |
| 6 | `05_Evidence` | 1 dòng = 1 bằng chứng | |
| 7 | `06_OpenQuestions` | 1 dòng = 1 câu hỏi treo | |
| 8 | `07_API` | 1 dòng = 1 API / batch / webhook / queue | → O2 |
| 9 | `08_API_Fields` | 1 dòng = 1 field request/response | → O2 |
| 10 | `09_Integration` | 1 dòng = 1 liên kết bên thứ 3 | |
| 11 | `10_Site` | 1 dòng = 1 website | |
| 12 | `11_Repo` | 1 dòng = 1 repo source | |

Header luôn ở **row 1**. Data từ **row 2**. Không merge cell, không sheet ẩn, không công thức.

---

## 2. `00_Meta` — 2 cột `Key` · `Value`

| Key | Ví dụ | Từ |
|---|---|---|
| `system_name` · `customer` | `EC Portal` · `ABC Corp` | P0 |
| `version_label` · `version_folder` · `version_type` | `ver1` · `ver1_011026_baseline` · `BASELINE` | `version-tool.py` |
| `generated_date` · `previous_version` · `run_mode` | `2026-10-01` · `—` · `FULL`/`DELTA`/`READ_ONLY_REVIEW` | G-R |
| `scope` | `Toàn hệ thống` | P0 |
| `websites` | `WEB-01=https://stg.abc.jp;WEB-02=https://stg-admin.abc.jp` | P1 |
| `accounts` · `access_approved_by` | `WEB-01: admin,user (test)` · `PM phía KH` — **chỉ role, không tên người, không mật khẩu** | P2 |
| `crawl_mode` | `READ_ONLY` · `SUBMIT_STAGING` · `SUBMIT_PROD` · `NO_CRAWL` | P3 (mặc định `READ_ONLY`) |
| `forbidden_zones` | `/admin/batch/*; nút 削除` | P4 |
| `source_repos` | `REPO-01=/src/web(FE→WEB-01);REPO-02=/src/api(BE)` | P5 |
| `db_mode` | `DUMP` · `READONLY_CONN` · `MIGRATION` · `NONE` | P6 |
| `figma_input_url` · `figma_output_url` | link hoặc `—` | P7 · P8 |
| `bug_list` · `bug_recipient` · `bug_scan_scope` | `YES` · `Nội bộ review trước` · `Blackbox` | P9 |
| `lang` · `audience` | `VN` · `Nội bộ` | P10 |
| `sensitive_scan` | `clean` / `stopped: <file> (đã xử lý: …)` | Bước 3 |
| `env_observed` · `crawl_budget_used` | `Chrome · 2026-10-01 14:00–15:20` · `137/200 URL · 22 phút` | recon |

## 3. `01_Function`

| Cột | Enum / định dạng | Bắt buộc |
|---|---|---|
| `Function ID` | `F-001` — liên tục, không trùng | ✅ |
| `Module` | theo **domain nghiệp vụ**, không theo folder code | ✅ |
| `Function` | động từ + tân ngữ | ✅ |
| `Primary Actor` | lấy từ role ở `00_Meta.accounts` / `10_Site.Roles Observed` | ✅ |
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
| `Screen ID` | `SC-014` — duy nhất trên **mọi** site | ✅ |
| `Site` | `WEB-01` — phải có trong `10_Site` | ✅ |
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

> Kit `requirement-to-flow` lấy danh sách màn từ `SPEC.md ## Screens`. Kit này **không có SPEC** — sheet này thay thế nó cho O1 (Basic Design) và O5 (Figma).

---

## 5. `03_DB_Tables`

`Table` · `Purpose` · `PK` · `FK` · `Important Columns` · `Est Rows` · `Related Function IDs` · `Evidence` · `Confidence` · `Note`

`Confidence` ∈ `High` · `Medium` · `Low`.

## 6. `04_DB_Columns`

`Table` · `Column` · `Type` · `PK` · `FK` · `Nullable` · `Default` · `Max Length` · `Format` · `Constraint` · `Meaning` · `Used By` · `Evidence` · `Confidence`

`Max Length` / `Format` / `Constraint` do `read-schema.py` suy từ kiểu (`varchar(255)` → 255 · `decimal(10,2)` → `10,2` · ENUM/UNIQUE/CHECK → Constraint).

**Luật `Meaning`:** chỉ được `Confidence = High` khi **có code đọc/ghi cột đó** (`Evidence` phải chứa ≥ 1 EV loại `code-ref`). Tên cột đẹp **không** phải bằng chứng.

**Quan hệ không có FK vật lý** → ghi ở `03_DB_Tables.Note`: `logical FK: orders.user_id → users.id — inferred from EV-0102`. **Không** điền vào cột `FK` như FK thật.

---

## 7. `05_Evidence` — ledger

| Cột | Ví dụ | Bắt buộc |
|---|---|---|
| `EV ID` | `EV-0031` — liên tục, không trùng | ✅ |
| `Type` | `screenshot` · `har` · `console-log` · `code-ref` · `db-query` · `doc-quote` | ✅ |
| `Locator` | screenshot: URL · code-ref: **`REPO-01:src/order/order.service.ts#L88-L104`** · db-query: `schema:schema.sql#L120` · doc-quote: `仕様書.pdf §3.2 p.12` | ✅ — **chính xác tới dòng/trang**; code-ref bắt buộc tiền tố repo |
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

## 9. `07_API` + `08_API_Fields`

`07_API`: `API ID` (`API-001`) · `Group` · `Kind` (`API`/`BATCH`/`WEBHOOK`/`QUEUE`) · `Method` (`GET`…`DELETE`/`ANY`/`CRON`/`EVENT`) · `Path / Schedule` · `Summary` · `Auth` · `Handler` (code-ref locator) · `Repo` · `Called By Screens` · `Related Tables` · `Evidence` · `Status` (`Confirmed`/`To verify`/`Inferred`) · `Open Q` · `Note`

`08_API_Fields`: `API ID` · `Direction` (`REQUEST`/`RESPONSE`) · `In` (`path`/`query`/`header`/`cookie`/`body`/`status`/`response-body`) · `Field` · `Type` · `Required` · `Format / Constraint` · `Description` · `Evidence`

| Status | Điều kiện |
|---|---|
| `Confirmed` | Có EV `code-ref` tới handler **và** `Summary` viết từ việc đọc code |
| `To verify` | Mới thấy route (giá trị mặc định từ `api-seed.csv`) — kèm Open Q |
| `Inferred` | Suy từ FE gọi tới, không thấy handler — kèm Open Q |

## 10. `09_Integration` · `10_Site` · `11_Repo`

`09_Integration`: `EXT ID` · `Name` · `Kind` (Payment/Email/Storage/…) · `Purpose` · `Direction` (`OUTBOUND`/`INBOUND`/`BOTH`) · `Used By` (F-/API-) · `Config Keys` (**chỉ tên key**, không bao giờ giá trị) · `Evidence` · `Status` · `Note`

`10_Site`: `Site ID` (`WEB-01`) · `Site Name` · `URL` · `Env` · `Roles Observed` · `Crawl Mode` · `FE Repo` · `Screen Count` (= số dòng `02_Screen` của site — gate kiểm) · `Note`

`11_Repo`: `Repo ID` (`REPO-01`) · `Path` (dùng để phân giải code-ref) · `Kind` (`FE`/`BE`/`FULLSTACK`/`BATCH`/`OTHER`) · `Stack` · `For Site` · `Note`

---

## 11. Bug List workbook (O7) — schema riêng

File `07_BugList/BugList_<sys>_ver<N>.xlsx`, 4 sheet:

| Sheet | Nội dung | Gửi KH? |
|---|---|---|
| `00_Meta` | như trên (`bug_scan_scope`, `bug_recipient` bắt buộc) | — |
| `Bugs` | bug đã reproduce được | ✅ |
| `Suspected` | nghi ngờ, chưa reproduce | ❌ nội bộ |
| `Observations` | quan sát cần điều tra (gồm mọi nghi vấn security chưa có PoC) | ❌ nội bộ |

**Cột sheet `Bugs` / `Suspected`:**

`Bug ID` · `Title` · `Screen / Module` · `URL / Route` · `Category` · `Severity` · `Repro Steps` · `Expected` · `Actual` · `Evidence` · `Reproduced` · `Detected By` · `Business Impact` · `Env` · `Pre-existing` · `Report To Customer` · `Status` · `Note`

| Cột | Enum |
|---|---|
| `Category` | `Functional` · `UI/Layout` · `Data` · `Performance` · `Compatibility` · `Security` |
| `Severity` | `High` · `Medium` (Low không ghi) |
| `Reproduced` | `Yes — n/n` · `Intermittent` · `No` |
| `Detected By` | `Playwright` · `Code review` · `DB check` · `Console` |
| `Pre-existing` | `Yes` · `Unknown` |
| `Report To Customer` | `Yes` · `Internal only` |

Ràng buộc gate V8 → `outputs/o7-bug-list.md`.
