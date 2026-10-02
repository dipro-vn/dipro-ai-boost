#!/usr/bin/env python3
"""Gom design token QUAN SAT DUOC (crawl styles.json + bien CSS trong source) -> tokens-draft.

  python3 extract-design-tokens.py --crawl <_internal>/recon/crawl \
          [--css-root REPO-01[@WEB-01]=/path/to/fe ...] --out <_internal>/recon/design \
          [--assets <_internal>/recon/design/assets] \
          [--emit-root <ver>/04_DesignSystem --name "<Ten DS>" [--force-mode single|themes|per-site]]
          (cu, 1 thu muc: --emit-tokens <ver>/04_DesignSystem/project/tokens.json [--emit-status [<path>]])

dsLayout (tokens-draft.json + stdout): >=2 website -> so fingerprint tung cap (font chinh, thang chu, spacing,
        radius, nut/input cao-radius-padding, nav/header) -> mode single (1 site / giong ca mau) · themes (chi khac
        mau: 1 DS, 1 theme/site) · per-site (khac ngoai mau: 1 DS / website). --force-mode = user quyet (forced:true).
--emit-root: single/themes -> <root>/project/tokens.json + <root>/STATUS.md ; per-site -> <root>/<WEB-xx>/project/
        tokens.json + <root>/<WEB-xx>/STATUS.md tu du lieu RIENG site do (theme light). Root da co layout kia -> exit 1.
        --css-root REPO-01@WEB-01 = repo chi tinh cho site do khi tach per-site (khong @ = moi site).

Input : moi */styles.json (+ pages.json: tieu de man) duoi --crawl (do crawl-site.js ghi); --css-root (lap lai
        duoc) quet .css/.scss/.sass/.less/.vue/.tsx/.jsx + tailwind.config.(js|ts|cjs) tim custom property,
        bien SCSS/LESS, mau theme tailwind, font-family (bo qua node_modules/dist/build/vendor).
Output: tokens-draft.json (colors · primaryCandidates · fonts · fontSizes · fontWeights · radii ·
        spacings · shadows · maxWidths · cssVars · pages · typeStyles · components · perSite(+observed) · contrast ·
        fontFaces · assets · viewports · dsLayout) va tokens-draft.md (bang tom tat cho nguoi doc).
--emit-tokens: tokens.json KHOI DAU dung grammar design-system-format.md: TEN VAI TRO §3.3 khi suy duoc
        (bang heuristic o emit_tokens), gia tri khong khop vai tro -> obs-<family>-NN; moi usage "TODO — ..."
        -> agent PHAI kiem vai tro + viet usage that (gate V-DS FAIL khi con obs-/TODO).
--emit-status: STATUS.md DRAFT (mac dinh <thu muc tokens>/../STATUS.md): nguon, platform, bang Thieu (TBD) =
        moi token §3.3 / component §5 chua co (khong bia gia tri de lap).
Chi ghi du lieu QUAN SAT DUOC — script khong tu dat ra token. verify-design-system.py doi chieu file nay.
Khong ghi gi vao repo duoc phan tich.
"""
import argparse
import colorsys
import datetime
import glob
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_roles as R_  # noqa: E402

SKIP_DIRS = {"node_modules", "dist", "build", "vendor", ".git", ".next", ".nuxt", "coverage", "out"}
CSS_EXT = (".css", ".scss", ".sass", ".less", ".vue", ".tsx", ".jsx")
TW_RE = re.compile(r"^tailwind\.config\.(js|ts|cjs|mjs)$")
MAX_FILE = 1024 * 1024

HEX_RE = re.compile(r"#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})\b")
RGB_RE = re.compile(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:[\s,/]+([\d.]+%?))?\s*\)")
HSL_RE = re.compile(r"hsla?\(\s*([\d.]+)(?:deg)?[\s,]+([\d.]+)%[\s,]+([\d.]+)%(?:[\s,/]+([\d.]+%?))?\s*\)")


# ---------- mau ----------
def _alpha(a):
    if a is None:
        return 1.0
    return float(a[:-1]) / 100 if a.endswith("%") else float(a)


def parse_color(s):
    """Tra ve (#RRGGBB, alpha) hoac None. Mau trong suot hoan toan -> None."""
    s = (s or "").strip()
    m = RGB_RE.search(s)
    if m:
        r, g, b = (int(round(float(x))) for x in m.group(1, 2, 3))
        hx, a = "#%02X%02X%02X" % (r, g, b), _alpha(m.group(4))
    else:
        m = HSL_RE.search(s)
        if m:
            h, sat, li = float(m.group(1)) / 360, float(m.group(2)) / 100, float(m.group(3)) / 100
            r, g, b = colorsys.hls_to_rgb(h, li, sat)
            hx, a = "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255)), _alpha(m.group(4))
        else:
            m = HEX_RE.search(s)
            if not m:
                return None
            h = m.group(1)
            if len(h) in (3, 4):
                h = "".join(c * 2 for c in h)
            hx, a = "#" + h[:6].upper(), (int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)
    if a <= 0:
        return None
    return hx, round(a, 3)


def is_neutral(hx):
    r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5))
    _, l, s = colorsys.rgb_to_hls(r, g, b)
    return s < 0.15 or l > 0.95 or l < 0.06


def first_family(stack):
    return (stack or "").split(",")[0].strip().strip("'\"")


def families(stack):
    return [f.strip().strip("'\"") for f in (stack or "").split(",") if f.strip()]


class Bag:
    """dem gia tri + vai tro + nguon"""
    def __init__(self):
        self.d = {}

    def add(self, key, n=1, role=None, source=None, extra=None):
        e = self.d.setdefault(key, {"count": 0, "roles": set(), "sources": [], "extra": {}})
        e["count"] += n
        if role:
            e["roles"].add(role)
        if source and source not in e["sources"]:
            e["sources"].append(source)
        if extra:
            for k, v in extra.items():
                e["extra"].setdefault(k, [])
                if v not in e["extra"][k]:
                    e["extra"][k].append(v)

    def rows(self, keyname):
        out = []
        for k, e in sorted(self.d.items(), key=lambda kv: (-kv[1]["count"], str(kv[0]))):
            row = {keyname: k, "count": e["count"], "roles": sorted(e["roles"]),
                   "sources": e["sources"][:12] + (["... +%d" % (len(e["sources"]) - 12)] if len(e["sources"]) > 12 else [])}
            row.update(e["extra"])
            out.append(row)
        return out


# ---------- crawl ----------
def site_of(f):
    try:
        return json.load(open(f, encoding="utf8")).get("site") or os.path.basename(os.path.dirname(f))
    except (OSError, ValueError):
        return os.path.basename(os.path.dirname(f))


def read_crawl(files, B, X, only=None):
    pages = []
    for f in files:
        data = json.load(open(f, encoding="utf8"))
        site = data.get("site") or os.path.basename(os.path.dirname(f))
        if only and site != only:
            continue
        if isinstance(data.get("viewport"), dict):
            X["viewports"][site] = data["viewport"]
        pj = os.path.join(os.path.dirname(f), "pages.json")
        try:   # tieu de man (nhan UI) -> sample cho type style Heading
            for pg in json.load(open(pj, encoding="utf8")) if os.path.isfile(pj) else []:
                for hd in pg.get("headings") or []:
                    lv, tx = hd.get("level"), (hd.get("text") or "").strip()
                    if lv and tx and len(X["uiLabels"].setdefault(lv, [])) < 5 and tx[:40] not in X["uiLabels"][lv]:
                        X["uiLabels"][lv].append(tx[:40])
        except (OSError, ValueError, AttributeError):
            pass
        for p in data.get("pages", []):
            src = "%s:%s" % (site, p.get("evId") or p.get("url"))
            pages.append({"site": site, "url": p.get("url"), "evId": p.get("evId")})

            def col(v, role, n=1):
                c = parse_color(v)
                if c:
                    B["colors"].add(c[0], n, role, src, {"alpha": c[1]})

            def font(stack, role):
                if stack:
                    B["fonts"].add(stack, 1, role, src)

            body = p.get("body") or {}
            col(body.get("bg"), "page-background")
            col(body.get("color"), "text")
            font(body.get("fontFamily"), "body")
            if body.get("fontSize"):
                B["fontSizes"].add(body["fontSize"], 1, "body", src)
            if body.get("lineHeight") and body["lineHeight"] != "normal":
                B["lineHeights"].add(body["lineHeight"], 1, "body", src)
            for h, s in (p.get("headings") or {}).items():
                col(s.get("color"), "heading-text")
                B["fontSizes"].add(s.get("fontSize"), 1, h, src) if s.get("fontSize") else None
                B["fontWeights"].add(s.get("fontWeight"), 1, h, src) if s.get("fontWeight") else None
                font(s.get("fontFamily"), h)
            for b in p.get("buttons") or []:
                c = parse_color(b.get("bg"))
                if c:
                    B["colors"].add(c[0], 1, "button-bg", src, {"alpha": c[1]})
                    B["buttonBg"].add(c[0], 1, None, src)
                col(b.get("color"), "button-text")
                bc = parse_color(b.get("border")) if b.get("border") and not str(b.get("border")).startswith("0px") else None
                if bc:
                    B["colors"].add(bc[0], 1, "button-border", src, {"alpha": bc[1]})
                for k, bag, role in (("borderRadius", "radii", "button"), ("fontSize", "fontSizes", "button"),
                                     ("fontWeight", "fontWeights", "button")):
                    if b.get(k):
                        B[bag].add(b[k], 1, role, src)
                font(b.get("fontFamily"), "button")
                for v in (b.get("padding") or "").split():
                    if v != "0px":
                        B["spacings"].add(v, 1, "button-padding", src)
                if b.get("boxShadow") and b["boxShadow"] != "none":
                    B["shadows"].add(b["boxShadow"], 1, "button", src)
            for i in p.get("inputs") or []:
                col(i.get("borderColor"), "input-border")
                col(i.get("bg"), "input-bg")
                for k, bag in (("borderRadius", "radii"), ("fontSize", "fontSizes"), ("height", "heights")):
                    if i.get(k):
                        B[bag].add(i[k], 1, "input", src)
                font(i.get("fontFamily"), "input")
                for v in (i.get("padding") or "").split():
                    if v != "0px":
                        B["spacings"].add(v, 1, "input-padding", src)
                if i.get("boxShadow") and i["boxShadow"] != "none":
                    B["shadows"].add(i["boxShadow"], 1, "input", src)
            if p.get("links"):
                col(p["links"].get("color"), "link")
            role_of = {"color": "text", "background-color": "background", "border-color": "border"}
            for prop, freq in (p.get("colorFreq") or {}).items():
                for v, n in freq.items():
                    col(v, role_of.get(prop, prop), n)
            if not p.get("valueFreq"):
                for v, n in (p.get("shadowFreq") or {}).items():
                    B["shadows"].add(v, n, "element", src)
            read_ds(p, site, src, B, col, X)
            for v, n in (p.get("fontFreq") or {}).items():
                B["fonts"].add(v, n, None, src)
    return pages


# ---------- component / typography / asset (crawl moi) ----------
SIG_KEYS = ("bg", "color", "borderColor", "borderWidth", "borderRadius", "padding", "fontSize", "fontWeight",
            "lineHeight", "fontFamily", "boxShadow", "height", "gap", "variant", "boxW", "boxH")
ROLE_OF = {"buttons": "button", "inputs": "input", "links": "link", "badges": "badge", "cards": "card",
           "alerts": "alert", "dialogs": "dialog", "breadcrumbs": "breadcrumb"}
GENERIC = {"sans-serif", "serif", "monospace", "system-ui", "cursive", "fantasy", "ui-sans-serif", "ui-serif",
           "ui-monospace", "-apple-system", "blinkmacsystemfont", "inherit", "initial"}


def hexa(v):
    """mau computed -> '#rrggbb' / '#rrggbbaa' (thuong) hoac None (trong suot)."""
    c = parse_color(v)
    if not c:
        return None
    return c[0].lower() + ("%02x" % round(c[1] * 255) if c[1] < 1 else "")


def norm_sample(smp):
    o = {k: smp.get(k) for k in SIG_KEYS if smp.get(k) not in (None, "")}
    for k in ("bg", "color", "borderColor"):
        if k in o:
            o[k] = hexa(o[k]) or "transparent"
    if o.get("borderWidth") in ("0px", "0"):
        o.pop("borderColor", None)
    return o


def read_ds(p, site, src, B, col, X):
    """Doc components/typeHist/valueFreq/fontFaces cua 1 trang (crawl-site.js moi)."""
    url = p.get("url")
    body_bg = (p.get("body") or {}).get("bg")
    S = X["sites"].setdefault(site, {"primary": {}, "navBg": {}, "headerBg": {}, "bodyBg": {}, "link": {}})

    def vote(key, v):
        h = hexa(v)
        if h:
            S[key][h] = S[key].get(h, 0) + 1
    vote("bodyBg", body_bg)

    def pair(fg, bg, where):
        bg = bg if hexa(bg) and len(hexa(bg)) == 7 else body_bg
        if hexa(fg) and hexa(bg):
            X["pairs"].append((hexa(fg), hexa(bg), where))
    pair((p.get("body") or {}).get("color"), body_bg, "body")

    comps = p.get("components") or {}
    for cat, g in comps.items():
        if not isinstance(g, dict) or not g.get("count"):
            continue
        ent = X["components"].setdefault(cat, {"count": 0, "pages": [], "variants": {}, "sig": {}})
        ent["count"] += g["count"]
        if url not in ent["pages"] and len(ent["pages"]) < 8:
            ent["pages"].append(url)
        for k, v in (g.get("variants") or {}).items():
            ent["variants"][k] = ent["variants"].get(k, 0) + v
        for smp in g.get("samples") or []:
            if cat == "tables":
                col(smp.get("headerBg"), "table-header-bg")
                rb = parse_color(smp.get("rowBorder") or "")
                if rb:
                    B["colors"].add(rb[0], 1, "table-row-border", src, {"alpha": rb[1]})
                key = json.dumps(smp, sort_keys=True)
                e = ent["sig"].setdefault(key, {"n": 0, "style": {k: (hexa(v) if k == "headerBg" else v)
                                                                  for k, v in smp.items()}, "labels": []})
                e["n"] += 1
                continue
            st = norm_sample(smp)
            key = json.dumps(st, sort_keys=True)
            e = ent["sig"].setdefault(key, {"n": 0, "style": st, "labels": []})
            e["n"] += smp.get("n", 1)
            lb = (smp.get("label") or "").strip()
            if lb and lb not in e["labels"] and len(e["labels"]) < 5:
                e["labels"].append(lb[:30])
            role = ROLE_OF.get(cat, cat)
            col(smp.get("bg"), role + "-bg")
            col(smp.get("color"), role + "-text")
            if smp.get("borderWidth") not in (None, "0px", "0"):
                col(smp.get("borderColor"), role + "-border")
            for k, bag in (("borderRadius", "radii"), ("fontSize", "fontSizes"), ("fontWeight", "fontWeights"),
                           ("height", "heights")):
                v = smp.get(k)
                if v and v not in ("0px", "auto", "normal") and not (k == "height" and cat in ("nav", "cards", "tables")):
                    B[bag].add(v, 0, cat, src)
            if smp.get("boxShadow") not in (None, "none"):
                B["shadows"].add(smp["boxShadow"], 0, cat, src)
            # cap mau chu/nen de tinh contrast
            if cat in ("buttons", "badges", "header", "tableTh", "navItem", "navActive", "tabs", "tabActive", "alerts"):
                bg = smp.get("bg")
                if cat in ("navItem", "navActive") and not hexa(bg):
                    nav = (comps.get("nav") or {}).get("samples") or [{}]
                    bg = nav[0].get("bg")
                if cat == "tableTh" and not hexa(bg):
                    tb = (comps.get("tables") or {}).get("samples") or [{}]
                    bg = tb[0].get("headerBg")
                pair(smp.get("color"), bg, cat)
        if cat == "buttons":
            for smp in g.get("samples") or []:
                h = hexa(smp.get("bg"))
                if h and len(h) == 7 and not is_neutral(h.upper()):
                    S["primary"][h] = S["primary"].get(h, 0) + smp.get("n", 1)
        elif cat in ("nav", "header"):
            for smp in g.get("samples") or []:
                vote("navBg" if cat == "nav" else "headerBg", smp.get("bg"))
        elif cat == "links":
            for smp in g.get("samples") or []:
                vote("link", smp.get("color"))
                pair(smp.get("color"), body_bg, "links")

    for t in p.get("typeHist") or []:
        fam = t.get("fontFamily") or ""
        lh = t.get("lineHeight") if t.get("lineHeight") != "normal" else None
        key = (first_family(fam), t.get("fontSize"), lh, str(t.get("fontWeight")))
        e = X["type"].setdefault(key, {"family": fam, "fontSize": t.get("fontSize"), "lineHeight": lh,
                                       "fontWeight": str(t.get("fontWeight")), "count": 0, "colors": [],
                                       "tags": [], "pages": []})
        e["count"] += t.get("count", 1)
        h = hexa(t.get("color"))
        if h and h not in e["colors"]:
            e["colors"].append(h)
        for tg in t.get("tags") or []:
            if tg not in e["tags"]:
                e["tags"].append(tg)
        if url not in e["pages"] and len(e["pages"]) < 5:
            e["pages"].append(url)
        if t.get("fontSize"):
            B["fontSizes"].add(t["fontSize"], 0, "text", src)
        if lh:
            B["lineHeights"].add(lh, 0, "text", src)

    vf = p.get("valueFreq") or {}
    for v, n in (vf.get("boxShadow") or {}).items():
        B["shadows"].add(v, n, "element", src)
    for v, n in (vf.get("borderRadius") or {}).items():
        B["radii"].add(v, n, "element", src)
    for k in ("padding", "gap"):
        for v, n in (vf.get(k) or {}).items():
            for part in set(v.split()):
                if part not in ("0px", "normal"):
                    B["spacings"].add(part, n, k, src)
    for v, n in (vf.get("maxWidth") or {}).items():
        B["maxWidths"].add(v, n, "container", src)
    for f in p.get("fontFaces") or []:
        key = (f.get("family"), f.get("weight"), f.get("style"))
        e = X["fontFaces"].setdefault(key, {"family": f.get("family"), "weight": f.get("weight"),
                                            "style": f.get("style"), "src": f.get("src") or [], "pages": []})
        if url not in e["pages"] and len(e["pages"]) < 5:
            e["pages"].append(url)
    for h in p.get("fontLinks") or []:
        if h not in X["fontLinks"]:
            X["fontLinks"].append(h)


def lum(h):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def blend(fg, bg):
    """fg co alpha (#rrggbbaa) phu len bg dac -> #rrggbb."""
    if len(fg) == 7:
        return fg
    a = int(fg[7:9], 16) / 255
    return "#" + "".join("%02x" % round(int(fg[i:i + 2], 16) * a + int(bg[i:i + 2], 16) * (1 - a)) for i in (1, 3, 5))


def contrast(fg, bg):
    bg = blend(bg, "#ffffff")
    fg = blend(fg, bg)
    l1, l2 = sorted((lum(fg), lum(bg)), reverse=True)
    return round((l1 + 0.05) / (l2 + 0.05), 2)


def read_assets(root, only=None):
    out = {"sites": {}, "logos": 0, "icons": 0, "iconFonts": {}}
    for f in sorted(glob.glob(os.path.join(root, "*", "assets.json"))):
        d = json.load(open(f, encoding="utf8"))
        site = d.get("site") or os.path.basename(os.path.dirname(f))
        if only and site != only:
            continue
        files = []
        for x in d.get("files") or []:
            x = dict(x)
            x["path"] = "%s/%s" % (os.path.basename(os.path.dirname(f)), x.get("file"))
            files.append(x)
        out["sites"][site] = {"files": files, "iconFonts": d.get("iconFonts") or {}, "skipped": len(d.get("skipped") or [])}
        out["logos"] += sum(1 for x in files if x.get("kind") != "icon")
        out["icons"] += sum(1 for x in files if x.get("kind") == "icon")
        for k, n in (d.get("iconFonts") or {}).items():
            out["iconFonts"][k] = out["iconFonts"].get(k, 0) + n
    return out


def logo_colors(root, assets, B):
    """Mau fill/stroke trong file logo SVG da tai -> colors (role logo) de suy brand-<n>."""
    for site, d in (assets.get("sites") or {}).items():
        for x in d.get("files") or []:
            if x.get("kind") == "icon" or not str(x.get("file", "")).endswith(".svg"):
                continue
            try:
                txt = open(os.path.join(root, x["path"]), encoding="utf8", errors="replace").read()
            except OSError:
                continue
            for v in re.findall(r"(?:fill|stroke|stop-color)\s*[=:]\s*[\"']?(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))", txt):
                c = parse_color(v)
                if c:
                    B["colors"].add(c[0], 1, "logo", "%s:%s" % (site, x.get("evId") or x.get("page")), {"alpha": c[1]})


def top(d):
    return max(d.items(), key=lambda kv: kv[1])[0] if d else None


# ---------- tokens.json khoi dau: TEN VAI TRO §3.3 suy tu du lieu quan sat ----------
# Heuristic tat dinh (agent PHAI kiem lai tung vai tro, viet usage that):
#  D1 primary        nen nut solid khong trung tinh pho bien nhat (site khac primary -> 1 theme/site, id = site thuong)
#     primary-text   mau link / chu nut outline-text cung hue primary · on-primary = chu tren nut nen primary
#     primary-subtle nen nhat cua nav / tab dang chon · brand-<n> = mau chi thay trong logo
#     KHONG sinh primary-hover/active (crawl khong co hover), KHONG tu tao thang 50..900
#  D2 page-bg nen body · surface nen sang cua card/dialog/nav/header · surface-subtle nen header bang
#     text-high chu heading · text-middle chu body/nhan · text-low chu trung tinh nhat hon text-middle
#     divider-low ke hang bang · divider-middle vien input · white #ffffff · overlay-scrim nen den alpha<1
#  D3 badge/alert theo hue nen: xanh la success · xanh duong info · vang/cam warning · do negative
#     nen -> <status>-100 · chu -> success-700/info-700/warning-800/negative-600 · nut solid do -> negative-500
#  D5 space-<px> moi padding/gap px · radius: bang 0 none · <=2px xs · badge/alert sm · nut/input md ·
#     card/muc nav lg · dialog xl · >= nua chieu cao hoac >= 999px full
#     shadow: card flat · nut/input raise · header stick · dialog/alert popout
#  D7 viewport-web (viewport crawl) · header-height · sidebar-width (nav doc rong <= 400px) · control-sm/md/lg
#     (chieu cao nut/input, md = pho bien nhat) · nav-item-height · table-header/row-height · modal-width · content-max
#  D4 Heading (h1-h4 hoac >= 18px dam) / Text / Mono (font monospace): heading-<px>[-bold] · text-<px>[-bold] · mono-<px>
#  Gia tri khong khop vai tro nao -> obs-<family>-NN (agent gan vai tro hoac bo).
LEN_RE = re.compile(r"^-?(\d+\.?\d*|\.\d+)(px|rem|em|%)$|^0$")
PX_RE = re.compile(r"^(\d+\.?\d*|\.\d+)px$")
BAD_STACK = re.compile(r"[;{}<>\\()]")
MONO_RE = re.compile(r"mono|courier|consolas|menlo|monaco|code", re.I)
HEAD_TAGS = {"h1", "h2", "h3", "h4"}
BODY_TAGS = {"p", "td", "label", "span", "div", "li", "dd", "dt", "small", "th"}
COMP_OF = {"Button": ["buttons"], "TextField": ["inputs"], "Select": ["select"], "Checkbox": ["checkbox"],
           "Radio": ["radio"], "Switch": ["switch"], "Badge": ["badges"], "Tabs": ["tabs"], "Table": ["tables"],
           "Pagination": ["pagination"], "Modal": ["dialogs"], "Toast": [], "InlineMessage": ["alerts"],
           "PageHeader": ["h1"], "Breadcrumb": ["breadcrumbs"], "AppHeader": ["header"],
           "AppShell": ["header", "nav"], "SideNav": ["nav"]}
STATUS_TEXT = {"success": "success-700", "info": "info-700", "warning": "warning-800", "negative": "negative-600"}


def num(v):
    m = re.match(r"^-?[\d.]+", v or "")
    return float(m.group(0)) if m else 0.0


def fmtn(x):
    return ("%.2f" % x).rstrip("0").rstrip(".")


def px(v):
    """'12px' / 12.5 -> 12.5 hoac None."""
    if isinstance(v, (int, float)):
        return float(v) if v > 0 else None
    m = PX_RE.match(str(v or "").strip())
    return float(m.group(1)) if m else None


def hls(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hh, l_, s_ = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, l_, s_


def solid(h):
    return h if h and len(h) == 7 else None


def hue_status(h):
    if not solid(h):
        return None
    hh, l_, s_ = hls(h)
    if s_ < 0.2 or l_ < 0.03 or l_ > 0.985:
        return None
    if hh < 15 or hh >= 340:
        return "negative"
    if hh < 70:
        return "warning"
    if hh < 170:
        return "success"
    if hh < 265:
        return "info"
    return None


def same_hue(a, b, tol=20):
    if not (solid(a) and solid(b)) or is_neutral(a.upper()) or is_neutral(b.upper()):
        return False
    d = abs(hls(a)[0] - hls(b)[0])
    return min(d, 360 - d) <= tol


class Votes(dict):
    def add(self, key, n=1, pages=()):
        e = self.setdefault(key, {"n": 0, "pages": []})
        e["n"] += n
        for p in pages:
            if p and p not in e["pages"] and len(e["pages"]) < 3:
                e["pages"].append(p)

    def top(self, ok=lambda k: True):
        rows = sorted(((k, e) for k, e in self.items() if ok(k)), key=lambda kv: (-kv[1]["n"], str(kv[0])))
        return rows[0] if rows else (None, None)


def todo(row, extra=""):
    roles = ", ".join(row.get("roles") or []) or "—"
    seen = ", ".join((row.get("sources") or [])[:3]) or "—"
    return ("TODO — khong khop vai tro nao (roles: %s); %s lan; thay o %s%s" % (roles, row.get("count", 0), seen, extra))[:1000]


def emit_tokens(draft, path, name, multi=None):
    """multi: None = 1 theme/site khi primary khac nhau · True = 1 theme/site (mode themes) · False = 1 theme light."""
    ev_url = {"%s:%s" % (p["site"], p["evId"]): p["url"] for p in draft["pages"] if p.get("evId")}

    def evid(row):
        for s_ in row.get("sources") or []:
            if s_ in ev_url:
                return ev_url[s_]
            if s_.startswith("REPO-"):
                return s_
        return None
    comps = draft.get("components") or {}

    def samples(*cats):
        for c in cats:
            g = comps.get(c) or {}
            for smp in g.get("samples") or []:
                yield c, smp.get("style") or {}, smp.get("n", 1), g.get("pages") or [], smp.get("labels") or []

    sites = sorted({p["site"] for p in draft["pages"]})
    src = "+".join(x for x, ok in (("website", bool(draft["pages"])), ("code", bool(draft["cssRoots"]))) if ok)
    prim = {s_: solid(d.get("primaryCandidate")) for s_, d in draft["perSite"].items()}
    prim = {k: v for k, v in prim.items() if v}
    if multi is None:
        multi = len(set(prim.values())) > 1
    multi = bool(multi) and len(sites) > 1
    themes = [{"id": s_.lower(), "name": s_} for s_ in sites] if multi else [{"id": "light", "name": "Light"}]
    R = {}   # ten -> {fam, value, ctx, n, pages}

    def put(fam, nm, value, ctx, n=0, pages=()):
        if nm in R or value in (None, "", {}):
            return
        R[nm] = {"fam": fam, "value": value, "ctx": ctx, "n": n, "pages": list(pages)[:3]}

    def put_vote(fam, nm, votes, ctx, ok=lambda k: True):
        k, e = votes.top(ok)
        if k is not None:
            put(fam, nm, k, ctx, e["n"], e["pages"])

    # --- D1 primary theo theme ---
    btn_pages = (comps.get("buttons") or {}).get("pages") or []
    n_prim = sum(p["buttons"] for p in draft.get("primaryCandidates") or [] if p["hex"].lower() in prim.values())
    if prim:
        if multi:
            put("color", "primary", {s_.lower(): v for s_, v in prim.items()}, "nen nut solid pho bien nhat moi site",
                n_prim, btn_pages)
        else:
            put("color", "primary", next(iter(prim.values())), "nen nut solid khong trung tinh pho bien nhat",
                n_prim, btn_pages)
    tprim = {s_.lower(): v for s_, v in prim.items()} if multi else {"light": next(iter(prim.values()))} if prim else {}

    def per_theme(nm, pick, ctx):
        val, pages, cnt = {}, [], 0
        for th, pv in tprim.items():
            v = Votes()
            for x, n, pg in pick(pv):
                v.add(x, n, pg)
            k, e = v.top()
            if k:
                val[th] = k
                pages += e["pages"]
                cnt += e["n"]
        if val:
            put("color", nm, val if multi else next(iter(val.values())), ctx, cnt, pages)

    def on_primary(pv):
        return [(st["color"], n, pg) for c, st, n, pg, _ in samples("buttons")
                if st.get("bg") == pv and solid(st.get("color"))]

    def primary_text(pv):
        return [(st["color"], n, pg) for c, st, n, pg, _ in samples("links", "buttons", "tabActive")
                if (c != "buttons" or st.get("variant") in ("outline", "text")) and same_hue(st.get("color"), pv)]

    def primary_subtle(pv):
        def ok(b):
            if not solid(b) or b == pv:
                return False
            hh, l_, s_ = hls(b)
            d = abs(hh - hls(pv)[0])
            return 0.8 < l_ < 0.99 and s_ >= 0.2 and min(d, 360 - d) <= 30
        return [(st["bg"], n, pg) for c, st, n, pg, _ in samples("navActive", "tabActive") if ok(st.get("bg"))]
    per_theme("on-primary", on_primary, "chu tren nut solid nen primary")
    per_theme("primary-text", primary_text, "link / nut outline-text cung hue primary")
    per_theme("primary-subtle", primary_subtle, "nen nhat cua nav / tab dang chon")
    for i, c in enumerate([c for c in draft["colors"] if c.get("roles") == ["logo"]
                           and not is_neutral(c["hex"])][:4], 1):
        put("color", "brand-%d" % i, c["hex"].lower(), "mau chi thay trong logo", c["count"], [evid(c)])

    # --- D2 nen / chu / ke ---
    v, pbg = Votes(), {}
    for s_, d in draft["perSite"].items():
        if solid(d.get("bodyBg")):
            v.add(d["bodyBg"], 1, [p["url"] for p in draft["pages"] if p["site"] == s_][:1])
            pbg[s_.lower()] = d["bodyBg"]
    if multi and len(set(pbg.values())) > 1:   # nen body khac nhau giua site -> theo theme
        put("color", "page-bg", pbg, "nen body moi site", len(pbg), [p["url"] for p in draft["pages"]][:3])
    put_vote("color", "page-bg", v, "nen body")
    v = Votes()
    for c, st, n, pg, _ in samples("cards", "dialogs", "nav", "header"):
        if solid(st.get("bg")) and hls(st["bg"])[1] > 0.85:
            v.add(st["bg"], n, pg)
    put_vote("color", "surface", v, "nen sang cua card / dialog / nav / header")
    v = Votes()
    for c, st, n, pg, _ in samples("tables", "tableTh"):
        b = st.get("headerBg") if c == "tables" else st.get("bg")
        if solid(b):
            v.add(b, n, pg)
    put_vote("color", "surface-subtle", v, "nen header bang", lambda k: k != (R.get("surface") or {}).get("value"))
    hv, bv = Votes(), Votes()
    for t in draft.get("typeStyles") or []:
        tags = set(t.get("tags") or [])
        for col in t.get("colors") or []:
            if not solid(col):
                continue
            if tags & HEAD_TAGS:
                hv.add(col, t["count"], t.get("pages") or [])
            if tags & BODY_TAGS:
                bv.add(col, t["count"], t.get("pages") or [])
    put_vote("color", "text-high", hv, "mau chu heading h1-h4", lambda k: hls(k)[1] < 0.5)
    put_vote("color", "text-middle", bv, "mau chu body / nhan / o bang",
             lambda k: hls(k)[1] < 0.5 and (hls(k)[2] < 0.25 or is_neutral(k.upper())))
    mid = (R.get("text-middle") or {}).get("value")
    if mid:
        lv = Votes()
        for t in draft.get("typeStyles") or []:
            for col in t.get("colors") or []:
                if solid(col) and is_neutral(col.upper()) and lum(mid) + 0.02 < lum(col) < 0.6 \
                        and contrast(col, "#ffffff") >= 2.0:
                    lv.add(col, t["count"] * (2 if num(t.get("fontSize")) <= 13 else 1), t.get("pages") or [])
        put_vote("color", "text-low", lv, "chu trung tinh nhat (helper / meta)")
    v = Votes()
    for c in draft["colors"]:
        if "table-row-border" in (c.get("roles") or []):
            v.add(c["hex"].lower(), c["count"], [evid(c)])
    put_vote("color", "divider-low", v, "ke giua cac hang bang")
    v = Votes()
    for c, st, n, pg, _ in samples("inputs", "select"):
        if solid(st.get("borderColor")) and st.get("borderWidth") not in (None, "0px", "0"):
            v.add(st["borderColor"], n, pg)
    put_vote("color", "divider-middle", v, "vien input / select")
    for c in draft["colors"]:
        if c["hex"] == "#FFFFFF" and 1.0 in (c.get("alpha") or [1.0]) and c["count"] > 0:
            put("color", "white", "#ffffff", "trang tuyet doi", c["count"], [evid(c)])
    v = Votes()
    for c in draft["colors"]:
        if lum(c["hex"]) < 0.02 and c["count"] > 0 and set(c.get("roles") or []) & {"background", "dialogs-bg"}:
            for a in c.get("alpha") or []:
                if 0.05 <= a < 1:
                    v.add(c["hex"].lower() + "%02x" % round(a * 255), c["count"], [evid(c)])
    put_vote("color", "overlay-scrim", v, "nen den trong suot (lop phu sau dialog)")

    # --- D3 trang thai ---
    sv = {}
    for c, st, n, pg, _ in samples("badges", "alerts"):
        b, f = solid(st.get("bg")), solid(st.get("color"))
        stt = hue_status(b)
        if stt:
            sv.setdefault((stt, "bg"), Votes()).add(b, n, pg)
            if f:
                sv.setdefault((stt, "fg"), Votes()).add(f, n, pg)
        elif hue_status(f):
            sv.setdefault((hue_status(f), "fg"), Votes()).add(f, n, pg)
    for stt in ("success", "info", "warning", "negative"):
        if (stt, "bg") in sv:
            put_vote("color", stt + "-100", sv[(stt, "bg")], "nen badge / alert tone %s" % stt)
        if (stt, "fg") in sv:
            put_vote("color", STATUS_TEXT[stt], sv[(stt, "fg")], "chu badge / alert tone %s" % stt)
    v = Votes()
    for c, st, n, pg, _ in samples("buttons"):
        if hue_status(st.get("bg")) == "negative" and st.get("bg") not in tprim.values():
            v.add(st["bg"], n, pg)
    put_vote("color", "negative-500", v, "nen nut solid do (xoa / nguy hiem)")

    # --- D5 spacing / radius / shadow ---
    sp = []
    for r in draft["spacings"]:
        x = px(str(r["value"]).strip())
        if x and fmtn(x) not in [s[0] for s in sp]:
            sp.append((fmtn(x), r))
    sp = sorted(sp[:60], key=lambda s: float(s[0]))
    for k, r in sp:
        put("spacing", "space-%s" % k, "%spx" % k, "padding/gap " + (", ".join(r.get("roles") or []) or "—"),
            r["count"], [evid(r)])
    RAD = {"badges": "radius-sm", "alerts": "radius-sm", "buttons": "radius-md", "inputs": "radius-md",
           "select": "radius-md", "cards": "radius-lg", "navItem": "radius-lg", "navActive": "radius-lg",
           "dialogs": "radius-xl"}
    if (comps.get("tables") or {}).get("count"):
        put("radius", "radius-none", "0px", "bang, divider (khong bo goc)", comps["tables"]["count"],
            (comps["tables"].get("pages") or [])[:2])
    rv, full = {}, Votes()
    for c, st, n, pg, _ in samples(*RAD):
        r_ = px(st.get("borderRadius"))
        if not r_:
            continue
        h = px(st.get("boxH")) or 0
        if r_ >= 999 or (h and r_ >= h / 2):
            full.add(st["borderRadius"], n, pg)
        else:
            rv.setdefault(RAD[c], Votes()).add(st["borderRadius"], n, pg)
    for nm in ("radius-md", "radius-lg", "radius-sm", "radius-xl"):
        if nm in rv:
            put_vote("radius", nm, rv[nm], {"radius-sm": "badge / alert", "radius-md": "nut / input / select",
                                            "radius-lg": "card / muc nav", "radius-xl": "dialog"}[nm])
    put_vote("radius", "radius-full", full, "pill / switch (>= nua chieu cao)")
    xs = sorted((px(r["value"]), r) for r in draft["radii"] if px(r["value"]) and px(r["value"]) <= 2)
    if xs:
        put("radius", "radius-xs", xs[0][1]["value"], "bo goc rat nho (<= 2px)", xs[0][1]["count"], [evid(xs[0][1])])
    SHD = [("shadow-flat", ("cards",), "card"), ("shadow-raise", ("inputs", "buttons", "select"), "input / nut"),
           ("shadow-stick", ("header",), "header"), ("shadow-popout", ("dialogs", "alerts"), "dialog / toast")]
    for nm, cats, ctx in SHD:
        v = Votes()
        for c, st, n, pg, _ in samples(*cats):
            b = st.get("boxShadow") or "none"
            if b != "none" or nm == "shadow-flat":
                v.add(b, n, pg)
        put_vote("shadow", nm, v, ctx)

    # --- D7 size ---
    vp = next(iter(draft.get("viewports", {}).values()), None)
    if vp and vp.get("width"):
        put("size", "viewport-web", "%dpx" % vp["width"], "viewport crawl %dx%d (cao %dpx)" % (
            vp["width"], vp.get("height", 0), vp.get("height", 0)), len(draft["pages"]), [draft["pages"][0]["url"]])

    def size_vote(nm, cats, key, ctx, ok=lambda st: True):
        v = Votes()
        for c, st, n, pg, _ in samples(*cats):
            x = px(st.get(key))
            if x and ok(st):
                v.add("%spx" % fmtn(x), n, pg)
        put_vote("size", nm, v, ctx)
    size_vote("header-height", ("header",), "boxH", "chieu cao header")
    size_vote("sidebar-width", ("nav",), "boxW", "chieu rong nav doc",
              lambda st: (px(st.get("boxW")) or 999) <= 400 and (px(st.get("boxH")) or 0) > (px(st.get("boxW")) or 0))
    cv = Votes()
    for c, st, n, pg, _ in samples("buttons", "inputs", "select"):
        x = px(st.get("boxH"))
        if x and x >= 16:
            cv.add("%spx" % fmtn(x), n, pg)
    k, e = cv.top()
    if k:
        put("size", "control-md", k, "chieu cao nut / input pho bien nhat", e["n"], e["pages"])
        lo = sorted(x for x in cv if num(x) < num(k))
        hi = sorted(x for x in cv if num(x) > num(k))
        if lo:
            put("size", "control-sm", lo[0], "chieu cao nut / input nho nhat", cv[lo[0]]["n"], cv[lo[0]]["pages"])
        if hi:
            put("size", "control-lg", hi[-1], "chieu cao nut / input lon nhat", cv[hi[-1]]["n"], cv[hi[-1]]["pages"])
    size_vote("nav-item-height", ("navItem",), "boxH", "chieu cao muc nav")
    size_vote("table-header-height", ("tables",), "headerH", "chieu cao hang header bang")
    size_vote("table-row-height", ("tables",), "rowH", "chieu cao hang du lieu bang")
    size_vote("modal-width", ("dialogs",), "boxW", "chieu rong dialog")
    mw = [r for r in draft.get("maxWidths") or [] if px(r["value"])]
    if mw:
        put("size", "content-max", mw[0]["value"], "max-width vung noi dung", mw[0]["count"], [evid(mw[0])])

    # --- D4 type ---
    fams, mono = {}, None
    for f in draft["fonts"]:
        stack = f["family"].strip()
        if f["count"] <= 0 or not stack or BAD_STACK.search(stack) or len(stack) > 200 \
                or all(n.lower() in GENERIC for n in f["names"]):
            continue
        if MONO_RE.search(first_family(stack)):
            fams.setdefault("mono", stack)
        else:
            fams.setdefault("sans", stack)
    labels = {}
    for c, st, n, pg, lb in samples(*[k for k in comps if k not in ("tables",)]):
        for x in lb:
            labels.setdefault((st.get("fontSize"), str(st.get("fontWeight"))), x)
    groups, snames, n_obs = {"Heading": [], "Text": [], "Mono": []}, set(), 0
    for t in draft["typeStyles"]:
        if sum(len(x) for x in groups.values()) >= 30:
            break
        x = px(t.get("fontSize"))
        if not x:
            continue
        w = int(t["fontWeight"]) if str(t.get("fontWeight", "")).isdigit() else 400
        tags = set(t.get("tags") or [])
        is_mono = bool(MONO_RE.search(first_family(t.get("family"))))
        generic_mono = is_mono and "mono" not in fams   # vd. textarea mac dinh trinh duyet
        grp = "Mono" if is_mono and not generic_mono else "Heading" if tags & HEAD_TAGS or (x >= 18 and w >= 600) else "Text"
        nm = {"Mono": "mono-%s", "Heading": "heading-%s", "Text": "text-%s"}[grp] % fmtn(x) + ("-bold" if w >= 600 and grp != "Mono" else "")
        if nm in snames or generic_mono:
            n_obs += 1
            nm = "obs-type-%02d" % n_obs
        snames.add(nm)
        smp = next((labels[k] for k in [(t.get("fontSize"), str(w))] if k in labels), None)
        if not smp and grp == "Heading":
            smp = next((draft.get("uiLabels", {}).get(h, [None])[0] for h in sorted(tags & HEAD_TAGS)
                        if draft.get("uiLabels", {}).get(h)), None)
        st = {"name": nm, "fontSize": "%spx" % fmtn(x)}
        if t.get("lineHeight") and LEN_RE.match(t["lineHeight"]):
            st["lineHeight"] = t["lineHeight"]
        st["fontWeight"] = w
        st["sample"] = smp or "TODO — nhan UI that"
        st["usage"] = ("TODO — vai tro suy tu tags %s; %d lan; mau %s; thay o %s" % (
            ", ".join(sorted(tags)) or "—", t["count"], ", ".join(t["colors"][:3]) or "—",
            ", ".join(t["pages"][:2]) or "—"))[:1000]
        groups[grp].append(st)

    # --- gia tri khong khop vai tro -> obs-* ---
    evidence = {}
    for nm, e in R.items():
        ev = next((p for p in e["pages"] if p), None)
        if ev:
            evidence[nm] = ev
    used = set()
    for e in R.values():
        if e["fam"] == "color":
            used |= set(e["value"].values()) if isinstance(e["value"], dict) else {e["value"]}
    obs = {"color": [], "radius": [], "shadow": []}
    for c in draft["colors"]:
        for a in sorted(set(c.get("alpha") or [1.0]), reverse=True):
            vv = c["hex"].lower() + ("%02x" % round(a * 255) if a < 1 else "")
            if vv in used or len(obs["color"]) >= 60:
                continue
            used.add(vv)
            obs["color"].append((vv, todo(c, "" if a == 1 else "; alpha %s" % a), evid(c)))
    rused = {e["value"] for e in R.values() if e["fam"] == "radius"}
    for r in draft["radii"]:
        v_ = str(r["value"]).strip()
        if LEN_RE.match(v_) and v_ not in rused and len(obs["radius"]) < 20:
            rused.add(v_)
            obs["radius"].append((v_, todo(r), evid(r)))
    shused = {e["value"] for e in R.values() if e["fam"] == "shadow"}
    for r in draft["shadows"]:
        v_ = str(r["value"]).strip()
        if v_ not in shused and "var(" not in v_ and "url(" not in v_ and len(obs["shadow"]) < 20:
            shused.add(v_)
            obs["shadow"].append((v_, todo(r), evid(r)))

    def tok(nm, e):
        return {"name": nm, "value": e["value"], "usage": ("TODO — vai tro suy tu %s; %d lan; thay o %s" % (
            e["ctx"], e["n"], ", ".join(p for p in e["pages"] if p) or "—"))[:1000]}
    fam_out = {f: [tok(nm, e) for nm, e in R.items() if e["fam"] == f] for f in ("color", "spacing", "radius", "shadow", "size")}
    for f, rows in obs.items():
        for i, (vv, u, ev) in enumerate(rows, 1):
            nm = "obs-%s-%02d" % (f, i)
            fam_out[f].append({"name": nm, "value": vv, "usage": u})
            if ev:
                evidence[nm] = ev
    files = []
    for s_ in sites:
        u = next((p["url"] for p in draft["pages"] if p["site"] == s_), None)
        if u:
            files.append(u)
    out = {"name": name, "version": 1,
           "meta": {"source": src or "UNKNOWN", "file": " ; ".join(files), "frames": [], "components": {},
                    "componentKeys": {}, "synced": datetime.date.today().isoformat(), "sites": sites,
                    "repos": sorted(draft["cssRoots"]), "evidence": evidence},
           "color": {"themes": themes, "tokens": fam_out["color"]},
           "type": {"fonts": [], "families": fams,
                    "groups": [dict({"name": g}, **({"family": "mono" if g == "Mono" else "sans"}
                                                    if ("mono" if g == "Mono" else "sans") in fams else {}),
                                    styles=st) for g, st in groups.items() if st]}}
    for f in ("spacing", "radius", "shadow", "size"):
        if fam_out[f]:
            out[f] = {"tokens": fam_out[f][:60]}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=2)
    return out, {"themes": len(themes), "roles": sorted(n for n in R if not n.startswith("space-")),
                 "obs": {f: len(r) for f, r in obs.items()},
                 "typeStyles": sum(len(x) for x in groups.values()), "path": path}


def emit_status(draft, tk, path, name, note=None, conflicts=()):
    """STATUS.md DRAFT tu template §8: nguon, platform, TBD = moi token/component bat buoc CHUA co.
    note: 1 dong '- Ghi chú:' (vd DS anh em) · conflicts: [(noi dung, quyet dinh tam)] -> ## Mâu thuẫn."""
    have = set()
    for k, v in tk.items():
        if k == "color":
            have |= {t["name"] for t in v.get("tokens", [])}
        elif isinstance(v, dict) and isinstance(v.get("tokens"), list):
            have |= {t["name"] for t in v["tokens"]}
    typ = tk.get("type") or {}
    gnames = {g["name"] for g in typ.get("groups") or []}
    sizes = {t["name"]: t["value"] for t in (tk.get("size") or {}).get("tokens", [])}
    comps = draft.get("components") or {}
    rows = []
    for d, nm in R_.all_required():
        alts = nm.split(" / ")
        if not any(a in have for a in alts):
            rows.append((d, nm, R_.NOTE_RO if any(a in R_.UNOBSERVABLE for a in alts) else R_.NOTE_NOT_SEEN))
    if not any(R_.SPACE_RE.match(n) for n in have):
        rows.append(("D5", "space-<px>", R_.NOTE_NOT_SEEN))
    if "sans" not in (typ.get("families") or {}):
        rows.append(("D4", "families.sans", R_.NOTE_NOT_SEEN))
    for g in R_.TYPE_GROUPS:
        if g not in gnames:
            rows.append(("D4", g, R_.NOTE_NOT_SEEN))
    icons = (draft.get("assets") or {}).get("icons", 0) + sum(((draft.get("assets") or {}).get("iconFonts") or {}).values())
    for c in R_.COMPONENTS + ["SideNav / TabBar"]:
        cats = COMP_OF.get(c.split(" / ")[0], [])
        seen = icons > 0 if c == "Icon" else bool(cats) and all((comps.get(k) or {}).get("count") for k in cats)
        if not seen:
            rows.append(("D6", c, R_.NOTE_RO if c in R_.UNOBSERVABLE else R_.NOTE_NOT_SEEN))
    sites = sorted({p["site"] for p in draft["pages"]})
    th = [t["id"] for t in tk["color"]["themes"]]
    n_pg = {s_: sum(1 for p in draft["pages"] if p["site"] == s_) for s_ in sites}
    url = {s_: next((p["url"] for p in draft["pages"] if p["site"] == s_), "") for s_ in sites}
    src = ["website %s (%s, %d màn đã quét)" % (s_, url[s_], n_pg[s_]) for s_ in sites]
    src += ["codebase %s (%d file CSS)" % kv for kv in sorted(draft["cssRoots"].items())]
    L = ["# Design System — %s" % name, "", "- Trạng thái: DRAFT", "- Artifact: — (chưa publish)",
         "- Nguồn: %s" % (" · ".join(src) or "UNKNOWN")] + (["- Ghi chú: %s" % note] if note else []) + [
         "", "## Platform", "",
         "| Platform | Theme (`data-theme`) | Viewport | Khung màn | Screen prefix |", "|---|---|---|---|---|"]
    for s_ in sites:
        vp = (draft.get("viewports") or {}).get(s_) or {}
        frame = " · ".join("%s `%s` %s" % (lb, k, sizes[k]) for lb, k in (("header", "header-height"),
                           ("sidebar", "sidebar-width"), ("tab bar", "tabbar-height")) if k in sizes) or "—"
        L.append("| Web desktop (%s) | `%s` | %s × %s (`viewport-web`) | %s | — |" % (
            s_, s_.lower() if len(th) > 1 and s_.lower() in th else th[0], vp.get("width", "?"), vp.get("height", "?"), frame))
    L += ["", "## Thứ tự ưu tiên nguồn (khi mâu thuẫn)", "1. Màu / size đo trên website đang chạy · code",
          "2. Variable / style trong Figma library", "3. Tài liệu guideline", "", "## Thiếu (TBD)", "",
          "| D# | Token / component | Ghi chú |", "|---|---|---|"]
    L += ["| %s | %s | %s |" % r for r in rows]
    L += ["", "## Mâu thuẫn cần xác nhận", "", "| # | Nội dung | Quyết định tạm |", "|---|---|---|"]
    L += ["| %d | %s | %s |" % (i, c.replace("|", "/"), q.replace("|", "/")) for i, (c, q) in enumerate(conflicts, 1)]
    L += ["",
          "## Changelog", "", "| Ngày | Thay đổi |", "|---|---|",
          "| %s | Khởi tạo từ extract-design-tokens.py (%d trang) — DRAFT, agent kiểm lại vai trò token |" % (
              datetime.date.today().isoformat(), len(draft["pages"])), ""]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    open(path, "w", encoding="utf8").write("\n".join(L))
    return {"path": path, "tbd": len(rows)}


# ---------- source CSS ----------
VAR_PATTERNS = [
    ("css-var", re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;{}]+?)\s*(?:;|$)")),
    ("scss-var", re.compile(r"^\s*(\$[A-Za-z0-9_-]+)\s*:\s*([^;{}]+?)\s*(?:!default)?\s*(?:;|$)")),
    ("less-var", re.compile(r"^\s*(@[A-Za-z0-9_-]+)\s*:\s*([^;{}]+?)\s*(?:;|$)")),
]
FONT_RE = re.compile(r"font-family\s*:\s*([^;{}]+?)\s*(?:;|$|})|fontFamily\s*:\s*['\"`]([^'\"`]+)['\"`]")
TW_COLOR_RE = re.compile(r"['\"]?([A-Za-z0-9_-]+)['\"]?\s*:\s*['\"](#[0-9a-fA-F]{3,8}|rgba?\([^'\"]+\)|hsla?\([^'\"]+\))['\"]")
TW_FONT_RE = re.compile(r"['\"]?([A-Za-z0-9_-]+)['\"]?\s*:\s*\[\s*((?:['\"][^'\"]+['\"]\s*,?\s*)+)\]")


def classify_var(name, value):
    n = name.lower()
    if "shadow" in n:
        return "shadows"
    if "radius" in n or "rounded" in n:
        return "radii"
    if re.search(r"font-?size|text-size|fs-", n):
        return "fontSizes"
    if "weight" in n:
        return "fontWeights"
    if re.search(r"font|family|typeface", n) and not re.search(r"line|height|spacing", n):
        return "fonts"
    if re.search(r"space|spacing|gap|gutter", n):
        return "spacings"
    if parse_color(value) and not re.search(r"\d+px\s+\d+px", value):
        return "colors"
    return None


def scan_css(repo_id, root, B, css_vars):
    nfiles = 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in fns:
            tw = bool(TW_RE.match(fn))
            if not (tw or fn.endswith(CSS_EXT)):
                continue
            fp = os.path.join(dp, fn)
            try:
                if os.path.getsize(fp) > MAX_FILE:
                    continue
                lines = open(fp, encoding="utf8", errors="replace").read().splitlines()
            except OSError:
                continue
            nfiles += 1
            rel = os.path.relpath(fp, root).replace(os.sep, "/")
            for no, line in enumerate(lines, 1):
                src = "%s:%s#L%d" % (repo_id, rel, no)
                if tw:
                    for name, val in TW_COLOR_RE.findall(line):
                        c = parse_color(val)
                        if c:
                            B["colors"].add(c[0], 0, "theme:" + name, src, {"codeNames": "tailwind:" + name, "alpha": c[1]})
                    for name, fams in TW_FONT_RE.findall(line):
                        if "font" in line.lower() or name in ("sans", "serif", "mono"):
                            stack = ", ".join(x.strip().strip("'\"") for x in fams.split(",") if x.strip())
                            B["fonts"].add(stack, 0, "tailwind:" + name, src)
                    continue
                if fn.endswith((".css", ".scss", ".sass", ".less", ".vue")):
                    for kind, rx in VAR_PATTERNS:
                        for name, val in rx.findall(line):
                            if kind == "less-var" and fn.endswith((".css", ".scss", ".sass")):
                                continue
                            val = val.strip()
                            cat = classify_var(name, val)
                            css_vars.append({"name": name, "value": val[:120], "kind": kind,
                                             "category": cat, "source": src})
                            if cat == "colors":
                                c = parse_color(val)
                                if c and ("var(" not in val):
                                    B["colors"].add(c[0], 0, None, src, {"codeNames": name, "alpha": c[1]})
                            elif cat == "fonts" and "var(" not in val and "$" not in val:
                                B["fonts"].add(val.rstrip(";").strip(), 0, None, src)
                            elif cat in ("radii", "spacings", "shadows", "fontSizes", "fontWeights") \
                                    and "var(" not in val and "$" not in val:
                                B[cat].add(val, 0, "code:" + name, src)
                for m in FONT_RE.finditer(line):
                    stack = (m.group(1) or m.group(2) or "").strip()
                    if stack and "var(" not in stack and "$" not in stack and not stack.startswith("@") \
                            and stack.lower() not in ("inherit", "initial", "unset"):
                        B["fonts"].add(stack, 0, None, src)
    return nfiles


# ---------- tach DS theo website: fingerprint phong cach tung site ----------
# Quy tac (tat dinh, chi tren du lieu quan sat):
#  font chinh   : ho font dau tien khong generic cua stack dung nhieu nhat -> phai trung (khong phan biet hoa thuong)
#  thang chu    : tap to hop size/lineHeight/weight top 15 -> Jaccard >= 0.6
#  spacing      : tap gia tri padding/gap px top 12 -> Jaccard >= 0.6 · radius: tap top 10 -> Jaccard >= 0.6
#  radius vai tro: nut / input / card / badge / dialog -> lech <= 1px
#  nut, input   : chieu cao + radius + padding mau dai dien -> lech <= 1px
#  nav / header : huong nav (doc/ngang) phai trung; rong nav doc, cao header lech <= max(2px, 5%)
#  mau          : primary · nen body · nen nav · nen header · mau link
# Thieu du lieu o 1 trong 2 site -> bo qua khia canh do (khong tinh la khac).
PX_TOL = 1.0
BOX_TOL = (2.0, 0.05)
JACC_MIN = 0.6
COLOR_KEYS = (("primaryCandidate", "primary"), ("bodyBg", "page-bg"), ("navBg", "nav-bg"),
              ("headerBg", "header-bg"), ("linkColor", "link"))
MODES = ("single", "themes", "per-site")


def pxs(v):
    """'4px 8px' / 34.5 -> [4.0, 8.0] / [34.5]; None neu khong doi duoc."""
    if isinstance(v, (int, float)):
        return [float(v)]
    out = []
    for part in str(v or "").split():
        x = px(part) if part not in ("0", "0px") else 0.0
        if x is None:
            return None
        out.append(x)
    return out or None


def fingerprint(d):
    comps = d.get("components") or {}

    def rep(cat, pred=lambda st: True):
        for smp in (comps.get(cat) or {}).get("samples") or []:
            st = smp.get("style") or {}
            if pred(st):
                return st
        return None
    font = None
    for f in d.get("fonts") or []:
        if f.get("count", 0) <= 0:
            continue
        font = next((x for x in f.get("names") or families(f.get("family")) if x.lower() not in GENERIC), None)
        if font:
            break
    typ = ["%s/%s/%s" % (fmtn(px(t.get("fontSize")) or 0), t.get("lineHeight") or "normal", t.get("fontWeight"))
           for t in (d.get("typeStyles") or [])[:15] if px(t.get("fontSize"))]

    def vset(key, n):   # n gia tri px pho bien nhat (rows da sap theo count giam dan)
        out = []
        for r in d.get(key) or []:
            x = px(str(r["value"]).strip())
            if r.get("count", 0) > 0 and x and fmtn(x) not in out:
                out.append(fmtn(x))
        return sorted(out[:n], key=float)
    fp = {"font": font, "type": typ, "spacing": vset("spacings", 12), "radius": vset("radii", 10), "roles": {}}
    for cat, nm in (("buttons", "button"), ("inputs", "input"), ("cards", "card"), ("badges", "badge"),
                    ("dialogs", "dialog")):
        st = rep(cat, (lambda s: s.get("variant") == "solid") if cat == "buttons" else (lambda s: True)) or rep(cat)
        if st:
            fp["roles"][nm] = {k: st.get(k) for k in (("boxH", "borderRadius", "padding") if cat in ("buttons", "inputs")
                                                       else ("borderRadius",)) if st.get(k) not in (None, "")}
    nv = rep("nav")
    if nv and px(nv.get("boxW")) and px(nv.get("boxH")):
        w, h = px(nv["boxW"]), px(nv["boxH"])
        fp["nav"] = {"orient": "vertical" if h > w and w <= 400 else "horizontal", "width": w}
    hd = rep("header")
    if hd and px(hd.get("boxH")):
        fp["header"] = px(hd["boxH"])
    ps = (d.get("perSite") or {})
    one = next(iter(ps.values()), {}) if len(ps) == 1 else {}
    fp["colors"] = {lbl: one.get(k) for k, lbl in COLOR_KEYS}
    return fp


def jacc(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1.0


def compare_fp(A, B):
    """-> [(aspect, kind 'visual'|'color', detail)]"""
    out = []
    if A["font"] and B["font"] and A["font"].lower() != B["font"].lower():
        out.append(("font", "visual", "%s vs %s" % (A["font"], B["font"])))
    for k, lbl in (("type", "type-scale"), ("spacing", "spacing-scale"), ("radius", "radius-scale")):
        if A[k] and B[k]:
            j = jacc(A[k], B[k])
            if j < JACC_MIN:
                out.append((lbl, "visual", "Jaccard %.2f < %.1f (%s | %s)" % (
                    j, JACC_MIN, ",".join(A[k][:6]), ",".join(B[k][:6]))))
    for role in sorted(set(A["roles"]) & set(B["roles"])):
        ra, rb = A["roles"][role], B["roles"][role]
        for k in sorted(set(ra) & set(rb)):
            va, vb = pxs(ra[k]), pxs(rb[k])
            same = (va is not None and vb is not None and len(va) == len(vb)
                    and all(abs(x - y) <= PX_TOL for x, y in zip(va, vb))) if (va or vb) else ra[k] == rb[k]
            if not same:
                out.append(("%s.%s" % (role, k), "visual", "%s vs %s" % (ra[k], rb[k])))
    na, nb = A.get("nav"), B.get("nav")
    if na and nb:
        if na["orient"] != nb["orient"]:
            out.append(("nav", "visual", "%s vs %s" % (na["orient"], nb["orient"])))
        elif na["orient"] == "vertical" and abs(na["width"] - nb["width"]) > max(BOX_TOL[0], BOX_TOL[1] * na["width"]):
            out.append(("nav.width", "visual", "%spx vs %spx" % (fmtn(na["width"]), fmtn(nb["width"]))))
    ha, hb = A.get("header"), B.get("header")
    if ha and hb and abs(ha - hb) > max(BOX_TOL[0], BOX_TOL[1] * ha):
        out.append(("header.height", "visual", "%spx vs %spx" % (fmtn(ha), fmtn(hb))))
    for _, lbl in COLOR_KEYS:
        ca, cb = A["colors"].get(lbl), B["colors"].get(lbl)
        if ca and cb and ca.lower() != cb.lower():
            out.append(("color." + lbl, "color", "%s vs %s" % (ca, cb)))
    return out


def decide_layout(site_drafts, force=None):
    sites = sorted(site_drafts)
    fps = {s_: fingerprint(site_drafts[s_]) for s_ in sites}
    diffs = []
    for i, a_ in enumerate(sites):
        for b_ in sites[i + 1:]:
            for asp, kind, det in compare_fp(fps[a_], fps[b_]):
                diffs.append({"siteA": a_, "siteB": b_, "aspect": asp, "kind": kind, "detail": det})
    vis = [x for x in diffs if x["kind"] == "visual"]
    if len(sites) < 2:
        auto, reason = "single", "1 website"
    elif vis:
        auto = "per-site"
        reason = "website khac phong cach ngoai mau (%s) -> 1 DS / website" % ", ".join(
            sorted({"%s~%s:%s" % (x["siteA"], x["siteB"], x["aspect"].split(".")[0]) for x in vis})[:8])
    elif diffs:
        auto, reason = "themes", "website chi khac mau (%s) -> 1 DS, 1 theme / website" % ", ".join(
            sorted({x["aspect"] for x in diffs}))
    else:
        auto, reason = "single", "%d website giong nhau ca mau -> 1 DS, 1 theme light" % len(sites)
    mode = force or auto
    if force and force != auto:
        reason = "FORCED %s (tu dong: %s — %s)" % (force, auto, reason)
    return {"mode": mode, "auto": auto, "forced": bool(force), "reason": reason, "sites": sites,
            "tolerances": {"px": PX_TOL, "box": "max(%spx, %d%%)" % (fmtn(BOX_TOL[0]), BOX_TOL[1] * 100),
                           "jaccard": JACC_MIN},
            "diffs": diffs, "fingerprints": fps}


# ---------- gom du lieu (toan he thong hoac 1 site) ----------
CSS_SPEC = re.compile(r"^(REPO-\d{2,})(?:@([A-Za-z0-9_,-]+))?=(.+)$")


def build_draft(files, css, assets_root, crawl_root, only=None):
    """css: [(rid, sites|None, path)] · only: site id -> draft chi cua site do."""
    B = defaultdict(Bag)
    X = {"sites": {}, "pairs": [], "components": {}, "type": {}, "fontFaces": {}, "fontLinks": [],
         "viewports": {}, "uiLabels": {}}
    pages = read_crawl(files, B, X, only)
    css_vars, scanned = [], {}
    for rid, sites, path in css:
        if only and sites and only not in sites:
            continue
        scanned[rid] = scan_css(rid, path, B, css_vars)
    assets = read_assets(assets_root, only)
    logo_colors(assets_root, assets, B)
    colors = B["colors"].rows("hex")
    for c in colors:
        c["observedOnSite"] = c["count"] > 0
        c["neutral"] = is_neutral(c["hex"])
    prim = [{"hex": r["hex"], "buttons": r["count"], "sources": r["sources"][:5]}
            for r in B["buttonBg"].rows("hex") if not is_neutral(r["hex"])]
    fonts = B["fonts"].rows("family")
    for f in fonts:
        f["primary"] = first_family(f["family"])
        f["names"] = families(f["family"])

    def bare(key):
        return [{k: v for k, v in r.items()} for r in B[key].rows("value")]

    components = {}
    for cat, e in sorted(X["components"].items()):
        sm = sorted(e["sig"].values(), key=lambda x: -x["n"])
        components[cat] = {"count": e["count"], "pages": e["pages"], "representative": sm[0]["style"] if sm else None,
                           "samples": sm[:6], **({"variants": e["variants"]} if e["variants"] else {})}
    type_styles = sorted(X["type"].values(), key=lambda t: -t["count"])
    per_site = {s_: {"primaryCandidate": top(d["primary"]), "navBg": top(d["navBg"]), "headerBg": top(d["headerBg"]),
                     "bodyBg": top(d["bodyBg"]), "linkColor": top(d["link"])} for s_, d in sorted(X["sites"].items())}
    cpairs = {}
    for fg, bg, where in X["pairs"]:
        e = cpairs.setdefault((fg, bg), {"fg": fg, "bg": bg, "where": []})
        if where not in e["where"]:
            e["where"].append(where)
    contrast_rows = []
    for e in cpairs.values():
        r = contrast(e["fg"], e["bg"])
        contrast_rows.append(dict(e, ratio=r, pass45=r >= 4.5, pass30=r >= 3.0))
    contrast_rows.sort(key=lambda e: e["ratio"])
    return {
        "note": "OBSERVED data only (crawl computed-style + source CSS). Not a design system. count=0 -> chi thay trong code.",
        "crawlFiles": [os.path.relpath(f, crawl_root) for f in files if not only or site_of(f) == only],
        "cssRoots": scanned, "colors": colors, "primaryCandidates": prim, "fonts": fonts,
        "fontSizes": bare("fontSizes"), "fontWeights": bare("fontWeights"), "lineHeights": bare("lineHeights"),
        "radii": bare("radii"), "spacings": bare("spacings"), "heights": bare("heights"), "shadows": bare("shadows"),
        "maxWidths": bare("maxWidths"), "viewports": X["viewports"], "uiLabels": X["uiLabels"], "cssVars": css_vars,
        "pages": pages, "typeStyles": type_styles, "components": components, "perSite": per_site,
        "contrast": contrast_rows, "fontFaces": list(X["fontFaces"].values()), "fontLinks": X["fontLinks"],
        "assets": assets,
    }


def observed(d):
    """mau + ten font quan sat duoc cua 1 site -> verify-design-system chong bia theo site."""
    cols = {}
    for c in d["colors"]:
        cols.setdefault(c["hex"].lower(), sorted(set(c.get("alpha") or [1.0])))
    names = sorted({n.lower() for f in d["fonts"] for n in f.get("names") or []}
                   | {str(f.get("family", "")).lower() for f in d["fontFaces"]})
    return {"colors": cols, "fontNames": names}


def write_md(draft, out_dir):
    pages, colors, prim, fonts = draft["pages"], draft["colors"], draft["primaryCandidates"], draft["fonts"]
    scanned, per_site, components = draft["cssRoots"], draft["perSite"], draft["components"]
    type_styles, contrast_rows, assets = draft["typeStyles"], draft["contrast"], draft["assets"]

    def tbl(title, rows, key, n=12):
        L = ["## %s" % title, "", "| %s | Count | Roles | Sources |" % key.capitalize(), "|---|---|---|---|"]
        for r in rows[:n]:
            src = ", ".join(r["sources"][:3]) + (" ..." if len(r["sources"]) > 3 else "")
            al = [x for x in r.get("alpha") or [] if x < 1]
            val = r[key] + (" (alpha %s)" % "/".join(map(str, r["alpha"])) if al else "")
            L.append("| `%s` | %d | %s | %s |" % (val.replace("|", "/"), r["count"], ", ".join(r["roles"]) or "—", src))
        if len(rows) > n:
            L.append("| ... | +%d | | |" % (len(rows) - n))
        return L + [""]

    md = ["# Tokens draft (OBSERVED)", "",
          "- Trang da do: %d (%s) · CSS roots: %s" % (len(pages), ", ".join(sorted({p["site"] for p in pages})) or "—",
                                                     ", ".join("%s=%d file" % kv for kv in scanned.items()) or "—"),
          "- Primary candidates (button bg khong trung tinh): %s" %
          (", ".join("`%s` x%d" % (p["hex"], p["buttons"]) for p in prim[:5]) or "UNKNOWN — khong thay nut co mau"),
          "- Day la du lieu quan sat, KHONG phai design system da duyet. count=0 = chi thay trong source.", ""]
    lay = draft.get("dsLayout")
    if lay:
        md += ["## Bo cuc Design System (dsLayout)", "",
               "- Mode: **%s**%s · %s" % (lay["mode"], " (FORCED)" if lay["forced"] else "", lay["reason"]),
               "- Dung sai: px ±%s · box %s · Jaccard >= %s" % (lay["tolerances"]["px"], lay["tolerances"]["box"],
                                                               lay["tolerances"]["jaccard"]), ""]
        if lay["diffs"]:
            md += ["| Site A | Site B | Khia canh | Loai | Chi tiet |", "|---|---|---|---|---|"]
            md += ["| %s | %s | %s | %s | %s |" % (x["siteA"], x["siteB"], x["aspect"], x["kind"],
                                                  x["detail"].replace("|", "/")) for x in lay["diffs"][:40]]
            md.append("")
    md += tbl("Colors", colors, "hex", 20)
    md += tbl("Fonts", fonts, "family", 8)
    for t, k in (("Font sizes", "fontSizes"), ("Font weights", "fontWeights"), ("Radii", "radii"),
                 ("Spacings (padding)", "spacings"), ("Shadows", "shadows")):
        md += tbl(t, draft[k], "value", 10)
    md += ["## Per site (can tach theme?)", "", "| Site | Primary | Nav bg | Header bg | Body bg | Link |",
           "|---|---|---|---|---|---|"]
    md += ["| %s | %s |" % (s_, " | ".join(str(d.get(k) or "—") for k in ("primaryCandidate", "navBg", "headerBg",
                                                                         "bodyBg", "linkColor")))
           for s_, d in per_site.items()]
    md += ["", "## Components", "", "| Category | Count | Representative | Pages |", "|---|---|---|---|"]
    for cat, c in components.items():
        rep_ = ", ".join("%s=%s" % kv for kv in list((c["representative"] or {}).items())[:7])
        md.append("| %s | %d | %s | %s |" % (cat, c["count"], rep_.replace("|", "/"), len(c["pages"])))
    md += ["", "## Type styles (top 15)", "", "| Family | Size | Line | Weight | Count | Tags |", "|---|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %s | %d | %s |" % (first_family(t["family"]), t["fontSize"], t["lineHeight"] or "normal",
                                              t["fontWeight"], t["count"], ", ".join(t["tags"]))
           for t in type_styles[:15]]
    md += ["", "## Contrast (WCAG)", "", "| Fg | Bg | Ratio | 4.5 | 3.0 | Where |", "|---|---|---|---|---|---|"]
    md += ["| `%s` | `%s` | %.2f | %s | %s | %s |" % (e["fg"], e["bg"], e["ratio"], "ok" if e["pass45"] else "FAIL",
                                                    "ok" if e["pass30"] else "FAIL", ", ".join(e["where"]))
           for e in contrast_rows[:20]]
    md += ["", "## Fonts & assets", "",
           "- @font-face: %s" % (", ".join(sorted({f["family"] for f in draft["fontFaces"]})) or "—"),
           "- Font link: %s" % (", ".join(draft["fontLinks"]) or "—"),
           "- Logo/favicon: %d · icon svg: %d · icon font: %s" % (
               assets["logos"], assets["icons"], ", ".join("%s=%d" % kv for kv in assets["iconFonts"].items()) or "—"), ""]
    open(os.path.join(out_dir, "tokens-draft.md"), "w", encoding="utf8").write("\n".join(md))


def layout_notes(lay, site=None):
    """-> (note 1 dong, [(mau thuan, quyet dinh tam)]) cho STATUS.md."""
    if len(lay["sites"]) < 2:
        return None, []
    how = "--force-mode" if not lay["forced"] else "da FORCED, doi lai bang --force-mode"
    if lay["mode"] == "per-site":
        others = [s_ for s_ in lay["sites"] if s_ != site]
        note = "Hệ thống có %d website khác phong cách — DS riêng: %s." % (
            len(lay["sites"]), ", ".join("%s (`../%s/`)" % (x, x) for x in others))
        return note, [("Tách 1 DS / website: %s" % lay["reason"], "Tạm tách; xác nhận với designer (%s để gộp)" % how)]
    if lay["mode"] == "themes":
        return None, [("Gộp 1 DS, 1 theme / website (%s): %s" % (", ".join(lay["sites"]), lay["reason"]),
                       "Tạm gộp; xác nhận với designer (%s để tách)" % how)]
    return None, [("Gộp 1 DS, 1 theme `light` cho %s: %s" % (", ".join(lay["sites"]), lay["reason"]),
                   "Tạm gộp; xác nhận với designer (%s)" % how)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crawl", required=True)
    ap.add_argument("--css-root", action="append", default=[], help="REPO-01=/path hoac REPO-01@WEB-01=/path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--assets", help="thu muc assets cua crawl (mac dinh <out>/assets)")
    ap.add_argument("--emit-root", help="<ver>/04_DesignSystem: ghi starter theo dsLayout.mode (single/themes: "
                                        "<root>/project + STATUS.md; per-site: <root>/<WEB-xx>/...)")
    ap.add_argument("--force-mode", choices=MODES, help="ghi de quyet dinh tu dong (user quyet); ghi forced:true")
    ap.add_argument("--emit-tokens", help="(cu) ghi tokens.json khoi dau vao duong dan nay (1 thu muc)")
    ap.add_argument("--emit-status", nargs="?", const="", default=None,
                    help="(cu) ghi STATUS.md DRAFT (mac dinh <thu muc tokens>/../STATUS.md); can --emit-tokens")
    ap.add_argument("--name", default="Design System", help="ten system cho --emit-*")
    a = ap.parse_args()
    if a.emit_root and (a.emit_tokens or a.emit_status is not None):
        print("--emit-root khong dung chung voi --emit-tokens/--emit-status", file=sys.stderr)
        return 1
    if a.emit_status is not None and not a.emit_tokens:
        print("--emit-status can --emit-tokens", file=sys.stderr)
        return 1

    files = sorted(glob.glob(os.path.join(a.crawl, "*", "styles.json")))
    css = []
    for spec in a.css_root:
        m = CSS_SPEC.match(spec)
        if not m:
            print("--css-root phai dang REPO-01=/path hoac REPO-01@WEB-01=/path: %s" % spec, file=sys.stderr)
            return 1
        if not os.path.isdir(m.group(3)):
            print("Khong thay thu muc %s" % m.group(3), file=sys.stderr)
            return 1
        css.append((m.group(1), m.group(2).split(",") if m.group(2) else None, m.group(3)))
    if not files and not css:
        print("Khong co styles.json nao duoi %s va khong co --css-root" % a.crawl, file=sys.stderr)
        return 1
    aroot = a.assets or os.path.join(a.out, "assets")
    draft = build_draft(files, css, aroot, a.crawl)
    sites = sorted({p["site"] for p in draft["pages"]})
    site_drafts = {s_: build_draft(files, css, aroot, a.crawl, s_) for s_ in sites} if len(sites) > 1 else \
        ({sites[0]: draft} if sites else {})
    lay = decide_layout(site_drafts, a.force_mode)
    draft["dsLayout"] = lay
    for s_, d in site_drafts.items():
        draft["perSite"].setdefault(s_, {})["observed"] = observed(d)
    os.makedirs(a.out, exist_ok=True)
    jp = os.path.join(a.out, "tokens-draft.json")
    json.dump(draft, open(jp, "w", encoding="utf8"), ensure_ascii=False, indent=2)
    write_md(draft, a.out)

    res = {"pages": len(draft["pages"]), "colors": len(draft["colors"]),
           "primaryCandidates": [p["hex"] for p in draft["primaryCandidates"][:3]],
           "fonts": len(draft["fonts"]), "cssVars": len(draft["cssVars"]), "typeStyles": len(draft["typeStyles"]),
           "components": {k: v["count"] for k, v in draft["components"].items()},
           "contrastFail45": sum(1 for e in draft["contrast"] if not e["pass45"]),
           "assets": {"logos": draft["assets"]["logos"], "icons": draft["assets"]["icons"]}, "out": jp,
           "dsLayout": {"mode": lay["mode"], "auto": lay["auto"], "forced": lay["forced"], "reason": lay["reason"],
                        "diffs": ["%s~%s %s: %s" % (x["siteA"], x["siteB"], x["aspect"], x["detail"])
                                  for x in lay["diffs"][:12]]}}
    multi = {"single": False, "themes": True}.get(lay["mode"])   # per-site ghi vao 1 thu muc (cu) -> tu dong
    if a.emit_tokens:
        tk, res["emitted"] = emit_tokens(draft, a.emit_tokens, a.name, multi)
        if a.emit_status is not None:
            sp = a.emit_status or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(a.emit_tokens))), "STATUS.md")
            res["status"] = emit_status(draft, tk, sp, a.name, *layout_notes(lay))
    if a.emit_root:
        root = os.path.abspath(a.emit_root)
        per = lay["mode"] == "per-site"
        clash = [x for x in (os.listdir(root) if os.path.isdir(root) else [])
                 if (per and x in ("project", "STATUS.md")) or (not per and re.match(r"^WEB-\d+$", x))]
        if clash:
            print("%s da co layout khac (%s) — xoa/doi ten truoc khi ghi mode %s (khong tron 2 layout)" % (
                root, ", ".join(sorted(clash)), lay["mode"]), file=sys.stderr)
            return 1
        res["emitted"] = []
        if per:
            for s_ in sites:
                base = os.path.join(root, s_)
                tk, info = emit_tokens(site_drafts[s_], os.path.join(base, "project", "tokens.json"),
                                       "%s — %s" % (a.name, s_), False)
                info["site"] = s_
                info["status"] = emit_status(site_drafts[s_], tk, os.path.join(base, "STATUS.md"),
                                             "%s — %s" % (a.name, s_), *layout_notes(lay, s_))
                res["emitted"].append(info)
        else:
            tk, info = emit_tokens(draft, os.path.join(root, "project", "tokens.json"), a.name, multi)
            info["status"] = emit_status(draft, tk, os.path.join(root, "STATUS.md"), a.name, *layout_notes(lay))
            res["emitted"].append(info)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
