---
name: security-input-validation
description: 
---

# Input Validation

**Category:** security · **Status:** 🟢 Active

## When to use
Khi nhận dữ liệu từ form, query param, hoặc API — bất kỳ input nào không kiểm soát.

## Steps
1. Validate ở client để UX tốt, NHƯNG server luôn phải validate lại — không tin client.
2. Định nghĩa schema bằng zod; dùng chung type giữa form và API.
3. Kiểm tra kiểu, độ dài, range, định dạng (email, số); từ chối field thừa.
4. Chuẩn hoá/sanitize trước khi dùng; trả lỗi rõ ràng theo từng field.
5. Parse dữ liệu API response bằng schema để bắt thay đổi backend sớm.

## Template
```ts
const Schema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(120),
});
const result = Schema.safeParse(input);
if (!result.success) return result.error.flatten();
```

## Example
**Good:** zod safeParse cho form + response, server validate lại.
**Avoid:** chỉ validate ở FE, tin tưởng dữ liệu API là đúng cấu trúc.

## Checklist
- [ ] Schema zod dùng chung type
- [ ] Server validate lại (không tin client)
- [ ] Kiểm tra kiểu/độ dài/range/format
- [ ] Parse cả API response
