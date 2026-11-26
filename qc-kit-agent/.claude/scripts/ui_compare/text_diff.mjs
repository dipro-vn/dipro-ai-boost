#!/usr/bin/env node
// So danh sách chữ của design với chữ trên web (dùng cho /ui-compare --quick): chữ nào design có mà web không có, và ngược lại.
// Kết quả là ỨNG VIÊN: dữ liệu động, placeholder của ô nhập (không nằm trong DOM text) và chữ trong ảnh phải do AI đối chiếu ảnh.
//
// Dùng: node text_diff.mjs --figma figma-390.json --dom dom-390.json --out text-390.json [--skip-under <id Figma>,<id>...]
import fs from 'fs';
import { parseArgs, need, readJson } from './lib.mjs';

const norm = s => String(s || '').replace(/\s+/g, '');
export function textDiff(figmaNodes, domNodes, skipUnder = []) {
  const parent = new Map(figmaNodes.map(n => [n.id, n.parent]));
  const skipped = id => { for (let c = id; c; c = parent.get(c)) if (skipUnder.includes(c)) return true; return false; };
  const fig = figmaNodes.filter(n => n.type === 'text' && norm(n.text) && !skipped(n.id));
  const web = domNodes.filter(n => norm(n.text));
  const page = norm(web.map(n => n.text).join(''));
  const design = norm(fig.map(n => n.text).join(''));
  return {
    figmaTexts: fig.length, webTexts: web.length,
    missingOnWeb: fig.filter(n => !page.includes(norm(n.text))).map(n => ({ figma: n.id, text: n.text })),
    extraOnWeb: web.filter(n => !design.includes(norm(n.text))).map(n => ({ dom: n.i, tag: n.tag, text: n.text })),
  };
}

if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) {
  const a = parseArgs(process.argv);
  need(a, ['figma', 'dom', 'out']);
  const r = textDiff(readJson(a.figma).nodes, readJson(a.dom).nodes, a['skip-under'] ? String(a['skip-under']).split(',') : []);
  fs.writeFileSync(a.out, JSON.stringify(r, null, 1));
  console.log(`text_diff: design ${r.figmaTexts} chữ, web ${r.webTexts} chữ | design có, web không: ${r.missingOnWeb.length} | web có, design không: ${r.extraOnWeb.length}` +
    r.missingOnWeb.map(x => `\n  - thiếu: ${JSON.stringify(x.text)} (${x.figma})`).join('') +
    r.extraOnWeb.map(x => `\n  + thừa: ${JSON.stringify(x.text)} (<${x.tag}> i=${x.dom})`).join('') + `\n  -> ${a.out}`);
}
