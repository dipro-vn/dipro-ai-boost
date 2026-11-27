#!/usr/bin/env node
// Chuyển dữ liệu Figma MCP thành `figma-<size>.json` (xem skill ui_compare), kèm NGUỒN của từng loại dữ liệu.
//
// Hai loại đầu vào:
//   1) XML từ `get_metadata` của Figma MCP chính thức: chỉ có vị trí và kích thước (hình học).
//   2) JSON từ `get_design_context` của figma-console: có sẵn style (màu, viền, bo góc, đệm, font).
//
// Nguồn (source): mỗi lần chạy khai báo dữ liệu đến từ file Figma nào. `original` là file thật của design,
// `copy` là bản copy cá nhân (khi không có quyền chạy plugin trong file gốc). QUY TẮC:
//   - Hình học (x, y, rộng, cao, tên, cây cha-con) LUÔN lấy từ nguồn mặc định (`original`).
//   - Nguồn khác chỉ được cung cấp loại dữ liệu ghi trong `dataTypes` của bản ánh xạ (hiện chỉ `style`).
//   - Id của bản copy khác id của bản gốc nên bắt buộc có file ánh xạ rõ ràng (--map); không tự ghép theo tên.
//
// Dùng:
//   # 1) Khung và hình học từ file gốc
//   node figma_meta.mjs --in meta.xml --out figma-1440.json --source original --file-key <key> --file-name soloworks
//   # 2) Style từ figma-console trên chính file gốc (cùng id, không cần ánh xạ)
//   node figma_meta.mjs --in a.json,b.json --out figma-1440.json --merge --source original --file-key <key>
//   # 3) Style từ bản copy: cần ánh xạ id copy -> id gốc
//   node figma_meta.mjs --in copy-a.json --out figma-1440.json --merge --source copy --file-key <key> --file-name Untitled --map map.json
//   # 3b) Gợi ý ánh xạ theo cấu trúc (AI/QC duyệt rồi mới dùng làm --map)
//   node figma_meta.mjs --in copy-a.json --out figma-1440.json --suggest-map map.json --from 240:229 --to 5532:50999 --source copy
//   # 4) Style do AI điền tay từ Figma MCP chính thức cho cả khối: đánh dấu đã lấy style cho node và con
//   node figma_meta.mjs --out figma-1440.json --styled-subtree 5532:57482,5532:50999
//
// File ánh xạ: {"source":"copy","mappings":[{"sourceNodeId":"240:229","targetNodeId":"5532:50999","dataTypes":["style"]}]}
//
// Ra: {sources, defaultSource, frame, nodes, sourceMappings, sourceMappingWarnings, warnings}
//   node: {id,name,type,parent,x,y,w,h,text?,style?,styleFetched,sourceOverrides?,sourceRefs?}
//   styleFetched: true khi style của node đã thật sự được lấy. Khi true, thuộc tính vắng nghĩa là giá trị mặc định
//   (không viền, nền trong suốt...); khi false, thuộc tính vắng nghĩa là CHƯA có dữ liệu (không so được).
//   sourceOverrides.style: nguồn dự kiến khi khác mặc định; sourceRefs.style: id node trong nguồn đó và cảnh báo nếu có.
// Lỗi (thiếu node, ánh xạ trùng...) => in lỗi, thoát mã 1, KHÔNG ghi file.
import fs from 'fs';
import { parseArgs, need, toHex } from './lib.mjs';

const a = parseArgs(process.argv);
need(a, ['out']);
const TOL = +(a.tol || 1);
const ALLOWED_TYPES = ['style', 'text']; // loại dữ liệu nguồn phụ được phép cung cấp (hình học thì không)
const errors = [];
const today = new Date().toLocaleDateString('sv-SE');   // ngày theo giờ máy

// ---- nạp file đã có (--merge, --suggest-map, --styled-subtree)
const mergeMode = !!(a.merge || a['suggest-map'] || a['styled-subtree']);
const prev = mergeMode && fs.existsSync(a.out) ? JSON.parse(fs.readFileSync(a.out, 'utf8')) : null;
if (mergeMode && !prev) { console.error('Chưa có ' + a.out + ' để gộp. Chạy bước 1 (hình học từ file gốc) trước.'); process.exit(1); }

const nodes = new Map();
const sources = prev?.sources ? { ...prev.sources } : {};
let defaultSource = prev?.defaultSource || null;
let sourceMappings = prev?.sourceMappings ? [...prev.sourceMappings] : [];
let mappingWarnings = prev?.sourceMappingWarnings ? [...prev.sourceMappingWarnings] : [];
if (prev) for (const n of prev.nodes) nodes.set(n.id, { styleFetched: !!n.style, ...n });

function put(rec) {
  const old = nodes.get(rec.id);
  if (!old) { nodes.set(rec.id, rec); return; }
  const style = { ...(old.style || {}), ...(rec.style || {}) };
  nodes.set(rec.id, { ...old, ...rec, text: rec.text ?? old.text,
    styleFetched: !!(old.styleFetched || rec.styleFetched),
    ...(Object.keys(style).length ? { style } : {}) });
}

// ---- XML (get_metadata của Figma MCP chính thức): hình học
function addXml(xml) {
  const dec = s => s.replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
  const tag = /<(\/?)([A-Za-z][\w-]*)((?:\s+[\w-]+="[^"]*")*)\s*(\/?)>/g;
  const stack = [];
  let m, first = null;
  while ((m = tag.exec(xml))) {
    const [, closing, type, attrStr, selfClose] = m;
    if (closing) { stack.pop(); continue; }
    const at = {};
    for (const k of attrStr.matchAll(/([\w-]+)="([^"]*)"/g)) at[k[1]] = dec(k[2]);
    if (!at.id) { if (!selfClose) stack.push(null); continue; }
    first ??= at.id;
    put({ id: at.id, name: at.name || '', type, parent: stack.length ? stack[stack.length - 1] : null,
      x: +at.x || 0, y: +at.y || 0, w: +at.width || 0, h: +at.height || 0, styleFetched: false });
    if (!selfClose) stack.push(at.id);
  }
  return first;
}

// ---- JSON (get_design_context của figma-console): hình học + style
const WEIGHT = { thin: 100, extralight: 200, light: 300, regular: 400, medium: 500, semibold: 600, bold: 700, extrabold: 800, black: 900 };
const solid = arr => (arr || []).find(f => f.type === 'SOLID' && f.visible !== false);
const hex = f => toHex([f.color.r * 255, f.color.g * 255, f.color.b * 255, f.opacity ?? 1]);
// Node có đủ trường style (figma-console trả `fills`/`strokes`/`fontSize` kể cả khi rỗng). Node bị cắt bởi `depth` thì không có.
const hasStyleFields = n => 'fills' in n || 'strokes' in n || 'fontSize' in n;

function jsonStyle(n) {
  const s = {};
  const fill = solid(n.fills), stroke = solid(n.strokes);
  if (n.type === 'TEXT') { if (fill) s.color = hex(fill); }
  else if (fill) s.bg = hex(fill);
  if (stroke) { s.borderColor = hex(stroke); if (typeof n.strokeWeight === 'number') s.borderWidth = n.strokeWeight; }
  if (typeof n.cornerRadius === 'number') s.radius = n.cornerRadius;
  if (n.padding && n.layoutMode && n.layoutMode !== 'NONE') s.padding = [n.padding.top, n.padding.right, n.padding.bottom, n.padding.left];
  if (typeof n.opacity === 'number' && n.opacity !== 1) s.opacity = n.opacity;
  if (typeof n.fontSize === 'number') s.fontSize = n.fontSize;
  if (n.fontName) {
    s.fontFamily = n.fontName.family;
    const w = n.fontName.variationSettings?.wght ?? WEIGHT[String(n.fontName.style || '').toLowerCase().replace(/\s/g, '')];
    if (w) s.fontWeight = w;
  }
  return s;
}

function walkJson(root, visit) {
  // node ẩn (visible: false) không hiển thị nên không có gì để so; bỏ cả cây con
  (function walk(n, parent) { if (n.visible === false) return; visit(n, parent); for (const c of n.children || []) walk(c, n.id); })(root, root.parentId ?? null);
}

// Nguồn mặc định: đọc cả hình học lẫn style
function addJson(root) {
  let first = null;
  walkJson(root, (n, parent) => {
    first ??= n.id;
    const style = jsonStyle(n);
    const rec = { id: n.id, name: n.name || '', type: String(n.type || '').toLowerCase(), parent,
      x: n.x || 0, y: n.y || 0, w: n.width || 0, h: n.height || 0, styleFetched: hasStyleFields(n) };
    if (n.text !== undefined) rec.text = n.text;
    if (Object.keys(style).length) rec.style = style;
    put(rec);
  });
  return first;
}

// Chỉ số node của nguồn phụ: id -> {node thô, style, w, h, name}
function indexJson(root) {
  const idx = new Map();
  walkJson(root, (n, parent) => idx.set(n.id, { raw: n, parent, w: n.width || 0, h: n.height || 0, name: n.name || '',
    fetched: hasStyleFields(n), style: jsonStyle(n), children: (n.children || []).map(c => c.id) }));
  return idx;
}

const loadInputs = () => String(a.in).split(',').map(x => x.trim()).filter(Boolean).map(f => ({ f, text: fs.readFileSync(f, 'utf8') }));
const isJson = t => t.trimStart().startsWith('{');
const sourceName = a.source || defaultSource || 'original';

// ---- gợi ý ánh xạ theo cấu trúc (không áp dụng, chỉ ghi file để duyệt)
if (a['suggest-map']) {
  need(a, ['in', 'from', 'to', 'source']);
  if (sourceName === defaultSource) { console.error(`--source "${sourceName}" là nguồn mặc định (hình học). Gợi ý ánh xạ dành cho nguồn phụ, ví dụ --source copy.`); process.exit(1); }
  const idx = new Map();
  for (const { text } of loadInputs()) if (isJson(text)) for (const [k, v] of indexJson(JSON.parse(text))) idx.set(k, v);
  if (!idx.has(a.from)) { console.error('Không có node ' + a.from + ' trong --in'); process.exit(1); }
  if (!nodes.has(a.to)) { console.error('Không có node ' + a.to + ' trong ' + a.out); process.exit(1); }
  const kidsOf = id => [...nodes.values()].filter(n => n.parent === id);
  const mappings = [], unmatched = [];
  // Ghép các con theo thứ tự nhưng cho phép bỏ qua node dư ở một phía (ví dụ XML đã lược các node Vector):
  // với mỗi con của bản gốc, tìm con kế tiếp của nguồn phụ cùng tên và cùng kích thước; nếu không có thì lấy con kế tiếp
  // cùng tên khác kích thước (đánh dấu needsReview); không có thì ghi "nguồn phụ không có node tương ứng".
  const sameSize = (u, v) => Math.abs(u.w - v.w) <= TOL && Math.abs(u.h - v.h) <= TOL;
  (function walk(sid, tid) {
    const s = idx.get(sid), t = nodes.get(tid);
    mappings.push({ sourceNodeId: sid, targetNodeId: tid, dataTypes: ['style'], needsReview: !(s.name === t.name && sameSize(s, t)) });
    const sk = s.children.map(c => ({ id: c, ...idx.get(c) })), tk = kidsOf(tid);
    let j = 0;
    for (const tc of tk) {
      let k = -1, review = false;
      for (let q = j; q < sk.length; q++) if (sk[q].name === tc.name && sameSize(sk[q], tc)) { k = q; break; }
      if (k < 0) for (let q = j; q < sk.length; q++) if (sk[q].name === tc.name) { k = q; review = true; break; }
      if (k < 0) { unmatched.push({ missing: 'source', sourceNodeId: null, targetNodeId: tc.id, name: tc.name, note: 'node có ở bản gốc nhưng nguồn phụ không có node tương ứng' }); continue; }
      for (let q = j; q < k; q++) unmatched.push({ missing: 'target', sourceNodeId: sk[q].id, targetNodeId: null, name: sk[q].name, note: 'node có ở nguồn phụ nhưng bản gốc không có node tương ứng' });
      j = k + 1;
      if (review) {
        unmatched.push({ missing: null, reason: 'cùng tên nhưng kích thước khác', sourceNodeId: sk[k].id, targetNodeId: tc.id, name: tc.name, source: { w: sk[k].w, h: sk[k].h }, target: { w: tc.w, h: tc.h } });
      }
      walk(sk[k].id, tc.id);
    }
    for (let q = j; q < sk.length; q++) unmatched.push({ missing: 'target', sourceNodeId: sk[q].id, targetNodeId: null, name: sk[q].name, note: 'node có ở nguồn phụ nhưng bản gốc không có node tương ứng' });
  })(a.from, a.to);
  fs.writeFileSync(a['suggest-map'], JSON.stringify({ source: sourceName, basis: 'structure', note: 'Gợi ý theo thứ tự cây + tên + kích thước. Duyệt các mục needsReview và unmatched rồi mới dùng làm --map.', mappings, unmatched }, null, 1));
  console.log(`suggest-map: ${mappings.length} cặp, ${unmatched.length} cần duyệt\n  -> ${a['suggest-map']}`);
  process.exit(0);
}

// ---- --styled-subtree: đánh dấu đã lấy style (AI đã điền style từ Figma MCP chính thức cho cả khối)
if (a['styled-subtree']) {
  const kids = new Map();
  for (const n of nodes.values()) { if (!kids.has(n.parent)) kids.set(n.parent, []); kids.get(n.parent).push(n.id); }
  let count = 0;
  for (const root of String(a['styled-subtree']).split(',').map(x => x.trim()).filter(Boolean)) {
    if (!nodes.has(root)) { errors.push(`--styled-subtree: không có node ${root}`); continue; }
    (function mark(id) { const n = nodes.get(id); if (!n.styleFetched) count++; n.styleFetched = true; (kids.get(id) || []).forEach(mark); })(root);
  }
  if (!a.in) finish(`đánh dấu đã lấy style cho ${count} node`);
}

// ---- khai báo nguồn
if (a.in) {
  const isDefaultRun = !defaultSource || sourceName === defaultSource;
  if (!sources[sourceName]) {
    need(a, ['file-key']);
    sources[sourceName] = { fileName: a['file-name'] || null, fileKey: a['file-key'], rootNodeId: null, retrievedAt: today, files: [] };
    if (!a['file-name']) console.warn(`Lưu ý: nguồn "${sourceName}" chưa có --file-name.`);
  } else if (a['file-key'] && sources[sourceName].fileKey !== a['file-key']) {
    errors.push(`Nguồn "${sourceName}" đã khai báo file ${sources[sourceName].fileKey}, lần này là ${a['file-key']}. Dùng tên nguồn khác.`);
  }
  if (!defaultSource) defaultSource = sourceName;
  const src = sources[sourceName];
  src.retrievedAt = today;
  for (const f of String(a.in).split(',').map(x => x.trim()).filter(Boolean)) if (!src.files.includes(f)) src.files.push(f);

  if (isDefaultRun) {
    for (const { text } of loadInputs()) {
      const root = isJson(text) ? addJson(JSON.parse(text)) : addXml(text);
      src.rootNodeId ??= root;
    }
  } else {
    // nguồn phụ: chỉ cung cấp style qua ánh xạ
    need(a, ['map']);
    const map = JSON.parse(fs.readFileSync(a.map, 'utf8'));
    if (map.source && map.source !== sourceName) errors.push(`File ánh xạ ghi nguồn "${map.source}" nhưng --source là "${sourceName}"`);
    const idx = new Map();
    for (const { f, text } of loadInputs()) {
      if (!isJson(text)) { errors.push(`${f}: nguồn phụ "${sourceName}" chỉ nhận JSON của figma-console`); continue; }
      const root = JSON.parse(text);
      src.rootNodeId ??= root.id;
      for (const [k, v] of indexJson(root)) idx.set(k, v);
    }
    const seenSrc = new Set(), seenTgt = new Set();
    const newWarn = [];
    for (const m of map.mappings || []) {
      const label = `${m.sourceNodeId} -> ${m.targetNodeId}`;
      const types = m.dataTypes || [];
      if (!m.sourceNodeId || !m.targetNodeId) { errors.push(`Ánh xạ thiếu id: ${JSON.stringify(m)}`); continue; }
      if (!types.length || types.some(t => !ALLOWED_TYPES.includes(t))) { errors.push(`${label}: dataTypes phải nằm trong [${ALLOWED_TYPES}] (hình học luôn lấy từ nguồn "${defaultSource}")`); continue; }
      if (seenSrc.has(m.sourceNodeId)) errors.push(`${label}: node nguồn ${m.sourceNodeId} bị ánh xạ hai lần`);
      if (seenTgt.has(m.targetNodeId)) errors.push(`${label}: node đích ${m.targetNodeId} bị ánh xạ hai lần`);
      seenSrc.add(m.sourceNodeId); seenTgt.add(m.targetNodeId);
      const s = idx.get(m.sourceNodeId), t = nodes.get(m.targetNodeId);
      if (!s) { errors.push(`${label}: không có node ${m.sourceNodeId} trong dữ liệu nguồn "${sourceName}"`); continue; }
      if (!t) { errors.push(`${label}: không có node đích ${m.targetNodeId} trong ${a.out}`); continue; }
      // kiểm hình học, luôn chạy dù ánh xạ style thành công; không bao giờ thay hình học của nguồn mặc định
      const dw = s.w - t.w, dh = s.h - t.h;
      let warning = null;
      if (Math.abs(dw) > TOL || Math.abs(dh) > TOL) {
        warning = 'geometry';
        newWarn.push({ source: sourceName, sourceNodeId: m.sourceNodeId, targetNodeId: m.targetNodeId, name: t.name, check: 'geometry',
          [defaultSource]: { width: t.w, height: t.h }, [sourceName]: { width: s.w, height: s.h }, delta: { width: dw, height: dh }, status: 'warning' });
      }
      if (types.includes('style')) {
        if (!s.fetched) { errors.push(`${label}: node ${m.sourceNodeId} trong nguồn "${sourceName}" không có dữ liệu style (bị cắt bởi depth?)`); continue; }
        t.style = { ...(t.style || {}), ...s.style };
        t.styleFetched = true;
        t.sourceOverrides = { ...(t.sourceOverrides || {}), style: sourceName };
        t.sourceRefs = { ...(t.sourceRefs || {}), style: { source: sourceName, nodeId: m.sourceNodeId, ...(warning ? { warning } : {}) } };
      }
      if (types.includes('text')) {
        if (s.raw.type !== 'TEXT') { /* chỉ node chữ mới có text */ }
        else if (s.raw.text === undefined) { newWarn.push({ source: sourceName, sourceNodeId: m.sourceNodeId, targetNodeId: m.targetNodeId, name: t.name, check: 'text', status: 'warning', note: 'node nguồn phụ không có text' }); }
        else {
          t.text = s.raw.text;
          t.sourceOverrides = { ...(t.sourceOverrides || {}), text: sourceName };
          t.sourceRefs = { ...(t.sourceRefs || {}), text: { source: sourceName, nodeId: m.sourceNodeId } };
        }
      }
    }
    sourceMappings = sourceMappings.filter(m => m.source !== sourceName);
    for (const m of map.mappings || []) sourceMappings.push({ source: sourceName, sourceNodeId: m.sourceNodeId, targetNodeId: m.targetNodeId, dataTypes: m.dataTypes });
    mappingWarnings = mappingWarnings.filter(w => w.source !== sourceName).concat(newWarn);
  }
}

if (!nodes.size) errors.push('Không đọc được node nào');

function finish(msg) {
  const warnings = [];
  for (const n of nodes.values()) {
    if (n.style && !n.styleFetched) warnings.push({ type: 'style-without-flag', nodeId: n.id, name: n.name, note: 'có style nhưng styleFetched=false (style điền tay?). Dùng --styled-subtree nếu style của khối này đã được lấy đủ' });
  }
  if (errors.length) { console.error('figma_meta: LỖI, không ghi file:\n - ' + errors.join('\n - ')); process.exit(1); }
  const noText = [...nodes.values()].filter(n => n.type === 'text' && (n.text === undefined || n.text === null)).map(n => n.id);
  if (noText.length) warnings.push({ type: 'text-without-content', count: noText.length, nodeIds: noText,
    note: 'node chữ chưa có `text` (XML chỉ có tên, `name` không được dùng thay chữ). Điền `text` cho node chữ cần so (checkText), nếu không kết quả là not_comparable' });
  const list = [...nodes.values()];
  const root = list.find(n => n.parent === null) || list[0];
  const out = { sources, defaultSource, frame: { id: root.id, name: root.name, width: root.w, height: root.h },
    nodes: list, sourceMappings, sourceMappingWarnings: mappingWarnings, warnings };
  fs.writeFileSync(a.out, JSON.stringify(out, null, 1));
  const fetched = list.filter(n => n.styleFetched).length, overrides = list.filter(n => n.sourceOverrides).length;
  console.log(`figma_meta: ${msg || ''}`.trim());
  console.log(`  ${list.length} node | đã lấy style ${fetched} | style từ nguồn phụ ${overrides} | cảnh báo ánh xạ ${mappingWarnings.length} | cảnh báo khác ${warnings.length}`);
  for (const w of mappingWarnings) console.log(w.delta ? `  ! ${w.sourceNodeId} -> ${w.targetNodeId} (${w.name}): hình học lệch ${w.delta.width}x${w.delta.height}` : `  ! ${w.sourceNodeId} -> ${w.targetNodeId} (${w.name}): ${w.note}`);
  for (const w of warnings.slice(0, 5)) console.log(w.count ? `  ! ${w.type}: ${w.count} node (${w.nodeIds.slice(0, 3).join(', ')}${w.count > 3 ? ', ...' : ''})` : `  ! ${w.nodeId} (${w.name}): ${w.type}`);
  if (warnings.length > 5) console.log(`  ! ... và ${warnings.length - 5} cảnh báo cùng loại`);
  console.log(`  -> ${a.out}`);
  process.exit(0);
}
finish(`frame "${[...nodes.values()].find(n => n.parent === null)?.name}"`);
