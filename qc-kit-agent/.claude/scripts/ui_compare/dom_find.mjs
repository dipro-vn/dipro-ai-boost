#!/usr/bin/env node
// Tra cứu nhanh `dom-<size>.json` để ghép cặp (không phải đọc cả file hàng nghìn phần tử).
//
// Dùng:
//   node dom_find.mjs --dom dom-1440.json --text "スカウト"            # phần tử có chữ chứa chuỗi (chữ của chính nó hoặc của con cháu)
//   node dom_find.mjs --dom dom-1440.json --tag button [--within 165]   # lọc theo thẻ, chỉ trong cây con của phần tử i
//   node dom_find.mjs --dom dom-1440.json --tree 165 [--depth 3]        # in cây con của phần tử i
//   node dom_find.mjs --dom dom-1440.json --box "x,y,w,h" [--tol 3]     # phần tử có khung gần khớp (vd khung lấy từ Figma)
// Tuỳ chọn chung: --limit 40 (mặc định)
// Mỗi dòng: i  cha  <thẻ>  "chữ"  [x,y rộng×cao]
import { parseArgs, need, readJson } from './lib.mjs';

const a = parseArgs(process.argv);
need(a, ['dom']);
const dom = readJson(a.dom);
const N = dom.nodes;
const kids = new Map();
for (const n of N) { if (!kids.has(n.parent)) kids.set(n.parent, []); kids.get(n.parent).push(n); }
const limit = +(a.limit || 40);

const inSubtree = (n, root) => { for (let c = n; c; c = N[c.parent]) { if (c.i === root) return true; if (c.parent < 0) break; } return false; };
const deepText = n => (n.text + ' ' + (kids.get(n.i) || []).map(deepText).join(' ')).replace(/\s+/g, ' ').trim();
const fmt = (n, depth = 0) =>
  `${'  '.repeat(depth)}${n.i} ←${n.parent} <${n.tag}${n.attrs?.role ? ' role=' + n.attrs.role : ''}> ` +
  `${n.text ? JSON.stringify(n.text) + ' ' : ''}[${n.x},${n.y} ${n.w}×${n.h}]`;

if (a.tree !== undefined) {
  const root = N[+a.tree];
  if (!root) { console.error('Không có phần tử ' + a.tree); process.exit(1); }
  const maxD = +(a.depth || 3);
  let shown = 0;
  (function walk(n, d) {
    if (shown++ >= limit * 5) return;
    console.log(fmt(n, d));
    if (d < maxD) for (const c of kids.get(n.i) || []) walk(c, d + 1);
  })(root, 0);
} else {
  let list = N;
  if (a.within !== undefined) list = list.filter(n => n.i !== +a.within && inSubtree(n, +a.within));
  if (a.tag) list = list.filter(n => n.tag === a.tag);
  if (a.text) list = list.filter(n => deepText(n).includes(a.text) && !(kids.get(n.i) || []).some(c => deepText(c).includes(a.text)) || n.text.includes(a.text));
  if (a.box) {
    const [x, y, w, h] = String(a.box).split(',').map(Number), t = +(a.tol || 3);
    list = list.filter(n => Math.abs(n.x - x) <= t && Math.abs(n.y - y) <= t && Math.abs(n.w - w) <= t && Math.abs(n.h - h) <= t);
  }
  console.log(`${list.length} phần tử` + (list.length > limit ? ` (hiện ${limit} đầu)` : ''));
  for (const n of list.slice(0, limit)) console.log(fmt(n));
}
