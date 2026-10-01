#!/usr/bin/env python3
"""GATE V5 — so do flow tong quan (chuong 7 cua Overview O6).

  python3 verify-flow-png.py <flow.json> --inventory <inventory.xlsx> [--png <flow.png>] [--out report.md]

Khong OCR anh. Thay vao do kiem **nguon sinh ra anh** (flow.json): moi node phai tro
ve mot F-/SC-/API-/EXT-/WEB- hoac bang DB CO THAT trong inventory. Node khong tro ve dau
= node bia ra -> FAIL.

Schema flow.json:
{
  "title": "...",
  "nodes": [{"id":"n1","label":"User / Admin","kind":"actor","row":0,"ref":""}],
  "edges": [{"from":"n1","to":"n2","label":""}],
  "explanation": ["1. User truy cap Web Application.", "..."]
}
kind ∈ actor · site · screen · api · db · external · batch
ref  : F-xxx | SC-xxx | API-xxx | EXT-xxx | WEB-xx | table:<ten bang>
       | "" (chi cho phep voi kind=actor/external)
"""
import argparse
import json
import os
import sys

import inv_schema as S
from gate_report import Gate

KINDS = ["actor", "site", "screen", "api", "db", "external", "batch"]
PREFIX_SHEET = [("F-", "01_Function", "Function ID"), ("SC-", "02_Screen", "Screen ID"),
                ("API-", "07_API", "API ID"), ("EXT-", "09_Integration", "EXT ID"),
                ("WEB-", "10_Site", "Site ID")]
REF_OPTIONAL = ["actor", "external"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("flow")
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--png", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    flow = json.load(open(a.flow, encoding="utf8"))
    data = S.load(a.inventory)
    g = Gate("GATE V5 — Overall flow")

    nodes = flow.get("nodes", [])
    edges = flow.get("edges", [])
    expl = flow.get("explanation", [])
    ids = [n.get("id") for n in nodes]

    known = {p: {r.get(col, "") for r in data[sheet]} for p, sheet, col in PREFIX_SHEET}
    sheet_of = {p: sheet for p, sheet, _ in PREFIX_SHEET}
    tset = {r.get("Table", "") for r in data["03_DB_Tables"]}

    g.check(1, "Co it nhat 1 node", [] if nodes else ["flow.json khong co node"])
    dup = sorted({i for i in ids if ids.count(i) > 1})
    g.check(2, "node id khong trung", dup)
    g.check(3, "kind thuoc enum",
            ["%s kind=%s" % (n.get("id"), n.get("kind")) for n in nodes
             if n.get("kind") not in KINDS])

    # 4 — ref phan giai duoc
    bad_ref = []
    for n in nodes:
        ref = (n.get("ref") or "").strip()
        kind = n.get("kind")
        if not ref:
            if kind not in REF_OPTIONAL:
                bad_ref.append("%s (%s) thieu ref" % (n.get("id"), kind))
            continue
        prefix = next((p for p in known if ref.startswith(p)), None)
        if prefix:
            if ref not in known[prefix]:
                bad_ref.append("%s -> %s khong co trong %s" % (n.get("id"), ref, sheet_of[prefix]))
        elif ref.startswith("table:"):
            t = ref.split(":", 1)[1]
            if t not in tset:
                bad_ref.append("%s -> bang %s khong co trong 03_DB_Tables" % (n.get("id"), t))
        else:
            bad_ref.append("%s ref=%r sai dinh dang" % (n.get("id"), ref))
    g.check(4, "Moi node tro ve F/SC/API/EXT/WEB/table co that (khong bia node)", bad_ref)

    # 5 — edge tro toi node co that
    idset = set(ids)
    g.check(5, "Edge tro toi node co that",
            ["%s->%s" % (e.get("from"), e.get("to")) for e in edges
             if e.get("from") not in idset or e.get("to") not in idset])

    # 6 — khong node mo coi
    touched = {e.get("from") for e in edges} | {e.get("to") for e in edges}
    g.check(6, "Khong node mo coi (khong noi voi node nao)",
            [i for i in ids if i not in touched] if len(ids) > 1 else [])

    # 7 — dien giai (chuong 7) phu het node
    text = "\n".join(expl).lower()
    g.check(7, "Flow co dien giai", [] if expl else ["explanation rong"])
    g.check(8, "Moi node duoc nhac trong dien giai",
            [n.get("label") for n in nodes
             if (n.get("label") or "").lower() not in text])

    # 9 — PNG ton tai
    if a.png:
        if not os.path.isfile(a.png):
            g.fail(9, "File PNG ton tai", a.png)
        elif os.path.getsize(a.png) < 2048:
            g.fail(9, "File PNG ton tai", "file qua nho (%d byte) — nghi la anh rong"
                   % os.path.getsize(a.png))
        else:
            g.ok(9, "File PNG ton tai")
    else:
        g.warn(9, "File PNG", "chua truyen --png")

    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
