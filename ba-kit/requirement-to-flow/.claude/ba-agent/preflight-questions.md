# BA Agent — Preflight Questions Detail (Bước 2b)

> **Scope:** Chi tiết 8 câu preflight (0.4 Scope · 0 Platform · 0.5 Figma URL · 0.8 Tech stack · 0.9 Granularity · 0.10 Actors · 0.11 Ngôn ngữ · 0.12 PII) + 10 câu checklist chuẩn + Discovery Brief.
> **Dùng ở:** `ba-agent.md` Bước 2b — agent body chỉ giữ bảng tóm tắt + reference file này khi cần copy enforcement/template chi tiết.
> **Thứ tự hỏi BẮT BUỘC:** 0.4 → 0 → 0.5 → 0.8 → 0.9 → 0.10 → 0.11 → 0.12 → 10 câu chuẩn 1-10 → **in Discovery Brief + chờ user confirm**. Không đảo, không skip.

---

## Câu 0.4 — Scope (hỏi ĐẦU TIÊN)

**Câu hỏi trình user:**

```
Feature này thuộc scope nào?
  [A] Chức năng đơn lẻ — 1 use-case cụ thể
      (VD: 'Đăng ký tài khoản', 'Reset password')
  [B] Cụm chức năng — nhiều use-case liên quan trong 1 domain
      (VD: 'Quản lý đơn hàng' gồm List/Detail/Cancel/Refund)
  [C] Toàn hệ thống — cross-domain, nhiều actor, nhiều flow
      (VD: hệ thống multi-module có 5+ flows như Auth / User Mgmt / Payment / Notification / Reporting)
```

**Lưu:** `SCOPE_TYPE`

**Quyết định logic ở Bước 5:**

| SCOPE_TYPE | Behavior ở Bước 5 Gate B1/B2 |
|---|---|
| `[A]` Single flow | Output 1/2/3 vẽ liền mạch — KHÔNG hỏi gate scope |
| `[B]` Cụm | Sau Output 1 hỏi Gate B1 "vẽ Output 2 toàn bộ N flows hay chỉ 1 flow"; sau Output 2 hỏi Gate B2 tương tự |
| `[C]` Toàn hệ thống | Same as `[B]` — bắt buộc Gate B1 + B2 |

**⚠️ Enforcement:**
- Nếu user CHƯA trả lời → **DỪNG**, không tự đoán scope
- KHÔNG được assume `[A]` chỉ vì "feature nghe có vẻ nhỏ"

---

## Câu 0 — Platform target (hỏi thứ HAI)

**Câu hỏi trình user:**

```
Feature này thiết kế cho platform nào?
(Mobile app / Web app / Website / iPad-Tablet)
```

**Lưu:** `TARGET_PLATFORM` — quyết định viewport Output 3 và Responsive Requirements

**Skip khi:**
- SPEC / user đã ghi rõ (ví dụ "app mobile cho User + web cho Admin") → tự extract từ context
- Feature multi-platform (VD: 1 phần mobile + 1 phần web) → hỏi rõ TỪNG NHÓM screens thuộc platform nào, ghi vào cột "App" trong bảng `## Screens`

**⚠️ Enforcement Câu 0:**
- Nếu user CHƯA trả lời VÀ SPEC / context CŨNG chưa có → **DỪNG trước Bước 4**
- KHÔNG tự đoán platform, KHÔNG viết `## Responsive Requirements` với breakpoint tự chọn
- Hỏi lại đến khi có answer

**Mapping platform → viewport CHUẨN CỨNG (không tự đổi):**

| Platform | Viewport (W×H) | Ghi chú |
|---|---|---|
| Mobile app | **375×812** | iPhone standard — dùng cho native iOS/Android |
| Web app (mobile-first PWA) | **375×812** | Same as mobile — web responsive mobile-first |
| Website (desktop) | **1440×1024** | Desktop standard |
| iPad / Tablet | **1024×768** | Landscape tablet |

**Áp dụng:**
- Output 3 mockup phone/screen dùng đúng viewport size theo `TARGET_PLATFORM`
- Bảng `## Responsive Requirements` liệt kê breakpoint tương ứng
- Nếu 1 feature có nhiều platform → mỗi group screens dùng viewport riêng, ghi rõ trong Screen Details

---

## Câu 0.5 — Figma URL (hỏi thứ BA)

**Câu hỏi trình user:**

```
Bạn có Figma Design file để tôi đặt output không?
(URL dạng `figma.com/design/...`)
```

**Lưu:** `FIGMA_OUTPUT_URL` — dùng xuyên suốt Output 1/2/3

**Fallback nếu chưa có tại thời điểm hỏi:** tiếp tục Bước 4 tạo SPEC.md (không cần Figma), NHƯNG **nhắc lại trước Bước 5**.

**⚠️ Enforcement Câu 0.5 (áp dụng khi bắt đầu Bước 5 — vẽ Figma):**

Phân biệt 3 câu trả lời của user + xử lý khác nhau:

| User answer | Xử lý |
|---|---|
| **"Có/Yes"** nhưng CHƯA dán URL (VD: "có mà chờ tôi lấy") | ⚠️ **DỪNG hoàn toàn, KHÔNG được auto-skip, KHÔNG tự chạy tiếp Output 1**. Hiển thị: `⏸ Đang chờ Figma URL từ bạn. Vui lòng paste URL dạng \`figma.com/design/...?node-id=...\` để BA tiếp tục Bước 5.` Chờ đến khi user paste URL mới chạy tiếp. Nếu user quên → nhắc lại mỗi turn kế. TUYỆT ĐỐI không suy diễn "chắc user không cần" rồi skip. |
| **"Không/Refuse"** rõ ràng (VD: "khỏi, không cần Figma") | Skip Output 1-3, ghi vào bảng status: "❌ Skipped — user refuse cung cấp Figma URL". Vẫn chạy Output 0 (SPEC.md) + Output 4 (HTML Prototype). |
| **URL trỏ `/board/`** (FigJam) khi user muốn vẽ high-fi mockup | Warn user, xác nhận có muốn dùng FigJam không (Output 3 cần Figma Design `/design/` để đúng chuẩn viewport). Chờ user confirm hoặc paste URL Design mới. |

- Không được tự chọn Figma file khác. Không được tự tạo file mới không hỏi.
- Nếu user để trống ≥ 2 turn liên tiếp mà không phản hồi → hỏi thẳng: **"Bạn muốn (a) tiếp tục chờ, (b) skip Figma output, hay (c) tôi tự tạo Figma file mới?"** — chờ chọn 1 trong 3 mới action.

---

## Câu 0.8 — Tech stack cho Technology Table (hỏi thứ TƯ)

> **Lý do BẮT BUỘC:** Output 1 Phần B là **Technology Table 8-10 dòng** (`figma-outputs/output-1-flow.md`). Trước rule này KHÔNG có câu hỏi nào cung cấp dữ liệu tech → BA buộc phải tự bịa tech stack, vi phạm chính `rules/RELIABILITY.md` của kit. Đây là lỗ hổng phát hiện khi audit.

**Câu hỏi trình user:**

```
Technology Table ở Output 1 cần list 8-10 công nghệ. Dự án đã chốt tech stack chưa?
  [A] Đã chốt — paste danh sách
      (framework / DB / cache / storage / auth / payment / push / 3rd-party)
  [B] Chưa chốt — BA đề xuất, MỌI dòng đánh dấu [PROPOSAL — chờ Tech Lead confirm]
  [C] Không cần Technology Table (chỉ vẽ Business Flow + Sitemap)
```

**Lưu:** `TECH_STACK` + `TECH_STATUS` (`FACT` / `PROPOSAL` / `SKIPPED`)

**⚠️ Enforcement:**

| User chọn | Ứng xử khi vẽ Output 1 Phần B |
|---|---|
| `[A]` | Mọi dòng = `FACT`, ghi nguồn vào `## Source Register` |
| `[B]` | Header bảng BẮT BUỘC ghi `⚠ PROPOSAL — chờ Tech Lead chốt trong Design-Technical.md`, MỌI dòng có badge `⚠` |
| `[C]` | Bỏ Phần B, vẫn vẽ Phần A + C, ghi note trong frame: `Technology Table: skipped theo yêu cầu user` |

- ❌ TUYỆT ĐỐI KHÔNG tự điền tech stack khi user chưa trả lời — kể cả khi "đoán được từ context dự án"

---

## Câu 0.9 — Mức granularity của Output 1 (hỏi thứ NĂM)

> **Lý do:** N business flow hiện do agent tự phán đoán qua Test A/B/F/E — định tính, 2 lần chạy trên cùng 1 requirement có thể ra 2 kết quả khác nhau. Hỏi trực tiếp biến "đoán N" thành "user chọn mức zoom".

**Câu hỏi trình user:**

```
Output 1 vẽ ở mức chi tiết nào?
  [A] Executive — 3-5 flow, gộp tối đa theo capability
      (cho họp stakeholder / báo cáo KH — thấy scope tổng, không sa đà chi tiết)
  [B] Standard — 1 capability = 1 flow  (recommended)
      (cho PM + Tech Lead plan sprint)
  [C] Detailed — 1 use-case = 1 flow
      (khi cần đối chiếu 1-1 với Function Inventory / Estimate)
```

**Lưu:** `FLOW_GRANULARITY`

**Impact xuống Test E (Cardinality Budget) ở `output-1-flow.md`:**

| FLOW_GRANULARITY | Ngưỡng N cảnh báo | Ứng xử khi vượt ngưỡng |
|---|---|---|
| `[A]` Executive | N > 5 | BẮT BUỘC quay lại gộp tiếp, KHÔNG được vẽ khi chưa gộp |
| `[B]` Standard | N > 8-10 | Tự vấn lại theo Test E, phải giải trình nếu vẫn giữ |
| `[C]` Detailed | Không giới hạn cứng | Vẫn phải in Merge Log, nhưng không ép gộp |

**⚠️ Enforcement:** user chưa chọn → mặc định `[B] Standard`, và PHẢI ghi rõ khi trình bảng N flow: `Granularity: [B] Standard (mặc định — bạn có thể đổi sang [A]/[C])`.

---

## Câu 0.10 — Actor inventory + ownership (hỏi thứ SÁU)

> **Lý do:** **Test F — Ubiquitous Language & Ownership Boundary** (`output-1-flow.md`) yêu cầu biết "actor/team nào sở hữu toàn trình" mới chạy được. Trước rule này không câu hỏi nào cung cấp dữ liệu đó → Test F buộc phải đoán, mâu thuẫn với chính nguyên tắc "không đoán mò".

**Câu hỏi trình user:**

```
Liệt kê đầy đủ Actor của scope này (kể cả actor hệ thống):
  - Actor người dùng:  <VD User / Admin / CS / Scout / Reviewer>
  - Actor hệ thống (chạy tự động, không có UI):
                       <VD Cron job / Webhook / Batch / 3rd-party callback>
  - Actor nào là PRIMARY của scope lần này?
```

**Lưu:** `ACTOR_LIST` + `PRIMARY_ACTOR` + `SYSTEM_ACTORS`

**Áp dụng:**
- Cột ACTOR của Output 1 Phần A + level 2 của Sitemap WBS Phần C
- Input BẮT BUỘC cho **Test G** và **Test F** (`output-1-flow.md`)
- Actor hệ thống → Trigger vẽ dạng ⚙ System, KHÔNG vẽ như actor người

**⚠️ Enforcement:** chưa có `ACTOR_LIST` → **KHÔNG được chạy Test F/G**, phải ghi `Test F: SKIPPED — thiếu ACTOR_LIST` và hỏi lại user, tuyệt đối không tự suy ownership.

---

## Câu 0.11 — Ngôn ngữ hiển thị + audience của Figma output (hỏi thứ BẢY)

> **Lý do:** kit nhắc "stakeholder Nhật / BRSE" ở nhiều nơi (Strict Mode, Source Register) nhưng KHÔNG bao giờ hỏi ngôn ngữ label trên Figma. Vẽ xong 3 frame sai ngôn ngữ = vẽ lại từ đầu.

**Câu hỏi trình user:**

```
Figma output (label node, tiêu đề bảng, mô tả) viết bằng ngôn ngữ nào, cho ai đọc?
  Ngôn ngữ: [VN] / [JP] / [EN] / [VN + JP song ngữ]
  Audience: PM nội bộ / BrSE / Khách hàng cuối / Dev-QC
```

**Lưu:** `OUTPUT_LANG` + `OUTPUT_AUDIENCE`

**Áp dụng:**
- `[JP]` / `[VN + JP]` → Screen Name + mô tả 1 dòng viết đúng ngôn ngữ đó; **Screen Code giữ nguyên ASCII** (không dịch)
- Audience = `Khách hàng cuối` → tránh thuật ngữ kỹ thuật trong mô tả node (không viết "API 500", viết "hệ thống lỗi")
- Audience = `Dev-QC` → được phép giữ thuật ngữ kỹ thuật

**⚠️ Enforcement:** chưa trả lời → mặc định `VN` + audience `PM nội bộ`, in rõ dòng này trong Discovery Brief để user kịp đổi trước khi vẽ.

---

## Câu 0.12 — Khai báo PII trong nguồn đầu vào (hỏi CUỐI CÙNG, trước Discovery Brief)

> **Lý do BẮT BUỘC:** hook H06 chỉ bắt được dữ liệu **có hình dạng** (email, SĐT, số thẻ, token). Hai nhóm còn lại — **dữ liệu production** và **dữ liệu KH xác định confidential** — không có hình dạng nào để nhận ra: `orders.csv` trông y hệt `mock_orders.csv`. Chỉ **người** mới biết. Không hỏi ở đây thì không có lớp nào chặn được hai nhóm đó.
>
> Xem `.claude/rules/DATA-PRIVACY.md` §7 (4 lớp phát hiện — câu hỏi này là lớp L3).

**Câu hỏi trình user — hỏi cho TỪNG file/nguồn:**

```
Nguồn `<tên file / URL>` có chứa 秘密情報・個人情報 của khách hàng không?
  [A] Không — dữ liệu mẫu / tài liệu mô tả thuần
  [B] Có PII — tên, email, SĐT, địa chỉ, thông tin member/user thực tế
  [C] Có dữ liệu production — dump, export, log, bản ghi nghiệp vụ thật
  [D] KH đã đánh dấu confidential / 社外秘 / thuộc NDA
  [E] Chưa rõ
```

**Lưu:** `SOURCE_PII[<file>]`

**Xử lý theo câu trả lời:**

| User chọn | BA làm gì |
|---|---|
| `[A]` | Dùng bình thường |
| `[B]` / `[C]` | ✅ Đọc được để hiểu **cấu trúc** và **nghiệp vụ**. ⛔ **Không copy giá trị thật vào bất kỳ output nào** — thay bằng bộ dữ liệu mẫu (`DATA-PRIVACY.md` §4). Ghi vào `## Source Register` cột Note: `PII — chỉ dùng cấu trúc` |
| `[D]` | ⛔ **DỪNG**, hỏi user đã có phê duyệt của PM/KH chưa. Chưa có → không đọc nguồn đó, ghi `BLOCKED — chờ phê duyệt` |
| `[E]` | **Mặc định coi là `[D]`** — confidential cho tới khi có câu trả lời rõ |

**⚠️ Enforcement:**
- Không trả lời → **mặc định `[E]`**, tức là coi như confidential. KHÔNG được assume `[A]` cho nhanh.
- Kết quả khai báo PHẢI in trong Discovery Brief để user sửa nếu BA hiểu nhầm.

---

## Discovery Brief — BẮT BUỘC in 1 lần trước khi sang Bước 4

> **Nguồn ý tưởng:** pattern *"collect inputs via interactive Q&A → generate document → update status"* của skill **BMAD Analyst** trên marketplace. Trước rule này, câu trả lời preflight nằm rải rác trong chat, không có artifact nào để đối chiếu về sau — Strict Mode thiếu đúng audit trail này.

Sau khi hỏi xong toàn bộ (0.4 → 0 → 0.5 → 0.8 → 0.9 → 0.10 → 0.11 → 0.12 → 10 câu chuẩn), BA PHẢI in block dưới rồi **DỪNG chờ user confirm 1 lần duy nhất**:

```
📋 DISCOVERY BRIEF — <Tên feature>

| # | Hạng mục | Giá trị | Nguồn |
|---|---|---|---|
| 0.4 | Scope | <A/B/C> | user |
| 0 | Platform | <...> → viewport <...> | user |
| 0.5 | Figma URL | <URL / chờ / refuse> | user |
| 0.8 | Tech stack | <FACT / PROPOSAL / SKIPPED> | user |
| 0.9 | Granularity | <A/B/C> | user / mặc định B |
| 0.10 | Actors | <list> · Primary: <...> · System: <...> | user |
| 0.11 | Ngôn ngữ / Audience | <VN/JP/EN> · <audience> | user / mặc định VN |
| 0.12 | PII trong nguồn | <xem bảng khai báo dưới> | user |
| 1-10 | 10 câu chuẩn | <tóm tắt 1 dòng mỗi câu; câu chưa trả lời ghi ⚠ CHƯA CÓ> | user |

Khai báo PII theo từng nguồn (BẮT BUỘC — sửa nếu BA hiểu nhầm):

| File / nguồn | Chứa PII? | Rule áp dụng | Được dùng để lấy |
|---|---|---|---|
| <tên file / URL / "chat với user"> | <A Không / B PII / C Production / D Confidential / E Chưa rõ> | <dùng bình thường / chỉ dùng cấu trúc / BLOCKED chờ duyệt> | <scope / rule / navigation / visual> |

Mode gate dự kiến: <Light / Strict> · Số gate sẽ hỏi: <2 / 5>
Hạng mục còn thiếu: <list — hoặc "không thiếu">

→ Xác nhận đúng chưa? (reply "OK" để BA bắt đầu viết SPEC, hoặc sửa hạng mục nào sai)
```

**⚠️ Enforcement:**
- ❌ KHÔNG được sang Bước 4 khi chưa in Discovery Brief và chưa có confirm của user
- Hạng mục `⚠ CHƯA CÓ` → ghi thẳng vào `## Source Register` của SPEC với classification `UNKNOWN`, KHÔNG tự điền
- Discovery Brief copy nguyên văn vào `versions/v<N>_<DDMMYYYY>/ba-outputs-log.md` làm audit trail
- Nguồn khai `[D]` mà chưa có phê duyệt → **không đọc**, ghi `BLOCKED — chờ phê duyệt` vào `## Source Register`

---

## Rules bắt buộc khi phân loại source input (BẮT BUỘC — áp dụng cùng lúc Bước 1.5)

> Trước khi trình 10 câu checklist, BA PHẢI xác định loại input requirement user đưa vào và enforce 2 rule dưới để tránh hallucination navigation.

### Rule R1 — Cấm suy navigation từ Simple Estimate

**Khi input là Simple Estimate** (file `.xlsx` chỉ có function inventory / cost breakdown, không có flow diagram):

- ❌ TUYỆT ĐỐI KHÔNG suy navigation order từ thứ tự dòng trong Estimate
- ❌ KHÔNG dùng column "Feature Name" → suy Screen Flow
- ✅ CHỈ dùng Estimate để lấy **scope / function inventory** (Function ID / In-scope / Related flow)

**Bắt buộc:** BA PHẢI hỏi user câu 0.6 dưới trước khi bắt đầu Bước 4:

```
Input là Simple Estimate — KHÔNG có Business Overview Flow.
Bạn muốn:
  [A] Cung cấp Raw Overview Flow (paste text / gửi Figma sketch / vẽ tay)
      → BA dùng làm source of truth cho navigation
  [B] BA đề xuất Business Overview Flow từ Function Inventory
      → mọi node/transition sẽ classify là [PROPOSAL — chờ BRSE approve]
  [C] Dừng, quay lại thu thập Raw Overview Flow từ BRSE trước
```

Chờ user chọn 1 trong 3. KHÔNG được tự vẽ flow từ Estimate mà không hỏi. Nếu user chọn `[B]`, BA note rõ trong `## Source Register` mọi row liên quan navigation = `PROPOSAL`.

### Rule R2 — Approved FigJam là navigation source of truth

**Khi input có Approved FigJam** (URL `figma.com/board/...` + user note "đã approve"):

- ✅ FigJam là **navigation source of truth** — mọi flow/transition/screen đặt theo FigJam
- ✅ Requirement khác (SPEC cũ, meeting note, Estimate) chỉ bổ sung **business rule + validation**, KHÔNG được override navigation
- ❌ KHÔNG được âm thầm sửa navigation dù thấy source khác nói khác — phải flag vào `## Source Register` với classification `CONFLICT`

**Bắt buộc verify:** đọc FigJam qua `mcp__plugin_figma_figma__get_metadata` + `get_screenshot` trước khi viết Flow Tổng Quan. Nếu FigJam có node/connector không hiểu → ghi `UNKNOWN` vào Source Register, không tự đoán destination.

### Rule R3 — Existing system / source code / Figma cũ là AS-IS, KHÔNG tự thành TO-BE

**Trigger:** input có 1 trong các source sau (thường gặp khi maintain feature cũ hoặc build phiên bản mới):

- Existing Figma file (Design/HiFi của phiên bản trước)
- Existing source code (screenshot, repo path, exported HTML)
- Existing production URL / staging URL
- Screenshot màn hình app đang chạy

**Rule bắt buộc:**

- ✅ Coi các source trên là **AS-IS evidence** (hiện trạng đang có) — chỉ dùng để hiểu context, business rule đang chạy, edge case đã handle
- ❌ TUYỆT ĐỐI KHÔNG copy AS-IS thành TO-BE mặc định — TO-BE là **đích user muốn đến**, có thể khác AS-IS nhiều
- ❌ KHÔNG generate Output 1/2/3 y hệt phiên bản cũ mà không hỏi user

**Bắt buộc hỏi user câu 0.7 trước Bước 4:**

```
Input có existing system / source cũ (Figma / code / screenshot / URL production).

Bạn muốn BA:
  [A] Dùng AS-IS làm baseline, TO-BE = AS-IS + delta user chỉ định
      → BA sẽ list phần giữ nguyên vs phần thay đổi trước khi viết SPEC
  [B] TO-BE khác AS-IS hoàn toàn (redesign) — chỉ dùng AS-IS để hiểu domain
      → BA chỉ đọc AS-IS làm reference, không copy structure vào Output
  [C] Delta-only — chỉ document phần THAY ĐỔI so với AS-IS, giữ nguyên phần khác
      → SPEC focus vào changeset, không viết lại toàn bộ
```

Chờ user chọn. **KHÔNG được assume `[A]` chỉ vì "có existing → chắc user muốn giữ"**.

**Xử lý theo lựa chọn:**

| User chọn | Ứng xử |
|---|---|
| `[A]` AS-IS baseline | Source Register mọi row AS-IS = `FACT — existing`; mọi row delta user chỉ định = `PROPOSAL` hoặc `FACT` tùy nguồn |
| `[B]` Redesign | Source Register mọi row AS-IS = `INFERENCE — reference only, cần verify TO-BE`; TO-BE viết mới hoàn toàn |
| `[C]` Delta-only | SPEC chỉ có sections liên quan delta; `## BA Deliverables` note rõ "Delta of `<phiên bản AS-IS>`"; Traceability Matrix chỉ trace row mới/đổi |

**Anti-pattern NGHIÊM CẤM:**
- ❌ Đọc Figma cũ → tự vẽ Output 1 y hệt → báo "đã xong theo phiên bản cũ"
- ❌ Screenshot màn hình prod → tự extract items table cho Output 3 → user tưởng đó là TO-BE
- ❌ Existing source code có route `/users/:id` → tự đưa vào Navigation Mapping mà không hỏi TO-BE có giữ route đó không

---

## 10 câu hỏi checklist chuẩn (hỏi sau Câu 0.4/0/0.5)

1. Feature này phục vụ actor nào? (xem danh sách Actors trong `AGENTS.md`)
2. Vấn đề cụ thể đang giải quyết là gì?
3. Điều kiện tiên quyết (phải login? phải có contract? ...)?
4. Happy path chính là gì? (mô tả step by step)
5. Edge cases nào quan trọng cần xử lý?
6. Acceptance criteria — khi nào coi là done?
7. Feature liên quan đến tính năng hiện có nào không?
8. Cần hiển thị / tương tác trên app mobile không (nếu dự án có repo vai trò `mobile`)?
9. Cần real-time không? (WebSocket, push notification)
10. Liên quan tích hợp bên ngoài không? (payment / push / SSO / API bên thứ ba — user phải nêu, BA không tự suy)
