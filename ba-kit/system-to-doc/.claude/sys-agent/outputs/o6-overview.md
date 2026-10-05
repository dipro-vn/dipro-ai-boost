# O6 — Tài liệu tổng hợp (docx)

> **Yêu cầu:** tham khảo `templates/high-level-template.docx` · tổng hợp dự án **nhưng không dài dòng** — chủ yếu cho biết **đã chạy những gì, đã có những gì, nằm ở đâu**.
>
> Thành phẩm: `06_Overview/Overview_<sys>_ver<N>.docx`. Luôn chạy, **sinh cuối cùng** (cần index các output khác).

---

## 1. Nội dung — đếm và trỏ, không chép lại

| Chương | Nội dung | Nguồn |
|---|---|---|
| Khối tiêu đề | dự án · khách hàng · version · ngày · BASELINE | `00_Meta` |
| 0. Phạm vi & nguồn khảo sát | website (URL, môi trường, role) · repo · DB mode · Figma · quyền thao tác | `10_Site` · `11_Repo` · `00_Meta` |
| 1. Tổng quan sản phẩm | 5–8 câu sản phẩm làm gì · actor · cấu thành hệ thống | `narrative.json` (agent viết) |
| **2. Danh sách output đã sinh** | Output · nội dung · file/link · số lượng · gate — **trọng tâm của tài liệu** | `_internal/index.json` |
| 3. Website & màn hình | mỗi site: số màn theo loại · mỗi module: số chức năng theo trạng thái | `02_Screen` · `01_Function` (chỉ đếm — danh sách đầy đủ ở O1) |
| 4. API & Batch | số API theo group · số batch · Confirmed / To verify · **ảnh code map** | `07_API` · O2 |
| 5. Database | số bảng / cột / quan hệ · **ảnh ERD** — hoặc `Database not available.` | `03/04` · O3 |
| 6. Liên kết bên thứ 3 | tên · loại · mục đích · chiều · trạng thái | `09_Integration` |
| 7. Luồng tổng quan | ảnh flow + vài câu diễn giải | `flow/flow.png` · `narrative.json` |
| Phụ lục A | Open Questions còn mở | `06_OpenQuestions` |
| Phụ lục B | điều kiện khảo sát (ngày, budget, chế độ) | `00_Meta` |

**Phân chia trách nhiệm:** mọi **bảng và con số** do script sinh từ inventory; **văn xuôi** do agent viết trong `narrative.json` (`project_name`, `customer`, `product_overview`, `actors`, `system_composition`, `flow_explanation`). Script không bịa văn, agent không gõ tay số.

Văn xuôi chỉ khẳng định điều có bằng chứng; điều chưa chắc → Phụ lục A, không viết vào chương 1.

---

## 2. Flow tổng quan (ảnh chương 7)

Viết `_internal/flow/flow.json` — **mọi node trỏ về ID có thật** (`F-` · `SC-` · `API-` · `EXT-` · `WEB-` · `table:<tên>`; node `actor`/`external` được phép không có `ref`). Mảng `explanation` (vài câu) phải **nhắc nguyên văn nhãn (`label`) của mọi node** — gate V5 check 8 đối chiếu, để không có node nào trên hình mà không được giải thích:

```bash
python3 $S/render-flow.py $I/flow/flow.json --out $I/flow/flow.png
python3 $S/verify-flow-png.py $I/flow/flow.json --inventory $I/inventory.xlsx --png $I/flow/flow.png --out $I/gates/v5.md
```

---

## 3. Render + gate

```bash
python3 $S/build-version-index.py $V --skip "O7=user không yêu cầu"        # → index.json cho chương 2
python3 $S/render-overview-docx.py --inventory $I/inventory.xlsx --narrative $I/narrative.json \
    --index $I/index.json --flow-png $I/flow/flow.png \
    --codemap-png $V/02_API/CodeMap_<sys>_ver<N>.png --erd-png $V/03_DB/ERD_<sys>_ver<N>.png \
    --out $V/06_Overview/Overview_<sys>_ver<N>.docx
python3 $S/verify-overview.py $V/06_Overview/Overview_<sys>_ver<N>.docx --inventory $I/inventory.xlsx \
    --index $I/index.json --out $I/gates/v3.md
python3 $S/build-version-index.py $V --skip "O7=user không yêu cầu"        # chạy lại để README có gate của O6
```

Gate V3 chặn: thiếu chương · placeholder còn sót · số liệu ≠ inventory · bảng output ≠ file thật trên đĩa · `db_mode = NONE` mà vẫn có bảng DB · ô trống · ảnh tràn khung · ID không tồn tại.

---

## 4. Anti-pattern

- ❌ Chép lại toàn bộ danh sách màn/API/bảng vào docx — đã có ở O1/O2/O3
- ❌ Viết văn xuôi khẳng định hành vi không có bằng chứng
- ❌ Gõ tay con số thay vì để script đếm
- ❌ Sinh O6 trước khi các output khác xong — bảng output sẽ sai
