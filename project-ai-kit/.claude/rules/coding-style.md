# Coding Style

## Chung (tất cả repo)

- **Tối giản**: Không thêm feature ngoài yêu cầu. Không abstract sớm khi chưa có 3+ use case
- **Nhất quán**: Ưu tiên follow pattern đang có trong codebase — không tự refactor phạm vi ngoài task
- **Đặt tên rõ nghĩa**: Mỗi function/method làm 1 việc, tên nói lên đó là việc gì
- **Không dead code**: Không comment-out code, không unused import, không unused variable
- **Không comment mô tả WHAT**: Chỉ comment khi WHY là non-obvious (constraint ẩn, workaround bug cụ thể)

## Match existing style khi surgical change (BẮT BUỘC)

> **Test:** mỗi dòng thay đổi trong diff phải trace trực tiếp về yêu cầu của task. Nếu không → revert dòng đó.

Khi edit code có sẵn (bug fix / add nhỏ / feature mở rộng), **KHÔNG được**:

- Đổi quote style (`'` ↔ `"`) nếu file gốc dùng consistent 1 kiểu
- Thêm type hints / annotations / return type nếu function xung quanh không có
- Reformat whitespace, indent, line break ngoài dòng đang sửa
- Thêm docstring / JSDoc / TSDoc nếu function xung quanh không có
- Đổi return pattern có sẵn (ví dụ `if x: return True else: return False` → `return x`)
- "Cải thiện" validation / error handling ngoài phần bug đang fix
- Thêm optional parameter / flag "cho linh hoạt" mà task không yêu cầu

Style mismatch của codebase là **task riêng** (refactor task, cleanup PR) — không kèm vào PR khác. Nếu bạn phát hiện style drift trong code cũ, **note trong output** để user quyết định tạo task riêng, không tự sửa.

**Ví dụ vi phạm điển hình** (task: "Add logging to upload function"):

```diff
- def upload_file(file_path, destination):
+ def upload_file(file_path: str, destination: str) -> bool:   ← thêm type hints
+     """Upload file to destination with logging."""            ← thêm docstring
+     logger.info(f"Uploading {file_path}")
      try:
-         with open(file_path, 'rb') as f:
+         with open(file_path, "rb") as f:                       ← đổi quote style
```

**Đúng scope:**

```diff
+ import logging
+ logger = logging.getLogger(__name__)
+
  def upload_file(file_path, destination):
+     logger.info(f'Starting upload: {file_path}')
      try:
          with open(file_path, 'rb') as f:                        ← giữ nguyên quote
```

## Test-first cho bug fix task (BẮT BUỘC)

> **Nguyên tắc:** không có test chứng minh bug tồn tại → không có bằng chứng bug đã fix. QA agent verify dựa trên test — không có test = không verify được.

Khi Dev agent nhận task type = **bug fix**, tuân thủ 3 bước:

1. **Viết test reproducing bug trước** → verify test **FAIL** (chứng minh bug tồn tại)
2. **Implement fix** → verify test **PASS**
3. **Run test suite non-regression** → verify không có test cũ nào FAIL

Đặt test ở đúng layer bug xảy ra (unit test cho service logic, integration test cho endpoint, widget test cho Flutter UI). Test name phải mô tả rõ input state gây bug — ví dụ `should_return_stable_order_when_scores_are_duplicate()`.

**Ví dụ áp dụng:**

Task: "Fix: sort scores broken khi có 2+ record cùng score"

```typescript
// Bước 1 — Test reproducing (verify FAIL trước fix)
it('should sort deterministically when scores are duplicate', () => {
  const input = [
    { name: 'Alice', score: 100 },
    { name: 'Bob', score: 100 },
    { name: 'Charlie', score: 90 },
  ];
  const result = sortScores(input);
  expect(result[0].score).toBe(100);
  expect(result[1].score).toBe(100);
  expect(result[2].score).toBe(90);
  // Chạy 10 lần — trước fix: order Alice/Bob không ổn định → test FAIL
});

// Bước 2 — Fix (add tiebreaker) → verify test PASS
function sortScores(scores) {
  return [...scores].sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
}

// Bước 3 — Run suite → verify không test cũ nào broken
```

**Escape hatch — micro-bug không cần test:**

Nếu bug thuộc 1 trong các loại sau, được skip Bước 1 nhưng **PHẢI ghi lý do vào output task**:

- Lỗi chính tả (typo trong string literal, tên biến sai)
- Lỗi format (missing semicolon, thừa dấu phẩy, indent sai)
- Đổi hằng số hiển nhiên (`MAX_RETRY = 3` → `MAX_RETRY = 5` theo yêu cầu)
- Đổi text UI / label / message hiển thị

Ghi trong output theo format:
```
Test-first: SKIPPED (loại micro-bug: <typo/format/constant/text>)
Lý do: <mô tả 1 dòng>
```

Không được skip khi bug thuộc business logic, edge case, race condition, data integrity, security — dù nhìn "đơn giản".

## NestJS (repo vai trò backend)

```typescript
// ✅ Column: snake_case explicit name
@Column({ name: 'company_code', length: 50 })
companyCode: string;

// ✅ Relation: eager: false để tránh N+1
@ManyToOne(() => CompanyEntity, { eager: false })
@JoinColumn({ name: 'company_id' })
company: CompanyEntity;

// ✅ orderBy whitelist — đã có bug prod từ việc này
const ORDER_BY_MAP = { createdAt: 'order.createdAt', status: 'order.status' };
.orderBy(ORDER_BY_MAP[dto.orderBy] ?? 'order.createdAt', 'DESC')
```

## React (repo vai trò frontend)

```tsx
// ✅ Named export + Props interface
interface OrderCardProps { orderId: string; }
export const OrderCard: React.FC<OrderCardProps> = ({ orderId }) => { ... };

// ✅ TanStack Query v5 — object syntax BẮT BUỘC
const { data } = useQuery({ queryKey: ['orders', id], queryFn: () => api.get(id) });

// ❌ v4 positional syntax — sai
const { data } = useQuery(['orders'], () => api.get()); // KHÔNG dùng
```

## Flutter (repo vai trò mobile)

```dart
// ✅ Riverpod — StateNotifierProvider
// ✅ Sizing dùng flutter_screenutil
Container(width: 100.w, height: 50.h) // KHÔNG hard-code pixel

// ✅ const constructor khi widget không đổi
const Text('Hello') // tiết kiệm rebuild
```
