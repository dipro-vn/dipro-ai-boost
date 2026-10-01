#!/usr/bin/env python3
"""Quan ly version folder trong <project>/outputs/ (Luong 1 baseline + Luong 2 CR).

  python3 version-tool.py next --outputs <project>/outputs --slug baseline [--cr-id CR-001] [--date DDMMYY] [--create]
  python3 version-tool.py latest-baseline --outputs <project>/outputs
  python3 version-tool.py list --outputs <project>/outputs [--json]

next            -> JSON {n, folder, path} ; --create moi mkdir folder + _internal/{gates,recon,evidence}
latest-baseline -> JSON {folder, path, n, inventory, outputs:{O1..O7: bool}} ; exit 1 neu khong co baseline
list            -> bang version + CR mo sau baseline moi nhat (canh bao xung dot CR-vs-CR)
KHONG BAO GIO sua folder version cu.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402

VER_RE = re.compile(r"^ver(\d+)_(\d{6})_(.+)$")
CR_SLUG_RE = re.compile(r"^(CR-\d+)(?:-(.*))?$", re.I)

# Duong dan output theo CONTRACT (glob tuong doi folder version)
OUTPUT_GLOBS = {
    "O1": ["01_Screens/BasicDesign_*.xlsx"],
    "O2": ["02_API/API_Doc_*.xlsx"],
    "O3": ["03_DB/DB_Doc_*.xlsx"],
    "O4": ["04_DesignSystem/project/design-system.json"],
    "O5": ["05_Figma/figma-links.md"],
    "O6": ["06_Overview/Overview_*.docx"],
    "O7": ["07_BugList/BugList_*.xlsx"],
}


def slugify(text):
    t = (text or "").replace("đ", "d").replace("Đ", "D")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return re.sub(r"-{2,}", "-", t)


def norm_cr_id(cr_id):
    c = (cr_id or "").strip().upper()
    m = re.match(r"^(?:CR-?)?(\d+)$", c)
    if not m:
        raise SystemExit("--cr-id khong hop le: %r (vd CR-001)" % cr_id)
    return "CR-%03d" % int(m.group(1))


def read_kv(xlsx, sheet):
    """Doc sheet Key/Value -> dict (khong yeu cau du sheet nhu S.load)."""
    try:
        from openpyxl import load_workbook
    except ImportError:
        print("Thieu openpyxl. Chay: pip install openpyxl", file=sys.stderr)
        sys.exit(2)
    try:
        wb = load_workbook(xlsx, read_only=True, data_only=True)
    except Exception:
        return {}
    if sheet not in wb.sheetnames:
        return {}
    out = {}
    for r in wb[sheet].iter_rows(min_row=2, values_only=True):
        if r and r[0] is not None:
            out[str(r[0]).strip()] = "" if len(r) < 2 or r[1] is None else str(r[1]).strip()
    wb.close()
    return out


def scan(outputs):
    """Liet ke version folder -> list dict, sap theo n."""
    if not os.path.isdir(outputs):
        return []
    vers = []
    for name in sorted(os.listdir(outputs)):
        p = os.path.join(outputs, name)
        m = VER_RE.match(name)
        if not (m and os.path.isdir(p)):
            continue
        n, date, slug = int(m.group(1)), m.group(2), m.group(3)
        inv = os.path.join(p, "_internal", "inventory.xlsx")
        vtype, cr_id, base_ref = "", "", ""
        if os.path.isfile(inv):
            vtype = read_kv(inv, "00_Meta").get("version_type", "").upper()
        if vtype not in S.VERSION_TYPE:
            rl = os.path.join(p, "run-log.md")
            txt = open(rl, encoding="utf8", errors="ignore").read() if os.path.isfile(rl) else ""
            mm = re.search(r"version_type\W{0,6}(BASELINE|CR)\b", txt)
            vtype = mm.group(1) if mm else ""
        impacts = sorted(glob.glob(os.path.join(p, "CR-*_Impact.xlsx")))
        mc = CR_SLUG_RE.match(slug)
        if mc:
            cr_id = mc.group(1).upper()
        if impacts:
            summ = read_kv(impacts[0], "00_Summary")
            cr_id = summ.get("cr_id") or cr_id or os.path.basename(impacts[0]).split("_")[0]
            base_ref = summ.get("baseline_version", "")
        if not vtype and (impacts or mc):
            vtype = "CR"
        vers.append({"n": n, "folder": name, "path": os.path.abspath(p),
                     "date": date, "type": vtype or "UNKNOWN", "cr_id": cr_id,
                     "baseline_ref": base_ref,
                     "impact": os.path.abspath(impacts[0]) if impacts else ""})
    vers.sort(key=lambda v: v["n"])
    return vers


def outputs_exist(path):
    res = {}
    for k, pats in OUTPUT_GLOBS.items():
        res[k] = any(glob.glob(os.path.join(path, g)) for g in pats)
    return res


def cmd_next(a):
    vers = scan(a.outputs)
    n = max([v["n"] for v in vers] or [0]) + 1
    date = a.date or datetime.date.today().strftime("%d%m%y")
    if not re.match(r"^\d{6}$", date):
        raise SystemExit("--date phai dang DDMMYY")
    slug = slugify(a.slug)
    if not slug:
        raise SystemExit("--slug rong sau khi chuan hoa")
    if a.cr_id:
        folder = "ver%d_%s_%s-%s" % (n, date, norm_cr_id(a.cr_id), slug)
    else:
        folder = "ver%d_%s_%s" % (n, date, slug)
    path = os.path.abspath(os.path.join(a.outputs, folder))
    if a.create:
        if os.path.exists(path):
            raise SystemExit("Da ton tai, khong ghi de: %s" % path)
        for sub in ("gates", "recon", "evidence"):
            os.makedirs(os.path.join(path, "_internal", sub))
    print(json.dumps({"n": n, "folder": folder, "path": path, "created": bool(a.create)},
                     ensure_ascii=False))
    return 0


def latest_baseline(vers):
    bases = [v for v in vers if v["type"] == "BASELINE"]
    return bases[-1] if bases else None


def cmd_latest(a):
    b = latest_baseline(scan(a.outputs))
    if not b:
        print("Khong tim thay version BASELINE nao trong %s "
              "(00_Meta.version_type / run-log 'version_type: BASELINE'). "
              "Chay Luong 1 truoc." % a.outputs, file=sys.stderr)
        return 1
    inv = os.path.join(b["path"], "_internal", "inventory.xlsx")
    print(json.dumps({"folder": b["folder"], "path": b["path"], "n": b["n"],
                      "inventory": inv, "inventory_exists": os.path.isfile(inv),
                      "outputs": outputs_exist(b["path"])}, ensure_ascii=False, indent=2))
    return 0


def cmd_list(a):
    vers = scan(a.outputs)
    b = latest_baseline(vers)
    open_crs = [v for v in vers if v["type"] == "CR" and b and v["n"] > b["n"]]
    if a.json:
        print(json.dumps({"versions": vers, "latest_baseline": b and b["folder"],
                          "open_crs": [v["folder"] for v in open_crs]},
                         ensure_ascii=False, indent=2))
        return 0
    print("| N | Folder | Type | Date | CR ID | Baseline ref |")
    print("|---|---|---|---|---|---|")
    for v in vers:
        print("| %d | %s | %s | %s | %s | %s |" % (
            v["n"], v["folder"], v["type"], v["date"], v["cr_id"] or "—",
            v["baseline_ref"] or "—"))
    print("")
    print("Latest baseline: %s" % (b["folder"] if b else "(khong co)"))
    if open_crs:
        print("Open CRs since latest baseline (%d) — kiem tra xung dot CR-vs-CR "
              "(verify-cr-impact.py --other-cr):" % len(open_crs))
        for v in open_crs:
            warn = ""
            if v["baseline_ref"] and b and v["baseline_ref"] != b["folder"]:
                warn = "  [CANH BAO: tham chieu baseline %s]" % v["baseline_ref"]
            print("  - %s (%s) %s%s" % (v["folder"], v["cr_id"] or "?", v["impact"] or "", warn))
    else:
        print("Open CRs since latest baseline: 0")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("next")
    p.add_argument("--outputs", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--cr-id", default=None)
    p.add_argument("--date", default=None)
    p.add_argument("--create", action="store_true")
    p = sub.add_parser("latest-baseline")
    p.add_argument("--outputs", required=True)
    p = sub.add_parser("list")
    p.add_argument("--outputs", required=True)
    p.add_argument("--json", action="store_true")
    a = ap.parse_args()
    return {"next": cmd_next, "latest-baseline": cmd_latest, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
