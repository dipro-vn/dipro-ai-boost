# Ba Agent — Bước 5.6 AI Self-Feedback (POLICIES.md §4.5)

> Sau Bước 5.5 (visual recheck), BA phải chạy tiếp **AI Self-Feedback** theo policy chung `POLICIES.md §4.5`.

**Đọc lại toàn bộ SPEC.md + 3 Figma outputs + HTML prototype** (và Basic Design workbook nếu Output 5 đã chạy), sau đó tự trả lời **2 câu hỏi cốt lõi**:

**Câu 1 — Flow có bị THIẾU BƯỚC nào không?**
- Actor nào chưa được đề cập trong `## Actors & Preconditions`?
- Bước nào trong Happy Path chưa có screen tương ứng?
- Non-happy case nào chưa cover (mất mạng, timeout, permission denied...)?
- Có edge case nào SPEC nêu mà chưa có node trong Figma Output 2?

**Câu 2 — Có điểm nào SAI hoặc THIẾU SÓT không?**
- SPEC section nào tự mâu thuẫn (VD: `## Screens` liệt kê 8 nhưng `## Screen Details` chỉ có 6)?
- Screen Code trong SPEC có khớp với Screen Code trong Figma bảng Index không?
- Có link Figma nào bị hỏng / chưa điền không?
- Số liệu trong Output 2 bảng "Tổng: N màn hình" có khớp với `## Screens` không?
- **Non-Happy đã ở dạng BẢNG 4 cột chưa, hay còn văn xuôi?** Đếm: `số screen có bảng Non-Happy` phải `= tổng số screen` (100%). Còn screen nào ghi kiểu `giống <CODE>` / `theo pattern chuẩn` / `(rút gọn)` → **FAIL**, phải viết bảng thật (xem `spec-template.md` → Rule FORMAT Non-Happy)
- **Cột `Message` có phải nội dung THẬT user nhìn thấy không**, hay chỉ là mô tả chung chung ("báo lỗi cho user")? Mô tả chung chung → FAIL
- **Thống kê màn hình đã cộng Toast/Modal/Popup/Banner/Full screen/Empty state chưa?** `TỔNG` trong SPEC `## Screens` phải khớp `TỔNG` in trên Figma Output 2 — lệch → FAIL
- **Bảng ⑦ ERROR/POPUP INDEX trên Figma có đủ 100% error display của SPEC không** (không rút gọn), và ID `E-xxx` có trace 1-1 về SPEC không?
- **Error-Screen Strip** đã vẽ đủ các lỗi loại `Full screen` · `Modal` · `Popup` thành node chưa, mỗi node có ghi `◀ màn cha` + message thật chưa?
- Actor color có nhất quán giữa Output 1/2/3 không?
- Có bước nào trong `## Flow Tổng Quan` chưa xuất hiện trong Figma Output 1 flow?
- **FR Coverage — đã in `THIẾU: []` chưa?** `set(FR nguồn) − set(FR trong bảng `## Screens`) = ∅`, và mỗi Hành động ở Sitemap Output 1 có tag `#N` chưa? (`recheck.md` Tiêu chí 8). **Đây là phép duy nhất bắt được "chức năng đáng lẽ phải có mà không có" — các phép còn lại chỉ đối chiếu nội bộ giữa các artifact với nhau.**

**Câu 3 — Output 4 có thật sự dùng được không? (không được trả lời bằng cảm tính)**

Phần này KHÔNG tự đánh giá bằng mắt — phải trích số thật từ Bước 5.7
(`verify-prototype.js`, xem `figma-outputs/output-4-verify.md`):

- `FAIL` có đúng bằng **0** không? Còn FAIL → chưa được PASS self-feedback
- Có màn nào **cụt đường** / **không tới được** không? (nhóm `REACH`)
- **Đăng nhập được** vào từng website chưa? Nhiều site → từng tab một
- Màn `UNKNOWN`/`INFERENCE` có hiện placeholder chờ BRSE chưa? (nhóm `P2`)
- Prototype là **website bấm được** hay tài liệu cuộn dọc? (nhóm `SHAPE`)
- Số `SKIPPED` có đúng bằng số error của màn UNKNOWN không? Lệch → đang né FAIL

**Format báo cáo (bắt buộc):**

```
🔍 BA Self-Feedback — <Feature Name>

✅ Flow đủ N bước (Actor A: X, Actor B: Y)
   • Đã cover: happy path, decision points, non-happy cases (mất mạng, timeout, mic denied, declined)

✅ Không có mâu thuẫn phát hiện
   • ## Screens (8 rows) khớp với ## Screen Details (8 blocks) khớp với Figma Output 2 bảng Index (15 items = 8 screen + 2 popup + 4 toast + 1 push)
   • Actor colors: DA=BLUE, CA=GREEN nhất quán 3 outputs
   • Tất cả Figma Link đã điền cho 8 screens

Kết quả: PASS ✅ → Sẵn sàng bàn giao
```

**Nếu phát hiện vấn đề:**
```
🔍 BA Self-Feedback — <Feature Name>

⚠️ Phát hiện 2 vấn đề:

[THIẾU] Non-happy "Actor B (Receiver) đăng xuất giữa cuộc gọi" chưa cover
  → SPEC ## Alternative Flows thiếu case này
  → Figma Output 2 Non-Happy zone chưa có luồng tương ứng
  → Đề xuất: bổ sung case + toast "Người dùng đăng xuất" → Call Ended

[SAI] Screen count không khớp
  → ## Screens ghi 8, nhưng ## Screen Details có 9 blocks (AX_FEAT_007 dư)
  → Figma bảng Index đếm 15 (không có AX_FEAT_007)
  → Đề xuất: xoá block AX_FEAT_007 khỏi ## Screen Details

→ Có cho phép BA fix ngay không? (Yes/No)
```

**Anti-patterns:** xem `POLICIES.md §4.5` — không được skip, không được báo PASS mà không list điểm đã check.
