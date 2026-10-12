# inputs/db/ — database (chỉ cấu trúc)

Bỏ **file schema-only** vào đây, ví dụ `schema.sql`.

| DB | Lệnh xuất (chỉ cấu trúc, không dữ liệu) |
|---|---|
| MySQL | `mysqldump --no-data -u <user> -p <db> > schema.sql` |
| PostgreSQL | `pg_dump --schema-only <db> > schema.sql` |

- ⚠️ File có dữ liệu (`INSERT INTO …`) → AI từ chối đọc và yêu cầu xuất lại chỉ cấu trúc.
- AI **không bao giờ** kết nối trực tiếp DB của khách; bạn tự chạy lệnh xuất.
- Không có file → source có migration / ORM model vẫn đủ để AI dựng tài liệu DB (độ tin cậy thấp hơn).
