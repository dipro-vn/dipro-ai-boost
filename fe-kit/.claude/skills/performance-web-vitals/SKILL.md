---
name: performance-web-vitals
description: 
---

# Web Vitals

**Category:** performance · **Status:** 🟢 Active

## When to use
Khi cần đạt ngưỡng Core Web Vitals (LCP, CLS, INP) cho SEO và trải nghiệm thật của người dùng.

## Steps
1. Đo bằng Lighthouse (lab) và `web-vitals` / RUM (field) — ưu tiên field data.
2. LCP (≤2.5s): tối ưu ảnh hero, preload tài nguyên quan trọng, giảm TTFB, tránh chặn render.
3. CLS (≤0.1): đặt width/height cho ảnh/iframe, chừa chỗ cho ad/embed, tránh chèn nội dung động đẩy layout.
4. INP (≤200ms): chia nhỏ tác vụ dài, tránh JS chặn main thread, debounce, dùng transition cho update nặng.
5. Theo dõi liên tục, đặt ngưỡng cảnh báo, tránh hồi quy khi thêm tính năng.

## Template
```tsx
import { onLCP, onCLS, onINP } from 'web-vitals';
onLCP(console.log); onCLS(console.log); onINP(console.log);
```

## Example
**Good:** ảnh có kích thước cố định (CLS thấp), preload font/hero (LCP tốt).
**Avoid:** font swap gây nhảy layout, handler nặng đồng bộ làm INP cao.

## Checklist
- [ ] Đo cả lab và field
- [ ] LCP: tối ưu ảnh hero + preload
- [ ] CLS: kích thước cố định, chừa chỗ
- [ ] INP: chia nhỏ tác vụ, tránh chặn main thread
