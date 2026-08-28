---
name: postgresql
description: PostgreSQL + TypeORM best practices cho repo backend. Schema design, migration, indexing, query optimization, N+1 prevention, transactions, Redis cache phối hợp. Dùng khi tạo/sửa schema, viết migration, tối ưu query, hoặc thiết kế caching layer.
metadata:
  tags: postgresql, typeorm, database, migration, indexing
---

# PostgreSQL

> Áp dụng cho: repo có vai trò `backend` trong bảng Ecosystem (`AGENTS.md`) — TypeORM 0.3.x + PostgreSQL

## Khi nào dùng skill này

- Thiết kế schema PostgreSQL mới
- Viết TypeORM migration
- Tối ưu query (N+1, index, QueryBuilder)
- Thiết kế Redis cache layer phối hợp với DB
- Review TypeORM entity hoặc repository code

## Quy ước cơ bản

| Yếu tố | Convention | Ví dụ |
|---|---|---|
| Column | `snake_case` | `company_code`, `created_at` |
| Primary Key | UUID | `gen_random_uuid()` |
| Timestamp | `timestamptz` (timezone-aware) | `created_at timestamptz` |
| Soft delete | `deleted_at timestamptz NULL` | không dùng `is_deleted boolean` |
| Migration | `src/migrations/` | `1700000000000-AddOrderStatus.ts` |

## TypeORM Entity Patterns

```typescript
// ✅ Đúng: Entity với explicit names
@Entity('orders')
export class OrderEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'company_code', length: 50 })
  companyCode: string;

  @Column({ name: 'order_status', length: 30, default: 'pending' })
  orderStatus: string;

  @Column({ name: 'deleted_at', type: 'timestamptz', nullable: true })
  deletedAt: Date | null;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;
}

// ✅ Relation với eager: false (tránh N+1)
@ManyToOne(() => CompanyEntity, { eager: false })
@JoinColumn({ name: 'company_id' })
company: CompanyEntity;
```

## Migration Rules

```typescript
// ✅ Đúng: Migration có cả up() và down()
export class AddOrderStatusColumn1700000000000 implements MigrationInterface {
  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "orders" ADD "order_status" varchar(30) NOT NULL DEFAULT 'pending'`
    );
    await queryRunner.query(
      `CREATE INDEX "idx_orders_company_status" ON "orders" ("company_code", "order_status")`
    );
  }

  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX "idx_orders_company_status"`);
    await queryRunner.query(`ALTER TABLE "orders" DROP COLUMN "order_status"`);
  }
}
```

**Rules:**
- `synchronize: false` trong production — LUÔN
- Mỗi migration 1 file, không gộp nhiều thay đổi
- Rollback phải work (`down()` thực sự reverses `up()`)

## N+1 Prevention

```typescript
// ❌ Sai: N+1
for (const order of orders) {
  order.items = await itemRepo.findBy({ orderId: order.id }); // N queries
}

// ✅ Đúng: JOIN trong 1 query
const orders = await orderRepo
  .createQueryBuilder('order')
  .leftJoinAndSelect('order.items', 'item')
  .where('order.companyCode = :code AND order.deletedAt IS NULL', { code })
  .orderBy('order.createdAt', 'DESC')
  .skip((page - 1) * limit)
  .take(limit)
  .getManyAndCount();
```

## orderBy Whitelist (BUG ĐÃ XẢY RA)

```typescript
// ❌ BUG: TypeError databaseName nếu orderBy không hợp lệ
.orderBy(dto.orderBy, 'DESC')

// ✅ FIX: Whitelist trước khi truyền vào
const ORDER_BY_MAP: Record<string, string> = {
  createdAt: 'order.createdAt',
  companyCode: 'order.companyCode',
  status: 'order.orderStatus',
};
.orderBy(ORDER_BY_MAP[dto.orderBy] ?? 'order.createdAt', 'DESC')
```

## Index Strategy

```sql
-- Composite index cho query filter + sort thường dùng
CREATE INDEX idx_orders_company_status ON orders (company_code, order_status);

-- Partial index cho soft-delete pattern
CREATE INDEX idx_orders_active ON orders (company_code) WHERE deleted_at IS NULL;

-- Index cho FK
CREATE INDEX idx_order_items_order_id ON order_items (order_id);
```

## Transaction

```typescript
// ✅ Đúng: Transaction cho multi-table write
await this.dataSource.transaction(async (manager) => {
  const order = await manager.save(OrderEntity, orderData);
  await manager.save(OrderItemEntity,
    items.map(item => ({ ...item, orderId: order.id }))
  );
  await manager.update(MenuEntity, { id: menuId }, { stockCount: () => 'stock_count - 1' });
});
```

## Redis Cache Patterns

```typescript
// ✅ Cache-aside với TTL
async getMenuByCompany(companyId: string): Promise<Menu[]> {
  const key = `menu:company:${companyId}`;
  const cached = await this.redis.get(key);
  if (cached) return JSON.parse(cached);

  const data = await this.menuRepo
    .createQueryBuilder('menu')
    .where('menu.companyId = :companyId AND menu.deletedAt IS NULL', { companyId })
    .orderBy('menu.sortOrder', 'ASC')
    .getMany();

  await this.redis.setex(key, 300, JSON.stringify(data)); // TTL: 5 phút
  return data;
}

// ✅ Invalidate khi data thay đổi
async updateMenu(companyId: string, ...): Promise<void> {
  await this.menuRepo.update(...);
  await this.redis.del(`menu:company:${companyId}`); // invalidate
}
```

## Checklist

- [ ] Column naming `snake_case` trong entity?
- [ ] UUID primary key?
- [ ] `timestamptz` cho timestamp columns?
- [ ] Soft delete dùng `deleted_at` nullable?
- [ ] Migration file có cả `up()` và `down()`?
- [ ] `synchronize: false` trong production?
- [ ] Mọi query filter column đều có index?
- [ ] QueryBuilder (không chain relations)?
- [ ] orderBy dùng whitelist map?
- [ ] N+1 không có?
- [ ] Multi-table write dùng transaction?
- [ ] Redis key có TTL?

## Chi tiết đầy đủ

> Skill này là nguồn guidelines đầy đủ cho PostgreSQL/TypeORM — không có file guidelines riêng bên ngoài.
