---
description: Deep review test cases theo bộ tiêu chí v3 — chạy kiểm máy bằng script rồi review đầy đủ bằng hai agent (Sonnet đọc từng TC, Opus suy luận kịch bản), sinh `[module]-review-vN.md` (report chính, ngắn, gom theo TC) và `[module]-review-detail-vN.md` (phụ lục bằng chứng). Không tự sửa TCs.
skills:
  - rbt_manual_testing
---

## Mục đích

Con mắt thứ hai cho bộ TC đã sinh. Câu hỏi gốc: **"bug nào lọt qua được bộ TC này?"**

- Tiêu chí, tier, verdict, quy tắc finding: **`.claude/skills/rbt_manual_testing/review_criteria.md`** (nguồn chuẩn duy nhất, gọi tắt là *tiêu chí*). File này chỉ mô tả cách chạy.
- **KHÔNG tự sửa TCs.** Chỉ output report.
- Review **độc lập**: không đọc report review cũ của module (`*-review-*.md`) trước khi review xong.

---

## Bước 1 — Thu thập artifacts

Tên file theo "Quy ước file và version" (skill `rbt_manual_testing`); mặc định lấy **version lớn nhất** bằng `python3 -I .claude/scripts/module_files.py latest testing/[module] testcases` (và `... analysis`). User nêu version khác (VD "review v2") thì dùng version đó, analysis cùng N (hoặc lớn nhất không vượt N). Nếu `module_files.py latest testing/[module] testcases xlsx` có version **lớn hơn** md thì in cảnh báo một dòng `xlsx đang chạy là vX nhưng md mới nhất chỉ là vY, md có thể đã cũ` và vẫn review md.

| File | Bắt buộc? | Dùng để |
|---|---|---|
| `[module]-testcases-vN.md` | ✅ | Input chính |
| `[module]-analysis-vN.md` | Bản Full | AC, Q&A, ASM, DIF, Permission Matrix, Impact Analysis, Platform |
| Spec gốc | Bắt buộc với bản Full, luôn có với bản Quick | Đối chiếu Expected (REV-02.1), kịch bản ngoài AC (REV-01.2), AC lệch spec (5.2) |

**Tìm spec:** bản Quick lấy theo dòng `**Nguồn:**` đầu file TC. Bản Full lấy `module_files.py latest testing/[module] spec`, không có thì `testing/[module]/spec.md`. Không tìm được thì hỏi user path; user không có thì vẫn review, verdict tối đa là **PASS có điều kiện** (tiêu chí mục 2).

**Không có file TC, hoặc không có cả analysis lẫn spec** → verdict BLOCKED, dừng.

### Xác định chế độ

- File TC có dòng `> Mode: Quick ...` → **bản Quick**: REQ-xx thay AC-xx, không có Q&A. Platform lấy dòng `**Platform:**` đầu file TC, sau đó `CLAUDE.md`. Luồng E2E và ô phân quyền lấy từ spec và Bảng 1/2 của chính file TC.
- Không có → **bản Full**.

Bản Quick **không đánh Critical/Major cho việc thiếu Q&A**: đó là đặc điểm của chế độ, không phải lỗi bộ TC. Expected `[ASSUMED]` là suy luận chưa PM/BA xác nhận.

---

## Bước 2 — Kiểm máy

```
python3 -I .claude/scripts/review_checks.py testing/[module]/[module]-testcases-vN.md \
  --spec <spec> [--analysis <analysis>] --json "${TMPDIR:-/tmp}/review-checks-[module]-vN.json"
```

Đọc phần đầu kết quả (chế độ, nguồn AC, Bảng 1/2) và bảng tổng số dòng theo K1–K15. Ý nghĩa từng kiểm và cách dùng kết quả: tiêu chí mục 5.8. **AI không dò lại các mục loại "chắc chắn".** Script lỗi hoặc không chạy được thì ghi vào phụ lục và tự kiểm các phần đó ở Bước 4.

---

## Bước 3 — Gán mức rủi ro

Bản Quick bắt buộc (tiêu chí mục 2 và 5.4): bảng `REQ/AC | High/Medium/Low | lý do 1 cụm`. Bản Full: High = AC có Q&A High hoặc thuộc component Risk High trong `analysis.md`, ô ❌ Permission Matrix, TC Security; còn lại theo `analysis.md`.

---

## Bước 4 — Review (hai agent chạy cùng lúc)

`/review-tcs` **luôn review đầy đủ 17 mục**, không có chế độ rút gọn. Muốn kiểm nhanh các lỗi cơ bản thì chạy riêng script ở Bước 2 (không phải review, không có verdict).

Việc chia theo **loại việc**, không theo nhóm TC (chạy thử chia 4 nhóm TC tốn token gấp 3 mà không nhanh hơn, vì agent nào cũng phải đọc cả file TC). Gọi **cùng lúc** (một lượt, hai lời gọi Agent). Mỗi agent tự đọc file, không chép nội dung file vào prompt.

| Agent | Model | Mục REV | Việc |
|---|---|---|---|
| **A — Từng TC** | `sonnet` | 01.1, 01.6, 02.1, 02.2 (bản Full), 03.1, 03.2, 04.1, 05.1, 05.2, 06, 08, mục 5.2 | Đọc từng TC so với spec/AC; tách vế (5.3); xác nhận ứng viên K7, K9–K15; gộp các dòng "chắc chắn" K1–K6, K12 thành finding |
| **B — Suy luận** | `opus` | 01.2, 01.3, 01.4, 01.5, 04.2, 07 | Tìm kịch bản và lỗ hổng không có trong AC: cắt ngang nhiều feature, kẻ gian lận (quyền, dữ liệu), trạng thái bị cấm, biên, negative còn thiếu; xác nhận ứng viên K8 |

Hai agent độc lập nên B không đọc kết quả của A. Hai bên có thể báo cùng một lỗi; Bước 5 gộp theo nguyên nhân gốc.

Môi trường không có Agent tool: chạy tuần tự A rồi B, cùng format đầu ra.

**Prompt cho mỗi agent** phải có:
- Đường dẫn: tiêu chí, file TC, spec, analysis (nếu có), JSON kết quả script.
- Chế độ Full/Quick, danh sách mục REV của agent, bảng gán rủi ro ở Bước 3.
- Nhắc: chỉ kiểm các mục REV của mình; không sửa file; không đọc review cũ; mỗi finding đủ trường theo tiêu chí 5.5; tier theo bảng 5.4; "một nguyên nhân gốc, một finding"; chỉ báo ngoại lệ; agent A đọc hết mọi TC, không lấy mẫu.
- **Định dạng trả về** (đúng các mục dưới, không thêm phần khác):

```
### FINDINGS
| Tier | TC | REV (chính; phụ) | Loại việc (Sửa TC / Thêm TC) | Vấn đề (1 câu) | Sửa thế nào (1 câu) | Bằng chứng (trích nguyên văn TC/spec) | Lý do cần fix | Loại kiểm (+ độ chắc chắn) | Hậu quả × rủi ro |
### VE_NGOAI_LE        (chỉ agent A)
| REQ/AC | Vế | Partial / Not Covered / Chưa kiểm tra được | Bằng chứng | Finding |
Tổng: X vế · Covered A · Partial B · Not Covered C · Chưa kiểm tra được D
### CAU_HOI_PM_BA
| Câu hỏi (1 câu) | TC bị ảnh hưởng | Nhãn (Unconfirmed / Nghi lỗi spec / Chưa nêu) |
### TRANG_THAI_MUC
| REV | Đạt / Có finding / Kiểm một phần / Không áp dụng / Chưa kiểm tra được | Ghi chú 1 câu |
### UNG_VIEN_LOAI
| Kiểm | TC | Lý do loại |
```

---

## Bước 5 — Lưu

1. **Gộp finding** từ hai agent: cùng nguyên nhân gốc → một finding, gộp danh sách TC (tiêu chí 5.5, bảng chồng lấn). Trạng thái một mục lấy theo bên nặng nhất (Có finding > Kiểm một phần > Chưa kiểm tra được > Đạt > Không áp dụng).
2. Đánh mã finding theo tier: `C-01…`, `M-01…`, `m-01…`, `S-01…`. Minor cùng kiểu gộp một mã.
3. **Verdict và độ phủ review** theo tiêu chí 5.4.
4. **Lưu hai file** (ghi đè khi review lại cùng version):
   - Report chính: `python3 -I .claude/scripts/module_files.py path testing/[module] review N`
   - Phụ lục: `python3 -I .claude/scripts/module_files.py path testing/[module] review-detail N`

### Format report chính (`[module]-review-vN.md`), mục tiêu ≤ 50 dòng

```markdown
# Review TC — [Module Name] (v[N])

**File:** `testing/[module]/[module]-testcases-vN.md` · **Chế độ:** Full | Quick · **Ngày:** [date] · **Tổng TC:** X
**Verdict:** NEEDS FIX · 🔴 Critical A · 🟠 Major B · 🟡 Minor C · Suggestion D
**Độ phủ review:** Đã kiểm X/17 · Kiểm một phần P · Không áp dụng Y · Chưa kiểm tra được Z

**Tóm tắt:** [tối đa 3 câu: bộ TC mạnh ở đâu, 2–3 vấn đề chính]

## A. Sửa TC có sẵn
| Tier | TC | Vấn đề | Sửa thế nào | Mã |
|---|---|---|---|---|
| 🟠 Major | 009 | Tắt mạng trước nên không hoàn tất được sheet Google | Hoàn tất đăng nhập rồi mới chặn request tới backend | M-03 |
| 🟡 Minor | 001, 002, 009 | Function Name lẫn Việt/Anh | Thống nhất một cách viết | m-07 |

## B. Thêm TC mới
| Tier | Thêm TC gì | Cho REQ/AC | Mã |
|---|---|---|---|

## C. Cần PM/BA trả lời
| # | Câu hỏi | TC bị ảnh hưởng |
|---|---|---|

> Chi tiết bằng chứng, lý do và trạng thái từng tiêu chí: `[module]-review-detail-vN.md` (tra theo Mã).
```

Quy tắc: gom theo TC; mỗi việc 1 dòng; Minor cùng kiểu gộp một dòng; sắp theo tier rồi theo TC; ID TC ghi số rút gọn khi cùng tiền tố. Không có việc ở mục nào thì ghi "Không có".

### Format phụ lục (`[module]-review-detail-vN.md`)

1. Header: file, chế độ, nguồn AC, verdict, độ phủ review.
2. Bảng gán rủi ro (Bước 3).
3. Trạng thái 17 mục REV (1 dòng mỗi mục).
4. Findings chi tiết theo mã: REV chính/phụ, TC/REQ, bằng chứng, lý do, đề xuất, loại kiểm, tier (hậu quả × rủi ro, lý do nếu lệch bậc), nhãn "lỗi lọt qua gen" / "ngoài mẫu" nếu có.
5. Coverage theo vế: dòng tổng + bảng vế ngoại lệ.
6. Chưa kiểm tra được: phần, lý do, ai bổ sung.
7. Kết quả kiểm máy: bảng tổng K1–K15 và các ứng viên bị loại kèm lý do.

---

## Kết thúc

```
✅ Review hoàn thành.
Report: testing/[module]/[module]-review-vN.md
Phụ lục: testing/[module]/[module]-review-detail-vN.md

Verdict: NEEDS FIX
🔴 Critical: A  |  🟠 Major: B  |  🟡 Minor: C  |  Suggestion: D
Độ phủ review: Đã kiểm X/17 · Kiểm một phần P · Không áp dụng Y · Chưa kiểm tra được Z
```
