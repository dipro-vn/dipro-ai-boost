# Kit 2: backend-kit

> **NestJS Backend Specialist** — Bộ agents, commands, skills chuyên sâu cho phát triển backend NestJS.

---

## Mục đích

`backend-kit` cung cấp AI workflow chuyên biệt cho **NestJS backend development**:

- Scaffold module, controller, service, DTO, migration từ đặc tả
- Review DB schema, query performance, cache strategy
- Sinh unit test + integration test
- Kiểm tra security (auth, authorization, input validation)
- Produce REST API Contract để handoff cho FE/Mobile

---

## Tech Stack cố định

| Layer | Bắt buộc | Không được dùng |
|-------|---------|----------------|
| Framework | NestJS + TypeScript | Express thuần, Fastify |
| Database | PostgreSQL 16 + TypeORM 0.3.x | MySQL, MongoDB, Prisma |
| API | REST + JWT Auth | GraphQL, gRPC, tRPC |
| Cache | Redis (cache-aside) | Memcached |
| Test | Jest + Supertest | Vitest, Mocha |
| Code analysis | CodeGraph / Understand-Anything | grep/cat/find thuần |

---

## Cài đặt

```bash
# Copy .claude vào NestJS project
cp -r /path/to/backend-kit/.claude my-backend/.claude

# Hoặc merge nếu .claude đã có
cp -rn /path/to/backend-kit/.claude/agents my-backend/.claude/
cp -rn /path/to/backend-kit/.claude/commands my-backend/.claude/
cp -rn /path/to/backend-kit/.claude/skills my-backend/.claude/
```

---

## Cấu trúc kit

```
backend-kit/
├── README.md
├── guideline/
│   └── step1-install-source-map.md
└── .claude/
    ├── agents/
    │   ├── backend-analyst.md     ← Phân tích requirement BE
    │   ├── backend-architect.md   ← Thiết kế module/DB
    │   ├── backend-developer.md   ← Implement code
    │   ├── backend-tester.md      ← Sinh test
    │   └── backend-reviewer.md    ← Review code
    ├── commands/
    │   ├── new-feature.md         ← /new-feature
    │   ├── bug-fix.md             ← /bug-fix
    │   ├── code-review.md         ← /code-review
    │   ├── test-generation.md     ← /test-generation
    │   ├── generate-api.md        ← /generate-api
    │   ├── migration.md           ← /migration
    │   ├── db-review.md           ← /db-review
    │   ├── refactoring.md         ← /refactoring
    │   └── api-contract.md        ← /api-contract
    ├── skills/
    │   ├── nestjs-best-practices/
    │   ├── nestjs-testing/
    │   ├── postgresql/
    │   ├── redis-development/
    │   ├── rest-api-contract/
    │   ├── backend-security-review/
    │   ├── backend-query-cache-performance/
    │   └── sourcebase-reuse-first/
    └── tools/
        ├── codegraph
        └── understand-anything
```

---

## Commands

### `/new-feature`

Thêm endpoint/module mới từ đặc tả:

```
/new-feature "Thêm API tìm kiếm đơn hàng với filter status, date range, pagination"
```

**Flow:**
1. Đọc DESIGN.md + task file
2. `tilth_search` tìm patterns tương tự trong codebase
3. Scaffold: module → entity → DTO → service → controller → migration
4. Viết unit test

### `/generate-api <entity>`

Scaffold đầy đủ từ tên entity:

```
/generate-api Order
```

**Output:**
```
src/modules/order/
├── order.module.ts
├── order.controller.ts
├── order.service.ts
├── entities/order.entity.ts
├── dto/
│   ├── create-order.dto.ts
│   └── list-order.dto.ts
└── order.service.spec.ts
```

### `/api-contract`

Produce REST API Contract để handoff FE/Mobile:

```
/api-contract OrderModule
```

**Output:** Bảng markdown `| Method | Path | Auth | Request | Response | Errors |`

### `/db-review`

Audit schema, query, index, cache:

```
/db-review OrderEntity
```

Kiểm tra: N+1 potential, missing index, no TTL on Redis, eager loading, orderBy injection risk.

### `/bug-fix`

**Test-first mandate:** Viết test reproduce trước, fix sau:

```
/bug-fix "Sort scores không ổn định khi 2 record cùng score"
```

1. Viết test → verify FAIL (chứng minh bug tồn tại)
2. Fix code → verify PASS
3. Run full test suite

---

## Core Rules

### Module Structure

```typescript
// Feature-first, không technical layers
src/modules/<feature>/
├── <feature>.module.ts
├── <feature>.controller.ts   // HTTP layer only
├── <feature>.service.ts      // Business logic
├── entities/<feature>.entity.ts
├── dto/
└── <feature>.service.spec.ts
```

### TypeORM Conventions

```typescript
// ✅ UUID PK
@PrimaryGeneratedColumn('uuid')
id: string;

// ✅ snake_case column name
@Column({ name: 'company_code', length: 50 })
companyCode: string;

// ✅ timestamptz
@CreateDateColumn({ type: 'timestamptz' })
createdAt: Date;

// ✅ Soft delete
@DeleteDateColumn({ name: 'deleted_at' })
deletedAt: Date;

// ✅ eager: false để tránh N+1
@ManyToOne(() => CompanyEntity, { eager: false })
@JoinColumn({ name: 'company_id' })
company: CompanyEntity;
```

### orderBy Whitelist (quan trọng)

```typescript
// ✅ Whitelist để tránh N+1 bug từ dynamic orderBy
const ORDER_BY_MAP = {
  createdAt: 'order.createdAt',
  status: 'order.status',
  totalAmount: 'order.totalAmount',
};
.orderBy(ORDER_BY_MAP[dto.orderBy] ?? 'order.createdAt', dto.dir ?? 'DESC')
```

### Redis Cache Pattern

```typescript
// Cache-aside: check cache → DB → set cache
async findById(id: string): Promise<Order> {
  const cached = await this.redis.get(`order:${id}`);
  if (cached) return JSON.parse(cached);

  const order = await this.orderRepo.findOne({ where: { id } });
  await this.redis.setex(`order:${id}`, 300, JSON.stringify(order)); // TTL bắt buộc
  return order;
}

// Invalidate on write
async update(id: string, dto: UpdateOrderDto): Promise<Order> {
  const order = await this.orderRepo.save({ id, ...dto });
  await this.redis.del(`order:${id}`); // Invalidate sau write
  return order;
}
```

### Migration Rules

```typescript
// Mỗi migration phải có up() và down()
export class AddOrderStatusIndex1234567890 implements MigrationInterface {
  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`CREATE INDEX idx_order_status ON orders (status)`);
  }
  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`DROP INDEX idx_order_status`);
  }
}
```

!!! warning "Không bao giờ"
    - `synchronize: true` trong production
    - Sửa migration đã chạy — tạo migration mới
    - Tự sửa migration file khi chưa hỏi Tech Lead

---

## Skills on-demand

| Skill | Khi nào load |
|-------|-------------|
| `nestjs-best-practices` | Viết module mới |
| `postgresql` | Thiết kế schema, query |
| `redis-development` | Implement cache |
| `rest-api-contract` | Tạo API contract |
| `nestjs-testing` | Viết test |
| `backend-security-review` | Review security |
| `backend-query-cache-performance` | Optimize performance |
| `sourcebase-reuse-first` | Trước khi thêm code mới |
