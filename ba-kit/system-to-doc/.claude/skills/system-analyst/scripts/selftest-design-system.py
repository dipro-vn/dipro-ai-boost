#!/usr/bin/env python3
"""Gate V-DS self-test: chung minh verify-design-system.py that su bat loi.

  python3 selftest-design-system.py [--keep]

Dung 1 04_DesignSystem HOP LE theo design-system-format.md (STATUS.md + project/: 1 theme, token vai tro §3.3
co hoac ghi TBD, type Heading/Text 4 style, Button + Badge co bundle/d.ts/preview, component con lai ghi TBD,
cover, nhom Icons) -> PASS. Sau do tiem tung loi vao ban copy -> khang dinh dung check do FAIL.
Chay lai sau MOI lan sua verify-design-system.py / ds_roles.py.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ds_roles as R_  # noqa: E402

COLORS = [("primary", "#0057b8", "Nen nut chinh, trang phan trang dang chon."),
          ("on-primary", "{white}", "Chu tren `primary` (6.9:1)."),
          ("primary-text", "#0057b8", "Link, chu nut outline tren `surface` (6.9:1)."),
          ("primary-subtle", "#e6eef8", "Nen muc nav dang chon."),
          ("white", "#ffffff", "Trang tuyet doi."),
          ("page-bg", "#f5f6fa", "Nen trang ung dung."),
          ("surface", "#ffffff", "Card, nav, modal tren `page-bg`."),
          ("surface-subtle", "#f0f2f5", "Header o bang."),
          ("text-high", "#1a2b4c", "Tieu de tren `surface` (14.5:1)."),
          ("text-middle", "#222222", "Noi dung tren `surface` (15.9:1)."),
          ("text-low", "#6b7280", "Meta tren `surface` (4.8:1)."),
          ("divider-low", "#e0e0e0", "Ke giua hang bang."),
          ("divider-middle", "#cccccc", "Vien input."),
          ("overlay-scrim", "rgba(0,0,0,0.4)", "Lop phu sau modal."),
          ("success-100", "#e3f4e8", "Nen badge thanh cong."),
          ("success-700", "#1e6b34", "Chu badge tren `success-100` (5.7:1)."),
          ("negative-100", "#ffebe9", "Nen badge loi."),
          ("negative-500", "#cf222e", "Nen nut xoa."),
          ("negative-600", "#a40e26", "Chu badge loi tren `negative-100` (7.4:1).")]
DRAFT_COLORS = ["#FFFFFF", "#F5F6FA", "#0057B8", "#E6EEF8", "#F0F2F5", "#1A2B4C", "#222222", "#6B7280",
                "#E0E0E0", "#CCCCCC", "#E3F4E8", "#1E6B34", "#FFEBE9", "#CF222E", "#A40E26"]
SIZES = [("viewport-web", "1440px", "Khung web (cao 900px)."), ("header-height", "56px", "Header."),
         ("sidebar-width", "220px", "Sidebar."), ("control-md", "34px", "Nut."),
         ("table-header-height", "32px", "Header bang."), ("table-row-height", "35px", "Hang bang.")]
TBD = ["primary-hover", "primary-active", "surface-disabled", "divider-high", "info-100", "info-700",
       "warning-100", "warning-800", "focus-ring", "radius-xs", "radius-xl", "shadow-stick", "shadow-float",
       "shadow-popout", "shadow-focus", "modal-width"]
COMPS_HAVE = ["Button", "Badge"]


def tokens():
    return {
        "name": "Fixture", "version": 1,
        "meta": {"source": "website", "file": "https://shop.example", "frames": [], "components": {},
                 "componentKeys": {}, "synced": "2026-10-01", "evidence": {"primary": "https://shop.example/list"}},
        "color": {"themes": [{"id": "light", "name": "Light"}],
                  "tokens": [{"name": n, "value": v, "usage": u} for n, v, u in COLORS]},
        "type": {"fonts": [], "families": {"sans": "\"Noto Sans JP\", Arial, sans-serif"},
                 "groups": [{"name": "Heading", "family": "sans", "styles": [
                     {"name": "heading-24-bold", "fontSize": "24px", "fontWeight": 700, "sample": "Danh sach don hang",
                      "usage": "Tieu de trang (h1)."}]},
                     {"name": "Text", "family": "sans", "styles": [
                         {"name": "text-14", "fontSize": "14px", "lineHeight": "20px", "fontWeight": 400,
                          "sample": "Dang nhap", "usage": "Chu than."},
                         {"name": "text-14-bold", "fontSize": "14px", "fontWeight": 600, "sample": "Ma don",
                          "usage": "Header bang."},
                         {"name": "text-12", "fontSize": "12px", "fontWeight": 400, "sample": "Hien thi 1-1 / 1",
                          "usage": "Meta phan trang."}]}]},
        "spacing": {"tokens": [{"name": "space-8", "value": "8px", "usage": "Padding doc cua nut."},
                               {"name": "space-16", "value": "16px", "usage": "Padding card."}]},
        "radius": {"tokens": [{"name": "radius-none", "value": "0px", "usage": "Bang."},
                              {"name": "radius-sm", "value": "4px", "usage": "Input."},
                              {"name": "radius-md", "value": "6px", "usage": "Nut."},
                              {"name": "radius-lg", "value": "8px", "usage": "Card."},
                              {"name": "radius-full", "value": "999px", "usage": "Badge pill."}]},
        "shadow": {"tokens": [{"name": "shadow-flat", "value": "none", "usage": "Card phang."},
                              {"name": "shadow-raise", "value": "rgba(0, 0, 0, 0.2) 0px 1px 2px 0px", "usage": "Nut."}]},
        "size": {"tokens": [{"name": n, "value": v, "usage": u} for n, v, u in SIZES]},
    }


def draft():
    return {"colors": [{"hex": h, "count": 3, "alpha": [1.0]} for h in DRAFT_COLORS]
            + [{"hex": "#000000", "count": 2, "alpha": [0.4]}],
            "fonts": [{"family": "\"Noto Sans JP\", Arial, sans-serif", "names": ["Noto Sans JP", "Arial", "sans-serif"]}],
            "spacings": [{"value": "8px"}, {"value": "16px"}],
            "radii": [{"value": "4px"}, {"value": "6px"}, {"value": "8px"}, {"value": "999px"}],
            "shadows": [{"value": "rgba(0, 0, 0, 0.2) 0px 1px 2px 0px"}], "fontFaces": []}


def status(state="DRAFT", artifact="— (chưa publish)", tbd_comps=None, tbd=None):
    rows = ["| D1 | %s | khong quan sat duoc |" % n for n in (TBD if tbd is None else tbd)]
    comps = [c for c in R_.COMPONENTS if c not in COMPS_HAVE] + ["SideNav / TabBar"] if tbd_comps is None else tbd_comps
    rows += ["| D6 | %s | khong thay tren cac man da quet |" % c for c in comps]
    return ("# Design System — ShopDemo\n\n- Trạng thái: %s\n- Artifact: %s\n- Nguồn: website WEB-01 (3 màn)\n\n"
            "## Platform\n\n| Platform | Theme (`data-theme`) | Viewport | Khung màn | Screen prefix |\n|---|---|---|---|---|\n"
            "| Web desktop | `light` | 1440 × 900 | header 56px | — |\n\n"
            "## Thứ tự ưu tiên nguồn (khi mâu thuẫn)\n1. Website · code\n\n"
            "## Thiếu (TBD)\n\n| D# | Token / component | Ghi chú |\n|---|---|---|\n%s\n\n"
            "## Mâu thuẫn cần xác nhận\n\n| # | Nội dung | Quyết định tạm |\n|---|---|---|\n\n"
            "## Changelog\n\n| Ngày | Thay đổi |\n|---|---|\n| 2026-10-01 | Khoi tao |\n" % (state, artifact, "\n".join(rows)))


README = """Design system cho ShopDemo, dung lai tu website dang chay WEB-01. Mot theme `light`.

## Màu

- Nen ung dung `page-bg`, card `surface`, header bang `surface-subtle`.
- Chu `text-high` cho tieu de, `text-middle` cho noi dung, `text-low` cho meta.
- Nut chinh `primary` voi chu `on-primary`; vien input `divider-middle`.

## Chữ

- Tieu de trang `heading-24-bold`, noi dung `text-14`.

## Khoảng cách, bố cục

- Buoc `space-8`, `space-16`; header `header-height`.
"""

BUNDLE = """/* @ds-bundle: {"format":4,"namespace":"Fixture","components":[{"name":"Button"},{"name":"Badge"}]} */
(function () {
  var h = window.React.createElement;
  function Button(p) { return h('button', { className: 'fx-btn' }, p.children); }
  function Badge(p) { return h('span', { className: 'fx-badge' }, p.children); }
  window.Fixture = { Button: Button, Badge: Badge };
})();
"""
DTS = """// Fixture — window.Fixture (React 18), 1 theme light.
export declare function Button(props: { children?: any }): JSX.Element;
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
    for c in COMPS_HAVE:
        w("components/%s/README.md" % c, "%s dung lai tu website. Consumer cung cap children.\n" % c)
        w("components/%s/preview.html" % c, preview(c))
    w("components/Cover/preview.html", COVER)
    w("assets/Icons/search.svg", ICON)
    w("assets/Icons/README.md", "Icon net 2px, muc `text-high`.\n")
    open(os.path.join(root, "04_DesignSystem", "STATUS.md"), "w", encoding="utf8").write(status())
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
        os.makedirs(os.path.dirname(os.path.join(P, rel)), exist_ok=True)
        open(os.path.join(P, rel), "w", encoding="utf8").write(text)
    return f


def write_status(text):
    return lambda P: open(os.path.join(P, "..", "STATUS.md"), "w", encoding="utf8").write(text)


def ctok(name):
    return lambda d: next(t for t in d["color"]["tokens"] if t["name"] == name)


def drop_color(name):
    return edit_tokens(lambda d: d["color"].update(tokens=[t for t in d["color"]["tokens"] if t["name"] != name]))


def no_status_link_md(P):
    os.remove(os.path.join(P, "..", "STATUS.md"))
    open(os.path.join(P, "..", "link.md"), "w").write("https://claude.ai/artifact/AbC123xyz\n")


# (ten, mutation, check mong doi FAIL)
CASES = [
    ("family dang map DTCG", edit_tokens(lambda d: d.update(spacing={"space-8": {"$value": "8px"}})), "3"),
    ("mau ten 'red'", edit_tokens(lambda d: ctok("divider-middle")(d).update(value="red")), "3"),
    ("alias toi token khong ton tai", edit_tokens(lambda d: ctok("on-primary")(d).update(value="{nope}")), "3"),
    ("ten trung giua 2 family", edit_tokens(lambda d: d["radius"]["tokens"][1].update(name="primary")), "3"),
    ("ten co dau cach", edit_tokens(lambda d: ctok("divider-low")(d).update(name="line color")), "3"),
    ("con ten obs- chua doi", edit_tokens(lambda d: ctok("divider-low")(d).update(name="obs-color-07")), "4"),
    ("usage TODO", edit_tokens(lambda d: ctok("primary")(d).update(usage="TODO — vai tro suy tu nut")), "4"),
    ("type style usage rong", edit_tokens(lambda d: d["type"]["groups"][1]["styles"][0].pop("usage")), "4"),
    ("mau bia (khong co trong draft)", edit_tokens(lambda d: ctok("primary")(d).update(value="#123456")), "5"),
    ("font bia", edit_tokens(lambda d: d["type"]["families"].update(sans="Inter, sans-serif")), "5"),
    ("meta.source chi code", edit_tokens(lambda d: d["meta"].update(source="code")), "6"),
    ("meta.source gia tri la", edit_tokens(lambda d: d["meta"].update(source="website+sketch")), "6"),
    ("README it muc ##", write("README.md", "Chi mot dong, `primary`.\n"), "7"),
    ("README co muc Chua dong bo", write("README.md", README + "\n## Chưa đồng bộ\n\n- Hover cua `primary`.\n"), "7"),
    ("preview khong co marker", write("components/Button/preview.html", "<!doctype html>\n<p>window.Fixture</p>\n"), "8"),
    ("preview co iframe", write("components/Badge/preview.html",
                                 preview("Badge").replace("<div id", "<iframe src=x></iframe><div id")), "8"),
    ("component thieu trong bundle", write("components/bundle.js", BUNDLE.replace("Badge", "Pill")), "8"),
    ("cover co img", write("components/Cover/preview.html", COVER.replace("</svg>", "</svg><img src=x>")), "9"),
    ("cover height 500", write("components/Cover/preview.html", COVER.replace("height=288", "height=500")), "9"),
    ("Cover co README (khong con tran)", write("components/Cover/README.md", "Cover.\n"), "1"),
    ("con components/_Example", write("components/_Example/README.md", "Folder mau.\n"), "1"),
    ("link.md, khong co STATUS.md", no_status_link_md, "1"),
    ("index sai v/layout", lambda P: (lambda p: json.dump(dict(json.load(open(p)), v=2), open(p + ".tmp", "w"))
                                      or os.replace(p + ".tmp", p))(os.path.join(P, "design-system.json")), "2"),
    ("asset ghi trong index nhung khong co file", lambda P: os.remove(os.path.join(P, "assets/Icons/search.svg")), "10"),
    ("STATUS APPROVED khong --approved-by", write_status(status(state="APPROVED 2026-10-01")), "13"),
    ("STATUS thieu muc Changelog", write_status(status().split("## Changelog")[0]), "13"),
    ("STATUS Trang thai con placeholder", write_status(status(state="<DRAFT | APPROVED YYYY-MM-DD>")), "13"),
    ("token vai tro thieu va khong TBD", drop_color("text-low"), "14"),
    ("token vai tro TBD bi xoa khoi STATUS", write_status(status(tbd=TBD[1:])), "14"),
    ("type style thieu sample", edit_tokens(lambda d: d["type"]["groups"][0]["styles"][0].pop("sample")), "15"),
    ("thieu group Heading", edit_tokens(lambda d: d["type"]["groups"].pop(0)), "15"),
    ("component thieu va khong TBD", write_status(status(tbd_comps=[c for c in R_.COMPONENTS if c not in COMPS_HAVE + ["Modal"]]
                                                       + ["SideNav / TabBar"])), "16"),
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
        sp = os.path.join(ds, "STATUS.md")
        open(sp, "w", encoding="utf8").write(status(artifact="https://claude.ai/artifact/AbC123xyz"))
        code, out = run(ds, dp, "--published-url", "https://claude.ai/artifact/AbC123xyz")
        record("--published-url co trong STATUS.md '- Artifact:' -> check 12 PASS",
               results(out).get("12") == "PASS" and code == 0, "nhan %s" % results(out).get("12"))
        code, out = run(ds, dp, "--published-url", "https://example.com/x")
        record("--published-url sai dang -> check 12 FAIL", results(out).get("12") == "FAIL", "nhan %s" % results(out).get("12"))
        open(sp, "w", encoding="utf8").write(status(state="APPROVED 2026-10-01"))
        code, out = run(ds, dp, "--approved-by", "Nguyen Van A")
        record("APPROVED + --approved-by -> check 13 PASS", results(out).get("13") == "PASS" and code == 0,
               "nhan %s (exit %d)" % (results(out).get("13"), code))
        open(sp, "w", encoding="utf8").write(status())
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
