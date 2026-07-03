---
name: ui-analysis-ux-risk-analysis
description: 
---

# UX Risk Analysis

**Category:** ui-analysis · **Status:** 🟢 Active

## When to use
Khi rà soát design để tìm rủi ro UX ở các trạng thái không phải happy path.

## Steps
1. Loading: design có skeleton/spinner cho fetch chậm chưa.
2. Empty: danh sách rỗng có empty state hướng dẫn hành động tiếp theo không.
3. Error: lỗi API/validation hiển thị ở đâu, có cách phục hồi/retry không.
4. Edge content: tên rất dài, số lớn, ảnh thiếu — có truncate/wrap/placeholder.
5. Phản hồi hành động: trạng thái success/disabled khi submit, chống double-click.
6. Đề xuất bổ sung state còn thiếu và ghi rõ hành vi mong đợi.

## Template
```md
## UX risks: <màn hình>
| State | Có trong design? | Rủi ro | Đề xuất |
|-------|------------------|--------|---------|
| Loading | thiếu | màn hình trắng | skeleton |
| Empty | thiếu | bí lối | empty state + CTA |
| Error | thiếu | không retry | toast + nút thử lại |
| Long text | — | vỡ layout | truncate + tooltip |
```

## Example
**Good:** Chỉ ra thiếu empty/error state, đề xuất skeleton và xử lý tên dài bằng truncate.
**Avoid:** Chỉ làm theo design happy path, bỏ trống loading/empty/error.

## Checklist
- [ ] Có loading state cho fetch chậm
- [ ] Có empty state với hướng dẫn
- [ ] Có error state và cách phục hồi
- [ ] Xử lý edge content dài/lớn/thiếu
