# SPEC: Orchestrator — Project & Config

> EPIC **E1** của sản phẩm Agent Pipeline Orchestrator. Bối cảnh sản phẩm, data model `.orchestrator/`, non-functional dùng chung → `docs/orchestrator/OVERVIEW.md`. Giả định chưa giải quyết → `docs/orchestrator/ASSUMPTIONS-GAPS.md`.
>
> Nguồn: `SPEC-pipeline-orchestrator.md` v0.1 §F1.1–F1.4.

## Mô tả nghiệp vụ

Trước khi chạy được bất kỳ agent nào, orchestrator cần biết **ba thứ**: project nằm ở đâu, mỗi agent chạy bằng model nào với quyền gì, và credentials để nói chuyện với Backlog/Slack.

Hiện tại cả ba đều là kiến thức nằm trong đầu người dùng. Model được chọn ngầm bởi frontmatter từng agent file (`ba-agent` = sonnet, `techlead-design-agent` = opus) — không đổi được mà không sửa kit. Quyền của agent chỉ được kiểm soát bằng rule văn xuôi trong `POLICIES.md` ("BA không sửa source code") cộng 3 hook security. Credentials nằm plaintext trong file config.

E1 biến cả ba thành cấu hình tường minh, lưu trong `.orchestrator/` của project, sửa được từ UI mà không đụng vào `.claude/` của kit.

Một ràng buộc quan trọng: app **chỉ đọc** `.claude/`. Người dùng đổi model cho `ba-agent` trong app thì app truyền `--model` khi spawn, chứ không sửa frontmatter của `ba-agent.md`. Kit vẫn dùng được độc lập với app.

Ngoài ba thứ trên, E1 còn giữ **thiết lập giao diện** — cụ thể là chuyển đổi theme dark/light. Khác với ba thứ kia, đây là thiết lập **của người dùng chứ không phải của project**: nó phải giữ nguyên khi đổi sang project khác, nên không nằm trong `.orchestrator/` mà lưu ở mức ứng dụng.

## Actors & Preconditions

| Actor | Vai trò trong feature này |
|---|---|
| **PM** | Actor chính — mở project, cấu hình model/permission, nhập credentials |
| **Tech Lead** | Quyết định permission profile cho từng agent (PM thực hiện thao tác) |

**Phạm vi repo:** single-repo (chỉ repo desktop app `E01`) — theo `.claude/context/doc-structure.md`, **không cần Contract Lock** cho feature này.

**Preconditions:**

- App đã được cài trên máy người dùng (macOS hoặc Windows).
- Trên máy đã có Claude Code CLI đăng nhập sẵn — app không xử lý đăng nhập Anthropic.
- Người dùng có sẵn ít nhất một project folder đã được setup kit (đã chạy `/init-kit`, có `AGENTS.md` điền xong).
- Với integration: người dùng có sẵn Backlog API key và/hoặc Slack bot token.

## Happy Path

1. PM mở app lần đầu → app hiện màn hình **Project Launcher** (`OR_CONF_001`), danh sách recent rỗng.
2. PM bấm "Mở project" → chọn thư mục gốc của project.
3. App hỏi 3 đường dẫn (điền sẵn giá trị dò được, PM sửa nếu sai):
   - **Agents root** — thư mục chứa `.claude/agents/`
   - **DOCS_ROOT** — thư mục chứa `features/`
   - **Repository root** — thư mục chứa các repo source
4. App validate 3 đường dẫn, đọc `AGENTS.md` để lấy bảng Ecosystem (danh sách repo + Epic code + vai trò), và đọc cấu hình MCP server của project để biết Figma được kết nối qua đâu.
5. App tạo `.orchestrator/` trong project folder, sinh `config.json` với **model mặc định theo bảng đề xuất** và permission profile mặc định cho từng agent tìm thấy trong `.claude/agents/`.
6. App mở **Pipeline Board** (`OR_MONI_001`, thuộc E3) — project đã sẵn sàng.
7. PM vào **Settings** (`OR_CONF_002`) → tab "Agents": bảng mỗi agent một dòng (Agent · Model · Max turns · Permission profile). PM đổi model của `qc-agent` từ sonnet sang haiku → app lưu ngay vào `config.json`.
8. PM sang tab "Integrations": nhập Backlog space + API key + project ID, nhập Slack bot token + channel. Bấm "Kiểm tra kết nối" → app gọi thử, hiện ✅ cho từng integration.
9. App lưu credentials vào **OS keychain**; `config.json` chỉ giữ tham chiếu (tên key), không giữ giá trị.
10. PM sang tab "Giao diện", bật theme **dark**. Toàn bộ app đổi màu ngay, agent đang chạy không bị ảnh hưởng.
11. Lần mở app tiếp theo, app vẫn ở theme dark, và project xuất hiện trong danh sách recent — PM bấm 1 lần là vào thẳng Pipeline Board.

### Model mặc định (chỉnh được)

| Agent | Model | Lý do |
|---|---|---|
| `ba-agent` | opus | Chất lượng SPEC quyết định toàn pipeline |
| `techlead-design-agent` · `techlead-tasks-agent` | opus | Quyết định kiến trúc |
| `pm-agent` | sonnet | Tổng hợp plan từ tasks có sẵn |
| `design-analyst-agent`* | sonnet | Đọc Figma qua MCP, sinh file phân tích |
| `qc-agent` | sonnet | Khối lượng lớn, format ổn định |
| `backend-agent` · `frontend-agent` · `mobile-agent` | sonnet | Codegen theo contract đã lock |
| `qa-agent` | sonnet | Verify theo test case có sẵn |
| `qc-automation-agent` | sonnet | Sinh E2E theo template |
| `init-agent` | sonnet | Hỏi-đáp setup, không suy luận phức tạp |

> `*` `design-analyst-agent` là **agent mới**, hiện chưa tồn tại trong `.claude/agents/` của kit (xem `ASSUMPTIONS-GAPS.md` B17). Dòng này chỉ là giá trị mặc định sẽ áp dụng theo `AC-E1-13` khi agent được thêm vào — không phải xác nhận agent đã tồn tại. `designer-agent` gốc của kit (dùng cho luồng greenfield) **vẫn hiển thị** trong bảng Settings nếu file đó tồn tại, theo `AC-E1-08`, dù pipeline của orchestrator không gọi tới nó.

### Permission profile

| Profile | Quyền | Agent áp dụng mặc định |
|---|---|---|
| `read-only` | Chỉ đọc, không ghi file nào | — |
| `write-scoped` | Chỉ ghi trong thư mục chỉ định (vd `qc-agent` chỉ ghi `test-cases/`) | BA, Tech Lead ×2, PM, QC, QA, Designer, QC-Automation |
| `full` | Ghi source code, chạy migration | Backend, Frontend, Mobile |

## Alternative Flows & Edge Cases

| # | Tình huống | Hành vi mong đợi |
|---|---|---|
| AF-1 | Thư mục chọn không có `.claude/agents/` ở bất kỳ cấp nào | App cảnh báo, cho mở ở **chế độ read-only** (xem artifact được, không chạy được agent) |
| AF-2 | Cấu trúc lồng — `.claude/agents/` nằm sâu trong subfolder (trường hợp ESKITCHEN) | App dò được vẫn điền sẵn; dò không được thì để trống cho PM tự chỉ. **Không tự đoán** |
| AF-3 | `AGENTS.md` còn nguyên placeholder (chưa chạy `/init-kit`) | App cảnh báo "project chưa init", cho mở read-only, gợi ý chạy `/init-kit` |
| AF-4 | Repo khai trong Ecosystem nhưng chưa clone về máy | Đánh dấu repo đó `chưa clone` — trạng thái riêng, **không** coi là lỗi. Agent nhắm vào repo đó bị chặn từ trước khi spawn |
| AF-5 | Project folder bị đổi tên / xoá sau khi đã lưu vào recent | Bấm vào recent → báo "không tìm thấy", cho xoá khỏi danh sách hoặc chỉ lại đường dẫn |
| AF-6 | `.orchestrator/config.json` bị hỏng (JSON không parse được) | App không crash — backup file hỏng thành `config.json.bak`, sinh lại config mặc định, báo PM |
| AF-7 | Agent tồn tại trong `.claude/agents/` nhưng chưa có trong `config.json` (kit thêm agent mới) | App tự thêm dòng với model + permission mặc định, đánh dấu "mới" để PM review |
| AF-8 | Agent có trong `config.json` nhưng file agent đã bị xoá khỏi kit | App hiện dòng đó dạng mờ + nhãn "không còn trong kit", cho PM xoá |
| AF-9 | OS keychain không truy cập được (bị khoá / không hỗ trợ) | Báo lỗi rõ, **không** fallback ghi plaintext. Integration bị vô hiệu cho tới khi keychain dùng được |
| AF-10 | "Kiểm tra kết nối" Backlog trả 401 | Hiện lỗi kèm gợi ý kiểm tra API key; không lưu key sai vào keychain |
| AF-11 | PM đổi model/permission khi đang có agent chạy | Thay đổi áp dụng cho **lần spawn kế tiếp**, không ảnh hưởng agent đang chạy. UI nói rõ điều này |
| AF-12 | Project không khai MCP server nào phục vụ Figma | Cảnh báo khi mở project, nêu rõ stage Design sẽ không chạy được. Vẫn cho mở project bình thường |
| AF-13 | MCP Figma khai dạng local http (cần Figma Desktop đang chạy) nhưng app đó chưa mở | App không tự phát hiện được ở bước mở project — cảnh báo ở thời điểm spawn Designer (xem E2) |
| AF-14 | Project khai nhiều MCP server liên quan Figma với tên khác nhau | Hiển thị hết, cho PM chọn cái nào dùng cho stage Design |
| AF-15 | Người dùng chuyển theme khi đang có agent chạy | Giao diện đổi ngay, agent **không** bị gián đoạn, log đang stream không mất dòng nào |
| AF-16 | Nơi lưu lựa chọn theme không đọc được (lần đầu chạy, hoặc file hỏng) | Dùng **light**, không báo lỗi làm phiền người dùng |

## Acceptance Criteria

**Nhận diện & mở project**

- **AC-E1-01** — Khi mở app, màn hình đầu tiên là Project Launcher, hiển thị danh sách recent project (rỗng nếu chưa từng mở project nào).
- **AC-E1-02** — Khi PM chọn một thư mục, app hỏi **3 đường dẫn riêng** (agents root · DOCS_ROOT · repository root) và điền sẵn giá trị dò được. App **không** yêu cầu 3 thứ này phải nằm theo một cấu trúc thư mục cố định.
- **AC-E1-03** — Nếu app không dò ra được đường dẫn nào, ô đó để trống cho PM tự chỉ; app không điền giá trị đoán.
- **AC-E1-04** — Sau khi đọc `AGENTS.md`, app hiển thị danh sách repo từ bảng Ecosystem, mỗi repo kèm trạng thái `đã clone` hoặc `chưa clone` (dựa trên thư mục có tồn tại tại đường dẫn khai báo hay không).
- **AC-E1-05** — Nếu không tìm thấy `.claude/agents/` tại đường dẫn PM chỉ, app vẫn cho mở project ở chế độ read-only và hiển thị nhãn "read-only" cố định trên UI.
- **AC-E1-06** — Sau khi mở project thành công, thư mục `.orchestrator/` tồn tại trong project folder và chứa `config.json`.
- **AC-E1-07** — Project đã mở thành công xuất hiện trong danh sách recent ở lần mở app kế tiếp; bấm vào đó vào thẳng Pipeline Board mà không hỏi lại 3 đường dẫn.

**Cấu hình agent ↔ model**

- **AC-E1-08** — Tab Agents trong Settings hiển thị **một dòng cho mỗi file `.md` trong `.claude/agents/`**, với 4 cột: Agent · Model · Max turns · Permission profile.
- **AC-E1-09** — Cột Model là dropdown chỉ có 3 lựa chọn: `opus`, `sonnet`, `haiku`.
- **AC-E1-10** — Lần đầu sinh `config.json`, model của mỗi agent khớp bảng "Model mặc định" trong SPEC này.
- **AC-E1-11** — Khi PM đổi model của một agent, giá trị mới được ghi vào `config.json` và giữ nguyên sau khi đóng/mở lại app.
- **AC-E1-12** — Khi spawn agent, app truyền đúng giá trị model trong `config.json` qua tham số `--model`. File `.claude/agents/<agent>.md` **không bị sửa đổi** (kiểm tra bằng checksum trước/sau).
- **AC-E1-13** — Agent mới xuất hiện trong `.claude/agents/` nhưng chưa có trong `config.json` được tự thêm với giá trị mặc định và đánh dấu "mới".
- **AC-E1-14** — Agent có trong `config.json` nhưng không còn file tương ứng được hiển thị dạng mờ kèm nhãn "không còn trong kit".

**Permission profile**

- **AC-E1-15** — Cột Permission profile là dropdown 3 lựa chọn: `read-only`, `write-scoped`, `full`.
- **AC-E1-16** — Khi chọn `write-scoped`, app yêu cầu nhập ít nhất một đường dẫn thư mục được phép ghi; không nhập thì không lưu được.
- **AC-E1-17** — Khi spawn agent, app áp dụng permission profile tương ứng qua cơ chế giới hạn tool của Claude Code. App **không bao giờ** truyền `--dangerously-skip-permissions`.
- **AC-E1-18** — Giá trị permission mặc định lần đầu khớp bảng "Permission profile" trong SPEC này (Dev = `full`, còn lại = `write-scoped`).

**Credentials**

- **AC-E1-19** — Backlog và Slack credentials được lưu vào OS keychain; đọc `config.json` bằng text editor **không thấy** giá trị API key/token, chỉ thấy tên tham chiếu.
- **AC-E1-20** — Nút "Kiểm tra kết nối" gọi thử tới từng integration và hiển thị kết quả thành công/thất bại riêng cho Backlog và Slack.
- **AC-E1-21** — Nếu kiểm tra kết nối thất bại, credentials **không** được lưu vào keychain và app hiển thị nguyên văn mã lỗi trả về.
- **AC-E1-22** — Nếu OS keychain không truy cập được, app báo lỗi và vô hiệu hoá phần integration. App **không** ghi credentials ra file dưới bất kỳ dạng nào.

**Bền bỉ**

- **AC-E1-23** — `config.json` không parse được thì app đổi tên nó thành `config.json.bak`, sinh lại config mặc định và thông báo cho PM — app không crash và không mất project khỏi recent.
- **AC-E1-24** — Đổi model hoặc permission trong lúc có agent đang chạy không làm gián đoạn agent đó; thay đổi chỉ áp dụng cho lần spawn kế tiếp và UI nói rõ điều này.

**Cấu hình MCP của project**

- **AC-E1-25** — Khi mở project, app đọc cấu hình MCP server **của chính project đó** (`.mcp.json` và/hoặc `.claude/settings.json`) và hiển thị danh sách MCP server tìm thấy trong Settings, ở dạng chỉ đọc.
- **AC-E1-26** — App nhận diện MCP server Figma theo cấu hình thật của project, **không** giả định một tên server cố định. Không tìm thấy MCP nào phục vụ Figma thì app hiển thị cảnh báo nêu rõ stage Design sẽ không chạy được.
- **AC-E1-27** — App **không** lưu và **không** yêu cầu credentials Figma riêng. Toàn bộ việc kết nối Figma do MCP server của project đảm nhiệm.

**Giao diện — chuyển đổi theme**

- **AC-E1-28** — App có nút chuyển đổi giữa hai theme **dark** và **light**, truy cập được từ Settings.
- **AC-E1-29** — Lần chạy đầu tiên, khi người dùng chưa từng chọn theme, app hiển thị ở **light**.
- **AC-E1-30** — Chuyển theme có hiệu lực **ngay lập tức** trên toàn bộ giao diện đang mở, không cần khởi động lại app và không làm gián đoạn agent đang chạy.
- **AC-E1-31** — Lựa chọn theme được lưu ở **mức ứng dụng**, giữ nguyên sau khi đóng/mở lại app và **không đổi** khi chuyển sang project khác.
- **AC-E1-32** — Theme **không** được lưu trong `.orchestrator/` của project — xoá thư mục đó hoặc mở project mới không làm mất lựa chọn theme.
- **AC-E1-33** — Ở cả hai theme, log console giữ font monospace, và mọi trạng thái node trên Pipeline Board vẫn phân biệt được bằng mắt (liên quan `AC-E3-09`).

## Out of Scope

- **Đăng nhập Anthropic / quản lý API key của Claude Code** — app giả định CLI đã đăng nhập sẵn.
- **Sửa nội dung agent / command / rule từ trong app** — app chỉ đọc `.claude/`. Muốn đổi quy trình thì dùng editor ngoài.
- **Multi-project song song** — v1 chỉ 1 project tại một thời điểm.
- **Multi-user / phân quyền team** — mọi cấu hình là của người đang mở app.
- **Chạy `/init-kit` từ trong app** — project chưa init thì app chỉ cảnh báo và gợi ý, không tự chạy.
- **Đồng bộ config giữa nhiều máy** — `.orchestrator/` là local, gitignore-able.
- **Tự động clone repo còn thiếu** — app chỉ báo trạng thái `chưa clone`.
- **Cấu hình hoặc cài đặt MCP server** — app chỉ đọc cấu hình MCP có sẵn của project. Thêm/sửa MCP thì dùng editor ngoài.
- **Quản lý credentials Figma** — do MCP server của project đảm nhiệm, app không đụng tới.
- **Theme tuỳ biến / theo màu thương hiệu** — v1 chỉ có đúng hai theme dark và light.
- **Tự đổi theme theo cài đặt OS hoặc theo giờ trong ngày** — v1 chỉ đổi khi người dùng tự chọn.
- **Theme riêng cho từng project** — lựa chọn theme là của người dùng, dùng chung cho mọi project.

## Screens

| Screen Code | Screen | Actor | App | Screen Type | Mô tả ngắn | Figma Link |
|---|---|---|---|---|---|---|
| `OR_CONF_001` | Project Launcher | PM | E01* | Wizard | Danh sách recent + chọn thư mục project, xác nhận 3 đường dẫn (agents root · DOCS_ROOT · repository root) và hiển thị trạng thái clone của từng repo | |
| `OR_CONF_002` | Settings | PM | E01* | Settings | Năm tab: Agents (bảng model + max turns + permission per agent), Integrations (Backlog · Slack + kiểm tra kết nối), MCP (danh sách MCP server của project, chỉ đọc, chọn server dùng cho stage Design), Runtime (timeout, số lần retry), Giao diện (chuyển dark/light) | |

> `*` Cột **App** = Epic code của repo đích. Bảng Ecosystem trong `AGENTS.md` của kit hiện còn placeholder (kit chưa chạy `/init-kit`), nên `E01` là giá trị **tạm** cho repo desktop app — cần xác nhận lại khi khởi tạo repo thật.
