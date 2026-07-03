---
name: react-query-query-pattern
description: 
---

# Query Pattern

**Category:** react-query · **Status:** 🟢 Active

## When to use
Khi fetch data server-state bằng TanStack Query (useQuery).

## Steps
1. Đặt queryKey dạng mảng ổn định, gồm cả tham số (`['user', id]`).
2. Tách queryFn ra service layer, không gọi fetch inline.
3. Cấu hình staleTime/enabled hợp lý; `enabled: !!id` khi phụ thuộc.
4. Xử lý isLoading/isError/data rõ ràng ở UI.
5. Đặt logic vào custom hook `useXxxQuery` để reuse.

## Template
```ts
export function useUser(id: string) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: () => userApi.getById(id),
    enabled: !!id,
    staleTime: 60_000,
  });
}
```

## Example
**Good:** queryKey gồm id, queryFn ở service, enabled guard.
**Avoid:** queryKey string trùng nhau, fetch trong component, bỏ qua error.

## Checklist
- [ ] queryKey ổn định, đủ tham số
- [ ] queryFn tách khỏi UI
- [ ] Có enabled/staleTime hợp lý
- [ ] Xử lý loading/error
