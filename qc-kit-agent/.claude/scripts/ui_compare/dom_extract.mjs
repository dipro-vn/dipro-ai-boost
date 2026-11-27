#!/usr/bin/env node
// Lấy số đo và style của mọi phần tử nhìn thấy trên trang web thật, ở một kích thước màn hình.
//
// Dùng:
//   node dom_extract.mjs --url <URL> --width 1440 [--height 900] --out dom-1440.json
//        [--shot act-full-1440.png] [--wait 1500] [--steps steps.json] [--storage state.json] [--eval script.js]
//
// Ra: <out> (cây phần tử, xem skill ui_compare) và ảnh toàn trang <shot> (mặc định cùng tên, đuôi .png).
// --steps: file JSON, mảng bước thao tác trước khi đo, ví dụ
//   [{"click":"text=スポット"}, {"fill":["input[name=q]","abc"]}, {"wait":500}]
// --storage: file trạng thái đăng nhập của Playwright (QC tự đăng nhập, không đưa mật khẩu vào chat).
// --eval: file JS chạy trong trang sau các bước `--steps`, trước khi đo (dùng để tiêm lỗi giả lập khi kiểm thử bộ so sánh,
//         xem tests/run_injection_tests.mjs). Chỉ thay đổi trang trong trình duyệt đang đo, không đụng vào site thật.
// Mỗi phần tử có `uid` = số thứ tự trong cây tài liệu (tính cả phần tử bị ẩn), ổn định khi một phần tử bị ẩn đi.
import fs from 'fs';
import { parseArgs, need, launchBrowser, readJson } from './lib.mjs';

const a = parseArgs(process.argv);
need(a, ['url', 'width', 'out']);
const width = +a.width, height = +(a.height || 900);
const shot = typeof a.shot === 'string' ? a.shot : a.out.replace(/\.json$/i, '') + '.png';

const browser = await launchBrowser();
const ctx = await browser.newContext({
  viewport: { width, height }, deviceScaleFactor: 1,
  ...(a.storage ? { storageState: a.storage } : {}),
});
const page = await ctx.newPage();
await page.goto(a.url, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(+(a.wait || 1500));
await page.evaluate(() => document.fonts && document.fonts.ready);

if (a.steps) {
  for (const s of readJson(a.steps)) {
    if (s.click) await page.locator(s.click).first().click();
    else if (s.fill) await page.locator(s.fill[0]).first().fill(s.fill[1]);
    else if (s.wait) await page.waitForTimeout(s.wait);
    await page.waitForTimeout(300);
  }
  await page.waitForLoadState('networkidle').catch(() => {});
}

if (a.eval) {
  await page.evaluate(fs.readFileSync(a.eval, 'utf8'));
  await page.waitForTimeout(400);
}

await page.screenshot({ path: shot, fullPage: true, animations: 'disabled' });

const data = await page.evaluate(() => {
  const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'META', 'LINK', 'HEAD', 'TITLE']);
  const px = v => { const n = parseFloat(v); return Number.isFinite(n) ? n : 0; };
  const r2 = v => Math.round(v * 100) / 100;
  const nodes = [];
  let uidc = 0;
  function visit(el, parentIdx) {
    if (SKIP.has(el.tagName)) return;
    const uid = uidc++;
    const cs = getComputedStyle(el);
    let idx = parentIdx;
    if (cs.display !== 'none') {
      const b = el.getBoundingClientRect();
      const visible = (b.width > 0 || b.height > 0) && cs.visibility !== 'hidden';
      if (visible) {
        const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' ')
          .replace(/\s+/g, ' ').trim().slice(0, 60);
        const attrs = {};
        for (const k of ['role', 'type', 'alt', 'aria-label']) if (el.getAttribute(k)) attrs[k] = el.getAttribute(k);
        if (el.tagName === 'IMG') attrs.src = (el.currentSrc || el.src || '').split('/').pop().split('?')[0];
        idx = nodes.length;
        nodes.push({
          i: idx, uid, parent: parentIdx, tag: el.tagName.toLowerCase(), text: own, attrs,
          x: r2(b.x + scrollX), y: r2(b.y + scrollY), w: r2(b.width), h: r2(b.height),
          style: {
            color: cs.color, bg: cs.backgroundColor,
            fontSize: px(cs.fontSize), lineHeight: cs.lineHeight === 'normal' ? null : px(cs.lineHeight),
            fontWeight: +cs.fontWeight, fontFamily: cs.fontFamily.split(',')[0].replace(/["']/g, '').trim(),
            padding: [px(cs.paddingTop), px(cs.paddingRight), px(cs.paddingBottom), px(cs.paddingLeft)],
            // margin và gap không được so trực tiếp (Figma không có margin); ghi lại để AI nêu nguyên nhân của lệch khoảng cách
            margin: [px(cs.marginTop), px(cs.marginRight), px(cs.marginBottom), px(cs.marginLeft)],
            gap: [px(cs.rowGap), px(cs.columnGap)], display: cs.display,
            radius: px(cs.borderTopLeftRadius),
            borderWidth: px(cs.borderTopWidth), borderColor: cs.borderTopColor,
            opacity: +cs.opacity, boxShadow: cs.boxShadow === 'none' ? '' : cs.boxShadow,
          },
        });
      }
    }
    for (const c of el.children) visit(c, idx);
  }
  visit(document.body, -1);
  return {
    page: {
      url: location.href, title: document.title,
      width: innerWidth, height: innerHeight,
      docWidth: document.documentElement.scrollWidth, docHeight: document.documentElement.scrollHeight,
    },
    nodes,
  };
});

data.page.overflowX = data.page.docWidth > data.page.width;
data.page.shot = shot;
fs.writeFileSync(a.out, JSON.stringify(data));
console.log(`dom_extract: ${data.nodes.length} phần tử, trang ${data.page.docWidth}x${data.page.docHeight}` +
  (data.page.overflowX ? ' (CÓ TRÀN NGANG)' : '') + `\n  -> ${a.out}\n  -> ${shot}`);
await browser.close();
