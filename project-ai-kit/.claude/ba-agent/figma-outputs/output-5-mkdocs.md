# Ba Agent — Output 5: MkDocs Site

## Output 5 — MkDocs Site (SPEC published trên browser)

> Publish toàn bộ docs (SPEC + tất cả features) qua MkDocs Material để stakeholder đọc trên browser với nav, search, table of contents.
> Chạy song song trên `http://127.0.0.1:8000`.

**Kiểm tra prerequisites (1 lần đầu tiên):**

```bash
# Check mkdocs đã install chưa
which mkdocs
# Nếu chưa:
pip install mkdocs mkdocs-material mkdocs-awesome-pages-plugin
```

**Setup `mkdocs.yml` (chỉ tạo 1 lần cho project):**

Copy template từ `.claude/templates/mkdocs.yml` đến root dự án (cùng cấp `<DOCS_ROOT>`):

```bash
# Tìm parent folder của <DOCS_ROOT>
cp .claude/templates/mkdocs.yml <PROJECT_ROOT>/mkdocs.yml
# Thay <TEN_DU_AN> trong file bằng tên thật của dự án
```

**Kiểm tra `mkdocs.yml` đã có chưa** — nếu có rồi thì skip bước setup.

**Chạy dev server (mỗi lần cần preview):**

```bash
cd <PROJECT_ROOT>   # nơi có mkdocs.yml
mkdocs serve
# → http://127.0.0.1:8000
```

MkDocs sẽ tự pick up SPEC.md mới ngay khi BA save file — không cần restart server.

**Nav tự động:**
- `mkdocs-awesome-pages-plugin` scan `docs/features/<feature>/` → tự sinh nav
- Muốn đặt tên riêng cho folder: tạo `.pages` file trong folder đó
- BA không cần sửa `nav:` thủ công

**Output BA cần thông báo user:**

```
✅ MkDocs đang chạy: http://127.0.0.1:8000
   Nav → Features → <tên feature> → SPEC
   (Ctrl+C ở terminal để dừng)
```

---

## ⚠️ Rule M1 — Không cài dependency hoặc đổi version nếu chưa cần cho scope hiện tại

- ❌ KHÔNG `pip install` package MkDocs mới (theme, plugin) không có trong `.claude/templates/mkdocs.yml`
- ❌ KHÔNG upgrade version `mkdocs` / `mkdocs-material` / `mkdocs-awesome-pages-plugin` để "cho mới hơn"
- ❌ KHÔNG thêm plugin để "làm site đẹp hơn" (VD `mkdocs-git-revision-date`, `mkdocs-minify`) — không thuộc scope BA
- ✅ Chỉ cài đúng 3 package trong template: `mkdocs`, `mkdocs-material`, `mkdocs-awesome-pages-plugin`
- ✅ Nếu user thực sự muốn add plugin/theme mới → BA đề xuất, chờ user confirm rồi mới cài

**Lý do:** dependency drift → project khác không reproduce được build; version mismatch → CI có thể fail.

---

## ⚠️ Preview Verify Checklist (BẮT BUỘC trước khi báo Output 5 ✅ Done)

> Sau khi `mkdocs serve` chạy xong, BA PHẢI verify site chạy đúng trước khi báo user "MkDocs đang chạy". Không được báo blindly.

**Checklist 6 items — verify từng cái trên browser:**

- [ ] **Site load** — `http://127.0.0.1:8000` mở được, không có error page
- [ ] **Nav tree** — sidebar hiển thị đủ folder `features/<feature>/` với 4 file (SPEC.md, audit/traceability.md, audit/consistency.md, audit/approval-history.md)
- [ ] **Link internal** — click 3 link nội bộ ngẫu nhiên (từ SPEC → audit → back) không 404
- [ ] **Search** — gõ 1 keyword từ SPEC vào ô search top-right → có result hiển thị
- [ ] **Table rendering** — bảng Source Register, Traceability Matrix, Consistency Report hiển thị đủ cột, không bị vỡ layout
- [ ] **Code block rendering** — YAML block trong SPEC hiển thị đúng syntax highlight (không bị escape sai)

**Nếu bất kỳ item FAIL** → BA phải fix (thường là fix mkdocs.yml theme config hoặc file path) rồi rerun verify. KHÔNG được báo Output 5 ✅ Done khi có FAIL.

**Report format bắt buộc sau verify:**

```
✅ Preview Verify — 6/6 checks passed
  ✅ Site load
  ✅ Nav tree đủ 4 files audit/
  ✅ Link internal (3 samples PASS)
  ✅ Search "AC-05" → 3 results
  ✅ Table rendering (Source Register 12 rows, Traceability 12 rows)
  ✅ Code block YAML highlight OK

hoặc

⚠️ Preview Verify — 4/6 checks passed
  ❌ Table rendering — bảng Traceability bị vỡ layout khi width < 1024px
  ❌ Search — không index được audit/ folder (thiếu plugin?)
  → Fix trước khi báo Done
```

---

## Content bổ sung BẮT BUỘC bên trong MkDocs site — Audit + Consistency

> MkDocs không chỉ để publish SPEC. Nó còn là **audit trail** cho toàn bộ pipeline BA. 3 artifact dưới đây BẮT BUỘC được sinh trong `<DOCS_ROOT>/features/<feature>/audit/` và publish qua MkDocs — cho BRSE/PM/QC verify consistency giữa các artifact.

### A. Traceability Matrix (`audit/traceability.md`)

> Trace end-to-end từ Requirement ID → Business node → Flow transition → Screen/Item/State → Prototype test. Cho BRSE audit "requirement này đã được implement chưa và ở đâu".

```markdown
# Traceability Matrix — <feature>

> Mọi row RQ trong `## Source Register` (SPEC.md) PHẢI có 1 row ở đây, trace về artifact đã produce.

| Requirement ID | Source/evidence | Business node (Output 1) | Flow transition (Output 2 manifest) | Screen/Item/State (Output 3) | Prototype test (Output 4) | Status |
|---|---|---|---|---|---|---|
| RQ-001 | user turn 3 | STAGE: USER_INPUT | AUTH_D01 (email exists?) | AX_AUTH_001 / item ①/S05 | T02 PASS | ✅ Covered |
| RQ-002 | POLICIES §5 | STAGE: PAYMENT | PAY_D01 (elepay) | AX_PAY_001 | T08 PASS | ✅ Covered |
| RQ-003 | INFERENCE | — | — | — | — | ⚠ Not implemented (waiting BRSE) |
| RQ-004 | UNKNOWN | — | — | — | — | ❌ Blocked (chờ user answer) |
```

**Rule:**
- Số row = số row trong `## Source Register` SPEC.md
- Row status `⚠ Not implemented` cho `INFERENCE/PROPOSAL` chưa approve
- Row status `❌ Blocked` cho `UNKNOWN/CONFLICT` — list vào Known Gaps
- 100% row `FACT` PHẢI có status `✅ Covered` — nếu không → Quality Gate O5 FAIL

### B. Final Consistency Report (`audit/consistency.md`)

> 4 check chéo giữa các artifact. Chống drift khi user update nhiều lần scoped.

```markdown
# Final Consistency Report — <feature>

| # | Check | Expected | Actual | PASS/FAIL | Action required |
|---|---|---|---|---|---|
| C1 | Requirement (Source Register) → Business Overview Flow (Output 1) | Mọi RQ `FACT` in-scope xuất hiện ở ≥ 1 node Output 1 | <đếm cụ thể — VD: 12/12 covered> | ✅ PASS | — |
| C2 | Business Overview (Output 1) → Screen Flow Manifest (Output 2) | Số business flows Output 1 = số screen-flow groups Output 2 | 5 flows = 5 groups | ✅ PASS | — |
| C3 | Screen Flow Manifest (Output 2) → Screen Spec (Output 3 tables) | Mọi transition ID trong Manifest có row trong Navigation Mapping | 18/18 transition có mapping | ✅ PASS | — |
| C4 | Screen Spec (Output 3) → HTML Prototype (Output 4) | Mọi action Navigation Mapping có 1 test row PASS trong Interaction Test Report | 18 transitions → 18 tests PASS | ✅ PASS | — |
```

**Rule:**
- Bất kỳ FAIL nào → Quality Gate O5 FAIL, BA phải quay lại output tương ứng fix rồi rerun (theo Scoped Update rule POLICIES.md §4.6)
- BA KHÔNG được tự sửa artifact upstream khi C1-C4 FAIL — phải notify user + đợi approve mở rộng scope

### C. Approval History + Known Gaps (`audit/approval-history.md`)

> Log lịch sử approve cho từng output + list mọi gap chưa resolve.

```markdown
# Approval History — <feature>

## Timeline

| Timestamp | Output | Version | Approver | Note |
|---|---|---|---|---|
| 2026-09-14 10:30 | O1 Flow Tổng Quan | v1 | BRSE Tanaka | Approved |
| 2026-09-14 11:45 | O2 Screen Flow | v1 | BRSE Tanaka | Approved with note "check EX-03 payment timeout" |
| 2026-09-14 14:20 | O2 Screen Flow | v2 | BRSE Tanaka | Re-approved sau fix EX-03 |
| 2026-09-15 09:00 | O3 Screens + Items | v1 | BRSE Tanaka | Approved |
| 2026-09-15 15:30 | O4 HTML Prototype | v1 | BRSE Tanaka | Approved |

## Known Gaps (chưa resolve tại thời điểm final approve)

| Gap ID | Type | Description | Impact | Owner | Target resolve |
|---|---|---|---|---|---|
| GAP-01 | UNKNOWN | RQ-003 refund window chưa confirm | Không viết được AC refund | BRSE | Before Phase 3 |
| GAP-02 | INFERENCE | EX-04 push deny fallback SMS chưa verify | User có thể miss OTP | PM | Before Phase 3 |
```

**Rule:**
- Mọi `WAITING_APPROVAL` → `APPROVED` transition PHẢI thêm 1 row vào Timeline (do BA tự log khi user reply Approve)
- Known Gaps = mọi row Source Register có classification `UNKNOWN / CONFLICT` + row Exception Matrix classification `INFERENCE / UNKNOWN` chưa resolve
- Final Approval Gate BLOCK nếu có `UNKNOWN/CONFLICT` blocking chưa có owner + target resolve

---

## Final Consistency Gate O5 (BẮT BUỘC trước khi báo Output 5 ✅ Done)

Block xuất ra khi hoàn thành:

```
✅ Output 5 — MkDocs Site published: http://127.0.0.1:8000
Audit artifacts:
  - Traceability Matrix: <DOCS_ROOT>/features/<feature>/audit/traceability.md
  - Consistency Report: <DOCS_ROOT>/features/<feature>/audit/consistency.md
  - Approval History: <DOCS_ROOT>/features/<feature>/audit/approval-history.md

Consistency Gate: <PASS / FAIL>
Known Gaps: <N gaps — X blocking, Y non-blocking>
Status: <WAITING_FINAL_APPROVAL / FINAL_APPROVED>
```

**PASS condition:**
- Traceability: 100% RQ `FACT` có status `✅ Covered`
- Consistency C1-C4: đủ 4 PASS
- Known Gaps: mọi `UNKNOWN/CONFLICT` blocking có owner + target resolve

**FAIL condition:** Bất kỳ tiêu chí trên FAIL → BA in list issues, KHÔNG chuyển state = `FINAL_APPROVED`, đợi user chỉ đạo fix.
