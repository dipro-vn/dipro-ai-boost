# O2 — API Documentation (+ Batch)

> **Yêu cầu:** file xlsx dễ tìm kiếm · liệt kê **toàn bộ API theo group** có trong source · mỗi API mô tả **làm gì · method · request · response** · sheet tổng hợp có **link tới sheet API tương ứng** · có **BATCH** thì gồm luôn. **Không có sơ đồ API (code map)** (feedback 28/10/2026).
>
> Thành phẩm: `02_API/API_Doc_<sys>_ver<N>.xlsx`. Chỉ chạy khi có source (P5).

---

## 1. Nguồn → inventory

| Bước | Lệnh / việc | Kết quả |
|---|---|---|
| 1 | `scan-repo.py <repo> --repo-id REPO-xx --out $I --ev-start … --api-start …` (mỗi repo) | `recon/code/REPO-xx/{api.json, api-seed.csv, batch.json, fe-routes.json, fe-api-calls.csv, fe-screen-files.json, api-roles.csv, table-refs.json, evidence.csv}` — repo FE: thêm `--api-seed <api-seed.csv của repo BE>`; luôn thêm `--sensitive-memory outputs/_project/preflight-memory.json` |
| 2 | Dán `api-seed.csv` → `07_API`, `evidence.csv` → `05_Evidence` (bằng script, không gõ tay ID) | API ở `Status = To verify`, `Summary = Cần xác nhận` |
| 3 | **Đọc handler** của từng API (theo `Handler` locator) → điền `Summary` (1 câu: làm gì), `Auth`, `Related Tables`, và `08_API_Fields` (request: path/query/header/body · response: field + status code) | Mỗi dòng điền được → `Evidence` = EV `code-ref` của đoạn code đó |
| 4 | `fe-api-calls.csv` (đồ thị gọi: màn → trigger / nút → API ID, cột `Confidence` static / inferred) → `Called By Screens`; `api-roles.csv` → bổ sung `Auth` (role + code-ref) | Route FE ↔ `02_Screen`. Cạnh `inferred` → `Status = Inferred` + Open Q. Không gán màn → API bằng import graph |
| 5 | Có code-ref cho handler + Summary đã điền từ code → `Status = Confirmed`. Không đọc được / logic động → giữ `To verify` + Open Q | |

**Luật:**
- `Summary` mô tả **cái code làm**, không phải cái tên hàm gợi ý. Tên `syncOrders` không chứng minh nó đồng bộ gì.
- Field request/response chỉ ghi khi thấy trong code (DTO, validator, serializer, câu `res.json({...})`). Không thấy → 1 dòng "Cần xác nhận — chưa xác định từ code".
- **Không** ghi giá trị mẫu lấy từ dữ liệu thật; ví dụ (nếu cần) dùng bộ dữ liệu mẫu `DATA-PRIVACY.md` §4.
- Batch / cron / queue: `Kind = BATCH/QUEUE`, `Method = CRON/EVENT`, `Path / Schedule` = biểu thức lịch. Batch không có màn → `Called By Screens = —`.
- Endpoint public không auth, lộ key trên FE… → ghi 1 dòng trong `run-log.md` (nội bộ), không thử khai thác.

---

## 2. Render + gate

```bash
python3 $S/build-api-doc.py --inventory $I/inventory.xlsx --system <sys> --version ver<N> \
    --out $V/02_API/API_Doc_<sys>_ver<N>.xlsx
python3 $S/verify-api-doc.py $V/02_API/API_Doc_<sys>_ver<N>.xlsx --inventory $I/inventory.xlsx --out $I/gates/v-api.md
```

Cấu trúc workbook:

| Sheet | Nội dung |
|---|---|
| `00_Index` | Tổng hợp: số API / batch / group / trạng thái + bảng mọi API (ID **có hyperlink** tới block chi tiết) |
| `G_<group>` | 1 sheet / group. Mỗi API 1 block: Summary · Kind · Auth · Handler · Repo · Màn gọi · Bảng DB · Status · Evidence · bảng **Request** · bảng **Response** · link "↑ Index" |
| `Batch` | Mọi batch/queue: lịch chạy · handler · làm gì · bảng DB |

---

## 3. Anti-pattern

- ❌ Đánh `Confirmed` chỉ vì scan thấy route
- ❌ Đoán request/response theo REST convention
- ❌ Bỏ batch vì "không phải API"
- ❌ Ghi giá trị secret/token thấy trong code vào Summary/Note — chỉ ghi **tên** key
