#!/usr/bin/env python3
"""GATE V3 (+V4 nhat quan DB, +V6 khong o trong) — Overview docx (O1).

  python3 verify-overview.py <ver>/01_Overview/Overview_<sys>_ver<N>.docx \
      --inventory <_internal>/inventory.xlsx --business <_internal>/business.json [--out report.md]

Chan: thieu / thua chuong (0-6, khong danh sach output, luong tong quan, phu luc) · con placeholder template ·
bang tong man hinh / API lech inventory · bia DB · chuong 2 (nghiep vu) co ma noi bo / ten bang / enum / ham,
muc khong co EV va khong co Q, EV / Q khong co trong inventory, luong < 2 buoc · o trong · nhac ID khong co trong
inventory · con chu cu · link ERD khong phai Figma va khong co ghi chu · (WARN) chuong 1 thieu hinh luong nghiep vu.
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
from gate_report import Gate, legacy_word_hits  # noqa: E402

_spec = importlib.util.spec_from_file_location("ov", os.path.join(HERE, "render-overview-docx.py"))
OV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(OV)

PLACEHOLDER = re.compile(r"\[[A-Z][A-Z0-9_ /]{2,}\]")
CODE_RX = re.compile(r"\b(?:SC|API|EV|F|EXT|WEB|REPO|IMP|CQ|FL|BUG|OBS|DS)-\d{2,}\b"
                     r"|\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b|\b\w+\(\)|#L\d+|\b[\w/.-]+\.(?:ts|tsx|js|py|php|rb|go|java|sql)\b")
REMOVED = ("danh sách output", "luồng tổng quan", "phụ lục")
ID_RX = {"SC-": ("02_Screen", "Screen ID"), "F-": ("01_Function", "Function ID"),
         "API-": ("07_API", "API ID"), "EXT-": ("09_Integration", "EXT ID")}


def find_table(tables, *keys):
    for t in tables:
        if t and all(k.lower() in " | ".join(t[0]).lower() for k in keys):
            return t
    return None


def as_rows(rows):
    return [[str(c) for c in r] for r in rows]


def chapter_text(d, num):
    out, grab = [], False
    for style, text in d.paragraphs:
        if style.startswith("Heading 1") or style == "Heading1":
            grab = text.strip().startswith(num)
            continue
        if grab:
            out.append(text)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--business", required=True)
    ap.add_argument("--index", default=None, help="(khong con dung — giu de lenh cu chay duoc)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    d = Docx(a.docx)
    data = S.load(a.inventory)
    meta = S.meta(data)
    biz = json.load(open(a.business, encoding="utf8"))
    cnt = OV.summary_counts(data)
    db_mode = meta.get("db_mode", "")
    g = Gate("GATE V3 — Overview document (O1)")

    heads = [h.strip() for h in d.headings()]
    miss = [c for c in OV.CHAPTERS + OV.BIZ_SECTIONS if c not in heads]
    extra = [h for h in heads if any(w in h.lower() for w in REMOVED)]
    g.check(1, "Du chuong 0-6 + 2.1-2.3, khong co danh sach output / luong tong quan / phu luc", miss + extra)

    g.check(2, "Khong con placeholder [PLACEHOLDER] cua template",
            sorted(set(PLACEHOLDER.findall(d.all_text))))

    t = find_table(d.tables, "Site", "Số màn hình")
    g.check(3, "Chuong 3: 1 bang tong man hinh theo site = inventory",
            [] if t is not None and as_rows(t[1:]) == as_rows(cnt["sites"]) else ["bang man hinh/site lech 02_Screen"])

    t = find_table(d.tables, *OV.API_HEAD[:3])
    if data["07_API"]:
        g.check(4, "Chuong 4: 1 bang tong API = 07_API",
                [] if t is not None and as_rows(t[1:]) == as_rows(cnt["api"]) else ["bang tong API lech hoac thieu"])
    else:
        g.check(4, "Chuong 4: khong co API thi khong co bang API", ["co bang API"] if t else [])

    ch5 = "\n".join(chapter_text(d, "5.")).lower()
    dbt = find_table(d.tables, "Chỉ số DB")
    if db_mode == "NONE":
        g.check(5, "db_mode=NONE -> chuong 5 ghi 'Database not available.' va khong co bang DB",
                ([] if "database not available" in ch5 else ["thieu cau khai bao"]) + (["co bang DB"] if dbt else []))
    else:
        g.check(5, "Chuong 5: so bang/cot/quan he = inventory",
                ([] if dbt is not None and as_rows(dbt[1:]) == as_rows(cnt["db"]) else ["bang Chi so DB lech hoac thieu"])
                + (["chuong 5 ghi khong co DB"] if "database not available" in ch5 else []))

    t = find_table(d.tables, "EXT ID", "Mục đích")
    n_doc = (len(t) - 1) if t else 0
    g.check(6, "Chuong 6: so lien ket = 09_Integration",
            [] if n_doc == len(data["09_Integration"]) else ["docx=%d vs xlsx=%d" % (n_doc, len(data["09_Integration"]))])

    # 7-10 — chuong 2 nghiep vu (business.json)
    body = [tx for tx in chapter_text(d, "2.") if not tx.startswith(OV.FIGMA_LINK)]
    tbl = {x.get("Table", "") for x in data["03_DB_Tables"] if len(x.get("Table", "")) >= 4}
    bad = sorted({m.group(0) for tx in body for m in CODE_RX.finditer(tx)})
    bad += sorted({n for n in tbl for tx in body if re.search(r"\b%s\b" % re.escape(n), tx)})
    g.check(7, "Chuong 2 viet cho khach: khong ma noi bo / ten bang / enum / ham / code-ref", bad)
    evids = {x.get("EV ID", "") for x in data["05_Evidence"]}
    qids = {x.get("Q ID", "") for x in data["06_OpenQuestions"]}
    items = [("flows", "title"), ("states", "object")]
    g.check(8, "Moi luong / trang thai co EV hoac Q (khong khang dinh khong can cu)",
            [it.get(k, "?") for key, k in items for it in biz.get(key, []) if not it.get("evidence") and not it.get("question")])
    ghost = [e for key, _ in items for it in biz.get(key, []) for e in it.get("evidence") or [] if e not in evids]
    ghost += [it["question"] for key, _ in items for it in biz.get(key, []) if it.get("question") and it["question"] not in qids]
    g.check(9, "EV / Q nhac toi co trong inventory", sorted(set(ghost)))
    g.check(10, "Co >= 1 luong, moi luong >= 2 buoc",
            (["khong co luong"] if not biz.get("flows") else []) +
            [f.get("title", "?") for f in biz.get("flows", []) if len(f.get("steps", [])) < 2])

    blanks = ["bang%d!r%dc%d" % (ti + 1, ri, ci)
              for ti, tb in enumerate(d.tables)
              for ri, row in enumerate(tb[1:], start=2)
              for ci, c in enumerate(row, start=1) if not c.strip()]
    g.check(11, "Khong o trong trong bang (thieu bang chung phai ghi 'Cần xác nhận — Q-xxx' / —)", blanks)

    ghost = []
    for pre, (sheet, col) in ID_RX.items():
        known = {r.get(col, "") for r in data[sheet]}
        ghost += sorted(set(re.findall(r"\b%s\d{3,}\b" % re.escape(pre), d.all_text)) - known)
    g.check(12, "Moi SC-/F-/API-/EXT- nhac trong docx co trong inventory", ghost)

    g.check(13, "Khong con chu cu '%s' (khong phan biet hoa thuong)" % S.LEGACY_WORD, legacy_word_hits(a.docx))

    links = [tx for _, tx in d.paragraphs if tx.startswith(OV.FIGMA_LINK)]
    nolink = [tx for _, tx in d.paragraphs if tx.startswith(OV.NO_FIGMA)]
    bad = ["link khong phai Figma: %s" % tx[:80] for tx in links if not OV.FIGMA_RX.search(tx)]
    if db_mode != "NONE" and not any("ERD" in tx for tx in links) and not nolink:
        bad.append("chuong 5 khong co link ERD Figma va khong co ghi chu")
    g.check(14, "Link Figma hop le; ERD co link hoac ghi chu", bad)

    imgs = d.images()[1]
    if imgs and any(tx.startswith(OV.FLOW_CAPTION) for _, tx in d.paragraphs):
        g.check(15, "Chuong 1 co hinh luong nghiep vu (Archify)", [])
    else:
        g.warn(15, "Chuong 1 co hinh luong nghiep vu (Archify)", "chua co hinh — ve bang Archify, chay lai --flow-image")

    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
