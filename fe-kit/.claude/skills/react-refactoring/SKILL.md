---
name: react-refactoring
description: 
---

# Refactoring

**Category:** react · **Status:** 🟢 Active

## When to use
Khi một component quá lớn, lặp logic, hoặc khó đọc nhưng không cần đổi hành vi.

## Steps
1. Xác định hành vi hiện tại làm mốc; ưu tiên có test trước khi sửa.
2. Tách phần UI lặp/độc lập thành sub-component nhỏ, đặt tên theo ý nghĩa.
3. Rút logic state/effect ra custom hook `use*` để render gọn lại.
4. Đổi tên biến/prop mơ hồ thành tên rõ nghĩa; bỏ code chết.
5. Refactor từng bước nhỏ, verify hành vi không đổi sau mỗi bước.

## Template
```tsx
// trước: 1 component 200 dòng
// sau: tách logic + UI
function useProductList(query: string) { /* fetch + filter */ }

function ProductList({ query }: { query: string }) {
  const { items, loading } = useProductList(query);
  if (loading) return <Spinner />;
  return <ul>{items.map((p) => <ProductRow key={p.id} product={p} />)}</ul>;
}
```

## Example
**Good:** Rút `useProductList`, tách `ProductRow`, tên rõ, hành vi giữ nguyên, test pass.
**Avoid:** Refactor + thêm feature cùng lúc; đổi nhiều thứ một commit khó review/rollback.

## Checklist
- [ ] Hành vi giữ nguyên (test/manual xác nhận)
- [ ] Logic tách thành hook, UI tách thành sub-component
- [ ] Tên rõ nghĩa, đã bỏ code chết
- [ ] Refactor tách biệt với thay đổi feature
