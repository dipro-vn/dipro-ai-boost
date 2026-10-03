#!/usr/bin/env python3
"""GATE V8 — Bug List (O7).

  python3 verify-bug-list.py <07_BugList/BugList_<sys>_ver<N>.xlsx> --inventory <_internal/inventory.xlsx> [--out report.md]

File nay di ra NGOAI cong ty (bao khach hang) nen nguong bang chung cao.
Chi ghi bug QUAN SAT TREN MAN khi Playwright quet website, muc Urgent / High (khach yeu cau).
Bug doc tu code / API / DB khong ghi o day (nghi van -> Observations, noi bo).
Chan: thieu buoc tai hien · thieu bang chung man hinh · URL la API · bug chua tai hien lot sheet
gui khach · trung lap · Screen / Module khong tro ve SC- co that.
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
            bad.append("%s Severity=%s (chi %s; bug Low khong ghi nhan)"
                       % (tag, r.get("Severity"), "/".join(S.BUG_SEVERITY)))
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
    inv = S.load(a.inventory) if a.inventory else None
    if inv:
        evids = {x.get("EV ID", "") for x in inv["05_Evidence"]}
        g.check(6, "Evidence tro toi EV co that trong inventory",
                ["%s!%s -> %s" % (r["__sheet__"], r.get("Bug ID"), r.get("Evidence"))
                 for r in allb
                 if not [e for e in S.split_ids(r.get("Evidence", "")) if e in evids]])
    else:
        g.warn(6, "Evidence phan giai", "chua truyen --inventory")

    # 7 — bug chua tai hien khong duoc nam o sheet gui khach
    g.check(7, "Sheet '%s' chi chua bug da tai hien duoc" % CUSTOMER_SHEET,
            [r.get("Bug ID") for r in bugs if not r.get("Reproduced", "").startswith("Yes")])

    # 8 — bug phai quan sat tren MAN (Playwright): URL khong phai API, evidence la anh/console/HAR
    ev_type = {x.get("EV ID", ""): x.get("Type", "") for x in inv["05_Evidence"]} if inv else {}
    bad8 = []
    for r in allb:
        tag = "%s!%s" % (r["__sheet__"], r.get("Bug ID"))
        url = r.get("URL / Route", "")
        if re.search(r"(^|/)api(/|$)", re.sub(r"^https?://[^/]+", "", url), re.I):
            bad8.append("%s URL '%s' la API — chi ghi bug tren man" % (tag, url))
        if inv and not [e for e in S.split_ids(r.get("Evidence", ""))
                        if ev_type.get(e) in S.BUG_SCREEN_EVIDENCE]:
            bad8.append("%s khong co evidence man hinh (%s)" % (tag, "/".join(S.BUG_SCREEN_EVIDENCE)))
    g.check(8, "Bug quan sat tren man khi quet (URL man, evidence screenshot/console/HAR)", bad8)

    # 9 — Suspected/Observations khong duoc gui khach
    g.check(9, "Sheet Suspected khong duoc danh dau gui khach hang",
            [r.get("Bug ID") for r in susp if r.get("Report To Customer") == "Yes"])

    # 10 — moi bug (High/Medium) phai co Business Impact
    g.check(10, "Bug Urgent/High phai ghi Business Impact",
            [r.get("Bug ID") for r in allb
             if r.get("Severity") in S.BUG_SEVERITY
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
    bad_meta = []
    for k in ("bug_scan_scope", "bug_recipient"):
        if k not in meta:
            bad_meta.append("thieu key %s (tao workbook bang build-inventory.py --bug-list)" % k)
        elif not meta[k].strip() or meta[k] == S.UNKNOWN:
            bad_meta.append("%s con %s — dien pham vi quet / nguoi nhan" % (k, meta[k] or "trong"))
    g.check(13, "00_Meta khai bug_scan_scope + bug_recipient", bad_meta)

    # 14 — Observations la noi chua nghi van chua co PoC
    obs = wb["Observations"]
    g.check(14, "Observations co du cot bat buoc",
            ["row%s thieu %s" % (r["__row__"], c) for r in obs
             for c in ("Title", "Why suspicious", "Suggested investigation")
             if not r.get(c, "").strip()])

    # 15 — Screen / Module tro ve SC-/F- co that trong inventory
    if inv:
        known = {x.get("Screen ID", "") for x in inv["02_Screen"]} | \
                {x.get("Function ID", "") for x in inv["01_Function"]}
        bad_ref = []
        for r in allb + obs:
            tag = "%s!%s" % (r["__sheet__"], r.get("Bug ID") or r.get("Obs ID") or r["__row__"])
            pat = r"\b(?:SC|F)-\d{3,}\b" if r["__sheet__"] == "Observations" else r"\bSC-\d{3,}\b"
            refs = re.findall(pat, r.get("Screen / Module", ""))
            if not refs:
                bad_ref.append("%s '%s' khong co %s" % (tag, r.get("Screen / Module", ""),
                               "SC-/F-" if r["__sheet__"] == "Observations" else "SC- (bug phai gan voi man)"))
            bad_ref += ["%s -> %s khong co trong inventory" % (tag, x) for x in refs if x not in known]
        g.check(15, "Screen / Module tro ve SC- co that (Observations: SC-/F-)", bad_ref)
    else:
        g.warn(15, "Screen / Module phan giai", "chua truyen --inventory")

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
