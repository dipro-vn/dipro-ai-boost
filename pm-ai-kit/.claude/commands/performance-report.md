# run-performance-report

Wizard thiết lập và chạy `performance_report.py`. Kết nối Backlog qua **MCP**. Cấu hình lưu vào `local.json`.

## Nhiệm vụ của bạn

Thực hiện tuần tự các bước sau. Không bỏ qua bước nào, không chạy script khi chưa đủ thông tin.

---

## BƯỚC 0 — Kiểm tra dependencies

```bash
python3 -c "import requests, pandas, openpyxl, numpy" 2>/dev/null && echo "OK" || echo "MISSING"
```

Nếu `MISSING` → `pip3 install requests pandas openpyxl numpy` → thông báo "✅ Dependencies đã sẵn sàng."

---

## BƯỚC 0.5 — Kết nối Backlog qua MCP

Gọi tool `mcp__backlog__get_space` (không cần tham số).

Kết quả trả về `spaceKey` (ví dụ: `<your-space>`) → tự động tính `BACKLOG_BASE_URL`:
```
https://<spaceKey>.backlog.com/api/v2
```

Hiển thị ngắn gọn:
```
🔗 Backlog MCP: <spaceKey> — OK
```

Lưu `backlog_base_url` vào biến để ghi vào `local.json` ở Bước 10.

---

## BƯỚC 1 — Load cấu hình đã lưu (nếu có)

```bash
cat local.json 2>/dev/null || echo "NOT_FOUND"
```

> ⚠️ Không in nội dung API key ra chat — chỉ hiển thị `***` khi tồn tại.

### Nếu `local.json` tồn tại và hợp lệ:

```
💾 Tìm thấy cấu hình đã lưu (local.json):
   🔑 API Key     : ****** (đã lưu)
   🏗️  Project ID  : <projectId>
   📅 Lần chạy cuối: 2026-07-28 → 2026-08-02
   👥 Thành viên  : N người có allocation
   🚫 Loại bỏ    : <danh sách>

▶️  Dùng cấu hình này? (Y = dùng ngay, N = cấu hình lại, E = chỉnh sửa từng phần)
```

- **Y**: nhảy thẳng đến **Bước 7**
- **N**: thực hiện lại từ Bước 2
- **E**: hỏi muốn chỉnh mục nào (API key / members / excluded), chỉ cập nhật mục đó → Bước 7

### Nếu không tồn tại:
> "Chưa có cấu hình lưu. Bắt đầu thiết lập lần đầu..."
> Copy `local.json.example` → `local.json` rồi điền theo các bước tiếp theo.

---

## BƯỚC 2 — Kiểm tra thư mục `data/`

```bash
ls data/member.json data/plan_resource.json data/excludeds.txt 2>/dev/null
mkdir -p data
```

---

## BƯỚC 3 — Project ID (xác nhận qua MCP)

Đọc `project_id` từ `local.json` (nếu có), sau đó gọi `mcp__backlog__get_project` để xác nhận:

```bash
python3 -c "import json; print(json.load(open('local.json')).get('project_id', ''))"
```

Hiển thị kết quả MCP:
```
🏗️  Project: <projectKey> — <projectName> (ID: <projectId>)
```

Hỏi:
> **Project ID có đúng là `<projectId>` không? (Enter = giữ nguyên)**

Nếu user đổi → gọi lại `mcp__backlog__get_project` để xác nhận → cập nhật `local.json["project_id"]`.

---

## BƯỚC 4 — API Key (cho Python script)

> ⚠️ MCP Backlog dùng xác thực riêng — Python script vẫn cần API Key riêng để gọi REST API.
> Script đọc trực tiếp từ `local.json["api_key"]`, không cần patch source.

Kiểm tra `local.json` có `api_key` chưa. Nếu có → dùng luôn, hiển thị `***`, bỏ qua.

Nếu chưa có → hướng dẫn nhập bảo mật qua `!` để key không hiện trong chat:

```
Nhập API Key bằng lệnh sau (key sẽ không hiện ra màn hình):

! python3 -c "
import json, getpass
key = getpass.getpass('Nhap Backlog API Key: ')
try: c = json.load(open('local.json', encoding='utf-8'))
except: c = {}
c['api_key'] = key
open('local.json','w').write(json.dumps(c, ensure_ascii=False, indent=2))
print('OK - da luu vao local.json')
"

(Lấy API Key tại: Backlog → Cài đặt cá nhân → API → Tạo mới)
```

Sau khi user chạy xong → xác nhận "✅ API Key đã lưu."

---

## BƯỚC 5 — Thành viên & allocation (unified — mapping qua email)

Nếu đã có `local.json["members"]` → ghi 2 file (`data/member.json` + `data/plan_resource.json`) từ đó, bỏ qua hỏi.

Nếu chưa có → hỏi user danh sách theo format thống nhất:

> **Nhập danh sách thành viên theo format: `Tên hiển thị | Email | Role | Allocation%`**
> - **Email** là khoá mapping với Backlog (bắt buộc, không trùng)
> - Role phổ biến: `BE`, `FE`, `QC`, `Mobile`, `Designer`, `DevOps`, `BrSE`, `Comtor`, `PM`
> - Allocation: `100%` = 40h/tuần, `75%` = 30h/tuần, `50%` = 20h/tuần

Ví dụ:
```
Nguyen Van A | a@dipro.vn   | BE | 100%
Tran Thi B   | b@dipro.vn   | QC | 100%
Le Van C     | c@dipro.vn   | FE | 50%
```

### Sau khi user nhập, mapping với Backlog qua email:

1. Gọi `mcp__backlog__get_users` để lấy toàn bộ user Backlog (mỗi user có: `id`, `userId`, `name`, `mailAddress`).
2. Với mỗi dòng user nhập, so email (case-insensitive, trim) với `mailAddress` trên Backlog:
   - **Match** → lấy `id` (backlog_id), `userId` (account), `name` (tên Backlog thật). Nếu tên user nhập khác tên Backlog → ưu tiên tên Backlog (vì script dùng `assignee` khớp với tên này).
   - **Không match** → cảnh báo:
     ```
     ⚠️  Không tìm thấy trên Backlog: <email> (Tên hiển thị: <name>)
        → Bỏ qua khỏi mapping. Kiểm tra email hoặc quyền user trên Backlog.
     ```
     Cho user chọn: **S** = skip dòng này, **R** = nhập lại email, **K** = giữ nguyên (backlog_id=0, tên = tên user nhập).

3. Hiển thị bảng tổng hợp trước khi ghi file:
   ```
   ✅ Đã mapping 5/6 thành viên qua email:
      Tên Backlog        | Email          | Backlog ID | Role | Allocation
      Nguyen Van A       | a@dipro.vn     | 12345      | BE   | 100%
      ...
   ⚠️  1 thành viên chưa mapping: c@dipro.vn (giữ lại backlog_id=0)
   ```

### Ghi file:

- `data/member.json`: `{ "<backlog_name>": "<role>", ... }` — dùng tên Backlog thật
- `data/plan_resource.json`: mỗi entry gồm `{backlog_id, full_name, account, email, role, plan}` — `plan` là ratio số thực (100% → 1.0)
- `local.json["members"]`: list gốc user đã nhập + kết quả mapping, dùng cho lần chạy sau:
  ```json
  [
    {"name": "Nguyen Van A", "email": "a@dipro.vn", "role": "BE", "allocation": 1.0,
     "backlog_id": 12345, "account": "nguyenvana"}
  ]
  ```

---

## BƯỚC 6 — `data/excludeds.txt`

Nếu đã có trong `local.json["excluded_members"]` → ghi file từ đó, bỏ qua hỏi.

Nếu chưa có → hỏi:
> **Thành viên cần loại khỏi báo cáo? (Enter = không có)**
> Thường là PM, BrSE, Comtor — những người không track task trực tiếp.
> Nhập **tên Backlog** (khớp với `data/member.json`), mỗi dòng 1 tên.

Tạo file (kể cả trống). Lưu `local.json["excluded_members"]`.

---

## BƯỚC 7 — Khoảng thời gian báo cáo

> **Báo cáo khoảng thời gian nào?**
>
> - Tuần này (mặc định): Enter → thứ Hai đến Chủ nhật của tuần hiện tại
> - Theo tháng         : `2026-07` → `2026-07-01` đến `2026-07-31`
> - Theo khoảng tùy ý : `2026-07-01 to 2026-07-27`

**Tính tuần hiện tại:**
```python
from datetime import date, timedelta
today = date.today()
monday = today - timedelta(days=today.weekday())   # weekday() = 0 là thứ Hai
sunday = monday + timedelta(days=6)
# from_date = monday.isoformat(), to_date = sunday.isoformat()
```

Parse thành `from_date` / `to_date`. Xử lý đúng ngày cuối tháng.

---

## BƯỚC 8 — Tên file output

Script tự sinh tên theo format `{projectKey}_{YYYYMMDD}_{YYYYMMDD}.xlsx` — không cần user nhập.

Ví dụ: `<projectkey>_20260803_20260809.xlsx`.

Nếu user muốn override → có thể truyền qua `--output <tên_file>.xlsx`.

---

## BƯỚC 9 — Lưu `local.json` và xác nhận chạy

Cấu trúc `local.json` sau khi hoàn thiện (dùng `backlog_base_url` đã lấy từ MCP ở Bước 0.5):

```json
{
  "_comment": "File cấu hình local — không commit lên git.",
  "backlog_base_url": "https://<spaceKey>.backlog.com/api/v2",
  "api_key": "<key>",
  "project_id": 0,
  "last_run": {
    "from_date": "2026-07-28",
    "to_date":   "2026-08-03",
    "output_file": "<projectkey>_20260728_20260803.xlsx"
  },
  "members": [
    {
      "name": "Nguyen Van A",
      "email": "a@dipro.vn",
      "role": "BE",
      "allocation": 1.0,
      "backlog_id": 12345,
      "account": "nguyenvana"
    }
  ],
  "excluded_members": [ ]
}
```

> Từ `members`, wizard tự sinh 2 file: `data/member.json` (name → role) và `data/plan_resource.json` (backlog_id + plan + email…).

Thêm `local.json` vào `.gitignore` nếu chưa có:
```bash
grep -q "local.json" .gitignore 2>/dev/null || echo "local.json" >> .gitignore
```

Hiển thị tóm tắt:
```
📋 Sẵn sàng chạy báo cáo:
   📅 Từ ngày  : 2026-07-28 (Thứ Hai)
   📅 Đến ngày : 2026-08-03 (Chủ Nhật)
   📄 Output   : {projectKey}_20260728_20260803.xlsx
   👥 Allocation: N người
   🚫 Loại bỏ  : M người
   💾 Config đã lưu vào local.json

▶️  Chạy ngay? (Y/N)
```

Nếu Y:
```bash
python3 performance_report.py \
  --from-date <from_date> \
  --to-date <to_date>
```

---

## SAU KHI CHẠY

- **Thành công**: thông báo tên file Excel, cập nhật `local.json["last_run"]`.
- **Lỗi 401**: API Key không hợp lệ → hướng dẫn nhập lại qua `! python3 getpass`, xóa `local.json["api_key"]`.
- **Warning `MEMBER_ALLOCATION_BY_ID trống`**: có email không match Backlog → chạy `/performance-report` → **E** → Members để cập nhật lại email.
- **Thiếu key trong local.json**: script sẽ báo `❌ Thiếu 'xxx' trong local.json` và exit — bổ sung theo `local.json.example`.

---

## Cấu trúc output Excel (5 sheet)

Mỗi sheet có **bảng Chú thích** đi kèm giải thích ngưỡng màu tốt / cảnh báo / xấu.

| Sheet | Nội dung |
|---|---|
| **Dashboard** | Tuần này — có 1 dòng header ghi khoảng thời gian báo cáo. Cột: Member \| Role \| Allocation (%) \| Effort Load (Còn dư/Đủ/Quá tải, chuẩn 100% = **40h/tuần**) \| Total/Done/Remain Task \| Total/Done/Remain Bug \| Estimate \| Actual \| Productivity (%) |
| **Monthly_Stats** | Cả tháng — cùng cột như Dashboard nhưng đổi Effort Load thành **Bug_Rate (%)** = Bug/Estimate × 100 |
| **Member_Availability** | Tuần này Mon–Fri — mỗi ô = Σ(estimate/duration) giờ tải trong ngày |
| **Action_Required** | Backlog cần PM sửa (thiếu Estimate / Start / Due) |
| **Raw_Data** | Toàn bộ issues đã fetch, dùng để verify |

**Productivity (%)** = Estimate ÷ Actual × 100
- `>100` 🟢 nhanh hơn | `80–100` 🟡 đúng | `<80` 🔴 tốn effort
