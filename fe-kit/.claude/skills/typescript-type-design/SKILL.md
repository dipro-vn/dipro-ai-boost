---
name: typescript-type-design
description: 
---

# Type Design

**Category:** typescript · **Status:** 🟢 Active

## When to use
Khi thiết kế kiểu cho domain model, props, hoặc dữ liệu có nhiều trạng thái.

## Steps
1. Dùng `interface` cho object/contract có thể mở rộng; `type` cho union/intersection/alias.
2. Mô hình hóa trạng thái loại trừ nhau bằng discriminated union (field `kind`/`status`).
3. Ưu tiên union literal thay vì `string` rộng cho tập giá trị cố định.
4. Làm field bất biến với `readonly`; tránh optional thừa gây "có thể undefined" lan tỏa.
5. "Make illegal states unrepresentable": thiết kế type sao cho không tạo được state sai.

## Template
```ts
type RequestState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: string };

function render(s: RequestState<User>) {
  if (s.status === "success") return s.data.name; // narrow an toàn
}
```

## Example
**Good:** Discriminated union theo `status`, `data` chỉ tồn tại khi `success`.
**Avoid:** `{ loading: boolean; data?: T; error?: string }` cho phép tổ hợp state vô lý.

## Checklist
- [ ] `interface` vs `type` chọn đúng mục đích
- [ ] Trạng thái loại trừ dùng discriminated union
- [ ] Tập giá trị cố định dùng union literal
- [ ] Không tạo được state bất hợp lệ
