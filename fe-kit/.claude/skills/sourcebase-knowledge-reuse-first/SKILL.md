---
name: sourcebase-knowledge-reuse-first
description: 
---

# Reuse First

**Category:** sourcebase-knowledge · **Status:** 🟢 Active

## When to use
Mọi lúc trước khi viết code mới: ưu tiên tìm và tái dùng thứ đã có.

## Steps
1. Search codebase cho component/hook/service/util giải quyết cùng vấn đề.
2. Nếu có thứ gần đúng: ưu tiên mở rộng (thêm prop/param) thay vì clone.
3. Nếu lặp logic ở nhiều nơi: trích xuất thành abstraction dùng chung.
4. Chỉ tạo mới khi không reuse hay generalize hợp lý được.
5. Đặt code mới đúng tầng (shared vs feature) theo phạm vi sử dụng.

## Template
```bash
# Quy trình reuse-first
rg -i "<keyword>" src              # 1. tìm thứ tương tự
# 2. có gần đúng? -> mở rộng props/params
# 3. lặp >2 nơi?  -> trích xuất shared util/hook
# 4. không có?    -> tạo mới đúng tầng
```

## Example
**Good:** Thêm prop `variant` vào `Button` có sẵn để cover case mới, không tạo `Button2`.
**Avoid:** Copy-paste component cũ rồi sửa nhẹ, sinh ra 2 bản phải maintain song song.

## Checklist
- [ ] Đã search trước khi viết bất kỳ code mới nào
- [ ] Ưu tiên mở rộng/generalize hơn là clone
- [ ] Trích xuất shared khi logic lặp ở nhiều nơi
- [ ] Code mới đặt đúng tầng theo phạm vi dùng
