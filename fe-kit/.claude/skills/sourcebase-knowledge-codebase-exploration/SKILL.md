---
name: sourcebase-knowledge-codebase-exploration
description: 
---

# Codebase Exploration

**Category:** sourcebase-knowledge · **Status:** 🟢 Active

## When to use
Khi bắt đầu làm việc với codebase lạ, trước khi thêm hoặc sửa code.

## Steps
1. Đọc `package.json`/`README` để xác định framework, scripts, dependency chính.
2. Map cấu trúc thư mục: tìm entry (`main`, `index`, `App`), routing, layout.
3. Nhận diện convention: cách đặt tên file, alias import, barrel `index.ts`.
4. Tìm tầng shared: `components/`, `hooks/`, `services/`, `utils/`, `types/`.
5. Đọc 1-2 feature tiêu biểu để hiểu data flow end-to-end.
6. Ghi lại pattern phát hiện được trước khi viết code mới.

## Template
```bash
# Khảo sát nhanh
cat package.json | jq '.scripts, .dependencies'
fd -e ts -e tsx . src | head -50          # cấu trúc file
rg -l "createBrowserRouter|<Routes>" src   # tìm routing
rg "export \* from" src/**/index.ts        # barrel exports
```

## Example
**Good:** Đọc config + 1 feature, nắm convention rồi mới sửa, theo đúng alias `@/`.
**Avoid:** Sửa ngay file đầu tiên thấy, đặt tên/đường dẫn lệch convention sẵn có.

## Checklist
- [ ] Đã xác định framework, scripts, dependency chính
- [ ] Đã map entry, routing, tầng shared
- [ ] Đã nắm convention đặt tên & import alias
- [ ] Đã đọc ít nhất 1 feature mẫu trước khi sửa
