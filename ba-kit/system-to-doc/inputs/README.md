# inputs/ — nơi bỏ tài liệu đầu vào cho AI

Bỏ file vào đúng folder con. AI **tự tìm** ở đây trước khi hỏi lại bạn đường dẫn.

| Folder | Bỏ gì | Dùng ở | Ví dụ |
|---|---|---|---|
| [`repo/`](repo/) | Source code của hệ thống (mỗi repo 1 folder con) | Luồng 1 — O2 API, O3 DB (migration/ORM), O5 màn hình | `repo/web-fe/` · `repo/api/` |
| [`db/`](db/) | File DB **chỉ cấu trúc** (`.sql`), không có dữ liệu | Luồng 1 — O3 Database | `db/schema.sql` |
| [`cr/`](cr/) | File yêu cầu thay đổi của khách (`.docx` `.pdf` `.xlsx` `.md` ảnh) | Luồng 2 — `/change-request` | `cr/yc-ma-giam-gia.docx` |

- Website **không** bỏ vào đây — chỉ cần URL; tài khoản test điền ở [`../.auth/`](../.auth/).
- Nội dung trong `repo/` `db/` `cr/` **không commit** (đã `.gitignore`).
- Không bỏ dữ liệu thật của khách / `.env` / key. AI quét nhạy cảm trước khi đọc và dừng nếu gặp.
- Copy repo: `cp -r /đường/dẫn/repo inputs/repo/web-fe` (hoặc `git clone <url> inputs/repo/web-fe`). Không muốn copy → trả lời đường dẫn tuyệt đối khi AI hỏi.
