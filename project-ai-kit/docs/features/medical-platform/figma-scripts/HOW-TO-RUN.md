# Medical Platform — Figma Scripts

## Cách chạy

### Prerequisites
- Figma Design file: https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30633-62845
- Page đích: page chứa node 30633-62845 (xác nhận tên page trước khi chạy)

### Bước 1: Mở Figma file
1. Mở URL trên trình duyệt
2. Vào đúng page chứa node `30633-62845`

### Bước 2: Chạy scripts qua Figma Plugin Console
1. Vào menu **Plugins > Development > Open console**
   HOẶC tạo plugin tạm: **Plugins > Development > New Plugin > Run once**
2. Paste nội dung từng file script vào editor
3. Chạy theo thứ tự: output1 → output2 → output3

### Files
| File | Output | Mô tả |
|---|---|---|
| `output1-flow-tong-quan.js` | Output 1 | Business Logic Flow + Tech Table + Sitemap WBS Tree |
| `output2-screen-flow.js` | Output 2 | Screen Flow 4 vùng (DA Happy / CA Happy / Non-Happy / Index) |
| `output3-hifi-screens.js` | Output 3 | 3 màn hình HiFi + bảng Items + Error Scenarios |

### Lưu ý
- Mỗi script tự tạo frame mới trên page hiện tại
- KHÔNG tạo page mới — chạy trên page user chỉ định
- Nếu script timeout (> 30s) → chia nhỏ thành nhiều lần chạy
