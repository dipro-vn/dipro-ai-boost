#!/usr/bin/env python3
"""GATE V3 (+V4 nhat quan DB, +V6 khong o trong) — Overview docx (O6).

  python3 verify-overview.py <ver>/06_Overview/Overview_<sys>_ver<N>.docx \
      --inventory <_internal>/inventory.xlsx --index <_internal>/index.json [--out report.md]

Chan: thieu chuong · con placeholder template · bang output != index.json hoac tro toi file
khong co · so lieu chuong 3-6 lech inventory · bia DB · Phu luc A lech Open Questions ·
anh tran khung/thieu anh khong giai thich · o trong · nhac ID khong co trong inventory.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402
from docx_read import Docx  # noqa: E402
from gate_report import Gate  # noqa: E402

_spec = importlib.util.spec_from_file_location("ov", os.path.join(HERE, "render-overview-docx.py"))
OV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(OV)

PLACEHOLDER = re.compile(r"\[[A-Z][A-Z0-9_ /]{2,}\]")
ID_RX = {"SC-": ("02_Screen", "Screen ID"), "F-": ("01_Function", "Function ID"),
         "API-": ("07_API", "API ID"), "EXT-": ("09_Integration", "EXT ID")}


def find_table(tables, *keys):
    for t in tables:
        if t and all(k.lower() in " | ".join(t[0]).lower() for k in keys):
            return t
    return None


def as_rows(rows):
    return [[str(c) for c in r] for r in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    d = Docx(a.docx)
    data = S.load(a.inventory)
    meta = S.meta(data)
    idx = json.load(open(a.index, encoding="utf8"))
    ver_dir = os.path.dirname(os.path.dirname(os.path.abspath(a.index)))
    cnt = OV.summary_counts(data)
    db_mode = meta.get("db_mode", "")
    g = Gate("GATE V3 — Overview document (O6)")

    heads = [h.strip() for h in d.headings()]
    g.check(1, "Du chuong 0-7 + Phu luc A/B",
            [c for c in OV.CHAPTERS if not any(h.startswith(c.split(".")[0] + ".") and
                                              c.split(". ", 1)[1].lower() in h.lower()
                                              for h in heads)])

    g.check(2, "Khong con placeholder [PLACEHOLDER] cua template",
            sorted(set(PLACEHOLDER.findall(d.all_text))))

    # 3,4 — bang output khop index.json + file ton tai
    otab = find_table(d.tables, "Output", "File / Link", "Gate")
    outs = idx.get("outputs", [])
    if otab is None:
        g.fail(3, "Chuong 2 co bang output", "khong thay bang co cot Output/File / Link/Gate")
        g.fail(4, "File trong bang output ton tai", "khong co bang")
    else:
        doc_ids = [r[0].split(" — ")[0].strip() for r in otab[1:]]
        idx_ids = [e.get("id") for e in outs]
        g.check(3, "So dong bang output = so entry index.json (dung thu tu ID)",
                [] if doc_ids == idx_ids else ["docx=%s vs index=%s" % (doc_ids, idx_ids)])
        fcol = otab[0].index("File / Link")
        skipped = {e.get("id") + e.get("name", "") for e in outs if e.get("status") == "skip"}
        missing = []
        for r in otab[1:]:
            oid_name = r[0].replace(" — ", "", 1)
            if oid_name in skipped:
                continue
            for f in re.split(r"[\n;]+", r[fcol]):
                f = f.strip()
                if not f or f == OV.DASH or re.match(r"^https?://", f):
                    continue
                if not os.path.exists(os.path.join(ver_dir, f)):
                    missing.append("%s -> %s" % (r[0], f))
        g.check(4, "File trong bang output ton tai (tuong doi thu muc version)", missing)

    # 5 — chuong 3: man hinh theo site + chuc nang theo module
    bad = []
    t = find_table(d.tables, "Site", "Số màn hình")
    if t is None or as_rows(t[1:]) != as_rows(cnt["sites"]):
        bad.append("bang man hinh/site lech 02_Screen")
    t = find_table(d.tables, "Module", "Số chức năng")
    if t is None or as_rows(t[1:]) != as_rows(cnt["modules"]):
        bad.append("bang chuc nang/module lech 01_Function")
    g.check(5, "Chuong 3: so man hinh/chuc nang = inventory", bad)

    # 6 — chuong 4: API theo nhom
    t = find_table(d.tables, "Nhóm API")
    if data["07_API"]:
        g.check(6, "Chuong 4: so API theo nhom = 07_API",
                [] if t is not None and as_rows(t[1:]) == as_rows(cnt["api_groups"])
                else ["bang API/nhom lech hoac thieu"])
    else:
        g.check(6, "Chuong 4: khong co API thi khong co bang API", ["co bang API"] if t else [])

    # 7,8 — chuong 5 nhat quan DB (V4)
    ch5 = []
    grab = False
    for style, text in d.paragraphs:
        if style.startswith("Heading") and text.strip().startswith("5."):
            grab = True
            continue
        if grab and style.startswith("Heading") and re.match(r"^(\d+\.|Phụ lục)", text.strip()):
            break
        if grab:
            ch5.append(text)
    ch5 = "\n".join(ch5).lower()
    dbt = find_table(d.tables, "Chỉ số DB")
    if db_mode == "NONE":
        g.check(7, "db_mode=NONE -> chuong 5 ghi 'Database not available.'",
                [] if "database not available" in ch5 else ["thieu cau khai bao"])
        g.check(8, "db_mode=NONE -> khong co bang DB", ["co bang DB"] if dbt else [])
    else:
        g.check(7, "Co DB -> chuong 5 khong ghi 'Database not available'",
                ["chuong 5 ghi khong co DB"] if "database not available" in ch5 else [])
        g.check(8, "Chuong 5: so bang/cot/quan he = inventory",
                [] if dbt is not None and as_rows(dbt[1:]) == as_rows(cnt["db"])
                else ["bang Chi so DB lech hoac thieu"])

    # 9 — chuong 6: lien ket ben thu 3
    t = find_table(d.tables, "EXT ID", "Mục đích")
    n_doc = (len(t) - 1) if t else 0
    g.check(9, "Chuong 6: so lien ket = 09_Integration",
            [] if n_doc == len(data["09_Integration"])
            else ["docx=%d vs xlsx=%d" % (n_doc, len(data["09_Integration"]))])

    # 10 — Phu luc A
    t = find_table(d.tables, "Q ID", "Cần làm")
    opens = [r for r in data["06_OpenQuestions"] if r.get("Status") == "Open"]
    doc_q = [r[0] for r in t[1:]] if t else []
    g.check(10, "Phu luc A = cac Open Question con Open",
            [] if sorted(doc_q) == sorted(r.get("Q ID") for r in opens)
            else ["docx=%s vs xlsx=%s" % (doc_q, [r.get("Q ID") for r in opens])])

    # 11 — anh: du slot (anh hoac cau giai thich) + khong tran khung
    media, exts = d.images()
    slots = 3 if db_mode != "NONE" else 2
    no_img = sum(1 for _, tx in d.paragraphs if tx.startswith(OV.NO_IMG))
    g.check(11, "Moi vi tri hinh co anh hoac cau giai thich vi sao khong co",
            [] if len(exts) + no_img >= slots
            else ["%d anh + %d cau giai thich < %d vi tri" % (len(exts), no_img, slots)])
    limit = d.content_width_emu()
    g.check(12, "Anh khong tran khung trang",
            ["anh rong %.2f inch > khung %.2f inch" % (cx / 914400, limit / 914400)
             for cx, _ in exts if cx > limit + 9144])

    # 13 (V6) — khong o trong trong bang
    blanks = ["bang%d!r%dc%d" % (ti + 1, ri, ci)
              for ti, tb in enumerate(d.tables)
              for ri, row in enumerate(tb[1:], start=2)
              for ci, c in enumerate(row, start=1) if not c.strip()]
    g.check(13, "Khong o trong trong bang (thieu bang chung phai ghi UNKNOWN / —)", blanks)

    # 14 — ID nhac trong docx co that
    ghost = []
    text = d.all_text
    for pre, (sheet, col) in ID_RX.items():
        known = {r.get(col, "") for r in data[sheet]}
        found = set(re.findall(r"\b%s\d{3,}\b" % re.escape(pre), text))
        ghost += sorted(found - known)
    g.check(14, "Moi SC-/F-/API-/EXT- nhac trong docx co trong inventory", ghost)

    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
