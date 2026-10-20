#!/usr/bin/env python3
"""Gate V-EST — kiem 見積書 Luong 2 (ban KH tieng Nhat hoac ban noi bo).

  python3 verify-estimate.py <CR-xxx_見積書.xlsx> --estimate <estimate.json> [--cr-json cr.json] [--lang ja|vi] \
      [--rates ...] [--template ...] [--out gates/v-est.md]
  python3 verify-estimate.py <bat ky 見積書.xlsx> --scan-only     # chi kiem cau truc + dai cong thuc tong (VD ban FINAL)

E1 cau truc · E2 流用可否/◉◯/STEP · E3 dai cong thuc tong · E4 ngon ngu ban KH · E5 実装 = rate x qty, Step1+Step2 = toan bo
· E6 (WARN) override / bang cong so chua duyet · E7 sheet 前提条件 4 khoi · E8 trace impact NEW/UPD
· E9 (WARN, ban vi) con chu Nhat ngoai letterhead · E10 (WARN) van phong: noi dung qua ngan / khong cau truc (writing-style.md).
Exit 0 PASS · 1 FAIL · 2 khong chay duoc.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estimate_core as E  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--estimate")
    ap.add_argument("--cr-json")
    ap.add_argument("--lang", choices=["ja", "vi"], default="ja")
    ap.add_argument("--rates", default=".claude/config/function-rates.json")
    ap.add_argument("--template", default="templates/template_mitsumori.xlsx")
    ap.add_argument("--sheet")
    ap.add_argument("--scan-only", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        from openpyxl import load_workbook
    except ImportError:
        print("Thieu openpyxl", file=sys.stderr)
        return 2
    if not a.scan_only and not a.estimate:
        print("Can --estimate (hoac --scan-only)", file=sys.stderr)
        return 2
    wb = load_workbook(a.xlsx)
    sheet = a.sheet or next((s.title for s in wb.worksheets if E.find_layout(s)[0] and "impl" in E.find_layout(s)[1]), None)
    if not sheet:
        print("Khong thay sheet 見積書 trong %s" % a.xlsx, file=sys.stderr)
        return 2
    est = rates = rmeta = tm = cr = None
    if not a.scan_only:
        est = json.load(open(a.estimate, encoding="utf8"))
        rmeta, rates = E.load_rates(a.rates)
        _, tm = E.load_template(a.template)
        cr = json.load(open(a.cr_json, encoding="utf8")) if a.cr_json else None
        err = E.validate(est, rates, cr)
        if err:
            print("estimate.json sai:\n  " + "\n  ".join(err), file=sys.stderr)
            return 1
    res = E.verify(wb, sheet, est, rates, rmeta or {}, tm, a.lang, cr)
    fail = sum(1 for _, _, b, w in res if b and not w)
    warn = sum(1 for _, _, b, w in res if b and w)
    lines = ["# V-EST — %s (sheet %s, lang %s%s)" % (os.path.basename(a.xlsx), sheet, a.lang, ", scan-only" if a.scan_only else ""), ""]
    for i, title, b, w in res:
        st = "PASS" if not b else ("WARN" if w else "FAIL")
        lines.append("- %s %s — %s" % (st, i, title))
        lines += ["    - %s" % x for x in b[:15]]
    lines += ["", "%d checks · %d PASS · %d FAIL · %d WARN" % (len(res), len(res) - fail - warn, fail, warn)]
    out = "\n".join(lines)
    print(out)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, "w", encoding="utf8").write(out + "\n")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
