#!/usr/bin/env python3
"""Gom design token QUAN SAT DUOC (crawl styles.json + bien CSS trong source) -> tokens-draft.

  python3 extract-design-tokens.py --crawl <_internal>/recon/crawl \
          [--css-root REPO-01=/path/to/fe ...] --out <_internal>/recon/design \
          [--assets <_internal>/recon/design/assets] [--emit-tokens <dir>/project/tokens.json --name "<Ten DS>"]

Input : moi */styles.json duoi --crawl (do crawl-site.js ghi); --css-root (lap lai duoc) quet
        .css/.scss/.sass/.less/.vue/.tsx/.jsx + tailwind.config.(js|ts|cjs) tim custom property,
        bien SCSS/LESS, mau theme tailwind, font-family (bo qua node_modules/dist/build/vendor).
Output: tokens-draft.json (colors · primaryCandidates · fonts · fontSizes · fontWeights · radii ·
        spacings · shadows · cssVars · pages · typeStyles · components · perSite · contrast · fontFaces ·
        assets) va tokens-draft.md (bang tom tat cho nguoi doc).
--emit-tokens: tokens.json KHOI DAU dung grammar Design System artifact (format.md): chi gia tri quan sat,
        ten obs-<family>-NN, usage "TODO — ..." -> agent PHAI doi ten ngu nghia + viet usage that
        (gate V-DS FAIL khi con obs-/TODO).
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
def read_crawl(root, B, X):
    files = sorted(glob.glob(os.path.join(root, "*", "styles.json")))
    pages = []
    for f in files:
        data = json.load(open(f, encoding="utf8"))
        site = data.get("site") or os.path.basename(os.path.dirname(f))
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
    return files, pages


# ---------- component / typography / asset (crawl moi) ----------
SIG_KEYS = ("bg", "color", "borderColor", "borderWidth", "borderRadius", "padding", "fontSize", "fontWeight",
            "lineHeight", "fontFamily", "boxShadow", "height", "gap", "variant")
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


def read_assets(root):
    out = {"sites": {}, "logos": 0, "icons": 0, "iconFonts": {}}
    for f in sorted(glob.glob(os.path.join(root, "*", "assets.json"))):
        d = json.load(open(f, encoding="utf8"))
        site = d.get("site") or os.path.basename(os.path.dirname(f))
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


def top(d):
    return max(d.items(), key=lambda kv: kv[1])[0] if d else None


# ---------- tokens.json khoi dau (grammar Design System artifact) ----------
LEN_RE = re.compile(r"^-?(\d+\.?\d*|\.\d+)(px|rem|em|%)$|^0$")
BAD_STACK = re.compile(r"[;{}<>\\()]")


def num(v):
    m = re.match(r"^-?[\d.]+", v or "")
    return float(m.group(0)) if m else 0.0


def todo(row, extra=""):
    roles = ", ".join(row.get("roles") or []) or "—"
    seen = ", ".join((row.get("sources") or [])[:3]) or "—"
    return ("TODO — roles: %s; count %s; seen: %s%s" % (roles, row.get("count", 0), seen, extra))[:1000]


def emit_tokens(draft, path, name):
    ev_url = {"%s:%s" % (p["site"], p["evId"]): p["url"] for p in draft["pages"] if p.get("evId")}

    def evid(row):
        for s_ in row.get("sources") or []:
            if s_ in ev_url:
                return ev_url[s_]
            if s_.startswith("REPO-"):
                return s_
        return None
    sites = sorted({p["site"] for p in draft["pages"]})
    src = "+".join(x for x, ok in (("website", bool(draft["pages"])), ("code", bool(draft["cssRoots"]))) if ok)
    evidence = {}
    prim = {s_: d.get("primaryCandidate") for s_, d in draft["perSite"].items()}
    multi = len({v for v in prim.values() if v}) > 1
    themes = [{"id": s_.lower(), "name": s_} for s_ in sites] if multi else [{"id": "light", "name": "Light"}]
    colors, used = [], set()

    def add(family_list, fam, value, usage, ev=None):
        nm = "obs-%s-%02d" % (fam, len(family_list) + 1)
        family_list.append({"name": nm, "value": value, "usage": usage})
        if ev:
            evidence[nm] = ev
    if multi:
        add(colors, "color", {s_.lower(): v for s_, v in prim.items() if v},
            "TODO — primary candidate theo site (button bg): " + ", ".join("%s=%s" % kv for kv in prim.items() if kv[1]),
            draft["pages"][0]["url"] if draft["pages"] else None)
    for c in draft["colors"]:
        for a in sorted(set(c.get("alpha") or [1.0]), reverse=True):
            v = c["hex"].lower() + ("%02x" % round(a * 255) if a < 1 else "")
            if v in used or len(colors) >= 120:
                continue
            used.add(v)
            add(colors, "color", v, todo(c, "" if a == 1 else "; alpha %s" % a), evid(c))
    fams, fam_key = {}, {}
    for f in draft["fonts"]:
        stack = f["family"].strip()
        if f["count"] <= 0 or not stack or BAD_STACK.search(stack) or len(stack) > 200 or len(fams) >= 4 \
                or all(n.lower() in GENERIC for n in f["names"]):
            continue
        k = "obs-family-%02d" % (len(fams) + 1)
        fams[k], fam_key[first_family(stack).lower()] = stack, k
        evidence[k] = evid(f)
    styles = []
    for t in draft["typeStyles"][:30]:
        if not LEN_RE.match(t.get("fontSize") or ""):
            continue
        st = {"name": "obs-type-%02d" % (len(styles) + 1), "fontSize": t["fontSize"]}
        if t.get("lineHeight") and LEN_RE.match(t["lineHeight"]):
            st["lineHeight"] = t["lineHeight"]
        if t.get("fontWeight", "").isdigit():
            st["fontWeight"] = int(t["fontWeight"])
        k = fam_key.get(first_family(t["family"]).lower())
        if k:
            st["family"] = k
        st["usage"] = ("TODO — tags %s; count %d; colors %s; pages %s" % (
            ", ".join(t["tags"]) or "—", t["count"], ", ".join(t["colors"][:3]) or "—",
            ", ".join(t["pages"][:2])))[:1000]
        styles.append(st)
    out = {"name": name, "version": 1,
           "meta": {"source": src or "UNKNOWN", "sites": sites, "repos": sorted(draft["cssRoots"]),
                    "synced": datetime.date.today().isoformat(), "evidence": evidence},
           "color": {"themes": themes, "tokens": colors},
           "type": {"fonts": [], "families": fams,
                    "groups": [{"name": "Observed", **({"family": next(iter(fams))} if fams else {}),
                                "styles": styles}] if styles else []}}
    for fam, key, single in (("spacing", "spacings", True), ("radius", "radii", True), ("shadow", "shadows", False)):
        rows, seen = [], set()
        for r in draft[key]:
            v = str(r["value"]).strip()
            if v in seen or (single and not LEN_RE.match(v)) or (not single and ("var(" in v or "url(" in v)):
                continue
            seen.add(v)
            rows.append(r)
        if single:
            rows.sort(key=lambda r: num(r["value"]))
        toks = []
        for r in rows[:60]:
            add(toks, fam, str(r["value"]).strip(), todo(r), evid(r))
        if toks:
            out[fam] = {"tokens": toks}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=2)
    return {"themes": len(themes), "colors": len(colors), "typeStyles": len(styles),
            "spacing": len(out.get("spacing", {}).get("tokens", [])), "radius": len(out.get("radius", {}).get("tokens", [])),
            "shadow": len(out.get("shadow", {}).get("tokens", [])), "path": path}


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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crawl", required=True)
    ap.add_argument("--css-root", action="append", default=[], help="REPO-01=/path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--assets", help="thu muc assets cua crawl (mac dinh <out>/assets)")
    ap.add_argument("--emit-tokens", help="ghi tokens.json khoi dau (obs-*, usage TODO) vao duong dan nay")
    ap.add_argument("--name", default="Design System", help="ten system cho --emit-tokens")
    a = ap.parse_args()

    B = defaultdict(Bag)
    X = {"sites": {}, "pairs": [], "components": {}, "type": {}, "fontFaces": {}, "fontLinks": []}
    files, pages = read_crawl(a.crawl, B, X)
    css_vars, scanned = [], {}
    for spec in a.css_root:
        if "=" not in spec or not re.match(r"^REPO-\d{2,}=", spec):
            print("--css-root phai dang REPO-01=/path: %s" % spec, file=sys.stderr)
            return 1
        rid, path = spec.split("=", 1)
        if not os.path.isdir(path):
            print("Khong thay thu muc %s" % path, file=sys.stderr)
            return 1
        scanned[rid] = scan_css(rid, path, B, css_vars)
    if not files and not scanned:
        print("Khong co styles.json nao duoi %s va khong co --css-root" % a.crawl, file=sys.stderr)
        return 1

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
                           "samples": sm[:3], **({"variants": e["variants"]} if e["variants"] else {})}
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
    assets = read_assets(a.assets or os.path.join(a.out, "assets"))

    draft = {
        "note": "OBSERVED data only (crawl computed-style + source CSS). Not a design system. count=0 -> chi thay trong code.",
        "crawlFiles": [os.path.relpath(f, a.crawl) for f in files],
        "cssRoots": scanned,
        "colors": colors,
        "primaryCandidates": prim,
        "fonts": fonts,
        "fontSizes": bare("fontSizes"),
        "fontWeights": bare("fontWeights"),
        "lineHeights": bare("lineHeights"),
        "radii": bare("radii"),
        "spacings": bare("spacings"),
        "heights": bare("heights"),
        "shadows": bare("shadows"),
        "cssVars": css_vars,
        "pages": pages,
        "typeStyles": type_styles,
        "components": components,
        "perSite": per_site,
        "contrast": contrast_rows,
        "fontFaces": list(X["fontFaces"].values()),
        "fontLinks": X["fontLinks"],
        "assets": assets,
    }
    os.makedirs(a.out, exist_ok=True)
    jp = os.path.join(a.out, "tokens-draft.json")
    json.dump(draft, open(jp, "w", encoding="utf8"), ensure_ascii=False, indent=2)

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
    md += tbl("Colors", colors, "hex", 20)
    md += tbl("Fonts", fonts, "family", 8)
    for t, k in (("Font sizes", "fontSizes"), ("Font weights", "fontWeights"), ("Radii", "radii"),
                 ("Spacings (padding)", "spacings"), ("Shadows", "shadows")):
        md += tbl(t, draft[k], "value", 10)
    md += ["## Per site (can tach theme?)", "", "| Site | Primary | Nav bg | Header bg | Body bg | Link |",
           "|---|---|---|---|---|---|"]
    md += ["| %s | %s |" % (s_, " | ".join(str(d[k] or "—") for k in ("primaryCandidate", "navBg", "headerBg",
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
           "- Font link: %s" % (", ".join(X["fontLinks"]) or "—"),
           "- Logo/favicon: %d · icon svg: %d · icon font: %s" % (
               assets["logos"], assets["icons"], ", ".join("%s=%d" % kv for kv in assets["iconFonts"].items()) or "—"), ""]
    open(os.path.join(a.out, "tokens-draft.md"), "w", encoding="utf8").write("\n".join(md))

    res = {"pages": len(pages), "colors": len(colors), "primaryCandidates": [p["hex"] for p in prim[:3]],
           "fonts": len(fonts), "cssVars": len(css_vars), "typeStyles": len(type_styles),
           "components": {k: v["count"] for k, v in components.items()},
           "contrastFail45": sum(1 for e in contrast_rows if not e["pass45"]),
           "assets": {"logos": assets["logos"], "icons": assets["icons"]}, "out": jp}
    if a.emit_tokens:
        res["emitted"] = emit_tokens(draft, a.emit_tokens, a.name)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
