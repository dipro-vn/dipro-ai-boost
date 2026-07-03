---
name: sourcebase-knowledge-component-discovery
description: 
---

# Component Discovery

**Category:** sourcebase-knowledge · **Status:** 🟢 Active

## When to use
Trước khi tạo component mới, để tìm component sẵn có có thể reuse.

## Steps
1. Search theo từ khóa chức năng (Button, Modal, Table) trong `components/`, `ui/`.
2. Tìm theo props/role tương tự nếu tên khác (vd: `Dialog` thay vì `Modal`).
3. Mở component ứng viên, đọc Props interface và variants có sẵn.
4. Xem usage thực tế bằng cách grep nơi import để hiểu cách dùng đúng.
5. Quyết định: reuse trực tiếp, mở rộng props, hay tạo mới nếu thật sự khác.

## Template
```bash
# Tìm component theo tên & cách dùng
rg -t tsx -l "export (function|const) \w*Button" src
rg "import .*Modal.* from" src             # nơi dùng Modal
rg "interface \w+Props" src/components -A8 # đọc props có sẵn
```

## Example
**Good:** Tìm thấy `<Dialog>` có sẵn variant `confirm`, reuse thay vì viết Modal mới.
**Avoid:** Tạo `MyButton` mới trong khi `ui/Button` đã hỗ trợ đủ variant cần dùng.

## Checklist
- [ ] Đã search theo tên và theo chức năng tương đương
- [ ] Đã đọc Props/variants của ứng viên reuse
- [ ] Đã xem ít nhất 1 usage thực tế
- [ ] Chỉ tạo mới khi không component nào đáp ứng
