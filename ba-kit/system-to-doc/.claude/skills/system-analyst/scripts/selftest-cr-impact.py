#!/usr/bin/env python3
"""GATE V-CR self-test: chung minh verify-cr-impact.py that su bat loi.

  python3 selftest-cr-impact.py [--keep]

Dung baseline gia (inventory + tokens.json + components.md) va 1 CR Impact DUNG -> PASS.
Sau do tiem tung loi vao ban copy -> khang dinh dung check do FAIL (hoac WARN).
Chay lai sau MOI lan sua verify-cr-impact.py.
"""
import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402

BASE = "ver1_011026_baseline"


def sh(script, *args):
    p = subprocess.run([sys.executable, os.path.join(HERE, script)] + list(args),
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def results(output):
    """-> {check_no: level} tu bang markdown cua Gate."""
    out = {}
    for line in output.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > 4 and parts[3] in ("PASS", "**FAIL**", "WARN"):
            out[parts[1]] = parts[3].strip("*")
    return out


def fill(path, kv=None, rows=None):
    """Ghi Key/Value vao sheet dau + them dong theo header (dict)."""
    from openpyxl import load_workbook
    wb = load_workbook(path)
    if kv:
        ws = wb[wb.sheetnames[0]]
        pos = {ws.cell(row=i, column=1).value: i for i in range(2, ws.max_row + 1)}
        for k, v in kv.items():
            i = pos.get(k) or ws.max_row + 1
            ws.cell(row=i, column=1, value=k)
            ws.cell(row=i, column=2, value=v)
    for sheet, items in (rows or {}).items():
        ws = wb[sheet]
        hdr = [c.value for c in ws[1]]
        for d in items:
            ws.append([d.get(h, "") for h in hdr])
    wb.save(path)


def make_baseline(root, with_ds=True):
    b = os.path.join(root, "outputs", BASE)
    os.makedirs(os.path.join(b, "_internal"))
    inv = os.path.join(b, "_internal", "inventory.xlsx")
    sh("build-inventory.py", "--out", inv)
    fill(inv, {"version_type": "BASELINE", "version_folder": BASE}, {
        "01_Function": [{"Function ID": "F-001", "Function": "Dat hang"}],
        "02_Screen": [{"Screen ID": "SC-001", "Screen Name": "Gio hang"},
                      {"Screen ID": "SC-002", "Screen Name": "Thanh toan"}],
        "03_DB_Tables": [{"Table": "orders"}, {"Table": "users"}],
        "04_DB_Columns": [{"Table": "orders", "Column": "id"},
                          {"Table": "orders", "Column": "status"},
                          {"Table": "users", "Column": "email"}],
        "07_API": [{"API ID": "API-001", "Method": "POST", "Path / Schedule": "/orders"}],
        "09_Integration": [{"EXT ID": "EXT-001", "Name": "VNPay"}],
        "10_Site": [{"Site ID": "WEB-01", "URL": "https://shop.example"}],
    })
    if with_ds:
        ds = os.path.join(b, "04_DesignSystem")
        os.makedirs(ds)
        json.dump({"color": {"status": {"error": {"$value": "#CF222E"}},
                             "primary": "#1A7F37"}},
                  open(os.path.join(ds, "tokens.json"), "w"))
        open(os.path.join(ds, "components.md"), "w").write(
            "# Components\n\n| Component | Variant |\n|---|---|\n| Button | primary |\n"
            "| `TextField` | default |\n")
    return b


def row(iid, ct, ref, item, **kw):
    d = {"Impact ID": iid, "Change Type": ct, "Baseline Ref": ref, "Item": item,
         "Change Description": "Mo ta thay doi cho %s" % item,
         "Impact On Current": "Anh huong toi luong hien tai", "Conflict": "No",
         "Risk": "Low", "Evidence": "CR.pdf muc 2.1"}
    d.update(kw)
    return d


def valid_cr():
    summary = {"cr_id": "CR-001", "cr_title": "Them xac thuc OTP",
               "baseline_version": BASE, "cr_version": "ver2_021026_CR-001-otp",
               "source_type": "FILE", "source_ref": "input/CR-001.pdf",
               "received_date": "02/10/2026", "requested_by": "KH A",
               "summary": "Them OTP truoc khi dat hang", "overall_risk": "Medium",
               "recommendation": "Lam theo 2 pha"}
    rows = {
        "01_System": [row("IMP-001", "UPD", "API-001", "POST /orders")],
        "02_DB": [row("IMP-002", "NEW", "column:orders.otp_code", "orders.otp_code"),
                  row("IMP-003", "UPD", "column:orders.status", "orders.status",
                      Conflict="Yes", **{"Conflict Detail": "Them trang thai PENDING_OTP",
                                         "Open Q": "CQ-001", "Risk": "High"})],
        "03_Business": [row("IMP-004", "UPD", "F-001", "Dat hang")],
        "04_Screen": [row("IMP-005", "NEW", "—", "Man OTP"),
                      row("IMP-006", "UPD", "SC-001", "Gio hang")],
        "05_ThirdParty": [row("IMP-007", "NONE", "—", "—", Evidence="",
                              **{"Change Description": "CR khong them tich hop, khong cham EXT-001"})],
        "06_Mockup": [row("IMP-008", "NEW", "DS:color.status.error;DS-component:Button", "Man OTP")],
        "07_Questions": [{"Q ID": "CQ-001", "Question": "Gia tri status moi?",
                          "Why It Matters": "Bao cao cu loc theo status", "Axis": "DB",
                          "Owner": "KH", "Status": "Open"}],
    }
    return summary, rows


def find(rows, iid):
    for items in rows.values():
        for d in items:
            if d.get("Impact ID") == iid:
                return d
    raise KeyError(iid)


def m_set(iid, **kw):
    def f(s, r):
        find(r, iid).update(kw)
    return f


def m_summary(**kw):
    def f(s, r):
        s.update(kw)
    return f


def m_clear(sheet):
    def f(s, r):
        r[sheet] = []
    return f


def m_add(sheet, d):
    def f(s, r):
        r[sheet].append(d)
    return f


# (ten, mutation, check, muc mong doi)
CASES = [
    ("truc ThirdParty bo trong", m_clear("05_ThirdParty"), "3", "FAIL"),
    ("NONE giai thich qua ngan", m_set("IMP-007", **{"Change Description": "khong"}), "3", "FAIL"),
    ("UPD man hinh SC-999 khong ton tai", m_set("IMP-006", **{"Baseline Ref": "SC-999"}), "5", "FAIL"),
    ("DEL bang khong ton tai", m_set("IMP-003", **{"Change Type": "DEL", "Baseline Ref": "table:ghost"}), "5", "FAIL"),
    ("NEW cot trung ten khong Conflict=Yes", m_set("IMP-002", **{"Baseline Ref": "column:orders.status"}), "6", "FAIL"),
    ("NEW cot vao bang khong ton tai", m_set("IMP-002", **{"Baseline Ref": "column:carts.x"}), "6", "FAIL"),
    ("High risk khong Note/Open Q", m_set("IMP-001", Risk="High"), "8", "FAIL"),
    ("Open Q tro CQ khong ton tai", m_set("IMP-004", **{"Open Q": "CQ-009"}), "9", "FAIL"),
    ("CQ sai dang", m_add("07_Questions", {"Q ID": "Q-1", "Question": "x"}), "9", "FAIL"),
    ("thieu key summary requested_by", m_summary(requested_by=""), "1", "FAIL"),
    ("baseline_version lech", m_summary(baseline_version="ver0_010126_baseline"), "1", "FAIL"),
    ("source_type sai enum", m_summary(source_type="EMAIL"), "1", "FAIL"),
    ("mockup khong bam DS", m_set("IMP-008", **{"Baseline Ref": "—"}), "10d", "FAIL"),
    ("mockup DS token khong ton tai", m_set("IMP-008", **{"Baseline Ref": "DS:color.nope"}), "6", "FAIL"),
    ("mockup Note DS chua co -> WARN", m_set("IMP-008", **{"Baseline Ref": "—", "Note": "Design system chua co OTP input"}), "10d", "WARN"),
    ("o bat buoc trong", m_set("IMP-004", **{"Impact On Current": ""}), "13", "FAIL"),
    ("Impact ID trung", m_set("IMP-004", **{"Impact ID": "IMP-001"}), "2", "FAIL"),
    ("Risk sai enum", m_set("IMP-004", Risk="Critical"), "4", "FAIL"),
    ("Conflict=Yes thieu detail", m_set("IMP-004", Conflict="Yes"), "7", "FAIL"),
    ("Evidence trong", m_set("IMP-005", Evidence=""), "11", "FAIL"),
    ("UPD man hinh ref F-", m_set("IMP-006", **{"Baseline Ref": "F-001"}), "10a", "FAIL"),
    ("DB ref SC-", m_set("IMP-002", **{"Baseline Ref": "SC-001"}), "10b", "FAIL"),
    ("ThirdParty ref API-", m_add("05_ThirdParty", row("IMP-009", "UPD", "API-001", "x")), "10c", "FAIL"),
]


def write_cr(path, summary, rows):
    if os.path.exists(path):
        os.remove(path)
    code, out = sh("build-inventory.py", "--cr", "--out", path)
    if code:
        raise SystemExit(out)
    fill(path, summary, rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("Thieu openpyxl", file=sys.stderr)
        return 2
    root = tempfile.mkdtemp(prefix="selftest-cr-")
    total = passed = 0
    lines = []

    def record(name, ok, detail=""):
        nonlocal total, passed
        total += 1
        passed += ok
        lines.append("%s %s%s" % ("PASS" if ok else "FAIL", name,
                                  (" — " + detail) if detail and not ok else ""))

    try:
        base = make_baseline(root)
        crdir = os.path.join(root, "outputs", "ver2_021026_CR-001-otp")
        os.makedirs(crdir)
        cr = os.path.join(crdir, "CR-001_Impact.xlsx")
        s0, r0 = valid_cr()
        write_cr(cr, s0, r0)
        code, out = sh("verify-cr-impact.py", cr, "--baseline", base)
        res = results(out)
        bad = [k for k, v in res.items() if v != "PASS"]
        record("fixture dung -> PASS", code == 0 and not bad, "khong PASS: %s" % bad if bad else "")

        for name, mut, chk, level in CASES:
            s, r = copy.deepcopy(s0), copy.deepcopy(r0)
            mut(s, r)
            write_cr(cr, s, r)
            code, out = sh("verify-cr-impact.py", cr, "--baseline", base)
            got = results(out).get(chk)
            want_code = 1 if level == "FAIL" else 0
            record("%s -> check %s %s" % (name, chk, level), got == level and code == want_code,
                   "" if got == level else "nhan %s (exit %d)" % (got, code))

        # CR-vs-CR: CR-002 cung UPD SC-001 -> WARN 12, exit 0
        write_cr(cr, s0, r0)
        other = os.path.join(root, "CR-002_Impact.xlsx")
        s2, r2 = valid_cr()
        s2["cr_id"] = "CR-002"
        write_cr(other, s2, r2)
        code, out = sh("verify-cr-impact.py", cr, "--baseline", base, "--other-cr", other)
        got = results(out).get("12")
        record("CR-vs-CR cung SC-001 -> check 12 WARN", got == "WARN" and code == 0,
               "nhan %s (exit %d)" % (got, code))

        # Baseline khong co 04_DesignSystem -> 10d chi WARN
        shutil.rmtree(os.path.join(base, "04_DesignSystem"))
        s, r = copy.deepcopy(s0), copy.deepcopy(r0)
        find(r, "IMP-008")["Baseline Ref"] = "—"
        write_cr(cr, s, r)
        code, out = sh("verify-cr-impact.py", cr, "--baseline", base)
        got = results(out).get("10d")
        record("baseline khong DS -> check 10d WARN", got == "WARN" and code == 0,
               "nhan %s (exit %d)" % (got, code))
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
