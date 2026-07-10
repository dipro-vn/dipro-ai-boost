# Kit 3: fe-kit

> **React Frontend Specialist** — Bộ agents, commands, 90+ skills chuyên sâu cho React 19 web development.

---

## Mục đích

`fe-kit` cung cấp AI workflow chuyên biệt cho **React frontend development**:

- Thêm feature/page mới với component + hook + store đúng pattern
- Fix UI/state bugs với test-first approach
- Review code component, TanStack Query, Redux slice
- Sinh test unit cho component, hook, store
- Refactor theo React 19 best practices

---

## Tech Stack cố định

| Layer | Bắt buộc | Không được dùng |
|-------|---------|----------------|
| UI Framework | React 19 + TypeScript | Vue, Angular |
| Build tool | Vite 7 | CRA, Webpack thuần |
| Server state | TanStack Query v5 (object syntax) | Redux cho server data, v4 positional |
| Client state | Redux Toolkit v2 | Context API cho global/auth state |
| Forms | react-hook-form + yup | Formik, AntD Form.Item rules |
| UI Components | Ant Design v6 | MUI, Chakra |
| Routing | react-router-dom v7 | Next.js router |
| Styling | TailwindCSS v4 | CSS Modules, styled-components |
| Secrets | `VITE_*` env via AWS Parameter Store | Hard-code URL |

---

## Cài đặt

```bash
cp -r /path/to/fe-kit/.claude my-react-project/.claude
cd my-react-project

claude
/new-feature "Thêm trang quản lý đơn hàng"
```

---

## Cấu trúc kit

```
fe-kit/
├── README.md
└── .claude/
    ├── agents/
    │   ├── frontend-analyst.md
    │   ├── frontend-architect.md
    │   ├── frontend-developer.md
    │   ├── frontend-tester.md
    │   └── frontend-reviewer.md
    ├── commands/
    │   ├── new-feature.md      ← /new-feature
    │   ├── bug-fix.md          ← /bug-fix
    │   ├── code-review.md      ← /code-review
    │   ├── refactoring.md      ← /refactoring
    │   └── test-generation.md  ← /test-generation
    ├── skills/                 ← 90+ skills
    ├── settings.local.json     ← (gitignore, chứa API key cá nhân)
    └── .mcp.json
```

---

## Commands

### `/new-feature`

```
/new-feature "Trang quản lý đơn hàng với filter, sort, pagination"
```

**Flow:**
1. Đọc DESIGN.md + API Contract từ backend
2. Kiểm tra patterns tương tự trong codebase
3. Tạo page component + query hooks + Redux slice (nếu cần)
4. Tạo API service function

### `/bug-fix`

```
/bug-fix "Danh sách đơn hàng không cập nhật sau khi cancel"
```

Test-first: viết test reproduce → fix → verify PASS

### `/code-review`

```
/code-review
```

Review: component pattern, TanStack Query syntax, Redux usage, TypeScript strict, memo hóa hợp lý.

### `/refactoring`

```
/refactoring "Tách OrderList component thành smaller components"
```

Không refactor ngoài scope — note style drift thay vì tự sửa.

### `/test-generation`

```
/test-generation OrderCard
```

Sinh Jest + React Testing Library tests.

---

## Core Patterns

### TanStack Query v5 — OBJECT SYNTAX BẮT BUỘC

```tsx
// ✅ v5 object syntax
const { data, isLoading } = useQuery({
  queryKey: ['orders', { status, page }],
  queryFn: () => orderApi.list({ status, page }),
  staleTime: 5 * 60 * 1000,
});

const mutation = useMutation({
  mutationFn: (id: string) => orderApi.cancel(id),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['orders'] });
  },
});

// ❌ v4 positional — KHÔNG dùng
const { data } = useQuery(['orders'], () => orderApi.list());
```

### Redux Toolkit — Client state only

```typescript
// ✅ Dùng Redux cho client state (UI state, auth)
const cartSlice = createSlice({
  name: 'cart',
  initialState: { items: [], isOpen: false },
  reducers: {
    addItem: (state, action) => { state.items.push(action.payload); },
    toggleCart: (state) => { state.isOpen = !state.isOpen; },
  },
});

// ❌ Không dùng Redux cho server data — dùng TanStack Query
// ❌ Không dùng Context API cho global/auth state — dùng Redux
```

### Component Pattern

```tsx
// ✅ Named export + Props interface
interface OrderCardProps {
  orderId: string;
  onCancel?: (id: string) => void;
}

export const OrderCard: React.FC<OrderCardProps> = ({ orderId, onCancel }) => {
  const { data: order } = useQuery({
    queryKey: ['orders', orderId],
    queryFn: () => orderApi.getById(orderId),
  });

  return <div>...</div>;
};

// ❌ Không dùng class component
// ❌ Không dùng default export cho component (khó refactor)
```

### Form với react-hook-form + yup

```tsx
const schema = yup.object({
  email: yup.string().email().required(),
  amount: yup.number().positive().required(),
});

const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: yupResolver(schema),
});
```

### TypeScript Strict

```typescript
// ❌ any bị cấm
const data: any = response; // KHÔNG

// ✅ Proper typing
interface OrderResponse {
  id: string;
  status: 'pending' | 'confirmed' | 'cancelled';
  totalAmount: number;
}
```

---

## Project Structure

```
src/
├── pages/          ← Route-level components (1 file = 1 route)
│   └── orders/
│       ├── OrderListPage.tsx
│       └── OrderDetailPage.tsx
├── components/     ← Shared, reusable UI
│   └── OrderCard/
│       ├── OrderCard.tsx
│       └── OrderCard.test.tsx
├── hooks/          ← Custom hooks
│   └── useOrderList.ts
├── store/          ← Redux slices (client state only)
│   └── cartSlice.ts
├── services/       ← API call functions
│   └── orderApi.ts
└── utils/          ← Pure utility functions
```

---

## Skills on-demand

| Skill | Khi nào |
|-------|---------|
| `react-expert` | Component/hook API questions |
| `react-query-query-pattern` | TanStack Query v5 patterns |
| `react-query-mutation-pattern` | Mutation + optimistic update |
| `react-state-management` | Redux vs Query decision |
| `form-react-hook-form` | Form implementation |
| `frontend-review` | Code review |
| `typescript-strict-mode` | TypeScript issues |
| `react-performance` | memo, useMemo, useCallback |
| `tailwind-component-styling` | TailwindCSS patterns |
| `security-token-handling` | JWT, httpOnly cookie |
