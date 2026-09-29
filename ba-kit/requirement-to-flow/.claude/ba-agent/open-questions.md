# BA Agent — Output OQ: Open Questions (Register + xlsx + Figma view)

> **Chạy ở đâu:** trong **giai đoạn Output 1 (Flow Tổng Quan)** — sau khi Output 1 PASS Quality Gate và BA **đã hỏi user bằng `AskUserQuestion`** (Gate A / Gate B1). Những gì user đã trả lời ở đó = đã chốt, KHÔNG đưa vào OQ nữa. Phần **còn lại chưa có câu trả lời** mới là Output OQ.
>
> **Vì sao chạy ở Output 1, không để tới cuối:** Output 2 (Screen Flow) và Output 3 (Screens) vẽ dựa trên business rule. Chốt rule muộn = vẽ lại toàn bộ. OQ là artifact để KH trả lời **song song** trong khi BA vẽ tiếp phần không bị chặn.

| Điều kiện | Kết quả |
|---|---|
| Sau `AskUserQuestion` không còn câu nào chưa trả lời | Output OQ = `⬜ N/A` — in `Output OQ: N/A — không còn open question` vào report, KHÔNG tạo file rỗng |
| Còn `n` câu, `1 ≤ n ≤ 20` | **xlsx + Figma OQ view** (đủ 2 artifact) |
| Còn `n` câu, `n > 20` | **CHỈ xlsx** — KHÔNG vẽ Figma view, report phải in đường dẫn folder đã lưu (xem §4) |

---

## §1 — Chỉ hỏi câu nghiệp vụ BA (rule lọc — làm TRƯỚC khi viết register)

**Được đưa vào OQ** — câu hỏi mà chỉ khách hàng / BrSE trả lời được, và câu trả lời làm đổi flow / screen / AC:

| Nhóm nghiệp vụ | Ví dụ câu hỏi đúng |
|---|---|
| Quyền & phê duyệt | "Ai được quyền duyệt đơn giá trị trên 10 triệu?" |
| Business rule / điều kiện | "Đơn quá hạn thanh toán bao lâu thì tự huỷ?" |
| Trạng thái & vòng đời | "Đơn đã huỷ có được đặt lại cùng suất đó không?" |
| Dữ liệu nghiệp vụ | "Số điện thoại là bắt buộc hay tuỳ chọn khi đặt hộ người khác?" |
| Nội dung hiển thị cho user | "Message khi đơn bị huỷ tự động ghi thế nào?" |
| Ngoại lệ nghiệp vụ | "Hết suất ngay lúc user bấm xác nhận thì xử lý ra sao?" |
| Quy trình / SLA nghiệp vụ | "Sau khi duyệt, KH được thông báo trong bao lâu?" |
| Phạm vi | "Nghiệp vụ hoàn tiền có nằm trong sprint này không?" |

**KHÔNG được đưa vào OQ** — câu hỏi kỹ thuật (việc của Tech Lead) và câu hỏi vô nghĩa:

| Loại | Ví dụ | Xử lý |
|---|---|---|
| Kỹ thuật / triển khai | API/endpoint, DB schema, tên bảng-field, framework, cache, queue, deploy, performance tuning | Gom vào list riêng `## Chuyển Tech Lead` ở cuối register — **không** vào bảng OQ, không export xlsx |
| Chung chung | "Còn gì cần bổ sung không?", "Anh/chị thấy thế nào?" | Bỏ. Không trả lời được = không phải open question |
| Đã có câu trả lời trong nguồn | Thông tin đã nằm trong requirement / meeting note đã confirm | Bỏ — phải trace `Source Register`, không hỏi lại điều đã có |
| Đã hỏi ở `AskUserQuestion` | User vừa trả lời ở Gate A | Bỏ — ghi vào SPEC dạng `FACT`, không hỏi lại |
| Câu hỏi ghép | "Ai duyệt đơn? Duyệt trong bao lâu?" | **Tách thành 2 OQ** |

**Nguồn sinh OQ (không tự nghĩ ra câu hỏi):** mỗi OQ phải trace về 1 trong 4 nguồn —
`Source Register` row có classification `UNKNOWN` hoặc `CONFLICT` · Flow Candidate Matrix có ô không xác định được Outcome/Actor · `Test G: SKIPPED — thiếu ACTOR_LIST` (thiếu input) · Non-Happy Case mà nguồn không mô tả hành vi.

---

## §2 — OQ Register (source of truth, dạng markdown)

Path: `<output-folder>/open-questions/OQ-REGISTER.md`

```markdown
# Open Question Register — <feature> (v<N>)

> Nguồn: `SPEC.md ## Source Register` (row UNKNOWN/CONFLICT) + Flow Candidate Matrix Output 1.
> Mỗi câu đã được user trả lời → chuyển classification sang FACT trong SPEC và xoá khỏi bảng này ở version sau.

| OQ ID | Nhóm nghiệp vụ | Câu hỏi | Vì sao cần trả lời (impact) | Liên quan (FR/Flow/Screen) | Mức chặn | Phương án BA đề xuất | Lựa chọn gợi ý |
|---|---|---|---|---|---|---|---|
| OQ-01 | Quyền & phê duyệt | Ai được quyền duyệt đơn giá trị trên 10 triệu? | Không rõ thì không vẽ được nhánh duyệt ở Flow 2 | FR-12 · Flow 2 · AX_ORD_004 | Blocker | Chỉ Trưởng phòng duyệt, Admin chỉ xem | A) Trưởng phòng · B) Admin · C) Cả hai |

## Chuyển Tech Lead (không thuộc Output OQ)

- <câu hỏi kỹ thuật phát sinh> — chuyển `Design-Technical.md`
```

**Rule từng cột:**

| Cột | Rule |
|---|---|
| `OQ ID` | Format `OQ-NN` (2-3 số), không trùng, không đánh lại số khi sang version mới (OQ-03 vẫn là OQ-03) |
| `Nhóm nghiệp vụ` | Theo bảng §1 — để KH trả lời gọn theo nhóm, không nhảy chủ đề |
| `Câu hỏi` | 1 câu = 1 vấn đề, kết thúc bằng `?`, cụ thể, trả lời được trong 1-2 dòng |
| `Vì sao cần trả lời` | Impact thật: cái gì bị chặn / sai nếu không có câu trả lời. Không ghi "để rõ hơn" |
| `Liên quan` | BẮT BUỘC trace: `FR No.` · flow · screen code. Không trace được → câu hỏi này chưa đủ chín, bỏ |
| `Mức chặn` | `Blocker` (chặn vẽ Output 2/3) · `High` (chặn chốt AC) · `Medium` (chặn chi tiết screen) · `Low` (nice to know) |
| `Phương án BA đề xuất` | BẮT BUỘC có — BA đưa default hợp lý để KH chỉ cần confirm thay vì viết bài. Đây là `PROPOSAL`, không phải `FACT` |
| `Lựa chọn gợi ý` | Nên có với `Blocker` — dạng `A) … · B) … · C) …` |

---

## §3 — Export xlsx (BẮT BUỘC dùng script, không gõ tay workbook)

```bash
python3 .claude/skills/business-analyst/scripts/export-open-questions.py \
    "<output-folder>/open-questions/OQ-REGISTER.md" \
    --out "<output-folder>/open-questions/open_questions.xlsx" \
    --feature "<feature>" --version "v<N>" --date "<DDMMYYYY>" \
    --report "<output-folder>/versions/v<N>_<DDMMYYYY>/oq-export.md"
```

Script làm 2 việc: **validate** register (11 check) + **build** workbook 3 sheet.

| Sheet | Nội dung |
|---|---|
| `Guideline` | Hướng dẫn KH cách trả lời (§5) — sheet đầu tiên, KH mở là thấy trước |
| `Open Questions` | Bảng 12 cột (8 cột BA + 4 cột để KH điền, tô vàng), sort `Blocker → Low`, freeze pane, autofilter, dropdown `Trạng thái` |
| `Summary` | Tổng số · đếm theo Mức chặn · đếm theo Nhóm · trạng thái Figma OQ view |

| Kết quả script | Hành động |
|---|---|
| `FAIL = 0` → exit 0 | Đọc 2 dòng cuối: `OQ COUNT: n` và `FIGMA_VIEW: DRAW / SKIP` → quyết định có vẽ Figma view hay không |
| `FAIL > 0` → exit 1 | **Script KHÔNG ghi xlsx.** Sửa `OQ-REGISTER.md` rồi chạy lại. Không gõ tay xlsx để lách gate |
| exit 2 | Thiếu `openpyxl` → `pip install openpyxl`. Không cài được → Output OQ = `❌ Blocked`, giao register `.md` kèm ghi chú, KHÔNG tự chấm PASS |

⚠️ **Con số `n` để quyết định vẽ Figma view phải lấy từ `OQ COUNT` của script**, không đếm bằng mắt.

---

## §4 — Figma OQ view (chỉ khi `n ≤ 20`)

### 4.1 Hard rule vị trí

- Section mới: `Open Questions — <feature> (v<N>)`, đặt **dưới Output 1**, gap ≥ 300px theo trục Y.
- ⛔ KHÔNG vẽ chồng / không sửa / không di chuyển node của Output 1/2/3 (cùng nguyên tắc `POLICIES.md §4.6` và CR view).
- Grid card: 3 cột × width 420px, gap 40px. Card height auto theo nội dung, min 200px.

### 4.2 Card mỗi OQ

| Vùng | Nội dung |
|---|---|
| Header | `OQ-NN` (bold) + badge `Mức chặn` + `Nhóm nghiệp vụ` |
| Body | Câu hỏi (≤ 2 dòng) · `Liên quan:` FR/Flow/Screen · `BA đề xuất:` default · `Lựa chọn:` A/B/C |
| Footer | Ô trống viền dashed cao 48px, label `Trả lời:` — để KH comment trực tiếp lên Figma |

| Mức chặn | Fill | Stroke badge |
|---|---|---|
| `Blocker` | `#FFF6F5` | `#CF222E` |
| `High` | `#FFF9EB` | `#F4860C` |
| `Medium` | `#E8F4FD` | `#0969DA` |
| `Low` | `#F6F8FA` | `#D0D7DE` |

Bắt buộc có trong view: **Legend 4 mức** · **Counter** `Tổng: n · Blocker: a · High: b · Medium: c · Low: d` · **Note** `Cách trả lời: comment trực tiếp lên card, hoặc điền file <đường dẫn xlsx>`.

### 4.3 Khi `n > 20` — chỉ xlsx

- KHÔNG vẽ Figma view (20+ card = frame dài không ai đọc hết, và KH trả lời trên Excel nhanh hơn).
- Report + `## BA Deliverables` BẮT BUỘC ghi: `Figma OQ view: ❌ Skipped — n = <n> > 20 (chỉ export xlsx)`.
- BẮT BUỘC in **đường dẫn folder đã lưu** + tên file + breakdown mức chặn (xem §6).
- User muốn vẽ view dù `n > 20` → chỉ vẽ khi user **yêu cầu explicit**; BA không tự vẽ, cũng không tự cắt bớt câu để lách xuống 20.

### 4.4 Quality Gate OQ view (FAIL = 0)

| # | Check | PASS |
|---|---|---|
| 1 | Số card = `OQ COUNT` từ script | Khớp |
| 2 | Card thiếu badge Mức chặn | `= 0` |
| 3 | Card thiếu ô `Trả lời:` | `= 0` |
| 4 | Overlap bbox với Section Output 1/2/3 | `= 0` (gap ≥ 300px) |
| 5 | Node Output 1/2/3 bị thay đổi | `= 0` (so `get_metadata` trước/sau) |
| 6 | Overlap nội bộ (`recheck.md` Tiêu chí 7) | `overlapCount == 0` |
| 7 | Legend + Counter + Note đường dẫn xlsx | Có đủ 3 |

---

## §5 — Guideline trả lời (đã nhúng trong sheet `Guideline`, in lại khi giao cho user)

BA PHẢI in block này trong report khi giao Output OQ (user không mở Excel vẫn biết cách trả lời):

```
📋 CÁCH TRẢ LỜI OPEN QUESTION

1. Chỉ cần điền 4 cột: "Câu trả lời của bạn" · "Người trả lời (role)" · "Ngày trả lời" · "Trạng thái".
   Các cột khác BA dùng để trace về SPEC — xin đừng sửa/xoá/đổi thứ tự cột.

2. Mỗi câu trả lời theo 1 trong 4 dạng:
   ✅ OK theo đề xuất — đồng ý cột "Phương án BA đề xuất", ghi "OK theo đề xuất"
   ✏️ Sửa lại        — ghi RULE ĐÚNG, có số/điều kiện. VD: "Hết 15 phút không thanh toán thì huỷ đơn"
   ❓ Chưa biết       — ghi rõ AI trả lời + KHI NÀO. VD: "Chờ kế toán xác nhận, trả lời trước 05/10"
   🚫 Không áp dụng   — ghi lý do ngắn. VD: "Nghiệp vụ này đã bỏ từ tháng 8"

3. Ưu tiên trả lời Blocker trước — các câu này đang chặn việc vẽ Output 2/3. High chặn việc chốt AC.

4. Nên: 1 ô trả lời cho 1 câu · nói bằng rule có điều kiện/con số/trạng thái/ai được làm gì.
   Không nên: "tuỳ", "linh động", "như hiện tại" mà không chỉ rõ hệ thống/màn nào · gộp nhiều câu vào 1 ô.

5. Có file/ảnh tham khảo → ghi TÊN FILE vào ô trả lời + để file vào cùng folder. Đừng dán ảnh vào cell.

6. Không điền dữ liệu thật của KH (tên/SĐT/email/dữ liệu production) — dùng dữ liệu mẫu.

7. Gửi lại: giữ nguyên tên file + cột; hoặc trả lời ngay trong chat theo format "OQ-03: <câu trả lời>" (mỗi câu 1 dòng).

8. Sau khi bạn trả lời: BA cập nhật SPEC (UNKNOWN → FACT), vẽ lại phần bị ảnh hưởng, lưu thành version MỚI.
   Câu chưa trả lời vẫn được giữ lại — BA KHÔNG tự suy diễn thay bạn.
```

Khi user trả lời (trong chat hoặc gửi file đã điền) → đi vào **Bước 7 nhánh FEEDBACK** (`post-meeting-workflow.md` — tiêu chí F2), không phải CR: OQ là chỗ baseline đã chừa sẵn.

---

## §6 — Output OQ là 1 output của feature (lưu + report + version)

**Path canonical (LATEST):**

```
<output-folder>/open-questions/
├── OQ-REGISTER.md        ← source of truth (markdown)
└── open_questions.xlsx   ← bản giao cho KH (script sinh ra)
```

**Snapshot version** (`versioning.md` Rule 2d): copy cả 2 file + `oq-export.md` (report script) vào `versions/v<N>_<DDMMYYYY>/`.

**SPEC.md** — 2 chỗ BẮT BUỘC cập nhật:
- `## BA Deliverables` → thêm row `OQ` (format ở `figma-outputs/shared-rules.md`)
- `## Open Questions` → bảng rút gọn `OQ ID · Câu hỏi · Mức chặn · Trạng thái` + link tới xlsx và Figma OQ view. Câu chưa trả lời **giữ nguyên ở đây**, TUYỆT ĐỐI không nối vào `## Happy Path` / `## Acceptance Criteria` bằng giả định.

**Block report bắt buộc (kể cả khi `n > 20`):**

```
Output OQ — Open Questions:
  ✅ Register   — <output-folder>/open-questions/OQ-REGISTER.md
  ✅ Excel      — <output-folder>/open-questions/open_questions.xlsx
     Folder     — <output-folder>/open-questions/        ← gửi KH folder này
  ✅/❌ Figma OQ view — <node URL>  |  ❌ Skipped — n = <n> > 20 (chỉ export xlsx)
  Tổng: <n> câu · Blocker <a> · High <b> · Medium <c> · Low <d>
  Export gate: <11 checks · X PASS · 0 FAIL · Y WARN>
  → Hướng dẫn trả lời: xem sheet "Guideline" trong file, hoặc block 📋 ở trên
```

---

## Anti-pattern NGHIÊM CẤM

- ❌ Đưa câu hỏi kỹ thuật (API/DB/framework/infra) vào OQ — đó là việc Tech Lead
- ❌ Hỏi lại điều user vừa trả lời ở `AskUserQuestion`, hoặc điều đã có trong nguồn
- ❌ Câu hỏi chung chung ("còn gì cần bổ sung không?") hoặc câu hỏi ghép 2 vấn đề
- ❌ OQ không có `Phương án BA đề xuất` → bắt KH viết bài thay vì confirm
- ❌ OQ không trace được về FR/Flow/Screen
- ❌ Gõ tay workbook xlsx thay vì chạy `export-open-questions.py`; hoặc script FAIL mà vẫn tự tạo file
- ❌ Đếm `n` bằng mắt rồi quyết định vẽ Figma view (phải lấy `OQ COUNT` từ script)
- ❌ `n > 20` mà vẫn vẽ Figma view, hoặc cắt bớt câu hỏi để lách xuống ≤ 20
- ❌ Vẽ OQ view chồng lên Output 1/2/3
- ❌ Giao xlsx mà không kèm guideline trả lời + đường dẫn folder
- ❌ Tự suy diễn câu trả lời cho OQ chưa được trả lời để "cho đủ" Happy Path / AC
- ❌ Đánh lại số OQ ID ở version sau (OQ-03 phải vẫn là OQ-03 để trace lịch sử)
