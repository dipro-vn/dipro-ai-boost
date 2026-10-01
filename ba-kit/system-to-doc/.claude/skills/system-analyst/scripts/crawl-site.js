#!/usr/bin/env node
/**
 * Recon website — CHE DO READ-ONLY LA MAC DINH.
 *
 *   node crawl-site.js --url https://stg.example.jp --site WEB-01 --out <ver>/_internal \
 *        [--mode read-only|submit-staging|submit-prod] [--max-urls 200] [--max-minutes 30] \
 *        [--storage-state <project>/.auth/WEB-01.json] [--role test_user] \
 *        [--forbid "/admin/batch,/payment"] [--ev-start 1] [--viewport 1440x900]
 *
 * Gate G2 duoc thuc thi o day, khong phai bang loi hua trong prompt:
 *   - read-only  : chan moi request khac GET/HEAD o tang network
 *   - moi mode   : chi di theo link cung origin, KHONG bam nut; bo qua link logout
 *                  (giet session) va link co tu khoa pha du lieu -> ghi vao blocked.json
 *
 * Output (--out = thu muc _internal/ cua version):
 *   evidence/EV-NNNN.png                 screenshot fullPage tung man
 *   recon/crawl/<site>/urls.txt          URL da tham, tru trang HTTP >= 400 (input cho verify-inventory.py --crawled)
 *   recon/crawl/<site>/pages.json        title · heading · form · header bang · item (KHONG luu gia tri input)
 *                                        trang HTTP >= 400: status + errorPage:true (giu screenshot lam bang chung bug)
 *   recon/crawl/<site>/styles.json       mau computed-style, tru trang loi (input cho extract-design-tokens.py)
 *   recon/crawl/<site>/ui-issues.json    loi do duoc (anh vo, tran ngang, cham, console, 4xx/5xx) -> Bug List
 *   recon/crawl/<site>/evidence.csv      dong san sang dan vao sheet 05_Evidence
 *   recon/crawl/<site>/console.json · network.json · blocked.json (bang chung Gate G9)
 * Stdout cuoi: JSON co next_ev de chain lan chay sau.
 */
const fs = require('fs');
const path = require('path');

const DESTRUCTIVE = [
  'delete', 'remove', 'destroy', 'xoa', 'xóa', '削除', '退会', 'withdraw',
  'pay', 'payment', 'checkout', 'purchase', 'thanh toan', 'thanh toán', '決済',
  'send mail', 'gui mail', 'gửi mail', '送信', 'submit order', 'confirm order',
];
const LOGOUT_RE = /log-?out|sign-?out|ログアウト|đăng xuất|dang xuat/i;
const EVIDENCE_HEADER = 'EV ID,Type,Locator,Captured At,Actor/Role,Artifact,Note';  // = S.SHEETS["05_Evidence"]
const SLOW_MS = 5000;

function arg(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  if (i === -1) return dflt;
  const v = process.argv[i + 1];
  return v && !v.startsWith('--') ? v : true;
}

function sameOrigin(a, b) {
  try { return new URL(a).origin === new URL(b).origin; } catch { return false; }
}

function normalize(u) {
  try {
    const x = new URL(u);
    x.hash = '';
    x.pathname = x.pathname.replace(/\/index\.(html?|php)$/i, '/');  // /index.html == /
    return x.toString().replace(/\/$/, '') || x.origin;
  } catch { return null; }
}

// tu khoa ASCII so theo ranh gioi tu (tranh "display" ~ "pay"); tu khoa unicode so substring
function destructiveHit(s) {
  const t = String(s || '').toLowerCase();
  return DESTRUCTIVE.find(k => /^[\x00-\x7f]+$/.test(k)
    ? new RegExp('(^|[^a-z])' + k.replace(/ /g, '[ _-]?') + '([^a-z]|$)').test(t)
    : t.includes(k)) || null;
}

function hrefPath(u) {
  try { const x = new URL(u); return decodeURIComponent(x.pathname + x.search); } catch { return String(u); }
}

(async () => {
  let chromium;
  try { ({ chromium } = require('playwright')); }
  catch { console.error('Thieu playwright. Chay: npm i -D playwright && npx playwright install chromium'); process.exit(2); }

  const start = arg('url');
  const site = arg('site');
  const out = arg('out', './_internal');
  const mode = arg('mode', 'read-only');
  const maxUrls = parseInt(arg('max-urls', '200'), 10);
  const maxMin = parseFloat(arg('max-minutes', '30'));
  const role = arg('role', 'anonymous');
  const storage = arg('storage-state', null);
  const forbid = String(arg('forbid', '')).split(',').map(s => s.trim()).filter(Boolean);
  const evStart = parseInt(arg('ev-start', '1'), 10);
  const vp = String(arg('viewport', '1440x900')).match(/^(\d+)x(\d+)$/);

  if (!start || start === true) { console.error('Thieu --url'); process.exit(1); }
  if (!site || !/^WEB-\d{2,}$/.test(String(site))) { console.error('Thieu/sai --site (vd WEB-01)'); process.exit(1); }
  if (!['read-only', 'submit-staging', 'submit-prod'].includes(mode)) {
    console.error('--mode phai la read-only | submit-staging | submit-prod'); process.exit(1);
  }
  if (!vp) { console.error('--viewport phai dang 1440x900'); process.exit(1); }
  if (!(evStart >= 1)) { console.error('--ev-start phai >= 1'); process.exit(1); }
  const viewport = { width: parseInt(vp[1], 10), height: parseInt(vp[2], 10) };

  const evDir = path.join(out, 'evidence');
  const crawlDir = path.join(out, 'recon', 'crawl', String(site));
  fs.mkdirSync(evDir, { recursive: true });
  fs.mkdirSync(crawlDir, { recursive: true });

  let browser;
  try { browser = await chromium.launch(); }
  catch (e) { console.error('Khong mo duoc chromium. Chay: npx playwright install chromium\n' + String(e).split('\n')[0]); process.exit(2); }
  const ctxOpts = { viewport, serviceWorkers: 'block' };   // SW co the vuot qua ctx.route
  if (storage) ctxOpts.storageState = storage;
  const ctx = await browser.newContext(ctxOpts);
  const page = await ctx.newPage();

  const consoleErrors = [], networkIssues = [], blocked = [];
  let curUrl = null;

  // --- Gate G2 thuc thi o tang network ---
  await ctx.route('**/*', route => {
    const req = route.request();
    const m = req.method();
    if (mode === 'read-only' && !['GET', 'HEAD'].includes(m)) {
      blocked.push({ kind: 'request', method: m, url: req.url(), page: curUrl, at: new Date().toISOString() });
      return route.abort();
    }
    return route.continue();
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push({ url: curUrl, text: msg.text().slice(0, 500), at: new Date().toISOString() });
    }
  });
  page.on('response', r => {
    if (r.status() >= 400) {
      networkIssues.push({ page: curUrl, url: r.url(), status: r.status(), at: new Date().toISOString() });
    }
  });

  const queue = [normalize(start)];
  const queued = new Set(queue);
  const seen = new Set(), pages = [], evidence = [], styles = [], uiIssues = [];
  const t0 = Date.now();
  let evNo = evStart - 1;

  while (queue.length && seen.size < maxUrls) {
    if ((Date.now() - t0) / 60000 > maxMin) { console.error('Het budget thoi gian'); break; }
    const url = queue.shift();
    if (!url || seen.has(url)) continue;
    if (forbid.some(f => url.includes(f))) { blocked.push({ kind: 'forbidden-zone', url }); continue; }
    seen.add(url);
    curUrl = url;

    let resp;
    const tNav = Date.now();
    try { resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 }); }
    catch (e) { networkIssues.push({ page: url, url, status: 'NAVIGATION_ERROR', detail: String(e).slice(0, 200) }); continue; }
    try { await page.waitForLoadState('load', { timeout: 15000 }); } catch { /* trang khong fire load */ }
    let loadMs = Date.now() - tNav;
    try {
      const nav = await page.evaluate(() => {
        const e = performance.getEntriesByType('navigation')[0];
        return e && e.loadEventEnd > 0 ? Math.round(e.loadEventEnd) : null;
      });
      if (nav) loadMs = nav;
    } catch { /* giu gia tri do bang dong ho */ }

    await page.waitForTimeout(400);

    evNo += 1;
    const evId = 'EV-' + String(evNo).padStart(4, '0');
    const shot = 'evidence/' + evId + '.png';
    try { await page.screenshot({ path: path.join(out, shot), fullPage: true }); }
    catch { /* anh loi khong lam dung crawl */ }

    let info;
    try {
      info = await page.evaluate(() => {
        const T = (s, n) => String(s || '').replace(/\s+/g, ' ').trim().slice(0, n);
        const visible = el => {
          if (!el.getClientRects().length) return false;
          const cs = getComputedStyle(el);
          return cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity || '1') > 0;
        };
        const labelOf = el => {
          const tag = el.tagName.toLowerCase();
          if (el.labels && el.labels.length) {
            // bo control con (select/textarea) de khong lo gia tri vao nhan
            const s = Array.from(el.labels).map(l => { const c = l.cloneNode(true);
              c.querySelectorAll('input,select,textarea,script,style').forEach(n => n.remove()); return c.textContent; }).join(' ');
            if (T(s, 60)) return T(s, 60);
          }
          if (el.getAttribute('aria-label')) return T(el.getAttribute('aria-label'), 60);
          const lb = el.getAttribute('aria-labelledby');
          if (lb) {
            const s = lb.split(/\s+/).map(id => document.getElementById(id)).filter(Boolean).map(n => n.innerText).join(' ');
            if (s) return T(s, 60);
          }
          if (el.getAttribute('placeholder')) return T(el.getAttribute('placeholder'), 60);
          if (tag === 'input' && ['submit', 'button', 'reset'].includes(el.type)) return T(el.value, 60);  // nhan nut, khong phai du lieu
          if (tag === 'button' || tag === 'a' || el.getAttribute('role') === 'button') return T(el.innerText || el.title, 60);
          return T(el.title, 60);
        };

        const sel = 'input,select,textarea,button,a[href],[role="button"]';
        const all = Array.from(document.querySelectorAll(sel));
        const itemSel = 'input:not([type=hidden]),select,textarea,button,[role="button"]';
        const items = [];
        for (const el of document.querySelectorAll(itemSel + ',a')) {
          const tag = el.tagName.toLowerCase();
          if (tag === 'a' && !(/btn|button/i.test(el.className || '') || el.getAttribute('role') === 'button')) continue;
          if (!visible(el)) continue;
          const type = tag === 'input' ? (el.type || 'text') : (tag === 'button' ? (el.type || 'submit') : (el.getAttribute('type') || null));
          let hasValue = false;   // CHI boolean — khong bao gio ghi gia tri (privacy)
          if (tag === 'input' && ['checkbox', 'radio'].includes(el.type)) hasValue = !!el.checked;
          else if (tag === 'input' && ['submit', 'button', 'reset', 'image'].includes(el.type)) hasValue = false;
          else if (tag === 'select') hasValue = el.selectedIndex >= 0 && el.value !== '';
          else if ('value' in el && (tag === 'input' || tag === 'textarea')) hasValue = String(el.value || '').length > 0;
          const num = a => { const v = el.getAttribute(a); return v === null ? null : parseInt(v, 10); };
          items.push({
            tag, type, name: el.getAttribute('name'), id: el.id || null, label: labelOf(el),
            required: el.hasAttribute('required') || el.getAttribute('aria-required') === 'true',
            maxlength: num('maxlength'), minlength: num('minlength'), pattern: el.getAttribute('pattern'),
            disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
            readonly: el.hasAttribute('readonly'),
            optionsCount: tag === 'select' ? el.options.length : null,
            hasValue,
          });
        }

        const tables = Array.from(document.querySelectorAll('table')).filter(visible).map(t => {
          let ths = Array.from(t.querySelectorAll('thead th'));
          if (!ths.length) { const r = t.querySelector('tr'); ths = r ? Array.from(r.querySelectorAll('th')) : []; }
          return { headers: ths.map(th => T(th.innerText, 80)) };   // CHI header, khong lay gia tri o
        });

        const anchors = Array.from(document.querySelectorAll('a[href]')).map(a => ({ href: a.href, text: T(a.innerText || a.title || a.getAttribute('aria-label'), 80) }));

        // --- mau computed-style (cho design token) ---
        const cs = el => getComputedStyle(el);
        const body = cs(document.body);
        const hs = {};
        for (const h of ['h1', 'h2', 'h3']) {
          const el = Array.from(document.querySelectorAll(h)).find(visible);
          if (el) { const s = cs(el); hs[h] = { fontSize: s.fontSize, fontWeight: s.fontWeight, color: s.color, fontFamily: s.fontFamily, lineHeight: s.lineHeight }; }
        }
        const btnEls = Array.from(document.querySelectorAll('button,input[type=submit],input[type=button],[role="button"],a.btn,a.button,a[class*="btn"],a[class*="button"]')).filter(visible).slice(0, 10);
        const buttons = btnEls.map(el => { const s = cs(el); return {
          bg: s.backgroundColor, color: s.color, borderRadius: s.borderRadius, padding: s.padding,
          fontSize: s.fontSize, fontWeight: s.fontWeight, fontFamily: s.fontFamily, border: s.border, boxShadow: s.boxShadow, label: labelOf(el) }; });
        const inEls = Array.from(document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=checkbox]):not([type=radio]),select,textarea')).filter(visible).slice(0, 10);
        const inputs = inEls.map(el => { const s = cs(el); return {
          borderColor: s.borderColor, borderRadius: s.borderRadius, height: s.height, padding: s.padding,
          fontSize: s.fontSize, fontFamily: s.fontFamily, bg: s.backgroundColor, boxShadow: s.boxShadow }; });
        const linkEl = Array.from(document.querySelectorAll('a[href]')).find(visible);
        const colorFreq = { 'color': {}, 'background-color': {}, 'border-color': {} };
        const shadowFreq = {}, fontFreq = {};
        const inc = (o, k) => { o[k] = (o[k] || 0) + 1; };
        const els = Array.from(document.body.querySelectorAll('*')).filter(visible).slice(0, 400);
        for (const el of els) {
          const s = cs(el);
          inc(colorFreq['color'], s.color);
          if (!/rgba\(0, 0, 0, 0\)|transparent/.test(s.backgroundColor)) inc(colorFreq['background-color'], s.backgroundColor);
          if (parseFloat(s.borderTopWidth) > 0 && s.borderTopStyle !== 'none') inc(colorFreq['border-color'], s.borderTopColor);
          if (s.boxShadow && s.boxShadow !== 'none') inc(shadowFreq, s.boxShadow);
          inc(fontFreq, s.fontFamily);
        }
        const style = {
          body: { bg: body.backgroundColor, color: body.color, fontFamily: body.fontFamily, fontSize: body.fontSize, lineHeight: body.lineHeight },
          headings: hs, buttons, inputs, links: linkEl ? { color: cs(linkEl).color } : null,
          colorFreq, shadowFreq, fontFreq, sampled: els.length,
        };

        const brokenImages = Array.from(document.images)
          .filter(i => i.complete && i.naturalWidth === 0 && (i.currentSrc || i.src))
          .map(i => { try { return new URL(i.currentSrc || i.src).pathname; } catch { return String(i.src).split('?')[0]; } });

        return {
          title: document.title,
          itemCount: all.length,
          headings: Array.from(document.querySelectorAll('h1,h2,h3')).filter(visible)
            .map(h => ({ level: h.tagName.toLowerCase(), text: T(h.innerText, 80) })),
          forms: Array.from(document.querySelectorAll('form')).map(f => ({
            action: f.getAttribute('action') === null ? location.href : f.action,
            method: (f.getAttribute('method') || 'GET').toUpperCase() })),
          tables, items, anchors, style, brokenImages,
          scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth,
        };
      });
    } catch (e) {
      networkIssues.push({ page: url, url, status: 'EVALUATE_ERROR', detail: String(e).slice(0, 200) });
      continue;
    }

    // link: cung origin, khong trung; logout / pha du lieu -> blocked, khong di theo
    const links = [];
    for (const a of info.anchors) {
      const n = normalize(a.href);
      if (!n || !/^https?:/.test(n) || !sameOrigin(n, start) || links.includes(n)) continue;
      links.push(n);
      if (seen.has(n) || queued.has(n)) continue;
      if (LOGOUT_RE.test(hrefPath(n)) || LOGOUT_RE.test(a.text)) {
        if (!blocked.some(b => b.kind === 'logout-link' && b.url === n)) blocked.push({ kind: 'logout-link', url: n, text: a.text, page: url });
        continue;
      }
      const hit = destructiveHit(hrefPath(n)) || destructiveHit(a.text);
      if (hit) {
        if (!blocked.some(b => b.kind === 'destructive-link' && b.url === n)) blocked.push({ kind: 'destructive-link', url: n, text: a.text, keyword: hit, page: url });
        continue;
      }
      queued.add(n);
      queue.push(n);
    }

    const status = resp ? resp.status() : null;
    const errorPage = typeof status === 'number' && status >= 400;  // vd 404 tu link hong -> input bug, khong phai man
    pages.push({
      url, title: info.title, status, evId, loadMs,
      headings: info.headings, forms: info.forms, tables: info.tables, links,
      items: info.items, itemCount: info.itemCount, ...(errorPage ? { errorPage: true } : {}),
    });
    if (!errorPage) styles.push(Object.assign({ url, evId }, info.style));
    evidence.push([evId, 'screenshot', url, new Date().toISOString(), role, shot,
                   (info.title || '').replace(/[",\n]/g, ' ')]);

    for (const src of info.brokenImages) uiIssues.push({ url, kind: 'brokenImage', detail: src, evId });
    if (info.scrollWidth > info.innerWidth + 2) {
      uiIssues.push({ url, kind: 'horizontalOverflow', detail: `scrollWidth ${info.scrollWidth} > viewport ${info.innerWidth}`, evId });
    }
    if (loadMs > SLOW_MS) uiIssues.push({ url, kind: 'slowLoad', detail: `loadMs ${loadMs} > ${SLOW_MS}`, evId });
  }

  // dem loi console / 4xx-5xx theo trang
  for (const p of pages) {
    const ce = consoleErrors.filter(c => c.url === p.url).length;
    const he = networkIssues.filter(n => n.page === p.url && typeof n.status === 'number').length;
    if (ce) uiIssues.push({ url: p.url, kind: 'consoleErrors', detail: `${ce} console error(s) — xem console.json`, evId: p.evId, count: ce });
    if (he) uiIssues.push({ url: p.url, kind: 'httpErrors', detail: `${he} response 4xx/5xx — xem network.json`, evId: p.evId, count: he });
  }

  // ghi output
  const W = (f, s) => fs.writeFileSync(path.join(crawlDir, f), s);
  W('urls.txt', pages.filter(p => !p.errorPage).map(p => p.url).join('\n') + '\n');
  W('pages.json', JSON.stringify(pages, null, 2));
  W('styles.json', JSON.stringify({ site, viewport, pages: styles }, null, 2));
  W('ui-issues.json', JSON.stringify(uiIssues, null, 2));
  W('console.json', JSON.stringify(consoleErrors, null, 2));
  W('network.json', JSON.stringify(networkIssues, null, 2));
  W('blocked.json', JSON.stringify(blocked, null, 2));
  W('evidence.csv',
    EVIDENCE_HEADER + '\n' +
    evidence.map(r => r.map(c => '"' + String(c).replace(/"/g, '""') + '"').join(',')).join('\n') + (evidence.length ? '\n' : ''));
  W('destructive-selectors.json', JSON.stringify(DESTRUCTIVE, null, 2));

  await browser.close();

  console.log(JSON.stringify({
    site, mode, role, viewport: `${viewport.width}x${viewport.height}`,
    urls: pages.filter(p => !p.errorPage).length, errorPages: pages.filter(p => p.errorPage).length, budget: `${pages.length}/${maxUrls} URL · ${((Date.now() - t0) / 60000).toFixed(1)}/${maxMin} phut`,
    consoleErrors: consoleErrors.length, networkIssues: networkIssues.length,
    uiIssues: uiIssues.length, blocked: blocked.length,
    ev_range: pages.length ? `EV-${String(evStart).padStart(4, '0')}..EV-${String(evNo).padStart(4, '0')}` : null,
    next_ev: evNo + 1, out, crawlDir,
  }, null, 2));
})();
