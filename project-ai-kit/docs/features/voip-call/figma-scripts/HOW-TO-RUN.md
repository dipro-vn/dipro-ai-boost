# Cách chạy Figma Plugin Scripts — VoIP Call BA Diagrams

## Scripts trong thư mục này

| File | Mô tả |
|---|---|
| `combined-run-once.js` | Script chính — tạo cả 2 pages trong 1 lần chạy (DÙNG FILE NÀY) |
| `manifest.json` | Plugin manifest — dùng khi import qua Figma Desktop |
| `page1-flow-tong-quan.js` | Script riêng cho page 1 (standalone, nếu cần chạy lại page 1) |
| `page2-screen-flow.js` | Script riêng cho page 2 (standalone, nếu cần chạy lại page 2) |

## Cách chạy (Figma Desktop — recommended)

### Phương án A: Import plugin từ manifest (chuẩn nhất)

1. Mở Figma Desktop
2. Mở file: `https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/`
3. Menu: `Plugins > Development > Import plugin from manifest...`
4. Chọn file `manifest.json` trong thư mục `figma-scripts/`
5. Chạy plugin: `Plugins > Development > BA - VoIP Flow Diagrams > Run`

### Phương án B: Tạo plugin "Run once"

1. Mở Figma Desktop, mở file target
2. Menu: `Plugins > Development > New Plugin`
3. Chọn template **"Run once"** (không cần UI)
4. Figma tạo thư mục plugin mới — mở file `code.js` trong editor
5. Xóa nội dung mặc định, paste toàn bộ nội dung `combined-run-once.js` vào
6. Lưu file
7. Quay lại Figma: `Plugins > Development > [tên plugin bạn đặt] > Run`

## Output sau khi chạy

Figma sẽ tạo 2 pages mới trong file:

### Page 1 — "BA - Flow Tổng Quan"
- Frame `BA - Flow Tổng Quan` (~1800 x 800px)
- Flow diagram từ trái sang phải (happy path)
- Hình dạng:
  - Rectangle xanh (`#E8F4FD`) = Screen chính Dipro Admin
  - Rectangle xanh lá (`#EDFDF0`) = Screen chính Company Admin
  - Diamond cam (`#FFF9EB`) = Decision node
  - Ellipse = External event (Push notification, Toast, System event)
  - Mũi tên xanh = Happy path
  - Mũi tên đỏ nét đứt = Error path / edge case
  - Mũi tên tím = Cross-actor connection (In-Call DA ↔ In-Call CA)

### Page 2 — "BA - Screen Flow"
- Frame `BA - Screen Flow` (~1010 x height px)
- Grid 3 cột, 3 hàng
- 8 cards cho 8 screens (DA_VOIP_001 → DA_VOIP_006, CA_VOIP_001 → CA_VOIP_002)
- Mỗi card có: Header (Screen Code + Name) / Meta (Actor + Type) / Components list / Non-Happy cases
- Arrows kết nối theo "Transition To" trong SPEC.md

## Lưu ý kỹ thuật

- Script dùng font **Inter** — đảm bảo Figma file đang có Inter font (hoặc file đang ở trạng thái connected to Figma cloud fonts)
- Nếu font Inter không available, thay `"Inter"` bằng `"Roboto"` hoặc font có trong file
- Script KHÔNG import bất kỳ design system component nào — chỉ dùng primitives (Rectangle, Ellipse, Vector, Text)
- Script idempotent-ish: mỗi lần chạy sẽ tạo page mới (không overwrite page cũ)

## Sau khi tạo xong

Lấy URL của 2 frames vừa tạo:
1. Click vào frame trong Figma
2. Copy link: `Right click > Copy link` hoặc từ address bar
3. Điền vào SPEC.md — section `## Figma Link` (cột Figma Link)

Format URL: `https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/...?node-id=<ID>&m=dev`
