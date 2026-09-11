---
name: code-review-bug-detection
description: Săn bug khi review code — off-by-one, null/undefined reference, lỗi async và race condition, stale state trong React, dependency array thiếu. Dùng khi review PR cần soi tính đúng đắn của logic.
---

# Bug Detection

**Category:** code-review · **Status:** 🟢 Active

## When to use

Khi review code để tìm bug, tập trung vào các lĩnh vực sau: lỗi off-by-one, tham chiếu null, các vấn đề async, state cũ trong React, và quản lý dependency.

## Steps

1. Off-by-one: biên vòng lặp `<` vs `<=`, slice/index, phân trang.
2. Null/undefined: optional chain thiếu, destructure giá trị rỗng, default sai.
3. Async: thiếu `await`, promise nuốt lỗi, race/stale, không cleanup.
4. State cũ (React): closure giữ giá trị cũ, set state theo giá trị cũ thay vì updater.
5. Dependency: `useEffect`/`useMemo` thiếu hoặc thừa deps gây loop hoặc giá trị cũ.

## Template

```tsx
// BUG: state cũ trong closure
setCount(count + 1); // sai khi gọi liên tiếp
setCount((c) => c + 1); // đúng: dùng updater

// BUG: thiếu await nuốt lỗi
const data = fetchData(); // sai
const data = await fetchData(); // đúng
```

## Example

**Good:** chỉ rõ dòng + kịch bản tái hiện + cách sửa.
**Avoid:** đoán mơ hồ, bỏ qua nhánh async/lỗi, chỉ nhìn happy path.

## Checklist

- [ ] Kiểm off-by-one ở biên/loop/slice
- [ ] Null/undefined được xử lý
- [ ] Async có await + bắt lỗi, không race
- [ ] State dùng updater, deps đúng
