---
name: nestjs-testing
description: Jest and Supertest guidance for NestJS unit, service, controller, endpoint, regression, and migration-adjacent tests.
metadata:
  stack: jest, supertest, nestjs, prisma
---

# NestJS Testing

Use this skill when adding or reviewing backend tests.

## Test Strategy

- Unit specs live next to the code as `src/modules/<feature>/<feature>.service.spec.ts` and run with `npm run test`. Endpoint specs live in `test/` and run with `npm run test:e2e`.
- Service tests cover business logic, validation branches delegated to services, and transactions.
- Controller tests cover route wiring only when endpoint tests are too heavy.
- Endpoint tests with Supertest cover guards, DTO validation, status codes, and response shape.
- Regression tests reproduce reported bugs before implementation changes.

## Unit Test Pattern

Mock the feature repository, not `PrismaService`. The repository is the seam the project already uses, so tests stay decoupled from Prisma call shapes.

```typescript
const mockRepo = {
  findAll: jest.fn(),
  count: jest.fn(),
  findOne: jest.fn(),
  create: jest.fn(),
  update: jest.fn(),
  delete: jest.fn(),
};

describe('OrdersService', () => {
  let service: OrdersService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        OrdersService,
        { provide: OrdersRepository, useValue: mockRepo },
      ],
    }).compile();

    service = module.get<OrdersService>(OrdersService);
    jest.clearAllMocks();
  });

  it('throws NotFoundException when the order does not exist', async () => {
    mockRepo.findOne.mockResolvedValue(null);

    await expect(service.findOne(999)).rejects.toThrow(NotFoundException);
  });

  it('passes the whitelisted sort field to the repository', async () => {
    mockRepo.findAll.mockResolvedValue([]);
    mockRepo.count.mockResolvedValue(0);

    await service.findAll({ getListOrdersDto: { page: 1, limit: 10, sortBy: 'createdAt' } });

    expect(mockRepo.findAll).toHaveBeenCalledWith(
      expect.objectContaining({ orderBy: { createdAt: 'asc' } }),
    );
  });
});
```

Ids are numeric in this project. Use numbers in fixtures and expectations, not UUID strings.

## Endpoint Test Pattern

```typescript
it('returns 400 when query validation fails', async () => {
  await request(app.getHttpServer())
    .get('/products?page=invalid')
    .expect(400);
});
```

Request paths carry no `/api` prefix. The app has no global prefix, so a route is the `@Controller('<resource>')` path plus the method path - `/products`, `/users/:id`, `/auth/login`.

## Regression Test Rules

- Write the failing test before changing implementation.
- Verify the failure is caused by the missing behavior.
- Implement the smallest change that makes the test pass.
- Run the focused test and the relevant suite.

## Checklist

- [ ] Test names describe behavior.
- [ ] Tests use real service logic where practical.
- [ ] External systems are replaced at provider boundaries.
- [ ] Request paths match the real routes and carry no `/api` prefix.
- [ ] List-endpoint assertions read `totalItems` / `allItems`, never `total` or `limit`.
- [ ] Validation failures are covered.
- [ ] Authorization failures are covered for protected routes, including the ADMIN-hits-`@Roles(USER)` 403 case.
- [ ] `ERole.PUBLIC` routes are tested without a token, and the handler is not assumed to have `@CurrentUser()`.
- [ ] Bug fixes include a regression test or documented micro-fix reason.
