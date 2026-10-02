#!/usr/bin/env node
/**
 * Tao Playwright storage state de crawl-site.js dung lai — KHONG luu mat khau.
 *
 *   # 1) Nguoi dang nhap tay trong cua so trinh duyet (khuyen dung: MFA/SSO/captcha)
 *   node login-site.js --manual --url https://stg.example.jp/login --save <project>/.auth/WEB-01.json \
 *        [--success-url-contains /dashboard | --success-selector "#logout"] [--timeout-min 5]
 *
 *   # 2) Dien form tu dong — credential CHI lay tu bien moi truong (khong bao gio tu CLI)
 *   WEB01_USER=... WEB01_PASS=... node login-site.js --form --url https://stg.example.jp/login \
 *        --save <project>/.auth/WEB-01.json --user-env WEB01_USER --pass-env WEB01_PASS \
 *        [--user-selector "#email"] [--pass-selector "#password"] [--submit-selector "button[type=submit]"] \
 *        [--success-url-contains ... | --success-selector ...]
 *
 *   # Site co HTTP Basic Auth (vd CloudFront): them --http-user-env VAR --http-pass-env VAR (ca 2 mode)
 *
 * Output: file storage state (cookie + localStorage) mode 0600. .auth/ PHAI nam trong .gitignore,
 * khong bao gio copy vao outputs/, khong in ra, khong ghi vao tai lieu.
 * --form: request khac GET/HEAD chi duoc phep toi origin cua form login (POST duy nhat kit cho phep).
 * Exit: 0 dang nhap OK · 1 dang nhap that bai / sai tham so · 2 thieu playwright · 3 tu choi (an toan)
 */
const fs = require('fs');
const path = require('path');

const DEF_USER = 'input[type=email], input[autocomplete=username], input[name*=user i], input[name*=login i], ' +
  'input[name*=email i], input[id*=user i], input[id*=login i], input[id*=email i], input[type=text]';
const DEF_PASS = 'input[type=password]';
const DEF_SUBMIT = 'button[type=submit], input[type=submit], button:not([type])';

function arg(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  if (i === -1) return dflt;
  const v = process.argv[i + 1];
  return v && !v.startsWith('--') ? v : true;
}

function mask(s) {
  s = String(s || '');
  return s.length <= 4 ? '****' : s.slice(0, 2) + '****' + s.slice(-2);
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

function strip(u) { try { const x = new URL(u); x.hash = ''; x.search = ''; return x.toString().replace(/\/$/, ''); } catch { return u; } }

async function firstVisible(scope, sel) {
  for (const l of await scope.locator(sel).all()) {
    try { if (await l.isVisible()) return l; } catch { /* bo qua */ }
  }
  return null;
}

async function loggedIn(page, loginUrl, opt) {
  try {
    const url = page.url();
    if (opt.urlContains) return url.includes(opt.urlContains);
    if (opt.selector) return !!(await firstVisible(page, opt.selector));
    if (strip(url) === strip(loginUrl) || url === 'about:blank') return false;
    return !(await firstVisible(page, DEF_PASS));
  } catch { return false; }   // dang chuyen trang
}

(async () => {
  for (const bad of ['user', 'pass', 'password', 'username']) {
    if (process.argv.includes('--' + bad)) {
      console.error(`Tu choi: khong nhan credential qua CLI (--${bad}). Dung --user-env / --pass-env.`); process.exit(3);
    }
  }
  const url = arg('url');
  const save = arg('save');
  const manual = arg('manual', false) === true;
  const form = arg('form', false) === true;
  const opt = { urlContains: arg('success-url-contains', null), selector: arg('success-selector', null) };
  const timeoutMin = parseFloat(arg('timeout-min', '5'));

  if (!url || url === true || !save || save === true || manual === form) {
    console.error('Can --url, --save va dung 1 trong --manual | --form'); process.exit(1);
  }
  const absSave = path.resolve(String(save));
  if (/[\\/]outputs[\\/]/.test(absSave)) {
    console.error('Tu choi: storage state khong duoc nam trong outputs/. Dung <project>/.auth/<WEB-xx>.json'); process.exit(3);
  }
  if (path.basename(path.dirname(absSave)) !== '.auth') {
    console.error('Canh bao: nen luu vao <project>/.auth/<WEB-xx>.json (thu muc .auth/ duoc git-ignore)');
  }

  let user = null, pass = null;
  if (form) {
    const ue = arg('user-env'), pe = arg('pass-env');
    if (!ue || ue === true || !pe || pe === true) { console.error('--form can --user-env VAR va --pass-env VAR'); process.exit(1); }
    user = process.env[ue]; pass = process.env[pe];
    if (!user || !pass) { console.error(`Bien moi truong ${ue} / ${pe} chua duoc dat`); process.exit(1); }
  }

  let chromium;
  try { ({ chromium } = require('playwright')); }
  catch { console.error('Thieu playwright. Chay: npm i -D playwright && npx playwright install chromium'); process.exit(2); }
  let browser;
  try { browser = await chromium.launch({ headless: !manual }); }
  catch (e) { console.error('Khong mo duoc chromium. Chay: npx playwright install chromium\n' + String(e).split('\n')[0]); process.exit(2); }

  const ctxOpts = { serviceWorkers: 'block' };
  const hc = httpCreds(arg, url);
  if (hc) ctxOpts.httpCredentials = hc;
  const ctx = await browser.newContext(ctxOpts);
  const page = await ctx.newPage();
  let ok = false;
  const blocked = [];

  try {
    if (manual) {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      console.error(`Hay dang nhap trong cua so trinh duyet (cho toi da ${timeoutMin} phut)...`);
      const end = Date.now() + timeoutMin * 60000;
      while (Date.now() < end) {
        if (page.isClosed()) break;
        if (await loggedIn(page, url, opt)) { ok = true; break; }
        await new Promise(r => setTimeout(r, 1000));
      }
      if (ok) await new Promise(r => setTimeout(r, 1500));   // cho cookie/localStorage on dinh
    } else {
      let allowOrigin = null;   // chi origin cua form login duoc POST
      await ctx.route('**/*', route => {
        const req = route.request();
        if (['GET', 'HEAD'].includes(req.method())) return route.continue();
        let o = null; try { o = new URL(req.url()).origin; } catch { /* */ }
        if (allowOrigin && o === allowOrigin) return route.continue();
        blocked.push(`${req.method()} ${req.url()}`);
        return route.abort();
      });
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      try { await page.waitForLoadState('networkidle', { timeout: 5000 }); } catch { /* */ }
      const pw = await firstVisible(page, String(arg('pass-selector', DEF_PASS)));
      if (!pw) throw new Error('Khong thay o mat khau (--pass-selector)');
      const us = await firstVisible(page, String(arg('user-selector', DEF_USER)));
      if (!us) throw new Error('Khong thay o user (--user-selector)');
      allowOrigin = await pw.evaluate(el => {
        const f = el.form; try { return new URL(f ? f.action : location.href).origin; } catch { return location.origin; }
      });
      await us.fill(user);
      await pw.fill(pass);
      const formScope = pw.locator('xpath=ancestor::form[1]');
      let submit = (await formScope.count()) ? await firstVisible(formScope, String(arg('submit-selector', DEF_SUBMIT))) : null;
      if (!submit) submit = await firstVisible(page, String(arg('submit-selector', DEF_SUBMIT)));
      if (submit) await submit.click(); else await pw.press('Enter');
      const end = Date.now() + 20000;
      while (Date.now() < end) {
        await new Promise(r => setTimeout(r, 500));
        if (await loggedIn(page, url, opt)) { ok = true; break; }
      }
      if (ok) { try { await page.waitForLoadState('networkidle', { timeout: 5000 }); } catch { /* */ } }
    }
  } catch (e) {
    console.error('Loi: ' + String(e.message || e).split('\n')[0]);
  }

  if (!ok) {
    await browser.close();
    console.error('Dang nhap THAT BAI' + (user ? ` (user ${mask(user)})` : '') + ' — khong ghi storage state.');
    process.exit(1);
  }

  fs.mkdirSync(path.dirname(absSave), { recursive: true, mode: 0o700 });
  const state = await ctx.storageState();
  fs.writeFileSync(absSave, JSON.stringify(state, null, 2), { mode: 0o600 });
  fs.chmodSync(absSave, 0o600);
  const finalUrl = page.url();
  await browser.close();

  // nhac git-ignore
  const proj = path.dirname(path.dirname(absSave));
  let ignored = false;
  try { ignored = /^\/?\.auth\/?\s*$/m.test(fs.readFileSync(path.join(proj, '.gitignore'), 'utf8')); } catch { /* */ }
  console.error('NHAC: thu muc .auth/ PHAI nam trong .gitignore va KHONG BAO GIO copy vao outputs/.' +
    (ignored ? '' : ` Chua thay ".auth/" trong ${path.join(proj, '.gitignore')} — hay them vao.`));

  console.log(JSON.stringify({
    ok: true, mode: manual ? 'manual' : 'form', user: user ? mask(user) : null,
    saved: absSave, fileMode: '0600', cookies: state.cookies.length, landedOn: strip(finalUrl),
    blockedRequests: blocked.length, gitignored: ignored,
  }, null, 2));
  process.exit(0);
})();
