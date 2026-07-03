---
name: typescript-api-typing
description: 
---

# API Typing

**Category:** typescript · **Status:** 🟢 Active

## When to use
Khi type request/response của API và muốn an toàn kiểu từ network đến UI.

## Steps
1. Định nghĩa schema bằng zod cho dữ liệu từ ngoài (response, form, env).
2. Suy type từ schema bằng `z.infer`, không khai báo interface trùng tay.
3. `parse`/`safeParse` response tại ranh giới I/O để validate runtime, không tin `as`.
4. Type request payload riêng; tách DTO server với model dùng trong UI nếu khác.
5. Không dùng `any` cho response; dùng generic cho client `request<T>()`.

## Template
```ts
import { z } from "zod";

const userSchema = z.object({ id: z.string(), name: z.string(), email: z.string().email() });
type User = z.infer<typeof userSchema>;

async function getUser(id: string): Promise<User> {
  const res = await api.get(`/users/${id}`);
  return userSchema.parse(res.data); // validate runtime + type
}
```

## Example
**Good:** `z.infer` cho type, `schema.parse` validate response trước khi trả về.
**Avoid:** `return res.data as User` bỏ qua validate; response để `any` rồi truy cập field bừa.

## Checklist
- [ ] Schema zod cho dữ liệu từ ngoài
- [ ] Type suy từ `z.infer`, không khai báo trùng
- [ ] Validate runtime tại ranh giới I/O, không `as`
- [ ] Response không dùng `any`
