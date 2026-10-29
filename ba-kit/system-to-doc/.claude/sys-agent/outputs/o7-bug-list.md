# O7 — Bug list hiện trạng (tuỳ chọn)

> **Giai đoạn 2** (sau điểm dừng của `/analyze-system`): sinh sau khi AI Playwright chạy trên website; lỗi đọc từ code ở Giai đoạn 1 được ghi tạm vào inventory, Giai đoạn 2 tái hiện rồi mới đưa vào Bug list. App / không chạy Giai đoạn 2 → README ghi ⬜.

> **Yêu cầu (feedback 28/10/2026):** file xlsx **1 sheet duy nhất `Bug List`** · liệt kê bug mức **High trở lên** (High · Urgent) tìm thấy khi **đọc source code** và / hoặc khi **crawl website**, chỉ lỗi **liên quan tới thao tác của người dùng**. Không có bug mức này → sheet chỉ có dòng tiêu đề.
>
> Thành phẩm: `07_Bug_List/BugList_<sys>_ver<N>.xlsx`. Chỉ chạy khi P9 = Có. Tài liệu có thể đi ra ngoài công ty → ngưỡng bằng chứng cao nhất trong kit.

---

## 1. Phát hiện

| Thứ tự | Nguồn | Tìm gì | Bằng chứng |
|---|---|---|---|
| 1 | **Code** (`Code review`) | Handler thiếu xử lý lỗi, validation thiếu, điều kiện sai làm thao tác hỏng, tham số không truyền lên API — **lần theo `fe-api-calls.csv`** từ nút trên màn tới handler | EV `code-ref` `REPO-xx:path#Lnn` (gate kiểm file / dòng có thật) |
| 2 | **Website** (`Playwright`) | Trang lỗi / trắng, layout vỡ che nút, JS error làm hỏng chức năng, request của trang trả 4xx/5xx, link menu chết | EV `screenshot` / `console-log` / `har` (`ui-issues.json`, `console.json`, `network.json`, `pages.json`) |
| — | Cả hai | Lỗi đọc từ code rồi tái hiện được trên màn | `Detected By = Code review + Playwright`, có cả 2 loại EV |

**Báo động giả của công cụ quét không phải bug:** `crawl-site.js` gắn `noise` = `read-only-block` / `csp-block` vào `console.json` / `network.json`. Không tạo bug từ các dòng đó — gate V8 từ chối.

**Không ghi vào Bug list:** lỗi mức thấp hơn High · lỗi thuần kỹ thuật / bảo mật / dữ liệu không gắn được với thao tác nào của người dùng (ghi 1 dòng trong `run-log.md` để BA biết, không khai thác, không PoC) · hành vi lạ nhưng không biết spec (→ Open Question) · ô "Cần xác nhận" ở O5.

## 2. Mức độ — chỉ High · Urgent

| Severity | Nghĩa | Ví dụ |
|---|---|---|
| **Urgent** | Màn chính không dùng được · luồng nghiệp vụ chính bị chặn · lỗi 5xx / trang trắng · nguy cơ mất dữ liệu người dùng thấy được | Bấm 「ログイン」 ra trang lỗi 500 · màn danh sách trắng vì JS error |
| **High** | Chức năng trên màn sai / thiếu nhưng còn đường vòng · lỗi giao diện làm khó thao tác rõ rệt | Nút 「保存」 bị che bởi layout tràn · link menu chính dẫn tới 404 |

Chọn theo **tác động tới thao tác của người dùng**, không theo độ khó sửa.

## 3. Cấu trúc

`build-inventory.py --bug-list --out $V/07_Bug_List/BugList_<sys>_ver<N>.xlsx` → 1 sheet `Bug List`. Phạm vi quét (`bug_scan_scope`) + người nhận (`bug_recipient`, P9) khai ở `00_Meta` của inventory.

Cột: `Bug ID` · `Title` · `Screen / Module` (**`SC-` bắt buộc**) · `URL / Route` (URL **màn**, không phải `/api/…`) · `Category` (Functional · UI/Layout · Performance · Compatibility) · `Severity` (**Urgent / High**) · `Repro Steps` (≥ 2 bước trên màn) · `Expected` · `Actual` · `Evidence` (≥ 1 EV screenshot / console-log / har / code-ref) · `Reproduced` (`Yes — n/n` · `Intermittent` · `Chỉ đọc từ code`) · `Detected By` (`Code review` · `Playwright` · `Code review + Playwright`) · `Business Impact` · `Env` · `Pre-existing` (`Yes` · `Cần xác nhận`) · `Status` · `Note`.

```bash
python3 $S/verify-bug-list.py $V/07_Bug_List/BugList_<sys>_ver<N>.xlsx --inventory $I/inventory.xlsx --out $I/gates/v8.md
```

Gate V8 chặn: workbook không đúng 1 sheet `Bug List` · mức ngoài High / Urgent · Category ngoài danh sách · URL là API · không có EV hợp lệ · code-ref trỏ file / dòng không có thật · EV console là `noise` của công cụ · `Detected By` không khớp loại EV · `Screen / Module` không phải `SC-` có thật · thiếu bước tái hiện · thiếu Business Impact · trùng lặp · `00_Meta` thiếu phạm vi quét / người nhận · còn chữ cũ (mọi kiểu viết hoa / thường).

`bug_recipient = Nội bộ review trước` → báo xong nhưng ghi rõ **chưa gửi khách hàng, chờ người duyệt**.
