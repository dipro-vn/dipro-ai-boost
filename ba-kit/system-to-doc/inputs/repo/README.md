# inputs/repo/ — source code hệ thống

Mỗi repo 1 folder con, đặt tên dễ hiểu:

```
repo/
├── web-fe/     ← frontend website user
├── admin-fe/   ← frontend website admin
├── api/        ← backend
└── batch/      ← batch / job (nếu có)
```

- Bỏ cả repo (có thể kèm `.git`) hoặc chỉ phần `src/` + file cấu hình dependency (`package.json`, `composer.json`, `pom.xml`…).
- **Xoá / không bỏ:** `.env`, key, file dump có dữ liệu thật, `node_modules/`, `vendor/`.
- AI hỏi: *repo FE nào thuộc website nào* (WEB-01 / WEB-02…) — chuẩn bị sẵn câu trả lời.
- Folder này để trống → AI hỏi đường dẫn repo ở nơi khác trên máy.
