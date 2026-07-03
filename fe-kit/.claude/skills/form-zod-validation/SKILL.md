---
name: form-zod-validation
description: 
---

# Zod Validation

**Category:** form · **Status:** 🟢 Active

## When to use
Khi validate form bằng zod schema kết hợp React Hook Form qua zodResolver.

## Steps
1. Định nghĩa schema zod với message rõ ràng cho từng rule.
2. Infer type từ schema bằng `z.infer` để dùng làm FormValues.
3. Gắn `zodResolver(schema)` vào useForm.
4. Dùng `.refine`/`.superRefine` cho rule liên field (vd confirm password).
5. Tái dùng schema cho cả client form và server action.

## Template
```ts
const schema = z.object({
  email: z.string().email('Email không hợp lệ'),
  password: z.string().min(8, 'Tối thiểu 8 ký tự'),
  confirm: z.string(),
}).refine((d) => d.password === d.confirm, {
  message: 'Mật khẩu không khớp', path: ['confirm'],
});
type FormValues = z.infer<typeof schema>;
useForm<FormValues>({ resolver: zodResolver(schema) });
```

## Example
**Good:** infer type từ schema, refine cho cross-field, message tiếng Việt.
**Avoid:** Khai báo type tách rời schema (lệch nhau), validate thủ công lặp lại.

## Checklist
- [ ] Schema có message rõ ràng
- [ ] Type infer từ schema (single source)
- [ ] zodResolver gắn vào useForm
- [ ] refine cho rule liên field
