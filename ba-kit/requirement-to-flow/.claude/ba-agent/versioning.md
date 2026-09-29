# BA Agent — Versioning & Snapshot (Bước 3)

> **Scope:** Folder structure + 5 rule versioning + template `ba-outputs-log.md`.
> **Dùng ở:** `ba-agent.md` Bước 3 và Output section (snapshot trước Report cuối). Agent body chỉ giữ 3-5 dòng note + reference file này.

---

## Folder structure (canonical + versions)

**Canonical path (LATEST)** cho mọi feature: `<output-folder>/`

```
<output-folder>/
├── SPEC.md                         ← latest (downstream agent Read từ đây)
├── prototype/index.html            ← latest HTML prototype
└── versions/                       ← snapshot mỗi lần BA chạy (feedback + so sánh lịch sử)
    ├── v1_<DDMMYYYY>/
    │   ├── SPEC.md                 ← snapshot SPEC lần chạy này
    │   ├── ba-outputs-log.md       ← record 5 outputs (path SPEC + 3 Figma URL + HTML path + ghi chú)
    │   ├── prototype/index.html    ← snapshot HTML (nếu có change)
    │   ├── basic_design_before.xlsx  ← BẮT BUỘC khi chạy Output 5: bản master TRƯỚC khi ghi
    │   ├── basic-design-gate.md      ← report Quality Gate O5 (chỉ khi chạy Output 5)
    │   ├── feedback-triage.md        ← BẮT BUỘC khi version này sinh từ Bước 7 (bảng triage CR/FEEDBACK + câu trả lời gate)
    │   ├── output_cr.md              ← BẮT BUỘC khi có item CR (nhiều CR → output_cr_<ID>.md)
    │   ├── OQ-REGISTER.md            ← BẮT BUỘC khi còn open question (Output OQ)
    │   ├── open_questions.xlsx       ← BẮT BUỘC khi còn open question — bản giao KH
    │   └── oq-export.md              ← report gate của export-open-questions.py
    ├── v2_<DDMMYYYY>/
    │   └── ...
    └── ...
```

---

## Rule versioning (BẮT BUỘC — không skip)

### Rule 1 — Trước khi bắt đầu BA workflow

Check `versions/` folder:
- Nếu CHƯA có → sẽ tạo `versions/v1_<DDMMYYYY>/` sau khi hoàn thành
- Nếu ĐÃ có → xác định `N` version tiếp theo (VD đã có `v3_...` → lần này là `v4_...`)

### Rule 2 — Sau khi hoàn thành 5 outputs (trước Report cuối)

Snapshot vào `versions/v<N>_<DDMMYYYY>/`:
- `cp SPEC.md versions/v<N>_<DDMMYYYY>/SPEC.md`
- Tạo `versions/v<N>_<DDMMYYYY>/ba-outputs-log.md` với bảng 5-row (path SPEC + 3 Figma URL + HTML path) + ghi chú thay đổi so với version trước (nếu có)

### Rule 2b — Output 5 (Basic Design): backup TRƯỚC khi ghi, không phải sau

> File Excel là binary — **không có git diff để rollback**. `openpyxl` không bảo toàn 100% conditional formatting, một số merged range, chart và macro.

Trước **bất kỳ** thao tác ghi nào vào master workbook:

```bash
cp "<master.xlsx>" "versions/v<N>_<DDMMYYYY>/basic_design_before.xlsx"
```

- Chưa có file backup → **KHÔNG được ghi**. Đây là điều kiện cứng, không phải khuyến nghị.
- Bản backup này cũng là input `--before` của Quality Gate O5 (`verify-basic-design.py`) — không có nó thì 3 trong 10 check chỉ chạy được ở mức `WARN`.
- Report của gate lưu cùng chỗ: `versions/v<N>_<DDMMYYYY>/basic-design-gate.md`
- Copy `prototype/index.html` → `versions/v<N>_<DDMMYYYY>/prototype/index.html` (nếu HTML có thay đổi so với version trước)

### Rule 2c — Version sinh từ Bước 7 (Feedback / CR)

> Feedback và CR **luôn** tạo version mới — không bao giờ sửa đè `v<N>` đang có. `v<N>` là bằng chứng "baseline trước thay đổi", cần để đối chiếu khi trao đổi KH.

| Trigger | Bắt buộc có trong `v<N+1>_<DDMMYYYY>/` |
|---|---|
| 🟡 FEEDBACK | `SPEC.md` (sau scoped update) · `feedback-triage.md` · `ba-outputs-log.md` (Trigger = FEEDBACK) · `prototype/` nếu có đổi |
| 🔴 CR | `output_cr.md` · `feedback-triage.md` (kèm block giải trình "vì sao là CR") · `ba-outputs-log.md` (Trigger = CR + CR view URL) · `SPEC.md` (chỉ update phần KH đã chốt) |

- Feedback **gốc** ghi vào `versions/v<N>_<DDMMYYYY>/ba-outputs-log.md` section "Feedback" (version nơi feedback phát sinh); **kết quả xử lý** ghi ở `v<N+1>`.
- CR chưa được KH chốt → KHÔNG ghi vào `## Happy Path` / `## Acceptance Criteria`; ghi `CR-<ID>: chờ KH xác nhận` vào `## Ambiguities`.
- Chi tiết 2 nhánh: `.claude/ba-agent/post-meeting-workflow.md` và `.claude/ba-agent/change-request.md`.

### Rule 2d — Output OQ (Open Questions): canonical + snapshot

Canonical (LATEST) nằm ngoài `versions/` để user luôn mở đúng bản mới nhất:

```
<output-folder>/open-questions/
├── OQ-REGISTER.md        ← source of truth (markdown, BA viết)
└── open_questions.xlsx   ← bản giao KH (do export-open-questions.py sinh, KHÔNG gõ tay)
```

Mỗi lần chạy: copy `OQ-REGISTER.md` + `open_questions.xlsx` + `oq-export.md` (report gate) vào `versions/v<N>_<DDMMYYYY>/`.

- OQ ID **không đánh lại số** giữa các version — `OQ-03` ở v2 vẫn là `OQ-03` ở v3 để trace lịch sử trả lời.
- Câu đã được trả lời → chuyển sang `FACT` trong SPEC `## Source Register`, xoá khỏi bảng OQ ở version sau, và ghi 1 dòng trong `Diff so với version trước` (VD `OQ-03 đã chốt: huỷ đơn sau 15 phút`).
- `ba-outputs-log.md` ghi `Figma OQ view: DRAW` hoặc `SKIP (n > 20)` — không để trống.
- Chi tiết rule: `.claude/ba-agent/open-questions.md`.

### Rule 3 — Format `<DDMMYYYY>`

- Dùng convention `DDMMYYYY` theo user quy định (VD `09092026`, `11092026`)
- Lấy today's date từ system context, KHÔNG tự đoán ngày

### Rule 4 — Template `ba-outputs-log.md` per version

```markdown
# BA Outputs Log — v<N> (<DDMMYYYY>)

> Snapshot output BA cho feature `<feature-name>` lần chạy v<N>. Mọi feedback từ user đối với version này ghi vào section "Feedback" cuối file (không sửa các bảng bên trên).

**Trigger:** `INITIAL` (lần chạy đầu / rerun luồng chính) · `FEEDBACK` · `CR` — kèm baseline nếu là FEEDBACK/CR (VD `CR · baseline v2_11092026`)

## 5 Outputs

| # | Output | Status | Path / URL | Note |
|---|---|---|---|---|
| 0 | SPEC.md | ... | `versions/v<N>_<DDMMYYYY>/SPEC.md` | ... |
| 1 | Figma Flow Tổng Quan | ... | `<URL>` | ... |
| 2 | Figma Screen Flow | ... | `<URL>` | ... |
| 3 | Figma Screens + Items | ... | `<URL>` | ... |
| 4 | HTML Prototype | ... | `versions/v<N>_<DDMMYYYY>/prototype/index.html` | ... |
| CR | CR view (chỉ khi Trigger = CR) | ... | `<Figma node URL>` | `NEW: <n> · UPD: <m> · DEL: <k>` |
| CR | `output_cr.md` (chỉ khi Trigger = CR) | ... | `versions/v<N>_<DDMMYYYY>/output_cr.md` | tài liệu trao đổi KH |
| OQ | Open Questions (register + xlsx) | ... | `versions/v<N>_<DDMMYYYY>/open_questions.xlsx` | `n = <n>` · Blocker `<a>` · Figma OQ view: `DRAW` / `SKIP (n > 20)` · hoặc `⬜ N/A` |

## Diff so với version trước (v<N-1>)

- <thay đổi cụ thể: VD "thêm Non-Happy Case 'mất mạng khi submit'", "sửa Actor 'User' → 'Admin'">
- Nếu là v1 → ghi "Version đầu tiên — không có diff"

## Feedback từ user (điền sau khi user review)

- <để trống, user điền sau khi review>
```

### Rule 5 — KHÔNG được

- ❌ Overwrite version cũ (không xóa `versions/v1_...` khi tạo `v2_...`)
- ❌ Skip snapshot vì "nhỏ nhặt" — mọi lần chạy đều snapshot
- ❌ Đặt tên version tự chế (`v-final`, `v-latest`) — chỉ dùng `v<N>_<DDMMYYYY>` với N tăng dần
- ❌ Xử lý feedback / CR (Bước 7) mà sửa đè lên version hiện tại thay vì tạo `v<N+1>`
- ❌ Version có Trigger = CR mà thiếu `output_cr.md` hoặc thiếu `feedback-triage.md`
- ❌ Version còn open question mà thiếu `open_questions.xlsx` / `OQ-REGISTER.md`
- ❌ Đánh lại số OQ ID khi sang version mới

