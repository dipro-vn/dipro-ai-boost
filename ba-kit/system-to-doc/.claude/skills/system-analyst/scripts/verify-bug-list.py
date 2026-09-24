#!/usr/bin/env python3
"""GATE V8 — Bug List (Output 2B).

  python3 verify-bug-list.py <02_BugList.xlsx> [--inventory <inventory.xlsx>] [--out report.md]

File nay di ra NGOAI cong ty (bao khach hang) nen nguong bang chung cao hon O2A.
Chan: bug thieu buoc tai hien · thieu bang chung · quy ket Security khong co PoC ·
bug chua tai hien duoc lot sheet gui khach · trung lap.
"""
import argparse
import re
import sys

import inv_schema as S
from gate_report import Gate

REQUIRED = ["Title", "Screen / Module", "Category", "Severity", "Repro Steps",
            "Expected", "Actual", "Evidence", "Reproduced", "Detected By",
            "Env", "Report To Customer"]
CUSTOMER_SHEET = "Bugs"


def load_bugs(path):
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise SystemExit("Thieu openpyxl. Chay: pip install openpyxl")
    wb = load_workbook(path, data_only=True)
    out = {}
    for name in S.BUG_SHEETS:
        if name not in wb.sheetnames:
            out[name] = None
            continue
        ws = wb[name]
        header = [str(c.value).strip() if c.value is not None else "" for c in ws[1]]
        rows = []
        for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if all(v is None or str(v).strip() == "" for v in r):
                continue
            d = {h: ("" if r[j] is None else str(r[j]).strip())
                 for j, h in enumerate(header) if h and j < len(r)}
            d["__row__"] = i
            d["__sheet__"] = name
            rows.append(d)
        out[name] = rows
    return out


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("buglist")
    ap.add_argument("--inventory", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    wb = load_bugs(a.buglist)
    g = Gate("GATE V8 — Bug List")

    missing_sheets = [k for k, v in wb.items() if v is None]
    g.check(1, "Du 4 sheet (00_Meta / Bugs / Suspected / Observations)", missing_sheets)
    if missing_sheets:
        return g.emit(a.out)

    bugs = wb["Bugs"]
    susp = wb["Suspected"]
    allb = bugs + susp

    ids = [r.get("Bug ID", "") for r in allb]
    rx = re.compile(r"^BUG-\d{3,}$")
    g.check(2, "Bug ID dung dinh dang BUG-NNN va khong trung",
            [i for i in ids if not rx.match(i)] +
            sorted({i for i in ids if ids.count(i) > 1}))

    # 3 — cot bat buoc
    blanks = []
    for r in allb:
        for c in REQUIRED:
            if not r.get(c, "").strip():
                blanks.append("%s!%s.%s" % (r["__sheet__"], r.get("Bug ID", r["__row__"]), c))
    g.check(3, "Moi bug dien du cot bat buoc", blanks)

    # 4 — enum
    bad = []
    for r in allb:
        tag = "%s!%s" % (r["__sheet__"], r.get("Bug ID", r["__row__"]))
        if r.get("Category") not in S.BUG_CATEGORY:
            bad.append("%s Category=%s" % (tag, r.get("Category")))
        if r.get("Severity") not in S.BUG_SEVERITY:
            bad.append("%s Severity=%s" % (tag, r.get("Severity")))
        if r.get("Detected By") not in S.BUG_DETECTED_BY:
            bad.append("%s Detected By=%s" % (tag, r.get("Detected By")))
        if r.get("Report To Customer") not in S.BUG_REPORT:
            bad.append("%s Report=%s" % (tag, r.get("Report To Customer")))
        if not re.match(r"^(Yes — \d+/\d+|Intermittent|No)$", r.get("Reproduced", "")):
            bad.append("%s Reproduced=%s" % (tag, r.get("Reproduced")))
    g.check(4, "Moi cot enum dung gia tri cho phep", bad)

    # 5 — buoc tai hien that su la cac buoc
    g.check(5, "Repro Steps co >= 2 buoc danh so",
            ["%s!%s" % (r["__sheet__"], r.get("Bug ID")) for r in allb
             if len(re.findall(r"(?m)^\s*\d+[.)]", r.get("Repro Steps", ""))) < 2])

    # 6 — bang chung phan giai duoc
    if a.inventory:
        evids = {x.get("EV ID", "") for x in S.load(a.inventory)["05_Evidence"]}
        g.check(6, "Evidence tro toi EV co that trong inventory",
                ["%s!%s -> %s" % (r["__sheet__"], r.get("Bug ID"), r.get("Evidence"))
                 for r in allb
                 if not [e for e in S.split_ids(r.get("Evidence", "")) if e in evids]])
    else:
        g.warn(6, "Evidence phan giai", "chua truyen --inventory")

    # 7 — bug chua tai hien khong duoc nam o sheet gui khach
    g.check(7, "Sheet '%s' chi chua bug da tai hien duoc" % CUSTOMER_SHEET,
            [r.get("Bug ID") for r in bugs if not r.get("Reproduced", "").startswith("Yes")])

    # 8 — Security phai co PoC
    g.check(8, "Bug Category=Security phai co PoC (tai hien duoc + co bang chung)",
            [r.get("Bug ID") for r in bugs if r.get("Category") == "Security"
             and (not r.get("Reproduced", "").startswith("Yes")
                  or not r.get("Evidence", "").strip())])

    # 9 — Suspected/Observations khong duoc gui khach
    g.check(9, "Sheet Suspected khong duoc danh dau gui khach hang",
            [r.get("Bug ID") for r in susp if r.get("Report To Customer") == "Yes"])

    # 10 — S1/S2 phai co Business Impact
    g.check(10, "Bug S1/S2 phai ghi Business Impact",
            [r.get("Bug ID") for r in allb
             if r.get("Severity", "").startswith(("S1", "S2"))
             and not r.get("Business Impact", "").strip()])

    # 11 — trung lap
    seen, dups = {}, []
    for r in allb:
        key = (norm(r.get("Title")), norm(r.get("URL / Route")))
        if key in seen:
            dups.append("%s ~ %s" % (seen[key], r.get("Bug ID")))
        else:
            seen[key] = r.get("Bug ID")
    g.check(11, "Khong co bug trung lap (cung tieu de + cung route)", dups)

    # 12 — Pre-existing
    g.check(12, "Moi bug khai Pre-existing (Yes/Unknown)",
            ["%s=%s" % (r.get("Bug ID"), r.get("Pre-existing"))
             for r in allb if r.get("Pre-existing") not in ("Yes", "Unknown")])

    # 13 — meta khai bao pham vi quet + nguoi nhan
    meta = {r.get("Key", ""): r.get("Value", "") for r in wb["00_Meta"]}
    g.check(13, "00_Meta khai g13_scan_scope + g13_recipient",
            [k for k in ("g13_scan_scope", "g13_recipient")
             if not meta.get(k) or meta.get(k) == S.UNKNOWN])

    # 14 — Observations la noi chua nghi van chua co PoC
    obs = wb["Observations"]
    g.check(14, "Observations co du cot bat buoc",
            ["row%s thieu %s" % (r["__row__"], c) for r in obs
             for c in ("Title", "Why suspicious", "Suggested investigation")
             if not r.get(c, "").strip()])

    rc = g.emit(a.out)
    sev = {}
    for r in bugs:
        sev[r.get("Severity", "?")] = sev.get(r.get("Severity", "?"), 0) + 1
    print("BUGS: %d gui khach · %d nghi ngo · %d quan sat · %s"
          % (len(bugs), len(susp), len(obs),
             " · ".join("%s=%d" % kv for kv in sorted(sev.items())) or "-"), file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
