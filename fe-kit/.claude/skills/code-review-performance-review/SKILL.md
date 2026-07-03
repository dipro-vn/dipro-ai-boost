---
name: code-review-performance-review
description: 
---

# Performance Review

**Category:** code-review · **Status:** 🟢 Active

## When to use
Khi review hiệu năng: re-render, query, bundle, vòng lặp tốn kém.

## Steps
1. Re-render: prop/inline object/function tạo mới mỗi render; memo hóa hợp lý (`useMemo`/`useCallback`/`React.memo`).
2. Query: tránh N+1, over-fetch; phân trang; cache dữ liệu lặp lại.
3. Bundle: import nặng/cả thư viện; dùng dynamic import, tree-shaking, tránh barrel file lớn.
4. Vòng lặp: tránh O(n²) lồng nhau, tính lại trong loop; precompute/Map lookup.
5. Đo trước khi tối ưu: profiler/DevTools/Lighthouse; tránh tối ưu sớm vô ích.

## Template
```tsx
// list lớn: memo item + key ổn định + lookup O(1)
const byId = useMemo(() => new Map(items.map((i) => [i.id, i])), [items]);
const Row = React.memo(({ item }: { item: Item }) => <li>{item.name}</li>);
```

## Example
**Good:** đo bằng profiler, chỉ memo nơi cần, dynamic import phần nặng, tránh N+1.
**Avoid:** memo bừa khắp nơi, tối ưu khi chưa đo, import cả lib chỉ dùng 1 hàm.

## Checklist
- [ ] Re-render thừa được xử lý (memo đúng chỗ)
- [ ] Query không N+1/over-fetch, có phân trang
- [ ] Bundle: dynamic import phần nặng
- [ ] Tránh O(n²), đã đo trước khi tối ưu
