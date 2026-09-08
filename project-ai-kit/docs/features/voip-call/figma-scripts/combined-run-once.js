// =============================================================
// FIGMA PLUGIN — BA Flow Diagrams for VoIP Call Feature
// Tạo 2 pages:
//   1. "BA - Flow Tổng Quan" — flow diagram đầy đủ
//   2. "BA - Screen Flow"    — 8 screen cards + arrows
//
// Cách chạy (Figma Desktop):
//   Plugins > Development > Import plugin from manifest...
//   → Chọn file manifest.json trong thư mục này → Run
//
// Hoặc: Plugins > Development > New Plugin (chọn "Run once") → paste code này
// =============================================================

// ============================================================
// SHARED UTILITIES
// ============================================================
function hexToRgb(hex) {
  hex = hex.replace("#", "");
  if (hex.length === 3) hex = hex.split("").map(c => c + c).join("");
  const n = parseInt(hex, 16);
  return {
    r: ((n >> 16) & 255) / 255,
    g: ((n >> 8) & 255) / 255,
    b: (n & 255) / 255
  };
}

function makeRect({ x, y, w, h, fill, strokeColor, radius = 0, name = "" }) {
  const rect = figma.createRectangle();
  rect.x = x; rect.y = y;
  rect.resize(w, h);
  rect.cornerRadius = radius;
  rect.fills = [{ type: "SOLID", color: hexToRgb(fill) }];
  if (strokeColor) {
    rect.strokes = [{ type: "SOLID", color: hexToRgb(strokeColor) }];
    rect.strokeWeight = 1.5;
  }
  if (name) rect.name = name;
  return rect;
}

function makeTextNode({ x, y, w, content, size, style = "Regular", color = "#24292F", align = "LEFT" }) {
  const t = figma.createText();
  t.fontName = { family: "Inter", style };
  t.fontSize = size;
  if (w) {
    t.textAutoResize = "HEIGHT";
    t.resize(w, 20);
  }
  t.characters = content;
  t.x = x; t.y = y;
  t.textAlignHorizontal = align;
  t.fills = [{ type: "SOLID", color: hexToRgb(color) }];
  return t;
}

function makeArrowVector({ x1, y1, x2, y2, color = "#0969DA", dashed = false }) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.max(Math.sqrt(dx * dx + dy * dy), 0.001);
  const ux = dx / len, uy = dy / len;
  const headLen = 8;
  const lx = x2 - headLen * ux + headLen * 0.4 * uy;
  const ly = y2 - headLen * uy - headLen * 0.4 * ux;
  const rx = x2 - headLen * ux - headLen * 0.4 * uy;
  const ry = y2 - headLen * uy + headLen * 0.4 * ux;

  const arrow = figma.createVector();
  arrow.vectorPaths = [{
    windingRule: "NONZERO",
    data: `M ${x1} ${y1} L ${x2} ${y2} M ${x2} ${y2} L ${lx} ${ly} M ${x2} ${y2} L ${rx} ${ry}`
  }];
  arrow.strokes = [{ type: "SOLID", color: hexToRgb(color) }];
  arrow.strokeWeight = 1.5;
  arrow.fills = [];
  if (dashed) arrow.dashPattern = [5, 3];
  return arrow;
}

// ============================================================
// PAGE 1 — BA - Flow Tổng Quan
// ============================================================
function buildPage1() {
  const page = figma.createPage();
  page.name = "BA - Flow Tổng Quan";
  figma.currentPage = page;

  const all = []; // collect nodes before appending to frame

  // Shape helpers (local to page1)
  function screenBox({ x, y, w = 150, h = 60, code, name, fill = "#E8F4FD", stroke = "#0969DA" }) {
    const bg = makeRect({ x, y, w, h, fill, strokeColor: stroke, radius: 8, name: code });
    const t1 = makeTextNode({ x: x + 6, y: y + 8, w: w - 12, content: code, size: 11, style: "Bold", color: "#24292F", align: "CENTER" });
    const t2 = makeTextNode({ x: x + 6, y: y + 28, w: w - 12, content: name, size: 11, color: "#424A53", align: "CENTER" });
    return [bg, t1, t2];
  }

  function decisionDiamond({ x, y, w = 130, h = 56, label }) {
    const cx = x + w / 2, cy = y + h / 2;
    const v = figma.createVector();
    v.vectorPaths = [{ windingRule: "NONZERO", data: `M ${cx} ${y} L ${x + w} ${cy} L ${cx} ${y + h} L ${x} ${cy} Z` }];
    v.fills = [{ type: "SOLID", color: hexToRgb("#FFF9EB") }];
    v.strokes = [{ type: "SOLID", color: hexToRgb("#F4860C") }];
    v.strokeWeight = 1.5;
    v.name = label;
    const t = makeTextNode({ x: x + 10, y: cy - 8, w: w - 20, content: label, size: 10, color: "#424A53", align: "CENTER" });
    return [v, t];
  }

  function externalEllipse({ x, y, w = 160, h = 48, label, fill = "#EDFDF0", stroke = "#1A7F37" }) {
    const e = figma.createEllipse();
    e.x = x; e.y = y;
    e.resize(w, h);
    e.fills = [{ type: "SOLID", color: hexToRgb(fill) }];
    e.strokes = [{ type: "SOLID", color: hexToRgb(stroke) }];
    e.strokeWeight = 1.5;
    e.name = label;
    const t = makeTextNode({ x: x + 10, y: y + h / 2 - 7, w: w - 20, content: label, size: 11, color: "#24292F", align: "CENTER" });
    return [e, t];
  }

  function arrow({ x1, y1, x2, y2, color = "#0969DA", label = "", dashed = false }) {
    const nodes = [makeArrowVector({ x1, y1, x2, y2, color, dashed })];
    if (label) {
      const mx = (x1 + x2) / 2 - 40, my = (y1 + y2) / 2 - 14;
      nodes.push(makeTextNode({ x: mx, y: my, w: 80, content: label, size: 10, color: color === "#CF222E" ? "#CF222E" : "#6E7781", align: "CENTER" }));
    }
    return nodes;
  }

  // ---- Layout constants ----
  const BW = 150, BH = 60, DW = 130, DH = 56, EW = 155, EH = 48;
  const GAP = 36;
  const R1 = 80;   // row 1 Y (Dipro Admin happy path)
  const R2 = 300;  // row 2 Y (Company Admin)
  const R3 = 480;  // error row Y

  // X positions — row 1
  const xApp    = 40;
  const xCL     = xApp + 80 + GAP;             // Company List
  const xCD     = xCL + BW + GAP;              // Company Detail
  const xOC     = xCD + BW + GAP;              // Outgoing Call
  const xD1     = xOC + BW + GAP;              // Decision: Response?
  const xIC_DA  = xD1 + DW + GAP;              // In-Call DA
  const xD2     = xIC_DA + BW + GAP;           // Decision: End?
  const xES     = xD2 + DW + GAP;              // Ended Summary
  const xCH     = xES + BW + GAP;              // Call History

  // X positions — row 2 (Company Admin)
  const xPush   = xD1 + 10;
  const xCA_001 = xPush + EW + GAP;
  const xD3     = xCA_001 + BW + GAP;          // Decision: Accept?
  const xCA_002 = xD3 + DW + GAP;              // In-Call CA

  // Title
  all.push(makeTextNode({ x: 40, y: 16, w: 800, content: "Flow Tổng Quan — In-App VoIP Call", size: 18, style: "Bold", color: "#24292F" }));
  all.push(makeTextNode({ x: 40, y: 40, w: 700, content: "Happy path: trái → phải  |  Error branches: xuống dưới  |  Row 2: Company Admin", size: 11, color: "#6E7781" }));

  // Row labels
  all.push(makeTextNode({ x: 40, y: R1 + 18, w: 70, content: "Dipro Admin", size: 10, style: "Bold", color: "#0969DA" }));
  all.push(makeTextNode({ x: 40, y: R2 + 18, w: 90, content: "Company Admin", size: 10, style: "Bold", color: "#1A7F37" }));

  // ---- ROW 1 shapes ----
  // [Mở App]
  all.push(...externalEllipse({ x: xApp, y: R1 + 5, w: 75, h: 46, label: "Mở App", fill: "#F6F8FA", stroke: "#8C959F" }));
  all.push(...arrow({ x1: xApp + 75, y1: R1 + 28, x2: xCL, y2: R1 + 30 }));

  // DA_VOIP_001
  all.push(...screenBox({ x: xCL, y: R1, code: "DA_VOIP_001", name: "Company List" }));
  all.push(...arrow({ x1: xCL + BW, y1: R1 + 30, x2: xCD, y2: R1 + 30, label: "Tap company" }));

  // DA_VOIP_002
  all.push(...screenBox({ x: xCD, y: R1, code: "DA_VOIP_002", name: "Company Detail" }));
  all.push(...arrow({ x1: xCD + BW, y1: R1 + 30, x2: xOC, y2: R1 + 30, label: "Tap \"Gọi\"" }));

  // DA_VOIP_003
  all.push(...screenBox({ x: xOC, y: R1, code: "DA_VOIP_003", name: "Outgoing Call" }));
  all.push(...arrow({ x1: xOC + BW, y1: R1 + 30, x2: xD1, y2: R1 + 28 }));

  // Decision: Response?
  all.push(...decisionDiamond({ x: xD1, y: R1, w: DW, h: DH, label: "Response?" }));
  all.push(...arrow({ x1: xD1 + DW, y1: R1 + 28, x2: xIC_DA, y2: R1 + 30, label: "Accept" }));

  // DA_VOIP_004
  all.push(...screenBox({ x: xIC_DA, y: R1, code: "DA_VOIP_004", name: "In-Call (Caller)" }));
  all.push(...arrow({ x1: xIC_DA + BW, y1: R1 + 30, x2: xD2, y2: R1 + 28 }));

  // Decision: End?
  all.push(...decisionDiamond({ x: xD2, y: R1, w: DW, h: DH, label: "End?" }));
  all.push(...arrow({ x1: xD2 + DW, y1: R1 + 28, x2: xES, y2: R1 + 30, label: "Hang up" }));

  // DA_VOIP_005
  all.push(...screenBox({ x: xES, y: R1, code: "DA_VOIP_005", name: "Call Ended" }));
  all.push(...arrow({ x1: xES + BW, y1: R1 + 30, x2: xCH, y2: R1 + 30, label: "Auto-log" }));

  // DA_VOIP_006
  all.push(...screenBox({ x: xCH, y: R1, code: "DA_VOIP_006", name: "Call History" }));

  // ---- ROW 2 shapes ----
  // Decision → Push/Overlay (down)
  all.push(...arrow({ x1: xD1 + DW / 2, y1: R1 + DH, x2: xD1 + DW / 2, y2: R2, color: "#1A7F37", label: "Ringing" }));

  // Push / Overlay
  all.push(...externalEllipse({ x: xPush, y: R2, w: EW, h: EH, label: "Push / Overlay" }));
  all.push(...arrow({ x1: xPush + EW, y1: R2 + EH / 2, x2: xCA_001, y2: R2 + 30 }));

  // CA_VOIP_001
  all.push(...screenBox({ x: xCA_001, y: R2, code: "CA_VOIP_001", name: "Incoming Call", fill: "#EDFDF0", stroke: "#1A7F37" }));
  all.push(...arrow({ x1: xCA_001 + BW, y1: R2 + 30, x2: xD3, y2: R2 + 28 }));

  // Decision: Accept?
  all.push(...decisionDiamond({ x: xD3, y: R2, w: DW, h: DH, label: "Accept?" }));
  all.push(...arrow({ x1: xD3 + DW, y1: R2 + 28, x2: xCA_002, y2: R2 + 30, label: "Chấp nhận" }));

  // CA_VOIP_002
  all.push(...screenBox({ x: xCA_002, y: R2, code: "CA_VOIP_002", name: "In-Call (Receiver)", fill: "#EDFDF0", stroke: "#1A7F37" }));

  // Connect In-Call DA ↔ In-Call CA (same call)
  all.push(...arrow({ x1: xCA_002 + BW / 2, y1: R2, x2: xIC_DA + BW / 2, y2: R1 + BH, color: "#8250DF", label: "Same call" }));

  // ---- ERROR BRANCHES ----
  // Error 1: Timeout/Reject from DA_VOIP_003 → DA_VOIP_002
  all.push(...arrow({ x1: xOC + BW / 2, y1: R1 + BH, x2: xOC + BW / 2, y2: R3, color: "#CF222E", label: "Timeout/Reject", dashed: true }));
  all.push(...externalEllipse({ x: xOC - 10, y: R3, w: 180, h: 44, label: "Toast: Timeout / Bị từ chối", fill: "#FFF6F5", stroke: "#CF222E" }));
  all.push(...arrow({ x1: xOC - 10 + 90, y1: R3 + 44, x2: xCD + BW / 2, y2: R1 + BH, color: "#CF222E", label: "→ Company Detail", dashed: true }));

  // Error 2: Network lost in call → Call Ended
  all.push(...arrow({ x1: xD2 + DW / 2, y1: R1 + DH, x2: xD2 + DW / 2, y2: R3, color: "#CF222E", label: "Network lost", dashed: true }));
  all.push(...externalEllipse({ x: xD2 - 20, y: R3, w: 170, h: 44, label: "Toast: Kết nối gián đoạn", fill: "#FFF6F5", stroke: "#CF222E" }));
  all.push(...arrow({ x1: xD2 - 20 + 85, y1: R3 + 44, x2: xES + BW / 2, y2: R1 + BH, color: "#CF222E", label: "→ Call Ended", dashed: true }));

  // Error 3: CA Decline
  const R3b = R2 + 120;
  all.push(...arrow({ x1: xD3 + DW / 2, y1: R2 + DH, x2: xD3 + DW / 2, y2: R3b, color: "#CF222E", label: "Từ chối", dashed: true }));
  all.push(...externalEllipse({ x: xD3 - 20, y: R3b, w: 150, h: 44, label: "Dismiss + Toast (Caller)", fill: "#FFF6F5", stroke: "#CF222E" }));

  // Error 4: Mic denied (from Outgoing / Incoming)
  all.push(...arrow({ x1: xOC + BW / 2 - 20, y1: R1 + BH, x2: xCL + BW / 2, y2: R3, color: "#CF222E", label: "Mic denied", dashed: true }));
  all.push(...externalEllipse({ x: xCL - 10, y: R3, w: 160, h: 44, label: "Modal: Cần quyền mic\n+ Mở Cài đặt", fill: "#FFF6F5", stroke: "#CF222E" }));

  // ---- LEGEND ----
  const LY = R3 + 120;
  all.push(makeTextNode({ x: 40, y: LY, w: 600, content: "LEGEND", size: 12, style: "Bold", color: "#24292F" }));
  all.push(...screenBox({ x: 40, y: LY + 20, w: 120, h: 36, code: "", name: "Screen (DA)" }));
  all.push(makeTextNode({ x: 170, y: LY + 28, w: 160, content: "Màn hình Dipro Admin (xanh)", size: 10, color: "#6E7781" }));
  all.push(...screenBox({ x: 40, y: LY + 70, w: 120, h: 36, code: "", name: "Screen (CA)", fill: "#EDFDF0", stroke: "#1A7F37" }));
  all.push(makeTextNode({ x: 170, y: LY + 78, w: 160, content: "Màn hình Company Admin (xanh lá)", size: 10, color: "#6E7781" }));
  all.push(...decisionDiamond({ x: 340, y: LY + 16, w: 100, h: 44, label: "Decision" }));
  all.push(makeTextNode({ x: 450, y: LY + 28, w: 180, content: "Rẽ nhánh điều kiện (cam)", size: 10, color: "#6E7781" }));
  all.push(...externalEllipse({ x: 340, y: LY + 66, w: 100, h: 38, label: "External", fill: "#EDFDF0", stroke: "#1A7F37" }));
  all.push(makeTextNode({ x: 450, y: LY + 76, w: 180, content: "Push / Toast / External event (xanh lá)", size: 10, color: "#6E7781" }));
  all.push(makeArrowVector({ x1: 640, y1: LY + 28, x2: 740, y2: LY + 28, color: "#0969DA" }));
  all.push(makeTextNode({ x: 750, y: LY + 20, w: 130, content: "Happy path (xanh)", size: 10, color: "#6E7781" }));
  all.push(makeArrowVector({ x1: 640, y1: LY + 60, x2: 740, y2: LY + 60, color: "#CF222E", dashed: true }));
  all.push(makeTextNode({ x: 750, y: LY + 52, w: 130, content: "Error path (đỏ, nét đứt)", size: 10, color: "#6E7781" }));
  all.push(makeArrowVector({ x1: 640, y1: LY + 90, x2: 740, y2: LY + 90, color: "#8250DF" }));
  all.push(makeTextNode({ x: 750, y: LY + 82, w: 130, content: "Cross-actor link (tím)", size: 10, color: "#6E7781" }));

  // ---- Build frame ----
  const FW = xCH + BW + 80;
  const FH = LY + 140;
  const frame = figma.createFrame();
  frame.name = "BA - Flow Tổng Quan";
  frame.resize(FW, FH);
  frame.fills = [{ type: "SOLID", color: hexToRgb("#FFFFFF") }];
  for (const n of all) frame.appendChild(n);
  page.appendChild(frame);
  return frame;
}

// ============================================================
// PAGE 2 — BA - Screen Flow
// ============================================================
function buildPage2() {
  const page = figma.createPage();
  page.name = "BA - Screen Flow";
  figma.currentPage = page;

  const CARD_W = 275;
  const PAD = 12;
  const CARD_STROKE = "#D0D7DE";
  const CARD_BG = "#FFFFFF";
  const DIV_COLOR = "#EAEEF2";

  function buildCard({ screenCode, screenName, actor, type, actorColor = "#0969DA", components, nonHappy }) {
    const f = figma.createFrame();
    f.name = screenCode;
    f.fills = [{ type: "SOLID", color: hexToRgb(CARD_BG) }];
    f.strokes = [{ type: "SOLID", color: hexToRgb(CARD_STROKE) }];
    f.strokeWeight = 1;
    f.cornerRadius = 8;
    f.clipsContent = true;
    f.resize(CARD_W, 200); // temp height

    let curY = 0;

    // Header bg
    const hdrBg = makeRect({ x: 0, y: 0, w: CARD_W, h: 38, fill: "#F6F8FA", radius: 0 });
    f.appendChild(hdrBg);

    // Screen code — name
    const t0 = makeTextNode({ x: PAD, y: 8, w: CARD_W - PAD * 2, content: `${screenCode} — ${screenName}`, size: 12, style: "Bold", color: "#24292F" });
    f.appendChild(t0);
    curY = 38;

    // Meta: Actor | Type (colored)
    const metaBg = makeRect({ x: 0, y: curY, w: CARD_W, h: 22, fill: "#FFFFFF", radius: 0 });
    f.appendChild(metaBg);
    const tMeta = makeTextNode({ x: PAD, y: curY + 4, w: CARD_W - PAD * 2, content: `Actor: ${actor}   |   Type: ${type}`, size: 11, color: actorColor });
    f.appendChild(tMeta);
    curY += 22;

    // Divider
    const d1 = makeRect({ x: 0, y: curY, w: CARD_W, h: 1, fill: DIV_COLOR, radius: 0 });
    f.appendChild(d1);
    curY += 1 + 4;

    // COMPONENTS label
    const tCompLbl = makeTextNode({ x: PAD, y: curY, w: CARD_W - PAD * 2, content: "COMPONENTS:", size: 10, style: "Bold", color: "#424A53" });
    f.appendChild(tCompLbl);
    curY += 16;

    for (const comp of components) {
      const tComp = makeTextNode({ x: PAD, y: curY, w: CARD_W - PAD * 2, content: `• ${comp}`, size: 11, color: "#424A53" });
      f.appendChild(tComp);
      curY += tComp.height + 2;
    }
    curY += 4;

    // Divider
    const d2 = makeRect({ x: 0, y: curY, w: CARD_W, h: 1, fill: DIV_COLOR, radius: 0 });
    f.appendChild(d2);
    curY += 1 + 4;

    // NON-HAPPY label
    const tNhLbl = makeTextNode({ x: PAD, y: curY, w: CARD_W - PAD * 2, content: "NON-HAPPY:", size: 10, style: "Bold", color: "#CF222E" });
    f.appendChild(tNhLbl);
    curY += 16;

    for (const nh of nonHappy) {
      const tNh = makeTextNode({ x: PAD, y: curY, w: CARD_W - PAD * 2, content: `• ${nh}`, size: 11, color: "#CF222E" });
      f.appendChild(tNh);
      curY += tNh.height + 2;
    }
    curY += PAD;

    // Resize to actual height
    f.resize(CARD_W, curY);
    return f;
  }

  // ---- Screen data ----
  const screens = [
    {
      screenCode: "DA_VOIP_001", screenName: "Company List",
      actor: "Dipro Admin", type: "List", actorColor: "#0969DA",
      components: [
        "Search bar: Tìm công ty...",
        "List item: Avatar + Tên + Online dot (xanh/xám)",
        "Sub-text: Last call timestamp",
        "Skeleton loader (khi loading)",
        "Pull-to-refresh / Infinite scroll",
        "FAB bottom-right: icon Lịch sử"
      ],
      nonHappy: [
        'Empty: "Chưa có công ty nào được assign"',
        "Load error: Banner + Retry button",
        'Mất mạng: Sticky banner "Không có kết nối"'
      ]
    },
    {
      screenCode: "DA_VOIP_002", screenName: "Company Detail",
      actor: "Dipro Admin", type: "Detail", actorColor: "#0969DA",
      components: [
        "Header: Avatar large + Tên + Status badge",
        "Status badge: Online / Offline / Busy",
        "Info rows: Tên, địa chỉ, đơn hàng active",
        "Recent calls: 3 cuộc gần nhất (thu gọn)",
        'Link "Xem tất cả" → DA_VOIP_006',
        'Sticky bottom: Button "Gọi ngay" (primary)'
      ],
      nonHappy: [
        "Offline: Button disabled + tooltip",
        "Busy: Button disabled + tooltip"
      ]
    },
    {
      screenCode: "DA_VOIP_003", screenName: "Outgoing Call",
      actor: "Dipro Admin", type: "Modal", actorColor: "#0969DA",
      components: [
        "Full-screen overlay (dark bg)",
        "Avatar large + pulse animation (ringing)",
        "Text: Tên company",
        'Text: "Đang gọi..." (animated dots)',
        "Icon btn: Speaker toggle",
        "Icon btn: Mute toggle",
        'Button đỏ: "Kết thúc" (cancel)'
      ],
      nonHappy: [
        "Timeout 30s: Auto dismiss + toast",
        "Rejected: Auto dismiss + toast",
        "Network lost: Auto dismiss + toast",
        'Mic denied: Modal + "Mở Cài đặt"'
      ]
    },
    {
      screenCode: "DA_VOIP_004", screenName: "In-Call (Caller)",
      actor: "Dipro Admin", type: "Modal", actorColor: "#0969DA",
      components: [
        'Full-screen overlay',
        'Call timer top: "00:00" (đếm lên)',
        "Avatar large + tên company (center)",
        "Icon btn: Mute (highlight khi active)",
        "Icon btn: Speaker (highlight khi active)",
        'Button đỏ: "Kết thúc"',
        "Waveform animation khi nói"
      ],
      nonHappy: [
        'Network lost: Toast + auto end → DA_VOIP_005',
        'Company Admin hang up: Toast → DA_VOIP_005'
      ]
    },
    {
      screenCode: "DA_VOIP_005", screenName: "Call Ended Summary",
      actor: "Dipro Admin", type: "Modal", actorColor: "#0969DA",
      components: [
        "Bottom sheet (slide-up animation)",
        "Status icon: xanh (completed) / đỏ (error)",
        "Text: Tên company + Thời lượng + Timestamp",
        "Status badge: Completed/Missed/Declined/Disconnected",
        'Button primary: "Gọi lại"',
        'Button outline: "Đóng"'
      ],
      nonHappy: [
        'Missed: Icon đỏ + badge "Không có phản hồi"',
        'Declined: Icon đỏ + badge "Bị từ chối"',
        'Disconnected: Icon đỏ + badge "Bị gián đoạn"'
      ]
    },
    {
      screenCode: "DA_VOIP_006", screenName: "Call History",
      actor: "Dipro Admin", type: "List", actorColor: "#0969DA",
      components: [
        "Filter tabs: Tất cả / Missed / Completed",
        "List item: Avatar + Tên + Status icon + Thời lượng + Timestamp",
        'Date separator: "Hôm nay" / "Hôm qua" / "DD/MM/YYYY"',
        "Skeleton loader",
        'Swipe-right: shortcut "Gọi lại"'
      ],
      nonHappy: [
        'Không có lịch sử: Empty state "Chưa có cuộc gọi"',
        "Filter Missed rỗng: Empty state",
        "Load error: Banner + Retry"
      ]
    },
    {
      screenCode: "CA_VOIP_001", screenName: "Incoming Call",
      actor: "Company Admin", type: "Modal", actorColor: "#1A7F37",
      components: [
        "Full-screen overlay (native-style)",
        'Avatar large "Dipro Admin" + tên + pulse animation',
        'Text: "Đang gọi đến..."',
        'Button xanh: "Chấp nhận"',
        'Button đỏ: "Từ chối"',
        "Ringing sound + vibration"
      ],
      nonHappy: [
        "App killed: Push notification với Action button",
        "Caller cancel: Auto dismiss overlay",
        'Mic denied: Modal + "Mở Cài đặt"'
      ]
    },
    {
      screenCode: "CA_VOIP_002", screenName: "In-Call (Receiver)",
      actor: "Company Admin", type: "Modal", actorColor: "#1A7F37",
      components: [
        "Full-screen overlay",
        'Call timer top: "00:00" (đếm lên)',
        'Avatar large "Dipro Admin" (center)',
        "Icon btn: Mute toggle",
        "Icon btn: Speaker toggle",
        'Button đỏ: "Kết thúc" → dismiss',
        "Waveform animation khi nói"
      ],
      nonHappy: [
        'Network lost: Toast + auto end',
        'Caller hang up: Toast "Cuộc gọi đã kết thúc"'
      ]
    }
  ];

  // ---- Grid positions: 3 cols ----
  // Row 0: DA_001, DA_002, DA_003
  // Row 1: DA_004, DA_005, DA_006
  // Row 2: CA_001, CA_002
  const gridPos = [
    { col: 0, row: 0 }, { col: 1, row: 0 }, { col: 2, row: 0 },
    { col: 0, row: 1 }, { col: 1, row: 1 }, { col: 2, row: 1 },
    { col: 0, row: 2 }, { col: 1, row: 2 }
  ];

  const COL_W = CARD_W + 50;
  const ROW_GAP = 40;
  const GRID_X = 40;
  const GRID_Y = 80;

  // ---- Main frame ----
  const mainFrame = figma.createFrame();
  mainFrame.name = "BA - Screen Flow";
  mainFrame.resize(GRID_X + COL_W * 3 + 80, 2000);
  mainFrame.fills = [{ type: "SOLID", color: hexToRgb("#F6F8FA") }];

  // Title
  mainFrame.appendChild(makeTextNode({ x: GRID_X, y: 20, w: 800, content: "Screen Flow — In-App VoIP Call (8 screens)", size: 18, style: "Bold", color: "#24292F" }));
  mainFrame.appendChild(makeTextNode({ x: GRID_X, y: 46, w: 700, content: "Xanh dương = Dipro Admin  |  Xanh lá = Company Admin  |  Mũi tên xanh = happy path  |  Đỏ = error path", size: 11, color: "#6E7781" }));

  // Build cards
  const cards = [];
  for (let i = 0; i < screens.length; i++) {
    const card = buildCard(screens[i]);
    cards.push(card);
    mainFrame.appendChild(card);
  }

  // Compute row heights
  const rowH = [0, 0, 0];
  for (let i = 0; i < cards.length; i++) {
    const row = gridPos[i].row;
    rowH[row] = Math.max(rowH[row], cards[i].height);
  }

  const rowStartY = [
    GRID_Y,
    GRID_Y + rowH[0] + ROW_GAP,
    GRID_Y + rowH[0] + ROW_GAP + rowH[1] + ROW_GAP
  ];

  // Section labels
  mainFrame.appendChild(makeTextNode({ x: GRID_X, y: rowStartY[0] - 22, w: 500, content: "DIPRO ADMIN (DA_VOIP_001 → DA_VOIP_006)", size: 11, style: "Bold", color: "#0969DA" }));
  mainFrame.appendChild(makeTextNode({ x: GRID_X, y: rowStartY[2] - 22, w: 500, content: "COMPANY ADMIN (CA_VOIP_001 → CA_VOIP_002)", size: 11, style: "Bold", color: "#1A7F37" }));

  // Place cards
  const cardPos = []; // store {x,y,w,h} per card
  for (let i = 0; i < cards.length; i++) {
    const { col, row } = gridPos[i];
    const cx = GRID_X + col * COL_W;
    const cy = rowStartY[row];
    cards[i].x = cx;
    cards[i].y = cy;
    cardPos.push({ x: cx, y: cy, w: cards[i].width, h: cards[i].height });
  }

  // ---- Transition arrows ----
  // (fromIdx, toIdx, label, isError)
  const transitions = [
    { fi: 0, ti: 1, label: "Tap company", err: false },
    { fi: 1, ti: 2, label: 'Tap "Gọi"', err: false },
    { fi: 2, ti: 3, label: "[Accept]", err: false },
    { fi: 2, ti: 1, label: "[No answer/Reject]", err: true },
    { fi: 3, ti: 4, label: "[Hang up]", err: false },
    { fi: 4, ti: 1, label: "[Close]", err: false },
    { fi: 4, ti: 5, label: "[View History]", err: false },
    { fi: 6, ti: 7, label: "[Accept]", err: false }
  ];

  for (const t of transitions) {
    const from = cardPos[t.fi];
    const to = cardPos[t.ti];
    const color = t.err ? "#CF222E" : "#0969DA";
    let x1, y1, x2, y2;

    if (Math.abs(from.y - to.y) < 5) {
      // Same row — horizontal
      if (from.x < to.x) {
        x1 = from.x + from.w; y1 = from.y + 30;
        x2 = to.x; y2 = to.y + 30;
      } else {
        x1 = from.x; y1 = from.y + 50;
        x2 = to.x + to.w; y2 = to.y + 50;
      }
    } else if (from.y < to.y) {
      x1 = from.x + from.w / 2; y1 = from.y + from.h;
      x2 = to.x + to.w / 2; y2 = to.y;
    } else {
      x1 = from.x + from.w / 2; y1 = from.y;
      x2 = to.x + to.w / 2; y2 = to.y + to.h;
    }

    mainFrame.appendChild(makeArrowVector({ x1, y1, x2, y2, color, dashed: t.err }));

    if (t.label) {
      const mx = (x1 + x2) / 2 - 35, my = (y1 + y2) / 2 - 14;
      mainFrame.appendChild(makeTextNode({ x: mx, y: my, w: 70, content: t.label, size: 9, color: t.err ? "#CF222E" : "#6E7781", align: "CENTER" }));
    }
  }

  // Resize main frame to fit
  const totalH = rowStartY[2] + rowH[2] + 60;
  mainFrame.resize(GRID_X + COL_W * 3 + 80, totalH);
  page.appendChild(mainFrame);
  return mainFrame;
}

// ============================================================
// MAIN — load fonts, then build both pages
// ============================================================
(async () => {
  try {
    await figma.loadFontAsync({ family: "Inter", style: "Regular" });
    await figma.loadFontAsync({ family: "Inter", style: "Bold" });
    await figma.loadFontAsync({ family: "Inter", style: "Medium" });

    const frame1 = buildPage1();
    const frame2 = buildPage2();

    // Switch to page 1 for final view
    figma.currentPage = frame1.parent;
    figma.viewport.scrollAndZoomIntoView([frame1]);

    figma.notify("Done! Created 2 pages: BA - Flow Tổng Quan + BA - Screen Flow", { timeout: 4000 });
  } catch (err) {
    figma.notify("Error: " + err.message, { error: true });
  } finally {
    figma.closePlugin();
  }
})();
