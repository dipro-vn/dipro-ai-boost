# Ba Agent — Output 1: Flow Tổng Quan

## Output 1 — Flow Tổng Quan (Use case + Technology Table + Sitemap)

> **Không phải screen flow.** Đây là bức tranh **use case**: mỗi flow = 1 use case — Actor nào → đi những bước nào → kết thúc ở đâu (happy) · lỗi / nhánh khác kết thúc ở đâu (non-happy). **Không đưa công nghệ / function / API vào luồng** — công nghệ chỉ nằm ở bảng Technology bên phải (feedback 20/10/2026).

> **Sau khi vẽ xong Output 1 + hỏi user ở Gate A (`AskUserQuestion`):** nếu vẫn còn business rule chưa được trả lời → BẮT BUỘC chạy **Bước 5.4 — Output OQ** (`.claude/ba-agent/open-questions.md`): viết `OQ-REGISTER.md` → export `open_questions.xlsx` bằng script → `n ≤ 20` thì vẽ thêm Figma OQ view, `n > 20` thì chỉ giao xlsx. Chốt rule muộn = phải vẽ lại Output 2/3.

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
6. Verify rule **"gộp = đổi tầng"**: mọi candidate bị gộp đã có mặt ở Sitemap Phần C (nhóm chức năng / màn) hoặc là nhánh / điểm bắt đầu phụ trong use case chưa?
7. Trình bảng N flow + Merge Log cho user xác nhận (đặc biệt khi input là Simple Estimate — kết hợp Rule R1 ở `preflight-questions.md`)
8. Chỉ sau khi user confirm N mới bắt đầu vẽ Phần A

**Merge Log — BẮT BUỘC in, không có log thì KHÔNG được vẽ:**

```
MERGE LOG (N thô: 11 → N chốt: 4 · Granularity: [B] Standard)
- Gộp "Quên mật khẩu" vào "Account Access"     — Test G: trùng (Actor=User, Outcome=Vào được hệ thống)
- Gộp "Đăng xuất" vào "Account Access"          — Test A: cùng cụm capability "Account Access"
- Gộp "Xem BĐS đề xuất" vào "Property Mgmt"     — Test B: không có outcome độc lập, chỉ là lối vào
- GIỮ TÁCH "Seminar Booking" khỏi "Payment"     — Test F: thuật ngữ cốt lõi khác (Seminar vs Transaction), actor sở hữu khác
→ Sitemap Phần C giữ đủ 11 mục gốc dưới dạng nhóm chức năng / màn (rule "gộp = đổi tầng")
```

**⚠️ Rule "GỘP = ĐỔI TẦNG HIỂN THỊ, KHÔNG PHẢI XOÁ THÔNG TIN" (BẮT BUỘC):**

> Đây chính là lý do agent hay ngại gộp (sợ mất thông tin của stakeholder) rồi để N phình to.

Mọi candidate bị gộp ở Phần A **PHẢI xuất hiện lại** ở ít nhất 1 trong 2 chỗ:
- **Phần C — Sitemap (Nhóm chức năng → Màn)** — mặc định
- **1 nhánh / điểm bắt đầu phụ** trong use case cha ở Phần A — khi candidate là 1 điểm vào khác (VD "Quên mật khẩu" = hàng "Nhánh khác" của use case Đăng nhập)

Gộp ở Phần A **không được làm mất bất kỳ mục nào** khỏi Phần C. Verify bằng **phép trừ tập hợp trên FR Register** (KHÔNG phải phép so số lượng):

```
set(FR No. trong FR Register)  −  set(FR No. đã gắn tag trên Sitemap)  =  ∅
```

> ⚠️ **Công thức cũ `số Hành động ở Sitemap ≥ số candidate thô trong Flow Candidate Matrix` đã bị bãi bỏ vì SAI** — Flow Candidate Matrix do chính BA gom từ nguồn, lấy nó làm mốc thì gate tự so với chính mình và luôn PASS. Sự cố thực tế: mốc lấy nhầm 34 nhóm giữa thay vì 58 dòng chức năng → `42 ≥ 34` PASS trong khi 3 chức năng đã biến mất. Chi tiết: `granularity-principles.md` § **GATE FR COVERAGE**.

**Bắt buộc khi vẽ Phần C:** mỗi **nhóm chức năng / màn** mang tag FR No. **trong tên layer** (không hiện chữ trên hình): `GROUP · <nhóm> · #19,20,21`. Chức năng `SYSTEM — không có màn` → nhánh "Hệ thống & tự động" của Sitemap (vẫn gắn tag) + ghi bằng lời trong use case liên quan (`⏱ Tự động: …`).

**In trước khi vẽ (THIẾU ≠ [] → dừng, không vẽ):**

```
FR COVERAGE — Sitemap: <số nhóm> nhóm · phủ <n>/<N> FR · THIẾU: []
```

**Gồm 3 phần trong cùng 1 frame (width 2280–2360px):**

### Phần A — Use case (trái, x = 40..1770)

**1 lane = 1 use case.** Mỗi lane:

```
👤 Actor → ▶ Bắt đầu → bước → ◇ rẽ nhánh → … → ✓ KẾT THÚC          (hàng 0 — happy case)
                         └─ NG (lỗi) → ✗ KẾT THÚC                      (hàng dưới — non-happy)
                ▶ Nhánh khác (đăng ký, quên mật khẩu…) → ✓ KẾT THÚC   (hàng dưới — "Nhánh khác")
```

- Dòng phụ dưới tên lane: **nền tảng / site · mục tiêu của use case** · việc hệ thống tự làm (ghi bằng lời).
- Bước viết theo **điều người dùng làm / thấy** ("Nhập email, mật khẩu", "Chọn ngày → màn mua"). **Cấm** trong lane: tên API, thư viện, bảng DB, SDK, mã màn.
- Mỗi lane bắt buộc: 1 actor · ≥ 1 điểm bắt đầu · ≥ 1 ✓ kết thúc · ≥ 1 non-happy (`◇` → NG → ✗ kết thúc / quay lại bước) — use case thật sự không có lỗi thì ghi lý do N/A ngay dưới tên lane. NG nào cũng phải đi tiếp.
- Tối đa **6 cột vị trí** mỗi hàng (dài hơn → gộp bước); hàng cách nhau ~118px.
- Rule chưa chốt (`INFERENCE` / `UNKNOWN` trong Source Register) → **không** vẽ vào đường đi: khung tím nét đứt "To verify" hoặc chip "CHƯA CHỐT" dưới lane.
- **Không hiện chữ `UNKNOWN` trên Figma** — viết "chưa rõ — chờ BRSE xác nhận" / "chưa xác định". Nhãn `UNKNOWN` chỉ nằm trong SPEC.md (Source Register).

**⚠️ Vertical gap rule (BẮT BUỘC — feedback từ user):** N use case xếp dọc, **gap MIN 100px** giữa 2 lane (có thể kẻ divider 1px `#D0D7DE`). Verify bằng script bbox (`recheck.md` Tiêu chí 7), không bằng mắt.

| Element | Figma shape | Màu |
|---|---|---|
| Actor | Pill (radius = h/2) | Fill `#E8F4FD`, stroke `#0969DA`, tiền tố 👤 |
| Bắt đầu | Pill | Fill `#E8F4FD`, stroke `#0969DA`, tiền tố ▶ |
| Bước | Rectangle `radius: 8` | Fill `#FFFFFF`, stroke `#0969DA` |
| Rẽ nhánh | Rectangle `radius: 20` | Fill `#FFF9EB`, stroke `#F4860C`, tiền tố ◇ |
| NG (lỗi) | Rectangle `radius: 8` + vạch đỏ trái | Fill `#FFF6F5`, stroke `#CF222E`, tiền tố `NG ·` |
| Hệ thống tự động | Rectangle `radius: 8` | Fill `#E8F7EC`, stroke `#1A7F37`, tiền tố ⏱ |
| ✓ Kết thúc | Pill, stroke 3px | Fill `#EDFDF0`, stroke `#1A7F37` |
| ✗ Kết thúc | Pill, stroke 3px | Fill `#FFF6F5`, stroke `#CF222E` |
| To verify | khung bất kỳ | Fill `#FBEEFF`, stroke `#6639BA` nét đứt |
| Arrow happy / lỗi | Line 2px | `#0969DA` / `#CF222E` |

### Phần B — Technology Table (bên phải, x = 1800..2260) — giữ như cũ

- Bảng 2 cột: `Technology | Mô tả mục đích sử dụng` · 8–10 tech (Framework/SDK/Service/Database/Cache/Storage/Auth)
- Header row 32px xanh, data row 60px xen kẽ trắng / `#F6F8FA` · ghi chú cuối: "Tech Lead sẽ chốt lại trong Design-Technical.md" (chưa chốt → `[PROPOSAL — chờ Tech Lead confirm]`)

### Phần C — Sitemap (dưới lane): Site → Actor / vai trò → Nhóm chức năng → Màn

```
[Tên hệ thống / feature]
├── [🛠 Site / nền tảng A — VD Admin web]
│   └── 👤 Admin · Staff
│       ├── Xác thực            → Trang đăng nhập · Trang quên mật khẩu · Trang đặt lại mật khẩu
│       └── Quản lý sản phẩm    → Danh sách · Tạo · Sửa · [Popup] Xác nhận xoá
├── [📱 Site / nền tảng B — VD App người dùng]
│   └── 👤 Người dùng → Tài khoản → Đăng nhập · Đăng ký · …
└── [⚙ Hệ thống & tự động — không có màn]
    └── Gửi mail nhắc · Đồng bộ dữ liệu
```

| Level | Figma shape | Màu | Nội dung |
|---|---|---|---|
| Root | Rectangle `radius: 8` | Fill `#0969DA`, chữ trắng | Tên hệ thống / feature |
| Site / nền tảng | Thanh ngang `radius: 8` | Fill màu site, chữ trắng | Tên site + ghi chú ngắn |
| Actor / vai trò | Pill viền màu site | Fill trắng | 👤 Tên actor (nhiều vai trò dùng chung màn → 1 pill, vai trò ghi trong nhóm) |
| Nhóm chức năng | Card `radius: 6` | Fill `#F6F8FA`, stroke màu site | Danh từ dễ hiểu ("Xác thực", "Đặt chỗ") + "Vai trò: …" + danh sách màn (•) |
| Connector | Line 1–2px | `#8C959F` | Nối cha → con |

**Nguyên tắc điền:** tên nhóm là **danh từ nghiệp vụ**, không phải hành động; tên màn viết dễ hiểu ("Trang đăng nhập"), **không** route / endpoint / mã màn trên hình (mã + FR tag ở tên layer); Popup ghi `[Popup]`; màn chưa chốt chữ tím "(chưa chốt)".
