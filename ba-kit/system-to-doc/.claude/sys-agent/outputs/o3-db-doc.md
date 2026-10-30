# O3 — Database Documentation (+ ERD)

> **Yêu cầu:** xlsx dễ tìm kiếm · **tổng quan** toàn bộ bảng · **mối liên hệ** giữa các bảng · mô tả từng bảng: **field · kiểu · format · giới hạn · maxlength · mục đích**.
>
> Thành phẩm: `03_DB/DB_Doc_<sys>_ver<N>.xlsx` + `03_DB/ERD_<sys>_ver<N>.png`. Chạy khi `db_mode` ≠ `NONE` (tool tự quyết dựa trên source code).

---

## 1. Nguồn — DUY NHẤT là source code (feedback 30/10/2026)

Tool **không** hỏi user về DB, **không** nhận dump / kết nối. Mọi thông tin DB đọc từ source:

| `db_mode` | Lấy schema từ | Lệnh |
|---|---|---|
| `MIGRATION` | migration / ORM model trong source (Prisma · TypeORM · SQL migration) | `read-orm-schema.py <repo> --repo-id REPO-xx --out $I --ev-start …` → `recon/db-code/REPO-xx/{tables,columns,evidence,code-schema}.csv` (Evidence = `code-ref`). Sequelize / Knex / Django / Rails: chưa có parser → agent đọc migration, ghi tay, mỗi dòng `code-ref` |
| `NONE` | — | Source không có ORM / migration → `db_mode = NONE`, O3 = ⬜, O1 chương DB ghi `Database not available.` |

Gate: `verify-db-doc.py … --code-schema $I/recon/db-code/REPO-xx/code-schema.csv` — check 10 FAIL khi bảng / cột trong code thiếu ở `03/04`. Carry O3 từ version cũ chỉ khi đã chạy lại `read-orm-schema.py` và check 10 PASS.

⛔ Agent **không** giữ mật khẩu DB, **không** tự kết nối DB, **không** chạy câu SQL nào trên DB của khách, **không** đọc dump file.

---

## 2. Điền nghĩa — chỗ dễ bịa nhất

| Cột | Điền từ | Confidence |
|---|---|---|
| `Type` · `Max Length` · `Format` · `Constraint` · `PK` · `FK` · `Nullable` · `Default` | script đọc từ schema | — (cấu trúc, không cần đoán) |
| `Meaning` (mục đích cột) | code đọc/ghi cột đó (`code-ref`) | `High` |
| | comment trong DB (`COMMENT`) | `Medium` (script tự điền) |
| | chỉ có tên cột | **giữ "Cần xác nhận"** (+ Open Question khi cần) — tên đẹp không phải bằng chứng |
| `Purpose` (mục đích bảng) | API/chức năng dùng bảng (`07_API.Related Tables`, `table-refs.json`) | theo bằng chứng |
| Quan hệ không có FK vật lý | code join 2 bảng | ghi ở `03_DB_Tables.Note`: `logical FK: orders.user_id → users.id — inferred from EV-0102` |

---

## 3. Render + gate

```bash
python3 $S/build-db-doc.py --inventory $I/inventory.xlsx --system <sys> --version ver<N> \
    --out $V/03_DB/DB_Doc_<sys>_ver<N>.xlsx --erd-png $V/03_DB/ERD_<sys>_ver<N>.png
python3 $S/verify-db-doc.py $V/03_DB/DB_Doc_<sys>_ver<N>.xlsx --inventory $I/inventory.xlsx --out $I/gates/v-db.md
```

| Sheet | Nội dung |
|---|---|
| `00_Overview` | Tổng: số bảng / cột / quan hệ · bảng mọi table (tên **có hyperlink** tới sheet chi tiết) · mục đích · PK · FK · bảng tham chiếu tới nó · chức năng liên quan |
| `01_Relationships` | Từ bảng.cột → tới bảng.cột · FK thật / logic suy ra · cardinality · evidence |
| `02_ERD` | Ảnh ERD |
| `T_<table>` | 1 sheet / bảng: Column · Type · Format · Max Length · Nullable · Default · PK · FK · Constraint · Mục đích · Evidence · Confidence |

---

## 4. Anti-pattern

- ❌ Đọc / in dữ liệu dòng của DB khách (kể cả "xem thử 5 dòng")
- ❌ Suy nghĩa cột từ tên rồi ghi `High`
- ❌ Ghi quan hệ logic vào cột `FK` như FK thật
- ❌ `db_mode = NONE` mà vẫn dựng bảng từ trí nhớ / tên route
