#!/usr/bin/env node
/**
 * Tao Playwright storage state de crawl-site.js dung lai — KHONG luu mat khau.
 *
 *   # 0) Tao template file credential (gia tri trong) — agent chay buoc nay, USER tu dien gia tri
 *   node login-site.js --init-cred-file <project>/.auth/credentials.local.env --site WEB-01 \
 *        --url https://dev.example.jp/admin --accounts admin,user [--basic]
 *        (chay lai: chi them key con thieu, KHONG ghi de gia tri da dien; in ten key con trong)
 *
 *   # 1) Nguoi dang nhap tay trong cua so trinh duyet (khuyen dung: MFA/SSO/captcha)
 *   node login-site.js --manual --url https://stg.example.jp/login --save <project>/.auth/WEB-01.json \
 *        [--success-url-contains /dashboard | --success-selector "#logout"] [--timeout-min 5]
 *        [--cred-file <...> --site WEB-01]   chi de lay URL + Basic Auth tu file (van bat buoc ENV=TEST)
 *
 *   # 2) Dien form tu dong tu file credential (cach chuan — agent khong thay / khong go gia tri)
 *   node login-site.js --form --cred-file <project>/.auth/credentials.local.env --site WEB-01 --account admin \
 *        [--url <trang login, mac dinh WEB-01.URL>] [--save <project>/.auth/WEB-01-admin.json]
 *        [--user-selector "#email"] [--pass-selector "#password"] [--submit-selector "button[type=submit]"] \
 *        [--success-url-contains ... | --success-selector ...]
 *
 *   # 2b) (cu, van chay) credential tu bien moi truong do USER tu export trong terminal cua ho
 *   node login-site.js --form --url ... --save ... --user-env WEB01_USER --pass-env WEB01_PASS \
 *        [--http-user-env VAR --http-pass-env VAR]
 *   --cred-file co mat thi uu tien hon --user-env / --http-*-env.
 *
 * An toan (auth-common.js): file credential phai trong .auth/, ngoai outputs/, khong bi git track;
 * <site>.ENV phai la TEST; credential chi gui toi origin cua <site>.URL; gia tri khong bao gio in / ghi.
 * Output: file storage state (cookie + localStorage) mode 0600. .auth/ PHAI nam trong .gitignore,
 * khong bao gio copy vao outputs/, khong in ra, khong ghi vao tai lieu.
 * --form: request khac GET/HEAD chi duoc phep toi origin cua form login (POST duy nhat kit cho phep).
 * Exit: 0 dang nhap OK · 1 dang nhap that bai / sai tham so · 2 thieu playwright · 3 tu choi (an toan)
 */
const fs = require('fs');
const path = require('path');
const A = require('./auth-common');

function arg(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  if (i === -1) return dflt;
  const v = process.argv[i + 1];
  return v && !v.startsWith('--') ? v : true;
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
      console.error(`Tu choi: khong nhan credential qua CLI (--${bad}). Dung --cred-file (hoac --user-env / --pass-env).`); process.exit(3);
    }
  }

  // --- che do tao template file credential ---
  const initFile = arg('init-cred-file', null);
  if (initFile) {
    const r = A.initCredFile({ file: initFile, site: arg('site', null), url: arg('url', null),
      accounts: String(arg('accounts', '') === true ? '' : arg('accounts', '')).split(','), basic: arg('basic', false) === true });
    console.log(JSON.stringify(r, null, 2));
    process.exit(0);
  }

  let url = arg('url');
  const manual = arg('manual', false) === true;
  const form = arg('form', false) === true;
  const opt = { urlContains: arg('success-url-contains', null), selector: arg('success-selector', null) };
  const timeoutMin = parseFloat(arg('timeout-min', '5'));
  const credFile = arg('cred-file', null);
  const site = arg('site', null);
  const account = arg('account', null);

  if (manual === form) { console.error('Can dung 1 trong --manual | --form'); process.exit(1); }
  let cred = null;
  if (credFile) {
    cred = A.loadCreds({ file: credFile, site, account: form ? account : null, url: url === true ? null : url, needAccount: form });
    url = cred.url;
  }
  let save = arg('save');
  if ((!save || save === true) && cred && cred.account) save = path.join(path.dirname(cred.file), `${cred.site}-${cred.account}.json`);
  if (!url || url === true || !save || save === true) {
    console.error('Can --url va --save (hoac --cred-file + --site + --account de tu suy ra)'); process.exit(1);
  }
  const absSave = path.resolve(String(save));
  if (/[\\/]outputs[\\/]/.test(absSave)) {
    console.error('Tu choi: storage state khong duoc nam trong outputs/. Dung <project>/.auth/<WEB-xx>.json'); process.exit(3);
  }
  if (path.basename(path.dirname(absSave)) !== '.auth') {
    console.error('Canh bao: nen luu vao <project>/.auth/<WEB-xx>.json (thu muc .auth/ duoc git-ignore)');
  }

  let user = null, pass = null;
  if (form && cred) { user = cred.user; pass = cred.pass; }
  else if (form) {
    const ue = arg('user-env'), pe = arg('pass-env');
    if (!ue || ue === true || !pe || pe === true) { console.error('--form can --cred-file ... --account <role> (hoac --user-env VAR va --pass-env VAR)'); process.exit(1); }
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
  const hc = cred ? cred.basic : httpCreds(arg, url);   // Basic Auth chi gui toi origin cua site
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
        if (await A.loggedIn(page, url, opt)) { ok = true; break; }
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
      const r = await A.formLogin(page, {
        loginUrl: url, user, pass, origin: cred ? cred.origin : null,
        userSel: String(arg('user-selector', A.DEF_USER)), passSel: String(arg('pass-selector', A.DEF_PASS)),
        submitSel: String(arg('submit-selector', A.DEF_SUBMIT)), opt, allow: o => { allowOrigin = o; },
      });
      ok = r.ok;
      if (!ok) console.error('Loi: ' + r.reason);
    }
  } catch (e) {
    console.error('Loi: ' + String(e.message || e).split('\n')[0]);
  }

  if (!ok) {
    await browser.close();
    console.error('Dang nhap THAT BAI' + (user ? ` (user ${A.mask(user)})` : '') + ' — khong ghi storage state.');
    process.exit(1);
  }

  fs.mkdirSync(path.dirname(absSave), { recursive: true, mode: 0o700 });
  const state = await ctx.storageState();   // chi cookie + localStorage, KHONG co mat khau
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
    ok: true, mode: manual ? 'manual' : 'form', credFile: cred ? cred.file : null, site: cred ? cred.site : null,
    account: cred ? cred.account : null, user: user ? A.mask(user) : null, basicAuth: !!hc,
    saved: absSave, fileMode: '0600', cookies: state.cookies.length, landedOn: A.strip(finalUrl),
    blockedRequests: blocked.length, gitignored: ignored,
  }, null, 2));
  process.exit(0);
})();
