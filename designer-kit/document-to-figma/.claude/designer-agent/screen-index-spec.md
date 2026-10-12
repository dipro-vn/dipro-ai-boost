# Screen Index — bảng "đã vẽ gì" trên Figma

> **BẮT BUỘC** sau khi vẽ xong (Bước 5.5 / K7 của `designer-agent.md`), trước khi báo hoàn thành.
> Mục đích: người mở file Figma biết ngay đã vẽ những màn nào, ở node nào, loại gì, ứng với phần nào của tài liệu / REQ / SPEC.
> Format mẫu: khối "BẢNG SCREEN INDEX" trong file ALPHA-TEAM (node `86:1655`, file `C5XoY5yubkAMX3RzVY1N2u`).

## 1. Vị trí & đặt tên
| Thuộc tính | Quy tắc |
|---|---|
| Container | **1 FRAME** trên **cùng page** với các section vừa vẽ, không đặt trong section của màn hình |
| Tên layer | `Screen Index — <Feature> · <platform>` |
| Vị trí | Phía trên-trái cụm section, cách ≥ 200px; không chồng frame khác (quét bbox) |
| Vẽ bổ sung | Cập nhật **chính frame đó** (thêm hàng, tăng `Tổng`, hàng mới highlight §3.4) — không tạo frame thứ hai |
| Bản markdown | Ghi thêm `output/<feature>/screen-index.md` (cùng bảng + node ID) |

## 2. Nội dung (từ trên xuống)
1. **Tiêu đề** `BẢNG SCREEN INDEX (<phạm vi>)`
2. **Dòng tổng** `Tổng: N frame (a màn chính · b popup/trạng thái) · cột Ref = <nguồn tham chiếu> · <phạm vi CHƯA vẽ>`
3. **Header row** `# · Screen · Ref · Loại · Mô tả`
4. **Hàng dữ liệu** — 1 hàng / 1 frame, theo thứ tự trên canvas. ≥ 2 section → chèn **hàng nhóm** trước mỗi nhóm (§3.5)
5. **Dòng chân** `Tổng: N frame — chi tiết: <path screen-index.md>`

| Cột | Nội dung | Ví dụ |
|---|---|---|
| `#` | STT liên tục (hàng nhóm không đánh số) | `7` |
| `Screen` | `<Screen Code> <Tên ngắn>` — bold, **hyperlink NODE** tới frame (`setRangeHyperlink(0, len, {type:'NODE', value: frameId})`) | `XX_FEAT_003 Sửa đơn` |
| `Ref` | Tham chiếu nguồn, màu primary, bold: `#` trạng thái trong tài liệu / FR / mục SPEC | `#043–049` |
| `Loại` | `List` · `Detail` · `Form` · `Wizard` · `Dashb.` · `Report` · `Settings` · `Chat` · `Modal` · `Popup` · `Toast` | `Form` |
| `Mô tả` | 1 dòng (≤ ~45 ký tự) — **nội dung đã vẽ**, ghi rõ trạng thái đại diện | `Sửa hóa đơn chưa phát hành` |

## 3. Style (đo từ file mẫu, kích thước gốc 480px)
Kit không có design system mặc định → **màu primary / neutral lấy từ token của Design System dự án** (`design-system/project/tokens.json`); bảng dưới là giá trị đo ở file mẫu, dùng khi chưa có token tương ứng.

### 3.1 Kích thước — hệ số `S`
Chữ gốc 7–9px không đọc được trên canvas có frame 1440 → nhân **`S = 2`** (rộng 960, mọi font/khoảng cách ×2).
| Phần tử | Gốc (S=1) | S=2 |
|---|---|---|
| Rộng bảng | 480 | 960 |
| Tiêu đề | 13 Bold `#24292F` | 26 |
| Dòng tổng / chân | 9 Regular `#6E777D` | 18 |
| Header row | cao 26, nền `#E8F4FD`, viền 1 `#0969DA`, radius 4; chữ 7 Bold `#0969DA` | cao 52, viền 2, chữ 14 |
| Hàng dữ liệu | cao 23, chữ 7 | cao 46, chữ 14 |
| Cột x | `#` 6 · Screen 26 · Ref 182 · Loại 232 · Mô tả 284 | ×2 |
| Divider hàng | 1px `#D0D7DE` | 2 |

### 3.2 Font
Dùng **một** font family cho cả bảng, lấy từ design system dự án. Có tiếng Nhật/Việt → chọn family hỗ trợ glyph (vd Noto Sans JP), không dùng Inter nếu thiếu glyph.

### 3.3 Màu chữ theo cột
`#` → `#6E777D` Bold · `Screen` → `#24292F` Bold · `Ref` → `#0969DA` Bold · `Loại`, `Mô tả` → `#424A53` Regular. Nền hàng xen kẽ trắng `#FFFFFF` / `#F6F8FA`.

### 3.4 Hàng bổ sung
Màn/popup thêm sau lần vẽ đầu → nền `#FFF8F0`, `#` và `Ref` màu `#D86107` Bold; ghi chú ở dòng Tổng.

### 3.5 Hàng nhóm
Cao bằng hàng dữ liệu, nền `#E8F4FD`, chữ `#0969DA` Bold: `▸ <Tên section> (<n> frame) — <node ID section>`; không có `#`.

## 4. Quy trình dựng
1. Duyệt các section vừa vẽ, mỗi FRAME màn hình/popup = 1 hàng (bỏ label TEXT): id, Screen Code, tên, Loại, Ref, mô tả.
2. Tạo frame auto-layout dọc, nền trắng, rộng `480*S` + padding; đặt vị trí an toàn.
3. Title + subtitle → header row → từng hàng (auto-layout ngang, ô FIXED width theo cột, nền xen kẽ).
4. Ô `Screen`: gắn hyperlink NODE. Frame root để `layoutSizingVertical = HUG`.
5. `get_screenshot` kiểm tra: không cắt chữ, không chồng frame khác, số `Tổng` khớp.

## 5. Definition of Done
- [ ] 1 hàng / 1 frame đã vẽ; `Tổng` khớp.
- [ ] Hyperlink NODE đúng; `Ref` đúng nguồn.
- [ ] Hàng nhóm khi ≥ 2 section; hàng bổ sung highlight.
- [ ] Dòng Tổng nêu **phạm vi chưa vẽ** (lỗi / 0 dòng / quyền…).
- [ ] Style đúng §3; không cắt chữ; không chồng frame.
- [ ] `output/<feature>/screen-index.md` đã ghi.
