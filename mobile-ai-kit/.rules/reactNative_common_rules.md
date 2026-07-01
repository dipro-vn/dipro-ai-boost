# React Native Common Rules — Mobile AI Kit

## 1. Stack cố định, dùng nhất quán
- Stack chuẩn: **React Native + TypeScript + Redux Toolkit**. Mọi source RN mới bám theo stack này, không tự ý đổi state management.
- **Server state** dùng **RTK Query**; **client/UI state** dùng slice (`createSlice`). Không nhét cache API vào slice thường nếu đã có RTK Query.
- Component: **functional component + hooks**. Không dùng class component.

## 2. Dependency Rule (tách tầng)
- Component **không gọi thẳng** `fetch`/axios/AsyncStorage → đi qua **service / RTK Query / thunk**.
- Logic nghiệp vụ nằm trong **slice reducer / thunk / service**, không nằm trong component.
- Tầng logic & service **không import** thứ thuộc UI (`react-native` component, navigation). Logic thuần, không phụ thuộc UI.

## 3. State bất biến (Immutable state)
- **Chỉ được "mutate" draft state bên trong reducer của `createSlice`** (Immer lo phần immutable). Ngoài reducer, **không** mutate state/props.
- Selector phải pure. Không sửa mảng/object props trực tiếp; tạo bản mới.

## 4. State holder phải UI-agnostic
- Slice / thunk / selector **không** gọi `navigation`, không đụng component.
- Side-effect (điều hướng, toast...) xử lý ở component/hook (qua `useEffect`, listener middleware), không nằm trong reducer.

## 5. Logic test được không cần UI
- Reducer / selector / thunk phải **unit test được** mà không cần render component.
- Nếu phải render mới test được logic → logic đặt sai chỗ.

## 6. Tổ chức code
- **Feature-first**: mỗi feature 1 folder (chứa slice, components, api, hooks của feature đó). Không gom hết `components/` toàn app vào 1 chỗ.
- Code dùng chung > 1 feature → đẩy vào `shared/` (hoặc `common/`). Store config + base api ở `app/` hoặc `store/`.
- **1 file = 1 trách nhiệm chính.**

```
src/
├── app/                # store, rootReducer, baseApi, navigation root
├── features/
│   └── <feature>/
│       ├── <feature>Slice.ts
│       ├── <feature>Api.ts        # RTK Query endpoints
│       ├── components/
│       ├── hooks/
│       └── screens/
├── shared/             # components, hooks, utils, types dùng chung
└── i18n/
```

## 7. Naming (file & folder)
- Component / Screen: file **PascalCase** → `UserProfile.tsx`, `LoginScreen.tsx`.
- Hook: `useXxx.ts` (`useAuth.ts`). Slice: `xxxSlice.ts`. API: `xxxApi.ts`. Util/type: `camelCase.ts`.
- Folder: `camelCase` hoặc `kebab-case` — **chọn 1 và nhất quán** toàn repo.

## 8. Class & symbol (TypeScript)
- Component / Type / Interface / Enum: `PascalCase`.
- Biến / hàm / hook: `camelCase`. Hook luôn prefix `use`.
- Constant cố định: `UPPER_SNAKE_CASE`.
- Boolean: prefix `is/has/can/should` (`isLoading`, `hasError`).

## 9. Rule code TS/RN (BẮT BUỘC)
- Bật **TypeScript strict**; **cấm `any`** (dùng `unknown` + thu hẹp kiểu khi cần).
- Chỉ dùng **functional component + hooks**; tuân thủ **Rules of Hooks**.
- **Không** `console.log` trong production → dùng logger.
- Không để Promise "trôi" (floating promise) — `await` hoặc xử lý rõ ràng.
- `useEffect` khai báo **đủ dependency** (không tắt lint `exhaustive-deps` tùy tiện).

## 10. Component & performance
- Component nhỏ, một trách nhiệm; không nhét logic nghiệp vụ / gọi API trong phần render.
- List dài → **`FlatList`/`FlashList`**, không `.map` trong `ScrollView`. Luôn có `key` ổn định (không dùng index nếu list thay đổi).
- Memo hóa hợp lý: `React.memo`, `useMemo`, `useCallback` cho props/handler truyền xuống list/child nặng.
- Tách `StyleSheet.create` ra ngoài render; tránh tạo object style/inline function mới mỗi lần render.

## 11. Async & data
- Server state qua **RTK Query** (hoặc `createAsyncThunk` nếu chưa dùng RTK Query); có **typed API layer**.
- Phân biệt **DTO (response API)** và **model dùng trong app**; có mapper khi cần, không xài thẳng response lên UI.
- Mọi call async có **loading / error state** rõ ràng.

## 12. Đa ngôn ngữ (i18n) — nếu project có config multi-language
- Dùng `i18next` / `react-i18next`. Không hard-code chuỗi hiển thị.
- Mọi label, message, format ngày/tiền tệ qua localization.

## 13. Linting baseline (chung mọi project)
ESLint + Prettier, đặt ở root repo:
```js
// .eslintrc.js
module.exports = {
  root: true,
  extends: [
    '@react-native',                       // base RN
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'prettier',
  ],
  plugins: ['@typescript-eslint', 'react-hooks'],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-floating-promises': 'error',
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    'no-console': ['warn', { allow: ['warn', 'error'] }],
  },
};
```
- CI fail nếu còn lint error. Chạy `prettier` + `eslint` trước khi commit.

## 14. Test (BẮT BUỘC tối thiểu)
- Stack test: **Jest + React Native Testing Library**.
- **Unit test**: reducer / selector / thunk / custom hook. Mock API, không gọi network thật.
- **Component test**: cho component có logic hiển thị quan trọng.
- File test mirror cấu trúc `src/`, đặt tên `<file>.test.ts(x)`.

## 15. Git / PR convention (nhẹ)
- Commit theo Conventional Commits: `feat:` `fix:` `refactor:` `test:` `chore:` `docs:`.
- 1 PR = 1 mục tiêu; PR phải pass lint + typecheck (`tsc --noEmit`) + test.

## 16. Checklist review (dán vào PR template)
```
[ ] Component không gọi thẳng API/storage — đi qua service/RTK Query/thunk
[ ] State chỉ "mutate" trong reducer của createSlice; ngoài ra immutable
[ ] Slice/thunk/selector không gọi navigation / không đụng component
[ ] Selector pure; logic nghiệp vụ không nằm trong phần render
[ ] Không dùng any; TypeScript strict pass (tsc --noEmit sạch)
[ ] useEffect đủ dependency; tuân thủ Rules of Hooks
[ ] List dài dùng FlatList/FlashList với key ổn định
[ ] Không hard-code chuỗi hiển thị (đã qua i18n) — nếu có i18n
[ ] Có unit test cho logic mới (reducer/selector/thunk/hook)
[ ] eslint + prettier sạch (0 error)
[ ] Đặt tên file/symbol đúng quy ước (mục 7, 8)
```

## 17. Hướng dẫn cho AI assistant (khi sinh/sửa code)
1. Mặc định stack **RN + TypeScript + Redux Toolkit**; server state dùng **RTK Query**, không tự đổi state management.
2. Luôn sinh **functional component + hooks**, **không** `any`, tuân thủ rule mục 2–12.
3. Đặt code đúng feature, đúng tầng (logic vào slice/thunk/service, không vào component).
4. Kèm/đề xuất unit test cho reducer/selector/thunk/hook mới.
5. Khi sửa code vi phạm rule, nêu rõ vi phạm điều nào (theo số mục).