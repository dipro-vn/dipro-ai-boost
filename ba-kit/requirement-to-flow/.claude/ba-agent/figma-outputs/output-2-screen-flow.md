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

**⑥ TERMINAL NODES (BẮT BUỘC — list explicit endpoint mỗi flow):**

> Terminal = điểm kết thúc flow (không có transition đi tiếp). Bảng này list explicit mọi terminal per flow để BA/BRSE/QC verify không sót endpoint nào. Đặt DƯỚI Bảng Screen Index, TRÊN Exception Matrix.

Bảng đặt bên phải frame, cùng width với Bảng Index:

| Flow ID | Terminal ID | Type | Destination sau terminal | Status | Source RQ-ID |
|---|---|---|---|---|---|
| AUTH_REGISTER | AUTH_SUCCESS | Success | Redirect ORIGINAL_ENTRY (URL trước khi login) | FACT | RQ-018 |
| AUTH_REGISTER | AUTH_CANCELED | Exit (user cancel) | Redirect HOME | FACT | RQ-019 |
| AUTH_REGISTER | AUTH_BLOCKED_EMAIL | Error (blocking) | Show modal + không transition | FACT | RQ-020 |
| CALL_FLOW | CALL_ENDED_NORMAL | Success | Back to AX_FEAT_002 (Company Detail) + toast "Đã kết thúc" | FACT | RQ-025 |
| CALL_FLOW | CALL_MISSED | Error (timeout) | Show AX_FEAT_005 (Missed screen) | FACT | RQ-026 |
| CALL_FLOW | CALL_REJECTED | Error (peer reject) | Toast + back to AX_FEAT_002 | UNKNOWN | RQ-027 ⚠ chờ BRSE confirm |

**Enum cột Type:**
- `Success` — flow hoàn tất đúng happy path
- `Exit` — user chủ động thoát (cancel, back button, close)
- `Error (blocking)` — lỗi chặn user tiếp tục, không có retry
- `Error (retry)` — lỗi có retry — link về Exception Matrix ID tương ứng
- `Timeout` — hết thời gian chờ system

**Enum cột Status:**
- `FACT` — destination + hành vi đã confirmed bởi BRSE
- `PROPOSAL` — BA đề xuất, chờ approve
- `UNKNOWN` — chưa rõ destination — BLOCKING cho Phase 3

**Rule bắt buộc:**
- **Mỗi flow trong Output 1 PHẢI có ≥ 2 terminals**: ít nhất 1 Success + 1 Exit (user có thể luôn cancel/back)
- Row `UNKNOWN` → PHẢI có tương ứng row trong Exception Matrix (⑤) với classification `UNKNOWN`
- Cột "Destination sau terminal" KHÔNG được để trống — nếu chưa rõ ghi `UNKNOWN — chờ BRSE`
- Cross-verification: count terminal = count end node (⏹ ellipse) trong flow diagram Figma — mismatch → refactor

**Downstream impact:**
- FE Dev đọc bảng này biết đúng redirect logic sau mỗi endpoint
- QC viết test case cho mỗi terminal (positive + negative)
- TL Design biết endpoint nào cần API call log/analytics

---

**⑤ EXCEPTION MATRIX (BẮT BUỘC — bổ sung cho Non-Happy sub-zone, đặt dưới Bảng Index):**

> Non-Happy sub-zone hiện tại vẽ các trigger + luồng lỗi VISUAL trên Figma. Exception Matrix bổ sung dạng bảng để **phân loại từng exception** theo status: có rule rõ ràng hay chưa, để BA/BRSE biết cần confirm gì trước Phase 3.

Bảng đặt dưới Bảng Screen Index bên phải frame, cùng width:

| ID | Trigger (nguyên nhân) | Current requirement | Classification | Agent assessment | Need confirm? | Impact nếu bỏ qua |
|---|---|---|---|---|---|---|
| EX-01 | Mất mạng khi submit | Chưa có trong SPEC | UNKNOWN | Undefined behavior | ✅ Yes | User double-submit → duplicate record |
| EX-02 | Email đã tồn tại | Toast "Email đã đăng ký" | FACT | Đã đủ | — | — |
| EX-03 | Payment timeout 30s | Retry 3 lần rồi báo lỗi | PROPOSAL | BA đề xuất | ✅ Yes | Cần BRSE quyết retry count/interval |
| EX-04 | Push notification bị deny | Fallback SMS OTP | INFERENCE | Suy từ pattern chung | ✅ Yes | Nếu sai → user không nhận được OTP |
| EX-05 | Session expired | Redirect Login + toast | FACT | Đã đủ | — | — |

**Enum cột Classification** (giống Source Register):
- `FACT` — user/BRSE đã confirm rule cụ thể
- `PROPOSAL` — BA đề xuất, chờ BRSE approve
- `INFERENCE` — BA suy từ pattern chung, cần verify
- `UNKNOWN` — chưa có rule, blocking cho Phase 3
- `CONFLICT` — có ≥ 2 source mâu thuẫn

**Rule bắt buộc:**
- Mọi Non-Happy trigger vẽ trên Figma PHẢI có 1 row trong Exception Matrix
- Row `UNKNOWN` / `CONFLICT` KHÔNG được vẽ vào Non-Happy sub-zone như FACT — chỉ vẽ dưới dạng ⚠ UNCLEAR node (dashed border + màu vàng `#FEE28A`) để user biết cần confirm
- Sau Bảng Index + Exception Matrix, BA in ra count summary: `Tổng: N exceptions (FACT: X · PROPOSAL: Y · INFERENCE: Z · UNKNOWN: W · CONFLICT: V)`

**Downstream impact:**
- TL Design đọc row `FACT` để design error handling logic
- QC đọc row `FACT + PROPOSAL` để viết test case
- Row `UNKNOWN + CONFLICT` → PM tạo ticket hỏi BRSE trước khi Phase 3

**AI Suggestion step — nếu feature có AI:**

Khi flow có bước AI xử lý, vẽ node riêng với icon 🤖:
```
┌─────────────────────────────────────┐
│ 🤖 AI Suggestion                    │
│    <mô tả AI làm gì ở bước này>     │
└─────────────────────────────────────┘
```
Kèm text annotation bên cạnh: "AI dùng model gì, input là gì, output là gì, fallback nếu AI fail".
