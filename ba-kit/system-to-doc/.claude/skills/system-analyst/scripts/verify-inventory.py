#!/usr/bin/env python3
"""GATE V2 — Function/Screen Inventory coverage + truy vet.

  python3 verify-inventory.py <inventory.xlsx> \
      [--routes routes.txt] [--crawled urls.txt] [--out report.md]

--routes   : danh sach route lay tu scan-repo.py (1 route / dong)
--crawled  : danh sach URL da crawl that (1 URL / dong)

Chan: chuc nang Confirmed khong co bang chung · muc chua chac khong khai bao
Open Question · route trong code bi bo quen · ID trung/nhay coc.
"""
import argparse
import os
import re
import sys

import inv_schema as S
from gate_report import Gate


def read_list(path):
    if not path or not os.path.isfile(path):
        return []
    out = []
    for line in open(path, encoding="utf8"):
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def norm_route(r):
    """/orders/123 va /orders/:id ve cung dang de so sanh."""
    r = r.split("?")[0].rstrip("/") or "/"
    r = re.sub(r"^https?://[^/]+", "", r)
    r = re.sub(r"/(\d+|\{[^/]+\}|:[^/]+|\[[^/]+\])(?=/|$)", "/:id", r)
    return r.lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory")
    ap.add_argument("--routes", default=None)
    ap.add_argument("--crawled", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    data = S.load(a.inventory)
    meta = S.meta(data)
    g = Gate("GATE V2 — Inventory coverage")

    funcs = data["01_Function"]
    screens = data["02_Screen"]
    questions = data["06_OpenQuestions"]
    tables = data["03_DB_Tables"]
    cols = data["04_DB_Columns"]

    fids = [r.get("Function ID", "") for r in funcs]
    sids = [r.get("Screen ID", "") for r in screens]
    qids = [r.get("Q ID", "") for r in questions]
    evids = {r.get("EV ID", "") for r in data["05_Evidence"]}

    # 1..3 — dinh dang + trung lap ID
    for no, (sheet, ids) in enumerate(
            [("01_Function", fids), ("02_Screen", sids), ("06_OpenQuestions", qids)], start=1):
        col, pat = S.ID_PATTERNS[sheet]
        rx = re.compile(pat)
        bad = [i for i in ids if not rx.match(i)]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        g.check(no, "%s: %s dung dinh dang va khong trung" % (sheet, col), bad + dup)

    # 4 — Function ID lien tuc
    nums = sorted(int(i.split("-")[1]) for i in fids if re.match(r"^F-\d+$", i))
    gaps = [("F-%03d" % n) for n in range(1, (nums[-1] if nums else 0) + 1) if n not in nums]
    g.check(4, "Function ID lien tuc, khong nhay coc", gaps)

    # 5 — enum
    bad_enum = []
    bad_enum += [("%s Status=%s" % (r["Function ID"], r.get("Status", "")))
                 for r in funcs if r.get("Status") not in S.FUNCTION_STATUS]
    bad_enum += [("%s Status=%s" % (r["Screen ID"], r.get("Status", "")))
                 for r in screens if r.get("Status") not in S.SCREEN_STATUS]
    bad_enum += [("%s Type=%s" % (r["Screen ID"], r.get("Type", "")))
                 for r in screens if r.get("Type") not in S.SCREEN_TYPE]
    bad_enum += [("%s Type=%s" % (r["Q ID"], r.get("Type", "")))
                 for r in questions if r.get("Type") not in S.QUESTION_TYPE]
    bad_enum += [("%s Status=%s" % (r["Q ID"], r.get("Status", "")))
                 for r in questions if r.get("Status") not in S.QUESTION_STATUS]
    g.check(5, "Moi cot enum dung gia tri cho phep", bad_enum)

    # 6 — Confirmed phai co bang chung
    g.check(6, "Moi chuc nang Confirmed co >=1 EV",
            [r["Function ID"] for r in funcs
             if r.get("Status") == "Confirmed"
             and not [e for e in S.split_ids(r.get("Evidence", "")) if e in evids]])

    # 7 — chua chac chan phai khai bao Open Question
    qset = set(qids)
    bad_q = []
    for r in funcs:
        if r.get("Status") in ("To verify", "Inferred", "CONFLICT"):
            refs = [q for q in S.split_ids(r.get("Open Q", "")) if q in qset]
            if not refs:
                bad_q.append("%s (%s)" % (r["Function ID"], r.get("Status")))
    g.check(7, "Moi chuc nang chua Confirmed co Open Question tuong ung", bad_q)

    # 8 — Screen IDs cua Function phan giai duoc
    sset = set(sids)
    bad_link = []
    for r in funcs:
        raw = r.get("Screen IDs", "")
        if raw.strip() == S.NO_SCREEN:
            continue
        if not raw.strip():
            bad_link.append("%s bo trong Screen IDs" % r["Function ID"])
            continue
        for sid in S.split_ids(raw):
            if sid not in sset:
                bad_link.append("%s -> %s khong ton tai" % (r["Function ID"], sid))
    g.check(8, "Screen IDs cua Function phan giai duoc (hoac khai 'SYSTEM — no screen')", bad_link)

    # 9 — Function IDs cua Screen phan giai duoc
    fset = set(fids)
    g.check(9, "Function IDs cua Screen phan giai duoc",
            ["%s -> %s" % (r["Screen ID"], f)
             for r in screens for f in S.split_ids(r.get("Function IDs", ""))
             if f not in fset])

    # 10 — Screenshot EV
    g.check(10, "Screenshot EV ton tai hoac khai bao NO IMAGE",
            [r["Screen ID"] for r in screens
             if S.NO_IMAGE not in r.get("Screenshot EV", "")
             and not [e for e in S.split_ids(r.get("Screenshot EV", "")) if e in evids]])

    # 11 — khong de o trong lang le
    required = {
        "01_Function": ["Module", "Function", "Primary Actor", "Description",
                        "Entry / Trigger", "Source", "Status"],
        "02_Screen": ["URL / Route", "Screen Name", "Type", "Actor", "Status"],
    }
    blanks = []
    for sheet, need in required.items():
        for r in data[sheet]:
            for c in need:
                if not r.get(c, "").strip():
                    blanks.append("%s!row%s.%s" % (sheet, r["__row__"], c))
    g.check(11, "Khong o trong lang le (thieu bang chung phai ghi UNKNOWN)", blanks)

    # 12 — nhat quan DB
    db_mode = meta.get("g4_db", "")
    if db_mode == "NONE":
        g.check(12, "g4_db=NONE thi 2 sheet DB phai rong",
                (["03_DB_Tables co %d dong" % len(tables)] if tables else []) +
                (["04_DB_Columns co %d dong" % len(cols)] if cols else []))
    elif db_mode in S.DB_MODE:
        g.check(12, "g4_db=%s thi phai co du lieu DB" % db_mode,
                [] if tables else ["03_DB_Tables rong"])
    else:
        g.warn(12, "Nhat quan DB", "00_Meta.g4_db=%r khong thuoc %s" % (db_mode, S.DB_MODE))

    # 13 — bang duoc nhac o Function phai ton tai
    tset = {r.get("Table", "") for r in tables}
    if db_mode != "NONE":
        g.check(13, "Related Tables cua Function ton tai trong 03_DB_Tables",
                ["%s -> %s" % (r["Function ID"], t) for r in funcs
                 for t in S.split_ids(r.get("Related Tables", "")) if t not in tset])
    else:
        g.ok(13, "Related Tables (bo qua — khong co DB)")

    # 14 — Meaning High confidence phai co code-ref
    ev_type = {r.get("EV ID", ""): r.get("Type", "") for r in data["05_Evidence"]}
    g.check(14, "04_DB_Columns: Meaning confidence High phai co EV loai code-ref",
            ["%s.%s" % (r.get("Table", ""), r.get("Column", "")) for r in cols
             if r.get("Confidence") == "High"
             and "code-ref" not in [ev_type.get(e) for e in S.split_ids(r.get("Evidence", ""))]])

    # 15 — route trong code da duoc phu
    routes = read_list(a.routes)
    if routes:
        covered = {norm_route(r.get("Entry / Trigger", "")) for r in funcs}
        covered |= {norm_route(r.get("URL / Route", "")) for r in screens}
        missing = [r for r in routes if norm_route(r) not in covered]
        g.check(15, "Moi route trong source code co mat trong inventory", missing)
        print("\nCOVERAGE: %d/%d route · THIEU: %s" %
              (len(routes) - len(missing), len(routes), missing or "[]"), file=sys.stderr)
    else:
        g.warn(15, "Route coverage", "chua truyen --routes -> khong kiem duoc bo sot")

    # 16 — URL da crawl deu co mat o 02_Screen
    crawled = read_list(a.crawled)
    if crawled:
        known = {norm_route(r.get("URL / Route", "")) for r in screens}
        g.check(16, "Moi URL da crawl co mat trong 02_Screen",
                [u for u in crawled if norm_route(u) not in known])
    else:
        g.warn(16, "Crawl coverage", "chua truyen --crawled")

    rc = g.emit(a.out)
    st = {}
    for r in funcs:
        st[r.get("Status", "?")] = st.get(r.get("Status", "?"), 0) + 1
    print("EVIDENCE: %d EV · %s" % (len(evids), " · ".join("%s=%d" % kv for kv in sorted(st.items()))),
          file=sys.stderr)
    print("OPEN QUESTIONS: %d con Open" %
          sum(1 for r in questions if r.get("Status") == "Open"), file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
