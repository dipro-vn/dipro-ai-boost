---
name: component_checklist
description: Checklist component-level behaviors — áp dụng sau testing_dimensions khi feature có form, layout, hoặc data display. Tự động detect từ AC text hoặc Figma design.
---

# Component Checklist

## Cách dùng

Skill này **không dùng độc lập** — dùng kết hợp với `rbt_manual_testing`, áp dụng **sau** `testing_dimensions`.

**Khi nào áp dụng:** Tự động detect từ AC text (hoặc từ Figma nếu có MCP):

| Keyword trong AC | Section áp dụng |
|-----------------|----------------|
| "nhập", "input", "textbox", "form", "upload", "download", "import", "export", "đăng ký", "tạo mới", "cập nhật", "xóa", nút hành động | **Section A — Form Components** |
| "dialog", "popup", "breadcrumb", "pager", "tooltip", "hyperlink", "link", "progress" | **Section B — Layout Components** |
| "tìm kiếm", "search", "danh sách", "bảng", "list", "paging", "phân trang", "sort", "sắp xếp", "filter", "lọc" | **Section C — Data Display** |

> Trước khi sinh TCs, agent confirm với user: "Tôi sẽ áp component checklist: [A/B/C]. Có cần thêm/bỏ gì không?"

---

## Section A — Form Components

### Textbox / Input Field

| Scenario | Cần verify |
|----------|-----------|
| Empty/null | Submit với field bắt buộc để trống → validation error đúng message |
| Whitespace-only | Chỉ nhập dấu cách → treat như empty hay accept? (theo spec) |
| Max length | Nhập đúng max → accept; nhập max+1 → blocked hoặc truncated |
| Leading/trailing whitespace | Trim trước khi lưu? Hay giữ nguyên? |
| Special chars — injection | Nhập `<script>alert(1)</script>` → escaped khi display, không execute |
| Special chars — SQL | Nhập `' OR '1'='1` → blocked hoặc escaped, không execute |
| Null character | Nhập `\0` hoặc ký tự null → không làm crash, không lưu corrupt data |
| Ký tự đặc ngôn ngữ | Kana/full-size/half-size (JP), dấu tiếng Việt, CJK, Arabic RTL — nhập và display đúng encoding |
| Copy/paste từ ngoài | Paste từ Word/Excel có rich text → plain text, không corrupt encoding |
| Readonly field | Không editable, không submit giá trị mới dù có thay đổi qua DevTools |
| Disabled field | Không focus được, style phân biệt rõ với enabled |
| Mask field (password) | Ký tự bị ẩn, không expose trong HTML source, không autocomplete không mong muốn |

### Select Box / Dropdown

| Scenario | Cần verify |
|----------|-----------|
| Default value | Đúng giá trị default khi mới mở, không phải placeholder trống |
| Option active/inactive | Inactive option: không chọn được, style phân biệt rõ |
| Single select | Chỉ 1 option được chọn tại 1 thời điểm |
| Multiple select | Mỗi option chọn/bỏ chọn độc lập; counter/tag hiển thị đúng số |
| Select all / Deselect all | Nếu có: check/uncheck đúng tất cả visible options |
| Search trong dropdown | Filter options đúng theo keyword; không kết quả → empty state rõ ràng |
| Dependent dropdown | Dropdown B reset khi Dropdown A thay đổi; không giữ giá trị cũ không hợp lệ |

### Button — theo loại hành động

#### Add / Register Button

| Scenario | Cần verify |
|----------|-----------|
| Confirm dialog | Hiện confirm trước khi submit (nếu có theo spec) |
| DB reflection | Record mới xuất hiện trong danh sách sau success |
| Double-click prevention | Click nhanh 2 lần → không tạo 2 records |
| Browser back sau submit | Không resubmit form → không tạo duplicate record |
| Concurrent register | 2 user tạo cùng unique data → chỉ 1 thành công, user kia nhận error rõ ràng |
| Rollback khi lỗi | Nếu fail giữa chừng (network, server error) → không để data ở trạng thái orphan |
| Required fields | Submit thiếu required field → validation error, không submit |

#### Update Button

| Scenario | Cần verify |
|----------|-----------|
| DB reflection | Data cập nhật đúng trong DB sau success |
| Chỉ update fields thay đổi | Fields không thay đổi không bị overwrite với giá trị cũ |
| Optimistic lock | 2 user cùng edit record → user submit sau nhận conflict warning |
| Cancel / Discard | Hủy edit → dữ liệu gốc được restore, không lưu thay đổi |
| Form dirty state | Đóng tab/navigate away khi có unsaved changes → confirm dialog |

#### Delete Button

| Scenario | Cần verify |
|----------|-----------|
| Confirm dialog bắt buộc | PHẢI có confirm trước khi xóa — không thể xóa 1 click |
| Soft delete | Record không hiện trong UI nhưng còn trong DB; có thể restore nếu spec yêu cầu |
| Hard delete | Record xóa khỏi DB hoàn toàn; không thể recover |
| Cascade delete | Dependencies liên quan (records con) xử lý đúng theo spec (xóa theo / block / detach) |
| Xóa hàng loạt | Multi-select + delete: confirm rõ số lượng, không xóa record không được chọn |

#### Export Button

| Scenario | Cần verify |
|----------|-----------|
| Format đúng | CSV / Excel / PDF đúng format theo spec |
| Encoding | UTF-8 BOM cho Excel hiển thị tiếng Việt/Nhật đúng (không bị lỗi font) |
| Empty data export | Xuất file với 0 records → file hợp lệ với header, không crash |
| Large data export | Xuất 10,000+ records → không timeout, progress indicator nếu lâu |
| Tên file | Tên file đúng convention (VD: `export_YYYYMMDD.csv`) |

#### Import Button

| Scenario | Cần verify |
|----------|-----------|
| File type validation | Chỉ accept đúng format (VD: `.csv`, `.xlsx`) — reject file khác |
| Max file size | File quá lớn → error rõ ràng với size limit cụ thể |
| Malformed file | File đúng extension nhưng nội dung sai format → error, không crash |
| Duplicate detection | Row trùng với data trong DB → reject và báo rõ row nào trùng |
| Rollback on partial failure | Row 5/100 lỗi → rollback toàn bộ hay import 99 rows thành công? (theo spec) |
| Preview trước import | Nếu có step preview: data hiển thị đúng trước khi confirm import |
| Import result report | Sau import: tổng thành công / thất bại / skip rõ ràng |

#### Download Button

| Scenario | Cần verify |
|----------|-----------|
| File content đúng | Nội dung file khớp với data hiển thị trên màn hình |
| MIME type đúng | Content-Type header đúng để browser xử lý/download đúng |
| Tên file | Không bị generic tên như `download` — đúng tên theo spec |
| Encoding | Ký tự đặc biệt trong tên file không bị corrupt |
| File không tồn tại | Link download file đã bị xóa → 404 message rõ ràng, không crash |
| Large file | File lớn → progress indicator, không timeout sớm |

#### Upload Button

| Scenario | Cần verify |
|----------|-----------|
| File type | Chỉ accept đúng MIME type — reject file giả extension |
| Max file size | File vượt giới hạn → error với size limit cụ thể |
| Min file size | File 0 bytes → reject |
| Preview | Image/video: preview trước khi confirm upload |
| Multiple files | Upload nhiều file: từng file được xử lý đúng, thất bại 1 file không block file khác |
| Upload progress | Progress bar / percentage hiện đúng, không freeze |
| Cancel upload | Hủy giữa chừng → không để file nửa vời trên server |
| Upload xong → DB reflection | File accessible ngay sau upload thành công |
| Virus scan | Nếu có: file độc hại → reject với message phù hợp, không lưu |
| Tên file đặc biệt | Tên có spaces, ký tự đặc biệt, unicode → handle đúng |

---

## Section B — Layout Components

### Dialog / Modal

| Scenario | Cần verify |
|----------|-----------|
| Đóng bằng nút Confirm | Action được thực hiện, dialog đóng |
| Đóng bằng nút Cancel | Không có action nào xảy ra, dialog đóng |
| Đóng bằng nút X | Tương đương Cancel — không action |
| Đóng bằng phím Escape | Tương đương Cancel — không action |
| Click overlay (ngoài dialog) | Đóng (nếu spec cho phép) hoặc không đóng (nếu action quan trọng) — đúng theo spec |
| Focus trap | Tab chỉ di chuyển giữa các elements trong dialog, không ra ngoài |
| Scroll trong dialog | Nếu content dài: dialog scrollable, không bị cắt |
| Nested dialog | Dialog mở từ dialog: đóng đúng thứ tự stack |

### Breadcrumb

| Scenario | Cần verify |
|----------|-----------|
| Link từng level | Click vào mỗi cấp → navigate đúng trang |
| Active state | Level hiện tại không phải link (non-clickable), style phân biệt rõ |
| Overflow | Breadcrumb rất dài → truncate hoặc wrap đúng, không vỡ layout |

### Pager / Pagination

| Scenario | Cần verify |
|----------|-----------|
| Trang đầu | Nút Previous/First bị disabled |
| Trang cuối | Nút Next/Last bị disabled |
| Direct input | Nhập số trang trực tiếp: đúng trang → navigate, trang không hợp lệ → error |
| Tổng trang | Số trang tính đúng khi total records thay đổi |

### Hyperlink / Link

| Scenario | Cần verify |
|----------|-----------|
| Internal link | Navigate đúng màn hình trong app |
| External link | Mở tab mới (nếu spec), không navigate rời khỏi app |
| Link với role restriction | User không có quyền → link ẩn hoặc disabled, không 403 khi click |
| Broken link | Link target không tồn tại → 404 page rõ ràng, không crash |

### Visual Elements

| Element | Cần verify |
|---------|-----------|
| Tooltip | Hiện khi hover, ẩn khi mouse rời hoặc click ra ngoài |
| Progress bar | Phần trăm chính xác, không stuck ở 99%, hoàn thành → 100% |
| Loading / Skeleton | Hiện trong khi chờ async, ẩn sau khi data load xong |
| Empty state | Khi không có data: message rõ ràng + action gợi ý, không blank |
| Tab navigation | Thứ tự Tab đúng theo visual layout, Shift+Tab reverse đúng |

---

## Section C — Data Display

### Search

| Scenario | Cần verify |
|----------|-----------|
| Free-word — partial match | Nhập 1 phần keyword → tìm thấy records có chứa keyword đó |
| Free-word — case-insensitive | "ABC" và "abc" cho cùng kết quả |
| Free-word — trim whitespace | Nhập "  keyword  " → tìm như "keyword" |
| Multiple keywords | "từ A từ B": AND (cả 2 phải có) hay OR (1 trong 2)? Đúng theo spec |
| Special chars trong query | Nhập `%`, `_`, `*`, `?`, `<script>` → không break query, không SQL inject |
| Empty search | Không nhập gì → hiển thị tất cả hoặc empty state (theo spec) |
| No result | Keyword không khớp → empty state rõ ràng, không blank |
| Search by role | User chỉ thấy records thuộc scope quyền của mình |
| Search result count | Tổng số kết quả hiển thị chính xác |
| Cache | Search cùng keyword lần 2 → kết quả nhất quán với lần 1 (không stale cache) |

### Paging trong Data Display

| Scenario | Cần verify |
|----------|-----------|
| Page size đúng | Mỗi trang hiển thị đúng số items theo page size config |
| Trang cuối | Số items ≤ page size, không hiện row trống |
| Tổng số records | Đếm đúng kể cả khi có filter/search active |
| Giữ sort state | Chuyển sang trang 2 → vẫn đúng thứ tự sort đang áp |
| Giữ filter state | Chuyển trang → filter không bị reset |
| Deep link | URL có thể share để đến thẳng trang X với sort/filter hiện tại |
| Reload | F5 trên trang X → về trang X (không về trang 1) nếu URL có state |

### Sort

| Scenario | Cần verify |
|----------|-----------|
| Default sort | Thứ tự mặc định đúng theo spec khi không sort thủ công |
| Toggle asc/desc | Click cột đang sort → đổi chiều; icon sort indicator cập nhật đúng |
| Sort cột khác | Sort column B → clear sort column A (hoặc multi-sort theo spec) |
| Null values | null/empty sort về đầu hay cuối? Đúng theo spec hoặc consistent |
| Sort + paging | Sau sort, page 2 vẫn chứa đúng records theo thứ tự |
| Sort + search | Sort không mất kết quả search, search không reset sort |

### Filter

| Scenario | Cần verify |
|----------|-----------|
| Single filter | Filter theo 1 criteria → kết quả đúng |
| Multi-filter | Nhiều filter cùng lúc: AND logic — records phải thỏa hết |
| Filter + search | Kết hợp filter và search: áp dụng cả 2 điều kiện |
| Clear 1 filter | Bỏ 1 filter → kết quả update, các filter khác vẫn còn |
| Clear all filters | Reset về initial state hoàn toàn |
| Filter state | Navigate back → filter state còn giữ hay reset? (theo spec) |
| Filter result count | Tổng records sau filter hiển thị đúng |
