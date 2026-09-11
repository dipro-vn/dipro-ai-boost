# Ba Agent — Output 2: Screen Flow

## Output 2 — Screen Flow (N screen-flows tương ứng N business flows từ Output 1)

> **Reference:** xem `example_output_2_screen_flow.png` — flow dọc + numbered badges tròn xanh, icon phân loại screen, decision diamond, có bảng text mô tả bên cạnh.

> **⚠️ Prerequisite:** Output 1 PHẢI vẽ xong trước. Đếm N = số business flows trong Output 1 để làm input cho Output 2.

**Bố cục frame Output 2 — N screen-flow groups (1 per business flow) + Bảng Index tổng:**

```
┌─────────────────────────────────────────────────────┬────────────────────┐
│ SCREEN-FLOW GROUP 1 (business flow 1 từ Output 1)  │                    │
│ ┌────────────┬────────────────┐                    │                    │
│ │ Happy Case │ Non-Happy Case │                    │                    │
│ │  ① → ② …  │ ⚠→ Error 1 …  │                    │  ④ BẢNG SCREEN     │
│ └────────────┴────────────────┘                    │      INDEX         │
├─────────────────────────────────────────────────────┤  (bên phải,        │
│ SCREEN-FLOW GROUP 2 (business flow 2)              │   spanning height  │
│  ...                                                │   toàn frame)      │
├─────────────────────────────────────────────────────┤                    │
│ SCREEN-FLOW GROUP N (business flow N)              │                    │
│  ...                                                │                    │
└─────────────────────────────────────────────────────┴────────────────────┘
```

**Rule chính:**
- **Số screen-flow groups = số business flows Output 1** (VD Output 1 có 5 flows → Output 2 phải có đúng 5 groups)
- Mỗi group đặt vertically stacked, gap MIN 120px giữa 2 groups liên tiếp
- Mỗi group có 2 sub-zones: Happy Case (bên trái) + Non-Happy Case (bên phải trong cùng group)
- **Bảng SCREEN INDEX chỉ 1 bảng tổng duy nhất** đặt bên phải toàn frame, spanning height — vì đây là tổng hợp toàn bộ screens/popups cần cho khách hàng (feedback từ user: "GIỮ LẠI ④ BẢNG SCREEN INDEX vì cái này là tổng hợp toàn bộ screen và popup")

**Group N — Screen-flow (Happy + Non-Happy trong cùng group):**

Mỗi group có tiêu đề group ở đầu (label business flow, VD "Flow 1 — User Application"):

```
┌─── Flow N: <Tên business flow> ────────────────────┐
│                                                    │
│  HAPPY CASE (bên trái)     NON-HAPPY CASE (phải)  │
│  Start → ① → ② → ③ → End   ⚠ Trigger 1 → ...     │
│                             ⚠ Trigger 2 → ...     │
│                             ⚠ Trigger 3 → ...     │
└────────────────────────────────────────────────────┘
```

- Happy sub-zone: chỉ luồng chính, decision chỉ đi nhánh Yes/Happy
- Non-Happy sub-zone: các trigger + luồng lỗi tương ứng flow đó

Ví dụ Output 2 cho feature sample-multi-flow-feature (5 business flows từ Output 1):

```
Group 1 — Application (User tìm & ứng tuyển Job)
  Happy: A1_MOD_001 → A1_MOD_002 → A1_APPL_001 → A2_APPL_001 → A1_CONT_001
  Non-Happy: ⚠ User bị block → ⚠ Billing chưa active → ⚠ PDF chưa ready

Group 2 — Scout (Admin chủ động scout User)
  ...

Group 3 — Contract (Ký & quản lý hợp đồng)
  ...

Group 4 — Admin (Quản trị nội bộ)
  ...

Group 5 — LINE (Integration LINE Webhook + Auth)
  ...
```

**④ BẢNG SCREEN INDEX (bên phải, spanning toàn frame — DUY NHẤT):**

BẮT BUỘC — bảng liệt kê TẤT CẢ màn hình (kể cả Popup) với 3 cột:

| # | Màn hình | Loại | Mô tả chức năng màn hình |
|---|---|---|---|
| 1 | AX_FEAT_001 — Company List | List | Hiển thị danh sách công ty, cho phép chọn để gọi |
| 2 | AX_FEAT_002 — Company Detail | Detail | Xem thông tin + khởi tạo cuộc gọi |
| 3 | AX_FEAT_003 — Outgoing Call | Modal | Chờ Actor B (Receiver) nhận máy (30s) |
| ... | ... | ... | ... |
| 9 | [Popup] Mic Permission | **Popup** | Yêu cầu quyền microphone khi tap Gọi |
| 10 | [Popup] Confirm Cancel | **Popup** | Xác nhận hủy cuộc gọi giữa chừng |

**⚠️ QUY TẮC ĐẾM TOTAL:**
- **Popup CŨNG LÀ MÀN HÌNH** — PHẢI đưa vào bảng và đếm vào total
- Toast/Banner CŨNG đếm (nếu là component riêng, không chỉ là inline notification)
- Tổng cuối bảng: **"Tổng: N màn hình (trong đó X popup + Y toast)"**

**Loại (cột 2) — enum:**
`List` · `Detail` · `Form` · `Modal` · `Popup` · `Toast` · `Banner` · `Wizard` · `Dashboard`

**Quy ước visual (áp dụng cho cả Vùng 1 + Vùng 2):**

| Element | Figma shape | Ghi chú |
|---|---|---|
| Start | Ellipse 32px với icon ▶ | Fill `#0969DA` |
| End | Ellipse 32px với icon ■ | Fill `#6E7781` |
| Numbered badge | Ellipse 24px + số | Xanh (Screen) / Tím (Popup) / Đỏ (Error) |
| Screen node | Rectangle 200×56px | Fill trắng, stroke `#0969DA` — icon 🖥 |
| Popup node | Rectangle 200×56px nét đứt | Fill `#FBEEFF`, stroke `#6639BA` — icon 💬 |
| Error/Toast node | Rectangle 200×56px nét đứt | Fill `#FFF6F5`, stroke `#CF222E` — icon ⚠ |
| Decision | Diamond 44px | Fill `#FFF9EB`, stroke `#F4860C` — label "Yes/No" |
| Happy arrow | Line 2px solid | `#0969DA` |
| Error arrow | Line 2px dashed | `#CF222E` |

**Format mỗi screen node — PHẢI có 1 dòng mục đích:**
```
┌─────────────────────────────────────┐
│ ① AX_FEAT_001  Company List   List  │
│    Hiển thị DS công ty, chọn để gọi │  ← mục đích 1 dòng
└─────────────────────────────────────┘
```

**AI Suggestion step — nếu feature có AI:**

Khi flow có bước AI xử lý, vẽ node riêng với icon 🤖:
```
┌─────────────────────────────────────┐
│ 🤖 AI Suggestion                    │
│    <mô tả AI làm gì ở bước này>     │
└─────────────────────────────────────┘
```
Kèm text annotation bên cạnh: "AI dùng model gì, input là gì, output là gì, fallback nếu AI fail".
