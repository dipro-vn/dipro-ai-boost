#!/usr/bin/env python3
"""Sinh JS ve view CR tren Figma (Luong 2) tu <ver>/_internal/cr-figma.json — dung FORMAT Output 1 / Output 2.

  python3 render-cr-figma.py --cr-json <ver>/_internal/cr.json --view <ver>/_internal/cr-figma.json \\
      --baseline outputs/<baseline> --rates .claude/config/md-unit-rates.json --page-id <id page> \\
      --y <y dat section> --out-dir <ver>/_internal/figma-js [--template templates/template_estimation.xlsx]

Agent viet cr-figma.json (noi dung nghiep vu), script nay sinh JS (bo cuc, mau, ten node, mui ten) — moi file
<= 45 KB, chay lan luot bang use_figma: 01-shell-flow.js · 02-screen-flow.js · 03-change-table.js ·
04-screens-<n>.js (CR-3) · 99-readback.js (doc nguoc -> cr-figma-nodes.json cho verify-cr-figma.py).

Sub-view (dung thu tu kit requirement-to-flow change-request.md §3):
  CR-1 Flow        = Output 1 Phan A (ACTOR → TRIGGER → FUNCTION → TECHNOLOGY → OUTCOME · EDGE) chi cac lane bi
                     CR cham + Phan B Technology (chi cong nghe NEW/UPD/IMPACT)
  CR-2 Screen Flow = Output 2: Group (Start ▶ · Screen · Decision ◇ · System · NG · Terminal) noi bang mui ten
                     that + Edge/Exceptional panel + bang Screen Index (pham vi CR)
  CR Change Table  = THONG KE (khong liet ke chi tiet): so doi tuong NEW/UPD/DEL/IMPACT theo Man hinh / API /
                     Bang DB / ... + 実装 MD + 総工数 人日 + 人月 (cung cong thuc Summary / Estimation)
  CR-3 Screens     = man de xuat dung token + component Design System cua baseline (doc tokens.json; component
                     site chua co -> block bat buoc khai "from": "<WEB-xx>" muon site khac, khong tu che)
Moi node mang dung 1 badge: ten "<BADGE> · <REF> · <nhan>", sharedPluginData("crkit","kind",...).

Schema cr-figma.json:
{"title": "...",
 "flows": [{"lane": "FL-08" | "CR-NEW-1", "title": "...", "nodes": [{"key","col": actor|trigger|function|
            technology|outcome|edge, "row": 0, "type": box|decision|ng, "badge", "ref", "label", "sub"}],
            "edges": [["from_key","to_key","nhan","ng|cross|"]]}],
 "tech": [{"badge","ref","label","sub"}],
 "screen_groups": [{"id": "G1", "title": "...", "site": "WEB-02", "nodes": [{"key","type": start|screen|decision|
            system|ng|terminal|edge, "badge","ref","label","sub"}], "edges": [["a","b","nhan","ng|"]]}],
 "screens": {"ds_read": ["outputs/<baseline>/04_DesignSystem/WEB-02/project/README.md", ...],
             "items": [{"badge","ref","site","shell": public|mypage|admin|auth, "title","label","nav_active",
                        "blocks": [ {"t": "title"|"breadcrumb"|"section"|"text"|"field"|"field2"|"select"|"radio"|
                                     "checkbox"|"buttons"|"table"|"badge"|"card"|"steps"|"modal"|"search"|
                                     "pagination", ..., "from": "WEB-01"} ]}]}}
Exit 0 OK · 1 du lieu sai (ref la, badge la, component khong co trong DS ma khong khai from) · 2 thieu openpyxl.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402
import cr_common as C  # noqa: E402

NS = "crkit"
BADGES = ["NEW", "UPD", "DEL", "IMPACT", "AS-IS"]
FLOW_COLS = ["actor", "trigger", "function", "technology", "outcome", "edge"]
SCREEN_TYPES = ["start", "screen", "decision", "system", "ng", "terminal", "edge"]
MAX_JS = 45000

# block -> component DS can co (None = ve tu token, khong can component)
BLOCK_COMP = {"field": "TextField", "field2": "TextField", "select": "Select", "radio": "Radio",
              "checkbox": "Checkbox", "buttons": "Button", "table": "Table", "badge": "Badge",
              "card": "Card", "modal": "Modal", "search": "Card", "pagination": "Pagination",
              "title": "PageHeader", "breadcrumb": "Breadcrumb", "section": None, "text": None, "steps": None}
SHELL_COMP = {"public": ["AppHeader"], "mypage": ["AppHeader", "SideNav"], "admin": ["SideNav"], "auth": []}
# auth: WEB-02 = AppHeader dang chua dang nhap; WEB-01 = card giua page-bg (man dang nhap admin khong co header)


def load_tokens(bdir, site):
    p = os.path.join(bdir, "04_DesignSystem", site, "project", "tokens.json")
    if not os.path.isfile(p):
        p = os.path.join(bdir, "04_DesignSystem", "project", "tokens.json")
    t = C.load_json(p)
    flat = {}
    for grp in ("color", "spacing", "radius", "shadow", "size"):
        for x in (t.get(grp) or {}).get("tokens") or []:
            flat[x["name"]] = x.get("value")
    for _ in range(3):                       # giai alias {primary}
        for k, v in flat.items():
            m = re.match(r"^\{(.+)\}$", str(v))
            if m and m.group(1) in flat:
                flat[k] = flat[m.group(1)]
    styles = {}
    for g in (t.get("type") or {}).get("groups") or []:
        for st in g.get("styles") or []:
            styles[st["name"]] = {"size": float(str(st.get("fontSize", "16")).rstrip("px") or 16),
                                  "weight": int(st.get("fontWeight") or 400)}
    return {"t": flat, "type": styles}


def px(v, default=0.0):
    try:
        return float(str(v).replace("px", "").strip())
    except (TypeError, ValueError):
        return default


def esc(o):
    return json.dumps(o, ensure_ascii=False)


# ---------------------------------------------------------------- JS library (dung chung moi file)
LIB = r"""
const NS = "crkit";
const BADGE = {NEW:{f:"#EDFDF0",s:"#1A7F37",d:false}, UPD:{f:"#FFF9EB",s:"#F4860C",d:true},
  DEL:{f:"#FFF6F5",s:"#CF222E",d:true}, IMPACT:{f:"#FBEEFF",s:"#6639BA",d:true}, "AS-IS":{f:"#F6F8FA",s:"#D0D7DE",d:false,o:0.6}};
const W8 = {300:"Light",400:"Regular",500:"Medium",600:"Bold",700:"Bold"};
for (const st of ["Regular","Bold","Medium","Light"]) await figma.loadFontAsync({family:"Noto Sans JP", style:st});
function rgb(h){ h=h.replace("#",""); return {r:parseInt(h.slice(0,2),16)/255,g:parseInt(h.slice(2,4),16)/255,b:parseInt(h.slice(4,6),16)/255}; }
function paint(h){ h=String(h).trim(); let m=h.match(/^rgba?\(([^)]+)\)$/);
  if(m){ const p=m[1].split(",").map(x=>parseFloat(x)); return {type:"SOLID",color:{r:p[0]/255,g:p[1]/255,b:p[2]/255},opacity:p.length>3?p[3]:1}; }
  h=h.replace("#",""); const o = h.length===8 ? parseInt(h.slice(6,8),16)/255 : 1; return {type:"SOLID",color:rgb(h.slice(0,6)),opacity:o}; }
function T(parent, s, x, y, w, size, weight, color, align){
  const t=figma.createText(); t.fontName={family:"Noto Sans JP",style:W8[weight]||(weight===true?"Bold":"Regular")};
  t.characters=String(s); t.fontSize=size; t.fills=[paint(color||"#1F2328")]; t.name="t";
  if(align) t.textAlignHorizontal=align;
  if(w){ t.resize(w, t.height); t.textAutoResize="HEIGHT"; }
  parent.appendChild(t); t.x=x; t.y=y; return t; }
function F(parent, name, x, y, w, h, fill){ const f=figma.createFrame(); f.name=name; f.resize(w,h); f.fills=fill?[paint(fill)]:[]; f.clipsContent=false;
  if(parent) { parent.appendChild(f); f.x=x; f.y=y; } return f; }
function R(parent, x, y, w, h, fill){ const r=figma.createRectangle(); r.resize(Math.max(w,1),Math.max(h,1)); r.fills=[paint(fill)]; parent.appendChild(r); r.x=x; r.y=y; r.name="r"; return r; }
function badgeBox(parent, n, x, y, w, h, kind, shape){
  const b=BADGE[n.badge]; const f=F(parent, `${n.badge} · ${n.ref} · ${n.label}`, x, y, w, h, b.f);
  f.strokes=[paint(b.s)]; f.strokeWeight=2; if(b.d) f.dashPattern=[6,4]; if(b.o) f.opacity=b.o;
  f.cornerRadius = shape==="pill" ? h/2 : (shape==="decision" ? 20 : 8);
  if(shape==="ng"){ const bar=R(f,0,0,6,h,"#CF222E"); bar.name="ng-bar"; }
  const pre = shape==="decision" ? "◇ " : (shape==="ng" ? "NG · " : (shape==="pill" ? "▶ " : ""));
  const t1=T(f, `${n.badge} · ${n.ref}`, 10, 6, w-20, 10, 700, b.s);
  const t2=T(f, pre+n.label+(n.badge==="DEL"?" (bỏ)":""), 10, t1.y+t1.height+2, w-20, 12, 700, "#1F2328");
  if(n.badge==="DEL") t2.textDecoration="STRIKETHROUGH";
  let bottomY = t2.y+t2.height;
  if(n.sub){ const t3=T(f, n.sub, 10, t2.y+t2.height+2, w-20, 10, 400, "#57606A"); bottomY = t3.y+t3.height; }
  if (bottomY+8 > h) { f.resize(w, bottomY+8); const bar=f.findOne(c=>c.name==="ng-bar"); if(bar) bar.resize(6, bottomY+8); }
  f.setSharedPluginData(NS,"kind",kind); return f; }
function head(parent, x, y, dir){ const v=figma.createVector(); const P={r:"M 0 0 L 10 5 L 0 10 Z",l:"M 10 0 L 0 5 L 10 10 Z",d:"M 0 0 L 10 0 L 5 10 Z",u:"M 0 10 L 10 10 L 5 0 Z"};
  v.vectorPaths=[{windingRule:"NONZERO",data:P[dir]}]; parent.appendChild(v); v.name="head";
  const o={r:[-10,-5],l:[0,-5],d:[-5,-10],u:[-5,0]}[dir]; v.x=x+o[0]; v.y=y+o[1]; return v; }
function arrow(parent, A, B, label, style){
  // A,B = node frame; noi tu canh phai A -> canh trai B (khac cot) hoac day A -> dinh B (cung cot)
  const col = style==="ng" ? "#CF222E" : (style==="cross" ? "#1A7F37" : "#0969DA");
  const g=[]; const seg=(x1,y1,x2,y2)=>{ const r=R(parent,Math.min(x1,x2)-1,Math.min(y1,y2)-1,Math.abs(x2-x1)+2,Math.abs(y2-y1)+2,col);
     if(style==="ng"){ r.opacity=0.85; } g.push(r); };
  const ax=A.x, ay=A.y, aw=A.width, ah=A.height, bx=B.x, by=B.y, bw=B.width, bh=B.height;
  let end, dir;
  if (bx >= ax+aw-2) {            // B ben phai
    const x1=ax+aw, y1=ay+ah/2, x2=bx, y2=by+bh/2, xm=Math.round((x1+x2)/2);
    if (Math.abs(y1-y2)<2) seg(x1,y1,x2-10,y2); else { seg(x1,y1,xm,y1); seg(xm,y1,xm,y2); seg(xm,y2,x2-10,y2); }
    end=[x2,y2]; dir="r";
  } else if (by >= ay+ah-2) {     // B ben duoi
    const x1=ax+aw/2, y1=ay+ah, x2=bx+bw/2, y2=by, ym=Math.round((y1+y2)/2);
    if (Math.abs(x1-x2)<2) seg(x1,y1,x2,y2-10); else { seg(x1,y1,x1,ym); seg(x1,ym,x2,ym); seg(x2,ym,x2,y2-10); }
    end=[x2,y2]; dir="d";
  } else {                         // B ben trai / tren -> vong duoi
    const x1=ax+aw/2, y1=ay+ah, x2=bx+bw/2, y2=by+bh, yb=Math.max(y1,y2)+24;
    seg(x1,y1,x1,yb); seg(x1,yb,x2,yb); seg(x2,yb,x2,y2+10); end=[x2,y2]; dir="u";
  }
  const h=head(parent,end[0],end[1],dir); h.fills=[paint(col)]; g.push(h);
  if (label) { const t=T(parent,label,(g[0].x+6),(g[0].y-14),null,10,500,col); g.push(t); }
  const grp=figma.group(g,parent); grp.name=`ARROW · ${A.name.split(" · ")[1]} → ${B.name.split(" · ")[1]}`;
  grp.setSharedPluginData(NS,"kind","arrow"); grp.setSharedPluginData(NS,"from",A.id); grp.setSharedPluginData(NS,"to",B.id);
  return grp; }
async function section(){ const page=await figma.getNodeByIdAsync(PAGE_ID); await figma.setCurrentPageAsync(page);
  let s=page.children.find(c=>c.type==="SECTION" && c.name===SECTION_NAME); return {page, s}; }
function bottom(s){ let m=0; for(const c of s.children) m=Math.max(m,c.y+c.height); return m; }
function fit(s){ let w=0,h=0; for(const c of s.children){ w=Math.max(w,c.x+c.width); h=Math.max(h,c.y+c.height);} s.resizeWithoutConstraints(w+80,h+80); }
"""


def js_file(head_vars, body):
    return "const PAGE_ID = %s;\nconst SECTION_NAME = %s;\n%s\n%s" % (
        esc(head_vars["page_id"]), esc(head_vars["section"]), LIB, body)


# ---------------------------------------------------------------- 01: section + legend + CR-1 Flow
def part_shell_flow(view, stats_line):
    body = r"""
const D = %s;
const {page, s:old} = await section();
if (old) return {error: "section da ton tai — xoa section cu (cua chinh lan chay nay) hoac doi ten truoc khi ve lai"};
const s = figma.createSection(); s.name = SECTION_NAME; s.x = %d; s.y = %d; page.appendChild(s);
const created=[];
T(s, SECTION_NAME, 40, 30, 2200, 32, 700);
T(s, D.subtitle, 40, 80, 2200, 14, 400, "#57606A");
// Legend
const lg = F(s, "LEGEND · badge", 40, 120, 1180, 64, "#FFFFFF"); lg.strokes=[paint("#D0D7DE")]; lg.cornerRadius=8;
lg.setSharedPluginData(NS,"kind","legend");
let lx=16; for (const [b,txt] of [["NEW","Tạo mới"],["UPD","Sửa cái đang có"],["DEL","Bỏ"],["IMPACT","Không sửa — bị kéo theo, kiểm lại"],["AS-IS","Giữ nguyên, ngữ cảnh"]]) {
  const sw=F(lg,"sw-"+b,lx,18,28,28,BADGE[b].f); sw.strokes=[paint(BADGE[b].s)]; sw.strokeWeight=2; if(BADGE[b].d) sw.dashPattern=[4,3]; if(BADGE[b].o) sw.opacity=BADGE[b].o; sw.cornerRadius=6;
  T(lg, b+" — "+txt, lx+36, 22, null, 12, 700, BADGE[b].s); lx += 36 + (b==="IMPACT"?300:180); }
T(lg, "NG = vạch đỏ bên trái · ◇ = rẽ nhánh · ▶ = điểm vào", lx, 22, null, 12, 500, "#CF222E");
// CR-1 Flow (format Output 1 Phan A + Phan B)
const fr = F(s, "CR-1 Flow — luồng nghiệp vụ bị CR chạm (format Output 1)", 40, 220, 2280, 400, "#FFFFFF");
fr.strokes=[paint("#D0D7DE")]; fr.cornerRadius=12;
T(fr, "CR-1 — Flow thay đổi (Output 1 · Phần A Business & Logic Flow + Phần B Technology)", 40, 24, 1700, 22, 700);
T(fr, D.flow_note, 40, 54, 1700, 12, 400, "#57606A");
const CX = {actor:98, trigger:250, function:500, technology:770, outcome:1040, edge:1320};
const CW = {actor:150, trigger:200, function:220, technology:220, outcome:220, edge:440};
for (const [k,lab] of [["actor","ACTOR"],["trigger","TRIGGER"],["function","FUNCTION"],["technology","TECHNOLOGY"],["outcome","OUTCOME"],["edge","EDGE / EXCEPTIONAL — chưa chốt"]]) T(fr, lab, CX[k]+(k==="actor"?2:0), 90, null, 12, 700, "#57606A");
R(fr, 40, 109, 1730, 2, "#1F2328");
let y = 130;
for (const L of D.flows) {
  T(fr, L.lane + " · " + L.title, 40, y, 1700, 16, 700, "#0969DA");
  T(fr, L.note, 40, y+22, 1700, 12, 400, "#57606A");
  const top = y + 56; const nodes = {}; let maxRow = 0; let edgeIdx = 0;
  for (const n of L.nodes) {
    const row = n.col==="edge" ? edgeIdx++ : (n.row || 0); maxRow = Math.max(maxRow, row);
    const yy = top + row*120;
    let f;
    if (n.col === "actor") { f = badgeBox(fr, n, CX.actor-40, yy, 150, 84, "flow", "pill"); }
    else f = badgeBox(fr, n, CX[n.col], yy, CW[n.col], n.col==="edge"?70:84, n.col==="edge"?"edge":"flow", n.type==="decision"?"decision":(n.type==="ng"?"ng":null));
    nodes[n.key] = f; created.push(f.id);
  }
  for (const [a,b,lab,st] of L.edges) created.push(arrow(fr, nodes[a], nodes[b], lab, st).id);
  let lb = 0; for (const k in nodes) lb = Math.max(lb, nodes[k].y + nodes[k].height);
  y = Math.max(top + (maxRow+1)*120, lb + 30) + 40;
  R(fr, 40, y, 1730, 1, "#D0D7DE"); y += 60;
}
// Phan B Technology (chi cong nghe bi cham)
T(fr, "TECHNOLOGY — thay đổi / bị ảnh hưởng", 1800, 90, 460, 13, 700, "#F4860C");
let ty = 120;
for (const n of D.tech) { const f = badgeBox(fr, n, 1800, ty, 460, 64, "tech"); created.push(f.id); ty = f.y + f.height + 12; }
fr.resize(2280, Math.max(y, ty) + 20);
fit(s);
return {section: s.id, flow: fr.id, created: created.length, bottom: fr.y + fr.height};
"""
    return body % (esc({"subtitle": view["subtitle"], "flow_note": view["flow_note"], "flows": view["flows"],
                        "tech": view.get("tech") or []}), view["_x"], view["_y"])


# ---------------------------------------------------------------- 02: CR-2 Screen Flow
def layout_group(g):
    """depth = do sau theo canh tu start (bo canh quay lui); -> {key: (depth, idx)}."""
    keys = [n["key"] for n in g["nodes"] if n["type"] != "edge"]
    adj = {k: [] for k in keys}
    for e in g["edges"]:
        if e[0] in adj and e[1] in adj:
            adj[e[0]].append(e[1])
    starts = [n["key"] for n in g["nodes"] if n["type"] == "start"] or keys[:1]
    depth = {k: 0 for k in starts}
    order = list(starts)
    i = 0
    while i < len(order):
        k = order[i]
        i += 1
        for b in adj[k]:
            if b not in depth:
                depth[b] = depth[k] + 1
                order.append(b)
    for k in keys:
        depth.setdefault(k, max(depth.values() or [0]) + 1)
    children = {k: [] for k in keys}
    seen = set(starts)
    for k in order:                                   # cay BFS: moi node 1 cha
        for c in adj[k]:
            if c not in seen and depth[c] == depth[k] + 1:
                children[k].append(c)
                seen.add(c)
    pos, used = {}, [-1]

    def place(k, row):
        pos[k] = (depth[k], row)
        used[0] = max(used[0], row)
        for i, c in enumerate(children[k]):
            place(c, row if i == 0 else used[0] + 1)
    for st in starts:
        place(st, used[0] + 1)
    for k in keys:                                    # node khong noi tu start
        if k not in pos:
            place(k, used[0] + 1)
    return pos


def part_screen_flow(view):
    groups = []
    for g in view["screen_groups"]:
        pos = layout_group(g)
        groups.append({**g, "pos": {k: list(v) for k, v in pos.items()}})
    index = []
    for g in view["screen_groups"]:
        for n in g["nodes"]:
            if n["type"] in ("screen", "system") and n["badge"] != "AS-IS":
                index.append([n["ref"], n["label"], g.get("site", ""), n["badge"]])
    body = r"""
const D = %s;
const {page, s} = await section();
if (!s) return {error: "chua co section — chay 01 truoc"};
const created=[];
const y0 = bottom(s) + 120;
const fr = F(s, "CR-2 Screen Flow — màn bị CR chạm (format Output 2)", 40, y0, 3000, 400, "#FFFFFF");
fr.strokes=[paint("#D0D7DE")]; fr.cornerRadius=12;
T(fr, "CR-2 — Screen Flow thay đổi (Output 2 · Group · Start ▶ · Screen · ◇ Decision · System · NG inline · Terminal · Edge/Exceptional)", 40, 24, 2300, 22, 700);
T(fr, D.note, 40, 54, 2300, 12, 400, "#57606A");
const NW=220, NH=78, DX=270, DY=118;
let y = 100;
for (const G of D.groups) {
  T(fr, "Group " + G.id + " — " + G.title + "  (" + G.site + ")", 40, y, 2200, 16, 700, "#0969DA");
  if (G.note) T(fr, G.note, 40, y+22, 2200, 12, 400, "#57606A");
  const top = y + 56; const nodes={}; let maxD=0, maxI=0;
  for (const n of G.nodes) { if (n.type==="edge") continue;
    const [d,i] = G.pos[n.key]; maxD=Math.max(maxD,d); maxI=Math.max(maxI,i);
    const shape = n.type==="start" ? "pill" : (n.type==="decision" ? "decision" : (n.type==="ng" ? "ng" : null));
    const w = n.type==="start" ? 200 : (n.type==="decision" ? 180 : NW), h = n.type==="decision" ? 64 : NH;
    const f = badgeBox(fr, n, 40 + d*DX, top + i*DY, w, h, n.type==="screen"||n.type==="system" ? "screen" : "flow-step", shape);
    if (n.type==="system") { f.fills=[paint("#E8F7EC")]; }
    nodes[n.key]=f; created.push(f.id); }
  for (const [a,b,lab,st] of G.edges) if (nodes[a] && nodes[b]) created.push(arrow(fr, nodes[a], nodes[b], lab, st).id);
  // Edge / Exceptional panel
  const ex = G.nodes.filter(n=>n.type==="edge");
  const px = 40 + (maxD+1)*DX + 40;
  if (ex.length) { T(fr, "EDGE / EXCEPTIONAL — chưa chốt, không vẽ inline", px, top-20, 420, 11, 700, "#6639BA");
    let ey = top; ex.forEach((n)=>{ const f=badgeBox(fr, n, px, ey, 420, 74, "edge"); created.push(f.id); nodes["_e"+ey]=f; ey = f.y + f.height + 12; }); }
  let gb = top; for (const k in nodes) gb = Math.max(gb, nodes[k].y + nodes[k].height);
  y = gb + 70; R(fr, 40, y, 2300, 1, "#D0D7DE"); y += 60;
}
// ④ Screen Index (pham vi CR)
let maxR = 0; for (const c of fr.children) maxR = Math.max(maxR, c.x + c.width);
const ix = Math.max(2420, maxR + 60); T(fr, "④ SCREEN INDEX — phạm vi CR", ix, 100, 540, 14, 700, "#0969DA");
let iy = 130;
const hdr = F(fr, "idx-header", ix, iy, 540, 28, "#DAEEF3"); T(hdr,"Ref",8,6,90,11,700); T(hdr,"Màn hình",100,6,300,11,700); T(hdr,"Site",400,6,60,11,700); T(hdr,"Badge",465,6,70,11,700);
iy += 28;
for (const [ref,lab,site,b] of D.index) { const r=F(fr,"IDX · "+ref, ix, iy, 540, 26, BADGE[b].f); T(r,ref,8,6,90,10,700,BADGE[b].s); T(r,lab,100,6,295,10,400); T(r,site,400,6,60,10,400); T(r,b,465,6,70,10,700,BADGE[b].s); iy+=26; }
fr.resize(ix + 580, Math.max(y, iy) + 20);
fit(s);
return {frame: fr.id, created: created.length, bottom: fr.y + fr.height};
"""
    return body % esc({"note": view["screen_note"], "groups": groups, "index": index})


# ---------------------------------------------------------------- 03: CR Change Table (thong ke)
def part_change_table(stats, totals):
    body = r"""
const D = %s;
const {page, s} = await section();
if (!s) return {error: "chua co section"};
const y0 = bottom(s) + 120;
const fr = F(s, "CR Change Table — thống kê thay đổi", 40, y0, 1180, 200, "#FFFFFF");
fr.strokes=[paint("#D0D7DE")]; fr.cornerRadius=12;
T(fr, "CR Change Table — thống kê (chi tiết từng hạng mục: CR-001_Impact.xlsx)", 32, 24, 1100, 20, 700);
T(fr, D.note, 32, 54, 1100, 12, 400, "#57606A");
const cols = [["Đối tượng",300],["NEW",110],["UPD",110],["DEL",110],["IMPACT",110],["Tổng",110],["実装 MD",160]];
const fills = {NEW:"#EDFDF0",UPD:"#FFF9EB",DEL:"#FFF6F5",IMPACT:"#FBEEFF"};
let y = 90, x = 32;
for (const [c,w] of cols) { const h=F(fr,"hdr-"+c,x,y,w,32,fills[c]||"#DAEEF3"); h.strokes=[paint("#D0D7DE")]; T(h,c,8,8,w-16,12,700,"#1F2328", c==="Đối tượng"?null:"CENTER"); x+=w; }
y += 32;
for (const row of D.rows) { x = 32; const tot = row[0]==="Tổng";
  row.forEach((v,k)=>{ const w=cols[k][1]; const c=F(fr, k===0 ? "STATROW · "+v : "STAT · "+row[0]+" · "+cols[k][0], x, y, w, 30, tot?"#F6F8FA":(k>0&&k<5&&Number(v)>0?fills[cols[k][0]]:"#FFFFFF"));
    c.strokes=[paint("#D0D7DE")]; if(k>0){ c.setSharedPluginData(NS,"kind","stat"); c.setSharedPluginData(NS,"value",String(v)); }
    T(c, String(v), 8, 7, w-16, 12, tot||k===0?700:400, "#1F2328", k===0?null:"CENTER"); x+=w; }); y+=30; }
y += 16;
for (const [lab,val,unit] of D.totals) { const c=F(fr,"STAT · TOTAL · "+lab,32,y,1010,34,"#DAEEF3"); c.strokes=[paint("#D0D7DE")];
  c.setSharedPluginData(NS,"kind","stat"); c.setSharedPluginData(NS,"value",String(val));
  T(c, lab, 10, 8, 640, 13, 700); T(c, String(val)+" "+unit, 660, 8, 340, 14, 700, "#0969DA", "RIGHT"); y+=38; }
fr.resize(1180, y + 24);
fit(s);
return {frame: fr.id, bottom: fr.y + fr.height};
"""
    rows = [[o] + [int(v) if v == int(v) else v for v in (d["NEW"], d["UPD"], d["DEL"], d["IMPACT"], d["total"])]
            + [C.fmt_md(d["md"])] for o, d in stats]
    return body % esc({"note": "Số lượng = số đối tượng (màn / API / bảng / cột / rule …) theo đơn vị của bảng đơn giá. "
                               "総工数 = 実装 × hệ số công đoạn của template Estimation.", "rows": rows,
                       "totals": totals})


# ---------------------------------------------------------------- 04: CR-3 Screens (mockup tu token DS)
def resolve_block_tokens(item, toks_by_site, comps_by_site, errors):
    """Kiem block dung component co trong DS (site hoac 'from'); -> list DS ref + gan _tok cho block."""
    site = item["site"]
    refs = set()
    for c in SHELL_COMP.get(item.get("shell", "public"), []):
        if c.lower() not in comps_by_site.get(site, set()):
            errors.append("%s: shell %s can component %s — %s chua co (khai shell khac hoac bo sung DS)" % (
                item["ref"], item.get("shell"), c, site))
        refs.add("DS-component:%s:%s" % (site, c))
    def walk(blocks, parent_site):
        for b in blocks:
            comp = BLOCK_COMP.get(b.get("t"), "?")
            if comp == "?":
                errors.append("%s: block t=%r khong ho tro" % (item["ref"], b.get("t")))
                continue
            src = b.get("from") or parent_site
            need = [(comp, src)] if comp else []
            if b.get("badge"):                         # badge dat trong card
                need.append(("Badge", b.get("badge_from") or src))
            for cp, st in need:
                if cp.lower() not in comps_by_site.get(st, set()):
                    other = [s for s, cs in comps_by_site.items() if cp.lower() in cs and s != st]
                    errors.append("%s: block %s can component %s — %s chua co trong DS%s" % (
                        item["ref"], b["t"], cp, st,
                        "; khai \"from\": \"%s\" (muon, hoi CR-3b) hoac hoi designer" % other[0] if other else
                        "; khong site nao co — UI-TOKEN-NEW + hoi designer, khong tu che"))
                refs.add("DS-component:%s:%s" % (st, cp))
            b["_site"] = src
            if b.get("blocks"):
                walk(b["blocks"], src)
    walk(item["blocks"], site)
    return sorted(refs)


def part_screens(items, toks_by_site, offset_y_first, note):
    body = r"""
const D = %s;
const {page, s} = await section();
if (!s) return {error: "chua co section"};
let host = s.children.find(c=>c.name.startsWith("CR-3 Screens"));
if (!host) { host = F(s, "CR-3 Screens — màn đề xuất theo Design System", 40, bottom(s)+120, 3120, 200, "#FFFFFF");
  host.strokes=[paint("#D0D7DE")]; host.cornerRadius=12;
  T(host, "CR-3 — Màn đề xuất (token + component Design System của baseline)", 40, 24, 3000, 22, 700);
  T(host, D.note, 40, 54, 3000, 12, 400, "#57606A"); }
const created=[];
function tok(site, name, dflt){ const v=D.tok[site].t[name]; if((v===undefined||v===null) && dflt===undefined) throw new Error("token '"+name+"' khong co trong Design System "+site+" — khong tu che (CR-3b)"); return v===undefined||v===null ? dflt : v; }
function ty(site, name){ const v=D.tok[site].type[name]; if(!v) throw new Error("type style '"+name+"' khong co trong Design System "+site); return v; }
function txt(parent, site, s, style, color, w){ const st=ty(site,style); const t=figma.createText();
  t.fontName={family:"Noto Sans JP",style:W8[st.weight]||"Regular"}; t.characters=String(s); t.fontSize=st.size;
  t.fills=[paint(tok(site,color))]; parent.appendChild(t); if(w){ t.layoutSizingHorizontal="FIXED"; t.resize(w,t.height); t.textAutoResize="HEIGHT"; } return t; }
function col(parent, gap, name){ const f=figma.createAutoLayout("VERTICAL",{itemSpacing:gap}); f.name=name||"col"; f.fills=[]; parent.appendChild(f); return f; }
function row(parent, gap, name){ const f=figma.createAutoLayout("HORIZONTAL",{itemSpacing:gap}); f.name=name||"row"; f.fills=[]; f.counterAxisAlignItems="CENTER"; parent.appendChild(f); return f; }
function boxv(parent, site, w, h, fill, radius, name){ const f=figma.createFrame(); f.name=name||"box"; f.resize(w,h); f.fills=[paint(tok(site,fill))]; f.cornerRadius=parseFloat(tok(site,radius))||0; parent.appendChild(f); return f; }
function field(parent, site, b, w){ const c=col(parent,6,"TextField");
  const lab=row(c,6,"label"); txt(lab,site,b.label, site==="WEB-01"?"label-14":"text-16", site==="WEB-01"?"text-label":"text-high");
  if(b.required) txt(lab,site,"[必須]", site==="WEB-01"?"label-14":"text-12","negative-600");
  if(b.hint) txt(c,site,b.hint,"text-12", site==="WEB-01"?"text-low":"text-high", w);
  const H = site==="WEB-01" ? parseFloat(tok(site,"control-md","48")) : parseFloat(tok(site,"field-height","56"));
  const bx=boxv(c,site,w,H, site==="WEB-01"?"page-bg":"primary-subtle", site==="WEB-01"?"radius-md":"radius-field","input");
  const p=txt(bx,site,b.value||b.placeholder||"", site==="WEB-01"?"text-16-light":"text-16-light", b.value ? (site==="WEB-01"?"text-middle":"text-field") : (site==="WEB-01"?"text-placeholder":"text-low"));
  p.x=15; p.y=(H-p.height)/2;
  if(b.select){ const a=txt(bx,site,"▼","text-14","icon-default"); a.x=w-30; a.y=(H-a.height)/2; }
  if(b.unit){ const u=txt(bx,site,b.unit,"text-16", site==="WEB-01"?"text-low":"text-high"); u.x=w-u.width-16; u.y=(H-u.height)/2; }
  return c; }
function button(parent, site, it){ const solid = it.variant!=="outline"; const lg = it.size!=="sm";
  const H = site==="WEB-01" ? (lg?48:40) : parseFloat(tok(site, lg?"control-md":"control-sm","64"));
  const W = it.width || (site==="WEB-01" ? (lg?200:140) : (lg?320:180));
  const f=boxv(parent,site,W,H, solid?"primary":(site==="WEB-01"?"surface":"surface"), site==="WEB-01"?"radius-lg":"radius-button","Button");
  if(!solid){ f.strokes=[paint(tok(site,"primary"))]; f.strokeWeight=1; }
  if(solid && site==="WEB-01"){ const a=paint(tok(site,"primary-gradient-top")), z=paint(tok(site,"primary"));
    f.fills=[{type:"GRADIENT_LINEAR", gradientTransform:[[0,1,0],[-1,0,1]], gradientStops:[{position:0,color:{...a.color,a:1}},{position:1,color:{...z.color,a:1}}]}]; }
  const t=txt(f,site,it.text, site==="WEB-01"?"text-16-bold":(lg?"heading-20-bold":"heading-16-bold"), solid?"on-primary":"primary-text"); t.x=(W-t.width)/2; t.y=(H-t.height)/2; return f; }
function table(parent, site, b, w){ const s2=b._site; const c=col(parent,0,"Table"); c.cornerRadius=8; c.clipsContent=true;
  const ws=b.widths || b.cols.map(()=>Math.floor(w/b.cols.length));
  const hh=parseFloat(tok(s2,"table-header-height","54")), rh=parseFloat(tok(s2,"table-row-height","52"));
  const hr=row(c,0,"thead"); hr.fills=[paint(tok(s2,"surface-subtle"))];
  b.cols.forEach((h,k)=>{ const cell=boxv(hr,s2,ws[k],hh,"surface-subtle","radius-none","th"); const t=txt(cell,s2,h,"text-16-bold","text-table-header",ws[k]-20); t.x=10; t.y=(hh-t.height)/2; });
  for(const r of b.rows){ const tr=row(c,0,"tr"); r.forEach((v,k)=>{ const cell=boxv(tr,s2,ws[k],rh,"surface","radius-none","td");
     cell.strokes=[paint(tok(s2,"divider-low"))]; cell.strokeBottomWeight=1; cell.strokeTopWeight=0; cell.strokeLeftWeight=0; cell.strokeRightWeight=0;
     const t=txt(cell,s2,v,"text-16-light","text-middle",ws[k]-20); t.x=10; t.y=(rh-t.height)/2; }); }
  return c; }
function badge(parent, site, text){ const s2=site; const f=figma.createAutoLayout("HORIZONTAL"); f.name="Badge"; f.paddingLeft=f.paddingRight=parseFloat(tok(s2,"space-20","20")); f.paddingTop=f.paddingBottom=parseFloat(tok(s2,"space-4","4"));
  f.fills=[paint(tok(s2,"divider-middle"))]; f.cornerRadius=999; parent.appendChild(f); txt(f,s2,text,"text-14","text-low"); return f; }
function card(parent, site, w, tone, name){ const f=figma.createAutoLayout("VERTICAL",{itemSpacing:16}); f.name=name||"Card"; parent.appendChild(f);
  f.fills=[paint(tok(site, tone==="tinted"?"surface-subtle":"surface"))]; f.cornerRadius=parseFloat(tok(site,"radius-lg","10"))||10;
  const pad = site==="WEB-01" ? [32,40] : [40,40]; f.paddingTop=f.paddingBottom=pad[0]; f.paddingLeft=f.paddingRight=pad[1];
  f.layoutSizingHorizontal="FIXED"; f.resize(w, f.height); if(tone!=="tinted"){ f.effects=[{type:"DROP_SHADOW",color:{r:0,g:0,b:0,a:0.12},offset:{x:0,y:2},radius:6,spread:0,visible:true,blendMode:"NORMAL"}]; } return f; }
function blocks(parent, site, list, w){
  for (const b of list) {
    if (b.t==="title") { if(site==="WEB-01"){ txt(parent,site,b.text,"heading-20-semibold","text-high"); }
       else { const c=col(parent,8,"PageHeader"); c.counterAxisAlignItems = b.variant==="mypage"?"MIN":"CENTER"; c.layoutSizingHorizontal="FIXED"; c.resize(w,c.height);
         txt(c,site,b.text, b.variant==="mypage"?"title-36":"heading-32", b.variant==="mypage"?"text-black":"text-high");
         const u=boxv(c,site, b.variant==="mypage"?w:120, b.variant==="mypage"?2:5, b.variant==="mypage"?"primary":"accent-yellow","radius-field","underline"); } }
    else if (b.t==="breadcrumb") txt(parent,site,b.items.join("  ›  "),"text-14", site==="WEB-01"?"text-low":"primary-text");
    else if (b.t==="section") txt(parent,site,b.text, site==="WEB-01"?"heading-20-bold":"heading-24-semibold", site==="WEB-01"?"text-high":"primary-text");
    else if (b.t==="text") txt(parent,site,b.text, b.tone==="note"?"text-12":"text-16", b.tone==="error"?"negative-600":(site==="WEB-01"?"text-middle":"text-high"), w);
    else if (b.t==="field") field(parent,site,b,w);
    else if (b.t==="select") field(parent,site,{...b,select:true},w);
    else if (b.t==="field2") { const r=row(parent,16,"field2"); r.counterAxisAlignItems="MIN"; for(const f of b.fields) field(r,site,f,(w-16*(b.fields.length-1))/b.fields.length); }
    else if (b.t==="radio") { const c=col(parent,8,"Radio"); txt(c,site,b.label, site==="WEB-01"?"label-14":"text-16", site==="WEB-01"?"text-label":"text-high");
       const r=row(c, site==="WEB-01"?16:32, "options"); b.options.forEach((o,k)=>{ const it=row(r,8,"opt"); const d=figma.createEllipse(); d.resize(20,20);
         d.fills=[paint(tok(site,"surface","#ffffff"))]; d.strokes=[paint(tok(site, k===(b.selected||0)?(site==="WEB-01"?"control-checked":"radio-checked"):(site==="WEB-01"?"control-border":"icon-muted")))]; d.strokeWeight= k===(b.selected||0)?6:2; it.appendChild(d);
         txt(it,site,o, site==="WEB-01"?"text-16":"text-18","text-high"); }); }
    else if (b.t==="checkbox") { const s2=b._site||site; const r=row(parent,8,"Checkbox"); const bx=boxv(r,s2,20,20, b.checked?"checkbox-checked":"surface","radius-checkbox","box"); if(!b.checked){ bx.strokes=[paint(tok(s2,"checkbox-border"))]; bx.strokeWeight=2; } txt(r,s2,b.label,"text-16","text-high"); }
    else if (b.t==="buttons") { const r=row(parent,16,"actions"); r.primaryAxisAlignItems="CENTER"; r.layoutSizingHorizontal="FIXED"; r.resize(w,r.height); for(const it of b.items) button(r,site,it); }
    else if (b.t==="table") table(parent,site,b,w);
    else if (b.t==="badge") badge(parent, b._site, b.text);
    else if (b.t==="card") { const c=card(parent, b._site, w, b.tone); if(b.title) txt(c,b._site,b.title, b._site==="WEB-01"?"heading-20-bold":"heading-20-bold","text-high");
       if(b.badge) badge(c, b.badge_from||b._site, b.badge); for(const l of (b.lines||[])) txt(c,b._site,l,"text-16", b._site==="WEB-01"?"text-middle":"text-high", w-80);
       if(b.blocks) blocks(c, b._site, b.blocks, w-80); }
    else if (b.t==="search") { const c=card(parent, site, w, "raised", "SearchCard"); const r=row(c,24,"grid"); r.counterAxisAlignItems="MIN";
       const fw=Math.floor((w-80-48)/3); for(const f of b.fields) field(r,site,{...f, select:!!f.select},fw); blocks(c,site,[{t:"buttons",items:b.buttons}],w-80); }
    else if (b.t==="steps") { const r=row(parent,24,"Steps"); b.items.forEach((s2,k)=>{ const it=row(r,8,"step"); const d=figma.createEllipse(); d.resize(32,32);
       d.fills=[paint(tok(site, k===b.active?"primary":"surface-disabled"))]; it.appendChild(d); txt(it,site,(k+1)+". "+s2, k===b.active?"text-16-bold":"text-16", k===b.active?"primary-text":"text-low"); }); }
    else if (b.t==="modal") { const s2=b._site; const m=card(parent, s2, Math.min(parseFloat(tok(s2,"modal-width","607")), w), "raised", "Modal"); m.counterAxisAlignItems="CENTER";
       txt(m,s2,b.title,"heading-20-bold","text-high"); if(b.message) txt(m,s2,b.message,"text-16","text-middle", 520);
       if(b.field) field(m,s2,b.field,520); blocks(m,s2,[{t:"buttons",items:b.buttons.map(x=>({...x,size:"sm"})),_site:s2}],520); }
    else if (b.t==="pagination") { const r=row(parent,8,"Pagination"); r.layoutSizingHorizontal="FIXED"; r.resize(w,r.height); r.primaryAxisAlignItems="MAX";
       ["‹","1","2","3","›"].forEach((p,k)=>{ const c=boxv(r,site,32,32, k===1?"primary":"surface","radius-sm","pg"); const t=txt(c,site,p,"text-14", k===1?"on-primary":"text-middle"); t.x=(32-t.width)/2; t.y=(32-t.height)/2; }); }
  } }
function shell(item){ const site=item.site; const W=parseFloat(tok(site,"viewport-web","1440"));
  const fr=figma.createAutoLayout("VERTICAL",{itemSpacing:0}); fr.name=`${item.badge} · ${item.ref} · ${item.label}`;
  fr.fills=[paint(tok(site,"page-bg","#ffffff"))]; fr.layoutSizingHorizontal="FIXED"; fr.resize(W, fr.height);
  if (item.shell==="admin") { fr.layoutMode="HORIZONTAL"; fr.primaryAxisSizingMode="FIXED"; fr.counterAxisSizingMode="AUTO"; const sw=parseFloat(tok(site,"sidebar-width","265"));
     const nav=col(fr,0,"SideNav"); nav.fills=[paint(tok(site,"page-bg"))]; nav.layoutSizingHorizontal="FIXED"; nav.resize(sw,nav.height); nav.layoutAlign="STRETCH"; nav.paddingTop=24;
     txt(nav,site,"KidoKido 管理画面","heading-18-bold","primary-text").name="logo";
     for (const m of item.nav||[]) { const it=boxv(nav,site,sw,parseFloat(tok(site,"nav-item-height","58")), m===item.nav_active?"nav-active-light":"page-bg","radius-md","nav-item");
        const t=txt(it,site,m,"nav-14", m===item.nav_active?"on-nav-active":"text-low"); t.x=24; t.y=(it.height-t.height)/2; }
     const main=col(fr,32,"main"); main.paddingLeft=20; main.paddingTop=main.paddingRight=main.paddingBottom=32; main.layoutSizingHorizontal="FIXED"; main.resize(W-sw, main.height);
     blocks(main, site, item.blocks, W-sw-52); }
  else if (item.shell==="auth" && site==="WEB-01") { // man dang nhap admin: khong sidebar, khong header — card giua page-bg
     const body=row(fr,0,"body"); body.layoutSizingHorizontal="FILL"; body.primaryAxisAlignItems="CENTER"; body.paddingTop=body.paddingBottom=120;
     const main=col(body,24,"content"); main.layoutSizingHorizontal="FIXED"; main.resize(560, main.height);
     blocks(main, site, item.blocks, 560); }
  else { // WEB-02: AppHeader 2 tang + noi dung giua + footer
     const hdr=col(fr,0,"AppHeader"); hdr.layoutSizingHorizontal="FILL";
     const tb=row(hdr,24,"topbar"); tb.fills=[paint(tok(site,"surface"))]; tb.layoutSizingHorizontal="FILL"; tb.paddingLeft=tb.paddingRight=40; tb.paddingTop=tb.paddingBottom=18; tb.primaryAxisAlignItems="MAX";
     txt(tb,site, item.shell==="auth" ? "新規利用登録 · ログイン" : "マイページ · ログアウト","text-20","primary-text");
     const band=row(hdr,48,"nav-band"); band.fills=[paint(tok(site,"surface-subtle"))]; band.layoutSizingHorizontal="FILL"; band.paddingLeft=40; band.paddingTop=band.paddingBottom=56;
     txt(band,site,"ボーネルンド あそび場","heading-16-bold","primary-text"); for(const m of ["当日利用","回数券購入","1DAYパス事前購入","年間・マンスリーパス購入","待ち時間/販売状況"]) txt(band,site,m,"heading-20-bold","primary-text");
     const body=row(fr,40,"body"); body.counterAxisAlignItems="MIN"; body.layoutSizingHorizontal="FILL"; body.paddingTop=40; body.paddingBottom=64; body.paddingLeft=40; body.paddingRight=40;
     let cw=parseFloat(tok(site,"content-max","896"));
     if (item.shell==="mypage") { const nav=col(body,0,"SideNav"); nav.fills=[paint(tok(site,"sidebar-bg"))]; nav.paddingTop=nav.paddingBottom=16;
        const sbw = parseFloat(tok(site,"sidebar-width", item.sidebar_width));
        for(const m of item.nav||[]){ const it=boxv(nav,site,sbw,parseFloat(tok(site,"nav-item-height","48")), m===item.nav_active?"surface":"sidebar-bg","radius-none","nav-item");
          const t=txt(it,site,m,"text-16", m===item.nav_active?"primary-text":"text-black"); t.x=20; t.y=(it.height-t.height)/2; } cw = W-80-sbw-40; }
     else { body.primaryAxisAlignItems="CENTER"; }
     const main=col(body,24,"content"); main.layoutSizingHorizontal="FIXED"; main.resize(cw, main.height);
     blocks(main, site, item.blocks, cw);
     const ft=row(fr,0,"footer"); ft.fills=[paint(tok(site,"surface-subtle"))]; ft.layoutSizingHorizontal="FILL"; ft.paddingTop=ft.paddingBottom=24; ft.primaryAxisAlignItems="CENTER";
     txt(ft,site,"© BørneLund","text-12","text-high"); }
  return fr; }
let gx = 40, gy = host.height + 0;
const existing = host.children.filter(c=>/^(NEW|UPD|DEL|IMPACT|AS-IS) · /.test(c.name)).length;
let k = existing;
let yStart = 100; for (const c of host.children) if (c.name.startsWith("cap ·") || /^(NEW|UPD) · /.test(c.name)) yStart = Math.max(yStart, c.y + c.height + 120);
let rowH = 0; let col2 = 0;
for (const it of D.items) {
  const x = 40 + (col2 %% 2) * 1540;
  const cap = T(host, `${it.badge} · ${it.ref} · ${it.label}`, x, yStart, 1440, 16, 700, BADGE[it.badge].s); cap.name = "cap · " + it.ref;
  const note = T(host, "DS: " + it.ds.join(", ") + (it.borrow.length ? "  ·  MƯỢN: " + it.borrow.join(", ") + " (chờ designer)" : "") + (it.sidebar_note ? "  ·  sidebar " + it.sidebar_width + "px: " + it.sidebar_note : "") + "  ·  Font Hiragino Kaku Gothic Pro → hiển thị Noto Sans JP (Figma không có font gốc)", x, yStart+24, 1440, 11, 400, "#57606A"); note.name="cap-note";
  const fr = shell(it); host.appendChild(fr); fr.x = x; fr.y = yStart + 60;
  const b = BADGE[it.badge]; fr.strokes=[paint(b.s)]; fr.strokeWeight=4; if (b.d) fr.dashPattern=[10,6];
  fr.setSharedPluginData(NS,"kind","mockup"); fr.setSharedPluginData(NS,"ds",it.ds.join(";")); fr.setSharedPluginData(NS,"site",it.site);
  created.push(fr.id); rowH = Math.max(rowH, fr.height + 60);
  col2++; if (col2 %% 2 === 0) { yStart += rowH + 160; rowH = 0; }
}
let hh=0; for (const c of host.children) hh=Math.max(hh,c.y+c.height); host.resize(3120, hh+60);
fit(s);
return {host: host.id, created};
"""
    return body % esc({"note": note, "items": items, "tok": toks_by_site})


READBACK = r"""
const page = await figma.getNodeByIdAsync(PAGE_ID); await figma.setCurrentPageAsync(page);
const s = page.children.find(c=>c.type==="SECTION" && c.name===SECTION_NAME);
if (!s) return {error:"khong thay section"};
const rx = /^(NEW|UPD|DEL|IMPACT|AS-IS) · ([^·]+?) · /;
const hex = c => "#"+[c.r,c.g,c.b].map(v=>Math.round(v*255).toString(16).padStart(2,"0")).join("");
const nodes = s.findAll(n => rx.test(n.name)).map(n => { const m = n.name.match(rx); const kind = n.getSharedPluginData("crkit","kind")||"other";
  const o = {id:n.id, name:n.name, badge:m[1], ref:m[2].trim(), kind};
  if (kind==="mockup") { o.ds = n.getSharedPluginData("crkit","ds"); o.site = n.getSharedPluginData("crkit","site");
    const cols = new Set(); for (const d of n.findAll(x => "fills" in x && Array.isArray(x.fills))) for (const p of d.fills) if (p.type==="SOLID") cols.add(hex(p.color));
    o.colors = [...cols]; }
  return o; });
const arrows = s.findAll(n => n.name.startsWith("ARROW · ")).map(n => ({id:n.id, from:n.getSharedPluginData("crkit","from"), to:n.getSharedPluginData("crkit","to")}));
const stats = s.findAll(n => n.name.startsWith("STAT · ")).map(n => ({name:n.name, value:n.getSharedPluginData("crkit","value")}));
const legend = s.findAll(n => n.name.startsWith("LEGEND")).length;
const unbadged = s.findAll(n => n.type==="FRAME" && n.parent && n.parent.name && (n.parent.name.startsWith("CR-1") || n.parent.name.startsWith("CR-2")) && !rx.test(n.name) && !/^(IDX|idx-|ARROW)/.test(n.name)).map(n=>n.name).slice(0,20);
const sb = s.absoluteBoundingBox; const others = page.children.filter(c=>c.id!==s.id).map(c=>({name:c.name, ...c.absoluteBoundingBox}));
const overlap = others.filter(b=>!(b.x+b.width<=sb.x||sb.x+sb.width<=b.x||b.y+b.height<=sb.y||sb.y+sb.height<=b.y)).map(b=>b.name);
return {section:{id:s.id, name:s.name, x:sb.x, y:sb.y, w:sb.width, h:sb.height}, nodes, arrows, stats, legend, unbadged, overlap};
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cr-json", required=True)
    ap.add_argument("--view", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--rates", required=True)
    ap.add_argument("--page-id", required=True)
    ap.add_argument("--y", type=float, required=True, help="y dat section (>= day node cu + 400)")
    ap.add_argument("--x", type=float, default=0)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--template", default=None)
    ap.add_argument("--per-file", type=int, default=2, help="so man CR-3 moi file JS")
    a = ap.parse_args()
    cr = C.load_json(a.cr_json)
    view = C.load_json(a.view)
    _rm, rates = C.load_rates(a.rates)
    B = C.load_baseline(a.baseline)
    tpl = C.find_template(a.template, KIT)
    est = C.load_estimation_template(tpl)[1] if tpl else None
    errors = []
    imp_ids = {i["id"]: i for i in cr.get("impacts") or []}

    def ok_ref(n, where):
        if n.get("badge") not in BADGES:
            errors.append("%s %s badge=%r" % (where, n.get("label"), n.get("badge")))
        if not C.txt(n.get("ref")):
            errors.append("%s %s thieu ref" % (where, n.get("label")))
    for L in view.get("flows") or []:
        keys = {n["key"] for n in L["nodes"]}
        for n in L["nodes"]:
            ok_ref(n, "flow %s" % L["lane"])
            if n.get("col") not in FLOW_COLS:
                errors.append("flow %s node %s col=%r" % (L["lane"], n.get("key"), n.get("col")))
        for e in L["edges"]:
            if e[0] not in keys or e[1] not in keys:
                errors.append("flow %s canh %s->%s tro toi key khong co" % (L["lane"], e[0], e[1]))
            while len(e) < 4:
                e.append("")
        L.setdefault("note", "")
        linked = {e[0] for e in L["edges"]} | {e[1] for e in L["edges"]}
        errors += ["flow %s node %s khong co canh — Output 1 cam the roi" % (L["lane"], n["key"])
                   for n in L["nodes"] if n.get("col") != "edge" and n["key"] not in linked]
    for n in view.get("tech") or []:
        ok_ref(n, "tech")
    for g in view.get("screen_groups") or []:
        keys = {n["key"] for n in g["nodes"]}
        for n in g["nodes"]:
            ok_ref(n, "group %s" % g["id"])
            if n.get("type") not in SCREEN_TYPES:
                errors.append("group %s node %s type=%r" % (g["id"], n.get("key"), n.get("type")))
        for e in g["edges"]:
            if e[0] not in keys or e[1] not in keys:
                errors.append("group %s canh %s->%s tro toi key khong co" % (g["id"], e[0], e[1]))
            while len(e) < 4:
                e.append("")
        linked = {e[0] for e in g["edges"]} | {e[1] for e in g["edges"]}
        errors += ["group %s node %s khong co canh — Output 2 cam the roi" % (g["id"], n["key"])
                   for n in g["nodes"] if n.get("type") != "edge" and n["key"] not in linked]
    # CR-3: token + component DS
    sites = sorted({it["site"] for it in (view.get("screens") or {}).get("items") or []})
    toks = {}
    for st in sorted(set(sites) | {s for s in B["ds"]}):
        try:
            toks[st] = load_tokens(a.baseline, st)
        except (OSError, ValueError) as e:
            errors.append("khong doc duoc tokens.json %s: %s" % (st, e))
    comps = {s: B["ds"][s]["comps"] for s in B["ds"]}
    scr = view.get("screens") or {}
    ds_read = scr.get("ds_read") or []
    items = scr.get("items") or []
    if items:
        for st in sites:
            need = [os.path.join("04_DesignSystem", st, "project", f) for f in ("README.md", "tokens.json")]
            for nd in need:
                if not any(nd in p for p in ds_read):
                    errors.append("CR-3: chua khai da doc %s (screens.ds_read) — doc Design System TRUOC khi ve" % nd)
    for it in items:
        ok_ref(it, "CR-3")
        if it.get("shell") == "mypage" and "sidebar-width" not in (toks.get(it["site"]) or {}).get("t", {}):
            if not it.get("sidebar_width") or not C.txt(it.get("sidebar_note")):
                errors.append("%s: %s chua co token sidebar-width (TBD) — khai sidebar_width + sidebar_note (nguon / "
                              "quyet dinh cua user o CR-3b), khong tu dat" % (it["ref"], it["site"]))
        it["ds"] = resolve_block_tokens(it, toks, comps, errors)
        it["borrow"] = sorted({r.split(":")[1] for r in it["ds"] if r.split(":")[1] != it["site"]})
        it.setdefault("label", it.get("title", ""))
    if errors:
        print("cr-figma.json KHONG hop le — khong sinh JS:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        return 1
    os.makedirs(a.out_dir, exist_ok=True)
    meta = cr["meta"]
    section = "%s — %s (baseline %s → %s)" % (meta["cr_id"], view.get("title") or meta["cr_title"],
                                               meta["baseline_version"].split("_")[0], meta["cr_version"].split("_")[0])
    hv = {"page_id": a.page_id, "section": section}
    stats = C.object_stats(cr["impacts"], rates)
    grand = stats[-1][1]["md"]
    totals = [("実装 — MD theo bảng đơn giá", C.fmt_md(grand), "MD")]
    if est:
        k = (1 + est["ratio_K"] + est["ratio_L"] + est["ratio_N"]) * (1 + est["ratio_O"])
        pd = round(grand * k, 2)
        totals += [("総工数 — 人日 (要件定義 + UI/UX + 実装 + テスト + 管理)", C.fmt_md(pd), "人日"),
                   ("人月 (人日 / %s)" % C.fmt_md(est["md_per_month"]), C.fmt_md(round(pd / est["md_per_month"], 2)), "人月")]
    mn, ex = C.plan_md(cr["impacts"], rates)
    totals += [("trong đó 最小改修案 — 実装", C.fmt_md(mn), "MD"), ("trong đó 拡張案 — 実装", C.fmt_md(ex), "MD")]
    view.setdefault("subtitle", "Baseline %s → %s · %d hạng mục · 実装 %s MD (đơn giá %s) · Không sửa Output 1/2 baseline — "
                    "chỉ vẽ phần CR chạm + hàng xóm 1 bước" % (meta["baseline_version"], meta["cr_version"],
                                                              len(cr["impacts"]), C.fmt_md(grand), _rm.get("status")))
    view.setdefault("flow_note", "Chỉ các lane FL-xx của baseline bị CR chạm (+ lane nghiệp vụ mới). Node AS-IS = giữ nguyên làm ngữ cảnh.")
    view.setdefault("screen_note", "Chỉ màn có dòng Impact + màn dẫn tới (AS-IS). Mỗi node đúng 1 badge; NG vẽ inline; case chưa chốt → panel Edge/Exceptional.")
    view["_x"], view["_y"] = a.x, a.y
    files = []

    def write(name, body):
        js = js_file(hv, body)
        if len(js.encode("utf8")) > MAX_JS:
            errors.append("%s %d byte > %d — chia nho cr-figma.json" % (name, len(js.encode("utf8")), MAX_JS))
        p = os.path.join(a.out_dir, name)
        open(p, "w", encoding="utf8").write(js)
        files.append((name, len(js.encode("utf8"))))
    write("01-shell-flow.js", part_shell_flow(view, ""))
    if view.get("screen_groups"):
        write("02-screen-flow.js", part_screen_flow(view))
    write("03-change-table.js", part_change_table(stats, totals))
    note = ("Dựng từ tokens.json + component README của Design System baseline (đã đọc: %s). Dữ liệu mẫu theo "
            "DATA-PRIVACY §4. Viền khung = badge thay đổi." % ", ".join(os.path.basename(os.path.dirname(os.path.dirname(p)))
                                                                    + "/" + os.path.basename(p) for p in ds_read))
    per = max(1, a.per_file)
    for k in range(0, len(items), per):
        write("04-screens-%02d.js" % (k // per + 1), part_screens(items[k:k + per], toks, 0, note))
    open(os.path.join(a.out_dir, "99-readback.js"), "w", encoding="utf8").write(
        "const PAGE_ID = %s;\nconst SECTION_NAME = %s;\n%s" % (esc(a.page_id), esc(section), READBACK))
    files.append(("99-readback.js", 0))
    if errors:
        for e in errors:
            print("  - " + e, file=sys.stderr)
        return 1
    print("Section: %s" % section)
    for n, sz in files:
        print("  %s  %s" % (n, ("%d byte" % sz) if sz else "doc nguoc -> cr-figma-nodes.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
