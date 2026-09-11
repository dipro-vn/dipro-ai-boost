# 📋 BACKLOG GUIDELINE

> **Tài liệu này là chuẩn Dipro để sử dụng tool Backlog trong Quản lý dự án** — hợp nhất "Quy định sử dụng Backlog Dipro V2.0" (hiệu lực 27/7/2026, ban hành LongTD/DuongLTT/Thuy_CEO) với kit template cho AI agent.
>
> **Mọi thành viên dự án + AI agent (đặc biệt pm-agent, qc-agent, dev agents)** đều đọc và tuân thủ.
>
> **Nguồn gốc:** `AI_Source/Rule_Dipro_Backlog_V2.0.xlsx` (Numbers format) — file gốc giữ ở đó để đối chiếu khi Dipro update version mới.

---

## I. Thông Tin Cơ Bản

### 1. Members & Roles (Project Setting)

| Role | Authority | Áp dụng cho |
|---|---|---|
| `Administrator` | Toàn quyền | Space admin |
| `Project Administrator (Member)` | Edit Project Setting + Edit all issue | PM, Sub PM, BrSE |
| `Member` | Edit all issue | Thành viên tham gia dự án |
| `Guest` | View only all issue | Khách hàng hoặc thành viên không tham gia dự án |

---

### 2. Issue Types (Dipro chuẩn — 6 loại)

| Issue Type | Purpose | Template | Quy ước Subject | Ví dụ |
|---|---|---|---|---|
| `User_Story` | Chức năng cần làm gì, như thế nào, kết quả là gì.<br>ProjectBase: Tên WBS.<br>Labo/Maintenance: yêu cầu Khách hàng gửi về — chia nhỏ nếu lớn.<br>ProjectBase dùng User_Story để tạo **Critical_Path** xác định ngày dự án hoàn thành. | User_Story | `Tên Chức năng / Yêu Cầu` | `H-03-06_ご希望・お悩み_worry` |
| `Task` | Giao task thực hiện | Task | `[Tên Chức năng/màn hình]_Mô tả ngắn gọn task` | `[H-03-06][ご希望・お悩み_worry]_Integrate API` |
| `ChangeRequest` | Yêu cầu thêm từ Khách hàng ngoài Scope/Estimate/Requirement đã chốt. **Áp dụng với ProjectBase.** | Task | `[Tên Chức năng/màn hình]_Mô tả ngắn gọn yêu cầu thay đổi` | `[H-03-05][ライフスタイル_Lifestyle] Xóa field cự ly ở mục cooking` |
| `Bug` | QC log bug → assign Teamlead/PM để assign người fix | Bug | `[Tên Chức năng/màn hình]_Mô tả thông tin sai khi thao tác + màn abcxyz` | `[H-04-2]_App_Chưa load lại data chính xác khi kết nối mạng trở lại` |
| `Issue` | Log vấn đề phát sinh trong dự án (ngoài dự kiến, ảnh hưởng Progress/Quality/Cost, cần support giải quyết) và tracking đến khi xong | Task | `Mô tả ngắn gọn vấn đề (Nguyên nhân và hậu quả)` | `Server UAT lỗi dẫn đến Khách không lưu data test được` |
| `Risk` | Log rủi ro có thể xảy ra trong tương lai, ảnh hưởng Progress/Quality/Cost — add người theo dõi và xử lý | Task | `Mô tả ngắn gọn rủi ro (Nguyên nhân và hậu quả dự kiến)` | `Tiến độ dự án có thể chậm so với plan do khả năng có nhiều task BE khó` |

**ROLE tag prefix trong Subject** (thêm vào trước Category để dễ filter):

| Tag | Dùng cho |
|---|---|
| `[BE]` | Backend developer |
| `[FE]` | Frontend developer |
| `[MOBILE]` | Mobile developer |
| `[QC]` | QC/Tester |
| `[DESIGNER]` | Designer |
| `[INFRA]` | DevOps/Infra |

Format cuối: `[ROLE] [Category] _ <mô tả>` — ví dụ `[BE] [H-03-06] _ Integrate worry API`.

---

### 3. Categories (Epic)

Category tương ứng **Epic/repo** dự án — điền theo bảng Ecosystem trong `AGENTS.md`. Mỗi issue bắt buộc gán Category.

| Category | Mô tả |
|---|---|
| _(vd: `Backend_API`)_ | _(1 dòng — điền qua `/init-kit` hoặc thủ công theo bảng Ecosystem)_ |
| _(vd: `Admin_Web`)_ | |
| _(vd: `Mobile_App`)_ | |

---

### 4. Milestones

Các mốc dự án đang hướng tới. Ví dụ Dipro:

- `Released 30/7/2026`
- `Golive 31/12/2026`
- `Event 25/12/2026`

Điền milestone thật của dự án qua `/init-kit` hoặc update trực tiếp bảng dưới:

| Milestone | Mô tả |
|---|---|
| _(vd: `Released xxx`)_ | Bản phát hành chính thức |
| _(vd: `Go-live yyy`)_ | Thời điểm hệ thống đi vào vận hành thực tế |

---

### 5. Version (theo loại dự án)

| Loại dự án | Cách define Version |
|---|---|
| **Project Base** | Giai đoạn/công đoạn: `Requirement / Design / Coding / Testing / UAT / Release`.<br>Coding có thể chia nhỏ theo team: `Coding_BE`, `Coding_FE`, `Coding_Mobile`. |
| **Project Labo** | Theo Sprint hoặc mốc milestone (3 tháng, 6 tháng), review dự án. |
| **Project Maintenance** | Theo tháng: `T9_Maintenance`, `T10_Maintenance`, ... |

Version mặc định kit (khi user chưa customize):

| Version | Mô tả |
|---|---|
| `Phase 1` | Giai đoạn phát triển đầu tiên |
| `Phase 2` | Giai đoạn phát triển tiếp theo |

---

### 6. Status & Workflow (Dipro chuẩn — 9 status)

| # | Status | Ai chuyển | Điều kiện / Mô tả |
|---|---|---|---|
| 1 | `Open` | Người tạo | Mặc định khi tạo mới. |
| 2 | `In-Progress` | Assignee | Assignee bắt đầu xử lý (thực hiện task / fix bug). |
| 3 | `Done` | Assignee | Assignee hoàn thành xử lý. |
| 4 | `Reviewing` | Assignee | Assignee **tạo subtask (Add child issue)** cho reviewer — **KHÔNG edit Assignee trong Issue Parent**. |
| 5 | `Testing` | Người tạo | Người tạo test, hoặc **tạo subtask** cho tester — **KHÔNG edit Assignee trong Issue Parent**. |
| 6 | `Close` | Người tạo | Người tạo xác nhận hoàn thành. |
| 7 | `Re-Open` | Người tạo | Chưa đồng ý kết quả xử lý → yêu cầu xử lý lại. Kèm comment lý do. |
| 8 | `Pending` | Người tạo | Chờ xem xét/confirm để xử lý sau. |
| 9 | `Cancel` | Người tạo | Không cần xử lý nữa. |

**⚠️ Quy tắc subtask (bắt buộc):**

Tạo thêm subtask (`Add child issue`) để ghi nhận đúng Assignee khi:

- Task có nhiều người cùng xử lý
- Phát sinh thêm task **review** (assign cho reviewer)
- Phát sinh thêm task **test** (assign cho tester)

**Không được** edit trực tiếp Assignee trong Issue Parent — sẽ mất track ai làm phần nào.

---

### 6b. Status flow đơn giản — chỉ 1 Assignee

Áp dụng khi task/bug chỉ có 1 người xử lý duy nhất (không cần reviewer/tester khác):

| Status | Người chuyển | Điều kiện | Chi tiết |
|---|---|---|---|
| `Open` | Người tạo Task Parent | — | Tạo mới, assign Assignee chịu trách nhiệm. |
| `In-Progress` | Assignee | Bắt đầu xử lý | Chuyển + comment báo Người tạo. |
| `Done` | Assignee | Hoàn thành | Chuyển + comment báo Người tạo. |
| `Close` | Người tạo | Hài lòng kết quả | Chuyển về Close. |
| `Re-Open` | Người tạo | Chưa hài lòng | Chuyển Re-Open + comment lý do. |
| `Pending` | Người tạo | Chờ confirm | Chuyển Pending. |

**Customize:** Nếu dự án cần status khác (VD `Request Review`, `Testing Request`, `Resolved`) → tham khảo team QA để thiết lập phù hợp.

---

## II. Template — Task

Các trường bắt buộc đánh dấu `*`.

| Trường | Mô tả | Ví dụ | Bắt buộc |
|---|---|---|---|
| `Subject` * | Tiêu đề task theo Subject convention của Issue Type | `[H-03-06][ご希望・お悩み_worry]_Integrate API` | ✅ |
| `Description` | Mô tả chi tiết (Backlog Markdown) | (xem template §II.b) | |
| `Status` | `Open` / `In-Progress` / `Done` / `Close` / `Re-Open` / `Pending` / `Cancel` | `Done` | |
| `Priority` | `High` / `Normal` / `Low` | `High` | |
| `Assignee` * | Người nhận xử lý | `Vũ Đức Phương` | ✅ |
| `Category` | Chức năng/màn hình define theo dự án | `H-03-06` | |
| `Milestone` | Giai đoạn/Sprint/Tháng theo Version schema | `Coding` | |
| `Due date` * | Thời hạn mong muốn hoàn thành | `2026-08-25 00:00:00` | ✅ |
| `Start date` * | Ngày bắt đầu thực tế | `2026-08-22 00:00:00` | ✅ |
| `End date` * | Ngày kết thúc thực tế | `2026-08-25 00:00:00` | ✅ |
| `Estimated Hours` * | Ước tính (giờ) | `10.0` | ✅ |
| `Actual Hours` * | Thực tế (giờ) — update khi `Done` | `8.0` | ✅ |
| `Parent Issue` * | Task/Bug bắt buộc link User_Story hoặc Epic cha | `PROJ-822` | ✅ |

### II.b — Description template (Backlog Markdown)

```markdown
## Mục tiêu
<copy từ section Mục tiêu trong task file>

### URL THAM KHẢO
- SPEC: <base>/<feature>/SPEC/
- DESIGN: <base>/<feature>/<repo>/DESIGN/
- Task: <base>/<feature>/<repo>/tasks/task-X-Y/

## File ảnh hưởng
<từ section Context > File liên quan>

## Phase & Dependencies
- Phase: <từ Metadata>
- Depends on: <từ Metadata>
- Song song với: <từ Metadata>

## Non-Regression
<copy Non-Regression Table>

## Definition of Done
<copy Definition of Done checklist>

---
🤖 Synced từ task file: `<đường dẫn task-X-Y.md>`
```

---

## III. Template — Bug

Các trường **thêm/khác** so với Task template:

| Trường | Mô tả | Enum / Ví dụ | Bắt buộc |
|---|---|---|---|
| `Title` (Parent issue) | `[Tên chức năng] + Bug màn hình` hoặc `+ user/admin` | — | |
| `Subject` * | `*[Tên Chức năng]_Mô tả thông tin sai khi thao tác + màn abcxyz*` — hạn chế ghi thiếu/lặp | `[H-04-2]_App_Chưa load lại data chính xác khi kết nối mạng trở lại` | ✅ |
| `Description` | Format bắt buộc: Environment / Ver / Device / PreCondition / Steps / Actual result / Expected result / Evidence | (xem §III.b) | |
| `Producer` * | Tên người **gây ra lỗi** | `Nguyễn Văn A` | ✅ |
| `Assignee` * | **Teamlead hoặc PM** để assign người fix | | ✅ |
| `Bug type` * | `Bug UI` / `Bug logic` | `Bug logic` | ✅ |
| `Root Cause` * | `Requirement` / `Design` / `Coding` / `CR Customer` | `Coding` | ✅ |

Các trường còn lại (Category, Milestone, Priority, Due/Start/End, Estimated/Actual) giống Task.

### III.b — Bug Description format (bắt buộc)

```markdown
**Environment Test:**
#100 (hoặc staging/dev/UAT)

**Device/Browser:**
SS A23
Android 13
Chrome 120

**Precondition:**
- Logined

**Steps:**
1. Ngắt kết nối
2. Vào màn H-04-2 quan sát
3. Mở mạng lại
4. Ở màn H-04-2 quan sát khi xem lịch ở tháng tiếp theo, sau đó back về tháng hiện tại

**Expected results:**
- Hiện đúng lịch khi có mạng trở lại khi đi tiếp hoặc back lại

**Actual results:**
- Hiện sai lịch / trắng lịch

**Evidence:**
(paste hình ảnh trực tiếp, video → embed link)

**Ver:**
(version bản release đang có bug — bỏ qua nếu không có info)
```

---

## IV. Phân Quyền

### 4.1 Định nghĩa Role dự án

| Role | Mô tả |
|---|---|
| `PM` | Project Manager |
| `BrSE` | Bridge System Engineer (cầu nối kỹ thuật với khách hàng) |
| `Team Leader` | Leader của từng nhóm chức năng |
| `Tech Leader` | Technical Leader toàn dự án |
| `Developer` | Lập trình viên (Frontend / Backend / Mobile) |
| `QC / Tester` | Kiểm thử chất lượng |
| `BA` | Business Analyst |
| `Designer` | UI/UX Designer |

### 4.2 Quyền tạo Issue

| Issue Type | PM | BrSE | Team Leader | Tech Leader | Developer | QC | BA / Designer |
|---|---|---|---|---|---|---|---|
| `User_Story` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `ChangeRequest` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `Task` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Bug` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Issue` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Risk` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 4.3 Quyền chuyển sang `Close`

| Issue Type | PM | BrSE | Team Leader | Tech Leader | Developer | QC |
|---|---|---|---|---|---|---|
| `User_Story` / `ChangeRequest` / `Task` / `Issue` / `Risk` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| `Bug` | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |

> **Lưu ý:**
> - Trừ Bug: chỉ PM/Leader mới được Close.
> - Bug: QC verify xong → chuyển `Testing → Done → Close`.

---

## V. Quy tắc chung

1. **Không tạo issue trùng lặp** — kiểm tra trước khi tạo mới.
2. **Cập nhật Actual Hour** khi chuyển sang `Done` / `Close`.
3. **Bug/Task phải có Parent Issue** — link rõ đến User_Story hoặc feature liên quan.
4. **Không tự đóng issue của người khác** nếu không có quyền.
5. **ChangeRequest phải được PM/BrSE xác nhận** trước khi assign cho dev.
6. **Re-Open bắt buộc comment lý do** — ghi rõ tại sao mở lại.
7. **Tạo subtask (Add child issue)** để ghi nhận đúng Assignee — **không edit Assignee Parent** khi task có nhiều người xử lý / cần reviewer / cần tester.
8. **QC log bug** → assign Teamlead/PM (không assign thẳng cho Dev fix) — Teamlead/PM sẽ điều phối người fix.

---

## VI. Ví dụ full flow (từ Dipro V2.0)

| Trạng thái | Bước thực hiện | Bước phụ (subtask) |
|---|---|---|
| `Open` | PM log Task, assign cho Dev | |
| `In-Progress` | Dev nhận task, chuyển In-Progress | |
| `Done` | Dev làm xong, chuyển Done | |
| `Testing` | Dev muốn request test, chuyển Testing | **→ Dev tạo Task child, assign cho QC** |
| `Testing` (cont.) | QC nhận test, đổi Assignee sang QC ở subtask | |
| `Deploy` | PM đổi Assignee sang Tech Leader deploy | **→ PM tạo Task child, assign cho Tech Leader** |
| `Close` | PM đóng | |

---

## VII. Doc Structure

Khi tạo task file (`task-X-Y.md`) trước khi sync Backlog, xem `.claude/context/doc-structure.md` để biết cấu trúc folder.

**Path duy nhất:** `<DOCS_ROOT>/features/<feature-name>/<repo-name>/tasks/task-X-Y.md`

---

## VIII. Lịch sử cập nhật

| Version | Ngày | Người cập nhật | Nội dung thay đổi |
|---|---|---|---|
| v1.0 | 20/10/2023 | DuongLTT | Ban hành mới (Dipro Backlog Rule V1.0) |
| v2.0 | 27/7/2026 | LongTD | Gộp Dipro Backlog Rule V2.0 vào kit — thêm 6 Issue Types (ChangeRequest/Issue/Risk), 9-status flow, quy tắc subtask, Template_Bug (Producer/Bug type/Root Cause), Description format bắt buộc |

---

*© Backlog Guideline — Tài liệu nội bộ Dipro + kit AI agent. Vui lòng không chia sẻ ra ngoài.*
