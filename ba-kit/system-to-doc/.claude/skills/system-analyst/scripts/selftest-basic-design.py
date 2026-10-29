#!/usr/bin/env python3
# SOURCE: ba-kit/requirement-to-flow/.claude/skills/business-analyst/scripts/selftest-basic-design.py @ 447770e
# DA TACH KHOI BAN GOC requirement-to-flow (D2, 27/10/2026): tu sinh fixture bang build-basic-design.py khi
# khong truyen workbook + case check 16-19 (cot S "API gọi"). Case check 1-15 van dung chung.
"""Self-test cho Quality Gate O4 — chung minh gate KHONG pass rong.

Cach dung:
    python3 selftest-basic-design.py                     # tu sinh fixture (inventory + recon + spec) -> --asis
    python3 selftest-basic-design.py <workbook-da-PASS.xlsx> [--before <backup.xlsx>] [--asis]

--asis: gate chay voi --asis + them case check 16-19 (AS-IS, kit system-to-doc).
Case nao thieu dieu kien tien quyet (vd workbook AS-IS khong co error) -> SKIP, khong tinh la loi.

Lay 1 workbook da PASS gate, tiem tung loi da biet vao ban copy, roi xac nhan
gate bat dung check ky vong. Gate PASS ma khong co self-test nay = chua chung
minh duoc gi: mot gate hong van "PASS" moi thu.

Bo test nay da tung tim ra 2 loi that cua gate:
  - check 14 CRASH khi border side = None (AttributeError, khong phai FAIL)
  - check 13 do im.width thay vi anchor.ext -> bo sot anh bi phong to trong Excel
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

import openpyxl
from openpyxl.styles import Border, PatternFill

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "verify-basic-design.py")
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402

# Dung lai chinh logic cua gate de xac dinh working sheet.
# Tu viet lai se sai: sheet `Screen Index` co cot F = "Sheet Type", nen
# ws["F6"] cua no cung bang "WORKING_SCREEN" — phai loai sheet he thong.
_spec = importlib.util.spec_from_file_location("bd_gate", GATE)
_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gate)


def unmerge_at(ws, r):
    for rng in [str(x) for x in ws.merged_cells.ranges]:
        if ws[rng.split(":")[0]].row == r:
            ws.unmerge_cells(rng)


def screen_sheets(wb):
    return _gate.working_sheets(wb)


def first_screen_sheet(wb):
    ws = screen_sheets(wb)
    return ws[0] if ws else None


# moi case: (ten, check ky vong, ham tiem loi)
# ham tiem loi tra ve chuoi ly do khi thieu dieu kien -> SKIP (khong tinh la loi)
def _no_border(wb):
    if "Screen Error message" not in wb.sheetnames:
        return "Screen Error message"
    es = wb["Screen Error message"]
    for r in range(_gate.CATALOG_HEADER_ROW + 1, es.max_row + 1):
        v = es.cell(r, 1).value
        if v and not str(v).startswith(("🔴", "🟡", "🔵", "🟢")):
            for c in range(1, 11):
                es.cell(r, c).border = Border()
            return None
    return "row trong Screen Error message"


def _header_fill(wb):
    if "Screen Index" not in wb.sheetnames or wb["Screen Index"].cell(6, 2).value is None:
        return "row trong Screen Index"
    for c in range(1, 13):
        wb["Screen Index"].cell(6, c).fill = PatternFill("solid", fgColor="FF1F4E78")


def _drop_err_table(wb):
    ws = first_screen_sheet(wb)
    for r in range(1, ws.max_row + 1):
        v = ws.cell(r, 8).value
        if v and "ERROR SCENARIOS" in str(v):
            for rr in range(r, r + 12):
                unmerge_at(ws, rr)
                for c in range(8, 19):
                    ws.cell(rr, c).value = None
            return None
    return f"bang ERROR SCENARIOS o {ws.title}"


def _touch_sample(wb):
    if "Sample" not in wb.sheetnames:
        return "sheet Sample"
    wb["Sample"]["B1"] = "BI GHI BAY"


def _blow_up_image(wb):
    ws = first_screen_sheet(wb)
    if not (ws and ws._images):
        return "anh UI o screen sheet dau"
    im = ws._images[0]
    im.anchor.ext.cx = int(1600 * 9525)
    im.anchor.ext.cy = int(1200 * 9525)


def _skip_chg_id(wb):
    if "Change History" not in wb.sheetnames or wb["Change History"].cell(6, 1).value is None:
        return "row trong Change History"
    h = wb["Change History"]
    r = 6
    while h.cell(r, 1).value is not None:
        r += 1
    h.cell(r - 1, 1).value = "CHG-0099"


def _drop_index_row(wb):
    if "Screen Index" not in wb.sheetnames or wb["Screen Index"].cell(6, 2).value is None:
        return "row trong Screen Index"
    wb["Screen Index"].delete_rows(6)


def _ghost_code(wb):
    first_screen_sheet(wb)["Q9"] = "loi -> E_ZZ_999"


def _strip_ev(wb):
    # xoa EV o cot R cua item data row dau tien (sau header H="#")
    ws = first_screen_sheet(wb)
    hdr = next((r for r in range(1, 41)
                if str(ws.cell(r, 8).value or "").strip() == "#"), None)
    if hdr is None:
        return f"header bang item o {ws.title}"
    for r in range(hdr + 1, ws.max_row + 1):
        if "ERROR SCENARIOS" in str(ws.cell(r, 8).value or ""):
            break
        name = str(ws.cell(r, 9).value or "") + str(ws.cell(r, 10).value or "")
        body = str(ws.cell(r, 16).value or "") + str(ws.cell(r, 17).value or "")
        if name.strip() and body.strip():
            ws.cell(r, 18).value = "xem man hinh"
            return None
    return f"item data row co mo ta o {ws.title}"


def _item_row(wb, pred):
    """-> (ws, row) cua item dau tien thoa pred(ws, r) trong bang item."""
    for ws in screen_sheets(wb):
        for r in range(9, ws.max_row + 1):
            if "ERROR SCENARIOS" in str(ws.cell(r, 8).value or ""):
                break
            if ws.cell(r, 9).value and pred(ws, r):
                return ws, r
    return None, None


def _blank_api(wb):
    ws, r = _item_row(wb, lambda w, r: str(w.cell(r, 11).value).lower() == "button")
    if not ws:
        return "item Button"
    ws.cell(r, 19).value = None


def _legacy_word(wb):
    ws, r = _item_row(wb, lambda w, r: True)
    if not ws:
        return "item"
    ws.cell(r, 17).value = "Hanh vi khi nhan: " + S.LEGACY_WORD


def _blank_cell(wb):
    ws, r = _item_row(wb, lambda w, r: True)
    if not ws:
        return "item"
    ws.cell(r, 13).value = None   # M required


CASES = [
    ("xoa duong ke data row", 14, _no_border),
    ("data row to fill header", 14, _header_fill),
    ("xoa bang ERROR SCENARIOS", 15, _drop_err_table),
    ("ghi bay vao Sample", 1, _touch_sample),
    ("phong to anh vuot khung", 13, _blow_up_image),
    ("Change ID nhay coc", 12, _skip_chg_id),
    ("xoa row Screen Index", 5, _drop_index_row),
    ("tro Message Code ma", 6, _ghost_code),
]
CASE_ASIS = [("xoa EV o cot R item dau", 16, _strip_ev),
             ("xoa o 'API gọi' cua nut", 17, _blank_api),
             ("con chu cu trong mo ta (D1)", 18, _legacy_word),
             ("bo trong o required cua item", 19, _blank_cell)]


def make_fixture(tmp):
    """Inventory + fe-api-calls + crawl + spec gia -> build-basic-design.py -> (workbook, before)."""
    import csv
    import json
    v = os.path.join(tmp, "ver1_011026_baseline")
    i = os.path.join(v, "_internal")
    os.makedirs(os.path.join(i, "crawl"))
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, cols in S.SHEETS.items():
        wb.create_sheet(name).append(cols)
    wb["10_Site"].append(["WEB-01", "Admin", "https://stg.example.jp", "STG", "test_user", "READ_ONLY", "REPO-01", 2, ""])
    wb["02_Screen"].append(["SC-001", "WEB-01", "/login", "ログイン", "Form", "User", "—", "F-001", "EV-0001", 2, "Confirmed", ""])
    wb["02_Screen"].append(["SC-002", "WEB-01", "/orders/:id", "注文詳細", "Detail", "User", "SC-001", "F-002", "EV-0002", 3,
                            "Confirmed", ""])
    wb.save(os.path.join(i, "inventory.xlsx"))
    cols = ["Screen Route", "Screen File", "Trigger", "UI Label", "Method", "Path", "API ID", "Via", "Trigger Ref",
            "Code Ref", "Confidence"]
    with open(os.path.join(i, "fe-api-calls.csv"), "w", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerow(["/orders/[id]", "REPO-01:src/pages/orders/[id].tsx", "mount", "—", "GET", "/api/orders/:id",
                    "API-001", "axios", "REPO-01:src/pages/orders/[id].tsx#L5", "REPO-01:src/services/o.ts#L2", "static"])
        w.writerow(["/orders/[id]", "REPO-01:src/pages/orders/[id].tsx", "handleSave → onClick", "保存", "POST",
                    "/api/orders", "API-002", "axios", "REPO-01:src/pages/orders/[id].tsx#L9", "REPO-01:src/services/o.ts#L3",
                    "static"])
        w.writerow(["/orders/[id]", "REPO-01:src/pages/orders/[id].tsx", "handleDelete → onClick", "削除", "DELETE",
                    "/api/orders/:id", "API-003", "axios", "REPO-01:src/pages/orders/[id].tsx#L12",
                    "REPO-01:src/services/o.ts#L4", "static"])
    page2 = "https://stg.example.jp/orders/1"
    json.dump([{"url": "https://stg.example.jp/login", "evId": "EV-0001", "items": []},
               {"url": page2, "evId": "EV-0002", "items": [
                   {"tag": "input", "type": "text", "label": "メモ", "maxlength": 50, "required": False},
                   {"tag": "button", "type": "submit", "label": "保存"},
                   {"tag": "button", "type": "button", "label": "印刷"},
                   {"tag": "a", "type": None, "label": "一覧へ戻る"}]}],
              open(os.path.join(i, "crawl", "pages.json"), "w", encoding="utf8"), ensure_ascii=False)
    json.dump([{"page": page2, "url": "https://stg.example.jp/api/stats", "status": 500},
               {"page": page2, "url": "https://stg.example.jp/api/log", "status": "REQUEST_BLOCKED", "noise": "read-only-block"}],
              open(os.path.join(i, "crawl", "network.json"), "w"))
    json.dump([{"url": page2, "text": "Failed to fetch", "noise": "read-only-block"}],
              open(os.path.join(i, "crawl", "console.json"), "w"))
    os.makedirs(os.path.join(v, "annotated"))
    try:
        from PIL import Image
        Image.new("RGB", (1400, 900), "white").save(os.path.join(v, "annotated", "SC-001.png"))
        img = {"image": "annotated/SC-001.png"}
    except ImportError:
        img = {}
    spec = {"screens": {"SC-001": dict(img, purpose="ログインする", items=[
        {"name_jp": "メールアドレス", "name_vn": "Email", "type": "Textbox", "status": "Enable", "required": "Yes",
         "maxlength": "256", "default": "ー", "p": "・必須\n1. 未入力 → E_SC001_001", "q": "・Bắt buộc\n1. Chưa nhập → E_SC001_001",
         "r": "REPO-01:src/pages/login.tsx#L20"}],
        errors=[{"item": "メールアドレス", "category": "🔴 Validation", "display": "Inline", "code": "E_SC001_001",
                 "msg_jp": "メールアドレスを入力してください。", "msg_vn": "Vui lòng nhập email.",
                 "action_jp": "未入力で「ログイン」を押す", "action_vn": "Để trống rồi nhấn 「ログイン」",
                 "next": "Không gửi form, focus ô email", "source": "REPO-01:src/i18n/ja.json#L3"}])}}
    json.dump(spec, open(os.path.join(i, "spec.json"), "w", encoding="utf8"), ensure_ascii=False)
    out = os.path.join(v, "05_BasicDesign", "BasicDesign_WEB-01_ver1.xlsx")
    before = os.path.join(i, "bd_before_WEB-01.xlsx")
    p = subprocess.run([sys.executable, os.path.join(HERE, "build-basic-design.py"), "--inventory",
                        os.path.join(i, "inventory.xlsx"), "--site", "WEB-01", "--version", "ver1",
                        "--fe-api-calls", os.path.join(i, "fe-api-calls.csv"), "--crawl", os.path.join(i, "crawl"),
                        "--spec", os.path.join(i, "spec.json"), "--q-start", "10", "--out", out, "--before", before,
                        "--date", "2026-10-27"], capture_output=True, text=True)
    if p.returncode:
        sys.exit("FAIL: build-basic-design.py loi:\n" + p.stdout + p.stderr)
    return out, before, json.loads(p.stdout)


def fixture_checks(out, stat):
    """build-basic-design: cot S dung nguon fe-api-calls, nut chi co trong code co dong, loi web vao ERROR SCENARIOS."""
    wb = openpyxl.load_workbook(out)
    ws = wb["SC-002"]
    rows = {str(ws.cell(r, 10).value): r for r in range(9, ws.max_row + 1) if ws.cell(r, 10).value}
    api = {k: str(ws.cell(r, 19).value) for k, r in rows.items()}
    txt = " ".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)
    ok = [("Mở màn -> GET (API-001)", api.get("Mở màn") == "Mở màn → GET /api/orders/:id (API-001)"),
          ("nut 保存 -> POST (API-002)", api.get("保存") == "POST /api/orders (API-002)"),
          ("nut 削除 chi co trong code -> dong item + code-ref", api.get("削除") == "DELETE /api/orders/:id (API-003)"
           and "#L12" in str(ws.cell(rows.get("削除", 1), 18).value)),
          ("nut 印刷 khong co bang chung -> Cần xác nhận — Q-010", api.get("印刷") == S.NEED_CONFIRM + " — Q-010"),
          ("link -> Không gọi API", api.get("一覧へ戻る", "").startswith("Không gọi API")),
          ("loi web HTTP 500 vao ERROR SCENARIOS, noise bi bo", "HTTP 500" in txt and "Failed to fetch" not in txt),
          ("khong freeze panel (R13)", all(w.freeze_panes is None for w in wb.worksheets)),
          ("stdout dem o Cần xác nhận + next_q", stat.get("confirm_cells", 0) >= 1 and stat.get("next_q", 0) > 10)]
    bad = 0
    for name, good in ok:
        bad += not good
        print(f"{'build: ' + name:60} {'OK' if good else 'THAT BAI'}")
    return bad


CODE_PAGE = """import { useRouter } from 'next/router';
import { removeOrder, exportCsv } from '../services/o';
export default function Orders() {
  const router = useRouter();
  const handleRemove = async () => { await removeOrder(1); };
  const goEdit = () => { router.push('/orders/1/edit'); };
  return (<div>
    <DesktopDatePicker label="from" />
    <IconButton aria-label="delete" onClick={handleRemove}><DeleteIcon /></IconButton>
    <Button onClick={goEdit}>編集</Button>
    <Button onClick={() => exportCsv()}>CSV出力</Button>
  </div>);
}
"""


def code_checks(tmp):
    """Nut khong khop nhan -> tra code (fe-screen-files.json), nhieu EV / o, nhan co gia tri dong."""
    import csv
    import json
    v = os.path.join(tmp, "ver1_021026_code")
    i, repo = os.path.join(v, "_internal"), os.path.join(tmp, "repo")
    code = os.path.join(i, "recon", "code", "REPO-01")
    for d in (code, os.path.join(i, "crawl"), os.path.join(repo, "src", "pages")):
        os.makedirs(d, exist_ok=True)
    open(os.path.join(repo, "src", "pages", "orders.tsx"), "w", encoding="utf8").write(CODE_PAGE)
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, cols in S.SHEETS.items():
        wb.create_sheet(name).append(cols)
    wb["10_Site"].append(["WEB-01", "Admin", "https://stg.example.jp", "STG", "test_user", "READ_ONLY", "REPO-01", 1, ""])
    wb["02_Screen"].append(["SC-001", "WEB-01", "/orders", "注文一覧", "List", "User", "—", "F-001",
                            "EV-0003; EV-0004", 1, "Confirmed", ""])
    wb["11_Repo"].append(["REPO-01", repo, "FE", "Next.js", "WEB-01", ""])
    wb.save(os.path.join(i, "inventory.xlsx"))
    ref = "REPO-01:src/pages/orders.tsx#L%d"
    with open(os.path.join(code, "fe-api-calls.csv"), "w", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Screen Route", "Screen File", "Trigger", "UI Label", "Method", "Path", "API ID", "Via",
                    "Trigger Ref", "Code Ref", "Confidence"])
        w.writerow(["/orders", "REPO-01:src/pages/orders.tsx", "handleRemove → onClick", "—", "DELETE",
                    "/api/orders/:id", "API-003", "x", ref % 5, "REPO-01:src/services/o.ts#L2", "static"])
        w.writerow(["/orders", "REPO-01:src/pages/orders.tsx", "onClick", "—", "GET", "/api/orders/csv", "API-004",
                    "x", ref % 11, "REPO-01:src/services/o.ts#L3", "static"])
        w.writerow(["/orders", "REPO-01:src/pages/orders.tsx", "handleSave → onClick", "保存", "POST", "/api/orders",
                    "API-002", "x", ref % 20, "REPO-01:src/services/o.ts#L4", "static"])
    json.dump({"/orders": ["src/pages/orders.tsx"]}, open(os.path.join(code, "fe-screen-files.json"), "w"))
    json.dump([{"url": "https://stg.example.jp/orders", "evId": "EV-0004", "items": [
        {"tag": "button", "type": "button", "label": "Choose date, selected date is Oct 28, 2026"},
        {"tag": "button", "type": "button", "label": "delete"},
        {"tag": "button", "type": "button", "label": "編集"},
        {"tag": "button", "type": "button", "label": "CSV出力"},
        {"tag": "button", "type": "button", "label": "保存する"},
        {"tag": "button", "type": "button", "label": "印刷"},
        {"tag": "button", "type": "button", "label": "10/28"},
        {"tag": "button", "type": "button", "label": "10/29"}]}],
        open(os.path.join(i, "crawl", "pages.json"), "w", encoding="utf8"), ensure_ascii=False)
    out = os.path.join(v, "05_BasicDesign", "BasicDesign_WEB-01_ver1.xlsx")
    p = subprocess.run([sys.executable, os.path.join(HERE, "build-basic-design.py"), "--inventory",
                        os.path.join(i, "inventory.xlsx"), "--site", "WEB-01", "--version", "ver1",
                        "--fe-api-calls", os.path.join(code, "fe-api-calls.csv"), "--crawl", os.path.join(i, "crawl"),
                        "--q-start", "1", "--out", out, "--date", "2026-10-28"], capture_output=True, text=True)
    if p.returncode:
        print("build (code): loi\n" + p.stdout + p.stderr)
        return 1
    stat = json.loads(p.stdout)
    ws = openpyxl.load_workbook(out)["SC-001"]
    rows = {str(ws.cell(r, 10).value): r for r in range(9, ws.max_row + 1) if ws.cell(r, 10).value}
    api = {k: str(ws.cell(r, 19).value) for k, r in rows.items()}
    ref_of = {k: str(ws.cell(r, 18).value) for k, r in rows.items()}
    txt = " ".join(str(c.value) for row in ws.iter_rows(min_row=9, min_col=9, max_col=17) for c in row if c.value)
    ok = [("Screenshot EV 'EV-0003; EV-0004' -> ghep trang EV-0004", "delete" in rows),
          ("nhan datepicker bo ngay da chon -> 'Choose date' + code-ref", api.get("Choose date", "").startswith(
              "Không gọi API — mở bộ chọn") and "orders.tsx#L8" in ref_of.get("Choose date", "")),
          ("nhan khong chua gia tri ngay (2026 / Oct 28)", "2026" not in txt and "Oct 28" not in txt),
          ("o ngay 10/28, 10/29 -> 1 dong （日付）", "（日付）" in rows and "10/28" not in txt),
          ("icon aria-label=delete -> handler -> DELETE (API-003)", api.get("delete") == "DELETE /api/orders/:id (API-003)"
           and "#L9" in ref_of.get("delete", "")),
          ("router.push -> Không gọi API — chuyển trang", api.get("編集", "").startswith("Không gọi API — chuyển trang")),
          ("onClick viet thang trong JSX -> Trigger Ref cung dong (API-004)",
           api.get("CSV出力") == "GET /api/orders/csv (API-004)"),
          ("nhan gan dung 保存する ~ 保存 -> POST (API-002)", api.get("保存する") == "POST /api/orders (API-002)"),
          ("khong co trong code -> Cần xác nhận — Q-001", api.get("印刷") == S.NEED_CONFIRM + " — Q-001"),
          ("stdout code_matched / confirm_cells", stat.get("code_matched") == 4 and stat.get("confirm_cells") == 2)]
    bad = 0
    for name, good in ok:
        bad += not good
        print(f"{'code: ' + name:60} {'OK' if good else 'THAT BAI'}")
    if bad:
        print(json.dumps({"api": api, "stat": stat}, ensure_ascii=False))
    return bad


def run_gate(path, before, screens, asis=False):
    cmd = [sys.executable, GATE, path, "--expect-screens", screens]
    if before:
        cmd += ["--before", before]
    if asis:
        cmd.append("--asis")
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout + p.stderr
    if "Traceback" in out:
        return "CRASH", []
    fails = []
    for line in out.splitlines():
        if line.startswith("| ") and "**FAIL**" in line:
            try:
                fails.append(int(line.split("|")[1].strip()))
            except ValueError:
                pass
    return p.returncode, fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook", nargs="?", help="bo trong -> tu sinh fixture bang build-basic-design.py (--asis)")
    ap.add_argument("--before")
    ap.add_argument("--asis", action="store_true",
                    help="gate chay --asis + them case check 16-19")
    args = ap.parse_args()
    pre_bad = 0
    fixture_dir = None
    if not args.workbook:
        fixture_dir = tempfile.mkdtemp(prefix="selftest-bd-")
        args.workbook, args.before, stat = make_fixture(fixture_dir)
        args.asis = True
        pre_bad = fixture_checks(args.workbook, stat) + code_checks(fixture_dir)
    cases = CASES + (CASE_ASIS if args.asis else [])

    wb = openpyxl.load_workbook(args.workbook)
    screens = ",".join(str(ws["F1"].value) for ws in screen_sheets(wb))
    if not screens:
        sys.exit("FAIL: workbook khong co working sheet nao")

    code, fails = run_gate(args.workbook, args.before, screens, args.asis)
    print(f"{'BASELINE (khong tiem loi)':34} exit={code} fails={fails or '[]'}")
    if code != 0:
        sys.exit("FAIL: workbook dau vao phai PASS gate truoc khi self-test")

    tmp = tempfile.mkdtemp()
    bad = skip = 0
    print()
    print(f"{'LOI DA TIEM':34} {'KY VONG':8} {'BAT DUOC':12} KQ")
    print("-" * 74)
    for name, want, inject in cases:
        p = os.path.join(tmp, f"t_{want}_{abs(hash(name)) % 9999}.xlsx")
        shutil.copy(args.workbook, p)
        w = openpyxl.load_workbook(p)
        why = inject(w)
        if why:
            skip += 1
            print(f"{name:34} #{want:<7} {'-':12} SKIP — workbook khong co {why}")
            continue
        w.save(p)
        code, fails = run_gate(p, args.before, screens, args.asis)
        ok = code == 1 and want in fails
        if not ok:
            bad += 1
        print(f"{name:34} #{want:<7} {str(fails) if fails != 'CRASH' else 'CRASH':12} "
              f"{'OK' if ok else 'THAT BAI'}")
    shutil.rmtree(tmp, ignore_errors=True)
    if fixture_dir:
        shutil.rmtree(fixture_dir, ignore_errors=True)
    print()
    n = len(cases) - skip
    print(f"{n - bad}/{n} case bat dung check ky vong" + (f" ({skip} SKIP)" if skip else "")
          + (f" · build-basic-design {pre_bad} THAT BAI" if pre_bad else "")
          + f" — {'PASS' if not (bad or pre_bad) else 'FAIL'}")
    sys.exit(1 if bad or pre_bad else 0)


if __name__ == "__main__":
    main()
