# Dipro AI Boost — Product Overview

> Tài liệu **cross-feature** cho sản phẩm Dipro AI Boost (desktop app).
> Nguồn gốc: `SPEC-pipeline-orchestrator.md` v0.1 (14/08/2026, Tran Duc Long — PM/BA) ở root kit.
> Phiên bản này: v0.2 — 14/08/2026, tái cấu trúc theo convention BMAD của kit.
>
> **File này KHÔNG phải SPEC.** Nội dung nghiệp vụ đã được tách thành 6 SPEC per-EPIC trong `docs/features/`.
> Ở đây chỉ giữ những thứ **dùng chung cho cả 6 feature** — nhét vào từng SPEC sẽ lặp 6 lần và phá template 7 section của `ba-agent`.
>
> **Giả định & điểm lệch chưa giải quyết** → `ASSUMPTIONS-GAPS.md` (đọc trước khi thiết kế).

---

## 1. Vấn đề đang giải quyết

`project-ai-kit` đã chuẩn hoá rất kỹ phần **quy trình** (12 agent, 24 skill, 9 rule, pipeline 8 stage), nhưng phần **điều khiển quy trình** gần như không tồn tại dưới dạng máy đọc được:

| Pipeline cần | Hiện có | Mức enforce |
|---|---|---|
| Trạng thái pipeline | Suy ra từ sự tồn tại file trên disk, do LLM tự đọc | Không có state file |
| Contract Lock ④ | 4 dòng `- [ ]` markdown (`.claude/workflows/new-feature.md`) | Không — `bmad-build-phase.js` gọi thẳng backend-agent |
| Gate Planning → Build | Chuỗi text `"⏸ GATE…"` return từ `bmad-plan-phase.js` | Prompt-level, dựa vào việc tách 2 lệnh |
| Chuyển stage | Handover message tiếng Việt để user copy-paste | Thủ công |
| Cost / ROI | Không có | — |
| Hook cứng | 3 hook trong `.claude/settings.json` | Chỉ cho security, không cho pipeline |

Dipro AI Boost **kéo control plane ra khỏi session LLM** thành process bên ngoài: file system làm source of truth, gate thành UI có checksum, agent chạy headless.

**Giá trị theo thứ tự ưu tiên:**

1. Contract Lock có checksum — chống rework do lệch contract BE/FE/Mobile (cơ chế giá trị nhất, hiện **hoàn toàn không tồn tại**).
2. Trạng thái pipeline quan sát được + resume sau crash.
3. Human-in-the-loop hoạt động được cả khi chạy automation (hiện agent được lệnh "phải hỏi user" nhưng chạy qua workflow thì không có ai trả lời).
4. Cost tracking → số liệu ROI thật (hiện chỉ có baseline thủ công: 38 màn hình / 2.5h).
5. Bản thân app là asset demo quy trình "AI-driven có kiểm soát" với khách hàng.

---

## 2. EPIC map

```
E1 Project & Config ──► E2 Pipeline Execution ◄──► E4 Gates
        │                       │
        │                       ▼
        └──────────────► E3 Monitoring & Artifacts
                                │
                                ▼
              E5 Integrations (Backlog · Slack)
                                │
                                ▼
                E6 Resume · Cost · Reliability
```

| EPIC | SPEC | Mô tả | Phụ thuộc |
|---|---|---|---|
| E1 | [`features/orchestrator-project-config/SPEC.md`](../features/orchestrator-project-config/SPEC.md) | Chọn project folder, map agent↔model, permission profile, credentials | — |
| E2 | [`features/orchestrator-pipeline-execution/SPEC.md`](../features/orchestrator-pipeline-execution/SPEC.md) | Chạy agent theo DAG 8 stage, stream log, clarification loop | E1 |
| E3 | [`features/orchestrator-monitoring-artifacts/SPEC.md`](../features/orchestrator-monitoring-artifacts/SPEC.md) | File watcher, pipeline board, artifact viewer, traceability | E1 |
| E4 | [`features/orchestrator-gates/SPEC.md`](../features/orchestrator-gates/SPEC.md) | Trigger gate + Contract Lock (diff, approve, checksum, violation) | E2, E3 |
| E5 | [`features/orchestrator-integrations/SPEC.md`](../features/orchestrator-integrations/SPEC.md) | Backlog sync, Slack notify | E2, E3 |
| E6 | [`features/orchestrator-resume-cost/SPEC.md`](../features/orchestrator-resume-cost/SPEC.md) | State machine resume, cost per stage/agent, retry | E2 |

---

## 3. Phạm vi v1 (đã chốt)

| Quyết định | Giá trị |
|---|---|
| Số project | 1 project tại một thời điểm (chọn folder khi mở app) |
| Model config | Config trực tiếp per-agent (opus / sonnet / haiku) |
| Integration | Backlog (Nulab) + Slack nằm trong v1 |
| Tech stack | Tauri 2.x + React (TypeScript) · Rust backend |
| UI layer | **shadcn/ui + TailwindCSS** |
| Agent runtime | Pipeline agents dùng Claude Code CLI headless — `claude -p "<prompt>" --output-format stream-json --model <model>`; project setup dùng Claude interactive trong PTY |
| Input stage ① | **Import một folder** chứa tài liệu dự án / mô tả feature — agent phân tích folder đó để sinh SPEC |
| Nguồn design | **Figma có sẵn** — `design-analyst-agent` (agent mới) hỏi URL selection rồi đọc qua Figma MCP, sinh file phân tích design |

> **Lưu ý về UI layer:** `.claude/rules/stack-constraints.md` của kit quy định web dùng **Ant Design v6**. Dipro AI Boost là sản phẩm desktop riêng, không phải web app của dự án khách hàng, nên dùng shadcn/ui + Tailwind. Ghi nhận là **sai lệch có chủ đích** → `ASSUMPTIONS-GAPS.md` B16.
>
> shadcn/ui và Tailwind là **quyết định kỹ thuật**, nên chỉ nằm ở tài liệu product-level này. Sáu file `SPEC.md` không nhắc tới chúng — `ba-agent` quy định rõ "không đưa ra giải pháp kỹ thuật trong SPEC".

### Ngoài phạm vi v1 (toàn sản phẩm)

- Multi-project song song; multi-user / phân quyền team.
- Tự deploy STG/PROD — stage ⑧ chỉ hiển thị checklist + trạng thái, không chạy CI/CD.
- Chỉnh sửa nội dung agent/command từ trong app — app chỉ **đọc** `.claude/`. Folder Explorer có thể tạo file/folder rỗng và xoá folder trong các project root được phép, nhưng không ghi/xoá `.claude/`, `.git/`, `.orchestrator/` hoặc path restricted.
- Biên tập nội dung file trong Folder Explorer — file mới được tạo rỗng; nội dung vẫn phải sửa bằng editor bên ngoài app.
- Mỗi node agent có console riêng trong Agent Console Dock. Log được route theo `feature/slot`, còn Action Panel chỉ giữ action của node đang chọn.

---

## 4. Bản đồ màn hình

Screen Code theo `<Module(2)>_<Feature(4)>_<Seq(3)>` (`.claude/agents/ba-agent.md`). Module `OR` = Dipro AI Boost. Unique toàn dự án.

| Screen Code | Screen | EPIC | Screen Type | Actor chính |
|---|---|---|---|---|
| `OR_CONF_001` | Project Launcher | E1 | Wizard | PM |
| `OR_CONF_002` | Settings | E1 | Settings | PM |
| `OR_EXEC_001` | New Run / Import Input | E2 | Form | BA |
| `OR_EXEC_002` | Agent Detail / Log Console | E2 | Detail | PM |
| `OR_MONI_001` | Pipeline Board | E3 | Dashboard | PM |
| `OR_MONI_002` | Artifact Viewer | E3 | Detail | BA |
| `OR_GATE_001` | Gate Review — Trigger | E4 | Detail | PM |
| `OR_GATE_002` | Gate Review — Contract Lock | E4 | Detail | PM |
| `OR_INTG_001` | Backlog Sync Panel | E5 | Modal | PM |
| `OR_COST_001` | Cost & Reports | E6 | Report | PM |

`OR_MONI_001` Pipeline Board là default view khi mở project.

---

## 5. Actors dùng chung

| Actor | Vai trò với app |
|---|---|
| **PM** | Actor chính — chạy pipeline, duyệt cả 2 gate, đọc cost, config app |
| **BA** | Nhập trigger stage ①, đọc/duyệt SPEC tại Trigger gate |
| **Tech Lead** | Review DESIGN trong Artifact Viewer, xác nhận role tại Contract Lock |
| **Dev (BE / FE / Mobile)** | Xác nhận role tại Contract Lock, đọc log agent khi debug |
| **QC** | Xác nhận role tại Contract Lock |

> v1 **chưa có multi-user**. Mọi role đều do 1 người đang mở app bấm xác nhận — app chỉ ghi nhận role nào đã được tick, không xác thực danh tính. Đây là giới hạn có chủ đích, ghi rõ trong từng SPEC.

---

## 6. Data model dùng chung — `.orchestrator/`

App tạo thư mục này trong project folder (gitignore-able). Đây là **state store duy nhất** của app; artifact nghiệp vụ vẫn nằm ở `<DOCS_ROOT>/features/`.

Hai artifact **mới** so với convention gốc của kit, sinh ra bởi luồng đảo chiều ở stage ① và ②c:

| Artifact | Path | Sinh bởi |
|---|---|---|
| Folder tài liệu đầu vào | `<project>/inputs/<run-id>/` — bản sao folder người dùng import | App (stage ①) |
| File phân tích design | `<DOCS_ROOT>/features/<feature>/design-analysis.md` | `design-analyst-agent` (stage ②c) — **agent mới**, chưa tồn tại trong kit |

> `design-analysis.md` **lệch với `.claude/context/doc-structure.md`**, vốn cấm Designer tạo file `.md`. Sai lệch có chủ đích, đã quyết định (14/08/2026): thêm agent mới `design-analyst-agent` thay vì sửa `designer-agent` gốc → `ASSUMPTIONS-GAPS.md` B17.

```
.orchestrator/
├── config.json        # agent↔model, permission profile, timeout, integration refs
├── pipeline.json      # định nghĩa DAG 8 stage (v1: template chuẩn)
├── state.json         # trạng thái runtime: stage/agent/task status, session-ids
├── contract.lock      # file list + sha256 + approver + timestamp
├── snapshots/         # bản chụp artifact phục vụ diff
└── runs/              # log + cost từng run (jsonl)
```

```jsonc
// state.json (rút gọn — hình dạng minh hoạ, chốt chính thức ở DESIGN)
{
  "pipelineRun": "run-2026-08-14-001",
  "stages": {
    "S1_input":  { "status": "done",    "agents": { "ba": { "status": "done", "sessionId": "...", "costUsd": 0.42 } } },
    "S2_design": { "status": "running", "agents": { "techlead": {}, "design-analyst": {}, "qc": {} } },
    "S4_lock":   { "status": "blocked", "gate": { "approved": false } }
  }
}
```

> Ghi state phải **atomic** (write-temp-rename) — xem §7.

---

## 7. Non-functional (áp dụng cho cả 6 EPIC)

| Nhóm | Yêu cầu |
|---|---|
| **Bảo mật** | Credentials lưu OS keychain, không plaintext trong project. Không mặc định `--dangerously-skip-permissions`. Agent chỉ ghi trong scope permission profile. |
| **Hiệu năng** | Watcher debounce 500ms. Log console virtualized — chịu được log hàng chục nghìn dòng không giật. |
| **Độ tin cậy** | Mọi thao tác ghi state atomic (write-temp-rename). App crash không làm hỏng `state.json`. |
| **Ngôn ngữ UI** | Tiếng Việt. Giữ tiếng Anh cho label kỹ thuật: Approve, Lock, Retry, Resume, Skip. |
| **Theme** | Người dùng **tự chuyển** dark / light, **mặc định light**. Lựa chọn lưu ở mức app (áp dụng cho mọi project), không lưu trong `.orchestrator/`. Log console dùng font monospace ở cả hai theme. |

---

## 8. MVP roadmap

Roadmap **cắt ngang** 6 EPIC — mỗi MVP lấy một phần AC của nhiều EPIC.

### MVP 1 — Dashboard đọc (target 1–2 tuần)

Chỉ đọc, không chạy agent. Mục tiêu: chứng minh việc suy ra trạng thái pipeline từ file system là khả thi.

| Task | Nội dung | EPIC | Est. |
|---|---|---|---|
| T1.1 | Scaffold Tauri 2 + React + TS + shadcn/ui + Tailwind, CI build macOS/Windows | — | 0.5d |
| T1.2 | Project Launcher + validate `.claude/`, tạo `.orchestrator/` | E1 | 1d |
| T1.3 | Rust file watcher (notify) + mapping file→stage → `state.json` | E3 | 2d |
| T1.4 | Pipeline Board read-only: 8 stage, trạng thái suy ra từ artifact | E3 | 2d |
| T1.5 | Artifact Viewer: markdown render + mermaid | E3 | 1.5d |
| T1.6 | Snapshot + diff view cơ bản (git-based) | E3 | 1.5d |
| T1.7 | Test với project thật + fix mapping | — | 1d |

> **Điều kiện tiên quyết cho T1.2/T1.7:** giả định "project folder có `.claude/agents/`" đã được chứng minh sai với target thật — xem `ASSUMPTIONS-GAPS.md` mục A1 trước khi implement.

### MVP 2 — Chạy 1 agent

Agent runner (spawn + parse `stream-json` + emit event) · Log Console · **Import Input (chọn folder)** · chạy BA Agent end-to-end từ folder đã import · cost parse cơ bản. **(E2, một phần E6)**

> Phụ thuộc spike R1 (format `stream-json` + field cost) — xem `ASSUMPTIONS-GAPS.md` mục A5.

### MVP 3 — Gate + chain

Trigger gate (approve / request changes + resume session) · orchestration chạy stage ② song song (gồm `design-analyst-agent` hỏi Figma URL → sinh file phân tích design qua Figma MCP — **cần thêm agent này vào kit trước**, xem `ASSUMPTIONS-GAPS.md` B17) · **Contract Lock + checksum + violation detect** · clarification loop. **(E4, phần còn lại E2)**

> Clarification loop phụ thuộc việc kit có marker máy đọc được — xem `ASSUMPTIONS-GAPS.md` mục A4.

### MVP 4 — Full pipeline + integrations

Stage ⑤–⑦ với git worktree + dependency BE→FE/Mobile · Memory Update Gate soft-check · Backlog push/sync · Slack notify · resume sau crash · Cost & Reports · stage ⑧ checklist view. **(E5, E6, phần còn lại E4)**

---

## 9. Quan hệ với `.claude/workflows/bmad-*.js`

Kit **đã có** một orchestrator chạy trong CLI: `bmad-plan-phase.js` và `bmad-build-phase.js`, gọi qua `/create-feature`.

**Quyết định (14/08/2026):** app **điều phối trực tiếp từng agent**, độc lập với `bmad-*.js`. App không gọi `/create-feature`, không sửa 2 file JS này. Lý do chọn hướng này thay vì 2 phương án còn lại:

| Phương án | Vì sao không chọn |
|---|---|
| App **bọc** 2 file JS (gọi `/create-feature` qua headless) | Mất quyền kiểm soát từng agent riêng lẻ (kill/retry/cost per agent) — mâu thuẫn trực tiếp với nhiều AC đã viết ở E2 (`AC-E2-09` kill từng agent), E4 (`AC-E4-23` chặn agent cụ thể khi vi phạm contract), E6 (cost/retry theo từng agent) |
| Hai thứ **song song, độc lập, không liên quan** | Không giải quyết được gì — bản chất giống phương án đã chọn nhưng thiếu tuyên bố rõ ràng về việc app không đụng tới `bmad-*.js` |

**Hệ quả của quyết định:**
- `bmad-*.js` **giữ nguyên**, vẫn dùng được cho người dùng chạy CLI thuần không qua app — không có gì trong SPEC này yêu cầu sửa 2 file JS đó.
- App tự đọc `.claude/agents/*.md` và tự dựng lệnh spawn cho từng agent (tương tự cách `bmad-*.js` gọi `agent(...)`), nhưng bằng engine riêng của app (Rust), không tái dùng runtime JS của kit.
- Rủi ro lệch hành vi giữa 2 đường chạy (CLI thuần vs qua app) là có thật và được **chấp nhận** — cả hai đều đọc chung nguồn `.claude/agents/*.md` nên phần lệch chỉ nằm ở tầng điều phối, không ở nội dung prompt agent.

Chi tiết đầy đủ và log quyết định → `ASSUMPTIONS-GAPS.md` mục B14.

---

## 10. Xem thêm

- `ASSUMPTIONS-GAPS.md` — sổ giả định + 14 điểm lệch SPEC ↔ thực tế (**đọc trước khi thiết kế**)
- `SPEC-pipeline-orchestrator.md` (root kit) — bản v0.1 gốc, giữ nguyên làm tham chiếu lịch sử
- `.claude/context/doc-structure.md` — convention folder feature
- `.claude/agents/ba-agent.md` — template SPEC 7 section
- `ai-agents-workflow.md` §4, §5 — bảng audit + common failure modes (nguồn cảm hứng cho phần lớn AC của E4)
