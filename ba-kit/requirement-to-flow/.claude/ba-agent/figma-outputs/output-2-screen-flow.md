# Ba Agent — Output 2: Screen Flow

## Output 2 — Screen Flow (Merged Branch)

> **Reference:** `examples/final_output_2.png` (= `example_output_2_screen_flow.png`) — flow hợp nhất phân nhánh (NHÁNH A/B) + NG vẽ inline + System (xanh lá) + Edge/Exceptional Panel riêng bên cạnh. **KHÔNG tách cột Happy/Non-Happy** như style cũ.
>
> Chi tiết pixel-level đầy đủ (frame size, x/y offset, code mẫu) nằm ở `.claude/skills/ba-figma-output/SKILL.md` §5. Nội dung file này mô tả cấu trúc chung: Shared Cluster rule, Bảng Screen Index, Terminal Nodes, Exception Matrix.

> **⚠️ Prerequisite:** Output 1 PHẢI vẽ xong trước. Đếm N = số business flows trong Output 1 để làm input cho Output 2.

## Shared Cluster — khi N business flows dùng chung 1 cụm màn hình

Nếu nhiều business flows ở Output 1 đều đi qua CÙNG 1 cụm màn hình dùng chung (VD: 5 flows khác nhau đều cần user Login/Đăng ký trước khi vào) → **KHÔNG lặp lại cụm đó N lần** — gộp thành **1 Group duy nhất**:
- Start node ghi rõ **tất cả N flow nguồn** dẫn vào group này
- Cuối flow, **fan-out** thành N terminal box — mỗi box = 1 flow nguồn, route user quay lại đúng chỗ

Khi đó rule "số groups = số business flows" đổi thành **"số groups = số cụm màn hình độc lập"** (1 cụm có thể phục vụ nhiều flow). Ghi rõ trong report: `Group <X> phục vụ N flows: <list>`.

**Đặt tên Group:** `Group <Module>_<Seq> — <Tên cụm chức năng>` (VD `Group U2 — Regist & Đăng nhập`) — KHÔNG dùng tên business flow gốc, vì group này có thể phục vụ nhiều flow cùng lúc. Group không dùng chung (chỉ 1 flow) vẫn vẽ theo cấu trúc chuẩn, chỉ là N=1 ở Start/Terminal.

## Combined Overview (BẮT BUỘC khi Output 2 có ≥ 2 Group)

> Khi Output 2 có từ 2 Group trở lên, BA PHẢI vẽ thêm phần **Combined** ở **CUỐI frame Output 2** (dưới Group cuối cùng, sau tất cả N Group riêng lẻ) — **sơ đồ gộp các flow lại**, đúng độ chi tiết như `examples/final_output_2.png` (NHÁNH A/B, System node, NG inline, Edge/Exceptional Panel, terminal fan-out). **Nếu chỉ có 1 Group (N=1) → bỏ qua** (Group đó tự nó đã là combined view).
>
> ⚠️ **Vẽ 1 hay nhiều Combined — KHÔNG tự quyết bằng cảm tính:** số lượng quyết định theo **2 tầng L0/L1 + ngưỡng node** ở section *"Vẽ 1 hay nhiều Combined?"* ngay bên dưới. Quy mô nhỏ (≤ 40 node) = đúng 1 Combined Detail như mô tả ở đây; quy mô lớn = 1 Master Map + nhiều Combined Detail theo cụm liên thông.

> ⚠️ **Đây KHÔNG phải navigation map sơ lược.** Combined Overview PHẢI có đầy đủ Decision/System/NG/Edge — vì mục đích của nó là cho stakeholder thấy TOÀN BỘ bức tranh nghiệp vụ (kể cả Non-Happy Case) khi các flow giao nhau/chia sẻ màn hình, chứ không chỉ đường đi giữa các screen.

**Nội dung — đầy đủ như 1 Group bình thường, nhưng GỘP N flow lại:**
- **Start** ghi rõ N flow nguồn dẫn vào (VD "Vào từ N luồng: Login · Đăng ký · Reset password")
- **NHÁNH A / NHÁNH B / …** — mỗi nhánh = 1 flow gốc (hoặc nhóm flow có chung hành vi), vẽ Screen/System/Decision nối tiếp nhau; nơi 2 flow **giao nhau tại cùng 1 screen** (VD cùng quay về Login) → vẽ **1 node duy nhất** cho screen đó, nhiều mũi tên dẫn vào (không vẽ trùng lặp)
- **NG inline**: mọi lỗi FACT của TỪNG flow con vẫn giữ nguyên — gộp lại tại đúng vị trí phát sinh trong nhánh tương ứng (không được bỏ bớt vì lý do "đã vẽ ở Group riêng")
- **System node**: hành động backend dùng chung giữa các nhánh (VD gửi email) vẽ 1 lần, mũi tên từ mọi nhánh cần dùng trỏ vào
- **Edge/Exceptional Panel**: gộp TẤT CẢ case UNKNOWN/INFERENCE của N flow vào 1 panel duy nhất bên cạnh (không tách panel theo từng flow)
- **Merge → fan-out terminal**: cuối cùng fan-out ra các terminal tương ứng từng flow gốc

**Rule bắt buộc:**
- ⚠️ **Mọi node (Start/Screen/Decision/System/NG/Edge/Merge/Terminal) PHẢI nối bằng connector vẽ thật (arrow) — KHÔNG được liệt kê dạng chip/card rời rạc chỉ cách nhau bằng gap, không có đường nối.** Nếu N flow lớn khiến vẽ đủ literal NHÁNH A/B tốn công → dùng "compact chip + spine pattern" (SKILL.md §5.0b: chip nhỏ + arrow nối trong nhánh + spine trái/phải fan-out/fan-in kiểu comb như Sitemap §4.4), KHÔNG được bỏ connector để tiết kiệm effort — đây là lỗi thực tế đã xảy ra, không lặp lại.
- Mọi NG box đã vẽ trong từng Group riêng ở trên PHẢI xuất hiện lại ở đây (Combined Overview = superset, không phải bản rút gọn)
- Mọi screen dùng chung ≥ 2 flow (VD Login) CHỈ vẽ 1 node duy nhất tại đây, nhiều mũi tên vào/ra
- Numbered badge trùng số đã dùng ở Group bên trên (không đánh số lại)
- Vị trí: LUÔN ở cuối frame (sau Group N), có khoảng cách MIN 150px với Group phía trên

**Tiêu đề bắt buộc:** `"Combined Overview — Toàn bộ Flow gộp (N flows merged)"` + subtitle `"Sơ đồ hợp nhất N flow trên — bao gồm đầy đủ Non-Happy/NG, xem chi tiết per-flow ở các Group phía trên"`

**⚠️ Combined Overview BẮT BUỘC có phần Non-Happy — không được chỉ vẽ happy path:**

> Lỗ hổng đã xảy ra thực tế: Combined Overview vẽ xong chỉ có 1 đường spine happy path nối các Group, **không có một NG nào** → user phản hồi "flow combine chưa liên kết toàn bộ screen flow (bao gồm happy case và non-happy case)".

Cấu trúc tối thiểu, đủ 4 tầng từ trên xuống:

| Tầng | Nội dung | Bắt buộc |
|---|---|---|
| 1 — Spine | Happy path xuyên suốt N Group, mỗi node ghi rõ `G<x>` nó thuộc về + nhãn handoff trên arrow giữa 2 Group | ✅ |
| 2 — Decision | Decision ◇ treo DƯỚI đúng node phát sinh rẽ nhánh, nối bằng arrow dọc | ✅ ≥1 decision / Group có rủi ro |
| 3 — NG | NG đỏ nét đứt dưới mỗi decision, nhãn `NO`/`YES` trên đường nối, text ghi rõ **message thật + màn quay lại** | ✅ |
| 4 — Thống kê | 1 block ghi `TỔNG = A màn chính + B màn lỗi/popup = N` + trỏ sang bảng ⑦ | ✅ |

**Rule vị trí terminal (lỗi đã gặp):** terminal box phải nằm **ngay dưới node/arrow nuôi nó**. Vẽ arrow dọc từ node cuối spine ở cạnh phải rồi đặt terminal ở cạnh trái → **mũi tên trỏ vào khoảng trống** = FAIL. Kiểm bằng: `|x_arrow − x_tâm_terminal| < ½ width terminal`.

**Rule đường dữ liệu phụ:** line dashed (VD Admin nhận số liệu) phải chạy ở dải Y **dưới đáy hàng NG**, không được cắt ngang qua các box NG. Kiểm: `y_bus > max(y_đáy tất cả NG box)`.

### ⚠️ Vẽ 1 hay nhiều Combined? — quyết định theo 2 TẦNG, không theo cảm tính

> **Vấn đề gốc:** "đủ mọi item" và "thấy bức tranh tổng thể" là 2 mục tiêu **xung đột trong cùng 1 sơ đồ**. Khi N lớn, ép 1 Combined duy nhất phải là superset đầy đủ → không ai đọc nổi, và đó chính là lúc agent bỏ connector để "tiết kiệm effort" (lỗi đã xảy ra thực tế).

| Tầng | Số lượng | Phục vụ |
|---|---|---|
| **L0 — Master Map** | LUÔN 1 cái | Thấy bức tranh tổng thể (mỗi Group = 1 box gộp, không xổ ruột) |
| **L1 — Combined Detail** | = số **cụm liên thông** (thường 1-3) | Không thiếu sót từng item của từng flow |

**Tiêu chí chia (cơ học):** dựng đồ thị — đỉnh = Group, cạnh = 2 Group dùng chung ≥1 screen. **Số Combined Detail = số thành phần liên thông có ≥2 Group.** Group độc lập không cần Combined riêng.

**Ngưỡng:** tổng node ≤ 40 → 1 Combined Detail (không cần Master Map) · 41-80 → Master Map + 1-2 Combined Detail · > 80 → Master Map + N Combined Detail (mỗi cụm ≤ 40 node).

**Node Coverage Checklist (bắt buộc khi tách > 1 Combined Detail):** `distinct node các Group` = `distinct node các Combined Detail` — mismatch → FAIL.

Chi tiết layout + pixel-level (Master Map, cách vẽ nhánh gộp, node dùng chung) xem `SKILL.md` §5.0 và §5.0b.

---

## ⚠️ Non-Happy Coverage Matrix (BẮT BUỘC — trả lời "số screen đã đủ chưa")

> **Lỗ hổng đã xác định khi audit:** kit có `## Non-Happy Case` trong SPEC và có NG node trong Figma, nhưng **không có bất kỳ phép đối chiếu nào giữa 2 thứ đó**. Bước 4.6 chỉ check *"Non-Happy Case có AC tương ứng"* — không check *"Non-Happy Case có screen/node tương ứng"*. Vì vậy "đủ hay chưa" trước đây hoàn toàn cảm tính.

Bảng đặt cạnh Bảng SCREEN INDEX (cột phải frame). **Mỗi Non-Happy Case trong SPEC = 1 dòng, 100% phải có mặt:**

| NH-ID | Trigger | Screen phát sinh | Cách hiển thị | Cần Screen Code riêng? | NG node ID | Đi đâu sau đó |
|---|---|---|---|---|---|---|
| NH-01 | Sai mật khẩu 3 lần | US_AUTH_001 | Modal | ✅ (có nội dung nghiệp vụ: đếm lần + khoá) | NG-03 | US_AUTH_001 (disabled 5 phút) |
| NH-02 | Mất mạng khi submit | US_AUTH_003 | Toast | ❌ (chỉ là state S06) | NG-05 | Giữ nguyên màn, cho retry |
| NH-03 | Hết phiên đăng nhập | mọi screen | Full screen | ✅ | NG-08 | US_AUTH_001 |

**Rule bắt buộc:**
- Cột **"Cần Screen Code riêng"** quyết định theo bảng phân loại mức hiển thị lỗi ở `spec-template.md` (Inline/Toast/Banner → ❌ · Modal → ⚠️ tuỳ nội dung · Full screen → ✅)
- Dòng nào ✅ mà bảng `## Screens` trong SPEC **chưa có Screen Code tương ứng** → **thiếu screen, phải bổ sung SPEC trước khi vẽ tiếp**
- Mỗi screen có submit/gọi API phải rà đủ **checklist 8 nhóm Non-Happy** (`spec-template.md`): Validation · Auth/session · Network · Server error · Empty · Conflict · Business rule · External integration. Nhóm không áp dụng → `N/A — lý do`; chưa rõ → `UNKNOWN` → vào Edge/Exceptional Panel

**Cross-check số học ở Quality Gate O2 (FAIL nếu sai):**
- `số NG node vẽ ra` ≥ `số Non-Happy Case trong SPEC ## Screen Details`
- `số Screen Code loại màn hình lỗi` = `số dòng có cột "Cần Screen Code riêng" = ✅`

## Bố cục frame Output 2 — Combined Overview (nếu ≥2 Group) + N Groups (1 per business flow, hoặc 1 per shared cluster) + Bảng Index tổng

```
┌─────────────────────────────────────────────────────┬────────────────────┐
│ Group 1 — <Tên cụm/flow 1>                          │                    │
│   Start (▶, ghi rõ N flow nguồn nếu Shared Cluster)  │                    │
│   NHÁNH A ──┐        NHÁNH B ──┐                    │  ④ BẢNG SCREEN     │
│   Screen/System/Decision, NG   │                    │      INDEX         │
│   vẽ inline ngay tại chỗ lỗi   │      Edge/          │  ⑥ TERMINAL NODES  │
│   phát sinh (không tách cột)   │      Exceptional     │  ⑤ EXCEPTION       │
│   ↓ merge point → fan-out N terminal    Panel        │      MATRIX        │
├─────────────────────────────────────────────────────┤  (bên phải,        │
│ Group 2 — <Tên cụm/flow 2>                           │   spanning height  │
│  ...                                                 │   toàn frame)      │
├─────────────────────────────────────────────────────┤                    │
│ Group N — <Tên cụm/flow N>                           │                    │
│  ...                                                 │                    │
├─────────────────────────────────────────────────────┤                    │
│ Combined Detail × <số cụm liên thông> (khi ≥ 2 Group) │                    │
│   Gộp các flow GIAO NHAU: NHÁNH A/B/…, System,       │                    │
│   NG inline (đủ như từng Group ở trên),              │                    │
│   Edge/Exceptional Panel gộp, terminal fan-out       │                    │
│ Master Map (chỉ khi tổng node > 40) — CUỐI frame     │                    │
│   Mỗi Group = 1 box gộp + shared screen + connector  │                    │
└─────────────────────────────────────────────────────┴────────────────────┘
```

**Rule chính:**
- Số Group = số cụm màn hình độc lập ở Output 1 (đã tính gộp Shared Cluster nếu có)
- Mỗi Group đặt vertically stacked, gap MIN 150px giữa 2 Group liên tiếp; Combined Overview đặt SAU Group cuối cùng, cách Group N cũng MIN 150px
- Trong mỗi Group: flow chính (Happy + NG inline) vẽ hợp nhất — KHÔNG tách cột Happy/Non-Happy; case chưa rõ (Edge/Exceptional) tách panel riêng bên cạnh
- **Bảng SCREEN INDEX chỉ 1 bảng tổng duy nhất** đặt bên phải toàn frame, spanning height — tổng hợp toàn bộ screens/popups cho khách hàng

Ví dụ Output 2 cho feature có Shared Cluster (Auth dùng chung 5 flow):

```
Group U2 — Regist & Đăng nhập (phân nhánh gộp: Happy · NG · Edge · Exceptional)
  Vào từ 5 luồng: VAS会員マイページ · IVPエントリー · 無料個別相談 · Lỗi mời sub-account · Lỗi mời seminar
  NHÁNH A — Mail ĐÃ tồn tại (đăng nhập): US_AUTH_001 → Password check → NG nếu sai
  NHÁNH B — Mail CHƯA tồn tại (đăng ký mới): System gửi code → US_AUTH_003 → US_AUTH_004
  Merge: "Luồng gốc đã bắt đầu từ đâu?" → fan-out 5 terminal (US_MYPG_001 / US_ENTR_002 / US_FREE_003 / US_INVT_006 / US_INVT_005)
  Edge/Exceptional Panel: 4 case chưa rõ (mail giả, account dở, mất mạng, bỏ dở giữa flow)
```

## ④ BẢNG SCREEN INDEX (bên phải, spanning toàn frame — DUY NHẤT)

BẮT BUỘC — bảng liệt kê TẤT CẢ màn hình (kể cả Popup) với 3 cột:

| # | Màn hình | Loại | Mô tả chức năng màn hình |
|---|---|---|---|
| 1 | AX_FEAT_001 — Company List | List | Hiển thị danh sách công ty, cho phép chọn để gọi |
| 2 | AX_FEAT_002 — Company Detail | Detail | Xem thông tin + khởi tạo cuộc gọi |
| 3 | AX_FEAT_003 — Outgoing Call | Modal | Chờ đối phương nhận máy (30s) |
| ... | ... | ... | ... |
| 9 | [Popup] Mic Permission | **Popup** | Yêu cầu quyền microphone khi tap Gọi |
| 10 | [Popup] Confirm Cancel | **Popup** | Xác nhận hủy cuộc gọi giữa chừng |

**⚠️ QUY TẮC ĐẾM TOTAL:**
- **Popup CŨNG LÀ MÀN HÌNH** — PHẢI đưa vào bảng và đếm vào total
- Toast/Banner CŨNG đếm (nếu là component riêng, không chỉ là inline notification)
- Tổng cuối bảng: **"Tổng: N màn hình (trong đó X popup + Y toast)"**

**Bảng quy đổi chốt cứng (đồng bộ `spec-template.md` — không diễn giải lại):**

| Loại hiển thị | Đếm vào tổng màn hình? | Vẽ thành NODE trong flow? |
|---|---|---|
| `Full screen` | ✅ | ✅ **BẮT BUỘC** — là màn hình độc lập |
| `Modal` | ✅ | ✅ nếu mang nội dung nghiệp vụ riêng (xác nhận huỷ, cảnh báo phí, conflict…) |
| `Popup` (quyền hệ thống) | ✅ | ✅ |
| `Toast` · `Banner` · `Empty state` | ✅ | ❌ — chỉ liệt kê ở bảng ⑦, vì là overlay/state của màn cha, vẽ hết sẽ vỡ sơ đồ |
| `Inline error` · `Button disabled` · `Tooltip` · `Chặn UI` | ❌ (chỉ là state) | ❌ |

---

## ⑦ BẢNG ERROR / POPUP INDEX (BẮT BUỘC — đặt cột phải, dưới Exception Matrix)

> Lỗ hổng đã xảy ra thực tế: Output 2 chỉ vẽ ~27 NG "đại diện" trong khi SPEC định nghĩa 189 error display → khách hàng không thấy màn lỗi/popup nào được thống kê, và không biết message thật hiển thị ra sao.

Bảng liệt kê **100% error display** trong SPEC (không rút gọn), 4 cột:

| ID | Screen | Hiển thị | Trigger → Message hiển thị |
|---|---|---|---|
| E-003 | CM_AUTH_001 | Modal | Sai 5 lần → "Tài khoản tạm khóa 15 phút" |
| E-042 | PT_SRCH_001 | Empty state | Không có kết quả → "Không tìm thấy phòng khám phù hợp" |

**Rule bắt buộc:**
- ID `E-xxx` **trùng khớp 1-1** với ID đã đánh trong SPEC `## Screen Details`
- ID của loại **được đếm** tô ĐỎ, loại chỉ-là-state tô XÁM → nhìn bảng biết ngay con số tổng đến từ đâu
- Đầu bảng có block thống kê: `ĐẾM là màn hình (B): Toast .. · Modal .. · …` + `TỔNG = A màn chính + B màn lỗi = N`
- Cross-check ở Quality Gate O2: `số dòng bảng ⑦` = `số error display trong SPEC` — lệch → **FAIL**

## ⑧ ERROR-SCREEN STRIP + BADGE ⚠N (BẮT BUỘC)

- Mỗi **Group** có 1 strip nằm NGAY DƯỚI group đó, chứa các error display loại `Full screen` · `Modal` · `Popup` của group, mỗi cái là 1 node: `E-ID` + loại + `◀ <SCREEN_CODE cha>` + message thật. Các node nối vào 1 **bus nét đứt đỏ có mũi tên** đi xuống từng node → thể hiện "phát sinh từ các màn phía trên".
- Mỗi **screen node** trong flow mang badge `⚠N` (N = số error display của màn đó) đặt cạnh Screen Code → nhìn 1 phát biết màn nào nhiều rủi ro nhất.
- Strip đặt trong khoảng trống giữa 2 Group (gap ≥ 150px) → **KHÔNG phải dàn lại layout** của flow đã vẽ.

**Loại (cột 2) — enum:**
`List` · `Detail` · `Form` · `Modal` · `Popup` · `Toast` · `Banner` · `Wizard` · `Dashboard`

## Quy ước visual

| Element | Figma shape | Ghi chú |
|---|---|---|
| Start | Ellipse 32px với icon ▶ | Fill `#0969DA` |
| Numbered badge | Ellipse 24-28px + số | Xanh (Screen) — số **liên tục toàn cục** qua các Group, không reset |
| **Screen** | Rectangle 200-260×70px | Fill `#E8F4FD`, stroke `#0969DA` |
| **Decision** | Rounded-rect, icon ◇ + rationale 1 dòng | Fill `#FFF9EB`, stroke `#F4860C` — label "YES/NO" trên nhánh ra |
| **System** | Rectangle, icon ⚙ | Fill `#EDFDF0`, stroke `#1A7F37` — hành động backend tự động, KHÔNG có numbered badge |
| **NG** | Rectangle nét đứt, icon ⚠, vẽ INLINE ngay tại điểm phát sinh | Fill `#FFF6F5`, stroke `#CF222E` — chỉ dùng cho lỗi đã ĐỊNH NGHĨA rõ (FACT) |
| **Edge / Exceptional** | Rectangle nét đứt, icon ▲, đặt trong panel riêng bên cạnh (KHÔNG inline) | Fill `#FBEEFF`, stroke `#6639BA` — case UNKNOWN/INFERENCE chưa rõ hành vi |
| Terminal box | Rectangle 200×~50px | Fill `#F6F8FA`, stroke `#D0D7DE` — 1 box / flow nguồn (fan-out cuối) |
| Happy/System arrow | Line 2px solid | `#0969DA` |
| NG arrow | Line 2px dashed, ngắn (route tại chỗ) | `#CF222E` |

**⚠️ Rule NG vs Edge (BẮT BUỘC phân biệt):**
- Lỗi đã rõ cách xử lý (validation thông thường, đã có trong Function detail/SPEC, classification `FACT` trong Source Register) → vẽ **NG** inline trong flow chính
- Case CHƯA rõ hành vi, cần BRSE confirm (`UNKNOWN`/`INFERENCE` trong Source Register) → **TUYỆT ĐỐI KHÔNG vẽ inline như NG** — đưa vào **Edge/Exceptional Panel** riêng (SKILL.md §5.6). Vẽ inline sẽ khiến flow chính trông như "đã confirm" trong khi thực ra chưa.

**Format mỗi screen node — PHẢI có 1 dòng mục đích:**
```
┌─────────────────────────────────────┐
│ ① AX_FEAT_001  Company List   List  │
│    Hiển thị DS công ty, chọn để gọi │  ← mục đích 1 dòng
└─────────────────────────────────────┘
```

## ⑥ TERMINAL NODES (BẮT BUỘC — list explicit endpoint mỗi flow)

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
- Nếu Group là Shared Cluster (N flow nguồn) → số terminal box = N = số flow đã liệt kê ở Start
- Row `UNKNOWN` → PHẢI có tương ứng row trong Exception Matrix (⑤) với classification `UNKNOWN`
- Cột "Destination sau terminal" KHÔNG được để trống — nếu chưa rõ ghi `UNKNOWN — chờ BRSE`
- Cross-verification: count terminal box trong flow diagram Figma = count row Terminal Nodes table — mismatch → refactor

**Downstream impact:**
- FE Dev đọc bảng này biết đúng redirect logic sau mỗi endpoint
- QC viết test case cho mỗi terminal (positive + negative)
- TL Design biết endpoint nào cần API call log/analytics

---

## ⑤ EXCEPTION MATRIX (BẮT BUỘC — bổ sung cho Edge/Exceptional Panel, đặt dưới Bảng Index)

> Edge/Exceptional Panel vẽ TRỰC QUAN các case chưa rõ trên Figma. Exception Matrix bổ sung dạng bảng để **phân loại từng exception** theo status: có rule rõ ràng hay chưa, để BA/BRSE biết cần confirm gì trước Phase 3.

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
- Mọi NG box (inline trong flow chính) PHẢI có 1 row Exception Matrix classification `FACT`
- Mọi box trong Edge/Exceptional Panel PHẢI có 1 row Exception Matrix classification `UNKNOWN` hoặc `INFERENCE`
- Row `UNKNOWN` / `CONFLICT` KHÔNG được vẽ như FACT (không vẽ như NG inline trong flow chính) — luôn đưa vào Edge/Exceptional Panel
- Sau Bảng Index + Exception Matrix, BA in ra count summary: `Tổng: N exceptions (FACT: X · PROPOSAL: Y · INFERENCE: Z · UNKNOWN: W · CONFLICT: V)`

**Downstream impact:**
- TL Design đọc row `FACT` để design error handling logic
- QC đọc row `FACT + PROPOSAL` để viết test case
- Row `UNKNOWN + CONFLICT` → PM tạo ticket hỏi BRSE trước khi Phase 3

## AI Suggestion step — nếu feature có AI

Khi flow có bước AI xử lý, vẽ node riêng với icon 🤖:
```
┌─────────────────────────────────────┐
│ 🤖 AI Suggestion                    │
│    <mô tả AI làm gì ở bước này>     │
└─────────────────────────────────────┘
```
Kèm text annotation bên cạnh: "AI dùng model gì, input là gì, output là gì, fallback nếu AI fail".
