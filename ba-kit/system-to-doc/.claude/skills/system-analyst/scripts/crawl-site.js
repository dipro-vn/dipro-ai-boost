#!/usr/bin/env node
/**
 * Recon website — CHE DO READ-ONLY LA MAC DINH.
 *
 *   node crawl-site.js --url https://stg.example.jp --site WEB-01 --out <ver>/_internal \
 *        [--mode read-only|submit-staging|submit-prod] [--max-urls 200] [--max-minutes 30] \
 *        [--storage-state <project>/.auth/WEB-01.json] [--role test_user] \
 *        [--forbid "/admin/batch,/payment"] [--ev-start 1] [--viewport 1440x900] [--assets on|off]
 *        [--http-user-env VAR --http-pass-env VAR]   HTTP Basic Auth, gia tri chi lay tu env
 *        [--seed-file urls.txt]   URL khoi tao them (SPA dieu huong bang nut) — van qua bo loc logout/pha du lieu
 *        [--headed]               mo cua so trinh duyet de user quan sat (mac dinh headless)
 *        [--cred-file <project>/.auth/credentials.local.env --account admin [--login-url <url>]]
 *                                 credential tu file user dien (auth-common.js: chi ENV=TEST, chi origin cua
 *                                 <site>.URL, file trong .auth/ khong bi git track). Co --cred-file thi:
 *                                 - tu dang nhap luc dau neu gap o mat khau; Basic Auth lay tu file (uu tien hon env)
 *                                 - MAT SESSION (bi chuyen ve trang co o mat khau / URL login) -> ghi blocked.json
 *                                   kind "session-lost", thu lai URL 1 lan de biet trang nao giet session
 *                                   (trang do = "session-killer": khong tham lai, pages.json sessionKiller:true,
 *                                   khong vao urls.txt neu khong quan sat duoc), dang nhap lai toi da 5 lan / run
 *                                 --role mac dinh = ten account
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
 *   recon/crawl/<site>/styles.json       mau computed-style, tru trang loi (input cho extract-design-tokens.py):
 *                                        + components (nut/input/bang/nav/card/badge/tab...: count + <=3 mau style),
 *                                        typeHist (to hop font), valueFreq (shadow/radius/padding/gap/maxWidth), fontFaces,
 *                                        boxW/boxH (kich thuoc that) moi mau, bang: headerH/rowH
 *   recon/design/assets/<site>/          (--assets on, mac dinh) logos/ (logo + favicon, tai bang GET)
 *                                        icons/icon-<hash8>.svg (svg inline <=64px) · assets.json (file -> trang + evId)
 *                                        KHONG luu anh noi dung (co the chua du lieu ca nhan)
 *   recon/crawl/<site>/ui-issues.json    loi do duoc (anh vo, tran ngang, cham, console, 4xx/5xx) -> Bug List
 *   recon/crawl/<site>/evidence.csv      dong san sang dan vao sheet 05_Evidence
 *   recon/crawl/<site>/console.json · network.json · blocked.json (bang chung Gate G9)
 * Stdout cuoi: JSON co next_ev de chain lan chay sau.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const A = require('./auth-common');

const DESTRUCTIVE = [
  'delete', 'remove', 'destroy', 'xoa', 'xóa', '削除', '退会', 'withdraw',
  'pay', 'payment', 'checkout', 'purchase', 'thanh toan', 'thanh toán', '決済',
  'send mail', 'gui mail', 'gửi mail', '送信', 'submit order', 'confirm order',
];
const LOGOUT_RE = /log-?out|sign-?out|ログアウト|đăng xuất|dang xuat/i;
const LOGIN_RE = /log-?in|sign-?in|ログイン/i;
const MAX_RELOGIN = 5;
const EVIDENCE_HEADER = 'EV ID,Type,Locator,Captured At,Actor/Role,Artifact,Note';  // = S.SHEETS["05_Evidence"]
const SLOW_MS = 5000;
const MAX_ICONS = 80, MAX_LOGOS = 20, MAX_ASSET_BYTES = 2 * 1024 * 1024;
const IMG_EXT = { 'image/png': 'png', 'image/jpeg': 'jpg', 'image/gif': 'gif', 'image/webp': 'webp', 'image/avif': 'avif',
  'image/svg+xml': 'svg', 'image/x-icon': 'ico', 'image/vnd.microsoft.icon': 'ico' };
const hash8 = b => crypto.createHash('sha1').update(b).digest('hex').slice(0, 8);

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

// HTTP Basic Auth (vd lop CloudFront) — CHI doc tu bien moi truong, chi gui toi origin cua --url
function httpCreds(arg, url) {
  const ue = arg('http-user-env', null), pe = arg('http-pass-env', null);
  if (!ue && !pe) return null;
  if (!ue || ue === true || !pe || pe === true) { console.error('Basic Auth can ca --http-user-env VAR va --http-pass-env VAR'); process.exit(1); }
  const username = process.env[ue], password = process.env[pe];
  if (!username || !password) { console.error(`Bien moi truong ${ue} / ${pe} chua duoc dat`); process.exit(1); }
  return { username, password, origin: new URL(String(url)).origin };
}

(async () => {
  for (const bad of ['user', 'pass', 'password', 'username']) {
    if (process.argv.includes('--' + bad)) {
      console.error(`Tu choi: khong nhan credential qua CLI (--${bad}). Dung --cred-file.`); process.exit(3);
    }
  }
  let chromium;
  try { ({ chromium } = require('playwright')); }
  catch { console.error('Thieu playwright. Chay: npm i -D playwright && npx playwright install chromium'); process.exit(2); }

  const start = arg('url');
  const site = arg('site');
  const out = arg('out', './_internal');
  const mode = arg('mode', 'read-only');
  const maxUrls = parseInt(arg('max-urls', '200'), 10);
  const maxMin = parseFloat(arg('max-minutes', '30'));
  const credFile = arg('cred-file', null);
  const account = arg('account', null);
  const role = arg('role', account && account !== true ? account : 'anonymous');
  const storage = arg('storage-state', null);
  const forbid = String(arg('forbid', '')).split(',').map(s => s.trim()).filter(Boolean);
  const evStart = parseInt(arg('ev-start', '1'), 10);
  const vp = String(arg('viewport', '1440x900')).match(/^(\d+)x(\d+)$/);
  const withAssets = !['off', 'false', 'no', '0'].includes(String(arg('assets', 'on')).toLowerCase());

  if (!start || start === true) { console.error('Thieu --url'); process.exit(1); }
  if (!site || !/^WEB-\d{2,}$/.test(String(site))) { console.error('Thieu/sai --site (vd WEB-01)'); process.exit(1); }
  if (!['read-only', 'submit-staging', 'submit-prod'].includes(mode)) {
    console.error('--mode phai la read-only | submit-staging | submit-prod'); process.exit(1);
  }
  if (!vp) { console.error('--viewport phai dang 1440x900'); process.exit(1); }
  if (!(evStart >= 1)) { console.error('--ev-start phai >= 1'); process.exit(1); }
  const viewport = { width: parseInt(vp[1], 10), height: parseInt(vp[2], 10) };
  // credential tu file — kiem tra an toan TRUOC khi mo trinh duyet / ghi output (exit 3 neu tu choi)
  const cred = credFile ? A.loadCreds({ file: credFile, site, account, url: start, needAccount: true }) : null;
  let loginUrl = arg('login-url', null);
  if (loginUrl === true) { console.error('--login-url can gia tri'); process.exit(1); }
  if (loginUrl && cred && A.originOf(loginUrl) !== cred.origin) {
    A.refuse(`origin cua --login-url khac origin cua ${site}.URL (${cred.origin}) — credential chi duoc gui toi origin do`);
  }
  const userSel = String(arg('user-selector', A.DEF_USER)), passSel = String(arg('pass-selector', A.DEF_PASS));
  const submitSel = String(arg('submit-selector', A.DEF_SUBMIT));
  const okOpt = { urlContains: arg('success-url-contains', null), selector: arg('success-selector', null) };

  const evDir = path.join(out, 'evidence');
  const crawlDir = path.join(out, 'recon', 'crawl', String(site));
  fs.mkdirSync(evDir, { recursive: true });
  fs.mkdirSync(crawlDir, { recursive: true });
  const assetDir = path.join(out, 'recon', 'design', 'assets', String(site));
  const assetFiles = [], assetSkipped = [], iconFonts = {}, assetSeen = new Set();

  let browser;
  try { browser = await chromium.launch({ headless: arg('headed', false) !== true }); }   // --headed: mo cua so de quan sat
  catch (e) { console.error('Khong mo duoc chromium. Chay: npx playwright install chromium\n' + String(e).split('\n')[0]); process.exit(2); }
  const ctxOpts = { viewport, serviceWorkers: 'block' };   // SW co the vuot qua ctx.route
  if (storage) ctxOpts.storageState = storage;
  const hc = cred ? cred.basic : httpCreds(arg, start);   // Basic Auth chi gui toi origin cua site
  if (hc) ctxOpts.httpCredentials = hc;
  const ctx = await browser.newContext(ctxOpts);
  const page = await ctx.newPage();

  const consoleErrors = [], networkIssues = [], blocked = [];
  let curUrl = null;
  let allowPost = null;   // chi mo khi dang dien form login (origin cua site), dong ngay sau do

  // --- Gate G2 thuc thi o tang network ---
  await ctx.route('**/*', route => {
    const req = route.request();
    const m = req.method();
    if (allowPost && !['GET', 'HEAD'].includes(m)) {
      let o = null; try { o = new URL(req.url()).origin; } catch { /* */ }
      if (o === allowPost) return route.continue();
    }
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

  // --- luu asset: logo/favicon tai bang GET (ctx.request dung chung cookie), icon svg tu markup ---
  const writeAsset = (kind, sub, prefix, buf, ext, meta) => {
    const h = hash8(buf);
    if (assetSeen.has(h)) return;
    assetSeen.add(h);
    const rel = sub + '/' + prefix + '-' + h + '.' + ext;
    fs.mkdirSync(path.join(assetDir, sub), { recursive: true });
    fs.writeFileSync(path.join(assetDir, rel), buf);
    assetFiles.push(Object.assign({ kind, file: rel, size: buf.length, type: ext === 'svg' ? 'image/svg+xml'
      : Object.keys(IMG_EXT).find(k => IMG_EXT[k] === ext) || 'application/octet-stream' }, meta));
  };
  const fetchImage = async (src, kind, prefix, meta) => {
    if (assetFiles.filter(f => f.kind !== 'icon').length >= MAX_LOGOS) return;
    try {
      let buf, type;
      if (/^data:image\//.test(src)) {
        const m = src.match(/^data:([^;,]+)(;base64)?,(.*)$/s);
        if (!m) return;
        type = m[1];
        buf = m[2] ? Buffer.from(m[3], 'base64') : Buffer.from(decodeURIComponent(m[3]));
      } else if (/^https?:/.test(src)) {
        if (forbid.some(f => src.includes(f))) { assetSkipped.push({ src, reason: 'forbidden-zone' }); return; }
        const r = await ctx.request.get(src, { timeout: 15000, maxRedirects: 3 });   // GET only
        if (!r.ok()) { assetSkipped.push({ src, reason: 'HTTP ' + r.status() }); return; }
        type = (r.headers()['content-type'] || '').split(';')[0].trim().toLowerCase();
        buf = await r.body();
      } else return;
      if (!IMG_EXT[type]) { assetSkipped.push({ src: src.slice(0, 200), reason: 'khong phai anh: ' + type }); return; }
      if (buf.length > MAX_ASSET_BYTES) { assetSkipped.push({ src: src.slice(0, 200), reason: 'qua 2MB' }); return; }
      writeAsset(kind, 'logos', prefix, buf, IMG_EXT[type], Object.assign({ source: src.slice(0, 300) }, meta));
    } catch (e) { assetSkipped.push({ src: String(src).slice(0, 200), reason: String(e).split('\n')[0].slice(0, 120) }); }
  };
  const saveAssets = async (a, url, evId) => {
    if (!a) return;
    for (const [k, n] of Object.entries(a.fontIcons || {})) iconFonts[k] = (iconFonts[k] || 0) + n;
    for (const l of a.logos || []) {
      if (l.kind === 'img') await fetchImage(l.src, 'logo', 'logo', { page: url, evId, alt: l.alt, w: l.w, h: l.h });
      else if (l.markup) writeAsset('logo', 'logos', 'logo', Buffer.from(l.markup), 'svg',
        { source: 'inline-svg', page: url, evId, ink: l.ink, w: l.w, h: l.h });
    }
    for (const f of a.favicons || []) await fetchImage(f, 'favicon', 'favicon', { page: url, evId });
    for (const ic of a.icons || []) {
      if (assetFiles.filter(f => f.kind === 'icon').length >= MAX_ICONS) break;
      writeAsset('icon', 'icons', 'icon', Buffer.from(ic.markup), 'svg',
        { source: 'inline-svg', page: url, evId, ink: ic.ink, w: ic.w, h: ic.h });
    }
  };

  const queue = [normalize(start)];
  const queued = new Set(queue);
  // --seed-file: URL khoi tao (vd route tinh lay tu source) — cung bo loc origin / logout / pha du lieu nhu link
  const seedFile = arg('seed-file', null);
  if (seedFile && seedFile !== true) {
    for (const line of fs.readFileSync(String(seedFile), 'utf8').split(/\r?\n/)) {
      const n = normalize(line.trim());
      if (!n || !/^https?:/.test(n) || !sameOrigin(n, start) || queued.has(n)) continue;
      if (LOGOUT_RE.test(hrefPath(n)) || destructiveHit(hrefPath(n))) { blocked.push({ kind: 'seed-skipped', url: n }); continue; }
      queued.add(n); queue.push(n);
    }
  }
  const seen = new Set(), pages = [], evidence = [], styles = [], uiIssues = [];
  const t0 = Date.now();
  let evNo = evStart - 1;

  // dieu huong 1 URL: domcontentloaded + load + 400ms; loadMs uu tien Navigation Timing
  const visit = async (u) => {
    let resp;
    const tNav = Date.now();
    try { resp = await page.goto(u, { waitUntil: 'domcontentloaded', timeout: 20000 }); }
    catch (e) { return { err: e }; }
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
    return { resp, loadMs };
  };

  // --- dang nhap (lai) bang form, credential tu file; chi POST toi origin cua site ---
  const killers = [];
  let relogins = 0, stopReason = null, lastOk = null;
  const isLoginUrl = u => (loginUrl && A.strip(u) === A.strip(loginUrl)) || LOGIN_RE.test(hrefPath(u));
  const sessionLost = async (reqUrl) => {
    if (isLoginUrl(reqUrl)) return false;   // tu mo trang login thi khong tinh
    const fin = page.url();
    if (A.strip(fin) === A.strip(reqUrl)) return false;   // khong bi chuyen trang
    if (isLoginUrl(fin)) return true;
    try { return !!(await A.firstVisible(page, passSel)); } catch { return false; }
  };
  const doLogin = async (lu) => {
    const prevCur = curUrl;
    curUrl = 'login';
    const r = await A.formLogin(page, { loginUrl: lu, user: cred.user, pass: cred.pass, origin: cred.origin,
      userSel, passSel, submitSel, opt: okOpt, allow: o => { allowPost = o; } });
    allowPost = null;
    curUrl = prevCur;
    return r;
  };
  const relogin = async () => {
    if (relogins >= MAX_RELOGIN) {
      stopReason = `Da dang nhap lai ${MAX_RELOGIN} lan — DUNG crawl. Con trang giet session chua xac dinh? Xem blocked.json (session-lost), them vao --forbid roi chay lai.`;
      console.error(stopReason);
      return false;
    }
    relogins += 1;
    const r = await doLogin(loginUrl);
    if (!r.ok) { stopReason = `Dang nhap lai THAT BAI (lan ${relogins}): ${r.reason} — DUNG crawl`; console.error(stopReason); return false; }
    console.error(`Dang nhap lai OK (${relogins}/${MAX_RELOGIN}) user ${A.mask(cred.user)}`);
    return true;
  };

  if (cred) {   // dang nhap luc dau neu gap o mat khau (storage state het han / chua co)
    try { await page.goto(loginUrl || start, { waitUntil: 'domcontentloaded', timeout: 30000 }); } catch { /* */ }
    try { await page.waitForLoadState('networkidle', { timeout: 5000 }); } catch { /* */ }
    if (await A.firstVisible(page, passSel)) {
      if (!loginUrl) loginUrl = page.url();
      const r = await doLogin(null);
      if (!r.ok) {
        await browser.close();
        console.error(`Dang nhap THAT BAI (user ${A.mask(cred.user)}): ${r.reason}`);
        process.exit(1);
      }
      console.error(`Dang nhap OK user ${A.mask(cred.user)} -> ${r.landedOn}`);
    }
  }

  while (queue.length && seen.size < maxUrls) {
    if ((Date.now() - t0) / 60000 > maxMin) { console.error('Het budget thoi gian'); break; }
    const url = queue.shift();
    if (!url || seen.has(url)) continue;
    if (forbid.some(f => url.includes(f))) { blocked.push({ kind: 'forbidden-zone', url }); continue; }
    seen.add(url);
    curUrl = url;

    let r = await visit(url);
    if (r.err) { networkIssues.push({ page: url, url, status: 'NAVIGATION_ERROR', detail: String(r.err).slice(0, 200) }); continue; }

    // --- mat session -> dang nhap lai, thu lai 1 lan de biet trang nao giet session ---
    if (cred && await sessionLost(url)) {
      if (!loginUrl) loginUrl = page.url();   // URL co o mat khau sau redirect
      const rec = { kind: 'session-lost', url, at: new Date().toISOString() };
      blocked.push(rec);
      console.error(`Mat session khi mo ${url} -> dang nhap lai`);
      if (!await relogin()) break;
      r = await visit(url);
      if (r.err) { networkIssues.push({ page: url, url, status: 'NAVIGATION_ERROR', detail: String(r.err).slice(0, 200) }); continue; }
      if (await sessionLost(url)) {
        // chinh trang nay giet session (vd goi signOut()) — co man hinh nhung khong quan sat duoc
        rec.killer = url; rec.how = 'redirect-to-login';
        killers.push({ url, how: 'redirect-to-login' });
        pages.push({ url, title: null, status: null, evId: null, sessionKiller: true,
          note: 'Mo trang nay lam mat session (bi chuyen ve trang dang nhap) — co man hinh o day nhung khong quan sat duoc' });
        if (!await relogin()) break;
        continue;
      }
      // trang nay binh thuong -> session bi giet boi trang tham ngay truoc (sau khi load)
      const prev = lastOk && pages.find(p => p.url === lastOk);
      rec.killer = prev ? prev.url : null;
      rec.how = prev ? 'after-load' : 'unknown';
      if (prev) { prev.sessionKiller = true; prev.sessionKillerHow = 'after-load'; killers.push({ url: prev.url, how: 'after-load' }); }
    }
    const { resp, loadMs } = r;

    evNo += 1;
    const evId = 'EV-' + String(evNo).padStart(4, '0');
    const shot = 'evidence/' + evId + '.png';
    try { await page.screenshot({ path: path.join(out, shot), fullPage: true }); }
    catch { /* anh loi khong lam dung crawl */ }

    let info;
    try {
      info = await page.evaluate((opt) => {
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

        // --- design system: mau style theo component (KHONG lay text du lieu; label chi cho nhan UI) ---
        const Q = s => Array.from(document.querySelectorAll(s));
        const TRANSP = v => !v || /rgba\(0, 0, 0, 0\)|transparent/.test(v);
        const pick = (el, withLabel) => {
          const s = cs(el);
          const o = { bg: s.backgroundColor, color: s.color, borderColor: s.borderTopColor, borderWidth: s.borderTopWidth,
            borderRadius: s.borderRadius, padding: s.padding, fontSize: s.fontSize, fontWeight: s.fontWeight,
            lineHeight: s.lineHeight, fontFamily: s.fontFamily, boxShadow: s.boxShadow, height: s.height, gap: s.gap };
          const r = el.getBoundingClientRect();   // kich thuoc that (border-box) cho token size
          o.boxW = Math.round(r.width * 100) / 100; o.boxH = Math.round(r.height * 100) / 100;
          if (s.borderTopStyle === 'none') o.borderWidth = '0px';
          if (withLabel) o.label = T(labelOf(el) || el.innerText, 30);
          return o;
        };
        const sig = o => [o.bg, o.color, o.borderColor, o.borderWidth, o.borderRadius, o.padding, o.fontSize,
          o.fontWeight, o.boxShadow, o.variant || ''].join('|');
        // gom theo chu ky style -> count + <=3 mau pho bien nhat
        const group = (list, withLabel, extra) => {
          const els = Array.from(new Set(list)).filter(visible).slice(0, 300);
          const by = new Map();
          for (const el of els) {
            const o = pick(el, withLabel);
            if (extra) Object.assign(o, extra(el, o));
            const k = sig(o);
            if (by.has(k)) by.get(k).n += 1; else by.set(k, Object.assign(o, { n: 1 }));
          }
          return { count: els.length, samples: Array.from(by.values()).sort((a, b) => b.n - a.n).slice(0, 3) };
        };
        const btnVariant = (el, o) => ({ variant: !TRANSP(o.bg) ? 'solid'
          : (parseFloat(o.borderWidth) > 0 ? 'outline' : 'text') });
        const BTN_SEL = 'button,input[type=submit],input[type=button],[role="button"],a.btn,a.button,a[class*="btn"],a[class*="button"]';
        const btnAll = Q(BTN_SEL).filter(visible);
        const variants = {};
        for (const el of btnAll) { const v = btnVariant(el, pick(el)).variant; variants[v] = (variants[v] || 0) + 1; }
        const notIn = (el, sel) => !el.closest(sel);
        const NAV_SEL = 'nav, aside, [role=navigation]';
        const CRUMB_SEL = 'nav[aria-label*=readcrumb], .breadcrumb, .breadcrumbs, [class*=breadcrumb]';
        const PAGI_SEL = 'nav[aria-label*=agination], .pagination, [class*=pagination]';
        const navs = Q(NAV_SEL).filter(n => !n.matches(CRUMB_SEL + ',' + PAGI_SEL));
        const inside = (roots, sel) => roots.flatMap(r => Array.from(r.querySelectorAll(sel)));
        const scan = Array.from(document.body.querySelectorAll('*')).filter(visible).slice(0, 1500);
        const SKIP_CARD = /^(HTML|BODY|TABLE|THEAD|TBODY|TR|TD|TH|NAV|HEADER|BUTTON|INPUT|SELECT|TEXTAREA|A|UL|OL|LI|IMG|SVG)$/;
        const cards = scan.filter(el => {
          if (SKIP_CARD.test(el.tagName.toUpperCase()) || el.children.length < 2 || el.matches('[role=dialog], dialog')) return false;
          const s = cs(el);
          return (s.boxShadow && s.boxShadow !== 'none') ||
            (parseFloat(s.borderTopWidth) > 0 && s.borderTopStyle !== 'none' && parseFloat(s.borderTopLeftRadius) > 0);
        });
        const BADGE_CLS = /(^|[\s_-])(badge|tag|chip|label|status|pill)s?([\s_-]|$)/i;
        const badges = scan.filter(el => {
          const tag = el.tagName.toLowerCase();
          if (['label', 'button', 'a', 'input', 'select', 'textarea', 'td', 'th', 'li'].includes(tag)) return false;
          const txt = (el.innerText || '').trim();
          if (!txt || txt.length > 20 || el.querySelector('div,p,table,ul,ol,input,select,textarea')) return false;
          const s = cs(el);
          if (BADGE_CLS.test(el.getAttribute('class') || '')) return true;
          return /inline/.test(s.display) && !TRANSP(s.backgroundColor) && parseFloat(s.borderTopLeftRadius) > 0;
        });
        const comps = {
          buttons: Object.assign(group(btnAll, true, btnVariant), { variants }),
          inputs: group(Q('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=checkbox]):not([type=radio]):not([type=image]),select,textarea'), false),
          select: group(Q('select'), false),
          checkbox: group(Q('input[type=checkbox]:not([role=switch])'), false),
          radio: group(Q('input[type=radio]'), false),
          switch: group(Q('[role=switch], .switch, .toggle, .form-switch input'), false),
          links: group(Q('a[href]').filter(a => !a.matches(BTN_SEL) && notIn(a, NAV_SEL)), false),
          header: group(Q('header, [role=banner]'), false),
          nav: group(navs, false),
          navItem: group(inside(navs, 'a, button, [role=menuitem]'), true),
          navActive: group(inside(navs, '[aria-current]:not([aria-current=false]), .active, .is-active'), true),
          cards: group(cards, false),
          badges: group(badges, true),
          tabs: group(Q('[role=tab], .tab, .tabs > *'), true),
          tabActive: group(Q('[role=tab][aria-selected=true], .tab.active, .tab.is-active, .tabs > .active'), true),
          pagination: group(Q(PAGI_SEL), false),
          paginationItem: group(inside(Q(PAGI_SEL), 'a, button, li > span'), false),
          dialogs: Object.assign(group(Q('[role=dialog], dialog'), false), { present: Q('[role=dialog], dialog').length }),
          alerts: group(Q('[role=alert], .alert, .toast, .notification'), false),
          breadcrumbs: group(Q(CRUMB_SEL), false),
          tableTh: group(Q('table th'), false),
          tableTd: group(Q('table td'), false),   // CHI style, khong bao gio lay text o
        };
        for (const h of ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) comps[h] = group(Q(h), false);
        const tb = Q('table').filter(visible);
        comps.tables = { count: tb.length, samples: tb.slice(0, 3).map(t => {
          const th = t.querySelector('thead') || t.querySelector('tr');
          const td = t.querySelector('tbody td') || t.querySelector('td');
          const tds = td ? cs(td) : null;
          const hb = [th, th && th.querySelector('tr'), t.querySelector('th')].filter(Boolean)
            .map(e => cs(e).backgroundColor).find(v => !TRANSP(v));
          const tr = t.querySelector('tbody tr') || (td && td.parentElement);
          const hh = th ? th.getBoundingClientRect().height : 0, rh = tr ? tr.getBoundingClientRect().height : 0;
          return { headerBg: hb || null, headerH: Math.round(hh * 100) / 100 || null, rowH: Math.round(rh * 100) / 100 || null,
            rowBorder: tds ? [tds.borderBottomWidth, tds.borderBottomStyle, tds.borderBottomColor].join(' ') : null,
            borderCollapse: cs(t).borderCollapse };
        }) };

        // to hop chu (font/co/line-height/weight/mau) cua phan tu co text truc tiep — chi dem, khong lay text
        const typeHist = {}, valueFreq = { boxShadow: {}, borderRadius: {}, padding: {}, gap: {}, maxWidth: {} };
        for (const el of scan) {
          const s = cs(el);
          if (Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim())) {
            const k = [s.fontFamily, s.fontSize, s.lineHeight, s.fontWeight, s.color].join('|');
            const e = typeHist[k] || (typeHist[k] = { fontFamily: s.fontFamily, fontSize: s.fontSize, lineHeight: s.lineHeight,
              fontWeight: s.fontWeight, color: s.color, count: 0, tags: [] });
            e.count += 1;
            const tg = el.tagName.toLowerCase();
            if (e.tags.length < 5 && !e.tags.includes(tg)) e.tags.push(tg);
          }
          if (s.boxShadow && s.boxShadow !== 'none') inc(valueFreq.boxShadow, s.boxShadow);
          if (s.borderRadius && !/^0px( 0px)*$/.test(s.borderRadius)) inc(valueFreq.borderRadius, s.borderRadius);
          if (s.padding && !/^0px( 0px)*$/.test(s.padding)) inc(valueFreq.padding, s.padding);
          if (s.gap && !/^(normal|0px)( (normal|0px))?$/.test(s.gap)) inc(valueFreq.gap, s.gap);
          if (/^[\d.]+px$/.test(s.maxWidth) && el.children.length > 1) inc(valueFreq.maxWidth, s.maxWidth);
        }
        const typeTop = Object.values(typeHist).sort((a, b) => b.count - a.count).slice(0, 60);

        // @font-face (chi stylesheet doc duoc cung origin; KHONG tai font)
        const fontFaces = [], unreadableSheets = [];
        const walkRules = (rules, base) => {
          for (const r of Array.from(rules || [])) {
            if (r.type === 5) {
              const st = r.style, src = st.getPropertyValue('src') || '';
              const urls = Array.from(src.matchAll(/url\(\s*['"]?([^'")]+)['"]?\s*\)/g)).map(m => {
                try { return new URL(m[1], base).href; } catch { return m[1]; } }).filter(u => !u.startsWith('data:')).slice(0, 6);
              fontFaces.push({ family: st.getPropertyValue('font-family').replace(/['"]/g, '').trim(),
                weight: st.getPropertyValue('font-weight') || null, style: st.getPropertyValue('font-style') || null, src: urls });
            } else if (r.cssRules) walkRules(r.cssRules, base);
          }
        };
        for (const sh of Array.from(document.styleSheets)) {
          let rules = null;
          try { rules = sh.cssRules; } catch { unreadableSheets.push(sh.href); continue; }
          walkRules(rules, sh.href || location.href);
        }
        const fontLinks = Q('link[rel=stylesheet][href]').map(l => l.href).filter(h => /fonts\.(googleapis|bunny)|typekit|fontawesome/i.test(h));

        // --- assets: logo / favicon / icon svg inline (KHONG lay anh noi dung) ---
        let assets = null;
        if (opt.assets) {
          const attr = (el, a) => el.getAttribute(a) || '';
          const hint = el => /logo/i.test([attr(el, 'alt'), attr(el, 'class'), el.id, attr(el, 'src'), attr(el, 'aria-label')].join(' '))
            || !!(el.parentElement && el.parentElement.closest('[class*=logo i],[id*=logo i]'));
          const box = el => { const r = el.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; };
          const cleanSvg = (svg) => {
            let c = svg.cloneNode(true);
            const use = svg.querySelector('use');
            const ref = use && (use.getAttribute('href') || use.getAttribute('xlink:href') || '');
            if (ref && ref.startsWith('#')) {   // sprite <use href="#id"> -> chep symbol vao
              const sym = document.getElementById(ref.slice(1));
              if (sym) { c = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                const vb = sym.getAttribute('viewBox') || svg.getAttribute('viewBox'); if (vb) c.setAttribute('viewBox', vb);
                c.innerHTML = sym.innerHTML; }
            }
            if (c.querySelector('text, image, foreignObject, script')) return null;   // co the chua du lieu
            const b = box(svg);
            if (!c.getAttribute('width') && b.w) c.setAttribute('width', b.w);
            if (!c.getAttribute('height') && b.h) c.setAttribute('height', b.h);
            let m = new XMLSerializer().serializeToString(c).replace(/\son\w+="[^"]*"/gi, '');
            if (!/xmlns=/.test(m.slice(0, 200))) m = m.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
            return m.length > 20000 ? null : m;
          };
          const logoSet = new Set();
          for (const el of Q('img, svg').filter(visible)) {
            if (el.parentElement && el.parentElement.closest('svg')) continue;   // svg con long trong svg
            const inBar = !!el.closest('header, nav, [role=banner]');
            const b = box(el);
            const isImg = el.tagName.toLowerCase() === 'img';
            if (hint(el) || (inBar && (isImg || b.w > 32 || b.h > 32))) logoSet.add(el);
          }
          const logos = Array.from(logoSet).slice(0, 5).map(el => el.tagName.toLowerCase() === 'img'
            ? Object.assign({ kind: 'img', src: el.currentSrc || el.src, alt: T(el.alt, 60) }, box(el))
            : Object.assign({ kind: 'svg', markup: cleanSvg(el), ink: cs(el).color }, box(el)));
          const icons = [];
          for (const el of Q('svg').filter(visible)) {
            if (logoSet.has(el) || (el.parentElement && el.parentElement.closest('svg'))) continue;
            const b = box(el);
            if (!b.w || !b.h || b.w > 64 || b.h > 64) continue;
            const m = cleanSvg(el);
            if (m) icons.push({ markup: m, ink: cs(el).color, w: b.w, h: b.h });
            if (icons.length >= 80) break;
          }
          const ICF = { fa: /(^|\s)(fa[srlbdk]?|fa-[\w-]+)(\s|$)/, 'material-icons': /material-(icons|symbols)/, ph: /(^|\s)ph(-[\w-]+)?(\s|$)/, bi: /(^|\s)bi(-[\w-]+)?(\s|$)/ };
          const fontIcons = {};
          for (const el of Q('i, span, [class]').slice(0, 3000)) {
            const c = typeof el.className === 'string' ? el.className : attr(el, 'class');
            for (const [k, rx] of Object.entries(ICF)) if (rx.test(c)) fontIcons[k] = (fontIcons[k] || 0) + 1;
          }
          assets = { logos, favicons: Q('link[rel~=icon][href], link[rel=apple-touch-icon][href]').map(l => l.href).slice(0, 4),
            icons, fontIcons };
        }
        Object.assign(style, { components: comps, typeHist: typeTop, valueFreq, fontFaces, unreadableSheets, fontLinks,
          fontIcons: assets ? assets.fontIcons : null });

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
          tables, items, anchors, style, brokenImages, assets,
          scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth,
        };
      }, { assets: withAssets });
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
    if (!errorPage) {
      styles.push(Object.assign({ url, evId }, info.style));
      await saveAssets(info.assets, url, evId);
    }
    evidence.push([evId, 'screenshot', url, new Date().toISOString(), role, shot,
                   (info.title || '').replace(/[",\n]/g, ' ')]);

    for (const src of info.brokenImages) uiIssues.push({ url, kind: 'brokenImage', detail: src, evId });
    if (info.scrollWidth > info.innerWidth + 2) {
      uiIssues.push({ url, kind: 'horizontalOverflow', detail: `scrollWidth ${info.scrollWidth} > viewport ${info.innerWidth}`, evId });
    }
    if (loadMs > SLOW_MS) uiIssues.push({ url, kind: 'slowLoad', detail: `loadMs ${loadMs} > ${SLOW_MS}`, evId });
    lastOk = url;
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
  const observed = p => !p.errorPage && !(p.sessionKiller && !p.evId);   // trang giet session chua quan sat -> khong vao urls.txt
  W('urls.txt', pages.filter(observed).map(p => p.url).join('\n') + '\n');
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
  if (withAssets) {
    fs.mkdirSync(assetDir, { recursive: true });
    fs.writeFileSync(path.join(assetDir, 'assets.json'), JSON.stringify({ site, files: assetFiles, iconFonts,
      skipped: assetSkipped, note: 'Chi logo/favicon/icon. Khong luu anh noi dung.' }, null, 2));
  }

  await browser.close();

  console.log(JSON.stringify({
    site, mode, role, viewport: `${viewport.width}x${viewport.height}`,
    urls: pages.filter(observed).length, errorPages: pages.filter(p => p.errorPage).length, budget: `${pages.length}/${maxUrls} URL · ${((Date.now() - t0) / 60000).toFixed(1)}/${maxMin} phut`,
    consoleErrors: consoleErrors.length, networkIssues: networkIssues.length,
    uiIssues: uiIssues.length, blocked: blocked.length,
    ...(cred ? { account: cred.account, user: A.mask(cred.user), relogins, sessionKillers: killers } : {}),
    ...(stopReason ? { stopped: stopReason } : {}),
    assets: withAssets ? { logos: assetFiles.filter(f => f.kind !== 'icon').length,
      icons: assetFiles.filter(f => f.kind === 'icon').length, dir: assetDir } : 'off',
    ev_range: pages.length ? `EV-${String(evStart).padStart(4, '0')}..EV-${String(evNo).padStart(4, '0')}` : null,
    next_ev: evNo + 1, out, crawlDir,
  }, null, 2));
})();
