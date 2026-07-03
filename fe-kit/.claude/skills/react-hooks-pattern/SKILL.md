---
name: react-hooks-pattern
description: 
---

# Hooks Pattern

**Category:** react · **Status:** 🟢 Active

## When to use
Khi dùng built-in hook hoặc viết custom hook để tách logic khỏi component.

## Steps
1. Tuân thủ rules-of-hooks: chỉ gọi ở top-level, không trong điều kiện/loop.
2. Khai báo đầy đủ dependency cho `useEffect`/`useMemo`/`useCallback`.
3. Tách logic tái dùng thành custom hook tên `use*`, return object/tuple rõ ràng.
4. Cleanup trong `useEffect` (unsubscribe, clearTimeout) để tránh leak.
5. Tránh effect không cần thiết: ưu tiên derive value khi render.

## Template
```tsx
function useUser(id: string) {
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {
    let active = true;
    fetchUser(id).then((u) => active && setUser(u));
    return () => { active = false; };
  }, [id]);
  return user;
}
```

## Example
**Good:** Deps array đủ `[id]`, cleanup chống set state sau unmount, tên `useUser`.
**Avoid:** Gọi hook trong `if`, bỏ trống deps `[]` khi có dùng biến ngoài, quên cleanup.

## Checklist
- [ ] Hook gọi ở top-level, không trong nhánh điều kiện
- [ ] Dependency array đầy đủ, đúng
- [ ] Có cleanup khi cần (sub/timer)
- [ ] Logic tái dùng tách thành `use*` hook
