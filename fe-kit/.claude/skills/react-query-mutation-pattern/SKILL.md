---
name: react-query-mutation-pattern
description: 
---

# Mutation Pattern

**Category:** react-query · **Status:** 🟢 Active

## When to use
Khi tạo/sửa/xoá data server-state bằng useMutation.

## Steps
1. Tách mutationFn ra service layer, nhận biến đầu vào rõ kiểu.
2. Trong `onSuccess` gọi `invalidateQueries` đúng queryKey liên quan.
3. Dùng `isPending` để disable nút, hiển thị loading.
4. Xử lý lỗi ở `onError` (toast/message); không nuốt lỗi.
5. Đóng gói vào hook `useXxxMutation` để tái sử dụng.

## Template
```ts
export function useCreatePost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: CreatePostInput) => postApi.create(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['posts'] }),
    onError: (e) => toast.error(getErrorMessage(e)),
  });
}
```

## Example
**Good:** invalidate sau success, isPending disable nút, onError toast.
**Avoid:** Không invalidate (UI stale), bỏ loading, nuốt lỗi im lặng.

## Checklist
- [ ] mutationFn ở service
- [ ] onSuccess invalidate đúng key
- [ ] isPending cho loading/disable
- [ ] onError xử lý lỗi
