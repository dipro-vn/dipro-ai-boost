---
name: performance-render-optimization
description: 
---

# Render Optimization

**Category:** performance · **Status:** 🟢 Active

## When to use
Khi component re-render nhiều lần không cần thiết, list dài giật lag, hoặc DevTools Profiler báo render thừa.

## Steps
1. Đo trước bằng React DevTools Profiler để biết component nào render thừa.
2. Tách state cục bộ xuống component nhỏ nhất; tránh đặt state ở cha khiến cả cây re-render.
3. Bọc component con bằng `memo` khi props ổn định; truyền callback qua `useCallback`, object/array qua `useMemo`.
4. Tránh tạo prop mới mỗi render (inline object/array/arrow) làm hỏng memo.
5. Dùng `key` ổn định, KHÔNG dùng index khi list reorder/insert.
6. Cân nhắc tách context hoặc dùng selector để giảm phạm vi cập nhật.

## Template
```tsx
const Row = memo(function Row({ item, onSelect }: Props) {
  return <li onClick={() => onSelect(item.id)}>{item.name}</li>;
});

function List({ items }: { items: Item[] }) {
  const onSelect = useCallback((id: string) => { /* ... */ }, []);
  return <ul>{items.map((it) => <Row key={it.id} item={it} onSelect={onSelect} />)}</ul>;
}
```

## Example
**Good:** key ổn định, callback memo hoá, state tách nhỏ.
**Avoid:** `style={{...}}` inline cho component đã memo, key={index} với list thay đổi.

## Checklist
- [ ] Đo bằng Profiler trước/sau
- [ ] memo + callback/memo prop ổn định
- [ ] key ổn định, không phải index
- [ ] State đặt ở phạm vi nhỏ nhất
