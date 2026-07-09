---
name: nestjs-testing
description: Jest and Supertest guidance for NestJS unit, service, controller, endpoint, regression, and migration-adjacent tests.
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
- [ ] Bug fixes include a regression test or documented micro-fix reason.
