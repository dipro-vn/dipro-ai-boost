---
name: performance-bundle-analysis
description: 
---

# Bundle Analysis

**Category:** performance · **Status:** 🟢 Active

## When to use
Khi initial load chậm, bundle phình to, hoặc cần tìm dependency nặng trước khi tối ưu.

## Steps
1. Build production và đo size thực tế (gzip/brotli), không đo dev build.
2. Mở source-map explorer / bundle analyzer để xem thành phần chiếm dung lượng.
3. Tìm dependency nặng (moment, lodash full, icon set) → thay bằng bản nhẹ hoặc import lẻ.
4. Code-split theo route/feature, tách vendor; lazy phần ít dùng.
5. Loại import thừa, tree-shake (ESM, `sideEffects: false`).
6. Đặt budget size và theo dõi trong CI.

## Template
```bash
# Next.js
ANALYZE=true next build
# Vite
npx vite-bundle-visualizer
# webpack
npx source-map-explorer dist/*.js
```

## Example
**Good:** import `lodash/debounce`, thay moment bằng date-fns, lazy chart lib.
**Avoid:** `import _ from 'lodash'`, import cả icon library cho 2 icon.

## Checklist
- [ ] Đo trên production build
- [ ] Xác định top dependency nặng
- [ ] Import lẻ / thay thư viện nhẹ
- [ ] Code-split + budget trong CI
