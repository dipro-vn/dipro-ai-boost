# O7 — Bug list hiện trạng (tuỳ chọn)

> **Yêu cầu:** file xlsx · trong lúc Playwright quét website hiện tại → thống kê **bug giao diện / chức năng mức MEDIUM – HIGH** để nắm sản phẩm đang **tồn đọng gì** trước khi mình nhận maintain.
>
> Thành phẩm: `07_BugList/BugList_<sys>_ver<N>.xlsx`. Chỉ chạy khi P9 = Có. Tài liệu có thể đi ra ngoài công ty → ngưỡng bằng chứng cao nhất trong kit.

---

## 0. Ba điều cấm

| ❌ Cấm | Vì sao | Thay bằng |
|---|---|---|
| Ghi `Security` mà không có PoC | Cáo buộc lỗ hổng sai = rủi ro pháp lý | Sheet `Observations`: "Cần pentest xác nhận" — **không** tự khai thác |
| Đưa bug `Reproduced = No` vào sheet gửi KH | Khách thử không ra → mất uy tín cả danh sách | Sheet `Suspected` (nội bộ) |
| Thao tác phá dữ liệu để tìm bug | Không hoàn tác được | Tuân thủ P3; gặp nút nguy hiểm → G9 |

---

## 1. Phát hiện — chỉ thứ đo được

| Nhóm | Đo bằng | Ngưỡng ứng viên | Nguồn |
|---|---|---|---|
| **Giao diện** | ảnh hỏng · tràn ngang ở viewport chuẩn | `brokenImages` · `horizontalOverflow` | `recon/crawl/<WEB>/ui-issues.json` |
| **JS error** | console listener | mọi `type = error` | `console.json` |
| **Network** | response listener | `4xx`/`5xx` trong luồng hợp lệ | `network.json` |
| **Link chết** | crawl | HTTP ≠ 2xx/3xx | `network.json` |
| **Hiệu năng** | thời gian tải | > 5 s ở màn chính | `pages.json.loadMs` |
| **Validation thiếu** | submit rỗng / vượt maxlength — *chỉ khi P3 cho submit* | server nhận giá trị lẽ ra phải chặn | thao tác + `code-ref` |
| **Toàn vẹn dữ liệu** | — | **không chạy**: kit không truy vấn DB của khách | — |

Ứng viên tự động **chưa phải bug**. Mỗi ứng viên phải: (1) tái hiện có chủ đích `n` lần, ghi `Yes — n/n`; (2) gắn `EV-xxxx` (screenshot/console/HAR); (3) viết 1 câu tác động nghiệp vụ.

---

## 2. Mức độ — chỉ ghi Medium trở lên

| Severity | Nghĩa | Ví dụ |
|---|---|---|
| **High** | Luồng nghiệp vụ chính không hoàn thành được · mất/hỏng dữ liệu · màn chính không hiển thị được | nút "Đăng nhập" lỗi 500 · trang danh sách trắng do JS error |
| **Medium** | Chức năng sai/thiếu nhưng có đường vòng · lỗi giao diện làm khó thao tác | ảnh sản phẩm hỏng · layout tràn che nút · link menu chết |
| ~~Low~~ | Chính tả, lệch vài px, màu hơi khác | **không ghi** (gate V8 chặn) |

Chọn theo **tác động nghiệp vụ**, không theo độ khó sửa. Phân vân giữa Medium/Low → không ghi, đưa vào `Observations`.

---

## 3. Cấu trúc

`build-inventory.py --bug-list --out $V/07_BugList/BugList_<sys>_ver<N>.xlsx`:

| Sheet | Nội dung | Gửi KH? |
|---|---|---|
| `00_Meta` | như inventory + `bug_scan_scope`, `bug_recipient` (P9) | — |
| `Bugs` | bug đã tái hiện được | ✅ |
| `Suspected` | nghi ngờ, chưa tái hiện | ❌ nội bộ |
| `Observations` | cần điều tra (gồm mọi nghi vấn bảo mật) | ❌ nội bộ |

Cột `Bugs`: `Bug ID` · `Title` · `Screen / Module` (`SC-`/`F-` — trace về inventory) · `URL / Route` · `Category` · `Severity` (High/Medium) · `Repro Steps` (≥ 2 bước đánh số) · `Expected` · `Actual` · `Evidence` · `Reproduced` · `Detected By` · `Business Impact` · `Env` · `Pre-existing` · `Report To Customer` · `Status` · `Note`.

```bash
python3 $S/verify-bug-list.py $V/07_BugList/BugList_<sys>_ver<N>.xlsx --inventory $I/inventory.xlsx --out $I/gates/v8.md
```

`bug_recipient = Nội bộ review trước` → báo xong nhưng ghi rõ **chưa gửi KH, chờ người duyệt**.

---

## 4. Ranh giới

| Không phải bug | Là |
|---|---|
| `UNKNOWN` ở O1 (chưa quan sát được) | Thiếu bằng chứng, không phải hỏng |
| Open Question | Cần hỏi khách |
| Hành vi lạ nhưng không biết spec | `Observations` |
