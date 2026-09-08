// =============================================================
// FIGMA PLUGIN SCRIPT — BA Output 2: Screen Flow
// Feature: Medical Platform — Nền tảng kết nối y tế
// 4 vùng: Doctor Happy / Hospital Happy / Non-Happy / Screen Index
//
// Chạy TRÊN page hiện tại (node-id=30633-62845)
// =============================================================

(async () => {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });
  await figma.loadFontAsync({ family: "Inter", style: "Bold" });

  const cv = (r,g,b) => ({r:r/255, g:g/255, b:b/255});
  const WHITE = cv(255,255,255);
  const BGL   = cv(246,248,250);
  const BLUE  = cv(9,105,218);
  const BLUELT= cv(229,246,255);
  const GREEN = cv(26,127,55);
  const GREENLT=cv(237,253,240);
  const ORANGE= cv(216,97,7);
  const ORANGELT=cv(255,249,235);
  const RED   = cv(207,34,46);
  const REDLT = cv(255,246,245);
  const PURP  = cv(102,57,186);
  const PURPLT= cv(251,239,255);
  const TH    = cv(36,41,47);
  const TM    = cv(66,74,83);
  const TL    = cv(110,119,125);
  const DIV   = cv(208,215,222);
  const GRAY  = cv(108,117,125);

  const page = figma.currentPage;
  const NW = 200; // node width
  const NH = 64;  // node height

  function t(s, sz, bold, col, x, y, p, w=0) {
    const tx = figma.createText();
    tx.fontName = {family:"Inter", style:bold?"Bold":"Regular"};
    tx.fontSize = sz;
    if (w) { tx.resize(w, 10); tx.textAutoResize = "HEIGHT"; }
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
  function vl(x, y1, y2, col, p, dashed=false) {
    if (y2<=y1) return;
    const rr = figma.createRectangle();
    rr.resize(2, y2-y1); rr.x = x-1; rr.y = y1;
    rr.fills = [{type:'SOLID', color:col}];
    if (dashed) rr.dashPattern=[5,4];
    p.appendChild(rr);
  }
  function hl(x1, x2, y, col, p, dashed=false) {
    if (x2<=x1) return;
    const rr = figma.createRectangle();
    rr.resize(x2-x1, 2); rr.x = x1; rr.y = y-1;
    rr.fills = [{type:'SOLID', color:col}];
    if (dashed) rr.dashPattern=[5,4];
    p.appendChild(rr);
  }
  function arrowHead(x, y, col, p, dir='down') {
    const ah = figma.createPolygon();
    ah.pointCount = 3; ah.resize(8,10);
    if (dir==='down') ah.rotation=180;
    else if (dir==='right') ah.rotation=-90;
    ah.x=x; ah.y=y;
    ah.fills=[{type:'SOLID',color:col}];
    p.appendChild(ah);
  }

  function screenNode(code, name, type, purpose, fillC, strokeC, x, y, p, num, actorColor) {
    r(NW, NH, fillC, x, y, p, 6, strokeC);
    t(code, 9, true, strokeC, x+6, y+6, p, 100);
    t(type, 9, false, TL, x+NW-45, y+6, p);
    t(name, 12, true, TH, x+6, y+22, p, NW-12);
    t(purpose, 9, false, TM, x+6, y+42, p, NW-12);
    // Badge
    el(28, actorColor, x-14, y+18, p);
    const nt = t(String(num), 12, true, WHITE, 0, 0, p);
    nt.x = x-14+14-nt.width/2;
    nt.y = y+18+14-nt.height/2;
    return {x, y, mid: y+NH/2};
  }

  function decisionNode(label, x, y, p) {
    r(160, 44, ORANGELT, x-80, y, p, 4, ORANGE);
    t(label, 11, true, ORANGE, x-80+10, y+12, p, 140);
  }

  // ══════════════════════════════════════════════
  // MAIN FRAME
  // ══════════════════════════════════════════════
  const frame = figma.createFrame();
  frame.name = "Output 2 — Screen Flow (Doctor Happy / Hospital Happy / Non-Happy / Index)";
  frame.resize(2100, 1600);
  frame.x = 200; frame.y = 1700;
  frame.fills = [{type:'SOLID', color:WHITE}];
  page.appendChild(frame);

  // Title
  t("Output 2 — Screen Flow — Medical Platform", 18, true, TH, 40, 24, frame, 1200);
  t("Vung 1: Doctor Happy · Vung 2: Hospital Happy · Vung 3: Non-Happy Case · Vung 4: Bang Screen Index", 11, false, TL, 40, 48, frame, 1400);

  // Zone constants
  const Z1_X=40, Z1_W=400;  // Doctor Happy
  const Z2_X=490, Z2_W=400; // Hospital Happy
  const Z3_X=940, Z3_W=380; // Non-Happy
  const Z4_X=1360, Z4_W=700;// Screen Index

  const DR_X = Z1_X + 100; // 140
  const HO_X = Z2_X + 100; // 590
  const EX_X = Z3_X + 100; // 1040

  // Zone headers
  t("① DOCTOR — HAPPY CASE (Application Flow)", 13, true, BLUE, Z1_X, 78, frame, Z1_W);
  t("② HOSPITAL — HAPPY CASE (Post & Scout)", 13, true, GREEN, Z2_X, 78, frame, Z2_W);
  t("③ NON-HAPPY CASE", 13, true, RED, Z3_X, 78, frame, Z3_W);
  t("④ BANG SCREEN INDEX", 13, true, PURP, Z4_X, 78, frame, Z4_W);

  // Zone dividers
  vl(460, 80, 1580, DIV, frame);
  vl(910, 80, 1580, DIV, frame);
  vl(1330, 80, 1580, DIV, frame);

  // ────────────────────────────────────────────────
  // VÙNG 1 — DOCTOR HAPPY (Application Flow)
  // ────────────────────────────────────────────────
  let dy = 120;

  // Start
  el(32, BLUE, DR_X-16, dy, frame);
  const startT = t("▶", 14, true, WHITE, 0, 0, frame);
  startT.x = DR_X-16+16-startT.width/2;
  startT.y = dy+16-startT.height/2;
  dy += 44;

  // Screens Doctor Application Flow
  const drScreens = [
    {code:"DR_AUTH_001", name:"Đăng ký Doctor", type:"Form", purpose:"Tạo tài khoản, đồng ý điều khoản"},
    {code:"DR_AUTH_002", name:"Liên kết LINE", type:"Detail", purpose:"Bắt buộc sau đăng ký"},
    {code:"DR_JOB_001", name:"Danh sách Job", type:"List", purpose:"Tìm kiếm, filter theo tiêu chí"},
    {code:"DR_JOB_003", name:"Chi tiết Job", type:"Detail", purpose:"Xem điều kiện, PDF, ứng tuyển"},
    {code:"DR_JOB_004", name:"Xác nhận Ứng tuyển", type:"Modal", purpose:"Confirm modal trước khi submit"},
    {code:"DR_CONT_001", name:"Danh sách Hợp đồng", type:"List", purpose:"Theo dõi trạng thái hợp đồng"},
    {code:"DR_CONT_002", name:"Chi tiết Hợp đồng", type:"Detail", purpose:"Xem điều kiện, chấp nhận/hủy"},
  ];
  const drNodes = [];
  drScreens.forEach((s, i) => {
    vl(DR_X, dy, dy+16, BLUE, frame);
    arrowHead(DR_X-4, dy+6, BLUE, frame);
    dy += 16;
    const node = screenNode(s.code, s.name, s.type, s.purpose, BLUELT, BLUE, DR_X-NW/2, dy, frame, i+1, BLUE);
    drNodes.push(node);
    dy += NH + 10;
  });

  // End
  vl(DR_X, dy, dy+20, BLUE, frame);
  arrowHead(DR_X-4, dy+10, BLUE, frame);
  dy += 20;
  el(32, GRAY, DR_X-16, dy, frame);
  const endT = t("■", 14, true, WHITE, 0, 0, frame);
  endT.x = DR_X-16+16-endT.width/2;
  endT.y = dy+16-endT.height/2;

  // ────────────────────────────────────────────────
  // VÙNG 2 — HOSPITAL HAPPY (Scout Flow)
  // ────────────────────────────────────────────────
  let hy = 120;
  el(32, GREEN, HO_X-16, hy, frame);
  const hs = t("▶", 14, true, WHITE, 0, 0, frame);
  hs.x = HO_X-16+16-hs.width/2; hs.y = hy+16-hs.height/2;
  hy += 44;

  const hoScreens = [
    {code:"HO_JOB_001", name:"Danh sách tin tuyển", type:"List", purpose:"Quản lý tin đang đăng"},
    {code:"HO_JOB_002", name:"Tạo tin tuyển", type:"Form", purpose:"Đăng Job mới (cần Billing)"},
    {code:"HO_SCOU_001", name:"Tìm bác sĩ", type:"List", purpose:"Tìm kiếm Doctor để scout"},
    {code:"HO_SCOU_002", name:"Hồ sơ Doctor", type:"Detail", purpose:"Xem profile ẩn danh Display ID"},
    {code:"HO_SCOU_003", name:"Tạo Scout", type:"Form", purpose:"Gửi lời mời + Work Condition"},
    {code:"HO_JOB_003", name:"Danh sách Ứng tuyển", type:"List", purpose:"Xem DS Doctor đã apply"},
    {code:"HO_JOB_004", name:"Duyệt Ứng tuyển", type:"Detail", purpose:"Phê duyệt → tạo Contract"},
  ];
  const hoNodes = [];
  hoScreens.forEach((s, i) => {
    vl(HO_X, hy, hy+16, GREEN, frame);
    arrowHead(HO_X-4, hy+6, GREEN, frame);
    hy += 16;
    const node = screenNode(s.code, s.name, s.type, s.purpose, GREENLT, GREEN, HO_X-NW/2, hy, frame, i+1, GREEN);
    hoNodes.push(node);
    hy += NH + 10;
  });
  vl(HO_X, hy, hy+20, GREEN, frame);
  arrowHead(HO_X-4, hy+10, GREEN, frame);
  hy += 20;
  el(32, GRAY, HO_X-16, hy, frame);
  const heT = t("■", 14, true, WHITE, 0, 0, frame);
  heT.x = HO_X-16+16-heT.width/2; heT.y = hy+16-heT.height/2;

  // Cross-actor: Hospital → Doctor (Scout Notification)
  if (hoNodes[3] && drNodes[2]) {
    const crossY = Math.min(hoNodes[3].mid, drNodes[2].mid);
    hl(HO_X-NW/2, DR_X+NW/2, crossY, PURP, frame, true);
    t("Scout notify →", 9, true, PURP, DR_X+NW/2+4, crossY-13, frame);
  }

  // ────────────────────────────────────────────────
  // VÙNG 3 — NON-HAPPY CASES
  // ────────────────────────────────────────────────
  let ey = 120;
  t("Moi luong bat dau bang trigger tu 1 man hinh happy", 9, false, TL, Z3_X, ey, frame, Z3_W-20);
  ey += 20;

  const nonHappyCases = [
    {
      trigger:"Hospital chua kich hoat Billing",
      from:"HO_JOB_002 Tạo tin tuyển",
      error:"Banner: 'Nang cap goi de dang tin'",
      next:"→ Billing Settings",
      isRedlt:true,
    },
    {
      trigger:"Doctor da block Hospital",
      from:"HO_SCOU_001 Tim bac si",
      error:"Empty state: Doctor khong hien thi",
      next:"→ Tim bac si khac",
      isRedlt:true,
    },
    {
      trigger:"Doctor tu choi Scout",
      from:"DR_SCOU_002 Chi tiet Scout",
      error:"Toast: 'Scout tu choi — Rejected'",
      next:"→ DR_SCOU_001 (status Rejected)",
      isRedlt:true,
    },
    {
      trigger:"PDF Dieu kien chua ready",
      from:"DR_JOB_003 Chi tiet Job",
      error:"Button disabled: 'Dang tao PDF...'",
      next:"→ (cho PDF ready roi tai)",
      isRedlt:false,
    },
    {
      trigger:"Doctor mat mang khi ung tuyen",
      from:"DR_JOB_004 Confirm Modal",
      error:"Toast error: 'Mat ket noi. Thu lai.'",
      next:"→ (giu nguyen modal, retry)",
      isRedlt:true,
    },
  ];

  nonHappyCases.forEach((c) => {
    // Trigger title
    t("⚠ " + c.trigger, 11, true, RED, Z3_X, ey, frame, Z3_W-20);
    ey += 18;
    // From
    r(200, 32, BLUELT, EX_X-100, ey, frame, 4, BLUE);
    t("From: " + c.from, 9, false, BLUE, EX_X-92, ey+8, frame, 184);
    ey += 32;
    // Arrow down
    vl(EX_X, ey, ey+16, RED, frame, true);
    arrowHead(EX_X-4, ey+8, RED, frame, 'down');
    ey += 16;
    // Error node
    const errFill = c.isRedlt ? REDLT : ORANGELT;
    const errStroke = c.isRedlt ? RED : ORANGE;
    r(200, 44, errFill, EX_X-100, ey, frame, 6, errStroke, true);
    t(c.error, 9, false, errStroke, EX_X-92, ey+8, frame, 184);
    ey += 44;
    // Arrow
    vl(EX_X, ey, ey+12, DIV, frame);
    arrowHead(EX_X-4, ey+4, DIV, frame, 'down');
    ey += 12;
    // Next
    r(200, 44, BGL, EX_X-100, ey, frame, 4, DIV);
    t(c.next, 9, false, TM, EX_X-92, ey+8, frame, 184);
    ey += 44;
    ey += 24; // gap
  });

  // ────────────────────────────────────────────────
  // VÙNG 4 — BẢNG SCREEN INDEX
  // ────────────────────────────────────────────────
  const BX = Z4_X;
  let by = 120;

  r(680, 32, BLUELT, BX, by, frame, 6, BLUE);
  t("#", 10, true, BLUE, BX+8, by+10, frame);
  t("Man hinh", 10, true, BLUE, BX+40, by+10, frame);
  t("Loai", 10, true, BLUE, BX+280, by+10, frame);
  t("Mo ta chuc nang", 10, true, BLUE, BX+360, by+10, frame);
  by += 32;

  const allScreens = [
    // Doctor screens
    {code:"DR_AUTH_001", name:"Đăng ký Doctor", type:"Form", desc:"Tạo tài khoản, xác nhận email", actor:"DR"},
    {code:"DR_AUTH_002", name:"Liên kết LINE", type:"Detail", desc:"Bắt buộc sau đăng ký, xác thực LINE", actor:"DR"},
    {code:"DR_JOB_001", name:"Danh sách Job", type:"List", desc:"Tìm kiếm + filter Job đang mở", actor:"DR"},
    {code:"DR_JOB_003", name:"Chi tiết Job", type:"Detail", desc:"Điều kiện làm việc, PDF, ứng tuyển", actor:"DR"},
    {code:"DR_JOB_004", name:"Xác nhận Ứng tuyển", type:"Modal", desc:"Confirm modal trước khi gửi đơn", actor:"DR"},
    {code:"DR_SCOU_001", name:"Danh sách Scout", type:"List", desc:"Scout nhận được, filter trạng thái", actor:"DR"},
    {code:"DR_SCOU_002", name:"Chi tiết Scout", type:"Detail", desc:"Xem lời mời + chấp nhận/từ chối", actor:"DR"},
    {code:"DR_CONT_001", name:"Danh sách Hợp đồng", type:"List", desc:"Trạng thái hợp đồng của Doctor", actor:"DR"},
    {code:"DR_CONT_002", name:"Chi tiết Hợp đồng", type:"Detail", desc:"Work Condition, chấp nhận/hủy, PDF", actor:"DR"},
    // Hospital screens
    {code:"HO_JOB_001", name:"Danh sách tin tuyển", type:"List", desc:"Quản lý Job Draft/Published/Closed", actor:"HO"},
    {code:"HO_JOB_002", name:"Tạo/Sửa tin tuyển", type:"Form", desc:"Đăng Job mới, cần Billing active", actor:"HO"},
    {code:"HO_JOB_003", name:"Danh sách Ứng tuyển", type:"List", desc:"Doctor đã apply vào Job", actor:"HO"},
    {code:"HO_JOB_004", name:"Duyệt Ứng tuyển", type:"Detail", desc:"Xem hồ sơ Doctor, phê duyệt/từ chối", actor:"HO"},
    {code:"HO_SCOU_002", name:"Hồ sơ Doctor", type:"Detail", desc:"Profile ẩn danh Display ID để scout", actor:"HO"},
    {code:"HO_SCOU_003", name:"Tạo Scout", type:"Form", desc:"Gửi lời mời + Work Condition", actor:"HO"},
    // Admin screens
    {code:"AD_DOCT_001", name:"Danh sách Doctor", type:"List", desc:"Quản lý Doctor, suspend/unsuspend", actor:"AD"},
    {code:"AD_DOCT_002", name:"Chi tiết Doctor", type:"Detail", desc:"Xem ứng tuyển, scout, trạng thái", actor:"AD"},
    {code:"AD_POLI_001", name:"Quản lý Policy", type:"List", desc:"Danh sách phiên bản điều khoản", actor:"AD"},
    // Popups / System
    {code:"DR_POLI_001", name:"[Popup] Đồng ý điều khoản", type:"Modal", desc:"Fullscreen modal buộc đồng ý trước login", actor:"SYS"},
    {code:"[Toast] Ứng tuyển OK", name:"[Toast] Ứng tuyển OK", type:"Toast", desc:"Thông báo tự dismiss sau 3s", actor:"DR"},
    {code:"[Toast] Network Error", name:"[Toast] Network Error", type:"Toast", desc:"Mất kết nối khi submit", actor:"SYS"},
    {code:"[Push] Scout mới", name:"[Push] Scout mới", type:"Push", desc:"Push notification khi Hospital scout Doctor", actor:"SYS"},
  ];

  allScreens.forEach((s, i) => {
    const rowH = 44;
    const fillC = i%2===0 ? WHITE : BGL;
    r(680, rowH, fillC, BX, by, frame);
    r(680, 1, DIV, BX, by+rowH-1, frame);
    t(String(i+1), 10, true, TH, BX+8, by+14, frame);
    const actorColor = s.actor==='DR' ? BLUE : (s.actor==='HO' ? GREEN : (s.actor==='AD' ? ORANGE : PURP));
    t(s.code + " — " + s.name, 10, true, actorColor, BX+40, by+14, frame, 232);
    const typeColor = s.type==='Toast'||s.type==='Modal'||s.type==='Push' ? PURP : TM;
    t(s.type, 10, true, typeColor, BX+280, by+14, frame);
    t(s.desc, 10, false, TM, BX+360, by+14, frame, 312);
    by += rowH;
  });

  // Total row
  r(680, 40, BLUELT, BX, by, frame, 6, BLUE);
  t("TONG: " + allScreens.length + " man hinh (15 screen + 2 popup + 2 toast + 1 push + 2 form)", 10, true, BLUE, BX+12, by+13, frame, 656);
  by += 40;

  // Note box
  r(680, 80, BGL, BX, by+8, frame, 6, DIV);
  t("GHI CHU QUAN TRONG:", 10, true, TH, BX+12, by+20, frame);
  t("• Popup CUNG LA MAN HINH — duoc dem vao total", 9, false, TM, BX+12, by+36, frame, 656);
  t("• Toast/Push notification cung dem neu la component rieng", 9, false, TM, BX+12, by+50, frame, 656);
  t("• Vung 1 (Doctor) va Vung 2 (Hospital) phan luong rieng — khong giao nhau", 9, false, TM, BX+12, by+64, frame, 656);

  // Final resize
  frame.resize(2100, Math.max(1600, Math.max(dy, ey, by) + 120));
  figma.viewport.scrollAndZoomIntoView([frame]);
  figma.notify("Output 2 done! Frame: " + frame.id);
})();
