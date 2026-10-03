# O7 — Bug list hiện trạng (tuỳ chọn)

> **Yêu cầu:** file xlsx · **chỉ lấy bug của MÀN HÌNH** phát hiện khi dùng Playwright quét website hiện tại — **không** lấy bug của API / code khi quét source · **chỉ mức nghiêm trọng URGENT / HIGH** — để nắm sản phẩm đang tồn đọng gì trước khi nhận maintain.
>
> Thành phẩm: `07_BugList/BugList_<sys>_ver<N>.xlsx`. Chỉ chạy khi P9 = Có. Tài liệu có thể đi ra ngoài công ty → ngưỡng bằng chứng cao nhất trong kit.

---

## 0. Phạm vi — cái gì vào, cái gì không

| ✅ Vào bug list | ❌ Không vào (ghi `Observations` nội bộ nếu đáng điều tra) |
|---|---|
| Lỗi **nhìn thấy trên màn** khi Playwright mở trang: trang lỗi / trắng, ảnh hỏng, layout vỡ / tràn che nút, JS error làm hỏng chức năng trên màn, request của **chính trang đó** trả 4xx/5xx khiến màn không hiển thị đúng, link menu chết, tải quá chậm | Lỗi đọc ra từ **source code / API handler** (thiếu `return`, sai SQL, tham số không validate…) mà chưa thấy trên màn |
| Mức **Urgent** hoặc **High** | Lỗi dữ liệu / toàn vẹn DB · nghi vấn bảo mật (không khai thác, không PoC) · mức Medium / Low |

Ứng viên từ code vẫn có giá trị cho maintain → đưa vào `Observations` (nội bộ) hoặc Open Question, **không** gọi là bug.

## 1. Phát hiện — chỉ thứ đo được trên màn

| Nhóm | Đo bằng | Nguồn |
|---|---|---|
| **Giao diện** | ảnh hỏng · tràn ngang ở viewport chuẩn | `recon/crawl/<WEB>/ui-issues.json` |
| **JS error trên trang** | console listener khi mở trang | `console.json` |
| **Trang / request lỗi** | HTTP ≥ 400 của trang hoặc request của trang | `network.json` · `pages.json.errorPage` |
| **Link chết** | crawl | `network.json` |
| **Hiệu năng** | thời gian tải > 5 s ở màn chính | `pages.json.loadMs` |
| **Validation thiếu** | submit rỗng / vượt maxlength — *chỉ khi P3 cho submit* | thao tác trên màn |

Ứng viên tự động **chưa phải bug**. Mỗi ứng viên phải: (1) tái hiện trên màn `n` lần → `Yes — n/n`; (2) gắn `EV-xxxx` loại **screenshot / console-log / har**; (3) 1 câu tác động nghiệp vụ.

## 2. Mức độ — chỉ ghi Urgent / High

| Severity | Nghĩa | Ví dụ |
|---|---|---|
| **Urgent** | Màn chính không dùng được · luồng nghiệp vụ chính bị chặn · lỗi 5xx / trang trắng · nguy cơ mất dữ liệu người dùng thấy được | Bấm "Đăng nhập" ra trang lỗi 500 · màn danh sách trắng vì JS error |
| **High** | Chức năng trên màn sai / thiếu nhưng còn đường vòng · lỗi giao diện làm khó thao tác rõ rệt | Nút "Lưu" bị che bởi layout tràn · link menu chính dẫn tới 404 · ảnh sản phẩm hỏng trên màn chính |
| ~~Medium / Low~~ | Lệch nhỏ, chính tả, màu, vài px | **không ghi** — gate V8 chặn |

Chọn theo **tác động nghiệp vụ**, không theo độ khó sửa. Phân vân High / Medium → không ghi, đưa `Observations`.

## 3. Cấu trúc

`build-inventory.py --bug-list --out $V/07_BugList/BugList_<sys>_ver<N>.xlsx`:

| Sheet | Nội dung | Gửi KH? |
|---|---|---|
| `00_Meta` | như inventory + `bug_scan_scope` (= `Playwright — màn hình`), `bug_recipient` (P9) | — |
| `Bugs` | bug đã tái hiện trên màn | ✅ |
| `Suspected` | thấy trên màn nhưng chưa tái hiện ổn định | ❌ nội bộ |
| `Observations` | nghi vấn từ code / API / DB / bảo mật | ❌ nội bộ |

Cột `Bugs`: `Bug ID` · `Title` · `Screen / Module` (**`SC-` bắt buộc** — bug gắn với màn) · `URL / Route` (URL **màn**, không phải `/api/…`) · `Category` (Functional · UI/Layout · Performance · Compatibility) · `Severity` (**Urgent / High**) · `Repro Steps` (≥ 2 bước trên màn) · `Expected` · `Actual` · `Evidence` (≥ 1 EV screenshot / console-log / har) · `Reproduced` · `Detected By` (`Playwright`) · `Business Impact` · `Env` · `Pre-existing` · `Report To Customer` · `Status` · `Note`.

```bash
python3 $S/verify-bug-list.py $V/07_BugList/BugList_<sys>_ver<N>.xlsx --inventory $I/inventory.xlsx --out $I/gates/v8.md
```

Gate V8 chặn: mức ngoài Urgent / High · Category Data / Security · URL là API · không có evidence màn hình (chỉ code-ref) · `Screen / Module` không phải `SC-` có thật · thiếu bước tái hiện · bug chưa tái hiện lọt sheet gửi khách · trùng lặp.

`bug_recipient = Nội bộ review trước` → báo xong nhưng ghi rõ **chưa gửi KH, chờ người duyệt**.

## 4. Ranh giới

| Không phải bug | Là |
|---|---|
| `UNKNOWN` ở O1 (chưa quan sát được) | Thiếu bằng chứng, không phải hỏng |
| Lỗi đọc từ code / API chưa thấy trên màn | `Observations` hoặc Open Question |
| Hành vi lạ nhưng không biết spec | `Observations` |
