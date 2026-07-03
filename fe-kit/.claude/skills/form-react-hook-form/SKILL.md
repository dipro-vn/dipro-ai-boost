---
name: form-react-hook-form
description: 
---

# React Hook Form

**Category:** form · **Status:** 🟢 Active

## When to use
Khi build form với React Hook Form (useForm) cần ít re-render, dễ validate.

## Steps
1. Khởi tạo `useForm` với type generic và `defaultValues`.
2. Dùng `register` cho input chuẩn; `Controller` cho component UI controlled (MUI/select).
3. Submit qua `handleSubmit(onValid, onInvalid)`.
4. Hạn chế re-render: tránh watch toàn form, dùng `useWatch` cục bộ khi cần.
5. Lấy lỗi từ `formState.errors`, hiển thị cạnh field.

## Template
```tsx
const { register, handleSubmit, control, formState: { errors } } = useForm<FormValues>({
  defaultValues: { email: '' },
});
return (
  <form onSubmit={handleSubmit(onSubmit)}>
    <input {...register('email')} aria-invalid={!!errors.email} />
    <Controller name="role" control={control} render={({ field }) => <Select {...field} />} />
  </form>
);
```

## Example
**Good:** register cho input, Controller cho UI lib, defaultValues đầy đủ.
**Avoid:** watch toàn form mỗi keystroke, controlled state thủ công song song RHF.

## Checklist
- [ ] useForm có type + defaultValues
- [ ] register/Controller đúng loại field
- [ ] handleSubmit xử lý valid/invalid
- [ ] Tránh re-render thừa (useWatch cục bộ)
