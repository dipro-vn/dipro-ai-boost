---
name: Automation Engineer
description: Skill sinh & chạy Playwright automation script từ test-cases.md có sẵn — dùng Playwright MCP để recon DOM thật, sinh Page Object + Test, chạy test với vòng lặp tự sửa lỗi (auto-heal). Dùng sau khi module đã có testing/[module]/test-cases.md từ pipeline rbt_manual_testing.
---

# Automation Engineer

## Description

Skill hỗ trợ agent chuyển **manual test case đã có sẵn** (`testing/[module]/test-cases.md`, sinh ra từ pipeline `rbt_manual_testing`) thành **Playwright automation script chạy thật** — dùng Playwright MCP để khảo sát UI thật, lấy locator chính xác, sinh Page Object Model + test, chạy test và tự sửa lỗi khi FAIL.

Được tổ chức thành **6 sections**, tương ứng các bước thực thi của command `/gen-automation`.

**Pipeline:**
```
testing/[module]/test-cases.md (đã có, từ /gen-tcs) → /gen-automation
```

**Nguyên tắc cốt lõi:**
- **Không đoán locator** — mọi locator phải lấy từ DOM thật qua Playwright MCP, verify bằng thao tác thử.
- **Output là code tĩnh, chạy độc lập** — sau khi sinh xong, test chạy bằng `npx playwright test`, không phụ thuộc MCP/agent nữa.
- **Tự sửa lỗi phía script (auto-heal)** — khi test FAIL do lỗi script (locator, timeout, compile, data), agent tự sửa và chạy lại TC fail, tối đa 2 vòng. **Assertion fail không heal** — đó là nghi bug, giao QC quyết định (xem Section 5).
- **1 project Playwright dùng chung** cho toàn bộ kit — tại `automation/` ở root, lớn dần theo từng module được automate.

---

## When to Use

Sử dụng skill này khi:
- Module đã có `testing/[module]/test-cases.md` và cần sinh automation script.
- Cần chạy lại / mở rộng automation cho module đã automate 1 phần.

**KHÔNG** sử dụng skill này khi:
- Module chưa có `test-cases.md` → chạy `/gen-tcs` trước.
- Cần sinh manual test case → dùng `rbt_manual_testing`.
- Cần test Selenium/Appium/API → ngoài phạm vi skill này (chỉ hỗ trợ Web qua Playwright).

---

# Section 1: Setup & Scaffold

**Input:** `testing/[module]/test-cases.md` (bắt buộc), `testing/[module]/plan-tcs.md` (nên có), `CLAUDE.md` (tùy).

1. Kiểm tra `automation/package.json` đã tồn tại chưa.

**Đã tồn tại** → bỏ qua scaffold, sang Section 2.

**Chưa tồn tại (lần chạy đầu tiên của cả kit):**

2. Xác định base URL:
   - Đọc `CLAUDE.md` nếu có trường URL/domain của ứng dụng.
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
   # Ví dụ: SELFTEST_LOGIN_DEMO_USERNAME=..., SELFTEST_LOGIN_DEMO_PASSWORD=...
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
     return `tester+${prefix}_${Date.now()}@dipro.vn`;
   }
   ```

10. Chạy `cd automation && npm install && npx playwright install --with-deps chromium`.

11. Cập nhật/tạo `automation/task.md` — checklist tiến độ cho lần chạy hiện tại:
    ```markdown
    # Automation Generation Progress — <module>
    - [x] Setup & Scaffold
    - [ ] Chọn phạm vi TC
    - [ ] MCP Recon
    - [ ] Sinh code
    - [ ] Run & Auto-heal
    - [ ] Report
    ```

---

# Section 2: Chọn phạm vi TC

1. Đọc `testing/[module]/test-cases.md`, liệt kê toàn bộ TC (ID, Test Scenario, Traceability ID).
2. Đọc mục `## High Risk & E2E` ở cuối `test-cases.md` (nếu có): Bảng 1 (nhóm TC high risk) và Bảng 2 (luồng E2E cần work trước).
3. Đề xuất phạm vi cho user chọn — **luôn hỏi, đây là checkpoint bắt buộc duy nhất trước khi tự động chạy hết các bước sau:**

   | Chế độ | Khi dùng |
   |---|---|
   | **A. High Risk & E2E (mặc định)** | Tự đề xuất TC thuộc Bảng 2 (E2E) trước, rồi Bảng 1 (nhóm high risk) |
   | **B. Chỉ định ID cụ thể** | User liệt kê TC ID muốn automate |
   | **C. Toàn bộ TC của module** | Automate hết — dùng khi module đã ổn định, cần phủ regression |

4. Hiển thị danh sách TC đã chọn (ID + Test Scenario) kèm số lượng, chờ user xác nhận trước khi sang Section 3.
5. Cập nhật `automation/task.md` với bảng TC đang automate:
   ```markdown
   ## Test Cases to Automate
   | TC ID | Test Scenario | Screen | Status |
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
   - Kiểm tra `automation/pages/<module>/<Screen>.page.ts` đã tồn tại chưa — nếu có, tái sử dụng, không tạo trùng.
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

2. Tạo test tại `automation/tests/<module>/<feature>.spec.ts`:
   ```typescript
   import { test, expect } from '@playwright/test';
   import { <Screen>Page } from '../../pages/<module>/<Screen>.page';

   test.describe('<module> — <feature>', () => {
     test('<TC ID> (<Traceability ID>): <mô tả TC>', async ({ page }) => {
       // Arrange
       const screenPage = new <Screen>Page(page);
       await page.goto('/'); // Điều chỉnh path nếu Screen không nằm ở route gốc (vd: '/login')

       // Act
       // gọi action methods từ Page Object

       // Assert
       await expect(/* locator */).toBeVisible(); // message rõ ràng lý do assert
     });
   });
   ```
3. Mỗi test PHẢI mang **TC ID** (cột `ID`, VD `HRD-004`) trong tên test và có comment liên kết cả hai ID gốc từ `test-cases.md`, dạng `// TC: HRD-004 | Trace: AC-03, Q-HRD-003`. TC ID dùng để map kết quả về `automation-report.md` và `BUG-<TC ID>`; Traceability ID chỉ để trace nguồn (nhiều TC dùng chung một AC).
4. Test data unique dùng `utils/test-data.ts`; credentials đọc từ `process.env`, không hardcode. Convention đặt tên biến credential: `<MODULE_NAME_UPPERCASE>_USERNAME` / `<MODULE_NAME_UPPERCASE>_PASSWORD` (module name viết hoa, ký tự không phải chữ/số thay bằng `_`) — thêm vào `.env` (và document dạng placeholder có comment trong `.env.example`) ngay lần đầu module cần đến.
5. Mỗi test độc lập — không phụ thuộc thứ tự chạy hay state của test khác.

---

# Section 5: Run & Auto-heal

> **Mục đích workflow:** hỗ trợ QC phát hiện lỗi theo TC, không phải bộ regression bàn giao. Vì vậy auto-heal chỉ sửa lỗi **phía script**; assertion fail là tín hiệu nghi bug, không được "sửa cho PASS".

1. Chạy full module: `cd automation && npx playwright test tests/<module>/`

2. **Nếu PASS hết:** cập nhật `task.md`: TC status → ✅ PASS, sang Section 6.

3. **Nếu có FAIL → phân loại từng TC fail:**

   | Lỗi | Nhóm | Hành động |
   |---|---|---|
   | Locator not found | Script | Mở lại Playwright MCP → browser_snapshot → xác nhận/thay locator |
   | Timeout | Script | Thêm wait condition cụ thể (không tăng timeout mù quáng) |
   | Test data conflict | Script | Sinh lại data qua uniqueValue()/uniqueEmail() |
   | Compile/import error | Script | Sửa import, kiểm tra tên class/method |
   | Assertion fail (Actual ≠ Expected của TC) | **Nghi bug** | **KHÔNG sửa assertion/Expected.** Ghi nhận vào nhóm "Nghi bug" (xem Section 6), giữ evidence |
   | CAPTCHA/2FA, app không truy cập được | Không chạy được | Ghi nhận, không heal |

4. **Vòng auto-heal (tối đa 2 vòng, chỉ cho TC nhóm Script):**

   ```
   VÒNG N (N ≤ 2):
     1. Đọc error output / trace của các TC fail nhóm Script.
     2. Sửa code theo bảng trên.
     3. Chạy lại CHỈ TC fail: npx playwright test tests/<module>/ --last-failed
     4. Ghi vào task.md: "Vòng N: <mô tả fix> → PASS/FAIL"
   ```

   - TC nghi bug **không** đưa vào vòng chạy lại.
   - Không chạy full lại để xác nhận và không `--repeat-each` (chỉ chạy khi QC yêu cầu).
   - Hết 2 vòng mà TC vẫn FAIL do lỗi script → chuyển vào nhóm "Không chạy được", kèm nguyên nhân dự đoán.

5. **CẤM hỏi user trong lúc auto-heal.** Chỉ dừng và hỏi khi:
   - Gặp CAPTCHA/2FA hoặc app không truy cập được.
   - Không phân biệt được lỗi script hay nghi bug (ví dụ element có nhưng nội dung khác Expected không rõ lý do).

---

# Section 6: Report

1. Kiểm tra nhanh trước khi giao (script phục vụ QC chạy lại để tái hiện lỗi, không cần dọn như code bàn giao):
   - [ ] Không còn `waitForTimeout()`.
   - [ ] Không hardcode credentials.

2. Cập nhật `automation/task.md` (log nội bộ của agent):
   ```markdown
   ## Kết quả
   | TC ID | Test Scenario | Status | Ghi chú |
   |---|---|---|---|

   ## Files Created/Modified
   ```

3. Sinh `testing/[module]/automation-report.md` — file QC đọc:
   ```markdown
   # Automation Report — [module]

   ## Tóm tắt: X PASS / Y nghi bug / Z không chạy được

   ## Nghi bug
   | Bug ID | TC ID | Tag TC | Expected | Actual | Evidence | Bước tái hiện |
   |---|---|---|---|---|---|---|

   ## Không chạy được
   | TC ID | Lý do |
   |---|---|

   ## PASS
   | TC ID | Script |
   |---|---|
   ```
   - **Bug ID** = `BUG-<TC ID>` (ví dụ TC `HRD-002` → `BUG-HRD-002`). 1 TC nhiều bug → hậu tố `-a`, `-b`. Nhiều TC cùng 1 nguyên nhân → gom 1 dòng, ID theo TC đầu, liệt kê TC còn lại.
   - **Tag TC**: giữ nguyên `[ASSUMED]` / `[UNCONFIRMED]` của TC gốc (nếu có) để QC biết mức tin cậy — Expected có thể sai chứ không phải app sai.
   - **Evidence**: đường dẫn tới screenshot/trace trong `automation/test-results/`, không copy.
   - Cần report chi tiết thành ticket → chạy `/gen-bug-report`.

4. Báo cáo trong chat: tóm tắt 3 nhóm + đường dẫn `automation-report.md` + danh sách file đã tạo/sửa. Không lặp lại toàn bộ bảng.

---

## Output

- `automation/` project (scaffold nếu lần đầu, hoặc mở rộng nếu đã có).
- Page Object classes — locator verified từ DOM thật.
- Test classes — chạy lại được bằng `npx playwright test`.
- `testing/[module]/automation-report.md` — PASS / Nghi bug / Không chạy được.
- `automation/task.md` — log nội bộ của agent.
