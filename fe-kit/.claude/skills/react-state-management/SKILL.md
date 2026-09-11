---
name: react-state-management
description: Quyết định đặt state ở đâu và chọn cơ chế nào — local useState, lift state up, Context cho state ít đổi, thư viện global store, phân biệt server state với client state. Dùng khi state bị prop drilling hoặc phải chia sẻ giữa nhiều component.
---

# State Management

**Category:** react · **Status:** 🟢 Active

## When to use

Khi quyết định đặt state cục bộ (local) hay toàn cục (global) ở đâu và chọn cơ chế quản lý phù hợp cho từng loại.

## Steps

1. Mặc định dùng local `useState`; chỉ lift lên khi nhiều con cùng cần.
2. Dùng Context cho state ít đổi, mang tính global (theme, auth, locale).
3. Dùng store (Zustand/Redux) khi state phức tạp, chia sẻ rộng, cần devtools.
4. Server state (API data) tách riêng cho react-query, không nhồi vào store UI.
5. Derive value từ state nguồn thay vì lưu state thừa gây lệch đồng bộ.

## Template

```tsx
// derive thay vì lưu state trùng
const [items, setItems] = useState<Item[]>([]);
const completed = items.filter((i) => i.done); // derived, không cần state riêng
const total = items.length; // derived
```

## Example

**Good:** `completedCount` tính từ `items`; auth để Context; danh sách API qua react-query.
**Avoid:** Lưu `completedCount` thành state riêng rồi sync tay; nhồi server data vào Redux.

## Checklist

- [ ] State đặt ở mức thấp nhất có thể (local trước)
- [ ] Context chỉ cho global ít thay đổi
- [ ] Server state tách cho react-query
- [ ] Derive value thay vì lưu state trùng lặp
