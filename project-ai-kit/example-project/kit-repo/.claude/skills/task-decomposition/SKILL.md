---
name: task-decomposition
description: Methodology phân rã DESIGN.md thành task files atomic — INVEST criteria, dependency detection, parallelism rules, estimation heuristics cho NestJS/React/Flutter. Dùng khi techlead-tasks-agent cần quyết định cắt task ở đâu và estimate bao nhiêu giờ.
metadata:
  tags: task-decomposition, agile, story-splitting, estimation
---

# Task Decomposition

> Áp dụng cho: `techlead-tasks-agent` khi phân rã DESIGN.md → task files

---

## Khi nào dùng skill này

- Quyết định cắt 1 feature thành bao nhiêu tasks
- Detect dependency ẩn giữa các tasks
- Quyết định tasks nào chạy song song vs sequential
- Estimate giờ cho từng task NestJS / React / Flutter

---

## 1. INVEST Criteria — Kiểm tra mỗi task trước khi tạo

Mỗi task phải pass đủ 6 tiêu chí:

| Tiêu chí | Câu hỏi kiểm tra | Fail → hành động |
|---|---|---|
| **I**ndependent | Task này có thể implement mà không cần task khác chưa merge? | Split hoặc reorder |
| **N**egotiable | Scope có thể điều chỉnh nếu phát sinh vấn đề? | Ghi "Không được làm" rõ ràng |
| **V**aluable | Task này deliver giá trị gì (dù nhỏ)? | Merge vào task khác nếu không có giá trị độc lập |
| **E**stimable | Có thể ước lượng giờ trong khoảng ±50%? | Break nhỏ hơn nếu không estimate được |
| **S**mall | ≤ 8h thực hiện? | Split thành 2+ tasks nếu > 8h |
| **T**estable | Có thể viết unit test verify behavior? | Thiếu unit test = task chưa đủ spec |

---

## 2. Phân rã theo Phase (repo lấy từ bảng Ecosystem trong `AGENTS.md`)

Thứ tự bắt buộc — không được đảo:

```
Phase 1 — DB / Migration (repo vai trò `backend`)
  └─ Tạo entity + migration file
  └─ KHÔNG viết service logic ở phase này

Phase 2 — Service + API (repo vai trò `backend`)
  ├─ task-2-1: Service methods + business logic + unit test
  └─ task-2-2: Controller + DTO + endpoint (có thể song song với 2-1 nếu interface đã lock)

Phase 3 — UI (song song nhau)
  ├─ task-3-x: React component / page (repo frontend)
  └─ task-3-y: Flutter screen / provider (repo mobile)

Phase 4 — Integration
  └─ task-4-1: E2E verify + smoke test toàn luồng
```

**Rule:** Phase sau chỉ bắt đầu khi Phase trước PASS. Phase 3 FE + Mobile được phép chạy song song nhau.

---

## 3. Dấu hiệu task cần Split

```
❌ Cần split khi:
- Estimate > 8h
- Task chạm > 3 files lớn không liên quan (service + entity + controller + 2 DTO cùng lúc)
- Task vừa tạo DB vừa viết API logic (luôn tách Phase 1 và Phase 2)
- Task FE vừa tạo component vừa tạo API service call + store (tách UI vs data layer)
- "Implement module X" không có file path cụ thể → chưa đủ spec

✅ Không cần split khi:
- Controller + DTO cùng 1 endpoint (cohesive, < 4h)
- Entity + migration của cùng 1 table (atomic DB change)
- React component + local hook của component đó (not shared hook)
```

---

## 4. Dependency Detection — Các pattern ẩn thường gặp

### Pattern 1: Shared Entity
```
task-2-1 tạo OrderEntity  →  task-2-2 dùng OrderEntity
→ task-2-2 depends on task-2-1, KHÔNG song song được
```

### Pattern 2: Shared Interface / DTO
```
task-2-1 định nghĩa CreateOrderDto  →  task-3-1 (FE) gọi API dùng DTO đó
→ Contract Lock bắt buộc trước Phase 3
→ task-3-1 chỉ bắt đầu sau khi task-2-2 merge
```

### Pattern 3: Shared Redis Key
```
task-2-1 set cache key `menu:company:{id}`
task-2-3 invalidate cùng key đó
→ Ghi rõ key pattern trong cả 2 task, không để mỗi task tự define
```

### Pattern 4: Shared Service Method
```
task-2-2 inject MenuService
task-2-3 inject MenuService (để add method mới)
→ Nếu cùng modify MenuService → SEQUENTIAL, không song song
→ Nếu chỉ read MenuService → song song OK
```

---

## 5. Parallelism Rules

| Tổ hợp | Song song? | Lý do |
|---|---|---|
| Phase 3 FE (React) + Phase 3 Mobile (Flutter) | ✅ | Khác repo, chỉ cần contract lock |
| task-2-1 Service + task-2-2 Controller | ✅ nếu interface lock | Controller chỉ gọi service, không modify |
| task-2-1 (tạo entity) + task-2-2 (dùng entity) | ❌ | Entity phải tồn tại trước |
| task-3-1 FE + task-2-2 API | ❌ | FE cần API hoạt động để test |
| Nhiều task cùng sửa 1 service file | ❌ | Merge conflict, regression risk |

---

## 6. Estimation Heuristics (ví dụ)

> Đây là baseline. Tăng 50% nếu: task cross nhiều entity phức tạp, cần debug DB, hoặc có edge case payment.

### NestJS (repo vai trò `backend`)

| Loại task | Estimate |
|---|---|
| Migration (thêm column / index) | 1h |
| Migration (tạo table mới) | 2h |
| Service method đơn giản (CRUD) | 2h |
| Service method có business logic + cache | 3–4h |
| Controller + DTO (1 endpoint) | 2h |
| Controller + DTO (CRUD 5 endpoints) | 4h |
| Guard / Interceptor mới | 2–3h |
| Unit test cho service (~80% coverage) | 1–2h (nếu viết song song với code) |
| Unit test retro (code đã có) | 2–3h |

### React (repo vai trò `frontend`)

| Loại task | Estimate |
|---|---|
| Page mới (list + filter + pagination) | 5–6h |
| Page mới (form create/edit) | 4–5h |
| Shared component đơn giản (< 100 lines) | 2h |
| Shared component phức tạp (table, modal, multi-step) | 4–5h |
| Hook + API service call + store integration | 3h |
| Redux slice mới | 2h |

### Flutter (repo vai trò `mobile`)

| Loại task | Estimate |
|---|---|
| Screen mới (list + API call) | 4–5h |
| Screen mới (form + validation) | 4–5h |
| Provider / StateNotifier mới | 3h |
| Socket.IO event mới + UI update | 3–4h |
| Retrofit API method + model freezed | 2h |
| Payment flow (payment SDK integration) | 5–6h |

---

## 7. Checklist trước khi finalize task list

- [ ] Mỗi task ≤ 8h?
- [ ] Mỗi task có file path cụ thể (không phải "implement module X")?
- [ ] Phase 1 tách khỏi Phase 2?
- [ ] Dependency được ghi rõ trong `Depends on` field?
- [ ] Song song được ghi rõ trong `Song song với` field?
- [ ] Contract Lock được confirm trước Phase 3?
- [ ] Mọi task code mới đều có Unit Tests section?
- [ ] Non-Regression table đã điền từ `tilth_deps` output?

---

## Anti-Patterns

- ❌ Task "Implement full order module" — quá rộng, phải break down
- ❌ Phase 2 task tạo entity trong migration — entity và migration thuộc Phase 1
- ❌ Estimate "1–2 ngày" — phải quy về giờ cụ thể
- ❌ Song song 2 tasks cùng modify 1 service file
- ❌ FE task không có contract lock với BE — dẫn đến làm lại khi API thay đổi
- ❌ Bỏ qua Non-Regression table — regression bug phổ biến nhất trong dự án
