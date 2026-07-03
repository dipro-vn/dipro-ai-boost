---
name: sourcebase-knowledge-hook-discovery
description: 
---

# Hook Discovery

**Category:** sourcebase-knowledge · **Status:** 🟢 Active

## When to use
Trước khi viết custom hook mới, để tìm hook sẵn có (data, form, UI) reuse được.

## Steps
1. Tìm thư mục `hooks/` và file `use*.ts` rải trong feature.
2. Phân loại hook theo nhóm: data-fetching, form, UI/DOM, util state.
3. Đọc signature: input params, return shape, dependency để biết cách dùng.
4. Grep usage để xem hook được gọi ở đâu, có cover case của bạn không.
5. Reuse hoặc generalize hook cũ; chỉ tạo mới nếu logic thực sự khác biệt.

## Template
```bash
# Liệt kê & đọc custom hooks
fd 'use[A-Z].*\.(ts|tsx)$' src
rg "export (function|const) use\w+" src/hooks
rg "useDebounce|useToggle|useDisclosure" src   # tránh viết trùng
```

## Example
**Good:** Phát hiện `useDebouncedValue` có sẵn, reuse cho ô search thay vì tự viết.
**Avoid:** Viết lại `useLocalStorage` mới trong khi đã có hook cùng chức năng.

## Checklist
- [ ] Đã quét `hooks/` và các `use*` trong feature
- [ ] Đã đọc signature (params/return) của hook ứng viên
- [ ] Đã xem usage thực tế để xác nhận phù hợp
- [ ] Chỉ tạo hook mới khi không reuse/generalize được
