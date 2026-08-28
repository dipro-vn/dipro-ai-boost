---
description: Review code thay đổi trên branch hiện tại hoặc một file cụ thể. Tự động detect repo và áp dụng đúng checklist. Dùng: /review-code [path/to/file hoặc để trống để review toàn bộ diff]
---

Thực hiện code review cho: $ARGUMENTS

## Bước 1 — Xác định repo và lấy code

Nếu `$ARGUMENTS` là file path cụ thể → đọc file đó.
Nếu không có argument → lấy git diff: `git diff HEAD` hoặc `git diff main...HEAD`.

Xác định repo đang review:
- Có `@Module()`, `@Injectable()`, `TypeORM` → **repo backend** (NestJS)
- Có `useQuery`, `createSlice`, `antd` → **repo frontend** (React)
- Có `@Riverpod`, `@freezed`, `Dio` → **repo mobile** (Flutter)

## Bước 2 — Áp dụng checklist theo repo

**NestJS (repo backend):**
- [ ] Column naming snake_case trong entity?
- [ ] Migration có `up()` và `down()`?
- [ ] Không N+1 query (check leftJoin thay vì loop)?
- [ ] Redis key có TTL?
- [ ] DTO có class-validator decorator?
- [ ] Exception dùng NestJS HttpException subclass?
- [ ] Không hard-code secret/key?
- [ ] `orderBy` dùng whitelist map?

**React (repo frontend):**
- [ ] Đúng repo — không lẫn domain logic giữa các repo frontend?
- [ ] TanStack Query v5 object syntax `{ queryKey, queryFn }`?
- [ ] Redux chỉ cho client state (không cache server data)?
- [ ] `invalidateQueries` sau mutation?
- [ ] `useNavigate` thay vì `useHistory`?
- [ ] `useEffect` deps đầy đủ?
- [ ] Không `as any` không có lý do?

**Flutter (repo mobile):**
- [ ] `hooks_riverpod` — không Provider/BLoC?
- [ ] Retrofit `@RestApi()` — không gọi Dio trực tiếp?
- [ ] Socket cleanup `off()` trong dispose?
- [ ] `@freezed` + build_runner đã chạy?
- [ ] `flutter_screenutil` cho sizing?
- [ ] Version pubspec.yaml đúng convention?

## Bước 3 — Output

```
## Code Review — [file/branch]
Repo: [tên repo] | Stack: [NestJS/React/Flutter]

🔴 Critical (phải fix trước merge):
  - [Line X] Vấn đề → Fix cụ thể

🟡 Warning (nên fix):
  - [Line X] Vấn đề → Đề xuất

🟢 Good:
  - [Điểm tốt]

✅ Kết luận: Approve / Request Changes
```
