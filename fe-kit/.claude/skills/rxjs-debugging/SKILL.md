---
name: rxjs-debugging
description: 
---

# Debugging

**Category:** rxjs · **Status:** 🟢 Active

## When to use
Khi cần lần theo và gỡ lỗi luồng RxJS: giá trị emit, thứ tự, lỗi không rõ nguồn.

## Steps
1. Chèn `tap` ở các điểm trong `pipe` để log giá trị mà không thay đổi luồng.
2. Gắn nhãn log rõ (`tap(v => console.log('[search]', v))`) để biết bước nào emit gì.
3. Theo dõi cả `next`/`error`/`complete` để biết luồng dừng vì lỗi hay hoàn tất.
4. Dùng marble test (`TestScheduler`) để kiểm tra timing/operator một cách xác định.
5. Khi nghi rò rỉ, log lúc subscribe/unsubscribe để xác nhận teardown.

## Template
```ts
source$.pipe(
  tap((v) => console.log('[in]', v)),
  switchMap((q) => api.search(q)),
  tap({ next: (r) => console.log('[out]', r),
        error: (e) => console.error('[err]', e) }),
).subscribe();

// marble test
testScheduler.run(({ cold, expectObservable }) => {
  expectObservable(stream$).toBe('--a--b|', { a: 1, b: 2 });
});
```

## Example
**Good:** `tap` có nhãn ở từng bước, theo dõi error/complete, marble test cho timing.
**Avoid:** subscribe rải `console.log` phá luồng, bỏ qua nhánh error, đoán timing thay vì marble test.

## Checklist
- [ ] Dùng `tap` có nhãn, không phá luồng
- [ ] Theo dõi cả next/error/complete
- [ ] Marble test cho logic timing
