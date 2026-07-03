---
name: testing-jest-unit-test-generation
description: 
---

# Unit Test Generation

**Category:** testing-jest · **Status:** 🟢 Active

## When to use
Khi viết unit test (Jest + Testing Library) cho function/component/hook.

## Steps
1. Xác định đơn vị cần test và contract (input → output/side-effect).
2. Cấu trúc AAA: Arrange, Act, Assert; mỗi test 1 hành vi.
3. Test theo hành vi người dùng (getByRole/Text), không test chi tiết nội bộ.
4. Phủ happy path + edge case + lỗi.
5. Tên test mô tả hành vi: `it('hiển thị lỗi khi email trống')`.

## Template
```ts
it('gọi onSubmit với giá trị đã nhập', async () => {
  const onSubmit = jest.fn();
  render(<LoginForm onSubmit={onSubmit} />);
  await userEvent.type(screen.getByLabelText('Email'), 'a@b.com');
  await userEvent.click(screen.getByRole('button', { name: /đăng nhập/i }));
  expect(onSubmit).toHaveBeenCalledWith({ email: 'a@b.com' });
});
```

## Example
**Good:** query theo role, assert hành vi, tên test rõ.
**Avoid:** test implementation detail, snapshot bừa, không cleanup.

## Checklist
- [ ] AAA rõ ràng, 1 hành vi/test
- [ ] Query theo accessibility
- [ ] Phủ edge case & lỗi
- [ ] Tên test mô tả hành vi
