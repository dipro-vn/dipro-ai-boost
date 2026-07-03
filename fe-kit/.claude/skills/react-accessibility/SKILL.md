---
name: react-accessibility
description: 
---

# Accessibility

**Category:** react · **Status:** 🟢 Active

## When to use
Khi render UI tương tác trong React để đảm bảo dùng được bằng bàn phím & screen reader.

## Steps
1. Dùng element semantic (`button`, `nav`, `label`) thay cho `div` click giả.
2. Bổ sung `aria-*` chỉ khi semantic không đủ (vd `aria-expanded`, `aria-label`).
3. Liên kết label-input qua `htmlFor`/`id`; nhóm bằng `fieldset`/`legend`.
4. Quản lý focus: trap trong modal, trả focus về trigger khi đóng.
5. Hỗ trợ bàn phím: Enter/Space kích hoạt, Esc đóng, Tab di chuyển hợp lý.

## Template
```tsx
<button
  type="button"
  aria-expanded={open}
  aria-controls="menu"
  onClick={() => setOpen((o) => !o)}
>
  Menu
</button>
<ul id="menu" hidden={!open} role="menu">{/* items */}</ul>
```

## Example
**Good:** `<button>` thật, `aria-expanded` đồng bộ state, Esc đóng, focus trả về trigger.
**Avoid:** `<div onClick>` không focusable, thiếu label cho input, modal không trap focus.

## Checklist
- [ ] Dùng element semantic đúng vai trò
- [ ] Input có label liên kết (`htmlFor`/`id`)
- [ ] Thao tác được bằng bàn phím (Tab/Enter/Esc)
- [ ] Focus quản lý đúng khi mở/đóng overlay
