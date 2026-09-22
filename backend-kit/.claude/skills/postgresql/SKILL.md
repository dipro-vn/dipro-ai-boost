---
name: postgresql
description: Use when creating or changing an entity, writing a migration, or building a QueryBuilder query. Symptoms — a new table or column, a migration with no down step, dynamic orderBy, a list query without skip and take, a loop that queries per row, a write touching two tables.
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

## Migrations On Large Or Live Tables

A migration that locks a busy table blocks every request that touches it. Plan for the table's real size, not the local copy.

| Change | Safe way |
| --- | --- |
| Add an index | `CREATE INDEX CONCURRENTLY`, in its own migration with `transaction = false` |
| Add a NOT NULL column | Add it nullable (or with a constant `DEFAULT`, metadata-only on PostgreSQL 11+), backfill in batches, then `SET NOT NULL` in a later migration |
| Rename or drop a column | Expand and contract: add the new column, write to both, backfill, switch reads, drop the old one in a later release. A rename is a breaking change for running code |
| Change a column type | Add a new column and backfill; `ALTER COLUMN TYPE` rewrites the whole table under lock |
| Add a foreign key | `ADD CONSTRAINT ... NOT VALID`, then `VALIDATE CONSTRAINT` in a separate step |
| Backfill data | Batches of a few thousand rows, in a separate migration or script, never one `UPDATE` over millions of rows |

```typescript
export class AddOrdersCompanyStatusIndex1735000000000 implements MigrationInterface {
  // CONCURRENTLY cannot run inside a transaction.
  transaction = false as const;

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE INDEX CONCURRENTLY IF NOT EXISTS "idx_orders_company_status" ON "orders" ("company_id", "status")`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX CONCURRENTLY IF EXISTS "idx_orders_company_status"`);
  }
}
```

`transaction = false` requires `migrationsTransactionMode: 'each'` in the DataSource (or `--transaction each` on the CLI). With the default `'all'`, TypeORM refuses to run the migration. Check the project's setting before relying on it.

## Concurrency

Two requests that read, change, and write the same row will lose one update unless the write is guarded.

| Situation | Guard |
| --- | --- |
| A user edits a record another user may edit | Optimistic lock: `@VersionColumn()`, update `WHERE id AND version`, 0 affected rows → `409 Conflict` |
| A read-modify-write that must not interleave (balance, stock, sequence) | Pessimistic lock inside a transaction: `lock: { mode: 'pessimistic_write' }` |
| A counter or quantity change | One atomic statement: `SET qty = qty - :n WHERE id = :id AND qty >= :n`, then check affected rows |
| A value that must be unique | A unique constraint in the database; map error `23505` to `409` (the `backend-error-logging` skill) |
| A POST that must not run twice (payment, order) | An `Idempotency-Key` header stored under a unique constraint on `(company_id, key)`; a repeat returns the first result |

```typescript
// Optimistic lock: the version the client read must still be current.
const result = await this.orderRepository
  .createQueryBuilder()
  .update(OrderEntity)
  .set({ status: dto.status })
  .where('id = :id AND company_id = :companyId AND version = :version', {
    id, companyId, version: dto.version,
  })
  .execute();

if (result.affected === 0) {
  throw new ConflictException('Order was changed by someone else — reload and retry');
}
```

```typescript
// Pessimistic lock: the row stays locked until the transaction ends.
await this.dataSource.transaction(async (manager) => {
  const stock = await manager.findOne(StockEntity, {
    where: { id: stockId, companyId },
    lock: { mode: 'pessimistic_write' },
  });
  if (!stock || stock.quantity < quantity) {
    throw new UnprocessableEntityException('Insufficient stock');
  }
  stock.quantity -= quantity;
  await manager.save(stock);
});
```

A check-then-insert in application code (`if (!exists) insert`) is not a uniqueness guarantee. Only the constraint is.

## QueryBuilder Rules

- Whitelist dynamic sort fields before calling `orderBy`.
- Use joins or batched lookups to avoid N+1 queries.
- Use `skip` and `take` for paginated list endpoints, with a maximum `limit` enforced in the DTO.
- For deep pages on large tables, prefer keyset pagination (`WHERE created_at < :cursor`) over large offsets.
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
// Side effects — cache invalidation, events, emails — go here, after commit.
```

Never call an external service or invalidate cache inside the transaction callback. If the transaction rolls back, the side effect has already happened; if it commits late, a concurrent reader may re-cache the old data.

## Checklist

- [ ] Entity uses explicit database names.
- [ ] Timestamp fields use `timestamptz`.
- [ ] Soft delete uses `deleted_at`.
- [ ] Migration has `up()` and `down()`.
- [ ] Sort fields are whitelisted.
- [ ] List queries are paginated.
- [ ] Relations do not cause N+1 queries.
- [ ] Multi-table writes use a transaction.
- [ ] Migrations on large tables avoid long locks (concurrent index, nullable-then-backfill, expand and contract).
- [ ] Concurrent writes to the same row are guarded (version, lock, atomic update, or constraint).
- [ ] Side effects run after the transaction commits.
