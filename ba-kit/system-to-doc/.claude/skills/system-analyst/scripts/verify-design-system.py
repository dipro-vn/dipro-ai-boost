#!/usr/bin/env python3
"""Gate V-DS — O4 Design System dung chuan design-system-format.md (= format artifact "Design System").

  python3 verify-design-system.py <ver>/04_DesignSystem \
          --draft <_internal>/recon/design/tokens-draft.json [--figma-used] [--approved-by "<ten nguoi duyet>"] \
          [--published-url https://claude.ai/artifact/<id>] [--out <_internal>/gates/v-ds.md]

Tham so dau = thu muc CHUA STATUS.md + project/ (project/design-system.json, tokens.json, README.md, components/...).
Checks: 1 du file (STATUS.md + project/, Cover tran, khong con _Example) · 2 index design-system.json ·
3 grammar tokens.json · 4 usage that (khong TODO, khong ten obs-) · 5 chong bia (mau/font phai co trong draft;
spacing/radius/shadow ngoai draft -> WARN) · 6 meta.source ⊆ figma|screens|docs|code|website + synced ·
7 README brand book (khong muc "Chua dong bo") · 8 components (README, preview @dsCard, bundle.js, index.d.ts) ·
9 cover · 10 assets · 11 contrast (WARN) · 12 link artifact trong STATUS.md (khi co --published-url) ·
13 STATUS.md (muc §8, Trang thai DRAFT|TBD; APPROVED chi khi --approved-by) · 14 token vai tro §3.3 co hoac
nam trong STATUS.md Thieu (TBD) · 15 type D4 (Heading/Text, >=4 style, sample+usage) · 16 component §5 co hoac TBD.
Danh sach bat buoc: ds_roles.py. Mau/font ngoai draft chi WARN khi --figma-used VA meta.source chua "figma".
Exit: 0 PASS · 1 FAIL
"""
import argparse
import datetime
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_report import Gate  # noqa: E402
import ds_roles as R_  # noqa: E402

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
JS_ID_RE = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
FN_RE = re.compile(r"^(rgb|rgba|hsl|hsla|oklch|oklab|lab|lch|color)\(([^()]*)\)$", re.I)
ARG_RE = re.compile(r"^-?(\d+\.?\d*|\.\d+)(%|deg|rad|grad|turn)?$|^none$", re.I)
ALIAS_RE = re.compile(r"^\{([^{}]+)\}$")
LEN_RE = re.compile(r"^-?(\d+\.?\d*|\.\d+)(px|rem|em|%)?$|^0$")
WEIGHT_RE = re.compile(r"^\d{1,4}( \d{1,4})?$")
BAD_STACK = re.compile(r"[;{}<>\\()]")
PLAIN_CSS = re.compile(r"^[A-Za-z0-9 #%(),./+_-]{1,200}$")
MARKER_RE = re.compile(r"^\s*<!--\s*@dsCard\b(.*?)-->\s*$")
FORBID_TAG = re.compile(r"<\s*(iframe|frame|object|embed|portal|noscript)\b", re.I)
PLACEHOLDER = re.compile(r"\bTODO\b|\bTBD\b|\{\{[^}\n]*\}\}|lorem ipsum|\bobs-[a-z]+-\d+\b", re.I)
URL_RE = re.compile(r"^https://claude\.ai/(code/)?artifact/[A-Za-z0-9_-]+/?$")
TOP_SCALAR = {"name", "version", "meta", "description", "$schema"}
GENERIC_FONTS = {"sans-serif", "serif", "monospace", "system-ui", "cursive", "fantasy", "ui-sans-serif",
                 "ui-serif", "ui-monospace", "-apple-system", "blinkmacsystemfont", "inherit", "initial",
                 "emoji", "math", "fangsong", "ui-rounded"}
NON_COMP = {"Cover", "lib", "src", "_Example"}
NOT_SYNCED = re.compile(r"^##+\s*(chua dong bo|not synced)", re.M)
CAP_OTHER = 60


def read(p):
    return open(p, encoding="utf8", errors="replace").read()


def is_color(v):
    if not isinstance(v, str):
        return False
    v = v.strip()
    if HEX_RE.match(v):
        return True
    m = FN_RE.match(v)
    if not m:
        return False
    args = [x for x in re.split(r"[\s,/]+", m.group(2).strip()) if x]
    if m.group(1).lower() == "color" and args and re.match(r"^[a-z][a-z0-9-]*$", args[0], re.I):
        args = args[1:]
    return bool(args) and all(ARG_RE.match(x) for x in args)


def to_rgba(v):
    """-> ('#rrggbb', alpha) cho hex/rgb()/hsl(); None neu khong doi duoc (oklch...)."""
    v = v.strip()
    if HEX_RE.match(v):
        h = v[1:].lower()
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        return "#" + h[:6], (int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)
    m = FN_RE.match(v)
    if not m:
        return None
    fn = m.group(1).lower()
    args = [x for x in re.split(r"[\s,/]+", m.group(2).strip()) if x]

    def alpha(i):
        if len(args) <= i:
            return 1.0
        x = args[i]
        return float(x[:-1]) / 100 if x.endswith("%") else float(x)
    try:
        if fn in ("rgb", "rgba"):
            rgb = [round(float(x[:-1]) * 2.55) if x.endswith("%") else round(float(x)) for x in args[:3]]
            return "#%02x%02x%02x" % tuple(rgb), alpha(3)
        if fn in ("hsl", "hsla"):
            import colorsys
            h, s_, li = float(args[0].rstrip("deg")) / 360, float(args[1].rstrip("%")) / 100, float(args[2].rstrip("%")) / 100
            r, g, b = colorsys.hls_to_rgb(h, li, s_)
            return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255)), alpha(3)
    except (ValueError, IndexError):
        return None
    return None


def lum(h):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def blend(c, bg):
    hx, a = c
    if a >= 1:
        return hx
    return "#" + "".join("%02x" % round(int(hx[i:i + 2], 16) * a + int(bg[i:i + 2], 16) * (1 - a)) for i in (1, 3, 5))


def ratio(fg, bg):
    b = blend(bg, "#ffffff")
    f = blend(fg, b)
    l1, l2 = sorted((lum(f), lum(b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def first_family(stack):
    return (stack or "").split(",")[0].strip().strip("'\"")


def marker(path):
    """-> (attrs dict, text) hoac (None, text)."""
    text = read(path)
    first = text.split("\n", 1)[0]
    m = MARKER_RE.match(first)
    if not m:
        return None, text
    kv = r"([A-Za-z]+)=(?:\"([^\"]*)\"|([^\s\"]+))"
    attrs = {k: (x or y) for k, x, y in re.findall(kv, m.group(1))}
    for w in re.sub(kv, " ", m.group(1)).split():
        attrs.setdefault(w, True)   # co khong gia tri: floor, page
    return attrs, text


def fold(x):
    """bo dau tieng Viet + thuong (so khop tieu de / nhan)."""
    x = unicodedata.normalize("NFD", str(x).replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in x if not unicodedata.combining(c)).lower().strip()


def read_status(path):
    """-> {lines: {trang thai, artifact, nguon}, heads: [..], tbd: set(ten)} hoac None."""
    if not os.path.isfile(path):
        return None
    text = read(path)
    lines = {}
    for raw in text.splitlines():
        m = re.match(r"^\s*[-*]\s*([^:]{1,40}):\s*(.*)$", raw)
        if m and fold(m.group(1)) not in lines:
            lines[fold(m.group(1))] = m.group(2).strip()
    heads = [fold(h) for h in re.findall(r"^##\s+(.+?)\s*$", text, re.M)]
    tbd, sec = set(), None
    for raw in text.splitlines():
        if raw.startswith("## "):
            sec = fold(raw[3:])
            continue
        if sec and sec.startswith("thieu") and raw.strip().startswith("|"):
            cells = [c.strip() for c in raw.strip().strip("|").split("|")]
            if len(cells) < 2 or set(cells[0]) <= set("-: ") or fold(cells[1]).startswith("token"):
                continue
            tbd |= set(re.findall(r"[A-Za-z][A-Za-z0-9_.<>-]*", cells[1]))
    return {"text": text, "lines": lines, "heads": heads, "tbd": tbd}


def height_ok(attrs, lo, hi):
    try:
        return lo <= int(str(attrs.get("height"))) <= hi
    except (TypeError, ValueError):
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ds_dir", help="thu muc 04_DesignSystem (chua project/)")
    ap.add_argument("--draft", required=True)
    ap.add_argument("--figma-used", action="store_true")
    ap.add_argument("--published-url")
    ap.add_argument("--approved-by", help="ten nguoi da duyet (cho phep Trang thai APPROVED)")
    ap.add_argument("--out")
    a = ap.parse_args()
    P = os.path.join(a.ds_dir, "project")
    g = Gate("Gate V-DS — Design System (%s)" % a.ds_dir)

    def pj(*x):
        return os.path.join(P, *x)

    # 1. du file + Cover tran + khong con _Example
    req = ["design-system.json", "tokens.json", "README.md", "components/Cover/preview.html"]
    bad = ["thieu project/%s" % f for f in req if not os.path.isfile(pj(f))]
    stat = read_status(os.path.join(a.ds_dir, "STATUS.md"))
    if stat is None:
        bad.append("thieu 04_DesignSystem/STATUS.md (trang thai, link artifact, Thieu TBD — thay link.md)")
    for f in ("README.md", "Cover.d.ts"):
        if os.path.exists(pj("components", "Cover", f)):
            bad.append("components/Cover/%s lam Cover thanh component thuong (giu thu muc tran)" % f)
    if os.path.exists(pj("components", "_Example")):
        bad.append("con components/_Example/ cua template (xoa truoc khi publish)")
    g.check(1, "Du file STATUS.md + project/ (design-system.json, tokens.json, README.md, Cover tran, khong _Example)", bad)
    if os.path.exists(os.path.join(a.ds_dir, "link.md")):
        g.warn("1w", "link.md la layout cu", "chuyen link vao STATUS.md dong '- Artifact:' roi xoa link.md")
    tbd = stat["tbd"] if stat else set()

    # 2. index
    idx, bad, warn = {}, [], []
    if os.path.isfile(pj("design-system.json")):
        try:
            idx = json.load(open(pj("design-system.json"), encoding="utf8"))
        except ValueError as e:
            bad.append("JSON loi: %s" % e)
    if not isinstance(idx, dict):
        bad.append("top-level khong phai object")
        idx = {}
    has_bundle = os.path.isfile(pj("components", "bundle.js"))
    if idx:
        if idx.get("v") != 3:
            bad.append("v=%r (phai 3)" % idx.get("v"))
        if idx.get("layout") != "files":
            bad.append("layout=%r (phai 'files')" % idx.get("layout"))
        cof = idx.get("createdOnFiles")
        if isinstance(cof, dict):
            if cof.get("v") != 1 or not ISO_RE.match(str(cof.get("at", ""))):
                bad.append("createdOnFiles phai {v:1, at: ISO-8601}")
        elif not isinstance(idx.get("convertedFrom"), dict):
            bad.append("thieu marker createdOnFiles (hoac convertedFrom)")
        if not str(idx.get("title") or "").strip():
            bad.append("title rong")
        if not JS_ID_RE.match(str(idx.get("namespace") or "")):
            bad.append("namespace %r khong phai JS identifier" % idx.get("namespace"))
        libs = idx.get("libraries")
        if not isinstance(libs, list):
            bad.append("libraries phai la list")
        elif has_bundle:
            have = {(x.get("name"), str(x.get("version"))) for x in libs if isinstance(x, dict)}
            for n in ("react", "react-dom"):
                if not any(h[0] == n and h[1].startswith("18") for h in have):
                    bad.append("co bundle.js nhung libraries thieu %s 18" % n)
        groups = idx.get("groups")
        if not isinstance(groups, list):
            bad.append("groups phai la list")
            groups = []
        ag = idx.get("assetGroups")
        if not isinstance(ag, dict):
            bad.append("assetGroups phai la object")
            ag = {}
        for gn, gv in ag.items():
            if gn not in groups:
                bad.append("assetGroups.%s khong co trong groups" % gn)
            if not isinstance(gv, dict) or gv.get("name") != gn or not isinstance(gv.get("order", []), list) \
                    or not isinstance(gv.get("files", {}), dict):
                bad.append("assetGroups.%s phai {name, tile?, order:[], files:{}}" % gn)
                continue
            for fk, fr in gv.get("files", {}).items():
                if not isinstance(fr, dict) or not all(k in fr for k in ("name", "size", "type")):
                    bad.append("assetGroups.%s.files.%s thieu name/size/type" % (gn, fk))
                elif not fr.get("blob"):
                    warn.append("%s/%s chua upload (khong co blob)" % (gn, fk))
        for k in ("sections", "blobs"):
            if not isinstance(idx.get(k), dict):
                bad.append("%s phai la {}" % k)
        docs = idx.get("docs")
        if not isinstance(docs, dict) or docs.get("readme") != "project/README.md" \
                or not isinstance(docs.get("sections"), list):
            bad.append('docs phai {"readme":"project/README.md","sections":[...]}')
        lc = idx.get("lastChange")
        if not isinstance(lc, dict) or not lc.get("by") or not lc.get("via") or not ISO_RE.match(str(lc.get("at", ""))):
            bad.append("lastChange phai {by, at ISO-8601, via}")
    elif not bad:
        bad.append("khong co design-system.json")
    g.check(2, "Index design-system.json dung shape (v3, files, marker, namespace, assetGroups, lastChange)", bad)
    if warn:
        g.warn("2w", "Asset chua upload len artifact", "; ".join(warn[:15]))
    ns = str(idx.get("namespace") or "")
    title = str(idx.get("title") or "")

    # 3. grammar tokens.json
    tk, bad = {}, []
    if os.path.isfile(pj("tokens.json")):
        try:
            tk = json.load(open(pj("tokens.json"), encoding="utf8"))
        except ValueError as e:
            bad.append("JSON loi: %s" % e)
    if not isinstance(tk, dict):
        bad.append("top-level khong phai object")
        tk = {}
    color = tk.get("color") if isinstance(tk.get("color"), dict) else {}
    if "color" in tk and not isinstance(tk.get("color"), dict):
        bad.append("color phai la object {themes, tokens}")
    themes = color.get("themes") or []
    theme_ids = []
    if not isinstance(themes, list) or not 1 <= len(themes) <= 8:
        bad.append("color.themes phai 1-8 theme")
        themes = themes if isinstance(themes, list) else []
    for t in themes:
        tid = t.get("id") if isinstance(t, dict) else None
        if not isinstance(tid, str) or not NAME_RE.match(tid):
            bad.append("theme id khong hop le: %r" % tid)
        else:
            theme_ids.append(tid)
    ctoks = color.get("tokens", [])
    if not isinstance(ctoks, list):
        bad.append("color.tokens phai la LIST (map DTCG khong doc duoc)")
        ctoks = []
    if len(ctoks) > 600:
        bad.append("qua 600 mau (%d)" % len(ctoks))
    families = {}   # family -> token list
    families["color"] = [t for t in ctoks if isinstance(t, dict)]
    for k, v in tk.items():
        if k in TOP_SCALAR or k in ("color", "type"):
            continue
        if not isinstance(v, dict) or not isinstance(v.get("tokens"), list):
            bad.append("family '%s' phai {tokens:[...]} (map name->value DTCG = page khong doc duoc)" % k)
            continue
        if len(v["tokens"]) > CAP_OTHER:
            bad.append("family %s qua %d token (%d)" % (k, CAP_OTHER, len(v["tokens"])))
        families[k] = [t for t in v["tokens"] if isinstance(t, dict)]
        if len(families[k]) != len(v["tokens"]):
            bad.append("family %s co phan tu khong phai object" % k)
    if len([k for k in families if k not in ("color", "spacing", "radius", "shadow")]) > 12:
        bad.append("qua 12 family phu")
    names = {}
    for fam, toks in families.items():
        for t in toks:
            n = t.get("name")
            if not isinstance(n, str) or not NAME_RE.match(n):
                bad.append("%s: ten khong hop le %r" % (fam, n))
                continue
            if n in names:
                bad.append("ten trung '%s' (%s va %s)" % (n, names[n], fam))
            names[n] = fam
    cnames = {t.get("name") for t in families["color"]}
    cval = {t.get("name"): t.get("value") for t in families["color"]}

    def alias_of(v):
        m = ALIAS_RE.match(v.strip()) if isinstance(v, str) else None
        return m.group(1) if m else None

    def resolve(n, theme, seen=()):
        """-> literal hoac None (alias hong/vong)."""
        if n in seen or len(seen) > 16 or n not in cval:
            return None
        v = cval[n]
        if isinstance(v, dict):
            v = v.get(theme, v.get(theme_ids[0] if theme_ids else "", None))
        if not isinstance(v, str):
            return None
        al = alias_of(v)
        return resolve(al, theme, seen + (n,)) if al else v
    for t in families["color"]:
        n, v = t.get("name"), t.get("value")
        vals = v.items() if isinstance(v, dict) else [(None, v)]
        if isinstance(v, dict):
            extra = [k for k in v if k not in theme_ids]
            if extra:
                bad.append("%s: key theme la %s" % (n, ",".join(extra)))
        good = 0
        for th, x in vals:
            al = alias_of(x)
            if al:
                if al not in cnames:
                    bad.append("%s: alias {%s} toi token mau khong ton tai" % (n, al))
                elif resolve(n, th or (theme_ids[0] if theme_ids else "")) is None:
                    bad.append("%s: alias vong / qua sau" % n)
                else:
                    good += 1
            elif is_color(x):
                good += 1
            else:
                bad.append("%s: gia tri mau khong hop le %r" % (n, x))
        if not good:
            bad.append("%s: khong co gia tri hop le o theme nao" % n)
    for fam in ("spacing", "radius"):
        for t in families.get(fam, []):
            if not LEN_RE.match(str(t.get("value", "")).strip()):
                bad.append("%s %s: do dai khong hop le %r" % (fam, t.get("name"), t.get("value")))
    for t in families.get("shadow", []):
        v = t.get("value")
        for th, x in (v.items() if isinstance(v, dict) else [(None, v)]):
            if not isinstance(x, str) or len(x) > 400 or re.search(r"var\(|url\(", x):
                bad.append("shadow %s: gia tri khong hop le %r" % (t.get("name"), x))
            if th and th not in theme_ids:
                bad.append("shadow %s: key theme la %s" % (t.get("name"), th))
    for fam, toks in families.items():
        if fam in ("color", "spacing", "radius", "shadow"):
            continue
        for t in toks:
            x = str(t.get("value", ""))
            if not PLAIN_CSS.match(x) or re.search(r"url\(|var\(", x) or x.count("(") != x.count(")"):
                bad.append("%s %s: gia tri CSS khong hop le %r" % (fam, t.get("name"), x))
    typ = tk.get("type", {"fonts": [], "families": {}, "groups": []})
    styles = []
    fam_keys = {}
    if not isinstance(typ, dict):
        bad.append("type phai la object")
        typ = {}
    else:
        if not isinstance(typ.get("fonts", []), list) or len(typ.get("fonts", [])) > 40:
            bad.append("type.fonts phai list <=40")
        for f in typ.get("fonts", []) if isinstance(typ.get("fonts", []), list) else []:
            if not isinstance(f, dict) or not f.get("family") or re.search(r"[\"']", str(f.get("family"))):
                bad.append("type.fonts: family phai ten tran %r" % f)
            elif f.get("file"):
                fp = f["file"] if "/" in f["file"] else "fonts/" + f["file"]
                if not os.path.isfile(pj(fp)):
                    bad.append("type.fonts: thieu file %s" % fp)
        fam_keys = typ.get("families", {})
        if not isinstance(fam_keys, dict) or len(fam_keys) > 12:
            bad.append("type.families phai object <=12 key")
            fam_keys = {}
        for k, v in fam_keys.items():
            if not NAME_RE.match(k):
                bad.append("type.families key khong hop le %r" % k)
            if not isinstance(v, str) or len(v) > 200 or BAD_STACK.search(v) \
                    or v.count('"') % 2 or v.count("'") % 2:
                bad.append("type.families.%s: stack khong hop le" % k)
        grps = typ.get("groups", [])
        if not isinstance(grps, list) or len(grps) > 12:
            bad.append("type.groups phai list <=12")
            grps = []
        snames = set()
        for gr in grps:
            if not isinstance(gr, dict) or not isinstance(gr.get("styles"), list):
                bad.append("type.groups: moi group {name, family?, styles:[...]}")
                continue
            if gr.get("family") and gr["family"] not in fam_keys:
                bad.append("group %s: family '%s' khong co trong type.families" % (gr.get("name"), gr["family"]))
            for st in gr["styles"]:
                if not isinstance(st, dict):
                    bad.append("type style khong phai object")
                    continue
                styles.append(st)
                n = st.get("name")
                if not isinstance(n, str) or not NAME_RE.match(n):
                    bad.append("type style ten khong hop le %r" % n)
                elif n in snames:
                    bad.append("type style trung ten %s" % n)
                snames.add(n)
                if not LEN_RE.match(str(st.get("fontSize", ""))):
                    bad.append("style %s: fontSize khong hop le %r" % (n, st.get("fontSize")))
                lh = st.get("lineHeight")
                if lh is not None and not LEN_RE.match(str(lh)):
                    bad.append("style %s: lineHeight khong hop le %r" % (n, lh))
                fw = st.get("fontWeight")
                if fw is not None:
                    ok = fw in ("normal", "bold") or (isinstance(fw, (int, float)) and 1 <= fw <= 1000) or \
                        (isinstance(fw, str) and WEIGHT_RE.match(fw) and all(1 <= int(x) <= 1000 for x in fw.split()))
                    if not ok:
                        bad.append("style %s: fontWeight khong hop le %r" % (n, fw))
                if st.get("family") and st["family"] not in fam_keys:
                    bad.append("style %s: family '%s' khong co trong type.families" % (n, st["family"]))
        if len(styles) > 80:
            bad.append("qua 80 type style (%d)" % len(styles))
    g.check(3, "tokens.json dung grammar format.md (list, ten, mau, alias, theme, type, cap)", bad)

    # 4. usage that, khong con ten obs-
    bad = []
    for fam, toks in families.items():
        for t in toks:
            u = str(t.get("usage") or "").strip()
            if not u or u.upper().startswith("TODO"):
                bad.append("%s %s: usage rong/TODO" % (fam, t.get("name")))
            if str(t.get("name", "")).startswith("obs-"):
                bad.append("%s %s: con ten starter obs-" % (fam, t.get("name")))
    for st in styles:
        u = str(st.get("usage") or "").strip()
        if not u or u.upper().startswith("TODO"):
            bad.append("type %s: usage rong/TODO" % st.get("name"))
        if str(st.get("name", "")).startswith("obs-"):
            bad.append("type %s: con ten starter obs-" % st.get("name"))
    for k in fam_keys:
        if k.startswith("obs-"):
            bad.append("type.families %s: con ten starter obs-" % k)
    g.check(4, "Moi token/type style co usage that + da doi ten ngu nghia (khong obs-/TODO)", bad)

    # 5. chong bia
    meta = tk.get("meta") if isinstance(tk.get("meta"), dict) else {}
    source = str(meta.get("source") or "")
    figma_ok = a.figma_used and "figma" in source.lower()
    draft = None
    try:
        draft = json.load(open(a.draft, encoding="utf8"))
    except (OSError, ValueError) as e:
        g.fail(5, "Mau/font co trong tokens-draft (chong bia)", "khong doc duoc draft: %s" % e)
    if draft is not None:
        obs = {}
        for c in draft.get("colors", []):
            obs.setdefault(c["hex"].lower(), set()).update(c.get("alpha") or [1.0])
        badc = []
        for t in families["color"]:
            v = t.get("value")
            for th, x in (v.items() if isinstance(v, dict) else [(None, v)]):
                if not isinstance(x, str) or alias_of(x) or not is_color(x):
                    continue
                c = to_rgba(x)
                if c is None:
                    badc.append("%s=%s (khong doi chieu duoc)" % (t.get("name"), x))
                elif c[0] not in obs or not any(abs(c[1] - al) <= 0.01 for al in obs[c[0]]):
                    badc.append("%s=%s" % (t.get("name"), x))
        names_obs = set()
        for f in draft.get("fonts", []):
            for n in f.get("names") or [x.strip().strip("'\"") for x in f.get("family", "").split(",")]:
                names_obs.add(n.lower())
        for f in draft.get("fontFaces", []):
            names_obs.add(str(f.get("family", "")).lower())
        badf = sorted({first_family(v) for v in fam_keys.values() if isinstance(v, str)
                       and first_family(v).lower() not in GENERIC_FONTS
                       and first_family(v).lower() not in names_obs})
        badall = badc + ["font %s" % f for f in badf]
        if badall and figma_ok:
            g.warn(5, "Mau/font co trong tokens-draft (chong bia)", "ngoai draft, chap nhan vi nguon Figma: "
                   + "; ".join(badall[:15]))
        else:
            g.check(5, "Mau/font co trong tokens-draft (chong bia)", badall)

        def nums(v):   # so sanh long: tap so khac 0 (bo thu tu / dinh dang rgba)
            return tuple(sorted({float(x) for x in re.findall(r"-?\d*\.?\d+", str(v))} - {0.0}))
        dvals = {"spacing": {str(r["value"]).strip() for r in draft.get("spacings", [])},
                 "radius": {str(r["value"]).strip() for r in draft.get("radii", [])}}
        dsh = {nums(r["value"]) for r in draft.get("shadows", [])}
        w = []
        for fam in ("spacing", "radius"):
            for t in families.get(fam, []):
                v = str(t.get("value", "")).strip()
                if v not in dvals[fam] and v not in ("0", "0px"):
                    w.append("%s %s=%s" % (fam, t.get("name"), v))
        for t in families.get("shadow", []):
            v = t.get("value")
            for x in (v.values() if isinstance(v, dict) else [v]):
                if str(x).strip() != "none" and nums(x) not in dsh:
                    w.append("shadow %s=%s" % (t.get("name"), x))
        if w:
            g.warn("5w", "spacing/radius/shadow ngoai draft (doi chieu nguon)", "; ".join(w[:15]))

    # 6. meta.source + synced
    bad = []
    parts = [x.strip().lower() for x in source.split("+")]
    if not source:
        bad.append("thieu meta.source")
    elif not set(parts) <= R_.SOURCES:
        bad.append("meta.source=%r — gia tri ngoai %s (noi bang '+')" % (source, "/".join(sorted(R_.SOURCES))))
    elif not set(parts) & {"website", "figma", "screens"}:
        bad.append("meta.source=%r — DS khong duoc dung tu code/docs mot minh (can website, figma hoac screens)" % source)
    if not DATE_RE.match(str(meta.get("synced") or "")):
        bad.append("meta.synced phai la ngay YYYY-MM-DD")
    g.check(6, "meta.source ⊆ figma/screens/docs/code/website, co website/figma/screens + meta.synced", bad)

    # 7. README brand book
    bad, rm = [], ""
    if os.path.isfile(pj("README.md")):
        rm = read(pj("README.md"))
    if not rm.strip():
        bad.append("README.md rong")
    else:
        secs = len(re.findall(r"^## \S", rm, re.M))
        if secs < 3:
            bad.append("chi %d muc '## ' (can >=3: content, visual foundations, iconography...)" % secs)
        known = set(names) | {st.get("name") for st in styles}
        cited = {x for x in re.findall(r"`([^`\s]+)`", rm) if x in known}
        need = min(5, len(known)) if known else 1
        if len(cited) < need:
            bad.append("README chi nhac %d ten token trong backtick (can >=%d)" % (len(cited), need))
        ph = sorted({m.group(0) for m in PLACEHOLDER.finditer(rm)})
        if ph:
            bad.append("con placeholder: %s" % ", ".join(ph[:8]))
        if NOT_SYNCED.search(fold(rm)):
            bad.append("co muc 'Chua dong bo / Not synced' — token/component thieu ghi vao STATUS.md ## Thieu (TBD)")
    g.check(7, "README brand book (>=3 muc ##, nhac >=5 token, khong TODO, khong muc Chua dong bo)", bad)
    w7 = []
    if rm.lstrip().startswith("# "):
        w7.append("bat dau bang tieu de '# ' (page da hien ten system): %s" % rm.lstrip().split("\n", 1)[0][:60])
    first = re.search(r"^##\s+(.+)$", rm, re.M)
    if len(theme_ids) >= 2 and not (first and re.match(r"^\d+\s+portal\s*=\s*\d+\s+theme", fold(first.group(1)))):
        w7.append("%d theme nhung muc ## dau khong phai '<N> portal = <N> theme'" % len(theme_ids))
    if w7:
        g.warn("7w", "README thu tu muc §4", "; ".join(w7))

    # 8. components
    bad = []
    cdir = pj("components")
    comps = sorted(d for d in os.listdir(cdir) if os.path.isdir(os.path.join(cdir, d)) and d not in NON_COMP) \
        if os.path.isdir(cdir) else []
    for c in comps:
        rp, pp = os.path.join(cdir, c, "README.md"), os.path.join(cdir, c, "preview.html")
        if not os.path.isfile(rp):
            bad.append("%s: thieu README.md" % c)
        else:
            body = re.sub(r"^#\s+.*\n", "", read(rp).lstrip(), count=1).strip()
            if not re.split(r"(?<=[.!?。])\s", body, 1)[0].strip():
                bad.append("%s: README thieu cau tom tat dau" % c)
        if not os.path.isfile(pp):
            bad.append("%s: thieu preview.html" % c)
            continue
        attrs, text = marker(pp)
        if attrs is None:
            bad.append("%s: dong 1 preview khong phai <!-- @dsCard ... -->" % c)
        elif not height_ok(attrs, 40, 4000):
            bad.append("%s: @dsCard height phai 40-4000" % c)
        if FORBID_TAG.search(text):
            bad.append("%s: preview co iframe/frame/object/embed/portal/noscript" % c)
        if ns and "window.%s" % ns not in text and not (attrs and ("floor" in attrs or "page" in attrs)):
            bad.append("%s: preview khong dung window.%s" % (c, ns))
    if comps:
        bj, dts = pj("components", "bundle.js"), pj("components", "index.d.ts")
        if not os.path.isfile(bj):
            bad.append("co component nhung thieu components/bundle.js")
        else:
            b = read(bj)
            if not re.search(r"window\.%s\s*=|window\[['\"]%s['\"]\]\s*=" % (re.escape(ns), re.escape(ns)), b):
                bad.append("bundle.js khong gan window.%s" % ns)
            if re.search(r"</script", b, re.I) or "<!--" in b:
                bad.append("bundle.js chua '</script' hoac '<!--'")
            if re.search(r"^\s*import\s|\brequire\(|\bfetch\(", b, re.M):
                bad.append("bundle.js co import/require/fetch (phai classic script, khong network)")
            miss = [c for c in comps if not re.search(r"\b%s\b" % re.escape(c), b)]
            if miss:
                bad.append("component khong co trong bundle.js: %s" % ", ".join(miss))
        if not os.path.isfile(dts):
            bad.append("thieu components/index.d.ts")
        else:
            d = read(dts)
            l1 = next((x.strip() for x in d.splitlines() if x.strip()), "")
            if not (l1.startswith(("//", "/*")) and ns and ns in l1):
                g.warn("8w", "index.d.ts dong 1 phai la chu thich namespace + cach doi theme", l1[:80])
            miss = [c for c in comps if not re.search(r"\b%s\b" % re.escape(c), d)]
            if miss:
                bad.append("component khong co trong index.d.ts: %s" % ", ".join(miss))
    g.check(8, "Components: README + preview @dsCard + bundle.js/index.d.ts khop (%d component)" % len(comps), bad)

    # 9. cover
    bad = []
    cp = pj("components", "Cover", "preview.html")
    if os.path.isfile(cp):
        attrs, text = marker(cp)
        if attrs is None:
            bad.append("dong 1 khong phai <!-- @dsCard ... -->")
        elif not height_ok(attrs, 240, 360):
            bad.append("@dsCard height phai 240-360")
        n_svg = len(re.findall(r"<svg\b", text, re.I))
        if n_svg != 1:
            bad.append("phai dung 1 <svg> (co %d)" % n_svg)
        if re.search(r"<img\b", text, re.I):
            bad.append("cover khong duoc co <img>")
        if title and title not in text and title.replace("&", "&amp;") not in text:
            bad.append("cover khong co ten system '%s'" % title)
        if FORBID_TAG.search(text):
            bad.append("cover co iframe/object/...")
    else:
        bad.append("thieu components/Cover/preview.html")
    g.check(9, "Cover: @dsCard 240-360, 1 svg, co ten system, khong img", bad)

    # 10. assets
    bad, warn = [], []
    ag = idx.get("assetGroups") if isinstance(idx.get("assetGroups"), dict) else {}
    for gn, gv in ag.items():
        files = (gv or {}).get("files") or {} if isinstance(gv, dict) else {}
        if files and not os.path.isfile(pj("assets", gn, "README.md")):
            bad.append("thieu assets/%s/README.md" % gn)
        for fk, fr in files.items():
            nm = fr.get("name", fk) if isinstance(fr, dict) else fk
            if ".." in nm or nm.startswith("/") or "\\" in nm:
                bad.append("%s: ten file khong an toan %r" % (gn, nm))
            elif not os.path.isfile(pj("assets", gn, nm)):
                bad.append("assets/%s/%s khong co file local" % (gn, nm))
    adir = pj("assets")
    if os.path.isdir(adir):
        for gn in sorted(os.listdir(adir)):
            gp = os.path.join(adir, gn)
            if not os.path.isdir(gp):
                continue
            gv = ag.get(gn) if isinstance(ag.get(gn), dict) else {}
            rec = {(fr.get("name") if isinstance(fr, dict) else k)
                   for k, fr in (gv.get("files") if isinstance(gv.get("files"), dict) else {}).items()}
            for root, _, fns in os.walk(gp):
                for fn in fns:
                    rel = os.path.relpath(os.path.join(root, fn), gp).replace(os.sep, "/")
                    if not fn.lower().endswith((".md", ".json", ".csv", ".txt")) and rel not in rec:
                        warn.append("assets/%s/%s chua ghi vao assetGroups" % (gn, rel))
    g.check(10, "Assets: moi group co README.md, moi file trong index co file local", bad)
    if warn:
        g.warn("10w", "File asset local chua co trong index", "; ".join(warn[:15]))

    # 11. contrast (WARN)
    fg_re, bg_re = re.compile(r"text|ink|(^|-)on-", re.I), re.compile(r"surface|bg|background|page", re.I)
    fgs = [t for t in families["color"] if fg_re.search(str(t.get("name", "")))]
    bgs = [t for t in families["color"] if bg_re.search(str(t.get("name", ""))) and t not in fgs]
    low = []
    for f in fgs:
        u = str(f.get("usage") or "")
        if re.search(r"\d+(\.\d+)?\s*:\s*1", u):
            continue
        named = [b for b in bgs if b.get("name") in u]
        for b in (named or bgs):
            for th in theme_ids or [""]:
                fv, bv = resolve(f.get("name"), th), resolve(b.get("name"), th)
                fc, bc = (to_rgba(fv) if fv else None), (to_rgba(bv) if bv else None)
                if fc and bc:
                    r = ratio(fc, bc)
                    if r < 4.5:
                        low.append("%s/%s [%s] %.2f:1" % (f.get("name"), b.get("name"), th, r))
    if low:
        g.warn(11, "Contrast chu/nen < 4.5:1 ma usage khong ghi ty le", "; ".join(low[:15]))
    else:
        g.ok(11, "Contrast chu/nen >= 4.5:1 (hoac usage da ghi ty le)")

    # 12. link publish
    if a.published_url:
        bad = []
        if not URL_RE.match(a.published_url.strip()):
            bad.append("URL khong dang https://claude.ai/(code/)artifact/<id>")
        art = (stat or {}).get("lines", {}).get("artifact", "")
        if a.published_url.strip().rstrip("/") not in art:
            bad.append("STATUS.md dong '- Artifact:' khong chua URL")
        g.check(12, "Link artifact Design System da publish + ghi STATUS.md '- Artifact:'", bad)

    # 13. STATUS.md (§8)
    bad = []
    if stat is None:
        bad.append("khong co STATUS.md")
    else:
        for h in R_.STATUS_HEADINGS:
            if not any(x.startswith(fold(h)) for x in stat["heads"]):
                bad.append("thieu muc '## %s'" % h)
        for k in R_.STATUS_LINES:
            v = stat["lines"].get(fold(k))
            if v is None:
                bad.append("thieu dong '- %s:'" % k)
            elif not v or re.search(r"<[^>]*>|…", v):
                bad.append("dong '- %s:' rong / con placeholder" % k)
        stt = fold(stat["lines"].get("trang thai", "")).upper()
        if stt.startswith("APPROVED"):
            if not a.approved_by:
                bad.append("Trang thai APPROVED nhung khong co --approved-by (agent khong tu duyet)")
        elif not re.match(r"^(DRAFT|TBD)\b", stt):
            bad.append("Trang thai phai DRAFT / TBD: D#... / APPROVED YYYY-MM-DD (nhan: %r)" % stt[:30])
    g.check(13, "STATUS.md dung §8 (muc, Trang thai DRAFT/TBD, Artifact, Nguon)", bad)

    # 14. token vai tro §3.3 (co trong tokens.json hoac ghi TBD)
    bad = []
    for d_, names_ in R_.ROLES:
        miss = [n for n in names_ if n not in names and n not in tbd]
        if miss:
            bad.append("%s: %s" % (d_, ", ".join(miss)))
    for d_, alts in R_.ROLE_ALT:
        if not any(x in names or x in tbd for x in alts):
            bad.append("%s: %s" % (d_, " / ".join(alts)))
    if not any(R_.SPACE_RE.match(n) for n in names) and not any(x.startswith("space") for x in tbd):
        bad.append("D5: khong co space-<px> nao")
    d7 = [n for _, ns_ in R_.ROLES if _ == "D7" for n in ns_]
    if not families.get("size") and not all(n in tbd for n in d7):
        bad.append("D7: thieu family size")
    g.check(14, "Token vai tro §3.3 co trong tokens.json hoac ghi STATUS.md ## Thieu (TBD)", bad)

    # 15. type D4
    bad = []
    if "sans" not in fam_keys and not tbd & {"sans", "families.sans"}:
        bad.append("thieu type.families.sans")
    gnames = {gr.get("name") for gr in (typ.get("groups") or []) if isinstance(gr, dict)} if isinstance(typ, dict) else set()
    for gn in R_.TYPE_GROUPS:
        if gn not in gnames and gn not in tbd:
            bad.append("thieu group %s" % gn)
    if len(styles) < R_.MIN_STYLES and not tbd & set(R_.TYPE_GROUPS):
        bad.append("chi %d type style (can >= %d)" % (len(styles), R_.MIN_STYLES))
    for st_ in styles:
        smp = str(st_.get("sample") or "").strip()
        if not smp or smp.upper().startswith("TODO"):
            bad.append("style %s: thieu sample (nhan UI that)" % st_.get("name"))
    g.check(15, "Type D4: families.sans, group Heading + Text, >= 4 style, moi style co sample", bad)

    # 16. component §5
    miss = [c for c in R_.COMPONENTS if c not in comps and c not in tbd]
    if not any(c in comps or c in tbd for c in R_.COMP_ALT):
        miss.append(" / ".join(R_.COMP_ALT))
    g.check(16, "Component toi thieu §5 co trong components/ hoac ghi STATUS.md ## Thieu (TBD)",
            ["thieu: " + ", ".join(miss)] if miss else [])

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
