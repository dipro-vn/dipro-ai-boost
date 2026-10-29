# O8 — Hướng dẫn chạy local và môi trường (md, dev đọc)

> **Yêu cầu (R12 · D7):** dev mới clone repo về chạy được trong ngày đầu. Thành phẩm: `08_Huong_dan_chay_local/DevSetup_<sys>_ver<N>.md`. Chạy khi có source (không có → `⬜ Không chạy — không có source code`). Sinh sau Pha A + inventory (cần batch).

---

## 1. Nội dung (script gom tự động, mỗi dòng có file nguồn)

| Mục | Nguồn |
|---|---|
| 1. Repo và công cụ | `package.json` (engines) · lockfile · composer / requirements / pyproject / Gemfile / go.mod · README (chỉ đường dẫn) |
| 2. Cài đặt và chạy | lệnh cài theo lockfile + **tên** script (`yarn dev`) · target Makefile — không chép thân script |
| 3. Database local | service trong `docker-compose*.yml` (image + port) — không chép `environment:` |
| 4. Cấu hình (chỉ tên key) | `.env.example` / `.env.sample` / `.env.template` — **cấm đọc `.env` thật** (`rules/SECURITY.md`); script tự bỏ qua |
| 5. Môi trường | hậu tố file env mẫu · `docker-compose.<env>.yml` · `environment:` trong workflow |
| 6. Pipeline / deploy | Dockerfile · compose · `.github/workflows/*` · `.gitlab-ci.yml` · `Jenkinsfile` · bitbucket · buildspec · serverless · appspec |
| 7. Lịch batch | `07_API` Kind = BATCH |

Chỗ máy không tìm thấy → "Cần xác nhận — <cần hỏi gì>". Agent được bổ sung tay vào file md **sau khi** build (câu hỏi cho Tech Lead), rồi chạy lại gate.

## 2. Lệnh

```bash
python3 $S/build-devsetup.py --repo REPO-01=<fe> --repo REPO-02=<be> --inventory $I/inventory.xlsx \
    --system <sys> --version ver<N> --out $V/08_Huong_dan_chay_local/DevSetup_<sys>_ver<N>.md
python3 $S/verify-devsetup.py $V/08_Huong_dan_chay_local/DevSetup_<sys>_ver<N>.md --out $I/gates/v-devsetup.md
```

Gate V-DEV chặn: thiếu mục 1–7 · chữ cũ · `detect-pii.js --scan` bắt được PII / credential · có `KEY=giá trị` hoặc `KEY: giá trị` · nguồn mục 4 không phải file mẫu · ô trống.

## 3. Anti-pattern

- ❌ Đọc / chép giá trị từ `.env`, `docker-compose` `environment:`, secret trong CI
- ❌ Đoán lệnh chạy không có trong repo — ghi "Cần xác nhận"
