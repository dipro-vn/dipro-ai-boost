---
name: mui-component-usage
description: 
---

# Component Usage

**Category:** mui · **Status:** 🟢 Active

## When to use
Khi cần dựng UI bằng component MUI (Button, TextField, Dialog...) thay vì tự chế lại từ thẻ HTML thô.

## Steps
1. Ưu tiên component MUI có sẵn; không tự dựng lại bằng `<div>`/`<button>` thuần.
2. Dùng đúng prop chuẩn của component (`variant`, `color`, `size`, `disabled`) thay vì override bằng CSS.
3. Với form, dùng `TextField` controlled (`value` + `onChange`) hoặc tích hợp form lib.
4. Dùng đúng component họ hàng (`Dialog` + `DialogTitle`/`DialogContent`/`DialogActions`), không nhồi vào 1 thẻ.
5. Tra docs prop trước khi viết logic thủ công cho hành vi MUI đã hỗ trợ.

## Template
```tsx
<Button variant="contained" color="primary" size="medium" onClick={onSave}>
  Save
</Button>

<TextField label="Email" value={email} onChange={(e) => setEmail(e.target.value)}
  error={!!error} helperText={error} fullWidth />

<Dialog open={open} onClose={onClose}>
  <DialogTitle>Confirm</DialogTitle>
  <DialogContent>{message}</DialogContent>
  <DialogActions>
    <Button onClick={onClose}>Cancel</Button>
    <Button onClick={onConfirm}>OK</Button>
  </DialogActions>
</Dialog>
```

## Example
**Good:** dùng `Button`/`TextField`/`Dialog` với prop chuẩn, controlled input, đúng cấu trúc con.
**Avoid:** tự dựng button bằng `<div onClick>`, override style thay vì dùng prop, nhồi nội dung Dialog không đúng slot.

## Checklist
- [ ] Dùng component MUI thay vì HTML thô
- [ ] Dùng prop chuẩn (`variant`/`color`/`size`) thay vì CSS override
- [ ] Input controlled, đúng cấu trúc component con
