# React Native Maintenance — Common Rules

> **Scope:** Áp dụng cho **mọi React Native project** khi nhận maintain (project từ client hoặc internal handoff).
> **Triết lý:** Ưu tiên **không phá vỡ** những gì đang chạy → **follow convention hiện có** → **chuẩn hóa dần** qua backlog.
> **Baseline file:** Đây là `common rules`. Pattern-specific rules (vd `redux-toolkit`, `tanstack-query`) sẽ bổ sung, không override phần này.

---

## 0. Nguyên tắc cốt lõi

1. **Đọc trước, sửa sau.** Không chạm code khi chưa hiểu pattern hiện tại.
2. **Không refactor code đang chạy** trừ khi task yêu cầu rõ ràng.
3. **Follow existing convention** > áp convention mới.
4. **Nhất quán** trong 1 project (state, navigation, styling, network) — không mix pattern.
5. **Mọi cleanup / chuẩn hóa** phải có task riêng, không gộp vào feature.

---

## 1. AUDIT_BEFORE_TOUCH — Làm đầu tiên khi nhận project

- Đọc `package.json` + lock file (`yarn.lock` / `package-lock.json` / `pnpm-lock.yaml`) trước khi chạm package nào.
- Xác định **package manager** (npm / yarn / pnpm) — dùng đúng cái đó, không mix lock file.
- Xác định **Expo vs Bare workflow** (có `expo` trong deps + `app.json/app.config` → Expo).
- Xác định **RN version** + **New Architecture** (Fabric / TurboModules) bật hay tắt.
- Liệt kê: **state management**, **navigation**, **styling**, **network / data-fetching** đang dùng.
- Xác định **TypeScript hay JavaScript** (có `tsconfig.json` không).
- Kiểm tra **env config** (`react-native-config` / `.env` / Expo `extra`).
- Ghi lại deprecated / outdated packages (**không fix ngay** — đưa vào backlog).
- Chạy thử `yarn lint` + build 1 lần (iOS & Android) để nắm baseline.

---

## 2. DO_NOT_REFACTOR_WORKING_CODE

- Không refactor code đang hoạt động trừ khi task yêu cầu rõ ràng.
- Không đổi state management giữa chừng (vd: không tự chuyển Context → Redux nếu không có migration plan).
- Không update RN version / native dependency không liên quan tới task.
- Không đổi class component → function component hàng loạt nếu không có task.
- Mọi "cleanup" phải có ticket riêng — **không gộp vào feature task**.

---

## 3. FOLLOW_EXISTING_NAMING

- Nếu component file dùng `PascalCase.tsx` → tiếp tục `PascalCase`.
- Nếu project dùng `kebab-case` cho non-component files → giữ nguyên.
- Nếu screen đặt tên `XxxScreen` → không tự đổi thành `XxxPage`.
- Nếu có prefix component (`AppButton`, `AppText`) → tiếp tục dùng prefix đó.
- Chỉ áp dụng convention chung khi project **chưa có**.

**Fallback (nếu project chưa có convention):**

| Loại | Convention |
|---|---|
| Component files | `PascalCase.tsx` (vd `UserCard.tsx`) |
| Hooks | `useCamelCase.ts` (vd `useAuth.ts`) |
| Utils / helpers | `camelCase.ts` |
| Components / types / interfaces | `PascalCase` |
| Variables / functions | `camelCase` |
| Constants | `UPPER_SNAKE_CASE` |
| Boolean props/vars | `is/has/should` prefix (`isLoading`) |

---

## 4. MAINTAIN_FOLDER_STRUCTURE

- Không tự tạo layer mới (`domain/`, `usecases/`) nếu project không có sẵn.
- **Feature-first** → thêm file vào đúng feature folder.
- **Type-first** → thêm file vào đúng thư mục theo loại.
- Không trộn 2 pattern trong cùng project.

**Cách nhận biết:**

- Feature-first: `src/features/auth/`, `src/features/home/…`
- Type-first: `src/screens/`, `src/components/`, `src/hooks/`, `src/services/…`

---

## 5. STATE_MANAGEMENT_CONSISTENCY

- Xác định pattern hiện tại và chỉ dùng đúng pattern đó cho task mới.
- Phân biệt rõ **server state** (data từ API) và **client state** (UI state).
- Nếu bắt buộc thêm solution mới → **document lý do + migration plan**.

**Nhận biết nhanh qua `package.json`:**

| Package | Pattern |
|---|---|
| `@reduxjs/toolkit` / `redux` | Redux / RTK |
| `zustand` | Zustand |
| `jotai` / `recoil` | Atomic state |
| `mobx` / `mobx-react` | MobX |
| `@tanstack/react-query` / `react-query` | Server state (React Query) |
| `@apollo/client` | GraphQL server state |
| (chỉ Context API) | React Context + `useReducer` |

---

## 6. COMPONENT_STANDARDS

- Prefer **function component + hooks** (không viết class mới nếu project đã dùng function).
- Extract component khi 1 file vượt ~150 lines hoặc JSX quá sâu.
- Không inline anonymous function nặng trong `renderItem` của `FlatList` (dùng `useCallback`).
- Dùng `React.memo` / `useMemo` / `useCallback` đúng chỗ — không lạm dụng.
- List luôn có `keyExtractor` ổn định (không dùng index nếu data thay đổi).
- Kiểm tra `src/components/` trước khi tạo component mới (tránh duplicate).
- Không đặt side-effect ngoài `useEffect`.

---

## 7. NAVIGATION_CONSISTENCY

- Xác định: **React Navigation** (v5/v6/v7) hay **react-native-navigation** (Wix).
- Không tự thêm navigation library thứ hai.
- Route / screen names theo convention đã có (string constant / enum / typed param list).
- Nếu dùng TypeScript → giữ đúng typed `ParamList` cho navigator.

**Không được làm:**

- Mix 2 navigation library.
- Hardcode screen name string rải rác (dùng constant / enum tập trung).
- Truyền object nặng / non-serializable qua route params.

---

## 8. NETWORK_LAYER

- Không thêm `axios` nếu project đang dùng `fetch` thuần (và ngược lại) — trừ khi có lý do.
- Tất cả API call đi qua **service / api layer** — không gọi thẳng trong component.
- Nếu dùng React Query / RTK Query → giữ đúng pattern (không gọi fetch thủ công song song).
- Error handling nhất quán (interceptor / error boundary / try-catch — chọn 1 style).
- Base URL / endpoint nằm trong `config / env` — **không hardcode**.

**Trước khi viết API mới:**

- Endpoint này đã có trong existing service chưa?
- Type / response model đã có chưa (tránh duplicate)?

---

## 9. STYLING_CONSISTENCY

- Xác định approach: `StyleSheet.create` / styled-components / NativeWind (Tailwind) / Tamagui.
- Không mix nhiều styling solution trong cùng project.
- Không hardcode màu / spacing / font nếu project có **theme / design token**.
- Ưu tiên dùng `theme` constant (`colors`, `spacing`, `typography`) nếu có sẵn.
- Responsive: dùng đúng util của project (`Dimensions` / `useWindowDimensions` / lib có sẵn).

---

## 10. ASSETS_AND_I18N

- Không thêm asset mà không đặt đúng folder + không import đúng cách.
- Ảnh: kiểm tra đã có `@2x / @3x` chưa; icon ưu tiên component/svg nếu project dùng.
- Nếu project có i18n (`i18next` / `react-i18next` / `react-intl`) → **không hardcode string UI**.
- Nếu project chưa có i18n → không tự thêm, **document lại để backlog**.
- `Colors / Strings / Metrics` constant — nếu có thì dùng, không tự đặt tên khác.

---

## 11. NATIVE_LAYER (iOS / Android)

- Không đụng native code (`ios/` `android/`) trừ khi task yêu cầu.
- Sau khi thêm/xóa native dependency → chạy `pod install` (iOS) và ghi lại thay đổi `Podfile.lock`.
- Không commit thay đổi native config (bundle id, signing, gradle) không nằm trong task.
- Expo: ưu tiên config qua `app.config` / plugin thay vì eject nếu không cần thiết.
- Ghi rõ nếu task yêu cầu bump native SDK / target version (breaking risk cao).

---

## 12. CODE_QUALITY_PRAGMATIC

- Chạy `yarn lint` (ESLint) + `tsc --noEmit` (nếu TS) trước khi commit → **zero error**.
- Giữ format theo **Prettier** config của project — không tự đổi rule.
- Không suppress lint (`// eslint-disable`) trừ khi có comment giải thích.
- Không để `console.log` trong production code — dùng logger nếu có sẵn.
- TODO phải có format: `// TODO(tên): mô tả` — không để TODO trống.

**Không bắt buộc ngay (đưa vào backlog):**

- 100% test coverage.
- Migrate JS → TS toàn bộ.
- Extract toàn bộ component thành file riêng.

---

## 13. MAINTAIN_DOCS

- Fix bug → ghi **root cause** trong commit / PR description.
- Thêm workaround → comment rõ: `// WORKAROUND: lý do (+ link issue nếu có)`.
- Breaking change khi update package / RN version → ghi changelog local.
- README phải có: setup, env vars, cách chạy iOS & Android, Expo/bare note, pod install.

**ADR (Architecture Decision Record)** — nếu có quyết định lớn:

- Ghi: `context / decision / consequences`.
- Đặt trong `docs/adr/` hoặc tương đương.

---

## Priority khi nhận project

| Priority | Action |
|---|---|
| **P0** | Audit: đọc package.json, xác định Expo/bare + pattern, build thử 2 platform |
| **P0** | Không thay đổi gì chưa có task |
| **P1** | Follow naming / folder / state / navigation convention hiện có |
| **P1** | Consistent styling + network layer |
| **P2** | Code quality: zero lint/type error, no console.log, no hardcode |
| **P3** | Chuẩn hóa dần qua backlog task |

---

## Checklist nhanh trước mỗi commit

- [ ] `yarn lint` + `tsc --noEmit` → zero error
- [ ] Không có `console.log` / lint-disable không giải thích
- [ ] Follow đúng naming + folder + state + navigation + styling của project
- [ ] Không refactor / update package / đụng native ngoài scope task
- [ ] Test trên **cả iOS và Android** (nếu thay đổi có ảnh hưởng UI/native)
- [ ] Commit message theo Conventional Commits
- [ ] PR chỉ 1 concern, có mô tả what/why/how-to-test
