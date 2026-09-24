#!/usr/bin/env python3
"""GATE V9 — self-test: chung minh V1/V2/V3/V5/V8 that su bat loi.

  python3 selftest-gates.py [--keep]

Cach lam: dung 1 bo fixture DUNG -> khang dinh moi gate PASS. Sau do tiem tung loi
da biet vao ban copy -> khang dinh dung check so may FAIL.

Gate bao PASS chua chung minh duoc gi: mot gate hong cung "PASS" moi thu.
Chay lai sau MOI lan sua verify-*.py.
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
import inv_schema as S  # noqa: E402


def sh(script, *args):
    p = subprocess.run([sys.executable, os.path.join(HERE, script)] + list(args),
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def failed_checks(output):
    nums = []
    for line in output.splitlines():
        if "**FAIL**" in line and line.startswith("|"):
            try:
                nums.append(int(line.split("|")[1].strip()))
            except ValueError:
                pass
    return nums


# ---------- fixture ----------
def build_inventory(path, root):
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    for name, cols in S.SHEETS.items():
        ws = wb.create_sheet(name)
        ws.append(cols)

    meta = {
        "system_name": "Fixture", "customer": "ABC", "doc_version": "v1",
        "generated_date": "2026-09-23", "previous_version": "—", "run_mode": "FULL",
        "g0_scope": "Toan he thong", "g1_websites": "https://stg.example.jp",
        "g2_crawl_mode": "READ_ONLY", "g3_accounts": "admin,user",
        "g4_db": "DUMP", "g5_source": "FULL_REPO", "g6_detail": "STANDARD",
        "g7_lang": "VN", "g7_audience": "Noi bo", "g8_format": "docx+xlsx",
        "env_observed": "Chrome 129", "crawl_budget_used": "10/200 URL",
        "forbidden_zones": "—",
    }
    for k, v in meta.items():
        wb["00_Meta"].append([k, v])

    os.makedirs(os.path.join(root, "evidence"), exist_ok=True)
    for n in ("EV-0001", "EV-0002"):
        with open(os.path.join(root, "evidence", n + ".png"), "wb") as fh:
            fh.write(b"\x89PNG\r\n\x1a\n" + b"0" * 3000)

    wb["05_Evidence"].append(["EV-0001", "screenshot", "https://stg.example.jp/login",
                              "2026-09-23T14:02+07", "test_user", "evidence/EV-0001.png", ""])
    wb["05_Evidence"].append(["EV-0002", "screenshot", "https://stg.example.jp/orders",
                              "2026-09-23T14:10+07", "test_user", "evidence/EV-0002.png", ""])
    wb["05_Evidence"].append(["EV-0003", "code-ref", "src/auth/login.ts#L10-L40",
                              "", "", "", "ham login"])

    wb["02_Screen"].append(["SC-001", "/login", "Dang nhap", "Form", "User", "—",
                            "F-001", "EV-0001", 6, "Confirmed", ""])
    wb["02_Screen"].append(["SC-002", "/orders", "Danh sach don", "List", "User",
                            "SC-001", "F-002", "EV-0002", 12, "Confirmed", ""])

    wb["01_Function"].append(["F-001", "Auth", "Dang nhap", "User",
                              "Xac thuc va tao session", "/login", "SC-001", "users",
                              "EV-0001;EV-0003", "UI+Code", "Confirmed", "—", ""])
    wb["01_Function"].append(["F-002", "Order", "Xem danh sach don", "User",
                              "Hien thi don cua user", "/orders", "SC-002", "orders",
                              "EV-0002", "UI", "Confirmed", "—", ""])
    wb["01_Function"].append(["F-003", "Batch", "Dong bo ton kho", "System",
                              "Cron chay hang dem", "0 2 * * *", S.NO_SCREEN, "orders",
                              "", "Code", "Inferred", "Q-001", ""])

    wb["03_DB_Tables"].append(["users", "Tai khoan", "id", "—", "email,status",
                               "1000", "F-001", "EV-0003", "High", ""])
    wb["03_DB_Tables"].append(["orders", "Don hang", "id", "user_id->users.id",
                               "status,total", "5000", "F-002,F-003", "EV-0003", "High", ""])
    wb["04_DB_Columns"].append(["users", "email", "VARCHAR(255)", "No", "—", "No", "—",
                                "Email dang nhap", "F-001", "EV-0003", "High"])

    wb["06_OpenQuestions"].append(["Q-001", "Inference", "Muc dich batch dong bo ton kho",
                                   "Chi thay ten job trong crontab", "Hoi maintainer",
                                   "BrSE", "Open", ""])
    wb.save(path)


def build_flow(path):
    json.dump({
        "title": "Fixture flow",
        "nodes": [
            {"id": "n1", "label": "User", "kind": "actor", "row": 0, "ref": ""},
            {"id": "n2", "label": "Dang nhap", "kind": "screen", "row": 1, "ref": "SC-001"},
            {"id": "n3", "label": "Database", "kind": "db", "row": 2, "ref": "table:users"},
        ],
        "edges": [{"from": "n1", "to": "n2"}, {"from": "n2", "to": "n3"}],
        "explanation": ["1. User mo man dang nhap.", "2. Dang nhap ghi vao database."],
    }, open(path, "w", encoding="utf8"), ensure_ascii=False)


def build_buglist(path):
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    for name, cols in S.BUG_SHEETS.items():
        wb.create_sheet(name).append(cols)
    for k, v in (("g13_scan_scope", "Blackbox+Code+DB"), ("g13_recipient", "Noi bo truoc")):
        wb["00_Meta"].append([k, v])
    wb["Bugs"].append([
        "BUG-001", "Nut Luu khong phan hoi", "SC-002", "/orders", "Functional",
        "S2 Major", "1. Mo /orders\n2. Bam Luu\n3. Khong co gi xay ra",
        "Luu thanh cong", "Khong phan hoi", "EV-0002", "Yes — 3/3", "Playwright",
        "User khong luu duoc thay doi", "Chrome 129 · 2026-09-23", "Yes", "Yes", "Open", ""])
    wb["Suspected"].append([
        "BUG-002", "Cham khi tai danh sach lon", "SC-002", "/orders", "Performance",
        "S3 Minor", "1. Mo /orders\n2. Cuon toi cuoi", "Tai nhanh", "Doi khi cham",
        "EV-0002", "Intermittent", "Playwright", "Anh huong trai nghiem",
        "Chrome 129", "Unknown", "Internal only", "Open", ""])
    wb["Observations"].append([
        "OBS-001", "Cookie thieu flag Secure", "SC-001",
        "Quan sat header Set-Cookie khong co Secure", "EV-0001",
        "Can pentest xac nhan", ""])
    wb.save(path)


# ---------- cac ca tiem loi ----------
def mutate(path, fn):
    from openpyxl import load_workbook
    wb = load_workbook(path)
    fn(wb)
    wb.save(path)


CASES = []


def case(gate, name, expect_check):
    def deco(fn):
        CASES.append((gate, name, expect_check, fn))
        return fn
    return deco


@case("V1", "Tro toi EV ma (EV-9999)", 8)
def _(ctx):
    mutate(ctx["inv"], lambda wb: wb["01_Function"].cell(row=2, column=9, value="EV-9999"))


@case("V1", "File artifact khong ton tai", 5)
def _(ctx):
    os.remove(os.path.join(ctx["root"], "evidence", "EV-0001.png"))


@case("V1", "EV ID trung nhau", 2)
def _(ctx):
    mutate(ctx["inv"], lambda wb: wb["05_Evidence"].cell(row=3, column=1, value="EV-0001"))


@case("V2", "Function Confirmed nhung khong co bang chung", 6)
def _(ctx):
    mutate(ctx["inv"], lambda wb: wb["01_Function"].cell(row=2, column=9, value=""))


@case("V2", "Function Inferred nhung khong khai Open Question", 7)
def _(ctx):
    mutate(ctx["inv"], lambda wb: wb["01_Function"].cell(row=4, column=12, value="—"))


@case("V2", "Screen ID tro toi man khong ton tai", 8)
def _(ctx):
    mutate(ctx["inv"], lambda wb: wb["01_Function"].cell(row=2, column=7, value="SC-999"))


@case("V2", "De o trong thay vi ghi UNKNOWN", 11)
def _(ctx):
    mutate(ctx["inv"], lambda wb: wb["01_Function"].cell(row=2, column=4, value=""))


@case("V2", "Khai khong co DB nhung van co bang DB", 12)
def _(ctx):
    def f(wb):
        for r in range(2, wb["00_Meta"].max_row + 1):
            if wb["00_Meta"].cell(row=r, column=1).value == "g4_db":
                wb["00_Meta"].cell(row=r, column=2, value="NONE")
    mutate(ctx["inv"], f)


@case("V2", "Cot Meaning High confidence nhung khong co code-ref", 14)
def _(ctx):
    mutate(ctx["inv"], lambda wb: wb["04_DB_Columns"].cell(row=2, column=10, value="EV-0001"))


@case("V5", "Node tro toi Function khong ton tai", 4)
def _(ctx):
    f = json.load(open(ctx["flow"], encoding="utf8"))
    f["nodes"][1]["ref"] = "F-999"
    json.dump(f, open(ctx["flow"], "w", encoding="utf8"), ensure_ascii=False)


@case("V5", "Node mo coi khong noi voi node nao", 6)
def _(ctx):
    f = json.load(open(ctx["flow"], encoding="utf8"))
    f["nodes"].append({"id": "n9", "label": "Database", "kind": "db",
                       "row": 3, "ref": "table:users"})
    json.dump(f, open(ctx["flow"], "w", encoding="utf8"), ensure_ascii=False)


@case("V8", "Bug chua tai hien duoc lot sheet gui khach", 7)
def _(ctx):
    mutate(ctx["bug"], lambda wb: wb["Bugs"].cell(row=2, column=11, value="No"))


@case("V8", "Quy ket Security ma khong co PoC", 8)
def _(ctx):
    def f(wb):
        wb["Bugs"].cell(row=2, column=5, value="Security")
        wb["Bugs"].cell(row=2, column=11, value="Intermittent")
    mutate(ctx["bug"], f)


@case("V8", "Repro Steps chi co 1 buoc", 5)
def _(ctx):
    mutate(ctx["bug"], lambda wb: wb["Bugs"].cell(row=2, column=7, value="1. Mo /orders"))


@case("V8", "Bug trung lap", 11)
def _(ctx):
    def f(wb):
        row = [wb["Bugs"].cell(row=2, column=c).value
               for c in range(1, len(S.BUG_SHEETS["Bugs"]) + 1)]
        row[0] = "BUG-003"
        wb["Bugs"].append(row)
    mutate(ctx["bug"], f)


def run_gates(ctx):
    """Chay 4 gate, tra ve {gate: (rc, failed_checks)}."""
    out = {}
    rc, o = sh("verify-evidence.py", ctx["inv"], "--root", ctx["root"])
    out["V1"] = (rc, failed_checks(o))
    rc, o = sh("verify-inventory.py", ctx["inv"])
    out["V2"] = (rc, failed_checks(o))
    rc, o = sh("verify-flow-png.py", ctx["flow"], "--inventory", ctx["inv"])
    out["V5"] = (rc, failed_checks(o))
    rc, o = sh("verify-bug-list.py", ctx["bug"], "--inventory", ctx["inv"])
    out["V8"] = (rc, failed_checks(o))
    return out


def make_ctx(root):
    os.makedirs(root, exist_ok=True)
    ctx = {"root": root,
           "inv": os.path.join(root, "inventory.xlsx"),
           "flow": os.path.join(root, "flow.json"),
           "bug": os.path.join(root, "buglist.xlsx")}
    build_inventory(ctx["inv"], root)
    build_flow(ctx["flow"])
    build_buglist(ctx["bug"])
    return ctx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    base = tempfile.mkdtemp(prefix="selftest-gates-")
    results = []

    # 0 — fixture dung phai PASS het
    ctx = make_ctx(os.path.join(base, "good"))
    got = run_gates(ctx)
    for gate, (rc, fails) in got.items():
        results.append(("baseline", "Fixture dung -> %s PASS" % gate, not fails,
                        "" if not fails else "FAIL o check %s" % fails))

    # 1 — tung ca tiem loi
    for i, (gate, name, expect, fn) in enumerate(CASES):
        d = os.path.join(base, "case%02d" % i)
        shutil.copytree(os.path.join(base, "good"), d)
        c = {"root": d, "inv": os.path.join(d, "inventory.xlsx"),
             "flow": os.path.join(d, "flow.json"),
             "bug": os.path.join(d, "buglist.xlsx")}
        fn(c)
        rc, fails = run_gates(c)[gate]
        ok = expect in fails
        results.append((gate, name, ok,
                        "ky vong check %d FAIL, thuc te FAIL: %s" % (expect, fails or "khong co")))

    # 2 — gate V3 phai FAIL tren template goc (con placeholder)
    tpl = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..",
                                       "templates", "high-level-template.docx"))
    if os.path.isfile(tpl):
        rc, o = sh("verify-high-level.py", tpl, "--inventory", ctx["inv"])
        fails = failed_checks(o)
        results.append(("V3", "Template goc (con placeholder) phai FAIL check 2",
                        2 in fails, "FAIL: %s" % fails))
    else:
        results.append(("V3", "Template goc", False, "khong tim thay %s" % tpl))

    print("# GATE V9 — Self-test\n")
    print("| Gate | Ca kiem tra | Ket qua | Chi tiet |")
    print("|---|---|---|---|")
    for gate, name, ok, detail in results:
        print("| %s | %s | %s | %s |" % (gate, name, "PASS" if ok else "**FAIL**",
                                         "" if ok else detail))
    bad = sum(1 for r in results if not r[2])
    print("\n**%d ca · %d PASS · %d FAIL**" % (len(results), len(results) - bad, bad))
    if a.keep:
        print("\nFixture giu tai: %s" % base)
    else:
        shutil.rmtree(base, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
