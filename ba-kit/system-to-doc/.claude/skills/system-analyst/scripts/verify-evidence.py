#!/usr/bin/env python3
"""GATE V1 — Evidence Ledger integrity.

  python3 verify-evidence.py <inventory.xlsx> [--root <thu muc chua evidence/>] [--out report.md]

Chan "EV ma": bang chung duoc tro toi nhung khong ton tai, file artifact khong co that,
code-ref khong phan giai duoc ra file#line co that.
"""
import argparse
import os
import re
import sys

import inv_schema as S
from gate_report import Gate

CODE_REF = re.compile(r"^(?P<path>[^#\s]+)#L(?P<a>\d+)(?:-L(?P<b>\d+))?$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory")
    ap.add_argument("--root", default=None,
                    help="Thu muc goc de phan giai Artifact va code-ref (mac dinh: thu muc chua inventory)")
    ap.add_argument("--code-root", default=None,
                    help="Thu muc source code de phan giai code-ref")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    root = a.root or os.path.dirname(os.path.abspath(a.inventory))
    data = S.load(a.inventory)
    g = Gate("GATE V1 — Evidence Ledger")

    ev_rows = data["05_Evidence"]
    ids = [r.get("EV ID", "") for r in ev_rows]

    # 1 — dinh dang + trung lap
    pat = re.compile(S.ID_PATTERNS["05_Evidence"][1])
    g.check(1, "EV ID dung dinh dang EV-NNNN",
            [i for i in ids if not pat.match(i)])
    dup = sorted({i for i in ids if ids.count(i) > 1})
    g.check(2, "EV ID khong trung", dup)

    # 3 — Type thuoc enum
    g.check(3, "Type thuoc enum cho phep",
            [(r["EV ID"], r.get("Type", "")) for r in ev_rows
             if r.get("Type", "") not in S.EVIDENCE_TYPE],
            fmt=lambda x: "%s=%s" % x)

    # 4 — Locator khong rong
    g.check(4, "Moi EV co Locator",
            [r["EV ID"] for r in ev_rows if not r.get("Locator")])

    # 5 — artifact ton tai that
    need_art = [r for r in ev_rows if r.get("Type") in S.EVIDENCE_NEEDS_ARTIFACT]
    missing_art = []
    for r in need_art:
        art = r.get("Artifact", "")
        if not art:
            missing_art.append("%s (trong Artifact)" % r["EV ID"])
        elif not os.path.exists(os.path.join(root, art)):
            missing_art.append("%s -> %s" % (r["EV ID"], art))
    g.check(5, "File artifact (screenshot/har/log) ton tai that", missing_art)

    # 6 — code-ref phan giai duoc
    bad_code = []
    code_root = a.code_root
    for r in ev_rows:
        if r.get("Type") != "code-ref":
            continue
        m = CODE_REF.match(r.get("Locator", ""))
        if not m:
            bad_code.append("%s locator sai dinh dang file#Lxx" % r["EV ID"])
            continue
        if code_root:
            fp = os.path.join(code_root, m.group("path"))
            if not os.path.isfile(fp):
                bad_code.append("%s -> khong thay %s" % (r["EV ID"], m.group("path")))
                continue
            try:
                n = sum(1 for _ in open(fp, encoding="utf8", errors="ignore"))
            except OSError:
                bad_code.append("%s -> khong doc duoc %s" % (r["EV ID"], m.group("path")))
                continue
            end = int(m.group("b") or m.group("a"))
            if end > n:
                bad_code.append("%s -> file chi co %d dong" % (r["EV ID"], n))
    g.check(6, "code-ref dung dinh dang va phan giai duoc" +
            ("" if code_root else " (chua truyen --code-root: chi kiem dinh dang)"), bad_code)

    # 7 — evidence tu website phai co Captured At + Actor/Role
    bad_web = []
    for r in ev_rows:
        if r.get("Type") in S.EVIDENCE_NEEDS_ARTIFACT:
            if not r.get("Captured At"):
                bad_web.append("%s thieu Captured At" % r["EV ID"])
            if not r.get("Actor/Role"):
                bad_web.append("%s thieu Actor/Role" % r["EV ID"])
    g.check(7, "Evidence quan sat co Captured At + Actor/Role", bad_web)

    # 8 — moi EV duoc tro toi deu ton tai (khong co EV ma)
    known = set(ids)
    referenced = {}
    ref_cols = [("01_Function", "Evidence"), ("02_Screen", "Screenshot EV"),
                ("03_DB_Tables", "Evidence"), ("04_DB_Columns", "Evidence"),
                ("06_OpenQuestions", "Reason / Evidence")]
    for sheet, col in ref_cols:
        for r in data.get(sheet, []):
            for ev in S.split_ids(r.get(col, "")):
                if not ev.startswith("EV-"):
                    continue
                referenced.setdefault(ev, []).append("%s!row%s" % (sheet, r["__row__"]))
    ghosts = ["%s (%s)" % (ev, locs[0]) for ev, locs in sorted(referenced.items())
              if ev not in known]
    g.check(8, "Khong co EV ma (tro toi evidence khong ton tai)", ghosts)

    # 9 — EV mo coi (co trong ledger nhung khong ai dung)
    orphan = sorted(known - set(referenced))
    g.check(9, "Khong co EV mo coi", orphan, level="WARN")

    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
