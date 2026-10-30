# Phân loại nguồn + luật RE1–RE4

> Áp dụng ở **Bước 0 (Intake)**, trước khi phân tích nội dung của bất kỳ file nào.
> Gán nhầm loại nguồn → sai classification → hallucination lan xuống mọi output.

---

## Thứ tự ĐỌC nguồn — code trước, website sau (Bước 4)

Đọc khác với ưu tiên khi mâu thuẫn (mục dưới). Đọc theo "reverse knowledge": cái bền + máy làm được trước, cái dễ đổi + đắt sau.

| Pha | Nguồn | Lấy gì | Script |
|---|---|---|---|
| **A — Code** (luôn chạy khi có source) | 1. Cấu trúc repo · 2. DB: model / entity + **toàn bộ** migration (Prisma, TypeORM, SQL) · 3. API, auth, batch · 4. FE: route → page → hàm gọi API → endpoint · 5. Quyền: guard / decorator / so sánh role | Danh sách đủ (không phụ thuộc crawl vào được hay không), quan hệ màn → API → bảng → cột, code-ref tới dòng, commit hash | `read-orm-schema.py` (DB — nguồn DUY NHẤT, feedback 30/10/2026) · `scan-repo.py` |
| **B — Website** (Playwright) | Màn đang chạy, seed từ route FE của Pha A | Chỉ cái code không cho biết: màn nào thật sự sống · role thấy gì · giao diện · lỗi khi thao tác | `login-site.js` · `crawl-site.js --seed-file` |

- Pha A xong hết mới bắt đầu Pha B. Reconcile (Bước 5) chỉ chạy khi **cả hai pha** đã nạp inventory.
- Màn → API lấy từ đồ thị gọi `fe-api-calls.csv` (mỗi cạnh `static` / `inferred`), **không** từ import graph theo file (ver3 gán API-185 cho 11 màn, có màn admin sai).
- DB: bảng / cột trong model, entity, migration là **nguồn duy nhất** của O3 — gate V-DB check 10 FAIL nếu thiếu. User không cung cấp dump / kết nối DB (feedback 30/10/2026). Không có ORM / migration → `db_mode=NONE`, O3 ⬜.
- Dự án **không giao source** → chế độ "chỉ website" (Pha B như cũ), ghi rõ trong Discovery Brief.

---

## Thứ tự ưu tiên khi mâu thuẫn (AS-IS)

```
Running Website  >  Source Code  >  Database  >  File khách hàng
```

> ⚠️ **Đảo ngược so với kit `requirement-to-flow`.** Ở chiều forward, tài liệu đã duyệt thắng. Ở chiều ngược, **cái đang chạy là sự thật**; tài liệu chỉ là ý định của ai đó tại một thời điểm.

Thứ tự này **chỉ quyết định giá trị nào ghi tạm vào inventory**. Mọi mâu thuẫn vẫn phải:
1. Sinh 1 dòng `06_OpenQuestions` với `Type = CONFLICT`
2. Đặt `01_Function.Status = CONFLICT`
3. Chờ BrSE quyết — **không tự resolve im lặng**

---

## RE1 — Running Website

| Lấy được | ⛔ CẤM suy ra |
|---|---|
| Màn hình tồn tại, URL, tên hiển thị thật | Business rule không quan sát được |
| Item nhìn thấy trên DOM, thứ tự, label | Hành vi của role chưa đăng nhập thử |
| Navigation **đã bấm qua** | Nhánh chưa bấm ("chắc nút này sang màn kia") |
| Validation **đã kích hoạt thử** | maxlength / required khi chưa thử nhập |

**Evidence bắt buộc:** `screenshot` + `Captured At` + `Actor/Role`.
**Role thiếu tài khoản** → mọi chức năng của role đó = `To verify`, **không** đoán theo tên menu.

---

## RE2 — Source Code

| Lấy được | ⛔ CẤM suy ra |
|---|---|
| Route, model, job/cron, integration | Dead code / code đã comment-out là rule đang chạy |
| Validation **đọc được trong code** | Hành vi phụ thuộc config môi trường không đọc được |
| Tên bảng/cột được truy cập | Feature flag đang bật hay tắt trên production |

**Evidence bắt buộc:** `code-ref` dạng `REPO-01:path/file.ts#L88-L104` (tiền tố repo bắt buộc) — **phải chính xác tới dòng**.

Route đọc được từ code nhưng **chưa quan sát trên UI** → `Status = To verify` + 1 dòng Open Question. Đây là lỗi phổ biến nhất của agent ở kit này.

---

## RE3 — Database (optional)

| Lấy được | ⛔ CẤM suy ra |
|---|---|
| Bảng, cột, kiểu, PK/FK, index, constraint | **Ý nghĩa nghiệp vụ của cột chỉ từ tên cột** |
| Quan hệ có FK vật lý | Quan hệ không có FK (phải có code chứng minh) |
| Số dòng ước lượng | Bảng nào còn dùng, bảng nào đã chết |

**Luật `Meaning`:** chỉ `Confidence = High` khi `Evidence` chứa ≥ 1 EV loại `code-ref` chứng minh có code đọc/ghi cột đó.
**Quan hệ logic không có FK** → ghi ở `03_DB_Tables.Note`: `logical FK: orders.user_id → users.id — inferred from EV-0102`. **Không** điền vào cột `FK`.

---

## RE4 — File khách hàng cung cấp

| Lấy được | ⛔ CẤM suy ra |
|---|---|
| Rule / validation / transition **được viết explicit** | Quan hệ mà tài liệu không mô tả |
| Thuật ngữ nghiệp vụ, tên actor | "Điền vào chỗ trống cho nhất quán" |

**Evidence locator bắt buộc:** `<tên file> § <section> (p.<trang>)`.

⚠️ **Tài liệu lệch với hệ thống thật = `CONFLICT`**, không phải "tài liệu cũ nên bỏ qua". Khách hàng có thể đang tin vào tài liệu đó.

---

## Bảng gán loại — in vào Discovery Brief

| File / nguồn | Loại đã gán | Rule | Dùng để lấy |
|---|---|---|---|
| *(1 dòng / 1 nguồn)* | Running Website / Source Code / Database / File KH | RE1–RE4 | ... |

In bảng này ra để **user sửa nếu agent gán nhầm**. Nguồn không gán được loại → không dùng làm input cho inventory.
