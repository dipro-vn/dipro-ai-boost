# AI Agents Workflow — Đọc gì · Thực thi gì · Output gì

> **Mục đích:** tài liệu tra cứu nhanh **cho user/PM (human)** audit từng agent làm gì trong pipeline BMAD. Nội dung tổng hợp từ 12 file trong `.claude/agents/`. Khi sửa workflow của agent nào → **sửa file agent tương ứng, không sửa file này** (sync lại sau).
>
> **Không phải canonical** — canonical là `.claude/agents/<agent>.md`. File này chỉ là bản tổng hợp.
>
> **Vị trí:** đặt ở root `project-ai-kit/` (không phải trong `.claude/`) — cố ý để agents không auto-load. Chỉ human đọc khi cần audit / onboarding developer mới.

---

## 1. Bảng tổng quan — Phase-Gate

| # | Phase | Agent | Trigger | Song song với |
|---|---|---|---|---|
| 0 | Setup | `init-agent` | `/init-kit` (1 lần) | — |
| 1 | Discovery | `ba-agent` | `/create-spec <feature>` | — |
| 2a | Design | `techlead-design-agent` | `/create-design <SPEC.md>` | 2b, 2c |
| 2b | Design | `qc-agent` (manual TC lần 1) | Pipeline: `/test/analyze-req` → `/test/plan-tcs` → `/test/gen-tcs` | 2a, 2c |
| 2c | Design | `designer-agent` | `/create-ui-design <SPEC.md>` | 2a, 2b |
| 3 | Planning | `techlead-tasks-agent` | `/create-tasks <feature/>` | — |
| 4a | Build | `backend-agent` | Implement task Phase 1 → 2 | — |
| 4b | Build | (manual) copy API Contract → task-3-x | — | — |
| 4c | Build | `frontend-agent` | Implement task Phase 3 | 4d |
| 4d | Build | `mobile-agent` | Implement task Phase 3 | 4c |
| 4e | Integration | BE + FE + Mobile | task-4-x integration test | — |
| 5 | Verify | `qa-agent` | `"Hãy là QA, verify task: <path>"` | — |
| 6a | Test | `qc-agent` (execution lần 2) | `/test/generate_test_execution_checklist` | 6c |
| 6b | Test | `qc-agent` (regression optional) | `/test/generate_regression_suite` | — |
| 6c | Test | `qc-automation-agent` | `"Hãy là QC Automation, test feature: ..."` | 6a |

> **On-demand (không thuộc phase-gate):** `/test/review-tcs` (deep review khi ≥2 QC) · `/test/export-xlsx <path> web\|app` (Excel bàn giao) · `/test/gen-bug-report` (bug template).

**Handover chain:** natural language (copy-paste vào turn kế tiếp) hoặc slash command — cả hai cùng load file agent.

---

## 2. Nguyên tắc chung

| Rule | Áp dụng cho |
|---|---|
| Bước 1 = đọc context + skill trước khi hành động | Mọi agent |
| Chỉ tạo/sửa `.md` (trừ Dev) | BA, Tech Lead, QC, QA, Designer, QC-Auto |
| `tilth_deps` blast radius BẮT BUỘC trước khi đổi public interface | Tech Lead Design, Tech Lead Tasks, Backend, Frontend, Mobile |
| Không tự đoán khi thiếu context — phải hỏi user | Mọi agent |
| Handover message = natural language + slash command song song | Mọi agent |
| Không commit / push khi user không yêu cầu rõ ràng | Mọi agent (đặc biệt Dev) |

---

## 3. Chi tiết per agent

> Mỗi flowchart mô tả trình tự **Đọc → Query/Check → Thực thi → Handover** cho 1 agent. Chi tiết đầy đủ (danh sách file đọc chính xác, template output, danh sách "Không được làm") → xem `.claude/agents/<agent-name>.md`.

### 3.0 `init-agent` — Kit Setup Assistant

```mermaid
flowchart TD
    A[User: /init-kit] --> B[Đọc AGENTS.md root<br/>check placeholder Ecosystem]
    B --> C{Đã init trước đó?}
    C -- Có --> D[Hỏi user chọn a/b/c<br/>a: overwrite<br/>b: merge phần thiếu<br/>c: cancel]
    C -- Chưa --> E[Hỏi 8 câu setup:<br/>1 Tên dự án + domain<br/>2 Docs root path<br/>3 Repos + vai trò + stack<br/>4 Epic code per repo<br/>5 Actors/personas<br/>6 Payment/integration<br/>7 Gotchas 2 repo dễ nhầm<br/>8 Cross-repo features]
    D --> E
    E --> F[Ghi AGENTS.md +<br/>context/specification.md +<br/>context/technical.md +<br/>rules/project-structure.md]
    F --> G{Stack khác default?}
    G -- Có --> H[Update rules/stack-constraints.md]
    G -- Không --> I{Payment thay đổi?}
    H --> I
    I -- Có --> J[Update POLICIES.md §5]
    I -- Không --> K[Bàn giao BA<br/>/create-spec feature-đầu-tiên]
    J --> K
```

**❌ Không:** sửa source code · ghi đè khi đã init (phải hỏi user a/b/c).

---

### 3.1 `ba-agent` — Business Analyst

```mermaid
flowchart TD
    A["User: /create-spec &lt;feature&gt;"] --> B[Đọc context/specification.md +<br/>doc-structure.md +<br/>skill business-analyst]
    B --> C["tilth_files SPEC.md +<br/>đọc business-flow-index.md +<br/>outline ## Mô tả nghiệp vụ SPEC hiện có"]
    C --> D{Có SPEC liên quan?}
    D -- Có --> E[User chọn related SPEC<br/>→ đọc full]
    D -- Không --> F[Hỏi 10 câu discovery:<br/>actor · problem · precondition ·<br/>happy path · edge case · AC ·<br/>related · mobile · real-time · integration]
    E --> F
    F --> G{Đủ thông tin?}
    G -- Không --> H[Hỏi user - KHÔNG tự đoán]
    H --> F
    G -- Đủ --> I["Viết SPEC.md:<br/>Mô tả nghiệp vụ · Actors ·<br/>Happy/Alt/Edge · AC ·<br/>Out of Scope · Screens table<br/>(Code+Screen+Actor+App+Type+Figma Link)"]
    I --> J[Bàn giao SONG SONG:<br/>Tech Lead Design 2a +<br/>Designer 2c +<br/>QC 2b]
```

**❌ Không:** đưa giải pháp kỹ thuật · sửa source code · skip Bước 1.5 scan SPEC cũ.

---

### 3.2 `techlead-design-agent` — Tech Lead Design

```mermaid
flowchart TD
    A["/create-design &lt;SPEC.md&gt;"] --> B[Đọc SPEC.md +<br/>context/technical.md +<br/>doc-structure.md +<br/>skill solution-architect]
    B --> C{SPEC ## Screens<br/>có Figma URL?}
    C -- Có --> D[get_design_context +<br/>get_screenshot]
    C -- Không --> E[Map nghiệp vụ → repo<br/>theo bảng Ecosystem]
    D --> E
    E --> F[tilth_search + tilth_read<br/>pattern hiện có]
    F --> G[BẮT BUỘC tilth_deps<br/>blast radius]
    G --> H{SPEC mơ hồ?}
    H -- Có --> I[Hỏi user - KHÔNG tự đoán]
    I --> H
    H -- Không --> J[Viết DESIGN.md per repo — 7 sections:<br/>1 Tổng quan · 2 Database Changes ·<br/>3 API Definition Contract Lock ·<br/>4 Service Layer · 5 Interface cross-repo ·<br/>6 Luồng xử lý · 7 Non-Regression Risks]
    J --> K[Bàn giao Tech Lead Tasks<br/>sau khi Designer có Figma URL]
```

**❌ Không:** viết source code · tự đoán khi SPEC mơ hồ · bypass `tilth_deps`.

---

### 3.3 `qc-agent` — QC Manual Tester

> **Chạy 3 lần trong pipeline:** lần 1 = sinh TC sau SPEC (2b — pipeline 3 bước) · lần 2 = execution checklist trước release (6a) · lần 3 song song với 6c (QC Automation).

```mermaid
flowchart TD
    A[QC được gọi] --> B{Lần thứ mấy?}

    B -- "Lần 1: sau SPEC (2b)" --> C[Đọc SPEC.md +<br/>skill rbt_manual_testing]
    C --> C1["/test/analyze-req<br/>Q&amp;A + AC + Screen Inventory"]
    C1 --> C2{User confirm?}
    C2 -- Chưa --> C1
    C2 -- OK --> C3["/test/plan-tcs<br/>Screen → Component + Risk + Technique"]
    C3 --> C4{User confirm?}
    C4 -- Chưa --> C3
    C4 -- OK --> C5["/test/gen-tcs<br/>TC chi tiết + Visual states +<br/>Traceability ID → AC-XX"]
    C5 --> C6["Output: test-cases/&lt;module&gt;/<br/>{analysis, plan-tcs, test-cases}.md"]

    B -- "Lần 2: pre-release (6a)" --> D["/test/generate_test_execution_checklist"]
    D --> D1[Output: checklist_release.md]

    B -- "Lần 3: song song 6c" --> E[Cross-check với E2E<br/>của qc-automation-agent]

    C6 --> F{On-demand?}
    F -- ≥2 QC review chéo --> F1["/test/review-tcs (8 tiêu chí)"]
    F -- Bàn giao Excel --> F2["/test/export-xlsx &lt;path&gt; web|app"]
    F -- Sau code change --> F3["/test/generate_regression_suite"]
    F -- Có bug --> F4["/test/gen-bug-report"]
```

**❌ Không:** sinh TC khi chưa đọc SPEC · test data placeholder · gộp validation nhiều field · auto-submit bug lên Backlog · lẫn vai trò với `qa-agent` (không chạy test suite) · gọi thẳng `/gen-tcs` khi chưa có `plan-tcs.md` · skip user confirm giữa các bước pipeline.

---

### 3.4 `designer-agent` — UI/UX Designer

```mermaid
flowchart TD
    A["/create-ui-design &lt;SPEC.md&gt;"] --> B[Đọc SPEC.md +<br/>context/designer-context BẮT BUỘC +<br/>rules/design_rule.md +<br/>skill figma-design +<br/>MCP skills figma-use / figma-generate-design]
    B --> C["Phân tích ## Screens"]
    C --> D[search_design_system 10 components:<br/>Sidebar · Header · Table · Button ·<br/>Input · DatePicker · StatusBadge ·<br/>Pagination · Modal · Icon]
    D --> E[get_design_context + get_metadata +<br/>get_variable_defs của reference screen]
    E --> F{Thiếu component<br/>trong design system?}
    F -- Có --> G[GATE - DỪNG<br/>hỏi user chọn:<br/>A dùng component thay thế + note<br/>B tạo component mới<br/>C skip screen]
    G --> F
    F -- Không --> H[Import component instance +<br/>tạo frame HIGH-FIDELITY +<br/>bind variables +<br/>fill sample data thật]
    H --> I["Update SPEC.md ## Screens<br/>điền cột Figma Link"]
    I --> J{Phát hiện gap?}
    J -- Có --> K["Append [Design] notes<br/>vào SPEC ## Open Questions"]
    J -- Không --> L[Bàn giao Tech Lead Tasks<br/>chờ DESIGN.md xong<br/>FE/Mobile đọc Figma URL từ task]
    K --> L
```

**❌ Không:** tạo file `.md` riêng (UI-SPEC.md / figma-context.md) · vẽ wireframe (rectangle + text) · tự generate component khi thiếu · commit / push code.

---

### 3.5 `techlead-tasks-agent` — Tech Lead Tasks

```mermaid
flowchart TD
    A["/create-tasks &lt;feature/&gt;"] --> B["Đọc tilth_files */DESIGN.md +<br/>doc-structure.md +<br/>skill task-decomposition +<br/>SPEC ## Screens (Code + Figma URL)"]
    B --> C{Cần estimate complexity?}
    C -- Có --> D[get_metadata + get_screenshot]
    C -- Không --> E[tilth_search + tilth_read +<br/>tilth_deps blast radius]
    D --> E
    E --> F["Map repo → Backlog Category +<br/>ROLE tag [BE] / [FE]"]
    F --> G[Phase numbering:<br/>1 DB migration<br/>2 Service + API<br/>3 FE + Mobile song song 3 sub-steps<br/>4 Integration test]
    G --> H[Estimate 4-8h per task]
    H --> I{Task &gt; 8h?}
    I -- Có --> J[Chia nhỏ]
    J --> H
    I -- Không --> K{DESIGN mơ hồ?}
    K -- Có --> L[Hỏi user - KHÔNG tự đoán]
    L --> K
    K -- Không --> M["Viết task-{phase}-{index}.md:<br/>Backlog Info · Metadata · Mục tiêu ·<br/>Context · Yêu cầu implement ·<br/>Unit Tests BẮT BUỘC ·<br/>API Definition (Phase 2) ·<br/>Non-Regression Table · Không được làm · DoD"]
    M --> N[Bàn giao Contract Lock<br/>trước khi Dev Phase 3]
```

**❌ Không:** task > 8h · task thiếu Unit Test · tự đoán khi DESIGN mơ hồ · sửa source code.

---

### 3.6 `backend-agent` — Backend Developer (NestJS)

```mermaid
flowchart TD
    A[Nhận task-x-y.md] --> B[Đọc task + SPEC + DESIGN +<br/>skill nestjs-best-practices +<br/>postgresql SKILL<br/>+ redis-development nếu có cache]
    B --> C{API response cần khớp UI?}
    C -- Có --> D[get_design_context + get_screenshot]
    C -- Không --> E[tilth_search pattern +<br/>tilth_deps blast radius]
    D --> E
    E --> F[Implement:<br/>module · service · entity ·<br/>DTO class-validator · migration up/down ·<br/>guard · interceptor]
    F --> G[Chạy npm run lint + test + test:cov]
    G --> H{≥80% service<br/>≥70% controller?}
    H -- Không --> F
    H -- OK --> I[Self-review checklist:<br/>snake_case column ·<br/>migration up+down ·<br/>không N+1 · Redis TTL ·<br/>không hard-code secret]
    I --> J["Output: Code +<br/>API Contract table (handoff) +<br/>Memory Update Gate:<br/>api-catalog.md / erd.md / patterns.md"]
    J --> K[Bàn giao QA verify]
    K --> L{QA PASS?}
    L -- FAIL --> F
    L -- PASS --> M[Copy API Contract<br/>vào task-3-x FE/Mobile]
    M --> Z[STOP — dừng session,<br/>không tự hỏi thêm xác nhận<br/>trừ khi thiếu thông tin thật]
```

**❌ Không:** sửa migration / linter / test config không được yêu cầu · commit khi không được yêu cầu · hard-code secret · N+1 query.

---

### 3.7 `frontend-agent` — Frontend Developer (React)

```mermaid
flowchart TD
    A[Nhận task-x-y.md] --> B[BẮT BUỘC đọc BE task-2-X.md<br/>lấy API Contract<br/>KHÔNG tự đoán endpoint]
    B --> C[Đọc SPEC + DESIGN +<br/>skill react-expert + frontend-review]
    C --> D{Có Figma URL<br/>trong task/SPEC/user paste?}
    D -- Có --> E[SONG SONG 4 tools:<br/>get_metadata + get_design_context +<br/>get_variable_defs + get_screenshot]
    D -- Không --> F[tilth_search pattern hiện có]
    E --> F
    F --> G["Step 1: src/services/&lt;feature&gt;Api.ts"]
    G --> H["Step 2: src/hooks/use&lt;Feature&gt;.ts<br/>TanStack Query v5 object syntax"]
    H --> I["Step 3: src/pages/&lt;Feature&gt;Page.tsx<br/>wire hooks vào UI"]
    I --> J[Chạy lint + type-check +<br/>build + test --coverage]
    J --> K{≥70% coverage?}
    K -- Không --> G
    K -- OK --> L[Integration check localhost<br/>BE + FE]
    L --> M[Memory Update Gate:<br/>patterns.md per repo]
    M --> N[Bàn giao QA verify]
```

**❌ Không:** hard-code URL (dùng `import.meta.env.VITE_API_URL`) · tự đoán endpoint · mock data trong production code · lẫn domain giữa 2 repo frontend · `useHistory` (dùng `useNavigate`) · Redux cho server state.

---

### 3.8 `mobile-agent` — Mobile Developer (Flutter)

```mermaid
flowchart TD
    A[Nhận task-x-y.md] --> B[Đọc task + SPEC + DESIGN +<br/>skill flutter-review]
    B --> C{Có Figma URL?}
    C -- Có --> D[SONG SONG 4 tools:<br/>get_metadata + get_design_context +<br/>get_variable_defs + get_screenshot]
    C -- Không --> E[tilth_search pattern hiện có]
    D --> E
    E --> F["Implement:<br/>hooks_riverpod + Retrofit @RestApi +<br/>freezed model + auto_route +<br/>Socket.IO cleanup"]
    F --> G[Chạy flutter analyze + flutter test]
    G --> H{≥75% provider coverage?}
    H -- Không --> F
    H -- OK --> I["Self-review:<br/>chỉ Riverpod (không Provider/BLoC/GetX) ·<br/>không Dio trực tiếp (chỉ qua Retrofit) ·<br/>socket off() trong dispose ·<br/>flutter_screenutil .w/.h/.sp"]
    I --> J[Memory Update Gate:<br/>structure.md · patterns.md]
    J --> K[Bàn giao QA verify]
```

**❌ Không:** Provider/BLoC/GetX · hard-code pixel/hex · sửa `.g.dart`/`.freezed.dart` thủ công · đảo version convention (DEV `0.0.x` · STG `0.1.x` · PROD `1.0.x`) · `Navigator.push` trực tiếp.

---

### 3.9 `qa-agent` — QA Engineer

```mermaid
flowchart TD
    A["Hãy là QA verify task: &lt;path&gt;"] --> B["Đọc task-x-y.md (coverage target + Non-Regression) +<br/>SPEC AC + ## Screens +<br/>skill requirements_analyzer"]
    B --> C{Verify UI?}
    C -- Có --> D[get_screenshot + get_design_context<br/>đối chiếu code thực]
    C -- Không --> E["Chạy per repo:<br/>NestJS: npm run test:cov<br/>React: type-check + build + test<br/>Flutter: flutter analyze + test"]
    D --> E
    E --> F[Validate từng AC:<br/>happy + edge + boundary<br/>đối chiếu AC ID cụ thể từ SPEC]
    F --> G[Check Non-Regression table<br/>từ task-x-y.md]
    G --> H["Viết QA Report:<br/>Test Results (unit/coverage/lint/build) ·<br/>AC table (pass/fail per AC + lý do) ·<br/>Non-Regression table · Kết luận"]
    H --> I{Kết luận?}
    I -- FAIL --> J[Issue list file:line +<br/>đề xuất fix →<br/>quay lại Dev]
    J --> E
    I -- PASS --> K[Status Testing Request →<br/>QC execution checklist 6a]
```

**❌ Không:** sửa source code · sinh manual TC (qc-agent việc) · so với assumption thay vì SPEC · thay đổi test cases đã approve.

---

### 3.10 `qc-automation-agent` — QC Automation Tester

```mermaid
flowchart TD
    A["Hãy là QC Automation<br/>test feature: &lt;path&gt;, Figma: &lt;url&gt;"] --> B["Preflight:<br/>&lt;e2e-repo&gt;/.env.test tồn tại +<br/>&lt;ROLE&gt;_URL env +<br/>curl probe website +<br/>npx playwright --version"]
    B --> C{Có &lt;testcases&gt; TC file?}
    C -- "Có (TC-driven)" --> D[Đọc TC file<br/>KHÔNG tự thêm scenario]
    C -- "Không (SPEC-driven)" --> E["Đọc SPEC:<br/>Actors · Preconditions ·<br/>Out of Scope · Screen Code"]
    D --> F[get_design_context + get_screenshot<br/>extract labels cho selectors:<br/>button · placeholder · heading · toast]
    E --> F
    F --> G{Chế độ?}
    G -- SPEC-driven --> H[Max 10 scenarios lần đầu<br/>để đảm bảo chất lượng]
    G -- TC-driven --> I[1 scenario per TC file]
    H --> J["Sinh .spec.ts per TC (1 file = 1 TC):<br/>storageState + getByRole /<br/>getByPlaceholder / getByText / getByTestId"]
    I --> J
    J --> K["Chạy: npx playwright test --headed<br/>--project=&lt;target-app&gt; --no-deps"]
    K --> L[Parse output]
    L --> M["Output:<br/>&lt;e2e-repo&gt;/e2e/&lt;target-app&gt;/&lt;feature&gt;/*.spec.ts +<br/>reports/&lt;feature&gt;/execution-report.md<br/>(PASS/FAIL/SKIP + screenshots FAIL +<br/>Lỗi cần xử lý + Bước tiếp theo)"]
```

**❌ Không:** sửa source code app · CSS class selector (`.btn-primary`) · `waitForTimeout` cứng · hard-code credentials trong `.spec.ts` (dùng `process.env`) · > 20 TC lần đầu (SPEC-driven) · test phụ thuộc nhau · TC-driven mà tự thêm scenario.

---

## 4. Điểm audit thường gặp

| # | Điểm cần check | Cách verify |
|---|---|---|
| 1 | BA có scan SPEC cũ trước khi tạo mới không? | `ba-agent.md` Bước 1.5 phải có `business-flow-index.md` + outline SPEC + hỏi user related feature |
| 2 | Tech Lead có `tilth_deps` blast radius không? | DESIGN.md ## 7 Non-Regression Risks phải có nội dung thật, không placeholder |
| 3 | Task có Unit Test không? | Mỗi task-x-y.md phải có section "Unit Tests (BẮT BUỘC)" với coverage target |
| 4 | FE có tự đoán endpoint không? | task-3-x.md ## API Contract phải copy từ BE task-2-X, không tự viết |
| 5 | Designer có vẽ wireframe hay không? | Verify: mỗi frame Figma phải dùng component instance, không rectangle + text |
| 6 | QA có so với SPEC.md AC hay assumption? | QA Report phải trích AC ID cụ thể từ SPEC, không mô tả chung |
| 7 | QC Automation có headed mode không? | `execution-report.md` phải có screenshot; command có `--headed` |
| 8 | Memory Update Gate có bị skip không? | Sau mỗi dev task, output phải liệt kê `api-catalog.md` / `erd.md` / `patterns.md` — updated hay skipped |
| 9 | Handover message có natural language không? | Output cuối mỗi agent phải có `"Hãy là <role>, ..."` để user copy-paste |
| 10 | Agent có commit tự động không? | KHÔNG được — chỉ commit khi user yêu cầu rõ ràng |
| 11 | QC có chạy `/plan-tcs` trước `/gen-tcs` không? | `/gen-tcs` sẽ tự dừng nếu module chưa có `plan-tcs.md` — verify không skip bằng cách gọi thẳng `/gen-tcs` |
| 12 | QC có handle TBD ACs đúng không? | `/gen-tcs` phải hỏi user chọn A/B/C khi phát hiện TBD AC, không tự đoán |

---

## 5. Common failure modes

| Failure | Nguyên nhân | Cách phòng |
|---|---|---|
| BA sinh SPEC trùng lặp | Bỏ qua Bước 1.5 SPEC scan | Enforce trong `ba-agent.md` — không skip được |
| Tech Lead design conflict với code hiện có | Không chạy `tilth_deps` | Rule cứng trong POLICIES.md — vi phạm phải rollback |
| FE code với endpoint không tồn tại | Không đọc BE task-2-X ## API Contract | Frontend Agent Bước 2 BẮT BUỘC đọc BE task |
| QC Automation sinh selector CSS class | Không đọc Figma labels | qc-automation-agent Bước 3 đọc Figma trước khi viết spec |
| QA PASS nhưng vẫn miss AC | So với assumption thay vì SPEC | qa-agent Bước 3 đối chiếu AC ID từ SPEC.md |
| Task quá lớn, dev không xong trong session | techlead-tasks-agent ước lượng sai | Enforce 4-8h/task, chia nhỏ nếu > 8h |
| QC gọi thẳng `/gen-tcs` khi chưa có `plan-tcs.md` | Skip pipeline steps | Command tự dừng + hướng dẫn quay lại `/plan-tcs` |
| Test data placeholder ("email hợp lệ") lọt vào TC | `/gen-tcs` self-check yếu | Self-check tự grep placeholder, tự fix trước khi lưu |

---

## 6. Xem thêm

- **Canonical workflow từng agent:** `.claude/agents/<agent-name>.md`
- **BMAD pipeline chi tiết:** `.claude/workflows/new-feature.md`
- **Bug fix workflow:** `.claude/workflows/bug-fix.md`
- **AI behavior policy:** `POLICIES.md` (always-loaded qua `CLAUDE.md`)
- **Companion rules:** `.claude/rules/SECURITY.md` (restricted files) · `POLICY.md` (IP protection) · `RELIABILITY.md` (no hallucination)
- **Ecosystem (repos + actors + docs root):** `AGENTS.md` section `<ecosystem>`
- **Context files:** `.claude/context/` (đọc on-demand theo cột "Ai đọc" trong `AGENTS.md`)
- **Skills:** `.claude/skills/README.md`
- **Commands:** `.claude/commands/README.md`
- **QC pipeline 4 bước chi tiết:** `.claude/agents/qc-agent.md` — section "Quy trình chuẩn"
