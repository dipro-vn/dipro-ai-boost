# Automation Test — Playwright E2E Guide

> Hướng dẫn **setup 1 lần** + **chạy hàng ngày** cho E2E automation test của dự án. Agent thực thi việc này là `qc-automation-agent` (xem `.claude/agents/qc-automation-agent.md` để biết chi tiết quy trình 7 bước AI tự làm) — file này là hướng dẫn cho **người** setup môi trường và trigger đúng cách.

## Phân biệt 2 loại test trong pipeline

| Agent | Output | Khi nào chạy | Ai/cái gì thực thi |
|---|---|---|---|
| `qc-agent` | Manual test case `.md` | Bước 2b — sau SPEC | Người đọc, thực hiện tay |
| `qc-automation-agent` (file này) | `.spec.ts` + `execution-report.md` | Sau khi **website DEV đang chạy** + có SPEC.md | Playwright, browser thật (headed mode) |

> Unit test / coverage là trách nhiệm của chính Dev agent trong mỗi task (xem "Unit Tests (BẮT BUỘC)" trong task file) — không còn bước QA riêng trong pipeline.

---

## Bước 1 — Setup repo E2E (chạy 1 lần cho cả dự án)

Kit **không tạo sẵn** repo E2E — tự tạo theo 1 trong 2 cách:

- **Repo riêng, ngang cấp** với `<ten-du-an>-repository/` (khuyến nghị nếu nhiều frontend/mobile) — ví dụ `<ten-du-an>-testing/`
- **Folder `e2e/` ngay trong 1 repo** nếu dự án dùng Cách B (monorepo) ở `README.md`

Sau khi tạo, **khai báo path thật** vào `AGENTS.md` section `<ecosystem>` → dòng "E2E Testing (optional)" — `qc-automation-agent` đọc path này, không tự đoán.

### 1a. Khởi tạo project + cài Playwright

```bash
cd <e2e-repo>
npm init -y
npm install -D @playwright/test dotenv
npx playwright install chromium
```

### 1b. Cấu trúc thư mục bắt buộc

```
<e2e-repo>/
├── playwright.config.ts
├── package.json
├── .env.test               ← KHÔNG commit — thêm vào .gitignore
├── .env.test.example       ← committed, template cho member khác
├── e2e/
│   ├── fixtures/
│   │   └── auth.<role>.setup.ts   ← 1 file setup auth cho mỗi actor cần login (xem Bước 1d)
│   ├── <target-app-1>/            ← đặt tên theo repo frontend/mobile tương ứng, agent tự tạo con feature-name/ bên trong khi chạy
│   ├── <target-app-2>/
│   └── ...
└── reports/                ← gitignored, agent tự sinh khi chạy test — KHÔNG tự tạo tay
    └── <feature>/
        ├── execution-report.md
        └── screenshots/
```

```bash
echo ".env.test" >> .gitignore
echo ".auth/" >> .gitignore
echo "reports/" >> .gitignore
```

### 1c. `playwright.config.ts`

Mỗi `project` ứng với 1 `<target-app>` (1 frontend/mobile-web repo trong AGENTS.md Ecosystem). URL đọc từ `.env.test`, KHÔNG hardcode.

```typescript
import { defineConfig, devices } from '@playwright/test'
import dotenv from 'dotenv'

dotenv.config({ path: '.env.test' })

export default defineConfig({
  testDir: './e2e',
  timeout: 10_000,
  fullyParallel: true,
  reporter: [['line'], ['json', { outputFile: 'reports/last-run.json' }]],
  use: {
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    // 1 project / target-app — thêm dòng tương ứng cho mỗi frontend/mobile-web repo
    {
      name: '<target-app-1>',
      use: { ...devices['Desktop Chrome'], baseURL: process.env.TARGET_APP_1_URL },
      testDir: './e2e/<target-app-1>',
    },
    // Nếu actor cần login → thêm 1 project setup riêng, xem Bước 1d
  ],
})
```

### 1d. `.env.test.example` (copy thành `.env.test`, điền giá trị thật)

```bash
# 1 biến URL cho mỗi target-app — đặt tên theo quy ước <APP>_URL, khớp với playwright.config.ts
TARGET_APP_1_URL=https://dev-app1.example.com
TARGET_APP_2_URL=https://dev-app2.example.com

# Credentials test — KHÔNG commit .env.test thật
ADMIN_EMAIL=qc-test@example.com
ADMIN_PASSWORD=changeme
```

### 1e. Auth fixture (nếu actor cần login trước khi test)

```typescript
// e2e/fixtures/auth.<role>.setup.ts
import { test as setup } from '@playwright/test'

setup('authenticate as <role>', async ({ page }) => {
  await page.goto(process.env.TARGET_APP_1_URL + '/login')
  await page.getByPlaceholder('Email').fill(process.env.ADMIN_EMAIL!)
  await page.getByPlaceholder('Password').fill(process.env.ADMIN_PASSWORD!)
  await page.getByRole('button', { name: /đăng nhập|login/i }).click()
  await page.waitForURL(/dashboard|home/)
  await page.context().storageState({ path: '.auth/<role>.json' })
})
```

`qc-automation-agent` inject state này qua `test.use({ storageState: '.auth/<role>.json' })` trong spec sinh ra — KHÔNG tự login lại mỗi test.

---

## Bước 2 — Chạy automation test

**Điều kiện tiên quyết** (agent tự kiểm tra, dừng nếu thiếu):
1. `.env.test` tồn tại và đã điền URL + credentials thật
2. Website DEV đang chạy (agent curl-probe trước khi test)
3. `SPEC.md` của feature đã có (và có Figma URL trong `## Screens` nếu muốn selector chính xác hơn)

**Trigger:**

```
/qc-automation <feature-path> <figma-url> [testcases]
```

hoặc tự nhiên: **"Hãy là QC Automation, test feature: `<path>`, Figma: `<url>`, app: `<target-app>`, website: `<url>`"**

- `<feature-path>` — ví dụ `<DOCS_ROOT>/features/<feature>`
- `<figma-url>` — Figma node URL trong SPEC.md `## Screens`
- `[testcases]` _(tuỳ chọn)_ — path tới file TC thủ công từ `qc-agent` (ví dụ `<feature-path>/test-cases/tc_*.md`). Có file này → agent map 1:1 theo TC, không tự suy scenario.

Agent tự sinh `.spec.ts` (tối đa 10 TC nếu SPEC-driven, không giới hạn nếu TC-driven), chạy Playwright **headed mode** (browser hiện ra để quan sát), rồi sinh `execution-report.md`.

---

## Bước 3 — Đọc kết quả

```
<e2e-repo>/reports/<feature>/execution-report.md      ← bảng PASS/FAIL/SKIP + lỗi cần xử lý
<e2e-repo>/reports/<feature>/screenshots/              ← screenshot cho từng TC FAIL
```

| Kết quả | Việc tiếp theo |
|---|---|
| ✅ PASS toàn bộ | Sẵn sàng demo / release |
| ❌ Có FAIL | Dev xem screenshot + error trong report, fix rồi yêu cầu agent chạy lại đúng feature đó |
| ⏭ SKIP | Thường do cần data động — ghi nhận, implement sau |

Chạy lại sau khi fix (giữ nguyên feature-path/figma-url, thêm `testcases:` nếu có):

```
"Hãy là QC Automation, test feature: <path>, Figma: <url>, app: <target-app>, website: <url>, testcases: <tc-path>"
```

---

## Troubleshooting

| Vấn đề | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| Agent báo thiếu `.env.test` | Chưa copy từ `.env.test.example` | `cp .env.test.example .env.test` rồi điền giá trị thật |
| Agent báo website không phản hồi | DEV server chưa chạy, hoặc URL sai trong `.env.test` | Start server, curl thử URL trước |
| Selector không tìm thấy element | UI dùng custom component, không render `<label>`/`role` chuẩn | Xem lại Figma text label thật; agent ưu tiên `getByRole` → `getByPlaceholder` → `getByText` → `getByTestId`, KHÔNG dùng CSS class |
| Test 2 fail vì phụ thuộc test 1 | Vi phạm nguyên tắc "mỗi test tự lập" | Báo agent sinh lại spec — không tự sửa tay để né |
| Auth hết hạn giữa chừng | `storageState` cũ | Xoá `.auth/<role>.json`, chạy lại `auth.<role>.setup.ts` |

## Ràng buộc cứng (agent tuân thủ, không cần nhắc)

- Không sửa source code app, không sửa `playwright.config.ts` khi đang chạy test
- Không commit `.env.test` hay `.auth/`
- Không hardcode credentials trong `.spec.ts` — luôn `process.env`
- Không dùng CSS class selector, không `waitForTimeout` cố định

Chi tiết đầy đủ quy trình 7 bước (đọc SPEC/TC → đọc Figma → sinh spec → chạy → report) → `.claude/agents/qc-automation-agent.md`.
