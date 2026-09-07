# SPEC: Orchestrator — Gates

> EPIC **E4** của sản phẩm Dipro AI Boost. Bối cảnh sản phẩm, data model `.orchestrator/`, non-functional dùng chung → `docs/orchestrator/OVERVIEW.md`. Giả định chưa giải quyết → `docs/orchestrator/ASSUMPTIONS-GAPS.md`.
>
> Nguồn: `SPEC-pipeline-orchestrator.md` v0.1 §F4.1–F4.3.
>
> **Đây là EPIC giá trị cao nhất của sản phẩm.** Contract Lock là cơ chế chống rework số 1 mà kit đang mô tả nhưng chưa hề thực thi.

## Mô tả nghiệp vụ

Pipeline BMAD có hai điểm mà **con người phải quyết định**, không được để agent tự đi tiếp:

**Điểm 1 — sau khi BA viết xong SPEC.** SPEC sai thì mọi thứ phía sau sai theo: DESIGN sai, task sai, code sai, test case sai. `ba-agent` tự nhắc "chi phí clarify 2–5 phút, chi phí rework SPEC sai là 2 tuần fan-out toàn bộ pipeline".

**Điểm 2 — trước khi FE/Mobile bắt đầu code.** Backend đã định nghĩa API contract; Frontend và Mobile code dựa lên contract đó. Nếu contract đổi sau khi FE đã code, phần việc đó phải làm lại. `ai-agents-workflow.md` §5 liệt kê "FE code với endpoint không tồn tại" là một trong các failure mode phổ biến nhất.

Hôm nay cả hai điểm này **chỉ tồn tại dưới dạng chữ**:

- Trigger gate là một node hình thoi trong sơ đồ Mermaid ở `README.md` — thực chất chỉ để phân biệt "gõ natural language hay gõ slash command", không phải điểm duyệt.
- Contract Lock là bốn dòng `- [ ]` trong `.claude/workflows/new-feature.md`, và `.claude/workflows/bmad-build-phase.js` gọi thẳng `backend-agent` mà **không kiểm tra gì cả**.

Không có checksum, không có state, không có gì chặn được ai đó sửa `DESIGN.md` sau khi mọi người đã "đồng ý" contract.

E4 biến hai điểm này thành cơ chế thật. Trigger gate thành màn hình duyệt có diff và đường quay lại BA. Contract Lock thành một **file khoá có checksum**: khi duyệt, app băm nội dung các file contract và ghi lại; sau đó nếu bất kỳ file nào trong khoá bị sửa, app phát hiện ngay, chuyển pipeline sang trạng thái vi phạm và **chặn các agent stage ⑤ trở đi chưa chạy**. Người có thẩm quyền xem diff rồi quyết định: duyệt lại tạo khoá mới, hay hoàn tác thay đổi.

Ngoài hai gate cứng còn một gate mềm: Memory Update Gate. Kit yêu cầu dev agent cập nhật docs overview của repo sau mỗi task. App kiểm tra và **cảnh báo** nếu không thấy, nhưng không chặn — vì đây là kỷ luật tài liệu, không phải rủi ro kỹ thuật tức thời.

## Actors & Preconditions

| Actor | Vai trò trong feature này |
|---|---|
| **PM** | Actor chính — duyệt Trigger gate, chủ trì Contract Lock, quyết định khi có vi phạm |
| **BA** | Đọc SPEC tại Trigger gate, nhận yêu cầu chỉnh sửa nếu bị từ chối |
| **Tech Lead** | Xác nhận vai trò của mình tại Contract Lock |
| **Dev BE / FE / Mobile** | Xác nhận vai trò của mình tại Contract Lock — đây là cam kết "tôi đã đọc và hiểu contract" |
| **QC** | Xác nhận vai trò của mình tại Contract Lock |

**Phạm vi repo:** single-repo (`E01`) cho chính feature này — **không cần Contract Lock** để xây feature Contract Lock.

**Preconditions:**

- E2 đã hoàn tất: engine dừng được pipeline tại điểm gate.
- E3 đã hoàn tất: có cơ chế watcher và diff dùng chung.
- Với Trigger gate: `SPEC.md` đã được `ba-agent` tạo ra.
- Với Contract Lock: có ít nhất một `DESIGN.md` chứa bảng API Definition.

> **Giới hạn có chủ đích của v1:** app **không xác thực danh tính**. Việc "5 vai trò xác nhận" là 5 ô tick do **một người đang mở app** bấm. App chỉ ghi lại vai trò nào đã được tick và thời điểm. Multi-user nằm ngoài phạm vi v1.

## Happy Path

### Trigger gate ①

1. `ba-agent` chạy xong, ghi `SPEC.md`. Pipeline **tự dừng** — stage ② không được spawn.
2. Node stage ① chuyển `blocked-by-gate`. App hiện thông báo có gate đang chờ duyệt.
3. PM mở **Gate Review — Trigger** (`OR_GATE_001`): nội dung `SPEC.md` render đầy đủ, kèm checklist tự động về việc SPEC có đủ 7 section bắt buộc hay không.
4. PM đọc thấy phần Acceptance Criteria còn mơ hồ → bấm **Request changes**, gõ nhận xét cụ thể.
5. App gửi nhận xét vào **cùng session** của `ba-agent`, agent chạy tiếp và sửa `SPEC.md`.
6. Gate mở lại với `SPEC.md` đã sửa. Lần này màn hình có thêm **diff** so với phiên bản PM đã từ chối.
7. PM hài lòng → bấm **Approve**. App ghi lại người duyệt và thời điểm vào `state.json`.
8. Pipeline chạy tiếp: 3 agent của stage ② được spawn song song.

### Contract Lock ④

9. Stage ③ xong. App kiểm tra điều kiện mở gate: tìm thấy bảng API Definition trong `DESIGN.md` của repo backend, đủ các cột bắt buộc.
10. Node stage ④ chuyển `blocked-by-gate`. Pipeline dừng, stage ⑤ chưa được spawn.
11. PM mở **Gate Review — Contract Lock** (`OR_GATE_002`): bảng API Contract gộp từ mọi `DESIGN.md` — REST endpoints, WebSocket events, Push payload.
12. App liệt kê **danh sách file sẽ đưa vào khoá** kèm checksum hiện tại của từng file.
13. PM lần lượt tick 5 vai trò: BE, FE, Mobile, PM, QC. Thiếu một vai trò thì nút **Lock** vẫn mờ.
14. PM bấm **Lock**. App tính SHA-256 cho từng file trong danh sách và ghi `.orchestrator/contract.lock` gồm: danh sách file, checksum, thời điểm, người duyệt, các vai trò đã xác nhận.
15. Node stage ④ chuyển `done`. `backend-agent` được spawn.
16. Giữa lúc build, ai đó sửa `DESIGN.md` của backend — thêm một field vào response.
17. Watcher phát hiện checksum lệch với `contract.lock` → pipeline chuyển **`CONTRACT VIOLATION`** ngay lập tức.
18. App **chặn mọi agent stage ⑤ trở đi chưa được spawn**. Agent đang chạy dở không bị kill — nhưng agent kế tiếp không được khởi động.
19. Màn hình gate mở lại, hiện diff giữa nội dung tại thời điểm lock và nội dung hiện tại, nêu đích danh file nào lệch.
20. PM xem diff, thấy thay đổi là hợp lý → tick lại 5 vai trò → bấm **Re-lock**. App ghi `contract.lock` mới, giữ lại bản cũ trong lịch sử. Pipeline được giải phóng, các agent bị chặn tiếp tục chạy.

### Memory Update Gate ⑤ (gate mềm)

21. Một dev agent hoàn thành task. App kiểm tra các file overview của repo (`api-catalog.md`, `erd.md`, `patterns.md`, `structure.md`) có được đụng tới trong lượt chạy đó không.
22. Không thấy file nào thay đổi → app hiện **cảnh báo** trên node và trong panel chi tiết, kèm danh sách file lẽ ra nên cập nhật.
23. Pipeline **vẫn chạy tiếp** — đây là gate mềm, không chặn.

## Alternative Flows & Edge Cases

| # | Tình huống | Hành vi mong đợi |
|---|---|---|
| AF-1 | PM bấm Request changes nhưng để trống nhận xét | Không gửi được — bắt buộc nhập nội dung, vì agent cần biết sửa gì |
| AF-2 | `ba-agent` đã kết thúc session, không resume được | App báo rõ, cho chọn chạy lại `ba-agent` từ đầu với nhận xét kèm theo |
| AF-3 | Feature chỉ chạm **1 repo** | Theo `doc-structure.md`, Contract Lock **không bắt buộc**. App hiện gate ở trạng thái `không áp dụng`, cho bỏ qua, và ghi lý do vào `state.json` |
| AF-3a | Feature chạm ≥2 repo nhưng **không repo nào vai trò `backend`** (vd web + mobile), hoặc có backend nhưng **không repo nào tiêu thụ API** | Không có contract 2 chiều để khoá, và `techlead-design-agent` chỉ viết bảng API Definition trong DESIGN.md của repo backend nên bảng đó sẽ không bao giờ xuất hiện. Gate hiện `không áp dụng`, nêu tên repo trong scope |
| AF-3b | Thư mục con của feature không khớp repo nào trong bảng Ecosystem (`AGENTS.md` chưa điền, hoặc tên repo lạ) | Không suy ra vai trò được → app **giữ nguyên hành vi chặn**, không tự bỏ qua. Ecosystem trống không được phép tắt gate trên toàn project |
| AF-4 | Không tìm thấy bảng API Definition trong bất kỳ `DESIGN.md` nào | Gate **không mở được** — mặc định vẫn chặn. App nêu rõ thiếu gì và gợi ý yêu cầu `techlead-design-agent` bổ sung. Kèm nút **bỏ qua thủ công** (bắt buộc nhập tên + lý do) cho feature thật sự không thêm endpoint nào; bỏ qua được gỡ lại |
| AF-5 | Bảng API Definition có nhưng thiếu cột bắt buộc | Gate mở được nhưng hiện cảnh báo liệt kê cột còn thiếu; PM tự quyết có lock hay không |
| AF-6 | Chỉ tick được 4/5 vai trò vì dự án không có mobile | Vai trò không áp dụng được đánh dấu `không áp dụng` và không tính vào điều kiện đủ |
| AF-7 | File trong `contract.lock` bị **xoá** thay vì sửa | Cũng tính là vi phạm; app nêu rõ file đã biến mất |
| AF-8 | File bị sửa rồi sửa ngược về đúng nội dung cũ | Checksum khớp lại → trạng thái vi phạm **tự gỡ**, pipeline được giải phóng, sự kiện vẫn được ghi vào lịch sử |
| AF-9 | Vi phạm xảy ra khi đang có agent stage ⑤ chạy dở | Agent đang chạy **không bị kill**; chỉ chặn agent kế tiếp. Cảnh báo nêu rõ có agent đang chạy trên contract cũ |
| AF-10 | PM muốn hoàn tác thay đổi thay vì re-lock | App hiện diff và đường dẫn file để người dùng tự hoàn tác bên ngoài; app **không tự sửa file** |
| AF-11 | `contract.lock` bị sửa tay hoặc hỏng | App coi như không có khoá hợp lệ, chuyển stage ④ về `blocked-by-gate`, yêu cầu lock lại |
| AF-12 | Đã lock rồi, PM muốn xem lại contract đã khoá | Xem được nội dung tại thời điểm lock và toàn bộ lịch sử các lần lock trước |
| AF-13 | Repo overview docs không tồn tại (project chưa có thư mục overview) | Memory Update Gate hiện `không áp dụng`, không cảnh báo nhiễu |
| AF-14 | Người dùng đóng app khi đang ở màn hình gate | Trạng thái gate giữ nguyên; mở lại app vẫn thấy gate đang chờ, chưa duyệt |

## Acceptance Criteria

**Trigger gate ①**

- **AC-E4-01** — Sau khi `ba-agent` kết thúc với trạng thái `done`, pipeline **tự động dừng**: không agent nào của stage ② được spawn cho tới khi gate được duyệt.
- **AC-E4-02** — Màn hình Gate Review — Trigger hiển thị toàn bộ nội dung `SPEC.md` đã render, kèm checklist tự động cho biết `SPEC.md` có đủ 7 section bắt buộc hay không.
- **AC-E4-03** — Nút **Request changes** yêu cầu nhập nhận xét; để trống thì không gửi được.
- **AC-E4-04** — Nhận xét khi Request changes được gửi vào **cùng session** của `ba-agent`; agent giữ nguyên ngữ cảnh, không chạy lại từ đầu.
- **AC-E4-05** — Session của `ba-agent` không resume được thì app báo rõ và cho phép chạy lại agent từ đầu với nhận xét kèm theo — app không im lặng bỏ qua.
- **AC-E4-06** — Sau một vòng Request changes, lần mở gate tiếp theo hiển thị **diff** giữa phiên bản đã bị từ chối và phiên bản hiện tại.
- **AC-E4-07** — Bấm **Approve** ghi vào `state.json`: gate đã duyệt, người duyệt, thời điểm. Ngay sau đó 3 agent của stage ② được spawn.

**Điều kiện mở Contract Lock ④**

- **AC-E4-08** — Gate Contract Lock chỉ mở được khi tìm thấy bảng API Definition trong ít nhất một `DESIGN.md`. Không có bảng thì gate không mở được và app nêu rõ đang thiếu gì.
- **AC-E4-08a** — Khi gate ở trạng thái `not-ready` (`AC-E4-08`), màn hình liệt kê **đích danh đường dẫn** từng `DESIGN.md` đã kiểm tra và không tìm thấy bảng API Definition, kèm gợi ý hành động: yêu cầu `techlead-design-agent` bổ sung bảng vào các file đó (theo đúng nội dung AF-4).
- **AC-E4-10** — Bảng API Definition thiếu cột bắt buộc thì gate vẫn mở được nhưng hiển thị cảnh báo liệt kê đích danh các cột còn thiếu.
- **AC-E4-10a** — Cảnh báo cột thiếu ở `AC-E4-10` kèm gợi ý hành động: bổ sung các cột đó vào bảng API Definition trong `DESIGN.md` tương ứng.
- **AC-E4-11** — Feature chỉ chạm một repo thì gate hiển thị trạng thái `không áp dụng` và cho bỏ qua; lý do bỏ qua được ghi vào `state.json`.
- **AC-E4-11a** — Contract Lock chỉ áp dụng khi scope của feature có **ít nhất một repo vai trò `backend` VÀ ít nhất một repo vai trò `frontend`/`mobile`**. Thiếu một trong hai vế thì gate hiển thị `không áp dụng`, nêu đích danh các repo trong scope. Vai trò suy từ tên thư mục con của feature khớp với bảng Ecosystem trong `AGENTS.md`; **nếu còn thư mục con nào không khớp được repo nào thì luật này không áp dụng** và gate giữ nguyên hành vi chặn (AF-3b).
- **AC-E4-11b** — Ở trạng thái `not-ready` (`AC-E4-08`), PM bỏ qua gate được bằng thao tác thủ công, bắt buộc nhập **tên người bỏ qua** và **lý do**, có xác nhận 2 bước. Bỏ qua được lưu xuống đĩa (sống qua recompute và restart), làm gate chuyển `không áp dụng`, và **gỡ lại được** để gate chặn trở lại. Chỉ bỏ qua được từ `not-ready` — `chờ duyệt` thì hành động đúng là Lock, `đã khoá`/`vi phạm` thì đã có khoá thật phải tôn trọng.

**Xác nhận vai trò**

- **AC-E4-12** — Màn hình gate liệt kê 5 vai trò: BE, FE, Mobile, PM, QC — mỗi vai trò một ô xác nhận riêng.
- **AC-E4-13** — Nút **Lock** chỉ bật khi mọi vai trò **áp dụng được** đã được xác nhận. Còn một vai trò chưa tick thì nút vẫn mờ.
- **AC-E4-13a** — Khi nút Lock đang mờ vì thiếu xác nhận vai trò, màn hình hiển thị **đích danh** những vai trò áp dụng được nhưng chưa tick, đặt ngay cạnh nút Lock — không để nút mờ mà không giải thích.
- **AC-E4-14** — Vai trò tương ứng với repo mà project không có được đánh dấu `không áp dụng` và không tính vào điều kiện đủ.
- **AC-E4-15** — Màn hình nêu rõ v1 không xác thực danh tính — các ô xác nhận là ghi nhận vai trò, do một người thao tác.

**Tạo khoá**

- **AC-E4-16** — Trước khi lock, app hiển thị **danh sách file sẽ đưa vào khoá** kèm checksum hiện tại của từng file.
- **AC-E4-17** — Bấm **Lock** tạo file `.orchestrator/contract.lock` chứa: danh sách file, checksum SHA-256 của từng file, thời điểm lock, người duyệt, và các vai trò đã xác nhận.
- **AC-E4-18** — Sau khi lock thành công, stage ④ chuyển `done` và `backend-agent` được spawn.
- **AC-E4-19** — Lịch sử các lần lock trước được giữ lại và xem lại được, không bị ghi đè.
- **AC-E4-20** — Xem lại được nội dung của các file contract **tại thời điểm lock**, không chỉ checksum.

**Phát hiện vi phạm**

- **AC-E4-21** — Sau khi đã lock, bất kỳ file nào trong `contract.lock` bị **sửa nội dung** khiến checksum lệch đều làm pipeline chuyển sang trạng thái `CONTRACT VIOLATION`.
- **AC-E4-22** — File trong `contract.lock` bị **xoá** cũng tính là vi phạm; thông báo nêu rõ file nào đã biến mất.
- **AC-E4-23** — Khi có vi phạm, app **chặn mọi agent từ stage ⑤ trở đi chưa được spawn**. Agent đang chạy dở **không bị kill**.
- **AC-E4-24** — Nếu có agent đang chạy tại thời điểm phát hiện vi phạm, cảnh báo nêu rõ agent đó đang làm việc trên contract cũ.
- **AC-E4-25** — Trạng thái vi phạm hiển thị **diff** giữa nội dung tại thời điểm lock và nội dung hiện tại, nêu đích danh từng file lệch.
- **AC-E4-26** — File bị sửa rồi được đưa về đúng nội dung cũ (checksum khớp lại) làm trạng thái vi phạm **tự gỡ** và giải phóng các agent bị chặn; sự kiện vi phạm vẫn được ghi vào lịch sử.
- **AC-E4-27** — Bấm **Re-lock** sau khi đã tick lại đủ vai trò tạo ra một `contract.lock` mới với checksum hiện tại, giải phóng các agent bị chặn.
- **AC-E4-28** — App **không tự sửa hay hoàn tác** file contract. Muốn hoàn tác thì app chỉ hiển thị diff và đường dẫn để người dùng tự làm bên ngoài.
- **AC-E4-29** — `contract.lock` bị hỏng hoặc sửa tay khiến app coi như không có khoá hợp lệ, chuyển stage ④ về `blocked-by-gate` và yêu cầu lock lại — app không crash và không âm thầm chạy tiếp.

**Memory Update Gate ⑤ (mềm)**

- **AC-E4-30** — Sau khi một dev agent hoàn thành task, app kiểm tra các file overview của repo tương ứng có thay đổi trong lượt chạy đó không.
- **AC-E4-31** — Không thấy file overview nào thay đổi thì app hiển thị **cảnh báo** kèm danh sách file lẽ ra nên cập nhật — nhưng **không chặn** pipeline.
- **AC-E4-32** — Repo không có thư mục overview thì gate hiện `không áp dụng` và không cảnh báo.

**Bền bỉ**

- **AC-E4-33** — Đóng app khi đang có gate chờ duyệt rồi mở lại thì gate vẫn ở trạng thái chờ duyệt, chưa được duyệt.

## Out of Scope

- **Xác thực danh tính người xác nhận** — v1 không có multi-user; các ô tick là ghi nhận vai trò, do một người thao tác.
- **Duyệt gate từ xa** (web, mobile, Slack) — v1 chỉ duyệt được trong app. Slack chỉ nhận thông báo (E5).
- **Tự động hoàn tác thay đổi vi phạm** — app chỉ phát hiện, hiển thị diff và chặn.
- **Tự sinh bảng API Definition khi thiếu** — app chỉ báo thiếu; bổ sung là việc của `techlead-design-agent`.
- **Kiểm tra tính đúng đắn nghiệp vụ của contract** — app chỉ đảm bảo contract **không đổi** sau khi đã khoá, không đánh giá contract đó có hợp lý hay không.
- **Chặn việc sửa file ở tầng hệ điều hành** — app phát hiện sau khi sửa, không ngăn thao tác sửa.
- **Gate cho stage ⑧ Deploy** — chỉ là checklist thủ công.
- **Enforce Contract Lock lên `bmad-*.js`** — nếu người dùng chạy `/create-feature` ngoài app thì gate của app không có tác dụng. Xem `ASSUMPTIONS-GAPS.md` B14.

## Screens

| Screen Code | Screen | Actor | App | Screen Type | Mô tả ngắn | Figma Link |
|---|---|---|---|---|---|---|
| `OR_GATE_001` | Gate Review — Trigger | PM | E01* | Detail | Xem `SPEC.md` render + checklist 7 section, nút Approve / Request changes kèm ô nhận xét, diff sau mỗi vòng sửa | |
| `OR_GATE_002` | Gate Review — Contract Lock | PM | E01* | Detail | Bảng API Contract (REST · WebSocket · Push), danh sách file + checksum, 5 ô xác nhận vai trò, nút Lock / Re-lock, diff khi có vi phạm | |

> `*` Cột **App** = Epic code của repo đích. Bảng Ecosystem trong `AGENTS.md` của kit hiện còn placeholder, nên `E01` là giá trị **tạm** cho repo desktop app — cần xác nhận lại khi khởi tạo repo thật.
