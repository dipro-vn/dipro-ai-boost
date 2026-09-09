# Ba Agent — Output 1: Flow Tổng Quan

## Output 1 — Flow Tổng Quan (Business Logic Flow + Technology Table + Sitemap)

> **Không phải screen flow.** Đây là luồng **nghiệp vụ + kỹ thuật**: Actor nào → trigger gì → function nào xử lý → công nghệ gì → outcome.

**Gồm 3 phần trong cùng 1 frame (width 2280px):**

**Phần A — Business & Logic Flow** (layout trái → phải, 5 cột — chiếm x=40..1770):
```
ACTOR → TRIGGER → FUNCTION → TECHNOLOGY → OUTCOME
```

**⚠️ Vertical gap rule (BẮT BUỘC — feedback từ user):**

Nếu feature có N business flows (VD Application / Scout / Contract / Admin / LINE), đặt chúng vertically stacked trong Phần A:

- **Gap giữa 2 flows liên tiếp: MIN 100px** (tránh arrow / node của flow N chồng đè lên flow N+1)
- Mỗi flow band: height ~180px (3 rows nodes) đến ~260px (4+ rows nodes)
- Tổng height Phần A: `N × (flowBandHeight + 100) - 100`
- **Verify sau khi vẽ:** `get_screenshot` — TUYỆT ĐỐI không được có arrow/node của flow N đè lên flow N+1. Nếu phát hiện → tăng gap lên 120-150px và vẽ lại.
- Có thể thêm horizontal divider line 1px `#D0D7DE` giữa 2 flow bands để rõ ràng thêm

**Phần B — Technology Table** (BÊN PHẢI Flow, x=1800..2260):
- Bảng 2 cột: `Technology | Mô tả mục đích sử dụng`
- Liệt kê 8-10 tech: Framework/SDK/Service/Database/Cache/Storage/Auth
- Format: header row 32px xanh, data row 60px alternating white/BGL
- Ghi chú cuối: "Tech Lead sẽ chốt lại trong Design-Technical.md"

**Phần C — Sitemap WBS Tree** (dưới Flow, y=560+):
- 4 levels: Feature → Actor → Hành động verb-first → Screen/Popup
- Legend rõ màu (Root/Actor/Hành động/Popup)

| Element | Figma shape | Màu |
|---|---|---|
| Actor (người dùng) | Ellipse 80px | Fill `#E8F4FD`, stroke `#0969DA` |
| Trigger / Action | Rectangle `radius: 8` | Fill `#E8F4FD`, stroke `#0969DA` |
| Function / System | Rectangle `radius: 8` | Fill `#FFF9EB`, stroke `#F4860C` |
| Technology (SDK, DB...) | Rectangle `radius: 8` | Fill `#FFF9EB`, stroke `#F4860C` |
| Outcome | Rectangle `radius: 8` | Fill `#F6F8FA`, stroke `#D0D7DE` |
| Arrow happy path | Line 2px solid | `#0969DA` |
| Arrow error | Line 2px dashed | `#CF222E` |
| Arrow cross-actor | Line 2px solid | `#1A7F37` |

Row phụ bên dưới: **Technology Stack** — các box nhỏ liệt kê framework/SDK/service.

**Phần B — Sitemap kiểu WBS Tree** (layout cây, bên dưới Phần A):

> **Reference:** xem `example_output_1.png` — style WBS tree, có icon minh họa mỗi node, tập trung **Actor + Hành động** (không phải chỉ list màn hình).

Sitemap = cây phân tách công việc (Work Breakdown Structure) theo:
- **Level 1 (Root):** Tên feature
- **Level 2 (Actor):** Từng actor liên quan
- **Level 3 (Hành động chính):** Action mà actor thực hiện (không phải screen name)
- **Level 4 (Sub-action / Screen):** Chi tiết bước hoặc screen liên quan

```
[Feature Name]
├── [👤 Actor A — Vai trò]
│   ├── ✔ Hành động 1 (VD: "Khởi tạo cuộc gọi")
│   │   └── Screen liên quan / Popup
│   └── ✔ Hành động 2 (VD: "Xem lịch sử")
│       └── Screen liên quan
├── [👤 Actor B — Vai trò]
│   └── ✔ Hành động 1 (VD: "Nhận cuộc gọi")
│       ├── Screen liên quan
│       └── Popup: Mic Permission
└── [⚙️ Hệ thống / Tự động]
    └── ✔ Ghi log cuộc gọi
```

| Level | Figma shape | Màu | Nội dung |
|---|---|---|---|
| Root (Level 1) | Rectangle lớn `radius: 8` | Fill `#0969DA`, text white | Tên feature |
| Actor (Level 2) | Rectangle `radius: 8` + icon | Fill nhạt màu actor, stroke đậm | 👤 Tên actor · vai trò |
| Hành động (Level 3) | Rectangle `radius: 6` | Fill `#F6F8FA`, stroke `#0969DA` | ✔ Tên hành động (verb-first) |
| Screen/Popup (Level 4) | Rectangle nhỏ `radius: 4` | Fill trắng, stroke màu actor | Screen Code + tên |
| Connector | Line 1px | `#D0D7DE` | Nối cha → con |

**Nguyên tắc điền:**
- Tên hành động **PHẢI bắt đầu bằng verb**: "Khởi tạo...", "Xem...", "Nhận...", "Ghi log..."
- KHÔNG đặt tên node = screen code (screen code chỉ ở Level 4)
- Mỗi Actor phải có ≥ 1 Hành động
- Popup/Modal xuất hiện ở Level 4, đánh dấu `[Popup]` prefix
