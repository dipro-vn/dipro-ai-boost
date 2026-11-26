#!/usr/bin/env node
// Tổng hợp phạm vi và mức độ kiểm tra từ kết quả của các script (xem skill ui_compare). Số liệu tính ở đây,
// AI chỉ chép bảng vào báo cáo và giải thích giới hạn; không tự ước lượng từ nội dung báo cáo.
//
// Dùng:
//   node coverage.mjs --result result-1440.json --figma figma-1440.json [--pixel pixel-1440/pixel.json] --out coverage-1440
// Ra: <out>.json (số liệu, có mục `reconcile` tự đối chiếu giữa các file) và <out>.md (bảng markdown để chép vào báo cáo).
//
// Quy ước: bảng "phép kiểm tra" đếm theo loại trên các cặp ghép chắc chắn (cặp match "thấp" đếm riêng, không vào bảng).
// Mẫu số mỗi loại = đạt + lệch + lệch do cha + không so được + bỏ qua. "Không áp dụng" không vào mẫu số.
// Không so được và bỏ qua KHÔNG được tính là đạt. Đây là coverage của PHÉP KIỂM TRA, không phải của màn hình.
import fs from 'fs';
import { parseArgs, need, readJson } from './lib.mjs';

const a = parseArgs(process.argv);
need(a, ['result', 'figma', 'out']);
const result = readJson(a.result), figma = readJson(a.figma);
const pixel = a.pixel && fs.existsSync(a.pixel) ? readJson(a.pixel) : null;

const LABEL = { position: 'Vị trí', size: 'Kích thước', padding: 'Đệm', radius: 'Bo góc', border: 'Viền', background: 'Màu nền',
  text_color: 'Màu chữ', font_size: 'Cỡ chữ (kèm chiều cao dòng, font)', font_weight: 'Độ đậm chữ', opacity: 'Độ mờ', text_content: 'Nội dung chữ' };
const CHECKS = result.meta.checkTypes || Object.keys(LABEL);
const pct = (n, d) => (d ? Math.round((100 * n) / d) : 0);
const cell = (n, d) => `${n}/${d} (${pct(n, d)}%)`;

// ---- phép kiểm tra theo loại (đếm lại từ pairs[].checks, đối chiếu với meta.summary)
const normal = result.pairs.filter(p => !p.uncertain), low = result.pairs.filter(p => p.uncertain);
const byCheck = {};
for (const c of CHECKS) {
  const t = { passed: 0, mismatch: 0, mismatch_inherited: 0, not_comparable: 0, skipped: 0, not_applicable: 0 };
  for (const p of normal) {
    const k = p.checks[c];
    if (k.status === 'mismatch') t[k.inherited ? 'mismatch_inherited' : 'mismatch']++; else t[k.status]++;
  }
  t.denominator = t.passed + t.mismatch + t.mismatch_inherited + t.not_comparable + t.skipped;
  t.executed = t.passed + t.mismatch + t.mismatch_inherited;   // đã thật sự so
  byCheck[c] = t;
}
const total = Object.fromEntries(['passed', 'mismatch', 'mismatch_inherited', 'not_comparable', 'skipped', 'not_applicable', 'denominator', 'executed']
  .map(k => [k, CHECKS.reduce((s, c) => s + byCheck[c][k], 0)]));

// ---- phạm vi phần tử
const E = result.elements || null;
const elements = E ? {
  figmaNodes: E.figma, extraOnWeb: E.extra_on_web,
  unmatchedFigma: E.unmatchedFigma.length, excluded: E.excluded.map(e => ({ index: e.index, reason: e.reason, figmaNodes: e.figmaNodes, domNodes: e.domNodes })),
  warnings: E.warnings,
  domCandidates: { total: result.unmatchedDomCandidates?.total ?? 0, groups: (result.unmatchedDomCandidates?.groups || []).map(g => ({ key: g.key, count: g.count })) },
} : null;

// ---- pixel
const px = pixel ? {
  summary: pixel.summary, pairs: pixel.pairs,
  compared: pixel.results.filter(r => r.status === 'compared').map(r => ({ figma: r.figma, role: r.role, strict: r.strict, aligned: r.aligned, source: r.figmaImage?.source ?? null })),
  invalid: pixel.results.filter(r => r.status === 'invalid_capture').map(r => ({ figma: r.figma, reason: r.reason })),
} : null;

// ---- nguồn dữ liệu Figma
const nodes = figma.nodes;
const pairsStyleMissing = normal.filter(p => Object.values(p.checks).some(k => /chưa lấy style/.test(k.reason || ''))).length;
const source = {
  sources: figma.sources || null, defaultSource: figma.defaultSource || null,
  nodes: nodes.length, styleFetched: nodes.filter(n => n.styleFetched ?? !!n.style).length,   // dữ liệu cũ: coi node có style là đã lấy
  styleFromOtherSource: nodes.filter(n => n.sourceOverrides?.style).length,
  mappingWarnings: (figma.sourceMappingWarnings || []).length,
  warnings: (figma.warnings || []).map(w => ({ type: w.type, count: w.count ?? 1 })),
  pairsWithoutStyle: pairsStyleMissing,
  legacyFormat: !figma.sources,
};

// ---- đối chiếu số liệu giữa các file: mọi con số phải truy ngược được
const rec = [];
const chk = (name, ok, detail) => rec.push({ name, ok: !!ok, ...(ok ? {} : { detail }) });
chk('số cặp trong result khớp meta', result.pairs.length === result.meta.pairs, `pairs=${result.pairs.length} meta=${result.meta.pairs}`);
chk('tổng các loại phép kiểm tra khớp meta.summary', CHECKS.every(c => ['passed', 'mismatch', 'mismatch_inherited', 'not_comparable', 'skipped', 'not_applicable'].every(k => byCheck[c][k] === result.meta.summary[c][k])), 'lệch giữa đếm lại và meta.summary');
chk('mỗi cặp có đủ loại phép kiểm tra', result.pairs.every(p => CHECKS.every(c => p.checks[c])), 'có cặp thiếu loại');
chk('checks khớp findings (meta.consistency)', result.meta.consistency?.ok, JSON.stringify(result.meta.consistency));
if (E) {
  chk('số node Figma trong result khớp file Figma', E.figma.total === nodes.length, `result=${E.figma.total} figma=${nodes.length}`);
  const st = E.figma;
  chk('mỗi node Figma đúng một trạng thái', st.matched + st.uncertain + st.missing_on_web + st.text_via_parent + st.excluded + st.unmatched_figma === st.total, 'tổng trạng thái khác tổng node');
}
if (px) {
  chk('mọi cặp có đúng một bản ghi pixel', px.pairs === result.meta.pairs && pixel.results.length === px.pairs, `pixel=${pixel.results.length} pairs=${result.meta.pairs}`);
  chk('tổng trạng thái pixel khớp số bản ghi', Object.values(px.summary).reduce((s, n) => s + n, 0) === pixel.results.length, 'summary khác số bản ghi');
}
const reconcile = { ok: rec.every(r => r.ok), checks: rec };

// ---- giới hạn tự động (AI giải thích thêm, không thay thế)
const limits = [];
if (source.legacyFormat) limits.push('Dữ liệu Figma ở định dạng cũ, chưa ghi nguồn (sources) và cờ styleFetched; thuộc tính Figma không ghi được coi là chưa có dữ liệu.');
if (source.pairsWithoutStyle) limits.push(`${source.pairsWithoutStyle} cặp có node Figma chưa lấy style, các phép về style của cặp đó là "không so được".`);
if (source.styleFromOtherSource) limits.push(`${source.styleFromOtherSource} node lấy style từ nguồn phụ (bản copy), cần kiểm lại với file gốc.`);
if (source.mappingWarnings) limits.push(`${source.mappingWarnings} cảnh báo ánh xạ: kích thước bản copy lệch bản gốc.`);
for (const w of source.warnings) if (w.type === 'text-without-content') limits.push(`${w.count} node chữ Figma chưa có nội dung (text): không so được chữ ở các cặp đó.`);
if (low.length) limits.push(`${low.length} cặp ghép chưa chắc (không tính vào bảng phép kiểm tra).`);
if (elements) {
  if (elements.unmatchedFigma) limits.push(`${elements.unmatchedFigma} node Figma chưa ghép với phần tử web.`);
  if (elements.domCandidates.total) limits.push(`${elements.domCandidates.total} khối web lớn chưa ghép (ứng viên cần xác minh, chưa phải kết luận thừa item).`);
  for (const e of elements.excluded) limits.push(`Loại khỏi phạm vi: ${e.reason} (${e.figmaNodes} node Figma, ${e.domNodes} phần tử web).`);
  for (const w of elements.warnings) limits.push('Cảnh báo phạm vi: ' + w);
}
if (px) {
  limits.push(`So pixel: ${px.summary.compared}/${px.pairs} cặp đã so; ${px.summary.not_comparable} không so được, ${px.summary.skipped} bỏ qua, ${px.summary.invalid_capture} ảnh không hợp lệ.`);
} else limits.push('Chưa chạy so pixel.');

const out = { inputs: { result: a.result, figma: a.figma, pixel: pixel ? a.pixel : null }, pairs: result.pairs.length, uncertainPairs: low.length,
  checks: byCheck, total, elements, pixel: px, source, limits, reconcile };
fs.writeFileSync(a.out + '.json', JSON.stringify(out, null, 1));

// ---- markdown
const L = [];
L.push('## Phạm vi và mức độ kiểm tra', '');
L.push('> Số liệu do script `coverage.mjs` tính từ kết quả so sánh. Đây là thống kê **phép kiểm tra**, không phải tỉ lệ màn hình đã kiểm. Phép "không so được" và "bỏ qua" không được tính là đạt.', '');
if (elements) {
  const f = elements.figmaNodes;
  L.push('### Phạm vi phần tử (theo node Figma)', '', '| Trạng thái | Số node |', '|---|---|');
  L.push(`| Đã ghép chắc chắn | ${f.matched} |`, `| Ghép chưa chắc | ${f.uncertain} |`, `| Có ở design, không có trên web | ${f.missing_on_web} |`,
    `| Chữ được so qua cặp cha | ${f.text_via_parent} |`, `| Loại khỏi phạm vi (có lý do) | ${f.excluded} |`, `| Chưa ghép | ${f.unmatched_figma} |`, `| **Tổng node Figma** | **${f.total}** |`, '');
  L.push(`Phía web: ${elements.extraOnWeb} phần tử ghép mà design không có; ${elements.domCandidates.total} khối lớn chưa ghép (ứng viên, ${elements.domCandidates.groups.length} nhóm).`, '');
}
L.push('### Phép kiểm tra theo loại', '', `Tính trên ${normal.length} cặp ghép chắc chắn (${low.length} cặp ghép chưa chắc không tính).`, '');
L.push('| Loại | Đạt | Lệch | Lệch do cha/khối thiếu | Không so được | Bỏ qua | Không áp dụng |', '|---|---|---|---|---|---|---|');
for (const c of CHECKS) {
  const t = byCheck[c], d = t.denominator;
  L.push(`| ${LABEL[c] || c} | ${cell(t.passed, d)} | ${cell(t.mismatch, d)} | ${cell(t.mismatch_inherited, d)} | ${cell(t.not_comparable, d)} | ${cell(t.skipped, d)} | ${t.not_applicable} |`);
}
L.push(`| **Tổng** | ${cell(total.passed, total.denominator)} | ${cell(total.mismatch, total.denominator)} | ${cell(total.mismatch_inherited, total.denominator)} | ${cell(total.not_comparable, total.denominator)} | ${cell(total.skipped, total.denominator)} | ${total.not_applicable} |`, '');
L.push(`Đã thật sự so: ${total.executed}/${total.denominator} phép (${pct(total.executed, total.denominator)}%).`, '');
if (px) {
  L.push('### So pixel', '', `| Đã so | Không so được | Bỏ qua | Ảnh không hợp lệ | Tổng cặp |`, '|---|---|---|---|---|', `| ${px.summary.compared} | ${px.summary.not_comparable} | ${px.summary.skipped} | ${px.summary.invalid_capture} | ${px.pairs} |`, '');
  for (const r of px.compared) L.push(`- ${r.role || r.figma}: chưa căn ${r.strict.mismatchPixels} pixel lệch (${r.strict.mismatchRatio}%), sau căn ${r.aligned.mismatchPixels} (${r.aligned.mismatchRatio}%), offset ${r.aligned.offset}. Tỉ lệ pixel chỉ là bằng chứng, không phản ánh mức nghiêm trọng.`);
  for (const r of px.invalid) L.push(`- Ảnh không hợp lệ ${r.figma}: ${r.reason}`);
  L.push('');
}
L.push('### Nguồn dữ liệu design', '');
if (source.sources) for (const [k, v] of Object.entries(source.sources)) L.push(`- **${k}**${k === source.defaultSource ? ' (mặc định, hình học)' : ''}: file ${v.fileName || '?'} (${v.fileKey}), lấy ngày ${v.retrievedAt}`);
else L.push('- Chưa ghi nguồn (dữ liệu định dạng cũ).');
L.push(`- ${source.styleFetched}/${source.nodes} node đã lấy style${source.legacyFormat ? ' (ước tính từ dữ liệu cũ)' : ''}; ${source.styleFromOtherSource} node có style từ nguồn phụ.`, '');
L.push('### Giới hạn của lần so này', '', ...limits.map(x => '- ' + x), '');
L.push('### Đối chiếu số liệu', '', reconcile.ok ? `Các số liệu trên khớp nhau giữa result, pixel và dữ liệu Figma (${rec.length} phép đối chiếu).` : '**CÓ SỐ LIỆU KHÔNG KHỚP:** ' + rec.filter(r => !r.ok).map(r => `${r.name} (${r.detail})`).join('; '), '');
fs.writeFileSync(a.out + '.md', L.join('\n'));
console.log(`coverage: ${result.pairs.length} cặp | phép kiểm tra đã so ${total.executed}/${total.denominator} | không so được ${total.not_comparable} | bỏ qua ${total.skipped} | đối chiếu ${reconcile.ok ? 'OK' : 'LỖI'}\n  -> ${a.out}.json, ${a.out}.md`);
if (!reconcile.ok) process.exit(3);
