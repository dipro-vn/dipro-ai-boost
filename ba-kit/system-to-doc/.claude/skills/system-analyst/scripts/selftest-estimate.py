#!/usr/bin/env python3
"""Self-test 見積書 Luong 2: estimate_core + build-estimate + gate V-EST (S10).

  python3 selftest-estimate.py [--golden <見積書 FINAL.xlsx>]

Fixture tong hop (khong dung du lieu KH) -> build ja / vi -> V-EST PASS; ca am: chu Viet o ban KH, dai cong thuc tong
thieu, 実装 bi sua tay, impact chua thuoc dong nao, schema sai. --golden: ban FINAL lam mau hoi quy — moi dong 'from' cua
function-rates.json phai co 実装 nam trong range, va gate E3 phai bat duoc loi dai tong neu ban do co.
Exit 0 tat ca PASS · 1 co ca FAIL.
"""
import argparse
import copy
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
import estimate_core as E  # noqa: E402

RATES = os.path.join(KIT, ".claude/config/function-rates.json")
TPL = os.path.join(KIT, "templates/template_mitsumori.xlsx")
J = lambda ja, vi: {"ja": ja, "vi": vi}  # noqa: E731


def fixture():
    row = lambda sec, code, pat, imps, must="◉", step="Step 1", qty=1: {  # noqa: E731
        "section": sec, "big": J("画面A", "Màn A"), "mid": J("一覧", "Danh sách"), "small": J("新規", "Mới"),
        "content": J("項目を追加する。", "Thêm mục."), "confirm": None, "reuse": "一部流用", "must": must, "step": step,
        "pattern": pat, "code": code, "qty": qty, "req": True, "impacts": imps, "impl_override": None, "override_note": None}
    pr = {k: [J("前提です。", "Tiền đề.")] for k in E.PREMISE_KEYS}
    return {"meta": {"cr_id": "CR-999", "title": J("テスト", "Thử"), "customer": J("株式会社サンプル", "Công ty ABC"), "date": "2026-01-05"},
            "patterns": [{"id": "A", "label": J("案A", "A")}, {"id": "B", "label": J("案B", "B")}],
            "combos": [{"label": J("案A", "A"), "patterns": ["A"]}, {"label": J("案B", "B"), "patterns": ["B"]}],
            "rows": [row("user", "SCR-UPD-L", "A", ["IMP-001"]), row("user", "SCR-UPD-M", "B", ["IMP-002"], must="◯"),
                     row("sa", "SETTING-FIELD", None, ["IMP-003"]), row("admin", "CSV-EXPORT", None, ["IMP-004"], step="Step 2", must="◯"),
                     row("common", "EXISTING-CONFIRM", None, []), row("common", "DB-COLUMN", None, ["IMP-005"], qty=2)],
            "premises": pr}


CR = {"impacts": [{"id": "IMP-00%d" % i, "axis": "Screen", "change_type": "UPD"} for i in range(1, 6)] +
      [{"id": "IMP-009", "axis": "Mockup", "change_type": "NEW"}, {"id": "IMP-010", "axis": "System", "change_type": "IMPACT"}]}


def run(est, lang, mutate=None, cr=CR):
    meta, rates = E.load_rates(RATES)
    wb, pos, tm = E.build_workbook(est, rates, meta, TPL, lang, internal=(lang == "vi"))
    if mutate:
        mutate(wb.worksheets[0], pos)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.xlsx")
        wb.save(p)
        from openpyxl import load_workbook
        wb2 = load_workbook(p)
    res = E.verify(wb2, wb2.sheetnames[0], est, rates, meta, tm, lang, cr)
    return {i: (bool(b) and not w) for i, _t, b, w in res}, pos


def _wb_for(est, lang):
    meta, rates = E.load_rates(RATES)
    wb, pos, tm = E.build_workbook(est, rates, meta, TPL, lang, internal=False)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.xlsx")
        wb.save(p)
        from openpyxl import load_workbook
        wb2 = load_workbook(p)
    return wb2, wb2.sheetnames[0], est, rates, meta, tm, lang


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=None)
    a = ap.parse_args()
    cases = []
    ok = lambda name, cond: cases.append((name, bool(cond)))  # noqa: E731
    meta, rates = E.load_rates(RATES)
    est = fixture()
    ok("fixture hop le", not E.validate(est, rates, CR))
    for lang in ("ja", "vi"):
        fails, pos = run(est, lang)
        ok("build %s -> V-EST khong FAIL" % lang, not any(fails.values()))
        ok("build %s -> 6 dong chuc nang" % lang, pos["rows"] == 6)
    _, tm = E.load_template(TPL)
    s1 = sum(E.row_numbers(x, rates, tm)["sub"] for x in est["rows"] if x["step"] == "Step 1")
    s2 = sum(E.row_numbers(x, rates, tm)["sub"] for x in est["rows"] if x["step"] == "Step 2")
    al = sum(v["sub"] for v in E.plan_totals(est, rates, tm).values())
    ok("Step1 + Step2 = toan bo", abs(s1 + s2 - al) < 1e-9)
    n = E.row_numbers(est["rows"][4], rates, tm)
    ok("EXISTING-CONFIRM: 実装 0, 要件/テスト/管理 co dinh 0.5", (n["impl"], n["req"], n["test"], n["mgmt"]) == (0, 0.5, 0.5, 0.5))
    n = E.row_numbers(est["rows"][3], rates, tm)
    ok("CSV (ui '-') -> UI 0", n["ui"] == 0)
    n = E.row_numbers(est["rows"][5], rates, tm)
    ok("DB-COLUMN x2 -> 実装 2", n["impl"] == 2)
    # ---- ca am
    bad = copy.deepcopy(est)
    bad["rows"][0]["content"]["ja"] = "Thêm mục IMP-001"
    ok("ban KH co chu Viet / ma noi bo -> E4 FAIL", run(bad, "ja")[0]["E4"])
    ok("dai cong thuc 全ての機能 thieu dong -> E3 FAIL",
       run(est, "ja", lambda ws, p: ws.cell(row=p["row_all"], column=12, value="=SUM(L%d:L%d)" % (p["first"] + 1, p["last"] - 1)))[0]["E3"])
    ok("実装 sua tay -> E5 FAIL", run(est, "ja", lambda ws, p: ws.cell(row=p["first"], column=12, value=9))[0]["E5"])
    cr2 = copy.deepcopy(CR)
    cr2["impacts"].append({"id": "IMP-011", "axis": "DB", "change_type": "NEW"})
    ok("impact NEW chua thuoc dong nao -> E8 FAIL", run(est, "ja", cr=cr2)[0]["E8"])
    ok("Mockup / IMPACT khong bat buoc thuoc dong", "IMP-009" not in E.trace_missing(est, CR) and "IMP-010" not in E.trace_missing(est, CR))
    for name, f in (("section sai", lambda e: e["rows"][0].update(section="x")), ("code khong co", lambda e: e["rows"][0].update(code="ZZZ")),
                    ("override khong note", lambda e: e["rows"][0].update(impl_override=3)), ("must sai", lambda e: e["rows"][0].update(must="○")),
                    ("pattern khong khai bao", lambda e: e["rows"][0].update(pattern="Q")), ("thieu tien de", lambda e: e["premises"].update({"想定されるリスク": []}))):
        b = copy.deepcopy(est)
        f(b)
        ok("validate bat: %s" % name, E.validate(b, rates))
    # ---- van phong (writing-style.md)
    b = copy.deepcopy(est)
    b["questions"] = [{"id": "Q1", "group": J("分類", "Nhóm"), "question": J("CQ-005 について", "Hỏi CQ-005"), "why": J("理由", "Vì sao"),
                       "proposal": J("提案", "Đề xuất"), "alt": J("影響", "Ảnh hưởng"), "due": "2026/01/05"}]
    ok("validate bat: cau hoi gui khach co ma noi bo", E.validate(b, rates))
    b["questions"][0]["question"] = J("1か月分は30日間でよろしいでしょうか。", "1 tháng = 30 ngày?")
    ok("cau hoi hop le -> build co sheet 確認事項", not E.validate(b, rates) and "確認事項" in E.build_workbook(b, rates, meta, TPL, "ja")[0].sheetnames)
    b2 = copy.deepcopy(est)
    b2["rows"][0]["content"]["vi"] = "Sửa 店舗詳細"
    fails, _ = run(b2, "vi")
    res = {i: bool(x) for i, _t, x, _w in E.verify(*_wb_for(b2, "vi"))}
    ok("ban vi con chu Nhat -> E9 WARN", res.get("E9"))
    ok("noi dung ngan / khong cau truc -> E10 WARN", res.get("E10"))
    # ---- golden (ban FINAL that, chi doc so — khong ghi noi dung ra ngoai)
    if a.golden:
        from openpyxl import load_workbook
        wb = load_workbook(a.golden)
        ws = next(s for s in wb.worksheets if E.find_layout(s)[0] and "impl" in E.find_layout(s)[1])
        lay, items, tots, _ = E.scan_sheet(ws)
        by = {it["row"]: it for it in items}
        miss = []
        for r in E.load_rates(RATES)[0]["rates"]:
            for fr in r.get("from") or []:
                v = by.get(fr, {}).get("impl")
                if not isinstance(v, (int, float)) or not (r["range"][0] <= v <= r["range"][1]):
                    miss.append("%s dong %s = %r ngoai %s" % (r["code"], fr, v, r["range"]))
        ok("golden: 実装 cac dong 'from' nam trong range cua function-rates (%s)" % ("; ".join(miss[:3]) or "OK"), not miss)
        ok("golden: %d dong hang muc, 4 nhom, du 流用可否 / STEP" % len(items),
           len(items) >= 100 and all(it.get("step") in E.STEPS for it in items))
        ok("golden: gate E3 chay duoc tren ban FINAL (%d loi dai tong)" % len(E.check_ranges(lay, items, tots)), True)
    fail = [c for c in cases if not c[1]]
    for name, good in cases:
        print("%s  %s" % ("PASS" if good else "FAIL", name))
    print("\n%d/%d PASS" % (len(cases) - len(fail), len(cases)))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
