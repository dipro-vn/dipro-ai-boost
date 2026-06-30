---
description: Bước 2/3 — Phân tích requirements: summary → phát hiện điểm mờ (Q&A) → mapping REQ→AC. Output là analysis.md gồm 3 sections đủ để triển khai Test Scenarios.
skills:
  - rbt_manual_testing
  - requirements_analyzer
---

Thực hiện **Section 2: Requirement Analysis** từ skill `rbt_manual_testing`.

## Hướng dẫn

1. Đọc requirements doc — project context đã được auto-load qua CLAUDE.md

2. **Requirements Summary** — hiển thị inline, chờ user xác nhận trước khi tiếp tục:
   - Tên tính năng / module
   - Mục đích nghiệp vụ (1-2 câu)
   - Actor chính
   - Các luồng chính trong spec (liệt kê sơ — preview cho Q&A)
   - Scope boundary (màn hình / flows được mô tả; out-of-scope nếu spec nói rõ)
   - Dependencies: scan thư mục `testing/` → list modules đã có `analysis.md` có thể bị ảnh hưởng

   > *"Summary trên có chính xác không? Có điểm nào cần điều chỉnh trước khi tôi phân tích?"*

3. Nếu có design input: đọc design → cross-check với spec theo `## Design Integration` trong skill `requirements_analyzer` → bổ sung AMB items cho inconsistencies phát hiện được

4. Thực hiện **song song** 2 việc:
   - **A — Phát hiện Ambiguities:** Sinh danh sách câu hỏi AMB-XX với Reference, Screen, Question + Assumption/Đề xuất, Impact, Severity
   - **B — Mapping REQ → AC:** Map từng requirement thành AC có thể kiểm chứng

5. Đánh dấu AC nào cần clarify từ Q&A (Status: TBD - To Be Decided)
6. Lưu output ra `testing/[module]/analysis.md`

## Input cần thiết

- Requirements doc (link Google Drive / Docs / Figma / file .md / mô tả trực tiếp)
- Design input: Figma link / screenshot / PDF export design *(optional — nếu có, AI sẽ cross-check spec vs design)*

## Output

`testing/[module]/analysis.md`

```markdown
# Requirements Analysis: [Module Name]

## Summary
**Module:** [tên module]
**Mục đích:** [1-2 câu mô tả nghiệp vụ]
**Actors liên quan:** [actors tương tác với module này]
**Platform:** [ghi nếu khác project default — để trống nếu giống]
**Luồng trong scope:** [list flows được mô tả]
**Out of scope:** [nếu spec nói rõ]
**Dependencies:** [modules liên quan trong testing/]

## Q&A — Ambiguities
| ID | Reference | Screen | Question (VN) + Assumption/Đề xuất | Impact | Severity | Status |
|----|-----------|--------|--------------------------------------|--------|----------|--------|
| AMB-01 | REQ-XX | [tên màn hình] | ... Đề xuất: ... | ... | High / Medium / Low | TBD |

> **TBD** = chưa được PM/BA confirm | **Answered** = đã có câu trả lời (dùng `/sync-qa` để update từ file Q&A công ty)

## Acceptance Criteria
| REQ ID | AC ID | AC Content | Status |
|--------|-------|-----------|--------|
| REQ-01 | AC-01 | ... | Confirmed / Assumed / TBD |

## History
- v1 ([ngày]): /analyze-req — khởi tạo
```

> AC **Status TBD** = AC phụ thuộc vào Q&A chưa được PM/BA trả lời — `/gen-tcs` sẽ cảnh báo khi gặp AC này.

## Bước tiếp theo

Sau khi có `analysis.md`, chạy `/decompose-modules` để phân rã module — hoặc chạy thẳng `/gen-tcs` nếu scope đủ rõ.
