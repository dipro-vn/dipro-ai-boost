#!/usr/bin/env python3
"""Render CR Impact workbook (Luong 2) tu cr.json: 1 file, DUNG 2 sheet Summary + Impact.

  python3 build-cr-impact.py --cr-json <ver>/_internal/cr.json \
      --rates .claude/config/md-unit-rates.json --out <ver>/CR-<id>_Impact.xlsx

MD do script tinh = rate.md x qty (AI chi chon rate_code + qty, KHONG go so MD).
cr.json sai (enum, rate_code la, rate khac truc/loai, qty <= 0) -> exit 1, khong ghi gi.

Schema <ver>/_internal/cr.json (agent viet):
{"meta": {cr_id, cr_title, baseline_version, cr_version, source_type FILE|CHAT|LINK, source_ref,
          received_date, requested_by, overall_risk High|Medium|Low, recommendation},
 "justification": [{item:"CR-001.1", request, baseline_ref:"SC-014", baseline_quote, criteria:["C1","C3"],
                    why:"<=2 cau", not_feedback:"1 cau"}],              # >=1 dong, ref phai co trong baseline
 "not_cr": [{item, label: BUG|QUESTION, reason, baseline_ref}],
 "no_impact_axes": [{axis, reason >=15 ky tu}],                      # truc khong co dong impact nao
 "questions": [{id:"CQ-001", question, why, axis, owner, status}],
 "impacts": [{id:"IMP-001", axis System|DB|Business|Screen|ThirdParty|Mockup,
              change_type NEW|UPD|DEL|IMPACT, baseline_ref "SC-014;DS:primary" | "—", item, change,
              why_change, impact_on_current, conflict Yes|No|UNKNOWN, conflict_detail,
              risk High|Medium|Low, rate_code (ma trong md-unit-rates.json), qty > 0, md_note,
              evidence, question "CQ-001;CQ-002" | ""}]}
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402
import cr_common as C  # noqa: E402

# nhan ngan co dau cho khach (ma -> nhan); thieu ma -> dung CR_CRITERIA
CRIT_SHORT = {
    "C1": "Chức năng mới, chưa có trong hệ thống",
    "C2": "Đổi hành vi đang chạy đúng",
    "C3": "Thêm/bỏ màn, actor, chức năng, liên kết ngoài",
    "C4": "Đổi business rule / validation",
    "C5": "Đổi nền tảng / yêu cầu phi chức năng",
    "C6": "Kéo theo đổi DB / API / tài liệu đã bàn giao",
}
SRC_VI = {"FILE": "File", "CHAT": "Chat", "LINK": "Link"}
RISK_VI = {"High": "Cao (High)", "Medium": "Trung bình (Medium)", "Low": "Thấp (Low)"}
WIDTH_SUM = [22, 30, 36, 13, 30, 14]          # cot A..F sheet Summary
WIDTH_IMPACT = {"No": 5, "Impact ID": 10, "Trục": 11, "Loại": 8, "Baseline Ref": 20,
                "Hạng mục": 24, "Nội dung thay đổi": 36, "Vì sao phải sửa": 36,
                "Ảnh hưởng tới hiện tại": 34, "Xung đột": 9, "Chi tiết xung đột": 26,
                "Rủi ro": 9, "Mã đơn giá": 13, "Số lượng": 8, "MD": 7, "Ghi chú MD": 36,
                "Evidence": 30, "Câu hỏi": 12}
WARN_RED = "FFC00000"


def est_lines(text, width):
    n = 0
    for part in str(text or "").split("\n"):
        n += max(1, math.ceil(len(part) * 1.1 / max(width, 1)))
    return n


class Sheet:
    """Ghi sheet Summary tung dong, tu uoc luong chieu cao dong."""

    def __init__(self, ws):
        self.ws, self.r = ws, 0

    def put(self, cells, kind="data", merge_to=None, center=(), bold=(), color=None):
        from openpyxl.styles import Font
        import bd_styles as BD
        self.r += 1
        r = self.r
        lines = 1
        for col, val in cells:
            c = self.ws.cell(row=r, column=col, value=val)
            fn = {"header": BD.header, "title": BD.title, "banner": BD.banner}.get(kind)
            if fn:
                fn(c)
            else:
                BD.data(c, size=10, center=col in center)
                if col in bold:
                    c.font = Font(name=BD.FONT, size=10, bold=True)
            if color:
                c.font = Font(name=BD.FONT, size=10, bold=True, color=color)
            end = merge_to.get(col, col) if merge_to else col
            w = sum(WIDTH_SUM[i - 1] for i in range(col, end + 1))
            lines = max(lines, est_lines(val, w))
        for col, end in (merge_to or {}).items():
            for cc in range(col + 1, end + 1):
                fn2 = {"header": BD.header, "title": BD.title, "banner": BD.banner}.get(kind, BD.data)
                fn2(self.ws.cell(row=r, column=cc))
            if end > col:
                self.ws.merge_cells(start_row=r, start_column=col, end_row=r, end_column=end)
        self.ws.row_dimensions[r].height = max(16, 14 * lines + 2)
        return r

    def gap(self):
        self.r += 1
        self.ws.row_dimensions[self.r].height = 8


def build_summary(ws, cr, rates_meta, rates):
    meta = cr["meta"]
    sh = Sheet(ws)
    full = {1: 6}
    sh.put([(1, "%s — %s" % (meta["cr_id"], meta["cr_title"]))], "title", merge_to=full)
    m, row_tot, col_tot, grand = C.md_matrix(cr["impacts"], rates)
    status = str(rates_meta.get("status", "")).upper()
    head = [(C.L_CR, meta["cr_id"]), (C.L_TITLE, meta["cr_title"]),
            (C.L_BASELINE, meta["baseline_version"]), ("Phiên bản CR", meta["cr_version"]),
            ("Nguồn", "%s — %s" % (SRC_VI.get(meta["source_type"], meta["source_type"]), meta["source_ref"])),
            ("Ngày nhận", meta["received_date"]), ("Người yêu cầu (vai trò)", meta["requested_by"]),
            ("Mức ảnh hưởng chung", RISK_VI.get(meta["overall_risk"], meta["overall_risk"])),
            ("Đề xuất", meta["recommendation"])]
    for k, v in head:
        sh.put([(1, k), (2, v)], merge_to={2: 6}, bold=(1,))
    sh.put([(1, C.L_TOTAL_MD), (2, grand), (3, "man-day · %d hạng mục · đơn giá %s" % (
        len(cr["impacts"]), status or "?"))], merge_to={3: 6}, bold=(1, 2), center=(2,))

    sh.gap()
    sh.put([(1, "1. Vì sao đây là Change Request")], "banner", merge_to=full)
    sh.put([(1, "Hạng mục"), (2, "Yêu cầu"), (3, "Hệ thống hiện tại (baseline)"),
            (4, "Tiêu chí"), (5, "Giải trình")], "header", merge_to={5: 6})
    for j in cr["justification"]:
        crit = "\n".join("%s · %s" % (c, CRIT_SHORT.get(c, S.CR_CRITERIA.get(c, ""))) for c in j["criteria"])
        why = C.txt(j.get("why"))
        if C.txt(j.get("not_feedback")):
            why += "\nKhông phải lỗi: " + C.txt(j["not_feedback"])
        sh.put([(1, j.get("item")), (2, j.get("request")),
                (3, "%s: “%s”" % (j.get("baseline_ref"), C.txt(j.get("baseline_quote")))),
                (4, crit), (5, why)], merge_to={5: 6}, bold=(1,))

    sh.gap()
    sh.put([(1, "2. Tổng MD (man-day) theo trục × loại thay đổi")], "banner", merge_to=full)
    sh.put([(1, C.L_AXIS_HDR)] + [(i + 2, t) for i, t in enumerate(S.CR_CHANGE_TYPE)] +
           [(6, C.L_TOTAL)], "header")
    num_cols = tuple(range(2, 7))
    for a in S.CR_AXES:
        sh.put([(1, "%s (%s)" % (C.AXIS_VI[a], a))] +
               [(i + 2, m[a][t]) for i, t in enumerate(S.CR_CHANGE_TYPE)] +
               [(6, row_tot[a])], center=num_cols)
    sh.put([(1, C.L_TOTAL)] + [(i + 2, col_tot[t]) for i, t in enumerate(S.CR_CHANGE_TYPE)] +
           [(6, grand)], center=num_cols, bold=(1, 2, 3, 4, 5, 6))
    sh.put([(1, C.L_RATES), (2, "%s v%s — %s" % (status or "?", rates_meta.get("version", "?"),
                                                  C.txt(rates_meta.get("scope_note"))))],
           merge_to={2: 6}, bold=(1,))
    if status != "APPROVED":
        sh.put([(1, "Lưu ý"), (2, "Ước lượng sơ bộ — chưa được PM/Tech Lead duyệt")],
               merge_to={2: 6}, color=WARN_RED)

    sh.gap()
    sh.put([(1, "3. Trục không ảnh hưởng")], "banner", merge_to=full)
    sh.put([(1, "Trục"), (2, "Lý do")], "header", merge_to={2: 6})
    for x in cr["no_impact_axes"] or [{"axis": "", "reason": "Không có — cả 6 trục đều có hạng mục"}]:
        ax = x.get("axis")
        sh.put([(1, "%s (%s)" % (C.AXIS_VI.get(ax, ax), ax) if ax else "—"), (2, x.get("reason"))],
               merge_to={2: 6})

    sh.gap()
    sh.put([(1, "4. Câu hỏi cần khách hàng trả lời")], "banner", merge_to=full)
    sh.put([(1, "Mã"), (2, "Câu hỏi"), (3, "Vì sao cần"), (4, "Trục"), (5, "Người trả lời"),
            (6, "Trạng thái")], "header")
    for q in cr["questions"] or [{"id": "—", "question": "Không có câu hỏi"}]:
        sh.put([(1, q.get("id")), (2, q.get("question")), (3, q.get("why")), (4, q.get("axis")),
                (5, q.get("owner")), (6, q.get("status"))], bold=(1,), center=(4, 6))

    if cr["not_cr"]:
        sh.gap()
        sh.put([(1, "5. Không thuộc CR")], "banner", merge_to=full)
        sh.put([(1, "Hạng mục"), (2, "Phân loại"), (3, "Lý do"), (6, "Baseline Ref")], "header",
               merge_to={3: 5})
        for n in cr["not_cr"]:
            sh.put([(1, n.get("item")), (2, "Lỗi hệ thống (BUG)" if n.get("label") == "BUG"
                                          else "Câu hỏi (QUESTION)"),
                    (3, n.get("reason")), (6, n.get("baseline_ref"))], merge_to={3: 5}, bold=(1,))

    from openpyxl.utils import get_column_letter
    for i, w in enumerate(WIDTH_SUM, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = "A1:F%d" % sh.r


def build_impact(ws, cr, rates):
    import bd_styles as BD
    from openpyxl.utils import get_column_letter
    cols = S.CR_IMPACT_COLS
    for i, h in enumerate(cols, start=1):
        BD.header(ws.cell(row=1, column=i, value=h))
        ws.column_dimensions[get_column_letter(i)].width = WIDTH_IMPACT.get(h, 14)
    ws.row_dimensions[1].height = 30
    center = {"No", "Impact ID", "Trục", "Loại", "Xung đột", "Rủi ro", "Mã đơn giá", "Số lượng", "MD"}
    total = 0.0
    for n, imp in enumerate(cr["impacts"], start=1):
        r = rates[imp["rate_code"]]
        md = C.md_of(imp, rates)
        total += md
        q = C.qty_of(imp)
        note = "%s (%s MD/%s × %s)" % (r.get("item"), C.fmt_md(float(r["md"])), r.get("unit"), C.fmt_md(q))
        if C.txt(imp.get("md_note")):
            note += "; " + C.txt(imp["md_note"])
        vals = {"No": n, "Impact ID": imp["id"], "Trục": imp["axis"], "Loại": imp["change_type"],
                "Baseline Ref": C.txt(imp.get("baseline_ref")) or "—", "Hạng mục": imp.get("item"),
                "Nội dung thay đổi": imp.get("change"), "Vì sao phải sửa": imp.get("why_change"),
                "Ảnh hưởng tới hiện tại": imp.get("impact_on_current"), "Xung đột": imp["conflict"],
                "Chi tiết xung đột": C.txt(imp.get("conflict_detail")) or "—", "Rủi ro": imp["risk"],
                "Mã đơn giá": imp["rate_code"], "Số lượng": q if q != int(q) else int(q), "MD": md,
                "Ghi chú MD": note, "Evidence": imp.get("evidence"),
                "Câu hỏi": C.txt(imp.get("question")) or "—"}
        lines = 1
        for i, h in enumerate(cols, start=1):
            c = ws.cell(row=n + 1, column=i, value=vals[h])
            BD.data(c, size=10, code=h == "Impact ID", center=h in center)
            lines = max(lines, est_lines(vals[h], WIDTH_IMPACT.get(h, 14)))
        ws.row_dimensions[n + 1].height = min(14 * lines + 4, 160)
    last = len(cr["impacts"]) + 1
    tr = last + 1
    for i, h in enumerate(cols, start=1):
        BD.banner(ws.cell(row=tr, column=i))
    ws.cell(row=tr, column=cols.index("Impact ID") + 1, value=C.L_TOTAL_MD)
    ws.cell(row=tr, column=cols.index("MD") + 1, value=round(total, 2))
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = "A1:%s%d" % (get_column_letter(len(cols)), last)
    ws.page_setup.orientation = "landscape"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_title_rows = "1:1"
    return round(total, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cr-json", required=True)
    ap.add_argument("--rates", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        from openpyxl import Workbook
    except ImportError:
        print("Thieu openpyxl. Chay: pip install openpyxl", file=sys.stderr)
        return 2
    try:
        cr = C.load_json(a.cr_json)
        rates_meta, rates = C.load_rates(a.rates)
    except (OSError, ValueError) as e:
        print("Khong doc duoc input: %s" % e, file=sys.stderr)
        return 1
    err = C.validate_cr(cr, rates)
    if not err and not cr.get("justification"):
        err.append("justification rong — phai giai trinh vi sao la CR")
    if err:
        print("cr.json KHONG hop le — khong ghi file:", file=sys.stderr)
        for e in err:
            print("  - " + e, file=sys.stderr)
        return 1
    for k in ("not_cr", "no_impact_axes", "questions", "impacts"):
        cr.setdefault(k, [])

    wb = Workbook()
    ws = wb.active
    ws.title = S.CR_SHEET_SUMMARY
    build_summary(ws, cr, rates_meta, rates)
    total = build_impact(wb.create_sheet(S.CR_SHEET_IMPACT), cr, rates)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    wb.save(a.out)
    print("Da ghi %s — %d hang muc · %s MD (don gia %s v%s)" % (
        a.out, len(cr["impacts"]), C.fmt_md(total), rates_meta.get("status"), rates_meta.get("version")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
