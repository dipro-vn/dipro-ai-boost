#!/usr/bin/env node
// Chuyển báo cáo /ui-compare (markdown) thành một trang HTML để đọc và gửi cho dev, PM: bảng, danh sách, và ảnh hiện
// ngay trong trang. Mỗi ảnh diff `…/pixel-<size>/diff/<id>.png` được đặt cạnh ảnh design (`figma-img/<id>.png`) và ảnh web
// (`pixel-<size>/act-img/<id>.png`) để so bằng mắt.
//
// Dùng: node report_html.mjs --md testing/<module>/<module>-uicompare-vN.md [--out <file.html>] [--inline]
// --inline: nhúng ảnh vào file HTML để gửi đi một file duy nhất. Mặc định ảnh dẫn bằng đường dẫn tương đối, nên phải giữ
//           thư mục uicompare/ cạnh file HTML.
// Chỉ hiểu phần markdown mà báo cáo dùng (tiêu đề, bảng, danh sách, **đậm**, `code`, link); dòng khác thành đoạn văn.
import fs from 'fs';
import path from 'path';
import { parseArgs, need } from './lib.mjs';

const a = parseArgs(process.argv);
need(a, ['md']);
const base = path.dirname(a.md);
const out = a.out || a.md.replace(/\.md$/i, '') + '.html';

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const exists = (rel) => fs.existsSync(path.join(base, rel));
const src = (rel) => (a.inline ? 'data:image/png;base64,' + fs.readFileSync(path.join(base, rel)).toString('base64') : esc(rel));

// Width and height from the PNG header, to blow tiny crops (a 1px border) up to a visible size.
function pngSize(rel) {
  const b = fs.readFileSync(path.join(base, rel));
  return b.length > 24 && b.toString('ascii', 12, 16) === 'IHDR' ? [b.readUInt32BE(16), b.readUInt32BE(20)] : null;
}

function figure(rel, caption) {
  const size = pngSize(rel);
  const zoom = size && Math.max(...size) < 120 ? Math.min(8, Math.ceil(120 / Math.max(...size, 1))) : 1;
  if (zoom > 1) caption += ` (phóng to ×${zoom})`;
  const dims = zoom > 1 ? ` width="${size[0] * zoom}" class="zoom"` : '';
  const img = `<img src="${src(rel)}" alt="${esc(caption)}"${dims} loading="lazy">`;
  return `<figure>${a.inline ? img : `<a href="${esc(rel)}" target="_blank">${img}</a>`}<figcaption>${esc(caption)}</figcaption></figure>`;
}

// A diff image brings its design and web crops along; any other image shows alone.
function images(rel) {
  const m = rel.match(/^(.*)\/pixel-[^/]+\/diff(?:-strict)?\/([^/]+\.png)$/i);
  if (!m) return exists(rel) ? `<span class="shots">${figure(rel, path.basename(rel))}</span>` : null;
  const trio = [
    [`${m[1]}/figma-img/${m[2]}`, 'Design'],
    [rel.replace(/\/diff(?:-strict)?\//, '/act-img/'), 'Web thật'],
    [rel, rel.includes('/diff-strict/') ? 'Web, khung đỏ = chỗ khác design (chưa dịch ảnh)' : 'Web, khung đỏ = chỗ khác design'],
  ].filter(([r]) => exists(r));
  return trio.length ? `<span class="shots">${trio.map(([r, c]) => figure(r, c)).join('')}</span>` : null;
}

// Inline markup on already-escaped text. Links only to http(s) or relative paths: report text quotes
// strings from the design and the web page, which must not become script links.
function inline(text) {
  const shots = [];
  let s = esc(text).replace(/`([^`]+)`/g, (_, code) => {
    const shot = /\.png$/i.test(code) ? images(code.replace(/&amp;/g, '&')) : null;
    if (!shot) return `<code>${code}</code>`;
    shots.push(shot);
    return `<code>${code}</code>`;
  });
  s = s.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
  // Markdown image `![alt](path.png)`: same treatment as a backticked path (design, web and boxed image side by side).
  s = s.replace(/!\[([^\]]*)\]\(([^)\s:]+\.png)\)/gi, (all, alt, rel) => images(rel.replace(/&amp;/g, '&')) || alt || all);
  // A relative path has no ":" at all, which keeps out javascript:, data: and the like.
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+|[^)\s:]+)\)/g, '<a href="$2" target="_blank">$1</a>');
  s = s.replace(/(^|[\s(（])(https?:\/\/[^\s<)）]+)/g, '$1<a href="$2" target="_blank">$2</a>');
  return s + shots.join('');
}

const cells = (line) => line.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());

function render(md) {
  const lines = md.split(/\r?\n/);
  const html = [];
  let para = [];
  const lists = []; // open list tags, innermost last: { tag, indent }
  const flushPara = () => {
    if (para.length) html.push(`<p>${inline(para.join(' '))}</p>`);
    para = [];
  };
  const closeLists = (indent = -1) => {
    while (lists.length && lists[lists.length - 1].indent > indent) html.push(`</li></${lists.pop().tag}>`);
  };
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    let m;
    if (!line.trim()) { flushPara(); closeLists(); continue; }
    if ((m = line.match(/^(#{1,6})\s+(.*)$/))) {
      flushPara(); closeLists();
      const id = m[2].match(/^([A-Z]{2,3}-\d+)/);
      html.push(`<h${m[1].length}${id ? ` id="${id[1]}"` : ''}>${inline(m[2])}</h${m[1].length}>`);
      continue;
    }
    if (/^\s*(-{3,}|\*{3,})\s*$/.test(line)) { flushPara(); closeLists(); html.push('<hr>'); continue; }
    if (line.trim().startsWith('|') && /^\s*\|?\s*:?-{3,}/.test(lines[i + 1] || '')) {
      flushPara(); closeLists();
      const head = cells(line);
      const rows = [];
      for (i += 2; i < lines.length && lines[i].trim().startsWith('|'); i++) rows.push(cells(lines[i]));
      i--;
      html.push('<div class="table"><table><thead><tr>' + head.map((c) => `<th>${inline(c)}</th>`).join('') + '</tr></thead><tbody>' +
        rows.map((r) => '<tr>' + r.map((c) => `<td>${inline(c)}</td>`).join('') + '</tr>').join('') + '</tbody></table></div>');
      continue;
    }
    if ((m = line.match(/^(\s*)([-*]|\d+\.)\s+(.*)$/))) {
      flushPara();
      const indent = m[1].length;
      const tag = /\d/.test(m[2]) ? 'ol' : 'ul';
      closeLists(indent);
      const top = lists[lists.length - 1];
      if (!top || top.indent < indent) {
        html.push(`<${tag}>`);
        lists.push({ tag, indent });
      } else html.push('</li>');
      html.push(`<li>${inline(m[3])}`);
      continue;
    }
    if (lists.length && /^\s+\S/.test(line)) { html.push(' ' + inline(line.trim())); continue; } // wrapped list item
    if ((m = line.match(/^>\s?(.*)$/))) { flushPara(); closeLists(); html.push(`<blockquote>${inline(m[1])}</blockquote>`); continue; }
    closeLists();
    para.push(line.trim());
  }
  flushPara(); closeLists();
  return html.join('\n');
}

const md = fs.readFileSync(a.md, 'utf8');
const title = (md.match(/^#\s+(.*)$/m) || [, path.basename(a.md)])[1];
const page = `<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<style>
  /* System fonts first: they carry Vietnamese and Japanese; Noto Sans JP alone breaks Vietnamese tone marks. */
  body { font: 14px/1.55 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, "Hiragino Sans", "Noto Sans JP", sans-serif; color: #1f2328; max-width: 1100px; margin: 32px auto; padding: 0 20px; }
  h1 { font-size: 22px; } h2 { font-size: 18px; margin-top: 32px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }
  h3 { font-size: 15px; margin-top: 24px; background: #f6f8fa; padding: 6px 10px; border-left: 3px solid #d0d7de; }
  .table { overflow-x: auto; } table { border-collapse: collapse; margin: 8px 0; font-size: 13px; }
  th, td { border: 1px solid #d0d7de; padding: 5px 9px; text-align: left; vertical-align: top; } th { background: #f6f8fa; }
  code { background: #f2f4f7; padding: 1px 4px; border-radius: 4px; font-size: 12px; word-break: break-all; }
  li { margin: 3px 0; }
  .shots { display: flex; flex-wrap: wrap; gap: 12px; margin: 8px 0 4px; }
  figure { margin: 0; } figcaption { font-size: 12px; color: #6b7280; text-align: center; margin-top: 2px; }
  img.zoom { image-rendering: pixelated; max-height: none; }
  figure img { display: block; max-width: 340px; max-height: 260px; border: 1px solid #d0d7de; background: repeating-conic-gradient(#f3f4f6 0 25%, #fff 0 50%) 0 0/12px 12px; }
  blockquote { margin: 8px 0; padding: 4px 12px; border-left: 3px solid #d0d7de; color: #57606a; }
  @media print { figure img { max-width: 240px; } }
</style>
</head>
<body>
${render(md)}
</body>
</html>
`;
fs.writeFileSync(out, page);
console.log(`Đã ghi ${out} (${(Buffer.byteLength(page) / 1024).toFixed(0)} KB${a.inline ? ', ảnh nhúng trong file' : ', ảnh dẫn tương đối'})`);
