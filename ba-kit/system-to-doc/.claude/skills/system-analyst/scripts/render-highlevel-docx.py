#!/usr/bin/env python3
"""Render Output 1 — High Level docx tu inventory.xlsx + narrative.json + flow.png.

  python3 render-highlevel-docx.py --inventory inv.xlsx --narrative narrative.json \
      --flow flow.json --png flow.png --out 01_HighLevel_<system>_v<N>.docx

Phan chia trach nhiem:
  - BANG  -> sinh tu inventory.xlsx (may lam, khong sai lech duoc)
  - VAN XUOI -> agent viet trong narrative.json (may khong bia ho)

narrative.json toi thieu:
{
  "project_name": "...", "customer": "...", "target_system": "WEB",
  "generated_date": "2026-09-23", "version": "v1",
  "product_overview": "doan van 5-8 cau",
  "system_composition": ["Frontend: ...", "Backend: ...", "Database: ..."],
  "actors": [{"actor":"User","role":"...","main_usage":"..."}],
  "scope_sources": [{"input":"Running Website","availability":"Yes",
                     "method":"Playwright","notes":"https://..."}],
  "business_rules": [{"id":"BR-001","rule":"...","applies_to":"F-001",
                      "evidence":"EV-0003","status":"Confirmed"}],
  "db_summary": "DBMS: MySQL ...",
  "relationships": ["users 1 — N orders"]
}
"""
import argparse
import json
import sys

import inv_schema as S

TITLE = "HIGH LEVEL SYSTEM ANALYSIS"
HEADER = "LABO / MAINTAIN PROJECT — HIGH LEVEL SYSTEM ANALYSIS"
FOOTER = "AI-generated analysis must be reviewed before use"
DASH = "—"


def add_table(doc, headers, rows, style="Table Grid"):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = style
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = str(h)
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row[:len(headers)]):
            cells[i].text = "" if v is None else (str(v) if str(v).strip() else DASH)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--narrative", required=True)
    ap.add_argument("--flow", default=None)
    ap.add_argument("--png", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    try:
        from docx import Document
        from docx.shared import Inches, Pt
    except ImportError:
        print("Thieu python-docx. Chay: pip install python-docx", file=sys.stderr)
        return 2

    data = S.load(a.inventory)
    meta = S.meta(data)
    nar = json.load(open(a.narrative, encoding="utf8"))
    flow = json.load(open(a.flow, encoding="utf8")) if a.flow else {}

    doc = Document()
    sec = doc.sections[0]
    sec.header.paragraphs[0].text = HEADER
    sec.footer.paragraphs[0].text = FOOTER

    doc.add_paragraph("LABO / MAINTAIN PROJECT")
    doc.add_heading(TITLE, level=0)
    doc.add_paragraph("Output #1 — Existing System Understanding")

    add_table(doc, ["Item", "Value"], [
        ["Project Name", nar.get("project_name", S.UNKNOWN)],
        ["Customer", nar.get("customer", S.UNKNOWN)],
        ["Target System", nar.get("target_system", S.UNKNOWN)],
        ["Analysis Inputs", meta.get("g1_websites", DASH)],
        ["Generated Date", nar.get("generated_date", meta.get("generated_date", DASH))],
        ["Version", nar.get("version", meta.get("doc_version", "v1"))],
    ])

    # --- 0 ---
    doc.add_heading("0. Analysis Scope & Source", level=1)
    add_table(doc, ["Input", "Availability", "Analysis Method", "Notes"],
              [[s.get("input"), s.get("availability"), s.get("method"), s.get("notes")]
               for s in nar.get("scope_sources", [])] or
              [["Running Website", meta.get("g1_websites", S.UNKNOWN),
                meta.get("g2_crawl_mode", S.UNKNOWN), DASH],
               ["Source Code", meta.get("g5_source", S.UNKNOWN), "Static scan", DASH],
               ["Database", meta.get("g4_db", S.UNKNOWN), "Schema read", DASH]])
    doc.add_paragraph(
        "Rule: Clearly distinguish Confirmed facts, AI Inference, and Unknown items. "
        "Do not present inferred behavior as confirmed.")

    # --- 1 ---
    doc.add_heading("1. Product Overview", level=1)
    doc.add_paragraph(nar.get("product_overview", S.UNKNOWN))
    doc.add_heading("1.1 Target Users / Actors", level=2)
    add_table(doc, ["Actor", "Role", "Main Usage"],
              [[x.get("actor"), x.get("role"), x.get("main_usage")]
               for x in nar.get("actors", [])] or [[S.UNKNOWN, S.UNKNOWN, S.UNKNOWN]])
    doc.add_heading("1.2 System Composition", level=2)
    for line in nar.get("system_composition", [S.UNKNOWN]):
        doc.add_paragraph(line, style="List Bullet")

    # --- 2 ---
    doc.add_heading("2. Functional Overview", level=1)
    doc.add_paragraph(
        "Danh sach chuc nang quan sat duoc tu UI, route, module nguon, API va tai lieu. "
        "Cot Evidence tro ve Evidence Ledger; cot Status phan biet Confirmed / To verify / "
        "Inferred / CONFLICT.")
    add_table(doc,
              ["Function ID", "Module", "Function", "Primary Actor", "Description",
               "Evidence", "Status"],
              [[f.get("Function ID"), f.get("Module"), f.get("Function"),
                f.get("Primary Actor"), f.get("Description"),
                f.get("Source"), f.get("Status")]
               for f in data["01_Function"]])

    doc.add_heading("2.1 Key Business Rules", level=2)
    brs = nar.get("business_rules", [])
    if brs:
        add_table(doc, ["BR ID", "Rule", "Applies to", "Evidence", "Status"],
                  [[b.get("id"), b.get("rule"), b.get("applies_to"),
                    b.get("evidence"), b.get("status")] for b in brs])
    else:
        doc.add_paragraph("%s — chua xac lap duoc business rule nao co bang chung." % S.UNKNOWN)

    doc.add_heading("2.2 Screen Inventory", level=2)
    add_table(doc, ["Screen ID", "URL / Route", "Screen Name", "Type", "Actor", "Status"],
              [[s.get("Screen ID"), s.get("URL / Route"), s.get("Screen Name"),
                s.get("Type"), s.get("Actor"), s.get("Status")]
               for s in data["02_Screen"]])

    # --- 3 ---
    doc.add_heading("3. Database Detail", level=1)
    if meta.get("g4_db") == "NONE":
        doc.add_paragraph("Database not available.")
        doc.add_paragraph(
            "Khong duoc cap quyen truy cap database. Cac entity suy ra tu source code "
            "duoc liet ke rieng trong Appendix A voi Status = Inferred.")
    else:
        doc.add_heading("3.1 Database Summary", level=2)
        doc.add_paragraph(nar.get("db_summary", S.UNKNOWN))
        doc.add_heading("3.2 Main Table List", level=2)
        add_table(doc,
                  ["Table", "Purpose", "Primary Key", "Main Foreign Keys",
                   "Important Columns", "Related Function IDs"],
                  [[t.get("Table"), t.get("Purpose"), t.get("PK"), t.get("FK"),
                    t.get("Important Columns"), t.get("Related Function IDs")]
                   for t in data["03_DB_Tables"]])
        doc.add_heading("3.3 Column Detail", level=2)
        add_table(doc,
                  ["Table", "Column", "Type", "PK", "FK", "Nullable", "Meaning",
                   "Source/Confidence"],
                  [[c.get("Table"), c.get("Column"), c.get("Type"), c.get("PK"),
                    c.get("FK"), c.get("Nullable"), c.get("Meaning"),
                    c.get("Confidence")] for c in data["04_DB_Columns"]])
        doc.add_heading("3.4 Main Relationships", level=2)
        for line in nar.get("relationships", [S.UNKNOWN]):
            doc.add_paragraph(line, style="List Bullet")

    # --- 4 ---
    doc.add_heading("4. Overall System Flow", level=1)
    if a.png:
        content_w = (sec.page_width - sec.left_margin - sec.right_margin)
        doc.add_picture(a.png, width=content_w)
        doc.add_paragraph("Figure 1. Overall System Flow")
    else:
        doc.add_paragraph("%s — chua co so do flow." % S.UNKNOWN)
    doc.add_heading("4.1 Flow Explanation", level=2)
    for line in flow.get("explanation", nar.get("flow_explanation", [S.UNKNOWN])):
        doc.add_paragraph(line)

    # --- Appendix A ---
    doc.add_heading("Appendix A. AI Analysis Notes / Open Questions", level=1)
    opens = [q for q in data["06_OpenQuestions"] if q.get("Status") == "Open"]
    add_table(doc, ["ID", "Type", "Item", "Reason / Evidence", "Required Action"],
              [[q.get("Q ID"), q.get("Type"), q.get("Item"),
                q.get("Reason / Evidence"), q.get("Required Action")] for q in opens]
              or [[DASH, DASH, "Khong con cau hoi treo", DASH, DASH]])

    # --- Appendix B ---
    doc.add_heading("Appendix B. Analysis Conditions", level=1)
    add_table(doc, ["Key", "Value"],
              [[k, meta.get(k, DASH)] for k in
               ("g0_scope", "g1_websites", "g2_crawl_mode", "g3_accounts", "g4_db",
                "g5_source", "g6_detail", "g7_lang", "g7_audience", "env_observed",
                "crawl_budget_used", "forbidden_zones", "run_mode", "previous_version")])

    doc.save(a.out)
    print("Da render %s — %d function · %d screen · %d table · %d open question"
          % (a.out, len(data["01_Function"]), len(data["02_Screen"]),
             len(data["03_DB_Tables"]), len(opens)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
