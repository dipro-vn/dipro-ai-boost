// =============================================================
// FIGMA PLUGIN SCRIPT — BA - Flow Tổng Quan
// Feature: In-App VoIP Call
// Page: "BA - Flow Tổng Quan"
//
// Cách chạy:
//   1. Mở Figma file: https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/
//   2. Vào menu Plugins > Development > Open console
//      HOẶC tạo plugin mới: Plugins > Development > New Plugin > Run once
//   3. Paste toàn bộ nội dung script này vào editor
//   4. Chạy script
// =============================================================

(async () => {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });
  await figma.loadFontAsync({ family: "Inter", style: "Bold" });
  await figma.loadFontAsync({ family: "Inter", style: "Medium" });

  // ---- Helper: tạo rectangle node ----
  function makeRect({ x, y, w, h, fill, strokeColor, radius = 0, name = "" }) {
    const rect = figma.createRectangle();
    rect.x = x;
    rect.y = y;
    rect.resize(w, h);
    rect.cornerRadius = radius;
    rect.fills = [{ type: "SOLID", color: hexToRgb(fill) }];
    rect.strokes = [{ type: "SOLID", color: hexToRgb(strokeColor) }];
    rect.strokeWeight = 1.5;
    rect.name = name;
    return rect;
  }

  // ---- Helper: tạo text node ----
  function makeText({ x, y, w, content, size, bold = false, color = "#24292F", align = "CENTER" }) {
    const t = figma.createText();
    t.fontName = { family: "Inter", style: bold ? "Bold" : "Regular" };
    t.fontSize = size;
    if (w) {
      t.textAutoResize = "HEIGHT";
      t.resize(w, 20); // set width first, height will auto-adjust
    }
    t.characters = content;
    t.x = x;
    t.y = y;
    t.textAlignHorizontal = align;
    t.fills = [{ type: "SOLID", color: hexToRgb(color) }];
    return t;
  }

  // ---- Helper: tạo arrow (line + arrowhead) ----
  function makeArrow({ x1, y1, x2, y2, color = "#0969DA", label = "", labelColor = "#6E7781" }) {
    const line = figma.createLine();
    // Figma createLine: vẽ theo rotation, ta dùng Vector thay thế
    // Dùng createVector để vẽ path mũi tên
    const arrow = figma.createVector();
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.sqrt(dx * dx + dy * dy);
    const headLen = 8;
    // Điểm arrowhead
    const ux = dx / len;
    const uy = dy / len;
    const lx = x2 - headLen * ux + headLen * 0.4 * uy;
    const ly = y2 - headLen * uy - headLen * 0.4 * ux;
    const rx = x2 - headLen * ux - headLen * 0.4 * uy;
    const ry = y2 - headLen * uy + headLen * 0.4 * ux;

    arrow.vectorPaths = [{
      windingRule: "NONZERO",
      data: `M ${x1} ${y1} L ${x2} ${y2} M ${x2} ${y2} L ${lx} ${ly} M ${x2} ${y2} L ${rx} ${ry}`
    }];
    arrow.strokes = [{ type: "SOLID", color: hexToRgb(color) }];
    arrow.strokeWeight = 1.5;
    arrow.fills = [];
    arrow.name = label ? `arrow-${label}` : "arrow";

    const nodes = [arrow];

    if (label) {
      const midX = (x1 + x2) / 2;
      const midY = (y1 + y2) / 2;
      const lbl = makeText({
        x: midX - 50,
        y: midY - 10,
        w: 100,
        content: label,
        size: 11,
        color: labelColor,
        align: "CENTER"
      });
      nodes.push(lbl);
    }

    return nodes;
  }

  // ---- Helper: hex to Figma RGB ----
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

  // ---- Helper: tạo "Screen box" (rectangle + label) ----
  function makeScreenBox({ x, y, w = 160, h = 60, label, sublabel = "", fill = "#E8F4FD", stroke = "#0969DA", bold = true }) {
    const nodes = [];
    const rect = makeRect({ x, y, w, h, fill, strokeColor: stroke, radius: 8, name: label });
    nodes.push(rect);

    const textY = sublabel ? y + 10 : y + (h - 16) / 2;
    const txt = makeText({ x: x + 8, y: textY, w: w - 16, content: label, size: 13, bold, color: "#24292F", align: "CENTER" });
    nodes.push(txt);

    if (sublabel) {
      const sub = makeText({ x: x + 8, y: textY + 18, w: w - 16, content: sublabel, size: 11, color: "#6E7781", align: "CENTER" });
      nodes.push(sub);
    }
    return nodes;
  }

  // ---- Helper: tạo "Decision box" (rhombus dùng vector) ----
  function makeDecisionBox({ x, y, w = 120, h = 48, label, fill = "#FFF9EB", stroke = "#F4860C" }) {
    const cx = x + w / 2;
    const cy = y + h / 2;
    const diamond = figma.createPolygon();
    // Figma createPolygon không hỗ trợ diamond trực tiếp → dùng Vector
    const dv = figma.createVector();
    dv.vectorPaths = [{
      windingRule: "NONZERO",
      data: `M ${cx} ${y} L ${x + w} ${cy} L ${cx} ${y + h} L ${x} ${cy} Z`
    }];
    dv.fills = [{ type: "SOLID", color: hexToRgb(fill) }];
    dv.strokes = [{ type: "SOLID", color: hexToRgb(stroke) }];
    dv.strokeWeight = 1.5;
    dv.name = label;

    const txt = makeText({
      x: x + 8,
      y: cy - 9,
      w: w - 16,
      content: label,
      size: 11,
      bold: false,
      color: "#424A53",
      align: "CENTER"
    });

    return [dv, txt];
  }

  // ---- Helper: tạo "External box" (ellipse) ----
  function makeExternalBox({ x, y, w = 160, h = 48, label, fill = "#EDFDF0", stroke = "#1A7F37" }) {
    const ellipse = figma.createEllipse();
    ellipse.x = x;
    ellipse.y = y;
    ellipse.resize(w, h);
    ellipse.fills = [{ type: "SOLID", color: hexToRgb(fill) }];
    ellipse.strokes = [{ type: "SOLID", color: hexToRgb(stroke) }];
    ellipse.strokeWeight = 1.5;
    ellipse.name = label;

    const txt = makeText({
      x: x + 8,
      y: y + (h - 14) / 2,
      w: w - 16,
      content: label,
      size: 12,
      color: "#24292F",
      align: "CENTER"
    });

    return [ellipse, txt];
  }

  // ============================================================
  // LAYOUT PLAN (x, y coordinates — happy path left-to-right)
  // ============================================================
  //
  // Row 1 (y=80):  Happy path — Dipro Admin side
  //   [START] → [Company List] → [Company Detail] → [Outgoing Call] → <Decision: Response?> → [In-Call DA] → <Decision: End?> → [Call Ended Summary] → [Call History]
  //
  // Row 2 (y=280): Company Admin side
  //                                               <Push/Overlay> → [Incoming Call CA] → <Accept/Decline?> → [In-Call CA]
  //
  // Error branches (y=400+): xuống dưới từ Decision nodes

  // Spacing
  const COL_GAP = 40;     // gap between boxes
  const BOX_W = 150;
  const BOX_H = 60;
  const DEC_W = 140;
  const DEC_H = 60;
  const EXT_W = 160;
  const EXT_H = 50;
  const ROW1_Y = 80;
  const ROW2_Y = 300;
  const ERR_Y = 480;

  // X positions — row 1 happy path
  const X_START = 40;
  const X_COMPANY_LIST = X_START + 100 + COL_GAP;       // 220
  const X_COMPANY_DETAIL = X_COMPANY_LIST + BOX_W + COL_GAP;  // 410
  const X_OUTGOING = X_COMPANY_DETAIL + BOX_W + COL_GAP;      // 600
  const X_DEC_RESPONSE = X_OUTGOING + BOX_W + COL_GAP;        // 790
  const X_INCALL_DA = X_DEC_RESPONSE + DEC_W + COL_GAP;       // 970
  const X_DEC_END = X_INCALL_DA + BOX_W + COL_GAP;            // 1160
  const X_ENDED = X_DEC_END + DEC_W + COL_GAP;                // 1340
  const X_HISTORY = X_ENDED + BOX_W + COL_GAP;                // 1530

  // X positions — row 2 (Company Admin, aligned under decision nodes)
  const X_PUSH = X_DEC_RESPONSE + 10;
  const X_INCOMING = X_PUSH + EXT_W + COL_GAP;
  const X_DEC_ACCEPT = X_INCOMING + BOX_W + COL_GAP;
  const X_INCALL_CA = X_DEC_ACCEPT + DEC_W + COL_GAP;

  // ---- Tạo page mới ----
  const page = figma.createPage();
  page.name = "BA - Flow Tổng Quan";
  figma.currentPage = page;

  const allNodes = [];

  // ============================================================
  // Section title
  // ============================================================
  const title = makeText({
    x: X_START, y: 20, w: 900,
    content: "Flow Tổng Quan — In-App VoIP Call",
    size: 20, bold: true, color: "#24292F", align: "LEFT"
  });
  allNodes.push(title);

  const subtitle = makeText({
    x: X_START, y: 46, w: 600,
    content: "Happy path: trái → phải  |  Error branches: xuống dưới  |  Company Admin side: row 2",
    size: 11, color: "#6E7781", align: "LEFT"
  });
  allNodes.push(subtitle);

  // ============================================================
  // ROW LABELS
  // ============================================================
  const labelDA = makeText({ x: X_START - 10, y: ROW1_Y + 10, w: 90, content: "Dipro Admin", size: 11, bold: true, color: "#0969DA", align: "LEFT" });
  allNodes.push(labelDA);

  const labelCA = makeText({ x: X_START - 10, y: ROW2_Y + 10, w: 90, content: "Company Admin", size: 11, bold: true, color: "#1A7F37", align: "LEFT" });
  allNodes.push(labelCA);

  // ============================================================
  // SHAPES — ROW 1 (Happy Path — Dipro Admin)
  // ============================================================

  // [Start] oval
  allNodes.push(...makeExternalBox({
    x: X_START + 10, y: ROW1_Y + 5,
    w: 80, h: 50,
    label: "Mở App",
    fill: "#F6F8FA", stroke: "#8C959F"
  }));

  // Arrow: Start → Company List
  allNodes.push(...makeArrow({ x1: X_START + 90, y1: ROW1_Y + 30, x2: X_COMPANY_LIST, y2: ROW1_Y + 30 }));

  // [DA_VOIP_001] Company List
  allNodes.push(...makeScreenBox({ x: X_COMPANY_LIST, y: ROW1_Y, label: "DA_VOIP_001", sublabel: "Company List" }));

  // Arrow: Company List → Company Detail
  allNodes.push(...makeArrow({ x1: X_COMPANY_LIST + BOX_W, y1: ROW1_Y + 30, x2: X_COMPANY_DETAIL, y2: ROW1_Y + 30, label: "Tap Company" }));

  // [DA_VOIP_002] Company Detail
  allNodes.push(...makeScreenBox({ x: X_COMPANY_DETAIL, y: ROW1_Y, label: "DA_VOIP_002", sublabel: "Company Detail" }));

  // Arrow: Company Detail → Outgoing Call
  allNodes.push(...makeArrow({ x1: X_COMPANY_DETAIL + BOX_W, y1: ROW1_Y + 30, x2: X_OUTGOING, y2: ROW1_Y + 30, label: "Tap \"Gọi\"" }));

  // [DA_VOIP_003] Outgoing Call
  allNodes.push(...makeScreenBox({ x: X_OUTGOING, y: ROW1_Y, label: "DA_VOIP_003", sublabel: "Outgoing Call" }));

  // Arrow: Outgoing Call → Decision
  allNodes.push(...makeArrow({ x1: X_OUTGOING + BOX_W, y1: ROW1_Y + 30, x2: X_DEC_RESPONSE, y2: ROW1_Y + 30 }));

  // <Decision: Response?>
  allNodes.push(...makeDecisionBox({ x: X_DEC_RESPONSE, y: ROW1_Y + 0, w: DEC_W, h: DEC_H, label: "Response?" }));

  // Arrow: Decision → In-Call DA (Accept)
  allNodes.push(...makeArrow({
    x1: X_DEC_RESPONSE + DEC_W, y1: ROW1_Y + 30,
    x2: X_INCALL_DA, y2: ROW1_Y + 30,
    label: "Accept", labelColor: "#0969DA"
  }));

  // [DA_VOIP_004] In-Call DA
  allNodes.push(...makeScreenBox({ x: X_INCALL_DA, y: ROW1_Y, label: "DA_VOIP_004", sublabel: "In-Call (Caller)" }));

  // Arrow: In-Call DA → Decision End
  allNodes.push(...makeArrow({ x1: X_INCALL_DA + BOX_W, y1: ROW1_Y + 30, x2: X_DEC_END, y2: ROW1_Y + 30 }));

  // <Decision: End?>
  allNodes.push(...makeDecisionBox({ x: X_DEC_END, y: ROW1_Y + 0, w: DEC_W, h: DEC_H, label: "End?" }));

  // Arrow: Decision End → Call Ended Summary (Hang up)
  allNodes.push(...makeArrow({
    x1: X_DEC_END + DEC_W, y1: ROW1_Y + 30,
    x2: X_ENDED, y2: ROW1_Y + 30,
    label: "Hang up", labelColor: "#0969DA"
  }));

  // [DA_VOIP_005] Call Ended Summary
  allNodes.push(...makeScreenBox({ x: X_ENDED, y: ROW1_Y, label: "DA_VOIP_005", sublabel: "Call Ended" }));

  // Arrow: Ended → History
  allNodes.push(...makeArrow({ x1: X_ENDED + BOX_W, y1: ROW1_Y + 30, x2: X_HISTORY, y2: ROW1_Y + 30, label: "View History" }));

  // [DA_VOIP_006] Call History
  allNodes.push(...makeScreenBox({ x: X_HISTORY, y: ROW1_Y, label: "DA_VOIP_006", sublabel: "Call History" }));

  // ============================================================
  // SHAPES — ROW 2 (Company Admin side)
  // ============================================================

  // Arrow: Decision Response → Push/Overlay (down to row 2)
  allNodes.push(...makeArrow({
    x1: X_DEC_RESPONSE + DEC_W / 2, y1: ROW1_Y + DEC_H,
    x2: X_DEC_RESPONSE + DEC_W / 2, y2: ROW2_Y,
    label: "Ringing", labelColor: "#1A7F37"
  }));

  // [Push / Overlay] — External
  allNodes.push(...makeExternalBox({
    x: X_PUSH, y: ROW2_Y,
    w: EXT_W, h: EXT_H,
    label: "Push / Overlay",
    fill: "#EDFDF0", stroke: "#1A7F37"
  }));

  // Arrow: Push → Incoming Call
  allNodes.push(...makeArrow({
    x1: X_PUSH + EXT_W, y1: ROW2_Y + EXT_H / 2,
    x2: X_INCOMING, y2: ROW2_Y + BOX_H / 2,
    label: "Company Admin sees"
  }));

  // [CA_VOIP_001] Incoming Call
  allNodes.push(...makeScreenBox({
    x: X_INCOMING, y: ROW2_Y,
    label: "CA_VOIP_001", sublabel: "Incoming Call",
    fill: "#EDFDF0", stroke: "#1A7F37"
  }));

  // Arrow: Incoming → Decision Accept
  allNodes.push(...makeArrow({
    x1: X_INCOMING + BOX_W, y1: ROW2_Y + BOX_H / 2,
    x2: X_DEC_ACCEPT, y2: ROW2_Y + DEC_H / 2
  }));

  // <Decision: Accept?>
  allNodes.push(...makeDecisionBox({
    x: X_DEC_ACCEPT, y: ROW2_Y,
    w: DEC_W, h: DEC_H,
    label: "Accept?"
  }));

  // Arrow: Accept → In-Call CA
  allNodes.push(...makeArrow({
    x1: X_DEC_ACCEPT + DEC_W, y1: ROW2_Y + DEC_H / 2,
    x2: X_INCALL_CA, y2: ROW2_Y + BOX_H / 2,
    label: "Chấp nhận", labelColor: "#1A7F37"
  }));

  // [CA_VOIP_002] In-Call CA
  allNodes.push(...makeScreenBox({
    x: X_INCALL_CA, y: ROW2_Y,
    label: "CA_VOIP_002", sublabel: "In-Call (Receiver)",
    fill: "#EDFDF0", stroke: "#1A7F37"
  }));

  // Vertical connection: In-Call CA ↔ In-Call DA (same call)
  allNodes.push(...makeArrow({
    x1: X_INCALL_CA + BOX_W / 2, y1: ROW2_Y,
    x2: X_INCALL_DA + BOX_W / 2, y2: ROW1_Y + BOX_H,
    color: "#8250DF", label: "Same call"
  }));

  // ============================================================
  // ERROR BRANCHES (y = ERR_Y)
  // ============================================================

  // --- Error 1: Timeout / Reject (from DA_VOIP_003 / Decision Response) ---
  const X_ERR1 = X_DEC_RESPONSE - 20;

  // Arrow: Decision Response down to error branch
  allNodes.push(...makeArrow({
    x1: X_DEC_RESPONSE + DEC_W / 2, y1: ROW1_Y + DEC_H,
    x2: X_ERR1 + 60, y2: ERR_Y,
    color: "#CF222E", label: "Timeout 30s / Reject"
  }));

  allNodes.push(...makeExternalBox({
    x: X_ERR1, y: ERR_Y,
    w: 180, h: 44,
    label: "Toast: \"Không có phản hồi\"\n/ \"Bị từ chối\"",
    fill: "#FFF6F5", stroke: "#CF222E"
  }));

  allNodes.push(...makeArrow({
    x1: X_ERR1 + 180, y1: ERR_Y + 22,
    x2: X_COMPANY_DETAIL + BOX_W / 2, y2: ROW1_Y + BOX_H,
    color: "#CF222E", label: "Back to Detail"
  }));

  // --- Error 2: Network lost in call (from DA_VOIP_004 / Decision End) ---
  const X_ERR2 = X_DEC_END - 20;

  allNodes.push(...makeArrow({
    x1: X_DEC_END + DEC_W / 2, y1: ROW1_Y + DEC_H,
    x2: X_ERR2 + 70, y2: ERR_Y,
    color: "#CF222E", label: "Network lost"
  }));

  allNodes.push(...makeExternalBox({
    x: X_ERR2, y: ERR_Y,
    w: 180, h: 44,
    label: "Toast: \"Kết nối bị gián đoạn\"",
    fill: "#FFF6F5", stroke: "#CF222E"
  }));

  allNodes.push(...makeArrow({
    x1: X_ERR2 + 180, y1: ERR_Y + 22,
    x2: X_ENDED + BOX_W / 2, y2: ROW1_Y + BOX_H,
    color: "#CF222E", label: "→ Call Ended"
  }));

  // --- Error 3: CA Decline (from Decision Accept / CA side) ---
  const X_ERR3 = X_DEC_ACCEPT - 20;
  const ERR3_Y = ROW2_Y + 120;

  allNodes.push(...makeArrow({
    x1: X_DEC_ACCEPT + DEC_W / 2, y1: ROW2_Y + DEC_H,
    x2: X_ERR3 + 70, y2: ERR3_Y,
    color: "#CF222E", label: "Từ chối"
  }));

  allNodes.push(...makeExternalBox({
    x: X_ERR3, y: ERR3_Y,
    w: 140, h: 44,
    label: "Dismiss overlay\n+ Toast (Caller)",
    fill: "#FFF6F5", stroke: "#CF222E"
  }));

  // --- Error 4: Mic permission denied ----
  const X_ERR4 = X_OUTGOING - 20;
  const ERR4_Y = ERR_Y;

  allNodes.push(...makeArrow({
    x1: X_OUTGOING + BOX_W / 2, y1: ROW1_Y + BOX_H,
    x2: X_ERR4 + 60, y2: ERR4_Y,
    color: "#CF222E", label: "Mic denied"
  }));

  allNodes.push(...makeExternalBox({
    x: X_ERR4, y: ERR4_Y,
    w: 160, h: 44,
    label: "Modal: Cần quyền mic\n+ \"Mở Cài đặt\"",
    fill: "#FFF6F5", stroke: "#CF222E"
  }));

  // ============================================================
  // LEGEND
  // ============================================================
  const LEGEND_X = X_START;
  const LEGEND_Y = ERR_Y + 100;

  const legendTitle = makeText({ x: LEGEND_X, y: LEGEND_Y, w: 500, content: "LEGEND", size: 12, bold: true, color: "#24292F", align: "LEFT" });
  allNodes.push(legendTitle);

  // Screen box legend
  allNodes.push(...makeScreenBox({ x: LEGEND_X, y: LEGEND_Y + 20, w: 120, h: 36, label: "Screen / State" }));
  allNodes.push(makeText({ x: LEGEND_X + 130, y: LEGEND_Y + 30, w: 200, content: "Màn hình chính (DA = xanh, CA = xanh lá)", size: 11, color: "#6E7781", align: "LEFT" }));

  // Decision box legend
  allNodes.push(...makeDecisionBox({ x: LEGEND_X + 360, y: LEGEND_Y + 18, w: 120, h: 44, label: "Decision" }));
  allNodes.push(makeText({ x: LEGEND_X + 490, y: LEGEND_Y + 30, w: 200, content: "Điều kiện rẽ nhánh (cam)", size: 11, color: "#6E7781", align: "LEFT" }));

  // External ellipse legend
  allNodes.push(...makeExternalBox({ x: LEGEND_X, y: LEGEND_Y + 70, w: 120, h: 36, label: "External / Push" }));
  allNodes.push(makeText({ x: LEGEND_X + 130, y: LEGEND_Y + 80, w: 300, content: "Sự kiện bên ngoài: push notification, toast, system event", size: 11, color: "#6E7781", align: "LEFT" }));

  // Error arrow legend
  allNodes.push(...makeArrow({ x1: LEGEND_X + 360, y1: LEGEND_Y + 90, x2: LEGEND_X + 480, y2: LEGEND_Y + 90, color: "#CF222E", label: "Error path" }));
  allNodes.push(makeText({ x: LEGEND_X + 490, y: LEGEND_Y + 82, w: 200, content: "Luồng lỗi / edge case (đỏ)", size: 11, color: "#6E7781", align: "LEFT" }));

  // ============================================================
  // GROUP tất cả vào 1 frame
  // ============================================================
  const FRAME_W = X_HISTORY + BOX_W + 80;
  const FRAME_H = LEGEND_Y + 140;

  const frame = figma.createFrame();
  frame.name = "BA - Flow Tổng Quan";
  frame.resize(FRAME_W, FRAME_H);
  frame.fills = [{ type: "SOLID", color: hexToRgb("#FFFFFF") }];

  for (const node of allNodes) {
    frame.appendChild(node);
  }

  page.appendChild(frame);
  figma.viewport.scrollAndZoomIntoView([frame]);

  figma.notify("BA - Flow Tổng Quan created successfully!", { timeout: 3000 });
  figma.closePlugin();
})();
