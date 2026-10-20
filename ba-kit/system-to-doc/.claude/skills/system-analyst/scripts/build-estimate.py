#!/usr/bin/env python3
"""Sinh 見積書 cho Luong 2 tu _internal/estimate.json (1 dong = 1 chuc nang) — deliverable gui KH.

  python3 build-estimate.py --estimate <ver>/_internal/estimate.json --out <ver>/CR-<id>_見積書.xlsx \
      [--lang ja|vi] [--internal] [--rates .claude/config/function-rates.json] [--template templates/template_mitsumori.xlsx] \
      [--cr-json <ver>/_internal/cr.json]

--lang ja (mac dinh) = ban gui KH: tieng Nhat, khong ma noi bo. --lang vi --internal = ban noi bo (them cot Impact + can cu).
Exit 0 OK · 1 estimate.json sai schema · 2 thieu openpyxl.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estimate_core as E  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--estimate", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", choices=["ja", "vi"], default="ja")
    ap.add_argument("--internal", action="store_true")
    ap.add_argument("--rates", default=".claude/config/function-rates.json")
    ap.add_argument("--template", default="templates/template_mitsumori.xlsx")
    ap.add_argument("--cr-json")
    a = ap.parse_args()
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("Thieu openpyxl", file=sys.stderr)
        return 2
    est = json.load(open(a.estimate, encoding="utf8"))
    meta, rates = E.load_rates(a.rates)
    cr = json.load(open(a.cr_json, encoding="utf8")) if a.cr_json else None
    err = E.validate(est, rates, cr)
    if err:
        print("estimate.json sai:\n  " + "\n  ".join(err), file=sys.stderr)
        return 1
    if a.lang == "ja" and a.internal:
        print("--internal chi dung voi --lang vi (ban KH khong co cot noi bo)", file=sys.stderr)
        return 1
    wb, pos, tm = E.build_workbook(est, rates, meta, a.template, a.lang, a.internal)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    wb.save(a.out)
    tot = E.plan_totals(est, rates, tm)
    al = sum(v["sub"] for v in tot.values())
    s1 = sum(E.row_numbers(x, rates, tm)["sub"] for x in est["rows"] if x["step"] == "Step 1")
    print("Da ghi %s — %d dong chuc nang (dong %d..%d) · Step1 %.2f · toan bo %.2f 人日 (%.2f 人月) · rates %s"
          % (a.out, pos["rows"], pos["first"], pos["last"], s1, al, al / tm["md_per_month"], meta.get("status")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
