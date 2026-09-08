// =============================================================
// FIGMA PLUGIN SCRIPT — BA Output 1: Flow Tổng Quan
// Feature: Medical Platform — Nền tảng kết nối y tế
// Page: Chạy trên page hiện tại (node-id=30633-62845)
//
// Cách chạy:
//   1. Mở Figma file: https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/
//   2. Vào đúng page chứa node 30633-62845
//   3. Plugins > Development > New Plugin > Run once → paste & run
// =============================================================

(async () => {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });
  await figma.loadFontAsync({ family: "Inter", style: "Bold" });

  const cv = (r,g,b) => ({r:r/255, g:g/255, b:b/255});
  const WHITE   = cv(255,255,255);
  const BGL     = cv(246,248,250);
  const BLUE    = cv(9,105,218);
  const BLUELT  = cv(229,246,255);
  const GREEN   = cv(26,127,55);
  const GREENLT = cv(237,253,240);
  const ORANGE  = cv(216,97,7);
  const ORANGELT= cv(255,249,235);
  const RED     = cv(207,34,46);
  const REDLT   = cv(255,246,245);
  const PURP    = cv(102,57,186);
  const TH      = cv(36,41,47);
  const TM      = cv(66,74,83);
  const TL      = cv(110,119,125);
  const DIV     = cv(208,215,222);
  const GRAY    = cv(108,117,125);

  const page = figma.currentPage;

  // ── Main Frame ──
  const frame = figma.createFrame();
  frame.name = "Output 1 — Flow Tổng Quan + Sitemap WBS";
  frame.resize(2280, 1400);
  frame.x = 200; frame.y = 200;
  frame.fills = [{type:'SOLID', color:WHITE}];
  page.appendChild(frame);

  // ── Helpers ──
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
  function hl(x1, x2, y, col, p, dashed=false) {
    if (x2<=x1) return;
    const rr = figma.createRectangle();
    rr.resize(x2-x1, 2); rr.x = x1; rr.y = y-1;
    rr.fills = [{type:'SOLID', color:col}];
    if (dashed) rr.dashPattern=[5,4];
    p.appendChild(rr);
  }
  function vl(x, y1, y2, col, p, dashed=false) {
    if (y2<=y1) return;
    const rr = figma.createRectangle();
    rr.resize(2, y2-y1); rr.x = x-1; rr.y = y1;
    rr.fills = [{type:'SOLID', color:col}];
    if (dashed) rr.dashPattern=[5,4];
    p.appendChild(rr);
  }
  function arrowHead(x, y, col, p, dir='right') {
    const ah = figma.createPolygon();
    ah.pointCount = 3;
    ah.resize(8, 10);
    if (dir==='right') ah.rotation=-90;
    else if (dir==='down') ah.rotation=180;
    ah.x = x; ah.y = y;
    ah.fills = [{type:'SOLID', color:col}];
    p.appendChild(ah);
  }
  function box(title, sub, fillC, strokeC, x, y, w, h, p) {
    r(w, h, fillC, x, y, p, 8, strokeC);
    const tt = t(title, 11, true, TH, x+8, y+10, p, w-16);
    if (sub) t(sub, 10, false, TM, x+8, y+10+tt.height+3, p, w-16);
  }

  // ══════════════════════════════════════════════
  // PHẦN A — FRAME TITLE
  // ══════════════════════════════════════════════
  t("Output 1 — Flow Tổng Quan — Medical Platform", 18, true, TH, 40, 24, frame, 1200);
  t("Phần A: Business & Logic Flow (Hospital → Doctor → Admin → System) · Phần B: Sitemap WBS Tree", 11, false, TL, 40, 48, frame, 1200);

  // Column divider
  r(1780, 1, DIV, 40, 70, frame);

  // Column labels
  const COLS = [130, 360, 610, 870, 1130, 1400, 1660];
  const COL_LABELS = ["HOSPITAL", "TRIGGER", "FUNCTION", "SYSTEM/API", "DOCTOR", "ADMIN", "OUTCOME"];
  COL_LABELS.forEach((label, i) => {
    t(label, 10, true, GRAY, COLS[i]-35, 78, frame);
  });
  r(1780, 1, DIV, 40, 96, frame);

  // ── Row 1: Application Flow (Hospital → Doctor) ──
  const R1 = 180;

  // Hospital actor (green)
  el(78, GREENLT, COLS[0]-39, R1-39, frame, GREEN);
  el(20, GREEN, COLS[0]-10, R1-24, frame);
  r(28, 18, GREEN, COLS[0]-14, R1-2, frame, 10);
  t("Hospital", 11, true, TH, COLS[0]-25, R1+50, frame, 80);
  t("Medical Org", 10, false, TL, COLS[0]-25, R1+64, frame, 80);

  // Trigger: Post Job
  box("Đăng tin tuyển", "Job → Published + PDF", GREENLT, GREEN, COLS[1]-75, R1-48, 150, 72, frame);

  // Function: System PDF gen
  box("PDF Service", "Tạo PDF Điều kiện\n(bất đồng bộ)", ORANGELT, ORANGE, COLS[2]-80, R1-48, 160, 88, frame);

  // Arrow Hospital → Trigger
  hl(COLS[0]+39, COLS[1]-75, R1, GREEN, frame);
  arrowHead(COLS[1]-75-4, R1-5, GREEN, frame);
  t("post job", 9, false, TL, (COLS[0]+39+COLS[1]-75)/2-15, R1-16, frame);

  // Arrow Trigger → Function
  hl(COLS[1]+75, COLS[2]-80, R1, ORANGE, frame);
  arrowHead(COLS[2]-80-4, R1-5, ORANGE, frame);
  t("async PDF", 9, false, TL, (COLS[1]+75+COLS[2]-80)/2-20, R1-16, frame);

  // System/API: Database
  box("Database", "Job + PDF\nPublished", ORANGELT, ORANGE, COLS[3]-75, R1-48, 150, 72, frame);
  hl(COLS[2]+80, COLS[3]-75, R1, ORANGE, frame);
  arrowHead(COLS[3]-75-4, R1-5, ORANGE, frame);

  // Doctor actor
  el(78, BLUELT, COLS[4]-39, R1-39, frame, BLUE);
  el(20, BLUE, COLS[4]-10, R1-24, frame);
  r(28, 18, BLUE, COLS[4]-14, R1-2, frame, 10);
  t("Doctor", 11, true, TH, COLS[4]-20, R1+50, frame, 60);
  t("Tìm việc", 10, false, TL, COLS[4]-20, R1+64, frame, 60);

  // Cross-actor arrow (DB → Doctor search)
  hl(COLS[3]+75, COLS[4]-39, R1, BLUE, frame, true);
  arrowHead(COLS[4]-39-4, R1-5, BLUE, frame);
  t("search/apply", 9, false, BLUE, (COLS[3]+75+COLS[4]-39)/2-20, R1-16, frame);

  // Outcome: Contract
  box("Hợp đồng thành lập", "Application\n→ Approved", BGL, DIV, COLS[6]-80, R1-36, 160, 72, frame);
  hl(COLS[4]+39, COLS[6]-80, R1, DIV, frame);
  arrowHead(COLS[6]-80-4, R1-5, DIV, frame);
  t("approve", 9, false, TL, COLS[5]+20, R1-16, frame);

  // ── Row 2: Scout Flow ──
  const R2 = 310;

  // Scout trigger
  box("Tìm bác sĩ (Scout)", "Search by criteria\nDisplay ID", GREENLT, GREEN, COLS[1]-75, R2-36, 150, 72, frame);
  hl(COLS[0]+39, COLS[1]-75, R2, GREEN, frame);
  arrowHead(COLS[1]-75-4, R2-5, GREEN, frame);
  t("scout", 9, false, TL, (COLS[0]+39+COLS[1]-75)/2-15, R2-16, frame);

  // Scout function
  box("Block Check", "Doctor not blocked\n→ Allow scout", ORANGELT, ORANGE, COLS[2]-80, R2-36, 160, 72, frame);
  hl(COLS[1]+75, COLS[2]-80, R2, ORANGE, frame);
  arrowHead(COLS[2]-80-4, R2-5, ORANGE, frame);

  // Doctor receives scout
  box("Nhận Scout", "Chấp nhận\n/ Từ chối", BLUELT, BLUE, COLS[4]-80, R2-36, 160, 72, frame);
  hl(COLS[2]+80, COLS[4]-80, R2, BLUE, frame, true);
  arrowHead(COLS[4]-80-4, R2-5, BLUE, frame);
  t("push notify", 9, false, TL, (COLS[2]+80+COLS[4]-80)/2-20, R2-16, frame);

  // Outcome
  box("Scout → Accepted\n→ Contract", "Hospital approve\n→ Active", BGL, DIV, COLS[6]-80, R2-36, 160, 72, frame);
  hl(COLS[4]+80, COLS[6]-80, R2, DIV, frame);
  arrowHead(COLS[6]-80-4, R2-5, DIV, frame);

  // Error branches
  vl(COLS[2]-40, R2+36, R2+80, RED, frame, true);
  r(160, 44, REDLT, COLS[2]-120, R2+80, frame, 6, RED, true);
  t("Doctor Blocked → Hospital không thấy", 9, false, RED, COLS[2]-118, R2+94, frame, 156);
  vl(COLS[4], R2+36, R2+80, RED, frame, true);
  r(160, 44, REDLT, COLS[4]-80, R2+80, frame, 6, RED, true);
  t("Doctor từ chối → Scout Rejected", 9, false, RED, COLS[4]-78, R2+94, frame, 156);

  // ── Row 3: Admin Flow ──
  const R3 = 430;

  // Admin actor (orange)
  el(78, ORANGELT, COLS[5]-39, R3-39, frame, ORANGE);
  el(20, ORANGE, COLS[5]-10, R3-24, frame);
  r(28, 18, ORANGE, COLS[5]-14, R3-2, frame, 10);
  t("Admin", 11, true, TH, COLS[5]-20, R3+50, frame, 60);
  t("Internal Ops", 10, false, TL, COLS[5]-20, R3+64, frame, 60);

  box("Quản lý thành viên", "Doctor / Hospital\nSuspend / Billing", ORANGELT, ORANGE, COLS[4]-80, R3-48, 160, 88, frame);
  box("Policy Version", "Tạo / Công khai\nBuộc đồng ý", ORANGELT, ORANGE, COLS[4]-80, R3+52, 160, 72, frame);
  hl(COLS[4]+80, COLS[5]-39, R3, ORANGE, frame);
  arrowHead(COLS[5]-39-4, R3-5, ORANGE, frame);

  // LINE Integration
  const R4 = 530;
  box("LINE Webhook", "Doctor liên kết LINE\nSignature verify", ORANGELT, ORANGE, COLS[2]-80, R4-36, 160, 72, frame);
  box("Thông báo LINE", "Kích hoạt sau liên kết\nWebhook → Backend", BGL, DIV, COLS[6]-80, R4-36, 160, 72, frame);
  hl(COLS[4]-80, COLS[2]+80, R4, ORANGE, frame);
  hl(COLS[2]+80, COLS[6]-80, R4, DIV, frame);
  arrowHead(COLS[2]+80-4, R4-5, ORANGE, frame);
  arrowHead(COLS[6]-80-4, R4-5, DIV, frame);
  t("LINE OAuth", 9, false, TL, COLS[3]-20, R4-16, frame);

  // ══════════════════════════════════════════════
  // TECHNOLOGY TABLE (BÊN PHẢI x=1800)
  // ══════════════════════════════════════════════
  const TX = 1800;
  let TY = 78;
  t("TECHNOLOGY STACK", 13, true, TH, TX, TY, frame);
  t("Các công nghệ sử dụng và mục đích", 10, false, TL, TX, TY+18, frame, 460);
  TY += 42;

  r(460, 32, BLUELT, TX, TY, frame, 6, BLUE);
  t("Technology", 10, true, BLUE, TX+12, TY+10, frame);
  t("Mô tả mục đích sử dụng", 10, true, BLUE, TX+160, TY+10, frame);
  TY += 32;

  const techList = [
    ["Flutter", "Mobile app cho Doctor & Hospital (iOS/Android)"],
    ["React/Next.js", "Admin Portal — web dashboard quản lý nền tảng"],
    ["NestJS", "Backend REST API — 134 endpoints (Doctor/Hospital/Admin)"],
    ["PostgreSQL", "Database chính: Job, Application, Scout, Contract, User"],
    ["Redis", "Cache session, rate limiting, job queue state"],
    ["BullMQ", "Job queue — sinh PDF bất đồng bộ, LINE notification"],
    ["AWS S3", "Storage PDF Điều kiện + PDF Hợp đồng"],
    ["LINE Messaging API", "Webhook liên kết tài khoản + push notification Doctor"],
    ["JWT", "Authentication token — Doctor/Hospital/Admin"],
    ["PDF Generator", "Wkhtmltopdf / Puppeteer — sinh PDF từ Work Condition"],
  ];
  techList.forEach(([tech, desc], i) => {
    const rowH = 56;
    r(460, rowH, i%2===0?WHITE:BGL, TX, TY, frame, 0, DIV);
    t(tech, 11, true, ORANGE, TX+12, TY+8, frame, 140);
    t(desc, 10, false, TM, TX+160, TY+8, frame, 290);
    r(460, 1, DIV, TX, TY+rowH-1, frame);
    TY += rowH;
  });

  r(460, 72, BLUELT, TX, TY+12, frame, 6, BLUE);
  t("GHI CHU", 10, true, BLUE, TX+12, TY+20, frame);
  t("Danh sach cong nghe de xuat — Tech Lead chot lai trong DESIGN.md.", 9, false, TH, TX+12, TY+36, frame, 436);
  t("BA chi liet ke de user hinh dung stack tong quan.", 9, false, TH, TX+12, TY+52, frame, 436);

  // ══════════════════════════════════════════════
  // PHẦN B — SITEMAP WBS TREE
  // ══════════════════════════════════════════════
  const SY = 650;
  r(1780, 1, DIV, 40, SY-10, frame);
  t("SITEMAP — WBS TREE (Actor + Hanh dong)", 13, true, TH, 40, SY+5, frame, 600);
  t("Level 1: Feature · Level 2: Actor · Level 3: Hanh dong (verb-first) · Level 4: Screen/Popup", 10, false, TL, 40, SY+23, frame, 700);

  // Legend
  r(380, 44, BGL, 40, SY+45, frame, 6, DIV);
  t("LEGEND:", 9, true, TH, 52, SY+58, frame);
  r(60, 18, BLUE, 110, SY+53, frame, 4);
  t("Root", 9, false, WHITE, 120, SY+57, frame);
  r(60, 18, GREENLT, 180, SY+53, frame, 4, GREEN);
  t("Actor", 9, false, GREEN, 188, SY+57, frame);
  r(60, 18, BGL, 250, SY+53, frame, 4, BLUE);
  t("Hanh dong", 9, false, BLUE, 255, SY+57, frame);
  r(60, 18, REDLT, 325, SY+53, frame, 4, RED, true);
  t("Error/Popup", 9, false, RED, 327, SY+57, frame);

  // Root node
  const rootY = SY + 110;
  const rootX = 890;
  r(280, 44, BLUE, rootX-140, rootY, frame, 8);
  t("Medical Platform — Nen tang ket noi y te", 13, true, WHITE, rootX-130, rootY+12, frame, 260);

  // Connector root → actors
  vl(rootX, rootY+44, rootY+88, DIV, frame);
  hl(200, 890, rootY+88, DIV, frame);
  hl(890, 1580, rootY+88, DIV, frame);

  // Actors (Level 2)
  const L2Y = rootY + 100;
  const actors = [
    {x:200, label:"Doctor", sub:"Tìm việc / Ứng tuyển", color:BLUE, lt:BLUELT},
    {x:700, label:"Hospital", sub:"Đăng tin / Scout", color:GREEN, lt:GREENLT},
    {x:1200, label:"Admin", sub:"Vận hành / Quản lý", color:ORANGE, lt:ORANGELT},
    {x:1580, label:"He thong", sub:"LINE / PDF / System", color:PURP, lt:cv(251,239,255)},
  ];

  actors.forEach(a => {
    vl(a.x, rootY+88, L2Y, DIV, frame);
    r(180, 52, a.lt, a.x-90, L2Y, frame, 8, a.color);
    t(a.label, 12, true, a.color, a.x-75, L2Y+10, frame, 150);
    t(a.sub, 10, false, TM, a.x-75, L2Y+28, frame, 150);
  });

  // Level 3: Actions + Level 4: Screens
  const L3Y = L2Y + 68;
  const actorActions = [
    { // Doctor
      ax: 200, color: BLUE, lt: BLUELT, actions: [
        {label:"Dang ky tai khoan", screens:["DR_AUTH_001 Form"]},
        {label:"Tim kiem Job", screens:["DR_JOB_001 List", "DR_JOB_002 Filter"]},
        {label:"Ung tuyen Job", screens:["DR_JOB_003 Detail", "DR_JOB_004 Modal"]},
        {label:"Quan ly Scout", screens:["DR_SCOU_001 List", "DR_SCOU_002 Detail"]},
        {label:"Ky hop dong", screens:["DR_CONT_002 Detail", "DR_CONT_003 Modal"]},
      ]
    },
    { // Hospital
      ax: 700, color: GREEN, lt: GREENLT, actions: [
        {label:"Dang tin tuyen", screens:["HO_JOB_001 List", "HO_JOB_002 Form"]},
        {label:"Duyet ung tuyen", screens:["HO_JOB_003 List", "HO_JOB_004 Detail"]},
        {label:"Scout bac si", screens:["HO_SCOU_001 List", "HO_SCOU_002 Detail", "HO_SCOU_003 Form"]},
        {label:"Quan ly hop dong", screens:["HO_CONT_001 List", "HO_CONT_002 Detail"]},
      ]
    },
    { // Admin
      ax: 1200, color: ORANGE, lt: ORANGELT, actions: [
        {label:"Quan ly Doctor", screens:["AD_DOCT_001 List", "AD_DOCT_002 Detail"]},
        {label:"Quan ly Hospital", screens:["AD_HOSP_001 List", "AD_HOSP_002 Detail"]},
        {label:"Quan ly Policy", screens:["AD_POLI_001 List", "AD_POLI_002 Form"]},
        {label:"Quan ly FAQ", screens:["AD_FAQ_001 List", "AD_FAQ_002 Form"]},
      ]
    },
    { // He thong
      ax: 1580, color: PURP, lt: cv(251,239,255), actions: [
        {label:"Lien ket LINE", screens:["LINE Webhook", "[Popup] LINE OAuth"]},
        {label:"Sinh PDF", screens:["BullMQ Job", "S3 Storage"]},
        {label:"Dong y dieu khoan", screens:["DR_POLI_001 Modal"]},
      ]
    },
  ];

  actorActions.forEach(actor => {
    let curY = L3Y;
    vl(actor.ax, L2Y+52, L3Y, DIV, frame);
    actor.actions.forEach((action, ai) => {
      // Action node (Level 3)
      r(200, 32, BGL, actor.ax-100, curY, frame, 6, actor.color);
      t("✔ " + action.label, 10, true, TH, actor.ax-92, curY+9, frame, 184);
      curY += 32;

      // Screen nodes (Level 4)
      action.screens.forEach((screen, si) => {
        vl(actor.ax-40, curY, curY+28, DIV, frame);
        const isPopup = screen.startsWith('[Popup]');
        const isError = screen.startsWith('[Error]');
        const fillC = isPopup ? cv(251,239,255) : (isError ? REDLT : WHITE);
        const strokeC = isPopup ? PURP : (isError ? RED : actor.color);
        r(190, 26, fillC, actor.ax-95, curY, frame, 4, strokeC, isPopup||isError);
        t(screen, 9, false, TH, actor.ax-87, curY+7, frame, 176);
        curY += 30;
      });
      curY += 12; // gap between actions
    });
  });

  // Resize frame to fit content
  frame.resize(2280, Math.max(1400, L3Y + 400));

  figma.viewport.scrollAndZoomIntoView([frame]);
  figma.notify("Output 1 done! Frame: " + frame.id);
})();
