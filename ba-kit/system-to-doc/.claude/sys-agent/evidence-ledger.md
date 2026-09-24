# Evidence Ledger — xương sống chống bịa

> Không có ledger thì mọi gate phía sau đều là gate rỗng. Đây là thứ phải dựng **trước** khi viết bất kỳ dòng nội dung nào.

---

## 1. Luật tối cao

> **Mọi ô có `Status = Confirmed` PHẢI mang ≥ 1 `EV ID` phân giải được.**
> Không có bằng chứng → `Inferred` hoặc `UNKNOWN`. **Không bao giờ để trống.**

Để trống lặng lẽ = người đọc tưởng "không áp dụng". Tự điền = biến giả định thành spec.

---

## 2. Cấu trúc thư mục

```
<OUT>/
├── evidence/
│   ├── EV-0001.png          screenshot man dang nhap
│   ├── EV-0002.har          network trace
│   ├── EV-0003.json         console log
│   └── ...
├── recon/
│   ├── crawl/               output cua crawl-site.js
│   ├── code/                output cua scan-repo.py
│   └── db/                  output cua read-schema.py
└── 01_Inventory_<system>_v<N>.xlsx   ← sheet 05_Evidence tro toi evidence/
```

---

## 3. Sáu loại evidence

| Type | Locator | Artifact | Dùng chứng minh |
|---|---|---|---|
| `screenshot` | URL đầy đủ | `evidence/EV-xxxx.png` | Màn tồn tại, item nhìn thấy, state |
| `har` | URL đầy đủ | `evidence/EV-xxxx.har` | Request/response thật, mã lỗi |
| `console-log` | URL đầy đủ | `evidence/EV-xxxx.json` | Lỗi JS (input cho Bug List) |
| `code-ref` | `src/a/b.ts#L88-L104` | — | Rule, validation, job, integration |
| `db-query` | `orders.status` hoặc câu SQL | — | Cấu trúc DB, tính toàn vẹn dữ liệu |
| `doc-quote` | `仕様書.pdf § 3.2 (p.12)` | — | Điều khách hàng đã viết ra |

**Quy tắc locator:** phải **chính xác tới dòng / trang / cột**. `"trong source code"` · `"trong tài liệu"` · `"trên web"` đều **không hợp lệ** — gate V1 không phân giải được thì FAIL.

---

## 4. Loại evidence nào chứng minh được cái gì

| Kết luận muốn viết | Evidence tối thiểu |
|---|---|
| "Màn này có ô nhập email" | `screenshot` |
| "Ô email là required" | `screenshot` chụp lúc submit rỗng **+** `code-ref` validation |
| "Ô email maxlength 256" | `code-ref` **hoặc** `screenshot` chụp lúc nhập tràn |
| "Bấm nút này sang màn X" | `screenshot` màn X sau khi bấm (cùng session) |
| "Sai format thì hiện message Y" | `screenshot` message **+** `code-ref` nơi sinh message |
| "Cột `status` nghĩa là trạng thái đơn" | `code-ref` nơi code đọc/ghi cột đó |
| "Job chạy 2h sáng làm việc Z" | `code-ref` crontab **+** `code-ref` thân job |

❌ **Không bao giờ** kết luận business rule chỉ bằng `screenshot`. Ảnh cho biết cái gì hiển thị, không cho biết vì sao.

---

## 5. Đánh số + nạp vào inventory

- `EV-0001` trở đi, **liên tục, không tái sử dụng số đã xoá**.
- `crawl-site.js` tự sinh `recon/crawl/evidence.csv` đúng 7 cột của sheet `05_Evidence` — dán thẳng vào, không gõ tay.
- Evidence từ code/DB/doc thì agent tự thêm dòng.

Kiểm tra:
```bash
python3 .claude/skills/system-analyst/scripts/verify-evidence.py \
    <inventory.xlsx> --root <OUT> --code-root <repo> --out <OUT>/gate-v1.md
```

---

## 6. Evidence cũ (chạy lại lần sau)

| Tuổi evidence | Xử lý |
|---|---|
| ≤ 30 ngày | Dùng lại được, giữ nguyên `EV ID` |
| > 30 ngày | Đánh `STALE` ở cột `Note`, **phải chụp lại** nếu dòng đó là `Confirmed` |
| Hệ thống đã deploy version mới | Toàn bộ evidence `screenshot`/`har` coi như `STALE` |

Dòng bê nguyên từ version trước → giữ `EV ID` cũ + ghi `Carried from v<N-1>` ở `Note`.
