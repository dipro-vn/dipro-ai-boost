---
description: Bước 1/3 — Phân tích requirements: System Model → tìm lỗ hổng bằng lens → Question Gate (ít câu, trúng đích) → mapping REQ→AC → Screen Inventory (nếu có design). Output là analysis.md dùng cho /plan-tcs.
skills:
  - rbt_manual_testing
  - requirements_analyzer
---

Thực hiện **Section 2: Requirement Analysis** từ skill `rbt_manual_testing`, theo phương pháp trong skill `requirements_analyzer` (System Model, 8 Lens, Question Gate).

**Mục tiêu:** giúp con người phát hiện lỗ hổng mà spec/design không nói tới. Chất lượng đo bằng độ trúng của câu hỏi, không bằng số lượng.

## Hướng dẫn

1. Đọc **toàn bộ** requirements doc (kể cả comments, attachments) — project context lấy từ CLAUDE.md (Claude Code tự nạp). **Chưa sinh câu hỏi ở bước này.**

2. Nếu có design input: đọc design theo `## Design Integration` trong skill `requirements_analyzer` (Figma 2 phase có checkpoint chọn page/frame). **Lưu lại danh sách frame/screen đã confirm** để làm Screen Inventory — để `/plan-tcs` dùng trực tiếp.

3. **Summary + System Model** — hiển thị inline, **chờ user xác nhận trước khi tiếp tục** (đây là checkpoint duy nhất của bước này):

   **Summary:**
   - Tên tính năng / module
   - **Mã module** (đề xuất 3 chữ cái viết hoa, VD `LOG`, `MED`) — dùng làm ID Q&A (`Q-LOG-001`) và ID test case (`LOG-001`); user xác nhận hoặc sửa ở checkpoint này
   - Mục đích nghiệp vụ (1-2 câu)
   - Actor chính (tên + vai trò **một dòng**; quyền theo hành động chỉ ghi ở Actor × Action)
   - **Locale** (`JP` nếu là hệ thống Nhật: UI/message tiếng Nhật hoặc `CLAUDE.md` ghi Locale: JP; user xác nhận ở checkpoint này) — `JP` bật bộ validate chuẩn Nhật ở `/gen-tcs`, không sinh Q&A thêm
   - Scope boundary (**tên** các màn hình / luồng, mỗi cái một dòng, không mô tả các bước; out-of-scope nếu spec nói rõ)
   - Dependencies: module/hệ thống mà spec nhắc tới, cùng modules trong `testing/` đã có `analysis.md` mà module này có thể chạm. Mỗi module ghi **mức ảnh hưởng** (trực tiếp / gián tiếp / nhẹ) và **điểm chạm** cụ thể, mỗi điểm một dòng — để user kiểm tra agent hiểu dependency đúng chưa. Module đã xét và loại thì gom vào một dòng "Đã xét, không liên quan"

   **System Model** (rút từ spec, không bịa thêm):
   - Thực thể & định danh
   - Vòng đời / State (cả state của UI: filter, sort, selection)
   - Actor × Action (nếu có phân quyền / điều kiện theo trạng thái): dạng ma trận Action × Actor, mỗi ô ✅ / ❌ (suy ra) / ? (spec im lặng) — xem skill `requirements_analyzer`
   - Luồng dữ liệu bên trong module (nguồn → đích). Phụ thuộc ngoài đã ghi ở Summary › Dependencies — không lặp lại
   - Giả định môi trường ngầm của spec

   **Một thông tin chỉ ghi ở một nơi:** theo `### Một thông tin chỉ ghi ở một nơi` trong skill `requirements_analyzer` — Summary = phạm vi (tên actor/luồng, Dependencies), System Model = cấu trúc và hành vi; chỗ cần nhắc phần kia thì tham chiếu, không chép lại.

   **Trình bày:** theo `### Quy tắc trình bày Summary và System Model` trong skill `requirements_analyzer` — mỗi mục là một bullet tiêu đề, mỗi đối tượng/ý độc lập một dòng con riêng, chỉ viết tiếp cùng dòng khi các vế liên quan trực tiếp. Không viết thành đoạn văn liền.

   > *"Tôi hiểu hệ thống như trên. Có chỗ nào hiểu sai hoặc thiếu không? (Nếu mô hình đúng, tôi sẽ đi tìm lỗ hổng trên mô hình này.)"*

4. Sau khi user xác nhận, thực hiện **không dừng lại hỏi thêm**:

   **A — Tìm lỗ hổng:**
   1. Áp 8 Lens (L1-L8) lên System Model → sinh danh sách **ứng viên** câu hỏi. Dành nhiều công sức nhất cho L1-L5 (state, định danh, thao tác hàng loạt, lỗi từng phần, môi trường).
   2. Cross-check design (nếu có) theo bảng ưu tiên trong skill: luồng/state thiếu trước, lệch hiển thị sau.
   3. Cho **từng ứng viên đi qua Question Gate** (G1-G4) → phân loại: **Q&A** (cần quyết định) / **ASM** (assumption có căn cứ) / **DIF** (lệch spec↔design) / loại bỏ.
   4. Xếp theo mức ảnh hưởng (không có trần số lượng — số câu do gate quyết định). Tự phản biện: chọn ★ 3 câu quan trọng nhất; câu nào có thể được trả lời "bỏ qua/theo design/có" thì hạ xuống ASM (chỉ khi đoán sai có rủi ro Medium trở lên) hoặc loại.

   **B — Impact Analysis** *(chỉ khi có dependency có căn cứ; không có thì bỏ qua mục này)*:
   - Với mỗi dependency: xác định điểm chạm, hành vi hiện có của module kia có thể vỡ, và mức rủi ro — theo `### Impact Analysis` trong skill `requirements_analyzer`
   - Mỗi dòng một hành vi cần kiểm lại; chỉ ghi khi có căn cứ (spec / `analysis.md` module kia / design); **không** viết test scenario ở bước này

   **C — Mapping REQ → AC:** *(riêng việc gán mã REQ phải làm trước A và B, vì Reference của Q&A và IMP dùng mã này)*
   - Xác định các luồng: Happy Path, Alternate Paths, Exception Paths
   - **Gán mã REQ trước khi sinh câu hỏi:** dùng đúng mã trong spec nếu có; nếu spec không đánh mã thì gán `REQ-01`, `REQ-02`, ... theo thứ tự trong spec. Mã này dùng nhất quán ở bảng AC, cột Reference của Q&A và ASM
   - Map từng requirement thành AC có thể kiểm chứng
   - Status: `Confirmed` (spec nói rõ) / `Assumed` (suy luận có căn cứ, gắn ASM-XX) / `TBD` (phụ thuộc Q-MOD-XXX chưa trả lời)

5. Lưu output ra `testing/[module]/analysis.md`

6. Sau khi lưu, **tóm tắt trong chat** (ngắn, không dán lại cả bảng):
   - Số lượng: Q&A (High/Medium), ASM, DIF, IMP (nếu có)
   - **3 câu ★ quan trọng nhất** (1 dòng mỗi câu)
   - Nhắc: chỉ Q&A cần PM/BA trả lời; ASM chỉ cần phản đối nếu sai; DIF chỉ cần chọn A/B

## Input cần thiết

- Requirements doc (link Google Drive / Docs / Figma / file .md / mô tả trực tiếp)
- Design input: Figma link / screenshot / PDF export design *(optional — nếu có, AI sẽ cross-check spec vs design)*

## Output

`testing/[module]/analysis.md`

```markdown
# Requirements Analysis: [Module Name]

## Summary
- **Module:** [tên module]
- **Mã module:** [3 chữ cái viết hoa, VD LOG — dùng cho ID Q-LOG-001 và TC LOG-001]
- **Mục đích:** [1-2 câu mô tả nghiệp vụ]
- **Actors liên quan:**
  - [Actor 1]: [vai trò một dòng — không liệt kê quyền, quyền nằm ở Actor × Action]
  - [Actor 2]: ...
- **Platform:** [ghi nếu khác project default — để trống nếu giống]
- **Locale:** [JP nếu là hệ thống Nhật — để trống nếu không]
- **Luồng trong scope:** *(chỉ tên luồng/màn hình — không mũi tên, không liệt kê các bước; chi tiết nằm ở System Model)*
  - [Tên luồng 1]
  - [Tên luồng 2]
- **Out of scope:** *(nếu spec nói rõ)*
  - [Mục 1]
- **Dependencies:** *(mỗi module: mức ảnh hưởng + điểm chạm, mỗi điểm một dòng; hành vi cần kiểm lại và rủi ro nằm ở Impact Analysis)*
  - [module / hệ thống] — ảnh hưởng trực tiếp / gián tiếp / nhẹ:
    - [điểm chạm 1: dữ liệu / luồng / quy tắc dùng chung]
    - [điểm chạm 2]
  - Đã xét, không liên quan: [module A, module B] *(bỏ dòng này nếu không có)*

## System Model
*(mỗi đối tượng/ý độc lập một dòng con riêng; chỉ viết tiếp cùng dòng khi các vế liên quan trực tiếp)*
- **Thực thể & định danh:**
  - [Thực thể 1]:
    - [thuộc tính / định danh / nguồn gốc]
    - [chỗ spec không nêu: ghi "spec không nêu"]
  - [Thực thể 2]: ...
  - Quan hệ: [A — B]
- **Vòng đời / State:**
  - [Thực thể / UI]: [State 1] → [State 2] → ...
  - Đường lùi: [nếu có]
- **Actor × Action:** *(bỏ nếu không áp dụng)*
  - Ma trận (✅ có căn cứ spec · ❌ suy ra · ? spec im lặng):

    | Action | [Actor 1] | [Actor 2] | [Actor 3] |
    |---|---|---|---|
    | [Action] | ✅ [§] | ❌ | ? |

  - Ô **?** có rủi ro Medium trở lên → có Q&A tương ứng (ghi mã `Q-MOD-XXX` vào ô)
- **Luồng dữ liệu:** *(bên trong module; phụ thuộc ngoài xem Summary › Dependencies)*
  - [Nguồn] → [Đích]: [dữ liệu gì]
- **Giả định môi trường ngầm:**
  - [Giả định 1]
  - [Giả định 2]

## Q&A — Cần quyết định
*(không giới hạn số câu; chỉ câu qua Question Gate; ★ ngay sau nhãn **Câu hỏi:** = 3 câu quan trọng nhất; ID dạng `Q-[MÃ MODULE]-[SỐ]`, VD `Q-LOG-001`)*

### [Chủ đề, VD: Dữ liệu & vòng đời]
| ID | Reference | Screen | Câu hỏi | Nếu đoán sai | Severity | Status |
|----|-----------|--------|---------|--------------|----------|--------|
| Q-MOD-001 | [chỉ mã REQ, VD REQ-03 hoặc REQ-03, REQ-07] | [tên màn hình] | * **REQ:** [trích/mô tả spec hoặc design, kèm §x — hoặc "Spec không đề cập tới ..."]<br>* **Câu hỏi:** ★ [một quyết định]<br>* **Phương án đề xuất:**<br>**A.** ...<br>**B.** ...<br>**→ Đề xuất:** A vì ... *(nguồn: theo spec §x / theo design / theo convention / phương án an toàn hơn)* | [TC/AC/hành vi nào sai] | High / Medium | TBD |

> **TBD** = chưa được PM/BA confirm | **Answered** = đã có câu trả lời (sửa tay `analysis.md` để update sau khi PM/BA trả lời)
> Severity: **High** = sai nghiệp vụ lõi / mất hoặc hỏng dữ liệu / tiền-bảo mật-phân quyền / ảnh hưởng ≥2 màn hình | **Medium** = sai 1 luồng chính nhưng không mất dữ liệu.

## Lệch spec ↔ design
*(gom theo loại; mỗi lỗi 1 dòng; người chỉ cần chọn A/B — tách riêng khỏi Q&A cần quyết định)*
| ID | Loại | Screen | Spec ghi | Design ghi | Chọn (A: spec / B: design) | Status |
|----|------|--------|----------|------------|----------------------------|--------|
| DIF-01 | Default / Tên field / Format / Ngôn ngữ / Typo / Element thiếu | ... | ... | ... | Đề xuất: ... | TBD |

## Assumptions
*(agent tự quyết có căn cứ — người chỉ cần phản đối nếu sai; chỉ ghi khi đoán sai có rủi ro Medium trở lên, hành vi hiển nhiên thì không ghi)*
| ID | Reference | Giả định | Căn cứ | Rủi ro nếu sai |
|----|-----------|----------|--------|----------------|
| ASM-01 | [REQ-XX] | ... | [trích spec/design/convention] | Medium / High |

## Impact Analysis
*(chỉ có khi module có dependency có căn cứ; mỗi dòng một hành vi cần kiểm lại — module bị chạm ở nhiều điểm thì tách thành nhiều dòng; đây là danh sách điểm cần regression, không phải test scenario)*
| ID | Reference | Module bị ảnh hưởng | Điểm chạm | Hành vi hiện có cần kiểm lại | Rủi ro | Căn cứ |
|----|-----------|---------------------|-----------|------------------------------|--------|--------|
| IMP-01 | [mã REQ của module này gây thay đổi] | [module / hệ thống] | [dữ liệu / luồng / màn hình dùng chung] | [một hành vi đang chạy có thể vỡ] | High / Medium / Low | [spec / testing/[module]/analysis.md / design] |

## Acceptance Criteria
| REQ ID | AC ID | AC Content | Status |
|--------|-------|-----------|--------|
| REQ-01 | AC-01 | ... | Confirmed / Assumed (ASM-XX) / TBD (Q-MOD-XXX) |

## Screen Inventory
*(chỉ có nếu đã cross-check với design — Figma/screenshot/PDF. Liệt kê frame; popup/dialog/submenu ghi chú rõ thuộc Screen nào — `/plan-tcs` sẽ gộp chúng vào Screen cha)*

| Screen/Frame | Nguồn (Figma frame name) | Ghi chú |
|---|---|---|
| [Tên screen] | [Frame name trong Figma] | ... |

## History
- v1 ([ngày]): /analyze-req — khởi tạo
```

> AC **Status TBD** = AC phụ thuộc Q&A chưa được PM/BA trả lời — `/gen-tcs` sẽ cảnh báo theo Severity của Q&A liên quan. AC phụ thuộc **DIF chưa chọn** được `/gen-tcs` coi như mức Low (tự động tag `[UNCONFIRMED]`, không dừng hỏi).

## Bước tiếp theo

Sau khi có `analysis.md`, chạy `/plan-tcs` để lên TC Implementation Plan (bắt buộc trước `/gen-tcs`).

> Nếu user gọi thẳng `/gen-tcs` mà module chưa có `analysis.md`, bước này sẽ được `/gen-tcs` tự động trigger trước — checkpoint **System Model confirm** vẫn giữ nguyên như khi chạy `/analyze-req` độc lập.
