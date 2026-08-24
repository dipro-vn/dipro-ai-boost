# SPEC: Orchestrator — Pipeline Execution

> EPIC **E2** của sản phẩm Agent Pipeline Orchestrator. Bối cảnh sản phẩm, data model `.orchestrator/`, non-functional dùng chung → `docs/orchestrator/OVERVIEW.md`. Giả định chưa giải quyết → `docs/orchestrator/ASSUMPTIONS-GAPS.md`.
>
> Nguồn: `SPEC-pipeline-orchestrator.md` v0.1 §F2.1–F2.4.

## Mô tả nghiệp vụ

Hôm nay, chạy hết pipeline BMAD nghĩa là ngồi trong một session Claude Code CLI và **copy-paste handover message** từ output agent này sang prompt agent kế tiếp. Mỗi agent kết thúc bằng một câu dạng `"Hãy là Tech Lead Design, làm DESIGN.md từ SPEC này: <path>"` — đó là toàn bộ "keo dán" giữa các stage.

Kit có sẵn một shortcut (`/create-feature` → `bmad-plan-phase.js` / `bmad-build-phase.js`) chạy tự động một phần, nhưng nó chạy **bên trong** session LLM: không kill được từng agent, không biết agent nào tốn bao nhiêu, không dừng lại được giữa chừng để trả lời câu hỏi, và không sống sót qua crash.

E2 đưa việc điều phối ra ngoài session: một engine trong app đọc định nghĩa pipeline, spawn từng agent thành **process riêng** qua Claude Code headless, đọc luồng output để cập nhật trạng thái, và cho người dùng can thiệp — pause, kill, retry, hoặc trả lời khi agent hỏi.

Điểm khó nhất không phải là spawn process. Đó là **human-in-the-loop**: kit cố tình thiết kế agent để **dừng lại hỏi** khi thiếu thông tin (`POLICIES.md` §1 "Không đoán mò"). Chạy tự động mà không có ai trả lời thì agent hoặc treo, hoặc vi phạm chính policy của nó. E2 phải làm cho việc hỏi-đáp giữa chừng hoạt động được, nếu không thì automation chỉ đang che giấu việc agent đoán bừa.

### Hai đầu vào của pipeline đều là thứ đã có sẵn

Pipeline này **không** bắt đầu từ trang giấy trắng. Cả hai đầu vào đều là tài sản người dùng đã có:

- **Stage ①** — người dùng **import một folder** chứa tài liệu dự án hoặc mô tả feature (tài liệu yêu cầu, biên bản họp, ảnh chụp màn hình, bảng tính). `ba-agent` đọc folder đó để **phân tích ra SPEC**, thay vì hỏi người dùng gõ lại từ đầu.
- **Stage ②c** — design **đã tồn tại trong Figma**. Agent phụ trách nhánh này không vẽ gì cả: nó hỏi URL selection của design, đọc qua Figma MCP đã cấu hình trong project, rồi **ghi ra một file phân tích design** cho các stage sau dùng.

Đây là chiều ngược với những gì `.claude/agents/designer-agent.md` mô tả (SPEC → Figma) — kit giả định greenfield, orchestrator cần brownfield. **Quyết định (14/08/2026, xem `ASSUMPTIONS-GAPS.md` B17):** thêm một agent **mới** vào kit, `design-analyst-agent`, chuyên trách chiều Figma → phân tích. `designer-agent` gốc **giữ nguyên**, không sửa — vẫn dùng được cho use case greenfield ở dự án khác. Đây là một **dependency mới của E2**: file `.claude/agents/design-analyst-agent.md` hiện **chưa tồn tại** trong kit và cần được thêm trước khi stage ②c chạy được (ngoài phạm vi sửa đổi của bộ SPEC này — xem `Out of Scope`).

## Actors & Preconditions

| Actor | Vai trò trong feature này |
|---|---|
| **BA** | Nhập yêu cầu ở stage ① (text hoặc file đính kèm), trả lời câu hỏi của `ba-agent` |
| **PM** | Actor chính — khởi động pipeline, theo dõi, pause/kill/retry, trả lời clarification |
| **Tech Lead** | Trả lời clarification của `techlead-design-agent` (chọn approach khi có nhiều hướng) |
| **Dev (BE/FE/Mobile)** | Đọc log agent khi debug lỗi implement |

**Phạm vi repo:** single-repo (`E01`) — **không cần Contract Lock** cho chính feature này.

**Preconditions:**

- E1 đã hoàn tất: project đã mở, `config.json` có model + permission cho từng agent.
- Claude Code CLI có trên PATH và đã đăng nhập.
- Với stage ①: người dùng có sẵn một folder chứa tài liệu dự án hoặc mô tả feature.
- Với stage ②c: project đã khai MCP server phục vụ Figma (xem `AC-E1-26`), người dùng có quyền truy cập file Figma cần phân tích, và **`.claude/agents/design-analyst-agent.md` đã tồn tại trong kit** (xem "Mô tả nghiệp vụ" ở trên và `ASSUMPTIONS-GAPS.md` B17).
- Với stage ⑤ trở đi: repo đích phải ở trạng thái `đã clone` (xem `AC-E1-04`).
- **Đã quyết định (14/08/2026):** app điều phối **trực tiếp từng agent**, độc lập với `bmad-*.js` / `/create-feature`. Kit vẫn giữ nguyên `bmad-*.js` cho người dùng CLI thuần — app không gọi qua đó, không sửa đó. Xem `ASSUMPTIONS-GAPS.md` B14.

## Happy Path

1. PM mở project → Pipeline Board hiện 8 stage, tất cả `idle`.
2. PM bấm "Chạy mới" → màn hình **New Run / Import Input** (`OR_EXEC_001`).
3. BA **chọn một folder** trên máy — folder này chứa tài liệu mô tả dự án hoặc mô tả một feature cần phát triển (tài liệu yêu cầu, biên bản họp, ảnh chụp màn hình, bảng tính…). BA nhập tên feature (kebab-case) và có thể ghi thêm vài dòng bối cảnh.
4. App quét folder, hiện cây thư mục cùng danh sách file đọc được và file bỏ qua, để BA xác nhận đúng folder trước khi chạy.
5. App copy toàn bộ folder vào `inputs/<run-id>/` của project, tạo run id, ghi vào `state.json`.
6. App spawn `ba-agent` — process riêng, `cwd` = agents root, truyền `--model opus` theo `config.json`, và chỉ cho agent đường dẫn folder đã import để **phân tích ra SPEC**.
7. Log Console (`OR_EXEC_002`) hiện luồng output realtime: từng message, từng tool call agent gọi, thời gian chạy, cost cộng dồn.
8. `ba-agent` đọc hết tài liệu trong folder, rồi **hỏi lại những gì tài liệu không nói rõ**. App phát hiện agent đang chờ người trả lời → chuyển node sang `waiting-input`, hiện notification + ô nhập.
9. BA đọc câu hỏi trong Log Console, gõ câu trả lời, bấm gửi. App gửi tiếp vào cùng session của agent đó.
10. `ba-agent` viết xong `SPEC.md`, process kết thúc. App ghi cost + session id vào `state.json`, node chuyển `done`.
11. Stage ① xong → pipeline dừng ở **Trigger gate** (thuộc E4). PM duyệt.
12. Sau khi duyệt, app spawn **3 agent song song** cho stage ②: `techlead-design-agent`, `design-analyst-agent`, `qc-agent`. Ba node cùng chạy, mỗi node một Log Console riêng.
13. `design-analyst-agent` **không đọc SPEC để vẽ Figma**. Nó hỏi ngay: "cho tôi URL selection của design cần phân tích". Node chuyển `waiting-input`.
14. BA mở Figma, copy URL của page hoặc feature tương ứng, dán vào ô nhập trong Log Console.
15. `design-analyst-agent` gọi **Figma MCP đã cấu hình trong project** để đọc design tại URL đó, rồi ghi ra `design-analysis.md` trong folder feature. Node chuyển `done`.
16. Cả 3 nhánh xong → app spawn `techlead-tasks-agent` (stage ③), rồi `pm-agent`. Hai agent này dùng `design-analysis.md` làm đầu vào cùng với `DESIGN.md`.
17. Stage ④ Contract Lock (E4) chặn lại. Sau khi lock, app spawn `backend-agent`.
18. `backend-agent` xong → app spawn `frontend-agent` và `mobile-agent` **song song**, mỗi agent chạy trong **git worktree riêng** của repo tương ứng.
19. Stage ⑥ `qa-agent`, stage ⑦ `qc-agent` ∥ `qc-automation-agent` song song.
20. Pipeline hoàn tất → Pipeline Board hiện toàn bộ 8 stage `done`, tổng cost hiển thị ở footer.

### Định nghĩa pipeline

Pipeline khai báo dạng DAG trong `.orchestrator/pipeline.json`. v1 dùng template chuẩn 8 stage theo sơ đồ trong `README.md` của kit:

| Stage | Agent | Quy tắc chạy |
|---|---|---|
| ① Input | `ba-agent` | Tuần tự. Đầu vào là **folder tài liệu đã import**, không phải mô tả tự do |
| ② Design | `techlead-design-agent` ∥ `design-analyst-agent` ∥ `qc-agent` | 3 nhánh song song, cùng bắt đầu sau khi Trigger gate mở. Nhánh Design-Analyst **luôn** dừng hỏi URL Figma trước khi làm việc |
| ③ Planning | `techlead-tasks-agent` → `pm-agent` | Tuần tự |
| ④ Contract Lock | — (gate, thuộc E4) | Chặn |
| ⑤ Build | `backend-agent` → (`frontend-agent` ∥ `mobile-agent`) → integration | BE xong mới tới FE/Mobile |
| ⑥ Verify | `qa-agent` | Tuần tự, per task |
| ⑦ Testing | `qc-agent` ∥ `qc-automation-agent` | Song song, sau khi QA PASS |
| ⑧ Deploy | — | Chỉ hiển thị checklist |

`pipeline.json` khai báo **tường minh** agent nào thuộc stage nào — app không suy diễn từ tên file agent. Lý do: kit đang có 3 hệ đánh số stage khác nhau, mapping không 1-1 (xem `ASSUMPTIONS-GAPS.md` B8).

## Alternative Flows & Edge Cases

| # | Tình huống | Hành vi mong đợi |
|---|---|---|
| AF-1 | Agent hỏi người dùng giữa chừng | Node → `waiting-input`, hiện ô nhập, **không** tự trả lời, **không** tự bỏ qua |
| AF-2 | Agent ở `waiting-input` quá lâu | Không tự huỷ. Giữ nguyên trạng thái cho tới khi người dùng trả lời hoặc kill thủ công |
| AF-3 | Agent thoát với mã lỗi khác 0 | Node → `failed`, giữ nguyên toàn bộ log, hiện nút Retry và Skip |
| AF-4 | Agent chạy quá timeout (mặc định 30 phút, chỉnh được per agent) | Kill process, node → `failed`, ghi rõ nguyên nhân là timeout chứ không phải lỗi agent |
| AF-5 | PM bấm Retry | Spawn lại agent đó với cùng input; số lần retry tối đa mặc định 2, vượt thì nút Retry bị vô hiệu |
| AF-6 | PM bấm Skip | Node → `skipped (manual)`, pipeline chạy tiếp stage sau. Trạng thái này hiển thị khác `done` |
| AF-7 | PM bấm Kill khi agent đang chạy | Process bị dừng, node → `failed`, log giữ nguyên tới thời điểm bị kill |
| AF-8 | Một trong 3 nhánh song song stage ② fail | Hai nhánh còn lại **chạy tiếp tới hết**. Stage ② chỉ `done` khi cả 3 xong; nhánh fail chặn việc mở stage ③ |
| AF-9 | `mobile-agent` được spawn nhưng project không có repo vai trò mobile | App **không spawn**. Node → `skipped (không áp dụng)`, ghi lý do |
| AF-10 | Repo đích ở trạng thái `chưa clone` | App chặn **trước khi spawn**, node → `blocked`, ghi rõ repo nào thiếu. Đây là trạng thái khác `failed` |
| AF-11 | Hai agent cùng ghi vào một repo ở stage ⑤ | Mỗi agent chạy trên **git worktree riêng**, merge sau. Bật/tắt được trong Settings, mặc định bật cho stage ⑤ |
| AF-12 | Merge worktree bị conflict | Không tự merge. Node → `waiting-input`, hiện danh sách file conflict để người dùng xử lý ngoài app |
| AF-13 | Claude Code CLI không có trên PATH | Báo lỗi ngay khi bấm "Chạy mới", không tạo run rỗng |
| AF-14 | App bị đóng khi agent đang chạy | Xem E6 — agent đang chạy được đánh dấu `interrupted`, không mất log đã ghi |
| AF-15 | Folder import rỗng, hoặc chỉ chứa file không đọc được | Báo lỗi tại chỗ, không copy vào `inputs/`, không tạo run |
| AF-16 | Log dài hàng chục nghìn dòng | Log Console vẫn cuộn mượt (virtualized), không đóng băng UI |
| AF-17 | Folder import chứa file nhị phân / định dạng lạ | Liệt kê trong danh sách bỏ qua kèm lý do, vẫn chạy tiếp với phần đọc được |
| AF-18 | Folder import chứa file nhạy cảm (`.env`, keystore, `.pem`) | **Loại khỏi bản copy**, liệt kê trong danh sách bỏ qua. Agent không bao giờ nhìn thấy các file này |
| AF-19 | Folder import rất lớn (hàng nghìn file) | Cảnh báo kích thước và số file trước khi copy, cho người dùng xác nhận hoặc chọn folder hẹp hơn |
| AF-20 | Folder import chứa symlink trỏ ra ngoài | Không đi theo symlink; liệt kê trong danh sách bỏ qua |
| AF-21 | Project không khai MCP nào phục vụ Figma | Nhánh Design-Analyst → `blocked`, **không spawn**. Hai nhánh còn lại của stage ② vẫn chạy bình thường |
| AF-22 | Figma MCP là loại local http nhưng Figma Desktop chưa mở | Agent hỏng khi gọi MCP → node `failed` kèm gợi ý mở Figma Desktop rồi Retry |
| AF-23 | Người dùng dán URL Figma sai hoặc không có quyền truy cập | Agent quay lại `waiting-input` để nhập URL khác, không tự bỏ qua |
| AF-24 | Design cần phân tích trải trên nhiều URL | Người dùng dán nhiều URL trong cùng một câu trả lời; agent phân tích tất cả vào một `design-analysis.md` |
| AF-25 | `design-analysis.md` đã tồn tại từ lần chạy trước | Cảnh báo sẽ ghi đè, cho người dùng xác nhận trước khi chạy lại nhánh Design-Analyst |
| AF-26 | `.claude/agents/design-analyst-agent.md` chưa tồn tại trong kit | Nhánh Design-Analyst → `blocked` ngay từ đầu, thông báo nêu rõ thiếu file agent — khác với AF-21 (thiếu MCP) |

## Acceptance Criteria

**Định nghĩa & điều phối pipeline**

- **AC-E2-01** — `.orchestrator/pipeline.json` khai báo tường minh, với mỗi stage: mã stage, danh sách agent, và stage phụ thuộc. App đọc file này để quyết định thứ tự chạy — không suy diễn từ tên file agent.
- **AC-E2-02** — Ba agent của stage ② (`techlead-design-agent`, `design-analyst-agent`, `qc-agent`) được spawn **đồng thời** — cả ba đều ở trạng thái `running` cùng lúc, quan sát được trên Pipeline Board.
- **AC-E2-03** — Ở stage ⑤, `frontend-agent` và `mobile-agent` chỉ được spawn **sau khi** `backend-agent` kết thúc với trạng thái `done`.
- **AC-E2-04** — Ở stage ⑦, `qc-agent` và `qc-automation-agent` được spawn đồng thời sau khi stage ⑥ đạt `done`.
- **AC-E2-05** — Một stage chỉ đạt `done` khi **tất cả** agent thuộc stage đó đạt `done` hoặc `skipped`. Còn một agent `failed` hoặc `blocked` thì stage không `done` và stage kế tiếp không được spawn.

**Chạy agent**

- **AC-E2-06** — Mỗi agent chạy trong một process **riêng biệt**, spawn qua Claude Code ở chế độ headless với model lấy từ `config.json` (`AC-E1-12`).
- **AC-E2-07** — Log Console hiển thị realtime, trong lúc agent còn đang chạy: nội dung agent trả về, các tool call agent gọi, thời gian đã chạy, và cost cộng dồn. Không phải chờ agent kết thúc mới thấy.
- **AC-E2-08** — Khi agent kết thúc, app ghi vào `state.json`: trạng thái cuối, session id, cost, thời điểm bắt đầu và kết thúc.
- **AC-E2-09** — Nút Kill dừng được process của một agent cụ thể mà không ảnh hưởng các agent khác đang chạy song song.
- **AC-E2-10** — Agent vượt timeout bị kill tự động và trạng thái ghi rõ nguyên nhân là **timeout**, phân biệt được với lỗi do agent trả về.
- **AC-E2-11** — Trước khi spawn bất kỳ agent nào nhắm vào một repo, app kiểm tra repo đó đã clone chưa. Chưa clone thì **không spawn**, node → `blocked`, thông báo nêu đích danh repo còn thiếu.
- **AC-E2-12** — Agent nhắm vào vai trò repo mà project không có (vd `mobile-agent` khi không có repo mobile) được đánh dấu `skipped (không áp dụng)` và **không** bị spawn.
- **AC-E2-13** — Nút Retry spawn lại đúng agent đó với input ban đầu. Sau số lần retry tối đa theo cấu hình (mặc định 2), nút Retry bị vô hiệu hoá.
- **AC-E2-14** — Trạng thái `skipped (manual)` hiển thị khác biệt rõ ràng với `done` trên Pipeline Board — người xem phân biệt được stage nào thực sự chạy và stage nào bị bỏ qua.

**Clarification loop (human-in-the-loop)**

- **AC-E2-15** — Khi agent kết thúc lượt mà **chưa tạo ra artifact được mong đợi** và nội dung trả về là câu hỏi cho người dùng, app chuyển node sang `waiting-input` thay vì đánh dấu `done` hoặc `failed`.
- **AC-E2-16** — Ở trạng thái `waiting-input`, app hiển thị thông báo cho người dùng và một ô nhập câu trả lời ngay trong Log Console.
- **AC-E2-17** — Câu trả lời của người dùng được gửi tiếp vào **cùng session** của agent đó (agent giữ nguyên ngữ cảnh đã có, không phải chạy lại từ đầu).
- **AC-E2-18** — App **không bao giờ** tự sinh câu trả lời thay người dùng, và không tự chuyển agent sang stage kế tiếp khi đang ở `waiting-input`.
- **AC-E2-19** — Một agent có thể vào `waiting-input` nhiều lần trong một lượt chạy; mỗi lần đều hoạt động như AC-E2-16 đến AC-E2-18.
- **AC-E2-20** — Toàn bộ cặp câu hỏi–câu trả lời được ghi vào log của run, đọc lại được sau khi agent kết thúc.

**Nhập đầu vào stage ① — import folder**

- **AC-E2-21** — Màn hình Import Input yêu cầu người dùng **chọn một folder** trên máy làm nguồn đầu vào. Không chọn folder thì không tạo được run.
- **AC-E2-22** — Sau khi chọn folder, app hiển thị cây thư mục kèm danh sách **file sẽ đọc** và **file bị bỏ qua** (kèm lý do bỏ qua), để người dùng xác nhận trước khi chạy.
- **AC-E2-23** — Toàn bộ folder được copy vào `inputs/<run-id>/` của project trước khi spawn agent, và đường dẫn folder đã copy được đưa vào prompt của `ba-agent`.
- **AC-E2-24** — Import Input yêu cầu nhập tên feature dạng kebab-case; không nhập hoặc sai định dạng thì không tạo được run.

**Chạy song song trên cùng repo**

- **AC-E2-25** — Khi bật chế độ worktree (mặc định bật cho stage ⑤), mỗi agent ghi vào cùng một repo được chạy trong một git worktree riêng.
- **AC-E2-26** — Merge worktree bị conflict thì app **không tự giải quyết**; node → `waiting-input` kèm danh sách file conflict.

**Hiệu năng & bền bỉ**

- **AC-E2-27** — Log Console cuộn mượt và không đóng băng UI với log từ 50.000 dòng trở lên.
- **AC-E2-28** — Không tìm thấy Claude Code CLI thì app báo lỗi ngay tại thao tác "Chạy mới" và không tạo run rỗng trong `state.json`.

**Import folder — chi tiết bổ sung**

- **AC-E2-29** — Người dùng nhập thêm được vài dòng bối cảnh kèm folder; phần này là **tuỳ chọn**, để trống vẫn chạy được.
- **AC-E2-30** — Folder rỗng hoặc không có file nào ở định dạng đọc được thì app báo lỗi tại chỗ, **không** copy vào `inputs/` và **không** tạo run.
- **AC-E2-31** — App đọc folder ở chế độ **chỉ đọc** — folder gốc do người dùng chọn không bị sửa đổi hay di chuyển.
- **AC-E2-32** — File trong folder khớp các pattern bị cấm đọc theo `.claude/rules/SECURITY.md` (`.env`, keystore, `.p12`, `.pem`…) bị **loại khỏi bản copy**, và được liệt kê trong danh sách bỏ qua kèm lý do.

**Nhánh Design-Analyst stage ②c — phân tích design có sẵn**

- **AC-E2-33** — Trước khi spawn `design-analyst-agent`, app kiểm tra project có MCP server phục vụ Figma hay không (theo `AC-E1-26`). Không có thì node chuyển `blocked` kèm lý do, và app **không** spawn agent.
- **AC-E2-34** — `design-analyst-agent` khi được spawn sẽ chuyển sang `waiting-input` để hỏi **URL selection của design**, trước khi thực hiện bất kỳ việc gì khác.
- **AC-E2-35** — Người dùng dán URL Figma vào ô nhập trong Log Console; app gửi vào cùng session của agent theo đúng cơ chế clarification loop (`AC-E2-17`).
- **AC-E2-36** — Sau khi nhận URL, `design-analyst-agent` đọc design qua Figma MCP **của project** và ghi ra file phân tích design tại `<DOCS_ROOT>/features/<feature>/design-analysis.md`.
- **AC-E2-37** — Nhánh Design-Analyst chỉ đạt `done` khi `design-analysis.md` tồn tại. Agent kết thúc mà không sinh ra file này thì node chuyển `failed`.
- **AC-E2-38** — URL không hợp lệ hoặc Figma MCP không đọc được nội dung thì agent quay lại `waiting-input` để người dùng nhập URL khác — app **không** tự đoán URL và **không** bỏ qua bước này.
- **AC-E2-39** — `design-analysis.md` được đưa vào ngữ cảnh của `techlead-tasks-agent` và `pm-agent` ở stage ③.
- **AC-E2-40** — File `.claude/agents/design-analyst-agent.md` không tồn tại trong kit thì app phát hiện được điều này khi liệt kê agent (liên kết `AC-E1-08`) và hiển thị cảnh báo rõ ràng "thiếu agent `design-analyst-agent`" thay vì lỗi chung chung khi spawn thất bại.

## Out of Scope

- **Chỉnh sửa nội dung prompt của agent từ trong app** — prompt sinh ra từ `.claude/agents/`, app chỉ đọc.
- **Sửa `pipeline.json` bằng UI** — v1 dùng template chuẩn; muốn đổi DAG thì sửa file bằng editor ngoài.
- **Chạy nhiều pipeline run song song trên cùng project** — v1 một run tại một thời điểm.
- **Tự giải quyết merge conflict của worktree** — chỉ phát hiện và báo.
- **Chạy stage ⑧ Deploy** — chỉ hiển thị checklist, không gọi CI/CD.
- **Cost tracking chi tiết và export** — thuộc E6; E2 chỉ hiển thị cost cộng dồn realtime.
- **Resume sau khi app crash** — thuộc E6.
- **Gate approve/reject** — thuộc E4; E2 chỉ dừng pipeline lại tại điểm gate.
- **Tạo hoặc sửa design trong Figma** — `design-analyst-agent` chỉ **đọc** design có sẵn và viết file phân tích. App không ghi ngược vào Figma.
- **Tự tìm URL Figma tương ứng với feature** — người dùng phải cung cấp URL; app không dò, không đoán.
- **Chuẩn hoá nội dung folder import** — app copy nguyên trạng (trừ file bị loại theo `AC-E2-32`), việc diễn giải là của `ba-agent`.
- **OCR ảnh hoặc trích xuất nội dung file nhị phân trong folder import** — app chỉ liệt kê; khả năng đọc tới đâu phụ thuộc agent.
- **Viết file `.claude/agents/design-analyst-agent.md`** — đây là công việc bổ sung vào kit, thuộc trách nhiệm Tech Lead của kit, không phải của bộ SPEC orchestrator này. E2 chỉ giả định agent đó tồn tại và mô tả cách app tương tác với nó (`AC-E2-33` đến `AC-E2-40`).
- **Sửa `bmad-plan-phase.js` / `bmad-build-phase.js`** — app không gọi và không đụng tới hai file này (xem Preconditions).

## Screens

| Screen Code | Screen | Actor | App | Screen Type | Mô tả ngắn | Figma Link |
|---|---|---|---|---|---|---|
| `OR_EXEC_001` | New Run / Import Input | BA | E01* | Form | Chọn folder tài liệu đầu vào, xem cây thư mục + danh sách file đọc được / bị bỏ qua, nhập tên feature và bối cảnh bổ sung, khởi động stage ① | |
| `OR_EXEC_002` | Agent Detail / Log Console | PM | E01* | Detail | Log stream realtime của một agent (message, tool call, cost, thời gian), nút Pause/Kill/Retry, ô nhập trả lời khi agent hỏi | |

> `*` Cột **App** = Epic code của repo đích. Bảng Ecosystem trong `AGENTS.md` của kit hiện còn placeholder, nên `E01` là giá trị **tạm** cho repo desktop app — cần xác nhận lại khi khởi tạo repo thật.
