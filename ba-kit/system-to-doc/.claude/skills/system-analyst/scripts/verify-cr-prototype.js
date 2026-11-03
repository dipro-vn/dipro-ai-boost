#!/usr/bin/env node
// verify-cr-prototype.js — Playwright gate cho HTML viewer CR-3.
//
// Mở HTML bằng Chromium thật, chuyển qua từng màn trong dropdown, kiểm tra:
//   • Không có JS error
//   • Mỗi màn render ảnh + ≥ 1 card panel + đúng title/code
//   • Overlay pin không vượt khung ảnh (fail nếu > 10% màn có pin tràn)
// FAIL > 0 → exit 1. Agent không được báo CR Done khi gate FAIL.
//
// Usage:
//   node verify-cr-prototype.js <CR-xxx_screens.html> [--out report.md] [--json report.json]
'use strict';
const fs = require('fs');
const path = require('path');

const argv = process.argv.slice(2);
if (!argv.length || argv[0].startsWith('-')) {
  console.error('Usage: node verify-cr-prototype.js <html> [--out r.md] [--json r.json]');
  process.exit(2);
}
const FILE = path.resolve(argv[0]);
const opt = (n, d) => { const i = argv.indexOf(n); return i > -1 ? argv[i + 1] : d; };
const OUT_MD = opt('--out'), OUT_JSON = opt('--json');

if (!fs.existsSync(FILE)) { console.error('Không thấy file: ' + FILE); process.exit(2); }

let chromium;
try { ({ chromium } = require('playwright')); }
catch (e) {
  console.error('Thiếu playwright. Cài: npm i -D playwright && npx playwright install chromium');
  process.exit(2);
}

const results = [];
let N = 0;
const add = (group, subject, action, expected, actual, status) =>
  results.push({ group, id: group[0] + String(++N).padStart(4, '0'), subject, action, expected, actual, status });

const launch = async () => {
  for (const o of [{}, { channel: 'chrome' }, { channel: 'msedge' }]) {
    try { return await chromium.launch(o); } catch (e) { /* next */ }
  }
  throw new Error('Không mở được Chromium. Chạy: npx playwright install chromium');
};

(async () => {
  const browser = await launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const jsErrs = [], consoleErrs = [];
  page.on('pageerror', e => jsErrs.push(String(e.message).slice(0, 240)));
  page.on('console', m => { if (m.type() === 'error') consoleErrs.push(m.text().slice(0, 240)); });

  const src = fs.readFileSync(FILE, 'utf8');
  const bytes = Buffer.byteLength(src);
  add('STATIC', 'Dung lượng', 'Đo kích thước HTML', '< 25 MB',
    (bytes / 1048576).toFixed(2) + ' MB', bytes < 25 * 1048576 ? 'PASS' : 'FAIL');

  await page.goto('file://' + FILE.split(path.sep).map(encodeURIComponent).join('/'), { waitUntil: 'load' });
  await page.waitForTimeout(600);

  // Contract: ORDER + SCREENS + go()
  const meta = await page.evaluate(() => ({
    hasOrder: Array.isArray(window.ORDER),
    hasScreens: window.SCREENS && typeof window.SCREENS === 'object',
    hasGo: typeof window.go === 'function',
    count: Array.isArray(window.ORDER) ? window.ORDER.length : 0,
  }));
  add('STATIC', 'Contract', 'Tìm ORDER + SCREENS + go()', 'Có đủ 3',
    `ORDER=${meta.hasOrder} SCREENS=${meta.hasScreens} go=${meta.hasGo}`,
    (meta.hasOrder && meta.hasScreens && meta.hasGo) ? 'PASS' : 'FAIL');
  if (!meta.hasOrder || !meta.hasGo) {
    await browser.close();
    report();
    return;
  }
  add('STATIC', 'Số màn', 'Đếm ORDER', '≥ 1 màn', meta.count + '', meta.count > 0 ? 'PASS' : 'FAIL');

  // For each screen: navigate + check render
  let overflowCount = 0;
  for (let i = 0; i < meta.count; i++) {
    await page.evaluate(idx => window.go(idx), i);
    await page.waitForTimeout(80);
    const info = await page.evaluate(() => {
      const code = document.getElementById('vCode')?.textContent || '';
      const stage = document.getElementById('stageWrap');
      const imgEl = stage?.querySelector('img');
      const imgReady = imgEl ? (imgEl.complete && imgEl.naturalWidth > 0) : false;
      const noimg = !!stage?.querySelector('.noimg');
      const pins = [...document.querySelectorAll('.overlay .pin')];
      const pinsOverflow = pins.filter(p => {
        const l = parseFloat(p.style.left), t = parseFloat(p.style.top);
        return isNaN(l) || isNaN(t) || l < 0 || l > 100 || t < 0 || t > 100;
      }).length;
      return {
        code,
        cards: document.querySelectorAll('.list .it').length,
        pins: pins.length,
        pinsOverflow,
        imgReady,
        noimg,
        panelEmpty: document.querySelector('.list.muted') !== null || document.querySelector('#list').children.length === 0,
      };
    });
    const expectCode = await page.evaluate(idx => window.ORDER[idx], i);
    add('NAV', expectCode, `go(${i})`, `Màn ${expectCode} + ảnh + panel`,
      `code=${info.code} cards=${info.cards} pins=${info.pins} imgReady=${info.imgReady} noimg=${info.noimg}`,
      (info.code === expectCode && (info.imgReady || info.noimg) && (info.cards > 0 || info.noimg)) ? 'PASS' : 'FAIL');
    if (info.pinsOverflow > info.pins * 0.3) {
      add('OVERLAY', expectCode, 'Đo pin tràn khung ảnh',
        '≤ 30% pin có toạ độ ngoài 0-100%',
        `${info.pinsOverflow}/${info.pins} tràn`, 'WARN');
      overflowCount++;
    }
  }

  // Runtime errors
  add('RUNTIME', 'Lỗi JS', 'Bắt pageerror', '0', jsErrs.length ? jsErrs[0] : '0', jsErrs.length ? 'FAIL' : 'PASS');
  add('RUNTIME', 'console.error', 'Bắt console error', '0', consoleErrs.length ? consoleErrs[0] : '0', consoleErrs.length ? 'FAIL' : 'PASS');

  await browser.close();
  report();

  function report() {
    const cnt = k => results.filter(r => r.status === k).length;
    const pass = cnt('PASS'), fail = cnt('FAIL'), warn = cnt('WARN');
    const byG = {};
    for (const r of results) {
      byG[r.group] = byG[r.group] || { PASS: 0, FAIL: 0, WARN: 0 };
      byG[r.group][r.status]++;
    }
    const esc = s => String(s == null ? '' : s).replace(/\|/g, '/').replace(/\n/g, ' ');
    const ICON = { PASS: '✅ PASS', FAIL: '❌ FAIL', WARN: '⚠ WARN' };
    const md = [
      '## Verify CR Prototype — Report',
      '',
      `> File: \`${path.relative(process.cwd(), FILE)}\` · ${new Date().toISOString().slice(0, 10)} · viewport 1600×1000`,
      '',
      '```',
      `Tổng: ${results.length} tests`,
      `  ✅ PASS: ${pass}`,
      `  ❌ FAIL: ${fail}   (BẮT BUỘC = 0)`,
      warn ? `  ⚠ WARN: ${warn}` : '',
      '```',
      '',
      '| Nhóm | PASS | FAIL | WARN |',
      '|---|---|---|---|',
      ...Object.keys(byG).map(g => `| ${g} | ${byG[g].PASS} | ${byG[g].FAIL} | ${byG[g].WARN} |`),
      '',
      '| ID | Nhóm | Màn | Action | Expected | Actual | Kết quả |',
      '|---|---|---|---|---|---|---|',
      ...results.map(r =>
        `| ${r.id} | ${r.group} | ${esc(r.subject)} | ${esc(r.action)} | ${esc(r.expected)} | ${esc(r.actual)} | ${ICON[r.status]} |`),
    ].filter(x => x !== '').join('\n');

    if (OUT_MD) fs.writeFileSync(OUT_MD, md + '\n');
    if (OUT_JSON) fs.writeFileSync(OUT_JSON, JSON.stringify({
      file: FILE, summary: { total: results.length, pass, fail, warn }, byG, results,
    }, null, 1));

    console.log(md.split('\n').slice(0, 16).join('\n'));
    if (fail) {
      console.log('\n❌ FAIL:');
      results.filter(r => r.status === 'FAIL').forEach(r =>
        console.log(`  ${r.id} [${r.group}] ${r.subject} — ${r.action}\n      expected: ${r.expected}\n      actual  : ${r.actual}`));
    }
    console.log(`\n${fail ? '❌ GATE FAIL' : '✅ GATE PASS'} — ${pass} pass · ${fail} fail${warn ? ' · ' + warn + ' warn' : ''}`);
    if (OUT_MD) console.log('Report: ' + OUT_MD);
    process.exit(fail ? 1 : 0);
  }
})().catch(e => { console.error('verify-cr-prototype lỗi:', e.message); process.exit(2); });
