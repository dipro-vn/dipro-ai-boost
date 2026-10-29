#!/usr/bin/env node
// Bo trich Basic Design muc B tu source FE (Next.js + React JSX) bang AST (ts-morph) — giai doan 1, chi doc code.
//
//   node extract-screen.mjs --frontend <repo FE> --workspace <thu muc du an> --site WEB-01 --repo-id REPO-01 \
//     --screens "SC-066=/tenant-list,SC-072=/user/x" --screen-files <recon>/fe-screen-files.json \
//     --api-calls <recon>/fe-api-calls.csv --s1-list <gates>/high-files.txt --out <thu muc xuat> [--only SC-066,SC-072]
// --screens = ban do man -> route cua ca site (de doi "bam -> sang man nao"); --only = chi trich cac man nay.
//
// --shell <regex>: duong dan file khung chung bo qua (mac dinh Layout|Header|Footer|Sidebar|Navbar|Breadcrumb|Menu|SignOut|Spinner).
// Ra: <out>/<SITE>.json (dung format spec cua build-basic-design.py) · <out>/fe-api-calls.ast.csv (cot UI Label
// dien tu AST) · stdout JSON thong ke. Moi gia tri lay tu code kem code-ref; khong co can cu -> "Cần xác nhận".
// File trong --s1-list (HIGH cua scan-sensitive.py) KHONG bao gio duoc mo. Thieu --s1-list -> exit 3.
// Exit: 0 OK · 2 thieu tham so / file · 3 thieu S1 (khong chay trich) · 4 framework chua ho tro (khong phai React JSX).
import fs from "node:fs";
import path from "node:path";
import { Project, SyntaxKind, Node } from "ts-morph";

const NEED = "Cần xác nhận";
const NA = "ー";
const JP = /[぀-ヿ㐀-鿿！-～]/;
const MAX_FILES = 80;          // shortcut: gioi han file / man (import sau 3 tang thuong la util chung)
const MAX_DEPTH = 3;

// ---------- tham so ----------
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf("--" + k); return i >= 0 ? argv[i + 1] : d; };
// khung chung (header / footer / layout / menu): khong phai item cua man — tru khi file nam trong fe-screen-files cua man
const SHELL_RX = new RegExp(opt("shell", "(Layout|Header|Footer|Sidebar|SideBar|Navbar|NavBar|Breadcrumb|Menu|SignOut|Spinner)"));
const need = ["frontend", "site", "repo-id", "screens", "screen-files", "out"];
for (const k of need) if (!opt(k)) { console.error(`thieu --${k}`); process.exit(2); }
const S1 = opt("s1-list");
if (!S1 || !fs.existsSync(S1)) {
  console.error("thieu --s1-list (high-files.txt cua scan-sensitive.py) — chay S1 truoc, khong trich");
  process.exit(3);
}
const FE = path.resolve(opt("frontend"));
// chi ho tro React JSX (Next.js / React): khong co react trong package.json -> bao chua ho tro (exit 4)
try {
  const pk = JSON.parse(fs.readFileSync(path.join(FE, "package.json"), "utf8"));
  if (!{ ...pk.dependencies, ...pk.devDependencies }.react) {
    console.error("framework chua ho tro: bo trich chi doc React JSX (Next.js / React) — repo nay khong co 'react' trong package.json");
    process.exit(4);
  }
} catch { console.error("khong doc duoc package.json cua --frontend"); process.exit(2); }
const WS = path.resolve(opt("workspace", process.cwd()));
const SITE = opt("site");
const REPO = opt("repo-id");
const OUT = path.resolve(opt("out"));
const screens = Object.fromEntries(opt("screens").split(",").map(s => s.trim()).filter(Boolean).map(s => {
  const i = s.indexOf("="); return [s.slice(0, i).trim(), s.slice(i + 1).trim()];
}));
const screenFiles = JSON.parse(fs.readFileSync(opt("screen-files"), "utf8"));

// S1: duong dan HIGH (tuong doi workspace hoac repo FE) -> tuyet doi
const high = new Set();
for (const line of fs.readFileSync(S1, "utf8").split(/\r?\n/)) {
  const t = line.trim().replace(/#L\d+.*$/, "");
  if (!t || t.startsWith("#")) continue;
  for (const base of [WS, FE]) high.add(path.resolve(base, t));
  if (path.isAbsolute(t)) high.add(path.resolve(t));
}
const isHigh = f => high.has(path.resolve(f));

// ---------- fe-api-calls.csv ----------
function parseCsv(text) {
  const rows = []; let row = [], cur = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"' && text[i + 1] === '"') { cur += '"'; i++; } else if (c === '"') q = false; else cur += c; }
    else if (c === '"') q = true;
    else if (c === ",") { row.push(cur); cur = ""; }
    else if (c === "\n") { row.push(cur.replace(/\r$/, "")); rows.push(row); row = []; cur = ""; }
    else cur += c;
  }
  if (cur || row.length) { row.push(cur); rows.push(row); }
  const [h, ...rest] = rows;
  return { header: h, rows: rest.filter(r => r.length > 1).map(r => Object.fromEntries(h.map((k, i) => [k, r[i] ?? ""]))) };
}
const apiCsv = opt("api-calls") && fs.existsSync(opt("api-calls"))
  ? parseCsv(fs.readFileSync(opt("api-calls"), "utf8")) : { header: [], rows: [] };

// ---------- import resolution (tsconfig baseUrl / paths) ----------
function readTsconfig() {
  for (const n of ["tsconfig.json", "jsconfig.json"]) {
    const p = path.join(FE, n);
    if (!fs.existsSync(p)) continue;
    try {
      const raw = fs.readFileSync(p, "utf8").replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "").replace(/,(\s*[}\]])/g, "$1");
      return JSON.parse(raw).compilerOptions || {};
    } catch { /* tsconfig khong parse duoc -> chi relative import */ }
  }
  return {};
}
const tsc = readTsconfig();
const baseUrl = path.resolve(FE, tsc.baseUrl || ".");
const aliases = Object.entries(tsc.paths || {}).map(([k, v]) => [k.replace(/\*$/, ""), (v[0] || "").replace(/\*$/, "")]);
const EXT = ["", ".tsx", ".ts", ".jsx", ".js", "/index.tsx", "/index.ts", "/index.jsx", "/index.js"];
function tryFile(base) {
  for (const e of EXT) { const f = base + e; if (fs.existsSync(f) && fs.statSync(f).isFile()) return f; }
  return null;
}
function resolveImport(from, spec) {
  let cands = [];
  if (spec.startsWith(".")) cands = [path.resolve(path.dirname(from), spec)];
  else {
    for (const [a, t] of aliases) if (spec.startsWith(a)) cands.push(path.resolve(baseUrl, t + spec.slice(a.length)));
    cands.push(path.resolve(baseUrl, spec));
  }
  for (const c of cands) {
    const f = tryFile(c);
    if (f && f.startsWith(FE + path.sep) && !f.includes(`${path.sep}node_modules${path.sep}`)) return f;
  }
  return null;
}

// ---------- AST helpers ----------
const project = new Project({ skipAddingFilesFromTsConfig: true, skipFileDependencyResolution: true,
  compilerOptions: { allowJs: true, jsx: 1 } });
const skipped = new Set();
function sourceFile(f) {
  if (isHigh(f)) { skipped.add(path.relative(FE, f)); return null; }
  return project.getSourceFile(f) || project.addSourceFileAtPathIfExists(f);
}
const ref = (n) => `${REPO}:${path.relative(FE, n.getSourceFile().getFilePath()).split(path.sep).join("/")}#L${n.getStartLineNumber()}` +
  (n.getEndLineNumber() > n.getStartLineNumber() ? `-L${n.getEndLineNumber()}` : "");
const strOf = (n) => {
  if (!n) return null;
  if (Node.isStringLiteral(n) || Node.isNoSubstitutionTemplateLiteral(n)) return n.getLiteralValue();
  if (Node.isTemplateExpression(n)) return n.getHead().getLiteralText() + n.getTemplateSpans().map(s => "（値）" + s.getLiteral().getLiteralText()).join("");
  if (Node.isJsxExpression(n)) return strOf(n.getExpression());
  if (Node.isParenthesizedExpression(n)) return strOf(n.getExpression());
  return null;
};
const tagOf = (el) => (Node.isJsxElement(el) ? el.getOpeningElement() : el).getTagNameNode().getText();
const attrsOf = (el) => (Node.isJsxElement(el) ? el.getOpeningElement() : el).getAttributes();
function attr(el, name) {
  const a = attrsOf(el).find(x => Node.isJsxAttribute(x) && x.getNameNode().getText() === name);
  if (!a) return undefined;
  const init = a.getInitializer();
  return init ? (Node.isJsxExpression(init) ? init.getExpression() : init) : true;   // <x required/> -> true
}
function textOf(el) {
  // chi chu hien thi (con JSX), khong lay gia tri thuoc tinh (className, href...)
  if (!Node.isJsxElement(el)) return "";
  const parts = [];
  const walk = (n) => {
    for (const c of n.getJsxChildren()) {
      if (Node.isJsxText(c)) { const t = c.getText().replace(/&nbsp;/g, " ").replace(/\s+/g, " ").trim(); if (t) parts.push(t); }
      else if (Node.isJsxExpression(c)) { const v = strOf(c.getExpression()); if (v) parts.push(v); }
      else if (Node.isJsxElement(c)) walk(c);
    }
  };
  walk(el);
  return parts.join(" ").trim();
}
const numOf = (n) => {
  if (!n || n === true) return null;
  if (Node.isNumericLiteral(n)) return Number(n.getLiteralValue());
  if (Node.isObjectLiteralExpression(n)) return numOf(propInit(n, "value"));
  return null;
};
function propInit(obj, name) {
  if (!obj || !Node.isObjectLiteralExpression(obj)) return null;
  const p = obj.getProperty(name);
  return p && Node.isPropertyAssignment(p) ? p.getInitializer() : null;
}
const constStr = (n) => n && Node.isPropertyAccessExpression(n) ? STR.get(n.getText()) || null : null;
const msgOf = (n) => strOf(n) || constStr(n) || (n && Node.isObjectLiteralExpression(n) ? msgOf(propInit(n, "message")) : null);

// ---------- thu thap theo man ----------
function collectFiles(route) {
  const start = (screenFiles[route] || []).map(f => path.resolve(FE, f));
  const seen = new Map(); const queue = start.map(f => [f, 0]);
  while (queue.length && seen.size < MAX_FILES) {
    const [f, d] = queue.shift();
    if (seen.has(f)) continue;
    const sf = sourceFile(f);
    if (!sf) continue;
    seen.set(f, { sf, depth: d });
    if (d >= MAX_DEPTH) continue;
    for (const imp of sf.getImportDeclarations()) {
      const t = resolveImport(f, imp.getModuleSpecifierValue());
      if (t && !seen.has(t)) queue.push([t, d + 1]);
    }
  }
  return [...seen.values()];
}

// hang so chuoi: <Ten>.<KEY> = "..." (object literal) — route ("/path") va thong bao (MESSAGES.X)
let STR = new Map();
function routeConsts(files) {
  const m = new Map(); STR = new Map();
  for (const { sf } of files) {
    for (const v of sf.getVariableDeclarations()) {
      const init = v.getInitializer();
      const obj = init && (Node.isAsExpression(init) ? init.getExpression() : init);
      if (!obj || !Node.isObjectLiteralExpression(obj)) continue;
      for (const p of obj.getProperties()) {
        if (!Node.isPropertyAssignment(p)) continue;
        const s = strOf(p.getInitializer());
        if (s && s.startsWith("/")) m.set(`${v.getName()}.${p.getName()}`, s);
        if (s) STR.set(`${v.getName()}.${p.getName()}`, s);
      }
    }
  }
  return m;
}

// luat yup: field -> {required, max, msgs[]}
function yupRules(files) {
  const rules = new Map();
  for (const { sf } of files) {
    for (const call of sf.getDescendantsOfKind(SyntaxKind.CallExpression)) {
      const ex = call.getExpression().getText();
      if (!/(^|\.)(object|shape)$/.test(ex)) continue;
      const obj = call.getArguments()[0];
      if (!obj || !Node.isObjectLiteralExpression(obj)) continue;
      const decl = call.getFirstAncestorByKind(SyntaxKind.VariableDeclaration);
      const schema = decl ? decl.getName() : "__inline__";
      for (const p of obj.getProperties()) {
        if (!Node.isPropertyAssignment(p)) continue;
        const key = schema + "." + p.getName();
        const r = rules.get(key) || { field: p.getName(), schema, required: false, max: null, msgs: [], ref: ref(p) };
        const init = p.getInitializer();
        for (const d of [init, ...init.getDescendants()]) {      // gom ca loi goi ngoai cung cua chuoi (.max / .test cuoi)
          if (!Node.isCallExpression(d) || !Node.isPropertyAccessExpression(d.getExpression())) continue;
          const fn = d.getExpression().getName(); const a = d.getArguments();
          if (fn === "required") { r.required = true; const s = msgOf(a[0]); if (s) r.msgs.push(["required", s, ref(d)]); }
          else if (fn === "max" && /string\(\)/.test(p.getInitializer().getText())) {
            r.max = numOf(a[0]); const s = msgOf(a[1]); if (s) r.msgs.push(["max", s, ref(d)]);
          } else if (fn === "test") {          // .test(ten, thong bao, ham) — tham so 1 la ten luat, khong phai chu hien thi
            const s = a.length >= 3 ? msgOf(a[1]) : (Node.isObjectLiteralExpression(a[0]) ? msgOf(propInit(a[0], "message")) : null);
            if (s) r.msgs.push([fn, s, ref(d)]);
          } else if (["min", "email", "matches", "typeError", "oneOf", "length", "url"].includes(fn)) {
            const s = [...a].map(msgOf).find(Boolean); if (s) r.msgs.push([fn, s, ref(d)]);
          }
        }
        rules.set(key, r);
      }
    }
  }
  return rules;
}

const INPUT_RX = /^(input|textarea|select)$|(TextField|Select|Checkbox|Radio|RadioGroup|Switch|DatePicker|TimePicker|DateTimePicker|Autocomplete|InputBase|OutlinedInput|TextArea|Textarea|Input|Field)$/;
const NOT_INPUT = /(Label|Adornment|Props|Group$)/;
const BUTTON_RX = /^(button|a|Link|NextLink)$|Button$/;
function inputType(tag, el) {
  const t = strOf(attr(el, "type")) || "";
  if (/checkbox/i.test(tag) || t === "checkbox") return "Checkbox";
  if (/radio/i.test(tag) || t === "radio") return "Radio";
  if (/switch/i.test(tag)) return "Toggle";
  if (/date|time/i.test(tag) || /date|time/.test(t)) return "Date";
  if (/select|autocomplete/i.test(tag) || attr(el, "select")) return "Select";
  if (/textarea/i.test(tag) || attr(el, "multiline")) return "Textarea";
  return { number: "Number", password: "Password", email: "Email" }[t] || "Textbox";
}
function fieldOf(el) {
  const n = strOf(attr(el, "name"));
  if (n) return n;
  for (const a of attrsOf(el)) {
    if (!Node.isJsxSpreadAttribute(a)) continue;
    const e = a.getExpression();
    if (Node.isCallExpression(e) && /register$/.test(e.getExpression().getText())) return strOf(e.getArguments()[0]);
    if (Node.isIdentifier(e) && e.getText() === "field") break;   // Controller render({field})
  }
  const ctl = el.getFirstAncestor(a => (Node.isJsxSelfClosingElement(a) || Node.isJsxElement(a)) && /Controller$/.test(tagOf(a)));
  return ctl ? strOf(attr(ctl, "name")) : null;
}
function registerOpts(el, field) {
  // register("x", {required, maxLength}) o spread hoac Controller rules
  for (const a of attrsOf(el)) {
    if (Node.isJsxSpreadAttribute(a) && Node.isCallExpression(a.getExpression())) return a.getExpression().getArguments()[1];
  }
  const ctl = el.getFirstAncestor(a => (Node.isJsxSelfClosingElement(a) || Node.isJsxElement(a)) && /Controller$/.test(tagOf(a)));
  return ctl ? attr(ctl, "rules") : (field ? null : null);
}
// <Label htmlFor="x" isRequired>姓</Label> -> nhan + bat buoc cua o co id / name = x
function labelsFor(sf) {
  const m = new Map();
  for (const el of sf.getDescendantsOfKind(SyntaxKind.JsxElement)) {
    if (!/(^label|Label)$/.test(tagOf(el))) continue;
    const id = strOf(attr(el, "htmlFor"));
    const t = textOf(el).replace(/[※＊*]|必須/g, "").trim();
    if (id && t) m.set(id, { text: t, required: attr(el, "isRequired") === true || Boolean(attr(el, "required")) ||
      (attr(el, "isRequired") && attr(el, "isRequired").getText && attr(el, "isRequired").getText() === "true") || /必須|※/.test(textOf(el)) });
  }
  return m;
}
const cleanLabel = (t) => {
  const v = (t || "").replace(/[:：]\s*$/, "").trim();
  return /[\p{L}\p{N}]/u.test(v) && !/^[a-z]+[A-Z]\w*$/.test(v) ? v : null;   // chi ky hieu (~, 〜) / camelCase -> khong phai nhan
};
let NEAR_REQ = false;   // nhan dung gan (khong htmlFor) co dau bat buoc
const insideInput = (el) => el.getFirstAncestor(a => (Node.isJsxElement(a) || Node.isJsxSelfClosingElement(a)) && INPUT_RX.test(tagOf(a)) && !NOT_INPUT.test(tagOf(a)));
function labelNear(el, lf) {
  const s0 = strOf(attr(el, "label"));
  if (s0) return s0;
  for (const k of ["id", "name"]) { const v = strOf(attr(el, k)); if (v && lf.has(v)) return lf.get(v).text; }
  const fcl = el.getFirstAncestor(a => (Node.isJsxSelfClosingElement(a) || Node.isJsxElement(a)) && /FormControlLabel$/.test(tagOf(a)));
  if (fcl) { const s = strOf(attr(fcl, "label")); if (s) return s; }
  // chu gan nhat dung truoc trong khoi cha (label / p / span / Typography), len toi 4 tang
  let cur = el;
  for (let up = 0; up < 4 && cur; up++) {
    const parent = cur.getFirstAncestor(a => Node.isJsxElement(a));
    if (!parent) break;
    const before = parent.getJsxChildren().filter(c => Node.isJsxElement(c) && c.getEnd() <= cur.getStart());
    for (let i = before.length - 1; i >= 0; i--) {
      if (before[i].getDescendants().some(d => (Node.isJsxElement(d) || Node.isJsxSelfClosingElement(d)) && INPUT_RX.test(tagOf(d)) && !NOT_INPUT.test(tagOf(d)))) continue;
      const t = textOf(before[i]).replace(/[※＊*]|必須/g, "").trim();
      if (t && t.length <= 30) {
        const b = before[i], bt = tagOf(b);
        NEAR_REQ = (/(^label|Label)$/.test(bt) && (attr(b, "isRequired") === true || (attr(b, "isRequired") && attr(b, "isRequired").getText && attr(b, "isRequired").getText() === "true"))) || /必須|※/.test(textOf(b));
        return t;
      }
    }
    cur = parent;
  }
  for (const k of ["aria-label", "title", "placeholder"]) { const v = strOf(attr(el, k)); if (v) return v; }   // placeholder = chu mau -> sau cung
  return null;
}
function visibility(el) {
  const ex = el.getFirstAncestor(a => Node.isJsxExpression(a));
  if (!ex) return null;
  const e = ex.getExpression();
  if (e && (Node.isConditionalExpression(e) || (Node.isBinaryExpression(e) && e.getOperatorToken().getText() === "&&")))
    return (Node.isConditionalExpression(e) ? e.getCondition() : e.getLeft()).getText().replace(/\s+/g, " ").slice(0, 120);
  return null;
}
function handlerBody(el, sf) {
  const h = attr(el, "onClick") || attr(el, "onSubmit");
  if (!h || h === true) return { name: null, body: null };
  if (Node.isIdentifier(h) || Node.isPropertyAccessExpression(h)) {
    const name = h.getText().split(".").pop();
    const decl = sf.getFunction(name) || sf.getDescendantsOfKind(SyntaxKind.VariableDeclaration).find(v => v.getName() === name);
    return { name, body: decl ? (Node.isVariableDeclaration(decl) ? decl.getInitializer() : decl) : null };
  }
  return { name: null, body: h };
}
function navTarget(node, consts) {
  if (!node) return null;
  let out = null;
  node.forEachDescendant((d, tr) => {
    if (out) return tr.stop();
    if (Node.isCallExpression(d) && /(router|Router)\.(push|replace)$/.test(d.getExpression().getText())) {
      out = routeValue(d.getArguments()[0], consts);
    }
  });
  return out;
}
function routeValue(n, consts) {
  if (!n) return null;
  const s = strOf(n);
  if (s) return s;
  if (Node.isPropertyAccessExpression(n) && consts.has(n.getText())) return consts.get(n.getText());
  if (Node.isCallExpression(n) && Node.isPropertyAccessExpression(n.getExpression())) return routeValue(n.getExpression().getExpression(), consts);  // ROUTE.X.replace(...)
  if (Node.isObjectLiteralExpression(n)) return routeValue(propInit(n, "pathname"), consts);
  return null;
}
const routeRx = (r) => new RegExp("^" + r.replace(/\[[^\]]+\]|:[^/]+/g, "[^/]+").replace(/\//g, "\\/") + "$");
const allRoutes = Object.entries(screens);
function screenOfRoute(r) {
  if (!r) return null;
  const clean = r.split("?")[0].replace(/（値）.*$/, "");
  const hit = allRoutes.find(([, rt]) => rt === clean) || allRoutes.find(([, rt]) => routeRx(rt).test(clean)) ||
    allRoutes.find(([, rt]) => routeRx(clean.replace(/\/$/, "")).test(rt));
  return hit ? hit[0] : clean;
}

const ERR_CALL = [
  [/(^|\.)setError$/, "Validation", "Inline", 1],
  [/toast(\.(error|warn|warning))?$/i, "System", "Toast", 0],
  [/enqueueSnackbar$|showToast$|notify$|showError$|openErrorDialog$/i, "System", "Toast", 0],
  [/^set\w*ErrorDialog\w*$/i, "System", "Dialog", 0],
  [/^set\w*Err\w*(Msg|Message)$/i, "System", "Cần xác nhận", 0],       // setErrorMsg (state -> cho hien thi tuy man)
];

function extractScreen(sid, route) {
  const files = collectFiles(route);
  const entry = files.filter(f => f.depth === 0).map(f => f.sf);
  const consts = routeConsts(files);
  const yupAll = yupRules(files);
  // chi schema man nay dung: yupResolver(<ten>) hoac yupResolver(yup.object(...)) trong file cua man
  const used = new Set();
  for (const { sf } of files) for (const c of sf.getDescendantsOfKind(SyntaxKind.CallExpression)) {
    if (!/yupResolver$/.test(c.getExpression().getText())) continue;
    const a0 = c.getArguments()[0];
    if (!a0) continue;
    used.add(Node.isIdentifier(a0) || Node.isPropertyAccessExpression(a0) ? a0.getText().split(".").pop() : "__inline__");
  }
  const yup = new Map([...yupAll.values()].filter(r => used.has(r.schema)).map(r => [r.field, r]));
  const apiRows = apiCsv.rows.filter(r => r["Screen Route"] === route);
  const items = [], errors = [], seenKey = new Set();
  let title = null;
  const scan = files.filter(f => f.depth === 0 || !SHELL_RX.test(path.relative(FE, f.sf.getFilePath())));
  // tieu de: h1/h2 / Typography h* trong file trang truoc, roi component
  const heading = (sfs) => {
    for (const sf of sfs) for (const el of sf.getDescendantsOfKind(SyntaxKind.JsxElement)) {
      const tag = tagOf(el), v = strOf(attr(el, "variant")) || "";
      if (/^h[1-3]$/.test(tag) || (/Typography$/.test(tag) && /^h[1-4]$/.test(v))) { const t = textOf(el); if (t && t.length <= 30) return t; }
    }
    return null;
  };
  const layoutTitle = (sfs) => {
    for (const sf of sfs) for (const el of [...sf.getDescendantsOfKind(SyntaxKind.JsxElement), ...sf.getDescendantsOfKind(SyntaxKind.JsxSelfClosingElement)]) {
      const t = strOf(attr(el, "title")) || strOf(attr(el, "pageTitle")) || strOf(attr(el, "heading"));
      if (t && t.length <= 30 && /Layout|Page|Container|Header/.test(tagOf(el))) return t;
    }
    return null;
  };
  const pageFiles = files.filter(f => f.depth === 0 && /pages?\//.test(f.sf.getFilePath())).map(f => f.sf);
  title = heading(pageFiles) || layoutTitle(pageFiles) || heading(entry) || heading(scan.map(f => f.sf));
  for (const { sf } of scan) {
    const lf = labelsFor(sf);
    for (const el of [...sf.getDescendantsOfKind(SyntaxKind.JsxElement), ...sf.getDescendantsOfKind(SyntaxKind.JsxSelfClosingElement)]) {
      const tag = tagOf(el);
      const cond = visibility(el);
      if (INPUT_RX.test(tag) && !NOT_INPUT.test(tag)) {
        if (insideInput(el)) continue;            // TextField trong renderInput cua Autocomplete...
        const field = fieldOf(el);
        NEAR_REQ = false;
        const label = cleanLabel(labelNear(el, lf)) || NEED;     // khong dung ten bien code lam nhan
        const lbl = lf.get(strOf(attr(el, "id")) || field || "");
        const key = "in:" + (field || label) + ":" + tag;
        if (seenKey.has(key)) continue;
        seenKey.add(key);
        const ro = registerOpts(el, field);
        const yr = field ? yup.get(field) : null;
        const typ = inputType(tag, el);
        let req = attr(el, "required") === true || Boolean(propInit(ro, "required")) || Boolean(yr && yr.required) || Boolean(lbl && lbl.required) || NEAR_REQ;
        let max = numOf(attr(el, "maxLength")) ?? numOf(propInit(attr(el, "inputProps"), "maxLength")) ??
          numOf(propInit(ro, "maxLength")) ?? (yr && yr.max);
        const refs = [ref(el)].concat(yr ? [yr.ref] : []);
        items.push({
          name_jp: label, name_vn: label, type: typ,
          status: cond ? "Hidden（表示条件あり）" : (attr(el, "disabled") === true ? "Disable" : "Enable"),
          required: req ? "Yes" : "No",      // khong co luat bat buoc nao trong code -> khong bat buoc
          maxlength: ["Select", "Radio", "Checkbox", "Date", "Toggle"].includes(typ) ? NA : (max != null ? String(max) : NEED),
          default: NA,
          p: `・${label}を${/Select|Radio|Checkbox|Date|Toggle/.test(typ) ? "選択" : "入力"}する。` + (req ? "\n・必須。" : ""),
          q: `・${/Select|Radio|Checkbox|Date|Toggle/.test(typ) ? "Chọn" : "Nhập"} 「${label}」.` + (req ? "\n・Bắt buộc." : ""),
          r: refs.join("; ") + (cond ? `; 表示条件: ${cond}` : ""),
          label, field: field || "", next: NA,
        });
        // loi validation tu register / Controller rules
        for (const k of ["required", "maxLength", "minLength", "pattern", "validate"]) {
          const s = msgOf(propInit(ro, k));
          if (s) errors.push(err(label, "Validation", "Inline", s, ro));
        }
        if (yr) yr.label = label;
      } else if (BUTTON_RX.test(tag) || /Pagination$/.test(tag) || (attr(el, "onClick") && !el.getFirstAncestor(a => (Node.isJsxElement(a) || Node.isJsxSelfClosingElement(a)) && BUTTON_RX.test(tagOf(a))))) {
        let label = /Pagination$/.test(tag) ? "ページネーション" :
          (textOf(el) || strOf(attr(el, "aria-label")) || strOf(attr(el, "title")) || strOf(attr(el, "label")));
        if (!label) {
          const icon = el.getDescendantsOfKind ? [...el.getDescendantsOfKind(SyntaxKind.JsxSelfClosingElement)].map(tagOf).find(t => /Icon$/.test(t)) : null;
          label = icon ? `（アイコン）${icon.replace(/Icon$/, "")}` : null;
        }
        if (!label || label.length > 40) continue;
        const key = "btn:" + label + ":" + sf.getFilePath();
        if (seenKey.has(key)) continue;
        seenKey.add(key);
        const { name, body } = handlerBody(el, sf);
        const href = routeValue(attr(el, "href"), consts);
        const nextRoute = href || navTarget(body, consts);
        const api = name ? apiRows.find(r => r.Trigger.split(/\s*→\s*/).includes(name)) : null;
        if (api && (!api["UI Label"] || api["UI Label"] === "—")) api["UI Label"] = label;
        const it = {
          name_jp: label, name_vn: label, type: /^(a|Link|NextLink)$/.test(tag) ? "Link" : "Button",
          status: cond ? "Hidden（表示条件あり）" : "Enable", required: NA, maxlength: NA, default: NA,
          p: `・「${label}」を押下する。`, q: `・Bấm 「${label}」.`,
          r: ref(el) + (body && name ? `; handler ${name}` : "") + (cond ? `; 表示条件: ${cond}` : ""),
          label, field: "", next: nextRoute ? screenOfRoute(nextRoute) : NA,
        };
        if (api) it.api = `${api.Method} ${api.Path} (${api["API ID"]})`;
        items.push(it);
      } else if (tag === "th") {
        const t = textOf(el);
        if (t && !seenKey.has("col:" + t)) {
          seenKey.add("col:" + t);
          items.push({ name_jp: t, name_vn: t, type: "Label", status: "Enable", required: NA, maxlength: NA, default: NA,
            p: `・一覧の列「${t}」。`, q: `・Cột 「${t}」 của danh sách.`, r: ref(el), label: t, field: "", next: NA });
        }
      }
    }
    // cot DataGrid: { field, headerName }
    for (const obj of sf.getDescendantsOfKind(SyntaxKind.ObjectLiteralExpression)) {
      const h = strOf(propInit(obj, "headerName"));
      if (!h || seenKey.has("col:" + h)) continue;
      seenKey.add("col:" + h);
      items.push({ name_jp: h, name_vn: h, type: "Label", status: "Enable", required: NA, maxlength: NA, default: NA,
        p: `・一覧の列「${h}」。`, q: `・Cột 「${h}」 của danh sách.`, r: ref(obj), label: h, field: strOf(propInit(obj, "field")) || "", next: NA });
    }
    // thong bao loi nguyen van
    for (const call of sf.getDescendantsOfKind(SyntaxKind.CallExpression)) {
      const ex = call.getExpression().getText();
      for (const [rx, cat, disp, idx] of ERR_CALL) {
        if (!rx.test(ex)) continue;
        // khop luat dau tien thoi (ErrorDialog truoc ErrorMsg)
        const s = msgOf(call.getArguments()[idx]);
        if (s && s.length >= 2) errors.push(err(idx ? strOf(call.getArguments()[0]) || "画面" : "画面", cat === "Validation" ? "🔴 Validation" : "🔵 System", disp, s, call));
        break;
      }
    }
    for (const nw of sf.getDescendantsOfKind(SyntaxKind.NewExpression)) {
      if (nw.getExpression().getText() !== "Error") continue;
      const s = strOf(nw.getArguments()[0]);
      if (s && JP.test(s)) errors.push(err("画面", "🔵 System", NEED, s, nw));
    }
  }
  for (const [fname, yr] of yup)
    for (const [, s, r] of yr.msgs) errors.push({ ...err(yr.label || fname, "🔴 Validation", "Inline", s, null), source: r });
  // khu trung loi (cung noi dung)
  const uniq = new Map();
  for (const e of errors) if (!uniq.has(e.item + e.msg_jp)) uniq.set(e.item + e.msg_jp, e);
  return { title: title || NEED, items, errors: [...uniq.values()], files: files.length };
}
function err(item, category, display, msg, node) {
  const cat = category.startsWith("🔴") || category.startsWith("🔵") ? category : (category === "Validation" ? "🔴 Validation" : "🔵 System");
  const val = cat.startsWith("🔴");   // loi kiem tra nhap: o lai man, sua noi dung nhap (suy tu co che validation)
  return { item: item || "画面", category: cat, display, code: "", msg_jp: msg, msg_vn: NEED,
    action_jp: val ? "入力内容を修正して再度操作する" : NEED, action_vn: val ? "Sửa nội dung nhập rồi thao tác lại" : NEED,
    next: NA, source: node ? ref(node) : "" };
}

// ---------- chay ----------
fs.mkdirSync(OUT, { recursive: true });
const spec = { screens: {} }, stat = {};
const only = opt("only") ? new Set(opt("only").split(",").map(x => x.trim())) : null;   // chi trich vai man (--screens van la ban do route day du)
for (const [sid, route] of Object.entries(screens)) {
  if (only && !only.has(sid)) continue;
  if (!screenFiles[route]) { stat[sid] = { route, error: "khong co trong fe-screen-files.json" }; continue; }
  const r = extractScreen(sid, route);
  // khong thay tieu de trong code -> bo "title" (build-basic-design.py lay ten man o 02_Screen), khong dat sheet "Cần xác nhận"
  spec.screens[sid] = r.title === NEED ? { items: r.items, errors: r.errors } : { title: r.title, items: r.items, errors: r.errors };
  stat[sid] = { route, files: r.files, title: r.title, items: r.items.length, errors: r.errors.length,
    need: JSON.stringify(r).split(NEED).length - 1 };
}
fs.writeFileSync(path.join(OUT, `${SITE}.json`), JSON.stringify(spec, null, 1));
if (apiCsv.header.length) {
  const esc = (v) => /[",\n]/.test(v) ? `"${String(v).replace(/"/g, '""')}"` : String(v);
  fs.writeFileSync(path.join(OUT, "fe-api-calls.ast.csv"),
    [apiCsv.header.join(","), ...apiCsv.rows.map(r => apiCsv.header.map(h => esc(r[h] ?? "")).join(","))].join("\n") + "\n");
}
console.log(JSON.stringify({ site: SITE, out: path.join(OUT, `${SITE}.json`), screens: stat,
  skipped_s1: [...skipped].sort() }, null, 1));
