# SPEC: Orchestrator — Monitoring & Artifacts

> EPIC **E3** của sản phẩm Agent Pipeline Orchestrator. Bối cảnh sản phẩm, data model `.orchestrator/`, non-functional dùng chung → `docs/orchestrator/OVERVIEW.md`. Giả định chưa giải quyết → `docs/orchestrator/ASSUMPTIONS-GAPS.md`.
>
> Nguồn: `SPEC-pipeline-orchestrator.md` v0.1 §F3.1–F3.3.

## Mô tả nghiệp vụ

Kit vận hành theo nguyên tắc **stateless** (`POLICIES.md` §1): mỗi session độc lập, mọi ngữ cảnh phải đọc lại từ file `.md`. Hệ quả là **file system chính là trạng thái của pipeline** — không có database, không có state server. Muốn biết một feature đang ở đâu, hôm nay người ta phải tự đi mở từng thư mục xem `SPEC.md` có chưa, `DESIGN.md` có chưa, `tasks/` có file nào chưa.

E3 giữ nguyên nguyên tắc đó nhưng tự động hoá việc quan sát: một watcher đọc file system liên tục, suy ra trạng thái từng stage, và vẽ nó lên một bảng nhìn một cái là biết pipeline đang ở đâu. Đây là phần chạy được **mà không cần chạy agent nào** — nên nó cũng là phần được làm trước tiên (MVP 1), và là phép thử xem giả định "file system là source of truth" có thật sự đứng vững không.

Việc suy ra trạng thái không đơn giản như "file tồn tại = stage xong". Hai chỗ đặc biệt:

- QA Report và QC execution checklist **không có path quy định** trong kit — không có gì để watch. App tự định nghĩa vị trí cho chúng trong `.orchestrator/runs/`.
- Nhánh Design-Analyst trong luồng của orchestrator (`design-analyst-agent`, agent mới — xem E2 và `ASSUMPTIONS-GAPS.md` B17) sinh ra `design-analysis.md`, **khác** với `designer-agent` gốc của kit vốn không tạo file `.md` nào. Nhờ vậy watcher có file thật để theo dõi.

Ngoài quan sát, E3 còn phải trả lời được câu hỏi "artifact này thay đổi gì so với lần trước" — nền tảng cho phần diff của gate ở E4.

## Actors & Preconditions

| Actor | Vai trò trong feature này |
|---|---|
| **PM** | Actor chính — nhìn Pipeline Board để biết tiến độ, mở artifact xem chi tiết |
| **BA** | Đọc `SPEC.md` render đẹp, xem diff giữa các phiên bản sau khi sửa |
| **Tech Lead** | Đọc `DESIGN.md`, xem sơ đồ mermaid, lần theo traceability từ task ngược lên SPEC |
| **Dev (BE/FE/Mobile)** | Mở task file, lần theo link tới SPEC và test case liên quan |

**Phạm vi repo:** single-repo (`E01`) — **không cần Contract Lock** cho chính feature này.

**Preconditions:**

- E1 đã hoàn tất: project đã mở, DOCS_ROOT đã xác định.
- Project có ít nhất một feature folder trong `<DOCS_ROOT>/features/`.
- Với diff dựa trên git: project (hoặc docs repo) là git repository. Không phải git thì dùng snapshot.
- E3 **không phụ thuộc E2** — chạy được ở chế độ read-only, chỉ quan sát artifact do người/agent tạo ra ngoài app.

## Happy Path

1. PM mở project → app quét `<DOCS_ROOT>/features/` một lượt, dựng trạng thái ban đầu cho mọi feature tìm thấy.
2. App mở **Pipeline Board** (`OR_MONI_001`) — 8 cột stage, mỗi node hiển thị tên agent + trạng thái.
3. Với feature `login`: `SPEC.md` đã có → stage ① `done`; `design-analysis.md` đã có → nhánh Design-Analyst của stage ② `done`. `DESIGN.md` chưa có → nhánh Tech Lead `idle`.
4. PM chạy `/create-design` **bên ngoài app** trong terminal. Agent ghi `DESIGN.md`.
5. Watcher phát hiện file mới trong vòng dưới 1 giây → node Tech Lead của stage ② tự chuyển `done` trên Pipeline Board mà PM không phải refresh.
6. PM bấm vào node → panel chi tiết mở ra: danh sách artifact node đó sinh ra, thời gian, cost (nếu chạy qua app).
7. PM bấm vào `DESIGN.md` → mở **Artifact Viewer** (`OR_MONI_002`): markdown render đẹp, sơ đồ mermaid trong đó vẽ ra thành hình.
8. PM bấm "So sánh phiên bản" → chọn 2 mốc → app hiện diff side-by-side, phần thêm/xoá tô màu.
9. PM mở `task-3-1.md`, bấm tab **Traceability** → app hiện: ngược lên `SPEC.md` (mục AC liên quan), xuôi xuống test case và bug report khớp ID.
10. Với một task khác, app không tìm được liên kết nào → hiện "chưa đủ dữ liệu để liên kết", **không** đoán bừa.

### Quy tắc suy ra trạng thái stage

| Stage | Tín hiệu `done` |
|---|---|
| ① Input | `<feature>/SPEC.md` tồn tại và có đủ 7 section bắt buộc |
| ② Design — Tech Lead | Có ít nhất một `<feature>/<repo>/DESIGN.md` |
| ② Design — Design-Analyst | `<feature>/design-analysis.md` tồn tại |
| ② Design — QC | `<feature>/test-cases/<module>/test-cases.md` tồn tại |
| ③ Planning | Có ít nhất một `<feature>/<repo>/tasks/task-*.md`; `PLAN.md` tồn tại là tín hiệu bổ sung |
| ④ Contract Lock | `.orchestrator/contract.lock` tồn tại và hợp lệ (chi tiết ở E4) |
| ⑤ Build | Trạng thái lấy từ `state.json` của run — không suy từ source code |
| ⑥ Verify | QA Report tồn tại tại path do app quy định |
| ⑦ Testing | QC checklist và/hoặc `execution-report.md` tồn tại |
| ⑧ Deploy | Không tự suy — người dùng tự tick checklist |

## Alternative Flows & Edge Cases

| # | Tình huống | Hành vi mong đợi |
|---|---|---|
| AF-1 | Agent ghi file liên tục nhiều lần trong 1 giây | Debounce — app chỉ cập nhật trạng thái một lần, không nhấp nháy UI |
| AF-2 | `SPEC.md` tồn tại nhưng thiếu section bắt buộc | Stage ① hiện `done (chưa đầy đủ)` kèm danh sách section còn thiếu — khác với `done` |
| AF-3 | `design-analysis.md` tồn tại nhưng rỗng hoặc quá ngắn | Hiện `done (chưa đầy đủ)` kèm cảnh báo, để người dùng tự quyết chạy lại nhánh Design-Analyst |
| AF-4 | Project không khai MCP Figma nên nhánh Design-Analyst bị `blocked` | Hiện `blocked` kèm lý do; hai nhánh còn lại của stage ② vẫn hiển thị tiến độ bình thường |
| AF-5 | File bị xoá sau khi đã ghi nhận `done` | Trạng thái quay lại `idle`, hiện cảnh báo artifact đã biến mất |
| AF-6 | Nhiều feature cùng tồn tại trong `<DOCS_ROOT>/features/` | Pipeline Board hiển thị một feature tại một thời điểm, có bộ chọn feature |
| AF-7 | Artifact chứa mermaid sai cú pháp | Hiện nguyên khối code kèm thông báo lỗi cú pháp, **không** làm hỏng phần render còn lại |
| AF-8 | Project không phải git repository | Diff dùng snapshot trong `.orchestrator/snapshots/`; UI nói rõ đang so sánh theo snapshot |
| AF-9 | Chưa có snapshot hoặc chưa có commit nào để so | Nút "So sánh phiên bản" bị vô hiệu kèm giải thích lý do |
| AF-10 | Task file không match được ID nào trong SPEC hay test case | Tab Traceability hiện "chưa đủ dữ liệu để liên kết", nêu rõ đã tìm theo quy ước nào |
| AF-11 | Thư mục `<DOCS_ROOT>/features/` rỗng | Pipeline Board hiện trạng thái rỗng kèm hướng dẫn tạo feature đầu tiên |
| AF-12 | Watcher mất kết nối với file system (thư mục bị unmount) | Hiện cảnh báo, giữ nguyên trạng thái cuối cùng, tự kết nối lại khi thư mục quay lại |
| AF-13 | Artifact rất lớn (hàng nghìn dòng markdown) | Viewer vẫn cuộn mượt, không đóng băng UI |

## Acceptance Criteria

**File watcher**

- **AC-E3-01** — App theo dõi liên tục các artifact trong `<DOCS_ROOT>/features/<feature>/`: `SPEC.md`, `PLAN.md`, `design-analysis.md`, `<repo>/DESIGN.md`, `<repo>/tasks/`, `test-cases/`, cùng với `.orchestrator/contract.lock`.
- **AC-E3-02** — Thay đổi trên file system được phản ánh lên Pipeline Board **trong vòng 2 giây** mà người dùng không phải refresh thủ công.
- **AC-E3-03** — Nhiều thay đổi liên tiếp trong khoảng dưới 500ms chỉ tạo ra **một** lần cập nhật trạng thái (debounce) — UI không nhấp nháy.
- **AC-E3-04** — Trạng thái nhánh Design-Analyst của stage ② được xác định bằng **sự tồn tại của `design-analysis.md`** trong folder feature.
- **AC-E3-05** — Với các artifact mà kit không quy định đường dẫn (QA Report, QC execution checklist), app ghi chúng vào vị trí do app tự định nghĩa trong `.orchestrator/runs/<run-id>/` và theo dõi tại đó.
- **AC-E3-06** — Artifact bị xoá sau khi đã ghi nhận `done` khiến trạng thái stage quay về `idle` kèm cảnh báo nêu tên file đã biến mất.
- **AC-E3-07** — Thư mục theo dõi tạm thời không truy cập được thì app hiện cảnh báo và giữ nguyên trạng thái cuối cùng, tự động theo dõi lại khi thư mục khả dụng trở lại — app không crash.

**Pipeline Board**

- **AC-E3-08** — Pipeline Board hiển thị đủ 8 stage, mỗi stage hiện các agent thuộc stage đó theo `pipeline.json`.
- **AC-E3-09** — Mỗi node hiển thị một trong các trạng thái: `idle`, `running`, `waiting-input`, `done`, `failed`, `blocked`, `skipped`. Mỗi trạng thái phân biệt được bằng mắt thường (màu và/hoặc icon khác nhau).
- **AC-E3-10** — Trạng thái stage được suy ra đúng theo bảng "Quy tắc suy ra trạng thái stage" trong SPEC này.
- **AC-E3-11** — `SPEC.md` tồn tại nhưng thiếu section bắt buộc thì stage ① hiện `done (chưa đầy đủ)` kèm danh sách section còn thiếu — trạng thái này phân biệt được với `done`.
- **AC-E3-12** — `design-analysis.md` chưa tồn tại thì nhánh Design-Analyst hiện `idle` hoặc `running` tuỳ trạng thái agent trong `state.json`; app **không** suy trạng thái nhánh này từ cột `Figma Link` trong `SPEC.md`.
- **AC-E3-13** — Bấm vào một node mở panel chi tiết liệt kê: artifact node đó sinh ra (kèm đường dẫn bấm được), thời gian chạy, và cost nếu agent chạy qua app.
- **AC-E3-14** — Khi `<DOCS_ROOT>/features/` có nhiều feature, Pipeline Board có bộ chọn feature và hiển thị đúng một feature tại một thời điểm.
- **AC-E3-15** — Pipeline Board là màn hình mặc định sau khi mở project thành công.

**Artifact Viewer**

- **AC-E3-16** — Artifact Viewer render markdown của `SPEC.md`, `DESIGN.md`, `PLAN.md`, task file và test case với định dạng đọc được (heading, bảng, danh sách, khối code).
- **AC-E3-17** — Khối mermaid trong artifact được vẽ thành sơ đồ.
- **AC-E3-18** — Mermaid sai cú pháp được hiện dưới dạng khối code nguyên văn kèm thông báo lỗi; phần còn lại của tài liệu vẫn render bình thường.
- **AC-E3-19** — Artifact từ 2.000 dòng trở lên vẫn cuộn mượt, không đóng băng UI.

**Diff**

- **AC-E3-20** — Người dùng chọn được 2 phiên bản của cùng một artifact và xem diff side-by-side, phần thêm và phần xoá được tô màu phân biệt.
- **AC-E3-21** — Project là git repository thì phiên bản lấy từ lịch sử git; không phải git thì lấy từ `.orchestrator/snapshots/`. UI hiển thị rõ đang dùng nguồn nào.
- **AC-E3-22** — Chưa có phiên bản nào để so sánh thì chức năng diff bị vô hiệu hoá kèm giải thích lý do, thay vì hiện diff rỗng.

**Traceability**

- **AC-E3-23** — Từ một task file, app hiển thị được liên kết ngược lên `SPEC.md` và xuôi xuống test case / bug report khi ID trong các artifact khớp theo quy ước của kit.
- **AC-E3-24** — Không tìm được liên kết nào thì app hiển thị "chưa đủ dữ liệu để liên kết" kèm quy ước ID đã dùng để tìm. App **không** suy đoán liên kết dựa trên độ tương đồng tên file hay nội dung.

## Out of Scope

- **Sửa artifact từ trong app** — Artifact Viewer chỉ đọc. Muốn sửa thì dùng editor ngoài hoặc chạy lại agent.
- **Tự chuẩn hoá ID artifact** — dữ liệu hiện có chưa đủ nhất quán (xem `ASSUMPTIONS-GAPS.md` A2); chuẩn hoá là việc của kit, không phải app.
- **Suy ra trạng thái stage ⑤ Build từ source code** — trạng thái build lấy từ `state.json`, app không phân tích code.
- **Tự tick checklist stage ⑧ Deploy** — người dùng tự tick.
- **Diff cho file nhị phân / hình ảnh** — chỉ diff văn bản.
- **Theo dõi nhiều project cùng lúc** — v1 một project tại một thời điểm.
- **Gọi Figma MCP để kiểm chứng nội dung `design-analysis.md`** — E3 chỉ theo dõi sự tồn tại của file; việc đọc Figma thuộc E2.
- **So sánh và diff của gate** — thuộc E4; E3 chỉ cung cấp cơ chế diff dùng chung.

## Screens

| Screen Code | Screen | Actor | App | Screen Type | Mô tả ngắn | Figma Link |
|---|---|---|---|---|---|---|
| `OR_MONI_001` | Pipeline Board | PM | E01* | Dashboard | Màn hình chính — 8 stage với trạng thái từng agent, bộ chọn feature, panel chi tiết khi bấm vào node | |
| `OR_MONI_002` | Artifact Viewer | BA | E01* | Detail | Render markdown + mermaid của SPEC/DESIGN/PLAN/task/test-case, so sánh 2 phiên bản, tab Traceability | |

> `*` Cột **App** = Epic code của repo đích. Bảng Ecosystem trong `AGENTS.md` của kit hiện còn placeholder, nên `E01` là giá trị **tạm** cho repo desktop app — cần xác nhận lại khi khởi tạo repo thật.
