#!/usr/bin/env python3
"""GATE V-CR-FIGMA — Figma cua CR chi ve phan lien quan truc tiep.

  python3 verify-cr-figma.py --nodes <ver>/_internal/cr-figma-nodes.json \
      --cr-json <ver>/_internal/cr.json --baseline <outputs>/verK_... \
      [--out <ver>/_internal/gates/v-cr-figma.md]

Quy uoc ten node: "<BADGE> · <REF> · <nhan>", BADGE = NEW|UPD|DEL|IMPACT|AS-IS.
REF = baseline_ref cua impact (SC-014, F-002, table:orders ...); impact NEW co baseline_ref "—" -> REF = Impact ID
(hoac dung Hang muc). Khi ve, gan kind: node.setSharedPluginData("cr","kind","screen|flow|table-row|other").
Doc lai bang 1 lan use_figma (sua ten section), luu ket qua thanh cr-figma-nodes.json:

  const sec = figma.currentPage.findOne(n => n.type === "SECTION" && n.name.startsWith("CR-001"));
  const rx = /^(NEW|UPD|DEL|IMPACT|AS-IS) · ([^·]+?) · /;
  return sec.findAll(n => rx.test(n.name)).map(n => {
    const m = n.name.match(rx);
    return {id: n.id, name: n.name, badge: m[1], ref: m[2].trim(),
            kind: n.getSharedPluginData("cr", "kind") || "other"};
  });

Checks: ref/badge khop impact · man/luong bi anh huong deu duoc ve · AS-IS chi la hang xom 1 buoc
(02_Screen.Entry From 2 chieu, 01_Function.Screen IDs, 07_API.Called By Screens) · so dong CR Change Table.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cr_common as C  # noqa: E402
from gate_report import Gate  # noqa: E402

BADGES = ["NEW", "UPD", "DEL", "IMPACT", "AS-IS"]
KINDS = ["screen", "flow", "table-row", "other"]
SEP = " · "


def keys_of(imp):
    """Cac REF hop le cho node cua impact nay."""
    refs = C.refs_of(imp.get("baseline_ref"))
    if refs:
        return set(refs)
    return {C.txt(imp.get("id")), C.txt(imp.get("item"))} - {""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", required=True)
    ap.add_argument("--cr-json", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    nodes = C.load_json(a.nodes)
    cr = C.load_json(a.cr_json)
    B = C.load_baseline(a.baseline)
    IMP = cr.get("impacts") or []
    g = Gate("GATE V-CR-FIGMA — %s" % C.txt((cr.get("meta") or {}).get("cr_id")))
    if not isinstance(nodes, list):
        nodes = []
        g.fail(1, "nodes.json la list", "khong phai list")

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
    bad, drawn = [], set()
    for n in nodes:
        badge, ref = n.get("badge"), C.txt(n.get("ref"))
        if badge == "AS-IS" or badge not in BADGES:
            continue
        hit = [i for i in IMP if ref in keys_of(i)]
        same = [i for i in hit if i.get("change_type") == badge]
        if same:
            if n.get("kind") != "table-row":
                drawn |= {C.txt(i.get("id")) for i in same}
        elif hit:
            bad.append("%s %s badge %s != Loai %s" % (n.get("id"), ref, badge,
                       "/".join(sorted({i.get("change_type") for i in hit}))))
        else:
            bad.append("%s %s · %s khong thuoc impact nao — ngoai pham vi CR" % (n.get("id"), badge, ref))
    g.check(2, "Moi node NEW/UPD/DEL/IMPACT tro toi impact co that, badge = Loai", bad)

    # 3. Man / luong bi anh huong phai duoc ve
    bad = []
    for i in IMP:
        if i.get("axis") not in ("Screen", "Business"):
            continue
        refs = [r for r in C.refs_of(i.get("baseline_ref")) if r.startswith(("SC-", "F-"))]
        for r in refs:
            if not any(C.txt(n.get("ref")) == r and n.get("badge") == i.get("change_type")
                       and n.get("kind") != "table-row" for n in nodes):
                bad.append("%s %s %s chua ve" % (i.get("id"), i.get("change_type"), r))
    g.check(3, "Impact truc Screen/Business co SC-/F- deu co node", bad)

    # 4. AS-IS chi la hang xom 1 buoc
    impacted = set()
    for i in IMP:
        impacted |= set(C.refs_of(i.get("baseline_ref")))
    near = set(impacted)
    for r in impacted:
        near |= B["links"].get(r, set())
    bad = ["%s AS-IS %s ngoai pham vi CR (khong ke 1 buoc voi muc bi anh huong)" % (n.get("id"), n.get("ref"))
           for n in nodes if n.get("badge") == "AS-IS" and C.txt(n.get("ref")) not in near]
    g.check(4, "AS-IS chi la muc bi anh huong hoac hang xom 1 buoc", bad)

    # 5. CR Change Table
    rows = [n for n in nodes if n.get("kind") == "table-row"]
    if rows or drawn:
        g.check(5, "CR Change Table: so dong = so impact da ve",
                [] if len(rows) == len(drawn) else
                ["%d dong table-row != %d impact da ve (%s)" % (len(rows), len(drawn), ",".join(sorted(drawn)))])
    else:
        g.ok(5, "CR Change Table", "khong co node")

    # 6. Trung node
    seen, dup = {}, []
    for n in nodes:
        if n.get("kind") == "table-row":
            continue
        k = (n.get("badge"), C.txt(n.get("ref")))
        if k in seen:
            dup.append("%s · %s (%s, %s)" % (k[0], k[1], seen[k], n.get("id")))
        seen.setdefault(k, n.get("id"))
    g.check(6, "Khong ve trung cung REF + BADGE", dup, level="WARN")

    print("FIGMA: %d node · %d impact da ve / %d · %d dong bang" % (
        len(nodes), len(drawn), len(IMP), len(rows)), file=sys.stderr)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
