---
name: react-performance
description: 
---

# Performance

**Category:** react · **Status:** 🟢 Active

## When to use
Khi component re-render thừa, list lớn lag, hoặc tính toán nặng lặp lại.

## Steps
1. Đo trước bằng React DevTools Profiler; tối ưu đúng chỗ nghẽn, không đoán.
2. `useMemo` cho tính toán nặng; `useCallback` cho callback truyền xuống child memo.
3. `React.memo` cho child tốn kém nhận props ổn định.
4. Dùng `key` ổn định, duy nhất (id thật, không dùng index khi list đổi thứ tự).
5. Code-split (`lazy`/`Suspense`) và virtualize list dài.

## Template
```tsx
const Row = React.memo(function Row({ item, onPick }: RowProps) {
  return <li onClick={() => onPick(item.id)}>{item.label}</li>;
});

const handlePick = useCallback((id: string) => select(id), [select]);
const sorted = useMemo(() => heavySort(items), [items]);
```

## Example
**Good:** `Row` memo + `handlePick` `useCallback` ổn định + `key={item.id}`.
**Avoid:** `key={index}`, memo hóa mọi thứ vô tội vạ, callback mới mỗi render phá memo.

## Checklist
- [ ] Đã profiling xác định nghẽn trước khi tối ưu
- [ ] `key` ổn định, duy nhất (không dùng index khi list đổi)
- [ ] `memo`/`useMemo`/`useCallback` dùng đúng chỗ
- [ ] List dài được virtualize / code-split khi cần
