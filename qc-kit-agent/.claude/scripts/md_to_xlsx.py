#!/usr/bin/env python3
"""
Convert markdown artifact to Excel.
- Each ## section -> 1 sheet
- Tables -> formatted with bold header, freeze row, wrap text
- Free text -> plain cell above table
- <br> -> actual newline in cell
"""

import sys
import re
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


def parse_markdown(content):
    sections = []
    current = {"heading": None, "lines": []}

    for line in content.split("\n"):
        m = re.match(r"^#{1,3}\s+(.+)$", line)
        if m:
            if current["heading"] or current["lines"]:
                sections.append(current)
            current = {"heading": m.group(1).strip(), "lines": []}
        else:
            current["lines"].append(line)

    if current["heading"] or current["lines"]:
        sections.append(current)

    return sections


def is_table_row(line):
    return line.strip().startswith("|") and line.strip().endswith("|")


def is_separator_row(line):
    return bool(re.match(r"^\|[-:\s|]+\|$", line.strip()))


def parse_table(table_lines):
    headers = []
    rows = []
    for line in table_lines:
        if is_separator_row(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not headers:
            headers = cells
        else:
            rows.append(cells)
    return headers, rows


def extract_blocks(lines):
    blocks = []
    i = 0
    text_buffer = []

    while i < len(lines):
        line = lines[i]
        if is_table_row(line):
            if text_buffer:
                text = "\n".join(text_buffer).strip()
                if text:
                    blocks.append({"type": "text", "content": text})
                text_buffer = []
            table_lines = []
            while i < len(lines) and is_table_row(lines[i]):
                table_lines.append(lines[i])
                i += 1
            headers, rows = parse_table(table_lines)
            if headers:
                blocks.append({"type": "table", "headers": headers, "rows": rows})
        else:
            text_buffer.append(line)
            i += 1

    if text_buffer:
        text = "\n".join(text_buffer).strip()
        if text:
            blocks.append({"type": "text", "content": text})

    return blocks


def convert_br(text):
    return re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)


def sanitize_sheet_name(name):
    name = re.sub(r"[\\/*?:\[\]]", "", name)
    return name[:31] or "Sheet"


def write_xlsx(sections, output_path):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
    HEADER_FILL = PatternFill(start_color="46BDC6", end_color="46BDC6", fill_type="solid")
    HEADER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
    CELL_ALIGN = Alignment(vertical="top", wrap_text=True)
    TEXT_ALIGN = Alignment(vertical="top", wrap_text=True)
    THIN = Side(style="thin", color="CCCCCC")
    BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

    for section in sections:
        sheet_name = sanitize_sheet_name(section["heading"] or "Sheet")
        # Avoid duplicate sheet names
        base = sheet_name
        count = 1
        existing = [s.title for s in wb.worksheets]
        while sheet_name in existing:
            sheet_name = f"{base[:28]}_{count}"
            count += 1

        ws = wb.create_sheet(title=sheet_name)
        ws.sheet_view.showGridLines = True
        row = 1

        blocks = extract_blocks(section["lines"])

        for block in blocks:
            if block["type"] == "text":
                cell = ws.cell(row=row, column=1, value=block["content"])
                cell.alignment = TEXT_ALIGN
                cell.font = Font(size=10, italic=True, color="555555")
                row += 2

            elif block["type"] == "table":
                headers = block["headers"]
                rows = block["rows"]

                # Header row
                for col, h in enumerate(headers, 1):
                    cell = ws.cell(row=row, column=col, value=convert_br(h))
                    cell.font = HEADER_FONT
                    cell.fill = HEADER_FILL
                    cell.alignment = HEADER_ALIGN
                    cell.border = BORDER

                ws.freeze_panes = ws.cell(row=row + 1, column=1)
                ws.row_dimensions[row].height = 24
                row += 1

                # Data rows
                for r_data in rows:
                    for col, val in enumerate(r_data, 1):
                        cell = ws.cell(row=row, column=col, value=convert_br(val))
                        cell.alignment = CELL_ALIGN
                        cell.border = BORDER
                    row += 1

                row += 1  # blank row after table

        # Auto column width (capped)
        for col_cells in ws.columns:
            max_w = 10
            for cell in col_cells:
                if cell.value:
                    for part in str(cell.value).split("\n"):
                        max_w = max(max_w, len(part) * 1.1)
            col_letter = get_column_letter(col_cells[0].column)
            ws.column_dimensions[col_letter].width = min(max_w, 55)

    wb.save(output_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: md_to_xlsx.py <input.md>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    output_path = input_path.with_suffix(".xlsx")
    content = input_path.read_text(encoding="utf-8")
    sections = parse_markdown(content)
    write_xlsx(sections, output_path)
    print(f"Done: {output_path}")


if __name__ == "__main__":
    main()
