---
name: Automation Engineer
description: Skill sinh & chạy Playwright automation script từ test-cases.md có sẵn — dùng Playwright MCP để recon DOM thật, sinh Page Object + Test, chạy test với vòng lặp tự sửa lỗi (auto-heal). Dùng sau khi module đã có test-cases.md từ pipeline rbt_manual_testing.
---

# Automation Engineer

## Description

Skill hỗ trợ agent chuyển **manual test case đã có sẵn** (`<DOCS_ROOT>/features/<feature>/test-cases/<module>/test-cases.md`, sinh ra từ pipeline `rbt_manual_testing`) thành **Playwright automation script chạy thật** — dùng Playwright MCP để khảo sát UI thật, lấy locator chính xác, sinh Page Object Model + test, chạy test và tự sửa lỗi khi FAIL.

Được tổ chức thành **6 sections**, tương ứng các bước thực thi của command `/test/gen-automation`.

**Pipeline:**
```
<DOCS_ROOT>/features/<feature>/test-cases/<module>/test-cases.md (đã có, từ /test/gen-tcs) → /test/gen-automation
```

**Nguyên tắc cốt lõi:**
- **Không đoán locator** — mọi locator phải lấy từ DOM thật qua Playwright MCP, verify bằng thao tác thử.
- **Output là code tĩnh, chạy độc lập** — sau khi sinh xong, test chạy bằng `npx playwright test`, không phụ thuộc MCP/agent nữa.
- **Tự sửa lỗi (auto-heal)** — khi test FAIL, agent tự đọc lỗi, tự sửa, chạy lại, tối đa 5 vòng, không hỏi user giữa chừng trừ trường hợp chặn cứng (xem Section 5).
- **1 project Playwright dùng chung** cho toàn bộ kit — tại `automation/` ở root, lớn dần theo từng module được automate.

---

## When to Use

Sử dụng skill này khi:
- Module đã có `test-cases.md` và cần sinh automation script.
- Cần chạy lại / mở rộng automation cho module đã automate 1 phần.

**KHÔNG** sử dụng skill này khi:
- Module chưa có `test-cases.md` → chạy `/test/gen-tcs` trước.
- Cần sinh manual test case → dùng `rbt_manual_testing`.
- Cần test Selenium/Appium/API → ngoài phạm vi skill này (chỉ hỗ trợ Web qua Playwright).

---

# Section 1: Setup & Scaffold

**Input:** `<DOCS_ROOT>/features/<feature>/test-cases/<module>/test-cases.md` (bắt buộc), `plan-tcs.md` (nên có), `.claude/context/specification.md` (tùy).

1. Kiểm tra `automation/package.json` đã tồn tại chưa.

**Đã tồn tại** → bỏ qua scaffold, sang Section 2.

**Chưa tồn tại (lần chạy đầu tiên của cả kit):**

2. Xác định base URL:
   - Đọc `.claude/context/specification.md` nếu có trường URL/domain của ứng dụng.
   - Nếu không có → hỏi user: "Base URL của ứng dụng cần automate là gì?"

3. Tạo cấu trúc thư mục:
   ```
   automation/
     package.json
     playwright.config.ts
     tsconfig.json
     .env.example
     .gitignore
     pages/
     tests/
     utils/test-data.ts
     task.md
   ```

4. Nội dung `package.json`:
   ```json
   {
     "name": "automation",
     "version": "1.0.0",
     "private": true,
     "scripts": {
       "test": "playwright test",
       "test:headed": "playwright test --headed",
       "report": "playwright show-report"
     },
     "devDependencies": {
       "@playwright/test": "^1.48.0",
       "dotenv": "^16.4.5"
     }
   }
   ```

5. Nội dung `playwright.config.ts`:
   ```typescript
   import { defineConfig, devices } from '@playwright/test';
   import * as dotenv from 'dotenv';

   dotenv.config();

   export default defineConfig({
     testDir: './tests',
     fullyParallel: false,
     retries: 0,
     reporter: 'html',
     use: {
       baseURL: process.env.BASE_URL,
       viewport: { width: 1920, height: 1080 },
       screenshot: 'only-on-failure',
       trace: 'retain-on-failure',
     },
     projects: [
       { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
     ],
   });
   ```

6. Nội dung `tsconfig.json`:
   ```json
   {
     "compilerOptions": {
       "target": "ES2021",
       "module": "commonjs",
       "strict": true,
       "esModuleInterop": true,
       "skipLibCheck": true,
       "resolveJsonModule": true
     }
   }
   ```

7. Nội dung `.env.example`:
   ```
   BASE_URL=https://example.com
   # Nếu module cần login, thêm biến credential theo convention: <MODULE>_USERNAME / <MODULE>_PASSWORD
   # Ví dụ: LOGIN_USERNAME=..., LOGIN_PASSWORD=...
   ```
   Tạo `.env` thật (copy từ `.env.example`, điền `BASE_URL` đã xác định ở bước 2) — **không commit `.env`**.

8. Nội dung `.gitignore`:
   ```
   node_modules/
   playwright-report/
   test-results/
   .env
   ```

9. Nội dung `utils/test-data.ts`:
   ```typescript
   export function uniqueValue(prefix: string): string {
     return `${prefix}_${Date.now()}`;
   }

   export function uniqueEmail(prefix: string): string {
     return `${prefix}_${Date.now()}@test.com`;
   }
   ```

10. Chạy `cd automation && npm install && npx playwright install --with-deps chromium`.

11. Cập nhật/tạo `automation/task.md` — checklist tiến độ cho lần chạy hiện tại:
    ```markdown
    # Automation Generation Progress — <feature>/<module>
    - [x] Setup & Scaffold
    - [ ] Chọn phạm vi TC
    - [ ] MCP Recon
    - [ ] Sinh code
    - [ ] Run & Auto-heal
    - [ ] Cleanup & Report
    ```

---

# Section 2: Chọn phạm vi TC

1. Đọc `<DOCS_ROOT>/features/<feature>/test-cases/<module>/test-cases.md`, liệt kê toàn bộ TC (ID, Title, Priority/Risk nếu có).
2. Đọc `<DOCS_ROOT>/features/<feature>/test-cases/<module>/plan-tcs.md` (nếu có) để lấy Risk Level per Screen/Component.
3. Đề xuất phạm vi cho user chọn — **luôn hỏi, đây là checkpoint bắt buộc duy nhất trước khi tự động chạy hết các bước sau:**

   | Chế độ | Khi dùng |
   |---|---|
   | **A. Risk cao nhất (mặc định)** | Tự đề xuất danh sách TC priority P1 / Risk Level cao nhất |
   | **B. Chỉ định ID cụ thể** | User liệt kê TC ID muốn automate |
   | **C. Toàn bộ TC của module** | Automate hết — dùng khi module đã ổn định, cần phủ regression |

4. Hiển thị danh sách TC đã chọn (ID + Title) kèm số lượng, chờ user xác nhận trước khi sang Section 3.
5. Cập nhật `automation/task.md` với bảng TC đang automate:
   ```markdown
   ## Test Cases to Automate — <feature>/<module>
   | TC ID | Title | Screen | Status |
   |---|---|---|---|
   ```

---

# Section 3: MCP Recon (Playwright MCP)

**TUYỆT ĐỐI KHÔNG ĐOÁN LOCATOR** — mọi locator phải lấy từ DOM thực tế.

1. Mở browser qua Playwright MCP, `browser_navigate` tới base URL, `browser_resize` 1920×1080.
2. Với mỗi TC đã chọn, đi qua từng bước:
   - `browser_snapshot` → đọc accessibility tree.
   - Xác định element cần tương tác, chọn locator theo thứ tự ưu tiên:
     `getByRole()` → `getByLabel()` → `getByPlaceholder()` → `getByText()` → `getByTestId()` → CSS selector → XPath (chót).
   - Thực thi thử (`browser_click`/`browser_type`) để verify locator đúng.
   - `browser_snapshot` lại để xác nhận kết quả action đúng như Expected Result trong TC.
3. Ghi bảng Locator Collection:

   | Page | Element | Action | Primary Locator | Fallback Locator | Verified |
   |---|---|---|---|---|---|

4. Xử lý tình huống:

   | Tình huống | Cách xử lý |
   |---|---|
   | Element không tìm thấy | `browser_snapshot` lại, kiểm tra DOM, thử locator khác |
   | Cần đăng nhập trước | Dùng fixture đăng nhập chung nếu đã có, hoặc hỏi credentials |
   | CAPTCHA / 2FA | Đánh dấu TC này SKIP, ghi rõ lý do — không automate |
   | Redirect / SPA chưa load xong | `browser_wait_for` element/text cụ thể trước khi snapshot |

---

# Section 4: Sinh code (Page Object + Test)

1. Với mỗi Screen xuất hiện trong TC đã chọn:
   - Kiểm tra `automation/pages/<feature>/<module>/<Screen>.page.ts` đã tồn tại chưa — nếu có, tái sử dụng, không tạo trùng.
   - Nếu chưa có, tạo mới theo cấu trúc:
     ```typescript
     import { Page, Locator } from '@playwright/test';

     export class <Screen>Page {
       readonly page: Page;
       // khai báo locator ở đây, lấy từ bảng Locator Collection

       constructor(page: Page) {
         this.page = page;
         // khởi tạo locator
       }

       // action methods mô tả hành vi, vd: async login(username: string, password: string)
     }
     ```
   - Method đặt tên theo hành vi người dùng (`login()`, `submitForm()`), không mô tả thao tác DOM (`clickButton()`).
   - Không hard sleep (`waitForTimeout`) — chỉ dùng smart wait có sẵn của Playwright (auto-waiting, `waitFor`).

2. Tạo test tại `automation/tests/<feature>/<module>/<screen>.spec.ts`:
   ```typescript
   import { test, expect } from '@playwright/test';
   import { <Screen>Page } from '../../../pages/<feature>/<module>/<Screen>.page';

   test.describe('<feature> / <module> — <screen>', () => {
     test('<Traceability ID>: <mô tả TC>', async ({ page }) => {
       // Arrange
       const screenPage = new <Screen>Page(page);
       await page.goto('/');

       // Act
       // gọi action methods từ Page Object

       // Assert
       await expect(/* locator */).toBeVisible();
     });
   });
   ```
3. Mỗi test PHẢI có comment liên kết Traceability ID gốc từ `test-cases.md`.
4. Test data unique dùng `utils/test-data.ts`; credentials đọc từ `process.env`, không hardcode. Convention đặt tên biến credential: `<MODULE_NAME_UPPERCASE>_USERNAME` / `<MODULE_NAME_UPPERCASE>_PASSWORD`.
5. Mỗi test độc lập — không phụ thuộc thứ tự chạy hay state của test khác.

---

# Section 5: Run & Auto-heal

1. Chạy: `cd automation && npx playwright test tests/<feature>/<module>/`

2. **Nếu PASS:**
   - Chạy lại để xác nhận ổn định: `npx playwright test tests/<feature>/<module>/ --repeat-each=2`
   - Cập nhật `task.md`: TC status → ✅ PASS.

3. **Nếu FAIL → vòng lặp Auto-heal (tối đa 5 vòng):**

   ```
   VÒNG N (N ≤ 5):
     1. Đọc error output / trace.
     2. Phân loại lỗi:
        | Lỗi | Hành động |
        |---|---|
        | Locator not found | Mở lại Playwright MCP → browser_snapshot → xác nhận/thay locator |
        | Timeout | Thêm wait condition cụ thể (không tăng timeout mù quáng) |
        | Assertion fail | Đối chiếu Expected Result trong TC gốc — nếu app đúng, TC sai → hỏi user (business logic mâu thuẫn) |
        | Test data conflict | Sinh lại data qua uniqueValue()/uniqueEmail() |
        | Compile/import error | Sửa import, kiểm tra tên class/method |
     3. Sửa code.
     4. Chạy lại bước 1.
     5. Ghi vào task.md: "Vòng N: <mô tả fix> → PASS/FAIL"
   ```

4. **CẤM hỏi user trong lúc auto-heal.** Chỉ dừng và hỏi khi:
   - Business logic mâu thuẫn (TC nói A, app hiển thị B — không rõ đâu đúng).
   - Gặp CAPTCHA/2FA hoặc app không truy cập được.
   - Đã hết 5 vòng mà vẫn FAIL.

---

# Section 6: Cleanup & Report

1. Cleanup bắt buộc trước khi bàn giao:
   - [ ] Xóa `console.log()` debug.
   - [ ] Xóa locator không dùng.
   - [ ] Xóa code comment thừa / commented-out code.
   - [ ] Không còn `waitForTimeout()`.
   - [ ] Không hardcode credentials/test data.

2. Cập nhật `automation/task.md` với kết quả cuối:
   ```markdown
   ## Kết quả — <feature>/<module>
   | TC ID | Title | Status | Stability | Ghi chú |
   |---|---|---|---|---|

   ## Files Created/Modified
   ```

3. Báo cáo cho user:
   - Tổng X TC PASS / Y FAIL / Z SKIP.
   - Danh sách file đã tạo/sửa.
   - Bảng Locator Collection (reference).
   - Known issues / limitations.

---

## Output

- `automation/` project (scaffold nếu lần đầu, hoặc mở rộng nếu đã có).
- Page Object classes tại `automation/pages/<feature>/<module>/` — locator verified từ DOM thật.
- Test classes tại `automation/tests/<feature>/<module>/` — chạy PASS, ổn định 2/2.
- `automation/task.md` — checklist + kết quả.
- Báo cáo PASS/FAIL/SKIP + bảng Locator Collection.
