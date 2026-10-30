# inputs/db/ — không dùng nữa (feedback 30/10/2026)

Tool **không yêu cầu** bạn cung cấp file database. DB doc (O3) sinh **duy nhất** từ source code (Prisma schema · TypeORM entity · SQL migration) qua `read-orm-schema.py`.

- Source có ORM / migration → O3 đầy đủ bảng · cột · quan hệ, Evidence `code-ref`.
- Source không có → `db_mode = NONE`, O3 ⬜, O1 chương DB ghi `Database not available.`

Thư mục này giữ để tương thích ngược với các version cũ (ver1 từng xuất qua `read-schema.py`). Dự án mới: để trống.
