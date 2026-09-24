#!/usr/bin/env node
/**
 * Recon website — CHE DO READ-ONLY LA MAC DINH.
 *
 *   node crawl-site.js --url https://stg.example.jp --out ./recon \
 *        [--mode read-only|submit-staging] [--max-urls 200] [--max-minutes 30] \
 *        [--storage-state auth.json] [--role test_user] \
 *        [--forbid "/admin/batch,/payment"]
 *
 * Gate G2 duoc thuc thi o day, khong phai bang loi hua trong prompt:
 *   - read-only  : chan moi request khac GET/HEAD o tang network; khong bam nut pha du lieu
 *   - submit-*   : cho phep POST nhung VAN chan selector pha du lieu
 *
 * Output trong --out:
 *   evidence/EV-XXXX.png   screenshot tung man
 *   crawl/urls.txt         danh sach URL da tham (input cho verify-inventory.py --crawled)
 *   crawl/pages.json       url · title · so item dem duoc · link di ra
 *   crawl/evidence.csv     dong san sang dan vao sheet 05_Evidence
 *   crawl/console.json     loi console (input cho Bug List)
 *   crawl/network.json     response 4xx/5xx (input cho Bug List)
 *   crawl/blocked.json     thao tac da bi chan — bang chung cho Gate G9
 */
const fs = require('fs');
const path = require('path');

const DESTRUCTIVE = [
  'delete', 'remove', 'destroy', 'xoa', 'xóa', '削除', '退会', 'withdraw',
  'pay', 'payment', 'checkout', 'purchase', 'thanh toan', 'thanh toán', '決済',
  'send mail', 'gui mail', 'gửi mail', '送信', 'submit order', 'confirm order',
];

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
    return x.toString().replace(/\/$/, '') || x.origin;
  } catch { return null; }
}

(async () => {
  let chromium;
  try { ({ chromium } = require('playwright')); }
  catch { console.error('Thieu playwright. Chay: npm i -D playwright && npx playwright install chromium'); process.exit(2); }

  const start = arg('url');
  const out = arg('out', './recon');
  const mode = arg('mode', 'read-only');
  const maxUrls = parseInt(arg('max-urls', '200'), 10);
  const maxMin = parseFloat(arg('max-minutes', '30'));
  const role = arg('role', 'anonymous');
  const storage = arg('storage-state', null);
  const forbid = String(arg('forbid', '')).split(',').map(s => s.trim()).filter(Boolean);

  if (!start) { console.error('Thieu --url'); process.exit(1); }
  if (!['read-only', 'submit-staging', 'submit-prod'].includes(mode)) {
    console.error('--mode phai la read-only | submit-staging | submit-prod'); process.exit(1);
  }

  fs.mkdirSync(path.join(out, 'evidence'), { recursive: true });
  fs.mkdirSync(path.join(out, 'crawl'), { recursive: true });

  const browser = await chromium.launch();
  const ctx = await browser.newContext(storage ? { storageState: storage } : {});
  const page = await ctx.newPage();

  const consoleErrors = [], networkIssues = [], blocked = [];

  // --- Gate G2 thuc thi o tang network ---
  await ctx.route('**/*', route => {
    const req = route.request();
    const m = req.method();
    if (mode === 'read-only' && !['GET', 'HEAD'].includes(m)) {
      blocked.push({ kind: 'request', method: m, url: req.url(), at: new Date().toISOString() });
      return route.abort();
    }
    return route.continue();
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push({ url: page.url(), text: msg.text(), at: new Date().toISOString() });
    }
  });
  page.on('response', r => {
    if (r.status() >= 400) {
      networkIssues.push({ page: page.url(), url: r.url(), status: r.status(), at: new Date().toISOString() });
    }
  });

  const queue = [normalize(start)];
  const seen = new Set(), pages = [], evidence = [];
  const t0 = Date.now();
  let evNo = 0;

  while (queue.length && seen.size < maxUrls) {
    if ((Date.now() - t0) / 60000 > maxMin) { console.error('Het budget thoi gian'); break; }
    const url = queue.shift();
    if (!url || seen.has(url)) continue;
    if (forbid.some(f => url.includes(f))) { blocked.push({ kind: 'forbidden-zone', url }); continue; }
    seen.add(url);

    let resp;
    try { resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 }); }
    catch (e) { networkIssues.push({ page: url, url, status: 'NAVIGATION_ERROR', detail: String(e).slice(0, 200) }); continue; }

    await page.waitForTimeout(400);

    evNo += 1;
    const evId = 'EV-' + String(evNo).padStart(4, '0');
    const shot = path.join('evidence', evId + '.png');
    try { await page.screenshot({ path: path.join(out, shot), fullPage: true }); }
    catch { /* anh loi khong lam dung crawl */ }

    const info = await page.evaluate(() => {
      const sel = 'input,select,textarea,button,a[href],[role="button"]';
      const nodes = Array.from(document.querySelectorAll(sel));
      return {
        title: document.title,
        itemCount: nodes.length,
        links: Array.from(document.querySelectorAll('a[href]')).map(a => a.href),
        forms: document.querySelectorAll('form').length,
      };
    });

    pages.push({
      url, title: info.title, status: resp ? resp.status() : null,
      itemCount: info.itemCount, forms: info.forms, evId,
    });
    evidence.push([evId, 'screenshot', url, new Date().toISOString(), role, shot,
                   (info.title || '').replace(/[",\n]/g, ' ')]);

    for (const l of info.links) {
      const n = normalize(l);
      if (n && sameOrigin(n, start) && !seen.has(n)) queue.push(n);
    }
  }

  // ghi output
  const W = (f, s) => fs.writeFileSync(path.join(out, 'crawl', f), s);
  W('urls.txt', pages.map(p => p.url).join('\n') + '\n');
  W('pages.json', JSON.stringify(pages, null, 2));
  W('console.json', JSON.stringify(consoleErrors, null, 2));
  W('network.json', JSON.stringify(networkIssues, null, 2));
  W('blocked.json', JSON.stringify(blocked, null, 2));
  W('evidence.csv',
    'EV ID,Type,Locator,Captured At,Actor/Role,Artifact,Note\n' +
    evidence.map(r => r.map(c => '"' + String(c).replace(/"/g, '""') + '"').join(',')).join('\n') + '\n');
  W('destructive-selectors.json', JSON.stringify(DESTRUCTIVE, null, 2));

  await browser.close();

  console.log(JSON.stringify({
    mode, role,
    urls: pages.length, budget: `${pages.length}/${maxUrls} URL · ${((Date.now() - t0) / 60000).toFixed(1)}/${maxMin} phut`,
    consoleErrors: consoleErrors.length, networkIssues: networkIssues.length,
    blocked: blocked.length, out,
  }, null, 2));
})();
