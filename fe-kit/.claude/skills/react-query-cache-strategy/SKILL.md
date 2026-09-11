---
name: react-query-cache-strategy
description: Chiến lược cache TanStack Query — thiết kế queryKey phân cấp, tinh chỉnh staleTime và gcTime, invalidateQueries có chủ đích, prefetch. Dùng khi data bị fetch lại quá nhiều, cache không cập nhật, hoặc cần tối ưu số request.
---

# Cache Strategy

**Category:** react-query · **Status:** 🟢 Active

## When to use

Khi quản lý cache: thiết kế queryKey, tinh chỉnh staleTime/gcTime, invalidate có chủ đích.

## Steps

1. Dùng queryKey factory tập trung để key nhất quán, tránh hardcode rải rác.
2. Đặt `staleTime` theo độ "tươi" cần thiết; data tĩnh để dài, data động để ngắn.
3. Đặt `gcTime` đủ để giữ cache khi quay lại; mặc định 5 phút.
4. Invalidate đúng phạm vi: theo prefix `['posts']` để cover cả list lẫn detail.
5. Tránh refetch thừa: chỉnh `refetchOnWindowFocus` khi cần.

## Template

```ts
export const postKeys = {
  all: ['posts'] as const,
  lists: () => [...postKeys.all, 'list'] as const,
  detail: (id: string) => [...postKeys.all, 'detail', id] as const,
};
qc.invalidateQueries({ queryKey: postKeys.all }); // cover list + detail
```

## Example

**Good:** key factory, invalidate theo prefix, staleTime theo loại data.
**Avoid:** key string rải rác, invalidate cả app, staleTime đồng loạt 0.

## Checklist

- [ ] queryKey factory tập trung
- [ ] staleTime/gcTime hợp lý: data động tối thiểu 5 phút, data tĩnh lên đến 24 giờ
- [ ] Invalidate đúng phạm vi (prefix)
- [ ] Không refetch thừa
