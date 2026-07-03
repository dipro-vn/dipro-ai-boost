---
name: nextjs-client-component
description: 
---

# Client Component

**Category:** nextjs · **Status:** 🟢 Active

## When to use
Khi cần state, event handler, hook, hoặc browser API → thêm `'use client'`.

## Steps
1. Đặt `'use client'` ở dòng đầu file khi cần useState/useEffect/onClick.
2. Giữ client component nhỏ, đặt ở "lá" của cây để giảm JS gửi xuống.
3. Nhận data từ Server Component qua props thay vì fetch lại.
4. Không bọc cả trang trong 'use client'; chỉ phần tương tác.
5. Có thể nhận `children` là Server Component để giữ phần tĩnh ở server.

## Template
```tsx
'use client';
import { useState } from 'react';

export function Counter({ initial }: { initial: number }) {
  const [count, setCount] = useState(initial);
  return <button onClick={() => setCount((c) => c + 1)}>{count}</button>;
}
```

## Example
**Good:** Button/counter nhỏ ở lá, nhận initial từ server qua props.
**Avoid:** 'use client' ở layout gốc, fetch lại data đã có ở server.

## Checklist
- [ ] 'use client' chỉ ở nơi cần tương tác
- [ ] Component nhỏ, đặt ở lá
- [ ] Nhận data qua props
- [ ] Không client-hoá cả trang
