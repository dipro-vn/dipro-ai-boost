#!/usr/bin/env node
// H06 — chan 秘密情報・個人情報 cua khach hang loi ra ngoai.
//
// Hai che do:
//   1) Hook PreToolUse  : doc payload tu stdin, exit 2 => tool call bi chan
//   2) CLI scan         : node detect-pii.js --scan <path...>  => quet file truoc khi ban giao
//                         (ca .xlsx/.docx/.pptx: doc text trong XML cua file zip, khong can npm)
//
// Nguon pattern: .claude/config/pii-patterns.json (dung chung voi rules/DATA-PRIVACY.md)
// Rule: POLICIES.md §3.6 · .claude/rules/DATA-PRIVACY.md
//
// GIOI HAN DA BIET — doc ky truoc khi tin:
//   - Chi doc duoc TEXT trong tool call. KHONG mo duoc noi dung file anh (.png/.jpg).
//     Screenshot chua email that van lot qua. Chan bang quy trinh (tai khoan test), khong bang script.
//   - Chi bat duoc nhom (1)(3)(4) vi chung co hinh dang. Nhom (2) du lieu production va
//     (5) KH xac dinh confidential KHONG co hinh dang -> chan o Discovery Brief.

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const CFG = path.join(__dirname, '..', 'config', 'pii-patterns.json');

function loadCfg() {
  const cfg = JSON.parse(fs.readFileSync(CFG, 'utf8'));
  cfg._deny = (cfg.denyPatterns || []).map((p) => {
    let src = p.re, flags = 'g';
    if (src.startsWith('(?i)')) { src = src.slice(4); flags += 'i'; }
    return { ...p, rx: new RegExp(src, flags) };
  });
  cfg._allowPath = (cfg.allowPathPatterns || []).map((r) => new RegExp(r));
  cfg._scanTool = (cfg.scanToolPatterns || []).map((r) => new RegExp(r));
  return cfg;
}

/** Bo gia tri mau chuan ra khoi text truoc khi quet -> tranh bao dong gia. */
function stripAllowed(text, cfg) {
  let out = text;
  for (const v of cfg.allowValues || []) {
    out = out.split(v).join(' ');
  }
  return out;
}

/** Che gia tri bat duoc — KHONG in nguyen PII ra transcript. */
function mask(s) {
  const t = String(s).trim();
  if (t.length <= 4) return '*'.repeat(t.length);
  return t.slice(0, 2) + '*'.repeat(Math.min(t.length - 4, 12)) + t.slice(-2);
}

function scanText(text, cfg) {
  if (!text) return [];
  const cleaned = stripAllowed(String(text), cfg);
  const hits = [];
  for (const p of cfg._deny) {
    p.rx.lastIndex = 0;
    const found = cleaned.match(p.rx);
    if (found && found.length) {
      hits.push({ id: p.id, group: p.group, desc: p.desc, count: found.length, sample: mask(found[0]) });
    }
  }
  return hits;
}

/** Lay phan text can quet theo tung loai tool. */
function extract(toolName, input) {
  if (!input) return '';
  switch (toolName) {
    case 'Write':        return String(input.content || '');
    case 'Edit':         return String(input.new_string || '');
    case 'MultiEdit':    return (input.edits || []).map((e) => e.new_string || '').join('\n');
    case 'NotebookEdit': return String(input.new_source || '');
    case 'Bash':         return String(input.command || '');
    default:             return JSON.stringify(input);   // MCP: figma / backlog / slack / drive
  }
}

function report(hits, where) {
  const byGroup = { 1: 'PII (ten/email/SDT/dia chi)', 3: 'Credential', 4: 'Giao dich' };
  const lines = [
    'H06 CHAN: phat hien 秘密情報・個人情報 trong ' + where,
    '',
    'Pattern khop:',
  ];
  for (const h of hits) {
    lines.push(`  - ${h.id} [nhom ${h.group} — ${byGroup[h.group] || '?'}] x${h.count}  vi du: ${h.sample}`);
  }
  lines.push(
    '',
    'POLICIES.md §3.6 — khong dua du lieu that cua khach hang vao AI / vao output.',
    'Cach xu ly (KHONG duoc hoi user de xin phep tiep tuc):',
    '  1. Thay bang bo du lieu mau chuan — .claude/rules/DATA-PRIVACY.md §4',
    '  2. Neu la credential: xoa han, khong thay bang gia tri khac',
    '  3. Neu khong chac day co phai du lieu that khong -> hoi user de PHAN LOAI',
    '  4. Neu da lo day ra ngoai (Figma/Backlog/commit) -> DUNG, bao PM theo POLICY.md §9',
    '',
    'Bao dong gia? Them gia tri mau vao allowValues trong .claude/config/pii-patterns.json.'
  );
  return lines.join('\n');
}

// ---------------- Doc text tu xlsx/docx/pptx (zip) — chi dung built-in ----------------
const OOXML_PART = /^(xl\/sharedStrings\.xml|xl\/worksheets\/[^/]+\.xml|xl\/comments\d*\.xml|word\/(document|header\d*|footer\d*|footnotes|endnotes|comments)\.xml|ppt\/(slides|notesSlides)\/[^/]+\.xml)$/;

/** Doc central directory cua zip -> [{name, data}] cho cac part khop filter. */
function readZip(buf, filter) {
  let eocd = -1;
  for (let i = buf.length - 22; i >= Math.max(0, buf.length - 65557); i--) {
    if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error('khong phai zip');
  const total = buf.readUInt16LE(eocd + 10);
  let off = buf.readUInt32LE(eocd + 16);
  const out = [];
  for (let k = 0; k < total; k++) {
    if (buf.readUInt32LE(off) !== 0x02014b50) throw new Error('central directory hong');
    const method = buf.readUInt16LE(off + 10);
    const csize = buf.readUInt32LE(off + 20);
    const nlen = buf.readUInt16LE(off + 28), xlen = buf.readUInt16LE(off + 30), clen = buf.readUInt16LE(off + 32);
    const lho = buf.readUInt32LE(off + 42);
    const name = buf.toString('utf8', off + 46, off + 46 + nlen);
    off += 46 + nlen + xlen + clen;
    if (!filter(name)) continue;
    const start = lho + 30 + buf.readUInt16LE(lho + 26) + buf.readUInt16LE(lho + 28);
    const raw = buf.subarray(start, start + csize);
    if (method === 0) out.push({ name, data: raw });
    else if (method === 8) out.push({ name, data: zlib.inflateRawSync(raw) });
  }
  return out;
}

/** XML -> text: het paragraph/cell/row xuong dong, bo tag, giai entity. */
function xmlText(xml) {
  return xml
    .replace(/<\/(w:p|a:p|si|c|row|w:tc)>/g, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(+d))
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'").replace(/&amp;/g, '&');
}

function ooxmlText(file) {
  return readZip(fs.readFileSync(file), (n) => OOXML_PART.test(n))
    .map((e) => xmlText(e.data.toString('utf8'))).join('\n');
}

// ---------------- CLI mode ----------------
if (process.argv.includes('--scan')) {
  const cfg = loadCfg();
  const targets = process.argv.slice(process.argv.indexOf('--scan') + 1);
  if (!targets.length) { console.error('Dung: node detect-pii.js --scan <file|dir>...'); process.exit(1); }

  const files = [];
  const walk = (p) => {
    let st;
    try { st = fs.statSync(p); } catch { return; }
    if (st.isDirectory()) {
      for (const f of fs.readdirSync(p)) {
        if (['node_modules', '.git', 'evidence'].includes(f)) continue;
        // .claude/ la noi bo cua kit (rule, skill, tai lieu tham khao) — khong phai output giao khach.
        // Quet no chi sinh bao dong gia tu vi du trong tai lieu. Dung --all de quet ca.
        if (f === '.claude' && !process.argv.includes('--all')) continue;
        walk(path.join(p, f));
      }
    } else if (/\.(md|html|json|csv|txt|ts|js|py|xlsx|xlsm|docx|pptx)$/i.test(p)) files.push(p);
  };
  targets.forEach(walk);

  let bad = 0;
  for (const f of files) {
    if (cfg._allowPath.some((r) => r.test(f))) continue;
    let text;
    try {
      text = /\.(xlsx|xlsm|docx|pptx)$/i.test(f) ? ooxmlText(f) : fs.readFileSync(f, 'utf8');
    } catch (e) {
      bad += 1;   // khong doc duoc = khong chung minh duoc sach
      console.log(`\nH06: khong doc duoc ${f} (${e.message}) — kiem tay`);
      continue;
    }
    const hits = scanText(text, cfg);
    if (hits.length) {
      bad += 1;
      console.log('\n' + report(hits, f));
    }
  }
  console.log(`\n${files.length} file da quet · ${bad} file co phat hien`);
  console.log('LUU Y: khong quet duoc noi dung anh (.png/.jpg). Anh phai chup bang tai khoan test.');
  console.log('Bo qua .claude/ (noi bo kit). Them --all de quet ca.');
  process.exit(bad ? 1 : 0);
}

// ---------------- Hook mode ----------------
try {
  const raw = fs.readFileSync(0, 'utf8');
  if (!raw.trim()) process.exit(0);
  const payload = JSON.parse(raw);
  const toolName = payload.tool_name || '';
  const input = payload.tool_input || {};

  const cfg = loadCfg();
  if (cfg._scanTool.length && !cfg._scanTool.some((r) => r.test(toolName))) process.exit(0);

  const filePath = input.file_path || input.notebook_path || '';
  if (filePath && cfg._allowPath.some((r) => r.test(filePath))) process.exit(0);

  const hits = scanText(extract(toolName, input), cfg);
  if (hits.length) {
    console.error(report(hits, `${toolName}${filePath ? ' -> ' + filePath : ''}`));
    process.exit(2);
  }
  process.exit(0);
} catch (e) {
  // Hook loi thi KHONG chan — tranh lam ket ca session. Bao ra stderr de biet.
  console.error('H06 warning: ' + e.message);
  process.exit(0);
}
