#!/usr/bin/env python3
"""Gate V-DS — kiem tra O4 04_DesignSystem/ (dung template, khong bia token).

  python3 verify-design-system.py <ver>/04_DesignSystem \
          --draft <_internal>/recon/design/tokens-draft.json [--figma-used] \
          [--out <_internal>/gates/v-ds.md]

Checks: 1 du file · 2 tokens.json hop le + giu key template · 3 khong con placeholder template
(TBD/UNKNOWN tran -> WARN) · 4 moi hex trong tokens.json + moi *.md (foundation/components/README/
platform-*) co trong draft ·
5 font family co trong draft · 6 README trang thai DRAFT · 7 README co nguon WEB-xx hoac Figma ·
8 anh refs/ duoc tham chieu ton tai.
Mau/font ngoai draft chi duoc WARN khi --figma-used VA README ghi Figma la nguon.
Exit: 0 PASS · 1 FAIL
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_report import Gate  # noqa: E402

TEMPLATE_TOKENS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "..", "..", "sys-agent", "design-system-template", "tokens.json")
FALLBACK_KEYS = ["project", "status", "source", "font", "color", "spacing", "radius", "shadow", "platforms"]
GENERIC_FONTS = {"sans-serif", "serif", "monospace", "system-ui", "cursive", "fantasy", "ui-sans-serif",
                 "ui-serif", "ui-monospace", "-apple-system", "blinkmacsystemfont", "inherit", "initial"}

PLACEHOLDER_RES = [
    re.compile(r"<(?!br\s*/?>|/?(?:b|i|u|sub|sup|code|kbd)>|!--)[^<>\n]{1,80}>"),  # <Ten du an> · <hex> · <…>
    re.compile(r"\{\{[^}\n]*\}\}"),                                                # {{...}}
    re.compile(r"#(?:…|\.\.\.|X{3,8}\b)"),                                         # #…… · #XXXXXX
]
TBD_RE = re.compile(r"\b(TBD|UNKNOWN)\b")
TBD_OK_RE = re.compile(r"\b(?:TBD|UNKNOWN)\b\s*(?:[(:—–]|-\s)\s*\S{2,}|—\s*\S+\s+\S+")
HEX_RE = re.compile(r"(?<![\w&])#([0-9A-Fa-f]{8}|[0-9A-Fa-f]{6})\b|`#([0-9A-Fa-f]{3})`")
RGB_RE = re.compile(r"rgba?\(\s*(\d{1,3})[\s,]+(\d{1,3})[\s,]+(\d{1,3})")
REFS_RE = re.compile(r"(?<![\w/])refs/[^\s)\]'\"`|>]+")


def read(p):
    return open(p, encoding="utf8").read()


def hexes(text):
    out = set()
    for m in HEX_RE.finditer(text):
        h = m.group(1) or "".join(c * 2 for c in m.group(2))
        out.add("#" + h[:6].upper())
    for m in RGB_RE.finditer(text):
        out.add("#%02X%02X%02X" % tuple(int(x) for x in m.groups()))
    return out


def walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(k, path + "/<key>")
            yield from walk_strings(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, "%s[%d]" % (path, i))
    elif isinstance(obj, str):
        yield path, obj


def font_values(obj, key=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ("family", "fontfamily", "font-family", "families") and isinstance(v, (str, list)):
                for s in ([v] if isinstance(v, str) else v):
                    if isinstance(s, str):
                        yield s
            else:
                yield from font_values(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from font_values(v, key)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ds_dir")
    ap.add_argument("--draft", required=True)
    ap.add_argument("--figma-used", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    d = a.ds_dir
    g = Gate("Gate V-DS — Design System (%s)" % d)

    # 1. du file
    req = ["README.md", "foundation.md", "components.md", "tokens.json"]
    missing = [f for f in req if not os.path.isfile(os.path.join(d, f))]
    platforms = sorted(glob.glob(os.path.join(d, "platform-*.md")))
    if not platforms:
        missing.append("platform-*.md (>=1) — copy template platform.md -> platform-<WEB-xx>.md"
                       + (" (dang con platform.md)" if os.path.isfile(os.path.join(d, "platform.md")) else ""))
    g.check(1, "Du file README/foundation/components/tokens.json/platform-*.md", missing)

    readme = read(os.path.join(d, "README.md")) if os.path.isfile(os.path.join(d, "README.md")) else ""
    mds = {os.path.basename(p): read(p) for p in sorted(glob.glob(os.path.join(d, "*.md")))}

    # 2. tokens.json hop le + giu key template
    tokens, tk_text = None, ""
    try:
        tpl_keys = list(json.load(open(TEMPLATE_TOKENS, encoding="utf8")).keys())
    except (OSError, ValueError):
        tpl_keys = FALLBACK_KEYS
    tp = os.path.join(d, "tokens.json")
    if os.path.isfile(tp):
        tk_text = read(tp)
        try:
            tokens = json.loads(tk_text)
        except ValueError as e:
            g.fail(2, "tokens.json hop le + giu key template", "JSON loi: %s" % e)
    if tokens is not None:
        if not isinstance(tokens, dict):
            g.fail(2, "tokens.json hop le + giu key template", "top-level khong phai object")
            tokens = {}
        else:
            g.check(2, "tokens.json hop le + giu key template", [k for k in tpl_keys if k not in tokens],
                    fmt=lambda k: "thieu key '%s'" % k)
    elif not tk_text:
        g.fail(2, "tokens.json hop le + giu key template", "khong co tokens.json")
        tokens = {}

    # 3. placeholder template / TBD tran
    ph, bare = [], []
    for name, text in mds.items():
        for no, line in enumerate(text.splitlines(), 1):
            if line.startswith("> SOURCE:"):
                continue
            for rx in PLACEHOLDER_RES:
                for m in rx.finditer(line):
                    ph.append("%s#L%d %s" % (name, no, m.group(0)[:40]))
            if TBD_RE.search(line) and not TBD_OK_RE.search(line):
                bare.append("%s#L%d" % (name, no))
    empties = []
    for path, s in walk_strings(tokens):
        for rx in PLACEHOLDER_RES:
            if rx.search(s):
                ph.append("tokens.json%s %s" % (path, s[:40]))
        if TBD_RE.search(s) and not TBD_OK_RE.search(s):
            bare.append("tokens.json%s" % path)
        if s.strip() == "" and not path.endswith("<key>"):
            empties.append("tokens.json%s" % path)
    g.check(3, "Khong con placeholder template (<...>, {{...}}, #……, #XXXXXX)", ph)
    if bare or empties:
        g.warn("3w", "TBD/UNKNOWN khong kem ly do / gia tri rong",
               "; ".join((["TBD tran: " + x for x in bare] + ["rong: " + x for x in empties])[:15]))

    # nguon trong README
    src_lines = [l for l in readme.splitlines() if re.match(r"^\s*[-*]?\s*\**(Nguồn|Nguon|Sources?)\**\s*:", l, re.I)]
    src_text = " ".join(src_lines)
    for rx in PLACEHOLDER_RES:   # placeholder template khong tinh la nguon
        src_text = rx.sub(" ", src_text)
    figma_src = bool(re.search(r"figma", src_text, re.I))
    figma_ok = a.figma_used and figma_src

    # draft
    draft = None
    try:
        draft = json.load(open(a.draft, encoding="utf8"))
    except (OSError, ValueError) as e:
        g.fail(4, "Mau co trong tokens-draft (chong bia)", "khong doc duoc draft: %s" % e)
        g.fail(5, "Font co trong tokens-draft (chong bia)", "khong doc duoc draft")

    if draft is not None:
        # 4. mau
        draft_hex = {c["hex"].upper() for c in draft.get("colors", [])}
        used = {}
        for label, text in [("tokens.json", json.dumps(tokens, ensure_ascii=False))] + \
                [(n, t) for n, t in mds.items()
                 if n in ("foundation.md", "components.md", "README.md") or n.startswith("platform")]:
            for h in hexes(text):
                used.setdefault(h, []).append(label)
        bad = ["%s (%s)" % (h, ",".join(sorted(set(v)))) for h, v in sorted(used.items()) if h not in draft_hex]
        if bad and figma_ok:
            g.warn(4, "Mau co trong tokens-draft (chong bia)", "ngoai draft, chap nhan vi nguon Figma — doi chieu Figma: " + "; ".join(bad[:15]))
        else:
            g.check(4, "Mau co trong tokens-draft (chong bia)", bad)

        # 5. font
        names = set()
        for f in draft.get("fonts", []):
            for n in f.get("names") or [x.strip().strip("'\"") for x in f.get("family", "").split(",")]:
                names.add(n.lower())
        badf = []
        for stack in font_values(tokens):
            for n in [x.strip().strip("'\"") for x in stack.split(",") if x.strip()]:
                if n.lower() in GENERIC_FONTS or TBD_RE.search(n):
                    continue
                if n.lower() not in names:
                    badf.append(n)
        badf = sorted(set(badf))
        if badf and figma_ok:
            g.warn(5, "Font co trong tokens-draft (chong bia)", "ngoai draft, chap nhan vi nguon Figma: " + ", ".join(badf))
        else:
            g.check(5, "Font co trong tokens-draft (chong bia)", badf)

    # 6. trang thai DRAFT
    st = [l for l in readme.splitlines() if re.search(r"Trạng thái|Trang thai|Status", l, re.I)]
    probs = []
    if not st:
        probs.append("README khong co dong Trang thai")
    elif not any("DRAFT" in l for l in st) or any("APPROVED" in l for l in st):
        probs.append("README: '%s' (AI chi duoc ghi DRAFT)" % st[0].strip()[:60])
    if isinstance(tokens, dict) and tokens.get("status") not in (None, "DRAFT"):
        probs.append("tokens.json status=%s" % tokens.get("status"))
    g.check(6, "Trang thai DRAFT (AI khong tu APPROVED)", probs)

    # 7. nguon co WEB-xx hoac Figma
    if not src_lines:
        g.fail(7, "README ghi nguon, co website (WEB-xx) hoac Figma", "khong co dong 'Nguon:'")
    elif not (re.search(r"\bWEB-\d{2,}\b", src_text) or figma_src):
        g.fail(7, "README ghi nguon, co website (WEB-xx) hoac Figma",
               "chi co nguon khac (source code?) — DS khong duoc dung tu code mot minh")
    else:
        g.ok(7, "README ghi nguon, co website (WEB-xx) hoac Figma")
    if isinstance(tokens, dict) and not tokens.get("source"):
        g.warn("7w", "tokens.json source rong", "nen liet ke WEB-xx / Figma / REPO-xx")

    # 8. refs/
    badr = []
    for name, text in mds.items():
        for m in REFS_RE.finditer(text):
            ref = m.group(0).rstrip(".,;:")
            if not os.path.isfile(os.path.join(d, ref)):
                badr.append("%s -> %s" % (name, ref))
    g.check(8, "Anh refs/ duoc tham chieu ton tai", sorted(set(badr)))

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
