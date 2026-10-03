#!/usr/bin/env python3
"""GATE V-CR — CR Impact (Luong 2): cr.json + CR-<id>_Impact.xlsx (2 sheet Summary + Impact).

  python3 verify-cr-impact.py <ver>/CR-001_Impact.xlsx --cr-json <ver>/_internal/cr.json \
      --baseline <outputs>/verK_... [--rates .claude/config/md-unit-rates.json] \
      [--other-cr <ver khac>/_internal/cr.json ...] [--out <ver>/_internal/gates/v-cr.md]

Baseline Ref: SC-/F-/API-/EXT-/WEB- · table:orders · column:orders.status · DS:<token> · DS-component:<Comp>
· DS:WEB-01:<token> / DS-component:WEB-01:<Comp> (chon site) · — ; nhieu ref cach nhau ';'.
Design system baseline: 04_DesignSystem/project/ (1 bo) hoac 04_DesignSystem/WEB-xx/project/ (moi site 1 bo).
--rates mac dinh: <kit>/.claude/config/md-unit-rates.json. Tom tat impact in ra stderr.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402
import cr_common as C  # noqa: E402
from gate_report import Gate  # noqa: E402

KIT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def read_xlsx(path):
    """-> (sheetnames, impact header, impact rows {col: value}, total MD row, summary rows [list])."""
    from openpyxl import load_workbook
    wb = load_workbook(path, data_only=True)
    names = wb.sheetnames
    hdr, rows, total, summ = [], [], None, []
    if S.CR_SHEET_IMPACT in names:
        ws = wb[S.CR_SHEET_IMPACT]
        hdr = [C.txt(c.value) for c in ws[1]]
        for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            d = {h: r[k] if k < len(r) else None for k, h in enumerate(hdr) if h}
            iid = C.txt(d.get("Impact ID"))
            if iid == C.L_TOTAL_MD:
                total = d.get("MD")
            elif iid:
                d["__row__"] = i
                rows.append(d)
    if S.CR_SHEET_SUMMARY in names:
        summ = [list(r) for r in wb[S.CR_SHEET_SUMMARY].iter_rows(values_only=True)]
    return names, hdr, rows, total, summ


def num(v):
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


def summary_matrix(summ):
    """Doc bang Truc x Loai tren Summary -> ({axis: [NEW,UPD,DEL,IMPACT,Tong]}, tong hang, Tong MD dau trang)."""
    mat, tot, head_total = {}, None, None
    start = None
    for i, r in enumerate(summ):
        a = C.txt(r[0] if r else "")
        if a == C.L_TOTAL_MD and head_total is None and len(r) > 1:
            head_total = num(r[1])
        if a == C.L_AXIS_HDR and [C.txt(x) for x in r[1:5]] == S.CR_CHANGE_TYPE:
            start = i
            break
    if start is None:
        return None, None, head_total
    for r in summ[start + 1:]:
        a = C.txt(r[0])
        vals = [num(x) for x in (list(r[1:6]) + [None] * 5)[:5]]
        if a == C.L_TOTAL:
            tot = vals
            break
        m = re.search(r"\((\w+)\)\s*$", a)
        if m:
            mat[m.group(1)] = vals
        else:
            break
    return mat, tot, head_total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("impact")
    ap.add_argument("--cr-json", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--rates", default=os.path.join(KIT, S.MD_RATES_PATH))
    ap.add_argument("--other-cr", action="append", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("Thieu openpyxl. Chay: pip install openpyxl", file=sys.stderr)
        return 2

    cr = C.load_json(a.cr_json)
    rates_meta, rates = C.load_rates(a.rates)
    B = C.load_baseline(a.baseline)
    names, hdr, xrows, xtotal, summ = read_xlsx(a.impact)
    g = Gate("GATE V-CR — %s" % os.path.basename(a.impact))
    meta = cr.get("meta") or {}
    J = cr.get("justification") or []
    IMP = cr.get("impacts") or []
    NOI = cr.get("no_impact_axes") or []
    Q = cr.get("questions") or []
    base_name = os.path.basename(os.path.normpath(a.baseline))

    # 1. Workbook
    bad = []
    if names != [S.CR_SHEET_SUMMARY, S.CR_SHEET_IMPACT]:
        bad.append("sheet = %s (phai dung %s, %s)" % (names, S.CR_SHEET_SUMMARY, S.CR_SHEET_IMPACT))
    if S.CR_SHEET_IMPACT in names and [h for h in hdr if h] != S.CR_IMPACT_COLS:
        bad.append("header Impact khac CR_IMPACT_COLS: %s" % [h for h in hdr if h])
    g.check(1, "Workbook dung 2 sheet Summary + Impact, header Impact dung schema", bad)

    # 2. Meta
    bad = ["meta.%s rong/UNKNOWN" % k for k in S.CR_META_KEYS
           if not C.txt(meta.get(k)) or C.txt(meta.get(k)) == S.UNKNOWN]
    if C.txt(meta.get("source_type")) and meta["source_type"] not in S.CR_SOURCE_TYPE:
        bad.append("source_type=%s" % meta["source_type"])
    if C.txt(meta.get("overall_risk")) and meta["overall_risk"] not in S.CR_RISK:
        bad.append("overall_risk=%s" % meta["overall_risk"])
    if C.txt(meta.get("baseline_version")) and meta["baseline_version"] != base_name:
        bad.append("baseline_version=%s != %s" % (meta["baseline_version"], base_name))
    g.check(2, "meta du key, source_type/overall_risk hop le, baseline_version khop", bad)

    ds_warn = []

    def res(ref):
        ok, why, w = C.resolve(ref, B)
        if w:
            ds_warn.append(w)
        return ok, why

    # 3. Justification
    bad = [] if J else ["justification rong — phai giai trinh vi sao la CR"]
    for i, j in enumerate(J):
        tag = C.txt(j.get("item")) or "justification[%d]" % i
        miss = [f for f in ("item", "request", "baseline_ref", "baseline_quote", "why", "not_feedback")
                if not C.txt(j.get(f))]
        if miss:
            bad.append("%s thieu %s" % (tag, ",".join(miss)))
        crit = j.get("criteria") if isinstance(j.get("criteria"), list) else []
        if not crit:
            bad.append("%s khong co tieu chi C1..C6" % tag)
        bad += ["%s tieu chi %s khong co trong C1..C6" % (tag, c) for c in crit if c not in S.CR_CRITERIA]
        for ref in C.refs_of(j.get("baseline_ref")):
            ok, why = res(ref)
            if not ok:
                bad.append("%s %s: %s" % (tag, ref, why))
    g.check(3, "Giai trinh CR: >=1 dong, tieu chi C1..C6, baseline_ref co that + trich dan", bad)

    # 4. Phu 6 truc
    bad = []
    noi = {}
    for x in NOI:
        noi.setdefault(C.txt(x.get("axis")), []).append(x)
    for ax in noi:
        if ax not in S.CR_AXES:
            bad.append("no_impact_axes axis=%s khong hop le" % ax)
    for ax in S.CR_AXES:
        has = any(i.get("axis") == ax for i in IMP)
        if has and ax in noi:
            bad.append("%s vua co impact vua khai khong anh huong" % ax)
        elif not has and ax not in noi:
            bad.append("%s bo trong — them impact hoac no_impact_axes kem ly do" % ax)
        elif not has and len(C.txt(noi[ax][0].get("reason"))) < 15:
            bad.append("%s khong anh huong nhung ly do < 15 ky tu" % ax)
    g.check(4, "Ca 6 truc: co impact HOAC no_impact_axes (ly do >= 15 ky tu), khong ca hai", bad)

    # 5. Impact ID
    bad, seen = [], set()
    for i, imp in enumerate(IMP):
        iid = C.txt(imp.get("id"))
        if not re.match(S.CR_IMPACT_ID, iid):
            bad.append("impacts[%d] id=%r sai dang" % (i, iid))
        if iid in seen:
            bad.append("%s trung" % iid)
        seen.add(iid)
    g.check(5, "Impact ID dung dang IMP-NNN, duy nhat", bad)

    def tag(imp):
        return C.txt(imp.get("id")) or "?"

    # 6. Enum
    bad = []
    for imp in IMP:
        for f, enum in (("axis", S.CR_AXES), ("change_type", S.CR_CHANGE_TYPE),
                        ("conflict", S.CR_CONFLICT), ("risk", S.CR_RISK)):
            if C.txt(imp.get(f)) not in enum:
                bad.append("%s %s=%s" % (tag(imp), f, imp.get(f)))
    g.check(6, "Enum axis / change_type / conflict / risk", bad)

    # 7. UPD/DEL/IMPACT ref ton tai
    bad = []
    for imp in IMP:
        if imp.get("change_type") not in ("UPD", "DEL", "IMPACT"):
            continue
        refs = C.refs_of(imp.get("baseline_ref"))
        if not refs:
            bad.append("%s %s khong co baseline_ref" % (tag(imp), imp.get("change_type")))
        for ref in refs:
            ok, why = res(ref)
            if not ok:
                bad.append("%s %s: %s" % (tag(imp), ref, why))
    g.check(7, "UPD/DEL/IMPACT: moi baseline_ref ton tai trong baseline", bad)

    # 8. NEW
    bad = []
    for imp in IMP:
        if imp.get("change_type") != "NEW":
            continue
        for ref in C.refs_of(imp.get("baseline_ref")):
            low = ref.lower()
            if low.startswith("column:"):
                tc = low[7:].strip()
                if "." not in tc or tc.split(".")[0] not in B["tables"]:
                    bad.append("%s %s: bang cha khong co trong baseline" % (tag(imp), ref))
                elif tc in B["cols"] and imp.get("conflict") != "Yes":
                    bad.append("%s %s: cot da ton tai — trung ten, phai conflict=Yes" % (tag(imp), ref))
                continue
            ok, why = res(ref)
            if not ok:
                bad.append("%s %s: %s (NEW chi gan vao cha da ton tai)" % (tag(imp), ref, why))
    g.check(8, "NEW: ref la — hoac cha ton tai; cot moi trung cot cu phai conflict=Yes", bad)

    # 9. Noi dung bat buoc
    bad = []
    for imp in IMP:
        miss = [f for f in ("item", "change", "impact_on_current") if not C.txt(imp.get(f))]
        if len(C.txt(imp.get("why_change"))) < 10:
            miss.append("why_change(>=10 ky tu)")
        if miss:
            bad.append("%s thieu %s" % (tag(imp), ",".join(miss)))
    g.check(9, "Moi impact co hang muc, noi dung, vi sao phai sua, anh huong", bad)

    # 10. Don gia
    bad = []
    for imp in IMP:
        bad += C.rate_errors(imp, rates, tag(imp))
    g.check(10, "rate_code co trong bang don gia, dung truc + loai; qty > 0", bad)

    # 11. Sheet Impact khop cr.json, MD = rate x qty
    bad = []
    by_id = {C.txt(r.get("Impact ID")): r for r in xrows}
    if [C.txt(r.get("Impact ID")) for r in xrows] != [tag(i) for i in IMP]:
        bad.append("Impact ID tren sheet %s != cr.json %s — chay lai build-cr-impact.py" % (
            list(by_id), [tag(i) for i in IMP]))
    for imp in IMP:
        r = by_id.get(tag(imp))
        if not r:
            continue
        loc = "Impact!%s" % r["__row__"]
        for col, f in (("Trục", "axis"), ("Loại", "change_type"), ("Mã đơn giá", "rate_code")):
            if C.txt(r.get(col)) != C.txt(imp.get(f)):
                bad.append("%s %s=%s != cr.json %s" % (loc, col, r.get(col), imp.get(f)))
        if num(r.get("Số lượng")) != num(imp.get("qty")):
            bad.append("%s Số lượng=%s != qty %s" % (loc, r.get("Số lượng"), imp.get("qty")))
        want = C.md_of(imp, rates)
        if want is not None and num(r.get("MD")) != want:
            bad.append("%s %s MD=%s != %s x %s = %s" % (loc, tag(imp), r.get("MD"),
                       C.fmt_md(rates[imp["rate_code"]].get("md")), imp.get("qty"), C.fmt_md(want)))
    m, row_tot, col_tot, grand = C.md_matrix(IMP, rates)
    if num(xtotal) != grand:
        bad.append("dong Tong MD sheet Impact=%s != %s" % (xtotal, C.fmt_md(grand)))
    g.check(11, "Sheet Impact khop cr.json; MD = don gia x so luong; dong Tong MD dung", bad)

    # 12. Tong tren Summary
    bad = []
    smat, stot, shead = summary_matrix(summ)
    if smat is None:
        bad.append("Summary khong co bang Truc x NEW/UPD/DEL/IMPACT")
    else:
        for ax in S.CR_AXES:
            got = smat.get(ax)
            want = [m[ax][t] for t in S.CR_CHANGE_TYPE] + [row_tot[ax]]
            if got != want:
                bad.append("%s: %s != %s" % (ax, got, want))
        want = [col_tot[t] for t in S.CR_CHANGE_TYPE] + [grand]
        if stot != want:
            bad.append("dong Tong: %s != %s" % (stot, want))
    if shead != grand:
        bad.append("Tong MD dau trang=%s != %s" % (shead, C.fmt_md(grand)))
    g.check(12, "Summary: tong MD theo truc / loai / tong chung = tong cac dong", bad)

    q_ids = [C.txt(q.get("id")) for q in Q]
    q_set = set(q_ids)

    def has_q(imp):
        return any(x in q_set for x in S.split_ids(imp.get("question")))

    # 13. Conflict
    bad = []
    for imp in IMP:
        if imp.get("conflict") != "Yes":
            continue
        if not C.txt(imp.get("conflict_detail")) or C.txt(imp.get("conflict_detail")) in C.NONE_REFS:
            bad.append("%s conflict=Yes thieu conflict_detail" % tag(imp))
        if not (has_q(imp) or C.txt(imp.get("md_note"))):
            bad.append("%s conflict=Yes khong co CQ hoac md_note" % tag(imp))
    g.check(13, "Conflict=Yes: co chi tiet + (CQ hoac md_note)", bad)

    # 14. High risk
    bad = ["%s risk=High khong co CQ / md_note" % tag(imp) for imp in IMP
           if imp.get("risk") == "High" and not (has_q(imp) or C.txt(imp.get("md_note")))]
    g.check(14, "Risk=High: co cau hoi hoac giai phap (question / md_note)", bad)

    # 15. CQ
    bad = ["questions %r sai dang CQ-NNN" % x for x in q_ids if not re.match(S.CR_QUESTION_ID, x)]
    bad += ["%s trung" % d for d in sorted({x for x in q_ids if x and q_ids.count(x) > 1})]
    for q in Q:
        if not C.txt(q.get("question")):
            bad.append("%s thieu noi dung cau hoi" % q.get("id"))
    for imp in IMP:
        bad += ["%s question %s khong co trong questions" % (tag(imp), x)
                for x in S.split_ids(imp.get("question")) if x not in q_set]
    g.check(15, "CQ dung dang, duy nhat, moi question tro toi CQ co that", bad)

    # 16. Loai ref theo truc
    def axis_imps(ax, types):
        return [i for i in IMP if i.get("axis") == ax and i.get("change_type") in types]
    bad = []
    for imp in axis_imps("Screen", ("UPD", "DEL", "IMPACT")):
        refs = C.refs_of(imp.get("baseline_ref"))
        if not refs or any(not x.startswith("SC-") for x in refs):
            bad.append("%s ref=%s (Screen UPD/DEL/IMPACT phai la SC-)" % (tag(imp), imp.get("baseline_ref")))
    g.check("16a", "Screen UPD/DEL/IMPACT tham chieu SC-", bad)
    bad = ["%s ref=%s (chi table:/column:/—)" % (tag(i), x) for i in axis_imps("DB", S.CR_CHANGE_TYPE)
           for x in C.refs_of(i.get("baseline_ref")) if not x.lower().startswith(("table:", "column:"))]
    g.check("16b", "DB tham chieu table:/column:/—", bad)
    bad = ["%s ref=%s (chi EXT-/—)" % (tag(i), x) for i in axis_imps("ThirdParty", S.CR_CHANGE_TYPE)
           for x in C.refs_of(i.get("baseline_ref")) if not x.startswith("EXT-")]
    g.check("16c", "ThirdParty tham chieu EXT-/—", bad)
    bad = ["%s mockup khong bam DS:/DS-component: nao" % tag(i) for i in axis_imps("Mockup", ("NEW", "UPD"))
           if not any(x.lower().startswith(("ds:", "ds-component:")) for x in C.refs_of(i.get("baseline_ref")))]
    title = "Mockup NEW/UPD bam design system baseline (DS:/DS-component:)"
    if B["has_ds"]:
        g.check("16d", title, bad)
    else:
        g.check("16d", title + " — baseline khong co 04_DesignSystem", bad, level="WARN")

    # 17. Evidence
    bad = [tag(i) for i in IMP if not C.txt(i.get("evidence"))]
    g.check(17, "Evidence (trich CR / file baseline) cho moi impact", bad)

    # 18. DS mo ho
    g.check(18, "Ref DS khong mo ho giua cac site (DS:WEB-xx:<token>)", sorted(set(ds_warn)), level="WARN")

    # 19. Don gia da duyet chua
    st = C.txt(rates_meta.get("status")).upper()
    if st == "APPROVED":
        g.ok(19, "Bang don gia APPROVED", "v%s" % rates_meta.get("version"))
    else:
        g.warn(19, "Bang don gia APPROVED", "status=%s v%s — MD la uoc luong so bo, PM/Tech Lead phai duyet"
               % (st or "?", rates_meta.get("version")))

    # 20. CR-vs-CR
    mine = {}
    for imp in IMP:
        if imp.get("change_type") in ("UPD", "DEL"):
            for x in C.refs_of(imp.get("baseline_ref")):
                mine.setdefault(x.lower(), []).append(tag(imp))
    overlap = []
    for other in a.other_cr:
        try:
            o = C.load_json(other)
        except (OSError, ValueError) as e:
            overlap.append("%s: khong doc duoc (%s)" % (other, e))
            continue
        ocr = C.txt((o.get("meta") or {}).get("cr_id")) or other
        for imp in o.get("impacts") or []:
            if imp.get("change_type") not in ("UPD", "DEL"):
                continue
            for x in C.refs_of(imp.get("baseline_ref")):
                if x.lower() in mine:
                    overlap.append("%s: %s (%s) <-> %s %s" % (x, ",".join(mine[x.lower()]),
                                   meta.get("cr_id", "?"), ocr, imp.get("id")))
    if a.other_cr:
        g.check(20, "Xung dot CR-vs-CR (cung baseline_ref bi UPD/DEL)", overlap, level="WARN")
    else:
        g.ok(20, "Xung dot CR-vs-CR", "khong truyen --other-cr")

    # 21. Khong thuoc CR
    bad = []
    for n in cr.get("not_cr") or []:
        if C.txt(n.get("label")) not in S.CR_NOT_CR_LABEL:
            bad.append("%s label=%s" % (n.get("item"), n.get("label")))
        if not C.txt(n.get("reason")):
            bad.append("%s thieu reason" % n.get("item"))
    g.check(21, "not_cr: label BUG/QUESTION + ly do", bad)

    # Tom tat impact
    print("IMPACT %s (baseline %s):" % (meta.get("cr_id", "?"), base_name), file=sys.stderr)
    for ax in S.CR_AXES:
        cnt = {t: sum(1 for i in IMP if i.get("axis") == ax and i.get("change_type") == t)
               for t in S.CR_CHANGE_TYPE}
        print("  %-11s %s · %s MD" % (ax, " · ".join("%s %d" % kv for kv in cnt.items()),
                                       C.fmt_md(row_tot[ax])), file=sys.stderr)
    print("  Tong MD: %s (don gia %s) · Conflict=Yes: %d · Risk=High: %d · CQ: %d" % (
        C.fmt_md(grand), st or "?", sum(i.get("conflict") == "Yes" for i in IMP),
        sum(i.get("risk") == "High" for i in IMP), len(Q)), file=sys.stderr)

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
