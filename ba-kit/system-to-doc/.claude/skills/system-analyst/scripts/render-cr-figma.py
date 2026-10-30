#!/usr/bin/env python3
"""Sinh JS ve view CR tren Figma (Luong 2) tu <ver>/_internal/cr-figma.json — dung FORMAT Output 1 / Output 2.

  python3 render-cr-figma.py --cr-json <ver>/_internal/cr.json --view <ver>/_internal/cr-figma.json \\
      --baseline outputs/<baseline> --rates .claude/config/md-unit-rates.json --page-id <id page> \\
      --y <y dat section> --out-dir <ver>/_internal/figma-js [--template templates/template_estimation.xlsx]

Agent viet cr-figma.json (noi dung nghiep vu), script nay sinh JS (bo cuc, mau, ten node, mui ten) — moi file
<= 45 KB, chay lan luot bang use_figma: 01-shell-flow.js · 02-screen-flow.js · 03-change-table.js ·
04-screens-<n>.js (CR-3) · 99-readback.js (doc nguoc -> cr-figma-nodes.json cho verify-cr-figma.py).

Sub-view (dung thu tu kit requirement-to-flow change-request.md §3):
  CR-1 Flow        = Output 1 dang USE CASE (feedback 20/10/2026): 1 lane = 1 use case — Actor → duong di (happy,
                     trai -> phai) → diem ket thuc; non-happy o hang duoi (◇ -> NG -> ket thuc ✗). KHONG co cot
                     Technology / Function trong lane — cong nghe chi o bang TECHNOLOGY ben phai (NEW/UPD/IMPACT)
  CR-2 Screen Flow = Output 2: site -> flow / use case -> section: moi site 1 Section, trong do moi Group 1 Section
                     con "Flow <id> — <ten>" (Start ▶ · Screen · Decision ◇ · System · NG · Terminal, mui ten that,
                     Edge/Exceptional) + frame ④ Screen Index / ⑦ cua site
  CR Change Table  = THONG KE (khong liet ke chi tiet): so doi tuong NEW/UPD/DEL/IMPACT theo Man hinh / API /
                     Bang DB / ... + 実装 MD + 総工数 人日 + 人月 (cung cong thuc Summary / Estimation)
  CR-3 Screens     = man de xuat dung token + component Design System cua baseline (doc tokens.json; component
                     site chua co -> block bat buoc khai "from": "<WEB-xx>" muon site khac, khong tu che)
Moi node mang dung 1 badge: ten "<BADGE> · <REF> · <nhan>", sharedPluginData("crkit","kind",...).

Bat buoc non-happy (feedback CR-001 r2 — chuan requirement-to-flow Output 1/2/3):
  CR-1: moi lane co >= 1 node type "ng" (loi da chot, noi bang canh "ng" tu decision) — hoac "no_ng": "<ly do>".
  CR-2: moi group co >= 1 node "ng" / "popup" (man / popup loi: display Modal|Popup|Toast|Banner|Full screen|Inline,
        msg, trigger, next) — hoac "no_ng"; node "screen" phai co "stype" (List|Detail|Form|Modal|Popup|Toast|Banner|
        Wizard|Dashboard|Complete|Full screen) + "desc". Ve ④ Screen Index (# · Ref · Man hinh · Loai · Mo ta · Site ·
        Badge, ke ca popup) + ⑦ Error / Popup Index + dong TONG = A man chinh + B man loi/popup.
  CR-3: moi man = 1 hang: MOCKUP BEN TRAI + MO TA BEN PHAI (Muc dich · Vao tu · Happy logic · bang ITEMS
        (# · Item · Mo ta · Action/Behavior · Thay doi) · bang ERROR SCENARIOS (# · Trigger · Hien thi · Message +
        Action)). Man UPD = ve man AS-IS + to vien mau badge len block thay doi ("chg": NEW|UPD|DEL, "n": so item).
        Popup / man loi = item "shell": "modal".

Schema cr-figma.json:
{"title": "...",
 "flows": [{"lane": "FL-08" | "CR-NEW-1", "title": "...", "nodes": [{"key","type": actor|start|step|decision|ng|
            end|edge, "pos": 1..6 (cot trai -> phai), "row": 0 happy | >=1 non-happy, "result": ok|fail (end),
            "badge", "ref" (SC- / F- / FL- / IMP- — khong API- / EXT- / table: / column:), "label", "sub"}],
            "edges": [["from_key","to_key","nhan","ng|cross|"]]}],
 "tech": [{"badge","ref","label","sub"}],
 "screen_groups": [{"id": "G1", "title": "...", "site": "WEB-02", "nodes": [{"key","type": start|screen|decision|
            system|ng|terminal|edge, "badge","ref","label","sub"}], "edges": [["a","b","nhan","ng|"]]}],
 "screens": {"ds_read": ["outputs/<baseline>/06_Design_System/WEB-02/project/README.md", ...],
             "items": [{"badge","ref","site","shell": public|mypage|admin|auth|modal|mobile (mobile: + viewport_width, viewport_note khi DS chua co token viewport-mobile), "title","label","nav_active",
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
UC_TYPES = ["actor", "start", "step", "decision", "ng", "end", "edge"]
UC_MAXPOS = 6
TECH_REF = re.compile(r"^(API-|EXT-|table:|column:|DS)")
SCREEN_TYPES = ["start", "screen", "decision", "system", "ng", "popup", "terminal", "edge"]
STYPES = ["List", "Detail", "Form", "Modal", "Popup", "Toast", "Banner", "Wizard", "Dashboard", "Complete", "Full screen"]
DISPLAYS = ["Modal", "Popup", "Toast", "Banner", "Full screen", "Inline", "Tooltip", "Empty state"]
CHG = ["NEW", "UPD", "DEL", "AS-IS"]
MAX_JS = 45000

# block -> component DS can co (None = ve tu token, khong can component)
BLOCK_COMP = {"field": "TextField", "field2": "TextField", "select": "Select", "radio": "Radio",
              "checkbox": "Checkbox", "buttons": "Button", "table": "Table", "badge": "Badge",
              "card": "Card", "modal": "Modal", "search": "Card", "pagination": "Pagination",
              "title": "PageHeader", "breadcrumb": "Breadcrumb", "section": None, "text": None, "steps": None}
SHELL_COMP = {"public": ["AppHeader"], "mypage": ["AppHeader", "SideNav"], "admin": ["SideNav"], "auth": [], "modal": [], "mobile": []}
# mobile: DS chi do o viewport-web -> khung SP khai viewport_width + viewport_note (nguon / quyet dinh), header thu gon
# auth: WEB-02 = AppHeader dang chua dang nhap; WEB-01 = card giua page-bg (man dang nhap admin khong co header)


def load_tokens(bdir, site):
    p = os.path.join(bdir, "06_Design_System", site, "project", "tokens.json")
    if not os.path.isfile(p):
        p = os.path.join(bdir, "06_Design_System", "project", "tokens.json")
    t = C.load_json(p)
    themes = [th.get("id") for th in (t.get("color") or {}).get("themes") or []]
    flat = {}
    for grp in ("color", "spacing", "radius", "shadow", "size"):
        for x in (t.get(grp) or {}).get("tokens") or []:
            v = x.get("value")
            if isinstance(v, dict):  # gia tri theo theme -> theme dau tien (VD Base DS: light)
                v = v.get(themes[0]) if themes and themes[0] in v else next(iter(v.values()), None)
            flat[x["name"]] = v
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
  f.cornerRadius = (shape==="pill"||shape==="end"||shape==="actor") ? h/2 : (shape==="decision" ? 20 : 8);
  if(shape==="ng"||shape==="popup"){ const bar=R(f,0,0,6,h,"#CF222E"); bar.name="ng-bar"; }
  const pre = shape==="decision" ? "◇ " : (shape==="ng" ? "NG · " : (shape==="popup" ? "⚠ "+(n.display||"Popup")+" · " : (shape==="pill" ? "▶ " : shape==="actor" ? "👤 " : (shape==="end" ? (n.result==="fail" ? "✗ KẾT THÚC · " : "✓ KẾT THÚC · ") : ""))));
  const t1=T(f, `${n.badge} · ${n.ref}`, 10, 6, w-20, 10, 700, b.s);
  const t2=T(f, pre+n.label+(n.badge==="DEL"?" (bỏ)":""), 10, t1.y+t1.height+2, w-20, 12, 700, "#1F2328");
  if(n.badge==="DEL") t2.textDecoration="STRIKETHROUGH";
  let bottomY = t2.y+t2.height;
  if(n.sub){ const t3=T(f, n.sub, 10, t2.y+t2.height+2, w-20, 10, 400, "#57606A"); bottomY = t3.y+t3.height; }
  if (bottomY+8 > h) { f.resize(w, bottomY+8); const bar=f.findOne(c=>c.name==="ng-bar"); if(bar) bar.resize(6, bottomY+8); }
  f.setSharedPluginData(NS,"kind",kind); f.setSharedPluginData(NS,"shape",shape||"box");
  if (n._grp) f.setSharedPluginData(NS,"grp",n._grp); return f; }
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
if (old && !D.redraw) return {error: "section da ton tai — xoa section cu (cua chinh lan chay nay) hoac doi ten truoc khi ve lai (hoac --redraw cr1,cr2)"};
const created=[];
let s = old;
if (!s) {
s = figma.createSection(); s.name = SECTION_NAME; s.x = %d; s.y = %d; page.appendChild(s);
T(s, SECTION_NAME, 40, 30, 2200, 32, 700);
T(s, D.subtitle, 40, 80, 2200, 14, 400, "#57606A");
// Legend
const lg = F(s, "LEGEND · badge", 40, 120, 1180, 64, "#FFFFFF"); lg.strokes=[paint("#D0D7DE")]; lg.cornerRadius=8;
lg.setSharedPluginData(NS,"kind","legend");
let lx=16; for (const [b,txt] of [["NEW","Tạo mới"],["UPD","Sửa cái đang có"],["DEL","Bỏ"],["IMPACT","Không sửa — bị kéo theo, kiểm lại"],["AS-IS","Giữ nguyên, ngữ cảnh"]]) {
  const sw=F(lg,"sw-"+b,lx,18,28,28,BADGE[b].f); sw.strokes=[paint(BADGE[b].s)]; sw.strokeWeight=2; if(BADGE[b].d) sw.dashPattern=[4,3]; if(BADGE[b].o) sw.opacity=BADGE[b].o; sw.cornerRadius=6;
  T(lg, b+" — "+txt, lx+36, 22, null, 12, 700, BADGE[b].s); lx += 36 + (b==="IMPACT"?300:180); }
T(lg, "NG / ⚠ popup lỗi = vạch đỏ bên trái · ◇ = rẽ nhánh · ▶ = điểm vào", lx, 22, null, 12, 500, "#CF222E");
}
if (D.only_cr2) return {section: s.id, created: 0, skipped: "CR-1"};
// CR-1 Flow — dang USE CASE: 1 lane = 1 use case (Actor → duong di happy → ket thuc; non-happy hang duoi)
const fr = F(s, "CR-1 Flow — use case bị CR chạm (format Output 1)", 40, 220, 2280, 400, "#FFFFFF");
fr.strokes=[paint("#D0D7DE")]; fr.cornerRadius=12;
T(fr, "CR-1 — Use case thay đổi (Output 1 · mỗi lane = 1 use case: Actor → đường đi → kết thúc · non-happy ở hàng dưới) + TECHNOLOGY bên phải", 40, 24, 1700, 22, 700);
T(fr, D.flow_note, 40, 54, 1700, 12, 400, "#57606A");
const X0 = 230, DXP = 250, NWP = 210, RH = 112;
T(fr, "ACTOR", 42, 90, null, 12, 700, "#57606A");
T(fr, "ĐƯỜNG ĐI — HAPPY CASE (trái → phải) → ✓ KẾT THÚC  ·  hàng dưới: NON-HAPPY CASE → ✗ KẾT THÚC", X0, 90, 1500, 12, 700, "#57606A");
R(fr, 40, 109, 1730, 2, "#1F2328");
let y = 130;
for (const L of D.flows) {
  T(fr, L.lane + " · " + L.title, 40, y, 1700, 16, 700, "#0969DA");
  T(fr, L.note + (L.no_ng ? "   ·   Non-happy: N/A — " + L.no_ng : ""), 40, y+22, 1700, 12, 400, L.no_ng ? "#CF222E" : "#57606A");
  const top = y + 56; const nodes = {}; let maxRow = 0;
  for (const n of L.nodes) { if (n.type==="edge") continue; n._grp = L.lane;
    const row = n.row || 0; maxRow = Math.max(maxRow, row);
    let f;
    if (n.type === "actor") f = badgeBox(fr, n, 40, top, 160, 84, "flow", "actor");
    else f = badgeBox(fr, n, X0 + (n.pos-1)*DXP, top + row*RH, NWP, 84, "flow",
      n.type==="decision" ? "decision" : (n.type==="ng" ? "ng" : (n.type==="end" ? "end" : (n.type==="start" ? "pill" : null))));
    if (n.type==="end") { f.strokeWeight = 3; if (n.result==="fail") f.strokes=[paint("#CF222E")]; }
    nodes[n.key] = f; created.push(f.id);
  }
  for (let r=1; r<=maxRow; r++) { const t=T(fr, "Non-happy", 40, top + r*RH + 34, 160, 11, 700, "#CF222E"); t.name="row-label"; }
  for (const [a,b,lab,st] of L.edges) if (nodes[a] && nodes[b]) created.push(arrow(fr, nodes[a], nodes[b], lab, st).id);
  let lb = 0; for (const k in nodes) lb = Math.max(lb, nodes[k].y + nodes[k].height);
  const ex = L.nodes.filter(n=>n.type==="edge");
  if (ex.length) { const ey = lb + 46; T(fr, "CHƯA CHỐT (To verify) — không vẽ vào đường đi", X0, ey - 20, 600, 11, 700, "#6639BA");
    ex.forEach((n,i)=>{ n._grp = L.lane; const f = badgeBox(fr, n, X0 + i*(NWP+40)*1.5, ey, NWP*1.5, 64, "edge"); created.push(f.id); lb = Math.max(lb, f.y+f.height); }); }
  y = lb + 50;
  R(fr, 40, y, 1730, 1, "#D0D7DE"); y += 50;
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
                        "tech": view.get("tech") or [], "redraw": bool(view.get("_redraw")),
                        "only_cr2": "cr1" not in (view.get("_redraw") or ["cr1"])}), view["_x"], view["_y"])


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


def site_order(view):
    """Thu tu site: view.site_order, roi theo lan xuat hien (screen_groups -> screens.items)."""
    out = list(view.get("site_order") or [])
    for g in view.get("screen_groups") or []:
        if g.get("site") and g["site"] not in out:
            out.append(g["site"])
    for it in ((view.get("screens") or {}).get("items") or []):
        if it.get("site") and it["site"] not in out:
            out.append(it["site"])
    return out


def site_label(view, site):
    return "%s (%s)" % ((view.get("site_labels") or {}).get(site) or "Site", site)


def part_screen_flow(view):
    """CR-2: moi site 1 Section rieng (CR-2 Screen Flow · <site>) — trong do: Group (= flow nghiep vu) -> man, + ④ / ⑦ cua site."""
    sites = []
    for st in site_order(view):
        gs = [g for g in view["screen_groups"] if g.get("site") == st]
        if not gs:
            continue
        groups, index, errs, seen = [], [], [], set()
        for g in gs:
            pos = layout_group(g)
            groups.append({**g, "pos": {k: list(v) for k, v in pos.items()}})
            for n in g["nodes"]:
                is_scr = n["type"] == "screen" or (n["type"] in ("popup", "ng") and n.get("display") in ("Modal", "Popup", "Toast", "Banner", "Full screen"))
                if is_scr and n["badge"] != "AS-IS" and (n["ref"], n["label"]) not in seen:
                    seen.add((n["ref"], n["label"]))
                    index.append([n["ref"], n["label"], n.get("stype") or n.get("display") or "Popup",
                                  n.get("desc") or n.get("msg") or "", st, n["badge"]])
                if n["type"] in ("ng", "popup"):
                    errs.append(["E-%02d" % (len(errs) + 1), n.get("parent") or "", n.get("display") or "Inline",
                                 n.get("trigger") or n["label"], n.get("msg") or n.get("sub") or "", n.get("next") or "",
                                 n["badge"], n["ref"]])
        main = sum(1 for r in index if r[2] not in ("Modal", "Popup", "Toast", "Banner", "Full screen"))
        sites.append({"site": st, "label": site_label(view, st), "groups": groups, "index": index, "errs": errs, "main": main})
    body = r"""
const D = %s;
const {page, s} = await section();
if (!s) return {error: "chua co section — chay 01 truoc"};
const created=[], frames=[];
const NW=230, NH=86, DX=280, DY=128;
for (const SD of D.sites) {
const y0 = bottom(s) + 120;
const sec = figma.createSection(); sec.name = "CR-2 Screen Flow · " + SD.label; s.appendChild(sec); sec.x = 40; sec.y = y0; sec.fills=[paint("#FFFFFF")];
sec.setSharedPluginData(NS,"kind","cr2-site"); sec.setSharedPluginData(NS,"site",SD.site);
T(sec, "CR-2 — Screen Flow · " + SD.label + " (site → flow / use case → section · Start ▶ · Screen · ◇ Decision · System · NG inline · ⚠ Popup / màn lỗi · Terminal · Edge/Exceptional)", 40, 30, 2600, 22, 700);
T(sec, D.note, 40, 62, 2600, 12, 400, "#57606A");
let sy = 110, maxW = 0;
for (const G of SD.groups) {
  // site -> flow / use case -> section: moi Group 1 Section con
  const gs = figma.createSection(); gs.name = "Flow " + G.id + " — " + G.title; sec.appendChild(gs); gs.x = 40; gs.y = sy; gs.fills=[paint("#F6F8FA")];
  gs.setSharedPluginData(NS,"kind","cr2-flow"); gs.setSharedPluginData(NS,"flow",G.id); gs.setSharedPluginData(NS,"site",SD.site);
  const fr = F(gs, "CR-2 Flow " + G.id + " — " + G.title, 40, 40, 2400, 400, "#FFFFFF");
  fr.strokes=[paint("#D0D7DE")]; fr.cornerRadius=12;
  let y = 24;
  T(fr, "Flow " + G.id + " — " + G.title, 40, y, 2200, 16, 700, "#0969DA");
  T(fr, (G.note||"") + (G.no_ng ? "   ·   Non-happy: N/A — " + G.no_ng : ""), 40, y+22, 2200, 12, 400, G.no_ng ? "#CF222E" : "#57606A");
  const top = y + 56; const nodes={}; let maxD=0, maxI=0;
  for (const n of G.nodes) { if (n.type==="edge") continue; n._grp = G.id;
    const [d,i] = G.pos[n.key]; maxD=Math.max(maxD,d); maxI=Math.max(maxI,i);
    const shape = n.type==="start" ? "pill" : (n.type==="decision" ? "decision" : (n.type==="ng" ? "ng" : (n.type==="popup" ? "popup" : null)));
    const w = n.type==="start" ? 200 : (n.type==="decision" ? 190 : NW), h = n.type==="decision" ? 64 : NH;
    const nn = (n.type==="screen" && n.stype) ? {...n, sub: "[" + n.stype + "] " + (n.desc || n.sub || "")} : ((n.type==="popup"||n.type==="ng") && n.msg ? {...n, sub: "「" + n.msg + "」" + (n.next ? " → " + n.next : "")} : n);
    const f = badgeBox(fr, nn, 40 + d*DX, top + i*DY, w, h, n.type==="screen"||n.type==="system"||n.type==="popup" ? "screen" : "flow-step", shape);
    if (n.type==="system") { f.fills=[paint("#E8F7EC")]; }
    nodes[n.key]=f; created.push(f.id); }
  for (const [a,b,lab,st] of G.edges) if (nodes[a] && nodes[b]) created.push(arrow(fr, nodes[a], nodes[b], lab, st).id);
  const ex = G.nodes.filter(n=>n.type==="edge");
  const px = 40 + (maxD+1)*DX + 40;
  if (ex.length) { T(fr, "EDGE / EXCEPTIONAL — chưa chốt, không vẽ inline", px, top-20, 420, 11, 700, "#6639BA");
    let ey = top; ex.forEach((n)=>{ n._grp = G.id; const f=badgeBox(fr, n, px, ey, 420, 74, "edge"); created.push(f.id); nodes["_e"+ey]=f; ey = f.y + f.height + 12; }); }
  let gb = top, gr = 0; for (const c of fr.children) { gb = Math.max(gb, c.y + c.height); gr = Math.max(gr, c.x + c.width); }
  fr.resize(Math.max(1200, gr + 40), gb + 40);
  gs.resizeWithoutConstraints(fr.width + 80, fr.height + 80);
  maxW = Math.max(maxW, gs.width); sy = gs.y + gs.height + 60;
}
// ④ / ⑦ cua site — frame rieng ben phai cac section flow
const IW = 980, ix0 = 40 + maxW + 60;
const fr = F(sec, "CR-2 Index — " + SD.label, ix0, 110, IW + 80, 400, "#FFFFFF"); fr.strokes=[paint("#D0D7DE")]; fr.cornerRadius=12;
const ix = 40;
T(fr, "④ SCREEN INDEX — " + SD.label + " (gồm cả popup / màn lỗi)", ix, 24, IW, 14, 700, "#0969DA");
const st = T(fr, "TỔNG = " + SD.main + " màn chính + " + (SD.index.length - SD.main) + " popup / màn lỗi = " + SD.index.length, ix, 46, IW, 12, 700, "#1F2328"); st.name = "IDX-TOTAL";
st.setSharedPluginData(NS,"kind","idx-total"); st.setSharedPluginData(NS,"value",String(SD.index.length));
let iy = 70;
const IC = [["#",28],["Ref",90],["Màn hình",230],["Loại",80],["Mô tả chức năng màn hình",370],["Site",62],["Badge",90]];
function hdrRow(cols, yy, fill){ const h=F(fr,"idx-header",ix,yy,IW,28,fill); let x=6; for(const [c,w] of cols){ T(h,c,x,7,w-6,11,700); x+=w; } return 28; }
iy += hdrRow(IC, iy, "#DAEEF3");
SD.index.forEach((r,k)=>{ const [ref,lab,typ,desc,site,b]=r; const vals=[String(k+1),ref,lab,typ,desc,site,b];
  const row=F(fr,"IDX · "+ref+" · "+typ, ix, iy, IW, 30, typ==="Modal"||typ==="Popup"||typ==="Toast"||typ==="Banner"||typ==="Full screen" ? "#FFF6F5" : BADGE[b].f);
  row.setSharedPluginData(NS,"kind","idx"); row.setSharedPluginData(NS,"type",typ); row.setSharedPluginData(NS,"ref",ref);
  let x=6, hmax=30; vals.forEach((v,c)=>{ const t=T(row,v,x,7,IC[c][1]-8,10,c===1||c===6||c===3?700:400, c===1||c===6?BADGE[b].s:(c===3&&row.fills[0].color.r>0.99?"#CF222E":"#1F2328")); hmax=Math.max(hmax,t.height+14); x+=IC[c][1]; });
  row.resize(IW,hmax); iy+=hmax; });
iy += 40;
T(fr, "⑦ ERROR / POPUP INDEX — " + SD.label + " (message thật hoặc đề xuất)", ix, iy, IW, 14, 700, "#CF222E"); iy += 26;
const EC = [["E-ID",50],["Màn cha",90],["Hiển thị",80],["Trigger",210],["Message",330],["Đi đâu sau đó",150],["Badge",70]];
iy += hdrRow(EC, iy, "#FFE3E3");
for (const e of SD.errs) { const [eid,par,disp,trg,msg,nxt,b,ref]=e; const vals=[eid,par,disp,trg,msg,nxt,b];
  const row=F(fr,"ERRIDX · "+eid+" · "+ref, ix, iy, IW, 30, "#FFFBFB"); row.strokes=[paint("#FFD7D5")];
  row.setSharedPluginData(NS,"kind","erridx");
  let x=6, hmax=30; vals.forEach((v,c)=>{ const t=T(row,v||"—",x,7,EC[c][1]-8,10,c===0||c===2?700:400, c===0?"#CF222E":"#1F2328"); hmax=Math.max(hmax,t.height+14); x+=EC[c][1]; });
  row.resize(IW,hmax); iy+=hmax; }
fr.resize(IW + 80, iy + 30);
sec.resizeWithoutConstraints(fr.x + fr.width + 80, Math.max(sy, fr.y + fr.height + 60));
frames.push(sec.id);
}
fit(s);
return {sections: frames, created: created.length};
"""
    return body % esc({"note": view["screen_note"], "sites": sites})


# ---------------------------------------------------------------- 03: CR Change Table (thong ke)
def part_change_table(stats, totals, cr_id, extra_note=""):
    body = r"""
const D = %s;
const {page, s} = await section();
if (!s) return {error: "chua co section"};
const y0 = bottom(s) + 120;
const fr = F(s, "CR Change Table — thống kê thay đổi", 40, y0, 1180, 200, "#FFFFFF");
fr.strokes=[paint("#D0D7DE")]; fr.cornerRadius=12;
T(fr, "CR Change Table — thống kê (chi tiết từng hạng mục: " + D.xlsx + ")", 32, 24, 1100, 20, 700);
const nt = T(fr, D.note, 32, 54, 1100, 12, 400, "#57606A");
const cols = [["Đối tượng",300],["NEW",110],["UPD",110],["DEL",110],["IMPACT",110],["Tổng",110],["実装 MD",160]];
const fills = {NEW:"#EDFDF0",UPD:"#FFF9EB",DEL:"#FFF6F5",IMPACT:"#FBEEFF"};
let y = Math.max(90, nt.y + nt.height + 14), x = 32;
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
                               "総工数 = 実装 × hệ số công đoạn của template Estimation." + (" " + extra_note if extra_note else ""), "rows": rows,
                       "totals": totals, "xlsx": "%s_Impact.xlsx" % cr_id})


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


def part_screens(items, toks_by_site, offset_y_first, note, labels):
    body = r"""
const D = %s;
const {page, s} = await section();
if (!s) return {error: "chua co section"};
// CR-3: 1 Section / site (nen #9DA5AD) -> trong do 1 Section / flow nghiep vu -> danh sach man (mockup trai · mo ta phai)
const BG3 = "#9DA5AD";
function siteHost(site){ let h = s.children.find(c=>c.type==="SECTION" && c.getSharedPluginData(NS,"kind")==="cr3-site" && c.getSharedPluginData(NS,"site")===site); if (h) return h;
  h = figma.createSection(); h.name = "CR-3 Screens · " + D.labels[site]; s.appendChild(h); h.x = 40; h.y = bottom(s) + 120; h.fills=[paint(BG3)];
  h.setSharedPluginData(NS,"kind","cr3-site"); h.setSharedPluginData(NS,"site",site);
  T(h, "CR-3 — " + D.labels[site] + " · chia theo flow nghiệp vụ → danh sách màn (format Output 3: mockup trái · mô tả + ITEMS + ERROR SCENARIOS phải · màn UPD tô màu phần đổi)", 40, 30, 3000, 22, 700, "#1F2328");
  T(h, D.note, 40, 66, 3000, 12, 400, "#1F2328"); return h; }
function hostFor(it){ const sh = siteHost(it.site); touched.add(sh);
  let h = sh.children.find(c=>c.type==="SECTION" && c.getSharedPluginData(NS,"flow")===it.flow); if (h) return h;
  h = figma.createSection(); h.name = "Flow " + it.flow + " — " + it.flow_title; sh.appendChild(h); h.x = 40; h.y = bottom(sh) + 80; h.fills=[];
  h.setSharedPluginData(NS,"kind","cr3-flow"); h.setSharedPluginData(NS,"flow",it.flow); h.setSharedPluginData(NS,"site",it.site);
  T(h, "Flow " + it.flow + " — " + it.flow_title, 40, 30, 3000, 20, 700, "#1F2328"); return h; }
let host = null; const touched = new Set(), flowsTouched = new Set();
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
const CHGC = {NEW:["#1A7F37","#EDFDF0"], UPD:["#F4860C","#FFF9EB"], DEL:["#CF222E","#FFF6F5"], "AS-IS":["#57606A",null]};
const CIRC = "⓪①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳";
function ann(parent, b, w){   // lop chu thich (khong phai UI): vien + nhan badge thay doi / so item
  if (!b.chg && !b.n) return [parent, w];
  const c = CHGC[b.chg||"AS-IS"]; const f=figma.createAutoLayout("VERTICAL",{itemSpacing:4});
  f.name = "CHG-ANN · " + (b.chg||"AS-IS") + " · " + (b.n||""); parent.appendChild(f);
  f.fills = c[1] ? [{...paint(c[1]), opacity:0.55}] : []; f.paddingLeft=f.paddingRight=8; f.paddingTop=f.paddingBottom=6; f.cornerRadius=6;
  if (b.chg && b.chg!=="AS-IS") { f.strokes=[paint(c[0])]; f.strokeWeight=2; f.dashPattern=[6,4]; }
  f.layoutSizingHorizontal="FIXED"; f.resize(w, f.height);
  const lab = T(f, (b.n ? (CIRC[b.n]||("("+b.n+")"))+" " : "") + (b.chg && b.chg!=="AS-IS" ? b.chg + (b.note ? " — " + b.note : "") : ""), 0, 0, null, 11, 700, c[0]);
  lab.name = "chg-label";
  return [f, w-16]; }
function blocks(parent, site, list, w){
  for (const b0 of list) { const [parent2, w2] = ann(parent, b0, w); const b = b0;
    if (parent2 !== parent) { blocks1(parent2, site, b, w2); continue; } blocks1(parent, site, b, w); } }
function blocks1(parent, site, b, w){
  {
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
    else if (b.t==="card") { const c=card(parent, b._site, w, b.tone); if(b.title) txt(c,b._site,b.title,"heading-20-bold","text-high", w-80);
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
  else if (item.shell==="modal") { // popup / man loi: nen mo + Modal giua
     const body=row(fr,0,"backdrop"); body.layoutSizingHorizontal="FILL"; body.primaryAxisAlignItems="CENTER"; body.paddingTop=body.paddingBottom=90;
     body.fills=[paint(tok(item.scrim_site||site, item.scrim||"page-bg"))];
     const main=col(body,0,"content"); main.layoutSizingHorizontal="FIXED"; main.resize(700, main.height); main.counterAxisAlignItems="CENTER";
     blocks(main, site, item.blocks, 680); }
  else if (item.shell==="auth" && site==="WEB-01") { // man dang nhap admin: khong sidebar, khong header — card giua page-bg
     const body=row(fr,0,"body"); body.layoutSizingHorizontal="FILL"; body.primaryAxisAlignItems="CENTER"; body.paddingTop=body.paddingBottom=120;
     const main=col(body,24,"content"); main.layoutSizingHorizontal="FIXED"; main.resize(560, main.height);
     blocks(main, site, item.blocks, 560); }
  else if (item.shell==="mobile") { // man SP: header thu gon + noi dung 1 cot (rong theo token viewport-mobile hoac viewport_width da khai)
     const MW=parseFloat(tok(site,"viewport-mobile", item.viewport_width)); fr.resize(MW, fr.height);
     const tb=row(fr,0,"AppHeader-SP"); tb.fills=[paint(tok(site,"surface-subtle"))]; tb.layoutSizingHorizontal="FILL"; tb.paddingLeft=tb.paddingRight=16; tb.paddingTop=tb.paddingBottom=16; tb.primaryAxisAlignItems="SPACE_BETWEEN";
     txt(tb,site,"ボーネルンド あそび場","heading-16-bold","primary-text"); txt(tb,site,"☰","heading-20-bold","primary-text");
     const main=col(fr,16,"content"); main.layoutSizingHorizontal="FILL"; main.paddingLeft=main.paddingRight=16; main.paddingTop=24; main.paddingBottom=40;
     blocks(main, site, item.blocks, MW-32);
     const ft=row(fr,0,"footer"); ft.fills=[paint(tok(site,"surface-subtle"))]; ft.layoutSizingHorizontal="FILL"; ft.paddingTop=ft.paddingBottom=16; ft.primaryAxisAlignItems="CENTER";
     txt(ft,site,"© BørneLund","text-12","text-high"); }
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
function descPanel(it, x, y){
  const PW = 1100; const p = F(host, "DESC · " + it.ref, x, y, PW, 200, "#FFFFFF"); p.strokes=[paint("#D0D7DE")]; p.cornerRadius=10;
  p.setSharedPluginData(NS,"kind","desc"); p.setSharedPluginData(NS,"ref",it.ref);
  let yy = 20; const b = BADGE[it.badge];
  T(p, `${it.badge} · ${it.ref} · ${it.label}`, 24, yy, PW-48, 18, 700, b.s); yy += 30;
  T(p, "Loại: " + it.stype + "   ·   Site: " + it.site + "   ·   Vào từ: " + (it.entry||"—") + (it.base ? "   ·   Màn AS-IS: " + it.base : ""), 24, yy, PW-48, 12, 500, "#57606A"); yy += 20;
  if (it.api_new || it.api_upd) {   // feedback: ghi so API moi / cap nhat trong phan thao tac
    T(p, "Thao tác tới server: " + (it.api_new ? it.api_new + " API tạo mới" : "") + (it.api_new && it.api_upd ? " · " : "") + (it.api_upd ? it.api_upd + " API cập nhật" : ""), 24, yy, PW-48, 12, 600, "#0969DA"); yy += 22;
  }
  const sec = (title, color) => { const t=T(p, title, 24, yy, PW-48, 13, 700, color||"#0969DA"); yy = t.y + t.height + 6; };
  const para = (s2) => { const t=T(p, s2, 24, yy, PW-48, 12, 400, "#1F2328"); yy = t.y + t.height + 12; };
  sec("■ Mục đích màn hình"); para(it.purpose);
  if (it.changes && it.changes.length) { sec("■ Thay đổi so với AS-IS (tô màu trên mockup)", "#F4860C"); para(it.changes.map(c=>"• "+c).join("\n")); }
  sec("■ Logic màn hình — Happy case"); para(it.happy.map((h,k)=>(k+1)+". "+h).join("\n"));
  function table(name, cols, rows, fillH, fillR, strokeC, kindRow){
    const t = F(p, name, 24, yy, PW-48, 30, fillR); t.strokes=[paint(strokeC)]; t.cornerRadius=8;
    let ty2 = 0; const hdr = F(t, "hdr", 0, 0, PW-48, 30, fillH); let x=8; for (const [c,w] of cols) { T(hdr,c,x,8,w-8,11,700); x+=w; } ty2 = 30;
    rows.forEach((r,k)=>{ const rr = F(t, kindRow + " · " + it.ref + " · " + (k+1), 0, ty2, PW-48, 30, (r._chg && CHGC[r._chg][1]) || fillR);
      rr.setSharedPluginData(NS,"kind",kindRow.toLowerCase()); let x2=8, hm=30;
      r.v.forEach((v,c)=>{ const tt=T(rr, String(v||"—"), x2, 8, cols[c][1]-10, 11, c===0||(r._chg&&c===cols.length-1)?700:400, (r._chg && c===cols.length-1) ? CHGC[r._chg][0] : "#1F2328"); hm=Math.max(hm, tt.height+16); x2+=cols[c][1]; });
      rr.resize(PW-48, hm); ty2 += hm; });
    t.resize(PW-48, ty2); yy = t.y + ty2 + 18; return t; }
  sec("■ Bảng ITEMS (số ① trên mockup)");
  // feedback 30/10/2026: cot "Action / Behavior" -> "Thao tác / Ảnh hưởng". Co row.impact -> append bullet
  // format giong cot Can cu Estimation: '· N API cập nhật\n· Mức ảnh hưởng: Nhỏ'. Khong co -> bo qua.
  function actionImpact(r){ return r.impact ? (r.action + "\n\n" + r.impact) : r.action; }
  table("ITEMS · " + it.ref, [["#",36],["Item",190],["Mô tả",290],["Thao tác / Ảnh hưởng",420],["Thay đổi",116]],
        it.items.map(r=>({v:[CIRC[r.n]||r.n, r.title, r.desc, actionImpact(r), r.chg||it.badge], _chg:r.chg||(it.badge==="NEW"?"NEW":null)})), "#DAEEF3", "#FFFFFF", "#D0D7DE", "ITEM");
  sec("■ ERROR SCENARIOS — nếu lỗi thì hiển thị gì", "#CF222E");
  table("ERRORS · " + it.ref, [["#",36],["Trigger (nguyên nhân)",250],["Hiển thị",110],["Message + Action tiếp theo",656]],
        it.errors.map((r,k)=>({v:[String(k+1), r.trigger, r.display, r.msg]})), "#FFE3E3", "#FFFBFB", "#CF222E", "ERR");
  if (it.cq) { sec("■ Chờ xác nhận", "#6639BA"); para(it.cq); }
  p.resize(PW, yy + 10); return p; }
for (const it of D.items) {
  host = hostFor(it); flowsTouched.add(host);
  let yStart = 80; for (const c of host.children) if (c.name.startsWith("cap ·") || c.name.startsWith("DESC ·") || /^(NEW|UPD|DEL) · /.test(c.name)) yStart = Math.max(yStart, c.y + c.height + 200);
  const x = 40;
  const cap = T(host, `${it.badge} · ${it.ref} · ${it.label}`, x, yStart, 1440, 18, 700, BADGE[it.badge].s); cap.name = "cap · " + it.ref;
  cap.fills=[paint("#FFFFFF")]; const capBg = figma.createRectangle(); host.insertChild(host.children.indexOf(cap), capBg); capBg.name="cap-bg"; capBg.resize(cap.width+16, cap.height+8); capBg.x=x-8; capBg.y=yStart-4; capBg.fills=[paint(BADGE[it.badge].s)]; capBg.cornerRadius=6;
  const note = T(host, "DS: " + it.ds.join(", ") + (it.borrow.length ? "  ·  MƯỢN: " + it.borrow.join(", ") + " (chờ designer)" : "") + (it.sidebar_note ? "  ·  sidebar " + it.sidebar_width + "px: " + it.sidebar_note : "") + (it.viewport_note ? "  ·  viewport SP " + it.viewport_width + "px: " + it.viewport_note : "") + "  ·  Font Hiragino Kaku Gothic Pro → hiển thị Noto Sans JP (Figma không có font gốc)", x, yStart+28, 1440, 11, 400, "#1F2328"); note.name="cap-note";
  const fr = shell(it); host.appendChild(fr); fr.x = x; fr.y = yStart + 70;
  const b = BADGE[it.badge]; fr.strokes=[paint(b.s)]; fr.strokeWeight=4; if (b.d) fr.dashPattern=[10,6];
  fr.setSharedPluginData(NS,"kind","mockup"); fr.setSharedPluginData(NS,"ds",it.ds.join(";")); fr.setSharedPluginData(NS,"site",it.site);
  created.push(fr.id);
  const dp = descPanel(it, x + fr.width + 60, yStart + 70);
}
function fitSec(h, minW){ let hh=0, ww=0; for (const c of h.children){ hh=Math.max(hh,c.y+c.height); ww=Math.max(ww,c.x+c.width);} h.resizeWithoutConstraints(Math.max(minW,ww+60), hh+60); }
function stack(list, gap){ list.sort((a,b)=>a.y-b.y); for (let i=1;i<list.length;i++) if (list[i].y < list[i-1].y + list[i-1].height + gap) list[i].y = list[i-1].y + list[i-1].height + gap; }
for (const f of flowsTouched) fitSec(f, 3040);
for (const h of touched) { stack(h.children.filter(c=>c.type==="SECTION"), 80); fitSec(h, 3120); }
// section CR-3 lon len -> day section ben duoi xuong, khong chong nhau
stack(s.children.filter(c=>c.type==="SECTION" && c.getSharedPluginData(NS,"kind")==="cr3-site"), 120);
fit(s);
return {hosts: [...touched].map(h=>h.id), created};
"""
    need = set()
    for it in items:
        need.add(it["site"])
        need |= {r.split(":")[1] for r in it.get("ds") or [] if r.count(":") >= 2}
    used_tok = {st: {"t": {k: v for k, v in toks_by_site[st]["t"].items() if not str(k).startswith("obs-")},
                     "type": toks_by_site[st]["type"]} for st in need if st in toks_by_site}
    return body % esc({"note": note, "items": items, "tok": used_tok, "labels": labels})


CLEAR = r"""
const WHAT = %s;
const {page, s} = await section();
if (!s) return {error: "chua co section"};
const old = s.children.filter(c => (WHAT.includes("cr1") && c.name.startsWith("CR-1 Flow")) ||
  (WHAT.includes("cr2") && c.type==="SECTION" && c.getSharedPluginData(NS,"kind")==="cr2-site"));
if (!old.length) return {cleared: 0};
let maxX = 0; for (const c of page.children) maxX = Math.max(maxX, c.x + c.width);
const ar = figma.createSection(); ar.name = SECTION_NAME + " — LƯU TRỮ bản cũ " + WHAT.join("/").toUpperCase() + " (trước khi vẽ lại)";
page.appendChild(ar); ar.x = maxX + 400; ar.y = s.y; ar.fills=[paint("#FFFFFF")];
let yy = 80; T(ar, ar.name, 40, 24, 3000, 24, 700, "#57606A");
for (const c of old) { const k = c.clone(); ar.appendChild(k); k.x = 40; k.y = yy; yy += k.height + 120;
  for (const x of [k, ...("findAll" in k ? k.findAll(() => true) : [])]) { try { x.setSharedPluginData(NS,"kind",""); } catch(e) {} } }
fit(ar);
const ids = old.map(c => c.id); for (const c of old) c.remove();
return {archive: ar.id, cleared: ids};
"""

RESTACK = r"""
const {page, s} = await section();
if (!s) return {error: "chua co section"};
const k = c => c.type==="SECTION" ? (c.getSharedPluginData(NS,"kind")||"") : "";
const rank = c => c.name.startsWith("CR-1 Flow") ? 1 : (k(c)==="cr2-site" ? 2 : (c.name.startsWith("CR Change Table") ? 3 : (k(c)==="cr3-site" ? 4 : 5)));
const body = s.children.filter(c => c.y >= 200 && (c.type==="FRAME" || c.type==="SECTION"));
body.sort((a,b) => rank(a)-rank(b) || a.y-b.y);
let y = 220; for (const c of body) { c.x = 40; c.y = y; y += c.height + 120; }
fit(s);
const sb = s.absoluteBoundingBox;
const overlap = page.children.filter(c => c.id!==s.id).map(c => ({id:c.id, name:c.name, ...c.absoluteBoundingBox}))
  .filter(b => !(b.x+b.width<=sb.x||sb.x+sb.width<=b.x||b.y+b.height<=sb.y||sb.y+sb.height<=b.y));
return {order: body.map(c => c.name.slice(0,50)), section: {x:sb.x, y:sb.y, w:sb.width, h:sb.height}, overlap};
"""


READBACK = r"""
// Use_figma gioi han ket qua 20 KB -> chay nhieu lan: PART = 0 (meta: arrows/stats/idx/desc...), 1..N (nodes, 50 node / phan).
// Ghep: python3 verify-cr-figma.py --nodes part0.json,part1.json,...  (hoac tu ghep thanh 1 file {nodes:[...], ...}).
const PART = 0, PAGE = 50;
const page = await figma.getNodeByIdAsync(PAGE_ID); await figma.setCurrentPageAsync(page);
const s = page.children.find(c=>c.type==="SECTION" && c.name===SECTION_NAME);
if (!s) return {error:"khong thay section"};
// CR-3 co the dat ngoai section CR (canh Output 1 / 2) — section site mang plugin data crkit.cr = ten section CR
const hosts = [s, ...page.children.filter(c => c.type==="SECTION" && c.getSharedPluginData("crkit","cr")===SECTION_NAME)];
const FA = f => hosts.flatMap(h => (f(h) ? [h] : []).concat(h.findAll(f)));
const rx = /^(NEW|UPD|DEL|IMPACT|AS-IS) · ([^·]+?) · /;
const hex = c => "#"+[c.r,c.g,c.b].map(v=>Math.round(v*255).toString(16).padStart(2,"0")).join("");
const all = FA(n => rx.test(n.name));
if (PART > 0) {
  const nodes = all.slice((PART-1)*PAGE, PART*PAGE).map(n => { const m = n.name.match(rx); const kind = n.getSharedPluginData("crkit","kind")||"other";
    const o = {id:n.id, name:n.name.slice(0,48), badge:m[1], ref:m[2].trim(), kind};
    const sh = n.getSharedPluginData("crkit","shape"), g = n.getSharedPluginData("crkit","grp"); if (sh) o.shape = sh; if (g) o.grp = g;
    if (kind==="mockup") { o.ds = n.getSharedPluginData("crkit","ds"); o.site = n.getSharedPluginData("crkit","site"); const src = n.getSharedPluginData("crkit","src"); if (src) o.src = src;
      // chi bo chinh khung CHG-ANN / chg-label (mau badge), KHONG bo noi dung ben trong khung
      const cols = new Set(); for (const d of n.findAll(x => "fills" in x && Array.isArray(x.fills))) { if (d.name && (d.name.startsWith("CHG-ANN") || d.name==="chg-label")) continue; for (const p of d.fills) if (p.type==="SOLID") cols.add(hex(p.color)); }
      o.colors = [...cols];
      o.chg = [...new Set(n.findAll(x => x.name && x.name.startsWith("CHG-ANN · ")).map(x => x.name.split(" · ")[1]))]; }
    return o; });
  return {part: PART, of: Math.ceil(all.length/PAGE), nodes};
}
const arrows = FA(n => n.name.startsWith("ARROW · ")).map(n => ({id:n.id, from:n.getSharedPluginData("crkit","from"), to:n.getSharedPluginData("crkit","to")}));
const stats = FA(n => n.name.startsWith("STAT · ")).map(n => ({name:n.name, value:n.getSharedPluginData("crkit","value")}));
const legend = FA(n => n.name.startsWith("LEGEND")).length;
const idx = FA(n => n.name.startsWith("IDX · ")).map(n => ({ref:n.getSharedPluginData("crkit","ref"), type:n.getSharedPluginData("crkit","type")}));
const idxTotal = FA(n => n.name==="IDX-TOTAL").map(n => n.characters);
const erridx = FA(n => n.name.startsWith("ERRIDX · ")).length;
const desc = FA(n => n.name.startsWith("DESC · ")).map(n => ({ref:n.getSharedPluginData("crkit","ref"),
  items:n.findAll(x=>x.name && x.name.startsWith("ITEM · ")).length, errors:n.findAll(x=>x.name && x.name.startsWith("ERR · ")).length}));
const unbadged = FA(n => n.type==="FRAME" && n.parent && n.parent.name && (n.parent.name.startsWith("CR-1") || n.parent.name.startsWith("CR-2")) && !rx.test(n.name) && !/^(IDX|idx-|ARROW|ERRIDX|CR-2 Screen Flow —|CR-2 Index —|CR-2 Flow )/.test(n.name)).map(n=>n.name).slice(0,20);
const sb = s.absoluteBoundingBox; const others = page.children.filter(c=>!hosts.includes(c)).map(c=>({name:c.name, ...c.absoluteBoundingBox}));
const overlap = others.filter(b=>!(b.x+b.width<=sb.x||sb.x+sb.width<=b.x||b.y+b.height<=sb.y||sb.y+sb.height<=b.y)).map(b=>b.name);
const kindOf = n => n.getSharedPluginData("crkit","kind");
const cr2 = FA(n => n.type==="SECTION" && kindOf(n)==="cr2-site").map(h => ({name:h.name, site:h.getSharedPluginData("crkit","site"),
  groups:[...new Set(h.findAll(x => !!x.getSharedPluginData("crkit","grp")).map(x => x.getSharedPluginData("crkit","grp")))],
  flows: h.children.filter(c => c.type==="SECTION" && kindOf(c)==="cr2-flow").map(f => ({name:f.name, flow:f.getSharedPluginData("crkit","flow"),
    groups:[...new Set(f.findAll(x => !!x.getSharedPluginData("crkit","grp")).map(x => x.getSharedPluginData("crkit","grp")))]}))}));
const cr3 = FA(n => n.type==="SECTION" && kindOf(n)==="cr3-site").map(h => ({name:h.name, site:h.getSharedPluginData("crkit","site"),
  fill: h.fills.length && h.fills[0].type==="SOLID" ? hex(h.fills[0].color) : "",
  flows: h.children.filter(c => c.type==="SECTION" && kindOf(c)==="cr3-flow").map(f => ({name:f.name, flow:f.getSharedPluginData("crkit","flow"), mockups:f.findAll(x => kindOf(x)==="mockup").length})),
  loose: h.children.filter(c => kindOf(c)==="mockup").length}));
const mockups = FA(n => kindOf(n)==="mockup").length;
return {part: 0, parts: Math.ceil(all.length/PAGE), layout:{cr2, cr3, mockups}, section:{id:s.id, name:s.name, x:sb.x, y:sb.y, w:sb.width, h:sb.height}, arrows, stats, legend, unbadged, overlap, idx, idxTotal, erridx, desc};
"""


def usecase_lane_errors(L):
    """CR-1 = Output 1 dang use case (feedback 20/10/2026): 1 lane = 1 use case — Actor → duong di happy (pos 1..6,
    row 0) → ket thuc ✓; non-happy row >= 1 (◇ → NG → ket thuc ✗). Lane khong chua technology / function."""
    errs, lane = [], L.get("lane")
    keys = {n.get("key") for n in L.get("nodes") or []}
    for n in L.get("nodes") or []:
        t = n.get("type")
        if t not in UC_TYPES:
            errs.append("flow %s node %s type=%r (%s) — lane cot TRIGGER/FUNCTION/TECHNOLOGY da bo" % (lane, n.get("key"), t, "|".join(UC_TYPES)))
            continue
        if t not in ("actor", "edge") and not (isinstance(n.get("pos"), int) and 1 <= n["pos"] <= UC_MAXPOS):
            errs.append("flow %s node %s pos=%r (1..%d)" % (lane, n.get("key"), n.get("pos"), UC_MAXPOS))
        if t != "edge" and (TECH_REF.match(C.txt(n.get("ref"))) or re.search(r"\b(API|EXT)-\d", C.txt(n.get("label")) + " " + C.txt(n.get("sub")))):
            errs.append("flow %s node %s chua technology / API (%s) — dua sang bang TECHNOLOGY, lane chi viet dieu nguoi dung lam / thay"
                        % (lane, n.get("key"), n.get("ref")))
    types = [n.get("type") for n in L.get("nodes") or []]
    if types.count("actor") != 1:
        errs.append("flow %s phai co dung 1 node actor (co %d)" % (lane, types.count("actor")))
    if "start" not in types:
        errs.append("flow %s thieu node start (diem bat dau use case)" % lane)
    if not any(n.get("type") == "end" and not n.get("row") and n.get("result") != "fail" for n in L.get("nodes") or []):
        errs.append("flow %s thieu diem ket thuc happy (type end, row 0)" % lane)
    for e in L.get("edges") or []:
        if e[0] not in keys or e[1] not in keys:
            errs.append("flow %s canh %s->%s tro toi key khong co" % (lane, e[0], e[1]))
        while len(e) < 4:
            e.append("")
    L.setdefault("note", "")
    if "ng" not in types and len(C.txt(L.get("no_ng"))) < 15:
        errs.append("flow %s thieu NON-HAPPY: can >= 1 node type 'ng' noi tu decision, hoac 'no_ng' (ly do >= 15 ky tu)" % lane)
    outs = {e[0] for e in L.get("edges") or []}
    errs += ["flow %s NG %s khong di tiep — non-happy phai co diem ket thuc (end result fail) hoac quay lai buoc" % (lane, n["key"])
             for n in L.get("nodes") or [] if n.get("type") == "ng" and n["key"] not in outs]
    linked = {e[0] for e in L.get("edges") or []} | {e[1] for e in L.get("edges") or []}
    errs += ["flow %s node %s khong co canh — Output 1 cam the roi" % (lane, n["key"])
             for n in L.get("nodes") or [] if n.get("type") != "edge" and n.get("key") not in linked]
    return errs


def unknown_text_errors(view):
    """Figma Output 1 / 2 (CR-1 / CR-2) khong hien chu cu S.LEGACY_WORD (feedback 20/10/2026 · D1): chua ro -> ghi
    "Cần xác nhận — Q-xxx" / "chưa quan sát được". Trang thai tuong ung trong xlsx / inventory = To verify."""
    errs = []
    def walk(o, where):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, "%s.%s" % (where, k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, "%s[%d]" % (where, i))
        elif S.has_legacy(o):
            errs.append("%s chua chu %s: %r — ghi 'Cần xác nhận — Q-xxx' / 'chưa quan sát được'" % (where, S.LEGACY_WORD, o[:60]))
    for k in ("title", "subtitle", "flow_note", "screen_note", "flows", "tech", "screen_groups"):
        walk(view.get(k), k)
    return errs


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
    ap.add_argument("--redraw", default=None, help="cr1,cr2 — ve lai CR-1 / CR-2 trong section da co (00-clear.js luu ban cu ra section luu tru, 98-restack.js xep lai)")
    ap.add_argument("--ds-baseline", default=None, help="version chua 06_Design_System moi nhat (mac dinh = --baseline)")
    a = ap.parse_args()
    cr = C.load_json(a.cr_json)
    view = C.load_json(a.view)
    _rm, rates = C.load_rates(a.rates)
    B = C.load_baseline(a.baseline)
    if a.ds_baseline:  # DS dung khi ve (DS moi hon, hoac Base Design System tam o version CR) thay DS cua baseline
        B["ds"] = C.load_ds_sites(os.path.join(a.ds_baseline, "06_Design_System"))
        B["has_ds"] = bool(B["ds"])
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
        for n in L["nodes"]:
            ok_ref(n, "flow %s" % L["lane"])
        errors += usecase_lane_errors(L)
    for n in view.get("tech") or []:
        ok_ref(n, "tech")
    errors += unknown_text_errors(view)
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
        if not any(n.get("type") in ("ng", "popup") for n in g["nodes"]) and len(C.txt(g.get("no_ng"))) < 15:
            errors.append("group %s thieu NON-HAPPY: can >= 1 node 'ng' / 'popup' (man / popup loi), hoac 'no_ng' (ly do)" % g["id"])
        for n in g["nodes"]:
            if n.get("type") == "screen" and n.get("badge") != "AS-IS":
                if n.get("stype") not in STYPES:
                    errors.append("group %s man %s thieu / sai 'stype' (%s) — Screen Index phai ghi Loai" % (g["id"], n.get("key"), "|".join(STYPES)))
                if not C.txt(n.get("desc")):
                    errors.append("group %s man %s thieu 'desc' (mo ta chuc nang man)" % (g["id"], n.get("key")))
            if n.get("type") in ("ng", "popup"):
                if n.get("display") not in DISPLAYS:
                    errors.append("group %s node loi %s thieu / sai 'display' (%s)" % (g["id"], n.get("key"), "|".join(DISPLAYS)))
                for f in ("msg", "trigger", "parent"):
                    if not C.txt(n.get(f)):
                        errors.append("group %s node loi %s thieu '%s'" % (g["id"], n.get("key"), f))
        linked = {e[0] for e in g["edges"]} | {e[1] for e in g["edges"]}
        errors += ["group %s node %s khong co canh — Output 2 cam the roi" % (g["id"], n["key"])
                   for n in g["nodes"] if n.get("type") != "edge" and n["key"] not in linked]
    # CR-3: token + component DS
    sites = sorted({it["site"] for it in (view.get("screens") or {}).get("items") or []})
    toks = {}
    dsb = a.ds_baseline or a.baseline
    for st in sorted(set(sites) | {s for s in B["ds"]}):
        try:
            toks[st] = load_tokens(dsb, st)
        except (OSError, ValueError) as e:
            errors.append("khong doc duoc tokens.json %s: %s" % (st, e))
    comps = {s: B["ds"][s]["comps"] for s in B["ds"]}
    scr = view.get("screens") or {}
    ds_read = scr.get("ds_read") or []
    items = scr.get("items") or []
    if items:
        for st in sites:
            need = [os.path.join("06_Design_System", st, "project", f) for f in ("README.md", "tokens.json")]
            for nd in need:
                if not any(nd in p for p in ds_read):
                    errors.append("CR-3: chua khai da doc %s (screens.ds_read) — doc Design System TRUOC khi ve" % nd)
    for it in items:
        ok_ref(it, "CR-3")
        for f in ("purpose", "stype"):
            if not C.txt(it.get(f)):
                errors.append("CR-3 %s thieu '%s' (mo ta man ben phai mockup)" % (it.get("ref"), f))
        if not it.get("happy"):
            errors.append("CR-3 %s thieu 'happy' (logic man — happy case)" % it.get("ref"))
        if not it.get("items"):
            errors.append("CR-3 %s thieu bang ITEMS" % it.get("ref"))
        if not it.get("errors"):
            errors.append("CR-3 %s thieu ERROR SCENARIOS (neu loi thi hien gi) — man that su khong loi: 1 dong ghi 'N/A — ly do'" % it.get("ref"))
        nums = set()
        def collect(bl):
            for b in bl:
                if b.get("n"):
                    nums.add(b["n"])
                if b.get("chg") and b["chg"] not in CHG:
                    errors.append("CR-3 %s block chg=%r" % (it.get("ref"), b["chg"]))
                collect(b.get("blocks") or [])
        collect(it.get("blocks") or [])
        miss = sorted({r.get("n") for r in it.get("items") or []} - nums)
        if miss:
            errors.append("CR-3 %s item %s co trong bang ITEMS nhung khong gan so 'n' tren mockup" % (it.get("ref"), miss))
        if it.get("badge") == "UPD":
            if not C.txt(it.get("base")):
                errors.append("CR-3 %s man UPD phai ghi 'base' (SC- man AS-IS goc)" % it.get("ref"))
            def has_chg(bl):
                return any(b.get("chg") in ("NEW", "UPD", "DEL") or has_chg(b.get("blocks") or []) for b in bl)
            if not has_chg(it.get("blocks") or []):
                errors.append("CR-3 %s man UPD khong co block nao danh 'chg' — phai to mau phan thay doi tren man cu" % it.get("ref"))
        if it.get("shell") == "mobile" and "viewport-mobile" not in (toks.get(it["site"]) or {}).get("t", {}):
            if not it.get("viewport_width") or not C.txt(it.get("viewport_note")):
                errors.append("%s: %s chua co token viewport-mobile — khai viewport_width + viewport_note (nguon / "
                              "quyet dinh), khong tu dat" % (it["ref"], it["site"]))
        if it.get("shell") == "mypage" and "sidebar-width" not in (toks.get(it["site"]) or {}).get("t", {}):
            if not it.get("sidebar_width") or not C.txt(it.get("sidebar_note")):
                errors.append("%s: %s chua co token sidebar-width (TBD) — khai sidebar_width + sidebar_note (nguon / "
                              "quyet dinh cua user o CR-3b), khong tu dat" % (it["ref"], it["site"]))
        it["ds"] = resolve_block_tokens(it, toks, comps, errors)
        it["borrow"] = sorted({r.split(":")[1] for r in it["ds"] if r.split(":")[1] != it["site"]})
        it.setdefault("label", it.get("title", ""))
    # CR-3 chia site -> flow nghiep vu -> man: moi man phai gan flow (id Group CR-2 / lane FL, hoac flow + flow_title)
    gtitle = {g["id"]: g.get("title", "") for g in view.get("screen_groups") or []}
    for L in view.get("flows") or []:
        gtitle.setdefault(L.get("lane"), L.get("title") or L.get("lane_title") or "")
    for it in items:
        if not C.txt(it.get("flow")):
            errors.append("CR-3 %s (%s) thieu 'flow' — gan id Group CR-2 / lane FL-xx (CR-3 chia site -> flow -> man)" % (it.get("ref"), it.get("label")))
            continue
        it["flow_title"] = it.get("flow_title") or gtitle.get(it["flow"]) or ""
        if not it["flow_title"]:
            errors.append("CR-3 %s flow %r khong co trong screen_groups / flows — khai them flow_title" % (it.get("ref"), it["flow"]))
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
    redraw = [x.strip() for x in (a.redraw or "").split(",") if x.strip()]
    if any(x not in ("cr1", "cr2") for x in redraw):
        print("--redraw chi nhan cr1,cr2", file=sys.stderr)
        return 1
    view["_redraw"] = redraw
    if redraw:
        # ve lai CR-1 / CR-2 trong section da co: luu ban cu ra section luu tru (khong mat), ve moi, xep lai thu tu
        write("00-clear.js", CLEAR % esc(redraw))
    write("01-shell-flow.js", part_shell_flow(view, ""))
    if view.get("screen_groups") and (not redraw or "cr2" in redraw):
        write("02-screen-flow.js", part_screen_flow(view))
    if redraw:
        write("98-restack.js", RESTACK)
        items = []
    else:
        write("03-change-table.js", part_change_table(stats, totals, meta["cr_id"], view.get("change_note", "")))
    note = ("Dựng từ tokens.json + component README của Design System baseline (đã đọc: %s). Dữ liệu mẫu theo "
            "DATA-PRIVACY §4. Viền khung = badge thay đổi." % ", ".join(os.path.basename(os.path.dirname(os.path.dirname(p)))
                                                                    + "/" + os.path.basename(p) for p in ds_read))
    per = max(1, a.per_file)
    order = site_order(view)
    forder = list(gtitle)
    for it in items:
        if it["flow"] not in forder:
            forder.append(it["flow"])
    # thu tu ve: site (site_order) -> flow (thu tu Group / lane) -> man
    items = sorted(items, key=lambda it: (order.index(it["site"]), forder.index(it["flow"])))
    labels = {st: site_label(view, st) for st in order}
    for k in range(0, len(items), per):
        write("04-screens-%02d.js" % (k // per + 1), part_screens(items[k:k + per], toks, 0, note, labels))
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
