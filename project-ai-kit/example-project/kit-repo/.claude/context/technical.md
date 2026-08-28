# \<PROJECT_NAME\> — Technical Memory

> `techlead-design-agent` và `backend-agent` đọc file này trước khi thiết kế/implement. Khung ban đầu được `/init-kit` điền từ câu trả lời setup (bảng Tech Stack); phần CI/CD và Known Bugs bổ sung dần bởi Tech Lead/Dev khi phát hiện — đây là nơi ghi lại "known bug đã gặp + cách fix" để AI không lặp lại sai lầm cũ.

---

## Tech Stack

_(điền qua `/init-kit` — mặc định kit nếu không đổi)_

| Layer | Technology |
|---|---|
| Backend | NestJS |
| Frontend | React 19 / Vite / Redux Toolkit v2 / TanStack Query v5 |
| Mobile | Flutter / Riverpod |
| Database | PostgreSQL |
| Secrets | AWS Parameter Store |
| Environments | DEV / STG / PROD |

### Integrations

_(điền qua `/init-kit` câu 6 — payment gateway, external API dự án dùng)_

---

## CI/CD

_(để trống — Tech Lead điền khi dự án có pipeline thật: build/test/deploy flow, secrets cần thiết, branch protection...)_

---

## Known Bugs / Gotchas

_(để trống — bổ sung mỗi khi Dev gặp 1 bug non-obvious đáng nhớ, kèm nguyên nhân + fix pattern, để agent không tái phạm. Ví dụ format:)_

```
### <Tên bug ngắn>
- Endpoint/File: <path>
- Nguyên nhân: <root cause>
- Fix: <pattern áp dụng>
```

---

## Doc Structure

Khi tạo DESIGN.md, xem `.claude/context/doc-structure.md` để đặt file đúng vị trí.
</content>
