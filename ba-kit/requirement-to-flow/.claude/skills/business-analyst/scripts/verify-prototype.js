#!/usr/bin/env node
/**
 * verify-prototype.js — Quality Gate cho Output 4 (HTML Prototype).
 *
 * Chạy prototype bằng Chromium thật, click thật từng điều hướng, bắn thật từng error,
 * rồi sinh Interaction Test Report. FAIL > 0 → exit code 1 → KHÔNG được báo Output 4 Done.
 *
 * Usage:
 *   node verify-prototype.js <prototype/index.html> [options]
 *     --out <file.md>     ghi Interaction Test Report dạng markdown
 *     --json <file.json>  ghi kết quả thô
 *     --shots <dir>       chụp màn hình mẫu
 *     --max-shots <n>     số ảnh chụp (mặc định 6)
 *     --quiet             chỉ in summary
 *
 * Contract: xem `.claude/ba-agent/figma-outputs/output-4-verify.md` section "Prototype Contract".
 * KHÔNG có contract = prototype không verify được = FAIL. Đây là chủ ý: gate từng cho lọt
 * một bản "spec browser" (đủ màn, 0 link gãy, nhưng không bấm được) vì chỉ cảnh báo WARN.
 */
'use strict';
const fs = require('fs');
const path = require('path');

/* ---------- args ---------- */
const argv = process.argv.slice(2);
if (!argv.length || argv[0].startsWith('-')) {
  console.error('Usage: node verify-prototype.js <prototype/index.html> [--out r.md] [--json r.json] [--shots dir]');
  process.exit(2);
}
const FILE = path.resolve(argv[0]);
const opt = (n, d) => { const i = argv.indexOf(n); return i > -1 ? argv[i + 1] : d; };
const has = n => argv.indexOf(n) > -1;
const OUT_MD = opt('--out'), OUT_JSON = opt('--json'), SHOTS = opt('--shots');
const MAX_SHOTS = parseInt(opt('--max-shots', '6'), 10);
const QUIET = has('--quiet');

if (!fs.existsSync(FILE)) { console.error('Không thấy file: ' + FILE); process.exit(2); }

let chromium;
try { ({ chromium } = require('playwright')); }
catch (e) {
  console.error('Thiếu playwright. Cài: npm i -D playwright && npx playwright install chromium');
  console.error('Hoặc chạy với NODE_PATH trỏ tới nơi đã cài playwright.');
  process.exit(2);
}

const SCREENISH = ['Toast', 'Modal', 'Popup', 'Banner', 'Full screen', 'Empty state'];
const results = [];   // {group, id, subject, action, expected, actual, status}
let N = 0;
const add = (group, subject, action, expected, actual, status) =>
  results.push({ group, id: group[0] + String(++N).padStart(4, '0'), subject, action, expected, actual, status });

const launch = async () => {
  for (const o of [{}, { channel: 'chrome' }, { channel: 'msedge' }]) {
    try { return await chromium.launch(o); } catch (e) { /* thử kiểu kế tiếp */ }
  }
  throw new Error('Không mở được Chromium. Chạy: npx playwright install chromium');
};

(async () => {
  const browser = await launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1024 } });
  const jsErrors = [], consoleErrors = [], badRequests = [];
  page.on('pageerror', e => jsErrors.push(String(e.message).slice(0, 200)));
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
  page.on('requestfailed', r => { if (!r.url().startsWith('file:')) badRequests.push(r.url()); });

  /* ---------- 1. STATIC ---------- */
  const src = fs.readFileSync(FILE, 'utf8');
  const bytes = Buffer.byteLength(src);
  const ext = [...src.matchAll(/(?:src|href)\s*=\s*"(https?:)?\/\/[^"]+"/gi)].map(m => m[0]);
  add('STATIC', 'Standalone', 'Quét tài nguyên ngoài trong HTML',
    'Không tham chiếu http(s) bên ngoài', ext.length ? ext.slice(0, 3).join(' ') : 'không có',
    ext.length ? 'FAIL' : 'PASS');
  add('STATIC', 'Kích thước', 'Đo dung lượng 1 file',
    '< 25 MB để mở mượt', (bytes / 1048576).toFixed(2) + ' MB', bytes < 25 * 1048576 ? 'PASS' : 'FAIL');
  const title = (src.match(/<title>([^<]*)<\/title>/i) || [])[1];
  add('STATIC', '<title>', 'Đọc thẻ title', 'Có tiêu đề', title || '(trống)', title ? 'PASS' : 'FAIL');

  await page.goto('file://' + FILE.split(path.sep).map(encodeURIComponent).join('/'), { waitUntil: 'load' });
  await page.waitForTimeout(400);

  /* ---------- 2. CONTRACT ---------- */
  const meta = await page.evaluate(() => {
    const P = window.__PROTO__ || window.__SPEC__ || null;
    const screens = {};
    if (P && typeof P === 'object' && !P.screens) Object.assign(screens, P);
    else if (P && P.screens) Object.assign(screens, P.screens);
    const domScreens = [...document.querySelectorAll('[id^="scr-"], section.screen, .scr')]
      .map(e => (e.id || '').replace(/^scr-/, '')).filter(Boolean);
    return {
      hasContract: !!P && typeof window.go === 'function',
      hasFireErr: typeof window.fireErr === 'function',
      codes: Object.keys(screens).length ? Object.keys(screens) : [...new Set(domScreens)],
      screens, domScreenCount: domScreens.length,
    };
  });
  // Không có contract = KHÔNG kiểm được = KHÔNG được approve.
  // Đây là lỗ hổng từng cho lọt bản "spec browser" (chỉ mô tả màn, không bấm được).
  add('STATIC', 'Prototype Contract', 'Tìm window.go + window.__PROTO__/__SPEC__',
    'Có contract để verify được (xem output-4-verify.md)',
    meta.hasContract ? 'có' : 'KHÔNG — prototype không thể verify',
    meta.hasContract ? 'PASS' : 'FAIL');

  const codes = meta.codes;
  if (!codes.length) {
    add('STATIC', 'Danh sách màn', 'Đếm màn trong prototype', '≥ 1 màn', '0', 'FAIL');
  }

  // Hình dạng: website chuyển màn, KHÔNG phải tài liệu cuộn dọc.
  const shape = await page.evaluate(() => {
    const sc = [...document.querySelectorAll('[id^="scr-"], section.screen, .scr')];
    const vis = sc.filter(e => e.offsetParent !== null || getComputedStyle(e).display !== 'none');
    return {
      total: sc.length, visible: vis.length,
      dataGo: document.querySelectorAll('[data-go]').length,
      inputs: document.querySelectorAll('input,select,textarea').length,
      buttons: document.querySelectorAll('button').length,
      anchors: document.querySelectorAll('a[href^="#"]').length,
    };
  });
  if (shape.total > 1) {
    add('SHAPE', 'Chuyển màn', 'Đếm màn đang hiển thị cùng lúc',
      'Chỉ 1 màn hiển thị (toggle display)',
      shape.visible + '/' + shape.total + ' màn hiển thị cùng lúc' +
        (shape.visible > 1 ? ' → đây là tài liệu cuộn, không phải website' : ''),
      shape.visible === 1 ? 'PASS' : 'FAIL');
  }
  add('SHAPE', 'Điều hướng', 'Đếm phần tử có data-go',
    '> 0 phần tử điều hướng được',
    shape.dataGo + ' data-go · ' + shape.anchors + ' anchor #',
    shape.dataGo > 0 ? 'PASS' : 'FAIL');
  add('SHAPE', 'UI thật', 'Đếm input + button',
    '> 0 input và > 0 button (không phải bảng mô tả)',
    shape.inputs + ' input · ' + shape.buttons + ' button',
    shape.inputs > 0 && shape.buttons > 0 ? 'PASS' : 'FAIL');

  /* ---------- 3. NAV + REACH ---------- */
  let graph = {}, navCount = 0;
  if (meta.hasContract) {
    const nav = await page.evaluate(() => {
      const M = window.__PROTO__?.screens || window.__PROTO__ || window.__SPEC__;
      const out = [], g = {};
      for (const code of Object.keys(M)) {
        window.go(code, { asPage: true });
        const sec = document.getElementById('scr-' + code) || document.getElementById(code);
        g[code] = [];
        if (!sec) continue;
        const seen = new Set();
        for (const el of sec.querySelectorAll('[data-go]')) {
          const to = el.dataset.go;
          if (seen.has(to)) continue;
          seen.add(to); g[code].push(to);
          const label = (el.textContent || el.getAttribute('title') || '').trim().slice(0, 44) || '(icon)';
          el.click();
          const scrim = document.querySelector('.scrim, [role=dialog], dialog[open]');
          let actual, kind;
          if (scrim && !document.querySelector('.scr.on#scr-' + to)) {
            kind = 'overlay';
            actual = (scrim.textContent || '').includes(to) ? to : '(overlay không rõ mã)';
            scrim.remove();
          } else {
            kind = 'page';
            const on = document.querySelector('.scr.on, .screen.on, [id^=scr-].on');
            actual = on ? on.id.replace(/^scr-/, '') : '(không đổi màn)';
          }
          out.push({ from: code, to, label, kind, actual, pass: actual === to });
          window.go(code, { asPage: true });
        }
      }
      return { out, g };
    });
    graph = nav.g; navCount = nav.out.length;
    for (const t of nav.out) {
      add('NAV', t.from, 'Bấm "' + t.label + '"',
        'Mở ' + t.to + (t.kind === 'overlay' ? ' (overlay)' : ''), t.actual, t.pass ? 'PASS' : 'FAIL');
    }
  }

  const entry = await page.evaluate(() =>
    [...document.querySelectorAll('nav a[data-go], .appnav a[data-go], [data-entry]')]
      .map(a => a.dataset.go).filter(Boolean));
  if (meta.hasContract && codes.length) {
    const dead = codes.filter(c => (graph[c] || []).length === 0);
    const roots = entry.length ? entry : [codes[0]];
    const seen = new Set(roots); const q = [...roots];
    while (q.length) for (const t of graph[q.shift()] || []) if (!seen.has(t)) { seen.add(t); q.push(t); }
    const unreach = codes.filter(c => !seen.has(c));
    add('REACH', 'Cụt đường', 'Duyệt đồ thị điều hướng',
      'Mọi màn có ≥ 1 lối ra', dead.length ? dead.slice(0, 8).join(' ') : 'không có',
      dead.length ? 'FAIL' : 'PASS');
    add('REACH', 'Không tới được', 'BFS từ menu chính',
      'Mọi màn tới được từ điểm vào', unreach.length ? unreach.slice(0, 8).join(' ') : 'không có',
      unreach.length ? 'FAIL' : 'PASS');
    const dangling = [...new Set(Object.values(graph).flat())].filter(c => !codes.includes(c));
    add('REACH', 'Mã màn gãy', 'Đối chiếu data-go với danh sách màn',
      'Mọi data-go trỏ tới màn có thật', dangling.length ? dangling.join(' ') : 'không có',
      dangling.length ? 'FAIL' : 'PASS');
  }

  /* ---------- 4. ERROR SIMULATION ---------- */
  if (meta.hasContract && meta.hasFireErr) {
    const er = await page.evaluate(() => {
      const M = window.__PROTO__?.screens || window.__PROTO__ || window.__SPEC__;
      const out = [];
      const clean = () => {
        document.querySelectorAll('.scrim, .toast, .pagebanner').forEach(n => n.remove());
      };
      for (const code of Object.keys(M)) {
        const m = M[code]; const errs = m.errs || m.errors || [];
        if (!errs.length) continue;
        window.go(code, { asPage: true });
        errs.forEach((e, i) => {
          const [id, grp, trig, disp, msg] = e;
          if (m.unk || m.unknown) {
            out.push({ code, id, grp, trig, disp, msg, status: 'SKIP',
                       actual: 'UNKNOWN/chưa chốt — không implement (Rule P2)' });
            return;
          }
          clean();
          try { window.fireErr(code, i); } catch (err) {
            out.push({ code, id, grp, trig, disp, msg, status: 'FAIL', actual: 'throw: ' + err.message });
            return;
          }
          const sec = document.getElementById('scr-' + code);
          const seen = {
            toast: !!document.querySelector('.toast'),
            overlay: !!document.querySelector('.scrim, [role=dialog], [role=alertdialog]'),
            banner: !!(sec && sec.querySelector('.pagebanner, .note.e, .banner')),
            inline: !!(sec && sec.querySelector('[data-inline-error], .inline-error')) ||
                    !!(sec && [...sec.querySelectorAll('div,span')].some(
                      d => d.style && /red/.test(d.style.color || ''))),
            disabled: !!(sec && sec.querySelector('button:disabled')),
          };
          const any = Object.values(seen).some(Boolean);
          out.push({ code, id, grp, trig, disp, msg, status: any ? 'PASS' : 'FAIL',
                     actual: Object.keys(seen).filter(k => seen[k]).join('+') || 'không hiển thị gì' });
          clean();
        });
      }
      return out;
    });
    for (const t of er) {
      add('ERR', t.code, (t.id ? t.id + ' · ' : '') + String(t.trig || '').slice(0, 40),
        'Hiển thị ' + t.disp, t.actual,
        t.status === 'SKIP' ? 'SKIPPED' : t.status);
    }
    // Rule P2: màn UNKNOWN phải hiện placeholder
    const unkScreens = await page.evaluate(() => {
      const M = window.__PROTO__?.screens || window.__PROTO__ || window.__SPEC__;
      return Object.keys(M).filter(c => M[c].unk || M[c].unknown);
    });
    for (const c of unkScreens) {
      const ok = await page.evaluate(code => {
        window.go(code, { asPage: true });
        const sec = document.getElementById('scr-' + code);
        return !!sec && /UNKNOWN|chờ BRSE|chưa chốt/i.test(sec.textContent || '');
      }, c);
      add('P2', c, 'Tìm placeholder UNKNOWN trên màn',
        'Hiện "⚠ UNKNOWN BEHAVIOR — chờ BRSE confirm"',
        ok ? 'có placeholder' : 'KHÔNG có', ok ? 'PASS' : 'FAIL');
    }
  }

  /* ---------- 5. RESPONSIVE ---------- */
  for (const w of [1440, 1024, 375]) {
    await page.setViewportSize({ width: w, height: 900 });
    await page.waitForTimeout(160);
    const over = await page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth);
    add('RESP', w + 'px', 'Đo tràn ngang toàn trang',
      'Không cuộn ngang (≤ 2px)', over + 'px', over <= 2 ? 'PASS' : 'FAIL');
  }
  await page.setViewportSize({ width: 1440, height: 1024 });

  /* ---------- 6. JS RUNTIME ---------- */
  add('RUNTIME', 'Lỗi JS', 'Bắt pageerror suốt phiên kiểm',
    '0 lỗi', jsErrors.length ? jsErrors[0] : '0', jsErrors.length ? 'FAIL' : 'PASS');
  add('RUNTIME', 'console.error', 'Bắt console error',
    '0 lỗi', consoleErrors.length ? consoleErrors[0] : '0', consoleErrors.length ? 'FAIL' : 'PASS');
  add('RUNTIME', 'Request hỏng', 'Bắt request failed',
    '0 request ra ngoài', badRequests.length ? badRequests[0] : '0', badRequests.length ? 'FAIL' : 'PASS');

  /* ---------- 7. SCREENSHOTS ---------- */
  const shots = [];
  if (SHOTS && meta.hasContract) {
    fs.mkdirSync(SHOTS, { recursive: true });
    const step = Math.max(1, Math.floor(codes.length / MAX_SHOTS));
    for (let i = 0; i < codes.length && shots.length < MAX_SHOTS; i += step) {
      const c = codes[i];
      await page.evaluate(x => window.go(x, { asPage: true }), c);
      await page.waitForTimeout(150);
      const f = path.join(SHOTS, c + '.png');
      await page.screenshot({ path: f });
      shots.push(f);
    }
  }

  await browser.close();

  /* ---------- 8. REPORT ---------- */
  const cnt = k => results.filter(r => r.status === k).length;
  const pass = cnt('PASS'), fail = cnt('FAIL'), skip = cnt('SKIPPED'), warn = cnt('WARN');
  const byGroup = {};
  for (const r of results) {
    byGroup[r.group] = byGroup[r.group] || { PASS: 0, FAIL: 0, SKIPPED: 0, WARN: 0 };
    byGroup[r.group][r.status]++;
  }

  const esc = s => String(s == null ? '' : s).replace(/\|/g, '/').replace(/\n/g, ' ');
  const ICON = { PASS: '✅ PASS', FAIL: '❌ FAIL', SKIPPED: '⚠ SKIPPED', WARN: '⚠ WARN' };
  const md = [
    '## Interaction Test Report — Output 4',
    '',
    '> Chạy tự động bằng Playwright + Chromium trên chính file prototype.',
    '> File: `' + path.relative(process.cwd(), FILE) + '` · ' + new Date().toISOString().slice(0, 10) +
      ' · viewport 1440×1024 · ' + codes.length + ' màn',
    '',
    '```',
    'Tổng: ' + results.length + ' tests',
    '  ✅ PASS   : ' + pass,
    '  ❌ FAIL   : ' + fail + '   (BẮT BUỘC = 0 trước khi Approve)',
    '  ⚠ SKIPPED: ' + skip + '   (UNKNOWN/INFERENCE — Rule P2)',
    warn ? '  ⚠ WARN   : ' + warn : '',
    '```',
    '',
    '| Nhóm | PASS | FAIL | SKIPPED | WARN |',
    '|---|---|---|---|---|',
    ...Object.keys(byGroup).map(g =>
      `| ${g} | ${byGroup[g].PASS} | ${byGroup[g].FAIL} | ${byGroup[g].SKIPPED} | ${byGroup[g].WARN} |`),
    '',
    '| Test ID | Màn | Action | Expected | Actual | Kết quả |',
    '|---|---|---|---|---|---|',
    ...results.map(r =>
      `| ${r.id} | ${esc(r.subject)} | ${esc(r.action)} | ${esc(r.expected)} | ${esc(r.actual)} | ${ICON[r.status]} |`),
    '',
  ].filter(x => x !== '').join('\n');

  if (OUT_MD) fs.writeFileSync(OUT_MD, md + '\n');
  if (OUT_JSON) fs.writeFileSync(OUT_JSON, JSON.stringify({
    file: FILE, screens: codes.length, navTested: navCount,
    summary: { total: results.length, pass, fail, skip, warn }, byGroup, results, shots,
  }, null, 1));

  if (!QUIET) {
    console.log(md.split('\n').slice(0, 24).join('\n'));
    if (fail) {
      console.log('\n❌ FAIL:');
      for (const r of results.filter(x => x.status === 'FAIL').slice(0, 20))
        console.log(`  ${r.id} [${r.group}] ${r.subject} — ${r.action}\n      mong đợi: ${r.expected}\n      thực tế : ${r.actual}`);
    }
  }
  console.log(`\n${fail ? '❌ GATE FAIL' : '✅ GATE PASS'} — ${pass} pass · ${fail} fail · ${skip} skipped${warn ? ' · ' + warn + ' warn' : ''}`);
  if (OUT_MD) console.log('Report: ' + OUT_MD);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('verify-prototype lỗi:', e.message); process.exit(2); });
