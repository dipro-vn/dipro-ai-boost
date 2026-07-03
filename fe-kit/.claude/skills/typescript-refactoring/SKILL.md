---
name: typescript-refactoring
description: 
---

# Refactoring

**Category:** typescript · **Status:** 🟢 Active

## When to use
Khi cải thiện kiểu trong code đã có: thu hẹp `any`, tách type, mà vẫn compile sạch.

## Steps
1. Bật/giữ strict; chạy `tsc --noEmit` làm mốc, sửa cho tới khi 0 lỗi.
2. Thay `any` bằng `unknown` rồi narrow, hoặc kiểu cụ thể đúng nghĩa.
3. Trích type lặp ra alias/interface dùng chung; đặt tên theo domain.
4. Thu hẹp dần từng chỗ, compile lại sau mỗi bước để khoanh vùng lỗi.
5. Không đổi hành vi runtime; chỉ thay đổi kiểu và tên.

## Template
```ts
// trước
function handle(data: any) { return data.items.map((x: any) => x.id); }

// sau
interface Payload { items: { id: string }[]; }
function handle(data: Payload): string[] {
  return data.items.map((x) => x.id);
}
```

## Example
**Good:** `any` -> `Payload` interface, `tsc --noEmit` pass, runtime không đổi.
**Avoid:** Thay `any` bằng `as SomeType` ép kiểu sai sự thật, lỗi dồn xuống runtime.

## Checklist
- [ ] `tsc --noEmit` pass trước & sau refactor
- [ ] `any` được thay bằng kiểu cụ thể hoặc `unknown`+narrow
- [ ] Type lặp tách thành alias/interface chung
- [ ] Hành vi runtime giữ nguyên
