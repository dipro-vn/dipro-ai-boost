#!/usr/bin/env python3
"""GATE V9 — self-test: chung minh V1/V2/V3/V5/V8 that su bat loi.

  python3 selftest-gates.py [--keep]

Cach lam: dung 1 thu muc version DUNG (inventory du 12 sheet, repo gia, evidence, flow,
bug list, index.json, overview docx) -> khang dinh moi gate PASS. Sau do tiem tung loi
da biet vao ban copy -> khang dinh dung check so may FAIL.
Gate bao PASS chua chung minh duoc gi: mot gate hong cung "PASS" moi thu.
Chay lai sau MOI lan sua verify-*.py / render-overview-docx.py / build-version-index.py.
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

VER = "ver1_011026_baseline"


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


def paths(base):
    v = os.path.join(base, VER)
    i = os.path.join(v, "_internal")
    return {"base": base, "ver": v, "root": i,
            "inv": os.path.join(i, "inventory.xlsx"),
            "flow": os.path.join(i, "flow", "flow.json"),
            "flow_png": os.path.join(i, "flow", "flow.png"),
            "nar": os.path.join(i, "narrative.json"),
            "index": os.path.join(i, "index.json"),
            "bug": os.path.join(v, "07_BugList", "BugList_Fixture_ver1.xlsx"),
            "docx": os.path.join(v, "06_Overview", "Overview_Fixture_ver1.docx")}


# ---------- fixture ----------
def write_lines(path, n):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf8") as fh:
        fh.write("".join("// line %d\n" % i for i in range(1, n + 1)))


def fake_png(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(4, 2))
        ax.plot([0, 1], [0, 1])
        fig.savefig(path, dpi=60)
        plt.close(fig)
    except ImportError:
        import base64
        with open(path, "wb") as fh:  # 1x1 PNG + dem cho > 2KB
            fh.write(base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="))


def new_wb(sheets):
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    for name, cols in sheets.items():
        wb.create_sheet(name).append(cols)
    return wb


def build_inventory(p):
    wb = new_wb(S.SHEETS)
    fe, be = os.path.join(p["base"], "repos", "fe"), os.path.join(p["base"], "repos", "be")
    write_lines(os.path.join(fe, "src", "pages", "login.tsx"), 50)
    write_lines(os.path.join(be, "src", "order", "order.service.ts"), 120)

    meta = {k: "—" for k in S.META_KEYS}
    meta.update({
        "system_name": "Fixture", "customer": "Cong ty ABC", "version_label": "ver1",
        "version_folder": VER, "version_type": "BASELINE", "generated_date": "2026-10-01",
        "run_mode": "FULL", "scope": "Toan he thong",
        "websites": "WEB-01=https://stg.example.jp", "accounts": "test_admin,test_user",
        "crawl_mode": "READ_ONLY", "source_repos": "REPO-01=fe(FE→WEB-01);REPO-02=be(BE)",
        "db_mode": "DUMP", "figma_output_url": "https://www.figma.com/design/abc/Fixture",
        "bug_list": "YES", "lang": "VN", "audience": "Noi bo",
        "env_observed": "Chrome 129", "crawl_budget_used": "10/200 URL",
        "bug_recipient": "PM", "bug_scan_scope": "Blackbox+Code"})
    for k in S.META_KEYS:
        wb["00_Meta"].append([k, meta[k]])

    for n in ("EV-0001", "EV-0002"):
        fake_png(os.path.join(p["root"], "evidence", n + ".png"))
    ev = wb["05_Evidence"]
    ev.append(["EV-0001", "screenshot", "https://stg.example.jp/login",
               "2026-10-01T14:02+07", "test_user", "evidence/EV-0001.png", ""])
    ev.append(["EV-0002", "screenshot", "https://stg.example.jp/orders",
               "2026-10-01T14:10+07", "test_user", "evidence/EV-0002.png", ""])
    ev.append(["EV-0003", "code-ref", "REPO-01:src/pages/login.tsx#L10-L40", "", "", "", "login"])
    ev.append(["EV-0004", "code-ref", "REPO-02:src/order/order.service.ts#L88-L104",
               "", "", "", "order list"])
    ev.append(["EV-0005", "db-query", "schema:dump.sql#L12", "", "", "", "orders"])

    wb["10_Site"].append(["WEB-01", "Admin site", "https://stg.example.jp", "STG",
                          "test_admin;test_user", "READ_ONLY", "REPO-01", 2, ""])
    wb["11_Repo"].append(["REPO-01", fe, "FE", "React 18", "WEB-01", ""])
    wb["11_Repo"].append(["REPO-02", be, "BE", "NestJS 10", "WEB-01", ""])

    wb["02_Screen"].append(["SC-001", "WEB-01", "/login", "Dang nhap", "Form", "User", "—",
                            "F-001", "EV-0001", 6, "Confirmed", ""])
    wb["02_Screen"].append(["SC-002", "WEB-01", "/orders", "Danh sach don", "List", "User",
                            "SC-001", "F-002", "EV-0002", 12, "Confirmed", ""])

    fn = wb["01_Function"]
    fn.append(["F-001", "Auth", "Dang nhap", "User", "Xac thuc va tao session", "/login",
               "SC-001", "users", "EV-0001;EV-0003", "UI+Code", "Confirmed", "—", ""])
    fn.append(["F-002", "Order", "Xem danh sach don", "User", "Hien thi don cua user",
               "/orders", "SC-002", "orders", "EV-0002", "UI", "Confirmed", "—", ""])
    fn.append(["F-003", "Batch", "Dong bo ton kho", "System", "Cron chay hang dem",
               "0 2 * * *", S.NO_SCREEN, "orders", "", "Code", "Inferred", "Q-001", ""])

    wb["03_DB_Tables"].append(["users", "Tai khoan", "id", "—", "email,status", "1000",
                               "F-001", "EV-0003", "High", ""])
    wb["03_DB_Tables"].append(["orders", "Don hang", "id", "user_id->users.id", "status,total",
                               "5000", "F-002,F-003", "EV-0005", "High", ""])
    wb["04_DB_Columns"].append(["users", "email", "VARCHAR(255)", "No", "—", "No", "—", "255",
                                "email", "UNIQUE", "Email dang nhap", "F-001", "EV-0003", "High"])
    wb["04_DB_Columns"].append(["orders", "user_id", "BIGINT", "No", "users.id", "No", "—", "—",
                                "—", "FK", "Chu don", "F-002", "EV-0005", "Medium"])

    q = wb["06_OpenQuestions"]
    q.append(["Q-001", "Inference", "Muc dich batch dong bo ton kho",
              "Chi thay ten job trong crontab", "Hoi maintainer", "BrSE", "Open", ""])
    q.append(["Q-002", "Unknown", "Handler cua batch API-002", "Khong thay file job",
              "Hoi maintainer", "BrSE", "Open", ""])

    api = wb["07_API"]
    api.append(["API-001", "Order", "API", "GET", "/api/orders", "Lay danh sach don", "JWT",
                "REPO-02:src/order/order.service.ts#L88-L104", "REPO-02", "SC-002", "orders",
                "EV-0004", "Confirmed", "—", ""])
    api.append(["API-002", "Batch", "BATCH", "CRON", "0 2 * * *", "Dong bo ton kho", "—",
                S.UNKNOWN, "REPO-02", "—", "orders", "—", "To verify", "Q-002", ""])
    f8 = wb["08_API_Fields"]
    f8.append(["API-001", "REQUEST", "query", "status", "string", "No", "enum", "Loc trang thai",
               "EV-0004"])
    f8.append(["API-001", "RESPONSE", "response-body", "items", "array", "Yes", "—",
               "Danh sach don", "EV-0004"])
    wb["09_Integration"].append(["EXT-001", "Stripe", "Payment", "Thanh toan the", "OUTBOUND",
                                 "API-001", "STRIPE_SECRET_KEY;STRIPE_WEBHOOK_SECRET", "EV-0004",
                                 "Confirmed", ""])
    os.makedirs(os.path.dirname(p["inv"]), exist_ok=True)
    wb.save(p["inv"])


def build_flow(p):
    os.makedirs(os.path.dirname(p["flow"]), exist_ok=True)
    json.dump({
        "title": "Fixture flow",
        "nodes": [
            {"id": "n1", "label": "User", "kind": "actor", "row": 0, "ref": ""},
            {"id": "n2", "label": "Admin site", "kind": "site", "row": 1, "ref": "WEB-01"},
            {"id": "n3", "label": "Order API", "kind": "api", "row": 2, "ref": "API-001"},
            {"id": "n4", "label": "Stripe", "kind": "external", "row": 2, "ref": "EXT-001"},
            {"id": "n5", "label": "Database", "kind": "db", "row": 3, "ref": "table:orders"},
        ],
        "edges": [{"from": "n1", "to": "n2"}, {"from": "n2", "to": "n3"},
                  {"from": "n3", "to": "n4"}, {"from": "n3", "to": "n5"}],
        "explanation": ["1. User mo Admin site.", "2. Admin site goi Order API.",
                        "3. Order API goi Stripe va doc Database."],
    }, open(p["flow"], "w", encoding="utf8"), ensure_ascii=False)
    fake_png(p["flow_png"])


def build_buglist(p):
    wb = new_wb(S.BUG_SHEETS)
    for k, v in (("bug_scan_scope", "Blackbox+Code+DB"), ("bug_recipient", "PM noi bo")):
        wb["00_Meta"].append([k, v])
    wb["Bugs"].append([
        "BUG-001", "Nut Luu khong phan hoi", "SC-002", "/orders", "Functional",
        "Medium", "1. Mo /orders\n2. Bam Luu\n3. Khong co gi xay ra",
        "Luu thanh cong", "Khong phan hoi", "EV-0002", "Yes — 3/3", "Playwright",
        "User khong luu duoc thay doi", "Chrome 129 · 2026-10-01", "Yes", "Yes", "Open", ""])
    wb["Suspected"].append([
        "BUG-002", "Cham khi tai danh sach lon", "SC-002", "/orders", "Performance",
        "Medium", "1. Mo /orders\n2. Cuon toi cuoi", "Tai nhanh", "Doi khi cham",
        "EV-0002", "Intermittent", "Playwright", "Anh huong trai nghiem",
        "Chrome 129", "Unknown", "Internal only", "Open", ""])
    wb["Observations"].append([
        "OBS-001", "Cookie thieu flag Secure", "SC-001",
        "Header Set-Cookie khong co Secure", "EV-0001", "Can pentest xac nhan", ""])
    os.makedirs(os.path.dirname(p["bug"]), exist_ok=True)
    wb.save(p["bug"])


def build_outputs(p):
    from openpyxl import Workbook
    v = p["ver"]
    wb = Workbook()
    wb.active.title = "Screen Index"
    for title in ("SC-001", "SC-002"):
        wb.create_sheet(title)["F6"] = "WORKING_SCREEN"
    os.makedirs(os.path.join(v, "01_Screens"), exist_ok=True)
    wb.save(os.path.join(v, "01_Screens", "BasicDesign_WEB-01_ver1.xlsx"))
    for sub, name in (("02_API", "API_Doc_Fixture_ver1.xlsx"), ("03_DB", "DB_Doc_Fixture_ver1.xlsx")):
        os.makedirs(os.path.join(v, sub), exist_ok=True)
        Workbook().save(os.path.join(v, sub, name))
    fake_png(os.path.join(v, "02_API", "CodeMap_Fixture_ver1.png"))
    fake_png(os.path.join(v, "03_DB", "ERD_Fixture_ver1.png"))
    os.makedirs(os.path.join(v, "04_DesignSystem", "project"), exist_ok=True)   # O4 = format artifact Design System
    json.dump({"v": 3, "layout": "files", "title": "Fixture"},
              open(os.path.join(v, "04_DesignSystem", "project", "design-system.json"), "w"))
    open(os.path.join(v, "04_DesignSystem", "STATUS.md"), "w", encoding="utf8").write(
        "# Design System — Fixture\n\n- Trạng thái: DRAFT\n- Artifact: https://claude.ai/artifact/FixtureDs01\n"
        "- Nguồn: website WEB-01\n\n## Thiếu (TBD)\n\n| D# | Token / component | Ghi chú |\n|---|---|---|\n"
        "| D1 | primary-hover | khong quan sat duoc |\n| D6 | Toast | khong quan sat duoc |\n")
    os.makedirs(os.path.join(v, "05_Figma"), exist_ok=True)
    open(os.path.join(v, "05_Figma", "figma-links.md"), "w").write(
        "- SC-001 https://www.figma.com/design/abc/F?node-id=1-2\n"
        "- SC-002 https://www.figma.com/design/abc/F?node-id=1-3\n")
    json.dump({"project_name": "Fixture", "customer": "Cong ty ABC",
               "product_overview": "He thong quan ly don hang noi bo.",
               "actors": [{"actor": "User", "role": "Nhan vien", "main_usage": "Xem don"}],
               "system_composition": ["Frontend: React (REPO-01)", "Backend: NestJS (REPO-02)"]},
              open(p["nar"], "w", encoding="utf8"), ensure_ascii=False)
    gdir = os.path.join(p["root"], "gates")
    os.makedirs(gdir, exist_ok=True)
    for name in ("v-bd-WEB-01", "v-api", "v-db"):
        open(os.path.join(gdir, name + ".md"), "w").write(
            "# %s\n\n**5 checks · 5 PASS · 0 FAIL · 0 WARN**\n" % name)


def render_overview(p):
    sh("build-version-index.py", p["ver"])
    return sh("render-overview-docx.py", "--inventory", p["inv"], "--narrative", p["nar"],
              "--index", p["index"], "--flow", p["flow"], "--flow-png", p["flow_png"],
              "--codemap-png", os.path.join(p["ver"], "02_API", "CodeMap_Fixture_ver1.png"),
              "--erd-png", os.path.join(p["ver"], "03_DB", "ERD_Fixture_ver1.png"),
              "--out", p["docx"])


def make_fixture(base):
    p = paths(base)
    build_inventory(p)
    build_flow(p)
    build_buglist(p)
    build_outputs(p)
    rc, o = render_overview(p)
    if rc:
        raise SystemExit("Render overview loi:\n" + o)
    return p


# ---------- cac ca tiem loi ----------
def mutate(path, fn):
    from openpyxl import load_workbook
    wb = load_workbook(path)
    fn(wb)
    wb.save(path)


def set_cell(sheet, row, col_name, value, schema=None):
    cols = (schema or S.SHEETS)[sheet]
    return lambda wb: wb[sheet].cell(row=row, column=cols.index(col_name) + 1, value=value)


def set_meta(key, value):
    def f(wb):
        for r in range(2, wb["00_Meta"].max_row + 1):
            if wb["00_Meta"].cell(row=r, column=1).value == key:
                wb["00_Meta"].cell(row=r, column=2, value=value)
    return f


def edit_json(path, fn):
    d = json.load(open(path, encoding="utf8"))
    fn(d)
    json.dump(d, open(path, "w", encoding="utf8"), ensure_ascii=False)


CASES = []


def case(gate, name, expect_check):
    def deco(fn):
        CASES.append((gate, name, expect_check, fn))
        return fn
    return deco


@case("V1", "Tro toi EV ma (EV-9999)", 8)
def _(p):
    mutate(p["inv"], set_cell("01_Function", 2, "Evidence", "EV-9999"))


@case("V1", "File artifact khong ton tai", 5)
def _(p):
    os.remove(os.path.join(p["root"], "evidence", "EV-0001.png"))


@case("V1", "EV ID trung nhau", 2)
def _(p):
    mutate(p["inv"], set_cell("05_Evidence", 3, "EV ID", "EV-0001"))


@case("V1", "code-ref tro toi repo khong co trong 11_Repo", 6)
def _(p):
    mutate(p["inv"], set_cell("05_Evidence", 4, "Locator", "REPO-09:src/pages/login.tsx#L10"))


@case("V1", "code-ref vuot qua so dong cua file", 6)
def _(p):
    mutate(p["inv"], set_cell("05_Evidence", 5, "Locator",
                              "REPO-02:src/order/order.service.ts#L88-L999"))


@case("V1", "code-ref thieu prefix REPO-xx", 6)
def _(p):
    mutate(p["inv"], set_cell("05_Evidence", 4, "Locator", "src/pages/login.tsx#L10"))


@case("V1", "db-query sai dinh dang locator", 10)
def _(p):
    mutate(p["inv"], set_cell("05_Evidence", 6, "Locator", "dump.sql line 12"))


@case("V2", "Function Confirmed nhung khong co bang chung", 6)
def _(p):
    mutate(p["inv"], set_cell("01_Function", 2, "Evidence", ""))


@case("V2", "Function Inferred nhung khong khai Open Question", 7)
def _(p):
    mutate(p["inv"], set_cell("01_Function", 4, "Open Q", "—"))


@case("V2", "Screen ID tro toi man khong ton tai", 8)
def _(p):
    mutate(p["inv"], set_cell("01_Function", 2, "Screen IDs", "SC-999"))


@case("V2", "De o trong thay vi ghi UNKNOWN", 11)
def _(p):
    mutate(p["inv"], set_cell("01_Function", 2, "Primary Actor", ""))


@case("V2", "Khai khong co DB nhung van co bang DB", 12)
def _(p):
    mutate(p["inv"], set_meta("db_mode", "NONE"))


@case("V2", "Cot Meaning High confidence nhung khong co code-ref", 14)
def _(p):
    mutate(p["inv"], set_cell("04_DB_Columns", 2, "Evidence", "EV-0001"))


@case("V2", "Screen tro toi Site khong ton tai", 24)
def _(p):
    mutate(p["inv"], set_cell("02_Screen", 2, "Site", "WEB-09"))


@case("V2", "10_Site.Screen Count lech so man hinh thuc te", 25)
def _(p):
    mutate(p["inv"], set_cell("10_Site", 2, "Screen Count", 5))


@case("V2", "API Confirmed khong co EV code-ref", 21)
def _(p):
    mutate(p["inv"], set_cell("07_API", 2, "Evidence", "EV-0002"))


@case("V2", "API To verify khong co Open Question", 22)
def _(p):
    mutate(p["inv"], set_cell("07_API", 3, "Open Q", "—"))


@case("V2", "08_API_Fields tro toi API khong ton tai", 23)
def _(p):
    mutate(p["inv"], set_cell("08_API_Fields", 2, "API ID", "API-999"))


@case("V2", "Config Keys chua gia tri (KEY=value)", 30)
def _(p):
    mutate(p["inv"], set_cell("09_Integration", 2, "Config Keys",
                              "STRIPE_SECRET_KEY" + "=" + "x" * 12))


@case("V2", "Config Keys chua chuoi token ngau nhien", 30)
def _(p):
    mutate(p["inv"], set_cell("09_Integration", 2, "Config Keys", "aB3d" * 6))


@case("V2", "API ID sai dinh dang", 17)
def _(p):
    mutate(p["inv"], set_cell("07_API", 3, "API ID", "API-1"))


@case("V5", "Node tro toi Function khong ton tai", 4)
def _(p):
    edit_json(p["flow"], lambda f: f["nodes"][1].update(ref="F-999"))


@case("V5", "Node tro toi API khong ton tai", 4)
def _(p):
    edit_json(p["flow"], lambda f: f["nodes"][2].update(ref="API-999"))


@case("V5", "Node mo coi khong noi voi node nao", 6)
def _(p):
    edit_json(p["flow"], lambda f: f["nodes"].append(
        {"id": "n9", "label": "Database", "kind": "db", "row": 4, "ref": "table:users"}))


@case("V8", "Bug chua tai hien duoc lot sheet gui khach", 7)
def _(p):
    mutate(p["bug"], set_cell("Bugs", 2, "Reproduced", "No", S.BUG_SHEETS))


@case("V8", "Quy ket Security ma khong co PoC", 8)
def _(p):
    def f(wb):
        set_cell("Bugs", 2, "Category", "Security", S.BUG_SHEETS)(wb)
        set_cell("Bugs", 2, "Reproduced", "Intermittent", S.BUG_SHEETS)(wb)
    mutate(p["bug"], f)


@case("V8", "Repro Steps chi co 1 buoc", 5)
def _(p):
    mutate(p["bug"], set_cell("Bugs", 2, "Repro Steps", "1. Mo /orders", S.BUG_SHEETS))


@case("V8", "Bug trung lap", 11)
def _(p):
    def f(wb):
        row = [wb["Bugs"].cell(row=2, column=c).value
               for c in range(1, len(S.BUG_SHEETS["Bugs"]) + 1)]
        row[0] = "BUG-003"
        wb["Bugs"].append(row)
    mutate(p["bug"], f)


@case("V8", "Severity Low (khong duoc ghi nhan)", 4)
def _(p):
    mutate(p["bug"], set_cell("Bugs", 2, "Severity", "Low", S.BUG_SHEETS))


@case("V8", "00_Meta bug_recipient con UNKNOWN", 13)
def _(p):
    mutate(p["bug"], set_meta("bug_recipient", S.UNKNOWN))


@case("V8", "Screen / Module khong tro ve SC-/F- co that", 15)
def _(p):
    mutate(p["bug"], set_cell("Bugs", 2, "Screen / Module", "SC-777", S.BUG_SHEETS))


@case("V3", "Bang output lech index.json (them output sau khi render)", 3)
def _(p):
    edit_json(p["index"], lambda d: d["outputs"].append(dict(d["outputs"][0], id="O9")))


@case("V3", "Bang output tro toi file khong ton tai", 4)
def _(p):
    os.remove(os.path.join(p["ver"], "02_API", "API_Doc_Fixture_ver1.xlsx"))


@case("V3", "Inventory them man hinh sau khi render -> so lieu chuong 3 lech", 5)
def _(p):
    def f(wb):
        wb["02_Screen"].append(["SC-003", "WEB-01", "/x", "X", "Detail", "User", "—", "F-002",
                                S.NO_IMAGE, 1, "Confirmed", ""])
    mutate(p["inv"], f)


@case("V3", "db_mode=NONE nhung chuong 5 van co bang DB", 8)
def _(p):
    mutate(p["inv"], set_meta("db_mode", "NONE"))


def run_gates(p):
    """Chay 5 gate, tra ve {gate: (rc, failed_checks)}."""
    out = {}
    rc, o = sh("verify-evidence.py", p["inv"])
    out["V1"] = (rc, failed_checks(o))
    rc, o = sh("verify-inventory.py", p["inv"])
    out["V2"] = (rc, failed_checks(o))
    rc, o = sh("verify-flow-png.py", p["flow"], "--inventory", p["inv"], "--png", p["flow_png"])
    out["V5"] = (rc, failed_checks(o))
    rc, o = sh("verify-bug-list.py", p["bug"], "--inventory", p["inv"])
    out["V8"] = (rc, failed_checks(o))
    rc, o = sh("verify-overview.py", p["docx"], "--inventory", p["inv"], "--index", p["index"])
    out["V3"] = (rc, failed_checks(o))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="selftest-gates-")
    results = []

    # 0 — fixture dung phai PASS het
    good = make_fixture(os.path.join(tmp, "good"))
    for gate, (rc, fails) in run_gates(good).items():
        results.append(("baseline", "Fixture dung -> %s PASS" % gate, not fails,
                        "" if not fails else "FAIL o check %s" % fails))
    # O4 trong index: link + trang thai + so TBD doc tu 04_DesignSystem/STATUS.md
    o4 = next((e for e in json.load(open(good["index"], encoding="utf8"))["outputs"] if e["id"] == "O4"), {})
    ok = o4.get("link") == "https://claude.ai/artifact/FixtureDs01" and "2 TBD · DRAFT" in str(o4.get("count"))
    results.append(("index", "O4 doc link/trang thai/TBD tu STATUS.md", ok, "O4=%s" % {k: o4.get(k) for k in ("link", "count")}))

    # 1 — tung ca tiem loi (repo gia nam trong thu muc fixture -> sua Path theo ban copy)
    for i, (gate, name, expect, fn) in enumerate(CASES):
        d = os.path.join(tmp, "case%02d" % i)
        shutil.copytree(os.path.join(tmp, "good"), d)
        p = paths(d)

        def fix_repo(wb, d=d):
            for r in range(2, wb["11_Repo"].max_row + 1):
                c = wb["11_Repo"].cell(row=r, column=2)
                c.value = c.value.replace(os.path.join(tmp, "good"), d)
        mutate(p["inv"], fix_repo)
        fn(p)
        fails = run_gates(p)[gate][1]
        results.append((gate, name, expect in fails,
                        "ky vong check %d FAIL, thuc te FAIL: %s" % (expect, fails or "khong co")))

    # 2 — V3 phai FAIL tren template goc (con placeholder)
    tpl = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..",
                                       "templates", "high-level-template.docx"))
    if os.path.isfile(tpl):
        rc, o = sh("verify-overview.py", tpl, "--inventory", good["inv"], "--index", good["index"])
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
        print("\nFixture giu tai: %s" % tmp)
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
