// =============================================================
// FIGMA PLUGIN SCRIPT — BA - Screen Flow
// Feature: In-App VoIP Call
// Page: "BA - Screen Flow"
//
// Cách chạy:
//   1. Mở Figma file: https://www.figma.com/design/VKAAOyoSPvgoB3H2qdeeV3/
//   2. Vào menu Plugins > Development > Open console
//      HOẶC tạo plugin mới: Plugins > Development > New Plugin > Run once
//   3. Paste toàn bộ nội dung script này vào editor
//   4. Chạy script
//
// Output: 8 screen cards (3 columns) + arrows theo Transition To
// =============================================================

(async () => {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });
  await figma.loadFontAsync({ family: "Inter", style: "Bold" });
  await figma.loadFontAsync({ family: "Inter", style: "Medium" });

  // ---- Helpers ----
  function hexToRgb(hex) {
    hex = hex.replace("#", "");
    if (hex.length === 3) hex = hex.split("").map(c => c + c).join("");
    const n = parseInt(hex, 16);
    return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 };
  }

  async function makeTextNode({ x, y, w, content, size, style = "Regular", color = "#24292F", align = "LEFT", lineH }) {
    const t = figma.createText();
    t.fontName = { family: "Inter", style };
    t.characters = content;
    t.fontSize = size;
    t.x = x;
    t.y = y;
    t.textAlignHorizontal = align;
    t.fills = [{ type: "SOLID", color: hexToRgb(color) }];
    t.textAutoResize = "HEIGHT";
    if (w) t.resize(w, t.height);
    return t;
  }

  function makeRect({ x, y, w, h, fill, strokeColor, radius = 0, name = "" }) {
    const rect = figma.createRectangle();
    rect.x = x; rect.y = y;
    rect.resize(w, h);
    rect.cornerRadius = radius;
    rect.fills = [{ type: "SOLID", color: hexToRgb(fill) }];
    if (strokeColor) {
      rect.strokes = [{ type: "SOLID", color: hexToRgb(strokeColor) }];
      rect.strokeWeight = 1;
    }
    rect.name = name;
    return rect;
  }

  function makeLine({ x1, y1, x2, y2, color = "#0969DA", label = "", dashed = false }) {
    const arrow = figma.createVector();
    const dx = x2 - x1; const dy = y2 - y1;
    const len = Math.max(Math.sqrt(dx * dx + dy * dy), 0.001);
    const ux = dx / len; const uy = dy / len;
    const headLen = 8;
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
    if (dashed) arrow.dashPattern = [4, 3];
    arrow.name = label || "arrow";
    return arrow;
  }

  // ============================================================
  // CARD BUILDER
  // Screen card structure:
  //   ┌──────────────────────────────────────────┐  h=auto
  //   │ [SCREEN_CODE] — Screen Name   (header)   │  row h=40
  //   │ Actor: X  |  Type: Y         (meta)      │  row h=24
  //   ├──────────────────────────────────────────┤
  //   │ COMPONENTS:                               │  row h=20
  //   │ • item 1                                  │
  //   │ • item 2                                  │
  //   ├──────────────────────────────────────────┤
  //   │ ⚠ NON-HAPPY:                             │
  //   │ description                               │
  //   └──────────────────────────────────────────┘
  // ============================================================

  const CARD_W = 280;
  const CARD_PAD = 12;
  const CARD_RADIUS = 8;
  const DIVIDER_COLOR = "#EAEEF2";
  const CARD_BG = "#FFFFFF";
  const CARD_STROKE = "#D0D7DE";

  async function buildCard({ x, y, screenCode, screenName, actor, type, components, nonHappy, actorColor = "#0969DA" }) {
    const nodes = [];
    let curY = 0;

    // Header background
    const headerBg = makeRect({ x: 0, y: 0, w: CARD_W, h: 40, fill: "#F6F8FA", radius: 0, name: "header-bg" });
    nodes.push(headerBg);

    // Screen code + name
    const titleNode = await makeTextNode({
      x: CARD_PAD, y: 10, w: CARD_W - CARD_PAD * 2,
      content: `${screenCode} — ${screenName}`,
      size: 13, style: "Bold", color: "#24292F"
    });
    nodes.push(titleNode);
    curY = 40;

    // Meta row: Actor + Type
    const metaBg = makeRect({ x: 0, y: curY, w: CARD_W, h: 24, fill: "#FFFFFF", radius: 0 });
    nodes.push(metaBg);
    const metaNode = await makeTextNode({
      x: CARD_PAD, y: curY + 5, w: CARD_W - CARD_PAD * 2,
      content: `Actor: ${actor}   |   Type: ${type}`,
      size: 11, style: "Regular", color: "#6E7781"
    });
    nodes.push(metaNode);
    curY += 24;

    // Divider
    const div1 = makeRect({ x: 0, y: curY, w: CARD_W, h: 1, fill: DIVIDER_COLOR, radius: 0 });
    nodes.push(div1);
    curY += 1;

    // COMPONENTS section
    const compLabel = await makeTextNode({
      x: CARD_PAD, y: curY + 6, w: CARD_W - CARD_PAD * 2,
      content: "COMPONENTS:",
      size: 11, style: "Bold", color: "#424A53"
    });
    nodes.push(compLabel);
    curY += 24;

    for (const comp of components) {
      const compText = await makeTextNode({
        x: CARD_PAD, y: curY, w: CARD_W - CARD_PAD * 2,
        content: `• ${comp}`,
        size: 12, style: "Regular", color: "#424A53"
      });
      nodes.push(compText);
      curY += compText.height + 2;
    }
    curY += 4;

    // Divider
    const div2 = makeRect({ x: 0, y: curY, w: CARD_W, h: 1, fill: DIVIDER_COLOR, radius: 0 });
    nodes.push(div2);
    curY += 1;

    // NON-HAPPY section
    const nhLabel = await makeTextNode({
      x: CARD_PAD, y: curY + 6, w: CARD_W - CARD_PAD * 2,
      content: "NON-HAPPY:",
      size: 11, style: "Bold", color: "#CF222E"
    });
    nodes.push(nhLabel);
    curY += 24;

    for (const nh of nonHappy) {
      const nhText = await makeTextNode({
        x: CARD_PAD, y: curY, w: CARD_W - CARD_PAD * 2,
        content: `• ${nh}`,
        size: 11, style: "Regular", color: "#CF222E"
      });
      nodes.push(nhText);
      curY += nhText.height + 2;
    }
    curY += CARD_PAD;

    // Card background + border (underneath)
    const cardBg = makeRect({ x: 0, y: 0, w: CARD_W, h: curY, fill: CARD_BG, strokeColor: CARD_STROKE, radius: CARD_RADIUS, name: screenCode });

    // Group all into a frame
    const cardFrame = figma.createFrame();
    cardFrame.name = screenCode;
    cardFrame.resize(CARD_W, curY);
    cardFrame.cornerRadius = CARD_RADIUS;
    cardFrame.fills = [{ type: "SOLID", color: hexToRgb(CARD_BG) }];
    cardFrame.strokes = [{ type: "SOLID", color: hexToRgb(CARD_STROKE) }];
    cardFrame.strokeWeight = 1;
    cardFrame.clipsContent = true;

    for (const n of nodes) {
      cardFrame.appendChild(n);
    }

    cardFrame.x = x;
    cardFrame.y = y;

    return cardFrame;
  }

  // ============================================================
  // SCREEN DATA — 8 screens
  // ============================================================
  const screens = [
    {
      screenCode: "DA_VOIP_001",
      screenName: "Company List",
      actor: "Dipro Admin",
      type: "List",
      actorColor: "#0969DA",
      components: [
        "Search bar (\"Tìm công ty...\")",
        "List item: Avatar + Tên + Online dot (xanh/xám)",
        "Sub-text: Last call timestamp",
        "Interactions: Pull-to-refresh, Infinite scroll",
        "Skeleton loader (khi loading)",
        "FAB bottom-right: icon Lịch sử"
      ],
      nonHappy: [
        "Empty → \"Chưa có công ty nào được assign\"",
        "Load error → Banner + Retry button",
        "Mất mạng → Sticky banner \"Không có kết nối\""
      ]
    },
    {
      screenCode: "DA_VOIP_002",
      screenName: "Company Detail",
      actor: "Dipro Admin",
      type: "Detail",
      actorColor: "#0969DA",
      components: [
        "Header: Avatar large + Tên + Status badge",
        "Status badge: Online / Offline / Busy",
        "Info rows: Tên, địa chỉ, đơn hàng active",
        "Recent calls: 3 cuộc gần nhất (thu gọn)",
        "Link \"Xem tất cả\" → DA_VOIP_006",
        "Sticky bottom: Button \"Gọi ngay\" (primary)"
      ],
      nonHappy: [
        "Offline → Button disabled + tooltip",
        "Busy → Button disabled + tooltip"
      ]
    },
    {
      screenCode: "DA_VOIP_003",
      screenName: "Outgoing Call",
      actor: "Dipro Admin",
      type: "Modal",
      actorColor: "#0969DA",
      components: [
        "Full-screen overlay (dark bg)",
        "Avatar large + pulse animation (ringing)",
        "Text: Tên company",
        "Text: \"Đang gọi...\" (animated dots)",
        "Icon btn: Speaker toggle",
        "Icon btn: Mute toggle",
        "Button đỏ: \"Kết thúc\" (cancel)"
      ],
      nonHappy: [
        "Timeout 30s → Auto dismiss + toast",
        "Rejected → Auto dismiss + toast",
        "Network lost → Auto dismiss + toast",
        "Mic denied → Modal + \"Mở Cài đặt\""
      ]
    },
    {
      screenCode: "DA_VOIP_004",
      screenName: "In-Call (Caller)",
      actor: "Dipro Admin",
      type: "Modal",
      actorColor: "#0969DA",
      components: [
        "Full-screen overlay",
        "Call timer top: \"00:00\" (đếm lên)",
        "Avatar large + tên company (center)",
        "Icon btn: Mute (highlight khi active)",
        "Icon btn: Speaker (highlight khi active)",
        "Button đỏ: \"Kết thúc\"",
        "Waveform animation khi nói"
      ],
      nonHappy: [
        "Network lost → Toast + auto end → DA_VOIP_005",
        "Company Admin hang up → Toast → DA_VOIP_005"
      ]
    },
    {
      screenCode: "DA_VOIP_005",
      screenName: "Call Ended Summary",
      actor: "Dipro Admin",
      type: "Modal",
      actorColor: "#0969DA",
      components: [
        "Bottom sheet (slide-up animation)",
        "Status icon: xanh (completed) / đỏ (error)",
        "Text: Tên company",
        "Text: Thời lượng (vd \"2 phút 34 giây\")",
        "Text: Timestamp (vd \"14:32 — 07/09/2026\")",
        "Status badge: Completed/Missed/Declined/Disconnected",
        "Button primary: \"Gọi lại\"",
        "Button outline: \"Đóng\""
      ],
      nonHappy: [
        "Missed → Icon đỏ + badge \"Không có phản hồi\"",
        "Declined → Icon đỏ + badge \"Bị từ chối\"",
        "Disconnected → Icon đỏ + badge \"Bị gián đoạn\""
      ]
    },
    {
      screenCode: "DA_VOIP_006",
      screenName: "Call History",
      actor: "Dipro Admin",
      type: "List",
      actorColor: "#0969DA",
      components: [
        "Filter tabs: Tất cả / Missed / Completed",
        "List item: Avatar + Tên + Status icon + Thời lượng + Timestamp",
        "Date separator: \"Hôm nay\" / \"Hôm qua\" / \"DD/MM/YYYY\"",
        "Skeleton loader",
        "Swipe-right → shortcut \"Gọi lại\""
      ],
      nonHappy: [
        "Không có lịch sử → Empty state \"Chưa có cuộc gọi\"",
        "Filter Missed rỗng → Empty state",
        "Load error → Error + Retry"
      ]
    },
    {
      screenCode: "CA_VOIP_001",
      screenName: "Incoming Call",
      actor: "Company Admin",
      type: "Modal",
      actorColor: "#1A7F37",
      components: [
        "Full-screen overlay (native-style)",
        "Avatar large \"Dipro Admin\" + tên + pulse",
        "Text: \"Đang gọi đến...\"",
        "Button xanh: \"Chấp nhận\"",
        "Button đỏ: \"Từ chối\"",
        "Ringing sound + vibration"
      ],
      nonHappy: [
        "App killed → Push notification với Action btn",
        "Caller cancel → Auto dismiss overlay",
        "Mic denied → Modal + \"Mở Cài đặt\""
      ]
    },
    {
      screenCode: "CA_VOIP_002",
      screenName: "In-Call (Receiver)",
      actor: "Company Admin",
      type: "Modal",
      actorColor: "#1A7F37",
      components: [
        "Full-screen overlay",
        "Call timer top: \"00:00\" (đếm lên)",
        "Avatar large \"Dipro Admin\" (center)",
        "Icon btn: Mute toggle",
        "Icon btn: Speaker toggle",
        "Button đỏ: \"Kết thúc\" → dismiss",
        "Waveform animation khi nói"
      ],
      nonHappy: [
        "Network lost → Toast + auto end",
        "Caller hang up → Toast \"Cuộc gọi đã kết thúc\""
      ]
    }
  ];

  // ============================================================
  // TRANSITION arrows definition
  // (from screenCode → toCode, label, isError)
  // ============================================================
  const transitions = [
    { from: "DA_VOIP_001", to: "DA_VOIP_002", label: "Tap company", error: false },
    { from: "DA_VOIP_002", to: "DA_VOIP_003", label: "Tap \"Gọi\"", error: false },
    { from: "DA_VOIP_003", to: "DA_VOIP_004", label: "[Accept]", error: false },
    { from: "DA_VOIP_003", to: "DA_VOIP_002", label: "[No answer/Reject]", error: true },
    { from: "DA_VOIP_004", to: "DA_VOIP_005", label: "[Hang up]", error: false },
    { from: "DA_VOIP_005", to: "DA_VOIP_002", label: "[Close]", error: false },
    { from: "DA_VOIP_005", to: "DA_VOIP_006", label: "[View History]", error: false },
    { from: "CA_VOIP_001", to: "CA_VOIP_002", label: "[Accept]", error: false },
  ];

  // ============================================================
  // GRID LAYOUT — 3 columns
  // Col 0: DA_VOIP_001, DA_VOIP_004, CA_VOIP_001
  // Col 1: DA_VOIP_002, DA_VOIP_005, CA_VOIP_002
  // Col 2: DA_VOIP_003, DA_VOIP_006
  // ============================================================
  const COL_W = CARD_W + 60;   // gap between columns
  const ROW_GAP = 40;
  const GRID_X = 40;
  const GRID_Y = 80;

  // Assign grid positions
  const gridLayout = [
    // [col, row] for each screen in order
    { code: "DA_VOIP_001", col: 0, row: 0 },
    { code: "DA_VOIP_002", col: 1, row: 0 },
    { code: "DA_VOIP_003", col: 2, row: 0 },
    { code: "DA_VOIP_004", col: 0, row: 1 },
    { code: "DA_VOIP_005", col: 1, row: 1 },
    { code: "DA_VOIP_006", col: 2, row: 1 },
    { code: "CA_VOIP_001", col: 0, row: 2 },
    { code: "CA_VOIP_002", col: 1, row: 2 },
  ];

  // ---- Tạo page mới ----
  const page = figma.createPage();
  page.name = "BA - Screen Flow";
  figma.currentPage = page;

  // ---- Main frame ----
  const MAIN_W = GRID_X + COL_W * 3 + 100;
  const MAIN_H = GRID_Y + 1600; // sẽ resize sau

  const mainFrame = figma.createFrame();
  mainFrame.name = "BA - Screen Flow";
  mainFrame.resize(MAIN_W, MAIN_H);
  mainFrame.fills = [{ type: "SOLID", color: hexToRgb("#F6F8FA") }];

  // ---- Title ----
  const titleNode = await makeTextNode({
    x: GRID_X, y: 20, w: 800,
    content: "Screen Flow — In-App VoIP Call (8 screens)",
    size: 20, style: "Bold", color: "#24292F"
  });
  mainFrame.appendChild(titleNode);

  const subtitleNode = await makeTextNode({
    x: GRID_X, y: 46, w: 700,
    content: "Xanh dương = Dipro Admin  |  Xanh lá = Company Admin  |  Mũi tên xanh = happy path  |  Đỏ = error path",
    size: 11, style: "Regular", color: "#6E7781"
  });
  mainFrame.appendChild(subtitleNode);

  // ---- Section dividers ----
  const sectionDA = await makeTextNode({
    x: GRID_X, y: GRID_Y - 24, w: 400,
    content: "DIPRO ADMIN (DA_VOIP_001 → DA_VOIP_006)",
    size: 12, style: "Bold", color: "#0969DA"
  });
  mainFrame.appendChild(sectionDA);

  // ---- Build and place cards ----
  const cardMap = {}; // screenCode → { frame, x, y, w, h }
  const ROW_HEIGHT = [0, 0, 0]; // track max height per row (to space rows)

  // First pass: build cards to know heights
  const builtCards = {};
  for (const screen of screens) {
    const card = await buildCard({
      x: 0, y: 0, // will reposition
      ...screen
    });
    builtCards[screen.screenCode] = card;
  }

  // Compute row heights
  const ROW_HEIGHTS = [0, 0, 0];
  for (const pos of gridLayout) {
    const card = builtCards[pos.code];
    ROW_HEIGHTS[pos.row] = Math.max(ROW_HEIGHTS[pos.row], card.height);
  }

  // Row Y start positions
  const ROW_Y = [
    GRID_Y,
    GRID_Y + ROW_HEIGHTS[0] + ROW_GAP,
    GRID_Y + ROW_HEIGHTS[0] + ROW_GAP + ROW_HEIGHTS[1] + ROW_GAP
  ];

  // Place cards
  for (const pos of gridLayout) {
    const card = builtCards[pos.code];
    const cx = GRID_X + pos.col * COL_W;
    const cy = ROW_Y[pos.row];
    card.x = cx;
    card.y = cy;
    mainFrame.appendChild(card);
    cardMap[pos.code] = { frame: card, x: cx, y: cy, w: card.width, h: card.height };
  }

  // Company Admin section label
  const sectionCA = await makeTextNode({
    x: GRID_X, y: ROW_Y[2] - 24, w: 400,
    content: "COMPANY ADMIN (CA_VOIP_001 → CA_VOIP_002)",
    size: 12, style: "Bold", color: "#1A7F37"
  });
  mainFrame.appendChild(sectionCA);

  // ---- Draw transition arrows ----
  for (const t of transitions) {
    const fromCard = cardMap[t.from];
    const toCard = cardMap[t.to];
    if (!fromCard || !toCard) continue;

    const color = t.error ? "#CF222E" : "#0969DA";

    // Arrow from right edge of from card to left edge of to card (same row)
    // or bottom to top (different row)
    let x1, y1, x2, y2;

    if (fromCard.y === toCard.y) {
      // Same row → horizontal arrow
      x1 = fromCard.x + fromCard.w;
      y1 = fromCard.y + 30;
      x2 = toCard.x;
      y2 = toCard.y + 30;
    } else if (fromCard.y < toCard.y) {
      // From is above to → vertical or diagonal
      x1 = fromCard.x + fromCard.w / 2;
      y1 = fromCard.y + fromCard.h;
      x2 = toCard.x + toCard.w / 2;
      y2 = toCard.y;
    } else {
      // From is below to → back arrow (error path going up/left)
      x1 = fromCard.x;
      y1 = fromCard.y + fromCard.h / 2;
      x2 = toCard.x + toCard.w;
      y2 = toCard.y + toCard.h / 2;
    }

    const arrow = makeLine({ x1, y1, x2, y2, color, label: t.label, dashed: t.error });
    mainFrame.appendChild(arrow);

    // Arrow label
    if (t.label) {
      const midX = (x1 + x2) / 2 - 35;
      const midY = (y1 + y2) / 2 - 12;
      const lbl = await makeTextNode({
        x: midX, y: midY, w: 80,
        content: t.label,
        size: 10, color: t.error ? "#CF222E" : "#6E7781", align: "CENTER"
      });
      mainFrame.appendChild(lbl);
    }
  }

  // ---- Resize main frame to fit content ----
  const totalH = ROW_Y[2] + ROW_HEIGHTS[2] + 60;
  mainFrame.resize(MAIN_W, totalH);

  page.appendChild(mainFrame);
  figma.viewport.scrollAndZoomIntoView([mainFrame]);

  figma.notify("BA - Screen Flow created successfully!", { timeout: 3000 });
  figma.closePlugin();
})();
