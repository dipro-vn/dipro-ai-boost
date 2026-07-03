---
name: prisma-transaction
description: 
---

# Prisma Transaction

**Category:** prisma · **Status:** 🟢 Active

## When to use
Khi nhiều thao tác ghi phải atomic: `$transaction`, interactive transaction.

## Steps
1. Nhóm các write phụ thuộc nhau vào 1 `$transaction` để all-or-nothing.
2. Thao tác độc lập không cần đọc giữa chừng: dùng array `$transaction([...])`.
3. Cần logic/đọc rồi quyết định ghi: dùng interactive `$transaction(async (tx) => {...})`.
4. Bên trong tx dùng `tx.*`, không dùng `prisma.*` (sẽ ngoài transaction).
5. Giữ transaction ngắn; tránh gọi API/chờ ngoài DB bên trong tx (giữ lock lâu).

## Template
```ts
await prisma.$transaction(async (tx) => {
  const acc = await tx.account.findUniqueOrThrow({ where: { id } });
  if (acc.balance < amount) throw new Error('Số dư không đủ');
  await tx.account.update({ where: { id }, data: { balance: { decrement: amount } } });
  await tx.ledger.create({ data: { accountId: id, amount } });
});
```

## Example
**Good:** đọc-kiểm tra-ghi trong interactive tx, dùng tx.*, transaction ngắn gọn.
**Avoid:** dùng prisma.* trong tx, gọi HTTP bên trong tx, ghi phụ thuộc nhau mà không bọc tx.

## Checklist
- [ ] Write phụ thuộc nhau được bọc $transaction
- [ ] Dùng tx.* xuyên suốt transaction
- [ ] Không I/O ngoài DB bên trong tx
- [ ] Transaction ngắn, rollback rõ khi lỗi
