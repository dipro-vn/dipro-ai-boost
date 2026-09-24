#!/usr/bin/env python3
"""GATE V3 (+V4 nhat quan DB, +V6 khong o trong) — tai lieu High Level.

  python3 verify-high-level.py <highlevel.docx> --inventory <inventory.xlsx> [--out report.md]

Chan: thieu chuong · con placeholder cua template · so dong docx != inventory ·
bia bang DB · anh tran khung · o trong lang le.
"""
import argparse
import re
import sys

import inv_schema as S
from docx_read import Docx
from gate_report import Gate

PLACEHOLDER = re.compile(r"\[[A-Z][A-Z0-9_ /]{2,}\]")
REQUIRED_HEADINGS = [
    ("0.", "Analysis Scope"),
    ("1.", "Product Overview"),
    ("2.", "Functional Overview"),
    ("3.", "Database Detail"),
    ("4.", "Overall System Flow"),
    ("Appendix A", None),
    ("Appendix B", None),
]


def find_table_with_header(tables, *keys):
    for t in tables:
        if not t:
            continue
        head = " ".join(t[0]).lower()
        if all(k.lower() in head for k in keys):
            return t
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    d = Docx(a.docx)
    data = S.load(a.inventory)
    meta = S.meta(data)
    g = Gate("GATE V3 — High Level document")

    heads = d.headings()
    joined = " | ".join(heads)

    # 1 — du chuong
    missing = []
    for prefix, name in REQUIRED_HEADINGS:
        hit = any(h.strip().startswith(prefix) for h in heads)
        if not hit and name:
            hit = name.lower() in joined.lower()
        if not hit:
            missing.append(prefix + (" " + name if name else ""))
    g.check(1, "Du 4 chuong + Appendix A/B", missing)

    # 2 — con placeholder cua template
    found = sorted(set(PLACEHOLDER.findall(d.all_text)))
    g.check(2, "Khong con placeholder [PLACEHOLDER] cua template", found)

    # 3 — bang chuc nang khop 01_Function
    ftab = find_table_with_header(d.tables, "function id")
    funcs = data["01_Function"]
    if ftab is None:
        g.fail(3, "Bang Functional Overview ton tai", "khong tim thay bang co cot 'Function ID'")
    else:
        n_doc, n_inv = len(ftab) - 1, len(funcs)
        g.check(3, "So dong bang chuc nang (docx) = 01_Function (xlsx)",
                [] if n_doc == n_inv else ["docx=%d vs xlsx=%d" % (n_doc, n_inv)])

    # 4 — moi Function ID trong docx co trong inventory va nguoc lai
    fids_inv = {r.get("Function ID", "") for r in funcs}
    fids_doc = set(re.findall(r"\bF-\d{3,}\b", d.all_text))
    g.check(4, "Function ID trong docx <-> inventory khop",
            sorted(fids_doc - fids_inv) + sorted(fids_inv - fids_doc))

    # 5,6 — nhat quan DB (GATE V4)
    db_mode = meta.get("g4_db", "")
    ch3 = ""
    grab = False
    for style, text in d.paragraphs:
        if style.startswith("Heading") and text.strip().startswith("3."):
            grab = True
            continue
        if grab and style.startswith("Heading1"):
            break
        if grab:
            ch3 += text + "\n"
    ttab = find_table_with_header(d.tables, "table", "primary key")
    if db_mode == "NONE":
        g.check(5, "Khong co DB -> chuong 3 phai khai bao 'Database not available'",
                [] if "database not available" in ch3.lower() else ["thieu cau khai bao"])
        g.check(6, "Khong co DB -> chuong 3 khong duoc co bang du lieu",
                ["bang DB ton tai trong docx"] if ttab else [])
    else:
        g.check(5, "Co DB -> chuong 3 phai co bang danh sach bang",
                [] if ttab else ["khong thay bang co cot Table/Primary Key"])
        n_doc = (len(ttab) - 1) if ttab else 0
        n_inv = len(data["03_DB_Tables"])
        g.check(6, "So dong bang DB (docx) = 03_DB_Tables (xlsx)",
                [] if n_doc == n_inv else ["docx=%d vs xlsx=%d" % (n_doc, n_inv)])

    # 7 — bang ten khong bi bia
    tset = {r.get("Table", "") for r in data["03_DB_Tables"]}
    if ttab and db_mode != "NONE":
        doc_tables = {r[0] for r in ttab[1:] if r and r[0]}
        g.check(7, "Bang DB nhac trong docx deu co trong 03_DB_Tables",
                sorted(doc_tables - tset))
    else:
        g.ok(7, "Bang DB nhac trong docx (bo qua — khong co DB)")

    # 8 — Appendix A khop Open Questions
    qtab = find_table_with_header(d.tables, "id", "required action")
    opens = [r for r in data["06_OpenQuestions"] if r.get("Status") == "Open"]
    if qtab is None:
        g.fail(8, "Appendix A co bang Open Questions", "khong tim thay bang")
    else:
        n_doc = len(qtab) - 1
        g.check(8, "So dong Appendix A = so Open Question con Open",
                [] if n_doc == len(opens) else ["docx=%d vs xlsx=%d" % (n_doc, len(opens))])

    # 9 — co anh flow
    media, exts = d.images()
    g.check(9, "Chuong 4 co anh flow nhung trong docx",
            [] if media else ["khong co file nao trong word/media/"])

    # 10 — anh khong tran khung trang
    limit = d.content_width_emu()
    over = ["anh rong %.2f inch > khung %.2f inch" % (cx / 914400, limit / 914400)
            for cx, _ in exts if cx > limit]
    g.check(10, "Anh khong tran khung trang", over)

    # 11 (GATE V6) — khong o trong lang le trong bang
    blanks = []
    for ti, t in enumerate(d.tables):
        for ri, row in enumerate(t[1:], start=2):
            for ci, cell in enumerate(row, start=1):
                if not cell.strip():
                    blanks.append("bang%d!r%dc%d" % (ti + 1, ri, ci))
    g.check(11, "Khong o trong trong bang (thieu bang chung phai ghi UNKNOWN)", blanks)

    # 12 — moi Screen ID nhac trong docx co that
    sids_inv = {r.get("Screen ID", "") for r in data["02_Screen"]}
    sids_doc = set(re.findall(r"\bSC-\d{3,}\b", d.all_text))
    g.check(12, "Screen ID trong docx deu co trong 02_Screen", sorted(sids_doc - sids_inv))

    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
