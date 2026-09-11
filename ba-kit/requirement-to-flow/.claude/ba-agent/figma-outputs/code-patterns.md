# Ba Agent — Figma Code Patterns

> Code patterns cho `use_figma` — FigJam (`/board/`) vs Figma Design (`/design/`). Đọc trước khi viết use_figma call.

---

## FigJam Code Patterns (dùng khi URL là `/board/`)

```js
// ✅ Node với text tích hợp (FigJam-only)
const s = figma.createShapeWithText();
s.shapeType = 'ROUNDED_RECTANGLE'; // ELLIPSE | DIAMOND | SQUARE | ROUNDED_RECTANGLE
s.resize(200, 80);
s.x = 100; s.y = 200;
s.fills = [{type:'SOLID', color:{r:0.9,g:0.95,b:1}}];
s.strokes = [{type:'SOLID', color:{r:0.04,g:0.41,b:0.85}}];
s.strokeWeight = 2;
await figma.loadFontAsync({family:"Inter", style:"Bold"});
s.text.fontName = {family:"Inter", style:"Bold"};
s.text.fontSize = 13;
s.text.characters = "Tên node\nSub-text nhỏ";
s.text.textAlignHorizontal = "CENTER";
// Sub-text nhỏ hơn:
s.text.setRangeFontSize(label.length+1, s.text.characters.length, 10);
s.text.setRangeFontName(label.length+1, s.text.characters.length, {family:"Inter",style:"Regular"});
page.appendChild(s);

// ✅ Connector thật (FigJam-only) — tự route giữa 2 nodes
const c = figma.createConnector();
c.connectorStart = {endpointNodeId: nodeA.id, magnet: 'AUTO'};
c.connectorEnd   = {endpointNodeId: nodeB.id, magnet: 'AUTO'};
c.strokes = [{type:'SOLID', color:{r:0.04,g:0.41,b:0.85}}];
c.strokeWeight = 2;
c.connectorEndStrokeCap = 'ARROW_EQUILATERAL';
c.dashPattern = [6,4]; // nếu dashed
c.text.characters = "label"; // label trên connector
page.appendChild(c);

// ✅ Section (group vùng làm việc)
const sec = figma.createSection();
sec.name = "Output 1 — Flow Tổng Quan";
sec.x = 0; sec.y = 0;
sec.resizeWithoutConstraints(1800, 700);
sec.fills = [{type:'SOLID', color:{r:0.04,g:0.41,b:0.85}, opacity:0.06}];
page.appendChild(sec);

// ✅ Sticky note
const sticky = figma.createSticky();
sticky.x = 500; sticky.y = 300;
sticky.fills = [{type:'SOLID', color:{r:1,g:0.97,b:0.88}}];
sticky.text.characters = "Nội dung sticky note";
page.appendChild(sticky);
```

## Figma Design Code Patterns (dùng khi URL là `/design/`)

```js
// Node = Rectangle + Text riêng (không có createShapeWithText)
function makeNode(label, sub, x, y, w, h, fill, stroke, parent) {
  const r = figma.createRectangle();
  r.resize(w, h); r.x = x; r.y = y; r.cornerRadius = 8;
  r.fills = [{type:'SOLID', color:fill}];
  r.strokes = [{type:'SOLID', color:stroke}]; r.strokeWeight = 1.5;
  parent.appendChild(r);
  const tx = figma.createText();
  tx.fontName = {family:"Inter", style:"Bold"}; tx.fontSize = 12;
  tx.resize(w-12, 10); tx.textAutoResize = "HEIGHT"; // resize TRƯỚC, set HEIGHT SAU
  tx.x = x+6; tx.y = y+8;
  parent.appendChild(tx);
  tx.characters = sub ? `${label}\n${sub}` : label;
  return r;
}

// Arrow = Rectangle 2px height (không có createConnector)
function arrow(x1, x2, y, color, parent) {
  const r = figma.createRectangle();
  r.resize(x2-x1, 2); r.x = x1; r.y = y-1;
  r.fills = [{type:'SOLID', color:color}];
  parent.appendChild(r);
}

// ⚠️ TEXT NODE BUG — LUÔN theo thứ tự này:
tx.resize(width, 10);          // 1. resize trước
tx.textAutoResize = "HEIGHT";  // 2. set SAU resize (resize() reset về NONE)
tx.characters = "...";         // 3. set text sau cùng
curY += tx.height + gap;       // 4. height giờ mới chính xác
```

**Trước khi bắt đầu:**
1. Hỏi user URL (Figma Design hay FigJam?) + page đích
2. Load skill `figma:figma-use` trước khi gọi `use_figma`
3. FigJam: `get_metadata` không hoạt động — dùng `use_figma` để đọc `figma.currentPage.children`
4. Figma Design: `get_metadata` để xác nhận page + lấy nodeId
