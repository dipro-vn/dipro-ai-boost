---
name: testing-jest-edge-case-testing
description: 
---

# Edge Case Testing

**Category:** testing-jest · **Status:** 🟢 Active

## When to use
Khi cần phủ biên: boundary, null/empty, async lỗi, race condition.

## Steps
1. Boundary: 0, 1, max, vượt max, số âm, chuỗi rỗng/quá dài.
2. Giá trị rỗng: `null`, `undefined`, `[]`, `{}`, `''` — kiểm tra không crash.
3. Async: test cả resolve và reject; assert thông báo lỗi/UI fallback.
4. Race: nhiều thao tác đồng thời, request cũ trả về sau (stale), debounce.
5. Dùng `it.each` để chạy nhiều input biên gọn gàng.

## Template
```ts
it.each([
  ['', 'Email là bắt buộc'],
  ['abc', 'Email không hợp lệ'],
])('input %s → lỗi %s', (input, msg) => {
  expect(validateEmail(input)).toBe(msg);
});

it('hiển thị lỗi khi API thất bại', async () => {
  (fetchData as jest.Mock).mockRejectedValue(new Error('fail'));
  render(<List />);
  expect(await screen.findByText(/đã có lỗi/i)).toBeInTheDocument();
});
```

## Example
**Good:** phủ boundary + null/empty + reject + race, dùng it.each.
**Avoid:** chỉ test happy path, bỏ qua nhánh reject, không test giá trị rỗng.

## Checklist
- [ ] Phủ boundary (0/1/max/âm)
- [ ] Phủ null/undefined/empty
- [ ] Test async reject + UI lỗi
- [ ] Cân nhắc race/stale request
