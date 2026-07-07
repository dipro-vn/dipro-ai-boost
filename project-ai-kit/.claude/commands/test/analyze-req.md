---
description: Bước 1/4 — Phân tích requirements/SPEC.md → phát hiện điểm mờ (Q&A) → mapping REQ→AC → Screen Inventory. Output là analysis.md dùng cho /plan-tcs. Nếu đã có SPEC.md từ BA, bỏ qua bước AC generation.
skills:
  - rbt_manual_testing
  - requirements_analyzer
argument-hint: <feature-name> [module-name]
---

Bạn là `qc-agent`. Thực hiện **Section 2: Requirement Analysis** từ skill `rbt_manual_testing`.

## Input

- **BMAD flow (thường):** `<DOCS_ROOT>/features/<feature>/SPEC.md` (do BA tạo)
- **Standalone (labo/maintain):** requirements doc link user cung cấp (Google Drive / Docs / Figma / .md / Backlog ticket)
- **Design input** (optional): Figma URL trong SPEC.md ## Screens, hoặc screenshot user paste

## Hướng dẫn

1. **Đọc SPEC.md** (nếu có) hoặc requirements doc user cung cấp.
   - Nếu SPEC.md **đã có AC section** đầy đủ (BA đã confirm) → **skip mapping REQ→AC**, chỉ chạy phần phát hiện Ambiguities + Screen Inventory
   - Nếu chưa có AC / SPEC mơ hồ → chạy full pipeline analyze

2. **Requirements Summary** — hiển thị inline, chờ user xác nhận trước khi tiếp tục:
   - Tên feature / module
   - Mục đích nghiệp vụ (1-2 câu)
   - Actor chính (đối chiếu với `AGENTS.md` bảng Actors nếu có)
   - Các luồng chính trong SPEC (liệt kê sơ)
   - Scope boundary (màn hình / flows in-scope; out-of-scope nếu SPEC nói rõ)
   - Dependencies: scan `<DOCS_ROOT>/features/` → list features/modules đã có `analysis.md` có thể bị ảnh hưởng

   > *"Summary trên có chính xác không? Có điểm nào cần điều chỉnh trước khi tôi phân tích?"*

3. Nếu có Figma URL trong SPEC.md ## Screens hoặc user paste: đọc design → cross-check với SPEC theo `## Design Integration` trong skill `requirements_analyzer` → bổ sung AMB items cho inconsistencies. Đồng thời **lưu danh sách frame/screen đã confirm** vào section Screen Inventory — để `/plan-tcs` dùng trực tiếp.

4. Thực hiện **song song** 2 việc (skip A nếu SPEC.md đã có AC đầy đủ):
   - **A — Mapping REQ → AC:** Map từng requirement thành AC có thể kiểm chứng (chỉ khi SPEC chưa có)
   - **B — Phát hiện Ambiguities:** Sinh danh sách AMB-XX với Reference, Screen, Question + Assumption/Đề xuất, Impact, Severity

5. Đánh dấu AC nào cần clarify từ Q&A (Status: TBD - To Be Decided)
6. Nếu có design input đã cross-check ở bước 3: tổng hợp Screen Inventory (frame/screen đã confirm)
7. Lưu output ra `<DOCS_ROOT>/features/<feature>/test-cases/<module>/analysis.md`

## Output

`<DOCS_ROOT>/features/<feature>/test-cases/<module>/analysis.md`

```markdown
# Requirements Analysis: [Module Name] — <feature>

## Summary
**Feature:** [feature-name]
**Module:** [tên module]
**Mục đích:** [1-2 câu mô tả nghiệp vụ]
**Actors liên quan:** [actors tương tác — đối chiếu AGENTS.md]
**Platform:** [Web / Mobile / API — ghi nếu khác project default]
**Luồng trong scope:** [list flows được mô tả]
**Out of scope:** [nếu SPEC nói rõ]
**Dependencies:** [features/modules liên quan trong <DOCS_ROOT>/features/]
**Source:** SPEC.md → `<DOCS_ROOT>/features/<feature>/SPEC.md` (hoặc doc user cung cấp)

## Q&A — Ambiguities
| ID | Reference | Screen | Question (VN) + Assumption/Đề xuất | Impact | Severity | Status |
|----|-----------|--------|--------------------------------------|--------|----------|--------|
| AMB-01 | REQ-XX / SPEC ## AC-01 | [tên màn hình / Screen Code] | ... Đề xuất: ... | ... | High / Medium / Low | TBD |

> **TBD** = chưa được PM/BA confirm | **Answered** = đã có câu trả lời (sửa tay `analysis.md` để update sau khi PM/BA trả lời)

## Acceptance Criteria
> Nếu SPEC.md đã có AC section confirmed → copy paste vào đây làm reference, **không tự sinh AC mới**.

| REQ ID | AC ID | AC Content | Status |
|--------|-------|-----------|--------|
| REQ-01 | AC-01 | ... | Confirmed / Assumed / TBD |

## Screen Inventory
*(chỉ có nếu đã cross-check với design — Figma/screenshot/PDF)*

| Screen Code | Screen/Frame Name | Nguồn (Figma frame name / SPEC section) | Ghi chú |
|---|---|---|---|
| [E01-S01] | [Tên screen] | [Frame name trong Figma] | ... |

## History
- v1 ([ngày]): /analyze-req — khởi tạo từ [source]
```

> AC **Status TBD** = AC phụ thuộc Q&A chưa được PM/BA trả lời — `/gen-tcs` sẽ cảnh báo khi gặp AC này.

## Bước tiếp theo

Sau khi có `analysis.md`, chạy `/plan-tcs <feature> <module>` để lên TC Implementation Plan (bắt buộc trước `/gen-tcs`).
