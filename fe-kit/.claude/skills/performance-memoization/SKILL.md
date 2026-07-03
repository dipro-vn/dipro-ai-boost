---
name: performance-memoization
description: 
---

# Memoization

**Category:** performance · **Status:** 🟢 Active

## When to use
Khi có tính toán nặng lặp lại, hoặc cần giữ tham chiếu ổn định cho props của component đã `memo`.

## Steps
1. Đo trước; KHÔNG tối ưu sớm — memo hoá vô tội vạ làm code rối và có thể chậm hơn.
2. `useMemo` cho giá trị tính toán tốn kém hoặc object/array cần ổn định tham chiếu.
3. `useCallback` cho hàm truyền xuống component đã `memo` hoặc làm dependency của effect.
4. `memo` cho component con render thường xuyên với props ổn định.
5. Khai báo dependency array đầy đủ, đúng; tránh dependency thay đổi mỗi render.

## Template
```tsx
const sorted = useMemo(() => heavySort(items), [items]);
const onChange = useCallback((v: string) => setQuery(v), []);
const Child = memo(ChildBase);
```

## Example
**Good:** memo hoá kết quả sort lớn, callback ổn định cho child memo.
**Avoid:** `useMemo` cho phép cộng đơn giản, `useCallback` khắp nơi không có child memo.

## Checklist
- [ ] Có đo trước khi tối ưu
- [ ] useMemo cho tính toán nặng / ref ổn định
- [ ] useCallback đi kèm child memo hoặc effect dep
- [ ] Dependency array đúng và đủ
