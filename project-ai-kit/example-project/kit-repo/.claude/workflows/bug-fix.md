# Workflow: Bug Fix

Quy trình điều tra và fix bug — từ report đến verified.

---

## Tổng quan

```
Bug report (Backlog issue)
        │
        ▼
  Reproduce bug
        │
        ▼
  Root cause (tilth_search)
        │
        ▼
  Fix implementation
        │
        ▼
  Non-regression verify
        │
        ▼
  QA sign-off → Resolved
```

---

## Bước 1 — Phân loại bug

Xác định trước khi bắt đầu:

| Câu hỏi | Trả lời cần có |
|---|---|
| Bug xảy ra ở env nào? | DEV / STG / PROD |
| Repo liên quan? | xem bảng Ecosystem trong `AGENTS.md` |
| Severity? | Critical (PROD down) / Major / Minor |
| Có thể reproduce không? | Steps to reproduce cụ thể |

**Env PROD / Critical** → report ngay cho PM trước khi fix.

---

## Bước 2 — Reproduce

Chạy lại bug với steps cụ thể. Ghi lại:
- Input gây ra bug
- Expected behavior (theo SPEC.md nếu có)
- Actual behavior
- Error message / stack trace

---

## Bước 3 — Tìm root cause

**Agent theo vai trò repo:** `backend-agent` / `frontend-agent` / `mobile-agent`

```bash
# Tìm điểm bắt đầu của lỗi
tilth_search(query: "<function/component/service tên trong stack trace>")

# Đọc file liên quan
tilth_read(paths: ["<file bị nghi ngờ>"])

# Kiểm tra blast radius nếu sửa method public
tilth_deps(path: "<file sẽ thay đổi>")
```

**Kiểm tra DB nếu cần (backend):**
- Hỏi Lead/DevOps để lấy hướng dẫn kết nối DB DEV/Staging của dự án.

---

## Bước 4 — Fix

**Nguyên tắc fix bug:**
- Fix **đúng root cause** — không patch symptom
- Scope tối thiểu — không refactor code lân cận
- Không thêm feature mới vào bug fix PR

**Checklist trước khi commit (theo repo):**

*NestJS:*
- [ ] Migration có `up()` + `down()` nếu sửa schema?
- [ ] Redis cache invalidate nếu data thay đổi?
- [ ] Không N+1 query mới?
- [ ] Exception đúng HTTP status?

*React:*
- [ ] TanStack Query v5 object syntax?
- [ ] `queryKey` đủ dependencies?
- [ ] Không `as any`?

*Flutter:*
- [ ] Socket cleanup trong dispose?
- [ ] `@freezed` rebuild nếu sửa model?

---

## Bước 5 — Viết / cập nhật test

- Viết test case cover đúng scenario gây ra bug
- Đảm bảo test **fail trước khi fix** và **pass sau khi fix**

```bash
# NestJS
npm run test -- --testPathPattern="<file>.spec.ts" --verbose

# Flutter
flutter test test/<file>_test.dart
```

---

## Bước 6 — Non-Regression

Dùng `tilth_deps` để biết những file nào gọi đến code vừa sửa:

```bash
tilth_deps(path: "<file đã fix>")
```

Với mỗi caller → verify tính năng vẫn hoạt động đúng.

---

## Bước 7 — Memory Update Gate

```
Sửa API endpoint / response?
  └─ YES → cập nhật api-catalog.md

Sửa entity / column?
  └─ YES → cập nhật erd.md

Phát hiện pattern bug mới (ví dụ: orderBy injection)?
  └─ YES → ghi chú vào patterns.md hoặc coding-style.md

Không có gì thay đổi ở trên?
  └─ Bỏ qua
```

---

## Bước 8 — QA Verify

**Agent:** `qa-agent`

- Chạy lại steps to reproduce → confirm đã fix
- Chạy test suite → confirm test pass
- Verify non-regression

**Status update:**
```
Dev: Request Review
Leader: In Review → Testing Request
QA: Testing Request → Resolved
PM/Leader: Resolved → Closed
```

---

## Output template khi báo done

```
## Bug Fix — [Issue ID] | [Repo]

Root cause: [mô tả ngắn gọn nguyên nhân]

Files đã thay đổi:
  - <path> → [mô tả thay đổi]

Test:
  - ✅ Test case mới: [tên test]
  - ✅ Regression: [N tính năng đã verify]

Memory Update Gate:
  - [✅ / skipped] api-catalog / erd / patterns

Reproduce sau fix: ❌ Không còn reproduce được
```
