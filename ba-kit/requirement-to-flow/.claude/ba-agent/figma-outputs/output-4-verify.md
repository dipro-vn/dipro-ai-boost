# Ba Agent — Output 4 Quality Gate (Playwright)

> Gate bắt buộc chạy **sau khi tạo xong `prototype/index.html`, trước khi báo Output 4 ✅ Done**.
> Thay thế hoàn toàn cách cũ "BA tự test manual rồi gõ bảng PASS/FAIL" — bảng gõ tay
> không phải bằng chứng, và thực tế đã từng bỏ lọt prototype không bấm được.

---

## 0. Vì sao cần gate này

Bản prototype đầu tiên của dự án CarePro đạt **130/130 màn**, sinh 100% tự động từ SPEC,
0 link gãy — và vẫn **không dùng được**: nó là tài liệu HTML cuộn dọc, không phải website.
Các phép đếm (đủ màn / đủ item / đủ error) đều PASS nhưng không phép nào hỏi
*"bấm vào có chạy không?"*.

Gate này hỏi đúng câu đó, bằng trình duyệt thật.

**4 lớp lỗi gate đã bắt được trong thực tế:**

| Lỗi | Vì sao đếm tay không thấy |
|---|---|
| Nút *Về trang chủ* trỏ mã màn **không tồn tại** (`OP_DASH_001`) | Mã đúng format `XX_YYYY_NNN` nên mọi regex đều thấy hợp lệ |
| **Không đăng nhập được** vào 1 trong 2 website | Cột Action ghi đích bằng lời ("màn mặc định theo role"), không mã |
| 5 màn **cụt đường** (ẩn sidebar + không lối ra) | Từng màn nhìn riêng đều ổn; chỉ lộ ra khi duyệt đồ thị |
| Prototype là **tài liệu cuộn** chứ không phải website | Mọi phép đếm nội dung đều PASS |

---

## 1. Prototype Contract (BẮT BUỘC)

Prototype PHẢI expose 1 API nhỏ trên `window` để verify được. **Không có contract →
gate FAIL → không được approve.** Đây không phải tuỳ chọn: prototype không kiểm được
thì không có cơ sở để báo Done.

```js
// Bắt buộc
window.__PROTO__ = {
  screens: {
    "CF_AUTH_001": {
      name:  "Đăng nhập",
      ty:    "Form",                    // Form · List · Detail · Modal · Full screen …
      unk:   false,                     // true = màn còn UNKNOWN/INFERENCE (Rule P2)
      errs:  [                          // đúng thứ tự bảng Non-Happy trong SPEC
        ["E-001", "Validation", "Bỏ trống ID", "Inline error", "Vui lòng nhập ID pháp nhân"]
        //  id      nhóm          trigger        hiển thị        message
      ]
    }
  }
};

window.go = function (code, opts) { /* chuyển tới màn `code`; opts.asPage = ép mở dạng trang */ };
window.fireErr = function (code, i) { /* bắn error thứ i của màn `code` */ };
```

**Quy ước DOM đi kèm:**

| Thứ | Quy ước | Dùng để |
|---|---|---|
| Container màn | `<section class="scr" id="scr-<CODE>">` | định vị màn |
| Màn đang mở | thêm class `.on` | kiểm "chỉ 1 màn hiển thị" |
| Phần tử điều hướng | `data-go="<CODE>"` | click thật + dựng đồ thị |
| Menu chính | `<nav class="appnav"><a data-go="…">` | điểm vào khi BFS |
| Overlay | `.scrim` hoặc `[role=dialog]` | nhận diện modal |
| Toast | `.toast` | nhận diện toast |
| Banner trong màn | `.pagebanner` | nhận diện banner |

`window.__SPEC__` được chấp nhận như tên cũ của `__PROTO__`.

---

## 2. Chạy gate

```bash
node .claude/skills/business-analyst/scripts/verify-prototype.js \
     <output-folder>/prototype/index.html \
     --out  <output-folder>/prototype/test-report.md \
     --json <output-folder>/prototype/test-report.json \
     --shots <output-folder>/prototype/shots
```

Chuẩn bị 1 lần:
```bash
npm i -D playwright && npx playwright install chromium
```
Máy đã có Chrome/Edge thì script tự dùng, không cần tải browser.

**Exit code là kết quả gate:** `0` = PASS · `1` = có FAIL · `2` = lỗi cấu hình.

---

## 3. Gate kiểm những gì

| Nhóm | Phép kiểm | Ngưỡng |
|---|---|---|
| `STATIC` | Không tài nguyên ngoài · dung lượng · có `<title>` · **có Prototype Contract** | FAIL nếu thiếu |
| `SHAPE` | **Chỉ 1 màn hiển thị cùng lúc** · có `data-go` · có input + button | FAIL nếu là tài liệu cuộn |
| `NAV` | Click thật **từng** phần tử `data-go`, assert đúng màn đích | FAIL = 0 |
| `REACH` | Không màn cụt đường · không màn không tới được (BFS từ menu) · không mã gãy | FAIL = 0 |
| `ERR` | Bắn thật **từng** error, assert có hiển thị đúng loại | FAIL = 0 |
| `P2` | Màn `unk: true` phải hiện placeholder `⚠ UNKNOWN BEHAVIOR — chờ BRSE confirm` | FAIL = 0 |
| `RESP` | Không cuộn ngang ở 1440 · 1024 · 375 px | FAIL = 0 |
| `RUNTIME` | 0 lỗi JS · 0 `console.error` · 0 request ra ngoài | FAIL = 0 |

---

## 4. Điều kiện Approve

```
❌ FAIL  = 0    ← BẮT BUỘC. Còn 1 FAIL là không được báo Output 4 Done.
⚠ SKIPPED      ← chỉ được phép cho màn UNKNOWN/INFERENCE (Rule P2)
```

FAIL → **sửa prototype rồi chạy lại**, không được ghi chú "sẽ sửa sau".
Nếu FAIL do SPEC thiếu (VD nhánh Transition không có mã màn đích) → sửa SPEC trước
theo Scoped Update `POLICIES.md §4.6`, rồi sinh lại prototype.

---

## 5. Đưa kết quả vào tài liệu

1. **`prototype/index.html`** — chèn `test-report.md` dạng HTML comment ở cuối file.
2. **`SPEC.md` → `## BA Deliverables`** — dưới row Output 4, chèn khối summary + bảng
   Happy Path. KHÔNG dán cả nghìn dòng error vào SPEC; để trong comment HTML và dẫn link.
3. Row Output 4 phải ghi con số thật: `1380 PASS · 0 FAIL · 41 SKIPPED`.

**Nếu build prototype bằng script:** gate phải chạy **sau** bước sinh file, vì bước sinh
sẽ ghi đè `index.html` và xoá mất comment report. Thứ tự đúng:

```
sinh prototype → chạy gate → chèn report vào HTML + SPEC
```

---

## 6. Anti-pattern

- ❌ Gõ tay bảng Interaction Test Report rồi ghi `✅ PASS` — không có bằng chứng
- ❌ Báo Output 4 Done khi gate chưa chạy, hoặc chạy mà còn FAIL
- ❌ Bỏ Prototype Contract cho "đỡ rườm rà" → gate không kiểm được → tự động FAIL
- ❌ Hạ ngưỡng gate để cho qua (sửa script thay vì sửa prototype)
- ❌ Đánh `SKIPPED` cho error bình thường để né FAIL — `SKIPPED` chỉ dành cho màn UNKNOWN
- ❌ Chạy gate trước bước sinh file rồi báo cáo số cũ
