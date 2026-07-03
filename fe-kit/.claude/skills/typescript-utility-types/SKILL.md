---
name: typescript-utility-types
description: 
---

# Utility Types

**Category:** typescript · **Status:** 🟢 Active

## When to use
Khi cần biến đổi type sẵn có thay vì khai báo lại từ đầu.

## Steps
1. `Pick`/`Omit` để lấy/loại field từ type gốc, giữ liên kết khi gốc đổi.
2. `Partial`/`Required` cho update payload hoặc bắt buộc toàn bộ field.
3. `Record<K, V>` cho map/dictionary có key cố định.
4. `ReturnType`/`Parameters` để suy kiểu từ hàm có sẵn, tránh khai báo trùng.
5. Compose nhiều utility nhưng giữ dễ đọc; đặt alias nếu type lồng sâu.

## Template
```ts
interface User { id: string; name: string; email: string; role: Role; }

type UserPreview = Pick<User, "id" | "name">;
type UserUpdate = Partial<Omit<User, "id">>;
type UsersByRole = Record<Role, User[]>;
type ApiUser = ReturnType<typeof fetchUser>;
```

## Example
**Good:** `Partial<Omit<User, "id">>` cho payload update; `Record<Role, User[]>` cho nhóm.
**Avoid:** Khai báo lại `UserUpdate` thủ công, lệch khi `User` thay đổi field.

## Checklist
- [ ] Biến đổi từ type gốc thay vì khai báo trùng
- [ ] Chọn đúng utility (Pick/Omit/Partial/Record/ReturnType)
- [ ] Type phái sinh tự cập nhật khi gốc đổi
- [ ] Type lồng sâu có alias dễ đọc
