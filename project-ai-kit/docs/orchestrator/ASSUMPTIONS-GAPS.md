# Sổ giả định & điểm lệch — Dipro AI Boost

> **Mục đích:** ghi nhận mọi giả định trong `SPEC-pipeline-orchestrator.md` v0.1 đã được đối chiếu với source thật, cộng các điểm lệch nội tại của kit ảnh hưởng tới orchestrator.
>
> **Đây là tài liệu ghi nhận — không phải quyết định.** Cột "Đề xuất" là gợi ý để PM/Tech Lead quyết. **Chưa sửa bất kỳ file nào trong `.claude/`.**
>
> Ngày đối chiếu: 14/08/2026. Nguồn: `project-ai-kit` @ `cabf0d9` + `/Users/dipro/Work/ESKITCHEN-WORKSPACE/`.

**Trạng thái:** ✅ đã verify đúng · ❌ đã verify sai · ⚠️ cần spike · 📌 cần người quyết · 🔒 đã quyết định

---

## Nhóm A — Giả định trong SPEC v0.1

### A1 ❌ Repo `es-kitchen-ai-agents` không tồn tại

**SPEC nói:** dòng 12 — orchestrate "repo `es-kitchen-ai-agents`"; dòng 208 (T1.7), dòng 264 (R5) đều tham chiếu tên này.

**Thực tế:** không có thư mục nào tên đó trong `/Users/dipro/Work`. Target thật là workspace `/Users/dipro/Work/ESKITCHEN-WORKSPACE/` với cấu trúc lồng:

```
ESKITCHEN-WORKSPACE/
├── .claude/                        ← chỉ settings.json + settings.local.json (mỏng)
├── .mcp.json                       ← figma, codegraph, backlog
├── es-kitchen-docs/                ← ĐÂY mới là "agents repo"
│   ├── .claude/agents/  (9 agent)  ← .claude/agents thật nằm SÂU 1 CẤP
│   ├── AGENTS.md · POLICIES.md
│   └── es-kitchen-docs/docs/features/   ← DOCS_ROOT, lồng thêm 1 cấp nữa
└── es-kitchen-repository/
    ├── es-kitchen-api/             ← không có .claude/, chỉ có docs/
    ├── es-kitchen-web-admin/       ← có .claude/ riêng
    ├── es-kitchen-web-company/     ← có .claude/ riêng
    └── es-kitchen-web-outsource-web-private/
```

**Ảnh hưởng:** F1.1 validate "folder phải có `.claude/agents/`" sẽ **fail ngay màn hình đầu** với target thật. Ngoài ra `.claude/` xuất hiện ở 3 cấp khác nhau với ý nghĩa khác nhau (workspace-level, docs-repo-level, source-repo-level) — app phải phân biệt được cái nào là nguồn agent.

**Đề xuất:** F1.1 không dò tự động theo 1 quy ước cứng. Cho user chỉ **3 path riêng** khi mở project (agents root · DOCS_ROOT · repository root), lưu vào `.orchestrator/config.json`. Đã phản ánh vào `AC-E1-02`, `AC-E1-03`.

---

### A2 ✅ R5 đã có câu trả lời — traceability tự động chưa đủ dữ liệu

**SPEC nói:** R5 — "Convention ID trong artifact đủ nhất quán cho traceability tự động", cách verify: "Audit artifacts hiện có của es-kitchen".

**Thực tế (audit đã chạy):** `es-kitchen-docs/es-kitchen-docs/docs/features/` có **15 feature, 62 file `.md`**:

| Chỉ số | Kết quả |
|---|---|
| Feature có `SPEC.md` | 15/15 ✅ |
| Feature có `tasks/` | **2/15** |
| Feature có `PLAN.md` | **1/15** (chỉ `api-hardening`) |
| Task ID unique toàn dự án | ❌ — chỉ `task-N-M.md`, unique trong scope repo |
| Đặt tên nhất quán | ❌ — có `PLAN-customer-type-api-integration.md` đặt sai cấp trong `company-contract-registration/es-kitchen-web-company/` |

**Ảnh hưởng:** F3.3 traceability panel ("từ 1 task → link ngược SPEC section, xuôi tới test-case + bug report") **không chạy được** trên dữ liệu hiện có. Không phải lỗi thiết kế app — dữ liệu nguồn chưa đủ.

**Đề xuất:** hạ F3.3 xuống best-effort trong v1 (link được thì hiện, không thì hiện "chưa đủ dữ liệu" — không đoán). Đã phản ánh vào `AC-E3-10`, `AC-E3-11`. Việc chuẩn hoá ID artifact là **task riêng của kit**, không thuộc phạm vi app.

---

### A3 ✅ 3/7 repo trong Ecosystem es-kitchen chưa clone về máy

**Thực tế:** `es-kitchen-docs/AGENTS.md` khai 7 repo (api, payment-app E01, web-company E02, web-admin E03, web-supplier E04, web-outsource E05, webapp-driver E06). Trên đĩa chỉ có **4**: api, web-admin, web-company, web-outsource. Thiếu: **payment-app, web-supplier, webapp-driver** — dù `docs/features/` vẫn có `DESIGN.md` cho chúng.

**Ảnh hưởng:** F2.1 spawn agent với `cwd = repo tương ứng` sẽ fail cho 3 repo này. F3.2 Pipeline Board sẽ hiện stage ⑤ vĩnh viễn không xong.

**Đề xuất:** app phải phân biệt **"repo chưa clone"** với **"agent failed"** — trạng thái riêng, thông báo rõ. Đã phản ánh vào `AC-E1-04`, `AC-E2-11`.

---

### A4 🔒 F2.3 giả định sai về cách agent hỏi user — ĐÃ QUYẾT ĐỊNH

> **Quyết định (17/08/2026, PM):** chọn **phương án 2 — heuristic**, cụ thể là cơ chế đã chạy thực tế từ MVP2: agent exit sạch (không lỗi) mà **chưa tạo ra artifact được mong đợi** → node chuyển `waiting-input`, nội dung câu hỏi lấy từ message cuối của agent (`run_log::classify_outcome`). Không sửa kit, không thêm marker. Đây cũng chính là cách `AC-E2-15` mô tả. Nếu heuristic phát sinh false positive/negative đáng kể trong thực tế → cân nhắc lại phương án 1 (marker) khi đó.

**SPEC nói:** dòng 117 — "detect qua pattern trong command design — vd agent kết thúc turn bằng block `## QUESTION`".

**Thực tế:** grep toàn bộ `.claude/agents/` (12 file) **không có chuỗi `QUESTION` nào**. Agent hỏi bằng **văn xuôi tiếng Việt**, mỗi agent một kiểu riêng:

| Agent | Cơ chế hỏi | Định danh máy đọc được? |
|---|---|---|
| `ba-agent` | Bước 2a "Check multiple interpretations" — template N option kèm Approach/Effort/Trade-off; Bước 2b checklist 10 câu | ❌ |
| `techlead-design-agent` | Bước 3c "Check multiple approaches" — 7 trục trade-off, kết bằng "Bạn xác nhận approach nào?" | ❌ |
| `qc-agent` | "Human checkpoint" trong bảng pipeline; hỏi A/B/C khi gặp TBD AC | ❌ |
| `designer-agent` | GATE DỪNG khi thiếu component trong design system | ❌ |

**Ảnh hưởng:** đây là **dependency ngược mà SPEC v0.1 không nêu** — F2.3 không thể implement nếu không sửa kit trước. Nghiêm trọng hơn: đây không phải chi tiết phụ. Kit **thiết kế agent để bắt buộc dừng hỏi** (`POLICIES.md` §1 "Không đoán mò", `RELIABILITY.md` §5 "Escalation Path"), nhưng `/create-feature` chạy chúng qua workflow **không có ai trả lời** → agent hoặc treo, hoặc vi phạm chính policy của nó.

**Đề xuất (cần người quyết — không tự sửa kit):**

| Phương án | Ưu | Nhược |
|---|---|---|
| Thêm marker chuẩn (vd `<!-- ORCHESTRATOR:QUESTION -->`) vào 12 agent file | Detect chính xác 100% | Sửa 12 file kit; kit dùng cho nhiều dự án khác |
| App detect heuristic (câu kết thúc bằng `?` + agent không tạo artifact nào) | Không đụng kit | Không đáng tin, dễ false positive/negative |
| App luôn dừng sau mỗi agent, người đọc output tự quyết | Đơn giản, an toàn | Mất phần lớn giá trị automation |

Đã phản ánh vào `AC-E2-07`, `AC-E2-08` (viết theo hành vi quan sát được, **không** giả định marker cụ thể).

---

### A5 ✅ R1 + R2 đã spike thật (14/08/2026, `claude` CLI v2.1.232)

**SPEC nói:** R1 format `stream-json` + field cost của Claude Code hiện tại; R2 `--resume` hoạt động ổn với clarification loop.

**Cách verify:** chạy thật `claude -p "<prompt>" --output-format stream-json --verbose --model haiku --max-budget-usd 0.05` trong thư mục scratchpad cô lập (không phải trong `project-ai-kit`), tổng chi phí 4 lần gọi ~$0.08. Không đoán từ tài liệu — đúng tinh thần `RELIABILITY.md`.

**Kết quả quan sát được (KHÔNG phải hợp đồng cố định — CLI có thể đổi giữa các version, F2.2 phải parse tolerant, bỏ qua field/type lạ thay vì crash):**

| Câu hỏi SPEC | Quan sát thật |
|---|---|
| Format `stream-json` là gì? | JSON Lines, mỗi dòng 1 object có `type`. Đã thấy: `system` (`subtype`: `hook_started`, `hook_response`, `init`, `thinking_tokens`), `assistant`, `rate_limit_event`, `result`. Danh sách này **không đầy đủ** — chỉ là những gì 1 lần gọi đơn giản tạo ra. |
| 1 message = 1 dòng `assistant`? | **Không.** Cùng 1 `message.id` xuất hiện ở **nhiều dòng `assistant` liên tiếp**, mỗi dòng chỉ chứa 1 content block (vd dòng 1: `content: [{type: "thinking"}]`, dòng 2: `content: [{type: "text"}]`). F2.2 phải **gộp theo `message.id`**, không được coi 1 dòng `assistant` là message hoàn chỉnh. |
| Field cost nằm ở đâu? | Dòng cuối `type: "result"` → `total_cost_usd` (số thực, đơn vị USD, vd `0.013452`). Có thêm `modelUsage.<model>.costUSD` (breakdown theo model) và `usage` (token thô) — nhưng field **tổng đáng tin cậy nhất là `total_cost_usd` ở top-level `result`**, đúng như AC-E6 đã viết ("khớp với tổng do CLI báo cáo"). |
| `session_id` có ổn định qua `--resume` không? | **Có.** `--resume <session_id>` giữ nguyên `session_id` cũ (trừ khi thêm `--fork-session` để cố ý tách session mới). |
| `--resume` có thật sự giữ context không? | **Có, xác nhận bằng thực nghiệm:** turn 1 yêu cầu nhớ số bí mật, turn 2 (resume) hỏi lại → trả lời đúng số đã cho ở turn 1. Đây là điều kiện tiên quyết cho clarification loop (F6.1) — **không còn là giả định**. |
| `--no-session-persistence` ảnh hưởng gì? | Session không lưa đĩa → **không thể `--resume`** sau đó. Agent runner (F2.1) **không được** dùng flag này nếu dự định hỗ trợ clarification loop/resume sau crash (MVP4). |
| `num_turns` trong `result` là gì? | Số turn của **riêng lần gọi này**, không cộng dồn qua các lần `--resume` trước đó — không dùng field này để tính tổng cost/turn toàn phiên, phải tự cộng dồn phía app. |

**Ảnh hưởng:** F2.2 (parse stream), F6.1 (session resume), F6.2 (cost) — cả 3 đều đã có bằng chứng thực nghiệm, không còn phụ thuộc giả định. `AC-E2-07`, `AC-E2-08`, `AC-E6-*` giữ nguyên cách viết theo hành vi quan sát được (không hard-code schema cụ thể vào AC) — bảng trên là tài liệu tham khảo implementation, không phải AC.

**Đề xuất:** MVP2 có thể bắt đầu implement **agent runner** dựa trên các quan sát này. Parser bắt buộc: (1) group theo `message.id`, (2) bỏ qua `type`/`subtype` không nhận diện được thay vì lỗi, (3) đọc cost duy nhất từ `result.total_cost_usd`, (4) không bao giờ dùng `--no-session-persistence` cho agent chạy thật.

---

### A7 ❌ CLI `claude` không có flag `--max-turns` — `AgentConfig.max_turns` (MVP1) không enforce được ở lớp CLI

**Phát hiện khi nào:** đọc `claude --help` đầy đủ lúc bắt đầu implement `agentrun::spawn` (MVP2/T2.1), trước khi viết code build command — không đoán tên flag.

**Thực tế:** `claude --help` (v2.1.232) liệt kê đầy đủ mọi flag của `-p`/`--print`. Không có `--max-turns`, không có alias nào tương đương. Flag gần nhất về "giới hạn chi phí 1 lượt chạy" là `--max-budget-usd <amount>` (giới hạn USD, không phải số turn).

**Ảnh hưởng:** `domain::config_file::AgentConfig.max_turns` (định nghĩa ở MVP1 theo bảng "Model mặc định" của `orchestrator-project-config/SPEC.md`) **không có cách truyền xuống CLI**. Field này vẫn giữ trong `config.json`/UI (không xoá — Settings screen tương lai có thể vẫn muốn hiển thị nó như một giá trị tham khảo), nhưng **`agentrun::spawn` sẽ không dùng nó để build command**, và app **không được** giả vờ đã enforce nó.

**Đề xuất:** Hàng rào chống chạy lặp vô hạn của MVP2 chỉ còn **timeout theo wall-clock** (`AC-E2-10`, mặc định 30 phút, đã có trong plan T2.3) — đây là safety net duy nhất thật sự hoạt động ở CLI layer hiện tại. Cân nhắc bổ sung `--max-budget-usd` (đã tồn tại, dùng thật được) như một lớp phòng vệ thứ 2 dựa trên chi phí thay vì số turn — **ngoài phạm vi MVP2 đã duyệt**, ghi nhận ở đây để cân nhắc khi làm Cost & Reports (MVP4).

---

### A6 ✅ Backlog project 684621 có thật

**SPEC nói:** dòng 97, 158 — default space `dipro-vn`, project ID `684621`.

**Thực tế:** xác nhận trong `es-kitchen-docs/es-kitchen-docs/docs/quality/phase1_quality.md` — link `dipro-vn.backlog.com/find/ESKITCHEN?...projectId=684621`, project key `ESKITCHEN`. MCP server `@nulab/backlog-mcp-server` đã khai trong `.claude/settings.json` của kit (env rỗng, đúng chuẩn template).

**Lưu ý:** `.claude/context/backlog-workflow.md` của kit là bản hợp nhất **"Quy định sử dụng Backlog Dipro V2.0"** (hiệu lực 27/07/2026) — 6 issue type, 9 status, quy tắc subtask, template Task/Bug bắt buộc. E5 phải tuân thủ tài liệu này, không tự đặt convention mới.

---

## Nhóm B — Điểm lệch nội tại của kit

> Các mục dưới đây là đặc điểm của `project-ai-kit` ảnh hưởng tới orchestrator. **Ghi nhận, không sửa.**

### B7 📌 Contract Lock không được enforce ở bất kỳ đâu

**Bằng chứng:**
- `.claude/workflows/new-feature.md:122-135` — Contract Lock là 4 dòng `- [ ]` markdown.
- `README.md:258-269` — stage ④ là node Mermaid, style `classDef gate`.
- `.claude/workflows/bmad-build-phase.js:16` — gọi thẳng `backend-agent`, **không check gì** về Contract Lock.
- `bmad-build-phase.js:31,38` — bước 5b ("copy API Contract → task-3-x", được đánh dấu `(manual)` trong `ai-agents-workflow.md:23`) được tự động hoá bằng cách nhét `JSON.stringify(be)` vào prompt FE/Mobile. Không lock, không checksum.

**Ảnh hưởng:** đây chính là lý do tồn tại của E4 và là hạng mục giá trị cao nhất của sản phẩm. Không phải "cải thiện" — là bổ sung cơ chế **chưa từng tồn tại**.

---

### B8 🔒 Ba hệ đánh số stage cùng tồn tại, mapping không 1-1 — ĐÃ QUYẾT ĐỊNH

| Nguồn | Hệ đánh số |
|---|---|
| `README.md:175-369` (Mermaid) | ① INPUT · ② DESIGN · ③ PLANNING · ④ CONTRACT LOCK · ⑤ BUILD · ⑥ VERIFY · ⑦ TESTING · ⑧ DEPLOY |
| `ai-agents-workflow.md:13-31` | 0 Setup · 1 Discovery · 2a/2b/2c Design · 3 Tasks · 4 PM · 5a–5e Build · 6 Verify · 7a/7b/7c Test |
| `.claude/workflows/new-feature.md` | Bước 1..7, Contract Lock **không đánh số** |

**Lệch cụ thể:** README gộp Tech Lead Tasks + PM vào ③, còn `ai-agents-workflow.md` tách thành #3 và #4. README tách Contract Lock thành stage ④ riêng, `new-feature.md` để nó không số. Ký tự ①..⑧ **chỉ là label chuỗi trong Mermaid**, không được tham chiếu ở bất kỳ agent/command/script nào.

**Quyết định (14/08/2026, PM):** dùng hệ **①..⑧ của README** làm canonical cho `pipeline.json` — khớp `SPEC-pipeline-orchestrator.md` v0.1 gốc, và **đã là hệ đang dùng xuyên suốt** `OVERVIEW.md` và cả 6 SPEC hiện có nên không cần viết lại gì.

**Cách áp dụng:** `pipeline.json` khai báo **tường minh** agent nào thuộc stage nào (không suy diễn từ tên file agent) — đã phản ánh vào `AC-E2-01`. Với ranh giới mơ hồ giữa ③/④ trong tài liệu kit (README tách Contract Lock riêng, `ai-agents-workflow.md` không), app tự coi Contract Lock là stage ④ độc lập, đúng theo README.

---

### B9 ✅ PM nằm ngoài `/create-feature` (đã giải quyết triệt để bởi B24)

`.claude/commands/create-feature.md` và cả 2 file `bmad-*.js` đều **loại PM ra**. Chạy shortcut sẽ đi ③ (tasks) → ⑤ (build) **không có `PLAN.md`**.

**Ảnh hưởng (lúc phát hiện):** F4.2 đặt điều kiện mở gate Contract Lock là "**PLAN.md tồn tại** + API Contract table đầy đủ". Nếu team quen dùng `/create-feature`, gate sẽ không bao giờ mở được.

**Đã xử lý:** ban đầu app hạ `PLAN.md` xuống mức cảnh báo (`AC-E4-09`), điều kiện mở gate chỉ dựa trên **API Contract table** (`AC-E4-04`). Từ **B24** (25/08/2026), `pm-agent` và `PLAN.md` bị gỡ hẳn khỏi kit — mâu thuẫn này không còn tồn tại, và `AC-E4-09` cũng đã được gỡ.

---

### B10 ✅ Designer không sinh file `.md` — watcher không có gì để watch (đã giải quyết bởi B17)

`.claude/context/doc-structure.md:23` và `ai-agents-workflow.md:174` **cấm** `designer-agent` tạo file `.md`. Output là Figma frames (cloud) + URL điền vào cột `Figma Link` **bên trong** `## Screens` của `SPEC.md`.

**Ảnh hưởng:** F3.1 watch danh sách file (`SPEC.md`, `DESIGN*.md`, `tasks/`…) **không phát hiện được** stage ②c hoàn thành — vì không có file mới nào xuất hiện, chỉ có nội dung `SPEC.md` thay đổi.

**Đề xuất:** ~~watcher phải parse nội dung `SPEC.md` (cột `Figma Link`)~~ — **đã được giải quyết bởi B17**: luồng Designer mới sinh ra `design-analysis.md`, nên watcher có file thật để theo dõi. Xem `AC-E3-04`.

---

### B11 📌 E2E execution report không có path quy định

`ai-agents-workflow.md` §3.9 — execution report trả về dạng **message/output**, không quy định path file. (Lịch sử: QA Report và QC execution checklist cũng vậy, trước khi 2 slot đó bị bỏ khỏi pipeline.)

**Ảnh hưởng:** F3.1 liệt kê `reports/` trong danh sách watch, nhưng kit không quy định artifact nào rơi vào đó → stage ⑥ và ⑦ không có tín hiệu hoàn thành đáng tin.

**Đề xuất:** app tự định nghĩa path trong `.orchestrator/` cho các artifact kit không quy định (vd `.orchestrator/runs/<run>/qa-report.md`), sinh từ output agent. Không sửa kit. Đã phản ánh vào `AC-E3-05`.

---

### B12 📌 `/create-ui-design` mô tả mâu thuẫn với `doc-structure.md`

Mô tả command `.claude/commands/create-ui-design.md` ghi "Tạo **UI-SPEC.md** + Figma screens", trong khi `doc-structure.md:23` và `ai-agents-workflow.md:174` **cấm** Designer tạo file `.md`.

**Ảnh hưởng:** nhẹ — nhưng nếu app map "stage ②c xong = có `UI-SPEC.md`" thì sai. Liên quan B10.

---

### B13 📌 `ba-agent.md:217` còn trỏ 2 command đã xoá

Section Output của `ba-agent` gợi ý `/test/generate_manual_testcases_rbt` và `/test/generate_testcases_from_requirements`. `.claude/commands/README.md` ghi rõ hai command này **đã bị xoá**, thay bằng pipeline `analyze-req → plan-tcs → gen-tcs`. `qc-agent.md` đã cập nhật đúng.

**Ảnh hưởng:** nhẹ — nhưng nếu app parse handover message của BA để tự chạy stage tiếp theo thì sẽ gọi command không tồn tại.

---

### B14 🔒 Chồng lấn với `.claude/workflows/bmad-*.js` — ĐÃ QUYẾT ĐỊNH

Kit **đã có** orchestrator chạy trong CLI (`bmad-plan-phase.js`, `bmad-build-phase.js` qua `/create-feature`). SPEC v0.1 không nói app *thay thế* hay *bọc* chúng.

**Quyết định (14/08/2026, PM + Tech Lead):** app **điều phối trực tiếp từng agent**, độc lập với `bmad-*.js`. Không gọi `/create-feature`, không sửa 2 file JS. Lý do: các AC đã viết ở E2/E4/E6 (kill/retry/cost per agent, chặn agent cụ thể khi Contract Lock vi phạm) đòi hỏi mức kiểm soát mà việc gọi qua `/create-feature` không cung cấp được — xem lập luận đầy đủ ở `OVERVIEW.md` §9.

**Hệ quả:** `bmad-*.js` giữ nguyên cho người dùng CLI thuần. Rủi ro lệch hành vi giữa 2 đường chạy được **chấp nhận có ý thức**, vì cả hai cùng đọc chung `.claude/agents/*.md` — phần lệch chỉ ở tầng điều phối.

---

### B16 🔒 shadcn/ui + Tailwind lệch với `stack-constraints.md` của kit — ĐÃ QUYẾT ĐỊNH

**Bằng chứng:** `.claude/rules/stack-constraints.md` và `POLICIES.md` §5 quy định web dùng **Ant Design v6**, và ghi rõ stack "không thương lượng trừ khi đổi qua `/init-kit`".

**Quyết định:** orchestrator dùng **shadcn/ui + TailwindCSS**.

**Lý do chấp nhận sai lệch:** `stack-constraints.md` là ràng buộc cho **dự án khách hàng xây bằng kit**, không phải cho công cụ nội bộ. Dipro AI Boost là ứng dụng desktop Tauri, không phải web app trong bảng Ecosystem của bất kỳ dự án nào. TailwindCSS v4 vốn đã nằm trong stack kit; chỉ có component library là khác.

**Ảnh hưởng:** không có với dự án khách hàng. Nhưng vì SPEC đang nằm trong repo kit, người đọc dễ nhầm đây là thay đổi stack của kit — **không phải**.

**Đề xuất:** giữ nguyên quyết định. Khi orchestrator tách ra repo riêng thì vấn đề tự hết. Không sửa `stack-constraints.md`.

---

### B17 🔒 Luồng Designer đảo chiều — ĐÃ QUYẾT ĐỊNH, tạo dependency mới cho kit

**Kit hiện quy định (SPEC → Figma):**
- `designer-agent` đọc `SPEC.md` §Screens → **tạo** Figma frames → điền URL ngược vào cột `Figma Link`.
- `doc-structure.md:23` và `ai-agents-workflow.md:174` **cấm** Designer tạo bất kỳ file `.md` nào.

**Dipro AI Boost cần (Figma → phân tích):**
- Agent **hỏi người dùng URL selection** của design có sẵn (một page hoặc một feature).
- Đọc design qua **Figma MCP được cấu hình trong repo dự án**.
- **Sinh ra một file phân tích design** để các stage sau dùng.

**Đây là đảo chiều, không phải điều chỉnh nhỏ.** Kit giả định greenfield (chưa có design, agent vẽ ra). Dipro AI Boost giả định brownfield (design đã có sẵn trong Figma, agent đọc và diễn giải). Cùng với việc stage ① nhận **folder tài liệu có sẵn** thay vì mô tả tự do, cả pipeline chuyển từ *sinh mới* sang *diễn giải cái đã có*.

**Quyết định (14/08/2026, PM + Tech Lead):** thêm **agent mới** vào kit, `design-analyst-agent`, chuyên trách chiều Figma → phân tích. `designer-agent` gốc **giữ nguyên không sửa** — vẫn phục vụ use case greenfield ở các dự án khác dùng kit.

**Lý do chọn "thêm agent mới" thay vì 2 phương án còn lại:**
- Không chọn **sửa `designer-agent.md` thành dual-mode**: sẽ làm phức tạp hoá agent đang hoạt động tốt cho các dự án khác, và trộn 2 trách nhiệm khác bản chất (vẽ mới vs đọc-diễn giải) vào 1 file.
- Không chọn **App tự dựng prompt, không qua agent file**: phá nguyên tắc "agent file là canonical workflow, command chỉ là entry point" (`.claude/agents/*.md` header) — và lệch mục tiêu dogfooding ban đầu của toàn bộ bộ SPEC này (phải chạy được qua chính pipeline BMAD của kit).

**Việc còn lại — KHÔNG thuộc phạm vi bộ SPEC này:**

File `.claude/agents/design-analyst-agent.md` **hiện chưa tồn tại**. Viết nó là việc bổ sung vào kit, do Tech Lead của kit thực hiện (tương tự cách 12 agent hiện có được viết), theo đúng khuôn mẫu: frontmatter (`name`/`description`/`model`/`tools`/`skills`), `## Ràng buộc cứng`, các `## Bước N` với `tilth_read` liệt kê input files, và `## Output` kèm handover message. Gợi ý nội dung dựa trên `AC-E2-33` đến `AC-E2-40` của `orchestrator-pipeline-execution/SPEC.md`:
1. Hỏi user URL selection (không tự đoán)
2. Gọi Figma MCP đọc design tại URL đó
3. Ghi `<DOCS_ROOT>/features/<feature>/design-analysis.md`
4. Ràng buộc cứng: chỉ đọc Figma, không tạo/sửa gì trong Figma; không tự tìm URL

**Ảnh hưởng đã phản ánh vào SPEC:**
- Tín hiệu nhận biết stage ②c hoàn thành: "`design-analysis.md` tồn tại" (`AC-E3-04`, `AC-E3-12`) — giải quyết luôn B10.
- E2 Preconditions và Out of Scope ghi rõ agent này là dependency ngoài phạm vi (`orchestrator-pipeline-execution/SPEC.md`).
- E1 Settings hiển thị cảnh báo riêng khi thiếu agent này, phân biệt với lỗi thiếu MCP (`AC-E2-40`, `AF-26`).

---

### B18 🔒 Figma MCP lấy cấu hình từ repo dự án, không phải từ app — ĐÃ QUYẾT ĐỊNH

Yêu cầu nêu rõ agent dùng "MCP Figma **được config trong repo**". Nghĩa là orchestrator **không tự quản lý** credentials Figma — nó dựa vào cấu hình MCP sẵn có của project (`.mcp.json` hoặc `.claude/settings.json`).

**Đối chiếu thực tế:**
- Kit khai `figma` là MCP dạng http tại `http://127.0.0.1:3845/mcp` — tức **Figma Desktop app phải đang chạy trên máy**, không phải API key.
- ESKITCHEN khai `figma-open-mcp` và `figma-bridge` trong `.mcp.json` — **tên khác** với kit.

**Quyết định (14/08/2026, Tech Lead):** app **auto-detect** MCP server phục vụ Figma theo cấu hình thật của project (không giả định tên cố định), và **luôn cho người dùng chọn lại** khi có nhiều hơn 1 server khả nghi hoặc auto-detect không chắc chắn. Đã áp dụng vào `AC-E1-25`, `AC-E1-26`, `AC-E1-27`, `AC-E2-33`, `AF-14` — không cần sửa thêm gì trong SPEC hiện có.

---

### B19 🔒 Worktree cho parallel build (AC-E2-25/26) — HOÃN CÓ CHỦ ĐÍCH

SPEC E2 yêu cầu mỗi dev agent chạy trong git worktree riêng để tránh ghi đè chéo khi FE ∥ Mobile chạy song song.

**Quyết định (17/08/2026, PM):** hoãn, chưa implement trong roadmap hoàn thiện hiện tại.

**Lý do:**
- Chuỗi orchestration từ Phase A đã là **BE → FE ∥ Mobile**, và FE/Mobile ghi vào **repo khác nhau** — phần lớn nguy cơ ghi đè chéo đã bị loại bởi chính thứ tự chạy, không cần cách ly filesystem.
- Worktree kéo theo chi phí thật: task Context trong `tasks/task-*.md` chứa **đường dẫn tuyệt đối** phải rewrite sang path worktree trước khi đưa vào prompt, và sau khi run xong cần **auto-merge** kết quả về branch chính (conflict resolution không có người). Chi phí/rủi ro chưa xứng với nhu cầu hiện tại.

**Điều kiện mở lại:** khi pipeline cần ≥ 2 dev agent ghi **cùng một repo** song song (vd 2 backend task độc lập), cân nhắc lại — lúc đó worktree là cách cách ly đúng.

---

### B20 🔒 Slack ngoài phạm vi v1 — QUYẾT ĐỊNH

E5 SPEC có 9 AC cho thông báo Slack (AC-E5-19..27) và AC-E1-19..22 nói tới credentials của **cả Backlog lẫn Slack**.

**Quyết định (18/08/2026, user):** **không làm Slack** trong bản này. Chỉ làm Backlog. Phần credentials chỉ implement cho Backlog; tab Settings › Integrations ghi rõ Slack ngoài phạm vi.

**Kéo theo:** AC-E5-19..27 = Not Implemented (không phải "thiếu sót", là phạm vi đã cắt). AC-E5-22/23 (deep-link) vì thế cũng không cần `tauri-plugin-deep-link` — app chưa đăng ký URL scheme nào.

**Điều kiện mở lại:** khi team thực sự cần thông báo chủ động thay vì tự mở app xem Board. Lúc đó cần quyết thêm về deep-link (chỉ test được trên bản đóng gói, không chạy ở dev mode macOS).

---

### B21 ⛔ Đẩy issue Backlog đi qua `pm-agent` + MCP, không gọi REST — ĐÃ BỊ THAY THẾ BỞI B24

> **Superseded (25/08/2026):** `pm-agent` đã bị gỡ khỏi kit, kéo theo toàn bộ tính năng Backlog trong app (xem **B24**). Mục này giữ lại làm hồ sơ lịch sử — nó chính là lý do việc gỡ agent PM lại kéo sập cả E5.

SPEC E5 mô tả app tự gọi Backlog API: tự fetch metadata, dựng dropdown, hiện bảng preview trong một modal riêng (`OR_INTG_001`).

**Quyết định (18/08/2026, user + Tech Lead):** phần **đẩy** đi qua `pm-agent` + MCP server `backlog` của chính project (app spawn `claude --agent pm-agent` với `cwd = agentsRoot` để CLI nạp đúng MCP config, `--add-dir <docsRoot>` để đọc task file). Phần **kéo trạng thái** vẫn gọi REST read-only.

**Lý do:**
- `mcp__backlog__*` là tool của Claude Code CLI — app đã spawn CLI sẵn, nên đường này không tốn thêm dependency và **app không đụng credentials** cho việc đẩy.
- `pm-agent.md` Bước 4 + `backlog-workflow.md` đã là nguồn quy định duy nhất. App tự implement lại = nguy cơ lệch convention, đúng thứ AC-E5-06 cấm.
- Ngược lại, **kéo trạng thái qua agent thì không thực tế**: refresh mỗi 15 phút × mỗi lần một lượt chạy `claude` = tốn tiền và mất ~30s/lần. REST read-only gần như miễn phí → giữ REST cho chiều đọc.

**Lệch AC (chấp nhận có chủ đích):**

| AC | SPEC | Thực tế |
|---|---|---|
| AC-E5-02 / AC-E5-04 | App fetch metadata, PM chọn từ dropdown trong app | `pm-agent` hỏi qua panel trả lời (agent tự gọi `get_categories`/`get_version_milestone_list`/…) — vẫn "chọn từ danh sách thật, không đoán", chỉ khác chỗ hiển thị |
| AC-E5-05 | Bảng preview đầy đủ trong app | App hiện bảng task file + phase + estimate + cảnh báo thiếu metadata; preview nội dung issue nằm trong output agent |
| AC-E5-14 | Trạng thái cạnh **task node** trên Pipeline Board | Board không có node cho từng task file (node = slot agent) → bảng task ↔ issue ↔ status nằm ở màn Backlog |
| AC-E5-01 | Nút Push chỉ bật khi **credentials đã cấu hình + test kết nối OK** | Nút bật khi feature **có task file** — đẩy không cần credentials của app (MCP server giữ credentials). Màn Backlog vẫn nhắc cấu hình vì phần *kéo trạng thái* cần API key |

**Vẫn đúng SPEC:** AC-E5-03 (5 thông tin bắt buộc — nằm trong prompt), 06 (convention), 07/08 (issue mẫu → confirm → batch), 09 (mapping `.orchestrator/backlog/<feature>/mapping.json` nhóm theo phase), 10 (agent ghi mapping sau **mỗi** issue → đứt giữa chừng vẫn tiếp tục được, không tạo trùng), 11 (prompt liệt kê task đã có issue), 12 (cảnh báo thiếu Estimate), 13 (app chỉ đọc task file), 15–18.

**Lưu ý AC-E5-15:** auto-refresh 15 phút chạy khi màn Backlog đang mở (không có background timer toàn app) — nút Làm mới thủ công luôn dùng được.

---

### B22 🔒 Pipeline chạy THỦ CÔNG hoàn toàn — bỏ auto-chain

SPEC E2 mô tả pipeline tự chạy tiếp: một node `Done` là stage sau tự spawn (`AC-E2-01..05`); duyệt Trigger Gate là 3 agent stage ② chạy luôn (`AC-E4-07`); Lock Contract là `backend-agent` chạy luôn (`AC-E4-18`).

**Quyết định (18/08/2026, user):** bỏ **cả 4** đường tự spawn. Mỗi node có nút **Run agent** riêng; không có gì tự khởi động.

**Lý do:**
- Mỗi lượt chạy tốn tiền thật. Lượt BA đầu tiên của `user-signup` tốn **$1.07** cho một lần chạy hỏng — duyệt một gate mà âm thầm chạy 3 agent nghĩa là ba lần như vậy từ một cú click, trước khi người dùng kịp xem kết quả bước trước.
- Người dùng cần đọc output của agent trước rồi mới quyết định chạy bước sau (modal artifact ở G2 phục vụ đúng việc này).

**Vẫn giữ nguyên toàn bộ luật phụ thuộc** — chỉ đảo chiều câu hỏi. `agentrun/chaining.rs` (`compute_chain_actions`: "spawn cái gì tiếp theo") được viết lại thành `agentrun/readiness.rs` (`compute_slot_readiness`: "slot này chạy được chưa"), port nguyên các test cũ: `after_slots` phải `Done`; stage trước phải hoàn tất (`Done`/`Skipped`, `DoneIncomplete` **không** tính); gate phía trước phải được duyệt; agent thiếu file `.md` thì ghi `Skipped`.

Nút Run bị mờ kèm **lý do đích danh** ("Đang chờ: qc-design", "Cần duyệt gate ④ trước"), và `run_slot` kiểm lại readiness ở backend nên UI sai cũng không cho vượt hàng.

**AC bị ảnh hưởng:** `AC-E2-01..05` (auto-chain → thủ công), `AC-E4-07` (duyệt gate không còn spawn), `AC-E4-18` (lock không còn spawn). Prompt vẫn dựng từ artifact upstream y như cũ (`build_slot_prompt`), nên "follow theo result của agent trước" không đổi.

**Điều kiện mở lại:** nếu sau này cần chạy hàng loạt không giám sát (vd chạy đêm), thêm chế độ auto **tuỳ chọn** dựng trên chính `compute_slot_readiness` — không khôi phục engine cũ.

---

### B23 📌 `pipeline.json` giờ có version + migration (phát hiện 18/08/2026)

**Triệu chứng:** node `design-analyst` hiện "Đã bỏ qua" và không có nút nào, dù file agent đã tồn tại trong kit.

**Nguyên nhân gốc (đã xác minh trên `example-project`):** `.orchestrator/pipeline.json` của project là bản ghi ngày 14/08 — **8 stage, không có 🚦 Trigger Gate, toàn bộ `dependsOn` rỗng**. `read_or_init_pipeline_def` chỉ ghi template mặc định khi file **thiếu hoặc hỏng**; file cũ vẫn parse được (serde điền default cho field mới) nên được giữ nguyên vĩnh viễn, **không version, không migration**.

Hệ quả dây chuyền: Board không có node Trigger Gate → gate chưa từng được duyệt → engine auto-chain cũ tìm stage kế bằng thứ tự danh sách (vì `dependsOn` rỗng) nên **nhảy thẳng từ BA sang cả 3 agent stage ②**, đi vòng qua gate. Đúng lúc đó `design-analyst` bị ghi `Skipped` vì fixture chưa có file agent.

**Đã vá:**
- `PipelineDef.version` + hằng `PIPELINE_DEF_VERSION` (hiện `2`; file cũ đọc ra `0`). `load_pipeline_def` phát hiện lệch → **backup `pipeline.json.v<n>.bak`** rồi ghi template hiện tại, `open_project` báo cảnh báo. Cùng khuôn `state.json.bak` (AC-E6-08) và `config.json.bak` (AC-E1-23). **Bump `PIPELINE_DEF_VERSION` mỗi khi đổi topology stage.**
- Trạng thái kết thúc có đường quay lại: node `skipped`/`blocked` mà readiness đã `Ready` trở lại thì hiện nút **Chạy lại agent** (trước đây không có nhánh UI nào cho 2 trạng thái này). Cùng gốc với gap E4-26 trong bản audit (slot `blocked` kẹt sau Re-lock).

---

### B24 🔒 Gỡ hẳn `pm-agent`, `PLAN.md` và tính năng Backlog — QUYẾT ĐỊNH (25/08/2026)

**Bối cảnh:** node PM (stage ③) đã bị loại khỏi mọi pipeline tự động từ trước — `/create-feature`, `bmad-plan-phase.js`, `bmad-build-phase.js` đều ghi rõ "không bao gồm PM". Nó chỉ còn tồn tại trên Pipeline Board như một bước phải bấm qua, sinh ra `PLAN.md` chứa timeline/estimate mà thực tế do người thật quyết.

**Quyết định (user):** gỡ **hoàn toàn** `pm-agent` khỏi kit, bỏ luôn khái niệm `PLAN.md`, và gỡ theo cả tính năng Push to Backlog trong app.

**Vì sao Backlog phải đi cùng:** theo **B21**, phần "đẩy issue" được implement bằng cách app spawn chính `pm-agent` (`commands/backlog.rs` chạy "Bước 4" của agent đó). Không còn agent thì không còn gì để spawn. Phần "kéo trạng thái" qua REST cũng mất ý nghĩa vì không còn mapping task ↔ issue để kéo về.

**Đã gỡ:**

| Lớp | Nội dung |
|---|---|
| Kit | `.claude/agents/pm-agent.md`, `.claude/commands/create-plan.md`, `.claude/commands/create-backlog.md`, `.claude/skills/project-planning/` |
| Pipeline | slot `pm` khỏi stage ③ (stage vẫn còn, chỉ còn `techlead-tasks`); `PIPELINE_DEF_VERSION` 3 → 4 |
| App — Rust | `commands/backlog.rs`, `commands/integrations.rs`, `integrations/`, `domain/integrations.rs`, `store/backlog_map.rs`, `inference/task_meta.rs`, 7 tauri command, field `backlog` trong `config.json`, dependency `reqwest` |
| App — FE | `screens/backlog/`, `screens/settings/BacklogSettings.tsx`, route + nút Push to Backlog, cảnh báo "Chưa có PLAN.md" ở Contract Lock |
| Inference | node `pm`, `plan_md_missing` (`AC-E4-09`) |
| AC không còn implement | `AC-E5-01..18` (Backlog), `AC-E4-09` (cảnh báo PLAN.md). `AC-E5-19..27` (Slack) vốn đã out-of-scope theo **B20** |

**Migration:** `store::legacy_cleanup::purge()` chạy khi mở project — xoá `nodes["pm"]` khỏi `state.json`, `agents["pm-agent"]` + `node_nicknames["pm"]` + block `backlog` khỏi `config.json`, các thư mục `agent-runs/<feature>/{pm,backlog-push}/` và cả cây `.orchestrator/backlog/`, cùng API key Backlog trong OS keychain. Idempotent, chỉ cảnh báo ở đúng lần dọn thật; file JSON hỏng thì để nguyên cho đường recovery sẵn có xử lý. `pipeline.json` tự nâng cấp qua `load_pipeline_def` (backup `pipeline.json.v3.bak`).

**Giữ lại có chủ đích:**
- Vai trò **người thật "PM"** — bảng RACI trong `POLICIES.md`, 5 ô xác nhận Contract Lock (`ALL_ROLES` vẫn có `"PM"`), quy định assignee trong `backlog-workflow.md`.
- `.claude/context/backlog-workflow.md` và MCP server `backlog` trong `.claude/settings.json` — `techlead-tasks-agent` vẫn dùng `mcp__backlog__get_categories`, và đây là quy định Backlog cho người thật.
- `docs/features/orchestrator-integrations/SPEC.md` — giữ làm hồ sơ lịch sử, có banner đánh dấu đã loại khỏi phạm vi.

---

## Nhóm C — Bảo mật (ngoài phạm vi dự án, xử lý độc lập)

### C15 ⚠️ `.mcp.json` của ESKITCHEN chứa Backlog API key plaintext

**Phát hiện:** `/Users/dipro/Work/ESKITCHEN-WORKSPACE/.mcp.json` chứa API key dạng plaintext (nội dung không được trích dẫn ở đây theo `.claude/rules/SECURITY.md`).

**Liên quan:** đây đúng là thứ F1.4 muốn dời sang OS keychain — nhưng nó là **rủi ro đang tồn tại**, không nên chờ orchestrator ra đời mới xử lý.

**Đề xuất (độc lập với dự án này):** rotate key → chuyển sang biến môi trường hoặc secret manager → verify `.mcp.json` đã nằm trong `.gitignore`. Theo `.claude/rules/POLICY.md` §9 INCIDENT_REPORTING, nếu file này từng được commit thì phải rotate + xoá khỏi git history.

---

## Quyết định đã chốt (14/08/2026)

| # | Quyết định | Người quyết | Áp dụng vào |
|---|---|---|---|
| B8 | Dùng hệ đánh số ①..⑧ của README làm canonical cho `pipeline.json` | PM | `AC-E2-01` |
| B14 | App điều phối trực tiếp từng agent, độc lập với `bmad-*.js` — không gọi `/create-feature` | PM + Tech Lead | `OVERVIEW.md` §9, Precondition E2 |
| B16 | shadcn/ui + TailwindCSS cho UI layer (sai lệch có chủ đích so với `stack-constraints.md`, chỉ áp dụng cho công cụ nội bộ này) | — (đã chốt từ đầu) | `OVERVIEW.md` §3 |
| B17 | Thêm agent mới `design-analyst-agent` vào kit; giữ nguyên `designer-agent` gốc | PM + Tech Lead | `AC-E2-33..40`, `AC-E3-04/12`, `AC-E1-*` model table |
| B18 | Auto-detect MCP Figma theo cấu hình project, luôn cho chọn lại khi mơ hồ | Tech Lead | `AC-E1-25..27`, `AC-E2-33`, `AF-14` |
| B19 *(17/08/2026)* | Hoãn worktree cho parallel build — chuỗi BE→FE∥Mobile đã giảm nguy cơ ghi chéo; mở lại khi có ≥2 dev agent cùng repo song song | PM | `AC-E2-25`, `AC-E2-26` (deferred) |
| B20 *(18/08/2026)* | Không làm Slack trong v1 — chỉ tích hợp Backlog | User | `AC-E5-19..27` (out of scope), `AC-E1-19..22` (chỉ phần Backlog) |
| B21 *(18/08/2026)* | ~~Đẩy issue qua `pm-agent` + MCP (không REST); kéo trạng thái qua REST read-only~~ — **thay thế bởi B24** | User + Tech Lead | `AC-E5-01..18` (đã gỡ) |
| B22 *(18/08/2026)* | Bỏ auto-chain — mọi node chạy bằng nút Run, gate chỉ ghi nhận duyệt | User | `AC-E2-01..05`, `AC-E4-07`, `AC-E4-18` |
| B24 *(25/08/2026)* | Gỡ hẳn `pm-agent` + `PLAN.md` + tính năng Backlog (thay thế B21) | User | `AC-E5-01..18`, `AC-E4-09` (không còn implement) |

## Bảng tổng hợp — việc còn cần quyết trước khi code

> Cập nhật 17/08/2026: A1 (resolved từ MVP1 — `AC-E1-02/03` đã implement), A5 (resolved từ MVP2 — spike đã chạy, kết quả ghi ở mục A5 ✅), A4 (đã quyết 17/08 — xem mục A4 🔒 ở trên) đã gạch khỏi bảng.

| # | Việc cần quyết | Người quyết | Chặn |
|---|---|---|---|
| **B17 (phần thực thi)** | **Viết `.claude/agents/design-analyst-agent.md`** — quyết định *cách làm* đã chốt ở trên, nhưng file agent thật vẫn chưa tồn tại. Đây là việc bổ sung vào kit, ngoài phạm vi bộ SPEC orchestrator này. *(17/08/2026: PM đã đồng ý cho đội Dipro AI Boost soạn file này — dự kiến trong Phase C của roadmap hoàn thiện app, PM review trước khi dùng thật.)* | Tech Lead của kit | **MVP 3 (stage ②c)** — spawn sẽ fail nếu chưa có file này |
| C15 | Rotate Backlog API key | Bất kỳ ai có quyền — **ngay** | — |
