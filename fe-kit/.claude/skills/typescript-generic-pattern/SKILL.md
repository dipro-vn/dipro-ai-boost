---
name: typescript-generic-pattern
description: 
---

# Generic Pattern

**Category:** typescript · **Status:** 🟢 Active

## When to use
Khi viết hàm/type tái dùng cho nhiều kiểu mà vẫn giữ liên kết kiểu input-output.

## Steps
1. Chỉ dùng generic khi cần liên kết kiểu giữa input và output; nếu không, dùng kiểu cụ thể.
2. Ràng buộc type param bằng `extends` để giới hạn miền giá trị hợp lệ.
3. Dùng `infer` trong conditional type để rút kiểu lồng bên trong.
4. Đặt tên param có nghĩa (`TItem`, `TKey`) thay vì chỉ `T` khi có nhiều param.
5. Tránh over-generic: nhiều param không dùng đến làm type khó đọc, dễ sai.

## Template
```ts
function getProp<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

type ElementType<A> = A extends (infer E)[] ? E : never;
type Item = ElementType<User[]>; // User
```

## Example
**Good:** `K extends keyof T` đảm bảo key hợp lệ; return type `T[K]` suy ra chính xác.
**Avoid:** `function getProp<T, K, V>(...)` với param thừa; generic không ràng buộc nhận mọi key.

## Checklist
- [ ] Generic thực sự liên kết input-output
- [ ] Type param có constraint `extends` khi cần
- [ ] Dùng `infer` đúng chỗ cho conditional type
- [ ] Không over-generic, param đều có mục đích
