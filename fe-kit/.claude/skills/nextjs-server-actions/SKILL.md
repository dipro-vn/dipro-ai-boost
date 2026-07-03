---
name: nextjs-server-actions
description: 
---

# Server Actions

**Category:** nextjs · **Status:** 🟢 Active

## When to use
Khi mutate data từ form/UI mà không cần tự tạo API route, dùng Server Action.

## Steps
1. Đánh dấu `'use server'` ở đầu file action hoặc trong function.
2. Validate input bằng zod trước khi xử lý; không tin dữ liệu client.
3. Thực hiện mutation (DB/API) phía server.
4. Gọi `revalidatePath`/`revalidateTag` để làm mới cache liên quan.
5. Trả về kết quả/lỗi serializable; dùng `redirect` khi cần điều hướng.

## Template
```ts
'use server';
import { z } from 'zod';
import { revalidatePath } from 'next/cache';

const schema = z.object({ title: z.string().min(1) });

export async function createPost(formData: FormData) {
  const data = schema.parse({ title: formData.get('title') });
  await db.post.create(data);
  revalidatePath('/posts');
}
```

## Example
**Good:** 'use server', validate zod, mutation, revalidatePath sau khi xong.
**Avoid:** Bỏ validate, không revalidate, ném object không serializable.

## Checklist
- [ ] 'use server' đúng chỗ
- [ ] Validate input (zod)
- [ ] revalidatePath/Tag sau mutation
- [ ] Trả về dữ liệu serializable
