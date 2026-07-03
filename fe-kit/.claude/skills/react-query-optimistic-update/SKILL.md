---
name: react-query-optimistic-update
description: 
---

# Optimistic Update

**Category:** react-query · **Status:** 🟢 Active

## When to use
Khi muốn UI phản hồi tức thì trước khi server xác nhận (like, toggle, edit nhanh).

## Steps
1. Trong `onMutate`: cancel query đang chạy, snapshot data cũ, set data mới lạc quan.
2. Trả về context chứa snapshot để rollback.
3. Trong `onError`: rollback bằng snapshot từ context.
4. Trong `onSettled`: invalidate để đồng bộ lại với server.
5. Dùng cho thao tác xác suất thành công cao; tránh cho thao tác quan trọng dễ fail.

## Template
```ts
useMutation({
  mutationFn: toggleLike,
  onMutate: async (id) => {
    await qc.cancelQueries({ queryKey: ['post', id] });
    const prev = qc.getQueryData(['post', id]);
    qc.setQueryData(['post', id], (o: Post) => ({ ...o, liked: !o.liked }));
    return { prev };
  },
  onError: (_e, id, ctx) => qc.setQueryData(['post', id], ctx?.prev),
  onSettled: (_d, _e, id) => qc.invalidateQueries({ queryKey: ['post', id] }),
});
```

## Example
**Good:** cancel + snapshot + rollback + settle invalidate.
**Avoid:** Bỏ rollback (UI sai khi fail), quên cancelQueries gây ghi đè.

## Checklist
- [ ] onMutate: cancel + snapshot + set lạc quan
- [ ] Trả context để rollback
- [ ] onError rollback
- [ ] onSettled invalidate đồng bộ
