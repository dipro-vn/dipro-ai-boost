#!/usr/bin/env python3
"""Gom design token QUAN SAT DUOC (crawl styles.json + bien CSS trong source) -> tokens-draft.

  python3 extract-design-tokens.py --crawl <_internal>/recon/crawl \
          [--css-root REPO-01=/path/to/fe ...] --out <_internal>/recon/design

Input : moi */styles.json duoi --crawl (do crawl-site.js ghi); --css-root (lap lai duoc) quet
        .css/.scss/.sass/.less/.vue/.tsx/.jsx + tailwind.config.(js|ts|cjs) tim custom property,
        bien SCSS/LESS, mau theme tailwind, font-family (bo qua node_modules/dist/build/vendor).
Output: tokens-draft.json (colors · primaryCandidates · fonts · fontSizes · fontWeights · radii ·
        spacings · shadows · cssVars · pages) va tokens-draft.md (bang tom tat cho nguoi doc).
Chi ghi du lieu QUAN SAT DUOC — script khong tu dat ra token. verify-design-system.py doi chieu file nay.
Khong ghi gi vao repo duoc phan tich.
"""
import argparse
import colorsys
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
def read_crawl(root, B):
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
                    B["colors"].add(c[0], n, role, src, {"alpha": c[1]} if c[1] < 1 else None)

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
                    B["colors"].add(c[0], 1, "button-bg", src)
                    B["buttonBg"].add(c[0], 1, None, src)
                col(b.get("color"), "button-text")
                bc = parse_color(b.get("border")) if b.get("border") and not str(b.get("border")).startswith("0px") else None
                if bc:
                    B["colors"].add(bc[0], 1, "button-border", src)
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
            for v, n in (p.get("shadowFreq") or {}).items():
                B["shadows"].add(v, n, "element", src)
            for v, n in (p.get("fontFreq") or {}).items():
                B["fonts"].add(v, n, None, src)
    return files, pages


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
                            B["colors"].add(c[0], 0, "theme:" + name, src, {"codeNames": "tailwind:" + name})
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
                                    B["colors"].add(c[0], 0, None, src, {"codeNames": name})
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
    a = ap.parse_args()

    B = defaultdict(Bag)
    files, pages = read_crawl(a.crawl, B)
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
    }
    os.makedirs(a.out, exist_ok=True)
    jp = os.path.join(a.out, "tokens-draft.json")
    json.dump(draft, open(jp, "w", encoding="utf8"), ensure_ascii=False, indent=2)

    def tbl(title, rows, key, n=12):
        L = ["## %s" % title, "", "| %s | Count | Roles | Sources |" % key.capitalize(), "|---|---|---|---|"]
        for r in rows[:n]:
            src = ", ".join(r["sources"][:3]) + (" ..." if len(r["sources"]) > 3 else "")
            val = r[key] + (" (alpha %s)" % "/".join(map(str, r["alpha"])) if r.get("alpha") else "")
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
    open(os.path.join(a.out, "tokens-draft.md"), "w", encoding="utf8").write("\n".join(md))

    print(json.dumps({"pages": len(pages), "colors": len(colors), "primaryCandidates": [p["hex"] for p in prim[:3]],
                      "fonts": len(fonts), "cssVars": len(css_vars), "out": jp}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
