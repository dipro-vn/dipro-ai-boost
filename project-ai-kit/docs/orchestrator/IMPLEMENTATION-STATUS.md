# Implementation Status — SPEC vs source (14/08/2026)

> ## ⚠️ FILE NÀY ĐÃ LẠC HẬU — ảnh chụp ngày 14/08/2026, KHÔNG phải hiện trạng
>
> Từ 15/08 đến 25/08/2026 đã build thêm (mỗi mục đều có test + đối chiếu AC):
>
> | Đợt | Nội dung | AC liên quan |
> |---|---|---|
> | Vá 9 Gap thật | 9 mục "Gap thật" liệt kê bên dưới | E1/E2/E3 rải rác |
> | MVP3 — E4 Gates | Trigger Gate + Contract Lock (tạo khoá + phát hiện vi phạm) | `AC-E4-01..29`, `33` |
> | Phase A | Orchestration engine — chuỗi tự động BE→FE∥Mobile, dừng ở gate | `AC-E2-01..05` |
> | Phase B | Settings đầy đủ (model/permission/timeout/max-retries/MCP) | `AC-E1-08..15`, `24..28` |
> | Phase C | `design-analyst-agent.md` cho kit | B17 |
> | Phase D-a | Run history + Cost & Reports + CSV, Skip/overwrite-warning, Memory Update Gate mềm | `AC-E6-12..18`, `20`, `24..26`, `28`, `AC-E4-30..32` |
> | Phase D-b | Crash-resume: trạng thái `interrupted`, Resume/Re-run, phát hiện process mồ côi, log ghi tăng dần | `AC-E6-04..07`, `09`, `10` |
> | Phase E | ~~Backlog: keychain + kiểm tra kết nối, đẩy issue qua `pm-agent`+MCP, kéo trạng thái qua REST~~ — **đã gỡ hẳn 25/08/2026 cùng `pm-agent`, xem B24** | `AC-E5-01..18` (không còn implement) |
> | Phase F (25/08) | Export design asset: `design-analyst-agent` ghi icon/ảnh vào `design-resources/`, app liệt kê chúng làm artifact của node Design-Analyst (chỉ hiển thị, không đổi điều kiện `done`) | `AC-E2-37a`, `AC-E3-01`, `AC-E3-04a` |
> | Phase G (25/08) | Gỡ `pm-agent` + `PLAN.md` + toàn bộ tính năng Backlog khỏi kit và app; thêm migration `store::legacy_cleanup` dọn `.ai-boost/` cũ | B24 — `AC-E5-01..18`, `AC-E4-09` không còn implement |
>
> **Đã loại khỏi phạm vi có chủ đích** (xem `ASSUMPTIONS-GAPS.md`): worktree `AC-E2-25/26` (B19), Slack `AC-E5-19..27` (B20), và toàn bộ Backlog `AC-E5-01..18` + `AC-E4-09` (B24 — thay thế B21).
>
> Bảng số lượng và toàn bộ nội dung bên dưới **giữ nguyên như bản 14/08** để đối chiếu lịch sử. Cần con số chính xác hôm nay thì phải chạy lại audit 185 AC trên source hiện tại.

> **Mục đích:** đối chiếu **toàn bộ 185 AC** trong 6 file `docs/features/orchestrator-*/SPEC.md` với source thật của `orchestrator-app/` — chỉ ghi lại phần **chưa xử lý** (Partial/Missing). Phần đã Done không liệt kê ở đây để giữ file gọn — xem lại SPEC gốc nếu cần đối chiếu đầy đủ.
>
> **Phương pháp:** đọc trực tiếp `src-tauri/src/` (Rust) + `src/` (React), trích hàm/dòng code cụ thể cho mỗi kết luận — không suy đoán từ tên file.
>
> **Cách đọc:** mỗi mục có 1 trong 2 nhãn:
> - **[Đúng roadmap]** — cố ý chưa làm, đã có quyết định từ trước (MVP3/MVP4), không phải thiếu sót.
> - **[Gap thật]** — nằm trong phạm vi MVP1/MVP2 đã báo "xong" nhưng thực tế chưa trọn vẹn, đáng cân nhắc vá.

---

## Tổng quan số lượng

| EPIC | Tổng AC | Done | Partial | Missing |
|---|---|---|---|---|
| E1 — Project Config | 33 | 15 | 4 | 14 |
| E2 — Pipeline Execution | 40 | 19 | 4 | 17 |
| E3 — Monitoring/Artifacts | 24 | 17 | 5 | 2 |
| E4 — Gates | 33 | 0 | 0 | 33 |
| E5 — Integrations | 27 | 0 | 0 | 27 |
| E6 — Resume/Cost | 28 | 4 | 6 | 18 |
| **Tổng** | **185** | **55** | **19** | **111** |

---

## Ưu tiên xử lý trước — Gap thật trong scope MVP1/MVP2 đã "xong"

Đây là 9 điểm **không nằm trong bất kỳ quyết định loại-khỏi-scope nào trước đó** — đáng vá sớm nhất vì user có thể đang mong đợi chúng hoạt động:

| # | AC | Vấn đề | File liên quan |
|---|---|---|---|
| 1 | AC-E2-07, AC-E6-19 | Cost **không** cộng dồn hiển thị realtime lúc agent đang chạy — chỉ biết cost ở dòng `result` cuối cùng (giới hạn CLI, xem A5), nhưng app cũng chưa hiện ước tính tạm thời. | `BaStepPanel.tsx::LiveLogView` (chỉ có đồng hồ elapsed) |
| 2 | AC-E2-20 | Log thô đã ghi ra `.ai-boost/agent-runs/<feature>/<slot>/log.jsonl` nhưng **không có command đọc lại** — tắt/mở lại app là mất lịch sử log dù file vẫn còn trên đĩa; `liveLines` chỉ là React state (mất khi unmount). | `agentrun/run_log.rs::write_run_log` (ghi), không có hàm đọc tương ứng |
| 3 | AC-E3-06 | Xoá 1 artifact đang track không có cảnh báo rõ tên file đã biến mất — node lặng lẽ quay về `Idle`. | `inference/stage_rules.rs` |
| 4 | AC-E3-07 | Watcher không tự kết nối lại sau lỗi (gap đã tự ghi chú từ T1.3, chưa vá). | `fswatch/watcher.rs` — comment "Reconnect-with-backoff... NOT implemented yet" |
| 5 | AC-E6-08 | `state.json` hỏng: không tạo `.bak`, không báo cho người dùng biết (dù state vẫn dựng lại đúng từ nguồn thật, không mất dữ liệu artifact). | `pipeline_state.rs` |
| 6 | AC-E6-27 | Lỗi khởi động agent (sai model, thiếu quyền) và lỗi giữa chừng dùng chung 1 thông báo chung chung — không phân biệt được nguyên nhân. | `agentrun/run_log.rs::classify_outcome` |
| 7 | AC-E1-16/17 | Permission "write-scoped" chỉ giới hạn qua danh sách tool (`--tools`), **chưa** giới hạn theo thư mục ghi được cụ thể như AC-E1-16 yêu cầu. | `agentrun/spawn.rs::tools_flag` |
| 8 | AC-E2-11/12 | Chưa kiểm tra "repo đã clone chưa" trước khi spawn — hàm kiểm tra đã có sẵn ở tầng E1 nhưng chưa nối vào luồng spawn E2 (hiện chưa ảnh hưởng vì chỉ `ba` — không nhắm vào repo cụ thể — spawn được). | `agents_reader.rs::resolve_repo_cloned` (có sẵn, chưa dùng ở E2) |
| 9 | AC-E2-13 | "Retry" hiện tại mở lại form import (người dùng chọn lại folder) thay vì tự phát lại đúng input ban đầu như câu chữ AC yêu cầu — đơn giản hoá đã có nhưng chưa khớp hoàn toàn. | `BaStepPanel.tsx` nhánh `status === "failed"` |

---

## E1 — Project Config (`orchestrator-project-config/SPEC.md`)

### [Đúng roadmap] — MVP4: Settings screen đầy đủ chưa có UI

Data layer backend đã đúng (`domain/config_file.rs`), chỉ thiếu màn hình:

- AC-E1-08 — không có Settings screen/tab nào cả.
- AC-E1-09 — không có dropdown chọn model.
- AC-E1-11 — không có command lẫn UI đổi model của 1 agent.
- AC-E1-13, AC-E1-14 — backend có tính `newly_discovered`/`stale` đúng, nhưng không UI nào hiện badge "mới"/"không còn trong kit" (Partial).
- AC-E1-15 — không có dropdown chọn permission profile.
- AC-E1-19 — không có dependency keychain/keyring nào trong `Cargo.toml`.
- AC-E1-20, AC-E1-21 — không có "Kiểm tra kết nối" cho Backlog/Slack.
- AC-E1-22 — không có code truy cập keychain nên fallback cũng không tồn tại.
- AC-E1-24 — không có UI để đổi config lúc agent đang chạy nên hành vi mô tả trong AC chưa kiểm chứng được (Partial).
- AC-E1-28 — theme toggle có nhưng nằm ở TopBar (vì Settings chưa có), không phải "truy cập từ Settings" như câu chữ AC (Partial).

### [Đúng roadmap] — MVP3: MCP Figma config

- AC-E1-25, AC-E1-26 — code tự ghi chú "deferred to MVP3" (`inference/stage_rules.rs`).
- AC-E1-27 — vacuously đúng (chưa có code Figma nào để vi phạm), nhưng chưa phải feature đã kiểm chứng.

### [Gap thật]

- AC-E1-16, AC-E1-17 — xem bảng ưu tiên #7 ở trên.

---

## E2 — Pipeline Execution (`orchestrator-pipeline-execution/SPEC.md`)

### [Đúng roadmap] — MVP3: multi-stage orchestration

> **Đã lỗi thời — cập nhật 24/08/2026.** Mục này viết khi chỉ `ba-agent` spawn được. Hiện lệnh `run_slot` (`commands/agentrun.rs`) + nút Run trong `AgentStepPanel.tsx` chạy được **mọi slot**, và `pipeline_def` đã khai báo `depends_on` giữa stage + `after_slots` trong stage (FE/Mobile chờ BE). Phần còn thiếu là **tự động fan-out**: readiness quyết định slot nào được phép chạy, nhưng người dùng vẫn phải bấm Run từng slot.

- AC-E2-02, AC-E2-03, AC-E2-04, AC-E2-05 — Partial: thứ tự/phụ thuộc đã có trong `pipeline.json` và được readiness thực thi, nhưng chưa có engine tự spawn chuỗi.
- AC-E2-01 — Done: `pipeline.json` vừa RENDER board vừa quyết định slot nào đủ điều kiện chạy (`agentrun::readiness`).
- AC-E2-14 — `NodeStatus::Skipped` tồn tại trong type nhưng không có action nào tạo ra trạng thái này.

### [Đúng roadmap] — MVP3: Design-Analyst + Figma MCP (8 AC)

AC-E2-33 đến AC-E2-40 — 100% chưa đụng, bị chặn bởi B17 (`design-analyst-agent.md` chưa tồn tại trong kit). `inference::stage_rules::infer_design_analyst` chỉ kiểm tra file có tồn tại trên đĩa để hiện Board, không liên quan đến việc thật sự chạy agent này.

> **Cập nhật 25/08/2026 (Phase F):** B17 đã đóng, nhánh này chạy thật. `AC-E2-37a` (export icon/ảnh vào `design-resources/`) đã implement ở cả hai phía: Bước 4 bắt buộc trong `.claude/agents/design-analyst-agent.md`, và `build_slot_prompt` nhắc lại đường dẫn tuyệt đối. `AC-E3-04a` (asset chỉ hiển thị, không phải điều kiện `done`) có test khẳng định trong `inference::stage_rules`.

### [Đúng roadmap] — MVP4: git worktree

- AC-E2-25, AC-E2-26 — 0 dòng code liên quan (`grep -i worktree` = 0 hit).

### [Gap thật]

- AC-E2-07 — xem bảng ưu tiên #1.
- AC-E2-11, AC-E2-12 — xem bảng ưu tiên #8.
- AC-E2-13 — xem bảng ưu tiên #9.
- AC-E2-20 — xem bảng ưu tiên #2.

---

## E3 — Monitoring & Artifacts (`orchestrator-monitoring-artifacts/SPEC.md`)

### [Đúng roadmap] — MVP3: Contract Lock inference

- AC-E3-01 — watcher **cố ý** không watch `.ai-boost/contract.lock` (comment rõ trong `fswatch/watcher.rs`) — Partial vì phần còn lại của AC (watch feature dir + runs dir) đã đúng.
- AC-E3-10 — stage ④ (Contract Lock) không có agent/inference nào — đúng, vì thuộc E4/MVP3 (Partial vì 7/8 stage còn lại đúng).
- AC-E3-09 — 8 `NodeStatus` đều có icon/màu riêng, nhưng `Blocked`/`Skipped` chưa từng được tạo ra bởi code nào (Partial).

### [Đúng roadmap] — MVP4: Traceability

- AC-E3-23, AC-E3-24 — 0 dòng code (`grep -ri "trace"` = 0 hit). `ASSUMPTIONS-GAPS.md` §A2 đã ghi chú dữ liệu kit thật (ESKITCHEN) quá thiếu để traceability tự động có giá trị.

### [Gap thật]

- AC-E3-06 — xem bảng ưu tiên #3.
- AC-E3-07 — xem bảng ưu tiên #4.

---

## E4 — Gates (`orchestrator-gates/SPEC.md`)

**[Đúng roadmap] — MVP3, 33/33 AC Missing.** Không có Gate Review screen, không có Contract Lock (khoá/checksum/phát hiện vi phạm), không có Memory Update Gate mềm. `fswatch/watcher.rs` tự ghi chú "Revisit properly once MVP3 needs Contract Lock inference".

---

## E5 — Integrations (`orchestrator-integrations/SPEC.md`)

> **Đã lỗi thời — cập nhật 24/08/2026.** Câu "0 hit" bên dưới không còn đúng: `Cargo.toml` có `reqwest 0.13`, và Backlog đã được build (`integrations/backlog_api.rs`, `commands/backlog.rs`, `commands/integrations.rs`, màn `BacklogScreen.tsx`, credential lưu trong OS keychain). Slack/webhook thì vẫn chưa có. Cần audit lại 27 AC của E5 để chốt cái nào Done — đừng tin con số 27/27 Missing.

**[Nguyên văn bản cũ]** — MVP4, 27/27 AC Missing. `grep -rniE "backlog|slack|nulab|webhook"` toàn bộ source = 0 hit. Không có dependency HTTP client (`reqwest`...) trong `Cargo.toml` để gọi API Backlog/Slack.

**Lưu ý bảo mật liên quan (không phải của app này):** `ASSUMPTIONS-GAPS.md` §C15 ghi nhận `.mcp.json` của target workspace ESKITCHEN có Backlog API key dạng plaintext — cần rotate, độc lập với tiến độ build E5.

---

## E6 — Resume & Cost (`orchestrator-resume-cost/SPEC.md`)

### [Đúng roadmap] — MVP4: crash-resume toàn app

- AC-E6-04 — không có trạng thái `Interrupted` trong `NodeStatus` enum (8 variant hiện tại không có).
- AC-E6-05, AC-E6-06, AC-E6-09 — phụ thuộc AC-E6-04, chưa có.
- AC-E6-07 — log giữa chừng bị mất nếu app bị kill (chỉ ghi 1 lần vào cuối, ở `finalize_run`).
- AC-E6-10 — không phát hiện process mồ côi sau khi app đóng (`ProcessRegistry` chỉ ở memory, mất khi restart).
- AC-E6-01, AC-E6-02 — Done (state reconstruction từ đĩa hoạt động đúng).
- AC-E6-03 — Partial: state dựng lại đúng cho node đã xong/lỗi/chờ trả lời, nhưng node đang chạy giữa chừng lúc app tắt sẽ hiện sai thành `Idle`.
- AC-E6-08 — xem bảng ưu tiên #5.

### [Đúng roadmap] — MVP4: Cost & Reports screen (8 AC)

AC-E6-12 đến AC-E6-19 — không có màn hình tổng hợp chi phí, không export CSV, không lưu lịch sử nhiều lần chạy (`last-run.json` chỉ giữ **lần gần nhất**, không phải toàn bộ lịch sử), `RunSummary` không lưu field `model` đã dùng.

### [Đúng roadmap] — MVP4: Skip + cấu hình lỗi

- AC-E6-20, AC-E6-24, AC-E6-25, AC-E6-26, AC-E6-28 — không có nút Skip ở đâu trong code.
- AC-E6-21, AC-E6-23 — timeout/max-retries có giá trị mặc định đúng nhưng hardcode, chưa cấu hình được qua UI (Partial, phụ thuộc Settings screen).

### [Gap thật]

- AC-E6-19 — xem bảng ưu tiên #1.
- AC-E6-27 — xem bảng ưu tiên #6.

---

## Companion files

- `docs/orchestrator/OVERVIEW.md` — roadmap MVP1-4 gốc.
- `docs/orchestrator/ASSUMPTIONS-GAPS.md` — giả định/gap phát hiện lúc viết SPEC (khác với file này — file này là audit SAU khi code đã chạy).
