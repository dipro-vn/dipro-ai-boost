#!/usr/bin/env python3
"""GATE V-CR — CR Impact workbook (Luong 2).

  python3 verify-cr-impact.py <ver>/CR-001_Impact.xlsx --baseline <outputs>/verK_... \
      [--other-cr <CR-xxx_Impact.xlsx> ...] [--out <ver>/_internal/gates/v-cr.md]

Baseline ids lay tu <baseline>/_internal/inventory.xlsx + 04_DesignSystem/project/ (tokens.json, components/).
Baseline Ref: SC-001 · F-001 · API-001 · EXT-001 · WEB-01 · table:orders · column:orders.status ·
DS:<ten token|type style> (vd DS:primary) · DS-component:<Comp> (thu muc components/<Comp>/ hoac export
trong index.d.ts) · — ; nhieu ref cach nhau bang ';'. Baseline cu (khong co project/tokens.json): DS: theo
duong dan cham trong 04_DesignSystem/tokens.json, DS-component: theo components.md.
Chan: truc bo trong · sua/xoa thu khong co trong baseline · cot moi trung ten ma khong khai Conflict ·
High risk khong co giai trinh · CQ treo · mockup khong bam design system cu.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402
from gate_report import Gate  # noqa: E402

REQUIRED = ["Impact ID", "Change Type", "Baseline Ref", "Item", "Change Description",
            "Impact On Current", "Conflict", "Risk"]
NONE_REFS = ("—", "-", "–", "")
ID_PREFIX = {"SC": "02_Screen", "F": "01_Function", "API": "07_API",
             "EXT": "09_Integration", "WEB": "10_Site"}
DS_LACK_RE = re.compile(r"design[ _-]?system|\bDS\b", re.I)


def refs_of(value):
    return [r.strip() for r in str(value or "").split(";")
            if r.strip() and r.strip() not in NONE_REFS]


def load_baseline(bdir):
    inv = os.path.join(bdir, "_internal", "inventory.xlsx")
    if not os.path.isfile(inv):
        raise SystemExit("Khong thay baseline inventory: %s" % inv)
    data = S.load(inv)
    ids = {}
    for pre, sheet in ID_PREFIX.items():
        col = S.ID_PATTERNS[sheet][0]
        ids[pre] = {r.get(col, "") for r in data.get(sheet, []) if r.get(col)}
    tables = {r.get("Table", "").lower() for r in data.get("03_DB_Tables", []) if r.get("Table")}
    cols = set()
    for r in data.get("04_DB_Columns", []):
        t, c = r.get("Table", "").lower(), r.get("Column", "").lower()
        if t and c:
            tables.add(t)
            cols.add("%s.%s" % (t, c))
    ds_dir = os.path.join(bdir, "04_DesignSystem")
    has_ds = os.path.isdir(ds_dir)
    tokens, comps = set(), set()
    pj = os.path.join(ds_dir, "project", "tokens.json")
    tj = os.path.join(ds_dir, "tokens.json")
    if os.path.isfile(pj):
        try:
            tokens = artifact_tokens(json.load(open(pj, encoding="utf8")))
        except ValueError as e:
            print("CANH BAO: project/tokens.json loi JSON: %s" % e, file=sys.stderr)
        comps = artifact_components(os.path.join(ds_dir, "project", "components"))
    elif os.path.isfile(tj):
        try:
            walk_tokens(json.load(open(tj, encoding="utf8")), "", tokens)
        except ValueError as e:
            print("CANH BAO: tokens.json loi JSON: %s" % e, file=sys.stderr)
    cm = os.path.join(ds_dir, "components.md")
    if not os.path.isfile(pj) and os.path.isfile(cm):
        comps = parse_components(open(cm, encoding="utf8").read())
    return {"ids": ids, "tables": tables, "cols": cols, "has_ds": has_ds,
            "tokens": tokens, "comps": comps}


def artifact_tokens(tk):
    """Ten token moi family ({tokens:[...]}) + ten type style (format artifact Design System)."""
    out = set()
    if not isinstance(tk, dict):
        return out
    for k, v in tk.items():
        if isinstance(v, dict) and isinstance(v.get("tokens"), list):
            out |= {str(t.get("name", "")).lower() for t in v["tokens"] if isinstance(t, dict) and t.get("name")}
    for gr in ((tk.get("type") or {}).get("groups") or []) if isinstance(tk.get("type"), dict) else []:
        for st in (gr.get("styles") or []) if isinstance(gr, dict) else []:
            if isinstance(st, dict) and st.get("name"):
                out.add(str(st["name"]).lower())
    return out


def artifact_components(cdir):
    """Thu muc components/<Comp>/ (tru Cover/lib/src) + ten export trong index.d.ts."""
    out = set()
    if os.path.isdir(cdir):
        out |= {d.lower() for d in os.listdir(cdir)
                if os.path.isdir(os.path.join(cdir, d)) and d not in ("Cover", "lib", "src")}
        dts = os.path.join(cdir, "index.d.ts")
        if os.path.isfile(dts):
            out |= {m.lower() for m in re.findall(
                r"export\s+(?:declare\s+)?(?:function|const|class)\s+([A-Za-z_$][\w$]*)",
                open(dts, encoding="utf8").read())}
    return out


def walk_tokens(node, prefix, out):
    if isinstance(node, dict):
        for k, v in node.items():
            p = "%s.%s" % (prefix, k) if prefix else str(k)
            out.add(p.lower())
            walk_tokens(v, p, out)


def parse_components(text):
    """Best effort: cot dau cua bang markdown + heading ## / ###."""
    out = set()
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^#{2,4}\s+(.+)$", s)
        if m:
            out.add(clean_name(m.group(1)))
        elif s.startswith("|") and not re.match(r"^\|[\s:|-]+\|?$", s):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if cells and cells[0]:
                out.add(clean_name(cells[0]))
    out.discard("")
    return out


def clean_name(s):
    return re.sub(r"[`*_]", "", s).strip().lower()


def resolve(ref, B):
    """-> (ok, ly do neu khong ok)."""
    low = ref.lower()
    if low.startswith("table:"):
        t = low[6:].strip()
        return (t in B["tables"], "bang khong co trong baseline")
    if low.startswith("column:"):
        c = low[7:].strip()
        return (c in B["cols"], "cot khong co trong baseline")
    if low.startswith("ds-component:"):
        return (clean_name(ref[13:]) in B["comps"], "component khong co trong design system baseline")
    if low.startswith("ds:"):
        return (low[3:].strip() in B["tokens"], "token khong co trong tokens.json baseline")
    m = re.match(r"^(SC|F|API|EXT|WEB)-\d+$", ref)
    if m:
        return (ref in B["ids"][m.group(1)], "id khong co trong baseline")
    return (False, "cu phap ref khong hop le")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("impact")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--other-cr", action="append", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    wb = S.load(a.impact, S.CR_SHEETS)
    B = load_baseline(a.baseline)
    g = Gate("GATE V-CR — %s" % os.path.basename(a.impact))
    summ = {r.get("Key", ""): r.get("Value", "") for r in wb["00_Summary"]}
    base_name = os.path.basename(os.path.normpath(a.baseline))

    # 1. Summary
    bad = ["%s rong/thieu" % k for k in S.CR_META_KEYS
           if not summ.get(k) or summ.get(k) == S.UNKNOWN]
    if summ.get("source_type") and summ["source_type"] not in S.CR_SOURCE_TYPE:
        bad.append("source_type=%s" % summ["source_type"])
    if summ.get("baseline_version") and summ["baseline_version"] != base_name:
        bad.append("baseline_version=%s != %s" % (summ["baseline_version"], base_name))
    g.check(1, "00_Summary du key, source_type hop le, baseline_version khop", bad)

    rows = []
    for sheet in S.CR_AXES:
        for r in wb[sheet]:
            r["__sheet__"] = sheet
            rows.append(r)

    def loc(r):
        return "%s!%s" % (r["__sheet__"], r["__row__"])

    # 2. Impact ID
    bad, seen = [], {}
    for r in rows:
        iid = r.get("Impact ID", "")
        if iid and not re.match(S.CR_IMPACT_ID, iid):
            bad.append("%s %s sai dang" % (loc(r), iid))
        if iid and iid in seen:
            bad.append("%s %s trung voi %s" % (loc(r), iid, seen[iid]))
        seen.setdefault(iid, loc(r))
    g.check(2, "Impact ID dung dang IMP-NNN, duy nhat tren 6 truc", bad)

    # 3. Moi truc tra loi tuong minh
    bad = []
    for sheet, axis in S.CR_AXES.items():
        rs = wb[sheet]
        nones = [r for r in rs if r.get("Change Type") == "NONE"]
        if not rs:
            bad.append("%s (%s) bo trong — them 1 dong NONE giai thich" % (sheet, axis))
        elif nones and len(rs) > 1:
            bad.append("%s co NONE lan voi dong khac" % sheet)
        elif nones and len(nones[0].get("Change Description", "")) < 15:
            bad.append("%s NONE thieu giai thich (>=15 ky tu)" % sheet)
    g.check(3, "Ca 6 truc co >=1 dong (khong anh huong = 1 dong NONE co ly do)", bad)

    # 4. Enum
    bad = []
    for r in rows:
        for col, enum in (("Change Type", S.CR_CHANGE_TYPE), ("Conflict", S.CR_CONFLICT),
                          ("Risk", S.CR_RISK)):
            v = r.get(col, "")
            if v and v not in enum:
                bad.append("%s %s=%s" % (loc(r), col, v))
    g.check(4, "Enum Change Type / Conflict / Risk", bad)

    # 5. UPD/DEL ref ton tai
    bad = []
    for r in rows:
        if r.get("Change Type") not in ("UPD", "DEL"):
            continue
        refs = refs_of(r.get("Baseline Ref"))
        if not refs:
            bad.append("%s %s khong co Baseline Ref" % (loc(r), r.get("Change Type")))
        for ref in refs:
            ok, why = resolve(ref, B)
            if not ok:
                bad.append("%s %s: %s" % (loc(r), ref, why))
    g.check(5, "UPD/DEL: moi Baseline Ref ton tai trong baseline", bad)

    # 6. NEW
    bad = []
    for r in rows:
        if r.get("Change Type") != "NEW":
            continue
        for ref in refs_of(r.get("Baseline Ref")):
            low = ref.lower()
            if low.startswith("column:"):
                tc = low[7:].strip()
                t = tc.split(".")[0]
                if "." not in tc or t not in B["tables"]:
                    bad.append("%s %s: bang cha khong co trong baseline" % (loc(r), ref))
                elif tc in B["cols"] and r.get("Conflict") != "Yes":
                    bad.append("%s %s: cot da ton tai — trung ten, phai Conflict=Yes"
                               % (loc(r), ref))
                continue
            ok, why = resolve(ref, B)
            if not ok:
                bad.append("%s %s: %s (NEW chi gan vao cha da ton tai)" % (loc(r), ref, why))
    g.check(6, "NEW: ref la — hoac cha ton tai; cot moi khong trung cot cu (tru Conflict=Yes)", bad)

    cq_ids = [q.get("Q ID", "") for q in wb["07_Questions"]]
    cq_set = set(cq_ids)

    # 7. Conflict
    bad = []
    for r in rows:
        if r.get("Conflict") != "Yes":
            continue
        if not r.get("Conflict Detail"):
            bad.append("%s Conflict=Yes thieu Conflict Detail" % loc(r))
        qs_ok = any(q in cq_set for q in S.split_ids(r.get("Open Q")))
        if not (qs_ok or r.get("Note")):
            bad.append("%s Conflict=Yes khong co CQ hop le hoac Note" % loc(r))
    g.check(7, "Conflict=Yes: co Conflict Detail + (CQ hoac Note)", bad)

    # 8. High risk
    bad = ["%s Risk=High khong co Open Q / Note" % loc(r) for r in rows
           if r.get("Risk") == "High" and not (r.get("Open Q") or r.get("Note"))]
    g.check(8, "Risk=High: co cau hoi hoac giai phap (Open Q / Note)", bad)

    # 9. CQ
    bad = []
    for q in wb["07_Questions"]:
        qid = q.get("Q ID", "")
        if not re.match(S.CR_QUESTION_ID, qid):
            bad.append("07_Questions!%s Q ID=%r sai dang" % (q["__row__"], qid))
    dup = sorted({x for x in cq_ids if x and cq_ids.count(x) > 1})
    bad += ["%s trung" % d for d in dup]
    for r in rows:
        for q in S.split_ids(r.get("Open Q")):
            if q not in cq_set:
                bad.append("%s Open Q %s khong co trong 07_Questions" % (loc(r), q))
    g.check(9, "CQ dung dang, duy nhat, moi Open Q tro toi CQ co that", bad)

    # 10. Loai ref theo truc
    def axis_rows(sheet, types=("NEW", "UPD", "DEL")):
        return [r for r in wb[sheet] if r.get("Change Type") in types]

    bad = []
    for r in axis_rows("04_Screen", ("UPD", "DEL")):
        refs = refs_of(r.get("Baseline Ref"))
        if not refs or any(not x.startswith("SC-") for x in refs):
            bad.append("%s ref=%s (UPD/DEL man hinh phai la SC-)" % (loc(r), r.get("Baseline Ref")))
    g.check("10a", "04_Screen UPD/DEL tham chieu SC-", bad)

    bad = []
    for r in axis_rows("02_DB"):
        for x in refs_of(r.get("Baseline Ref")):
            if not x.lower().startswith(("table:", "column:")):
                bad.append("%s ref=%s (chi table:/column:/—)" % (loc(r), x))
    g.check("10b", "02_DB tham chieu table:/column:/—", bad)

    bad = []
    for r in axis_rows("05_ThirdParty"):
        for x in refs_of(r.get("Baseline Ref")):
            if not x.startswith("EXT-"):
                bad.append("%s ref=%s (chi EXT-/—)" % (loc(r), x))
    g.check("10c", "05_ThirdParty tham chieu EXT-/—", bad)

    fail, warn = [], []
    for r in axis_rows("06_Mockup", ("NEW", "UPD")):
        refs = refs_of(r.get("Baseline Ref"))
        if any(x.lower().startswith(("ds:", "ds-component:")) for x in refs):
            continue
        if DS_LACK_RE.search(r.get("Note", "")):
            warn.append("%s khong co DS ref, Note: DS chua co" % loc(r))
        else:
            fail.append("%s mockup khong bam DS:/DS-component: nao" % loc(r))
    title = "06_Mockup NEW/UPD bam design system cu (DS:/DS-component:)"
    if not B["has_ds"]:
        g.check("10d", title + " — baseline khong co 04_DesignSystem", fail + warn, level="WARN")
    elif fail:
        g.check("10d", title, fail + warn)
    else:
        g.check("10d", title, warn, level="WARN")

    # 11. Evidence
    bad = ["%s %s" % (loc(r), r.get("Impact ID")) for r in rows
           if r.get("Change Type") not in ("NONE", "") and not r.get("Evidence")]
    g.check(11, "Evidence (trich CR / file baseline) cho moi dong khac NONE", bad)

    # 12. CR-vs-CR
    mine = {}
    for r in rows:
        if r.get("Change Type") in ("UPD", "DEL"):
            for x in refs_of(r.get("Baseline Ref")):
                mine.setdefault(x.lower(), []).append(r.get("Impact ID"))
    overlap = []
    for other in a.other_cr:
        try:
            ow = S.load(other, S.CR_SHEETS)
        except SystemExit as e:
            overlap.append("%s: khong doc duoc (%s)" % (os.path.basename(other), e))
            continue
        ocr = {r.get("Key"): r.get("Value") for r in ow["00_Summary"]}.get("cr_id") \
            or os.path.basename(other)
        for sheet in S.CR_AXES:
            for r in ow[sheet]:
                if r.get("Change Type") not in ("UPD", "DEL"):
                    continue
                for x in refs_of(r.get("Baseline Ref")):
                    if x.lower() in mine:
                        overlap.append("%s: %s (%s) <-> %s %s" % (
                            x, ",".join(mine[x.lower()]), summ.get("cr_id", "?"),
                            ocr, r.get("Impact ID")))
    if a.other_cr:
        g.check(12, "Xung dot CR-vs-CR (cung Baseline Ref bi UPD/DEL)", overlap, level="WARN")
    else:
        g.ok(12, "Xung dot CR-vs-CR", "khong truyen --other-cr")

    # 13. Cot bat buoc
    bad = []
    for r in rows:
        miss = [c for c in REQUIRED if not r.get(c)]
        if miss:
            bad.append("%s thieu %s" % (loc(r), ",".join(miss)))
    g.check(13, "Khong o trong o cot bat buoc", bad)

    # Tom tat impact
    print("IMPACT %s (baseline %s):" % (summ.get("cr_id", "?"), base_name), file=sys.stderr)
    for sheet, axis in S.CR_AXES.items():
        cnt = {t: 0 for t in S.CR_CHANGE_TYPE}
        for r in wb[sheet]:
            if r.get("Change Type") in cnt:
                cnt[r["Change Type"]] += 1
        print("  %-11s NEW %d · UPD %d · DEL %d · NONE %d" % (
            axis, cnt["NEW"], cnt["UPD"], cnt["DEL"], cnt["NONE"]), file=sys.stderr)
    print("  Conflict=Yes: %d · Risk=High: %d · CQ: %d" % (
        sum(r.get("Conflict") == "Yes" for r in rows),
        sum(r.get("Risk") == "High" for r in rows), len(cq_ids)), file=sys.stderr)

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
