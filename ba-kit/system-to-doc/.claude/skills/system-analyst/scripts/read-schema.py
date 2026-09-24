#!/usr/bin/env python3
"""Recon database — doc schema tu SQL dump hoac SQLite. CHI DOC.

  python3 read-schema.py --dump schema.sql --out ./recon
  python3 read-schema.py --sqlite app.db  --out ./recon

Output:
  recon/db/tables.csv          dan thang vao sheet 03_DB_Tables
  recon/db/columns.csv         dan thang vao sheet 04_DB_Columns
  recon/db/schema.json         ban day du
  recon/db/integrity-checks.sql  cau SQL kiem orphan FK (input cho Bug List nhom Data)

⚠ Script chi doc duoc CAU TRUC. Y NGHIA nghiep vu cua cot KHONG suy ra tu ten cot —
phai co code doc/ghi cot do (EV loai code-ref) moi duoc ghi Confidence=High.
"""
import argparse
import csv
import json
import os
import re
import sys

CREATE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?(\w+)[`\"\]]?\s*\((.*?)\)\s*(?:ENGINE|;)",
                    re.I | re.S)
COLDEF = re.compile(r"^\s*[`\"\[]?(\w+)[`\"\]]?\s+([A-Za-z]+(?:\s*\([^)]*\))?)(.*)$")
FK = re.compile(r"FOREIGN\s+KEY\s*\(\s*[`\"\[]?(\w+)[`\"\]]?\s*\)\s*REFERENCES\s+[`\"\[]?(\w+)[`\"\]]?\s*\(\s*[`\"\[]?(\w+)",
                re.I)
PK = re.compile(r"PRIMARY\s+KEY\s*\(\s*(.+?)\s*\)", re.I)


def split_defs(body):
    out, depth, cur = [], 0, ""
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def parse_dump(text):
    tables = {}
    for name, body in CREATE.findall(text):
        cols, fks, pks = [], [], []
        for d in split_defs(body):
            s = d.strip()
            if not s:
                continue
            up = s.upper()
            if up.startswith(("PRIMARY KEY", "CONSTRAINT", "FOREIGN KEY", "KEY ",
                              "UNIQUE KEY", "INDEX ")):
                m = FK.search(s)
                if m:
                    fks.append({"column": m.group(1), "ref_table": m.group(2),
                                "ref_column": m.group(3)})
                m = PK.search(s)
                if m and up.startswith("PRIMARY KEY"):
                    pks += [c.strip(" `\"[]") for c in m.group(1).split(",")]
                continue
            m = COLDEF.match(s)
            if not m:
                continue
            rest = m.group(3).upper()
            if "PRIMARY KEY" in rest:
                pks.append(m.group(1))
            cols.append({
                "name": m.group(1), "type": m.group(2).strip(),
                "nullable": "NO" if "NOT NULL" in rest else "YES",
                "default": (re.search(r"DEFAULT\s+('[^']*'|\S+)", rest).group(1)
                            if "DEFAULT" in rest else ""),
            })
        tables[name] = {"columns": cols, "fks": fks, "pks": pks}
    return tables


def parse_sqlite(path):
    import sqlite3
    con = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    tables = {}
    for (name,) in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        cols, pks = [], []
        for cid, cname, ctype, notnull, dflt, pk in con.execute("PRAGMA table_info(%s)" % name):
            cols.append({"name": cname, "type": ctype,
                         "nullable": "NO" if notnull else "YES",
                         "default": "" if dflt is None else str(dflt)})
            if pk:
                pks.append(cname)
        fks = [{"column": r[3], "ref_table": r[2], "ref_column": r[4]}
               for r in con.execute("PRAGMA foreign_key_list(%s)" % name)]
        try:
            n = con.execute("SELECT COUNT(*) FROM %s" % name).fetchone()[0]
        except Exception:
            n = ""
        tables[name] = {"columns": cols, "fks": fks, "pks": pks, "rows": n}
    con.close()
    return tables


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    ap.add_argument("--sqlite")
    ap.add_argument("--out", default="./recon")
    a = ap.parse_args()

    if not a.dump and not a.sqlite:
        print("Can --dump hoac --sqlite", file=sys.stderr)
        return 1
    if a.dump:
        tables = parse_dump(open(a.dump, encoding="utf8", errors="ignore").read())
    else:
        tables = parse_sqlite(a.sqlite)

    outdir = os.path.join(a.out, "db")
    os.makedirs(outdir, exist_ok=True)

    with open(os.path.join(outdir, "tables.csv"), "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["Table", "Purpose", "PK", "FK", "Important Columns", "Est Rows",
                    "Related Function IDs", "Evidence", "Confidence", "Note"])
        for name, t in sorted(tables.items()):
            fk = "; ".join("%s->%s.%s" % (f["column"], f["ref_table"], f["ref_column"])
                           for f in t["fks"]) or "—"
            w.writerow([name, "UNKNOWN", ",".join(t["pks"]) or "—", fk,
                        ",".join(c["name"] for c in t["columns"][:6]),
                        t.get("rows", ""), "UNKNOWN", "UNKNOWN", "Low",
                        "Purpose/Related Function phai dien tay sau khi doi chieu code"])

    with open(os.path.join(outdir, "columns.csv"), "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["Table", "Column", "Type", "PK", "FK", "Nullable", "Default",
                    "Meaning", "Used By", "Evidence", "Confidence"])
        for name, t in sorted(tables.items()):
            fkmap = {f["column"]: "%s.%s" % (f["ref_table"], f["ref_column"]) for f in t["fks"]}
            for c in t["columns"]:
                w.writerow([name, c["name"], c["type"],
                            "Yes" if c["name"] in t["pks"] else "No",
                            fkmap.get(c["name"], "—"), c["nullable"],
                            c["default"] or "—", "UNKNOWN", "UNKNOWN", "", "Low"])

    lines = ["-- Kiem tinh toan ven du lieu — input cho Bug List nhom 'Data'",
             "-- Chay READ-ONLY. Moi dong tra ve > 0 la mot ung vien bug.", ""]
    for name, t in sorted(tables.items()):
        for f in t["fks"]:
            lines.append(
                "SELECT '%s.%s orphan' AS issue, COUNT(*) AS n FROM %s c "
                "LEFT JOIN %s p ON c.%s = p.%s WHERE c.%s IS NOT NULL AND p.%s IS NULL;"
                % (name, f["column"], name, f["ref_table"], f["column"],
                   f["ref_column"], f["column"], f["ref_column"]))
    open(os.path.join(outdir, "integrity-checks.sql"), "w", encoding="utf8").write(
        "\n".join(lines) + "\n")

    json.dump(tables, open(os.path.join(outdir, "schema.json"), "w", encoding="utf8"),
              indent=2, ensure_ascii=False)

    print(json.dumps({"tables": len(tables),
                      "columns": sum(len(t["columns"]) for t in tables.values()),
                      "fks": sum(len(t["fks"]) for t in tables.values()),
                      "out": outdir}, indent=2))
    print("\nLUU Y: cot Purpose/Meaning/Related Function deu la UNKNOWN. "
          "Dien chung bang bang chung code-ref, KHONG doan tu ten cot.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
