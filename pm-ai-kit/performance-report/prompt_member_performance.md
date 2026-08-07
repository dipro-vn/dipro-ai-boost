# Prompt — Member Performance Report từ Backlog

Prompt này dùng trên **Claude Desktop** đã cài **Backlog MCP server**.
Claude sẽ tự fetch issues **qua MCP trên Desktop** (không cần API key trong prompt), xử lý và xuất file Excel 5 sheet tải xuống.

**Yêu cầu môi trường:**
- **Claude Desktop** (bắt buộc) đã bật server MCP `backlog` — kiểm tra bằng cách hỏi "list backlog tools" và thấy các tool `mcp__backlog__get_space`, `get_project`, `get_issues`, `get_users` khả dụng.
- Analysis tool (Python sandbox) — bật để tạo file Excel.

> ⚠️ Không dùng được trên **claude.ai web** vì MCP local chỉ chạy trên Desktop app.

---

## 📥 PHẦN 1 — ĐIỀN THÔNG TIN

> Copy khối dưới, chỉ chỉnh 2 chỗ **REQUIRED** rồi gửi cho Claude. Tất cả phần còn lại AI tự xử.

```yaml
# ===================== INPUT =====================

project_id: <projectId>          # REQUIRED — số nguyên, xem tại URL project trên Backlog

members:                         # REQUIRED — format: name | email | role | allocation_pct
  - Nguyen Van A | anv@example.com | BE       | 100
  - Tran Thi B   | btt@example.com | QC       | 50
  - Le Van C     | cvl@example.com | FE       | 100
  - Pham Thi D   | dpt@example.com | Designer | 25
```

**Ghi chú về `members`:**
- `name`: đúng như tên hiển thị trong Backlog (`assignee.name`)
- `email`: email công ty — dùng làm **primary key** để match với Backlog user (`mcp__backlog__get_users` → field `mailAddress`). Ưu tiên hơn `name` vì tránh trùng tên.
- `role`: BE / FE / QC / Mobile / Designer / DevOps / BrSE / Comtor / PM / INFRA
- `allocation_pct`: 100 = 40h/tuần, 75 = 30h/tuần, 50 = 20h/tuần, 25 = 10h/tuần

**Optional — chỉ thêm nếu cần**

```yaml
excluded_members:                # Người mà bạn không muốn thống kê — format: name | email
  - PM Nguyen   | pmn@example.com
  - BrSE Trần   | trbrse@example.com
```

> Match ưu tiên theo **email** (giống `members`), fallback theo `name` nếu email không khớp. Issue của người trong list này sẽ bị loại khỏi mọi thống kê.

---

## ⚙️ PHẦN 2 — THỰC THI (dán y nguyên phần này cho Claude sau block YAML)

Bạn là data engineer chạy trên **Claude Desktop**. Đọc block YAML `INPUT` ở trên và thực hiện đúng các bước sau. Không hỏi lại nếu thông tin đã đủ. Nếu thiếu thì **hỏi user một lần** với đúng key thiếu.

### ⚡ Ràng buộc bắt buộc về data source

- **CHỈ ĐƯỢC** lấy data Backlog qua **MCP server `backlog` có sẵn trên Claude Desktop** — dùng các tool `mcp__backlog__get_space`, `get_project`, `get_users`, `get_issues`, `get_issue_comments`, v.v.
- **CẤM** các cách sau:
  - ❌ Gọi REST API Backlog trực tiếp (fetch/requests/curl) — kể cả khi user paste URL space.
  - ❌ Chạy script Python (`performance_report.py`) hoặc bất kỳ CLI nào để scrape Backlog.
  - ❌ Hỏi user cung cấp API key / cookie / bearer token — MCP đã có credential rồi.
  - ❌ Dùng WebFetch / browser để crawl trang Backlog.
- **Trước Bước 1**: verify MCP đang bật bằng cách gọi `mcp__backlog__get_space` một phát. Nếu lỗi → dừng ngay, in hướng dẫn ở "Ghi chú xử lý lỗi" cuối tài liệu (không tự fallback sang REST).

### Bước 1 — Áp dụng default cho các field optional

- **`report_period`** — mặc định = **tuần chứa hôm nay** (Mon → Sun):
  - `monday = today - today.weekday() days` (weekday: Mon=0, Sun=6)
  - `sunday = monday + 6 days`
  - Log 1 dòng: `Tuần báo cáo (auto): <monday> → <sunday> (Tuần W##/YYYY)`
  - **User có thể override** bằng cách reply thêm dòng, ví dụ: `report_period: 2026-08-03 to 2026-08-09` hoặc paste block YAML:
    ```yaml
    report_period:
      from_date: 2026-08-03
      to_date:   2026-08-09
    ```
- **`excluded_members`** — mặc định `[]` (không loại ai).

### Bước 2 — Detect space, verify project & fetch issues (qua MCP trên Claude Desktop)

> Tất cả tool `mcp__backlog__*` dưới đây là **MCP server chạy local trên Claude Desktop**. AI **không** cần API key trong prompt — Desktop tự inject credential từ MCP config khi gọi tool.

1. Lấy space bằng `mcp__backlog__get_space` (không cần user điền). Log: `Space: <spaceKey>`.
2. Verify project bằng `mcp__backlog__get_project` với `projectId = INPUT.project_id`. Log: `Project: <name> — key <projectKey> (ID <projectId>)`. Lưu:
   - `project_name` (dùng đặt tên file — xem Bước 6)
   - `project_key` (fallback nếu name lỗi)
   - `space_key` (dùng build `backlogUrl` cho từng issue)
3. **Fetch users của project** bằng `mcp__backlog__get_users` → build map `mailAddress → { id, name }`. Dùng ở Bước 3 để match member theo email.
4. Tính **month range** từ `from_date`: `month_start = 1st of that month`, `month_end = last day`.
5. Fetch **full month** issues bằng `mcp__backlog__get_issues` với params:
   - `projectId[]`: `INPUT.project_id`
   - `dueDateSince`: `<month_start YYYY-MM-DD>`
   - `dueDateUntil`: `<month_end YYYY-MM-DD>`
   - `count`: 100 (phân trang qua `offset` cho đến khi hết)
   - `order`: `dueDate`

### Bước 3 — Resolve backlog_id cho members + XÁC NHẬN mapping

Ưu tiên match theo **email** (primary key, không trùng), fallback theo **name**:

1. Với mỗi member trong `INPUT.members`:
   - **B1 — Match theo email**: tra `email` trong map `mailAddress → {id, name}` (từ `get_users` ở Bước 2). Match → gán `backlog_id`, `backlog_name`.
   - **B2 — Fallback theo name**: nếu email không match (email placeholder / user chưa có trên Backlog), thử match `name` exact hoặc case-insensitive trong tập assignee của issues fetched.
   - **B3 — Không match**: đánh dấu `⚠️ Không tìm thấy`.

2. **Dừng lại, hiển thị bảng mapping cho user và hỏi confirm** trước khi chạy tiếp:

   ```
   📋 Mapping members ↔ Backlog user (kiểm tra giúp mình):

   | Name             | Email             | Backlog ID | Role     | Alloc% | Match by | Status       |
   |------------------|-------------------|------------|----------|--------|----------|--------------|
   | Nguyen Van A     | anv@example.com   | 1234567    | BE       | 100    | email    | ✅ Matched   |
   | Tran Thi B       | btt@example.com   | 2345678    | QC       | 50     | email    | ✅ Matched   |
   | Le Van C         | cvl@example.com   | 3456789    | FE       | 100    | name     | ⚠️ Email không khớp, dùng name |
   | Pham Thi D       | dpt@example.com   | —          | Designer | 25     | —        | ⚠️ Không tìm thấy |

   → Mapping trên đã đúng chưa? (Y = chạy tiếp | N = tôi sửa email/tên/alloc lại)
   ```

3. Nếu user reply `N` → user sửa lại INPUT và gửi lại. Nếu `Y` → sang Bước 4.
4. Member `⚠️ Không tìm thấy` → skip khỏi thống kê (log 1 dòng warning). Không auto-guess.

### Bước 4 — Parse & normalize

Cho mỗi issue lưu record với các field:
- `issueKey`, `summary`, `status.name`, `priority.name`, `issueType.name`
- `assignee.name` (mặc định "Unassigned"), `assignee.id`
- `estimatedHours` (số, mặc định 0), `actualHours` (số, mặc định 0)
- `startDate`, `dueDate`, `created`, `updated` — parse UTC → convert timezone **Asia/Ho_Chi_Minh** rồi drop tz
- `backlogUrl` = `https://<space_key>.backlog.com/view/<issueKey>`
- `month` = `dueDate.strftime("%Y-%m")` (fallback `updated` nếu `dueDate` null)

Cờ tính toán:
- `isBug` = `issueType.name.strip().lower() == "bug"`
- `isDone` = `status.name ∈ {"Resolved", "Closed", "Done", "完了", "解決済み", "処理済み"}`

Filter chung: loại các issue có assignee ∈ `excluded_members`. Cách match:
- Resolve từng entry trong `excluded_members` sang `backlog_id` bằng logic của Bước 3 (email → name).
- Loại issue nếu `assignee.id ∈ excluded_ids` (ưu tiên) hoặc `assignee.name ∈ excluded_names` (fallback khi không resolve được id).

Tạo 2 DataFrame:
- **weekly_df**: issues có `dueDate ∈ [from_date 00:00, to_date 23:59]`
- **monthly_df**: toàn bộ tập full month đã fetch

### Bước 5 — Aggregation

Định nghĩa helper:
- `alloc_pct(name, uid)`:
  - Nếu uid có trong roster (theo backlog_id) → `allocation_pct` tương ứng.
  - Nếu không, match theo name → `allocation_pct`.
  - Mặc định `100`.
- `productivity(actual, estimate)`:
  - Nếu `actual <= 0` → chuỗi rỗng `""`.
  - Ngược lại → `round(estimate / actual * 100, 1)`.
- `effort_label(estimate, alloc_pct)` — chuẩn **40h/tuần** cho 100% allocation:
  - `alloc_h = alloc_pct/100 * 40`. Nếu `alloc_h <= 0` → `""`.
  - `ratio = estimate / alloc_h`.
  - `> 1.0` → `"Quá tải"` | `>= 0.875` → `"Đủ"` | else → `"Còn dư"`.
- `bug_rate(bug_count, estimate)`:
  - Nếu `estimate <= 0` → `""`.
  - Ngược lại → `round(bug_count / estimate * 100, 1)`.

**Groupby `assignee.name` cho weekly_df** → sheet **Dashboard**:
| Member | Role | Allocation (%) | Effort Load | Total Task | Task Done | Task Remain | Total Bug | Bug Done | Bug Remain | Total Estimate (h) | Total Actual (h) | Productivity (%) |
- `Total Task` = count issues
- `Task Done` = count where `isDone`
- `Task Remain` = `max(0, Total - Done)`
- `Total Bug` = count where `isBug`
- `Bug Done` = count where `isBug AND isDone`
- `Bug Remain` = `max(0, Total Bug - Bug Done)`
- `Total Estimate (h)` = sum `estimatedHours` (làm tròn 1 chữ số)
- `Total Actual (h)` = sum `actualHours`
- Sort theo `Member` ASC.

**Groupby `assignee.name` cho monthly_df** → sheet **Monthly_Stats**:
| Tháng | Member | Role | Allocation (%) | Total Task | Task Done | Task Remain | Total Bug | Bug Done | Bug Remain | Total Estimate (h) | Total Actual (h) | Productivity (%) | Bug_Rate (%) |
- Cùng agg như Dashboard, thêm cột `Tháng` = `<YYYY-MM>` và `Bug_Rate (%)`.

**Member_Availability** (chỉ dùng weekly_df, giá trị theo ngày):
| Member | Role | Allocation (%) | Mon MM/DD | Tue MM/DD | Wed MM/DD | Thu MM/DD | Fri MM/DD |
- Các cột ngày là 5 workday (Mon–Fri) trong khoảng `[from_date, to_date]`. Header format: `"Mon 08/03"`.

> **Đơn vị**: `estimatedHours` từ Backlog API đã là **giờ dạng số thập phân** (VD `4` = 4 tiếng, `0.5` = 30 phút). **KHÔNG** nhân/chia thêm bất kỳ hệ số nào (không quy đổi ra %, không chia cho allocation, không đổi qua man-day).

- **Suy luận start/due còn thiếu** cho mỗi issue có `assigneeId`:
  - Chỉ dùng issue có `estimatedHours > 0`.
  - Nếu thiếu `dueDate`: `startDate` (hoặc `from_date` nếu cũng thiếu) → tính `dueDate = start + ceil(estimate/7) workdays`.
  - Nếu thiếu `startDate` nhưng có `dueDate` + `estimate`: `startDate = due - ceil(estimate/7) workdays`.
  - Nếu thiếu cả hai: dùng `updated` làm cả start và due (single-day).

- **Tính effective_duration** (fix bug: task 4h span 10 workday không được ghi 0.4h/day):
  - `actual_span = số workday (Mon–Fri) từ startDate đến dueDate (bao gồm 2 đầu), tối thiểu 1`.
  - `max_useful_days = max(1, ceil(estimate / 7))` — giả định mỗi workday tối đa ~7h focused work cho 1 task.
  - `effective_duration = min(actual_span, max_useful_days)` — **cap để tránh spread quá loãng**.
  - `load_per_day = estimate / effective_duration` (đây là giờ/ngày thực).

- **Rải load lên các ngày**:
  - Chỉ rải `load_per_day` lên **`effective_duration` workday đầu tiên** kể từ `startDate` (không rải đều ra toàn bộ `actual_span`).
  - Với mỗi cột ngày trong tuần: cộng dồn `load_per_day` của tất cả task có ngày đó nằm trong khoảng `[startDate, startDate + effective_duration workday)`.
  - Làm tròn 1 chữ số, format `"X.Xh"`.

- **Ví dụ kiểm chứng** (bắt buộc trùng, nếu sai → công thức đang lệch):
  - Task A: `estimate=4h`, `start=Mon 08/03`, `due=Fri 08/14` (span 10 workday) → `max_useful=1`, `effective=1` → **4.0h vào Mon 08/03**, các ngày khác 0h.
  - Task B: `estimate=16h`, `start=Mon 08/03`, `due=Wed 08/05` (span 3 workday) → `max_useful=3`, `effective=3` → **5.3h/ngày cho Mon+Tue+Wed**.
  - Task C: `estimate=40h`, `start=Mon 08/03`, `due=Fri 08/07` (span 5 workday) → `max_useful=6`, `effective=5` → **8.0h/ngày cho cả 5 ngày**.

- **Sanity check trước khi ghi Excel**: `sum(all cells của member trong tuần) ≈ sum(estimate của các task overlap tuần đó)`. Nếu sai lệch > 5%, log warning và không được ghi ra file.

- Sort theo `Member` ASC.

**Action_Required** (từ weekly_df và monthly_df hợp lại, hoặc chỉ monthly_df):
Chọn các issue KHÔNG done VÀ có assignee, mà thiếu ít nhất 1 trong: `estimatedHours == 0`, `startDate null`, `dueDate null`.
Cột: `issueKey | backlogUrl | summary | assignee | status | priority | category | startDate | dueDate | estimatedHours | actualHours | Loại cảnh báo | updated`
- `Loại cảnh báo` join bằng ` | ` các nhãn: `Thiếu Estimate`, `Thiếu Start Date`, `Thiếu Due Date`.
- Sort theo `assignee`, `Loại cảnh báo`.

**Raw_Data**: dump toàn bộ record đã parse (bỏ các cột phụ như `isBug`, `isDone`, `month`).

### Bước 6 — Tạo file Excel qua analysis tool (Python + openpyxl)

Dùng Python analysis tool, tạo file với các đặc tả:

#### 6.1 Sheet Dashboard
- **Row 1** merged A1:M1: banner nền `#1F4E79`, chữ trắng bold size 12:
  `📊 Báo cáo hiệu suất tuần: DD/MM/YYYY → DD/MM/YYYY (Tuần W##/YYYY)`
- **Row 2**: header (nền `#1F4E79`, chữ trắng bold), freeze `A3`.
- **Row 3+**: data. Alternating row `#EBF3FB` cho row chẵn.
- **Conditional formatting:**
  - `Productivity (%)`: `>100` → xanh `#C6EFCE`/`#276221` bold | `80-100` → vàng `#FFEB9C`/`#9C6500` | `<80` → đỏ `#FFC7CE`/`#9C0006`.
  - `Effort Load`: `"Quá tải"` → đỏ `#FFC7CE`/`#9C0006` | `"Đủ"` → xanh `#C6EFCE`/`#276221` | `"Còn dư"` → vàng `#FFF2CC`/`#9C6500`.

#### 6.2 Sheet Monthly_Stats
- **Row 1**: header trực tiếp (không banner).
- Conditional formatting:
  - `Productivity (%)`: giống Dashboard.
  - `Bug_Rate (%)`: `<10` → xanh | `>=10` → đỏ.

#### 6.3 Sheet Member_Availability
- **Row 1**: header. Freeze `D2` (giữ 3 cột đầu: Member/Role/Allocation).
- Cell các cột ngày tô theo giờ load:
  - `<= 0h`: không tô
  - `0 < load < 4h`: xanh `#6BCB77`
  - `4h <= load <= 7h`: vàng `#FFD93D`
  - `> 7h`: đỏ `#FF6B6B`

#### 6.4 Sheet Action_Required
- **Row 1** merged: banner nền `#FFF2CC` chữ vàng đậm bold:
  `📋 Danh sách backlog cần PM sửa — thiếu Estimate / Start Date / Due Date. Bổ sung để báo cáo chính xác.`
- **Row 2**: header, freeze `A3`.
- Ô rỗng trong `startDate`/`dueDate`/`estimatedHours` (hoặc `= 0`) → nền vàng nhạt `#FFF2CC`.
- Cột `Loại cảnh báo` có value → nền đỏ `#C00000` chữ trắng bold.

#### 6.5 Sheet Raw_Data
- Header row 1, không tô conditional.
- Cột `backlogUrl` chuyển thành hyperlink (display là `issueKey`, click mở URL).

#### 6.6 Bảng Chú thích (Legend) — thêm sang bên phải mỗi sheet
Cách vẽ: bắt đầu ở cột `max_column + 2`, row 1.
- Row 1 legend: title nền `#2E4057` chữ trắng bold `"📖 Chú thích — <SheetName>"`, span 3 cột.
- Row 2 legend: 3 header cells nền `#2E4057` trắng bold: `"Chỉ số"`, `"Công thức / Nguồn gốc"`, `"Cách đọc"`.
- Row 3+: mỗi legend entry là 1 dòng — cột 1 nền `#D9E1F2` chữ `#1F4E79` bold; 2 cột còn lại theo level:
  - `ok` → nền `#E2EFDA`
  - `warn` → nền `#FFF2CC`
  - `bad` → nền `#FCE4D6`
  - `""` → nền `#F2F2F2`
- Column widths: 22 / 30 / 45.

**Nội dung legend từng sheet:**

- **Dashboard:**
  1. `Productivity > 100%` / `Estimate ÷ Actual × 100` / `🟢 Hoàn thành nhanh hơn estimate` / ok
  2. `Productivity 80–100%` / `Estimate ÷ Actual × 100` / `🟡 Làm đúng effort dự kiến` / warn
  3. `Productivity < 80%` / `Estimate ÷ Actual × 100` / `🔴 Tốn nhiều effort hơn estimate` / bad
  4. `Effort Load = Còn dư` / `Estimate < 87.5% × Alloc-hours (100% = 40h/tuần)` / `🟡 Có thể assign thêm` / warn
  5. `Effort Load = Đủ` / `Estimate ≈ 87.5–100% × Alloc-hours` / `🟢 Cân bằng` / ok
  6. `Effort Load = Quá tải` / `Estimate > Alloc-hours` / `🔴 Cần chia bớt task` / bad

- **Monthly_Stats:**
  1–3. Productivity giống Dashboard.
  4. `Bug_Rate < 10%` / `Bug ÷ Estimate × 100` / `🟢 Chất lượng tốt` / ok
  5. `Bug_Rate ≥ 10%` / `Bug ÷ Estimate × 100` / `🔴 Nhiều bug so với effort` / bad

- **Member_Availability:**
  1. `Ô 🟢 Xanh` / `Load < 4h` / `Còn nhiều capacity` / ok
  2. `Ô 🟡 Vàng` / `Load 4h–7h` / `Bận nhưng còn chỗ` / warn
  3. `Ô 🔴 Đỏ` / `Load > 7h` / `Quá tải trong ngày` / bad
  4. `Cách tính load` / `Σ (estimate ÷ duration)` / `duration = workday từ start → due, min 1` / ""

- **Action_Required:**
  1. `Thiếu Estimate` / `estimatedHours = 0` / `🔴 Không tính vào Effort/Availability` / bad
  2. `Thiếu Start Date` / `startDate = null` / `🟡 Không track được điểm bắt đầu` / warn
  3. `Thiếu Due Date` / `dueDate = null` / `🟡 Không có deadline` / warn
  4. `Ô vàng nhạt` / `Ô trống trong Start/Due/Estimate` / `Highlight ô thiếu` / ""

### Bước 7 — Deliverable

1. **Tên file** = `<slug(project_name)>_<fromYYYYMMDD>_<toYYYYMMDD>.xlsx`, trong đó `slug(project_name)`:
   - Lấy `project_name` từ `mcp__backlog__get_project` (đã fetch ở Bước 2, field `name`).
   - Bỏ dấu tiếng Việt, thay khoảng trắng bằng `_`, giữ chữ/số/`_`/`-` (regex `[^\w\-]` → `_`), lowercase, gộp `__` → `_`.
   - Nếu `project_name` trống hoặc lỗi → fallback dùng `project_key.lower()`.

   **Ví dụ:**
   - `"ES kitchen"` → `es_kitchen_20260803_20260809.xlsx`
   - `"Dự Án Alpha"` → `du_an_alpha_20260803_20260809.xlsx`
2. Đưa file cho user tải xuống qua analysis tool (`create_file` hoặc equivalent).
3. Trả tóm tắt ngắn (5–8 dòng):
   - Kỳ báo cáo, số issue tuần, số issue tháng, số member trong Dashboard, số task Action Required.
   - Top 3 member Effort Load = Quá tải (nếu có).
   - Top 3 member Bug_Rate cao nhất tháng (nếu có).

### Ghi chú xử lý lỗi

- Nếu MCP server `backlog` chưa bật trên **Claude Desktop** (tool `mcp__backlog__*` không khả dụng) → dừng, in hướng dẫn: *"Vào Claude Desktop → Settings → Developer → Edit Config → thêm entry `backlog` trong `mcpServers`, restart Desktop rồi thử lại."*
- Nếu `get_issues` trả lỗi 401/403 → credential trong MCP config sai — báo user check API key trong Desktop MCP config (không hỏi user paste key vào chat).
- Nếu `weekly_df` rỗng → vẫn tạo Dashboard header + trống, không crash.
- Nếu `analysis tool` không khả dụng → in cảnh báo và trả CSV thay thế cho từng sheet.
- Không in `api_key`, `mailAddress` hay bất kỳ credential nào ra chat.
