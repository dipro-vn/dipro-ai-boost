// =============================================================
// FIGMA PLUGIN SCRIPT — BA Output 3: HiFi Screens + Items Tables
// Feature: Medical Platform — Nền tảng kết nối y tế
//
// 3 màn hình đại diện (layout dọc):
//   Row 1: DR_JOB_001 — Job List (Doctor App)
//   Row 2: HO_SCOU_002 — Doctor Profile (Hospital Scout)
//   Row 3: AD_DOCT_002 — Doctor Detail (Admin Portal)
//
// Chạy TRÊN page hiện tại (node-id=30633-62845)
// =============================================================

(async () => {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });
  await figma.loadFontAsync({ family: "Inter", style: "Bold" });

  const cv = (r,g,b) => ({r:r/255, g:g/255, b:b/255});
  const WHITE  = cv(255,255,255);
  const BGL    = cv(246,248,250);
  const BLUE   = cv(9,105,218);
  const BLUELT = cv(229,246,255);
  const GREEN  = cv(26,127,55);
  const GREENLT= cv(237,253,240);
  const ORANGE = cv(216,97,7);
  const ORANGELT=cv(255,249,235);
  const RED    = cv(207,34,46);
  const REDLT  = cv(255,246,245);
  const PURP   = cv(102,57,186);
  const PURPLT = cv(251,239,255);
  const TH     = cv(36,41,47);
  const TM     = cv(66,74,83);
  const TL     = cv(110,119,125);
  const DIV    = cv(208,215,222);
  const INP    = cv(234,238,242);
  const BGDK   = cv(26,31,46);

  const page = figma.currentPage;

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

  // Badge overlay
  function badge(num, x, y, color, p) {
    el(20, color, x, y, p);
    const n = t(String(num), 10, true, WHITE, 0, 0, p);
    n.x = x+10-n.width/2; n.y = y+10-n.height/2;
  }

  // ── Build Items Table ──
  function buildItemsTable(code, name, actorColor, items, x, y, p) {
    const TW = 990;
    const PAD = 12;
    const tbl = figma.createFrame();
    tbl.resize(TW, 100); // resize later
    tbl.x = x; tbl.y = y;
    tbl.fills = [{type:'SOLID', color:WHITE}];
    tbl.strokes = [{type:'SOLID', color:DIV}]; tbl.strokeWeight = 1;
    tbl.cornerRadius = 8;
    p.appendChild(tbl);

    let cy = 14;
    // Header
    const hd = t(code + "  ·  " + name, 14, true, actorColor, PAD, cy, tbl, TW-PAD*2);
    cy += hd.height + 6;
    t("BANG ITEMS — Liet ke DAY DU tung element tren man hinh", 10, false, TL, PAD, cy, tbl, TW-PAD*2);
    cy += 18;
    r(TW, 1, DIV, 0, cy, tbl); cy += 12;

    // Column headers
    r(TW-PAD*2, 28, BGL, PAD, cy, tbl, 4);
    t("#", 10, true, actorColor, PAD+8, cy+9, tbl);
    t("Title (Ten item)", 10, true, actorColor, PAD+40, cy+9, tbl);
    t("Mo ta", 10, true, actorColor, PAD+220, cy+9, tbl);
    t("Action / Behavior", 10, true, actorColor, PAD+430, cy+9, tbl);
    cy += 28;

    // Data rows
    items.forEach(([title, desc, action], i) => {
      let rowH = 48;
      if (action && action.length > 50) rowH = 68;
      if (action && action.length > 100) rowH = 88;
      if (i%2!==0) r(TW, rowH, BGL, 0, cy, tbl);
      t(String(i+1), 10, true, TH, PAD+8, cy+8, tbl);
      t(title, 10, true, TH, PAD+40, cy+8, tbl, 174);
      t(desc, 10, false, TM, PAD+220, cy+8, tbl, 204);
      const actColor = action && action!=="—" ? TH : TL;
      t(action||"—", 10, false, actColor, PAD+430, cy+8, tbl, 538);
      r(TW, 1, DIV, 0, cy+rowH-1, tbl);
      cy += rowH;
    });

    cy += 8;
    tbl.resize(TW, cy);
    return cy;
  }

  // ── Build Error Table ──
  function buildErrorTable(code, errors, x, y, p) {
    const TW = 990;
    const PAD = 12;
    const errBg = cv(255,251,251);
    const tbl = figma.createFrame();
    tbl.resize(TW, 100);
    tbl.x = x; tbl.y = y;
    tbl.fills = [{type:'SOLID', color:errBg}];
    tbl.strokes = [{type:'SOLID', color:RED}]; tbl.strokeWeight = 1;
    tbl.cornerRadius = 8;
    p.appendChild(tbl);

    let cy = 14;
    const hd = t("⚠ ERROR SCENARIOS — " + code, 14, true, RED, PAD, cy, tbl, TW-PAD*2);
    cy += hd.height + 6;
    t("Cac truong hop loi co the xay ra + popup/message/action tiep theo", 10, false, TM, PAD, cy, tbl, TW-PAD*2);
    cy += 18;
    r(TW, 1, RED, 0, cy, tbl); cy += 12;

    // Column headers
    r(TW-PAD*2, 28, REDLT, PAD, cy, tbl, 4);
    t("#", 10, true, RED, PAD+8, cy+9, tbl);
    t("Trigger (nguyen nhan)", 10, true, RED, PAD+40, cy+9, tbl);
    t("Hien thi", 10, true, RED, PAD+240, cy+9, tbl);
    t("Message + Action tiep theo", 10, true, RED, PAD+370, cy+9, tbl);
    cy += 28;

    errors.forEach(([trigger, display, msgAction], i) => {
      let rowH = 68;
      if (msgAction && msgAction.length > 100) rowH = 88;
      if (i%2!==0) r(TW, rowH, cv(255,246,246), 0, cy, tbl);
      t(String(i+1), 10, true, TH, PAD+8, cy+8, tbl);
      t(trigger, 10, true, TH, PAD+40, cy+8, tbl, 194);
      t(display, 10, true, RED, PAD+240, cy+8, tbl, 124);
      t(msgAction, 10, false, TM, PAD+370, cy+8, tbl, 596);
      r(TW, 1, cv(255,220,220), 0, cy+rowH-1, tbl);
      cy += rowH;
    });

    cy += 8;
    tbl.resize(TW, cy);
    return cy;
  }

  // ══════════════════════════════════════════════
  // MAIN FRAME
  // ══════════════════════════════════════════════
  const frame = figma.createFrame();
  frame.name = "Output 3 — HiFi Screens + Bang Chi Tiet Item";
  frame.resize(1450, 100); // will resize
  frame.x = 200; frame.y = 3500;
  frame.fills = [{type:'SOLID', color:BGL}];
  page.appendChild(frame);

  // Title
  t("Output 3 — HiFi Screens + Bang Items + Error Scenarios", 18, true, TH, 40, 24, frame, 1200);
  t("3 man hinh dai dien: DR_JOB_001 (Doctor Job List) · HO_SCOU_002 (Hospital Scout Doctor) · AD_DOCT_002 (Admin Doctor Detail)", 11, false, TL, 40, 48, frame, 1200);

  const PHONE_X = 40;
  const PHONE_Y_START = 100;
  const TABLE_X = 470;
  const ROW_GAP = 60;
  const PHONE_H = 844;
  const ROW_HEIGHT = 1600; // fixed per row (items + errors + gaps)

  let totalH = PHONE_Y_START;

  // ══════════════════════════════════════════════
  // ROW 1: DR_JOB_001 — Job List (Doctor App)
  // ══════════════════════════════════════════════
  const row1Y = PHONE_Y_START;

  // Phone frame
  const phone1 = figma.createFrame();
  phone1.name = "DR_JOB_001 — Job List";
  phone1.resize(390, PHONE_H);
  phone1.x = PHONE_X; phone1.y = row1Y;
  phone1.fills = [{type:'SOLID', color:WHITE}];
  phone1.cornerRadius = 12;
  phone1.clipsContent = true;
  frame.appendChild(phone1);

  // Status bar
  r(390, 44, BGL, 0, 0, phone1);
  t("10:30", 14, true, TH, 16, 15, phone1);
  const sw1 = t("●●● WiFi", 12, false, TH, 0, 16, phone1);
  sw1.x = 374 - sw1.width;

  // Nav
  r(390, 56, WHITE, 0, 44, phone1);
  const nt1 = t("求人検索 / Tim kiem Job", 15, true, TH, 0, 58, phone1);
  nt1.x = 195 - nt1.width/2;
  const nb1 = t("🔔 3", 13, false, BLUE, 0, 60, phone1);
  nb1.x = 358 - nb1.width;
  r(390, 1, DIV, 0, 99, phone1);

  // Search bar
  r(358, 44, INP, 16, 108, phone1, 6);
  t("🔍  Tim theo ten, chuyen khoa...", 13, false, TL, 32, 122, phone1);

  // Filter chips
  const chips = ["Tat ca", "Noi khoa", "Ngoai khoa", "Khu vuc", "Luong"];
  chips.forEach((chip, i) => {
    const chipW = chip.length * 8 + 24;
    const chipX = 16 + chips.slice(0,i).reduce((acc,c,j) => acc+c.length*8+24+8,0);
    r(chipW, 28, i===0?BLUE:WHITE, chipX, 160, phone1, 14, i===0?null:DIV);
    t(chip, 11, true, i===0?WHITE:TL, chipX+(chipW-chip.length*7)/2, 165, phone1);
  });

  // Job cards (2 cards)
  const jobs = [
    {title:"Noi khoa thuong tru", hospital:"Tokyo Medical Center", tags:["Noi khoa","Thuong tru","Tokyo"], salary:"¥1,500,000~/thang", date:"3 ngay truoc", heart:"♥"},
    {title:"Ngoai khoa part-time", hospital:"Yokohama Hospital", tags:["Ngoai khoa","Non-chan","Kanagawa"], salary:"¥60,000~/lan", date:"1 tuan truoc", heart:"♡"},
    {title:"Tam than khoa spot", hospital:"Osaka Mental Clinic", tags:["Tam than","Spot","Osaka"], salary:"¥80,000~/ngay", date:"2 ngay truoc", heart:"♥"},
  ];
  let jy = 200;
  jobs.forEach(job => {
    r(358, 90, WHITE, 16, jy, phone1, 6, DIV);
    t(job.title, 13, true, TH, 28, jy+10, phone1, 290);
    t(job.hospital, 11, false, TL, 28, jy+28, phone1);
    t(job.heart, 16, false, RED, 352, jy+10, phone1);
    const tgs = t(job.tags.join(" · "), 10, false, BLUE, 28, jy+46, phone1, 290);
    t(job.salary, 13, true, BLUE, 28, jy+66, phone1);
    t(job.date, 11, false, TL, 270, jy+66, phone1);
    jy += 100;
  });

  // Number badges on phone
  badge(1, 6, 108, BLUE, phone1);  // search bar
  badge(2, 6, 160, BLUE, phone1);  // filter chips
  badge(3, 6, 200, BLUE, phone1);  // job card 1
  badge(4, 6, 300, BLUE, phone1);  // job card 2
  badge(5, 6, 400, BLUE, phone1);  // job card 3

  // Build Items table
  const items1 = [
    ["Status Bar", "Thanh trang thai tren cung: gio, pin, wifi", "—"],
    ["Nav Title 'Tim kiem Job'", "Tieu de trung tam navigation bar", "—"],
    ["Badge thong bao (🔔 3)", "So thong bao chua doc, goc phai nav", "TAP → DR_NOTI_001 Danh sach thong bao"],
    ["Search bar", "O tim kiem co placeholder, fill mau xam", "TAP → focus keyboard + search theo tu khoa real-time"],
    ["Filter chip 'Tat ca'", "Chip active mau xanh, chon tat ca chuyen khoa", "TAP → hien thi tat ca Job, deselect chip khac"],
    ["Filter chip (Noi khoa / Ngoai khoa / Khu vuc / Luong)", "Chip filter inactive, bo tron, co vien", "TAP → mo DR_JOB_002 Filter modal hoac loc inline"],
    ["Job card (x3+)", "Card vien, co ten Job, Hospital, tags, luong, ngay dang", "TAP → DR_JOB_003 Chi tiet Job"],
    ["Icon ♥ trai tim (per card)", "Icon yeu thich goc phai moi card", "TAP toggle: luu vao DR_JOB_005 Favorites / bo yeu thich"],
    ["Tags (chuyen khoa, loai hinh, khu vuc)", "Pill tags mau xanh duoi ten hospital", "—"],
    ["Luong hien thi", "Text luong in dam mau xanh, goc trai duoi cung card", "—"],
    ["Ngay dang hien thi", "Thoi gian tuong doi, goc phai duoi cung card", "—"],
    ["Pagination / Infinite scroll", "Load them khi scroll den cuoi", "SCROLL DOWN → load them Job (pagination hoac infinite)"],
    ["Pull-to-refresh", "Keo xuong de reload danh sach", "PULL DOWN → goi API reload, hien spinner"],
  ];
  const errItems1 = [
    ["Khong tim thay Job", "Empty state", "Text: 'Khong co tin tuyen phu hop. Thu loc khac.' + Button [Xoa filter]"],
    ["Mat mang khi load", "Banner", "Text: 'Khong co ket noi. Hien thi cache cu.' — tu dismiss khi co mang lai"],
    ["API timeout", "Toast", "Text: 'Tai du lieu that bai. Thu lai.' + Button [Thu lai] goi API"],
    ["Session het han", "Modal", "Text: 'Phien lam viec het han. Vui long dang nhap lai.' + Button [Dang nhap]"],
  ];
  const h1 = buildItemsTable("DR_JOB_001", "Danh sach Job / Tim kiem", BLUE, items1, TABLE_X, row1Y, frame);
  buildErrorTable("DR_JOB_001", errItems1, TABLE_X, row1Y + h1 + 20, frame);

  // ══════════════════════════════════════════════
  // ROW 2: HO_SCOU_002 — Doctor Profile (Hospital Scout)
  // ══════════════════════════════════════════════
  const row2Y = row1Y + ROW_HEIGHT;

  const phone2 = figma.createFrame();
  phone2.name = "HO_SCOU_002 — Doctor Profile (Scout)";
  phone2.resize(390, PHONE_H);
  phone2.x = PHONE_X; phone2.y = row2Y;
  phone2.fills = [{type:'SOLID', color:WHITE}];
  phone2.cornerRadius = 12;
  phone2.clipsContent = true;
  frame.appendChild(phone2);

  // Status bar
  r(390, 44, BGL, 0, 0, phone2);
  t("10:35", 14, true, TH, 16, 15, phone2);
  const sw2 = t("●●● WiFi", 12, false, TH, 0, 16, phone2);
  sw2.x = 374 - sw2.width;

  // Nav
  r(390, 56, WHITE, 0, 44, phone2);
  t("←", 20, false, GREEN, 16, 60, phone2);
  const nt2 = t("Ho so Bac si / Physician Profile", 15, true, TH, 0, 58, phone2);
  nt2.x = 195 - nt2.width/2;
  r(390, 1, DIV, 0, 99, phone2);

  // Hero section
  r(390, 140, BGL, 0, 100, phone2);
  el(72, BLUELT, 159, 112, phone2, BLUE);
  const docInitial = t("DR", 24, true, BLUE, 0, 0, phone2);
  docInitial.x = 195 - docInitial.width/2;
  docInitial.y = 140;
  t("Bac si #DR-20240312", 16, true, TH, 0, 180, phone2).x = 195-60;
  t("Display ID — thong tin ca nhan an danh", 11, false, TL, 0, 200, phone2).x = 195-80;
  r(390, 1, DIV, 0, 240, phone2);

  // Tags row
  r(70, 24, BLUELT, 16, 252, phone2, 12);
  t("Noi khoa", 10, true, BLUE, 22, 258, phone2);
  r(60, 24, BLUELT, 94, 252, phone2, 12);
  t("Ngoai khoa", 10, true, BLUE, 98, 258, phone2);
  r(100, 24, GREENLT, 162, 252, phone2, 12);
  t("KN 10+ nam", 10, true, GREEN, 168, 258, phone2);

  // Info rows
  const ph2Infos = [
    ["Thu nhap mong muon", "¥1,200,000〜/thang"],
    ["Loai hinh lam viec", "Thuong tru / Non-chan"],
    ["Khu vuc mong muon", "Tokyo, Kanagawa"],
    ["Thoi gian bat dau", "4/2024〜"],
  ];
  let py2 = 290;
  ph2Infos.forEach(([label, val]) => {
    r(390, 48, WHITE, 0, py2, phone2);
    r(390, 1, DIV, 0, py2+47, phone2);
    t(label, 12, false, TL, 16, py2+10, phone2);
    const vt = t(val, 13, true, TH, 0, py2+24, phone2);
    vt.x = 374 - vt.width;
    py2 += 48;
  });

  // Section header
  r(390, 40, BGL, 0, py2, phone2);
  t("Chuyen mon va chung chi", 13, true, TH, 16, py2+12, phone2);
  py2 += 40;
  r(390, 100, WHITE, 0, py2, phone2);
  t("Chuyen gia Noi khoa, chung chi Ngoai khoa. Thanh vien Hoi Y khoa Nhat Ban. Tieng Anh tot (TOEIC 850).", 13, false, TL, 16, py2+10, phone2, 358);

  // Sticky CTA
  r(390, 1, DIV, 0, 764, phone2);
  r(390, 80, WHITE, 0, 765, phone2);
  r(358, 48, GREEN, 16, 773, phone2, 6);
  const ctaT = t("Scout Bac si nay", 16, true, WHITE, 0, 0, phone2);
  ctaT.x = 195 - ctaT.width/2; ctaT.y = 785;

  // Badges
  badge(1, 6, 44, GREEN, phone2);
  badge(2, 6, 112, GREEN, phone2);
  badge(3, 6, 250, GREEN, phone2);
  badge(4, 6, 290, GREEN, phone2);
  badge(5, 6, 770, GREEN, phone2);

  const items2 = [
    ["Status Bar", "Thanh trang thai chung (gio, pin, wifi)", "—"],
    ["Nav back ←", "Nut quay lai, mau xanh la", "TAP → HO_SCOU_001 Tim bac si"],
    ["Nav Title", "Tieu de 'Ho so Bac si'", "—"],
    ["Avatar tron (initial DR)", "Hinh dai dien an danh voi chu viet tat", "—"],
    ["Ten: Bac si #DR-20240312", "Display ID an danh — khong lo thong tin that", "—"],
    ["Sub: thong tin an danh", "Luu y Display ID, khong lo info ca nhan", "—"],
    ["Tag chuyen khoa (x3)", "Pill tag mau xanh (Noi khoa / Ngoai khoa / KN)", "—"],
    ["Row 'Thu nhap mong muon'", "Label trai + gia tri phai, co duong ngan", "—"],
    ["Row 'Loai hinh lam viec'", "Label trai + gia tri phai", "—"],
    ["Row 'Khu vuc mong muon'", "Label trai + gia tri phai", "—"],
    ["Row 'Thoi gian bat dau'", "Label trai + gia tri phai", "—"],
    ["Section header 'Chuyen mon'", "Nen xam nhat, chu dam", "—"],
    ["Text mo ta chuyen mon", "Noi dung chuyen mon, chung chi, ngoai ngu", "—"],
    ["Sticky CTA 'Scout Bac si nay'", "Button xanh la co dinh day man hinh", "TAP → HO_SCOU_003 Tao Scout. Disabled neu Doctor da block Hospital nay."],
  ];
  const errItems2 = [
    ["Doctor da block Hospital nay", "Tooltip + Disabled button", "Text: 'Bac si nay khong nhan scout tu benh vien cua ban.' Button [Scout] disabled"],
    ["Khong tai duoc profile", "Empty state", "Text: 'Khong the tai ho so. Thu lai.' + Button [Thu lai]"],
    ["Hospital chua co Billing", "Banner", "Text: 'Nang cap goi de su dung tinh nang Scout.' + Button [Nang cap]"],
    ["Session het han", "Modal", "Text: 'Phien lam viec het han. Dang nhap lai.' + Button [Dang nhap]"],
  ];
  const h2 = buildItemsTable("HO_SCOU_002", "Ho so Doctor (Hospital Scout)", GREEN, items2, TABLE_X, row2Y, frame);
  buildErrorTable("HO_SCOU_002", errItems2, TABLE_X, row2Y + h2 + 20, frame);

  // ══════════════════════════════════════════════
  // ROW 3: AD_DOCT_002 — Doctor Detail (Admin Portal — Web/iPad)
  // ══════════════════════════════════════════════
  const row3Y = row2Y + ROW_HEIGHT;

  // Admin Portal is web — show as iPad/desktop mockup instead of mobile phone
  const phone3 = figma.createFrame();
  phone3.name = "AD_DOCT_002 — Doctor Detail (Admin Web Portal)";
  phone3.resize(390, PHONE_H);
  phone3.x = PHONE_X; phone3.y = row3Y;
  phone3.fills = [{type:'SOLID', color:WHITE}];
  phone3.cornerRadius = 12;
  phone3.clipsContent = true;
  frame.appendChild(phone3);

  // Status bar (web style — orange theme for Admin)
  r(390, 44, ORANGELT, 0, 0, phone3);
  t("Admin Portal", 13, true, ORANGE, 16, 14, phone3);
  t("v2.1", 11, false, TL, 320, 16, phone3);

  // Nav
  r(390, 56, WHITE, 0, 44, phone3);
  t("←", 20, false, ORANGE, 16, 60, phone3);
  const nt3 = t("Chi tiet Bac si", 15, true, TH, 0, 58, phone3);
  nt3.x = 195 - nt3.width/2;
  r(390, 1, DIV, 0, 99, phone3);

  // Tab row
  r(390, 44, BGL, 0, 100, phone3);
  const tabs = ["Thong tin", "Ung tuyen", "Scout"];
  tabs.forEach((tab, i) => {
    t(tab, 13, i===0, i===0?ORANGE:TL, 16+i*130, 118, phone3);
    if (i===0) r(100, 2, ORANGE, 16, 142, phone3);
  });
  r(390, 1, DIV, 0, 144, phone3);

  // Doctor info
  r(390, 100, BGL, 0, 145, phone3);
  el(56, ORANGELT, 16, 160, phone3, ORANGE);
  t("田", 22, true, ORANGE, 30, 175, phone3);
  t("Tanaka Taro", 15, true, TH, 84, 158, phone3);
  t("DR-001 | tanaka@example.com", 11, false, TL, 84, 178, phone3);
  r(80, 24, GREENLT, 84, 198, phone3, 12);
  t("Active", 11, true, GREEN, 96, 204, phone3);

  // Info rows
  const ph3Infos = [
    ["Ngay dang ky", "15/10/2023"],
    ["Dang nhap cuoi", "Hom nay 09:22"],
    ["Lien ket LINE", "✅ Da lien ket"],
    ["So ung tuyen", "12 ung tuyen"],
    ["Scout nhan duoc", "5 scout"],
    ["Hop dong thanh lap", "3 hop dong"],
  ];
  let py3 = 260;
  ph3Infos.forEach(([label, val]) => {
    r(390, 44, py3%88===0?BGL:WHITE, 0, py3, phone3);
    r(390, 1, DIV, 0, py3+43, phone3);
    t(label, 12, false, TL, 16, py3+10, phone3);
    const vt3 = t(val, 13, true, TH, 0, py3+22, phone3);
    vt3.x = 374 - vt3.width;
    py3 += 44;
  });

  // Warning box
  r(358, 60, cv(255,246,245), 16, py3+8, phone3, 6, RED);
  t("⚠️ Dung tai khoan se anh huong ngay lap tuc. Kiem tra ki truoc khi thao tac.", 10, false, RED, 24, py3+18, phone3, 342);

  // Sticky CTA
  r(390, 1, DIV, 0, 764, phone3);
  r(390, 80, WHITE, 0, 765, phone3);
  r(358, 48, RED, 16, 773, phone3, 6);
  const ctaA = t("Dung tai khoan (Suspend)", 15, true, WHITE, 0, 0, phone3);
  ctaA.x = 195 - ctaA.width/2; ctaA.y = 785;

  // Badges
  badge(1, 6, 44, ORANGE, phone3);
  badge(2, 6, 100, ORANGE, phone3);
  badge(3, 6, 145, ORANGE, phone3);
  badge(4, 6, 260, ORANGE, phone3);
  badge(5, 6, 770, ORANGE, phone3);

  const items3 = [
    ["Admin header bar", "Thanh tieu de 'Admin Portal' mau cam nhat", "—"],
    ["Nav back ←", "Quay lai AD_DOCT_001 Danh sach Doctor", "TAP → AD_DOCT_001"],
    ["Nav title 'Chi tiet Bac si'", "Tieu de trang, trung tam nav bar", "—"],
    ["Tab 'Thong tin'", "Tab dang active, hien info co ban Doctor", "TAP → hien tab Thong tin (default)"],
    ["Tab 'Ung tuyen'", "Tab inactive — danh sach ung tuyen cua Doctor", "TAP → hien danh sach ung tuyen"],
    ["Tab 'Scout'", "Tab inactive — danh sach scout Doctor nhan duoc", "TAP → hien danh sach scout"],
    ["Avatar tron (initial)", "Hinh dai dien Admin view — co the thay hinh that (khac Doctor App)", "—"],
    ["Ten Doctor + ID", "Ten day du, Display ID, email admin", "—"],
    ["Status badge 'Active'", "Pill trang thai: Active (xanh) / Suspended (do)", "—"],
    ["Row 'Ngay dang ky'", "Thong tin dang ky tai khoan", "—"],
    ["Row 'Dang nhap cuoi'", "Thoi gian dang nhap gan nhat", "—"],
    ["Row 'Lien ket LINE'", "Trang thai lien ket LINE (da lien ket / chua)", "—"],
    ["Row 'So ung tuyen'", "Tong so ung tuyen Doctor da gui", "TAP → chuyen sang Tab 'Ung tuyen'"],
    ["Row 'Scout nhan duoc'", "Tong so scout Hospital da gui cho Doctor", "TAP → chuyen sang Tab 'Scout'"],
    ["Row 'Hop dong thanh lap'", "So hop dong da ky ket thanh cong", "—"],
    ["Warning box do", "Canh bao truoc khi thuc hien suspend", "—"],
    ["Sticky CTA 'Dung tai khoan'", "Button do, chi hien khi account active", "TAP → Modal xac nhan → PATCH /admin/doctor/{id}/suspend"],
  ];
  const errItems3 = [
    ["Doctor da bi dung truoc do", "Button thay thanh 'Mo khoa'", "Text: 'Tai khoan dang bi dung.' Button [Mo khoa] → PATCH unsuspend (TBD - xem OQ-04)"],
    ["Thao tac suspend that bai", "Toast error", "Text: 'Khong the dung tai khoan. Thu lai.' + Button [Thu lai]"],
    ["Khong co quyen Admin", "Modal 403", "Text: 'Ban khong co quyen thuc hien thao tac nay.' + Button [Quay lai]"],
    ["Session Admin het han", "Redirect Login", "Chuyen huong ve trang Admin Login, luu return URL"],
  ];
  buildItemsTable("AD_DOCT_002", "Chi tiet Doctor (Admin View)", ORANGE, items3, TABLE_X, row3Y, frame);
  buildErrorTable("AD_DOCT_002", errItems3, TABLE_X, row3Y + 1100 + 20, frame);

  // Resize final frame
  frame.resize(1450, row3Y + ROW_HEIGHT + 80);

  figma.viewport.scrollAndZoomIntoView([frame]);
  figma.notify("Output 3 done! 3 rows: DR_JOB_001 / HO_SCOU_002 / AD_DOCT_002");
})();
