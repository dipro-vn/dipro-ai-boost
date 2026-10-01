#!/usr/bin/env python3
"""Gate V-DS self-test: chung minh verify-design-system.py that su bat loi.

  python3 selftest-design-system.py [--keep]

Dung 1 project/ HOP LE (dang artifact Design System: 1 theme, 8 mau, 1 type group, spacing, radius,
Button + Badge co bundle/d.ts/preview, cover, nhom Icons) -> PASS. Sau do tiem tung loi vao ban copy
-> khang dinh dung check do FAIL. Chay lai sau MOI lan sua verify-design-system.py.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

COLORS = [("surface", "#ffffff", "Nen card, header bang, input tren `page-bg`."),
          ("page-bg", "#f5f6fa", "Nen trang ung dung."),
          ("text-high", "#222222", "Chu than va tieu de tren `surface` va `page-bg` (15.9:1)."),
          ("primary", "#0057b8", "Nen nut chinh, link, muc nav dang chon."),
          ("on-primary", "#ffffff", "Chu tren `primary` (6.9:1)."),
          ("border", "#cccccc", "Vien input."),
          ("divider", "#e0e0e0", "Duong ke giua hang bang va vien card."),
          ("success-text", "#1e6b34", "Chu badge thanh cong tren `success-bg` (5.7:1).")]
DRAFT_COLORS = ["#FFFFFF", "#F5F6FA", "#222222", "#0057B8", "#CCCCCC", "#E0E0E0", "#1E6B34", "#E3F4E8"]


def tokens():
    return {
        "name": "Fixture", "version": 1,
        "meta": {"source": "website", "sites": ["WEB-01"], "synced": "2026-10-01",
                 "evidence": {"primary": "https://shop.example/list"}},
        "color": {"themes": [{"id": "light", "name": "Light"}],
                  "tokens": [{"name": n, "value": v, "usage": u} for n, v, u in COLORS]
                  + [{"name": "success-bg", "value": "{surface}", "usage": "Nen badge (alias)."}]},
        "type": {"fonts": [], "families": {"sans": "\"Noto Sans JP\", Arial, sans-serif"},
                 "groups": [{"name": "Text", "family": "sans", "styles": [
                     {"name": "body", "fontSize": "14px", "lineHeight": "20px", "fontWeight": 400, "usage": "Chu than."},
                     {"name": "title", "fontSize": "24px", "fontWeight": 700, "usage": "Tieu de trang (h1)."}]}]},
        "spacing": {"tokens": [{"name": "space-2", "value": "8px", "usage": "Padding doc cua nut."},
                               {"name": "space-4", "value": "16px", "usage": "Padding card."}]},
        "radius": {"tokens": [{"name": "radius-sm", "value": "4px", "usage": "Input."},
                              {"name": "radius-md", "value": "6px", "usage": "Nut."}]},
    }


def draft():
    return {"colors": [{"hex": h, "count": 3, "alpha": [1.0]} for h in DRAFT_COLORS],
            "fonts": [{"family": "\"Noto Sans JP\", Arial, sans-serif", "names": ["Noto Sans JP", "Arial", "sans-serif"]}],
            "spacings": [{"value": "8px"}, {"value": "16px"}], "radii": [{"value": "4px"}, {"value": "6px"}],
            "shadows": [], "fontFaces": []}


README = """Design system cho ShopDemo, dung lai tu website dang chay.

## Noi dung

- Giong van ngan, tieng Viet, khong emoji.

## Nen tang hinh anh

- Nen trang `page-bg`, card `surface`, chu `text-high`.
- Nut chinh `primary` voi chu `on-primary`; vien input `border`.

## Bieu tuong

- Icon SVG net 2px, xem nhom Icons.
"""

BUNDLE = """/* @ds-bundle: {"format":4,"namespace":"Fixture","components":[{"name":"Button"},{"name":"Badge"}]} */
(function () {
  var h = window.React.createElement;
  function Button(p) { return h('button', { className: 'fx-btn' }, p.children); }
  function Badge(p) { return h('span', { className: 'fx-badge' }, p.children); }
  window.Fixture = { Button: Button, Badge: Badge };
})();
"""
DTS = """export declare function Button(props: { children?: any }): JSX.Element;
export declare function Badge(props: { children?: any }): JSX.Element;
"""


def preview(comp, height=88):
    return ("<!-- @dsCard group=\"Actions\" height=%d -->\n<!doctype html>\n<html><body><div id=\"r\"></div>\n"
            "<script>ReactDOM.createRoot(document.getElementById('r')).render("
            "React.createElement(window.Fixture.%s, null, 'OK'));</script></body></html>\n" % (height, comp))


COVER = """<!-- @dsCard height=288 -->
<!doctype html>
<html><body style="margin:0;background:var(--page-bg)">
<svg width="960" height="288"><rect class="b" x="480" y="0" width="240" height="288"/></svg>
<div style="position:absolute;left:48px;bottom:64px;font-size:96px">ShopDemo</div>
<div style="position:absolute;left:48px;bottom:40px;font-size:13px">Quan ly don hang.</div>
</body></html>
"""
ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><circle cx="8" cy="8" r="5"/></svg>'


def build(root):
    P = os.path.join(root, "04_DesignSystem", "project")
    for d in ("components/Button", "components/Badge", "components/Cover", "assets/Icons"):
        os.makedirs(os.path.join(P, d), exist_ok=True)

    def w(rel, text):
        open(os.path.join(P, rel), "w", encoding="utf8").write(text)
    idx = {"v": 3, "layout": "files", "createdOnFiles": {"v": 1, "at": "2026-10-01T08:00:00Z"},
           "title": "ShopDemo", "namespace": "Fixture",
           "libraries": [{"name": "react", "version": "18"}, {"name": "react-dom", "version": "18"}],
           "sections": {}, "groups": ["Icons"],
           "assetGroups": {"Icons": {"name": "Icons", "tile": "xs", "order": ["search.svg"],
                                     "files": {"search.svg": {"name": "search.svg", "blob": "a" * 32,
                                                              "size": len(ICON), "type": "image/svg+xml"}}}},
           "blobs": {}, "docs": {"readme": "project/README.md", "sections": []},
           "lastChange": {"by": "Claude", "at": "2026-10-01T08:00:00Z", "via": "Claude Code"}}
    w("design-system.json", json.dumps(idx, indent=1))
    w("tokens.json", json.dumps(tokens(), indent=1, ensure_ascii=False))
    w("README.md", README)
    w("components/bundle.js", BUNDLE)
    w("components/index.d.ts", DTS)
    for c in ("Button", "Badge"):
        w("components/%s/README.md" % c, "%s dung lai tu website. Consumer cung cap children.\n" % c)
        w("components/%s/preview.html" % c, preview(c))
    w("components/Cover/preview.html", COVER)
    w("assets/Icons/search.svg", ICON)
    w("assets/Icons/README.md", "Icon net 2px, muc `text-high`.\n")
    dp = os.path.join(root, "tokens-draft.json")
    json.dump(draft(), open(dp, "w"))
    return os.path.join(root, "04_DesignSystem"), P, dp


def results(output):
    out = {}
    for line in output.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > 4 and parts[3] in ("PASS", "**FAIL**", "WARN"):
            out[parts[1]] = parts[3].strip("*")
    return out


def run(ds, dp, *extra):
    p = subprocess.run([sys.executable, os.path.join(HERE, "verify-design-system.py"), ds, "--draft", dp] + list(extra),
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def edit_tokens(fn):
    def f(P):
        p = os.path.join(P, "tokens.json")
        d = json.load(open(p))
        fn(d)
        json.dump(d, open(p, "w"))
    return f


def write(rel, text):
    def f(P):
        open(os.path.join(P, rel), "w").write(text)
    return f


def ctok(name):
    return lambda d: next(t for t in d["color"]["tokens"] if t["name"] == name)


# (ten, mutation, check mong doi FAIL)
CASES = [
    ("family dang map DTCG", edit_tokens(lambda d: d.update(spacing={"space-2": {"$value": "8px"}})), "3"),
    ("mau ten 'red'", edit_tokens(lambda d: ctok("border")(d).update(value="red")), "3"),
    ("alias toi token khong ton tai", edit_tokens(lambda d: ctok("success-bg")(d).update(value="{nope}")), "3"),
    ("ten trung giua 2 family", edit_tokens(lambda d: d["radius"]["tokens"][0].update(name="primary")), "3"),
    ("ten co dau cach", edit_tokens(lambda d: ctok("divider")(d).update(name="line color")), "3"),
    ("con ten obs- chua doi", edit_tokens(lambda d: ctok("divider")(d).update(name="obs-color-07")), "4"),
    ("usage TODO", edit_tokens(lambda d: ctok("primary")(d).update(usage="TODO — roles: button-bg")), "4"),
    ("type style usage rong", edit_tokens(lambda d: d["type"]["groups"][0]["styles"][0].pop("usage")), "4"),
    ("mau bia (khong co trong draft)", edit_tokens(lambda d: ctok("primary")(d).update(value="#123456")), "5"),
    ("font bia", edit_tokens(lambda d: d["type"]["families"].update(sans="Inter, sans-serif")), "5"),
    ("meta.source chi code", edit_tokens(lambda d: d["meta"].update(source="code")), "6"),
    ("README it muc ##", write("README.md", "Chi mot dong, `primary`.\n"), "7"),
    ("preview khong co marker", write("components/Button/preview.html", "<!doctype html>\n<p>window.Fixture</p>\n"), "8"),
    ("preview co iframe", write("components/Badge/preview.html",
                                 preview("Badge").replace("<div id", "<iframe src=x></iframe><div id")), "8"),
    ("component thieu trong bundle", write("components/bundle.js", BUNDLE.replace("Badge", "Pill")), "8"),
    ("cover co img", write("components/Cover/preview.html", COVER.replace("</svg>", "</svg><img src=x>")), "9"),
    ("cover height 500", write("components/Cover/preview.html", COVER.replace("height=288", "height=500")), "9"),
    ("Cover co README (khong con tran)", write("components/Cover/README.md", "Cover.\n"), "1"),
    ("index sai v/layout", lambda P: (lambda p: json.dump(dict(json.load(open(p)), v=2), open(p + ".tmp", "w"))
                                      or os.replace(p + ".tmp", p))(os.path.join(P, "design-system.json")), "2"),
    ("asset ghi trong index nhung khong co file", lambda P: os.remove(os.path.join(P, "assets/Icons/search.svg")), "10"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="selftest-ds-")
    total = passed = 0
    lines = []

    def record(name, ok, detail=""):
        nonlocal total, passed
        total += 1
        passed += ok
        lines.append("%s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + detail) if detail and not ok else ""))

    try:
        base = os.path.join(root, "base")
        ds, P, dp = build(base)
        code, out = run(ds, dp)
        r = results(out)
        bad = {k: v for k, v in r.items() if v == "FAIL"}
        record("project hop le -> PASS", code == 0 and not bad, "exit %d, FAIL: %s" % (code, bad))
        lk = os.path.join(ds, "link.md")
        open(lk, "w").write("https://claude.ai/artifact/AbC123xyz\n")
        code, out = run(ds, dp, "--published-url", "https://claude.ai/artifact/AbC123xyz")
        record("--published-url co trong link.md -> check 12 PASS", results(out).get("12") == "PASS" and code == 0,
               "nhan %s" % results(out).get("12"))
        code, out = run(ds, dp, "--published-url", "https://example.com/x")
        record("--published-url sai dang -> check 12 FAIL", results(out).get("12") == "FAIL", "nhan %s" % results(out).get("12"))
        os.remove(lk)
        for i, (name, fn, chk) in enumerate(CASES, 1):
            d = os.path.join(root, "c%02d" % i)
            shutil.copytree(base, d)
            dsx, Px = os.path.join(d, "04_DesignSystem"), os.path.join(d, "04_DesignSystem", "project")
            fn(Px)
            code, out = run(dsx, os.path.join(d, "tokens-draft.json"))
            got = results(out).get(chk)
            record("%s -> check %s FAIL" % (name, chk), got == "FAIL" and code == 1, "nhan %s (exit %d)" % (got, code))
        # Figma: mau ngoai draft chi WARN khi --figma-used VA meta.source co figma
        d = os.path.join(root, "figma")
        shutil.copytree(base, d)
        Px = os.path.join(d, "04_DesignSystem", "project")
        edit_tokens(lambda t: (ctok("primary")(t).update(value="#123456"), t["meta"].update(source="website+figma")))(Px)
        code, out = run(os.path.join(d, "04_DesignSystem"), os.path.join(d, "tokens-draft.json"), "--figma-used")
        record("mau ngoai draft + --figma-used + source figma -> check 5 WARN",
               results(out).get("5") == "WARN" and code == 0, "nhan %s (exit %d)" % (results(out).get("5"), code))
    finally:
        if a.keep:
            print("Giu fixture tai %s" % root)
        else:
            shutil.rmtree(root, ignore_errors=True)

    print("\n".join(lines))
    print("\n%d ca · %d PASS" % (total, passed))
    return 0 if total == passed else 1


if __name__ == "__main__":
    sys.exit(main())
