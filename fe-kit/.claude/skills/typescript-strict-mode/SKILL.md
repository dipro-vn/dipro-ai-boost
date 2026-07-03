---
name: typescript-strict-mode
description: 
---

# Strict Mode

**Category:** typescript · **Status:** 🟢 Active

## When to use
Khi cấu hình project hoặc viết code TypeScript cần an toàn kiểu tối đa.

## Steps
1. Bật `"strict": true` trong `tsconfig.json` (gồm `strictNullChecks`, `noImplicitAny`...).
2. Xử lý `null`/`undefined` tường minh: optional chaining, nullish coalescing, guard.
3. Không tắt check bằng `// @ts-ignore` hay `as any`; sửa gốc kiểu thay vì che.
4. Dùng `unknown` thay `any` cho input chưa rõ, rồi narrow trước khi dùng.
5. Bật thêm `noUncheckedIndexedAccess` khi truy cập mảng/object động.

## Template
```jsonc
// tsconfig.json
{ "compilerOptions": { "strict": true, "noUncheckedIndexedAccess": true } }
```
```ts
function getName(u: User | null): string {
  return u?.name ?? "Khách";   // xử lý null tường minh
}
```

## Example
**Good:** `u?.name ?? "Khách"`, narrow `unknown` bằng `typeof` trước khi dùng.
**Avoid:** `(u as any).name`, `// @ts-ignore` để bỏ qua lỗi null thay vì sửa.

## Checklist
- [ ] `strict: true` được bật, không nới lỏng
- [ ] Null/undefined xử lý tường minh
- [ ] Không dùng `any`/`@ts-ignore` để che lỗi
- [ ] Input chưa rõ dùng `unknown` + narrow
