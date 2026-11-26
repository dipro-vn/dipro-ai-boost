// Hàm dùng chung cho các script ui_compare (xem skill `ui_compare`).
import { chromium } from 'playwright';
import fs from 'fs';
import os from 'os';
import path from 'path';

/** Đọc tham số dạng `--key value` hoặc `--flag`. */
export function parseArgs(argv) {
  const a = {};
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i];
    if (!k.startsWith('--')) continue;
    const n = argv[i + 1];
    if (n === undefined || n.startsWith('--')) a[k.slice(2)] = true;
    else { a[k.slice(2)] = n; i++; }
  }
  return a;
}

export function need(a, keys) {
  const miss = keys.filter(k => a[k] === undefined || a[k] === true);
  if (miss.length) { console.error('Thiếu tham số: ' + miss.map(k => '--' + k).join(', ')); process.exit(2); }
}

export const readJson = f => JSON.parse(fs.readFileSync(f, 'utf8'));
export const round2 = v => Math.round(v * 100) / 100;

// ---- Mở Chromium ---------------------------------------------------------
// Playwright mới có thể đòi bản Chromium mới hơn bản có trên máy. Nếu mở mặc định
// lỗi thì tìm bản Chromium đã cài sẵn trong cache của Playwright và dùng bản đó.
function cacheDirs() {
  const h = os.homedir();
  return [
    process.env.PLAYWRIGHT_BROWSERS_PATH,
    path.join(h, 'Library/Caches/ms-playwright'),
    path.join(h, '.cache/ms-playwright'),
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'ms-playwright'),
  ].filter(d => d && fs.existsSync(d));
}

function findFile(dir, names, depth) {
  if (depth < 0) return null;
  let ents;
  try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return null; }
  for (const e of ents) if (e.isFile() && names.has(e.name)) return path.join(dir, e.name);
  for (const e of ents) if (e.isDirectory()) { const r = findFile(path.join(dir, e.name), names, depth - 1); if (r) return r; }
  return null;
}

export async function launchBrowser() {
  let first;
  try { return await chromium.launch(); } catch (e) { first = e; }
  const names = new Set(['chrome-headless-shell', 'chrome-headless-shell.exe', 'Chromium', 'chrome', 'chrome.exe']);
  for (const prefix of ['chromium_headless_shell-', 'chromium-']) {
    for (const d of cacheDirs()) {
      const vers = fs.readdirSync(d).filter(n => n.startsWith(prefix))
        .sort((x, y) => parseInt(y.slice(prefix.length)) - parseInt(x.slice(prefix.length)));
      for (const v of vers) {
        const exe = findFile(path.join(d, v), names, 7);
        if (!exe) continue;
        try { return await chromium.launch({ executablePath: exe }); } catch { /* thử bản khác */ }
      }
    }
  }
  throw new Error('Không mở được Chromium. Chạy: cd .claude/scripts/ui_compare && node node_modules/playwright/cli.js install chromium\n' + first.message);
}

// ---- Màu -----------------------------------------------------------------
/** Trả [r,g,b,a] từ '#rgb', '#rrggbb', '#rrggbbaa', 'rgb(...)', 'rgba(...)'; null nếu không đọc được. */
export function parseColor(s) {
  if (s === undefined || s === null || s === '') return null;
  s = String(s).trim().toLowerCase();
  if (s === 'transparent') return [0, 0, 0, 0];
  let m = s.match(/^#([0-9a-f]{3,8})$/);
  if (m) {
    let h = m[1];
    if (h.length === 3 || h.length === 4) h = [...h].map(c => c + c).join('');
    if (h.length !== 6 && h.length !== 8) return null;
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16),
      h.length === 8 ? parseInt(h.slice(6, 8), 16) / 255 : 1];
  }
  m = s.match(/^rgba?\(([^)]+)\)$/);
  if (m) {
    const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(parseFloat);
    if (p.length < 3 || p.some(Number.isNaN)) return null;
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  }
  return null;
}

export function toHex([r, g, b, a]) {
  const h = v => Math.round(v).toString(16).padStart(2, '0');
  return '#' + h(r) + h(g) + h(b) + (a < 1 ? h(a * 255) : '');
}

// ---- pairs + exclude dùng chung cho compare.mjs và pixel_diff.mjs --------------
// `pairs-<size>.json` là mảng cặp (dạng cũ) hoặc {pairs:[...], exclude:[...]}.
export function splitPairs(raw) {
  return Array.isArray(raw) ? { pairs: raw, excludeSpec: [] } : { pairs: raw.pairs || [], excludeSpec: raw.exclude || [] };
}

/** Cây con theo cha: Map(parentId -> [node]). `key` là tên trường id ('id' cho Figma, 'i' cho web). */
export function kidsMap(nodes) {
  const m = new Map();
  for (const n of nodes) { if (!m.has(n.parent)) m.set(n.parent, []); m.get(n.parent).push(n); }
  return m;
}

/**
 * Mở rộng danh sách exclude thành tập id bị loại. Mỗi mục:
 * {figma?: id|[id], dom?: i|[i], figmaChildrenOf?: id, domChildrenOf?: i, keep?: n, scope?: "subtree"|"node", reason}
 * Trả {exFigma: Map(id->index), exDom: Map(i->index), excludes: [...], errors: [...]}.
 */
export function expandExcludes(excludeSpec, F, D, figKids, domKids) {
  const exFigma = new Map(), exDom = new Map(), excludes = [], errors = [];
  excludeSpec.forEach((e, k) => {
    const tag = `exclude[${k}]`;
    if (!e.reason || !String(e.reason).trim()) errors.push(`${tag}: thiếu "reason" (mọi phần tử bị loại khỏi phạm vi phải có lý do)`);
    const figIds = [].concat(e.figma ?? []), domIds = [].concat(e.dom ?? []);
    if (e.figmaChildrenOf) { if (!F.has(e.figmaChildrenOf)) errors.push(`${tag}: không có node Figma ${e.figmaChildrenOf}`); else figIds.push(...(figKids.get(e.figmaChildrenOf) || []).slice(e.keep ?? 0).map(n => n.id)); }
    if (e.domChildrenOf != null) { if (!D.has(e.domChildrenOf)) errors.push(`${tag}: không có phần tử web ${e.domChildrenOf}`); else domIds.push(...(domKids.get(e.domChildrenOf) || []).slice(e.keep ?? 0).map(n => n.i)); }
    for (const id of figIds) if (!F.has(id)) errors.push(`${tag}: không có node Figma ${id}`);
    for (const i of domIds) if (!D.has(i)) errors.push(`${tag}: không có phần tử web ${i}`);
    if (!figIds.length && !domIds.length && !(e.figmaChildrenOf || e.domChildrenOf != null)) errors.push(`${tag}: không trỏ tới phần tử nào`);
    const whole = (e.scope || 'subtree') === 'subtree';
    let nf = 0, nd = 0;
    const markF = id => { if (!exFigma.has(id)) { exFigma.set(id, k); nf++; } if (whole) for (const c of figKids.get(id) || []) markF(c.id); };
    const markD = i => { if (!exDom.has(i)) { exDom.set(i, k); nd++; } if (whole) for (const c of domKids.get(i) || []) markD(c.i); };
    figIds.filter(id => F.has(id)).forEach(markF); domIds.filter(i => D.has(i)).forEach(markD);
    excludes.push({ index: k, figma: figIds, dom: domIds, scope: e.scope || 'subtree', reason: e.reason || '', figmaNodes: nf, domNodes: nd,
      ...(e.figmaChildrenOf ? { figmaChildrenOf: e.figmaChildrenOf, keep: e.keep ?? 0 } : {}), ...(e.domChildrenOf != null ? { domChildrenOf: e.domChildrenOf, keep: e.keep ?? 0 } : {}) });
  });
  return { exFigma, exDom, excludes, errors };
}
