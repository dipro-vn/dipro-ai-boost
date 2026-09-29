# BA Agent — Bước 7: Feedback / Meeting Note Intake (on-demand)

> Không thuộc luồng chính 0→5. Kích hoạt khi user nói: "vừa có cuộc họp", "KH feedback", "có meeting note cần xử lý", hoặc paste feedback trực tiếp vào chat sau khi đã có version trước.
>
> **Nguyên tắc số 1 của bước này:** trước khi sửa bất cứ thứ gì, BA phải **phân định** mỗi item là `CR` (ChangeRequest) hay `FEEDBACK` (góp ý về luồng hiện tại). Sửa trước — phân loại sau = vi phạm, vì 2 nhánh có output và cách vẽ Figma khác nhau.
>
> **Nhánh CR:** BẮT BUỘC `Read('.claude/ba-agent/change-request.md')` trước khi làm bất kỳ việc gì của nhánh đó.

---

## Bước 7.1 — Tạo document ghi nhận (trước khi phân tích)

```
<output-folder>/meetings/customer_feedback_<DDMMYY>.md   ← feedback trực tiếp từ KH
<output-folder>/meetings/meeting_note_<DDMMYY>.md         ← note đầy đủ từ Gemini / ghi tay
```

Template `meeting_note_DDMMYY.md`:
```markdown
# Meeting Note — <DD/MM/YY>

## Participants
- <role> (KHÔNG ghi họ tên đầy đủ — `rules/DATA-PRIVACY.md`)

## Các điểm đã quyết định
- <quyết định 1>

## Các điểm chưa quyết định
- <vấn đề còn open + owner + deadline trả lời>

## Các điểm khách hàng đang feedback
- <feedback + screen / feature liên quan>
```

⚠️ Meeting note / transcript = source loại **R5 / R6** (`preflight-questions.md`) — KHÔNG được biến discussion thành `FACT`. Trước khi lưu, áp `rules/DATA-PRIVACY.md` (bỏ tên thật, số điện thoại, dữ liệu production).

---

## Bước 7.2 — Triage: CR hay FEEDBACK? (BẮT BUỘC — gate cứng)

### Xác định baseline trước khi phân loại

Không có baseline thì không phân loại được. Baseline = **version gần nhất đã chốt** với user:

1. Đọc `versions/` → lấy `v<M>` mới nhất (hoặc version user chỉ định)
2. Đọc `versions/v<M>_<DDMMYYYY>/SPEC.md` — 3 vùng quyết định: `## Mô tả nghiệp vụ`, `## Out of Scope`, `## Acceptance Criteria`
3. Đọc `versions/v<M>_<DDMMYYYY>/ba-outputs-log.md` — biết output nào đã `APPROVED`

Chưa có version nào / chưa có SPEC → **không phải Bước 7**. Đây là lần chạy đầu → về Bước 1 chạy luồng chính.

### Phân loại TỪNG ITEM, không gán nhãn cho cả note

1 meeting note thường chứa **cả CR lẫn feedback**. BA phải tách thành từng item rồi gán nhãn riêng. Gán 1 nhãn cho cả note = sai.

### Bảng tiêu chí (chỉ cần thỏa 1 dòng → CR)

| # | Dấu hiệu CR | Vì sao là CR |
|---|---|---|
| C1 | Yêu cầu không có trong SPEC baseline, **và** không phải chi tiết hóa của mục đã có | Scope mới |
| C2 | Yêu cầu nằm trong `## Out of Scope` của baseline | Đã chốt là KHÔNG làm |
| C3 | Thêm / bỏ screen, actor, function, integration so với baseline | Đổi cấu trúc deliverable |
| C4 | Đổi business rule hoặc AC **đã approve** (KH đổi ý, không phải BA vẽ sai) | Đảo quyết định đã chốt |
| C5 | Đổi platform / viewport / non-functional đã chốt ở Discovery Brief | Đổi nền tảng thiết kế |
| C6 | Kéo theo thay đổi effort / schedule / cost, hoặc phải sửa Basic Design đã giao | Ảnh hưởng cam kết |

| # | Dấu hiệu FEEDBACK (góp ý luồng hiện tại) | Vì sao KHÔNG phải CR |
|---|---|---|
| F1 | BA vẽ sai / thiếu so với requirement gốc — lỗi của artifact, không phải KH đổi ý | Sửa cho đúng baseline |
| F2 | Trả lời Open Question (OQ-xx trong `open-questions/OQ-REGISTER.md` / `## Open Questions` của SPEC) mà baseline đã ghi `UNKNOWN` | Baseline đã chừa chỗ sẵn |
| F3 | Chỉnh wording, label, thứ tự item, layout, typo | Không đổi nghiệp vụ |
| F4 | Bổ sung chi tiết của item đã có trong scope (VD validation của field đã có) | Chi tiết hóa |
| F5 | Bổ sung Non-Happy Case của flow đã có | Hoàn thiện flow cũ |

### In bảng triage cho user (BẮT BUỘC trước khi hỏi)

```markdown
## Triage — Feedback ngày <DD/MM/YY> · Baseline: v<M>_<DDMMYYYY>

| # | Item (nguyên văn ý KH) | Phân loại | Tiêu chí | Bằng chứng từ baseline |
|---|---|---|---|---|
| 1 | <...> | 🔴 CR | C2 | `SPEC.md ## Out of Scope` (v<M>) ghi "<trích dẫn>" |
| 2 | <...> | 🟡 FEEDBACK | F1 | `SPEC.md ## Screen Details` AX_003 ghi "<trích>" — Figma O3 vẽ thiếu |
| 3 | <...> | ⚪ CHƯA RÕ | — | Baseline không đề cập, cũng không nằm Out of Scope |
```

- Mỗi row **phải có bằng chứng trích từ baseline** (section + nội dung). Không có bằng chứng → xếp `⚪ CHƯA RÕ`, không tự đoán.
- `⚪ CHƯA RÕ` = BẮT BUỘC hỏi user ở Bước 7.3, KHÔNG tự chọn nhánh.

---

## Bước 7.3 — AskUserQuestion chốt phân loại (BẮT BUỘC — gọi tool, không in text rồi tự đi tiếp)

Gọi `AskUserQuestion` sau khi in bảng triage:

| Câu | Nội dung | Lựa chọn |
|---|---|---|
| 1 | Bảng triage trên đúng chưa? | `[Đúng — làm theo bảng]` · `[Sai — tôi chỉ lại item nào là CR]` · `[Coi tất cả là feedback trong scope]` |
| 2 | *(chỉ khi có row `⚪ CHƯA RÕ`)* Item #<n> xếp nhánh nào? | `[CR — ngoài scope đã chốt]` · `[Feedback — trong scope]` · `[Chưa xử lý lần này]` |
| 3 | Baseline so sánh là version nào? | `[v<M> — mới nhất]` · `[version khác — tôi chỉ định]` |

Im lặng / "ok" / "tuỳ bạn" ≠ confirm phân loại CR. Chưa có câu trả lời → DỪNG, không sửa artifact.

Sau khi chốt:
- Có item `🔴 CR` → chạy **nhánh CR**: `Read('.claude/ba-agent/change-request.md')` rồi làm theo file đó.
- Có item `🟡 FEEDBACK` → chạy **nhánh Feedback** (Bước 7.4 dưới).
- Có cả hai → chạy Feedback trước (sửa cho đúng baseline), CR sau (vẽ view riêng). **Không trộn 2 nhánh vào cùng 1 lần vẽ.**

---

## Bước 7.4 — Nhánh FEEDBACK: Impact Analysis → hỏi → update → version mới

### 7.4.1 Impact Analysis

Với mỗi item feedback, xác định:
- Ảnh hưởng section nào trong SPEC (`Happy Path` / `AC` / `Screens` / `Screen Details` / `Ambiguities`)
- Có cần thêm / sửa / xóa screen không
- Downstream artifact nào thành `STALE` (Figma O1/O2/O3 · prototype · Basic Design sheet) — theo `POLICIES.md §4.6`
- Cần thông báo Tech Lead không

In bảng impact:

| # | Feedback | Screen / Flow ảnh hưởng | SPEC section | Downstream STALE | Action |
|---|---|---|---|---|---|
| 1 | <...> | AX_FEAT_003 | `## Screen Details` | Figma O3, prototype | Update |
| 2 | <...> | — | `## Ambiguities` OQ-02 | — | Chốt OQ |

### 7.4.2 AskUserQuestion TRƯỚC khi update (BẮT BUỘC)

Không được sửa ngay sau khi in bảng impact. Gọi `AskUserQuestion`:

| Câu | Nội dung | Lựa chọn |
|---|---|---|
| 1 | Bảng impact đúng chưa? Update theo scope nào? | `[Scoped — chỉ các section trong bảng]` · `[Mở rộng — kèm downstream STALE]` · `[Chỉ ghi nhận, chưa sửa]` |
| 2 | Artifact nào vẽ/ build lại lần này? | `[Chỉ SPEC.md]` · `[SPEC + Figma O<x> bị STALE]` · `[SPEC + Figma + HTML prototype]` |
| 3 | *(chỉ khi feedback đối lập quyết định đã chốt ở v<M>)* Giữ cái nào? | `[Theo feedback mới]` · `[Giữ quyết định v<M>]` · `[Đây là CR — chuyển nhánh CR]` |

Câu 3 trả lời `[Đây là CR]` → quay lại Bước 7.3, xếp lại nhãn, sang nhánh CR.

### 7.4.2b Riêng feedback là câu trả lời Open Question (OQ-xx)

- Cập nhật `open-questions/OQ-REGISTER.md`: điền câu trả lời, `Trạng thái` = `Đã trả lời`, **không đánh lại OQ ID**.
- Đổi classification trong SPEC `## Source Register`: `UNKNOWN`/`CONFLICT` → `FACT` (evidence = ai trả lời + ngày).
- Xoá câu đã chốt khỏi bảng OQ ở version sau; ghi 1 dòng trong `Diff so với version trước` (VD `OQ-03 đã chốt: huỷ đơn sau 15 phút`).
- Còn câu chưa trả lời → **chạy lại** `export-open-questions.py` để sinh xlsx mới (bản còn lại), giữ nguyên ID.
- Chi tiết: `.claude/ba-agent/open-questions.md` §6.

### 7.4.3 Update — scoped, theo `POLICIES.md §4.6`

- Chỉ sửa section đã được confirm. KHÔNG regenerate toàn bộ SPEC / toàn bộ Figma frame.
- Cập nhật đồng bộ tất cả màn liên quan trong **cùng 1 lần edit** (không sửa rải rác nhiều lượt).
- Sau update: state artifact đó = `WAITING_APPROVAL` (không tự set `APPROVED`).
- Artifact ngoài scope đã `APPROVED` = immutable — muốn chạm phải xin approve mở rộng.

### 7.4.4 Lưu version MỚI (BẮT BUỘC — không sửa đè version cũ)

Theo `.claude/ba-agent/versioning.md` Rule 2c:

```
versions/v<N+1>_<DDMMYYYY>/
├── SPEC.md                  ← bản sau update
├── feedback-triage.md       ← bảng triage 7.2 + câu trả lời 7.3/7.4.2
├── OQ-REGISTER.md + open_questions.xlsx  ← khi feedback là câu trả lời OQ, hoặc còn OQ chưa chốt
├── ba-outputs-log.md        ← Trigger = FEEDBACK · diff so với v<N>
└── prototype/index.html     ← nếu prototype có thay đổi
```

Ghi feedback gốc vào `versions/v<N>_<DDMMYYYY>/ba-outputs-log.md` section "Feedback" (version **cũ** — nơi feedback phát sinh), kết quả xử lý ghi ở version **mới**.

---

## Anti-pattern NGHIÊM CẤM (Bước 7)

- ❌ Nhận feedback → sửa SPEC luôn, không phân loại CR/FEEDBACK
- ❌ Gán 1 nhãn cho cả meeting note thay vì phân loại từng item
- ❌ In bảng triage / bảng impact rồi tự đi tiếp, không gọi `AskUserQuestion`
- ❌ Phân loại CR mà không trích được bằng chứng từ baseline
- ❌ Sửa đè lên version cũ, hoặc update xong không tạo version mới
- ❌ Coi mọi thứ KH nói sau khi chốt scope là "feedback nhỏ" để né CR
- ❌ Ngược lại: gọi mọi feedback là CR để né việc sửa lỗi BA tự gây ra (F1)
- ❌ Tự suy `APPROVED` cho baseline chỉ vì `ba-outputs-log.md` ghi `✅ Done`
