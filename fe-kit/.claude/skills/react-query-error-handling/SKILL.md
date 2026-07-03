---
name: react-query-error-handling
description: 
---

# Error Handling

**Category:** react-query · **Status:** 🟢 Active

## When to use
Khi xử lý lỗi cho query/mutation: phân loại, retry, error boundary, toast.

## Steps
1. Chuẩn hoá lỗi qua helper `getErrorMessage(err)`; phân biệt network vs 4xx vs 5xx.
2. Cấu hình `retry` hợp lý: không retry lỗi 4xx, có retry lỗi mạng/5xx.
3. Dùng `throwOnError`/`useQueryErrorResetBoundary` để bắt bằng Error Boundary.
4. Mutation: hiển thị lỗi qua toast ở `onError`.
5. Đặt default options ở QueryClient để nhất quán toàn app.

## Template
```ts
new QueryClient({
  defaultOptions: {
    queries: {
      retry: (count, err) => !isClientError(err) && count < 2,
    },
    mutations: {
      onError: (e) => toast.error(getErrorMessage(e)),
    },
  },
});
```

## Example
**Good:** không retry 4xx, toast ở mutation, error boundary cho query critical.
**Avoid:** retry vô hạn, hiện lỗi raw `[object Object]`, nuốt lỗi.

## Checklist
- [ ] getErrorMessage chuẩn hoá lỗi
- [ ] retry phân biệt loại lỗi
- [ ] Error boundary cho query critical
- [ ] Toast/feedback ở mutation
