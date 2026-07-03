---
name: testing-jest-snapshot-testing
description: 
---

# Snapshot Testing

**Category:** testing-jest · **Status:** 🟢 Active

## When to use
Khi dùng snapshot có chủ đích: nhỏ, ổn định, review diff; tránh lạm dụng.

## Steps
1. Snapshot chỉ cho output ổn định, ít đổi (markup nhỏ, kết quả serialize).
2. Ưu tiên `toMatchInlineSnapshot` để diff nằm ngay trong test, dễ review.
3. Review kỹ mọi diff snapshot trong PR; không `-u` mù khi test đỏ.
4. Tránh snapshot component lớn/động (ngày giờ, id ngẫu nhiên) — gây flaky.
5. Với hành vi cụ thể, dùng assertion thường thay vì snapshot toàn bộ.

## Template
```ts
it('render badge đúng nhãn', () => {
  const { container } = render(<Badge tone="success">OK</Badge>);
  expect(container.firstChild).toMatchInlineSnapshot(`
    <span class="badge badge--success">OK</span>
  `);
});
```

## Example
**Good:** snapshot nhỏ, inline, output ổn định, diff được review.
**Avoid:** snapshot cả trang, chứa giá trị động, update `-u` không nhìn diff.

## Checklist
- [ ] Snapshot nhỏ & ổn định
- [ ] Ưu tiên inline snapshot
- [ ] Review diff, không -u mù
- [ ] Không chứa giá trị động (date/id)
