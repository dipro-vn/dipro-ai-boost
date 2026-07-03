---
name: rxjs-operator-selection
description: 
---

# Operator Selection

**Category:** rxjs · **Status:** 🟢 Active

## When to use
Khi cần chọn đúng operator RxJS cho biến đổi/làm phẳng luồng (map, các *Map, debounceTime).

## Steps
1. `map` để biến đổi đồng bộ từng giá trị; không dùng cho Observable lồng.
2. `switchMap` khi chỉ cần kết quả mới nhất, hủy request cũ (search, autocomplete).
3. `mergeMap` khi chạy song song và giữ mọi kết quả (không quan tâm thứ tự).
4. `concatMap` khi cần tuần tự, giữ thứ tự, chờ xong cái trước (ghi tuần tự).
5. `debounceTime`/`throttleTime` để giảm tần suất; `distinctUntilChanged` bỏ lặp.

## Template
```ts
// search: hủy cái cũ
input$.pipe(debounceTime(300), switchMap((q) => api.search(q)));

// upload song song, giữ hết
files$.pipe(mergeMap((f) => api.upload(f)));

// lưu tuần tự, đúng thứ tự
saves$.pipe(concatMap((p) => api.save(p)));
```

## Example
**Good:** `switchMap` cho search, `mergeMap` cho song song, `concatMap` cho tuần tự, debounce input.
**Avoid:** `mergeMap` cho search (race kết quả cũ), `switchMap` cho ghi tuần tự (mất dữ liệu), `map` lồng Observable.

## Checklist
- [ ] Đúng *Map theo nhu cầu hủy/song song/tuần tự
- [ ] debounce/throttle cho luồng tần suất cao
- [ ] Không dùng `map` để làm phẳng Observable
