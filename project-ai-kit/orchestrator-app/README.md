# Orchestrator App

> Desktop app (Tauri + React) chạy pipeline BMAD của `project-ai-kit` bằng UI thay vì gõ tay từng slash command trong Claude Code CLI — Pipeline Board hiển thị 8 stage, bấm Run/Skip/Kill/Retry cho từng agent, theo dõi trạng thái theo thời gian thực.

> Guide chi tiết A→Z cho **kit** (agent/command/skill, quy trình feature BA → Design → Build → QA → QC → Deploy) nằm ở [`../README.md`](../README.md) — file này chỉ tập trung vào **app**: cách chạy app và cách trỏ app vào 1 project để dùng được.

---

## 1. Yêu cầu hệ thống

| Thành phần | Bắt buộc | Ghi chú |
|---|---|---|
| Node.js ≥ 18 + pnpm | ✅ | `npm install -g pnpm` nếu chưa có |
| Rust toolchain (stable) | ✅ | Tauri build phần backend bằng Cargo — cài qua [rustup.rs](https://rustup.rs) |
| Claude Code CLI, đã login | ✅ | App **spawn** `claude` CLI để chạy từng agent — không tự có logic gọi model. Xem Bước 0 ở [`../README.md`](../README.md) nếu chưa cài/login |
| macOS: Xcode Command Line Tools | ✅ (macOS) | `xcode-select --install` |
| Linux: `webkit2gtk` + các gói dev Tauri yêu cầu | ✅ (Linux) | Xem [Tauri prerequisites](https://tauri.app/start/prerequisites/) theo distro |

---

## 2. Chạy app

```bash
cd orchestrator-app
pnpm install
pnpm tauri dev      # mở cửa sổ desktop, hot-reload cả frontend (Vite) lẫn backend (Rust rebuild + restart tự động)
```

Build bản release (đóng gói thành app cài đặt được):

```bash
pnpm tauri build
```

`pnpm dev` (không qua `tauri`) chỉ chạy Vite dev server cho phần frontend — dùng để sửa UI nhanh mà không cần build lại Rust, nhưng sẽ không mở được cửa sổ desktop thật (không có backend Tauri phía sau).

---

## 3. Setup 1 project để dùng trong app

App không tự viết code hay tạo repo — nó **trỏ vào** một project đã có (hoặc sắp có) trên máy, thông qua 3 đường dẫn độc lập:

| Root | Chứa gì | Ví dụ |
|---|---|---|
| **Agents root** | `AGENTS.md` + `.claude/agents/` — nơi kit "sống" | `~/work/<ten-du-an>` |
| **DOCS_ROOT** | `features/` — SPEC/DESIGN/tasks của từng feature | `~/work/<ten-du-an>/docs` |
| **Repository root** | Các repo source code thật (backend/frontend/mobile...) | `~/work/<ten-du-an>/repos` |

3 root này **không bắt buộc lồng nhau** — có thể tách hẳn ra 3 vị trí khác nhau trên máy (ví dụ Agents root và DOCS_ROOT nằm trong 1 repo docs riêng, Repository root là 1 thư mục hoàn toàn khác chứa các repo clone về). App validate độc lập từng root, không giả định quan hệ thư mục cha-con giữa chúng.

### Bước 1 — Tạo project mới trong app

1. Mở app → màn hình Launcher → bấm **Mở project mới**.
2. Chọn 1 thư mục gốc bất kỳ (browse) — app dùng path này để **gợi ý** (không đoán bừa) `agentsRoot`/`docsRoot`/`repositoryRoot` nếu đã có `AGENTS.md`/`docs/`/repo clone sẵn trong đó, rồi chuyển sang form **Mở project**.
3. Điền **Tên project**.
4. Với 3 field path — có 2 cách:
   - Bấm từng nút **Chọn thư mục** để browse riêng lẻ, hoặc gõ tay.
   - Hoặc bấm **Dùng bố cục mặc định**: tự điền `agentsRoot = <root>`, `docsRoot = <root>/docs`, `repositoryRoot = <root>/repos` — quy ước gọn cho project mới, không bắt buộc.
   - **Không có thư mục nào cũng không sao** — hint "Chưa có cũng được — app sẽ tạo thư mục khi mở" nghĩa đúng như vậy.
5. Bấm **Mở project**.

Ngay khi mở, app tự động:
- Tạo 3 thư mục nếu chưa tồn tại.
- **Dựng khung kit** vào `agentsRoot`/`docsRoot` — copy `.claude/` (agents/commands/skills/rules/workflows...), `CLAUDE.md`, `POLICIES.md`, `AGENTS.md` (bản placeholder), `docs/features/` skeleton — **không cần `cp -r` tay** như luồng CLI thuần ở `../README.md` Bước 2 nữa, app làm thay.
- Tạo `.orchestrator/` (state nội bộ của app — xem mục 5).

Nếu dựng khung kit thất bại (ví dụ thư mục read-only), app báo warning và có nút **Bổ sung khung kit** để thử lại mà không cần đóng project.

### Bước 2 — Bỏ repo source vào Repository root

Ngoài app, `git clone` (hoặc `git submodule add`) từng repo backend/frontend/mobile vào đúng **Repository root** vừa chọn ở Bước 1 — giống hệt Bước 3 ở `../README.md`, chỉ khác là path gốc do app quản lý, không cần tự tạo cấu trúc thư mục tay.

### Bước 3 — Chạy `/init-kit`

`AGENTS.md` vừa được app dựng còn là **placeholder** — chưa biết tên repo thật, vai trò, actor nghiệp vụ. App phát hiện việc này và hiện banner **"Project chưa init"** ngay trên Launcher/Board, kèm 2 lệnh copy-paste sẵn:

```bash
cd "<agentsRoot>"
claude
```

rồi trong Claude Code:

```
/init-kit Tên dự án: <ten-du-an>
```

`init-agent` sẽ hỏi ~8 câu (tên repo, path thật, vai trò, docs root, actor...) — trả lời dựa trên cấu trúc đã tạo ở Bước 2. Chi tiết từng câu hỏi → `../README.md` Bước 4.

### Bước 4 — Quay lại app, kiểm tra lại

Bấm **"Đã chạy init, kiểm tra lại"** trên banner. App đọc lại `AGENTS.md`, parse bảng `## Repos` thành Ecosystem, và nếu hợp lệ sẽ chuyển project sang trạng thái sẵn sàng — Pipeline Board (8 stage, Run/Skip/Kill từng agent) dùng được từ đây.

Nếu vẫn còn `"Project chưa init"` hoặc warning về Ecosystem, thường do:
- Bảng `## Repos` trong `AGENTS.md` vẫn còn dòng placeholder — chạy lại `/init-kit`.
- Repo khai trong `AGENTS.md` không tìm thấy trên đĩa — kiểm tra lại `repositoryRoot` hoặc clone repo còn thiếu.
- Ô "Vai trò" của 1 repo không đọc được (phải đúng 1 từ `backend`/`frontend`/`mobile`/`other`) — sửa tay trong `AGENTS.md`.

App luôn nêu rõ lý do trong warning, không im lặng bỏ qua.

---

## 4. Mở lại project đã setup

Launcher mặc định hiện khối **Project gần đây** — chọn project đã mở trước đó trong danh sách để mở lại. Khác với luồng "Mở project mới" (Bước 1), đường này **không tự tạo thư mục thiếu** — nếu path đã bị xoá/đổi tên, app báo lỗi để bạn sửa lại path đã lưu thay vì âm thầm tạo project rỗng mới.

---

## 5. Ghi chú vận hành

- **`.orchestrator/`** (nằm trong `agentsRoot`) là state nội bộ của app — config, log run agent, snapshot, execution report... App tự thêm `.gitignore` cho thư mục này; nếu repo đã commit nhầm trước đó, app cảnh báo và gợi ý `git rm -r --cached .orchestrator`.
- **Read-only mode**: nếu `agentsRoot` không có `.claude/agents/`, project vẫn mở được nhưng ở chế độ chỉ xem — dùng **Bổ sung khung kit** để thoát khỏi trạng thái này.
- **Auth Claude CLI**: mặc định app dùng nguyên cách `claude` CLI đã login trên máy (`cli-default`). Có thể đổi sang Subscription/Console/API key riêng trong **Settings** của app nếu tổ chức cần tách biệt credential khỏi CLI mặc định.
- **1 project/lúc**: app chỉ mở được 1 project tại 1 thời điểm — đóng project hiện tại (Kill agent đang chạy nếu có) trước khi mở project khác.
- App không tự chạy agent nào — mọi run đều do người dùng bấm (Run/Retry/Resume trên từng node), kể cả sau khi qua gate/lock.
