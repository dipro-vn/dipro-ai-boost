#!/usr/bin/env python3
"""GATE V9 — self-test: chung minh V1/V2/V3/V8 + gate schema V-DB check 10 (R1) + preflight-memory (R9) that su bat loi.

  python3 selftest-gates.py [--keep]

Cach lam: dung 1 thu muc version DUNG (inventory du 12 sheet, repo gia, evidence, flow,
bug list, index.json, overview docx) -> khang dinh moi gate PASS. Sau do tiem tung loi
da biet vao ban copy -> khang dinh dung check so may FAIL.
Gate bao PASS chua chung minh duoc gi: mot gate hong cung "PASS" moi thu.
Chay lai sau MOI lan sua verify-*.py / render-overview-docx.py / build-version-index.py.
"""
import argparse
import importlib.util
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
            "nar": os.path.join(i, "narrative.json"),
            "biz": os.path.join(i, "business.json"),
            "index": os.path.join(i, "index.json"),
            "bug": os.path.join(v, "07_Bug_List", "BugList_Fixture_ver1.xlsx"),
            "docx": os.path.join(v, "01_Overview", "Overview_Fixture_ver1.docx")}


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
    q.append(["Q-002", S.QUESTION_TYPE[0], "Handler cua batch API-002", "Khong thay file job",
              "Hoi maintainer", "BrSE", "Open", ""])

    api = wb["07_API"]
    api.append(["API-001", "Order", "API", "GET", "/api/orders", "Lay danh sach don", "JWT",
                "REPO-02:src/order/order.service.ts#L88-L104", "REPO-02", "SC-002", "orders",
                "EV-0004", "Confirmed", "—", ""])
    api.append(["API-002", "Batch", "BATCH", "CRON", "0 2 * * *", "Dong bo ton kho", "—",
                S.NEED_CONFIRM, "REPO-02", "—", "orders", "—", "To verify", "Q-002", ""])
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


def build_buglist(p):
    wb = new_wb(S.BUG_SHEETS)
    wb[S.BUG_SHEET].append([
        "BUG-001", "Nut Luu khong phan hoi", "SC-002", "/orders", "Functional",
        "High", "1. Mo /orders\n2. Bam Luu\n3. Khong co gi xay ra",
        "Luu thanh cong", "Khong phan hoi", "EV-0002", "Yes — 3/3", "Playwright",
        "User khong luu duoc thay doi", "Chrome 129 · 2026-10-01", "Yes", "Open", ""])
    wb[S.BUG_SHEET].append([   # bug chi doc tu code van vao danh sach neu muc High tro len
        "BUG-004", "Loc trang thai don bo qua gia tri da chon", "SC-002", "/orders", "Functional",
        "High", "1. Mo /orders\n2. Chon trang thai roi bam Loc", "Danh sach chi con don dung trang thai",
        "Handler khong truyen tham so status len API", "EV-0004", S.BUG_CODE_ONLY, "Code review",
        "Nguoi dung loc don sai", "Chrome 129", S.BUG_PRE_EXISTING[1], "Open", ""])
    os.makedirs(os.path.dirname(p["bug"]), exist_ok=True)
    wb.save(p["bug"])


def build_outputs(p):
    from openpyxl import Workbook
    v = p["ver"]
    wb = Workbook()
    wb.active.title = "Screen Index"
    for title in ("SC-001", "SC-002"):
        wb.create_sheet(title)["F6"] = "WORKING_SCREEN"
    os.makedirs(os.path.join(v, "05_Basic_Design"), exist_ok=True)
    wb.save(os.path.join(v, "05_Basic_Design", "BasicDesign_WEB-01_ver1.xlsx"))
    for sub, name in (("02_API", "API_Doc_Fixture_ver1.xlsx"), ("03_DB", "DB_Doc_Fixture_ver1.xlsx")):
        os.makedirs(os.path.join(v, sub), exist_ok=True)
        Workbook().save(os.path.join(v, sub, name))
    fake_png(os.path.join(v, "03_DB", "ERD_Fixture_ver1.png"))
    os.makedirs(os.path.join(v, "06_Design_System", "project"), exist_ok=True)   # O6 = format artifact Design System
    json.dump({"v": 3, "layout": "files", "title": "Fixture"},
              open(os.path.join(v, "06_Design_System", "project", "design-system.json"), "w"))
    open(os.path.join(v, "06_Design_System", "STATUS.md"), "w", encoding="utf8").write(
        "# Design System — Fixture\n\n- Trạng thái: DRAFT\n- Artifact: https://claude.ai/artifact/FixtureDs01\n"
        "- Nguồn: website WEB-01\n\n## Thiếu (TBD)\n\n| D# | Token / component | Ghi chú |\n|---|---|---|\n"
        "| D1 | primary-hover | khong quan sat duoc |\n| D6 | Toast | khong quan sat duoc |\n")
    os.makedirs(os.path.join(v, "04_Figma"), exist_ok=True)
    open(os.path.join(v, "04_Figma", "figma-links.md"), "w").write(
        "| Output | Frame | Node URL |\n|---|---|---|\n"
        "| Output 1 — Flow tổng quan | Flow | https://www.figma.com/design/abcdef/F?node-id=1-2 |\n"
        "| Output 2 — Screen flow | Screens | https://www.figma.com/design/abcdef/F?node-id=1-3 |\n"
        "| Sơ đồ DB (ERD) | ERD | https://www.figma.com/board/abcdef/F?node-id=2-2 |\n")
    json.dump({"project_name": "Fixture", "customer": "Cong ty ABC",
               "product_overview": "He thong quan ly don hang noi bo.",
               "actors": [{"actor": "User", "role": "Nhan vien", "main_usage": "Xem don"}],
               "system_composition": ["Frontend: React (REPO-01)", "Backend: NestJS (REPO-02)"]},
              open(p["nar"], "w", encoding="utf8"), ensure_ascii=False)
    json.dump({"overview": "Nhan vien xem va cap nhat don hang.",
               "flows": [{"title": "Xem don hang", "actor": "Nhan vien", "screens": ["「注文一覧」"],
                          "steps": ["Dang nhap.", "Mo danh sach don hang."], "evidence": ["EV-0002"]}],
               "states": [{"object": "Don hang", "flow": ["Moi", "Da giao"], "question": "Q-001"}]},
              open(p["biz"], "w", encoding="utf8"), ensure_ascii=False)
    gdir = os.path.join(p["root"], "gates")
    os.makedirs(gdir, exist_ok=True)
    for name in ("v-bd-WEB-01", "v-api", "v-db"):
        open(os.path.join(gdir, name + ".md"), "w").write(
            "# %s\n\n**5 checks · 5 PASS · 0 FAIL · 0 WARN**\n" % name)


def render_overview(p):
    sh("build-version-index.py", p["ver"])
    return sh("render-overview-docx.py", "--inventory", p["inv"], "--narrative", p["nar"],
              "--business", p["biz"], "--index", p["index"],
              "--figma-links", os.path.join(p["ver"], "04_Figma", "figma-links.md"),
              "--out", p["docx"])


def make_fixture(base):
    p = paths(base)
    build_inventory(p)
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


@case("V2", "De o trong thay vi ghi 'Cần xác nhận'", 11)
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


@case("V8", "Workbook co them sheet ngoai 'Bug List'", 1)
def _(p):
    mutate(p["bug"], lambda wb: wb.create_sheet("Suspected"))


@case("V8", "Bug website ghi Reproduced = No", 4)
def _(p):
    mutate(p["bug"], set_cell(S.BUG_SHEET, 2, "Reproduced", "No", S.BUG_SHEETS))


@case("V8", "Bug gan URL /api thay vi man", 7)
def _(p):
    def f(wb):
        set_cell(S.BUG_SHEET, 2, "URL / Route", "/api/orders", S.BUG_SHEETS)(wb)
        set_cell(S.BUG_SHEET, 2, "Evidence", "EV-0004", S.BUG_SHEETS)(wb)
    mutate(p["bug"], f)


@case("V8", "Category Data (khong quan sat tren man)", 4)
def _(p):
    mutate(p["bug"], set_cell(S.BUG_SHEET, 2, "Category", "Data", S.BUG_SHEETS))


@case("V8", "Bug gan voi chuc nang F- thay vi man SC-", 11)
def _(p):
    mutate(p["bug"], set_cell(S.BUG_SHEET, 2, "Screen / Module", "F-001", S.BUG_SHEETS))


@case("V8", "Repro Steps chi co 1 buoc", 5)
def _(p):
    mutate(p["bug"], set_cell(S.BUG_SHEET, 2, "Repro Steps", "1. Mo /orders", S.BUG_SHEETS))


@case("V8", "Bug trung lap", 9)
def _(p):
    def f(wb):
        ws = wb[S.BUG_SHEET]
        row = [ws.cell(row=2, column=c).value for c in range(1, len(S.BUG_SHEETS[S.BUG_SHEET]) + 1)]
        row[0] = "BUG-003"
        ws.append(row)
    mutate(p["bug"], f)


@case("V8", "Severity Medium (chi ghi High / Urgent)", 4)
def _(p):
    mutate(p["bug"], set_cell(S.BUG_SHEET, 2, "Severity", "Medium", S.BUG_SHEETS))


@case("V8", "00_Meta inventory bug_recipient con 'Cần xác nhận'", 10)
def _(p):
    mutate(p["inv"], set_meta("bug_recipient", S.NEED_CONFIRM))


@case("V8", "code-ref cua bug tro dong khong co that", 7)
def _(p):
    mutate(p["inv"], set_cell("05_Evidence", 5, "Locator", "REPO-02:src/order/order.service.ts#L900"))


@case("V8", "console error la noise cua cong cu quet (read-only-block)", 7)
def _(p):
    def f(wb):
        set_cell("05_Evidence", 3, "Type", "console-log")(wb)
        set_cell("05_Evidence", 3, "Note", "noise=read-only-block")(wb)
    mutate(p["inv"], f)


@case("V8", "Detected By Code review nhung chi co anh man", 7)
def _(p):
    mutate(p["bug"], set_cell(S.BUG_SHEET, 2, "Detected By", "Code review", S.BUG_SHEETS))


@case("V8", "Bug list con chu cu viet thuong 'Unknown'", 12)
def _(p):
    mutate(p["bug"], set_cell(S.BUG_SHEET, 2, "Note", "Unknown", S.BUG_SHEETS))


@case("V8", "Screen / Module khong tro ve SC- co that", 11)
def _(p):
    mutate(p["bug"], set_cell(S.BUG_SHEET, 2, "Screen / Module", "SC-777", S.BUG_SHEETS))


@case("V3", "Docx con chuong cu 'Phụ lục'", 1)
def _(p):
    from docx import Document
    d = Document(p["docx"])
    d.add_heading("Phụ lục A. Open Questions", level=1)
    d.save(p["docx"])


@case("V3", "Inventory them man hinh sau khi render -> bang tong chuong 3 lech", 3)
def _(p):
    def f(wb):
        wb["02_Screen"].append(["SC-003", "WEB-01", "/x", "X", "Detail", "User", "—", "F-002",
                                S.NO_IMAGE, 1, "Confirmed", ""])
    mutate(p["inv"], f)


@case("V3", "db_mode=NONE nhung chuong 5 van co bang DB", 5)
def _(p):
    mutate(p["inv"], set_meta("db_mode", "NONE"))


@case("V3", "Chuong 2 nghiep vu co ma noi bo SC-", 7)
def _(p):
    edit_json(p["biz"], lambda d: d.update(overview="Xem man SC-001."))
    render_overview(p)


@case("V3", "Luong nghiep vu khong co EV va khong co Q", 8)
def _(p):
    edit_json(p["biz"], lambda d: d["flows"][0].pop("evidence"))
    render_overview(p)


@case("V3", "Docx con chu cu viet thuong 'Unknow'", 13)
def _(p):
    edit_json(p["nar"], lambda d: d.update(product_overview="He thong Unknow"))
    render_overview(p)


@case("V3", "Khong co link ERD Figma va khong co ghi chu", 14)
def _(p):
    from docx import Document
    d = Document(p["docx"])
    for para in d.paragraphs:
        if para.text.startswith("Sơ đồ trên Figma:") and "ERD" in para.text:
            para._p.getparent().remove(para._p)
    d.save(p["docx"])


def run_gates(p):
    """Chay 5 gate, tra ve {gate: (rc, failed_checks)}."""
    out = {}
    rc, o = sh("verify-evidence.py", p["inv"])
    out["V1"] = (rc, failed_checks(o))
    rc, o = sh("verify-inventory.py", p["inv"])
    out["V2"] = (rc, failed_checks(o))
    rc, o = sh("verify-bug-list.py", p["bug"], "--inventory", p["inv"])
    out["V8"] = (rc, failed_checks(o))
    rc, o = sh("verify-overview.py", p["docx"], "--inventory", p["inv"], "--business", p["biz"])
    out["V3"] = (rc, failed_checks(o))
    return out


def index_cases(tmp):
    """build-version-index: O6 moi site 1 bo (WEB-xx/project/) + thu muc CR (Impact xlsx, Figma CR, input/)."""
    out = []
    # O6 layout moi: 06_Design_System/WEB-01/ + WEB-02/
    d = os.path.join(tmp, "o4sites")
    shutil.copytree(os.path.join(tmp, "good"), d)
    v = os.path.join(d, VER)
    ds = os.path.join(v, "06_Design_System")
    for site in ("WEB-01", "WEB-02"):
        shutil.copytree(os.path.join(ds, "project"), os.path.join(ds, site, "project"))
        txt = open(os.path.join(ds, "STATUS.md"), encoding="utf8").read()
        open(os.path.join(ds, site, "STATUS.md"), "w", encoding="utf8").write(
            txt.replace("FixtureDs01", "FixtureDs" + site[-2:]))
    shutil.rmtree(os.path.join(ds, "project"))
    os.remove(os.path.join(ds, "STATUS.md"))
    open(os.path.join(v, "_internal", "gates", "v-ds-WEB-02.md"), "w").write(
        "**3 checks · 2 PASS · 1 FAIL · 0 WARN**\n")
    sh("build-version-index.py", v)
    o4 = [e for e in json.load(open(os.path.join(v, "_internal", "index.json"), encoding="utf8"))["outputs"]
          if e["id"] == "O6"]
    got = {e.get("site"): (e.get("link", "")[-2:], e["status"]) for e in o4}
    out.append(("index", "O6 layout WEB-xx/project/ -> 1 dong / site, link + gate rieng",
                got == {"WEB-01": ("01", "warn"), "WEB-02": ("02", "fail")}, "O6=%s" % got))

    # Folder CR layout moi chua co Impact xlsx -> khong duoc ghi la BASELINE
    cr0 = os.path.join(d, "CR-002_031026_coupon")
    os.makedirs(os.path.join(cr0, "_internal"))
    sh("build-version-index.py", cr0)
    i0 = json.load(open(os.path.join(cr0, "_internal", "index.json"), encoding="utf8"))
    out.append(("index", "Folder CR-<id>_… chua co Impact xlsx -> version_type CR, dong CR = chua co file",
                i0["version_type"] == "CR" and i0["outputs"][0]["status"] == "fail", "%s %s" % (i0["version_type"], i0["outputs"])))
    shutil.rmtree(cr0)

    # Thu muc CR
    cr = os.path.join(d, "ver2_021026_CR-001-otp")
    os.makedirs(os.path.join(cr, "_internal", "gates"))
    os.makedirs(os.path.join(cr, "input"))
    open(os.path.join(cr, "input", "CR-001.md"), "w").write("# CR-001\n")
    cj = os.path.join(cr, "_internal", "cr.json")
    json.dump({"meta": {"cr_id": "CR-001", "cr_title": "OTP", "baseline_version": VER,
                        "cr_version": "ver2_021026_CR-001-otp", "source_type": "FILE",
                        "source_ref": "input/CR-001.md", "received_date": "02/10/2026",
                        "requested_by": "PM khach hang", "overall_risk": "Low", "recommendation": "Lam"},
               "justification": [{"item": "CR-001.1", "request": "OTP", "baseline_ref": "SC-001",
                                  "baseline_quote": "Dang nhap khong OTP", "criteria": ["C1"],
                                  "why": "Chua co", "not_feedback": "Khong phai loi"}],
               "impacts": [{"id": "IMP-001", "axis": "Screen", "change_type": "UPD", "baseline_ref": "SC-001",
                            "item": "Dang nhap", "change": "Them OTP", "why_change": "Yeu cau CR muc 1",
                            "impact_on_current": "Luong login", "conflict": "No", "risk": "Low",
                            "rate_code": "SCR-UPD-M", "qty": 2, "evidence": "input/CR-001.md",
                            "cr_item": "CR-001.1"}]},
              open(cj, "w"))
    rates = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", S.MD_RATES_PATH))
    rc, o = sh("build-cr-impact.py", "--cr-json", cj, "--rates", rates,
               "--out", os.path.join(cr, "CR-001_Impact.xlsx"))
    open(os.path.join(cr, "_internal", "gates", "v-cr.md"), "w").write("**20 checks · 20 PASS · 0 FAIL · 0 WARN**\n")
    sh("build-version-index.py", cr)
    idx = json.load(open(os.path.join(cr, "_internal", "index.json"), encoding="utf8"))
    e = {x["id"]: x for x in idx["outputs"]}
    st = json.load(open(rates)).get("status")
    ok = (rc == 0 and list(e) == ["CR", "O4", "IN"] and e["CR"]["count"] == "1 hạng mục · 3 MD (đơn giá %s)" % st
          and e["CR"]["status"] == "ok" and e["O4"]["status"] == "skip" and "không vẽ" in e["O4"]["status_text"]
          and idx["baseline_ref"] == VER)
    out.append(("index", "CR: Impact xlsx (N hang muc · MD · don gia), Figma skip, khong co Summary.md",
                ok, "%s %s" % (o.strip()[-80:], {k: (x["count"], x["status"]) for k, x in e.items()})))
    open(os.path.join(cr, "_internal", "gates", "v-cr-figma.md"), "w").write("**6 checks · 5 PASS · 1 FAIL · 0 WARN**\n")
    sh("build-version-index.py", cr)
    e = {x["id"]: x for x in json.load(open(os.path.join(cr, "_internal", "index.json"), encoding="utf8"))["outputs"]}
    out.append(("index", "CR: co gate v-cr-figma -> dong Figma theo gate (FAIL)",
                e["O4"]["gate"] == "FAIL" and e["CR"]["gate"] == "PASS", "O4=%s CR=%s" % (e["O4"]["gate"], e["CR"]["gate"])))

    # O4: --skip luon duoc ton trong (ke ca da co figma-links.md); figma-links chua co link -> "chưa vẽ"
    d5 = os.path.join(tmp, "o5skip")
    shutil.copytree(os.path.join(tmp, "good"), d5)
    v5 = os.path.join(d5, VER)

    def o5(*args):
        sh("build-version-index.py", v5, *args)
        return next(x for x in json.load(open(os.path.join(v5, "_internal", "index.json"), encoding="utf8"))["outputs"]
                    if x["id"] == "O4")
    e5 = o5("--skip", "O4=lam o buoc sau")
    out.append(("index", "--skip O4 khi da co 04_Figma/figma-links.md -> O4 skip dung ly do",
                e5["status"] == "skip" and "lam o buoc sau" in e5["status_text"], str(e5.get("status_text"))))
    open(os.path.join(v5, "04_Figma", "figma-links.md"), "w", encoding="utf8").write(
        "# Figma\n\n| So do | Link |\n|---|---|\n| API map | (chua ve) |\n")
    e5 = o5()
    out.append(("index", "figma-links.md chua co link figma.com -> O4 'chưa vẽ' (khong phai 'chưa chạy gate')",
                e5["status"] == "skip" and "chưa vẽ" in e5["status_text"], str(e5.get("status_text"))))
    return out


# ---------- scan-repo: tsconfig baseUrl/paths · template `${APIs.X}/${id}` · --sensitive-memory ----------
SCAN_REPO = {
    "package.json": '{"dependencies":{"next":"14.0.0","react":"18.2.0","axios":"1.6.0"}}',
    "tsconfig.json": """{
  // comment + dau phay thua (JSONC)
  "$schema": "https://json.schemastore.org/tsconfig",
  "compilerOptions": {
    "baseUrl": "./src", /* bare import -> src/ */
    "paths": { "#lib/*": ["lib/*"], },
  },
}
""",
    "src/libs/apis.ts": "export const APIs = {\n  ORDER: '/api/orders',\n};\n",
    "src/other/apis.ts": "export const APIs = {\n  ORDER: '/api/other',\n};\n",   # trung ten hang so
    "src/lib/http.ts": "import axios from 'axios';\nexport const http = axios;\n",
    "src/services/order.ts": """import { http } from '#lib/http';
import { APIs } from 'libs/apis';
export const removeOrder = (id: number) => http.delete(`${APIs.ORDER}/${id}`);
export const listOrders = () => http.get(APIs.ORDER);
""",
    "src/components/ChangePasswordForm.tsx": """import { removeOrder } from 'services/order';
export default function ChangePasswordForm({ id }) {
  const handleRemove = async () => { await removeOrder(id); };
  return <IconButton aria-label="delete" onClick={handleRemove}><DeleteIcon /></IconButton>;
}
""",
    "src/pages/orders.tsx": """import { listOrders } from 'services/order';
import ChangePasswordForm from 'components/ChangePasswordForm';
import { useEffect } from 'react';
export default function Orders() {
  useEffect(() => { listOrders(); }, []);
  return <div><ChangePasswordForm id={1} /></div>;
}
""",
    "src/pages/api/orders/index.ts": "export default function h(req, res) { if (req.method === 'GET') return res.json([]); }\n",
    "src/pages/api/orders/[id].ts": "export default function h(req, res) { if (req.method === 'DELETE') return res.json({}); }\n",
    ".yarnrc.yml": "npmAuthToken: fixture\n",
    ".env": "X=fixture\n",
    "src/secret_token.ts": "export const x = 1;\n",
}


def scan_cases(tmp):
    import csv as _csv
    out = []
    base = os.path.join(tmp, "scan")
    repo = os.path.join(base, "web")
    for rel, text in SCAN_REPO.items():
        os.makedirs(os.path.dirname(os.path.join(repo, rel)), exist_ok=True)
        open(os.path.join(repo, rel), "w", encoding="utf8").write(text)
    mem = os.path.join(base, "preflight-memory.json")
    json.dump({"answers": {}, "sensitive": [
        {"classification": "[A] Báo nhầm — tên file chứa password", "by_role": "PM", "date": "2026-10-28",
         "files": ["web/src/components/ChangePasswordForm.tsx", "web/.yarnrc.yml", "web/.env"]},
        {"classification": "[B] Không mở", "by_role": "PM", "date": "2026-10-28", "files": ["web/src/secret_token.ts"]}]},
        open(mem, "w", encoding="utf8"), ensure_ascii=False)

    def run(*extra):
        I = os.path.join(base, "I%d" % len(extra))
        rc, o = sh("scan-repo.py", repo, "--repo-id", "REPO-01", "--out", I, *extra)
        code = os.path.join(I, "recon", "code", "REPO-01")
        edges = list(_csv.DictReader(open(os.path.join(code, "fe-api-calls.csv"), encoding="utf8"))) if rc == 0 else []
        sk = json.load(open(os.path.join(code, "skipped-sensitive.json"), encoding="utf8")) if rc == 0 else {}
        sf = json.load(open(os.path.join(code, "fe-screen-files.json"), encoding="utf8")) if rc == 0 else {}
        return rc, edges, sk, sf
    rc, edges, sk, sf = run()
    got = sorted((e["Trigger"], e["Method"], e["Path"]) for e in edges)
    out.append(("R1", "scan-repo: import theo tsconfig baseUrl ('services/order') + paths ('#lib/*'), JSONC -> co canh mount",
                rc == 0 and ("mount", "GET", "/api/orders") in got, "got=%s" % got))
    out.append(("R1", "scan-repo: khong --sensitive-memory -> file ten chua 'password' van bi bo qua",
                "src/components/ChangePasswordForm.tsx" in {x["path"] for x in sk.get("sensitive", [])}
                and not any(e["Method"] == "DELETE" for e in edges), str(sk.get("sensitive"))))
    rc, edges, sk, sf = run("--sensitive-memory", mem)
    got = sorted((e["Trigger"], e["Method"], e["Path"], e["API ID"] != "—") for e in edges)
    skipped = {x["path"]: x["reason"] for x in sk.get("sensitive", [])}
    out.append(("R1", "scan-repo: template `${APIs.ORDER}/${id}` -> /api/orders/:id (hang so cua file import, ten trung)",
                ("handleRemove → onClick", "DELETE", "/api/orders/:id", True) in got, "got=%s" % got))
    out.append(("R1", "--sensitive-memory: chi mo lai file 'báo nhầm' bi chan vi ten; .env / .yarnrc.yml / [B] van chan",
                sk.get("reopened") == ["src/components/ChangePasswordForm.tsx"]
                and skipped == {".env": "env-file", ".yarnrc.yml": "credential-config", "src/secret_token.ts": "name-keyword"},
                "reopened=%s skipped=%s" % (sk.get("reopened"), skipped)))
    out.append(("R1", "fe-screen-files.json: route -> file component cua man (cho build-basic-design tra handler)",
                sf.get("/orders") == ["src/pages/orders.tsx", "src/components/ChangePasswordForm.tsx"], str(sf)))
    return out


# ---------- R1 code-first: Prisma + migration -> gate schema · do thi FE -> API · commit ----------
R1_REPO = {
    "package.json": '{"dependencies":{"next":"14.0.0","react":"18.2.0","@prisma/client":"5.0.0","axios":"1.6.0"}}',
    "prisma/schema.prisma": """datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
enum Role {
  ADMIN
  USER
}
/// Tai khoan
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique @db.VarChar(255)
  role      Role     @default(USER)
  orders    Order[]
  createdAt DateTime @default(now()) @map("created_at")
  @@map("users")
}
model Order {
  id     Int     @id @default(autoincrement())
  userId Int     @map("user_id")
  user   User    @relation(fields: [userId], references: [id])
  note   String?
  @@map("orders")
}
""",
    "prisma/migrations/20240101000000_init/migration.sql": """CREATE TYPE "Role" AS ENUM ('ADMIN', 'USER');
CREATE TABLE "users" ("id" SERIAL NOT NULL, "email" VARCHAR(255) NOT NULL, "role" "Role" NOT NULL DEFAULT 'USER',
  "legacy" BOOLEAN, "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP, CONSTRAINT "users_pkey" PRIMARY KEY ("id"));
CREATE TABLE "orders" ("id" SERIAL NOT NULL, "user_id" INTEGER NOT NULL, CONSTRAINT "orders_pkey" PRIMARY KEY ("id"));
CREATE TABLE "tmp_import" ("id" SERIAL NOT NULL);
ALTER TABLE "orders" ADD CONSTRAINT "orders_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id");
""",
    "prisma/migrations/20240201000000_note/migration.sql": """ALTER TABLE "orders" ADD COLUMN "note" TEXT;
ALTER TABLE "users" DROP COLUMN "legacy";
DROP TABLE "tmp_import";
""",
    "src/services/order.service.ts": """import axios from 'axios';
export const getOrders = async () => (await axios.get('/api/orders')).data;
export const createOrder = (body: unknown) => axios.post('/api/orders', body);
""",
    "src/services/index.ts": "export * from './order.service';\n",
    "src/hooks/useOrders.ts": """import { useEffect, useState } from 'react';
import { getOrders } from '@/services';
export function useOrders() {
  const [d, setD] = useState([]);
  useEffect(() => { getOrders().then(setD); }, []);
  return d;
}
""",
    "src/components/Shared.tsx": "export default function Shared() { return <div>x</div>; }\n",
    "src/pages/orders.tsx": """import { useOrders } from '@/hooks/useOrders';
import { createOrder } from '@/services';
import Shared from '@/components/Shared';
const OrdersPage = () => {
  const rows = useOrders();
  const handleSave = async () => { await createOrder({}); };
  return (<div><Shared /><button onClick={handleSave}>保存</button></div>);
};
export default OrdersPage;
""",
    "src/pages/about.tsx": """import Shared from '@/components/Shared';
import { getOrders } from '@/services/order.service';
export default function About() { return <Shared />; }
""",
    "src/pages/api/orders.ts": """export default async function handler(req, res) {
  if (req.user?.role !== 'ADMIN') return res.status(403).end();
  if (req.method === 'GET') return res.json([]);
  if (req.method === 'POST') return res.json({});
}
""",
}


def r1_cases(tmp):
    import csv as _csv
    out = []
    repo = os.path.join(tmp, "r1", "repo")
    for rel, text in R1_REPO.items():
        os.makedirs(os.path.dirname(os.path.join(repo, rel)), exist_ok=True)
        open(os.path.join(repo, rel), "w", encoding="utf8").write(text)
    I = os.path.join(tmp, "r1", "_internal")

    # 1 read-orm-schema: model + replay migration (ADD / DROP COLUMN / DROP TABLE / enum co ngoac kep)
    rc, o = sh("read-orm-schema.py", repo, "--repo-id", "REPO-01", "--out", I, "--ev-start", "1")
    dbc = os.path.join(I, "recon", "db-code", "REPO-01")
    cs = list(_csv.DictReader(open(os.path.join(dbc, "code-schema.csv"), encoding="utf8"))) if rc == 0 else []
    got = sorted((r["Table"], r["Column"]) for r in cs)
    want = sorted([("users", "id"), ("users", "email"), ("users", "role"), ("users", "created_at"),
                   ("orders", "id"), ("orders", "user_id"), ("orders", "note")])
    cols = list(_csv.DictReader(open(os.path.join(dbc, "columns.csv"), encoding="utf8"))) if rc == 0 else []
    fk = next((c["FK"] for c in cols if c["Table"] == "orders" and c["Column"] == "user_id"), None)
    out.append(("R1", "read-orm-schema: Prisma model + migration replay (@map, DROP, enum, FK)",
                rc == 0 and got == want and fk == "users.id" and '"mismatches": 0' in o,
                "rc=%s got=%s fk=%s" % (rc, got, fk)))

    # 2 gate schema: inventory nap tu tables/columns -> check 10 PASS; mat 1 cot / 1 bang -> FAIL
    def inventory(drop_col=None, drop_table=None):
        wb = new_wb(S.SHEETS)
        meta = {k: "—" for k in S.META_KEYS}
        meta.update({"system_name": "R1", "db_mode": "MIGRATION"})
        for k in S.META_KEYS:
            wb["00_Meta"].append([k, meta[k]])
        for sheet, fn in (("03_DB_Tables", "tables.csv"), ("04_DB_Columns", "columns.csv"), ("05_Evidence", "evidence.csv")):
            for r in _csv.DictReader(open(os.path.join(dbc, fn), encoding="utf8")):
                if (r.get("Table"), r.get("Column")) == drop_col or (drop_table and r.get("Table") == drop_table):
                    continue
                wb[sheet].append([r.get(h, "") for h in S.SHEETS[sheet]])
        wb["11_Repo"].append(["REPO-01", repo, "FULLSTACK", "Next.js", "WEB-01", ""])
        p = os.path.join(tmp, "r1", "inv_%s_%s.xlsx" % (drop_col and drop_col[1], drop_table))
        wb.save(p)
        return p

    def gate(inv):
        doc = inv.replace(".xlsx", "_doc.xlsx")
        sh("build-db-doc.py", "--inventory", inv, "--system", "R1", "--version", "ver1", "--out", doc)
        return sh("verify-db-doc.py", doc, "--inventory", inv, "--code-schema", os.path.join(dbc, "code-schema.csv"))
    rc, o = gate(inventory())
    out.append(("R1", "Gate schema: inventory du bang/cot tu code -> verify-db-doc check 10 PASS",
                10 not in failed_checks(o) and "| 10 |" in o, "FAIL: %s" % failed_checks(o)))
    rc, o = gate(inventory(drop_col=("orders", "note")))
    out.append(("R1", "Gate schema: xoa cot orders.note khoi 04_DB_Columns -> check 10 FAIL",
                10 in failed_checks(o) and "orders.note" in o, "FAIL: %s" % failed_checks(o)))
    rc, o = gate(inventory(drop_table="users"))
    out.append(("R1", "Gate schema: thieu ca bang users trong 03 -> check 10 FAIL",
                10 in failed_checks(o) and "bang users" in o, "FAIL: %s" % failed_checks(o)))

    # 3 scan-repo: do thi FE -> API muc ky hieu (about import getOrders nhung khong dung -> khong co canh)
    rc, o = sh("scan-repo.py", repo, "--repo-id", "REPO-01", "--out", I, "--ev-start", "100")
    code = os.path.join(I, "recon", "code", "REPO-01")
    edges = list(_csv.DictReader(open(os.path.join(code, "fe-api-calls.csv"), encoding="utf8"))) if rc == 0 else []
    got = sorted((e["Screen Route"], e["Trigger"], e["UI Label"], e["Method"], e["API ID"] != "—", e["Confidence"]) for e in edges)
    want = sorted([("/orders", "mount", "—", "GET", True, "static"),
                   ("/orders", "handleSave → onClick", "保存", "POST", True, "static")])
    out.append(("R1", "scan-repo fe-api-calls.csv: man -> trigger/nut -> API ID, khong gan nham man khong goi",
                got == want, "got=%s" % got))
    roles = list(_csv.DictReader(open(os.path.join(code, "api-roles.csv"), encoding="utf8"))) if rc == 0 else []
    out.append(("R1", "scan-repo api-roles.csv: role doc tu so sanh role trong handler",
                bool(roles) and all(r["Roles"] == "ADMIN" for r in roles), str(roles)[:200]))

    # 4 commit: lan sau so voi 00_Meta.repo_commit -> khong doi / doi
    commit = json.loads(o[o.index("{"):o.rindex("}") + 1])["commit"] if rc == 0 else ""
    wb = new_wb({"00_Meta": S.SHEETS["00_Meta"]})
    wb["00_Meta"].append(["repo_commit", "REPO-01=%s;REPO-02=abc" % commit])
    prev = os.path.join(tmp, "r1", "prev.xlsx")
    wb.save(prev)
    rc1, o1 = sh("scan-repo.py", repo, "--repo-id", "REPO-01", "--out", I, "--commit-only", "--prev-inventory", prev)
    open(os.path.join(repo, "src", "pages", "about.tsx"), "a", encoding="utf8").write("// doi\n")
    rc2, o2 = sh("scan-repo.py", repo, "--repo-id", "REPO-01", "--out", I, "--commit-only", "--prev-inventory", prev)
    out.append(("R1", "repo_commit: hash khong doi -> commit_changed=false; sua 1 file -> true",
                bool(commit) and '"commit_changed": false' in o1 and '"commit_changed": true' in o2,
                "%s | %s" % (o1[-80:], o2[-80:])))
    return out


def legacy_cases(tmp):
    """Version cu (truoc D1) con chu UNKNOWN -> carry bang build-inventory.py --carry-from tu doi."""
    old = os.path.join(tmp, "legacy_old.xlsx")
    wb = new_wb(S.SHEETS)
    wb["07_API"].append(["API-001", "Order", "API", "GET", "/api/orders", "UNKNOWN", "UNKNOWN — chua ro",  # du lieu cu
                         "—", "REPO-01", "—", "—", "—", "UNKNOWN", "Q-001", ""])
    wb.save(old)
    new = os.path.join(tmp, "legacy_new.xlsx")
    rc, o = sh("build-inventory.py", "--out", new, "--carry-from", old)
    r = S.load(new)["07_API"][0] if rc == 0 else {}
    ok = (r.get("Status") == "To verify" and r.get("Summary") == S.NEED_CONFIRM
          and r.get("Auth", "").startswith(S.NEED_CONFIRM + " —") and S.LEGACY_WORD not in str(r))
    return [("legacy", "Carry version cu: UNKNOWN -> Status 'To verify', o noi dung 'Cần xác nhận'", ok,
             "rc=%s %s" % (rc, {k: r.get(k) for k in ("Summary", "Auth", "Status")}))]


def preflight_cases(tmp):
    global PMX
    _s = importlib.util.spec_from_file_location("pmx", os.path.join(HERE, "preflight-memory.py"))
    PMX = importlib.util.module_from_spec(_s)
    _s.loader.exec_module(PMX)
    """R9 · D8: preflight-memory.py — memory du -> khong hoi lai (tru 4 cau an toan dang xac nhan), khong credential."""
    out = []
    outs = os.path.join(tmp, "pm", "outputs")
    mem = os.path.join(outs, "_project", "preflight-memory.json")
    spec = importlib.util.spec_from_file_location("pm", os.path.join(HERE, "preflight-memory.py"))
    PM = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(PM)
    # 00_Meta cua baseline -> P0a duoc ke thua, khong hoi lai
    inv = os.path.join(outs, VER, "_internal", "inventory.xlsx")
    os.makedirs(os.path.dirname(inv))
    wb = new_wb({"00_Meta": S.SHEETS["00_Meta"]})
    wb["00_Meta"].append(["system_name", "Fixture"])
    wb["00_Meta"].append(["version_type", "BASELINE"])
    wb.save(inv)
    for code, _, _, _ in PM.QUESTIONS:
        if code != "P0a":
            sh("preflight-memory.py", "set", "--outputs", outs, "--code", code, "--answer", "ok " + code, "--by-role", "PM")
    rc, o = sh("preflight-memory.py", "missing", "--outputs", outs)
    j = json.loads(o) if rc == 0 else {}
    p0a = [x for x in j.get("confirm_table", []) if x["code"] == "P0a"]
    out.append(("R9", "Memory du + 00_Meta -> ask rong, 4 cau an toan o confirm_safety, P0a ke thua 00_Meta",
                rc == 0 and j["ask"] == [] and sorted(x["code"] for x in j["confirm_safety"]) == sorted(PM.SAFETY)
                and len(PM.SAFETY) == 4 and p0a and p0a[0]["source"] == PM.SOURCES["meta"], o[-300:]))
    sh("preflight-memory.py", "set", "--outputs", outs, "--code", "P7", "--pending", "--by-role", "PM")
    rc1, _ = sh("preflight-memory.py", "set", "--outputs", outs, "--code", "P11", "--pending", "--by-role", "PM")
    j = json.loads(sh("preflight-memory.py", "missing", "--outputs", outs)[1])
    out.append(("R9", "Bo qua cau thuong -> pending, hoi lai; cau an toan khong cho bo qua (exit 2)",
                rc1 == 2 and [x["code"] for x in j["ask"]] == ["P7"] and j["ask"][0]["why"] == "pending", str(j["ask"])))
    secret = "pass" + "word=" + "Abc" + "12345"
    rc2, _ = sh("preflight-memory.py", "set", "--outputs", outs, "--code", "P2a", "--answer", "admin " + secret,
                "--by-role", "PM")
    txt = open(mem, encoding="utf8").read()
    rc3 = subprocess.run(["node", os.path.join(HERE, "..", "..", "..", "hooks", "detect-pii.js"), "--scan", mem],
                         capture_output=True, text=True).returncode
    out.append(("R9", "Cau tra loi giong credential bi tu choi (exit 2); file memory khong co credential (H06 scan sach)",
                rc2 == 2 and secret not in txt and not PM.CRED_RX.search(txt) and rc3 == 0, "rc=%s scan=%s" % (rc2, rc3)))
    sh("preflight-memory.py", "set-sensitive", "--outputs", outs, "--classification", "Du lieu mau do khach tao",
       "--files", "inputs/repo/api/seed.json", "--by-role", "PM")
    j = json.loads(sh("preflight-memory.py", "missing", "--outputs", outs, "--sensitive-files",
                      "inputs/repo/api/seed.json", "inputs/repo/api/new.json")[1])
    out.append(("R9", "S1 da phan loai -> khong hoi lai; file moi -> sensitive_unclassified",
                j["sensitive_unclassified"] == ["inputs/repo/api/new.json"], str(j["sensitive_unclassified"])))
    j1 = json.loads(sh("preflight-memory.py", "missing", "--outputs", outs, "--phase", "1")[1])
    j2 = json.loads(sh("preflight-memory.py", "missing", "--outputs", outs, "--phase", "2")[1])
    c1 = {q["code"] for q in j1["ask"]} | {q["code"] for q in j1["confirm_safety"]}
    c2 = {q["code"] for q in j2["ask"]} | {q["code"] for q in j2["confirm_safety"]}
    out.append(("R9", "Giai đoạn 1 khong hoi website / 4 cau an toan; Giai đoạn 2 chi hoi website + an toan",
                not (c1 & PMX.PHASE2) and "P0d" in c1 | {q["code"] for q in j1["confirm_table"]}
                and c2 <= PMX.PHASE2 and {"P1-env", "P2b", "P3", "P11"} <= c2, "p1=%s p2=%s" % (sorted(c1), sorted(c2))))
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
    # O6 trong index: link + trang thai + so TBD doc tu 06_Design_System/STATUS.md
    o4 = next((e for e in json.load(open(good["index"], encoding="utf8"))["outputs"] if e["id"] == "O6"), {})
    ok = o4.get("link") == "https://claude.ai/artifact/FixtureDs01" and "2 TBD · DRAFT" in str(o4.get("count"))
    results.append(("index", "O6 doc link/trang thai/TBD tu STATUS.md", ok, "O6=%s" % {k: o4.get(k) for k in ("link", "count")}))
    results += index_cases(tmp)
    # Diem dung giua 2 giai doan: README liet ke giai doan 2 se lam gi
    d = os.path.join(tmp, "stage2")
    shutil.copytree(os.path.join(tmp, "good"), d)
    v2 = paths(d)["ver"]
    sh("build-version-index.py", v2, "--skip", "O7=chờ giai đoạn 2")
    r2 = open(os.path.join(v2, "README.md"), encoding="utf8").read()
    sh("build-version-index.py", v2)
    r0 = open(os.path.join(v2, "README.md"), encoding="utf8").read()
    results.append(("index", "O7 'chờ giai đoạn 2' -> README co muc 'Giai đoạn 2 — chưa chạy' (7 viec); het cho -> khong co",
                    "## Giai đoạn 2 — chưa chạy" in r2 and "7. Cập nhật Tài liệu tổng hợp" in r2
                    and "Giai đoạn 2 — chưa chạy" not in r0, ""))
    results += r1_cases(tmp)
    results += scan_cases(tmp)
    results += legacy_cases(tmp)
    results += preflight_cases(tmp)
    # Khong co link Figma -> chuong 5 ghi chu "xem anh ERD trong 03_DB" -> V3 van PASS
    d = os.path.join(tmp, "nolink")
    shutil.copytree(os.path.join(tmp, "good"), d)
    pn = paths(d)
    os.remove(os.path.join(pn["ver"], "04_Figma", "figma-links.md"))
    render_overview(pn)
    from docx_read import Docx
    dx = Docx(pn["docx"])
    fails = run_gates(pn)["V3"][1]
    results.append(("V3", "Khong co link Figma -> ghi chu ERD o chuong 5 -> PASS", not fails and
                    sum(1 for _, t in dx.paragraphs if t.startswith("Chưa có sơ đồ trên Figma")) == 1, "FAIL: %s" % fails))
    gx = Docx(good["docx"])
    # Chuong 1: co --flow-image -> hinh + chu thich, V3 check 15 khong WARN; khong co -> WARN 15
    d = os.path.join(tmp, "flowimg")
    shutil.copytree(os.path.join(tmp, "good"), d)
    pf = paths(d)
    png = os.path.join(pf["root"], "archify", "luong.png")
    fake_png(png)
    sh("render-overview-docx.py", "--inventory", pf["inv"], "--narrative", pf["nar"], "--business", pf["biz"],
       "--index", pf["index"], "--flow-image", png, "--out", pf["docx"])
    rc1, o1 = sh("verify-overview.py", pf["docx"], "--inventory", pf["inv"], "--business", pf["biz"])
    rc0, o0 = sh("verify-overview.py", good["docx"], "--inventory", good["inv"], "--business", good["biz"])
    results.append(("V3", "Hinh luong nghiep vu Archify o chuong 1: co -> PASS 15, khong co -> WARN 15",
                    "| 15 |" in o1 and "| 15 | " in o0 and "WARN" in [l for l in o0.splitlines() if l.startswith("| 15 |")][0]
                    and "PASS" in [l for l in o1.splitlines() if l.startswith("| 15 |")][0], o1[-200:]))
    ft = [t for _, t in gx.paragraphs if t.startswith("Sơ đồ trên Figma:") and "figma.com" in t]
    results.append(("V3", "Co figma-links.md -> 2 link Figma (luong Output 1 · ERD), khong co so do API",
                    len(ft) == 2 and not any("API" in t for t in ft),
                    str([t for _, t in gx.paragraphs if "Figma" in t])))

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
        rc, o = sh("verify-overview.py", tpl, "--inventory", good["inv"], "--business", good["biz"])
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
