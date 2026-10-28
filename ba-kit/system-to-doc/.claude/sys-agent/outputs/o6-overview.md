# O6 — Tài liệu tổng hợp (docx)

> **Yêu cầu (feedback 28/10/2026):** tham khảo `templates/high-level-template.docx` · ngắn — cho khách hàng / BA biết **hệ thống làm gì, nghiệp vụ chính chạy thế nào**, còn màn hình / API / DB chỉ **1 bảng tổng**. Không có danh sách output, luồng tổng quan, phụ lục.
>
> Thành phẩm: `06_Overview/Overview_<sys>_ver<N>.docx`. Luôn chạy, **sinh cuối cùng**.

---

## 1. Nội dung

| Chương | Nội dung | Nguồn |
|---|---|---|
| Khối tiêu đề | dự án · khách hàng · version · ngày · BASELINE | `00_Meta` · `index.json` |
| 0. Phạm vi & nguồn khảo sát | website (URL, môi trường, role) · repo · DB mode · Figma · quyền thao tác | `10_Site` · `11_Repo` · `00_Meta` |
| 1. Tổng quan sản phẩm | 3–5 câu sản phẩm làm gì · actor · cấu thành hệ thống | `narrative.json` (agent viết) |
| **2. Nghiệp vụ chính** | 2.1 Hệ thống này làm gì · 2.2 Luồng nghiệp vụ chính (bước đánh số, link Figma Output 1) · 2.3 Trạng thái của đối tượng chính | `business.json` (agent viết) |
| 3. Website & màn hình | **1 bảng tổng**: mỗi site — số màn theo loại | `02_Screen` (chi tiết ở O1) |
| 4. API & Batch | **1 bảng tổng**: tổng · API · batch · webhook/queue · theo trạng thái bằng chứng | `07_API` (chi tiết ở O2) |
| 5. Database | số bảng / cột / quan hệ · **link Figma ERD** — hoặc `Database not available.` | `03/04` · `figma-links.md` |
| 6. Liên kết bên thứ 3 | tên · loại · mục đích · chiều · trạng thái | `09_Integration` |

**Phân chia trách nhiệm:** mọi **bảng và con số** do script sinh từ inventory; **văn xuôi** do agent viết trong `narrative.json` và `business.json`. Script không bịa văn, agent không gõ tay số.

### `business.json` — chương 2, viết cho khách hàng / BA

```json
{ "overview": "2-4 câu: hệ thống làm gì, ai dùng",
  "flows":  [{"title": "Bệnh viện mời bác sĩ", "actor": "Bệnh viện", "screens": ["「医師検索」"],
              "steps": ["Bệnh viện tìm bác sĩ theo chuyên khoa.", "..."], "figma": "<url, tuỳ chọn>",
              "evidence": ["EV-0012"]}],
  "states": [{"object": "Lời mời", "flow": ["Chờ trả lời", "Đã đồng ý", "Đã từ chối"], "explain": "1-2 câu",
              "question": "Q-004"}] }
```

- Câu thường, theo văn phong `sys-agent/writing-style.md`: **không** mã nội bộ (`SC-` `API-` `EV-`…), tên bảng, enum, tên hàm, đường dẫn code.
- Mỗi luồng / trạng thái có `evidence` (EV) hoặc `question` (Q). Chỉ có Q → docx tự ghi "Cần xác nhận — Q-xxx".
- Mỗi luồng ≥ 2 bước.

---

## 2. Sơ đồ DB trên Figma

- ERD vẽ ở file Figma design của P8 (`o5-figma.md` §3b) khi Brief đồng ý (B5). Link ghi ở dòng `Sơ đồ DB (ERD)` của `05_Figma/figma-links.md`; `render-overview-docx.py --figma-links` chèn vào chương 5 (và link `Output 1` vào mục 2.2).
- Không có Figma → chương 5 ghi "Chưa có sơ đồ trên Figma — xem ảnh ERD trong thư mục 03_DB."
- **Không có sơ đồ API (code map)** ở bất kỳ output nào.

---

## 3. Render + gate

```bash
python3 $S/build-version-index.py $V --skip "O7=user không yêu cầu"        # → index.json (bìa)
python3 $S/render-overview-docx.py --inventory $I/inventory.xlsx --narrative $I/narrative.json \
    --business $I/business.json --index $I/index.json --figma-links $V/05_Figma/figma-links.md \
    --out $V/06_Overview/Overview_<sys>_ver<N>.docx
python3 $S/verify-overview.py $V/06_Overview/Overview_<sys>_ver<N>.docx --inventory $I/inventory.xlsx \
    --business $I/business.json --out $I/gates/v3.md
python3 $S/build-version-index.py $V --skip "O7=user không yêu cầu"        # chạy lại để README có gate của O6
```

Gate V3 chặn: thiếu chương 0–6 / 2.1–2.3 hoặc còn chương đã bỏ (danh sách output, luồng tổng quan, phụ lục) · placeholder còn sót · bảng tổng màn hình / API ≠ inventory · `db_mode = NONE` mà vẫn có bảng DB · chương 2 có mã nội bộ / tên bảng / enum / hàm · luồng / trạng thái không có EV hoặc Q · EV / Q không có trong inventory · luồng < 2 bước · ô trống · ID không tồn tại · còn chữ cũ (mọi kiểu viết hoa / thường) · link ERD không phải Figma mà cũng không có ghi chú.

---

## 4. Anti-pattern

- ❌ Chép danh sách màn / API / bảng vào docx — đã có ở O1 / O2 / O3
- ❌ Viết văn xuôi khẳng định hành vi không có bằng chứng
- ❌ Gõ tay con số thay vì để script đếm
- ❌ Đưa sơ đồ DB lên Figma khi Brief chưa xác nhận (B5)
