---
name: testing-jest-mocking
description: 
---

# Mocking

**Category:** testing-jest · **Status:** 🟢 Active

## When to use
Khi cần mock module/function/timer hoặc giả lập API (msw) trong test.

## Steps
1. Mock ở ranh giới (module/network), không mock chi tiết nội bộ của unit đang test.
2. `jest.mock('module')` cho dependency; `jest.fn()` cho callback; `jest.spyOn` khi cần giữ impl thật.
3. API request: ưu tiên `msw` chặn ở tầng network thay vì mock fetch thủ công.
4. Timer/Date: `jest.useFakeTimers()` + `advanceTimersByTime`; nhớ restore.
5. Reset giữa các test: `clearMocks`/`resetMocks` để tránh rò trạng thái.

## Template
```ts
jest.mock('@/lib/api');
import { getUser } from '@/lib/api';

beforeEach(() => jest.clearAllMocks());

it('hiển thị tên user', async () => {
  (getUser as jest.Mock).mockResolvedValue({ name: 'An' });
  render(<Profile id="1" />);
  expect(await screen.findByText('An')).toBeInTheDocument();
});
```

## Example
**Good:** mock ở ranh giới network/module, dùng msw cho API, reset mock mỗi test.
**Avoid:** mock quá sâu khiến test vô nghĩa, quên restore timer, để mock rò qua test khác.

## Checklist
- [ ] Mock đúng ranh giới, không mock nội bộ unit
- [ ] API dùng msw khi có thể
- [ ] Fake timer/Date được restore
- [ ] Reset mock giữa các test
