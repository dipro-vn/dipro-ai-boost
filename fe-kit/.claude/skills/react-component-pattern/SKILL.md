---
name: react-component-pattern
description: 
---

# Component Pattern

**Category:** react · **Status:** 🟢 Active

## When to use
Khi tạo mới hoặc refactor một React function component.

## Steps
1. Xác định component là presentational hay container; tách logic phức tạp ra custom hook.
2. Định nghĩa Props interface rõ ràng, ưu tiên required, không dùng `any`.
3. Destructure props ở signature, đặt default value tại đây.
4. Giữ render thuần: side-effect đưa vào `useEffect`/handler.
5. Early-return cho loading/error/empty trước khi render chính.
6. Named export, 1 component/file.

## Template
```tsx
interface UserCardProps {
  user: User;
  onSelect?: (id: string) => void;
}

export function UserCard({ user, onSelect }: UserCardProps) {
  if (!user) return null;
  return <button type="button" onClick={() => onSelect?.(user.id)}>{user.name}</button>;
}
```

## Example
**Good:** Props có type, handler optional gọi qua `?.`, early-return khi thiếu data.
**Avoid:** `export default function(props: any)`, fetch trong render.

## Checklist
- [ ] Props có interface, không `any`
- [ ] Không side-effect trong thân render
- [ ] Xử lý loading/error/empty
- [ ] Named export, 1 component/file
