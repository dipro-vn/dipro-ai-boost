# Design Analysis — User Login

> Nguồn: https://www.figma.com/design/XFnJRTPYlqXHfLcOplDHkZ/Test-ES?node-id=370-4248 (đọc qua Figma desktop, MCP Bridge — file: "Test-ES", Page 1) · Phân tích lúc: 2026-08-18

## 1. Screens tìm thấy trong design

Trang "Page 1" của file có 6 node top-level, trong đó chỉ **1 frame liên quan đến login**: `OW_AUTH_001`. Không tìm thấy frame nào cho màn "Quên mật khẩu" hay "Đặt mật khẩu mới" trên page này.

| Frame Figma | Screen Code khớp (SPEC ## Screens) | Ghi chú |
|---|---|---|
| `OW_AUTH_001` (1440×1024) | `WB_AUTH_001` — Đăng nhập | **Tên prefix khác nhau: design dùng `OW_`, SPEC dùng `WB_`**. Cần đối chiếu lại quy ước module prefix — SPEC đã tự ghi chú prefix `WB` là suy đoán tạm vì `AGENTS.md` chưa khai Epic code chính thức. |
| — không có frame | `WB_AUTH_002` — Quên mật khẩu | Không tìm thấy trong file/page hiện tại. |
| — không có frame | `WB_AUTH_003` — Đặt mật khẩu mới | Không tìm thấy trong file/page hiện tại. |

Các frame khác trên page (`Flow note`, `R05_Location Information` ×2, `[AW_MAIVER_001] List Update version`) không liên quan đến feature User Login — không phân tích.

## 2. Component chính per screen

**`OW_AUTH_001`** (đọc trực tiếp cây node, 35 node, 1 trạng thái default duy nhất):

- Background: hình ảnh full-bleed phủ toàn frame (layer `image 454`, fill type IMAGE, 1440×1028)
- Card "login" (464×568, bo góc 34px) dạng hiệu ứng kính (glass): layer con `Shadow` (Mask + Blur), `Fill`, `Glass Effect` — nhiều lớp effect chồng
- `logo` — hình ảnh, có drop-shadow trắng
- Tiêu đề text `ログイン` ("Đăng nhập") — Noto Sans JP Bold 24px/28
- Ô input 1 — label `ログインID` ("Mã đăng nhập" / Login ID), input box bo góc 6px, không thấy icon show/hide
- Ô input 2 (component instance `Input`) — label `パスワード` ("Mật khẩu"), input box có icon con mắt (show/hide password) — component `Iconly`
- Nút chính (`btn` instance) — text `ログイン` ("Đăng nhập"), fill xanh lá `#8ACA0D`, có gradient stroke + inner/drop shadow, bo góc 8px
- Nút phụ (`Button` frame) — text `新規契約` ("Đăng ký hợp đồng mới / New Contract"), fill `#F1FFD5`, viền `#8ACA0D`
- Link text `パスワードを忘れた方はこちら` ("Quên mật khẩu, bấm vào đây") — màu `#0969DA`, căn giữa

**Không có dữ liệu** cho `WB_AUTH_002` và `WB_AUTH_003` — chưa có frame để phân tích component.

Không thấy trạng thái empty/loading/error/khoá tài khoản trong file — chỉ có 1 frame ở trạng thái mặc định.

## 3. Design tokens quan sát được

- Font family: `Noto Sans JP` (Regular/Medium/Bold) — khớp `typography.font-family.default` trong `design_rule.md`.
- Tiêu đề `ログイン`: 24px / line-height 28px, Bold — khớp `font.display xs.bold` (24/28).
- Label/input text: 16px / line-height 24px, Regular — khớp `font.text md.regular`.
- Text nút chính/phụ: 18px / line-height 24px — khớp `font.text lg` (18/24).
- Link "quên mật khẩu": 14px / line-height 20px — khớp `font.text sm`.
- Màu text tiêu đề: `#24292F` — khớp `colors.components.text.high` / `colors.semantics.neutral.900`.
- Màu link: `#0969DA` — khớp `colors.semantics.company.500` / `colors.semantics.info.500`.
- Bo góc ô input: 6px — khớp `borders.semantics.border-radius.action` (6px, đúng chuẩn cho input).
- Bo góc nút (`btn`, `Button`): 8px — **không khớp** `action` (6px) mà lại trùng `halfmodal` (8px); theo `design_rule.md` §9, nút nên dùng `action`.
- Bo góc card `login`: 34px — **không có trong thang** `borders.primitives.border-radius.*` (giá trị lớn nhất định nghĩa là `3xl` = 24px). Đây là giá trị custom ngoài token scale.
- Màu nút chính `#8ACA0D` (xanh lá) và nút phụ nền `#F1FFD5` — **không khớp** bất kỳ token màu nào trong `design_rule.md` (nhóm green primitives gần nhất là `#2da44e` family, khác hẳn `#8ACA0D`). Đây là màu thương hiệu riêng của repo `example-web`, chưa được ghi vào bảng "Figma → Token Quick Lookup" (§11 `design_rule.md`).
- Padding ô input quan sát: top/bottom 10px, left/right 14px — gần nhưng không trùng khớp chính xác các bước `spacing.padding.*` (8, 12, 16...).

## 4. Khoảng trống design ↔ SPEC

- **Screen thiếu trong design**: `WB_AUTH_002` (Quên mật khẩu) và `WB_AUTH_003` (Đặt mật khẩu mới) — SPEC yêu cầu cả 3 màn nhưng file Figma chỉ có 1 frame cho màn đăng nhập. Khớp với ghi chú sẵn có trong SPEC: *"Chưa có thiết kế Figma — cả 2 mô tả màn hình đều là chụp lại từ bảng buổi họp."*
- **Nhãn trường đăng nhập không khớp BR-01**: design ghi label `ログインID` ("Mã đăng nhập") cho ô đầu tiên, trong khi SPEC (BR-01, HP-A bước 2) yêu cầu định danh đăng nhập là **Email**. Cần xác nhận: đây có phải field cũ (mã nhân viên `NVxxxx`) chưa được cập nhật theo feature mới, hay là cách gọi tên khác cho cùng field email.
- **Thiếu checkbox "Ghi nhớ đăng nhập"**: SPEC mô tả `WB_AUTH_001` bắt buộc có checkbox này (mặc định không tick, BR-07) nhưng không thấy trong cây node của `OW_AUTH_001`.
- **Nút thừa không có trong SPEC**: nút `新規契約` ("Đăng ký hợp đồng mới") xuất hiện trong design nhưng SPEC không nhắc tới, và Out of Scope #8 ghi rõ "Đăng ký tài khoản tự phục vụ" **không thuộc phạm vi đợt này**. Cần làm rõ với BA/PO mục đích của nút này trước khi FE code theo design.
- **Background ảnh full-bleed mâu thuẫn với mô tả SPEC**: bảng Screens của SPEC ghi rõ `WB_AUTH_001` phải "không ảnh nền/banner", nhưng design có layer `image 454` phủ toàn frame làm nền. Cũng mâu thuẫn với NFR PO nêu: *"đơn giản thôi, nhân viên kho mở bằng máy tính bảng đời cũ, đừng nặng."*
- **Card hiệu ứng kính (glass) nhiều lớp effect** (Shadow + Blur + Fill + Glass Effect) — có thể ảnh hưởng hiệu năng trên tablet cũ, cần Tech Lead FE đánh giá trước khi implement đúng như thiết kế.
- **Trạng thái thiếu hoàn toàn trong design**: không có frame/variant nào thể hiện lỗi inline dưới ô email (AF-01/AF-02), banner lỗi chung đầu form (AF-03, BR-11), trạng thái loading/disabled của nút (AF-10), hay thông báo khoá tài khoản kèm thời gian còn lại (AF-04, AF-05, BR-05). Toàn bộ các AC liên quan (AC-03, AC-05, AC-06, AC-10, AC-11) hiện chưa có tham chiếu trực quan.
- **`WB_AUTH_003` phụ thuộc OQ-04** (quy tắc mật khẩu, thanh độ mạnh) — vốn đã chưa chốt ở SPEC; nay còn chưa có cả frame để bắt đầu thiết kế.

## 5. Ghi chú cho stage sau

- **Cho Tech Lead Tasks**: (1) Xác nhận với BA/PO trước khi chia task FE xem ô "Mã đăng nhập" có phải field email hay không — ảnh hưởng trực tiếp đến binding form/validation AC-01, AC-02. (2) Task FE cho `WB_AUTH_002`/`WB_AUTH_003` chưa có design để ước lượng — cần yêu cầu Designer bổ sung frame trước khi giao task. (3) Đánh giá hiệu năng hiệu ứng glass-card trên tablet cũ trước khi cam kết pixel-perfect. (4) Task cần bao gồm việc xây các trạng thái UI còn thiếu (error inline, banner, loading, khoá tài khoản) vì design hiện chỉ có 1 trạng thái mặc định.
- **Cho PM**: Khối lượng phát sinh — cần Designer bổ sung ít nhất 2 frame còn thiếu (`WB_AUTH_002`, `WB_AUTH_003`) và các trạng thái lỗi/loading/khoá cho `WB_AUTH_001` trước khi Dev có thể bắt đầu đầy đủ. Rủi ro: nút "Đăng ký hợp đồng mới" xuất hiện ngoài scope SPEC — nếu giữ lại cần làm rõ phạm vi (có thể phát sinh thêm work ngoài Out of Scope #8). Field "Mã đăng nhập" mâu thuẫn tiềm ẩn với BR-01 cần chốt sớm để không ảnh hưởng timeline 15/09.

## 6. Assets đã export

Thư mục: `design-resources/`

| File | Loại | Node Figma |
|---|---|---|
| — | — | — |

- Đã bỏ qua: không có
- Không export được: fixture này được tạo trước khi Bước 4 (export asset) tồn tại trong `design-analyst-agent` — chạy lại nhánh Design-Analyst để sinh `design-resources/`.
