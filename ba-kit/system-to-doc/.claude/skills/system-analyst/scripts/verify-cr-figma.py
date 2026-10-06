#!/usr/bin/env python3
"""GATE V-CR-FIGMA — view CR tren Figma: dung format Output 1/2, chi phan lien quan, thong ke dung, man de xuat bam DS.

  python3 verify-cr-figma.py --nodes <ver>/_internal/cr-figma-nodes.json --cr-json <ver>/_internal/cr.json \\
      --baseline <outputs>/verK_... [--view <ver>/_internal/cr-figma.json] [--rates ...] [--template ...] \\
      [--out <ver>/_internal/gates/v-cr-figma.md]

cr-figma-nodes.json = ket qua chay <ver>/_internal/figma-js/99-readback.js (render-cr-figma.py sinh) bang use_figma:
  {"section": {...}, "nodes": [{id,name,badge,ref,kind[,ds,site,colors]}], "arrows": [{id,from,to}],
   "stats": [{name,value}], "legend": n, "unbadged": [...], "overlap": [...]}
  (dang cu: chi list nodes — van doc duoc, cac check moi bao FAIL vi thieu du lieu).
Quy uoc ten node: "<BADGE> · <REF> · <nhan>", BADGE = NEW|UPD|DEL|IMPACT|AS-IS; sharedPluginData namespace "crkit"
(Figma bat buoc namespace >= 3 ky tu): kind = flow | tech | screen | flow-step | edge | mockup | arrow | stat | legend.

Checks: 1 ten/badge/kind · 2 node tro toi impact co that, badge = Loai · 3 man / luong bi anh huong deu duoc ve ·
4 AS-IS chi la muc bi anh huong / hang xom 1 buoc / lane FL-xx cua baseline · 5 CR Change Table = THONG KE dung
(so doi tuong NEW/UPD/DEL/IMPACT + 実装 MD) · 6 khong ve trung (WARN) · 7 moi node CR-1/CR-2 co mui ten noi (format
Output 1/2, khong chip roi) · 8 legend + khong node thieu badge · 9 khong chong node cu · 10 CR-3: man de xuat bam DS
(ref DS resolve, mau ⊆ token cua site / site muon), du man theo cr-figma.json, da khai doc DS.
"""
import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402
import cr_common as C  # noqa: E402
from gate_report import Gate  # noqa: E402

BADGES = ["NEW", "UPD", "DEL", "IMPACT", "AS-IS"]
KINDS = ["flow", "tech", "screen", "flow-step", "edge", "mockup", "other"]
NEED_ARROW = ("flow", "screen", "flow-step")
SEP = " · "


def keys_of(imp):
    """Cac REF hop le cho node cua impact nay."""
    refs = C.refs_of(imp.get("baseline_ref"))
    if refs:
        return set(refs) | {C.txt(imp.get("id"))}
    return {C.txt(imp.get("id")), C.txt(imp.get("item"))} - {""}


def baseline_lanes(bdir):
    ids = set()
    for p in glob.glob(os.path.join(bdir, "_internal", "figma", "output1*.md")):
        ids |= set(re.findall(r"\bFL-\d+\b", open(p, encoding="utf8").read()))
    return ids


def token_colors(bdir, site):
    p = os.path.join(bdir, "04_DesignSystem", site, "project", "tokens.json")
    if not os.path.isfile(p):
        p = os.path.join(bdir, "04_DesignSystem", "project", "tokens.json")
    if not os.path.isfile(p):
        return set()
    t = C.load_json(p)
    out = set()
    for x in (t.get("color") or {}).get("tokens") or []:
        v = str(x.get("value") or "").strip().lower()
        m = re.match(r"^#([0-9a-f]{6})", v)
        if m:
            out.add("#" + m.group(1))
        m = re.match(r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", v)
        if m:
            out.add("#%02x%02x%02x" % tuple(int(g) for g in m.groups()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", required=True)
    ap.add_argument("--cr-json", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--view", default=None, help="cr-figma.json (de doi chieu man CR-3 + ds_read)")
    ap.add_argument("--rates", default=os.path.join(KIT, S.MD_RATES_PATH))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    raw = C.load_json(a.nodes)
    data = raw if isinstance(raw, dict) else {"nodes": raw}
    nodes = data.get("nodes") or []
    cr = C.load_json(a.cr_json)
    _rm, rates = C.load_rates(a.rates)
    B = C.load_baseline(a.baseline)
    view = C.load_json(a.view) if a.view and os.path.isfile(a.view) else None
    IMP = cr.get("impacts") or []
    g = Gate("GATE V-CR-FIGMA — %s" % C.txt((cr.get("meta") or {}).get("cr_id")))
    real = [n for n in nodes if n.get("kind") != "table-row"]

    # 1. Dang node
    bad = []
    for n in nodes:
        nid, name = C.txt(n.get("id")), C.txt(n.get("name"))
        parts = [p.strip() for p in name.split(SEP)]
        if n.get("badge") not in BADGES:
            bad.append("%s badge=%s" % (nid, n.get("badge")))
        if n.get("kind") not in KINDS:
            bad.append("%s kind=%s" % (nid, n.get("kind")))
        if len(parts) < 3 or parts[0] != n.get("badge") or parts[1] != C.txt(n.get("ref")):
            bad.append("%s ten '%s' sai quy uoc '<BADGE> · <REF> · <nhan>'" % (nid, name))
    g.check(1, "Node dung quy uoc ten + badge/kind hop le", bad)

    # 2. Node CR khop impact (ref + badge == change_type)
    bad = []
    for n in real:
        badge, ref = n.get("badge"), C.txt(n.get("ref"))
        if badge == "AS-IS" or badge not in BADGES:
            continue
        hit = [i for i in IMP if ref in keys_of(i)]
        if hit and not any(i.get("change_type") == badge for i in hit):
            bad.append("%s %s badge %s != Loai %s" % (n.get("id"), ref, badge,
                       "/".join(sorted({i.get("change_type") for i in hit}))))
        elif not hit:
            bad.append("%s %s · %s khong thuoc impact nao — ngoai pham vi CR" % (n.get("id"), badge, ref))
    g.check(2, "Moi node NEW/UPD/DEL/IMPACT tro toi impact co that, badge = Loai", bad)

    # 3. Man / luong bi anh huong phai duoc ve
    bad = []
    drawn = {(C.txt(n.get("ref")), n.get("badge")) for n in real if n.get("kind") != "mockup"}
    for i in IMP:
        if i.get("axis") not in ("Screen", "Business"):
            continue
        refs = [r for r in C.refs_of(i.get("baseline_ref")) if r.startswith(("SC-", "F-"))]
        if i.get("axis") == "Screen" and not C.refs_of(i.get("baseline_ref")):
            refs = [i["id"]]                      # man NEW chua co trong baseline -> ref = Impact ID
        for r in refs:
            if (r, i.get("change_type")) not in drawn:
                bad.append("%s %s %s chua ve" % (i.get("id"), i.get("change_type"), r))
    g.check(3, "Impact Screen (SC- / man NEW) va Business (SC-/F-) deu co node tren CR-1/CR-2", bad)

    # 4. AS-IS chi la hang xom 1 buoc
    impacted = set()
    for i in IMP:
        impacted |= set(C.refs_of(i.get("baseline_ref"))) | {i["id"]}
    near = set(impacted)
    for r in list(impacted):
        near |= B["links"].get(r, set())
    near |= baseline_lanes(a.baseline)
    bad = ["%s AS-IS %s ngoai pham vi CR (khong ke 1 buoc / khong phai lane FL baseline)" % (n.get("id"), n.get("ref"))
           for n in real if n.get("badge") == "AS-IS" and C.txt(n.get("ref")) not in near]
    g.check(4, "AS-IS chi la muc bi anh huong, hang xom 1 buoc hoac lane FL-xx cua baseline", bad)

    # 5. CR Change Table = thong ke
    bad = []
    stats = {C.txt(s.get("name")): C.txt(s.get("value")) for s in data.get("stats") or []}
    if not stats:
        bad.append("khong co o STAT nao — CR Change Table phai la bang thong ke (chay 03-change-table.js)")
    else:
        cols = S.CR_CHANGE_TYPE + ["Tổng", "実装 MD"]
        for o, d in C.object_stats(IMP, rates):
            want = [d[t] for t in S.CR_CHANGE_TYPE] + [d["total"], d["md"]]
            for c, w in zip(cols, want):
                got = stats.get("STAT · %s · %s" % (o, c))
                try:
                    ok = got is not None and round(float(got), 2) == round(float(w), 2)
                except ValueError:
                    ok = False
                if not ok:
                    bad.append("%s / %s = %s != %s" % (o, c, got, C.fmt_md(w)))
        tot = [v for k, v in stats.items() if k.startswith("STAT · TOTAL · 実装")]
        grand = C.object_stats(IMP, rates)[-1][1]["md"]
        if not tot or round(float(tot[0]), 2) != round(grand, 2):
            bad.append("o 実装 tong = %s != %s" % (tot[0] if tot else None, C.fmt_md(grand)))
    if [n for n in nodes if n.get("kind") == "table-row"]:
        bad.append("CR Change Table con dong chi tiet tung hang muc (table-row) — chi giu thong ke")
    g.check(5, "CR Change Table: thong ke so doi tuong NEW/UPD/DEL/IMPACT + 実装 MD khop cr.json", bad)

    # 6. Trung node
    seen, dup = {}, []
    for n in real:
        k = (n.get("badge"), C.txt(n.get("ref")), n.get("kind"))
        if k in seen and n.get("kind") not in ("edge",):
            dup.append("%s · %s (%s, %s)" % (k[0], k[1], seen[k], n.get("id")))
        seen.setdefault(k, n.get("id"))
    g.check(6, "Khong ve trung cung REF + BADGE trong cung loai node", dup, level="WARN")

    # 7. Mui ten that
    bad = []
    if "arrows" not in data:
        bad.append("nodes.json khong co 'arrows' — doc nguoc bang 99-readback.js")
    else:
        ends = set()
        for e in data["arrows"]:
            ends |= {C.txt(e.get("from")), C.txt(e.get("to"))}
        bad += ["%s %s chua noi mui ten (Output 1/2 cam chip roi)" % (n.get("id"), n.get("name"))
                for n in real if n.get("kind") in NEED_ARROW and C.txt(n.get("id")) not in ends]
    g.check(7, "Moi node CR-1 / CR-2 noi bang mui ten that (format Output 1 / Output 2)", bad)

    # 8. Legend + node thieu badge
    bad = []
    if not data.get("legend"):
        bad.append("thieu LEGEND badge")
    bad += ["node khong badge: %s" % x for x in data.get("unbadged") or []]
    g.check(8, "Co legend; khong node nao trong CR-1 / CR-2 thieu badge", bad)

    # 9. Chong node cu
    bad = ["section CR chong len %s" % x for x in data.get("overlap") or []]
    if "overlap" not in data:
        bad.append("nodes.json khong co 'overlap' — doc nguoc bang 99-readback.js")
    g.check(9, "Section CR khong chong node cu (Output 1/2, CR khac)", bad)

    # 10. CR-3 man de xuat
    mock = [n for n in nodes if n.get("kind") == "mockup"]
    items = ((view or {}).get("screens") or {}).get("items") or []
    bad = []
    if items or mock:
        drawn_m = {(C.txt(n.get("ref")), n.get("badge")) for n in mock}
        bad += ["CR-3 thieu man %s %s" % (it.get("badge"), it.get("ref")) for it in items
                if (C.txt(it.get("ref")), it.get("badge")) not in drawn_m]
        ds_read = ((view or {}).get("screens") or {}).get("ds_read") or []
        for st in sorted({it.get("site") for it in items}):
            for f in ("README.md", "tokens.json"):
                if not any(os.path.join(st, "project", f) in p for p in ds_read):
                    bad.append("CR-3 chua khai doc %s/project/%s truoc khi ve" % (st, f))
        for n in mock:
            refs = C.refs_of(C.txt(n.get("ds")))
            if not refs:
                bad.append("%s khong ghi DS ref nao" % n.get("name"))
            sites = {n.get("site")}
            for r in refs:
                ok, why, _w = C.resolve(r, B)
                if not ok:
                    bad.append("%s %s: %s" % (n.get("name"), r, why))
                m = re.match(r"^DS(?:-component)?:(WEB-\d+):", r)
                if m:
                    sites.add(m.group(1))
            allowed = {"#ffffff", "#000000"}
            for st in sites:
                allowed |= token_colors(a.baseline, st)
            extra = sorted({c.lower() for c in n.get("colors") or []} - allowed)
            if extra:
                bad.append("%s dung mau ngoai Design System %s: %s" % (n.get("name"), "/".join(sorted(sites)), extra))
        g.check(10, "CR-3: man de xuat du theo pham vi, da doc DS truoc, ref DS ton tai, mau chi tu token", bad)
    else:
        g.ok(10, "CR-3 man de xuat", "khong ve (CR-3 = khong) — ghi ly do trong README version")

    print("FIGMA: %d node · %d mui ten · %d o thong ke · %d man de xuat" % (
        len(nodes), len(data.get("arrows") or []), len(data.get("stats") or []), len(mock)), file=sys.stderr)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
