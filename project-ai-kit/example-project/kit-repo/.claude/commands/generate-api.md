---
description: Generate scaffold NestJS API endpoint theo đúng pattern dự án — module/controller/service/dto/entity. Dùng: /generate-api <module-name> [resource-name]
---

Generate NestJS API endpoint scaffold cho: **$ARGUMENTS**

## Bước 1 — Xác nhận pattern hiện có

```
tilth_search(query: "AdminController")   ← xem pattern controller hiện tại
tilth_files(pattern: "**/*.module.ts", path: "<repo-backend>/src/modules/")
```

## Bước 2 — Generate theo đúng pattern dự án

Tạo các file sau (nếu chưa có):

**Module** (`<module>.module.ts`):
```typescript
@Module({
  imports: [TypeOrmModule.forFeature([<Entity>])],
  controllers: [<Module>Controller],
  providers: [<Module>Service],
  exports: [<Module>Service],
})
export class <Module>Module {}
```

**Controller** (`<module>.controller.ts`):
```typescript
@ApiTags('<resource>')
@Controller('<prefix>/<resource>')
export class <Module>Controller {
  constructor(private readonly service: <Module>Service) {}

  @Get() @UseGuards(JwtAuthGuard)
  findAll(@Query() dto: List<Resource>Dto) { ... }

  @Post() @UseGuards(JwtAuthGuard)
  create(@Body() dto: Create<Resource>Dto) { ... }
}
```

**Service** (`<module>.service.ts`):
```typescript
@Injectable()
export class <Module>Service {
  constructor(
    @InjectRepository(<Entity>)
    private readonly repo: Repository<Entity>,
  ) {}
}
```

**DTOs** (`dto/create-<resource>.dto.ts`, `dto/list-<resource>.dto.ts`):
- Request DTO dùng `class-validator` decorators
- Response DTO dùng `@Exclude()` cho sensitive fields

**Entity** (`entities/<resource>.entity.ts`):
- UUID primary key, `snake_case` columns, `timestamptz`, `deleted_at`

**Migration**: Tạo file migration nếu có entity mới.

## Bước 3 — Sau khi generate

Nhắc nhở:
- Thêm module vào `app.module.ts` hoặc parent module
- Chạy `npm run migration:generate` nếu có entity mới
- Viết unit test cho service
