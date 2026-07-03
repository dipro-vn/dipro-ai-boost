---
name: rxjs-observable-pattern
description: 
---

# Observable Pattern

**Category:** rxjs · **Status:** 🟢 Active

## When to use
Khi xử lý luồng giá trị bất đồng bộ theo thời gian (event, request, websocket) bằng Observable.

## Steps
1. Dùng Observable khi có nhiều giá trị theo thời gian; Promise chỉ hợp 1 giá trị.
2. Hiểu cold vs hot: cold tạo nguồn riêng mỗi subscribe (HTTP), hot chia sẻ nguồn (event/subject).
3. Dùng `share`/`shareReplay` khi cần multicast một nguồn cold cho nhiều subscriber.
4. Mọi `subscribe` đều phải có đường hủy (`unsubscribe`/`takeUntil`/async pipe).
5. Giữ side-effect trong `tap`/subscribe callback, không trong operator biến đổi.

## Template
```ts
const clicks$ = fromEvent(button, 'click');        // hot
const user$ = http.get<User>('/api/me');           // cold

const sub = user$.subscribe({
  next: (user) => render(user),
  error: (err) => showError(err),
});
// dọn dẹp
sub.unsubscribe();
```

## Example
**Good:** chọn Observable cho luồng nhiều giá trị, hiểu cold/hot, share khi cần, luôn hủy.
**Avoid:** subscribe không hủy, side-effect trong `map`, lạm dụng Observable cho việc 1 phát.

## Checklist
- [ ] Đúng case: nhiều giá trị theo thời gian
- [ ] Hiểu cold/hot, share khi multicast
- [ ] Mọi subscribe có đường hủy
