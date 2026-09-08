# BA Figma Output Skill (Canonical v2)

> Skill này dạy BA Agent cách tạo **3 outputs** trên Figma Design file (`/design/` URL) theo đúng style đã được user approve.
> **Reference chuẩn:** 3 file trong `examples/`:
> - `final_output_1.png` — Flow Tổng Quan + Sitemap WBS Tree
> - `final_output_2.png` — Screen Flow 3 vùng (Happy · Non-Happy · Bảng Index)
> - `final_output_3.png` — HiFi Screens + bảng liệt kê đầy đủ item
>
> BẮT BUỘC `Read` cả 3 file này trước khi viết use_figma call nào.

---

## 0. Load ngay đầu

```js
await figma.loadFontAsync({family:"Inter", style:"Bold"});
await figma.loadFontAsync({family:"Inter", style:"Regular"});

// Chọn đúng page user cung cấp (KHÔNG tạo page mới)
const targetPage = figma.root.children.find(p => p.name === "<page name>");
await figma.setCurrentPageAsync(targetPage);
```

---

## 1. Color System (chốt cứng)

```js
const cv = (r,g,b) => ({r:r/255, g:g/255, b:b/255});

// Core palette
const WHITE   = cv(255,255,255);
const BGL     = cv(246,248,250);     // background xám nhạt
const BGDK    = cv(26,31,46);        // dark screen bg (call screens)

// Actor colors
const BLUE    = cv(9,105,218);       // Dipro Admin
const BLUELT  = cv(229,246,255);
const GREEN   = cv(26,127,55);       // Company Admin
const GREENLT = cv(237,253,240);
const GREENDOT= cv(26,127,55);
const ORANGE  = cv(216,97,7);        // Hệ thống / Trigger / Function
const ORANGELT= cv(255,249,235);

// State colors
const RED     = cv(207,34,46);       // Error / Non-happy
const REDLT   = cv(255,246,245);
const PURP    = cv(102,57,186);      // Popup / Modal / Cross-session
const PURPLT  = cv(251,239,255);

// Neutrals
const GRAY    = cv(108,117,125);
const GRAYLT  = cv(246,248,250);
const TH      = cv(36,41,47);        // text high
const TM      = cv(66,74,83);        // text mid
const TL      = cv(110,119,125);     // text low
const DIV     = cv(208,215,222);     // divider
const INP     = cv(234,238,242);     // input background
```

### Ý nghĩa màu — KHÔNG tráo đổi giữa 3 outputs:

| Ý nghĩa | Fill | Stroke/Text | Dùng cho |
|---|---|---|---|
| **Dipro Admin** (actor caller) | `BLUELT` | `BLUE` | Node/screen thuộc DA |
| **Company Admin** (actor receiver) | `GREENLT` | `GREEN` | Node/screen thuộc CA |
| **Hệ thống / Function / Trigger** | `ORANGELT` | `ORANGE` | Nghiệp vụ auto, quyết định |
| **Error / Non-happy** | `REDLT` | `RED` | Toast/Error screen (dashed) |
| **Popup / Modal / Cross-actor** | `PURPLT` | `PURP` | Popup screen (dashed), same-session |
| **Outcome / Neutral** | `GRAYLT` | `DIV` | Call Ended, tech stack, tổng kết |

---

## 2. Typography (đo từ bản chuẩn)

| Vai trò | Font | Size | Weight | Màu |
|---|---|---|---|---|
| Frame title | Inter | **18px** | Bold | `TH` |
| Frame subtitle | Inter | 11px | Regular | `TL` |
| Section header (SITEMAP, TECHNOLOGY STACK) | Inter | 13px | Bold | `TH` |
| Column label (ACTOR, TRIGGER...) | Inter | 10px | Bold | `GRAY` |
| Node title | Inter | 11-12px | Bold | `TH` hoặc actor color |
| Node sub-text | Inter | 10px | Regular | `TM` hoặc `TL` |
| Table header | Inter | 10px | Bold | actor color |
| Table cell | Inter | 10px | Regular | `TM` |
| Legend label | Inter | 9px | Regular | `TH` |

**Rule:** KHÔNG dùng font khác Inter. Chỉ 3 weights: Bold, Regular. Line-height mặc định.

---

## 3. Helper functions BẮT BUỘC (copy nguyên vào every use_figma call)

```js
function t(s, sz, bold, col, x, y, p, w=0) {
  const tx = figma.createText();
  tx.fontName = {family:"Inter", style:bold?"Bold":"Regular"};
  tx.fontSize = sz;
  if (w) { tx.resize(w, 10); tx.textAutoResize = "HEIGHT"; }  // ⚠️ resize TRƯỚC, HEIGHT SAU
  else tx.textAutoResize = "WIDTH_AND_HEIGHT";
  tx.x = x; tx.y = y; p.appendChild(tx);
  tx.characters = s;
  tx.fills = [{type:'SOLID', color:col}];
  return tx;
}

function r(w, h, fill, x, y, p, cr=6, stroke=null, dashed=false) {
  const n = figma.createRectangle();
  n.resize(w, h); n.x = x; n.y = y; n.cornerRadius = cr;
  n.fills = [{type:'SOLID', color:fill}];
  if (stroke) { n.strokes = [{type:'SOLID', color:stroke}]; n.strokeWeight = 1.5; }
  if (dashed) n.dashPattern = [5, 4];
  p.appendChild(n); return n;
}

function el(sz, fill, x, y, p, stroke=null) {
  const e = figma.createEllipse();
  e.resize(sz, sz); e.x = x; e.y = y;
  e.fills = [{type:'SOLID', color:fill}];
  if (stroke) { e.strokes = [{type:'SOLID', color:stroke}]; e.strokeWeight = 1.5; }
  p.appendChild(e); return e;
}

// Vertical line (dùng thay createVector cho stability)
function vl(x, y1, y2, col, p, dashed=false) {
  if (y2 <= y1) return;
  const rr = figma.createRectangle();
  rr.resize(2, y2-y1); rr.x = x-1; rr.y = y1;
  rr.fills = [{type:'SOLID', color:col, opacity:dashed?0.5:1}];
  if (dashed) rr.dashPattern = [5, 4];
  p.appendChild(rr);
}

// Horizontal line
function hl(x1, x2, y, col, p, dashed=false) {
  if (x2 <= x1) return;
  const rr = figma.createRectangle();
  rr.resize(x2-x1, 2); rr.x = x1; rr.y = y-1;
  rr.fills = [{type:'SOLID', color:col, opacity:dashed?0.5:1}];
  if (dashed) rr.dashPattern = [5, 4];
  p.appendChild(rr);
}

// Arrowhead (triangle) — polygon 3 points
function arrowHead(x, y, col, p, dir='right') {
  const ah = figma.createPolygon();
  ah.pointCount = 3;
  ah.resize(8, 10);
  if (dir === 'right') ah.rotation = -90;
  else if (dir === 'down') ah.rotation = 180;
  ah.x = x; ah.y = y;
  ah.fills = [{type:'SOLID', color:col}];
  p.appendChild(ah);
}

// Numbered badge (dùng nhiều nơi)
function badge(num, x, y, color, p, sz=24) {
  el(sz, color, x, y, p);
  const nt = t(String(num), sz===24?12:10, true, WHITE, 0, 0, p);
  nt.x = x + sz/2 - nt.width/2;
  nt.y = y + sz/2 - nt.height/2;
}

// Box với title + sub (dùng chung Output 1 flow)
function box(title, sub, fillC, strokeC, x, y, w, h, p) {
  r(w, h, fillC, x, y, p, 8, strokeC);
  const tt = t(title, 11, true, TH, x+8, y+10, p, w-16);
  if (sub) t(sub, 10, false, TM, x+8, y+10+tt.height+3, p, w-16);
}
```

⚠️ **NGUYÊN TẮC TEXT (không được sai):**
```
1. resize(w, 10)          — set width TRƯỚC
2. textAutoResize="HEIGHT" — set SAU resize (resize() reset thành "NONE")
3. characters = "..."     — set nội dung sau cùng
4. curY += tx.height + gap — tích lũy Y để không overlap
```

---

## 4. Output 1 — Flow Tổng Quan + Sitemap WBS Tree

### 4.1. Frame chính

```
Name:  "Output 1 — Flow Tổng Quan + Sitemap WBS"
Size:  1780 × dynamic (auto-fit content)
Fill:  WHITE
```

### 4.2. Layout tổng thể (3 phần)

> ⚠️ **UPDATE:** Bỏ Tech Stack hàng ngang cũ. Chuyển thành **BẢNG Technology BÊN PHẢI** Flow.

```
Frame width = 2280 (không phải 1780 nữa — cần chỗ cho bảng bên phải)

y=24    Title + Subtitle (2 dòng)
─────────────────────────────────────────────────────
LEFT (x=40..1770): PHẦN A — BUSINESS & LOGIC FLOW
y=90    Column labels: ACTOR · TRIGGER · FUNCTION · TECHNOLOGY · OUTCOME
y=108   Divider 1px
y=180   Main flow row (nodes ngang)
y=300   Decision + branches

RIGHT (x=1800..2260): TECHNOLOGY TABLE
y=90    Section header "TECHNOLOGY STACK"
y=108   Subtitle "Các công nghệ sử dụng và mục đích"
y=130   Bảng 2 cột: Technology | Mô tả mục đích sử dụng
─────────────────────────────────────────────────────
BOTTOM (từ y=560): PHẦN B — SITEMAP WBS TREE
y=572   Title "SITEMAP — WBS TREE (Actor + Hành động)"
y=592   Subtitle 4 levels
y=620   Legend box (320×50px)
y=700   Root node (In-App VoIP Call, xanh full)
y=810   Level 2: N actors ngang
y=910+  Level 3+4: Hành động → Screen (verticals)
```

### 4.3. Phần A — Business & Logic Flow

**Column X centers (5 columns + 2 extra):**
```
C = [130, 360, 610, 870, 1130, 1400, 1660]
     ACTOR  TRIG   FUNC   TECH   ACTOR2  IN-CALL  OUTCOME
```

**Column labels (10px Bold GRAY, tại y=90):**
- x=C[0]-30: "ACTOR"
- x=C[1]-30: "TRIGGER"
- x=C[2]-35: "FUNCTION"
- x=C[3]-42: "TECHNOLOGY"
- x=C[5]-30: "OUTCOME"

**Actor node (ellipse 78px + person icon inside):**
```js
el(78, BLUELT, C[0]-39, R1-39, frame, BLUE);
el(20, BLUE, C[0]-10, R1-24, frame);       // head
r(28, 18, BLUE, C[0]-14, R1-2, frame, 10);  // body
t("Dipro Admin", 11, true, TH, C[0]-30, R1+50, frame, 120);
t("Mobile App", 10, false, TL, C[0]-30, R1+64, frame, 120);
```
(y=R1=180)

**Trigger box 150×72, radius:8, fill BLUELT stroke BLUE:**
```js
box('Tap "Gọi ngay"', 'Company Detail screen', BLUELT, BLUE, C[1]-70, R1-36, 150, 72, frame);
```

**Function/Technology box 160-180×96, radius:8, fill ORANGELT stroke ORANGE:**
```js
box('VoIP SDK', 'Tạo call session\n+ generate token', ORANGELT, ORANGE, C[2]-80, R1-48, 160, 96, frame);
```

**Arrow ngang giữa 2 nodes:**
```js
line(nodeAX+halfW, R1, nodeBX-halfW, R1, actorColor, frame);
arrowHead(nodeBX-halfW-7, R1-5, actorColor, frame);
t("tap", 9, false, TL, midX-15, R1-16, frame);  // label trên arrow
```

**Decision node (Accept?)** — ROUNDED RECT bo góc 4, không phải diamond:
```js
r(140, 44, ORANGELT, cx-70, y, frame, 4, ORANGE);
t("Accept?", 11, true, ORANGE, cx-25, y+13, frame);
```

**Arrow decline (dashed RED):**
```js
line(cx, decY+44, cx, targetY, RED, frame, true);  // dashed
arrowHead(cx-4, targetY-7, RED, frame, 'down');
```

### 4.3.1. Technology Table (BÊN PHẢI Flow — thay Tech Stack row cũ)

```js
const TX = 1800;
let TY = 90;

// Section header
t("TECHNOLOGY STACK", 13, true, TH, TX, TY, frame);
t("Các công nghệ sử dụng và mục đích", 10, false, TL, TX, TY+18, frame);
TY += 40;

// Header row (32px, fill BLUELT stroke BLUE, radius:6)
r(460, 32, BLUELT, TX, TY, frame, 6, BLUE);
t("Technology", 10, true, BLUE, TX+12, TY+9, frame);
t("Mô tả mục đích sử dụng", 10, true, BLUE, TX+160, TY+9, frame);
TY += 32;

// Data rows (60px each — 2 dòng text nếu dài)
for (let i = 0; i < techList.length; i++) {
  const [tech, desc] = techList[i];
  const rowH = 60;
  r(460, rowH, i%2===0 ? WHITE : BGL, TX, TY, frame, 0, DIV);
  t(tech, 11, true, ORANGE, TX+12, TY+8, frame, 140);       // tên tech màu ORANGE
  t(desc, 10, false, TM, TX+160, TY+8, frame, 290);         // mô tả wrap
  r(460, 1, DIV, TX, TY+rowH-1, frame);
  TY += rowH;
}

// Ghi chú
r(460, 60, BLUELT, TX, TY+10, frame, 6, BLUE);
t("💡 GHI CHÚ", 10, true, BLUE, TX+12, TY+18, frame);
t("Danh sách công nghệ đề xuất — Tech Lead sẽ chốt lại trong DESIGN.md.", 9, false, TH, TX+12, TY+34, frame, 436);
t("BA chỉ liệt kê để user hình dung stack tổng quan.", 9, false, TH, TX+12, TY+48, frame, 436);
```

**Danh sách tech tối thiểu cho VoIP-like feature (9 tech):**
- Flutter — Framework mobile app đa nền tảng
- NestJS — Backend API framework
- Agora / Twilio SDK — VoIP Engine (WebRTC)
- APNs (iOS) — Apple Push Notification
- FCM (Android) — Firebase Cloud Messaging
- PostgreSQL — Database call log
- Redis — Cache call session
- AWS S3 — Recording storage (optional)
- JWT — Authentication token

### 4.4. Phần B — Sitemap WBS Tree (4 levels)

**Nguyên tắc VÀNG:**
- Level 1: **1 root duy nhất** = tên feature
- Level 2: **N actor** (kể cả `⚙️ Hệ thống` cho auto processes)
- Level 3: **Hành động verb-first** — bắt đầu bằng ✔ + verb ("Chọn công ty", "Xem thông tin", "Khởi tạo cuộc gọi")
- Level 4: **Screen / Popup / Error** dưới mỗi hành động

**Root node (Level 1):**
```js
// Rectangle 200×50, fill BLUE, cornerRadius 8, text white 13px Bold
r(200, 50, BLUE, cx-100, rootY, frame, 8);
t("In-App VoIP Call", 13, true, WHITE, cx-w/2, rootY+16, frame);
```

**Actor node (Level 2) — 200×54, radius:8, fill nhạt actor stroke đậm:**
```js
r(200, 54, actorBg, ax-100, L2_Y+30, frame, 8, actorColor);
t("👤 Dipro Admin", 12, true, actorColor, ax-w/2, L2_Y+40, frame);
t("Caller", 10, false, TM, ax-w/2, L2_Y+58, frame);
```

**Hành động node (Level 3) — 220×36, radius:6, fill GRAYLT stroke actor:**
```js
r(220, 36, GRAYLT, ax-110, curY, frame, 6, actorColor);
t("✔ Chọn công ty", 10, true, TH, ax-w/2, curY+11, frame);  // ✔ + verb
```

**Screen/Popup/Error node (Level 4) — 200×28, radius:5:**
```js
// Screen thường: WHITE + stroke actor
r(200, 28, WHITE, ax-100, sy, frame, 5, actorColor);
// Popup: PURPLT + stroke PURP + dashed
r(200, 28, PURPLT, ax-100, sy, frame, 5, PURP, true);
// Error: REDLT + stroke RED + dashed
r(200, 28, REDLT, ax-100, sy, frame, 5, RED, true);
```

**Connector dọc cha → con:** vl(x, y1, y2, DIV, frame)

**Legend box (320×50, top của Phần B):**
```
LEGEND
[■ Root] [□ Actor] [□ Hành động] [╌ Popup]
```

**Ba actor tối thiểu:**
1. `👤 Dipro Admin` (Caller) — BLUE
2. `👤 Company Admin` (Receiver) — GREEN
3. `⚙️ Hệ thống` (Auto process) — ORANGE

---

## 5. Output 2 — Screen Flow 3 Vùng

### 5.1. Frame chính

```
Name: "Output 2 — Screen Flow (Happy · Non-Happy · Index)"
Size: 1700 × dynamic
Fill: WHITE
```

### 5.2. Layout 4 VÙNG (cột dọc) — CHỐNG CHỒNG ĐÈ

> ⚠️ **LESSON LEARNED:** Không dùng 3 vùng vì CA node sẽ đè lên Non-Happy zone. **BẮT BUỘC 4 vùng** để DA và CA có column riêng.

```
Frame width = 2100px (bắt buộc rộng để đủ 4 zones)

x=40    Vùng 1 — DA HAPPY CASE   (width 400)
        ────── divider tại x=460 ──────
x=490   Vùng 2 — CA HAPPY CASE   (width 400)
        ────── divider tại x=910 ──────
x=940   Vùng 3 — NON-HAPPY CASE  (width 380)
        ────── divider tại x=1330 ──────
x=1360  Vùng 4 — BẢNG SCREEN INDEX (width 580)
```

**Boundaries constant (dùng trong code):**
```js
const Z1_X=40,   Z1_W=400;   // DA Happy
const Z2_X=490,  Z2_W=400;   // CA Happy
const Z3_X=940,  Z3_W=380;   // Non-Happy
const Z4_X=1360, Z4_W=580;   // Screen Index

// Node center X trong mỗi zone
const DA_X = Z1_X + 100;  // 140
const CA_X = Z2_X + 100;  // 590
const EX   = Z3_X + 100;  // 1040
```

**Zone headers (13px Bold tại y=80):**
- ① DA HAPPY CASE — BLUE
- ② CA HAPPY CASE — GREEN
- ③ NON-HAPPY CASE — RED
- ④ BẢNG SCREEN INDEX — PURP

**Divider giữa các vùng:**
```js
vl(460,80,frameH,DIV,frame);
vl(910,80,frameH,DIV,frame);
vl(1330,80,frameH,DIV,frame);
```

**Cross-actor arrow (DA_003 → CA_001):**
```js
// Push notification: từ DA_003 (bên phải) sang CA_001 (bên trái Zone 2)
hl(DA_X+NW, CA_X, h3.mid, GREEN, frame, true);
arrowHead(CA_X-4, h3.mid-5, GREEN, frame, 'right');
t("push notification / overlay", 9, false, GREEN, DA_X+NW+8, h3.mid-14, frame);
```

**Cross-session connector (DA_004 ↔ CA_002 same call):**
```js
const sessionY = Math.max(h4.mid, ca2.mid);
hl(DA_X+NW, CA_X, sessionY, PURP, frame);
t("← same call session →", 9, true, PURP, (DA_X+NW+CA_X)/2 - 50, sessionY-14, frame);
```

### 5.3. Vùng 1 — Happy Flow

**Screen node (numbered):**
```
Kích thước: 200 × 64
Fill: BLUELT (DA) hoặc GREENLT (CA)
Stroke: BLUE hoặc GREEN, 1.5px
CornerRadius: 6

Cấu trúc bên trong:
  y+6:  Screen Code (9px Bold actor color)
  y+6:  Type (9px Regular TL, top-right)
  y+20: Screen Name (12px Bold TH)
  y+38: Purpose 1 dòng (9px Regular TM)  ← BẮT BUỘC
```

**Numbered badge (bên trái node):**
```
Ellipse 28px, fill actor color
Số Bold 12px WHITE, căn giữa
Vị trí: x = nodeX - 42
```

**Start/End (ellipse 32px + icon):**
```
Start: fill actor color, icon "▶" 14px Bold WHITE
End: fill GRAY, icon "■" 14px Bold WHITE
```

**Decision node (Accept?):** rounded rect 160×44, fill ORANGELT stroke ORANGE.

**Cross-session connector giữa DA_004 và CA_002:**
```js
hl(HX+NW, CA_HX, mid, PURP, frame);
t("← same session →", 9, true, PURP, midX-45, mid-14, frame);
```

**Connector giữa Happy nodes:**
- Vertical line 2px, màu actor
- KHÔNG dùng dashed cho happy path

### 5.4. Vùng 2 — Non-Happy Flow (mỗi luồng 1 nhóm)

**Mỗi non-happy flow gồm 3 phần dọc:**

```
[⚠ Trigger title]                          ← 11px Bold RED
[From: <source screen>]                    ← 180×32 BLUELT + BLUE stroke
     ↓ (dashed line + arrowhead)
[Error/Popup node]                         ← 200×44 REDLT+RED dashed / PURPLT+PURP dashed
     ↓
[→ Next screen name]                       ← 200×44 GRAYLT + GRAY, có "→" prefix
     ↓
Description                                ← 9px Regular TM
```

**Các luồng non-happy điển hình (5 luồng mẫu cho VoIP-like feature):**
1. ⚠ Timeout 30s
2. ⚠ Network Lost (đang gọi)
3. ⚠ Mic Permission Denied
4. ⚠ CA Declined
5. ⚠ App Killed (background)

### 5.5. Vùng 3 — Bảng Screen Index (CRITICAL)

**Kích thước bảng:** 560px width, dynamic height.

**Header row (32px, fill BLUELT stroke BLUE, radius:6):**
```
| #  | Màn hình | Loại | Mô tả chức năng |
```
Tất cả 10px Bold, màu BLUE.

**Data row (44px):**
```
Alternate: WHITE / BGL
Column widths: 30 · 180 · 80 · 260 (px offset)
Cell text: 10px Regular TM
Screen name: Bold + màu actor
Type: Bold + màu actor
```

**Loại (Type) values — enum:**
`List` · `Detail` · `Modal` · `Popup` · `Toast` · `Banner` · `Push` · `Form` · `Wizard`

**⚠️ RULE ĐẾM TOTAL:**
```
Total row: fill BGL, stroke BLUE, radius:6
Text: "TỔNG: N màn hình (X screen + Y popup + Z toast + W push)"
```

**Popup, Toast, Push notification CŨNG LÀ MÀN HÌNH — bắt buộc đưa vào bảng và đếm.**

**Ghi chú quan trọng (box dưới Total):**
- Popup CŨNG LÀ MÀN HÌNH — được đếm vào total
- Toast/Banner/Push cũng đếm nếu là component riêng
- 2 luồng Happy Case và Non-Happy Case tách riêng (Vùng 1 + Vùng 2)
- Decision node có ở cả 2 phía DA + CA

---

## 6. Output 3 — HiFi Screens + Bảng Liệt Kê Đầy Đủ Item

### 6.1. Frame chính

```
Name: "Output 3 — HiFi Screens + Bảng Chi Tiết Item"
Size: 2400 × dynamic (rất tall)
Fill: BGL
```

### 6.2. Layout DỌC — 1 phone + 1 table 1 hàng

> ⚠️ **UPDATE:** Bỏ layout 4×2 grid cũ (bị đè). Dùng **layout DỌC N hàng** (N = số màn hình). Mỗi hàng = 1 phone (390×844) bên trái + 1 bảng bên phải cạnh nhau.

```
Frame width = 1450 (đủ cho phone + table)

y=24    Title + Subtitle
─────────────────────────────────────────────────
Hàng 1 (y=100..944):
  x=40..430:  Phone S1
  x=470..1410: Table S1

Hàng 2 (y=1004..1848):
  x=40..430:  Phone S2
  x=470..1410: Table S2

... (N hàng, mỗi hàng = PHONE_H + ROW_GAP = 844 + 60 = 904px)
```

**Constants layout dọc:**
```js
const PHONE_X = 40;
const PHONE_Y_START = 100;
const TABLE_X = 470;        // phone width 390 + 40 gap
const TABLE_W = 940;
const ROW_GAP = 60;
const PHONE_H = 844;

// Y position của row idx
const rowY = PHONE_Y_START + rowIdx * (PHONE_H + ROW_GAP);
```

**Ưu điểm layout dọc:**
- KHÔNG bị đè: mỗi phone tự do full 844px, không đè bảng ở dưới
- Đọc tự nhiên: scroll dọc từng màn hình + spec cạnh nhau
- Dễ compare: user nhìn cùng row = 1 screen + tables đồng nhất chiều cao

**Cấu trúc bảng bên phải:**
- Header row 32px fill BGL, radius 4
- Column widths: `#`(30) `Title`(220) `Mô tả`(300) `Mục đích`(360) — total 940px
- Data row 48px với alternating BGL/WHITE
- Table.resize width fixed 940, height = cy+PAD (dynamic)

### 6.3. Phone Screen (390 × 844)

**Cấu trúc chung mọi phone:**

```
Frame:
  Fill: WHITE (light screen) hoặc BGDK cv(26,31,46) (dark call screen)
  clipsContent: true

y=0..44   Status Bar
y=44..100 Nav Header (nếu có)
y=100...  Body content
y=764..844 Sticky CTA (nếu có)
```

**Status Bar (44px):**
```js
r(390, 44, isDark?BGDK:BGL, 0, 0, phone);
t("10:09", 14, true, isDark?WHITE:TH, 16, 15, phone);
const wi = t("▸▸▸", 12, false, isDark?WHITE:TH, 0, 16, phone);
wi.x = 374 - wi.width;  // right-align
```

**Nav Header (56px, tại y=44):**
```js
r(390, 56, isDark?BGDK:WHITE, 0, 44, phone);
t("←", 20, false, BLUE, 16, 60, phone);  // back
const ti = t(title, 16, true, isDark?WHITE:TH, 0, 58, phone);
ti.x = 195 - ti.width/2;  // center
r(390, 1, DIV, 0, 99, phone);  // bottom border
```

**Search bar (44×358, tại y=108):**
```js
r(358, 44, INP, 16, 108, phone, 6);
t("🔍  Tìm ...", 13, false, TL, 32, 122, phone);
```

**List item (72px):**
```js
r(390, 72, WHITE, 0, ly, phone);
// Avatar 40×40 với initial
el(40, avatarBg, 16, ly+16, phone);
t(initial, 15, true, avatarFg, ..., ..., phone);  // center in ellipse
// Online dot 10×10
el(10, dotColor, 50, ly+11, phone);
// Name Bold 14
t(name, 14, true, TH, 68, ly+12, phone);
// Sub 11px Regular TL
t(sub, 11, false, TL, 68, ly+32, phone);
// Chevron ›
t("›", 18, false, TL, 364, ly+27, phone);
// Divider
r(358, 1, DIV, 16, ly+71, phone);
```

**Sticky CTA (48px button trong container 80px):**
```js
r(390, 1, DIV, 0, 764, phone);       // top border
r(390, 80, WHITE, 0, 765, phone);    // container
r(358, 48, BLUE, 16, 773, phone, 6); // button
const c = t("📞  Gọi ngay", 16, true, WHITE, ..., ..., phone);
c.x = 195 - c.width/2;
c.y = 785;
```

**Dark call screen — Avatar + Pulse Rings:**
```js
// Outer ring (opacity 0.12)
el(180, BLUE, CX-90, AY-90, phone);
const r1 = phone.children[phone.children.length-1];
r1.fills = [{type:'SOLID', color:BLUE, opacity:0.12}];
// Mid ring (opacity 0.20)
el(150, BLUE, CX-75, AY-75, phone);
phone.children.at(-1).fills = [{type:'SOLID', color:BLUE, opacity:0.20}];
// Inner (opacity 0.30 — as avatar bg)
el(120, BLUE, CX-60, AY-60, phone);
phone.children.at(-1).fills = [{type:'SOLID', color:BLUE, opacity:0.30}];
// Initial 44px Bold WHITE centered
const av = t("Y", 44, true, WHITE, 0, 0, phone);
av.x = CX - av.width/2;
av.y = AY - av.height/2;
```

**Call Controls (3 buttons ở y=700):**
```js
// Speaker/Mute: circle 64px fill cv(50,60,80)
el(64, cv(50,60,80), CX-130, ctrlY, phone);
t("🔊", 22, false, WHITE, ..., ..., phone);
t("Loa", 11, false, TL, ..., ..., phone);  // label ở y+70

// End call: circle 72px fill RED
el(72, RED, CX+64, ctrlY-4, phone);
t("✕", 26, true, WHITE, ..., ..., phone);
t("Kết thúc", 11, false, TL, ...);
```

**Active control state (mute đang bật):**
```js
el(64, BLUE, x, y, phone);
phone.children.at(-1).fills = [{type:'SOLID', color:BLUE, opacity:0.4}];
// Icon + label color = cv(151,211,255) (light blue)
```

**Bottom Sheet (Call Ended):**
```js
// Dark background phía trên
r(390, 500, BGDK, 0, 0, phone);
// Sheet trắng slide up
const sheet = figma.createFrame();
sheet.resize(390, 420); sheet.x = 0; sheet.y = 424;
sheet.fills = [{type:'SOLID', color:WHITE}];
sheet.cornerRadius = 12;
phone.appendChild(sheet);
// Handle bar
r(32, 4, DIV, 179, 12, sheet, 2);
// Status icon 52px + check
el(52, GREENLT, 169, 32, sheet);
t("✓", 22, true, GREEN, ..., ..., sheet);
```

### 6.4. Numbered overlay TRÊN mỗi phone

Với mỗi item hiển thị trên phone, tạo 1 badge số nhỏ **bên trong phone frame** (clipped):
```js
// Ellipse 20px, fill BLUE (hoặc GREEN cho CA)
el(20, BLUE, badgeX, badgeY, phone);
const n = t(String(num), 10, true, WHITE, 0, 0, phone);
n.x = badgeX + 10 - n.width/2;
n.y = badgeY + 10 - n.height/2;
```

Đặt badges tại các vị trí đại diện: ngoài trái, ngoài phải, top item, giữa list, cuối màn hình. Số của badge tương ứng với số dòng trong bảng.

### 6.5. Bảng ITEMS (cột Action thay Mục đích)

> ⚠️ **UPDATE:** Bảng items dùng **cột `Action / Behavior`** thay cho `Mục đích` cũ. Cho phép mô tả tương tác + Happy Case + Error Case ngay trong 1 cell.

**Bảng frame:**
```
Width: 990 (thay cho 760 cũ — cần rộng hơn cho Action content)
Fill: WHITE
Stroke: DIV 1px, cornerRadius: 8
clipsContent: false (chờ resize xong mới true)
```

**Cấu trúc:**
```
y=14  Screen Code · Screen Name (14px Bold actor color)
y+18  Subtitle "🖥 BẢNG ITEMS — Liệt kê ĐẦY ĐỦ từng element trên màn hình" (10px Regular TL)
y+40  Divider 1px DIV

y+50  Column header row (28px, fill BGL, radius:4):
      | #  | Title (Tên item) | Mô tả | Action / Behavior |
       10px Bold actor color
       Column offsets: PAD+8, PAD+40, PAD+220, PAD+430

y+80  Data rows (dynamic 48-88px based on Action length):
      - action.length === 0 or "—" → rowH = 48
      - action.length > 50  → rowH = 68
      - action.length > 100 → rowH = 88
      Alternating: i%2===0 ? no bg : BGL
      # (10px Bold TH),
      Title (10px Bold TH, width 175),
      Mô tả (10px Regular TM, width 205),
      Action (10px Regular TH nếu có, TL nếu "—", width 525)
      Divider bottom 1px DIV
```

**Format cột Action / Behavior:**

- **Item không có action** → `"—"` (visual only: Status Bar, Label, Divider, Icon decorative)
- **Item có action đơn giản** → `"TAP → <đích>"`
- **Item có action phức tạp** → dòng gộp:
  ```
  TAP → <đích>. Happy: <mô tả>. Error nếu <trigger> → <hiển thị>
  ```

**Ví dụ ĐÚNG:**
```
✅ "TAP → DA_VOIP_003 Outgoing Call. Happy: chuyển màn + phát signal push tới CA.
   Error nếu Offline/Busy → disabled + tooltip"

✅ "TAP toggle mute mic. Happy: đổi active state, CA không nghe thấy DA"

✅ "Swipe down → dismiss + về DA_VOIP_002"
```

### 6.5b. Bảng ERROR SCENARIOS (BẮT BUỘC — dưới bảng ITEMS)

> Sau bảng ITEMS, tạo **bảng riêng liệt kê tất cả trường hợp lỗi có thể xảy ra ở màn hình này** với popup/message/action tiếp theo.

**Bảng frame:**
```
Width: 990 (same as Items table)
Fill: cv(255,251,251) — hồng nhạt để phân biệt
Stroke: RED 1px, cornerRadius: 8
Position: bên dưới items table, gap 20px
```

**Cấu trúc:**
```
y=14  "⚠ ERROR SCENARIOS — <Screen Code>" (14px Bold RED)
y+18  Subtitle "Các trường hợp lỗi có thể xảy ra ở màn hình này + popup/message/action tiếp theo" (10px Regular TM)
y+40  Divider 1px RED

y+50  Column header row (28px, fill REDLT, radius:4):
      | #  | Trigger (nguyên nhân) | Hiển thị | Message + Action tiếp theo |
       10px Bold RED
       Column offsets: PAD+8, PAD+40, PAD+240, PAD+370

y+80  Data rows (68-88px dynamic):
      msgAction.length > 100 → rowH = 88
      Alternating: i%2===0 ? no bg : cv(255,246,246)
      # (10px Bold TH),
      Trigger (10px Bold TH, width 195),
      Hiển thị (10px Bold RED, width 125),
      Message + Action (10px Regular TM, width 585)
      Divider bottom 1px cv(255,220,220)
```

**Cột "Hiển thị" — enum recommended:**
- `Toast` (bottom, auto dismiss 3s)
- `Modal` (blocking, cần user action)
- `Popup` (system-level như permission)
- `Banner` (sticky top/bottom)
- `Tooltip` (khi hover/tap)
- `Empty state` (thay content chính)
- `Push notification` (khi app background)
- `Auto dismiss` (không có UI, chỉ log)

**Ví dụ cột "Message + Action tiếp theo":**
```
✅ "Text: 'Không có phản hồi'. Action: auto về DA_VOIP_002 Company Detail, log 'Missed'"
✅ "Text: 'Cần quyền microphone để gọi VoIP' + Nút [Mở Cài đặt] deep-link tới Settings"
✅ "Text: 'Không có kết nối mạng. Vui lòng thử lại.' + Nút [Retry] retry gọi"
```

**Danh sách error scenarios tối thiểu cho từng loại màn hình:**

| Loại màn hình | Errors bắt buộc phải có |
|---|---|
| List | Empty state · Network error · Load timeout |
| Detail | Load fail · Data missing · Permission denied |
| Modal call (Outgoing) | Timeout · Rejected · Network lost · Permission denied · Busy |
| Modal call (In-call) | Network lost · Peer hang up · App killed · Mic revoked |
| Form | Validation fail · Submit fail · Duplicate · Network error |

### 6.6. NGUYÊN TẮC LIỆT KÊ (CRITICAL)

**KHÔNG lược bỏ item nào.** Trên UI có N item thì bảng có N dòng.

**Tính TẤT CẢ:**
- Status Bar, Nav Header (kể cả nếu chỉ có logo/title)
- Nút (Button, IconButton, FAB, CTA)
- Input (Search, TextField, Dropdown)
- Label / Text hiển thị (headers, sub-text, timestamps)
- List item (template row — ghi "×N" nếu repeat)
- Icon riêng lẻ, Avatar, Badge, Online dot
- Tab, Filter chip
- Divider, Section header
- Sticky bar, Overlay, Modal, Sheet

**KHÔNG tính:** whitespace decorative thuần, background layer thuần.

**Format 3 cột (Items):**
| Cột | Nội dung | Ví dụ |
|---|---|---|
| Title (Tên item) | Tên gọi element hiển thị trên UI | "Nút [Gọi ngay]", "Avatar tròn (initial)" |
| Mô tả | Element trông ntn, có gì | "Circle với chữ đầu tên cty" |
| Action / Behavior | Tương tác + Happy/Error case | "TAP → DA_VOIP_003. Disabled nếu Offline" hoặc "—" nếu visual only |

**KHÔNG viết design spec (px/hex/font) trong Mô tả** — Description tập trung "trông thế nào" chứ không phải "spec bao nhiêu px". Ví dụ:
- ✅ "Circle xanh với icon 🔊, có label bên dưới"
- ❌ "Circle 64px màu #323C50, icon 22px, label 11px Regular #6E7781"

**Row height dynamic (Items):**
```js
let rowH = 48;
if (action && action.length > 50) rowH = 68;
if (action && action.length > 100) rowH = 88;
```

---

## 7. Quy trình 3 bước tạo Output (BẮT BUỘC)

### 7.1. Trước khi vẽ (mọi output)

```
1. Read các file trong .claude/skills/ba-figma-output/examples/:
   - final_output_1.png (Output 1 reference)
   - final_output_2.png (Output 2 reference)
   - final_output_3.png (Output 3 reference)
2. Load skill figma:figma-use (đọc SKILL.md của Figma plugin)
3. get_metadata → xác nhận Figma file tồn tại, lấy fileKey
4. Xác định target page name → setCurrentPageAsync
5. KHÔNG createPage() mới
```

### 7.2. Chia calls (tránh vượt 50k chars)

```
Output 1: 1 call duy nhất (flow + sitemap + tech table bên phải)
Output 2: 1 call duy nhất (4 vùng)
Output 3 (layout DỌC với 2 tables/row): 4 calls tuần tự, mỗi call = 2 rows:
  Call 1: Container + Row 1 (S1) + Row 2 (S2)
  Call 2: Row 3 (S3) + Row 4 (S4)  — dark call screens
  Call 3: Row 5 (S5) + Row 6 (S6)
  Call 4: Row 7 (S7) + Row 8 (S8) + resize container final

Mỗi row build 3 thành phần qua helper:
  buildRow(rowIdx, code, name, actor, isDark, phoneBuilder, items, errorScenarios)
    - rowY = PHONE_Y_START + rowIdx * ROW_HEIGHT (ROW_HEIGHT = 1500 fix)
    - Phone bên trái (x=40..430, height 844)
    - itemsTable bên phải (x=470..1460, dynamic height)
    - errorTable bên phải DƯỚI itemsTable (x=470..1460, gap 20px)
  
  items[] format: [ [title, desc, action], ... ]
    - action null hoặc "—" nếu không tương tác
    - action string dài với "TAP → ... Happy: ... Error: ..."
  
  errorScenarios[] format: [ [trigger, display, msgAction], ... ]
    - trigger: nguyên nhân
    - display: Toast/Modal/Popup/Banner/Tooltip enum
    - msgAction: "Text: '<message>' + Nút [<action>]"
```

### 7.3. Sau khi vẽ mỗi frame

- `frame.screenshot({scale:0.4})` để verify visual
- Nếu text overlap → check text helper (resize trước, HEIGHT sau)
- Return `{done:true, frameId, ...}` từ mỗi call

---

## 8. Anti-patterns — TUYỆT ĐỐI KHÔNG làm

| ❌ Sai | ✅ Đúng |
|---|---|
| `tx.textAutoResize = "HEIGHT"; tx.resize(w, 10);` | `tx.resize(w, 10); tx.textAutoResize = "HEIGHT";` |
| Đặt node trực tiếp lên page | Luôn `parent.appendChild()` — parent = frame |
| Fill opacity qua `node.opacity = 0.5` | `node.fills = [{type:'SOLID', color:c, opacity:0.5}]` |
| Hardcode Y position | `curY += node.height + gap` tích lũy |
| Vẽ arrow bằng createVector | `hl()` / `vl()` (rectangle 2px height) + `arrowHead()` polygon |
| Tạo page mới | `setCurrentPageAsync(existingPage)` |
| Đếm Popup vào total mà **quên** Toast/Push | Total = "N (X screen + Y popup + Z toast + W push)" |
| Bỏ item khi liệt kê Output 3 | Liệt kê từng cái một, kể cả divider/section header |
| Ghi px/hex trong Output 3 Mô tả | Chỉ mô tả "trông ntn" + "mục đích nghiệp vụ" |
| Vẽ Level 3 = screen name | Level 3 phải là **hành động verb-first** (✔ Chọn công ty) |
| Trộn màu actor DA/CA | Giữ nhất quán: DA = BLUE, CA = GREEN toàn bộ 3 outputs |

---

## 9. Return values chuẩn cho mỗi call

```js
return {
  done: true,
  frameId: frame.id,
  nodeIds: [/* các node quan trọng để reference lần sau */],
  finalY: cursorY,  // cho call tiếp biết đặt tiếp ở đâu
};
```

Đây là contract giữa các calls — call sau đọc `nodeIds` từ return trước bằng `figma.getNodeByIdAsync(id)`.

---

## 10. Summary — What makes output 10/10

| Output | Điểm 10 khi... |
|---|---|
| **Output 1 Flow** | Đủ 5 columns · Actor icon rõ · Decision + branches · Tech Stack đầy đủ · Sitemap 4 levels verb-first · Legend rõ |
| **Output 2 Screen Flow** | **4 vùng dọc riêng biệt (không đè)** · DA và CA có column riêng · Non-Happy tách biệt · Bảng Index có TỔNG · Popup/Toast/Push đều đếm |
| **Output 3 HiFi + Table** | Phone mockup thật (light + dark) · Number badge trên từng item · Bảng liệt kê **KHÔNG bỏ sót** · 3 cột Title/Mô tả/Mục đích |

---

## 11. AI Recheck — BẮT BUỘC sau khi vẽ

Sau khi hoàn thành mỗi Output, **PHẢI** chụp screenshot và tự đánh giá theo checklist 5 tiêu chí.

### 11.1. Quy trình

```
1. get_screenshot(frameId, maxDimension=1400, enableBase64Response=true)
2. Zoom + đọc screenshot bằng vision
3. Check 5 tiêu chí bên dưới
4. Nếu FAIL → viết use_figma call sửa → chụp lại
5. Chỉ PASS toàn bộ mới sang frame tiếp theo
```

### 11.2. 5 tiêu chí PASS/FAIL

| # | Tiêu chí | PASS khi |
|---|---|---|
| 1 | **Đủ nội dung** | Đủ sections theo §4/§5/§6 tương ứng |
| 2 | **Không chồng đè** | Không node nào overlap: text/box/arrow/badge |
| 3 | **Text đầy đủ** | Không bị crop, tất cả label readable |
| 4 | **Đúng vùng** | Node X-coord nằm gọn trong Zone boundary |
| 5 | **Số badge = số row bảng** (Output 3 only) | Đếm badge phone == đếm rows table |

### 11.3. Common overlap patterns (đã gặp)

**Đặc biệt check các điểm dưới đây khi zoom screenshot:**

| Vấn đề | Ví dụ | Cách phát hiện |
|---|---|---|
| CA node đè Non-Happy zone | CA_VOIP_001 tràn sang vùng Timeout | X-coord của CA node > Zone 2 boundary |
| Cross-arrow đè lên In-Call node | "same session" line đè text | Line Y == node Y range |
| Numbered badge đè border Zone trước | Badge số 7 CA đè divider zone 1/2 | Badge X < divider X |
| Decision label đè "Yes/No" | "Accept?" text đè "Yes ↓" | Text Y overlap |
| Text purpose bị crop | "Trao đổi âm thanh 2 c..." bị cắt | Text width < node width |
| Cross-session tím đè label khác | Đường tím đè "push notification" | 2 hl() cùng Y, khác X range |
| Non-happy trigger đè error node | "From: X" chồng lên "Toast: Y" | curY không cộng đủ height |
| **Output 3 phone đè bảng dưới (grid layout)** | Phone S1 dài 844px đè lên bảng bắt đầu y=944 | Table Y < phoneY + PHONE_H — dùng layout DỌC thay grid |
| **Tech Stack ngang đè Sitemap** | Tech Stack row y=436 đè lên Sitemap section y=560 | Tech boxes height > Y gap — chuyển tech thành TABLE bên phải Flow |

### 11.4. Format báo cáo recheck

```
🔍 AI Recheck — Output <N>

✅ Tiêu chí 1: Đủ nội dung
✅ Tiêu chí 2: Không chồng đè
✅ Tiêu chí 3: Text đầy đủ
✅ Tiêu chí 4: Đúng vùng
✅ Tiêu chí 5: Badge/row khớp (Output 3)

Kết quả: PASS ✅  →  chuyển sang Output tiếp theo
```

hoặc:

```
🔍 AI Recheck — Output <N>

✅ Tiêu chí 1: Đủ nội dung
❌ Tiêu chí 2: Có chồng đè
   → Vấn đề: CA_VOIP_001 đè lên push notification label
   → Fix: dời CA column sang phải, mở frame width từ 1700 → 2100
✅ ...

Kết quả: FAIL → tiến hành fix rồi chụp lại
```

### 11.5. Anti-pattern KHÔNG được làm

- ❌ Báo user "đã xong" mà không chạy recheck
- ❌ Skip 1 tiêu chí vì "chắc là ok"
- ❌ Fix bằng cách xoá node overlap (phải dời/mở rộng)
- ❌ Chụp screenshot 1 lần rồi bỏ qua (phải chụp SAU khi fix)
- ❌ Chỉ dựa vào `frame.width/height` return code (không detect overlap được)
