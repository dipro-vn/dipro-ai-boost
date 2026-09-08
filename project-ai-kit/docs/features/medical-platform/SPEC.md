# SPEC: Medical Platform — Nền tảng kết nối y tế

> Figma Design File: https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30633-62845
> Chi tiết screen mapping do Designer agent điền vào cột "Figma Link" trong bảng Screens sau khi thiết kế.

---

## Mô tả nghiệp vụ

Nền tảng kết nối bác sĩ (Doctor) với bệnh viện / cơ sở y tế (Hospital) tại Nhật Bản. Hệ thống hỗ trợ toàn bộ vòng đời tuyển dụng y tế: từ đăng tin tuyển dụng, ứng tuyển, scout (chủ động tiếp cận bác sĩ), đến ký hợp đồng và quản lý sau hợp đồng (tin nhắn, lịch làm việc, đánh giá, tài liệu PDF).

Nền tảng được vận hành bởi Admin (Vận hành nội bộ) và tích hợp với LINE (nhắn tin / thông báo), hệ thống thanh toán (billing), và sinh PDF bất đồng bộ.

Tổng số endpoint: **134** (Doctor: 48, Hospital: 61, Admin: 21, Public: 2, System: 2).

**Hai luồng matching chính:**
1. **Qua ứng tuyển:** Hospital đăng tin → Doctor tìm & ứng tuyển → Hospital duyệt → Hợp đồng thành lập
2. **Qua scout:** Hospital tìm & gửi scout → Doctor chấp nhận → Hospital duyệt → Hợp đồng thành lập

---

## Figma Outputs

> BA Figma outputs cho feature này. Click để xem trực tiếp trên Figma.

| Output | Nội dung | Figma Frame |
|---|---|---|
| **Output 1 — Flow Tổng Quan** | Business Logic Flow (5 flows: Application / Scout / Contract / Admin / LINE) + Technology Table (11 tech items) + Sitemap WBS (5 actors) — **v2: refactor 5 flows gap 120px, không chồng chéo** | [Mở Figma](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30659-48283) |
| **Output 2 — Screen Flow** | v2: 5 screen-flow groups tương ứng 5 business flows Output 1 (Application / Scout / Contract / Admin / LINE) + 1 Bảng Index tổng 56 màn hình (bên phải, spanning) | [Mở Figma](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30665-48283) |
| **Output 3 — Screens + Items v2 Batch 1** | **v2 Batch 1** (20/56 màn hình — user chọn [B] Phased): **Group 1 — Flow Application** (14 screens: DR_AUTH_001..003, DR_HOME_001, DR_JOB_001..004, DR_POLI_001, HO_AUTH_001..002, HO_JOB_001..004) + **Group 2 — Flow Scout partial** (6/9 screens: HO_SCOU_001..004). Viewport Doctor/Hospital = 375×812 Mobile. Layout dọc: phone mockup + bảng ITEMS + bảng ERROR SCENARIOS per screen. | [Mở Figma v2 Batch 1](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30676-48283) |
| **Output 3 — Screens + Items v2 Batch 2** | **v2 Batch 2** (20/56 màn hình tiếp theo — screens 21-40 cumulative): **Group 2 — Flow Scout còn lại** (5 screens: HO_SCOU_005..007, DR_SCOU_001..002) + **Group 3 — Flow Contract** (15 screens: HO_CONT_001..002, HO_MSG_001..003, HO_SETT_001, DR_CONT_001..004, DR_MSG_001, DR_CAL_001, DR_MYPA_001..003). Viewport 375×812 Mobile. Layout dọc + group headers phân màu (Scout=GREEN, Contract=PURPLE). | [Mở Figma v2 Batch 2](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30686-48283) |
| **Output 3 — Screens + Items v2 Batch 3 (FINAL)** | **v2 Batch 3** (17 screens — cumulative total = 56/56 ✅ COMPLETE): **Group 3 — Flow Contract còn lại** (8 screens: DR_MYPA_004..009, DR_NOTI_001, DR_JOB_005) + **Group 4 — Flow Admin** (8 screens: AD_DOCT_001..002, AD_HOSP_001..002, AD_FAQ_001..002, AD_POLI_001..002) + **Supplement** (1 screen: HO_HOME_001 Hospital Dashboard). Admin Portal = Desktop viewport 1440×1024 (represented as 375×812 with desktop sidebar layout). Group 5 LINE = cross-reference note (DR_AUTH_002+003 đã vẽ Batch 1). Layout dọc + group headers phân màu (Contract=PURPLE, Admin=ORANGE, LINE=BLUE). | [Mở Figma v2 Batch 3](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30698-48283) |

> **Output 3 Total: 56/56 screens ✅ COMPLETE** — Batch 1 (19) + Batch 2 (20) + Batch 3 (17) = 56 screens khớp với SPEC ## Screens (Doctor 28 + Hospital 20 + Admin 8 = 56).

> Frame Output 3 v1 cũ (3 màn hình đại diện): `30647-48283` — giữ lại để so sánh.
> Frame Output 3 Batch 1 cũ (layout cũ): `30655-48283` — giữ lại để so sánh.
> Frame Output 1 cũ (v1, chồng chéo): `30645-48283` — giữ lại để so sánh, không xóa.
> Frame Output 2 cũ (v1, 3 vùng DA/CA/Non-Happy/Index): `30646-48283` — giữ lại để so sánh, không xóa.

**Figma file gốc:** [ES-Kitchen-phase-2](https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30633-62845)
**Page:** `Project_Demo_BA_AGENT`

---

## Domain Glossary

| Thuật ngữ | Định nghĩa |
|---|---|
| **Tin tuyển (Job)** | Vị trí làm việc do Hospital đăng lên nền tảng, bao gồm điều kiện làm việc, lịch, thù lao |
| **Ứng tuyển (Application)** | Hành động Doctor gửi đơn đăng ký vào 1 Job đang mở |
| **Scout** | Hospital chủ động tiếp cận Doctor đủ điều kiện, gửi lời mời làm việc |
| **Hợp đồng (Contract)** | Thoả thuận làm việc giữa Doctor và Hospital, phát sinh sau khi Application/Scout được duyệt |
| **Điều kiện làm việc (Work Condition)** | Điều khoản cụ thể của hợp đồng: lịch làm, thù lao, loại công việc |
| **PDF Điều kiện** | Tài liệu PDF được sinh bất đồng bộ từ Work Condition của Job, Doctor có thể tải |
| **PDF Hợp đồng** | Tài liệu PDF hợp đồng chính thức giữa Doctor và Hospital |
| **Billing** | Gói trả phí của Hospital để mở khoá chức năng nâng cao (đăng tin, scout...) |
| **Scout Work Condition** | Template điều kiện làm việc dùng riêng cho luồng scout |
| **LINE Webhook** | Sự kiện từ LINE Messaging API khi Doctor/Hospital thực hiện liên kết tài khoản |
| **Policy Version** | Phiên bản điều khoản sử dụng nền tảng, cần Doctor và Hospital đồng ý khi thay đổi |
| **Favorite (Yêu thích)** | Doctor đánh dấu Job để xem lại sau |
| **Block** | Doctor chặn Hospital, Hospital bị chặn sẽ không thể scout Doctor đó |
| **Display ID** | ID hiển thị public của Doctor, dùng khi Hospital xem hồ sơ (ẩn ID nội bộ) |

---

## Actors & Preconditions

### Actors

| Actor | Mô tả | Base URL | Số Endpoint |
|---|---|---|---|
| **Doctor** | Bác sĩ — tìm việc, ứng tuyển, chấp nhận scout, ký hợp đồng | `/doctor` | 48 |
| **Hospital** | Bệnh viện / cơ sở y tế — đăng tin, tuyển dụng, ký hợp đồng, billing | `/hospital` | 61 |
| **Admin** | Vận hành nền tảng nội bộ — quản lý thành viên, điều khoản, FAQ | `/admin` | 21 |
| **Public** | Endpoint công khai không cần auth | `/public` | 2 |
| **System** | Tích hợp ngoài: LINE Webhook, sinh PDF bất đồng bộ | `/webhook`, shared router | 2 |

### Preconditions per Actor

| Actor | Precondition bắt buộc |
|---|---|
| Doctor | Đã đăng ký tài khoản và xác thực; đã liên kết LINE (bắt buộc sau đăng ký); đã đồng ý Policy Version hiện hành |
| Hospital | Đã đăng ký, đã khởi tạo hồ sơ bệnh viện, đã kích hoạt Billing để đăng tin/scout |
| Admin | Đã đăng nhập bằng tài khoản Admin nội bộ |
| Public | Không cần auth |
| System | LINE signature hợp lệ (webhook); job queue hợp lệ (PDF generation) |

---

## Flow Tổng Quan

### Flow 1 — Ứng tuyển (Application)

```
Hospital → Đăng tin tuyển (Job, trạng thái Draft → Published)
         → Phát hành PDF Điều kiện (async)
         → Doctor tìm kiếm / lọc / xem chi tiết Job
         → Doctor ứng tuyển (Application)
         → Hospital xem danh sách ứng tuyển → Duyệt
         → [Duyệt OK] → Hợp đồng thành lập
         → Hospital phát hành PDF Hợp đồng (async)
         → Doctor xem / chấp nhận / hủy Hợp đồng
         → [Chấp nhận] → Tin nhắn · Lịch · Đánh giá

         ↓ [Doctor chưa đủ điều kiện]
    Doctor không thấy Job trong kết quả tìm kiếm

         ↓ [Hospital chưa kích hoạt Billing]
    Không thể đăng tin → Redirect sang trang Billing
```

### Flow 2 — Scout

```
Hospital → Tìm bác sĩ (search by criteria)
         → Xem hồ sơ bác sĩ (Doctor Display ID)
         → [Doctor chưa bị block] → Tạo Scout + gán Work Condition
         → Doctor nhận Scout → Chấp nhận / Từ chối
         → [Chấp nhận] → Hospital duyệt Scout
         → Hợp đồng thành lập → (tiếp theo giống Flow 1)

         ↓ [Doctor đã block Hospital]
    Hospital không thấy Doctor trong kết quả tìm kiếm

         ↓ [Doctor từ chối Scout]
    Scout trạng thái "Rejected" — không tạo Hợp đồng
```

### Flow 3 — Quản lý Hợp đồng (sau khi thành lập)

```
Hospital/Doctor → Xem danh sách Hợp đồng
              → Xem chi tiết (Work Condition, Schedule Requirement)
              → Gửi tin nhắn (Contract Message)
              → Cập nhật lịch / điều kiện (Hospital)
              → Xem PDF Hợp đồng (download)
              → Đánh giá sau khi hoàn thành
```

### Flow 4 — Vận hành (Admin)

```
Admin → Xem danh sách Doctor / Hospital
      → Xem chi tiết + ứng tuyển + scout của từng thành viên
      → Khóa (suspend) Doctor vi phạm
      → Cập nhật Billing của Hospital
      → Quản lý FAQ (tạo / cập nhật / xóa)
      → Quản lý Policy Version (tạo / công khai / lưu trữ)
```

### Flow 5 — Liên kết LINE (System Integration)

```
Doctor → Tạo nonce liên kết LINE → Mở LINE OAuth
       → LINE gửi Webhook → Backend xử lý → Liên kết thành công
       → Thông báo qua LINE được kích hoạt

         ↓ [Hủy liên kết]
    Doctor hủy liên kết → Thông báo LINE bị tắt
```

---

## Happy Path

### HP-1: Doctor ứng tuyển Job thành công

1. Doctor đăng nhập → xem trang chủ / trang tìm kiếm Job
2. Doctor nhập từ khóa / filter điều kiện → nhận kết quả danh sách Job
3. Doctor tap vào Job → xem chi tiết (điều kiện, lịch, thù lao, lợi nhuận dự kiến)
4. Doctor tap "Yêu thích" (tùy chọn) → Job được lưu vào danh sách Favorite
5. Doctor tap "Ứng tuyển" → xác nhận
6. Hệ thống tạo Application → gửi thông báo cho Hospital
7. Doctor xem trạng thái ứng tuyển trong MyPage

### HP-2: Hospital duyệt ứng tuyển → Hợp đồng

1. Hospital nhận thông báo có ứng tuyển mới
2. Hospital vào danh sách ứng tuyển → xem hồ sơ Doctor
3. Hospital bấm "Duyệt" → Hệ thống tạo Contract
4. Hospital phát hành PDF Hợp đồng → sinh bất đồng bộ
5. Hospital gửi tin nhắn thông báo cho Doctor qua Contract Message
6. Doctor nhận thông báo → vào chi tiết Hợp đồng → Chấp nhận
7. Hợp đồng trạng thái "Active"

### HP-3: Hospital scout Doctor

1. Hospital vào trang tìm bác sĩ → nhập tiêu chí (chuyên khoa, kinh nghiệm, vị trí...)
2. Hospital xem hồ sơ Doctor (bằng Display ID)
3. Hospital chọn Scout Work Condition đã tạo sẵn (hoặc tạo mới)
4. Hospital tạo Scout → gửi đến Doctor
5. Doctor nhận thông báo Scout → xem chi tiết → Chấp nhận
6. Hospital vào trang duyệt Scout → Duyệt
7. Hệ thống tạo Contract → tiếp tục như HP-2 (bước 4 trở đi)

### HP-4: Admin quản lý Policy Version

1. Admin tạo phiên bản điều khoản mới (nội dung, ngày hiệu lực)
2. Admin xem preview → Công khai phiên bản
3. Doctor/Hospital đăng nhập → hệ thống kiểm tra Policy Agreement → hiển thị popup đồng ý
4. Doctor/Hospital đồng ý → tiếp tục dùng app
5. Admin lưu trữ phiên bản cũ sau khi phiên bản mới đã có hiệu lực

---

## Alternative Flows & Edge Cases

| ID | Kịch bản | Xử lý |
|---|---|---|
| AF-01 | Doctor ứng tuyển Job đã hết hạn / đã đóng | Nút "Ứng tuyển" disabled, hiển thị trạng thái "Đã đóng" |
| AF-02 | Doctor ứng tuyển Job nhưng đã ứng tuyển trước đó | Hệ thống trả lỗi duplicate, UI hiển thị "Bạn đã ứng tuyển" |
| AF-03 | Hospital chưa kích hoạt Billing cố đăng tin | Redirect sang trang Billing, hiển thị thông báo cần nâng cấp |
| AF-04 | Doctor bị khóa (suspend) cố đăng nhập | Tài khoản không truy cập được, hiển thị thông báo bị khóa |
| AF-05 | Doctor block Hospital, Hospital cố scout | Doctor không xuất hiện trong kết quả tìm kiếm của Hospital đó |
| AF-06 | PDF Điều kiện / Hợp đồng sinh lỗi | Hiển thị trạng thái "Lỗi", có nút "Thử lại" (retry endpoint) |
| AF-07 | Doctor từ chối Scout | Scout chuyển trạng thái "Rejected", không tạo Contract |
| AF-08 | Doctor hủy Hợp đồng đã chấp nhận | Contract chuyển trạng thái "Cancelled", Hospital nhận thông báo |
| AF-09 | Doctor chưa liên kết LINE | Sau đăng ký, hiển thị màn hình yêu cầu liên kết LINE; không thể dùng chức năng chính |
| AF-10 | Policy Version mới được công khai | Lần đăng nhập tiếp theo hiển thị popup buộc đồng ý trước khi tiếp tục |
| AF-11 | LINE Webhook chữ ký không hợp lệ | Hệ thống từ chối, không xử lý event |
| AF-12 | Doctor xem Job của Hospital đã block mình | Assumption: Doctor vẫn thấy Job (block chỉ ngăn scout từ phía Hospital) — TBD |
| AF-13 | Hospital mời nhân viên (Invitation) nhưng email đã tồn tại | Hệ thống trả lỗi duplicate invitation |
| AF-14 | Download PDF khi trạng thái PDF chưa "Ready" | Nút download disabled, hiển thị spinner / trạng thái "Đang tạo..." |

---

## Acceptance Criteria

### AC-Doctor-01: Đăng ký và onboarding

**Given** Doctor chưa có tài khoản
**When** Doctor điền form đăng ký và submit
**Then** Tài khoản được tạo với trạng thái "chờ liên kết LINE"

**Given** Doctor chưa liên kết LINE
**When** Doctor cố vào trang chính
**Then** Hệ thống redirect sang màn hình yêu cầu liên kết LINE

**Given** Doctor đã liên kết LINE thành công
**When** Doctor vào trang chính lần đầu
**Then** Doctor thấy trang chủ đầy đủ chức năng

### AC-Doctor-02: Tìm kiếm và ứng tuyển Job

**Given** Doctor đã đăng nhập đầy đủ
**When** Doctor tìm kiếm Job với filter (chuyên khoa, vị trí, mức lương)
**Then** Danh sách Job hiển thị đúng điều kiện lọc, có pagination

**Given** Doctor xem chi tiết Job
**When** Doctor tap "Xem lợi nhuận dự kiến tối đa"
**Then** Hệ thống hiển thị số liệu lợi nhuận dự kiến dựa trên thông tin hồ sơ Doctor

**Given** Doctor chưa ứng tuyển Job này
**When** Doctor tap "Ứng tuyển" và xác nhận
**Then** Application được tạo, Doctor thấy xác nhận thành công, Hospital nhận thông báo

### AC-Doctor-03: Hợp đồng

**Given** Hospital duyệt ứng tuyển / scout
**When** Doctor vào danh sách Hợp đồng
**Then** Hợp đồng mới xuất hiện với trạng thái "Chờ chấp nhận"

**Given** Doctor xem chi tiết Hợp đồng
**When** Doctor tap "Chấp nhận hợp đồng"
**Then** Hợp đồng chuyển trạng thái "Active", Hospital nhận thông báo

**Given** Doctor muốn tải PDF Điều kiện làm việc của Job
**When** PDF đã sinh xong (trạng thái "Ready")
**Then** Doctor tải được file PDF về thiết bị

### AC-Hospital-01: Đăng tin tuyển và quản lý ứng tuyển

**Given** Hospital đã kích hoạt Billing
**When** Hospital tạo và đăng tin tuyển
**Then** Tin tuyển hiển thị cho Doctor tìm kiếm; PDF Điều kiện được sinh bất đồng bộ

**Given** Doctor ứng tuyển vào Job của Hospital
**When** Hospital vào danh sách ứng tuyển
**Then** Hiển thị đầy đủ hồ sơ Doctor, có nút "Duyệt"

**Given** Hospital bấm "Duyệt" ứng tuyển
**When** Hệ thống xử lý
**Then** Contract được tạo với trạng thái "Chờ chấp nhận của Doctor"

### AC-Hospital-02: Scout

**Given** Hospital tìm bác sĩ phù hợp
**When** Hospital tạo Scout với Work Condition và gửi cho Doctor
**Then** Doctor nhận thông báo Scout; Scout xuất hiện trong danh sách của Doctor

**Given** Doctor chấp nhận Scout
**When** Hospital vào trang duyệt Scout
**Then** Scout hiển thị trạng thái "Chờ duyệt"; Hospital có thể duyệt để tạo Contract

### AC-Admin-01: Quản lý thành viên

**Given** Admin truy cập danh sách Doctor/Hospital
**When** Admin tìm kiếm và xem chi tiết thành viên
**Then** Admin thấy toàn bộ thông tin (ứng tuyển, scout, hợp đồng liên quan)

**Given** Doctor vi phạm quy định nền tảng
**When** Admin khóa tài khoản Doctor
**Then** Doctor không thể đăng nhập; nếu đang đăng nhập thì bị logout ngay lần request tiếp theo

### AC-Admin-02: Policy Version

**Given** Admin tạo phiên bản điều khoản mới và công khai
**When** Doctor/Hospital đăng nhập lần tiếp theo
**Then** Hệ thống hiển thị popup đồng ý điều khoản; không thể bỏ qua

**Given** Admin lưu trữ phiên bản điều khoản cũ
**When** Doctor/Hospital xem lịch sử điều khoản
**Then** Phiên bản cũ có nhãn "Đã lưu trữ" và chỉ đọc

### AC-System-01: PDF Generation

**Given** Hospital phát hành yêu cầu sinh PDF
**When** Job queue xử lý
**Then** PDF được sinh trong vòng 5 phút; trạng thái cập nhật từ "Đang xử lý" → "Ready"

**Given** PDF sinh lỗi
**When** Hospital/Doctor xem trạng thái
**Then** Hiển thị trạng thái "Lỗi" với nút "Thử lại"

### AC-System-02: LINE Integration

**Given** Doctor thực hiện liên kết LINE
**When** LINE Webhook nhận sự kiện liên kết thành công
**Then** Backend cập nhật trạng thái liên kết, Doctor nhận xác nhận

---

## Business Rules & Constraints

| ID | Rule |
|---|---|
| BR-01 | Hospital phải kích hoạt Billing (trả phí) trước khi đăng tin tuyển và sử dụng chức năng Scout |
| BR-02 | Doctor phải liên kết LINE sau khi đăng ký mới được dùng chức năng chính |
| BR-03 | Một Job chỉ có thể có 1 Application từ 1 Doctor tại 1 thời điểm (no duplicate) |
| BR-04 | Doctor bị block Hospital thì không xuất hiện trong kết quả tìm kiếm Scout của Hospital đó |
| BR-05 | Doctor bị Admin khóa không thể đăng nhập và mọi session hiện tại bị vô hiệu hóa |
| BR-06 | PDF được sinh bất đồng bộ — không đồng bộ với request; UI phải polling trạng thái |
| BR-07 | Contract chỉ được tạo khi ứng tuyển HOẶC scout được duyệt — không tạo trực tiếp |
| BR-08 | Doctor và Hospital đều phải đồng ý Policy Version hiện hành trước khi dùng dịch vụ |
| BR-09 | Doctor có thể block nhiều Hospital; Hospital bị block không nhận scout được Doctor đó |
| BR-10 | Lời mời (Invitation) của Hospital dùng để mời nhân viên nội bộ vào tài khoản Hospital |
| BR-11 | Đánh giá Hợp đồng chỉ được thực hiện sau khi hợp đồng hoàn thành (trạng thái "Completed") — TBD |
| BR-12 | LINE Webhook phải xác minh chữ ký trước khi xử lý (HMAC validation) |

---

## Data Entities (High-Level)

### Doctor

| Field | Mô tả |
|---|---|
| `id` | ID nội bộ |
| `displayId` | ID hiển thị public (dùng cho Hospital xem hồ sơ) |
| `profile` | Hồ sơ: chuyên khoa, kinh nghiệm, chứng chỉ, thu nhập mong muốn, loại công việc |
| `lineStatus` | Trạng thái liên kết LINE: `not_linked` / `linked` |
| `status` | Trạng thái: `active` / `suspended` |
| `policyAgreement` | Phiên bản điều khoản đã đồng ý gần nhất |
| `blockedHospitals` | Danh sách Hospital bị Doctor này chặn |
| `calendarId` | ID lịch làm việc của Doctor |
| `files` | Tài liệu upload (chứng chỉ, hồ sơ) |
| `notificationSettings` | Cài đặt thông báo LINE |

### Hospital

| Field | Mô tả |
|---|---|
| `id` | ID nội bộ |
| `profile` | Thông tin bệnh viện: tên, địa chỉ, chuyên khoa, ảnh |
| `billingStatus` | Trạng thái billing: `free` / `paid` / `trial` |
| `platformContract` | Hợp đồng nền tảng |
| `staff` | Danh sách nhân viên (từ Invitation) |
| `notificationSettings` | Cài đặt thông báo |

### Job (Tin tuyển)

| Field | Mô tả |
|---|---|
| `id` | ID tin tuyển |
| `hospitalId` | Hospital tạo tin |
| `status` | `draft` / `published` / `closed` |
| `workCondition` | Điều kiện làm việc chi tiết |
| `workConditionPdf` | Trạng thái PDF điều kiện: `pending` / `processing` / `ready` / `error` |
| `scheduleRequirement` | Yêu cầu lịch làm |

### Application (Ứng tuyển)

| Field | Mô tả |
|---|---|
| `id` | ID ứng tuyển |
| `jobId` | Job được ứng tuyển |
| `doctorId` | Doctor ứng tuyển |
| `status` | `pending` / `approved` / `rejected` |
| `createdAt` | Thời gian ứng tuyển |

### Scout

| Field | Mô tả |
|---|---|
| `id` | ID scout |
| `hospitalId` | Hospital tạo scout |
| `doctorId` | Doctor được scout |
| `workConditionId` | Điều kiện làm việc áp dụng |
| `status` | `sent` / `accepted` / `rejected` / `pending_approval` / `approved` |

### Contract (Hợp đồng)

| Field | Mô tả |
|---|---|
| `id` | ID hợp đồng |
| `hospitalId` | Hospital |
| `doctorId` | Doctor |
| `sourceType` | `application` / `scout` |
| `status` | `pending_doctor` / `active` / `cancelled` / `completed` |
| `workCondition` | Điều kiện làm việc đã thoả thuận |
| `scheduleRequirement` | Yêu cầu lịch |
| `pdf` | Trạng thái PDF hợp đồng |
| `evaluation` | Đánh giá sau hoàn thành |
| `messages` | Danh sách tin nhắn |

### PolicyVersion (Điều khoản)

| Field | Mô tả |
|---|---|
| `id` | ID phiên bản |
| `content` | Nội dung điều khoản |
| `status` | `draft` / `published` / `archived` |
| `effectiveDate` | Ngày có hiệu lực |

### Notification

| Field | Mô tả |
|---|---|
| `id` | ID thông báo |
| `recipientId` | ID người nhận (Doctor/Hospital) |
| `type` | Loại thông báo |
| `readAt` | Thời điểm đọc (null nếu chưa đọc) |

---

## User Stories per Actor

### Doctor

| Story | Mô tả |
|---|---|
| D-US-01 | Là Doctor, tôi muốn đăng ký tài khoản và liên kết LINE để bắt đầu dùng nền tảng |
| D-US-02 | Là Doctor, tôi muốn tìm kiếm và lọc tin tuyển theo chuyên khoa, vị trí, thù lao |
| D-US-03 | Là Doctor, tôi muốn xem chi tiết Job và lợi nhuận dự kiến để quyết định ứng tuyển |
| D-US-04 | Là Doctor, tôi muốn lưu yêu thích Job để xem lại sau |
| D-US-05 | Là Doctor, tôi muốn ứng tuyển vào Job và theo dõi trạng thái |
| D-US-06 | Là Doctor, tôi muốn xem danh sách Scout nhận được và chấp nhận / từ chối |
| D-US-07 | Là Doctor, tôi muốn xem và chấp nhận / hủy Hợp đồng |
| D-US-08 | Là Doctor, tôi muốn nhắn tin với Hospital qua giao diện Contract Message |
| D-US-09 | Là Doctor, tôi muốn quản lý lịch làm việc và ngày lễ |
| D-US-10 | Là Doctor, tôi muốn tải PDF Điều kiện và PDF Hợp đồng |
| D-US-11 | Là Doctor, tôi muốn đánh giá Hospital sau khi hợp đồng hoàn thành |
| D-US-12 | Là Doctor, tôi muốn chặn Hospital để không nhận scout từ họ nữa |
| D-US-13 | Là Doctor, tôi muốn quản lý cài đặt thông báo LINE |
| D-US-14 | Là Doctor, tôi muốn upload và quản lý tài liệu chứng chỉ |
| D-US-15 | Là Doctor, tôi muốn hủy tài khoản khi không dùng nữa |

### Hospital

| Story | Mô tả |
|---|---|
| H-US-01 | Là Hospital, tôi muốn đăng ký tài khoản và thiết lập hồ sơ bệnh viện |
| H-US-02 | Là Hospital, tôi muốn kích hoạt Billing để đăng tin và sử dụng scout |
| H-US-03 | Là Hospital, tôi muốn tạo và đăng tin tuyển với điều kiện làm việc rõ ràng |
| H-US-04 | Là Hospital, tôi muốn phát hành PDF Điều kiện để Doctor tải về tham khảo |
| H-US-05 | Là Hospital, tôi muốn xem danh sách ứng tuyển và duyệt Doctor phù hợp |
| H-US-06 | Là Hospital, tôi muốn tìm kiếm bác sĩ và gửi Scout |
| H-US-07 | Là Hospital, tôi muốn thiết lập Scout Work Condition làm template |
| H-US-08 | Là Hospital, tôi muốn duyệt Scout sau khi Doctor chấp nhận |
| H-US-09 | Là Hospital, tôi muốn quản lý Hợp đồng đang hoạt động |
| H-US-10 | Là Hospital, tôi muốn phát hành PDF Hợp đồng chính thức |
| H-US-11 | Là Hospital, tôi muốn nhắn tin với Doctor và dùng template có sẵn |
| H-US-12 | Là Hospital, tôi muốn cập nhật điều kiện làm việc và lịch của hợp đồng |
| H-US-13 | Là Hospital, tôi muốn mời nhân viên nội bộ vào tài khoản Hospital |
| H-US-14 | Là Hospital, tôi muốn xem và cập nhật cài đặt thông báo |

### Admin

| Story | Mô tả |
|---|---|
| A-US-01 | Là Admin, tôi muốn xem toàn bộ danh sách Doctor/Hospital và chi tiết từng thành viên |
| A-US-02 | Là Admin, tôi muốn khóa tài khoản Doctor vi phạm |
| A-US-03 | Là Admin, tôi muốn cập nhật Billing của Hospital khi cần thiết |
| A-US-04 | Là Admin, tôi muốn tạo, chỉnh sửa và xóa FAQ |
| A-US-05 | Là Admin, tôi muốn tạo và công khai phiên bản điều khoản mới |
| A-US-06 | Là Admin, tôi muốn lưu trữ phiên bản điều khoản cũ |

---

## Screens

> Figma File: https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/ES-Kitchen-phase-2?node-id=30633-62845
> Chi tiết screen mapping do Designer agent điền vào cột "Figma Link" bên dưới sau khi hoàn thành thiết kế.

> Tổng: 56 màn hình chính (*một số nhóm màn hình dùng chung pattern, Designer sẽ xác nhận screen count thực tế)

### Doctor Screens (28 màn hình)

| Screen Code | Screen | Actor | App | Screen Type | Transition To | Figma Link |
|---|---|---|---|---|---|---|
| DR_AUTH_001 | Đăng ký Doctor | Doctor | Doctor App | Form | → DR_AUTH_002 | TBD |
| DR_AUTH_002 | Yêu cầu liên kết LINE | Doctor | Doctor App | Detail | → DR_AUTH_003 | TBD |
| DR_AUTH_003 | Liên kết LINE (OAuth) | Doctor | Doctor App | Wizard | → DR_HOME_001 | TBD |
| DR_HOME_001 | Trang chủ / Dashboard Doctor | Doctor | Doctor App | Dashboard | → DR_JOB_001 / DR_SCOU_001 | TBD |
| DR_JOB_001 | Tìm kiếm / Danh sách Job | Doctor | Doctor App | List | → DR_JOB_002 / DR_JOB_003 | TBD |
| DR_JOB_002 | Filter tìm Job | Doctor | Doctor App | Form | → DR_JOB_001 | TBD |
| DR_JOB_003 | Chi tiết Job | Doctor | Doctor App | Detail | → DR_JOB_004 / DR_JOB_005 | TBD |
| DR_JOB_004 | Xác nhận ứng tuyển (Modal) | Doctor | Doctor App | Modal | → DR_MYPA_001 | TBD |
| DR_JOB_005 | Danh sách yêu thích | Doctor | Doctor App | List | → DR_JOB_003 | TBD |
| DR_SCOU_001 | Danh sách Scout nhận được | Doctor | Doctor App | List | → DR_SCOU_002 | TBD |
| DR_SCOU_002 | Chi tiết Scout + Chấp nhận/Từ chối | Doctor | Doctor App | Detail | → DR_SCOU_001 | TBD |
| DR_CONT_001 | Danh sách Hợp đồng | Doctor | Doctor App | List | → DR_CONT_002 | TBD |
| DR_CONT_002 | Chi tiết Hợp đồng | Doctor | Doctor App | Detail | → DR_CONT_003 / DR_MSG_001 | TBD |
| DR_CONT_003 | Chấp nhận / Hủy Hợp đồng (Modal) | Doctor | Doctor App | Modal | → DR_CONT_001 | TBD |
| DR_CONT_004 | Đánh giá Hợp đồng | Doctor | Doctor App | Form | → DR_CONT_001 | TBD |
| DR_MSG_001 | Tin nhắn Hợp đồng | Doctor | Doctor App | Chat | → DR_MSG_001 | TBD |
| DR_CAL_001 | Lịch làm việc | Doctor | Doctor App | Calendar | — | TBD |
| DR_MYPA_001 | MyPage — Tổng quan | Doctor | Doctor App | Dashboard | → DR_MYPA_002~007 | TBD |
| DR_MYPA_002 | Hồ sơ cá nhân | Doctor | Doctor App | Form | → DR_MYPA_001 | TBD |
| DR_MYPA_003 | Quản lý tài liệu / File | Doctor | Doctor App | List | — | TBD |
| DR_MYPA_004 | Tài khoản LINE | Doctor | Doctor App | Settings | — | TBD |
| DR_MYPA_005 | Cài đặt thông báo LINE | Doctor | Doctor App | Settings | — | TBD |
| DR_MYPA_006 | Danh sách bệnh viện bị chặn | Doctor | Doctor App | List | — | TBD |
| DR_MYPA_007 | FAQ | Doctor | Doctor App | List | — | TBD |
| DR_MYPA_008 | Điều khoản sử dụng | Doctor | Doctor App | Detail | — | TBD |
| DR_MYPA_009 | Hủy tài khoản | Doctor | Doctor App | Form | — | TBD |
| DR_NOTI_001 | Danh sách thông báo | Doctor | Doctor App | List | — | TBD |
| DR_POLI_001 | Popup đồng ý điều khoản | Doctor | Doctor App | Modal | → DR_HOME_001 | TBD |

### Hospital Screens (20 màn hình)

| Screen Code | Screen | Actor | App | Screen Type | Transition To | Figma Link |
|---|---|---|---|---|---|---|
| HO_AUTH_001 | Đăng ký Hospital | Hospital | Hospital App | Wizard | → HO_AUTH_002 | TBD |
| HO_AUTH_002 | Thiết lập Billing | Hospital | Hospital App | Wizard | → HO_HOME_001 | TBD |
| HO_HOME_001 | Trang chủ / Dashboard Hospital | Hospital | Hospital App | Dashboard | → HO_JOB_001 / HO_SCOU_001 | TBD |
| HO_JOB_001 | Danh sách tin tuyển | Hospital | Hospital App | List | → HO_JOB_002 / HO_JOB_003 | TBD |
| HO_JOB_002 | Tạo / Chỉnh sửa tin tuyển | Hospital | Hospital App | Form | → HO_JOB_001 | TBD |
| HO_JOB_003 | Danh sách ứng tuyển | Hospital | Hospital App | List | → HO_JOB_004 | TBD |
| HO_JOB_004 | Chi tiết ứng tuyển + Duyệt | Hospital | Hospital App | Detail | → HO_CONT_001 | TBD |
| HO_SCOU_001 | Tìm bác sĩ | Hospital | Hospital App | List | → HO_SCOU_002 | TBD |
| HO_SCOU_002 | Hồ sơ Doctor (để scout) | Hospital | Hospital App | Detail | → HO_SCOU_003 | TBD |
| HO_SCOU_003 | Tạo Scout | Hospital | Hospital App | Form | → HO_SCOU_004 | TBD |
| HO_SCOU_004 | Danh sách Scout | Hospital | Hospital App | List | → HO_SCOU_005 | TBD |
| HO_SCOU_005 | Duyệt Scout | Hospital | Hospital App | Detail | → HO_CONT_001 | TBD |
| HO_SCOU_006 | Quản lý Work Condition | Hospital | Hospital App | List | → HO_SCOU_007 | TBD |
| HO_SCOU_007 | Tạo / Sửa Work Condition | Hospital | Hospital App | Form | → HO_SCOU_006 | TBD |
| HO_CONT_001 | Danh sách Hợp đồng | Hospital | Hospital App | List | → HO_CONT_002 | TBD |
| HO_CONT_002 | Chi tiết Hợp đồng | Hospital | Hospital App | Detail | → HO_MSG_001 | TBD |
| HO_MSG_001 | Tin nhắn Hợp đồng | Hospital | Hospital App | Chat | → HO_MSG_002 | TBD |
| HO_MSG_002 | Quản lý template tin nhắn | Hospital | Hospital App | List | → HO_MSG_003 | TBD |
| HO_MSG_003 | Tạo / Sửa template | Hospital | Hospital App | Form | → HO_MSG_002 | TBD |
| HO_SETT_001 | Cài đặt bệnh viện (thông tin, billing, thông báo) | Hospital | Hospital App | Settings | — | TBD |

### Admin Screens (8 màn hình)

| Screen Code | Screen | Actor | App | Screen Type | Transition To | Figma Link |
|---|---|---|---|---|---|---|
| AD_DOCT_001 | Danh sách Doctor | Admin | Admin Portal | List | → AD_DOCT_002 | TBD |
| AD_DOCT_002 | Chi tiết Doctor | Admin | Admin Portal | Detail | — | TBD |
| AD_HOSP_001 | Danh sách Hospital | Admin | Admin Portal | List | → AD_HOSP_002 | TBD |
| AD_HOSP_002 | Chi tiết Hospital | Admin | Admin Portal | Detail | — | TBD |
| AD_FAQ_001 | Quản lý FAQ | Admin | Admin Portal | List | → AD_FAQ_002 | TBD |
| AD_FAQ_002 | Tạo / Sửa FAQ | Admin | Admin Portal | Form | → AD_FAQ_001 | TBD |
| AD_POLI_001 | Quản lý Policy Version | Admin | Admin Portal | List | → AD_POLI_002 | TBD |
| AD_POLI_002 | Tạo / Xem / Công khai Policy Version | Admin | Admin Portal | Detail | → AD_POLI_001 | TBD |

---

## Screen Details

### DR_AUTH_001 — Đăng ký Doctor

**Happy Case:**
- Layout: Single-column form
- Components:

| Vị trí | Component | Nội dung | Action |
|---|---|---|---|
| Top | Logo | Logo nền tảng | — |
| Body | Input | Email | — |
| Body | Input | Password (masked) | — |
| Body | Input | Xác nhận password | — |
| Body | Checkbox | Đồng ý điều khoản (link điều khoản) | Mở DR_POLI_001 |
| Bottom | Button primary | "Đăng ký" | Submit → DR_AUTH_002 |
| Bottom | Link | "Đã có tài khoản? Đăng nhập" | → màn hình login |

- Interactions: Button disabled khi form trống hoặc chưa tick Checkbox
- Animation đề xuất: None

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Email đã tồn tại | Toast error | "Email này đã được đăng ký" |
| Password không khớp | Inline error | "Mật khẩu xác nhận không khớp" |
| Mất mạng | Banner | "Không có kết nối mạng. Thử lại." |

---

### DR_AUTH_002 — Yêu cầu liên kết LINE

**Happy Case:**
- Layout: Centered card, thông báo onboarding
- Components:

| Vị trí | Component | Nội dung | Action |
|---|---|---|---|
| Top | Illustration | Hình minh hoạ LINE | — |
| Body | Text | "Vui lòng liên kết LINE để nhận thông báo" | — |
| Body | Text mô tả | Lý do cần LINE | — |
| Bottom | Button primary | "Liên kết LINE ngay" | → DR_AUTH_003 (LINE OAuth) |
| Bottom | Link | "Liên kết sau" | → DR_HOME_001 (giới hạn chức năng) |

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| LINE OAuth thất bại | Toast error | "Liên kết LINE thất bại. Thử lại." |

---

### DR_JOB_001 — Tìm kiếm / Danh sách Job

**Happy Case:**
- Layout: List có search bar và filter chip ở top
- Components:

| Vị trí | Component | Nội dung | Action |
|---|---|---|---|
| Header | Search bar | Placeholder "Tìm theo tên, chuyên khoa..." | Nhập từ khóa |
| Header | Filter chips | Chuyên khoa / Vị trí / Thù lao / Loại hình | → DR_JOB_002 |
| Body | Job card (×N) | Tên Job, Tên Hospital, Chuyên khoa, Thù lao, ngày đăng | → DR_JOB_003 |
| Body | Icon trái tim (per card) | Yêu thích | Toggle yêu thích |
| Footer | Pagination | Page number | — |
| Header right | Badge thông báo | Số thông báo chưa đọc | → DR_NOTI_001 |

- Interactions: Pull-to-refresh, infinite scroll (hoặc pagination)

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Không tìm thấy Job | Empty state | "Không có tin tuyển phù hợp. Thử lọc khác." |
| Mất mạng | Banner | "Không có kết nối. Hiển thị cache cũ." |

---

### DR_JOB_003 — Chi tiết Job

**Happy Case:**
- Layout: Scrollable detail với sticky CTA ở dưới
- Components:

| Vị trí | Component | Nội dung | Action |
|---|---|---|---|
| Header | Nav back | Mũi tên quay lại | → DR_JOB_001 |
| Header right | Icon trái tim | Toggle yêu thích | Toggle |
| Body | Hospital info | Avatar + Tên bệnh viện | — |
| Body | Job title | Tên vị trí | — |
| Body | Tags | Chuyên khoa, loại hình | — |
| Body | Section "Điều kiện làm việc" | Lịch, thù lao, yêu cầu... | — |
| Body | Button "Lợi nhuận dự kiến" | "Xem lợi nhuận tối đa" | Gọi API → hiển thị số liệu |
| Body | Button "Tải PDF Điều kiện" | Link PDF | Tải về (nếu Ready) |
| Sticky bottom | Button primary | "Ứng tuyển ngay" | → DR_JOB_004 (confirm modal) |

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Job đã đóng | Button disabled | "Tin tuyển đã kết thúc" |
| Đã ứng tuyển | Button disabled | "Bạn đã ứng tuyển tin này" |
| PDF chưa ready | Button loading | "Đang tạo PDF..." |
| PDF lỗi | Toast | "PDF lỗi. Liên hệ bệnh viện để yêu cầu lại." |

---

### DR_SCOU_001 — Danh sách Scout nhận được

**Happy Case:**
- Layout: List với filter trạng thái ở top (Tất cả / Chờ xử lý / Đã chấp nhận / Từ chối)
- Components:

| Vị trí | Component | Nội dung | Action |
|---|---|---|---|
| Header | Tab filter | Tất cả / Chờ xử lý / Đã chấp nhận / Từ chối | Lọc list |
| Body | Scout card (×N) | Tên Hospital, Chuyên khoa, ngày gửi, trạng thái | → DR_SCOU_002 |

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Không có scout | Empty state | "Bạn chưa nhận được scout nào" |

---

### DR_CONT_002 — Chi tiết Hợp đồng

**Happy Case:**
- Layout: Tab detail — "Thông tin" / "Tin nhắn" / "Tài liệu"
- Components:

| Vị trí | Component | Nội dung | Action |
|---|---|---|---|
| Header | Nav back | Quay lại | → DR_CONT_001 |
| Body | Status badge | Trạng thái hợp đồng | — |
| Body | Tab "Thông tin" | Work Condition, lịch, Hospital info | — |
| Body | Tab "Tin nhắn" | Shortcut vào Chat | → DR_MSG_001 |
| Body | Tab "Tài liệu" | PDF Hợp đồng — Download | Tải PDF |
| Footer | Button "Chấp nhận" (nếu pending) | CTA xanh | → DR_CONT_003 |
| Footer | Button "Hủy" (nếu active) | CTA đỏ | → DR_CONT_003 (confirm) |

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| PDF chưa ready | Button "Tải PDF" loading | "Đang tạo tài liệu..." |
| PDF lỗi | Button "Thử lại" | "Lỗi tạo PDF. Thử lại." |
| Mất mạng khi chấp nhận | Toast error | "Không thể kết nối. Thử lại." |

---

### HO_JOB_002 — Tạo / Chỉnh sửa tin tuyển

**Happy Case:**
- Layout: Multi-section form (Thông tin cơ bản / Điều kiện làm việc / Lịch)
- Components:

| Vị trí | Component | Nội dung | Action |
|---|---|---|---|
| Header | Nav back | Quay lại | → HO_JOB_001 (confirm nếu có thay đổi) |
| Body | Input | Tên Job | — |
| Body | Select | Chuyên khoa | — |
| Body | Input | Thù lao | — |
| Body | DatePicker | Ngày làm việc | — |
| Body | Rich text area | Mô tả điều kiện | — |
| Footer | Button "Lưu nháp" | Lưu draft | — |
| Footer | Button "Đăng tin" | Publish | → HO_JOB_001 |

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Bỏ trống trường bắt buộc | Inline error | "Trường này không được để trống" |
| Hospital chưa kích hoạt Billing | Banner | "Nâng cấp gói để đăng tin" |

---

### HO_SCOU_002 — Hồ sơ Doctor (để scout)

**Happy Case:**
- Layout: Scrollable profile + sticky CTA "Scout Doctor này"
- Components:

| Vị trí | Component | Nội dung | Action |
|---|---|---|---|
| Header | Avatar + Tên (Display ID) | Thông tin Doctor ẩn danh | — |
| Body | Tags | Chuyên khoa, kinh nghiệm | — |
| Body | Section "Thu nhập mong muốn" | Range mức thu nhập | — |
| Body | Section "Loại hình làm việc" | Full-time / Part-time / LocumTenens | — |
| Sticky bottom | Button "Scout Doctor này" | CTA xanh | → HO_SCOU_003 |

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Doctor đã block Hospital này | Button disabled | "Bác sĩ này không nhận scout từ bệnh viện của bạn" |

---

### AD_DOCT_002 — Chi tiết Doctor (Admin View)

**Happy Case:**
- Layout: Tab detail — "Thông tin" / "Ứng tuyển" / "Scout"
- Components:

| Vị trí | Component | Nội dung | Action |
|---|---|---|---|
| Header | Nav back | Quay lại | → AD_DOCT_001 |
| Body | Doctor info | Tên, email, trạng thái tài khoản, ngày đăng ký | — |
| Body | Tab "Ứng tuyển" | Danh sách ứng tuyển | — |
| Body | Tab "Scout" | Danh sách scout | — |
| Footer | Button "Khóa tài khoản" | Button đỏ (chỉ hiện nếu account active) | Modal xác nhận → PATCH /admin/doctor/{id}/suspend |

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Doctor đã bị khóa | Button "Mở khóa" (nếu có chức năng) | TBD — xem Open Questions OQ-04 |

---

### DR_POLI_001 — Popup đồng ý điều khoản

**Happy Case:**
- Layout: Fullscreen modal, không thể dismiss bằng tap ngoài
- Components:

| Vị trí | Component | Nội dung | Action |
|---|---|---|---|
| Header | Title | "Điều khoản sử dụng đã cập nhật" | — |
| Body | Scrollable content | Nội dung điều khoản mới | Scroll |
| Body | Checkbox | "Tôi đã đọc và đồng ý" | Toggle |
| Footer | Button primary | "Đồng ý và tiếp tục" | Submit → POST /doctor/policy-agreement → DR_HOME_001 |
| Footer | Link | "Xem toàn văn điều khoản" | Mở trang điều khoản |

- Interactions: Button disabled cho đến khi user scroll đến cuối nội dung VÀ tick Checkbox — TBD (xem OQ-06)

**Non-Happy Case:**

| Trigger | Hiển thị | Message |
|---|---|---|
| Mất mạng khi submit | Toast error | "Không thể lưu. Kiểm tra kết nối và thử lại." |

---

## Responsive Requirements

> Dự án có 2 platform riêng biệt: Doctor App và Hospital App (mobile), Admin Portal (web). Xác nhận từ user vẫn là TBD — xem OQ-01.

### Doctor App / Hospital App (Mobile)

| Breakpoint | Screen size | Layout |
|---|---|---|
| Mobile | 390×844 (iPhone 14) | Layout chính — single column |
| Mobile | 430×932 (iPhone 14 Plus) | Scale tương ứng |

### Admin Portal (Web)

| Breakpoint | Screen size | Layout changes |
|---|---|---|
| MacBook | 1440×900 | Layout chuẩn — sidebar + content |
| Wide | 1920×1080 | Mở rộng content area |
| Tablet | 768×1024 | Sidebar thu gọn / collapse |

---

## UX Review Notes

**UX:** Happy path Doctor ứng tuyển Job có 7 bước (Tìm kiếm → Filter → Danh sách → Chi tiết → Confirm → Success). Đề xuất: bỏ confirm modal nếu không có thêm thông tin cần điền; thay bằng bottom sheet 1 tap. Màn hình Scout cho Doctor cần hiển thị Work Condition ngay trong detail để Doctor không phải click nhiều bước để xem điều kiện.

**Information Design:** Trạng thái (Application, Scout, Contract) phải hiển thị nhất quán bằng color-coded badge. Tên trạng thái tiếng Nhật/tiếng Việt cần thống nhất — hiện tài liệu dùng cả hai, Designer cần chốt.

**Performance:** Danh sách Job cần pagination hoặc infinite scroll — không load all-at-once. PDF sinh bất đồng bộ cần UI polling (mỗi 10 giây kiểm tra trạng thái) hoặc WebSocket push khi ready — TBD (xem OQ-02).

---

## Open Questions (Ambiguities — TBD)

| ID | Câu hỏi | Assumption BA đề xuất | Cần xác nhận từ |
|---|---|---|---|
| OQ-01 | Doctor App và Hospital App là 2 app mobile riêng hay 1 app với role-based UI? | Assumption: 2 app riêng (Doctor App / Hospital App) dựa theo tên base URL `/doctor` vs `/hospital` | PM / Tech Lead |
| OQ-02 | PDF trạng thái cập nhật qua polling hay WebSocket / push? | Assumption: Polling mỗi 15 giây khi user đang ở màn hình liên quan; thêm push notification khi PDF ready | Tech Lead |
| OQ-03 | Scout Work Condition và Job Work Condition có cùng schema không? | Assumption: Tương tự nhau nhưng là entity riêng (Scout Condition chỉ dùng cho scout, không liên kết Job) | Tech Lead |
| OQ-04 | Admin có chức năng "Mở khóa" Doctor đã bị suspend không? | Assumption: Không có endpoint mở khóa trong tài liệu này — Admin chỉ có thể suspend. Nếu cần mở khóa thì cần endpoint mới | PM |
| OQ-05 | Hospital có thể xem Doctor profile tự do hay chỉ trong màn hình Scout? | Assumption: Chỉ xem trong luồng Scout (endpoint `/hospital/doctor/{doctorDisplayId}` validator `hospital.scout`) | PM |
| OQ-06 | Popup đồng ý điều khoản có bắt buộc scroll hết nội dung trước khi cho phép đồng ý không? | Assumption: Bắt buộc scroll đến cuối — UX best practice cho legal consent | PM / Legal |
| OQ-07 | Doctor block Hospital thì Doctor có còn thấy Job của Hospital đó trong kết quả tìm kiếm không? | Assumption: Doctor vẫn thấy Job (block chỉ ngăn scout từ Hospital đó đến Doctor) — nhưng cần xác nhận business rule | PM |
| OQ-08 | Khi Hospital bị lock bởi Admin thì các Contract đang active xử lý thế nào? | Assumption: Contract đang active vẫn tiếp tục; Hospital không thể tạo Job / Scout mới | PM / Legal |
| OQ-09 | Invitation (mời nhân viên Hospital) có màn hình quản lý riêng hay nằm trong Settings? | Assumption: Nằm trong Settings của Hospital (không có screen riêng trong API reference) | PM / Designer |
| OQ-10 | Lịch làm việc Doctor (Calendar) tích hợp với Contract Schedule hay độc lập? | Assumption: Doctor có thể thêm lịch thủ công; Contract Schedule là constraint riêng từ Hospital | Tech Lead |

---

## Out of Scope

Những nội dung sau KHÔNG thuộc phạm vi phân tích SPEC này:

- Thiết kế chi tiết Database Schema (thuộc DESIGN.md của Tech Lead)
- API authentication/authorization mechanism chi tiết (JWT, session...) — biết là có nhưng không phải focus
- Màn hình Admin Portal chi tiết (chỉ có 8 màn hình cơ bản — nếu cần mở rộng thì tách SPEC riêng)
- Analytics / Reporting / Dashboard KPI cho Admin
- Quy trình onboarding giải thích từng bước cho Doctor/Hospital sau đăng ký lần đầu (tour guide)
- Payment gateway chi tiết (biết là có billing nhưng gateway cụ thể và flow thanh toán chi tiết chưa trong scope)
- Chức năng rating / review Doctor công khai (endpoint chỉ có đánh giá nội bộ trong contract)
- Tích hợp Google Maps / địa chỉ bệnh viện interactive
- App notification (push) infrastructure (APNs/FCM) — cần DESIGN.md
- Internationalization chi tiết (biết dùng tiếng Nhật nhưng i18n implementation không trong scope BA)
