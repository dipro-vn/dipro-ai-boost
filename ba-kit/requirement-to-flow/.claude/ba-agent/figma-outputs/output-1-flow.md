# Ba Agent — Output 1: Flow Tổng Quan

## Output 1 — Flow Tổng Quan (Business Logic Flow + Technology Table + Sitemap)

> **Không phải screen flow.** Đây là luồng **nghiệp vụ + kỹ thuật**: Actor nào → trigger gì → function nào xử lý → công nghệ gì → outcome.

## Xác định N — bao nhiêu business flow? (BẮT BUỘC đọc trước khi đếm N)

> Tổng quan nguyên tắc granularity chung (cả Flow lẫn Screen) xem `.claude/ba-agent/granularity-principles.md`.

> Lỗ hổng đã xảy ra thực tế: agent tự suy N từ cách nhóm sẵn của nguồn input (VD 1 hàng 中分類/medium-category trong Estimate = 1 flow) mà không kiểm tra lại theo nguyên tắc nghiệp vụ, dẫn tới over-split — quá nhiều flow nhỏ, trong đó có flow chỉ là "lối vào khác" của flow khác chứ không phải mục tiêu nghiệp vụ riêng.

**Nguyên tắc gốc:** Output 1 là **bức tranh tổng quan cho PM/Tech Lead/stakeholder nắm scope**, KHÔNG phải bảng liệt kê screen (đó là việc của Output 2). Vì vậy 1 business flow PHẢI là **1 mục tiêu nghiệp vụ trọn vẹn của actor** (trigger → outcome có ý nghĩa độc lập), không phải mọi bước con / mọi biến thể / mọi điểm vào.

**Bước 0 — Flow Candidate Matrix (BẮT BUỘC lập TRƯỚC khi chạy test):**

> Lỗ hổng cũ: rule chỉ yêu cầu chạy test cho "từng cặp ứng viên **có vẻ liên quan**" — cặp nào agent không thấy "có vẻ" thì không bao giờ được test. Nay bắt buộc lập bảng đầy đủ, để quyết định gộp/tách trở thành **artifact kiểm chứng được**, user review được ngay thay vì tin vào phán đoán ngầm.

Liệt kê **TOÀN BỘ** ứng viên flow thô (từ Function Inventory / requirement gốc) — KHÔNG bỏ sót dòng nào:

| # | Candidate thô | Actor | Trigger | Outcome cuối | Test G | Test A | Test B | Test F | Quyết định | Gộp vào |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Đăng nhập | User | Tap "Đăng nhập" | Vào được hệ thống | — | cụm Account Access | — | — | GỘP | #3 |
| 2 | Quên mật khẩu | User | Tap "Quên MK" | Vào được hệ thống | trùng (Actor,Outcome) với #1 | — | không có outcome riêng | — | GỘP | #3 |
| 3 | Account Access | User | 3 trigger | Vào được hệ thống | — | — | — | — | **GIỮ** | — |

**Rule chạy test:** chạy cho **MỌI cặp cùng Actor HOẶC cùng Outcome cuối** — KHÔNG phải chỉ cặp "có vẻ liên quan".

**5 phép test bắt buộc chạy cho MỌI ứng viên flow trước khi chốt N (thứ tự: G → A → B → F → E):**

0. **Test G — Merge-by-outcome (phép gom CƠ HỌC, chạy ĐẦU TIÊN):** nhóm candidate theo cặp `(Actor, Outcome cuối)`. **Trùng CẢ HAI → GỘP ngay**, không cần tranh luận định tính. Test G lọc sạch các case hiển nhiên trước, để Test A/B/F (vốn định tính, dễ lệch giữa 2 lần chạy) chỉ phải xử lý phần thật sự mơ hồ. Cần `ACTOR_LIST` từ **Câu 0.10** (`preflight-questions.md`) — chưa có thì ghi `Test G: SKIPPED — thiếu ACTOR_LIST` và hỏi user, không tự suy.

1. **Test A — Capability grouping (theo cách PM mô tả sản phẩm; củng cố bởi nguyên tắc Single Responsibility trong Domain-Driven Design):** Nếu phải mô tả sản phẩm trong 1 câu ngắn ("hệ thống có Đăng nhập/Tài khoản, Đặt Seminar, Tra cứu BĐS..."), các ứng viên nào rơi vào CÙNG 1 cụm từ mô tả đó → gộp thành 1 flow, biểu diễn biến thể bằng nhiều Trigger box hoặc 1 Decision node ngay trong flow đó, KHÔNG tách thành flow riêng. 1 flow nên gói gọn đúng 1 nhóm capability gắn kết (single responsibility ở tầng flow), không lẫn 2 capability khác nhau vào 1 flow.
   - *Ví dụ:* Login / Logout / Reset password đều nằm trong cụm "Account Access" mà PM sẽ mô tả chung 1 câu → gộp thành **1 flow "Account Access"** với 3 Trigger box (Login / Logout / Quên mật khẩu) cùng dẫn vào chung Function xử lý auth, rẽ nhánh Outcome khác nhau — KHÔNG vẽ 3 flow riêng.
2. **Test B — Independent-outcome test (điểm vào phụ hay mục tiêu riêng?):** Hỏi "Nếu bỏ ứng viên B đi, ứng viên A có còn tự đứng vững là 1 hành trình nghiệp vụ hoàn chỉnh không? B có outcome nào KHÁC outcome của A không, hay B chỉ dẫn vào giữa/cuối hành trình của A?" — nếu B không có outcome độc lập (chỉ là 1 lối vào khác dẫn tới cùng đích của A) → gộp B vào A như 1 Trigger box phụ, KHÔNG tách flow.
   - *Ví dụ:* "Xem danh sách BĐS đề xuất" chỉ dẫn tới "Xem chi tiết BĐS" (outcome giống hệt flow BĐS chính, không có outcome riêng) → gộp làm Trigger phụ trong flow "Property Management", KHÔNG tách flow riêng.
3. **Test F — Ubiquitous Language & Ownership Boundary (nguồn: Domain-Driven Design — Bounded Context, Eric Evans / Martin Fowler) — dùng làm tie-breaker khi Test A chưa rõ:** 2 ứng viên dùng CHUNG 1 bộ thuật ngữ nghiệp vụ (cùng danh từ/khái niệm cốt lõi, VD cùng nói về "Member"/"Seminar") VÀ do cùng 1 actor/team sở hữu toàn trình → nghiêng về gộp. Nếu thuật ngữ cốt lõi đổi hẳn (VD từ "Member/Seminar" sang "Property/Bank/Loan") HOẶC actor sở hữu khác nhau → nghiêng về tách.
4. **Test E — Cardinality Budget (nguồn: Jeff Patton, *User Story Mapping* — backbone nên có 4-8 activities, >10 là dấu hiệu over-scoped) — chạy SAU CÙNG như sanity-check:** Sau khi đã chạy Test A/B/F, đếm lại N. Nếu **N > 8-10** cho 1 SPEC/feature → đây là cảnh báo tự động, BẮT BUỘC BA tự vấn lại toàn bộ danh sách tìm thêm ứng viên gộp trước khi chốt — KHÔNG được im lặng chấp nhận N lớn chỉ vì tài liệu nguồn liệt kê nhiều mục. Nếu rà lại vẫn không gộp được (VD scope thực sự là toàn hệ thống nhiều actor) → phải nêu rõ lý do "N > 10 vì <lý do cụ thể>" khi trình bảng cho user ở bước dưới, không giấu con số bất thường.

**Khi NÀO giữ tách riêng dù cùng actor/domain:** nếu ứng viên có đủ độ phức tạp/rủi ro nghiệp vụ đáng để stakeholder thấy riêng ngay ở tầng overview (nhiều bước, nhiều Non-happy case quan trọng, tích hợp bên ngoài phức tạp — VD "Seminar Booking" với 4 hình thức checkout + hoàn tiền) → giữ là 1 flow riêng dù cùng domain với flow khác, KHÔNG gộp chung chung tới mức mất tín hiệu quan trọng cho PM.

**Quy trình bắt buộc trước khi vẽ Phần A:**
1. Lập **Flow Candidate Matrix** đầy đủ (Bước 0 ở trên) — mọi candidate thô đều có 1 dòng, không bỏ sót
2. Chạy **Test G** (cơ học) trên mọi cặp trùng `(Actor, Outcome)` → gộp ngay các case hiển nhiên
3. Chạy **Test A → Test B → Test F** cho mọi cặp còn lại cùng Actor HOẶC cùng Outcome
4. Chạy **Test E** (cardinality sanity-check) theo ngưỡng của `FLOW_GRANULARITY` (Câu 0.9 `preflight-questions.md`) — vượt ngưỡng → quay lại bước 2
5. In **Merge Log** (bắt buộc — format bên dưới)
6. Verify rule **"gộp = đổi tầng"**: mọi candidate bị gộp đã có mặt ở Sitemap WBS Phần C hoặc là Trigger box phụ chưa?
7. Trình bảng N flow + Merge Log cho user xác nhận (đặc biệt khi input là Simple Estimate — kết hợp Rule R1 ở `preflight-questions.md`)
8. Chỉ sau khi user confirm N mới bắt đầu vẽ Phần A

**Merge Log — BẮT BUỘC in, không có log thì KHÔNG được vẽ:**

```
MERGE LOG (N thô: 11 → N chốt: 4 · Granularity: [B] Standard)
- Gộp "Quên mật khẩu" vào "Account Access"     — Test G: trùng (Actor=User, Outcome=Vào được hệ thống)
- Gộp "Đăng xuất" vào "Account Access"          — Test A: cùng cụm capability "Account Access"
- Gộp "Xem BĐS đề xuất" vào "Property Mgmt"     — Test B: không có outcome độc lập, chỉ là lối vào
- GIỮ TÁCH "Seminar Booking" khỏi "Payment"     — Test F: thuật ngữ cốt lõi khác (Seminar vs Transaction), actor sở hữu khác
→ Sitemap Phần C giữ đủ 11 mục gốc dưới dạng Hành động (rule "gộp = đổi tầng")
```

**⚠️ Rule "GỘP = ĐỔI TẦNG HIỂN THỊ, KHÔNG PHẢI XOÁ THÔNG TIN" (BẮT BUỘC):**

> Đây chính là lý do agent hay ngại gộp (sợ mất thông tin của stakeholder) rồi để N phình to.

Mọi candidate bị gộp ở Phần A **PHẢI xuất hiện lại** ở ít nhất 1 trong 2 chỗ:
- **Phần C — Sitemap WBS level 3 (Hành động)** — mặc định
- **1 Trigger box phụ** trong flow cha ở Phần A — khi candidate là 1 điểm vào khác

Gộp ở Phần A **không được làm mất bất kỳ mục nào** khỏi Phần C. Verify bằng phép đếm:
`số mục Hành động ở Sitemap` **≥** `số candidate thô trong Flow Candidate Matrix`

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
