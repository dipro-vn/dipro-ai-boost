#!/usr/bin/env python3
"""
Đọc / cập nhật file TC .xlsx hoặc .md đang chạy (phục vụ /update-tcs).

  python3 -I xlsx_tcs.py read  <file.xlsx> <out.json>
      Đọc mọi sheet TC (sheet có header `ID` + `Test Scenario`) thành JSON:
      từng dòng TC theo tên header, cột kết quả tách riêng. Sheet khác
      (High Risk & E2E, Test view point, ...) xuất các ô không rỗng.
      In tóm tắt: số TC mỗi sheet, số TC đã có kết quả.

  python3 -I xlsx_tcs.py write <src.xlsx> <changes.json> <out.xlsx>
      Copy <src.xlsx> -> <out.xlsx> (file gốc KHÔNG bị sửa) rồi áp thay đổi.
      Không dùng delete_rows: ghi lại các dòng TC từ danh sách đã cập nhật,
      nên công thức "No.", dropdown, ô merge không bị lệch.

Đầu vào `.md` ([module]-testcases-vN.md, giai đoạn đang design, chưa có kết quả): dùng đúng hai lệnh
trên với file `.md` (read/write chọn theo đuôi file). Khác biệt:
  - mỗi `## <Screen>` là một "sheet"; không có cột kết quả (`results` luôn rỗng);
  - `Notes` chưa có trong bảng md -> script tự thêm cột `Notes` vào bảng cần ghi chú;
  - `cells` không dùng cho md; thay bằng `text_replace`:
      "text_replace": {"High Risk & E2E": [["2 review mới nhất", "3 review mới nhất"]]}
  - mục `## Changelog` được thêm/nối cuối file.
  - Ký tự đặc biệt (< > & |) tự được mã hoá entity theo quy ước của md_to_xlsx.py.

changes.json:
{
  "sheets": {
    "<tên sheet TC>": {
      "delete": ["APB-015"],
      "update": {"APB-021": {"Steps": "...", "Expected results": "...", "Notes": "[v2] ..."}},
      "note":   {"APB-044": "[v2] Cần xem lại: ..."},
      "add":    [{"ID": "APB-049", "Function Name": "...", "Category": "...", "Notes": "[v2] Mới: AC-07"}]
    }
  },
  "cells": {"High Risk & E2E": {"B3": "APB-049"}},
  "changelog": {"version": "v2", "date": "2026-11-08", "source": "spec-v2.md",
                "rows": [["APB-021", "Sửa", "AC-07 đổi 5→3", "AC-07"]]}
}
  - update : ghi đè các cột nêu tên, XOÁ toàn bộ cột kết quả. Riêng `Notes`
             được NỐI vào ghi chú sẵn có của QC, không ghi đè.
  - note   : chỉ nối vào Notes, giữ nguyên nội dung và kết quả.
  - add    : thêm cuối sheet (cột kết quả để trống).
  - cells  : sửa ô lẻ ở sheet không phải sheet TC (VD High Risk & E2E).
"""
import copy
import html
import json
import re
import shutil
import sys
from pathlib import Path

import openpyxl
from openpyxl.worksheet.cell_range import MultiCellRange

TC_TEMPLATE_MAX_ROW = 97  # công thức/dropdown template chỉ dựng sẵn tới dòng này
HEADER_ROW = 1
NO_COL = 1
CHANGELOG_SHEET = "Changelog"


# ---------- tiện ích ----------

def norm(v):
    return "" if v is None else str(v).strip()


def is_tc_sheet(ws):
    headers = [norm(c.value).lower() for c in ws[HEADER_ROW]]
    return "id" in headers and "test scenario" in headers


def header_map(ws):
    """Trả về (list tên header theo cột, dict tên-duy-nhất -> số cột).
    Header trùng tên (VD `Bug ID` xuất hiện hai lần) được thêm hậu tố ` #2`, ` #3`."""
    names, seen = [], {}
    for c in ws[HEADER_ROW]:
        h = norm(c.value)
        if not h:
            names.append(None)
            continue
        seen[h] = seen.get(h, 0) + 1
        names.append(h if seen[h] == 1 else f"{h} #{seen[h]}")
    return names, {n: i + 1 for i, n in enumerate(names) if n}


def result_columns(names):
    """Cột kết quả = mọi cột nằm giữa `Test Data` và `Notes` (bền khi thêm vòng R3...)."""
    low = [(n or "").lower() for n in names]
    if "test data" not in low or "notes" not in low:
        raise SystemExit("Sheet TC thiếu cột `Test Data` hoặc `Notes`; không xác định được cột kết quả.")
    a, b = low.index("test data"), low.index("notes")
    return [i + 1 for i in range(a + 1, b) if names[i]]


def data_rows(ws, id_col):
    """Các số dòng có ID (bỏ dòng trống)."""
    return [r for r in range(HEADER_ROW + 1, ws.max_row + 1) if norm(ws.cell(r, id_col).value)]


def extend_dropdowns(ws, last_row):
    end = str(TC_TEMPLATE_MAX_ROW)
    for dv in ws.data_validations.dataValidation:
        toks = []
        for t in str(dv.sqref).split():
            if ":" in t and t.endswith(end):
                t = t[: -len(end)] + str(last_row)
            toks.append(t)
        dv.sqref = MultiCellRange(" ".join(toks))


# ---------- read ----------

def cmd_read(src, out):
    wb = openpyxl.load_workbook(src)
    result = {"file": Path(src).name, "sheets": []}
    for ws in wb.worksheets:
        if is_tc_sheet(ws):
            names, cols = header_map(ws)
            res_cols = set(result_columns(names))
            id_col = cols["ID"]
            tcs = []
            for r in data_rows(ws, id_col):
                row = {"row": r, "fields": {}, "results": {}}
                for i, n in enumerate(names):
                    if not n or i + 1 == NO_COL:
                        continue
                    v = ws.cell(r, i + 1).value
                    if v is None or norm(v) == "":
                        continue
                    (row["results"] if (i + 1) in res_cols else row["fields"])[n] = v
                tcs.append(row)
            result["sheets"].append({"name": ws.title, "kind": "tc", "headers": [n for n in names if n], "tcs": tcs})
        else:
            cells = {}
            for row in ws.iter_rows():
                for c in row:
                    if c.value is not None and norm(c.value) != "":
                        cells[c.coordinate] = c.value
            result["sheets"].append({"name": ws.title, "kind": "other", "cells": cells})
    Path(out).write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"Đã đọc {src}")
    total = filled = 0
    for s in result["sheets"]:
        if s["kind"] == "tc":
            n = len(s["tcs"])
            f = sum(1 for t in s["tcs"] if t["results"])
            total += n
            filled += f
            print(f"  [TC]    {s['name']}: {n} TC, {f} có kết quả, {n - f} chưa chạy")
        else:
            print(f"  [khác]  {s['name']}: {len(s['cells'])} ô có dữ liệu")
    print(f"Tổng: {total} TC, {filled} có kết quả. JSON: {out}")


# ---------- write ----------

def append_note(old, add):
    old, add = norm(old), norm(add)
    if not add:
        return old or None
    return f"{old}\n{add}" if old else add


def cmd_write(src, changes_path, out):
    changes = json.loads(Path(changes_path).read_text(encoding="utf-8"))
    if Path(src).resolve() == Path(out).resolve():
        raise SystemExit("Output trùng file gốc. /update-tcs luôn ghi ra file mới, không sửa file gốc.")
    shutil.copyfile(src, out)
    wb = openpyxl.load_workbook(out)
    warnings, stats = [], {"delete": 0, "update": 0, "note": 0, "add": 0}

    for sheet_name, ch in changes.get("sheets", {}).items():
        if sheet_name not in wb.sheetnames:
            warnings.append(f"Không có sheet `{sheet_name}` — bỏ qua.")
            continue
        ws = wb[sheet_name]
        if not is_tc_sheet(ws):
            warnings.append(f"Sheet `{sheet_name}` không phải sheet TC — bỏ qua.")
            continue
        names, cols = header_map(ws)
        res_cols = result_columns(names)
        lcols = {k.lower(): v for k, v in cols.items()}
        id_col, notes_col = lcols["id"], lcols["notes"]
        max_col = max(c for c in cols.values())

        # 1. chụp toàn bộ dòng TC hiện có (theo cột, trừ cột No. là công thức)
        old_rows = data_rows(ws, id_col)
        snapshot = []
        for r in old_rows:
            snapshot.append({c: ws.cell(r, c).value for c in range(2, max_col + 1)})
        by_id = {norm(row[id_col]): row for row in snapshot}
        order = [norm(row[id_col]) for row in snapshot]

        # 2. áp thay đổi trên snapshot
        for tid in ch.get("delete", []):
            if tid in by_id:
                order.remove(tid)
                del by_id[tid]
                stats["delete"] += 1
            else:
                warnings.append(f"[{sheet_name}] delete: không thấy ID {tid}")
        for tid, fields in ch.get("update", {}).items():
            if tid not in by_id:
                warnings.append(f"[{sheet_name}] update: không thấy ID {tid}")
                continue
            row = by_id[tid]
            for k, v in fields.items():
                if k.lower() not in lcols:
                    warnings.append(f"[{sheet_name}] update {tid}: không có cột `{k}`")
                elif k.lower() == "notes":
                    row[notes_col] = append_note(row.get(notes_col), v)
                else:
                    row[lcols[k.lower()]] = v
            for c in res_cols:  # TC đã sửa -> phải test lại -> xoá kết quả
                row[c] = None
            stats["update"] += 1
        for tid, text in ch.get("note", {}).items():
            if tid not in by_id:
                warnings.append(f"[{sheet_name}] note: không thấy ID {tid}")
                continue
            by_id[tid][notes_col] = append_note(by_id[tid].get(notes_col), text)
            stats["note"] += 1
        for new in ch.get("add", []):
            tid = norm(new.get("ID"))
            if not tid or tid in by_id:
                warnings.append(f"[{sheet_name}] add: thiếu hoặc trùng ID `{tid}`")
                continue
            row = {c: None for c in range(2, max_col + 1)}
            for k, v in new.items():
                if k.lower() in lcols:
                    row[lcols[k.lower()]] = v
                else:
                    warnings.append(f"[{sheet_name}] add {tid}: không có cột `{k}`")
            by_id[tid] = row
            order.append(tid)
            stats["add"] += 1

        # 3. ghi lại từ dòng 2, xoá phần thừa ở cuối
        last_old = old_rows[-1] if old_rows else HEADER_ROW
        for i, tid in enumerate(order):
            r = HEADER_ROW + 1 + i
            for c in range(2, max_col + 1):
                ws.cell(r, c).value = by_id[tid].get(c)
            if r > TC_TEMPLATE_MAX_ROW:
                ws.cell(r, NO_COL).value = "=row()-2"
                if r > ws.max_row or ws.cell(r, id_col).style_id == 0:
                    for c in range(1, max_col + 1):  # mượn định dạng từ dòng 2
                        ws.cell(r, c)._style = copy.copy(ws.cell(HEADER_ROW + 1, c)._style)
        new_last = HEADER_ROW + len(order)
        for r in range(new_last + 1, last_old + 1):
            for c in range(2, max_col + 1):
                ws.cell(r, c).value = None
        if new_last > TC_TEMPLATE_MAX_ROW:
            extend_dropdowns(ws, new_last)

    for sheet_name, cells in changes.get("cells", {}).items():
        if sheet_name not in wb.sheetnames:
            warnings.append(f"cells: không có sheet `{sheet_name}`")
            continue
        for coord, v in cells.items():
            wb[sheet_name][coord].value = v

    cl = changes.get("changelog")
    if cl:
        ws = wb[CHANGELOG_SHEET] if CHANGELOG_SHEET in wb.sheetnames else wb.create_sheet(CHANGELOG_SHEET)
        r = ws.max_row + 2 if ws.max_row > 1 or ws["A1"].value else 1
        ws.cell(r, 1).value = f"{cl.get('version', '')} — {cl.get('date', '')} — nguồn: {cl.get('source', '')}"
        ws.cell(r, 1).font = openpyxl.styles.Font(bold=True)
        r += 1
        for j, h in enumerate(["ID", "Thay đổi", "Lý do", "AC liên quan"], 1):
            ws.cell(r, j).value = h
            ws.cell(r, j).font = openpyxl.styles.Font(bold=True)
        for row in cl.get("rows", []):
            r += 1
            for j, v in enumerate(row, 1):
                ws.cell(r, j).value = v
        for col, w in zip("ABCD", (14, 14, 60, 18)):
            ws.column_dimensions[col].width = w

    wb.save(out)
    print(f"Đã ghi {out} (file gốc giữ nguyên): "
          f"xoá {stats['delete']}, sửa {stats['update']}, chỉ ghi chú {stats['note']}, thêm {stats['add']}.")
    for w in warnings:
        print("CẢNH BÁO:", w)


# ---------- Markdown (test-cases.md) ----------

def md_unescape(cell):
    return html.unescape(re.sub(r"<br\s*/?>", "\n", cell, flags=re.I)).strip()


def md_escape(v):
    if v is None:
        return ""
    t = str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;")
    return t.replace("\n", "<br>")


def md_is_row(line):
    t = line.strip()
    return t.startswith("|") and t.endswith("|")


def md_is_sep(line):
    return bool(re.match(r"^\|[-:\s|]+\|$", line.strip()))


def md_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_render(cells):
    return "| " + " | ".join(cells) + " |"


def md_parse(lines):
    """Trả về list section {name, start, end, tables}. Chỉ `## ` là ranh giới section.
    Mỗi table: {head, sep, rows:[line idx], headers} (chỉ bảng TC có cột ID + Test Scenario)."""
    secs, cur = [], {"name": "", "start": 0, "tables": []}
    i = 0
    while i < len(lines):
        m = re.match(r"^##\s+(.+?)\s*$", lines[i])
        if m and not lines[i].startswith("###"):
            cur["end"] = i
            secs.append(cur)
            cur = {"name": m.group(1), "start": i, "tables": []}
            i += 1
            continue
        if md_is_row(lines[i]):
            j = i
            while j < len(lines) and md_is_row(lines[j]):
                j += 1
            block = list(range(i, j))
            if len(block) >= 2 and md_is_sep(lines[block[1]]):
                headers = md_cells(lines[block[0]])
                low = [h.lower() for h in headers]
                if "id" in low and "test scenario" in low:
                    cur["tables"].append({"head": block[0], "sep": block[1], "rows": block[2:], "headers": headers})
            i = j
            continue
        i += 1
    cur["end"] = len(lines)
    secs.append(cur)
    return secs


def md_read(src, out):
    lines = Path(src).read_text(encoding="utf-8").split("\n")
    result = {"file": Path(src).name, "format": "md", "sheets": []}
    total = 0
    for sec in md_parse(lines):
        if sec["tables"]:
            t0 = sec["tables"][0]
            tcs = []
            for tb in sec["tables"]:
                for ri in tb["rows"]:
                    cells = md_cells(lines[ri])
                    cells += [""] * (len(tb["headers"]) - len(cells))
                    fields = {h: md_unescape(c) for h, c in zip(tb["headers"], cells) if md_unescape(c)}
                    tcs.append({"row": ri + 1, "fields": fields, "results": {}})
            total += len(tcs)
            result["sheets"].append({"name": sec["name"], "kind": "tc", "headers": t0["headers"], "tcs": tcs})
            print(f"  [TC]    {sec['name']}: {len(tcs)} TC")
        elif sec["name"]:
            text = "\n".join(lines[sec["start"] + 1: sec["end"]]).strip()
            result["sheets"].append({"name": sec["name"], "kind": "other", "text": text})
            print(f"  [khác]  {sec['name']}: {len(text)} ký tự")
    Path(out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Tổng: {total} TC (file .md không có cột kết quả). JSON: {out}")


def md_write(src, changes_path, out):
    changes = json.loads(Path(changes_path).read_text(encoding="utf-8"))
    if Path(src).resolve() == Path(out).resolve():
        raise SystemExit("Output trùng file gốc. /update-tcs luôn ghi ra file mới, không sửa file gốc.")
    lines = Path(src).read_text(encoding="utf-8").split("\n")
    warnings, stats = [], {"delete": 0, "update": 0, "note": 0, "add": 0}

    # 1. thay thế văn bản trong section (không đổi số dòng)
    for sec_name, pairs in changes.get("text_replace", {}).items():
        secs = [s for s in md_parse(lines) if s["name"] == sec_name]
        if not secs:
            warnings.append(f"text_replace: không có section `{sec_name}`")
            continue
        sec = secs[0]
        for a, b in pairs:
            hit = 0
            for i in range(sec["start"], sec["end"]):
                if a in lines[i]:
                    lines[i] = lines[i].replace(a, b)
                    hit += 1
            if not hit:
                warnings.append(f"text_replace [{sec_name}]: không thấy `{a}`")

    # 2. sửa bảng TC, xử lý từ section cuối lên để chỉ số dòng không lệch
    secs = md_parse(lines)
    for sheet_name, ch in changes.get("sheets", {}).items():
        sec = next((s for s in secs if s["name"] == sheet_name), None)
        if not sec or not sec["tables"]:
            warnings.append(f"Không có section/bảng TC `{sheet_name}` — bỏ qua.")
            continue
        sec["_ch"] = ch
    for sec in reversed(secs):
        ch = sec.get("_ch")
        if not ch:
            continue
        tb = sec["tables"][0]
        headers = list(tb["headers"])
        low = [h.lower() for h in headers]
        idc = low.index("id")
        rows = {}   # tid -> cells
        order = []
        for tb_i in sec["tables"]:
            for ri in tb_i["rows"]:
                cells = md_cells(lines[ri]) + [""] * len(headers)
                cells = cells[: len(headers)]
                tid = md_unescape(cells[idc])
                rows[tid] = {"cells": cells, "orig": lines[ri], "dirty": False}
                order.append(tid)

        def col(name):
            return low.index(name.lower()) if name.lower() in low else None

        need_notes = (
            any(k.lower() == "notes" for v in ch.get("update", {}).values() for k in v)
            or bool(ch.get("note"))
            or any(k.lower() == "notes" for a in ch.get("add", []) for k in a))
        added_notes = False
        if need_notes and "notes" not in low:
            headers.append("Notes"); low.append("notes"); added_notes = True
            for r in rows.values():
                r["cells"].append(""); r["pad"] = True  # chỉ nối 1 ô trống, không render lại dòng
        nc = col("notes")

        def put(r, name, val):
            ci = col(name)
            if ci is None:
                return False
            r["cells"][ci] = md_escape(val); r["dirty"] = True
            return True

        def put_note(r, val):
            old = md_unescape(r["cells"][nc]) if r["cells"][nc] else ""
            r["cells"][nc] = md_escape(append_note(old, val)); r["dirty"] = True

        for tid in ch.get("delete", []):
            if tid in rows:
                order.remove(tid); del rows[tid]; stats["delete"] += 1
            else:
                warnings.append(f"[{sheet_name}] delete: không thấy ID {tid}")
        for tid, fields in ch.get("update", {}).items():
            if tid not in rows:
                warnings.append(f"[{sheet_name}] update: không thấy ID {tid}"); continue
            for k, v in fields.items():
                if k.lower() == "notes":
                    put_note(rows[tid], v)
                elif not put(rows[tid], k, v):
                    warnings.append(f"[{sheet_name}] update {tid}: không có cột `{k}`")
            stats["update"] += 1
        for tid, text in ch.get("note", {}).items():
            if tid not in rows:
                warnings.append(f"[{sheet_name}] note: không thấy ID {tid}"); continue
            put_note(rows[tid], text); stats["note"] += 1
        for new in ch.get("add", []):
            tid = norm(new.get("ID"))
            if not tid or tid in rows:
                warnings.append(f"[{sheet_name}] add: thiếu hoặc trùng ID `{tid}`"); continue
            r = {"cells": [""] * len(headers), "orig": None, "dirty": True}
            for k, v in new.items():
                if k.lower() == "notes":
                    put_note(r, v)
                elif not put(r, k, v):
                    warnings.append(f"[{sheet_name}] add {tid}: không có cột `{k}`")
            rows[tid] = r; order.append(tid); stats["add"] += 1

        if added_notes:
            new_block = [lines[tb["head"]].rstrip() + " Notes |", lines[tb["sep"]].rstrip() + "---|"]
        else:
            new_block = [lines[tb["head"]], lines[tb["sep"]]]
        for tid in order:
            r = rows[tid]
            if r["dirty"] or r["orig"] is None:
                new_block.append(md_render(r["cells"]))
            elif r.get("pad"):
                new_block.append(r["orig"].rstrip() + " |")
            else:
                new_block.append(r["orig"])
        first = sec["tables"][0]["head"]
        last = sec["tables"][0]["rows"][-1] if sec["tables"][0]["rows"] else sec["tables"][0]["sep"]
        lines[first: last + 1] = new_block

    cl = changes.get("changelog")
    if cl:
        while lines and lines[-1].strip() == "":
            lines.pop()
        if not any(re.match(r"^##\s+Changelog\s*$", l) for l in lines):
            lines += ["", "## Changelog"]
        lines += ["", f"**{cl.get('version', '')} — {cl.get('date', '')} — nguồn: {cl.get('source', '')}**", "",
                  "| ID | Thay đổi | Lý do | AC liên quan |", "|---|---|---|---|"]
        for row in cl.get("rows", []):
            lines.append(md_render([md_escape(x) for x in row]))
        lines.append("")

    Path(out).write_text("\n".join(lines), encoding="utf-8")
    print(f"Đã ghi {out} (file gốc giữ nguyên): "
          f"xoá {stats['delete']}, sửa {stats['update']}, chỉ ghi chú {stats['note']}, thêm {stats['add']}.")
    for w in warnings:
        print("CẢNH BÁO:", w)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 3 and a[0] == "read":
        (md_read if a[1].lower().endswith(".md") else cmd_read)(a[1], a[2])
    elif len(a) == 4 and a[0] == "write":
        (md_write if a[1].lower().endswith(".md") else cmd_write)(a[1], a[2], a[3])
    else:
        print(__doc__)
        sys.exit(1)
