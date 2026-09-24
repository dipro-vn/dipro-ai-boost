# Output 1 — High Level System Analysis

> **Mục đích:** người mới vào dự án maintain đọc trong 1 giờ là nắm được hệ thống; và là **baseline để impact-analysis mọi request sửa đổi về sau**.
>
> Thành phẩm: `01_HighLevel_<system>_v<N>.docx` (bản người đọc) + `01_Inventory_<system>_v<N>.xlsx` (artifact nội bộ agent — xem `inventory-spec.md`).

---

## 0. Tiêu chí — khi nào Output 1 được coi là ĐẠT

| Nhóm | Tiêu chí | Kiểm bằng |
|---|---|---|
| **A. Điều kiện vào** | Đã qua Discovery Brief · đã có confirm của user · đã khai `g2_crawl_mode` | §1 |
| **B. Nội dung** | Mọi chức năng quan sát được đều có mặt · mọi `Confirmed` có evidence · mọi thứ chưa chắc có Open Question · mọi route trong code đã được đối chiếu | Gate V1 · V2 |
| **C. Trình bày** | docx đủ 4 chương + 2 phụ lục · không còn placeholder · số dòng docx = số dòng xlsx · PNG chèn đúng khổ | Gate V3 · V5 |
| **D. Cái KHÔNG được làm** | Không sửa hệ thống · không thao tác ghi ngoài quyền G2 · không bịa bảng DB · không để ô trống | Gate V2 check 11 · V3 check 11 · V4 |

---

## 1. Quy trình recon (Bước 3)

### 1.1 Website
```bash
node .claude/skills/system-analyst/scripts/crawl-site.js \
    --url "<URL>" --out "<OUT>" \
    --mode read-only \
    --max-urls 200 --max-minutes 30 \
    --role "<role>" --storage-state "<auth.json>" \
    --forbid "<forbidden_zones>"
```
Sinh ra `recon/crawl/{urls.txt,pages.json,console.json,network.json,blocked.json,evidence.csv}`.

- `evidence.csv` dán thẳng vào sheet `05_Evidence` — **không gõ tay**.
- `blocked.json` là bằng chứng cho Gate G9: mỗi thao tác bị chặn → 1 Open Question.
- **Nhiều site** → chạy nhiều lần, mỗi site 1 `--out` con; `Screen ID` không được trùng giữa các site (dùng tiền tố module).

### 1.2 Source code
```bash
python3 .claude/skills/system-analyst/scripts/scan-repo.py "<repo>" --out "<OUT>/recon"
```
Sinh `recon/code/{routes.txt,routes.json,jobs.json,integrations.json,stack.json}`.

⚠️ Kết quả là **gợi ý**. Route chưa quan sát trên UI → `Status = To verify`, **không** `Confirmed`.

### 1.3 Database
```bash
python3 .claude/skills/system-analyst/scripts/read-schema.py --dump "<schema.sql>" --out "<OUT>/recon"
```
Sinh `recon/db/{tables.csv,columns.csv,schema.json,integrity-checks.sql}`.

Mọi cột `Purpose` / `Meaning` / `Related Function IDs` đều ra `UNKNOWN` — **đúng như thiết kế**. Điền chúng bằng evidence `code-ref`, không đoán từ tên cột.

---

## 2. Reconcile — đối chiếu 3 nguồn (Bước 5)

Đây là bước quyết định chất lượng tài liệu. Lập bảng đối chiếu trước khi ghi vào inventory:

| Chức năng ứng viên | Thấy trên UI | Thấy trong code | Thấy trong tài liệu | → Status |
|---|---|---|---|---|
| Đăng nhập | ✅ EV-0001 | ✅ EV-0003 | ✅ | `Confirmed` |
| Xoá tài khoản | ❌ (G2 chặn) | ✅ EV-0044 | — | `To verify` + Q |
| Xuất báo cáo | ❌ | ✅ (dead code?) | ✅ | `CONFLICT` + Q |
| Gửi mail nhắc hạn | ❌ | ✅ cron EV-0051 | — | `Inferred` + Q |

**Quy tắc gộp module:** gộp theo **domain nghiệp vụ**, không theo folder code. `src/controllers/` không phải là một module nghiệp vụ.

**Chức năng không có màn hình** (batch/cron/webhook) → `Screen IDs = SYSTEM — no screen`. Bỏ im lặng bị tính là thiếu coverage.

---

## 3. Flow tổng quan (Bước 6)

Viết `flow/flow.json` — **mọi node phải trỏ về `F-xxx` / `SC-xxx` / `table:<tên bảng>` có thật**:

```bash
python3 .claude/skills/system-analyst/scripts/render-flow.py flow/flow.json --out flow/flow.png
python3 .claude/skills/system-analyst/scripts/verify-flow-png.py flow/flow.json \
    --inventory "<inv.xlsx>" --png flow/flow.png
```

Node `kind = actor` hoặc `external` được phép không có `ref`. Mọi kind khác không có `ref` → FAIL.

---

## 4. Render docx (Bước 7)

```bash
python3 .claude/skills/system-analyst/scripts/render-highlevel-docx.py \
    --inventory "<inv.xlsx>" --narrative narrative.json \
    --flow flow/flow.json --png flow/flow.png \
    --out "01_HighLevel_<system>_v<N>.docx"
```

**Phân chia trách nhiệm — quan trọng:**

| Phần | Ai viết |
|---|---|
| Mọi **bảng** | Script sinh từ `inventory.xlsx` — máy làm, không sai lệch được |
| Mọi **văn xuôi** | Agent viết trong `narrative.json` — máy không bịa hộ |

`narrative.json` cần: `product_overview` · `system_composition` · `actors` · `scope_sources` · `business_rules` · `db_summary` · `relationships`.

**Business rule:** mỗi dòng phải có `evidence` là EV loại `code-ref`. Rule không có code chứng minh → không đưa vào bảng, đưa xuống Open Questions.

---

## 5. Gate (Bước 7 cuối)

```bash
S=.claude/skills/system-analyst/scripts
python3 $S/verify-evidence.py   "<inv.xlsx>" --root "<OUT>" --code-root "<repo>" --out gates/v1.md
python3 $S/verify-inventory.py  "<inv.xlsx>" --routes recon/code/routes.txt \
                                --crawled recon/crawl/urls.txt --out gates/v2.md
python3 $S/verify-flow-png.py   flow/flow.json --inventory "<inv.xlsx>" --png flow/flow.png --out gates/v5.md
python3 $S/verify-high-level.py "<docx>" --inventory "<inv.xlsx>" --out gates/v3.md
python3 $S/selftest-gates.py > gates/selftest.md
```

`FAIL > 0` → **sửa rồi chạy lại**. Không hạ ngưỡng gate, không tự chấm PASS.
Script không chạy được → Output 1 = `❌ Blocked`.

---

## 6. Chương 3 khi KHÔNG có DB

`g4_db = NONE` → chương 3 chỉ được chứa đúng câu `Database not available.` + 1 đoạn giải thích. **Mọi entity suy ra từ code** đưa xuống Appendix A với `Type = Inference`, **không** dựng bảng giả trong chương 3.

Gate V3 check 5/6 và V2 check 12 bắt trực tiếp lỗi này.
