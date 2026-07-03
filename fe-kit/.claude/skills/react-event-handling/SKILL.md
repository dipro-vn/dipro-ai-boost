---
name: react-event-handling
description: 
---

# Event Handling

**Category:** react · **Status:** 🟢 Active

## When to use
Khi viết handler cho sự kiện DOM/UI trong component React.

## Steps
1. Đặt tên handler theo `handle<Subject><Event>` (vd `handleSubmitForm`).
2. Type chính xác event (`React.ChangeEvent<HTMLInputElement>`, `React.MouseEvent`).
3. Tránh tạo hàm nặng/inline tốn kém trong JSX; tách ra hoặc `useCallback` khi cần.
4. Debounce/throttle cho input search, scroll, resize tần suất cao.
5. `preventDefault`/`stopPropagation` khi cần; truyền tham số qua closure gọn.

## Template
```tsx
const handleSearchChange = useMemo(
  () => debounce((value: string) => onSearch(value), 300),
  [onSearch],
);

<input onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
  handleSearchChange(e.target.value)} />
```

## Example
**Good:** `handleSearchChange` debounce 300ms, event được type, prop callback ổn định.
**Avoid:** `onChange={() => doHeavyWork()}` inline mỗi render; không debounce ô search.

## Checklist
- [ ] Handler đặt tên `handle*` rõ nghĩa
- [ ] Event được type, không dùng `any`
- [ ] Debounce/throttle cho sự kiện tần suất cao
- [ ] Không tạo hàm nặng inline mỗi render
