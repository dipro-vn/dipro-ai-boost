---
name: sourcebase-knowledge-api-discovery
description: 
---

# API Discovery

**Category:** sourcebase-knowledge · **Status:** 🟢 Active

## When to use
Trước khi viết call API mới, để tìm service/endpoint đã tồn tại.

## Steps
1. Tìm tầng service: `services/`, `api/`, `lib/api`, client axios/fetch wrapper.
2. Grep theo resource (vd `user`, `order`) để tìm function đã gọi endpoint đó.
3. Đọc base URL, interceptor, cách inject token để tái dùng client chung.
4. Kiểm tra query/mutation hook (react-query) đã wrap sẵn service chưa.
5. Reuse function/hook có sẵn; chỉ thêm endpoint mới theo đúng pattern hiện tại.

## Template
```bash
# Tìm service layer & endpoint
rg "axios\.create|fetch\(|createApi" src
rg -i "get.*User|/users" src/services -A3
rg "useQuery|useMutation" src -l        # hook đã wrap API
```

## Example
**Good:** Dùng lại `userService.getById()` + `useUserQuery` có sẵn thay vì gọi axios trực tiếp.
**Avoid:** `fetch('/api/users')` raw trong component, bỏ qua client + interceptor chung.

## Checklist
- [ ] Đã xác định tầng service & API client chung
- [ ] Đã grep endpoint theo resource trước khi tạo mới
- [ ] Reuse client + interceptor (token, baseURL) sẵn có
- [ ] Endpoint mới theo đúng pattern service hiện tại
