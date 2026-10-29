#!/usr/bin/env python3
"""Render O1 — Overview docx (tom tat khao sat) tu inventory + narrative + business + index.

  python3 render-overview-docx.py --inventory <_internal>/inventory.xlsx \
      --narrative <_internal>/narrative.json --business <_internal>/business.json \
      --index <_internal>/index.json [--figma-links <ver>/05_Figma/figma-links.md] \
      [--template templates/high-level-template.docx] --out <ver>/01_Overview/Overview_<sys>_ver<N>.docx

Chay build-version-index.py TRUOC (sinh index.json) va SAU (cap nhat gate O1).
Cau truc (feedback 28/10/2026): 0 pham vi · 1 tong quan · 2 nghiep vu chinh (business.json: he thong lam gi ·
luong nghiep vu · trang thai) · 3 man hinh (1 bang tong) · 4 API & Batch (1 bang tong) · 5 DB (+ link ERD Figma)
· 6 lien ket ben thu 3. Khong co danh sach output, luong tong quan, phu luc.
BANG/SO LIEU -> may sinh tu inventory; VAN XUOI -> agent viet:
narrative.json { "project_name", "customer", "product_overview": "3-5 cau",
                 "actors": [{"actor", "role", "main_usage"}], "system_composition": ["Frontend: ..."] }
business.json  — cau thuong cho khach (khong ma SC- API- EV-, ten bang, enum, ham):
{ "overview": "2-4 cau",
  "flows":  [{"title", "actor", "screens": ["「医師検索」"], "steps": ["..."], "figma": "<url>",
              "evidence": ["EV-0012"] | "question": "Q-003"}],
  "states": [{"object", "flow": ["Cho tra loi", "Da dong y"], "explain", "evidence": [...] | "question": "Q-004"}] }
Muc chi co question -> ghi "Cần xác nhận — Q-xxx".
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402

TITLE = "TỔNG QUAN KHẢO SÁT HỆ THỐNG"
HEADER = "LABO / MAINTAIN PROJECT — SYSTEM OVERVIEW"
FOOTER = "AI-generated analysis must be reviewed before use"
DASH = "—"
FIGMA_LINK = "Sơ đồ trên Figma:"
NO_FIGMA = "Chưa có sơ đồ trên Figma — xem ảnh ERD trong thư mục 04_DB."
FIGMA_RX = re.compile(r"https://(?:www\.)?figma\.com/(?:design|board|file)/[A-Za-z0-9]{6,}[^\s|)<>]*")
# dong figma-links.md (cot dau, chu thuong) -> so do
LINK_KEYS = (("flow", ("output 1",)), ("db", ("sơ đồ db", "erd")))
DEFAULT_TPL = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..",
                                           "templates", "high-level-template.docx"))
FK_EMPTY = ("", "—", "-", "No", "NO", "N/A", S.NEED_CONFIRM)
SCREEN_TYPES = S.SCREEN_TYPE
API_STATUS = S.API_STATUS

CHAPTERS = [
    "0. Phạm vi & nguồn khảo sát", "1. Tổng quan sản phẩm", "2. Nghiệp vụ chính",
    "3. Website & màn hình", "4. API & Batch", "5. Database", "6. Liên kết bên thứ 3",
]
BIZ_SECTIONS = ["2.1 Hệ thống này làm gì", "2.2 Luồng nghiệp vụ chính", "2.3 Trạng thái của đối tượng chính"]
API_HEAD = ["Tổng", "API", "Batch", "Webhook/Queue"] + API_STATUS


# ---------- so lieu dung chung (verify-overview.py import ham nay) ----------
def role_names(meta, sites):
    """Chi lay TEN vai tro — khong bao gio in user/password."""
    roles = []
    for tok in re.split(r"[;,]", meta.get("accounts", "") or ""):
        name = re.split(r"[:=/@\s(]", tok.strip())[0] if tok.strip() else ""
        if name and name != S.NEED_CONFIRM and name not in roles:
            roles.append(name)
    for r in sites:
        for tok in re.split(r"[;,]", r.get("Roles Observed", "")):
            t = tok.strip()
            if t and t not in (S.NEED_CONFIRM, DASH) and t not in roles:
                roles.append(t)
    return roles


def summary_counts(data):
    screens, apis = data["02_Screen"], data["07_API"]
    site_ids = [r.get("Site ID", "") for r in data["10_Site"]]
    site_ids += sorted({r.get("Site", "") or S.NEED_CONFIRM for r in screens} - set(site_ids))
    sites = []
    for sid in site_ids:
        rows = [r for r in screens if (r.get("Site", "") or S.NEED_CONFIRM) == sid]
        sites.append([sid, len(rows)] + [sum(1 for r in rows if r.get("Type") == t)
                                         for t in SCREEN_TYPES])
    k = [r.get("Kind") for r in apis]
    api = [[len(apis), k.count("API"), k.count("BATCH"), k.count("WEBHOOK") + k.count("QUEUE")] +
           [sum(1 for r in apis if r.get("Status") == st) for st in API_STATUS]]
    cols = data["04_DB_Columns"]
    if cols:
        rels = sum(1 for c in cols if str(c.get("FK", "")).strip() not in FK_EMPTY)
    else:
        rels = sum(len(S.split_ids(t.get("FK", ""))) for t in data["03_DB_Tables"])
    db = [["Số bảng", len(data["03_DB_Tables"])], ["Số cột", len(cols)],
          ["Số quan hệ (FK)", rels]]
    return {"sites": sites, "api": api, "db": db}


# ---------- docx helpers ----------
def cell_text(v):
    s = "" if v is None else str(v).strip()
    return s if s else DASH


def add_table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = h
        for p in c.paragraphs:
            for r in p.runs:
                r.bold = True
    for row in rows:
        cells = t.add_row().cells
        for i in range(len(headers)):
            cells[i].text = cell_text(row[i] if i < len(row) else None)
    doc.add_paragraph()
    return t


def bullet(doc, text):
    try:
        doc.add_paragraph(text, style="List Bullet")
    except KeyError:
        doc.add_paragraph("• " + text)


def figma_links(path):
    """figma-links.md -> {flow|api|db: url} (dong bang dau tien khop LINK_KEYS)."""
    out = {}
    if not path or not os.path.isfile(path):
        return out
    for line in open(path, encoding="utf8"):
        url = FIGMA_RX.search(line)
        first = line.strip().strip("|").split("|")[0].strip().lower() if line.strip().startswith("|") else ""
        for key, words in LINK_KEYS:
            if url and key not in out and any(w in first for w in words):
                out[key] = url.group(0)
    return out


def add_hyperlink(paragraph, url):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True))
    r, rpr, u, t = OxmlElement("w:r"), OxmlElement("w:rPr"), OxmlElement("w:u"), OxmlElement("w:t")
    u.set(qn("w:val"), "single")
    rpr.append(u)
    r.append(rpr)
    t.text = url
    r.append(t)
    h.append(r)
    paragraph._p.append(h)


def add_figma(doc, url, what):
    if url:
        add_hyperlink(doc.add_paragraph("%s %s — " % (FIGMA_LINK, what)), url)
    else:
        doc.add_paragraph("%s (%s)" % (NO_FIGMA, what))


def need(item):
    """'Cần xác nhận — Q-xxx' khi muc chi co cau hoi (D1)."""
    return "%s — %s" % (S.NEED_CONFIRM, item["question"]) if item.get("question") and not item.get("evidence") else ""


def new_document(template):
    from docx import Document
    if template and os.path.isfile(template):
        doc = Document(template)
        body = doc.element.body
        for el in list(body):
            if not el.tag.endswith("}sectPr"):
                body.remove(el)
    else:
        doc = Document()
    sec = doc.sections[0]
    for part, text in ((sec.header, HEADER), (sec.footer, FOOTER)):
        ps = part.paragraphs
        if ps:
            ps[0].text = text
            for p in ps[1:]:
                p.text = ""
        else:
            part.add_paragraph(text)
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--narrative", required=True)
    ap.add_argument("--business", required=True, help="business.json (chuong 2: nghiep vu chinh)")
    ap.add_argument("--index", required=True)
    ap.add_argument("--figma-links", default=None, help="<ver>/05_Figma/figma-links.md (link Output 1 + ERD)")
    ap.add_argument("--template", default=DEFAULT_TPL)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    try:
        import docx  # noqa: F401
    except ImportError:
        print("Thieu python-docx. Chay: pip install python-docx", file=sys.stderr)
        return 2

    data = S.load(a.inventory)
    meta = S.meta(data)
    nar = json.load(open(a.narrative, encoding="utf8"))
    biz = json.load(open(a.business, encoding="utf8"))
    idx = json.load(open(a.index, encoding="utf8"))
    cnt = summary_counts(data)
    links = figma_links(a.figma_links)
    db_mode = meta.get("db_mode", S.NEED_CONFIRM)

    doc = new_document(a.template)
    doc.add_paragraph("LABO / MAINTAIN PROJECT")
    doc.add_heading(TITLE, level=0)
    add_table(doc, ["Mục", "Giá trị"], [
        ["Dự án", nar.get("project_name") or meta.get("system_name")],
        ["Khách hàng", nar.get("customer") or meta.get("customer")],
        ["Phiên bản", "%s (%s)" % (idx.get("version", DASH), idx.get("version_folder", DASH))],
        ["Ngày", idx.get("date") or meta.get("generated_date")],
        ["Loại chạy", idx.get("version_type") or meta.get("version_type") or "BASELINE"],
    ])

    # 0
    doc.add_heading(CHAPTERS[0], level=1)
    add_table(doc, ["Site ID", "Tên site", "URL", "Môi trường", "Crawl Mode"],
              [[r.get("Site ID"), r.get("Site Name"), r.get("URL"), r.get("Env"),
                r.get("Crawl Mode")] for r in data["10_Site"]] or [[DASH, "Không có website"]])
    add_table(doc, ["Repo ID", "Loại", "Stack", "Cho site"],
              [[r.get("Repo ID"), r.get("Kind"), r.get("Stack"), r.get("For Site")]
               for r in data["11_Repo"]] or [[DASH, "Không có source code"]])
    figma = meta.get("figma_input_url", "")
    add_table(doc, ["Hạng mục", "Giá trị"], [
        ["Database", db_mode],
        ["Figma đầu vào", "Có" if figma and figma not in (S.NEED_CONFIRM, DASH, "NO") else "Không"],
        ["Crawl mode", meta.get("crawl_mode")],
        ["Tài khoản (vai trò)", ", ".join(role_names(meta, data["10_Site"])) or S.NEED_CONFIRM],
    ])

    # 1
    doc.add_heading(CHAPTERS[1], level=1)
    doc.add_paragraph(nar.get("product_overview") or S.NEED_CONFIRM)
    add_table(doc, ["Actor", "Vai trò", "Sử dụng chính"],
              [[x.get("actor"), x.get("role"), x.get("main_usage")] for x in nar.get("actors", [])]
              or [[S.NEED_CONFIRM, S.NEED_CONFIRM, S.NEED_CONFIRM]])
    for line in nar.get("system_composition") or [S.NEED_CONFIRM]:
        bullet(doc, line)

    # 2 — nghiep vu chinh (business.json)
    doc.add_heading(CHAPTERS[2], level=1)
    doc.add_heading(BIZ_SECTIONS[0], level=2)
    doc.add_paragraph(biz.get("overview") or S.NEED_CONFIRM)
    doc.add_heading(BIZ_SECTIONS[1], level=2)
    if links.get("flow"):
        add_figma(doc, links["flow"], "toàn bộ luồng — Figma Output 1")
    for f in biz.get("flows", []):
        doc.add_heading(f["title"], level=3)
        if f.get("actor"):
            doc.add_paragraph("Người thực hiện: %s" % f["actor"])
        for i, st in enumerate(f.get("steps", []), 1):
            doc.add_paragraph("%d. %s" % (i, st))
        if f.get("screens"):
            doc.add_paragraph("Màn hình liên quan: %s" % ", ".join(f["screens"]))
        if f.get("figma"):
            add_figma(doc, f["figma"], f["title"])
        if need(f):
            doc.add_paragraph(need(f))
    doc.add_heading(BIZ_SECTIONS[2], level=2)
    for st in biz.get("states", []):
        doc.add_paragraph("%s: %s." % (st["object"], " → ".join(st.get("flow", []))))
        if st.get("explain"):
            doc.add_paragraph(st["explain"])
        if need(st):
            doc.add_paragraph(need(st))
    if not biz.get("states"):
        doc.add_paragraph("Không có đối tượng có nhiều trạng thái trong phạm vi khảo sát.")

    # 3
    doc.add_heading(CHAPTERS[3], level=1)
    doc.add_paragraph("Số màn hình theo site và loại. Danh sách chi tiết: O2 Basic Design.")
    add_table(doc, ["Site", "Số màn hình"] + SCREEN_TYPES, cnt["sites"])

    # 4
    doc.add_heading(CHAPTERS[4], level=1)
    apis = data["07_API"]
    if apis:
        doc.add_paragraph("Số API / batch theo loại và trạng thái bằng chứng. Danh sách chi tiết: O3 API doc.")
        add_table(doc, API_HEAD, cnt["api"])
    else:
        doc.add_paragraph("Không phát hiện API/batch trong source code đã khảo sát.")

    # 5
    doc.add_heading(CHAPTERS[5], level=1)
    if db_mode == "NONE":
        doc.add_paragraph("Database not available.")
        doc.add_paragraph("Không được cấp dump/kết nối DB và không có migration/ORM để suy ra "
                          "(db_mode=NONE).")
    else:
        doc.add_paragraph("Nguồn: %s. Danh sách bảng/cột đầy đủ: O4 DB doc." % db_mode)
        add_table(doc, ["Chỉ số DB", "Giá trị"], cnt["db"])
        add_figma(doc, links.get("db"), "sơ đồ DB (ERD)")

    # 6
    doc.add_heading(CHAPTERS[6], level=1)
    exts = data["09_Integration"]
    if exts:
        add_table(doc, ["EXT ID", "Tên", "Loại", "Mục đích", "Chiều", "Trạng thái"],
                  [[r.get("EXT ID"), r.get("Name"), r.get("Kind"), r.get("Purpose"),
                    r.get("Direction"), r.get("Status")] for r in exts])
    else:
        doc.add_paragraph("Không phát hiện liên kết bên thứ 3.")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    doc.save(a.out)
    print("Da render %s — %d site · %d man hinh · %d API · %d EXT · %d luong nghiep vu"
          % (a.out, len(data["10_Site"]), len(data["02_Screen"]), len(apis), len(exts), len(biz.get("flows", []))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
