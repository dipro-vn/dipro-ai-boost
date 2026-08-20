# Prompt — Member Performance Report từ Backlog

Prompt này **giả định Backlog MCP (nulab/backlog-mcp-server) và Google Drive MCP đều đã connect và sẵn sàng dùng**. Không cần API key trong prompt — MCP tự inject credential.

Claude sẽ fetch issues qua MCP, xử lý và xuất file Excel 5 sheet, upload thẳng lên Google Drive.

**MCP server được dùng cho Backlog:**
- Repo: <https://github.com/nulab/backlog-mcp-server> — MCP server chính thức của Nulab cho Backlog.
- Cài đặt qua Claude Desktop (`claude_desktop_config.json` → `mcpServers.backlog`). Sau khi restart Claude Desktop, các tool `mcp__backlog__*` sẽ xuất hiện.

**Tool bắt buộc phải khả dụng (assume đã connected):**
- **Backlog MCP (nulab)** — các tool tối thiểu cần dùng: `mcp__backlog__get_myself`, `mcp__backlog__get_space`, `mcp__backlog__get_project`, `mcp__backlog__get_users`, `mcp__backlog__get_issues`, `mcp__backlog__get_issue_comments`.
- **Google Drive MCP** — tool tạo file trong folder (thường là `create_file` hoặc `upload_file`) với quyền write vào folder đích ở Bước 8.
- **Analysis tool** (Python sandbox) — để tạo file Excel.

### 🔎 Pre-check — Verify Backlog MCP đã connect (chạy 1 lần trước Bước 1)

Trước khi bắt đầu Bước 1, chạy đúng **1 tool call** để xác nhận MCP nulab đã connect:

1. Gọi `mcp__backlog__get_myself` (không tham số).
   - ✅ Trả về object có `id` + `name` + `mailAddress` → MCP connected OK. Log 1 dòng: `Backlog MCP OK — logged in as <name> (<mailAddress>)` (che email nếu cần theo POLICIES).
   - ❌ Tool không tồn tại trong danh sách tool khả dụng → dừng, in hướng dẫn:
     > *"Backlog MCP (nulab/backlog-mcp-server) chưa connected. Trên Claude Desktop: mở `~/Library/Application Support/Claude/claude_desktop_config.json`, thêm entry `backlog` trong `mcpServers` theo hướng dẫn tại <https://github.com/nulab/backlog-mcp-server>, restart Claude Desktop. Sau đó gõ lại `/performance-report`."*
   - ❌ Tool tồn tại nhưng call trả 401/403/authorization error → credential trong MCP config sai. Báo user check `BACKLOG_API_KEY` + `BACKLOG_BASE_URL` trong config (KHÔNG hỏi user paste key vào chat).
2. Không được gọi `list_tools` hay pre-check thêm bất cứ tool nào khác — nếu `get_myself` OK thì assume các tool `mcp__backlog__*` còn lại cũng dùng được.

> Prompt environment-agnostic: chạy được trên **Claude Desktop**, **claude.ai web**, và **scheduled task cloud** miễn là 3 tool trên đều connect. Nếu môi trường thiếu tool → dừng ở Bước tương ứng, in hướng dẫn user re-authorize connector (không tự fallback REST API, không hỏi user paste API key).

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

Bạn là data engineer. Đọc block YAML `INPUT` ở trên và thực hiện đúng các bước sau. Không hỏi lại nếu thông tin đã đủ. Nếu thiếu thì **hỏi user một lần** với đúng key thiếu.

### ⚡ Ràng buộc bắt buộc về data source

- **Đã pre-check ở phần đầu tài liệu** (chỉ chạy `mcp__backlog__get_myself` đúng 1 lần). Nếu pre-check pass → gọi thẳng `mcp__backlog__get_space` / `get_project` / `get_users` / `get_issues` / `get_issue_comments` từ Bước 2, KHÔNG pre-check lại, KHÔNG list tools. Nếu tool call trả lỗi giữa chừng → xử lý theo "Ghi chú xử lý lỗi" cuối tài liệu.
- **CHỈ ĐƯỢC** lấy data Backlog qua các tool `mcp__backlog__*` của **nulab/backlog-mcp-server**.
- **CẤM** các cách sau:
  - ❌ Gọi REST API Backlog trực tiếp (fetch/requests/curl) — kể cả khi user paste URL space.
  - ❌ Chạy script Python (`performance_report.py`) hoặc bất kỳ CLI nào để scrape Backlog.
  - ❌ Hỏi user cung cấp API key / cookie / bearer token — MCP đã có credential rồi.
  - ❌ Dùng WebFetch / browser để crawl trang Backlog.

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

### Bước 2 — Detect space, verify project & fetch issues (qua Backlog MCP)

> Tất cả tool `mcp__backlog__*` dưới đây là **Backlog MCP đã connected**. AI **không** cần API key trong prompt — MCP tự inject credential khi gọi tool.

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
- `isOverdue` = `dueDate != null AND dueDate.date() < today (Asia/Ho_Chi_Minh) AND NOT isDone` — task đã quá hạn nhưng **chưa xong** (outstanding risk). Task không có `dueDate` → `isOverdue = False` (không đủ dữ kiện để kết luận trễ; issue này sẽ xuất hiện ở `Action_Required` do thiếu Due Date).
- `resolvedAt` — timestamp task được dev "delivered". Fetch bằng `mcp__backlog__get_issue_comments` (mỗi issue done 1 call, parallel để nhanh), duyệt tất cả `changeLog` entry có `field == "status"` theo thứ tự thời gian, tìm lần **ĐẦU TIÊN** chuyển sang trạng thái ∈ `DONE_STATUSES` **mà sau đó KHÔNG bị bounce ra** (không có transition ra khỏi Done sau lần đó).
  - Ví dụ `Open → In Progress → Resolved (10/8 15:20) → Closed (11/8 11:13)` → `resolvedAt = 10/8 15:20` (không phải 11/8 — vì Closed chỉ là PM verify, dev đã báo xong từ Resolved).
  - Ví dụ reopen `Resolved (5/8) → In Progress (6/8) → Resolved (10/8) → Closed (11/8)` → `resolvedAt = 10/8` (bỏ Resolved 5/8 vì bị bounce; lấy Resolved 10/8 vì stay).
  - Task chưa done → `resolvedAt = null` (không cần fetch).
- `isLateDelivered` = `isDone AND dueDate != null AND resolvedAt != null AND resolvedAt.date() > dueDate.date()` — task **đã đóng nhưng deliver trễ deadline** (historical delivery quality). Bổ sung cho `isOverdue`:
  - `isOverdue` = **forward-looking** — task ĐANG treo, chưa xong.
  - `isLateDelivered` = **backward-looking** — task đã xong nhưng delivery bị trễ.
  - 2 metric **không overlap**: task chỉ có thể thuộc 1 trong 2 (hoặc cả 2 = 0 nếu deliver đúng hạn).

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
| Member | Role | Allocation (%) | Effort Load | Total Task | Task Done | Task Remain | Task Overdue | Task Late Delivered | Total Bug | Bug Done | Bug Remain | Total Estimate (h) | Total Actual (h) | Productivity (%) |
- `Total Task` = count issues
- `Task Done` = count where `isDone`
- `Task Remain` = `max(0, Total - Done)`
- `Task Overdue` = count where `isOverdue` (task chưa done VÀ `dueDate < today`). Bao gồm cả task có `dueDate` rơi ngoài tuần báo cáo (task quá hạn từ tuần trước vẫn tính vào member đang gánh).
- `Task Late Delivered` = count where `isLateDelivered` (task đã done VÀ `resolvedAt.date() > dueDate.date()`). Đo delivery quality **trong tuần đã đóng**.
- `Total Bug` = count where `isBug`
- `Bug Done` = count where `isBug AND isDone`
- `Bug Remain` = `max(0, Total Bug - Bug Done)`
- `Total Estimate (h)` = sum `estimatedHours` (làm tròn 1 chữ số)
- `Total Actual (h)` = sum `actualHours`
- Sort theo `Member` ASC.

**Groupby `assignee.name` cho monthly_df** → sheet **Monthly_Stats**:
| Tháng | Member | Role | Allocation (%) | Total Task | Task Done | Task Remain | Task Overdue | Task Late Delivered | Total Bug | Bug Done | Bug Remain | Total Estimate (h) | Total Actual (h) | Productivity (%) | Bug_Rate (%) |
- Cùng agg như Dashboard, thêm cột `Tháng` = `<YYYY-MM>` và `Bug_Rate (%)`.
- `Task Overdue` ở monthly: count issue trong tháng có `isOverdue = True` tại thời điểm chạy report.
- `Task Late Delivered` ở monthly: count issue trong tháng có `isLateDelivered = True` — cumulative delivery quality của member trong tháng.

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
- **Row 1** merged A1:O1 (15 cột: Member/Role/Alloc/Effort + Total/Done/Remain/Overdue/LateDelivered + Bug/BgDone/BgRem + Est/Act/Prod): banner nền `#1F4E79`, chữ trắng bold size 12:
  `📊 Báo cáo hiệu suất tuần: DD/MM/YYYY → DD/MM/YYYY (Tuần W##/YYYY)`
- **Row 2**: header (nền `#1F4E79`, chữ trắng bold), freeze `A3`.
- **Row 3+**: data. Alternating row `#EBF3FB` cho row chẵn.
- **Conditional formatting:**
  - `Productivity (%)`: `>100` → xanh `#C6EFCE`/`#276221` bold | `80-100` → vàng `#FFEB9C`/`#9C6500` | `<80` → đỏ `#FFC7CE`/`#9C0006`.
  - `Effort Load`: `"Quá tải"` → đỏ `#FFC7CE`/`#9C0006` | `"Đủ"` → xanh `#C6EFCE`/`#276221` | `"Còn dư"` → vàng `#FFF2CC`/`#9C6500`.
  - `Task Overdue`: `>0` → đỏ `#FFC7CE`/`#9C0006` bold | `=0` → xanh nhạt `#E2EFDA`/`#276221`.
  - `Task Late Delivered`: `>0` → đỏ `#FFC7CE`/`#9C0006` bold | `=0` → xanh nhạt `#E2EFDA`/`#276221`.

#### 6.2 Sheet Monthly_Stats
- **Row 1**: header trực tiếp (không banner).
- Conditional formatting:
  - `Productivity (%)`: giống Dashboard.
  - `Bug_Rate (%)`: `<10` → xanh | `>=10` → đỏ.
  - `Task Overdue`: `>0` → đỏ `#FFC7CE`/`#9C0006` bold | `=0` → xanh nhạt `#E2EFDA`/`#276221`.
  - `Task Late Delivered`: `>0` → đỏ `#FFC7CE`/`#9C0006` bold | `=0` → xanh nhạt `#E2EFDA`/`#276221`.

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
  7. `Task Overdue = 0` / `dueDate < today AND NOT isDone` / `🟢 Không có task quá hạn` / ok
  8. `Task Overdue > 0` / `dueDate < today AND NOT isDone` / `🔴 Có task quá hạn — cần review deadline / re-assign` / bad
  9. `Task Late Delivered = 0` / `resolvedAt.date > dueDate.date AND isDone` / `🟢 Task đã đóng đều đúng hoặc trước deadline` / ok
  10. `Task Late Delivered > 0` / `resolvedAt.date > dueDate.date AND isDone` / `🔴 Task đã đóng nhưng deliver trễ (resolvedAt = lần Resolved đầu tiên không bị bounce)` / bad

- **Monthly_Stats:**
  1–3. Productivity giống Dashboard.
  4. `Bug_Rate < 10%` / `Bug ÷ Estimate × 100` / `🟢 Chất lượng tốt` / ok
  5. `Bug_Rate ≥ 10%` / `Bug ÷ Estimate × 100` / `🔴 Nhiều bug so với effort` / bad
  6. `Task Overdue = 0` / `dueDate < today AND NOT isDone` / `🟢 Không có task quá hạn trong tháng` / ok
  7. `Task Overdue > 0` / `dueDate < today AND NOT isDone` / `🔴 Có task quá hạn tồn đọng` / bad
  8. `Task Late Delivered = 0` / `resolvedAt.date > dueDate.date AND isDone` / `🟢 Tháng này task đóng đúng hoặc trước deadline` / ok
  9. `Task Late Delivered > 0` / `resolvedAt.date > dueDate.date AND isDone` / `🔴 Tháng này có task đóng trễ deadline (resolvedAt từ changeLog /comments)` / bad

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

#### 6.7 Chuẩn hóa ZIP để Google Sheets đọc được (BẮT BUỘC)

Sau khi openpyxl save xong file `.xlsx`, chạy thêm 1 lượt **extract + re-zip** trong analysis tool. Nếu bỏ bước này, khi upload lên Drive ở Bước 8 và user chọn "Open with Google Sheets" có thể fail với lỗi:
> `UNSUPPORTED_CONVERSION ... java.util.zip.ZipException: invalid code -- missing end-of-block`

Lý do: parser Java của Google Sheets converter khắt khe hơn với DEFLATE stream do openpyxl/Python zipfile ghi trực tiếp. Extract rồi zip lại "từ đầu" sẽ chuẩn hóa archive (file type đổi từ `Microsoft Excel 2007+` → `Microsoft OOXML`, kích thước gần như giữ nguyên, mọi sheet/hyperlink/format vẫn nguyên vẹn).

```python
import os, zipfile, tempfile

def _normalize_xlsx_for_gsheets(filepath: str) -> None:
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(filepath, "r") as zin:
            zin.extractall(td)
        tmp_out = filepath + ".rezip"
        with zipfile.ZipFile(tmp_out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zout:
            for root, _, files in os.walk(td):
                for f in files:
                    full = os.path.join(root, f)
                    arcname = os.path.relpath(full, td).replace(os.sep, "/")
                    zout.write(full, arcname)
        os.replace(tmp_out, filepath)

_normalize_xlsx_for_gsheets(output_path)
```

Sau khi chạy: verify bằng `zipfile.ZipFile(output_path).testzip() is None` và log 1 dòng `Normalized xlsx ZIP → ready for Google Sheets`. Nếu bước này raise exception → không tiếp tục Bước 8, báo user "Không normalize được file, thử mở bằng Numbers/Excel rồi Save As lại".

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
   - Top 3 member Task Overdue cao nhất tuần (nếu có) — kèm số task quá hạn.
   - Top 3 member Task Late Delivered cao nhất tuần (nếu có) — kèm số task đóng trễ, phân biệt rõ với Overdue (Late Delivered = đã đóng nhưng trễ; Overdue = còn treo).

### Bước 8 — Upload file lên Google Drive (qua Google Drive MCP), convert thành Google Sheet native

Sau khi có file `.xlsx` ở Bước 7, upload lên folder Drive dùng chung và **để Drive tự convert sang Google Sheets native** (mimeType đích `application/vnd.google-apps.spreadsheet`).

**Folder đích:**
```
https://drive.google.com/drive/u/0/folders/1W4xJgjh0D3DyX-Xlf8koCqPSv5jikpLN
```
- `folder_id = 1W4xJgjh0D3DyX-Xlf8koCqPSv5jikpLN` — dùng làm `parent` khi upload.

#### Ràng buộc bắt buộc

- **CHỈ ĐƯỢC** upload bằng **Google Drive MCP đã connected**. Gọi tool upload tương ứng của connector (thường là `create_file` / `upload_file` — tên chính xác tuỳ connector đang dùng).
- **CẤM**:
  - ❌ Chạy code Python / shell / `curl` / `gcloud` / bất kỳ CLI nào để upload.
  - ❌ Dùng Google Drive REST API trực tiếp.
  - ❌ Hỏi user OAuth token / service account key — MCP đã có credential rồi.
  - ❌ Tự tạo folder mới — luôn upload thẳng vào `folder_id` ở trên.

#### Thao tác

1. **Assume Google Drive MCP đã connected.** Gọi thẳng tool upload — không pre-check bằng `list_files`. Nếu tool call fail → xử lý theo "Ghi chú xử lý lỗi".
2. **Upload** nội dung file `.xlsx` ở Bước 7 (base64), **để MCP tự convert sang Google Sheets** — KHÔNG set `disableConversionToGoogleType` (hoặc set `false`):
   - `title` / `name`: `<slug>_<from>_<to>` — **không kèm đuôi `.xlsx`** (file đích là Google Sheet, không phải file nhị phân).
   - `parent` / `folder_id`: `1W4xJgjh0D3DyX-Xlf8koCqPSv5jikpLN`.
   - `contentMimeType` (mime của nội dung đang upload lên, không phải mime đích): `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
   - Kết quả kỳ vọng: object trả về có `mimeType: application/vnd.google-apps.spreadsheet`.
   - **Lưu ý cho user (log 1 dòng cảnh báo)**: convert xlsx → Sheets có thể làm nhạt/lệch nhẹ màu nền tô tay (openpyxl static fill) và merge cell ở banner/legend so với bản `.xlsx` gốc — đây là hạn chế của converter, không phải lỗi data. Nếu cần giữ 100% định dạng gốc, chạy lại và yêu cầu xuất `.xlsx` thay vì Sheet.
3. **Base64 content dài (~20K+ ký tự với file 5 sheet)** — khi gõ base64 vào tool call, **PHẢI** chia nhỏ và tự verify từng đoạn (so khớp byte-by-byte, VD bằng `cmp` trong analysis tool) trước khi ghép thành 1 chuỗi cuối để gọi `create_file`, rồi verify lại `fileSize` trả về khớp với size file cục bộ. Không dùng thẳng 1 lần gõ chuỗi dài mà không verify — dễ gây lỗi transcription (lặp/thiếu đoạn) dẫn tới file lỗi trên Drive.
4. **Nếu đã tồn tại file cùng tên trong folder** → upload thành **version mới** (nếu MCP hỗ trợ `update_file` theo `fileId`), fallback: upload thêm bản mới và log warning `⚠️ Trùng tên, đã upload bản mới`.
5. **Nếu cần xoá bản cũ mà `trash_file` báo lỗi permission** → không retry nhiều lần, giữ nguyên cả 2 bản trên Drive và báo user tự xoá bản thừa.
6. Log kết quả (1 dòng):
   ```
   ☁️  Uploaded (Google Sheet): <fileName> → https://docs.google.com/spreadsheets/d/<fileId>/edit
   ```
7. Nối link Drive vào cuối tóm tắt ở Bước 7 (dòng cuối cùng): `📎 Drive (Google Sheet): <link>`.

### Ghi chú xử lý lỗi

- Nếu tool `mcp__backlog__*` (nulab) không khả dụng → dừng, in: *"Backlog MCP (nulab/backlog-mcp-server) chưa connected. Trên Claude Desktop: mở `~/Library/Application Support/Claude/claude_desktop_config.json`, thêm entry `backlog` trong `mcpServers` theo README <https://github.com/nulab/backlog-mcp-server>, restart Claude Desktop. Trên claude.ai: Settings → Connectors → bật & authorize Backlog connector. Rồi thử lại."*
- Nếu `get_myself` / `get_issues` trả lỗi 401/403 → credential trong MCP config sai — báo user check `BACKLOG_API_KEY` + `BACKLOG_BASE_URL` trong MCP config (không hỏi user paste key vào chat).
- Nếu Google Drive MCP không khả dụng / chưa authorize → dừng ở Bước 8 (không huỷ file Excel), in: *"Google Drive MCP chưa connected. Trên Claude Desktop: Settings → Connectors → bật & authorize Google Drive. Trên claude.ai: Settings → Connectors → tương tự. Rồi bảo mình 'upload lại lên Drive'."* File Excel vẫn giữ để user tải tay hoặc chạy lại upload.
- Nếu upload lỗi quota / permission → in message MCP trả về + link folder đích để user check quyền.
- Nếu `trash_file` (xoá bản cũ khi trùng tên) báo lỗi permission → không retry, giữ nguyên cả bản cũ lẫn bản mới trên Drive, log warning và báo user tự xoá bản thừa.
- Nếu `weekly_df` rỗng → vẫn tạo Dashboard header + trống, không crash.
- Nếu `analysis tool` không khả dụng → in cảnh báo và trả CSV thay thế cho từng sheet (bỏ Bước 8, vì Drive folder này để chứa file `.xlsx` chuẩn).
- Không in `api_key`, `mailAddress`, OAuth token hay bất kỳ credential nào ra chat.
