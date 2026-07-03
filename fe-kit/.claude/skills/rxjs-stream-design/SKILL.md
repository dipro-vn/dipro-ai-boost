---
name: rxjs-stream-design
description: 
---

# Stream Design

**Category:** rxjs · **Status:** 🟢 Active

## When to use
Khi thiết kế luồng dữ liệu RxJS theo mô hình declarative: nguồn → pipe biến đổi → output.

## Steps
1. Xác định rõ nguồn (event, input, HTTP) làm điểm bắt đầu luồng.
2. Mô tả biến đổi bằng chuỗi operator trong `pipe`, mỗi bước một nhiệm vụ.
3. Giữ luồng declarative: không nhồi `if`/biến trạng thái ngoài; để operator lo.
4. Kết hợp nhiều nguồn bằng `combineLatest`/`merge`/`withLatestFrom` thay vì subscribe lồng.
5. Đầu ra (subscribe/async pipe) chỉ nhận kết quả, không chứa logic biến đổi.

## Template
```ts
const results$ = searchInput$.pipe(
  map((e) => e.target.value),
  debounceTime(300),
  distinctUntilChanged(),
  filter((q) => q.length > 1),
  switchMap((q) => api.search(q)),
);

results$.subscribe(render);  // output: chỉ hiển thị
```

## Example
**Good:** nguồn rõ, mỗi operator một việc, luồng declarative, kết hợp nguồn bằng operator.
**Avoid:** subscribe lồng subscribe, biến trạng thái ngoài để điều khiển luồng, logic trong output.

## Checklist
- [ ] Nguồn → pipe → output tách bạch
- [ ] Mỗi operator một nhiệm vụ
- [ ] Kết hợp nguồn bằng operator, không subscribe lồng
