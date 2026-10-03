/**
 * Dung chung cho login-site.js va crawl-site.js — credential cho moi truong TEST da xac nhan.
 *
 *   File credential: <project>/.auth/credentials.local.env (user tu dien, agent KHONG doc)
 *     WEB-01.URL=https://dev.example.com/admin
 *     WEB-01.ENV=TEST                  bat buoc TEST; PRODUCTION / trong -> tu choi
 *     WEB-01.BASIC_USER= / BASIC_PASS= tuy chon: HTTP Basic Auth
 *     WEB-01.<account>.USER= / .PASS=  1 cap / role
 *
 * An toan (exit 3, khong bao gio in gia tri):
 *   - file phai nam trong thu muc .auth/, KHONG nam trong outputs/, KHONG bi git track
 *   - <site>.ENV phai dung la TEST
 *   - credential chi gui toi origin cua <site>.URL (form login + Basic Auth)
 *   - quyen file rong hon 0600 -> canh bao + chmod 600
 * Gia tri chi giu trong bo nho; chi in username da mask (ab****yz).
 */
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const DEF_USER = 'input[type=email], input[autocomplete=username], input[name*=user i], input[name*=login i], ' +
  'input[name*=email i], input[id*=user i], input[id*=login i], input[id*=email i], input[type=text]';
const DEF_PASS = 'input[type=password]';
const DEF_SUBMIT = 'button[type=submit], input[type=submit], button:not([type])';
const TEST_ONLY = 'chi dung credential cho moi truong TEST da xac nhan (POLICIES.md §3.2)';
const NAME_RE = /^[A-Za-z0-9_-]+$/;

function refuse(msg) { console.error('Tu choi: ' + msg); process.exit(3); }
function fail(msg) { console.error(msg); process.exit(1); }

function mask(s) {
  s = String(s || '');
  return s.length <= 4 ? '****' : s.slice(0, 2) + '****' + s.slice(-2);
}

function strip(u) { try { const x = new URL(u); x.hash = ''; x.search = ''; return x.toString().replace(/\/$/, ''); } catch { return u; } }

function originOf(u) { try { return new URL(String(u)).origin; } catch { return null; } }

// dotenv don gian: # comment, KEY=VALUE, gia tri co the dat trong nhay; khong nhay -> bo comment " # ..."
function parseCredText(text) {
  const m = new Map();
  for (const line of String(text).split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t[0] === '#') continue;
    const i = t.indexOf('=');
    if (i < 1) continue;
    const key = t.slice(0, i).trim();
    let v = t.slice(i + 1).trim();
    if (v[0] === '"' || v[0] === "'") {
      const q = v[0], j = v.indexOf(q, 1);
      v = j > 0 ? v.slice(1, j) : v.slice(1);
    } else if (v[0] === '#') v = '';
    else v = v.replace(/\s+#.*$/, '').trim();
    m.set(key, v);
  }
  return m;
}

function git(args, cwd) {
  try { return spawnSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }); }
  catch { return { status: -1, stdout: '' }; }
}

// kiem tra vi tri file credential — dung cho ca doc lan tao template
function checkCredPath(file) {
  if (!file || file === true) fail('Can --cred-file <project>/.auth/credentials.local.env');
  const abs = path.resolve(String(file));
  const parts = abs.split(path.sep);
  if (!parts.slice(0, -1).includes('.auth')) refuse(`file credential phai nam trong thu muc .auth/ (git-ignore): ${abs}`);
  if (parts.includes('outputs')) refuse(`file credential khong duoc nam trong outputs/: ${abs}`);
  // thu muc ton tai gan nhat de chay git
  let cwd = path.dirname(abs);
  while (!fs.existsSync(cwd) && path.dirname(cwd) !== cwd) cwd = path.dirname(cwd);
  const inside = git(['rev-parse', '--is-inside-work-tree'], cwd);
  if (inside.status === 0 && String(inside.stdout).trim() === 'true') {
    if (git(['ls-files', '--error-unmatch', '--', abs], cwd).status === 0) {
      refuse(`file credential dang bi git track — chay "git rm --cached" + doi mat khau, roi them .auth/ vao .gitignore: ${abs}`);
    }
    if (git(['check-ignore', '-q', '--', abs], cwd).status !== 0) {
      console.error(`Canh bao: ${abs} chua duoc .gitignore — them ".auth/" vao .gitignore cua project.`);
    }
  }
  return abs;
}

function fixMode(abs) {
  try {
    const mode = fs.statSync(abs).mode & 0o777;
    if (mode & 0o077) {
      console.error(`Canh bao: quyen file credential la 0${mode.toString(8)} (rong hon 0600) -> chmod 600`);
      fs.chmodSync(abs, 0o600);
    }
  } catch { /* */ }
}

/**
 * Doc credential cho <site> (+ <account>). Tra ve object CHI dung trong bo nho:
 * { file, site, account, siteUrl, origin, url, basic, user, pass }
 */
function loadCreds({ file, site, account, url, needAccount }) {
  if (!site || site === true || !NAME_RE.test(String(site))) fail('Can --site <WEB-xx> khi dung --cred-file');
  if (account !== null && account !== undefined && (account === true || !NAME_RE.test(String(account)))) fail('--account sai (chi chu, so, _ -)');
  if (needAccount && !account) fail('Can --account <role> khi dung --cred-file');
  const abs = checkCredPath(file);
  if (!fs.existsSync(abs)) fail(`Chua co file ${abs}. Tao template: node login-site.js --init-cred-file ${abs} --site ${site} --url <url> --accounts <role,...>`);
  fixMode(abs);
  const m = parseCredText(fs.readFileSync(abs, 'utf8'));
  const g = k => m.get(k) || '';
  const env = g(`${site}.ENV`).trim();
  if (env.toUpperCase() !== 'TEST') {
    refuse(`${site}.ENV = ${env ? '"' + env + '"' : '(trong)'} — ${TEST_ONLY}`);
  }
  const siteUrl = g(`${site}.URL`).trim();
  const origin = originOf(siteUrl);
  if (!siteUrl || !origin || !/^https?:/.test(origin)) fail(`Thieu / sai ${site}.URL trong ${abs}`);
  const eff = url && url !== true ? String(url) : siteUrl;
  const effOrigin = originOf(eff);
  if (effOrigin !== origin) {
    refuse(`origin cua --url (${effOrigin}) khac origin cua ${site}.URL (${origin}) — credential chi duoc gui toi ${origin}`);
  }
  let basic = null;
  const bu = g(`${site}.BASIC_USER`), bp = g(`${site}.BASIC_PASS`);
  if (bu || bp) {
    if (!bu || !bp) fail(`Basic Auth can ca ${site}.BASIC_USER va ${site}.BASIC_PASS (dang thieu 1)`);
    basic = { username: bu, password: bp, origin };
  }
  let user = null, pass = null;
  if (account) {
    user = g(`${site}.${account}.USER`) || null;
    pass = g(`${site}.${account}.PASS`) || null;
    if (needAccount && (!user || !pass)) fail(`Chua dien ${site}.${account}.USER / ${site}.${account}.PASS trong ${abs}`);
  }
  console.error(`Credential: ${abs} · ${site} · ENV=TEST · origin ${origin}` +
    (account ? ` · account ${account} (user ${user ? mask(user) : '-'})` : '') + ` · Basic Auth: ${basic ? 'co' : 'khong'}`);
  return { file: abs, site: String(site), account: account ? String(account) : null, siteUrl, origin, url: eff, basic, user, pass };
}

// tao / bo sung template — KHONG ghi de gia tri da co, chi them key con thieu
function initCredFile({ file, site, url, accounts, basic }) {
  if (!site || site === true || !NAME_RE.test(String(site))) fail('Can --site <WEB-xx>');
  const accs = (accounts || []).map(s => String(s).trim()).filter(Boolean);
  for (const a of accs) if (!NAME_RE.test(a)) fail(`--accounts: ten role sai "${a}" (chi chu, so, _ -)`);
  if (url && url !== true && !/^https?:/.test(originOf(url) || '')) fail('--url sai');
  const abs = checkCredPath(file);
  fs.mkdirSync(path.dirname(abs), { recursive: true, mode: 0o700 });
  const existed = fs.existsSync(abs);
  const old = existed ? fs.readFileSync(abs, 'utf8') : '';
  const m = parseCredText(old);
  const want = [
    [`${site}.URL`, url && url !== true ? String(url) : '', ''],
    [`${site}.ENV`, '', '# điền TEST nếu đây là môi trường kiểm thử (PRODUCTION / để trống → script từ chối)'],
  ];
  if (basic) {
    want.push([`${site}.BASIC_USER`, '', '# tuỳ chọn: HTTP Basic Auth']);
    want.push([`${site}.BASIC_PASS`, '', '']);
  }
  for (const a of accs) {
    want.push([`${site}.${a}.USER`, '', `# role ${a}`]);
    want.push([`${site}.${a}.PASS`, '', '']);
  }
  const added = [];
  let body = '';
  for (const [k, v, c] of want) {
    if (m.has(k)) continue;
    added.push(k);
    body += `${k}=${v}${c ? '   ' + c : ''}\n`;
  }
  if (m.has(`${site}.URL`) && url && url !== true && originOf(m.get(`${site}.URL`)) !== originOf(url)) {
    console.error(`Canh bao: ${site}.URL da co trong file va khac origin voi --url — giu gia tri cu (sua tay neu can).`);
  }
  let text = old;
  if (!existed) {
    text = '# Môi trường kiểm thử — KHÔNG commit (.auth/ đã gitignore). Điền giá trị, AI không đọc file này.\n' +
      '# Giá trị có dấu # hoặc khoảng trắng → đặt trong dấu nháy: KEY="giá trị"\n';
  }
  if (body) {
    if (text && !text.endsWith('\n')) text += '\n';
    text += `\n# --- ${site} ---\n` + body;
  }
  if (!existed || body) fs.writeFileSync(abs, text, { mode: 0o600 });
  fs.chmodSync(abs, 0o600);
  const after = parseCredText(fs.readFileSync(abs, 'utf8'));
  const empty = Array.from(after.keys()).filter(k => k.startsWith(site + '.') && !after.get(k)
    && !/\.BASIC_(USER|PASS)$/.test(k));
  const envOk = (after.get(`${site}.ENV`) || '').toUpperCase() === 'TEST';
  return { ok: true, credFile: abs, created: !existed, added, emptyKeys: empty, envIsTest: envOk, fileMode: '0600',
    next: `Nho user mo ${abs}, dien gia tri (ENV=TEST chi khi da xac nhan la moi truong kiem thu). AI khong doc file nay.` };
}

async function firstVisible(scope, sel) {
  for (const l of await scope.locator(sel).all()) {
    try { if (await l.isVisible()) return l; } catch { /* bo qua */ }
  }
  return null;
}

async function loggedIn(page, loginUrl, opt, passSel) {
  try {
    const url = page.url();
    if (opt && opt.urlContains) return url.includes(opt.urlContains);
    if (opt && opt.selector) return !!(await firstVisible(page, opt.selector));
    if (strip(url) === strip(loginUrl) || url === 'about:blank') return false;
    return !(await firstVisible(page, passSel || DEF_PASS));
  } catch { return false; }   // dang chuyen trang
}

/**
 * Dien form login. allow(origin|null): mo / dong cho phep POST toi origin cua form (tang network).
 * origin (neu co): chi dien credential khi trang login + form action thuoc dung origin nay.
 * Tra ve { ok, reason, landedOn } — khong bao gio tra / in gia tri credential.
 */
async function formLogin(page, { loginUrl, user, pass, origin, userSel, passSel, submitSel, opt, allow }) {
  const ps = passSel || DEF_PASS, us0 = userSel || DEF_USER, ss = submitSel || DEF_SUBMIT;
  const setAllow = typeof allow === 'function' ? allow : () => {};
  try {
    if (loginUrl) {
      await page.goto(loginUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      try { await page.waitForLoadState('networkidle', { timeout: 5000 }); } catch { /* */ }
    }
    const here = page.url();
    if (origin && originOf(here) !== origin) {
      return { ok: false, reason: `trang dang nhap thuoc origin khac (${originOf(here)}) — khong dien credential` };
    }
    const pw = await firstVisible(page, ps);
    if (!pw) return { ok: false, reason: 'Khong thay o mat khau (--pass-selector)' };
    const us = await firstVisible(page, us0);
    if (!us) return { ok: false, reason: 'Khong thay o user (--user-selector)' };
    const act = await pw.evaluate(el => {
      const f = el.form; try { return new URL(f ? f.action : location.href).origin; } catch { return location.origin; }
    });
    if (origin && act !== origin) return { ok: false, reason: `form login gui toi origin khac (${act}) — khong dien credential` };
    setAllow(act);
    try {
      await us.fill(user);
      await pw.fill(pass);
      const formScope = pw.locator('xpath=ancestor::form[1]');
      let submit = (await formScope.count()) ? await firstVisible(formScope, ss) : null;
      if (!submit) submit = await firstVisible(page, ss);
      if (submit) await submit.click(); else await pw.press('Enter');
      let ok = false;
      const end = Date.now() + 20000;
      while (Date.now() < end) {
        await new Promise(r => setTimeout(r, 500));
        if (await loggedIn(page, here, opt, ps)) { ok = true; break; }
      }
      if (ok) { try { await page.waitForLoadState('networkidle', { timeout: 5000 }); } catch { /* */ } }
      return ok ? { ok: true, landedOn: strip(page.url()) } : { ok: false, reason: 'van o trang dang nhap sau 20s (sai tai khoan / can MFA?)' };
    } finally { setAllow(null); }
  } catch (e) {
    return { ok: false, reason: String(e.message || e).split('\n')[0] };
  }
}

module.exports = {
  DEF_USER, DEF_PASS, DEF_SUBMIT, TEST_ONLY,
  refuse, mask, strip, originOf, parseCredText, checkCredPath, loadCreds, initCredFile,
  firstVisible, loggedIn, formLogin,
};
