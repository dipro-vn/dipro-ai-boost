---
name: performance-lazy-loading
description: 
---

# Lazy Loading

**Category:** performance · **Status:** 🟢 Active

## When to use
Khi muốn giảm bundle ban đầu: hoãn tải route, component nặng, modal, ảnh dưới màn hình.

## Steps
1. Dùng `React.lazy` + `Suspense` cho component nặng/ít dùng; bọc fallback hợp lý.
2. Tách route bằng dynamic import (Next.js: `next/dynamic`, React Router: lazy route).
3. Lazy ảnh: `loading="lazy"`, `next/image` tự tối ưu; đặt width/height tránh CLS.
4. Prefetch khi hover/visible cho phần khả năng dùng cao để tránh trễ.
5. Tránh lazy phần ngay above-the-fold (gây nhấp nháy/chậm cảm nhận).

## Template
```tsx
const Chart = lazy(() => import('./Chart'));
<Suspense fallback={<Spinner />}><Chart data={data} /></Suspense>

// Next.js
const Map = dynamic(() => import('./Map'), { ssr: false, loading: () => <Skeleton /> });
```

## Example
**Good:** lazy modal/editor, ảnh `loading="lazy"` có kích thước cố định.
**Avoid:** lazy hero above-the-fold, Suspense không fallback.

## Checklist
- [ ] Component nặng dùng lazy + Suspense
- [ ] Route được code-split
- [ ] Ảnh lazy + đặt kích thước (chống CLS)
- [ ] Không lazy above-the-fold
