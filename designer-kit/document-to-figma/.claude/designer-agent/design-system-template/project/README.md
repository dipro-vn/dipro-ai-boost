Design system cho <sản phẩm / các site>. Dựa trên <thư viện / file nguồn> và cách nó được dùng thật trong <file / màn đã duyệt>. Một bộ component phục vụ <N> portal; chỉ <token nào> đổi theo portal.

## <N> portal = <N> theme

Chọn portal bằng `data-theme` trên `<html>` (hoặc phần tử bao ngoài). Chỉ các token `primary*`, `on-primary` <…> đổi giá trị; neutral, status, type, spacing, radius giữ nguyên.

| `data-theme` | Portal | Người dùng | `primary` | Nguồn |
| --- | --- | --- | --- | --- |
| `<theme-id>` | <tên portal> | <ai dùng> | `#……` <tên màu> | <file, đúng giá trị / mới> |

- Dùng token vai trò, không dùng mã màu: `primary` cho nền nút chính / mục nav đang chọn / gạch chân tab; `primary-text` khi màu portal là chữ hoặc nét mảnh; `primary-subtle` cho nền nhạt; `on-primary` cho chữ trên nền `primary`.
- <Cảnh báo tương phản theo portal, nếu có.>

## Màu

- Nền ứng dụng `page-bg` (#……). Card, section, header, sidebar, modal dùng `surface`. Header ô bảng, dải tiêu đề section, giá trị chỉ đọc dùng `surface-subtle`.
- Chữ: `text-high` cho tiêu đề và giá trị quan trọng, `text-middle` cho nội dung và nhãn, `text-low` cho helper / placeholder / meta (chỉ trên nền trắng).
- Đường kẻ: `divider-low` giữa các hàng, `divider-middle` cho viền input và viền ngoài bảng, `divider-high` khi hover.
- Trạng thái (không đổi theo portal): `success-*`, `info-*`, `warning-*`, `negative-*`. Nền badge dùng bước 100, chữ dùng bước <…>. Nút xoá dùng `negative-500`.
- `brand-*` chỉ dành cho logo và khoảnh khắc thương hiệu. Không dùng làm màu trạng thái.

### Badge trạng thái <đối tượng>

| Nhãn | Tone | Ghi chú |
| --- | --- | --- |
| <nhãn thật> | success | |

## Chữ

- Font: **<Font chính>** (`font-sans`) cho mọi chữ; **<Font mono>** (`font-mono`) cho ID và mã (<ví dụ ID thật>).
- Thang chữ theo <nguồn> (<size/line-height …>). Màn <loại> dùng:
  - Tiêu đề trang: `<style>` (<px>). Một cái mỗi màn.
  - Tiêu đề section: `<style>`. Tiêu đề modal: `<style>`.
  - Nội dung, ô bảng, giá trị input: `<style>`. Nhãn field và header bảng: `<style>`.
  - Helper / lỗi / breadcrumb / meta: `<style>`.
- Số tiền viết `<…>`, ngày `<…>`. Căn phải cột số, dùng `font-variant-numeric: tabular-nums`.

## Khoảng cách, bố cục

- Lưới <4>px: `space-4` … `space-24` là các bước dùng hằng ngày.
- Khung màn hình (thiết kế ở `viewport-web` <1440>px): sidebar `sidebar-width` <…> · header `header-height` <…> · page header (breadcrumb + tiêu đề + nút hành động bên phải) · vùng nội dung padding `space-24`, card cách nhau `space-16`.
- Form chi tiết: <số cột>, mỗi field = nhãn + input `control-md` + helper.
- Bảng: header `table-header-height` trên `surface-subtle`, hàng `table-row-height`, kẻ `divider-low`. Phân trang <vị trí + mẫu chữ>.

## Mẫu màn hình <loại>

- <Màn 一覧 / danh sách: nút page header, link cột đầu, cột thao tác.>
- <Màn chi tiết: tiêu đề, nút theo chế độ.>
- <Hộp xác nhận, toast sau khi lưu / xoá.>

## Viền, bo góc, đổ bóng

- `radius-md` cho nút, input, select; `radius-lg` cho card, mục nav, menu; `radius-xl` cho modal; `radius-sm` cho badge; `radius-full` cho pill, switch.
- Card <phẳng / shadow-flat>. Menu thả xuống `shadow-float`, modal và toast `shadow-popout`.
- Focus bàn phím: `shadow-focus` (`focus-ring`).

## Trạng thái tương tác

- Nút solid: `primary` → hover `primary-hover` → nhấn `primary-active`; disabled `surface-disabled` + `text-low`.
- Nút outline: viền `primary`, chữ `primary-text`, hover nền `primary-subtle`. Nút ghost: chỉ chữ.
- Nút nguy hiểm: nền `negative-500`, hover `negative-600`.
- Loading: spinner thay icon, không nhận click.
- Không có quyền: <ẩn / disable>.

## Nội dung và giọng văn

- Nhãn UI bằng <ngôn ngữ>, <kiểu>: 「<…>」.
- Hộp xác nhận: tiêu đề 「<…>」, nội dung 「<…>」, nút 「<…>」+「<…>」.
- Thành công: 「<…>」. Lỗi: 「<…>」.
- Thuật ngữ thống nhất: <…>. <Emoji: không dùng.>

## Icon

- Bộ icon **<tên bộ>**, độ đậm <…>, <px> trong nav / nút, <px> trong input. <N> icon trong nhóm asset **Icons**; component `Icon` vẽ bằng `currentColor`.
- Icon đứng một mình phải có `aria-label`.

## Logo

- Logo **<tên>** (<mô tả, màu `brand-*`>) trong nhóm asset **Logos** (<định dạng, kích thước>). Đặt ở <vị trí> (cao <px>), luôn trên <nền>.
- Không đổi màu, không kéo giãn, không đặt lên nền `primary`.
