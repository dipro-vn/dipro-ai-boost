---
name: form-form-state
description: 
---

# Form State

**Category:** form · **Status:** 🟢 Active

## When to use
Khi quản lý trạng thái form: dirty/touched/isSubmitting, default values, reset.

## Steps
1. Luôn cung cấp `defaultValues` đầy đủ để field controlled từ đầu.
2. Dùng `formState.isDirty` để bật/tắt nút Save, cảnh báo rời trang khi dirty.
3. Disable submit khi `isSubmitting` để tránh double submit.
4. Sau khi load data async, `reset(data)` để set lại default + clear dirty.
5. Dùng `isValid`/`touchedFields` để hiện lỗi đúng lúc (sau khi chạm).

## Template
```tsx
const { reset, formState: { isDirty, isSubmitting } } = useForm({ defaultValues });
useEffect(() => { if (data) reset(data); }, [data, reset]);
<button type="submit" disabled={!isDirty || isSubmitting}>
  {isSubmitting ? 'Đang lưu...' : 'Lưu'}
</button>
```

## Example
**Good:** reset(data) sau fetch, disable theo isDirty/isSubmitting.
**Avoid:** defaultValues thiếu (uncontrolled→controlled warning), không reset sau load.

## Checklist
- [ ] defaultValues đầy đủ
- [ ] isDirty điều khiển Save/cảnh báo rời trang
- [ ] isSubmitting chặn double submit
- [ ] reset sau khi load data async
