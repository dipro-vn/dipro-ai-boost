# SPEC: Orchestrator — Integrations (Backlog · Slack)

> ## ⛔ EPIC E5 ĐÃ BỊ LOẠI KHỎI PHẠM VI (25/08/2026) — xem quyết định **B22** trong `ASSUMPTIONS-GAPS.md`
>
> Toàn bộ nội dung dưới đây **không còn được implement**. File giữ lại làm hồ sơ lịch sử, không phải mô tả hiện trạng.
>
> - **Backlog** (`AC-E5-01..18`) — đã gỡ khỏi app cùng lúc với `pm-agent`: phần "đẩy" chạy bằng cách spawn chính `pm-agent` (quyết định B21), nên agent bị gỡ thì tính năng mất chỗ dựa. Phần "kéo trạng thái" qua REST cũng gỡ theo vì không còn mapping issue để kéo về.
> - **Slack** (`AC-E5-19..27`) — vốn đã out-of-scope từ trước theo B20, chưa từng được implement.
>
> Việc tạo issue Backlog từ task file giờ làm thủ công theo `.claude/context/backlog-workflow.md` (file này **vẫn còn** trong kit, cùng MCP server `backlog` mà `techlead-tasks-agent` dùng để tra Category).

> EPIC **E5** của sản phẩm Dipro AI Boost. Bối cảnh sản phẩm, data model `.orchestrator/`, non-functional dùng chung → `docs/orchestrator/OVERVIEW.md`. Giả định chưa giải quyết → `docs/orchestrator/ASSUMPTIONS-GAPS.md`.
>
> Nguồn: `SPEC-pipeline-orchestrator.md` v0.1 §F5.1–F5.2.

## Mô tả nghiệp vụ

Pipeline sinh ra task dưới dạng file `.md`. Nhưng công ty theo dõi công việc trên **Backlog (Nulab)**, và team trao đổi trên **Slack**. Không nối hai đầu này lại thì PM phải làm hai việc thủ công: gõ tay từng issue lên Backlog, và tự đi báo cho team mỗi khi có gì cần chú ý.

Kit đã có sẵn một nửa: command `/create-backlog` chạy `pm-agent` để tạo issue từ `tasks/task-*.md`, và MCP server `@nulab/backlog-mcp-server` đã khai trong `.claude/settings.json`. Nhưng nó là thao tác một chiều, chạy tay, và không có đường về — trạng thái issue trên Backlog không quay lại được vào pipeline.

E5 làm hai việc:

**Đẩy đi** — sau khi kế hoạch được duyệt, PM bấm một nút để tạo issue hàng loạt lên Backlog, đúng quy định `backlog-workflow.md` (bản hợp nhất "Quy định sử dụng Backlog Dipro V2.0", hiệu lực 27/07/2026).

**Kéo về** — trạng thái issue trên Backlog hiển thị ngay cạnh task trong Pipeline Board, để PM nhìn một chỗ là biết cả tiến độ agent lẫn tiến độ người.

Và **báo tin** — Slack nhận thông báo cho những sự kiện đáng để ngắt quãng người khác: gate đang chờ duyệt, agent hỏng, contract bị vi phạm, QA trượt.

Nguyên tắc xuyên suốt: **không bao giờ tự tạo issue hàng loạt mà chưa được xác nhận**. `pm-agent` đã có quy tắc "tạo 1 issue mẫu → confirm với user → mới batch phần còn lại"; app giữ đúng quy tắc đó.

## Actors & Preconditions

| Actor | Vai trò trong feature này |
|---|---|
| **PM** | Actor chính — cấu hình mapping, duyệt issue mẫu, bấm đẩy hàng loạt, đọc trạng thái sync |
| **Tech Lead** | Nhận thông báo Slack khi agent hỏng hoặc contract bị vi phạm |
| **Dev (BE/FE/Mobile)** | Nhận thông báo Slack; xem trạng thái issue của mình cạnh task |
| **QC** | Nhận thông báo khi QA trượt hoặc pipeline hoàn tất |

**Phạm vi repo:** single-repo (`E01`) — **không cần Contract Lock** cho chính feature này.

**Preconditions:**

- E1 đã hoàn tất: Backlog credentials (space, API key, project ID) và Slack credentials (bot token, channel) đã lưu vào OS keychain và kiểm tra kết nối thành công.
- Với đẩy Backlog: feature đã có ít nhất một `tasks/task-*.md`.
- Người dùng có quyền tạo issue trên Backlog project đích.
- `.claude/context/backlog-workflow.md` là **nguồn quy định duy nhất** về issue type, status, subtask, template — app không tự đặt convention riêng.

## Happy Path

### Đẩy task lên Backlog

1. Kế hoạch đã duyệt, feature có 12 file `tasks/task-*.md`. PM bấm **Push to Backlog** trên Pipeline Board.
2. Mở **Backlog Sync Panel** (`OR_INTG_001`). App đọc metadata thật từ Backlog project (categories, milestones, issue types, priorities, danh sách thành viên) — chỉ đọc, chưa ghi gì.
3. App hỏi 5 thông tin bắt buộc theo `pm-agent` Bước 4.1: Parent Issue · Category · Milestone · Assignee · URL tham chiếu base.
4. PM chọn từ danh sách thật lấy về, không phải gõ tay. Giá trị nào không khớp thì app liệt kê lựa chọn để PM chọn, **không tự đoán**.
5. App hiện bảng preview: mỗi task file → một dòng, kèm Subject đã format, Issue Type, Priority, Estimated Hours, và nội dung description sẽ tạo.
6. PM bấm **Tạo issue mẫu**. App tạo **đúng một** issue trên Backlog và hiện link để PM mở kiểm tra.
7. PM xem thấy đúng → bấm **Tạo phần còn lại**. App tạo 11 issue còn lại, hiện tiến độ từng cái.
8. Xong, app hiện danh sách issue key nhóm theo phase, ghi mapping `task file ↔ issue key` vào `.orchestrator/`.

### Kéo trạng thái về

9. Pipeline Board hiển thị trạng thái Backlog ngay cạnh mỗi task node.
10. Cứ 15 phút app tự làm mới; PM cũng bấm làm mới thủ công được bất cứ lúc nào.
11. Dev đổi issue sang `In-Progress` trên Backlog → lần làm mới kế tiếp Pipeline Board hiện đúng trạng thái đó.

### Thông báo Slack

12. Contract Lock bị vi phạm giữa lúc build. App gửi tin nhắn vào channel đã cấu hình: nêu tên feature, file nào lệch, và kèm deep-link mở đúng màn hình gate trong app.
13. Tech Lead bấm link trong Slack → app bật lên đúng màn hình `OR_GATE_002`.
14. PM vào Settings tắt loại thông báo "stage hoàn thành" vì quá ồn, giữ lại các loại còn lại.

### Các loại sự kiện gửi Slack (bật/tắt từng loại)

| Sự kiện | Mặc định |
|---|---|
| Gate đang chờ duyệt | Bật |
| Contract violation | Bật |
| Agent failed | Bật |
| QA Report FAIL | Bật |
| Pipeline hoàn tất | Bật |
| Stage hoàn thành | Tắt |

## Alternative Flows & Edge Cases

| # | Tình huống | Hành vi mong đợi |
|---|---|---|
| AF-1 | Chưa cấu hình Backlog credentials | Nút Push to Backlog bị vô hiệu kèm hướng dẫn vào Settings |
| AF-2 | Metadata PM chọn không khớp gì trên Backlog (vd milestone không tồn tại) | App liệt kê lựa chọn có thật để PM chọn lại; **không tự tạo** milestone mới, **không đoán** |
| AF-3 | PM xem issue mẫu thấy sai | Bấm huỷ → app **không tạo** các issue còn lại. Issue mẫu đã tạo được nêu link để PM tự xoá trên Backlog |
| AF-4 | Backlog trả lỗi giữa chừng khi tạo hàng loạt (rate limit, mạng đứt) | Dừng tại chỗ, giữ nguyên các issue đã tạo, hiện rõ đã tạo tới đâu và cái nào chưa. Cho tiếp tục từ điểm dừng, **không** tạo lại từ đầu |
| AF-5 | Bấm Push to Backlog lần hai cho feature đã đẩy rồi | App phát hiện qua mapping đã lưu, cảnh báo và chỉ hiện những task **chưa** có issue |
| AF-6 | Task file bị sửa sau khi đã tạo issue | App **không tự cập nhật** issue. Hiện dấu hiệu lệch, để PM quyết |
| AF-7 | Issue bị xoá trên Backlog | Làm mới thấy không còn → đánh dấu `không tìm thấy`, không tự tạo lại |
| AF-8 | Làm mới thất bại (mạng, token hết hạn) | Giữ nguyên trạng thái đã biết kèm nhãn "số liệu cũ từ &lt;thời điểm&gt;", không xoá trắng |
| AF-9 | Chưa cấu hình Slack | Thông báo bị bỏ qua âm thầm, không hiện lỗi lặp đi lặp lại mỗi sự kiện |
| AF-10 | Slack trả lỗi khi gửi | Ghi vào log của app, thử lại tối đa số lần theo cấu hình, sau đó bỏ qua. **Không** chặn pipeline |
| AF-11 | Nhiều sự kiện xảy ra dồn dập | Gom lại, không spam channel từng tin một |
| AF-12 | Người dùng bấm deep-link Slack khi app đang đóng | App mở lên và đi thẳng tới màn hình tương ứng |
| AF-13 | Deep-link trỏ tới project khác project đang mở | App hỏi trước khi chuyển project, không tự đóng project đang làm dở |
| AF-14 | Task file không đủ metadata bắt buộc (thiếu Estimated Hours) | Hiện cảnh báo tại dòng đó trong preview; PM bổ sung tay hoặc bỏ qua task đó |

## Acceptance Criteria

**Đẩy task lên Backlog**

- **AC-E5-01** — Nút Push to Backlog chỉ bật khi Backlog credentials đã cấu hình và kiểm tra kết nối thành công; chưa cấu hình thì nút mờ kèm hướng dẫn.
- **AC-E5-02** — Trước khi tạo bất kỳ issue nào, app đọc metadata thật từ Backlog project (categories, milestones, issue types, priorities, danh sách thành viên) và chỉ cho PM **chọn từ danh sách lấy về**.
- **AC-E5-03** — App hỏi đủ 5 thông tin bắt buộc: Parent Issue, Category, Milestone, Assignee, URL tham chiếu base. Thiếu bất kỳ thông tin nào thì không tạo được issue.
- **AC-E5-04** — Giá trị PM nhập không khớp metadata thật thì app liệt kê các lựa chọn có thật để chọn lại. App **không tự tạo** category/milestone mới và **không tự chọn** giá trị gần đúng.
- **AC-E5-05** — App hiển thị bảng preview toàn bộ issue sẽ tạo — mỗi task file một dòng, kèm Subject đã format, Issue Type, Priority, Estimated Hours và nội dung description.
- **AC-E5-06** — Subject, Issue Type, và cấu trúc description tuân thủ đúng quy định trong `.claude/context/backlog-workflow.md`; app không dùng convention riêng.
- **AC-E5-07** — App tạo **đúng một issue mẫu** trước, hiển thị link tới issue đó, và **chỉ** tạo các issue còn lại sau khi PM xác nhận.
- **AC-E5-08** — PM huỷ sau khi xem issue mẫu thì các issue còn lại **không được tạo**, và app hiển thị link issue mẫu để PM tự xử lý.
- **AC-E5-09** — Sau khi tạo xong, app hiển thị danh sách issue key nhóm theo phase và lưu mapping `task file ↔ issue key` trong `.orchestrator/`.
- **AC-E5-10** — Lỗi giữa chừng khi tạo hàng loạt khiến app dừng tại chỗ, giữ nguyên các issue đã tạo, hiển thị đã tạo tới đâu, và cho tiếp tục từ điểm dừng mà **không** tạo trùng.
- **AC-E5-11** — Push to Backlog lần thứ hai cho cùng feature chỉ hiển thị các task **chưa có** issue tương ứng, kèm cảnh báo.
- **AC-E5-12** — Task file thiếu metadata bắt buộc được đánh dấu cảnh báo ngay tại dòng đó trong preview.
- **AC-E5-13** — App **không tự sửa** nội dung task file `.md` trong bất kỳ bước nào của quá trình đẩy.

**Kéo trạng thái về**

- **AC-E5-14** — Pipeline Board hiển thị trạng thái issue Backlog ngay cạnh task tương ứng, dựa trên mapping đã lưu.
- **AC-E5-15** — App tự làm mới trạng thái mỗi 15 phút, và người dùng bấm làm mới thủ công được bất cứ lúc nào.
- **AC-E5-16** — Làm mới thất bại thì app giữ nguyên trạng thái đã biết và hiển thị nhãn cho biết số liệu lấy từ thời điểm nào — không xoá trắng dữ liệu.
- **AC-E5-17** — Issue không còn tồn tại trên Backlog được đánh dấu `không tìm thấy`; app **không** tự tạo lại.
- **AC-E5-18** — Task file thay đổi sau khi đã tạo issue thì app hiển thị dấu hiệu lệch nhưng **không tự cập nhật** issue trên Backlog.

**Thông báo Slack**

- **AC-E5-19** — App gửi thông báo Slack cho 6 loại sự kiện liệt kê trong SPEC này, mỗi loại bật/tắt độc lập trong Settings.
- **AC-E5-20** — Giá trị bật/tắt mặc định của 6 loại sự kiện khớp bảng "Các loại sự kiện gửi Slack" trong SPEC này.
- **AC-E5-21** — Nội dung thông báo bằng tiếng Việt, nêu tên feature và bối cảnh cụ thể của sự kiện (vd với contract violation: nêu đích danh file bị lệch).
- **AC-E5-22** — Mỗi thông báo kèm một deep-link; bấm vào mở app đúng màn hình liên quan tới sự kiện đó.
- **AC-E5-23** — Deep-link trỏ tới project khác project đang mở thì app hỏi xác nhận trước khi chuyển, không tự đóng project đang làm dở.
- **AC-E5-24** — Slack chưa cấu hình thì thông báo được bỏ qua âm thầm, app **không** hiện lỗi lặp lại theo từng sự kiện.
- **AC-E5-25** — Gửi Slack thất bại thì app ghi log, thử lại theo số lần cấu hình, rồi bỏ qua — việc này **không** làm pipeline dừng hay chuyển sang trạng thái lỗi.
- **AC-E5-26** — Nhiều sự kiện xảy ra trong khoảng thời gian ngắn được gom lại thay vì gửi từng tin riêng lẻ.

**Bảo mật**

- **AC-E5-27** — Nội dung gửi lên Slack **không chứa** đoạn source code, giá trị credentials, hay nội dung file bị hạn chế theo `.claude/rules/SECURITY.md` — chỉ chứa tên feature, tên file, và trạng thái.

## Out of Scope

- **Tạo issue cho loại khác ngoài Task** — v1 chỉ đẩy từ `tasks/task-*.md`. Bug, ChangeRequest, Risk vẫn tạo tay theo `backlog-workflow.md`.
- **Đồng bộ hai chiều nội dung** — trạng thái kéo về một chiều; app không ghi ngược task file, cũng không cập nhật issue khi task file đổi.
- **Tự động chuyển status issue theo tiến độ agent** — chuyển status là quyết định của người, theo quy trình 9 status trong `backlog-workflow.md`.
- **Tự tạo subtask** — quy tắc subtask trong `backlog-workflow.md` phụ thuộc phân công người thật; PM tạo tay.
- **Duyệt gate từ Slack** — Slack chỉ nhận thông báo một chiều; duyệt phải làm trong app (E4).
- **Tích hợp ngoài Backlog và Slack** (Jira, Teams, email) — không thuộc v1.
- **Tự động submit bug report lên Backlog** — kit quy định rõ QC không auto-submit bug.
- **Quản lý quyền trên Backlog** — app dùng đúng quyền của API key được cấp.

## Screens

| Screen Code | Screen | Actor | App | Screen Type | Mô tả ngắn | Figma Link |
|---|---|---|---|---|---|---|
| `OR_INTG_001` | Backlog Sync Panel | PM | E01* | Modal | Chọn 5 metadata bắt buộc từ danh sách thật, preview bảng issue sẽ tạo, tạo issue mẫu → xác nhận → tạo hàng loạt, hiện tiến độ và danh sách issue key | |

> Cấu hình credentials và bật/tắt loại thông báo Slack nằm trong `OR_CONF_002` (Settings, thuộc E1). Trạng thái issue Backlog hiển thị trong `OR_MONI_001` (Pipeline Board, thuộc E3). E5 chỉ bổ sung một màn hình riêng.
>
> `*` Cột **App** = Epic code của repo đích. Bảng Ecosystem trong `AGENTS.md` của kit hiện còn placeholder, nên `E01` là giá trị **tạm** cho repo desktop app — cần xác nhận lại khi khởi tạo repo thật.
