# Output 2B — Bug List (lỗi tồn tại trước bàn giao)

> **Mục đích thật:** báo khách hàng danh sách lỗi **đã có trước khi ta nhận dự án**, để sau này không bị quy trách nhiệm. Đây là tài liệu có mục đích **thương mại/pháp lý**, không chỉ kỹ thuật.
>
> Vì nó đi ra ngoài công ty, ngưỡng bằng chứng cao hơn hẳn Output 1 và 2A.

---

## 0. Ba điều cấm tuyệt đối

| ❌ Cấm | Vì sao | Thay bằng |
|---|---|---|
| Ghi `Category = Security` mà không có PoC | Cáo buộc lỗ hổng sai = rủi ro pháp lý cho cả hai bên | Đưa xuống sheet `Observations`, ghi `Cần pentest xác nhận` |
| Đưa bug `Reproduced = No` vào sheet gửi khách | Khách thử không ra → mất uy tín toàn bộ danh sách | Đưa xuống sheet `Suspected` (nội bộ) |
| Thao tác phá dữ liệu để tìm bug | Không hoàn tác được trên hệ thống thật | Tuân thủ `g2_crawl_mode`; gặp nút nguy hiểm → Gate G9 |

---

## 1. Sáu nhóm tiêu chí phát hiện — mỗi nhóm là 1 phép đo

| Nhóm | Phát hiện bằng | Ngưỡng tính là ứng viên bug | Nguồn |
|---|---|---|---|
| **Console/JS error** | Playwright console listener | mọi message `type = error` | `recon/crawl/console.json` |
| **Network** | HAR / response listener | `4xx`/`5xx` trong luồng thao tác hợp lệ | `recon/crawl/network.json` |
| **Broken link / dead route** | crawl | HTTP ≠ 2xx/3xx | `recon/crawl/network.json` |
| **Validation thiếu** | submit form rỗng / vượt maxlength *(chỉ khi G2 = submit-\*)* | server chấp nhận giá trị lẽ ra phải chặn | thao tác + `code-ref` |
| **Data integrity** | SQL | orphan FK, duplicate unique, NULL ở cột logic bắt buộc | `recon/db/integrity-checks.sql` |
| **Performance** | Playwright timing | load > 5s ở màn chính | `recon/crawl/pages.json` |

> `g13_scan_scope` quyết định nhóm nào được chạy. `Chỉ blackbox` → bỏ nhóm Data integrity và phần `code-ref` của nhóm Validation.

---

## 2. Từ ứng viên → bug thật

Ứng viên phát hiện tự động **chưa phải bug**. Mỗi ứng viên phải qua 3 bước:

1. **Tái hiện lại có chủ đích** — viết được các bước đánh số, chạy lại `n` lần, ghi `Yes — n/n`.
2. **Gắn bằng chứng** — `EV ID` trỏ tới screenshot/HAR/console log có thật trong ledger.
3. **Diễn giải tác động nghiệp vụ** — 1 câu khách hàng đọc hiểu. `S1`/`S2` bắt buộc có.

Không qua đủ 3 bước → xuống `Suspected` hoặc `Observations`.

---

## 3. Cấu trúc 1 item bug

| # | Cột | Enum / ràng buộc |
|---|---|---|
| 1 | `Bug ID` | `BUG-001`, không trùng |
| 2 | `Title` | 1 câu |
| 3 | `Screen / Module` | `SC-xxx` / `F-xxx` — **trace về Output 1** |
| 4 | `URL / Route` | |
| 5 | `Category` | `Functional` · `UI/Layout` · `Data` · `Performance` · `Compatibility` · `Security` |
| 6 | `Severity` | `S1 Blocker` · `S2 Major` · `S3 Minor` · `S4 Cosmetic` |
| 7 | `Repro Steps` | **≥ 2 bước đánh số** — gate V8 check 5 |
| 8 | `Expected` / `Actual` | 2 ô tách riêng |
| 9 | `Evidence` | `EV-xxxx` phân giải được — gate V8 check 6 |
| 10 | `Reproduced` | `Yes — n/n` · `Intermittent` · `No` |
| 11 | `Detected By` | `Playwright` · `Code review` · `DB check` · `Console` |
| 12 | `Business Impact` | bắt buộc với `S1`/`S2` |
| 13 | `Env` | URL + browser + ngày |
| 14 | `Pre-existing` | `Yes` · `Unknown` — **lý do tồn tại của cả file này** |
| 15 | `Report To Customer` | `Yes` (chỉ ở sheet `Bugs`) · `Internal only` |
| 16 | `Status` | `Open` · `Fixed` · `Won't fix` |

Severity chọn theo tác động nghiệp vụ, **không** theo độ khó sửa:

| Severity | Nghĩa |
|---|---|
| `S1 Blocker` | Luồng nghiệp vụ chính không hoàn thành được, hoặc mất/hỏng dữ liệu |
| `S2 Major` | Chức năng sai kết quả nhưng có đường vòng |
| `S3 Minor` | Sai lệch nhỏ, không chặn nghiệp vụ |
| `S4 Cosmetic` | Hiển thị, chính tả, layout |

---

## 4. Quy trình (Bước 9)

```bash
S=.claude/skills/system-analyst/scripts
python3 $S/build-inventory.py --bug-list --out "02_BugList_<system>_v<N>.xlsx"
# ... agent điền 3 sheet Bugs / Suspected / Observations ...
python3 $S/verify-bug-list.py "02_BugList_<system>_v<N>.xlsx" \
    --inventory "01_Inventory_<system>_v<N>.xlsx" --out gates/v8.md
```

| Bước | Việc | Điều kiện chuyển tiếp |
|---|---|---|
| 1 | Gom ứng viên từ 6 nhóm | Mỗi ứng viên có nguồn file cụ thể |
| 2 | Khử trùng lặp (cùng tiêu đề + cùng route) | Gate V8 check 11 |
| 3 | Tái hiện từng ứng viên | Ghi đúng `Yes — n/n` / `Intermittent` / `No` |
| 4 | Phân sheet: `Bugs` / `Suspected` / `Observations` | Gate V8 check 7 · 8 · 9 |
| 5 | Gán Severity + Business Impact | `S1`/`S2` phải có impact |
| 6 | Điền `00_Meta` (`g13_scan_scope`, `g13_recipient`) | Gate V8 check 13 |
| 7 | Chạy gate V8, `FAIL = 0` | Không hạ ngưỡng |
| 8 | Nếu `g13_recipient = Nội bộ review trước` → **DỪNG**, chờ người duyệt | Không tự gửi |

---

## 5. Ranh giới với Output 1

| Thuộc Output 1 | Thuộc Output 2B |
|---|---|
| "Hệ thống làm gì" | "Hệ thống làm sai chỗ nào" |
| `UNKNOWN` = ta chưa quan sát được | Bug = ta quan sát được và nó sai |
| Open Question = cần hỏi khách | Bug = cần báo khách |

❌ Không biến `UNKNOWN` của Output 1 thành bug. Không quan sát được ≠ hỏng.
