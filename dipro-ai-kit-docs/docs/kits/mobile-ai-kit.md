# Kit 4: mobile-ai-kit

> **Flutter + React Native Specialist** — Bộ rules, workflows, skills chuyên sâu cho mobile development.

---

## Mục đích

`mobile-ai-kit` cung cấp AI workflow chuyên biệt cho **Flutter** và **React Native** mobile development:

- Plan trước khi code (bắt buộc với task trung bình trở lên)
- Fix bug với workflow rõ ràng
- Implement feature theo Clean Architecture / MVVM
- Refactor, optimize performance
- Tuân thủ strict linting

---

## Cài đặt qua Symlink (khuyến nghị)

```bash
# Thêm dipro-ai-kit như git submodule
git submodule add -b main git@github.com:dipro-vn/dipro-ai-kit.git tools/dipro-ai-kit

# Tạo .claude folder
mkdir -p .claude

# Symlink các thành phần
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/CLAUDE.md .claude/CLAUDE.md
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/settings.json .claude/settings.json
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/rules .claude/rules
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/workflows .claude/workflows
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/skills .claude/skills
ln -s ../tools/dipro-ai-kit/mobile-ai-kit/.claude/tools .claude/tools
```

Xem `guideline/step1-3` để cài đầy đủ gồm MCP tools.

---

## Cấu trúc kit

```
mobile-ai-kit/
├── README.md
├── guideline/
│   ├── step1-install-source-map.md
│   ├── step2-setup-mcp.md
│   └── step3-custom.md
├── docs/                       ← ADR (Architecture Decision Records)
├── skills-lock.json            ← Lock file skill đã cài
└── .claude/
    ├── CLAUDE.md               ← Entrypoint (symlink in project)
    ├── settings.json
    ├── rules/
    │   ├── project-base/
    │   │   ├── flutter_common_rules.md
    │   │   └── reactNative_common_rules.md
    │   ├── maintenance/
    │   │   ├── flutter-maintain-common-rules.md
    │   │   └── react-native-maintain-common-rules.md
    │   ├── planning-spec.md          ← Plan trước khi code
    │   ├── skill-selection-spec.md
    │   ├── SECURITY.md
    │   ├── RELIABILITY.md
    │   └── POLICY.md
    ├── workflows/
    │   ├── fix-bug.md
    │   ├── new-feature.md
    │   ├── refactor.md
    │   ├── performance.md
    │   ├── investigate.md
    │   └── default.md
    ├── skills/
    │   ├── flutter-expert/
    │   └── flutter-review/
    └── tools/
        ├── codegraph
        └── understand-anything
```

---

## Workflows

Thay vì commands, mobile-kit dùng **workflows** được trigger bởi task type:

| Task type | Workflow | Khi nào |
|-----------|---------|---------|
| Fix bug | `workflows/fix-bug.md` | Có bug report |
| Feature mới | `workflows/new-feature.md` | Thêm chức năng |
| Refactor | `workflows/refactor.md` | Cải cấu trúc code |
| Performance | `workflows/performance.md` | Optimize |
| Điều tra | `workflows/investigate.md` | Tìm nguyên nhân issue |
| Khác | `workflows/default.md` | Mọi task khác |

---

## Flutter Stack

### Bắt buộc

| Layer | Package | Version |
|-------|---------|---------|
| State Management | `hooks_riverpod` | 3.0.1 |
| HTTP | Retrofit + Dio | Latest |
| Routing | `auto_route` | Latest |
| Immutable State | `freezed` | Latest |
| Sizing | `flutter_screenutil` | Latest |

### Không được dùng

```
❌ Provider, BLoC, GetX, MobX (state management)
❌ http package, chopper (HTTP)
❌ go_router, Navigator.push trực tiếp (routing)
❌ Equatable (dùng freezed thay)
```

### Code conventions

```dart
// ✅ Riverpod StateNotifierProvider
@riverpod
class OrderNotifier extends _$OrderNotifier {
  @override
  FutureOr<List<Order>> build() => ref.watch(orderRepositoryProvider).getAll();
}

// ✅ freezed cho immutable state
@freezed
class Order with _$Order {
  const factory Order({
    required String id,
    required OrderStatus status,
    required double totalAmount,
  }) = _Order;
}

// ✅ flutter_screenutil cho sizing
Container(
  width: 100.w,
  height: 50.h,
  padding: EdgeInsets.all(16.r),
)

// ✅ const constructor
const Text('Hello') // tiết kiệm rebuild
```

### Flutter linting (strict)

```yaml
# analysis_options.yaml bắt buộc
analyzer:
  strong-mode:
    implicit-casts: false
    implicit-dynamic: false

linter:
  rules:
    - require_trailing_commas
    - unawaited_futures
    - avoid_print   # dùng logger thay
    - prefer_const_constructors
```

---

## React Native Stack

### Bắt buộc

| Layer | Package |
|-------|---------|
| State Management | Redux Toolkit + RTK Query |
| HTTP | Axios hoặc RTK Query |
| Routing | React Navigation v6/v7 |
| Language | TypeScript strict mode |

### Không được dùng

```
❌ MobX, Context API (state)
❌ Fetch thuần (HTTP)
❌ JavaScript (dùng TypeScript)
```

### Code conventions

```typescript
// ✅ Redux Toolkit
const orderSlice = createSlice({
  name: 'orders',
  initialState: { items: [] as Order[] },
  reducers: {
    setOrders: (state, action) => { state.items = action.payload; },
  },
});

// ✅ RTK Query
const orderApi = createApi({
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  endpoints: (builder) => ({
    getOrders: builder.query<Order[], void>({ query: () => '/orders' }),
  }),
});

// ✅ Feature-first structure
src/features/orders/
├── components/
├── screens/
├── hooks/
├── store/
└── api/
```

---

## Nguyên tắc chung (Flutter và RN)

!!! warning "Plan trước khi code — BẮT BUỘC"
    Task trung bình trở lên phải lên plan, chờ approve trước khi bắt đầu code.
    
    ```
    "Tôi sẽ implement theo cách sau:
    1. ...
    2. ...
    Bạn có muốn tôi bắt đầu không?"
    ```

| Nguyên tắc | Áp dụng |
|-----------|---------|
| Không refactor working code | Chỉ sửa khi task yêu cầu |
| Follow existing convention | Không tự đặt naming/pattern mới |
| Consistent state management | Chỉ 1 pattern per project |
| Audit trước khi code | Đọc pubspec.yaml/package.json trước |
| Zero error | Không console.log, print, hardcode |

---

## Version Convention (Mobile)

```
DEV:  0.0.<build_number>
STG:  0.1.<build_number>
PROD: 1.0.<build_number>
```

Không bỏ qua STG để lên thẳng PROD.
