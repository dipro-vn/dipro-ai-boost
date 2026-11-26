#!/usr/bin/env node
// Cắt ảnh từng phần tử web đã ghép và so pixel với ảnh Figma tương ứng (bằng chứng, không phải kết luận).
//
// Dùng:
//   node pixel_diff.mjs --figma figma-1440.json --dom dom-1440.json --pairs pairs-1440.json \
//        --shot dom-1440.png --figma-img figma-img --out . [--threshold 0.05] [--search 4] [--only id1,id2] [--max-margin 32] [--max-area 400000]
//
// Ảnh Figma đặt ở <figma-img>/<id, dấu ':' và ';' đổi thành '-'>.png, xuất tỉ lệ 1:1 (xem skill ui_compare).
// Ảnh Figma thường lớn hơn node vì có bóng đổ. Mỗi cặp có HAI kết quả:
//   strict  = so đúng vị trí dự kiến (đặt phần tử web vào giữa ảnh Figma, không dịch);
//   aligned = dò độ lệch ±<search>px để căn ảnh, ghi `offset` tìm được. offset khác 0 nghĩa là còn dư lề bóng hoặc item lệch.
// Tỉ lệ pixel lệch chỉ là bằng chứng bổ sung, KHÔNG nói lên mức nghiêm trọng.
//
// MỖI cặp trong pairs có đúng một bản ghi với `status`:
//   compared        đã so (có strict, aligned)
//   not_comparable  thiếu dữ liệu: chưa có ảnh Figma, khối ảo, thiếu phần tử, id không có trong dữ liệu
//   skipped         chủ động bỏ qua: nằm trong exclude, bị --only loại, ảnh quá lớn so với giới hạn xử lý
//   invalid_capture ảnh/vùng cắt không hợp lệ: ảnh Figma sai tỉ lệ so với node (không 1:1), vùng web nằm ngoài ảnh chụp,
//                   ảnh chụp sai tỉ lệ so với viewport, không đọc được ảnh
// Ra: <out>/pixel.json, <out>/act-img/<id>.png (ảnh web đã cắt, đã căn), <out>/diff/<id>.png (khác biệt sau khi căn),
//     <out>/diff-strict/<id>.png (khác biệt khi chưa căn, chỉ tạo nếu offset khác 0).
import fs from 'fs';
import path from 'path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
// Ảnh "chỗ khác nhau" cho người đọc: chính ảnh web, giữ nguyên màu, có KHUNG ĐỎ quanh từng vùng khác design.
// Tô đỏ từng pixel thì chữ nào cũng đỏ và không đọc được; khung thì nhìn ra ngay khác ở đâu.
const CELL = 8, MIN_PX = 6; // ô lưới 8px; ô có dưới 6 pixel khác là nhoè mép chữ, bỏ qua
export function markRegions(web, design, w, h, threshold) {
  const mask = new PNG({ width: w, height: h });
  pixelmatch(web.data, design.data, mask.data, w, h, { threshold, diffMask: true });
  const gw = Math.ceil(w / CELL), gh = Math.ceil(h / CELL), cnt = new Uint16Array(gw * gh);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (mask.data[(y * w + x) * 4 + 3]) cnt[((y / CELL) | 0) * gw + ((x / CELL) | 0)]++;
  const seen = new Uint8Array(gw * gh), boxes = [];
  for (let i = 0; i < cnt.length; i++) {
    if (seen[i] || cnt[i] < MIN_PX) continue;
    let x0 = gw, y0 = gh, x1 = 0, y1 = 0; const st = [i]; seen[i] = 1;
    while (st.length) { // gom các ô kề nhau (kể cả chéo) thành một vùng
      const c = st.pop(), cx = c % gw, cy = (c / gw) | 0;
      x0 = Math.min(x0, cx); y0 = Math.min(y0, cy); x1 = Math.max(x1, cx); y1 = Math.max(y1, cy);
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const nx = cx + dx, ny = cy + dy, n = ny * gw + nx;
        if (nx < 0 || ny < 0 || nx >= gw || ny >= gh || seen[n] || cnt[n] < MIN_PX) continue;
        seen[n] = 1; st.push(n);
      }
    }
    boxes.push([Math.max(0, x0 * CELL - 2), Math.max(0, y0 * CELL - 2), Math.min(w - 1, (x1 + 1) * CELL + 1), Math.min(h - 1, (y1 + 1) * CELL + 1)]);
  }
  const out = new PNG({ width: w, height: h }); web.data.copy(out.data);
  // Khung phủ gần hết ảnh (icon nhỏ, cả phần tử đều khác): viền đỏ chỉ che mất hình, để người đọc so hai ảnh cạnh nhau.
  if (boxes.some(([bx0, by0, bx1, by1]) => (bx1 - bx0 + 1) * (by1 - by0 + 1) > 0.6 * w * h)) return { png: out, regions: boxes.length };
  const dot = (x, y) => { const k = (y * w + x) * 4; out.data[k] = 230; out.data[k + 1] = 0; out.data[k + 2] = 0; out.data[k + 3] = 255; };
  for (const [bx0, by0, bx1, by1] of boxes) for (let t = 0; t < 2; t++) { // viền 2px
    for (let x = bx0; x <= bx1; x++) { dot(x, Math.min(h - 1, by0 + t)); dot(x, Math.max(0, by1 - t)); }
    for (let y = by0; y <= by1; y++) { dot(Math.min(w - 1, bx0 + t), y); dot(Math.max(0, bx1 - t), y); }
  }
  return { png: out, regions: boxes.length };
}
import { parseArgs, need, readJson, round2, splitPairs, kidsMap, expandExcludes } from './lib.mjs';

const a = parseArgs(process.argv);
need(a, ['figma', 'dom', 'pairs', 'shot', 'figma-img', 'out']);
const TH = +(a.threshold ?? 0.05), S = +(a.search ?? 4);
const only = a.only ? new Set(String(a.only).split(',')) : null;
const MAX_AREA = +(a['max-area'] ?? 400000); // --quick so cả khối lớn nên nâng giới hạn
const MAXM = +(a['max-margin'] ?? 32);
const figma = readJson(a.figma), dom = readJson(a.dom);
const { pairs, excludeSpec } = splitPairs(readJson(a.pairs));
const F = new Map(figma.nodes.map(n => [n.id, n]));
const D = new Map(dom.nodes.map(n => [n.i, n]));
const { exFigma, exDom, excludes, errors: exErrors } = expandExcludes(excludeSpec, F, D, kidsMap(figma.nodes), kidsMap(dom.nodes));
if (exErrors.length) { console.error('pixel_diff: LỖI exclude, không ghi file:\n - ' + exErrors.join('\n - ')); process.exit(1); }
const shot = PNG.sync.read(fs.readFileSync(a.shot));
// nguồn của ảnh Figma: mặc định là nguồn mặc định của figma-<size>.json (ảnh xuất từ file gốc qua connector chính thức)
const imgSrcName = a['image-source'] || figma.defaultSource || null;
const imageSource = imgSrcName ? { source: imgSrcName, ...(figma.sources?.[imgSrcName] ? { fileName: figma.sources[imgSrcName].fileName, fileKey: figma.sources[imgSrcName].fileKey } : {}) } : null;
// Ảnh chụp phải cùng tỉ lệ với viewport (không bị nhân đôi do thiết bị): nếu không, mọi tọa độ web đều sai.
const shotScaleBad = dom.page?.width && Math.abs(shot.width - dom.page.width) > 1;
fs.mkdirSync(path.join(a.out, 'act-img'), { recursive: true });
fs.mkdirSync(path.join(a.out, 'diff'), { recursive: true });
fs.mkdirSync(path.join(a.out, 'diff-strict'), { recursive: true });

// Ghép ảnh lên nền trắng (bỏ trong suốt) và cắt vùng (x,y,w,h); ngoài ảnh gốc coi là trắng.
function crop(png, x, y, w, h) {
  const o = new PNG({ width: w, height: h });
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    const sx = x + i, sy = y + j, di = (j * w + i) * 4;
    let r = 255, g = 255, b = 255;
    if (sx >= 0 && sy >= 0 && sx < png.width && sy < png.height) {
      const si = (sy * png.width + sx) * 4, al = png.data[si + 3] / 255;
      r = png.data[si] * al + 255 * (1 - al); g = png.data[si + 1] * al + 255 * (1 - al); b = png.data[si + 2] * al + 255 * (1 - al);
    }
    o.data[di] = r; o.data[di + 1] = g; o.data[di + 2] = b; o.data[di + 3] = 255;
  }
  return o;
}

const results = [];
const exNote = (k) => `exclude[${k}]: ${excludes[k]?.reason || ''}`;
for (const p of pairs) {
  const rec = { figma: p.figma ?? null, dom: p.dom ?? null, role: p.role || '', match: p.match || 'cao' };
  const out = (status, reason, extra) => results.push({ ...rec, status, ...(reason ? { reason } : {}), ...(extra || {}) });
  if (only && !(p.figma && only.has(p.figma))) { out('skipped', 'không nằm trong --only'); continue; }
  if (!p.figma) { out('not_comparable', 'design không có phần tử tương ứng'); continue; }
  if (exFigma.has(p.figma)) { out('skipped', exNote(exFigma.get(p.figma))); continue; }
  if (p.dom != null && exDom.has(p.dom)) { out('skipped', exNote(exDom.get(p.dom))); continue; }
  if (p.dom == null) { out('not_comparable', Array.isArray(p.domBox) ? 'khối ảo (domBox) không có phần tử web để cắt ảnh' : 'web không có phần tử tương ứng'); continue; }
  if (!F.has(p.figma) || !D.has(p.dom)) { out('not_comparable', 'id Figma hoặc web không có trong dữ liệu'); continue; }
  const key = p.figma.replace(/[:;]/g, '-');
  const imgFile = path.join(a['figma-img'], key + '.png');
  if (!fs.existsSync(imgFile)) { out('not_comparable', 'chưa có ảnh Figma ' + imgFile); continue; }
  const fn = F.get(p.figma), dn = D.get(p.dom);
  const figmaImage = { file: imgFile, ...(imageSource ? { source: fn.sourceOverrides?.image || imageSource.source, ...(imageSource.fileKey ? { fileKey: imageSource.fileKey } : {}) } : {}) };
  if (shotScaleBad) { out('invalid_capture', `ảnh chụp rộng ${shot.width}px khác viewport ${dom.page.width}px (sai tỉ lệ), tọa độ web không dùng được`, { figmaImage }); continue; }
  let fimg;
  try { fimg = PNG.sync.read(fs.readFileSync(imgFile)); } catch (e) { out('invalid_capture', 'không đọc được ảnh Figma: ' + e.message.split('\n')[0], { figmaImage }); continue; }
  const nodeSize = [round2(fn.w), round2(fn.h)];
  // ảnh xuất 1:1 chỉ lớn hơn node bởi lề bóng đổ (mỗi phía tối đa MAXM px); ngoài khoảng đó là sai tỉ lệ hoặc nhầm node
  if (fimg.width < Math.floor(fn.w) - 1 || fimg.height < Math.floor(fn.h) - 1) { out('invalid_capture', `ảnh Figma ${fimg.width}x${fimg.height} nhỏ hơn node ${nodeSize.join('x')}: không phải ảnh 1:1`, { figmaImage, imageSize: [fimg.width, fimg.height], nodeSize }); continue; }
  if (fimg.width > fn.w + 2 * MAXM || fimg.height > fn.h + 2 * MAXM) { out('invalid_capture', `ảnh Figma ${fimg.width}x${fimg.height} lớn hơn node ${nodeSize.join('x')} quá ${2 * MAXM}px: có thể sai tỉ lệ hoặc nhầm node`, { figmaImage, imageSize: [fimg.width, fimg.height], nodeSize }); continue; }
  if (dn.w <= 0 || dn.h <= 0) { out('invalid_capture', 'phần tử web có kích thước 0, không cắt được ảnh', { figmaImage }); continue; }
  if (fimg.width * fimg.height > MAX_AREA) { out('skipped', `ảnh ${fimg.width}x${fimg.height} vượt giới hạn xử lý ${MAX_AREA} pixel`, { figmaImage }); continue; }
  const fimgFlat = crop(fimg, 0, 0, fimg.width, fimg.height);
  // Đoán lề bóng đổ đối xứng, rồi dò ±S px.
  const mx = Math.floor((fimg.width - fn.w) / 2), my = Math.floor((fimg.height - fn.h) / 2);
  const x0 = Math.round(dn.x) - mx, y0 = Math.round(dn.y) - my;
  // vùng cắt phải nằm trong ảnh chụp (ít nhất 90% diện tích)
  const ix = Math.max(0, Math.min(shot.width, x0 + fimg.width) - Math.max(0, x0)), iy = Math.max(0, Math.min(shot.height, y0 + fimg.height) - Math.max(0, y0));
  if ((ix * iy) / (fimg.width * fimg.height) < 0.9) { out('invalid_capture', `vùng web (${Math.round(dn.x)},${Math.round(dn.y)}) nằm ngoài ảnh chụp ${shot.width}x${shot.height}`, { figmaImage, imageSize: [fimg.width, fimg.height] }); continue; }
  const cmpAt = (dx, dy) => { const c = crop(shot, x0 + dx, y0 + dy, fimg.width, fimg.height); return { c, n: pixelmatch(fimgFlat.data, c.data, null, fimg.width, fimg.height, { threshold: TH }), dx, dy }; };
  const strict = cmpAt(0, 0);
  let best = strict;
  for (let dy = -S; dy <= S; dy++) for (let dx = -S; dx <= S; dx++) {
    if (!dx && !dy) continue;
    const r = cmpAt(dx, dy);
    if (r.n < best.n || (r.n === best.n && Math.abs(dx) + Math.abs(dy) < Math.abs(best.dx) + Math.abs(best.dy))) best = r;
  }
  const area = fimg.width * fimg.height, ratio = n => round2((100 * n) / area);
  const { png: diff, regions } = markRegions(best.c, fimgFlat, fimg.width, fimg.height, TH);
  // Ảnh web cho người đọc lấy đủ phần tử web kể cả khi nó to hơn design (nếu cắt theo cỡ design thì chữ bị cụt).
  const aw = Math.max(fimg.width, Math.ceil(dn.w) + 2 * mx), ah = Math.max(fimg.height, Math.ceil(dn.h) + 2 * my);
  fs.writeFileSync(path.join(a.out, 'act-img', key + '.png'), PNG.sync.write(crop(shot, x0 + best.dx, y0 + best.dy, aw, ah)));
  fs.writeFileSync(path.join(a.out, 'diff', key + '.png'), PNG.sync.write(diff));
  let strictDiffFile = null;
  if (best.dx || best.dy) {
    const sd = markRegions(strict.c, fimgFlat, fimg.width, fimg.height, TH).png;
    strictDiffFile = path.join('diff-strict', key + '.png');
    fs.writeFileSync(path.join(a.out, strictDiffFile), PNG.sync.write(sd));
  }
  out('compared', null, {
    figmaImage, imageSize: [fimg.width, fimg.height], nodeSize, webSize: [round2(dn.w), round2(dn.h)],
    strict: { mismatchPixels: strict.n, mismatchRatio: ratio(strict.n) },
    aligned: { offset: [best.dx, best.dy], mismatchPixels: best.n, mismatchRatio: ratio(best.n), regions },
    // giữ tên cũ cho báo cáo hiện có: bằng kết quả aligned
    offset: [best.dx, best.dy], mismatchPixels: best.n, mismatchRatio: ratio(best.n),
    actFile: path.join('act-img', key + '.png'), diffFile: path.join('diff', key + '.png'), ...(strictDiffFile ? { strictDiffFile } : {}),
  });
}
const summary = { compared: 0, not_comparable: 0, skipped: 0, invalid_capture: 0 };
for (const r of results) summary[r.status]++;
fs.writeFileSync(path.join(a.out, 'pixel.json'), JSON.stringify({ threshold: TH, search: S, maxMargin: MAXM, imageSource, pairs: pairs.length, summary, results }, null, 1));
const done = results.filter(r => r.status === 'compared');
console.log(`pixel_diff: ${pairs.length} cặp | ${JSON.stringify(summary)}` +
  done.map(r => `\n  ${r.figma} ${r.role}: chưa căn ${r.strict.mismatchPixels}px (${r.strict.mismatchRatio}%), sau căn ${r.aligned.mismatchPixels}px (${r.aligned.mismatchRatio}%), offset ${r.aligned.offset}`).join('') +
  results.filter(r => r.status === 'invalid_capture').map(r => `\n  ! ${r.figma} ${r.role}: ${r.reason}`).join(''));
