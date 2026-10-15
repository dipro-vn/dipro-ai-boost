# BA Agent — Output US: Danh sách User Story (xlsx)

> **Scope:** quy trình, định dạng và ràng buộc của **Danh sách User Story** — deliverable **ON-DEMAND**, nằm NGOÀI Definition of Done (giống Output 5).
> **BẮT BUỘC Read** khi chạy Bước 5.9 của `ba-agent.md`. Đọc kèm: `ac-standard.md` (AC) · `story-splitting.md` (tách Story / Spike).
> **Script:** `.claude/skills/business-analyst/scripts/export-user-stories.py`

---

## 1. Là gì — và KHÔNG là gì

| Là | KHÔNG là |
|---|---|
| Danh sách **phẳng** các User Story (`As a / I want to / So that`) sinh **từ SPEC đã có**, để Dev ước lượng / PO ưu tiên / đẩy Backlog (`User_Story`) | Một output Figma. **KHÔNG vẽ lên Sitemap / Output 1 / 2 / 3** |
| Tối đa **2 tầng: `Epic → User Story`** (Epic là tuỳ chọn) | Cây chức năng 3 cấp. **KHÔNG chia Level 1-2-3** |
| Có **tham chiếu** `AC ref`, `FR No.`, `Screen Code`, `Flow` | Nơi chứa nội dung AC (AC chỉ ở SPEC) |
| BA điền `INVEST`, `Spike` | Nơi BA ước lượng. Cột `Estimate (Dev điền)` và `Ưu tiên (PO điền)` **để trống** |

## 2. Input Gate (kiểm trước khi chạy)

| # | Điều kiện | Nếu không thỏa |
|---|---|---|
| 1 | Có trigger từ user: `/user-stories`, hoặc câu như *"tạo danh sách user story cho…"* | Không tự khởi động. Được **đề nghị 1 lần** sau khi SPEC xong; im lặng = không |
| 2 | `SPEC.md` có `## Acceptance Criteria` (viết theo `ac-standard.md`) và `## Screens` có cột `FR No.` | In `Input Gate US: BLOCKED — <thiếu gì>`, hỏi user có muốn bổ sung trước không |
| 3 | Biết **tập FR cần phủ** (FR Register). Nguồn không có danh sách đánh số → ghi `FR coverage: N/A — nguồn không đánh số` | Không tự bịa số FR |
| 4 | Đã chốt có dùng **Epic** hay không (§4) | Hỏi bằng `AskUserQuestion` (1 lần) |

**Khuyến nghị:** chạy sau khi AC đã `APPROVED` — Story trỏ vào AC; AC đổi thì Story `STALE`. Nhưng **không** bắt buộc Output 1/2/3 đã approve (kit này không đụng Figma).

## 3. Cấu trúc danh sách

Nguồn sự thật: `<output-folder>/user-stories/USER-STORIES.md` (BA viết). File `.xlsx` **do script sinh**, KHÔNG gõ tay.

```markdown
| Epic | US ID | Tiêu đề | As a | I want to | So that | FR No. | Screen Code | Flow | AC ref | INVEST | Spike | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EP-01 Gửi & theo dõi đơn nghỉ | US-LEAV-001 | Gửi đơn nghỉ phép | nhân viên đã đăng nhập | gửi đơn nghỉ với loại nghỉ và khoảng ngày | quản lý nhận được đơn để xử lý đúng hạn | #12,13 | AX_LEAV_002 | Flow 2 | AC-01,AC-07 | I✅ N✅ V✅ E✅ S✅ T✅ | — | |
| EP-01 Gửi & theo dõi đơn nghỉ | US-LEAV-002 | Xem trạng thái đơn đã gửi | nhân viên | xem danh sách đơn đã gửi kèm trạng thái | biết đơn đã được duyệt hay chưa | #14 | AX_LEAV_005 | Flow 2 | AC-04 | I✅ N✅ V✅ E✅ S✅ T✅ | — | |
| — | US-LEAV-003 | Giới hạn số ngày nghỉ mỗi năm | quản lý | hệ thống chặn đơn vượt hạn mức | tránh duyệt vượt chính sách | #15 | — | Flow 2 | PENDING-OQ-03 | I✅ N✅ V✅ E⚠️ S✅ T⚠️ | Có | Chờ OQ-03 (hạn mức) |
```

| Cột | Bắt buộc | Quy tắc |
|---|---|---|
| `Epic` | Không | `EP-NN <tên>` hoặc `—`. Cùng `EP-NN` phải cùng tên. **Chỉ 1 tầng Epic** — không Epic lồng Epic |
| `US ID` | ✅ | `US-<FEAT>-<NNN>` — `<FEAT>` là mã Feature 4 chữ hoa (cùng quy ước mã Feature của Screen Code). **Không đánh lại số** giữa các version |
| `Tiêu đề` | ✅ | Danh từ/động từ cụ thể. Không chứa "và" nối 2 mục tiêu (xem `story-splitting.md` §1) |
| `As a` | ✅ | Persona **cụ thể** (lấy từ `ACTOR_LIST`, Câu 0.10). Cấm `user` / `người dùng` / `mọi người`. Story của chức năng hệ thống (`SYSTEM`) → persona là **người nhận kết quả / hưởng lợi** (VD `nhân viên CSKH`), không dùng `hệ thống`; ghi chức năng tự động ở `I want to` |
| `I want to` | ✅ | Hành động cụ thể, quan sát được. Không "quản lý", "xử lý" chung chung |
| `So that` | ✅ | Giá trị nghiệp vụ, **khác** `I want to`. Không viết lại phần trước |
| `FR No.` | ✅ | Tập FR nguồn mà Story phủ: `#12,13` · `#19-21`. Chức năng batch không có màn → vẫn ghi số FR và thêm nhãn: `#24 SYSTEM` (phải có ≥ 1 số FR) |
| `Screen Code` | Có thể `—` | Screen Code chính; nhiều → ngăn bằng dấu phẩy. Story `SYSTEM` ghi `—` |
| `Flow` | Không | `Flow <N>` theo số business flow ở Output 1 (chỉ để trace, **không vẽ ngược** lên Figma). Chưa có Output 1 → để trống hoặc dùng cùng nhãn nhóm nghiệp vụ như `Trace` của AC |
| `AC ref` | ✅ | `AC-NN` và/hoặc `PENDING-OQ-NN`, ngăn bằng dấu phẩy; **được trộn** (VD `AC-01,AC-04,PENDING-OQ-04`). Có `--spec` thì script kiểm AC tồn tại trong SPEC |
| `INVEST` | ✅ | 6 ký hiệu: `I✅ N✅ V✅ E✅ S✅ T✅`. Mỗi ký hiệu: `✅` đạt · `⚠️` có vấn đề · `❌` không đạt (sửa Story trước khi export) |
| `Spike` | ✅ | `Có` khi `E⚠️`; còn lại `—` |
| `Ghi chú` | Không | Dependency · assumption · OQ liên quan · "đã tách → …" |

### INVEST — tiêu chí tự đánh giá

| Ký hiệu | Hỏi | Fail thì |
|---|---|---|
| **I** Independent | Làm / test độc lập được không? | Tách dependency hoặc gộp |
| **N** Negotiable | Còn chỗ cho thảo luận cách làm? (không chỉ định công nghệ/UI từng pixel) | Bỏ chi tiết "how" |
| **V** Valuable | `So that` có giá trị nghiệp vụ, khác `I want to`? | Viết lại `So that` hoặc gộp vào Story khác |
| **E** Estimable | Dev ước lượng được từ thông tin hiện có? | `Spike = Có` + ghi cái chưa biết (`story-splitting.md` §4) |
| **S** Small | Vừa trong 1 sprint? | `story-splitting.md` |
| **T** Testable | Có AC cụ thể trỏ tới? | Viết AC (`ac-standard.md`) hoặc `PENDING-OQ` + `T⚠️` |

> Đây là **tự đánh giá của BA**, không phải kết quả đo. Đừng gọi là "đã verify".

## 4. Epic — chỉ khi có

- **Có Epic khi:** SPEC có ≥ 2 nhóm chức năng nghiệp vụ rõ rệt (vd cột `App` trong `## Screens` đã mang mã nhóm; hoặc FR nguồn đã chia nhóm), và user đồng ý ở Input Gate.
- **Không Epic khi:** feature đơn lẻ (SCOPE `[A]`) hoặc user từ chối. Cột `Epic` ghi `—` cho tất cả; xlsx vẫn là bảng phẳng.
- Epic **KHÔNG** đồng nghĩa Flow. Một Epic có thể chứa Story của nhiều Flow, và ngược lại. Cấm gán `Epic = Flow` chỉ để cho gọn.
- Không phát sinh tầng thứ 3 (sub-story / task). Muốn chi tiết hơn → tách Story (`story-splitting.md`).

## 5. Quy trình (Bước 5.9 của `ba-agent.md`)

```
Input Gate (§2)
  → AskUserQuestion: Epic? phạm vi (toàn bộ FR / một Epic)?
  → Lập USER-STORIES.md từ: FR Register · ## Screens (FR No.) · ## Acceptance Criteria · ## Actors
  → Tự đánh giá INVEST từng Story; áp dụng story-splitting.md
  → python3 .claude/skills/business-analyst/scripts/export-user-stories.py \
        <output-folder>/user-stories/USER-STORIES.md \
        --out <output-folder>/user-stories/user_stories.xlsx \
        --feature "<tên feature>" --version v<N> \
        --expect-fr "<tập FR cần phủ, VD 1-58>" \   # bỏ nếu nguồn không đánh số
        --spec <output-folder>/SPEC.md             # khuyến nghị LUÔN truyền
  → Đọc 2 dòng cuối: US COUNT · US COVERAGE
  → Snapshot (versioning.md Rule 2e) → in report (§7)
```

**Gate của script là gate CẤU TRÚC, không phải gate chất lượng nghiệp vụ:**

| Check | Mức |
|---|---|
| Đủ cột bắt buộc · `US ID` không trùng, đúng format | FAIL |
| `As a` / `I want to` / `So that` / `FR No.` / `AC ref` không rỗng | FAIL |
| `AC ref` đúng dạng `AC-NN` hoặc `PENDING-OQ-NN` | FAIL |
| `INVEST` đủ 6 ký hiệu, không có `❌` | FAIL |
| `Epic` cùng mã phải cùng tên; đúng format `EP-NN` | FAIL |
| **US COVERAGE:** `set(--expect-fr) − set(FR trong Story) = ∅` (in `THIẾU: [...]` kể cả rỗng) | FAIL |
| Persona là `user`/`người dùng`… · `So that` trùng `I want to` · `E⚠️` mà `Spike ≠ Có` · `S⚠️` | WARN |
| Tiêu đề có chữ "và" — **heuristic thô**, có thể báo nhầm ("Xem danh sách **và** trạng thái" = 1 mục tiêu). Chỉ cần đổi tiêu đề hoặc ghi lý do, không phải tách Story | WARN |

`FAIL > 0` → script **không ghi xlsx**; sửa register rồi chạy lại. Không gõ tay xlsx để lách.
`WARN` không chặn nhưng **phải** được nêu trong report, không được im lặng.

**Khi truyền `--spec <SPEC.md>`** script đối chiếu thêm tham chiếu với SPEC thật:

| Check | Mức |
|---|---|
| SPEC có `## Acceptance Criteria` | FAIL |
| Mọi `AC-NN` trong `AC ref` **tồn tại** trong SPEC và không phải AC `(đã bỏ ở v…)` | FAIL |
| AC có trong SPEC mà **không Story nào** trỏ tới (AC mồ côi; AC `PENDING-OQ` được miễn) | WARN |
| `OQ-NN` của `PENDING-OQ-NN` có trong `## Open Questions` | WARN |
| `Screen Code` có trong `## Screens` · `FR No.` có trong cột `FR No.` / chú thích của `## Screens` | WARN |

> ⚠️ Script **không chấm chất lượng AC** (Given/When/Then có đủ không, có từ mơ hồ không) — chỉ kiểm *tham chiếu*. Phần chất lượng BA tự rà bằng checklist `ac-standard.md` §9. **Không truyền `--spec`** thì script cũng không biết `AC-NN` có thật hay không.

## 6. Ràng buộc với các output khác

| Output | Quan hệ |
|---|---|
| **Output 1 / 2 / 3 (Figma)** | **Không đổi gì, không đọc lại, không vẽ lại.** Story không gắn tag lên Sitemap — Sitemap chỉ giữ tag `#N` (FR) như cũ |
| **SPEC.md** | Không tạo heading `##` mới cho User Story. `## BA Deliverables` chỉ thêm row `User Stories` **khi đã chạy** (giống Output 5), không ghi `❌ Skipped` khi chưa chạy |
| **Output OQ** | Story phụ thuộc OQ → `AC ref = PENDING-OQ-NN`, `T⚠️`, ghi `Ghi chú`. Không suy diễn câu trả lời |
| **Output 5 (Basic Design)** | Độc lập. Không prerequisite lẫn nhau |
| **CR / Feedback (Bước 7)** | AC hoặc Screens đổi → danh sách US thành `STALE`; hỏi user rồi **scoped update** + version mới (không regenerate cả file) |
| **Granularity** | Số Story không là đầu vào của Test G/A/B/F/E, không là mốc FR Coverage (`story-splitting.md` §0) |

## 7. Report (in sau khi chạy)

```
User Stories (Output US — on-demand):
  ✅ Register — <output-folder>/user-stories/USER-STORIES.md
  ✅ Excel    — <output-folder>/user-stories/user_stories.xlsx
  Tổng: <n> Story · <e> Epic (hoặc "không dùng Epic")
  Export gate: <N checks · X PASS · 0 FAIL · Y WARN>
  US COVERAGE — phủ <n>/<N> · THIẾU: []
  Cần chú ý: <WARN list: Spike = Có ... | PENDING-OQ ... | S⚠️ ...>
  Estimate / Ưu tiên: để trống — Dev / PO điền
```

## 8. Dữ liệu mẫu & bảo mật

- Persona, ví dụ, ghi chú dùng **dữ liệu mẫu** `DATA-PRIVACY.md` §4. Không tên người thật, không số liệu hợp đồng thật.
- File xlsx có thể được gửi KH/Dev → chạy `node .claude/hooks/detect-pii.js --scan <output-folder>` trước bàn giao (theo `DATA-PRIVACY.md` §5).

## 9. Anti-pattern

- ❌ Chạy Output US khi chưa có `## Acceptance Criteria` theo `ac-standard.md` (Story không có AC để trỏ)
- ❌ Chia Story theo "Level 1 / 2 / 3" hoặc tạo cây nhiều tầng
- ❌ Vẽ / gắn tag Story lên Sitemap hay bất kỳ Figma frame nào
- ❌ Chép nội dung AC vào xlsx (chỉ `AC ref`)
- ❌ Điền `Estimate` / `Ưu tiên` thay Dev / PO
- ❌ Dùng `Epic = Flow` máy móc
- ❌ Gõ tay xlsx / sửa xlsx trực tiếp thay vì sửa `USER-STORIES.md` rồi chạy lại script
- ❌ Dùng "số Story" để kết luận "đã đủ chức năng"
- ❌ Tự chạy khi chưa có trigger từ user
