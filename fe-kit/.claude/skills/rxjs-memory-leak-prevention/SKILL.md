---
name: rxjs-memory-leak-prevention
description: 
---

# Memory Leak Prevention

**Category:** rxjs · **Status:** 🟢 Active

## When to use
Khi cần đảm bảo subscription RxJS được hủy đúng lúc, tránh rò rỉ bộ nhớ.

## Steps
1. Ưu tiên `async` pipe (Angular template) để framework tự subscribe/unsubscribe.
2. Khi subscribe thủ công, hủy bằng `takeUntil(destroy$)` phát ở thời điểm hủy component.
3. Hoặc gom các sub vào `Subscription` và gọi `unsubscribe()` khi teardown.
4. Đặt `takeUntil`/`take(1)` ở cuối `pipe`, sau mọi operator biến đổi.
5. Cẩn thận với nguồn vô hạn (interval, fromEvent, subject) — luôn có điều kiện kết thúc.

## Template
```ts
private destroy$ = new Subject<void>();

ngOnInit() {
  this.data$.pipe(takeUntil(this.destroy$)).subscribe(this.update);
}
ngOnDestroy() {
  this.destroy$.next();
  this.destroy$.complete();
}

// hoặc trong template:  {{ data$ | async }}
```

## Example
**Good:** async pipe khi được, `takeUntil(destroy$)` cho sub thủ công, dọn nguồn vô hạn.
**Avoid:** subscribe không hủy, `takeUntil` đặt sai vị trí, quên teardown interval/fromEvent.

## Checklist
- [ ] Async pipe khi có thể
- [ ] `takeUntil`/`unsubscribe` cho mọi sub thủ công
- [ ] Nguồn vô hạn có điều kiện kết thúc
