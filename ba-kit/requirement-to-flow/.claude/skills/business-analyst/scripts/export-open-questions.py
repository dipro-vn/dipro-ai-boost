#!/usr/bin/env python3
"""Output OQ — export Open Question Register (.md) ra workbook .xlsx.

Doc rule day du: .claude/ba-agent/open-questions.md

Script lam 2 viec:
  1. VALIDATE register — chi giu cau hoi nghiep vu BA, khong trung ID,
     khong cau hoi ghep, khong cau hoi chung chung, khong cau hoi ky thuat.
  2. EXPORT xlsx 3 sheet: Guideline (cach tra loi) · Open Questions · Summary.

Nguong 20 cau (xem open-questions.md muc 4):
  n <= 20  -> FIGMA_VIEW: DRAW  (BA ve them Figma OQ view)
  n >  20  -> FIGMA_VIEW: SKIP  (chi giao xlsx + duong dan folder)

Usage:
  python3 export-open-questions.py <OQ-REGISTER.md> --out <open_questions.xlsx> \
      [--feature NAME] [--version v2] [--date DDMMYYYY] [--allow "tu1,tu2"]

Exit: 0 = PASS | 1 = co FAIL (khong ghi file) | 2 = thieu openpyxl / khong doc duoc input
"""
import argparse
import datetime
import re
import sys

try:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
except ImportError:
    sys.stderr.write("FAIL: thieu openpyxl. Chay: pip install openpyxl\n")
    sys.exit(2)

# --- cot bat buoc trong register markdown (khop khong phan biet hoa/thuong) ---
COLS = [
    "OQ ID",
    "Nhom",
    "Cau hoi",
    "Impact",
    "Lien quan",
    "Muc chan",
    "De xuat cua BA",
    "Lua chon goi y",
]
# Header thuc te trong file .md co dau — map ve khoa ASCII o tren.
HEADER_ALIASES = {
    "oq id": "OQ ID",
    "id": "OQ ID",
    "nhóm nghiệp vụ": "Nhom",
    "nhóm": "Nhom",
    "nhom": "Nhom",
    "câu hỏi": "Cau hoi",
    "cau hoi": "Cau hoi",
    "vì sao cần trả lời (impact)": "Impact",
    "vì sao cần trả lời": "Impact",
    "impact": "Impact",
    "liên quan (fr/flow/screen)": "Lien quan",
    "liên quan": "Lien quan",
    "lien quan": "Lien quan",
    "mức chặn": "Muc chan",
    "muc chan": "Muc chan",
    "phương án ba đề xuất": "De xuat cua BA",
    "đề xuất của ba": "De xuat cua BA",
    "de xuat cua ba": "De xuat cua BA",
    "lựa chọn gợi ý": "Lua chon goi y",
    "lua chon goi y": "Lua chon goi y",
}

LEVELS = ["Blocker", "High", "Medium", "Low"]
LEVEL_FILL = {
    "Blocker": "FFFFF6F5",
    "High": "FFFFF9EB",
    "Medium": "FFE8F4FD",
    "Low": "FFF6F8FA",
}
LEVEL_FONT = {
    "Blocker": "FFCF222E",
    "High": "FFF4860C",
    "Medium": "FF0969DA",
    "Low": "FF57606A",
}
STATUS_OPTIONS = ["Chua tra loi", "Da tra loi", "Can thao luan", "Khong ap dung"]

# Cau hoi ky thuat -> viec cua Tech Lead, khong thuoc Output OQ.
TECH_WORDS = [
    "api", "endpoint", "schema", "database", "db", "sql", "query", "index",
    "migration", "table", "column", "framework", "redis", "cache", "s3",
    "docker", "kubernetes", "deploy", "ci/cd", "socket", "websocket", "sdk",
    "latency", "throughput", "server", "microservice", "repository", "orm",
    "jwt", "oauth", "webhook", "cronjob", "queue", "load balancer",
]
# Cau hoi chung chung -> khong tra loi duoc, khong duoc dua vao register.
VAGUE_PATTERNS = [
    r"còn\s+(gì|thiếu|vấn đề)", r"có\s+gì\s+(cần|muốn)", r"ý kiến\s+(khác|gì)",
    r"bạn\s+thấy\s+(thế nào|sao)", r"còn\s+yêu cầu\s+nào", r"anh/chị\s+bổ sung",
    r"^ok\b", r"có\s+đúng\s+không\s*$",
]

GUIDELINE = [
    ("H", "Cach tra loi Open Question"),
    ("P", "File nay la cac diem BA CHUA CO CAU TRA LOI trong nghiep vu. Cau nao khong duoc tra loi thi BA "
          "se KHONG tu suy dien — no se nam o SPEC muc `## Open Questions` va chan viec chot flow/AC."),
    ("H2", "1. Ban chi can dien 4 cot"),
    ("P", "`Cau tra loi cua ban` · `Nguoi tra loi (role)` · `Ngay tra loi` · `Trang thai`. "
          "Cac cot con lai BA dung de trace ve SPEC — xin dung sua/xoa/doi thu tu cot."),
    ("H2", "2. Moi cau tra loi theo 1 trong 4 dang"),
    ("P", "OK theo de xuat  — dong y cot `Phuong an BA de xuat`, ghi: \"OK theo de xuat\"."),
    ("P", "Sua lai          — ghi RULE DUNG, cu the, co so/dieu kien. VD: \"Het 15 phut khong thanh toan thi huy don\"."),
    ("P", "Chua biet        — ghi ro AI se tra loi + KHI NAO. VD: \"Cho ke toan xac nhan, tra loi truoc 05/10\"."),
    ("P", "Khong ap dung    — ghi ly do ngan. VD: \"Nghiep vu nay da bo tu thang 8\"."),
    ("H2", "3. Uu tien"),
    ("P", "Tra loi cac cau `Blocker` truoc — day la cac cau dang chan BA ve Output 2 (Screen Flow) va Output 3 (Screens). "
          "`High` chan viec chot Acceptance Criteria."),
    ("H2", "4. Nen / khong nen"),
    ("P", "NEN     — 1 o tra loi cho 1 cau; noi bang rule co dieu kien, con so, trang thai, ai duoc lam gi."),
    ("P", "KHONG   — tra loi \"tuy\", \"linh dong\", \"nhu hien tai\" ma khong chi ro he thong/man hinh nao; "
          "gop nhieu cau vao 1 o; tra loi bang cau hoi khac."),
    ("H2", "5. File / anh tham khao"),
    ("P", "Co tai lieu kem theo -> ghi TEN FILE vao o tra loi va de file vao cung folder chua workbook nay. "
          "Xin dung dan anh truc tiep vao cell (BA can duong dan de trace nguon)."),
    ("H2", "6. Du lieu bao mat"),
    ("P", "Khong dien du lieu that cua khach hang (ten/SDT/email/du lieu production) vao file nay. "
          "Dung du lieu mau — file nay se duoc dua vao tai lieu thiet ke."),
    ("H2", "7. Gui lai cho BA"),
    ("P", "Giu nguyen ten file + cot, gui lai file da dien; hoac tra loi truc tiep trong chat theo format: "
          "\"OQ-03: <cau tra loi>\" (moi cau 1 dong)."),
    ("H2", "8. Sau khi ban tra loi"),
    ("P", "BA cap nhat SPEC (Source Register doi UNKNOWN -> FACT), ve lai phan bi anh huong, "
          "roi luu thanh version MOI. Cac cau con trong van duoc giu lai o vong sau."),
]

THIN = Side(style="thin", color="FFD0D7DE")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
ANSWER_FILL = "FFFFF8C5"   # vang — o can ban dien
HEADER_FILL = "FF0969DA"


class Report:
    def __init__(self):
        self.rows = []

    def add(self, name, status, detail=""):
        self.rows.append((name, status, detail))

    def counts(self):
        ok = sum(1 for r in self.rows if r[1] == "PASS")
        fail = sum(1 for r in self.rows if r[1] == "FAIL")
        warn = sum(1 for r in self.rows if r[1] == "WARN")
        return ok, fail, warn


def parse_register(path):
    """Doc bang markdown dau tien co du cot bat buoc."""
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        sys.stderr.write("FAIL: khong doc duoc %s (%s)\n" % (path, exc))
        sys.exit(2)

    header_idx, keys = None, None
    for i, line in enumerate(lines):
        if line.count("|") < 4:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        mapped = [HEADER_ALIASES.get(c.lower().strip(), None) for c in cells]
        if mapped.count("OQ ID") == 1 and mapped.count("Cau hoi") == 1:
            header_idx, keys = i, mapped
            break
    if header_idx is None:
        sys.stderr.write(
            "FAIL: khong tim thay bang OQ trong %s. "
            "Header phai co cot 'OQ ID' va 'Cau hoi' — xem open-questions.md muc 2\n" % path)
        sys.exit(2)

    rows = []
    for line in lines[header_idx + 2:]:
        if line.count("|") < 4:
            if rows:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        row = {}
        for k, v in zip(keys, cells):
            if k:
                row[k] = v
        if row.get("OQ ID"):
            rows.append(row)
    return keys, rows


def validate(keys, rows, allow, rep):
    missing = [c for c in COLS if c not in keys]
    if missing:
        rep.add("Cot bat buoc", "FAIL", "thieu: %s" % ", ".join(missing))
    else:
        rep.add("Cot bat buoc", "PASS", "du %d cot" % len(COLS))

    if not rows:
        rep.add("So cau hoi", "FAIL", "register khong co dong nao")
        return
    rep.add("So cau hoi", "PASS", "%d cau" % len(rows))

    ids = [r.get("OQ ID", "") for r in rows]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    rep.add("OQ ID khong trung", "FAIL" if dup else "PASS",
            ("trung: %s" % ", ".join(dup)) if dup else "%d ID duy nhat" % len(set(ids)))

    bad_fmt = [i for i in ids if not re.fullmatch(r"OQ-\d{2,3}", i)]
    rep.add("Format OQ ID", "FAIL" if bad_fmt else "PASS",
            ("sai format (can OQ-01): %s" % ", ".join(bad_fmt)) if bad_fmt else "OQ-NN")

    empty = [r["OQ ID"] for r in rows
             if not r.get("Cau hoi") or not r.get("Impact") or not r.get("De xuat cua BA")]
    rep.add("Cau hoi / Impact / De xuat khong rong", "FAIL" if empty else "PASS",
            ("thieu noi dung: %s" % ", ".join(empty)) if empty else "day du")

    bad_lv = [r["OQ ID"] for r in rows if r.get("Muc chan") not in LEVELS]
    rep.add("Muc chan hop le", "FAIL" if bad_lv else "PASS",
            ("sai (can Blocker/High/Medium/Low): %s" % ", ".join(bad_lv)) if bad_lv
            else "Blocker %d · High %d · Medium %d · Low %d" % tuple(
                sum(1 for r in rows if r.get("Muc chan") == lv) for lv in LEVELS))

    no_trace = [r["OQ ID"] for r in rows if not r.get("Lien quan")]
    rep.add("Trace ve FR/Flow/Screen", "FAIL" if no_trace else "PASS",
            ("thieu trace: %s" % ", ".join(no_trace)) if no_trace else "moi cau co trace")

    tech = []
    for r in rows:
        low = r.get("Cau hoi", "").lower()
        hit = [w for w in TECH_WORDS
               if w not in allow and re.search(r"(?<![a-z])%s(?![a-z])" % re.escape(w), low)]
        if hit:
            tech.append("%s (%s)" % (r["OQ ID"], ", ".join(hit)))
    rep.add("Chi cau hoi nghiep vu", "FAIL" if tech else "PASS",
            ("cau hoi ky thuat -> chuyen Tech Lead: %s" % "; ".join(tech)) if tech
            else "khong co tu khoa ky thuat")

    vague = [r["OQ ID"] for r in rows
             if any(re.search(p, r.get("Cau hoi", ""), re.I) for p in VAGUE_PATTERNS)]
    rep.add("Khong cau hoi chung chung", "FAIL" if vague else "PASS",
            ("cau hoi khong tra loi duoc: %s" % ", ".join(vague)) if vague else "moi cau cu the")

    compound = [r["OQ ID"] for r in rows if r.get("Cau hoi", "").count("?") > 1]
    rep.add("1 cau = 1 van de", "FAIL" if compound else "PASS",
            ("cau hoi ghep (tach ra): %s" % ", ".join(compound)) if compound else "khong ghep")

    long_q = [r["OQ ID"] for r in rows if len(r.get("Cau hoi", "")) > 300]
    if long_q:
        rep.add("Do dai cau hoi", "WARN", "qua dai (>300 ky tu): %s" % ", ".join(long_q))
    no_opt = [r["OQ ID"] for r in rows
              if r.get("Muc chan") == "Blocker" and not r.get("Lua chon goi y")]
    if no_opt:
        rep.add("Blocker co lua chon goi y", "WARN",
                "nen cho san option de KH chi can chon: %s" % ", ".join(no_opt))


def _hdr(cell, text):
    cell.value = text
    cell.fill = PatternFill("solid", fgColor=HEADER_FILL)
    cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFFFF")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = BORDER


def build_workbook(rows, feature, version, date_str, out):
    wb = openpyxl.Workbook()

    # --- Sheet 1: Guideline ---
    ws = wb.active
    ws.title = "Guideline"
    ws.column_dimensions["A"].width = 118
    r = 1
    for kind, text in GUIDELINE:
        c = ws.cell(row=r, column=1, value=text)
        if kind == "H":
            c.font = Font(name="Arial", size=14, bold=True, color="FF0969DA")
            r += 1
            ws.cell(row=r, column=1,
                    value="Feature: %s · Version: %s · Ngay: %s" % (feature, version, date_str)
                    ).font = Font(name="Arial", size=9, italic=True, color="FF57606A")
        elif kind == "H2":
            c.font = Font(name="Arial", size=11, bold=True)
        else:
            c.font = Font(name="Arial", size=10)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[r].height = 30
        r += 2 if kind == "H2" else 1

    # --- Sheet 2: Open Questions ---
    oq = wb.create_sheet("Open Questions")
    headers = [
        ("OQ ID", 9), ("Nhom nghiep vu", 20), ("Cau hoi", 58),
        ("Vi sao can tra loi (impact)", 38), ("Lien quan (FR/Flow/Screen)", 24),
        ("Muc chan", 11), ("Phuong an BA de xuat", 34), ("Lua chon goi y", 28),
        ("Cau tra loi cua ban", 42), ("Nguoi tra loi (role)", 18),
        ("Ngay tra loi", 13), ("Trang thai", 15),
    ]
    for i, (name, width) in enumerate(headers, start=1):
        _hdr(oq.cell(row=1, column=i), name)
        oq.column_dimensions[get_column_letter(i)].width = width
    oq.row_dimensions[1].height = 34

    order = {lv: i for i, lv in enumerate(LEVELS)}
    rows = sorted(rows, key=lambda r: (order.get(r.get("Muc chan"), 9), r.get("OQ ID", "")))
    for i, row in enumerate(rows, start=2):
        lv = row.get("Muc chan", "Low")
        vals = [
            row.get("OQ ID", ""), row.get("Nhom", ""), row.get("Cau hoi", ""),
            row.get("Impact", ""), row.get("Lien quan", ""), lv,
            row.get("De xuat cua BA", ""), row.get("Lua chon goi y", ""),
            "", "", "", STATUS_OPTIONS[0],
        ]
        for j, v in enumerate(vals, start=1):
            c = oq.cell(row=i, column=j, value=v)
            c.border = BORDER
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.font = Font(name="Arial", size=10)
            if j <= 8:
                c.fill = PatternFill("solid", fgColor=LEVEL_FILL.get(lv, "FFFFFFFF"))
            else:
                c.fill = PatternFill("solid", fgColor=ANSWER_FILL)
            if j == 1:
                c.font = Font(name="Arial", size=10, bold=True)
            if j == 6:
                c.font = Font(name="Arial", size=10, bold=True,
                              color=LEVEL_FONT.get(lv, "FF57606A"))
                c.alignment = Alignment(horizontal="center", vertical="center")
        oq.row_dimensions[i].height = 58

    last = len(rows) + 1
    oq.freeze_panes = "C2"
    oq.auto_filter.ref = "A1:L%d" % last
    dv = DataValidation(type="list", formula1='"%s"' % ",".join(STATUS_OPTIONS),
                        allow_blank=True, showDropDown=False)
    oq.add_data_validation(dv)
    dv.add("L2:L%d" % max(last, 2))

    # --- Sheet 3: Summary ---
    sm = wb.create_sheet("Summary")
    sm.column_dimensions["A"].width = 30
    sm.column_dimensions["B"].width = 12
    sm.cell(row=1, column=1, value="Open Questions — %s (%s)" % (feature, version)
            ).font = Font(name="Arial", size=13, bold=True, color="FF0969DA")
    r = 3
    sm.cell(row=r, column=1, value="Tong so cau hoi").font = Font(name="Arial", bold=True)
    sm.cell(row=r, column=2, value=len(rows))
    r += 2
    _hdr(sm.cell(row=r, column=1), "Muc chan")
    _hdr(sm.cell(row=r, column=2), "So cau")
    for lv in LEVELS:
        r += 1
        c = sm.cell(row=r, column=1, value=lv)
        c.border = BORDER
        c.fill = PatternFill("solid", fgColor=LEVEL_FILL[lv])
        c.font = Font(name="Arial", size=10, bold=True, color=LEVEL_FONT[lv])
        c2 = sm.cell(row=r, column=2, value=sum(1 for x in rows if x.get("Muc chan") == lv))
        c2.border = BORDER
        c2.alignment = Alignment(horizontal="center")
    r += 2
    _hdr(sm.cell(row=r, column=1), "Nhom nghiep vu")
    _hdr(sm.cell(row=r, column=2), "So cau")
    groups = {}
    for x in rows:
        groups[x.get("Nhom", "(chua phan nhom)")] = groups.get(x.get("Nhom", "(chua phan nhom)"), 0) + 1
    for g, n in sorted(groups.items(), key=lambda kv: (-kv[1], kv[0])):
        r += 1
        sm.cell(row=r, column=1, value=g).border = BORDER
        c2 = sm.cell(row=r, column=2, value=n)
        c2.border = BORDER
        c2.alignment = Alignment(horizontal="center")
    r += 2
    sm.cell(row=r, column=1, value="Figma OQ view").font = Font(name="Arial", bold=True)
    sm.cell(row=r, column=2,
            value="DRAW (<=20 cau)" if len(rows) <= 20 else "SKIP (>20 cau — chi xlsx)")

    wb.save(out)
    return rows


def render(rep, src, out, n):
    lines = ["# Output OQ — Export Report", "",
             "Source: `%s`" % src, "Output: `%s`" % out, "",
             "| Check | Status | Chi tiet |", "|---|---|---|"]
    for name, status, detail in rep.rows:
        icon = {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "WARN": "⚠️ WARN"}[status]
        lines.append("| %s | %s | %s |" % (name, icon, detail.replace("|", "/")))
    ok, fail, warn = rep.counts()
    lines += ["", "**%d checks · %d PASS · %d FAIL · %d WARN**" % (len(rep.rows), ok, fail, warn),
              "", "OQ COUNT: %d" % n,
              "FIGMA_VIEW: %s" % ("DRAW" if n <= 20 else "SKIP (n > 20 — chi export xlsx)")]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("register", help="duong dan OQ-REGISTER.md")
    ap.add_argument("--out", required=True, help="duong dan xlsx xuat ra")
    ap.add_argument("--feature", default="<feature>", help="ten feature")
    ap.add_argument("--version", default="v1", help="version BA dang chay (VD v2)")
    ap.add_argument("--date", default="", help="DDMMYYYY — mac dinh hom nay")
    ap.add_argument("--allow", default="",
                    help="tu khoa ky thuat duoc phep xuat hien (phan cach dau phay) — "
                         "chi dung khi do la thuat ngu nghiep vu that")
    ap.add_argument("--report", help="ghi report markdown ra file")
    args = ap.parse_args()

    allow = {w.strip().lower() for w in args.allow.split(",") if w.strip()}
    date_str = args.date or datetime.date.today().strftime("%d%m%Y")

    keys, rows = parse_register(args.register)
    rep = Report()
    validate(keys, rows, allow, rep)
    ok, fail, warn = rep.counts()

    if fail:
        out = render(rep, args.register, "(khong ghi — con FAIL)", len(rows))
        print(out)
        if args.report:
            with open(args.report, "w", encoding="utf-8") as fh:
                fh.write(out)
        print("\nFAIL > 0 -> sua OQ-REGISTER.md roi chay lai. Khong ghi xlsx.")
        sys.exit(1)

    rows = build_workbook(rows, args.feature, args.version, date_str, args.out)
    out = render(rep, args.register, args.out, len(rows))
    print(out)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(out)
        print("Report: %s" % args.report)
    sys.exit(0)


if __name__ == "__main__":
    main()
