#!/usr/bin/env node
// So số liệu từng cặp đã ghép Figma ↔ web (xem skill ui_compare).
//
// Dùng:
//   node compare.mjs --figma figma-1440.json --dom dom-1440.json --pairs pairs-1440.json --out result-1440.json
//        [--tol 1] [--color-tol 2] [--opacity-tol 0.02]
//
// Quy tắc: vị trí tính TƯƠNG ĐỐI trong cặp cha gần nhất đã ghép (cha lệch thì không báo lặp ở con);
// kích thước lệch do cha lệch cùng một lượng thì ghi vào `inherited`, không vào `findings`;
// cặp có match "thấp" đưa vào `uncertain`, không vào `findings`.
//
// Ngoài `findings/inherited/uncertain/ok`, mỗi cặp có `checks` đủ 11 loại phép kiểm tra (CHECKS), mỗi loại một trạng thái:
//   passed (đã so, khớp) | mismatch (đã so, lệch; có `inherited` nếu lệch theo cha/khối thiếu) |
//   not_comparable (thiếu dữ liệu để so, có lý do) | skipped (chủ động bỏ qua theo `skip`/`checkText`) |
//   not_applicable (loại này không áp dụng cho node, ví dụ node không phải chữ; không tính vào mẫu số coverage).
// `checks` và `findings` sinh ra từ cùng một chỗ nên không mâu thuẫn; `meta.consistency` tự kiểm lại.
import fs from 'fs';
import { parseArgs, need, readJson, round2, parseColor, toHex, splitPairs, expandExcludes } from './lib.mjs';

const a = parseArgs(process.argv);
need(a, ['figma', 'dom', 'pairs', 'out']);
const TOL = +(a.tol ?? 1), CTOL = +(a['color-tol'] ?? 2), OTOL = +(a['opacity-tol'] ?? 0.02);
const figma = readJson(a.figma), dom = readJson(a.dom), pairsRaw = readJson(a.pairs);
// `pairs` có thể là mảng cặp (dạng cũ) hoặc {pairs:[...], exclude:[...]}.
const { pairs, excludeSpec } = splitPairs(pairsRaw);
const CAND_W = +(a['cand-min-w'] ?? 100), CAND_H = +(a['cand-min-h'] ?? 20);
const F = new Map(figma.nodes.map(n => [n.id, n]));
const D = new Map(dom.nodes.map(n => [n.i, n]));

// Vị trí tuyệt đối của node Figma trong frame (cộng dồn x,y của các node cha, không tính frame gốc).
function figBox(id) {
  const n = F.get(id);
  let x = 0, y = 0, c = n;
  while (c && c.parent) { x += c.x; y += c.y; c = F.get(c.parent); }
  return { x, y, w: n.w, h: n.h };
}
const domBox = i => { const n = D.get(i); return { x: n.x, y: n.y, w: n.w, h: n.h }; };

// `domBox: [x, y, rộng, cao]` trong pairs: khung "ảo" cho khối Figma không có thẻ web tương ứng
// (ví dụ cột nội dung mà web không bọc bằng một thẻ riêng). Tính như đã ghép, không có style để so.
// Hai dạng: `domBox: [x, y, rộng, cao]` (số cố định) hoặc `domBox: {"of": <i phần tử web>, "inset": [trên, phải, dưới, trái]}`
// (khung lấy từ một phần tử web rồi thu vào theo `inset`; dịch theo khi bố cục đổi, nên nên dùng dạng này).
const isBox = p => Array.isArray(p.domBox) || (p.domBox && typeof p.domBox === 'object' && p.domBox.of != null);
const hasDom = p => p.dom != null || isBox(p);
function pairBox(p) {
  if (Array.isArray(p.domBox)) return { x: p.domBox[0], y: p.domBox[1], w: p.domBox[2], h: p.domBox[3] };
  if (p.domBox && typeof p.domBox === 'object') {
    const r = domBox(p.domBox.of), [t, rt, b, l] = p.domBox.inset || [0, 0, 0, 0];
    return { x: r.x + l, y: r.y + t, w: r.w - l - rt, h: r.h - t - b };
  }
  return domBox(p.dom);
}
for (const p of pairs) if (p.domBox && !Array.isArray(p.domBox) && !D.has(p.domBox.of)) { console.error(`compare: LỖI domBox.of ${p.domBox.of} không có trong dữ liệu web (cặp ${p.figma})`); process.exit(1); }
const byFigma = new Map(pairs.filter(p => p.figma && hasDom(p)).map(p => [p.figma, p]));
function parentPair(figmaId) {
  let c = F.get(figmaId);
  while (c && c.parent) { c = F.get(c.parent); if (c && byFigma.has(c.id)) return byFigma.get(c.id); }
  return null;
}

// Chữ phía web: ưu tiên chữ trực tiếp của phần tử; chỉ khi rỗng mới lấy chữ gộp từ con cháu.
const domKids = new Map();
for (const n of dom.nodes) { if (!domKids.has(n.parent)) domKids.set(n.parent, []); domKids.get(n.parent).push(n); }
const normText = t => String(t ?? '').replace(/\s+/g, '').trim();
const deepWebText = n => normText(n.text) + (domKids.get(n.i) || []).map(deepWebText).join('');
const webText = n => normText(n.text) || deepWebText(n);

// Các node Text trong cây con của node Figma `id` (không tính chính nó), tách thành:
// `own` = chưa có cặp riêng (dùng được), `covered` = đã nằm trong một cặp ghép khác (được so ở cặp đó).
const figKids = new Map();
for (const n of figma.nodes) { if (!figKids.has(n.parent)) figKids.set(n.parent, []); figKids.get(n.parent).push(n); }
function subtreeTexts(id) {
  const own = [], covered = [];
  (function walk(nid, underPaired) {
    for (const c of figKids.get(nid) || []) {
      const paired = byFigma.has(c.id);
      if (c.type === 'text') (paired || underPaired ? covered : own).push(c);
      walk(c.id, underPaired || paired);
    }
  })(id, false);
  return { own, covered };
}

// ---- exclude: phần tử chủ động loại khỏi phạm vi so sánh (phải có lý do; không tự thêm khi ghép không được)
// Mỗi mục: {figma?: id|[id], dom?: i|[i], figmaChildrenOf?: id, domChildrenOf?: i, keep?: n, scope?: "subtree"|"node", reason}
// `figmaChildrenOf`/`domChildrenOf` + `keep` loại các con từ vị trí `keep` trở đi (ví dụ chỉ giữ 3 hàng đầu của danh sách).
const { exFigma, exDom, excludes, errors: exErrors } = expandExcludes(excludeSpec, F, D, figKids, domKids);
if (exErrors.length) { console.error('compare: LỖI exclude, không ghi file:\n - ' + exErrors.join('\n - ')); process.exit(1); }

const label = n => (n.text ? `"${n.text}"` : n.name || n.tag || '');
const normRadius = (r, w, h) => (r >= Math.min(w, h) / 2 - 0.5 && r > 0 ? 'tròn' : r);

const CHECKS = ['position', 'size', 'padding', 'radius', 'border', 'background', 'text_color', 'font_size', 'font_weight', 'opacity', 'text_content'];
const CHECK_OF_PROP = { 'màu viền': 'border', 'độ dày viền': 'border', 'màu nền': 'background', 'màu chữ': 'text_color', 'cỡ chữ': 'font_size',
  'chiều cao dòng': 'font_size', font: 'font_size', 'độ đậm chữ': 'font_weight', 'độ mờ': 'opacity', 'bo góc': 'radius' };
const checkOf = (group, prop) => group === 'size' ? 'size' : group === 'position' ? 'position' : group === 'text' ? 'text_content'
  : /^đệm /.test(prop) ? 'padding' : CHECK_OF_PROP[prop];
const STYLE_CHECKS = ['padding', 'radius', 'border', 'background', 'text_color', 'font_size', 'font_weight', 'opacity'];

// Gộp các phép nhỏ (ev) của một loại thành một trạng thái.
function summarizeChecks(ev) {
  const checks = {};
  for (const c of CHECKS) {
    const list = ev.filter(e => e.check === c);
    const reasons = [...new Set(list.filter(e => e.reason).map(e => e.reason))];
    const via = [...new Set(list.map(e => e.via).filter(Boolean))];
    const mism = list.filter(e => e.status === 'mismatch');
    let r;
    if (!list.length) r = { status: 'not_comparable', reason: 'chưa có phép so nào chạy cho loại này' };
    else if (mism.length) r = { status: 'mismatch', inherited: mism.every(e => e.inherited), items: mism.map(e => ({ prop: e.item.prop, expected: e.item.expected, actual: e.item.actual, delta: e.item.delta, detail: e.item.detail, inherited: !!e.inherited })), ...(reasons.length ? { notes: reasons } : {}) };
    else if (list.some(e => e.status === 'passed')) r = { status: 'passed', ...(reasons.length ? { notes: reasons } : {}) };
    else {
      const st = ['skipped', 'not_comparable', 'not_applicable'].find(x => list.some(e => e.status === x));
      r = { status: st, reason: reasons.join('; ') };
    }
    if (via.length) r.via = via;
    const tx = list.find(e => e.source_text_node);
    if (tx) { r.source_text_node = tx.source_text_node; if (r.status === 'passed') { r.expected = tx.expected; r.actual = tx.actual; } }
    checks[c] = r;
  }
  return checks;
}

const findings = [], inherited = [], uncertain = [], ok = [], okComplete = [], pairResults = [];

for (const p of pairs) {
  const base = { figma: p.figma ?? null, dom: p.dom ?? null, role: p.role || '', level: p.level ?? null, match: p.match || 'cao', note: p.note || '' };
  const mine = [], inh = [];
  const ev = [];   // các phép kiểm tra nhỏ của cặp, gộp lại thành `checks` ở cuối
  const nc = (check, reason) => ev.push({ check, status: 'not_comparable', reason });
  const na = (check, reason) => ev.push({ check, status: 'not_applicable', reason });
  const skp = (check, reason) => ev.push({ check, status: 'skipped', reason });
  const pass = (check, via) => ev.push({ check, status: 'passed', via });
  // `skip` trong pairs: bỏ qua một loại so sánh cho cặp này, dùng cho khối có nội dung động
  // (danh sách, bảng: bỏ "cao"; khối co giãn: bỏ "rộng"). Giá trị: rộng, cao, vị trí, vị trí dưới, style, text.
  const sk = new Set(p.skip || []);
  const GROUP_TOKEN = { position: 'vị trí', style: 'style', text: 'text' };
  const skipped = (group, prop) => sk.has(prop) || sk.has(GROUP_TOKEN[group] || '\0') ||
    (group === 'position' && sk.has('vị trí ' + (prop.match(/trên|dưới|trái|phải/) || [''])[0]));
  // `shiftBy` trong pairs: id Figma các khối bị THIẾU nằm phía trên. Lệch dọc của cặp này được coi là
  // hệ quả của khối thiếu, đưa vào `inherited` thay vì báo thành nghi bug riêng.
  const shiftNames = (p.shiftBy || []).map(id => F.get(id)?.name || id).join(', ');
  const record = (rec, isInh, via) => {
    (isInh ? inh : mine).push(rec);
    const check = checkOf(rec.group, rec.prop);
    if (check) ev.push({ check, status: 'mismatch', inherited: isInh, via, item: rec });
  };
  const add = (group, prop, expected, actual, delta, detail, via) => {
    if (skipped(group, prop)) { const c = checkOf(group, prop); if (c) skp(c, `skip trong pairs: ${prop}`); return; }
    const rec = { ...base, group, prop, expected, actual, delta: delta === undefined ? null : round2(delta), detail: detail || '' };
    if (group === 'position' && /trên/.test(prop) && shiftNames) record({ ...rec, detail: `lệch theo khối bị thiếu phía trên: ${shiftNames}` }, true, via);
    else record(rec, false, via);
  };
  // So một giá trị: bỏ qua theo skip, hoặc ghi khớp, hoặc ghi lệch.
  const cmp = (group, prop, bad, expected, actual, delta, detail, via) => {
    if (skipped(group, prop)) { skp(checkOf(group, prop), `skip trong pairs: ${prop}`); return; }
    if (bad) add(group, prop, expected, actual, delta, detail, via); else pass(checkOf(group, prop), via);
  };

  if (p.figma && !hasDom(p)) {
    add('missing', 'item', `có "${p.role || F.get(p.figma)?.name || p.figma}"`, 'không có trên web', undefined, p.note);
  } else if (!p.figma && p.dom != null) {
    add('extra', 'item', 'không có trong design', `có ${label(D.get(p.dom))}`, undefined, p.note);
  } else if (!F.has(p.figma) || (p.dom != null && !D.has(p.dom))) {
    add('invalid', 'cặp', 'id Figma và phần tử web tồn tại', `figma=${p.figma} dom=${p.dom}`, undefined, 'id không có trong file dữ liệu');
  } else {
    const fn = F.get(p.figma), dn = p.dom != null ? D.get(p.dom) : { style: {}, text: '' };
    const fb = figBox(p.figma), db = pairBox(p);
    const pp = parentPair(p.figma);

    // --- kích thước (bỏ qua nếu lệch cùng lượng với cha → ghi vào inherited)
    let dpw = 0, dph = 0, parentLabel = '';
    if (pp) {
      const pf = figBox(pp.figma), pd = pairBox(pp);
      dpw = pd.w - pf.w; dph = pd.h - pf.h;
      parentLabel = F.get(pp.figma).name;
    }
    for (const [prop, ev_, av, dparent] of [['rộng', fb.w, db.w, dpw], ['cao', fb.h, db.h, dph]]) {
      const d = av - ev_;
      if (skipped('size', prop)) { skp('size', `skip trong pairs: ${prop}`); continue; }
      if (Math.abs(d) <= TOL) { pass('size'); continue; }
      const rec = { ...base, group: 'size', prop, expected: round2(ev_), actual: round2(av), delta: round2(d), detail: '' };
      if (pp && Math.abs(dparent) > TOL && Math.abs(d - dparent) <= TOL) {
        record({ ...rec, detail: `lệch theo khối cha "${parentLabel}" (cha lệch ${round2(dparent)})` }, true);
      } else record(rec, false);
    }

    // --- vị trí tương đối trong cha (khung trang nếu không có cha đã ghép)
    const pf = pp ? figBox(pp.figma) : { x: 0, y: 0, w: figma.frame.width, h: figma.frame.height };
    const pd = pp ? pairBox(pp) : { x: 0, y: 0, w: dom.page.width, h: dom.page.docHeight };
    const fg = { l: fb.x - pf.x, t: fb.y - pf.y, r: pf.x + pf.w - (fb.x + fb.w), b: pf.y + pf.h - (fb.y + fb.h) };
    const dg = { l: db.x - pd.x, t: db.y - pd.y, r: pd.x + pd.w - (db.x + db.w), b: pd.y + pd.h - (db.y + db.h) };

    // Khối liền trên (cùng cha đã ghép, chồng nhau theo chiều ngang): đo KHOẢNG CÁCH tới nó thay vì
    // đo từ mép trên của cha, để lệch không bị cộng dồn qua các khối xếp dọc.
    let prev = null;
    for (const q of pairs) {
      if (q === p || !q.figma || !hasDom(q) || !F.has(q.figma)) continue;
      const qp = parentPair(q.figma);
      if ((qp ? qp.figma : null) !== (pp ? pp.figma : null)) continue;
      const qf = figBox(q.figma);
      const overlap = Math.min(fb.x + fb.w, qf.x + qf.w) - Math.max(fb.x, qf.x);
      if (qf.y + qf.h <= fb.y + TOL && overlap > 0.5 * Math.min(fb.w, qf.w) && (!prev || qf.y + qf.h > prev.fbBottom)) {
        prev = { pair: q, fbBottom: qf.y + qf.h };
      }
    }
    if (prev) {
      const qd = pairBox(prev.pair);
      const fGap = fb.y - prev.fbBottom, dGap = db.y - (qd.y + qd.h);
      const d = dGap - fGap;
      cmp('position', 'khoảng cách tới khối liền trên', Math.abs(d) > TOL, round2(fGap), round2(dGap), d,
        `từ mép dưới của "${prev.pair.role || F.get(prev.pair.figma).name}" xuống mép trên của khối này`, 'relative_to_previous');
    }
    const axis = (lo, hi, nameLo, nameHi, useHi) => {
      const dLo = dg[lo] - fg[lo], dHi = dg[hi] - fg[hi];
      const sym = useHi && Math.abs(dLo - dHi) <= TOL;       // dịch đối xứng = căn giữa, không phải lệch vị trí
      const okLo = Math.abs(dLo) <= TOL, okHi = useHi && Math.abs(dHi) <= TOL;
      const via = lo === 'l' ? 'edge_left_right' : 'edge_top_bottom';
      const sk1 = skipped('position', `khoảng cách tới cạnh ${nameLo}`), sk2 = skipped('position', `khoảng cách tới cạnh ${nameHi}`);
      if (sk1 && (!useHi || sk2)) { skp('position', `skip trong pairs: vị trí (${nameLo}${useHi ? '/' + nameHi : ''})`); return; }
      if (okLo || okHi || sym) { pass('position', via); return; }
      const useLo = !useHi || Math.abs(dLo) <= Math.abs(dHi);
      const k = useLo ? lo : hi, d = useLo ? dLo : dHi;
      add('position', `khoảng cách tới cạnh ${useLo ? nameLo : nameHi} của khối cha`,
        round2(fg[k]), round2(dg[k]), d, pp ? `đo trong khối "${parentLabel}"` : 'đo trong khung trang', via);
    };
    axis('l', 'r', 'trái', 'phải', true);
    if (!prev) axis('t', 'b', 'trên', 'dưới', !!pp);   // khung trang: chiều cao khác nhau, chỉ so cạnh trên

    // --- style và chữ. `styleFetched` của node Figma (xem figma_meta.mjs):
    //   true  => style đã lấy; thuộc tính vắng là giá trị mặc định (không viền, nền trong suốt, bo góc 0, độ mờ 1);
    //   false => chưa lấy style, mọi phép về style là not_comparable.
    // File cũ chưa có cờ: coi là đã lấy nếu node có `style`, và chỉ so các khoá có điền (không áp giá trị mặc định).
    const fs_ = fn.style || {}, ds = dn.style || {};
    const explicit = fn.styleFetched === true;
    const fetched = fn.styleFetched ?? !!fn.style;
    const isText = fn.type === 'text';
    const NOFETCH = 'Figma chưa lấy style của node này (styleFetched=false)';
    const NOKEY = 'Figma không ghi thuộc tính này' + (explicit ? '' : ' (dữ liệu cũ, chưa có styleFetched)');
    const NOWEB = 'web không có giá trị đo được';
    const dflt = (key, v) => (fs_[key] !== undefined ? fs_[key] : explicit ? v : undefined);

    const colorCmp = (check, prop, fv, dv) => {
      const cf = parseColor(fv), cd = parseColor(dv);
      if (!cf) return nc(check, `không đọc được màu Figma "${fv}"`);
      if (!cd) return nc(check, NOWEB);
      if (cf[3] <= OTOL && cd[3] <= OTOL) return cmp('style', prop, false);   // cả hai trong suốt: không có màu để so
      const worst = Math.max(Math.abs(cf[0] - cd[0]), Math.abs(cf[1] - cd[1]), Math.abs(cf[2] - cd[2]));
      const da = Math.abs(cf[3] - cd[3]);
      cmp('style', prop, worst > CTOL || da > OTOL, toHex(cf), toHex(cd), worst, da > OTOL ? `độ trong suốt lệch ${round2(da)}` : '');
    };
    const numCmp = (prop, fv, dv, tol) => {
      if (dv === undefined || dv === null) return nc(checkOf('style', prop), NOWEB);
      cmp('style', prop, Math.abs(fv - dv) > tol, fv, dv, dv - fv);
    };

    if (p.dom == null) {
      for (const c of [...STYLE_CHECKS, 'text_content']) nc(c, 'khối ảo (domBox) không có phần tử web để đo style hoặc chữ');
    } else if (sk.has('style')) {
      for (const c of STYLE_CHECKS) skp(c, 'skip trong pairs: style');
    } else {
      // Node chữ của Figma không có nền, viền, bo góc, đệm riêng (thuộc khung chứa nó); phần tử web bọc chữ có thể có, nhưng đó không phải thuộc tính của node chữ.
      const TEXT_NODE_NA = 'node chữ của Figma không có thuộc tính này (thuộc khung chứa nó)';
      if (isText) { for (const c of ['background', 'border', 'radius', 'padding']) na(c, TEXT_NODE_NA); }
      // nền
      if (isText) {}
      else if (!fetched) nc('background', NOFETCH);
      else { const fv = dflt('bg', 'transparent'); if (fv === undefined) nc('background', NOKEY); else colorCmp('background', 'màu nền', fv, ds.bg); }
      // viền
      if (isText) {}
      else if (!fetched) nc('border', NOFETCH);
      else {
        const w = dflt('borderWidth', 0), c = fs_.borderColor;
        if (w === undefined && c === undefined) nc('border', NOKEY);
        else {
          if (w !== undefined) numCmp('độ dày viền', w, ds.borderWidth, 0.5);   // có viền (1) hay không (0) là khác biệt thật
          if (c !== undefined && (w ?? 1) > 0) colorCmp('border', 'màu viền', c, ds.borderColor);
          else if (c === undefined && w > 0) nc('border', 'Figma có viền nhưng không ghi màu viền');
        }
      }
      // bo góc
      if (isText) {}
      else if (!fetched) nc('radius', NOFETCH);
      else {
        const fv = dflt('radius', 0);
        if (fv === undefined) nc('radius', NOKEY);
        else if (ds.radius === undefined || ds.radius === null) nc('radius', NOWEB);
        else {
          const rf = normRadius(fv, fb.w, fb.h), rd = normRadius(ds.radius, db.w, db.h);
          cmp('style', 'bo góc', rf !== rd && !(typeof rf === 'number' && typeof rd === 'number' && Math.abs(rf - rd) <= TOL), rf, rd);
        }
      }
      // độ mờ
      if (!fetched) nc('opacity', NOFETCH);
      else { const fv = dflt('opacity', 1); if (fv === undefined) nc('opacity', NOKEY); else numCmp('độ mờ', fv, ds.opacity, OTOL); }
      // đệm: chỉ có khi node Figma dùng auto layout
      if (isText) {}
      else if (!fetched) nc('padding', NOFETCH);
      else if (!fs_.padding) na('padding', 'node Figma không dùng auto layout, không có đệm để so');
      else if (!ds.padding) nc('padding', NOWEB);
      else ['trên', 'phải', 'dưới', 'trái'].forEach((side, k) => numCmp(`đệm ${side}`, fs_.padding[k], ds.padding[k], TOL));
      // chữ: màu, cỡ, đậm. Style chữ lấy từ chính node nếu nó là chữ hoặc có khoá chữ; nếu là khung thì từ đúng MỘT node chữ
      // trong cây con chưa có cặp riêng (nhiều hơn một thì không so được, không tự chọn).
      const TEXT_KEYS = ['color', 'fontSize', 'lineHeight', 'fontFamily', 'fontWeight'];
      let tsNode = fn, tsStyle = fs_, tsFetched = fetched, tsMulti = 0;
      if (!isText && !TEXT_KEYS.some(k => fs_[k] !== undefined)) {
        const { own, covered } = subtreeTexts(p.figma);
        // chỉ lấy khi cây con có đúng MỘT node chữ: nếu còn node chữ khác đã ghép riêng thì style chữ của phần tử bọc không đại diện cho một node
        if (own.length === 1 && !covered.length) { tsNode = own[0]; tsStyle = own[0].style || {}; tsFetched = own[0].styleFetched ?? !!own[0].style; }
        else if (own.length + covered.length > 1) tsMulti = own.length + covered.length;
      }
      const hasAny = (...keys) => keys.some(k => tsStyle[k] !== undefined);
      const mark = (checks) => { if (tsNode !== fn) for (const e of ev) if (checks.includes(e.check) && !e.source_text_node) e.source_text_node = tsNode.id; };
      const tgate = check => {
        if (tsMulti) { na(check, `khung chứa ${tsMulti} node chữ: màu, cỡ, độ đậm thuộc từng chữ, không thuộc khung (ghép riêng từng chữ nếu cần so)`); return false; }
        if (!(isText || tsNode !== fn || TEXT_KEYS.some(k => fs_[k] !== undefined))) { na(check, 'node Figma không phải chữ và không có node chữ con duy nhất'); return false; }
        if (!tsFetched) { nc(check, NOFETCH); return false; }
        return true;
      };
      if (tgate('text_color')) {
        if (tsStyle.color === undefined) nc('text_color', NOKEY); else colorCmp('text_color', 'màu chữ', tsStyle.color, ds.color);
      }
      if (tgate('font_size')) {
        if (!hasAny('fontSize', 'lineHeight', 'fontFamily')) nc('font_size', NOKEY);
        else {
          if (tsStyle.fontSize !== undefined) numCmp('cỡ chữ', tsStyle.fontSize, ds.fontSize, 0.5);
          if (tsStyle.lineHeight !== undefined) numCmp('chiều cao dòng', tsStyle.lineHeight, ds.lineHeight, 0.5);
          if (tsStyle.fontFamily && ds.fontFamily) cmp('style', 'font', tsStyle.fontFamily.toLowerCase() !== ds.fontFamily.toLowerCase(), tsStyle.fontFamily, ds.fontFamily);
        }
      }
      if (tgate('font_weight')) {
        if (tsStyle.fontWeight === undefined) nc('font_weight', NOKEY); else numCmp('độ đậm chữ', tsStyle.fontWeight, ds.fontWeight, 0);
      }
      mark(['text_color', 'font_size', 'font_weight']);
    }

    // --- chữ cố định: chỉ so khi AI đánh dấu `checkText`.
    // Chữ lấy từ chính node Figma nếu nó là Text; nếu là khung thì từ đúng MỘT node Text trong cây con chưa có cặp riêng.
    if (p.dom != null) {
      const textCmp = (ft, label_) => {
        if (ft.text === undefined || ft.text === null) return nc('text_content', `node chữ Figma ${ft.id} chưa có nội dung (text); cần điền khi lấy dữ liệu Figma`);
        const wt = webText(dn);
        if (!wt) return nc('text_content', 'phần tử web không có chữ đo được (chữ có thể nằm trong ảnh)');
        const bad = normText(ft.text) !== wt;
        const note = ft.id !== fn.id ? `chữ lấy từ node Figma ${ft.id} (${label_})` : '';
        if (bad) { add('text', 'chữ', ft.text, dn.text || wt, undefined, note); const last = ev[ev.length - 1]; if (last?.status === 'mismatch') last.source_text_node = ft.id; }
        else ev.push({ check: 'text_content', status: 'passed', expected: ft.text, actual: dn.text || wt, source_text_node: ft.id });
      };
      if (fn.text !== undefined) {
        if (skipped('text', 'chữ')) skp('text_content', 'skip trong pairs: text');
        else if (!p.checkText) skp('text_content', 'chữ có thể là dữ liệu động, AI chưa đánh dấu checkText');
        else textCmp(fn, 'chính node này');
      } else {
        const { own, covered } = subtreeTexts(p.figma);
        if (skipped('text', 'chữ')) skp('text_content', 'skip trong pairs: text');
        else if (!own.length && !covered.length) {
          if (p.checkText) nc('text_content', 'đã đánh dấu checkText nhưng không tìm thấy node chữ trong cây con Figma');
          else na('text_content', 'node và cây con Figma không có chữ');
        }
        else if (!p.checkText) skp('text_content', 'chữ có thể là dữ liệu động, AI chưa đánh dấu checkText');
        else if (own.length === 0) skp('text_content', 'chữ được so ở cặp con');
        else if (own.length > 1) nc('text_content', `có ${own.length} node chữ trong cây con Figma chưa ghép riêng (${own.map(t => t.id).join(', ')}), không tự chọn; ghép riêng từng chữ để so`);
        else textCmp(own[0], own[0].name);
      }
    }
  }

  // Cặp không chạy được phép so nào (thiếu item, thừa item, id sai): mọi loại là not_comparable.
  if (!ev.length) {
    const why = p.figma && !hasDom(p) ? 'web không có phần tử tương ứng (xem findings: thiếu item)'
      : !p.figma ? 'design không có phần tử tương ứng (xem findings: thừa item)' : 'id Figma hoặc web không có trong file dữ liệu';
    for (const c of CHECKS) nc(c, why);
  }

  // Đệm trên/dưới (trái/phải) lệch cùng lúc với cao (rộng) thường là cùng một nguyên nhân (chiều cao/rộng cố định).
  for (const f of mine) {
    if (f.group !== 'style' || !/^đệm /.test(f.prop)) continue;
    const dim = /trên|dưới/.test(f.prop) ? 'cao' : 'rộng';
    if (mine.some(g => g.group === 'size' && g.prop === dim)) f.detail = (f.detail ? f.detail + '; ' : '') + `có thể là nguyên nhân của lệch ${dim} ở trên`;
  }

  const checks = summarizeChecks(ev);
  const low = base.match === 'thấp';
  pairResults.push({ figma: base.figma, dom: base.dom, role: base.role, level: base.level, match: base.match, ...(low ? { uncertain: true } : {}), checks });
  if (low) { if (mine.length || inh.length) uncertain.push(...mine, ...inh); }
  else {
    findings.push(...mine); inherited.push(...inh);
    if (!mine.length && !inh.length && p.figma && hasDom(p)) {
      ok.push(p.figma);
      if (CHECKS.every(c => ['passed', 'not_applicable'].includes(checks[c].status))) okComplete.push(p.figma);
    }
  }
}

// ---- tổng hợp và tự kiểm tra checks <-> findings
const summary = {}, summaryInherited = {};
for (const c of CHECKS) summary[c] = { passed: 0, mismatch: 0, mismatch_inherited: 0, not_comparable: 0, skipped: 0, not_applicable: 0 };
let lowPairs = 0;
for (const r of pairResults) {
  if (r.uncertain) { lowPairs++; continue; }
  for (const c of CHECKS) {
    const k = r.checks[c];
    if (k.status === 'mismatch') summary[c][k.inherited ? 'mismatch_inherited' : 'mismatch']++;
    else summary[c][k.status]++;
  }
}
const itemsOf = (rs, wantInherited) => {
  let n = 0;
  for (const r of rs) for (const c of CHECKS) {
    const k = r.checks[c];
    if (k.status === 'mismatch') for (const it of k.items) if (wantInherited === undefined || it.inherited === wantInherited) n++;
  }
  return n;
};
const checkable = g => ['size', 'position', 'style', 'text'].includes(g);
const normalPairs = pairResults.filter(r => !r.uncertain), lowResults = pairResults.filter(r => r.uncertain);
const consistency = {
  findingsInChecks: itemsOf(normalPairs, false), findingsCount: findings.filter(f => checkable(f.group)).length,
  inheritedInChecks: itemsOf(normalPairs, true), inheritedCount: inherited.length,
  uncertainInChecks: itemsOf(lowResults), uncertainCount: uncertain.length,
};
consistency.ok = consistency.findingsInChecks === consistency.findingsCount && consistency.inheritedInChecks === consistency.inheritedCount &&
  consistency.uncertainInChecks === consistency.uncertainCount;
if (!consistency.ok) console.error('compare: CẢNH BÁO checks và findings không khớp: ' + JSON.stringify(consistency));

// ---- phạm vi phần tử: mỗi node Figma có đúng một trạng thái
const pairWarnings = [];
for (const e of excludes) if (!e.figmaNodes && !e.domNodes) pairWarnings.push(`exclude[${e.index}] không khớp phần tử nào (${e.reason}); kiểm tra lại id hoặc "keep"`);
for (const e of excludes) if ((e.figmaChildrenOf && !e.figmaNodes) || (e.domChildrenOf != null && !e.domNodes)) pairWarnings.push(`exclude[${e.index}] một phía không loại được phần tử nào (có thể phía đó không có hàng vượt "keep")`);
const pairOfFigma = new Map(pairs.filter(x => x.figma).map(x => [x.figma, x]));
const textSources = new Set(pairResults.flatMap(r => { const t = r.checks.text_content; return t.source_text_node ? [t.source_text_node] : []; }));
const figStatus = { matched: 0, uncertain: 0, missing_on_web: 0, text_via_parent: 0, excluded: 0, unmatched_figma: 0 };
const unmatchedFigma = [];
for (const n of figma.nodes) {
  const pr = pairOfFigma.get(n.id);
  if (exFigma.has(n.id)) { figStatus.excluded++; if (pr) pairWarnings.push(`Node Figma ${n.id} vừa nằm trong exclude[${exFigma.get(n.id)}] vừa có cặp ghép`); }
  else if (pr && hasDom(pr)) figStatus[(pr.match || 'cao') === 'thấp' ? 'uncertain' : 'matched']++;
  else if (pr) figStatus.missing_on_web++;
  else if (textSources.has(n.id)) figStatus.text_via_parent++;
  else { figStatus.unmatched_figma++; unmatchedFigma.push({ id: n.id, name: n.name, type: n.type, parent: n.parent }); }
}
const pairedDom = new Set(pairs.filter(x => x.dom != null).map(x => x.dom));
for (const x of pairs) if (x.dom != null && exDom.has(x.dom)) pairWarnings.push(`Phần tử web ${x.dom} vừa nằm trong exclude[${exDom.get(x.dom)}] vừa có cặp ghép`);
const extraOnWeb = pairs.filter(x => !x.figma && x.dom != null).length;

// ---- ứng viên khối web chưa ghép (chỉ là ứng viên cần xác minh, KHÔNG phải kết luận "thừa item")
// Điều kiện: nằm trong cây con của một phần tử đã ghép; đủ lớn; chưa ghép; không bị exclude; không phải tổ tiên của
// phần tử đã ghép; không phải lớp bọc trùng khung với cha; không nằm trong một ứng viên khác (chỉ lấy khối ngoài cùng).
const ancestorsOfPaired = new Set();
for (const i of pairedDom) for (let c = D.get(i); c && c.parent >= 0; c = D.get(c.parent)) ancestorsOfPaired.add(c.parent);
const sameBox = (u, v) => Math.abs(u.x - v.x) <= 1 && Math.abs(u.y - v.y) <= 1 && Math.abs(u.w - v.w) <= 1 && Math.abs(u.h - v.h) <= 1;
const candSet = new Set(), cands = [];
for (const n of dom.nodes) {
  if (pairedDom.has(n.i) || exDom.has(n.i) || ancestorsOfPaired.has(n.i)) continue;
  if (n.w < CAND_W || n.h < CAND_H) continue;
  let pairedAnc = null, insideCand = false;
  for (let c = D.get(n.parent); c; c = c.parent >= 0 ? D.get(c.parent) : null) {
    if (candSet.has(c.i)) { insideCand = true; break; }
    if (!pairedAnc && pairedDom.has(c.i)) pairedAnc = c.i;
  }
  if (insideCand || pairedAnc === null) continue;
  const par = D.get(n.parent);
  if (par && sameBox(n, par)) continue;
  candSet.add(n.i);
  const pp_ = pairs.find(x => x.dom === pairedAnc);
  cands.push({ dom: n.i, parentDom: n.parent, tag: n.tag, x: n.x, y: n.y, w: n.w, h: n.h, text: String(n.text || '').trim().slice(0, 40),
    pairedAncestor: { dom: pairedAnc, figma: pp_?.figma ?? null, role: pp_?.role || '' } });
}
const groups = new Map();
for (const c of cands) {
  const key = `${c.tag}|${Math.round(c.w)}x${Math.round(c.h)}`;
  if (!groups.has(key)) groups.set(key, { key, tag: c.tag, size: [Math.round(c.w), Math.round(c.h)], count: 0, members: [] });
  const g = groups.get(key); g.count++; g.members.push(c);
}
const candidateGroups = [...groups.values()].sort((u, v) => u.members[0].y - v.members[0].y);

const out = {
  meta: { tolerance: TOL, colorTolerance: CTOL, opacityTolerance: OTOL, pairs: pairs.length,
    figmaFrame: figma.frame, page: dom.page, checkTypes: CHECKS, summary, uncertainPairs: lowPairs, consistency,
    candidateThreshold: { minWidth: CAND_W, minHeight: CAND_H } },
  elements: { figma: { total: figma.nodes.length, ...figStatus }, extra_on_web: extraOnWeb, unmatchedFigma, excluded: excludes, warnings: pairWarnings },
  unmatchedDomCandidates: { note: 'Ứng viên cần xác minh, chưa phải kết luận thừa item', total: cands.length, groups: candidateGroups },
  findings, inherited, uncertain, ok, okComplete, pairs: pairResults,
};
fs.writeFileSync(a.out, JSON.stringify(out, null, 1));
const by = {};
for (const f of findings) by[f.group] = (by[f.group] || 0) + 1;
console.log(`compare: ${pairs.length} cặp | khớp ${ok.length} (đủ mọi phép ${okComplete.length}) | nghi lệch ${findings.length} ` +
  `${JSON.stringify(by)} | kế thừa từ cha ${inherited.length} | cặp ghép thấp ${uncertain.length} | nhất quán checks/findings: ${consistency.ok ? 'OK' : 'LỖI'}\n  phần tử Figma ${JSON.stringify(figStatus)} | ứng viên web chưa ghép ${cands.length} (${candidateGroups.length} nhóm)${pairWarnings.length ? ' | CẢNH BÁO: ' + pairWarnings.length : ''}\n  -> ${a.out}`);
