---
name: nestjs-testing
description: Use before writing implementation code for any feature or bug fix. Symptoms — a plan to add tests after the code, a bug fix with no failing test, a test that only asserts a mock was called, an endpoint with no validation or authorization test, acceptance criteria with no matching assertions.
metadata:
  stack: jest, supertest, nestjs
---

# NestJS Testing

Use this skill when adding or reviewing backend tests.

## Test Strategy

- Service tests cover business logic, validation branches delegated to services, transactions, and cache invalidation.
- Controller tests cover route wiring only when endpoint tests are too heavy.
- Endpoint tests with Supertest cover guards, DTO validation, status codes, and response shape.
- Regression tests reproduce reported bugs before implementation changes.
- Feature tests are written from the approved contract and acceptance criteria — before or in parallel with the implementation, never read back from it. A test copied from the code proves only that the code does what it does.

## Unit Test Pattern

```typescript
describe('OrdersService', () => {
  let service: OrdersService;
  let orders: jest.Mocked<OrdersRepository>;

  beforeEach(async () => {
    orders = {
      findById: jest.fn(),
      save: jest.fn(),
    } as unknown as jest.Mocked<OrdersRepository>;

    const moduleRef = await Test.createTestingModule({
      providers: [
        OrdersService,
        { provide: OrdersRepository, useValue: orders },
      ],
    }).compile();

    service = moduleRef.get(OrdersService);
  });

  it('throws NotFoundException when the order does not exist', async () => {
    orders.findById.mockResolvedValue(null);

    await expect(service.getById('order-id')).rejects.toThrow(NotFoundException);
  });
});
```

## Endpoint Test Pattern

```typescript
it('returns 400 when query validation fails', async () => {
  await request(app.getHttpServer())
    .get('/api/orders?page=invalid')
    .expect(400);
});
```

## Integration Tests Against A Real Database

A test that mocks the repository cannot see the SQL. It passes when the tenant filter is missing, when the QueryBuilder has a typo, when soft-deleted rows leak, and when a unique constraint is violated. Those are exactly the defects that reach production.

Write an integration test against a real PostgreSQL database when the change involves:

- Tenant or owner scope inside a query.
- A QueryBuilder with filters, joins, sorting, or pagination.
- Soft delete filtering.
- A transaction, lock, or unique constraint.
- A migration.

Rules:

- Use the project's existing test database setup. If there is none, propose one to the user (a dedicated test database or Testcontainers) — do not add a library without approval.
- Build the schema with migrations, not `synchronize`, so the test also proves the migration.
- Isolate tests: truncate touched tables in `beforeEach`, or wrap each test in a transaction that rolls back.
- Seed **two** tenants. A scope test with one tenant proves nothing.

```typescript
it("does not return another company's order", async () => {
  const other = await seedOrder({ companyId: companyB });

  await request(app.getHttpServer())
    .get(`/api/orders/${other.id}`)
    .set('Authorization', tokenFor(companyA))
    .expect(404);
});
```

## Regression Test Rules

- Write the failing test before changing implementation.
- Verify the failure is caused by the missing behavior.
- Implement the smallest change that makes the test pass.
- Run the focused test and the relevant suite.

## Checklist

- [ ] Test names describe behavior.
- [ ] Tests use real service logic where practical.
- [ ] External systems are replaced at provider boundaries.
- [ ] Validation failures are covered.
- [ ] Authorization failures are covered for protected routes.
- [ ] Query scope, QueryBuilder, soft delete, and constraint behavior are covered by an integration test against a real database.
- [ ] Bug fixes include a regression test or documented micro-fix reason.
