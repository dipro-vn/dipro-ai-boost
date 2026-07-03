---
name: requirement-analysis-backlog-refinement
description: 
---

# Backlog Refinement

**Category:** requirement-analysis · **Status:** 🟢 Active

## When to use
Khi refine một story trong backlog cho sẵn sàng vào sprint.

## Steps
1. Kiểm tra story đạt INVEST: độc lập, nhỏ, có giá trị, ước lượng được.
2. Chia story lớn theo lát cắt dọc (vertical slice), mỗi phần giao được giá trị.
3. Viết/duyệt AC rõ ràng, đo được trước khi ước lượng.
4. Ước lượng tương đối bằng story point qua planning poker.
5. Kiểm Definition of Ready (DoR): đủ thông tin để bắt đầu chưa.
6. Thống nhất Definition of Done (DoD): code + test + review + tài liệu.

## Template
```md
## Story: <tiêu đề>
As a <actor>, I want <mục tiêu> so that <giá trị>.

### Acceptance Criteria
- [ ] …

### DoR
- [ ] AC rõ, đã làm rõ phụ thuộc, có thiết kế

### DoD
- [ ] Code + unit test + review + merge

Estimate: <SP>
```

## Example
**Good:** Story nhỏ theo INVEST, có AC, DoR/DoD rõ, ước lượng đồng thuận.
**Avoid:** Story "làm xong module thanh toán" 21 SP, không AC, không chia nhỏ.

## Checklist
- [ ] Story đạt INVEST, đã chia nhỏ đủ
- [ ] AC rõ, đo được
- [ ] Có ước lượng đồng thuận
- [ ] Thỏa DoR và thống nhất DoD
