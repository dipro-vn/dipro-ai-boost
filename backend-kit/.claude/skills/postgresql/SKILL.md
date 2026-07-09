---
name: postgresql
description: PostgreSQL and TypeORM guidance for schema design, migrations, indexing, QueryBuilder usage, N+1 prevention, and transactions.
metadata:
  stack: postgresql, typeorm
---

# PostgreSQL And TypeORM

Use this skill when creating or reviewing entities, migrations, repositories, QueryBuilder logic, indexes, and transactions.

## Schema Conventions

| Area | Rule |
| --- | --- |
| Primary key | UUID |
| Column names | Explicit `snake_case` names |
| Timestamps | `timestamptz` |
| Soft delete | Nullable `deleted_at` |
| Relations | Explicit join columns |
| Migrations | One logical schema change per migration |

## Entity Pattern

```typescript
@Entity('orders')
export class OrderEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'company_id', type: 'uuid' })
  companyId: string;

  @Column({ name: 'status', length: 30 })
  status: string;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @Column({ name: 'deleted_at', type: 'timestamptz', nullable: true })
  deletedAt: Date | null;
}
```

## Migration Rules

- Every migration must implement both `up()` and `down()`.
- Rollback must reverse the schema change.
- Add indexes for common filter, join, and sort paths.
- Do not include production data dumps in migrations.
- Keep `synchronize` disabled for normal project work.

## QueryBuilder Rules

- Whitelist dynamic sort fields before calling `orderBy`.
- Use joins or batched lookups to avoid N+1 queries.
- Use `skip` and `take` for paginated list endpoints.
- Filter soft-deleted rows consistently.

```typescript
const ORDER_BY: Record<string, string> = {
  createdAt: 'order.createdAt',
  status: 'order.status',
};

const orderBy = ORDER_BY[dto.orderBy ?? 'createdAt'] ?? ORDER_BY.createdAt;

return this.orderRepository
  .createQueryBuilder('order')
  .where('order.companyId = :companyId', { companyId })
  .andWhere('order.deletedAt IS NULL')
  .orderBy(orderBy, dto.direction ?? 'DESC')
  .skip((dto.page - 1) * dto.limit)
  .take(dto.limit)
  .getManyAndCount();
```

## Transactions

Use a transaction when one business action writes multiple tables or depends on read-modify-write consistency.

```typescript
await this.dataSource.transaction(async (manager) => {
  const order = await manager.save(OrderEntity, orderData);
  await manager.save(OrderItemEntity, items.map((item) => ({
    ...item,
    orderId: order.id,
  })));
});
```

## Checklist

- [ ] Entity uses explicit database names.
- [ ] Timestamp fields use `timestamptz`.
- [ ] Soft delete uses `deleted_at`.
- [ ] Migration has `up()` and `down()`.
- [ ] Sort fields are whitelisted.
- [ ] List queries are paginated.
- [ ] Relations do not cause N+1 queries.
- [ ] Multi-table writes use a transaction.
