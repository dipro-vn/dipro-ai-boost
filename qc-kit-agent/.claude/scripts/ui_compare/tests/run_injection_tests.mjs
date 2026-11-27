#!/usr/bin/env node
// Bộ kiểm thử có chủ đích cho /ui-compare: tiêm 6 sai lệch giả lập vào trang web (chỉ trong trình duyệt đang đo, không đụng
// vào site thật), chạy lại dom_extract + compare, rồi kiểm 3 điều:
//   1) có phát hiện đúng sai lệch đã tiêm không;
//   2) có báo nhầm phần tử không thay đổi không (mọi thay đổi khác so với bản gốc đều phải được giải thích);
//   3) có chỉ đúng nguyên nhân gốc không (TC-01: các khối con rộng hơn phải nằm ở `inherited`, không thành nghi bug riêng).
//
// Dùng:
//   node tests/run_injection_tests.mjs --url <URL> --figma figma-1440.json --pairs pairs-1440.json --pairs-dom dom-1440.json \
//        --out inject-test [--width 1440] [--only tc01,tc03]
// --pairs-dom: file DOM mà `pairs` đang trỏ chỉ số tới (bản đo trước khi tiêm lỗi).
// Ra: <out>/summary.json, <out>/summary.md, và dom/pairs/result của từng ca.
import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';
import { parseArgs, need, readJson, splitPairs } from '../lib.mjs';

const a = parseArgs(process.argv);
need(a, ['url', 'figma', 'pairs', 'pairs-dom', 'out']);
const U = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const W = a.width || '1440';
fs.mkdirSync(a.out, { recursive: true });

const run = (script, args) => {
  const r = spawnSync('node', [path.join(U, script), ...args], { encoding: 'utf8' });
  if (r.status !== 0) { console.error(`${script} lỗi (mã ${r.status}):\n${r.stdout}\n${r.stderr}`); process.exit(1); }
  return r.stdout;
};

// ---- 6 sai lệch. Mỗi đoạn JS chạy trong trang; không tìm thấy phần tử thì báo lỗi to (không bỏ qua im lặng).
const DEFECTS = {
  tc01: { title: 'Menu bên trái rộng hơn 10px (210 → 220)', js: `
    const e = [...document.querySelectorAll('div')].find(d => { const b = d.getBoundingClientRect(); return Math.round(b.width) === 210 && Math.round(b.x) === 0 && Math.round(b.y) === 0; });
    if (!e) throw new Error('tc01: không tìm thấy menu');
    for (const [k, v] of [['width', '220px'], ['min-width', '220px'], ['flex', 'none']]) e.style.setProperty(k, v, 'important');` },
  tc02: { title: 'Nút (combobox 表示件数) lệch phải 3px', js: `
    const e = document.querySelector('button[role="combobox"][aria-label="表示件数"]');
    if (!e) throw new Error('tc02: không tìm thấy combobox');
    e.style.setProperty('position', 'relative', 'important'); e.style.setProperty('left', '3px', 'important');` },
  tc03: { title: 'Nút bulk thấp hơn 2px (36 → 34)', js: `
    const e = [...document.querySelectorAll('button')].find(b => b.textContent.includes('一括スカウト'));
    if (!e) throw new Error('tc03: không tìm thấy nút bulk');
    e.style.setProperty('height', '34px', 'important'); e.style.setProperty('min-height', '34px', 'important');` },
  tc04: { title: 'Chữ mã ID đổi màu từ #424242 sang #9e9e9e', js: `
    const e = [...document.querySelectorAll('span')].find(s => /^DR-/.test(s.textContent.trim()) && s.children.length === 0);
    if (!e) throw new Error('tc04: không tìm thấy mã ID');
    e.style.setProperty('color', '#9e9e9e', 'important');` },
  tc05: { title: 'Checkbox hàng 1 bo góc thêm 4px (4 → 8)', js: `
    const e = document.querySelector('tbody tr button[role="checkbox"]');   // checkbox của hàng 1 (không phải checkbox ở dòng tiêu đề)
    if (!e) throw new Error('tc05: không tìm thấy checkbox');
    e.style.setProperty('border-radius', '8px', 'important');` },
  tc06: { title: 'Ẩn icon mũi tên của thanh lọc', js: `
    const b = [...document.querySelectorAll('button')].find(x => x.textContent.includes('絞り込み条件'));
    const s = b && b.querySelector('svg');
    if (!s) throw new Error('tc06: không tìm thấy icon');
    s.style.setProperty('display', 'none', 'important');` },
};

// ---- kỳ vọng: `must` là điều bắt buộc phải thấy; `allowed` là hệ quả được giải thích (mọi thay đổi khác là báo nhầm)
const num = (v, t, tol = 1) => typeof v === 'number' && Math.abs(v - t) <= tol;
const EXPECT = {
  tc01: { must: e => e.figma === '5532:44111' && e.group === 'size' && e.prop === 'rộng' && num(e.actual, 220),
    allowed: [{ why: 'khối con rộng hơn/hẹp hơn theo menu (hệ quả của lệch rộng của menu)', fn: e => ['size', 'position'].includes(e.group) }] },
  tc02: { must: e => e.role === 'combobox 表示件数' && e.group === 'position' && num(Math.abs(e.delta), 3, 1), allowed: [] },
  tc03: { must: e => e.role.startsWith('nút bulk') && e.group === 'size' && e.prop === 'cao' && num(e.actual, 34), allowed: [] },
  tc04: { must: e => e.role === 'mã ID hàng 1' && e.group === 'style' && e.prop === 'màu chữ' && String(e.actual).toLowerCase() === '#9e9e9e', allowed: [] },
  tc05: { must: e => e.role === 'checkbox hàng 1' && e.group === 'style' && e.prop === 'bo góc' && (num(e.actual, 8) || e.actual === 'tròn'), allowed: [] },   // 8px trên khối 16x16 là hình tròn: script báo "tròn"
  tc06: { must: e => e.role === 'icon mũi tên thanh lọc' && e.group === 'missing', allowed: [] },
};

const entriesOf = res => [
  ...res.findings.map(x => ({ ...x, cat: 'findings' })),
  ...res.inherited.map(x => ({ ...x, cat: 'inherited' })),
  ...res.uncertain.map(x => ({ ...x, cat: 'uncertain' })),
];
const keyOf = e => `${e.figma}|${e.group}|${e.prop}`;
function diffResults(base, inj) {
  const B = new Map(entriesOf(base).map(e => [keyOf(e), e])), I = new Map(entriesOf(inj).map(e => [keyOf(e), e]));
  const added = [], removed = [], changed = [];
  for (const [k, e] of I) {
    const b = B.get(k);
    if (!b) added.push(e);
    else if (b.cat !== e.cat || String(b.actual) !== String(e.actual) || String(b.expected) !== String(e.expected)) changed.push({ before: b, after: e });
  }
  for (const [k, e] of B) if (!I.has(k)) removed.push(e);
  return { added, removed, changed };
}

// ---- ghép lại `pairs` sau khi đo lại: theo uid (số thứ tự trong cây tài liệu), phần tử bị ẩn thì `dom: null`
function remapPairs(raw, baseDom, injDom) {
  const { pairs, excludeSpec } = splitPairs(raw);
  const uidOf = new Map(baseDom.nodes.map(n => [n.i, n.uid])), idxOf = new Map(injDom.nodes.map(n => [n.uid, n.i]));
  const map = i => (i == null ? i : idxOf.has(uidOf.get(i)) ? idxOf.get(uidOf.get(i)) : null);
  const hidden = [];
  const np = pairs.map(p => {
    if (p.dom == null) return p.domBox && p.domBox.of != null ? { ...p, domBox: { ...p.domBox, of: map(p.domBox.of) } } : p;
    const m = map(p.dom);
    if (m === null) hidden.push({ figma: p.figma, role: p.role });
    return { ...p, dom: m, ...(m === null ? { note: 'phần tử web không còn thấy sau khi đo lại' } : {}) };
  });
  const ex = excludeSpec.map(e => ({ ...e, ...(e.dom != null ? { dom: [].concat(e.dom).map(map).filter(x => x !== null) } : {}), ...(e.domChildrenOf != null ? { domChildrenOf: map(e.domChildrenOf) } : {}) }));
  return { pairs: { pairs: np, exclude: ex }, hidden };
}

// ---- bản gốc: đo lại web (có uid) và kiểm `pairs` còn trỏ đúng
const pairsRaw = readJson(a.pairs), pairsDom = readJson(a['pairs-dom']);
const base = path.join(a.out, 'base');
fs.mkdirSync(base, { recursive: true });
run('dom_extract.mjs', ['--url', a.url, '--width', W, '--out', path.join(base, 'dom.json')]);
const baseDom = readJson(path.join(base, 'dom.json'));
{
  const A = new Map(pairsDom.nodes.map(n => [n.i, n])), B = new Map(baseDom.nodes.map(n => [n.i, n]));
  const bad = splitPairs(pairsRaw).pairs.filter(p => p.dom != null && !(B.get(p.dom) && A.get(p.dom).tag === B.get(p.dom).tag &&
    ['x', 'y', 'w', 'h'].every(k => Math.abs(A.get(p.dom)[k] - B.get(p.dom)[k]) <= 1)));
  if (bad.length) { console.error(`Bản đo gốc khác bản \`pairs\` đang trỏ tới (${bad.length} cặp): ${bad.map(p => p.role).join(', ')}. Ghép lại cặp trước khi kiểm thử.`); process.exit(1); }
}
fs.writeFileSync(path.join(base, 'pairs.json'), JSON.stringify(pairsRaw, null, 1));
run('compare.mjs', ['--figma', a.figma, '--dom', path.join(base, 'dom.json'), '--pairs', path.join(base, 'pairs.json'), '--out', path.join(base, 'result.json')]);
const baseRes = readJson(path.join(base, 'result.json'));

// ---- từng ca và ca gộp
const ids = a.only ? String(a.only).split(',') : [...Object.keys(DEFECTS), 'all'];
const results = [];
for (const id of ids) {
  const dir = path.join(a.out, id);
  fs.mkdirSync(dir, { recursive: true });
  const parts = id === 'all' ? Object.keys(DEFECTS) : [id];
  fs.writeFileSync(path.join(dir, 'inject.js'), '(() => {\n' + parts.map(k => `(() => {${DEFECTS[k].js}})();`).join('\n') + '\n})()');
  run('dom_extract.mjs', ['--url', a.url, '--width', W, '--out', path.join(dir, 'dom.json'), '--eval', path.join(dir, 'inject.js')]);
  const injDom = readJson(path.join(dir, 'dom.json'));
  const { pairs, hidden } = remapPairs(pairsRaw, baseDom, injDom);
  fs.writeFileSync(path.join(dir, 'pairs.json'), JSON.stringify(pairs, null, 1));
  run('compare.mjs', ['--figma', a.figma, '--dom', path.join(dir, 'dom.json'), '--pairs', path.join(dir, 'pairs.json'), '--out', path.join(dir, 'result.json')]);
  const res = readJson(path.join(dir, 'result.json'));
  const d = diffResults(baseRes, res);
  const changes = [...d.added.map(e => ({ kind: 'mới', e })), ...d.changed.map(c => ({ kind: 'đổi', e: c.after, before: c.before })), ...d.removed.map(e => ({ kind: 'mất', e }))];
  const mustFns = parts.map(k => ({ id: k, fn: EXPECT[k].must }));
  const allowed = parts.flatMap(k => EXPECT[k].allowed);
  const entries = entriesOf(res);
  const detected = mustFns.map(m => ({ id: m.id, title: DEFECTS[m.id].title, found: entries.find(m.fn) || null }));
  const matchedMust = new Set(detected.map(x => x.found && keyOf(x.found)).filter(Boolean));
  // báo nhầm = thay đổi so với bản gốc mà không phải lỗi đã tiêm và không thuộc hệ quả được giải thích
  const falsePos = changes.filter(c => !(matchedMust.has(keyOf(c.e)) || allowed.some(al => al.fn(c.e))));
  const explained = changes.filter(c => !matchedMust.has(keyOf(c.e)) && allowed.some(al => al.fn(c.e)));
  // nguyên nhân gốc (TC-01): các khối con đổi chiều rộng phải nằm ở `inherited`, không thành nghi bug riêng
  let rootCause = null;
  if (parts.includes('tc01')) {
    const kids = changes.filter(c => c.e.group === 'size' && c.e.prop === 'rộng' && c.e.figma !== '5532:44111' && c.e.role !== 'cột nội dung');
    // so với baseline: khối con từng được gom vào `inherited` mà giờ thành nghi bug riêng là mất gom nguyên nhân gốc
    const flipped = kids.filter(c => c.before && c.before.cat === 'inherited' && c.e.cat === 'findings');
    rootCause = { childWidthChanges: kids.length, asInherited: kids.filter(c => c.e.cat === 'inherited').length, asFinding: kids.filter(c => c.e.cat === 'findings').length,
      flippedToFinding: flipped.map(c => c.e.role) };
  }
  results.push({ id, title: id === 'all' ? 'Cả 6 lỗi cùng lúc' : DEFECTS[id].title, hidden, detected: detected.map(x => ({ id: x.id, title: x.title, ok: !!x.found, finding: x.found && { role: x.found.role, group: x.found.group, prop: x.found.prop, expected: x.found.expected, actual: x.found.actual, delta: x.found.delta, cat: x.found.cat } })),
    changes: changes.length, explained: explained.map(c => ({ kind: c.kind, role: c.e.role, group: c.e.group, prop: c.e.prop, before: c.before ? { actual: c.before.actual, cat: c.before.cat } : null, after: { actual: c.e.actual, cat: c.e.cat } })),
    falsePositives: falsePos.map(c => ({ kind: c.kind, role: c.e.role, group: c.e.group, prop: c.e.prop, before: c.before ? { actual: c.before.actual, cat: c.before.cat } : null, after: { actual: c.e.actual, cat: c.e.cat } })), rootCause });
}

fs.writeFileSync(path.join(a.out, 'summary.json'), JSON.stringify({ url: a.url, baseline: { findings: baseRes.findings.length, inherited: baseRes.inherited.length }, results }, null, 1));
const L = ['# Kiểm thử bộ so sánh bằng 6 sai lệch có chủ đích', '', `Baseline: ${baseRes.findings.length} nghi lệch, ${baseRes.inherited.length} lệch do cha. Mỗi ca tiêm lỗi vào trình duyệt khi đo (không đụng vào site thật) rồi so với baseline.`, '',
  '| Ca | Sai lệch đã tiêm | Phát hiện | Báo nhầm | Hệ quả được giải thích |', '|---|---|---|---|---|'];
for (const r of results) L.push(`| ${r.id} | ${r.title} | ${r.detected.filter(x => x.ok).length}/${r.detected.length} | ${r.falsePositives.length} | ${r.explained.length} |`);
L.push('');
for (const r of results) {
  L.push(`## ${r.id}: ${r.title}`, '');
  for (const d of r.detected) L.push(`- ${d.ok ? '✔' : '✘'} ${d.title}${d.finding ? `: ${d.finding.group}/${d.finding.prop} của "${d.finding.role}", design ${d.finding.expected}, thực tế ${d.finding.actual}${d.finding.delta != null ? ` (chênh ${d.finding.delta})` : ''}` : ': KHÔNG phát hiện'}`);
  if (r.hidden.length) L.push(`- Phần tử không còn thấy sau khi ẩn (ghép lại thành \`dom: null\`): ${r.hidden.map(h => h.role).join(', ')}`);
  if (r.rootCause) {
    L.push(`- Nguyên nhân gốc: ${r.rootCause.childWidthChanges} khối con đổi chiều rộng; ${r.rootCause.asInherited} nằm ở \`inherited\`, ${r.rootCause.asFinding} là nghi bug riêng (phần lớn đã là nghi bug riêng ở baseline).`);
    if (r.rootCause.flippedToFinding.length) L.push(`- ⚠ GOM NGUYÊN NHÂN GỐC CHƯA ĐỦ: ${r.rootCause.flippedToFinding.length} khối con từ \`inherited\` thành nghi bug riêng (${r.rootCause.flippedToFinding.join(', ')}): các khối này chia đều chiều rộng của khối cha nên chênh lệch của chúng không bằng chênh lệch của cha.`);
  }
  for (const f of r.falsePositives) L.push(`- ⚠ BÁO NHẦM (${f.kind}): ${f.group}/${f.prop} của "${f.role}" ${f.before ? `${f.before.actual} → ` : ''}${f.after.actual}`);
  for (const f of r.explained) L.push(`- (hệ quả) ${f.kind}: ${f.group}/${f.prop} của "${f.role}" ${f.before ? `${f.before.actual} → ` : ''}${f.after.actual}`);
  L.push('');
}
fs.writeFileSync(path.join(a.out, 'summary.md'), L.join('\n'));
const miss = results.reduce((n, r) => n + r.detected.filter(x => !x.ok).length, 0), fp = results.reduce((n, r) => n + r.falsePositives.length, 0);
const warnRc = results.reduce((n, r) => n + (r.rootCause?.flippedToFinding.length || 0), 0);
console.log(`injection tests: ${results.length} ca | bỏ sót ${miss} | báo nhầm ${fp} | cảnh báo gom nguyên nhân gốc ${warnRc}\n  -> ${path.join(a.out, 'summary.md')}`);
if (miss || fp) process.exit(4);
