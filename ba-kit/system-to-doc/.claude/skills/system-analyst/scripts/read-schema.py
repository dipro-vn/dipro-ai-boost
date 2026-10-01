#!/usr/bin/env python3
"""Recon database — doc CAU TRUC schema tu SQL dump (MySQL / PostgreSQL) hoac SQLite. CHI DOC.

  python3 read-schema.py --dump schema.sql --out <_internal> --ev-start N
  python3 read-schema.py --sqlite app.db  --out <_internal> --ev-start N

Output (<_internal>/recon/db/):
  tables.csv / columns.csv     header = S.SHEETS 03_DB_Tables / 04_DB_Columns (dan thang vao inventory)
  evidence.csv                 header = S.SHEETS 05_Evidence, 1 dong db-query / table
  schema.json                  ban day du (cot, PK, FK, unique, check, index, comment)
  integrity-checks.sql         SELECT COUNT orphan FK (READ-ONLY, input Bug List nhom Data)
  (sqlite) sqlite-schema.sql   DDL lay tu sqlite_master — Locator tro vao file nay

⚠ Dump co DU LIEU (INSERT/REPLACE/COPY FROM stdin) -> tu choi, exit 3. Can dump schema-only.
⚠ Y NGHIA nghiep vu KHONG suy tu ten cot: Meaning=UNKNOWN tru khi DB co COMMENT (Confidence=Medium).
"""
import argparse
import csv
import datetime
import json
import os
import re
import sys

import inv_schema as S

NAME = r'(?:`[^`]+`|"[^"]+"|\[[^\]]+\]|[\w$]+)'
QNAME = r'%s(?:\s*\.\s*%s)?' % (NAME, NAME)
DROP_SCHEMAS = ("public", "dbo", "main")

MYSQL_TEXT_BYTES = {"tinytext": "255 bytes", "text": "65535 bytes",
                    "mediumtext": "16777215 bytes", "longtext": "4294967295 bytes",
                    "tinyblob": "255 bytes", "blob": "65535 bytes",
                    "mediumblob": "16777215 bytes", "longblob": "4294967295 bytes"}
INT_TYPES = ("tinyint", "smallint", "mediumint", "int", "integer", "bigint", "int2",
             "int4", "int8", "serial", "bigserial", "smallserial", "serial4", "serial8")


# ---------------------------------------------------------------- tach statement
def scan_statements(text):
    """Tach dump thanh [(line, sql)] — bo comment, ton trong quote, $$...$$, DELIMITER."""
    out, buf, i, n = [], [], 0, len(text)
    line, start_line = 1, None
    delim = ";"
    while i < n:
        ch = text[i]
        # DELIMITER (mysql client) — chi o dau dong
        if (i == 0 or text[i - 1] == "\n") and text[i:i + 10].upper() == "DELIMITER ":
            j = text.find("\n", i)
            j = n if j < 0 else j
            delim = text[i + 10:j].strip() or ";"
            i = j
            continue
        if ch == "\n":
            line += 1
            buf.append(ch)
            i += 1
            continue
        if ch == "-" and text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if ch == "#" and not "".join(buf).strip():
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if ch == "/" and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            seg = text[i:j]
            line += seg.count("\n")
            buf.append("\n" * seg.count("\n") + " ")
            i = j
            continue
        if ch in ("'", '"', "`"):
            j = i + 1
            while j < n:
                if text[j] == "\\" and ch == "'":
                    j += 2
                    continue
                if text[j] == ch:
                    if j + 1 < n and text[j + 1] == ch:
                        j += 2
                        continue
                    break
                j += 1
            seg = text[i:j + 1]
            if start_line is None:
                start_line = line
            line += seg.count("\n")
            buf.append(seg)
            i = j + 1
            continue
        if ch == "$":
            m = re.match(r"\$(\w*)\$", text[i:i + 64])
            if m:
                tag = m.group(0)
                j = text.find(tag, i + len(tag))
                j = n if j < 0 else j + len(tag)
                seg = text[i:j]
                line += seg.count("\n")
                buf.append(seg)
                i = j
                continue
        if text.startswith(delim, i):
            sql = "".join(buf).strip()
            if sql:
                out.append((start_line or line, sql))
            buf, start_line = [], None
            i += len(delim)
            continue
        if start_line is None and not ch.isspace():
            start_line = line
        buf.append(ch)
        i += 1
    sql = "".join(buf).strip()
    if sql:
        out.append((start_line or line, sql))
    return out


DATA_STMT = re.compile(r"^(INSERT\s|REPLACE\s+INTO\s|COPY\s[^;]*\sFROM\s+stdin)", re.I)


def data_statements(stmts):
    return [ln for ln, s in stmts if DATA_STMT.match(s)]


# ---------------------------------------------------------------- tien ich
def unq(name):
    name = name.strip()
    if name[:1] in "`\"[" and len(name) > 1:
        return name[1:-1]
    return name


def tname(q):
    parts = [unq(p) for p in re.split(r"\s*\.\s*(?=(?:[`\"\[]|[\w$]))", q.strip())]
    if len(parts) > 1 and parts[0].lower() not in DROP_SCHEMAS:
        return "%s.%s" % (parts[-2], parts[-1])
    return parts[-1]


def split_top(body, sep=","):
    out, depth, cur, q = [], 0, [], None
    for ch in body:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            continue
        if ch in ("'", '"', "`"):
            q = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == sep and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        out.append("".join(cur))
    return [x.strip() for x in out if x.strip()]


def paren_block(s, start):
    """s[start]=='(' -> (noi dung ben trong, vi tri sau ')')."""
    depth, q, i = 0, None, start
    while i < len(s):
        ch = s[i]
        if q:
            if ch == q:
                q = None
        elif ch in ("'", '"', "`"):
            q = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return s[start + 1:i], i + 1
        i += 1
    return s[start + 1:], len(s)


def cols_of(lst):
    return [unq(c.split()[0]) if re.match(r"^[`\"\[\w]", c.strip()) and "(" not in c
            else c.strip() for c in split_top(lst)]


def sql_str(s):
    s = s[1:-1]
    return s.replace("''", "'").replace("\\'", "'").replace("\\n", " ")


def strip_strings(s):
    return re.sub(r"'(?:[^'\\]|\\.|'')*'", "''", s)


STR = r"'(?:[^'\\]|\\.|'')*'"
TYPE_RE = re.compile(r"""^(
    (?:national\s+)?(?:character|char)\s+varying(?:\s*\(\s*\d+\s*\))?
  | bit\s+varying(?:\s*\(\s*\d+\s*\))?
  | double\s+precision
  | (?:timestamp|time)(?:\s*\(\s*\d+\s*\))?(?:\s+with(?:out)?\s+time\s+zone)?
  | [\w$]+(?:\s*\.\s*[\w$]+)?(?:\s*\((?:%s|[^)'])*\))?
)((?:\s*\[\s*\d*\s*\])*)""" % STR, re.I | re.X)


# ---------------------------------------------------------------- parse
def new_table(name, line):
    return {"name": name, "line": line, "columns": [], "pks": [], "fks": [],
            "uniques": [], "checks": [], "indexes": [], "comment": "", "options": ""}


def find_col(t, name):
    for c in t["columns"]:
        if c["name"].lower() == name.lower():
            return c
    return None


def parse_coldef(s, enum_types):
    m = re.match(r"^(%s)\s+(.*)$" % NAME, s, re.S)
    if not m:
        return None
    name, rest = unq(m.group(1)), m.group(2).strip()
    tm = TYPE_RE.match(rest)
    if not tm:
        return None
    ctype = re.sub(r"\s+", " ", tm.group(1).strip()) + re.sub(r"\s+", "", tm.group(2) or "")
    rest = rest[tm.end():]
    bare = strip_strings(rest)
    up = bare.upper()
    col = {"name": name, "type": ctype, "nullable": "YES", "default": "",
           "unsigned": False, "auto": "", "unique": False, "checks": [],
           "comment": "", "on_update": "", "enum": [], "ref": None, "pk": False}
    if re.search(r"\bNOT\s+NULL\b", up):
        col["nullable"] = "NO"
    if re.search(r"\bUNSIGNED\b", up):
        col["unsigned"] = True
    if re.search(r"\bAUTO_?INCREMENT\b", up):
        col["auto"] = "AUTO_INCREMENT"
    if re.search(r"GENERATED\s+(ALWAYS|BY\s+DEFAULT)\s+AS\s+IDENTITY", up):
        col["auto"] = "IDENTITY"
    if re.search(r"\bPRIMARY\s+KEY\b", up):
        col["pk"] = True
        col["nullable"] = "NO"
    if re.search(r"\bUNIQUE\b", up):
        col["unique"] = True
    d = re.search(r"\bDEFAULT\s+(%s(?:::[\w\s]+?(?=\s|$))?|[\w.$]+\s*\((?:[^()]|\([^()]*\))*\)(?:::\w+)?|[^\s,]+)"
                  % STR, rest, re.I)
    if d:
        col["default"] = d.group(1).strip()
    ou = re.search(r"\bON\s+UPDATE\s+(\w+(?:\(\d*\))?)", rest, re.I)
    if ou:
        col["on_update"] = ou.group(1)
    cm = re.search(r"\bCOMMENT\s+(%s)" % STR, rest, re.I)
    if cm:
        col["comment"] = sql_str(cm.group(1)).strip()
    pos = 0
    while True:
        k = re.search(r"\bCHECK\s*\(", rest[pos:], re.I)
        if not k:
            break
        inner, end = paren_block(rest, pos + k.end() - 1)
        col["checks"].append("CHECK (%s)" % re.sub(r"\s+", " ", inner.strip()))
        pos = end
    r = re.search(r"\bREFERENCES\s+(%s)\s*\(\s*(%s)" % (QNAME, NAME), rest, re.I)
    if r:
        col["ref"] = (tname(r.group(1)), unq(r.group(2)))
    em = re.match(r"^(enum|set)\s*\((.*)\)$", ctype, re.I | re.S)
    if em:
        col["enum"] = [sql_str(v) for v in re.findall(STR, em.group(2))]
    elif ctype.lower().split(".")[-1].strip('"') in enum_types:
        col["enum"] = enum_types[ctype.lower().split(".")[-1].strip('"')]
    if col["default"].lower().startswith("nextval("):
        col["auto"] = "SERIAL (sequence)"
    if ctype.lower() in ("serial", "bigserial", "smallserial", "serial4", "serial8"):
        col["auto"] = "SERIAL"
        col["nullable"] = "NO"
    return col


def apply_constraint(t, s):
    """Rang buoc muc bang (trong CREATE hoac ALTER ... ADD)."""
    s = re.sub(r"^CONSTRAINT\s+%s\s+" % NAME, "", s.strip(), flags=re.I)
    up = s.upper()
    if up.startswith("PRIMARY KEY"):
        i = s.index("(")
        inner, _ = paren_block(s, i)
        for c in cols_of(inner):
            if c not in t["pks"]:
                t["pks"].append(c)
        return True
    if up.startswith("FOREIGN KEY"):
        i = s.index("(")
        inner, end = paren_block(s, i)
        m = re.search(r"REFERENCES\s+(%s)\s*\(" % QNAME, s[end:], re.I)
        if m:
            rinner, _ = paren_block(s, end + m.end() - 1)
            for a, b in zip(cols_of(inner), cols_of(rinner)):
                t["fks"].append({"column": a, "ref_table": tname(m.group(1)), "ref_column": b})
        return True
    um = re.match(r"^UNIQUE(?:\s+(?:KEY|INDEX))?(?:\s+(?!\()%s)?\s*(?:USING\s+\w+\s*)?\(" % NAME, s, re.I)
    if um:
        inner, _ = paren_block(s, um.end() - 1)
        t["uniques"].append(cols_of(inner))
        return True
    if up.startswith("CHECK"):
        inner, _ = paren_block(s, s.index("("))
        t["checks"].append(re.sub(r"\s+", " ", inner.strip()))
        return True
    km = re.match(r"^(?:FULLTEXT\s+|SPATIAL\s+)?(?:KEY|INDEX)(?:\s+(?!\()%s)?\s*(?:USING\s+\w+\s*)?\(" % NAME, s, re.I)
    if km:
        inner, _ = paren_block(s, km.end() - 1)
        t["indexes"].append(cols_of(inner))
        return True
    return False


def parse_create(line, sql, enum_types):
    m = re.match(r"CREATE\s+(?:(?:GLOBAL\s+|LOCAL\s+)?(?:TEMP|TEMPORARY)\s+|UNLOGGED\s+)?TABLE\s+"
                 r"(?:IF\s+NOT\s+EXISTS\s+)?(%s)\s*\(" % QNAME, sql, re.I)
    if not m:
        return None
    t = new_table(tname(m.group(1)), line)
    body, end = paren_block(sql, m.end() - 1)
    opts = sql[end:]
    t["options"] = re.sub(r"\s+", " ", re.sub(r"COMMENT\s*=?\s*%s" % STR, "", opts, flags=re.I)).strip()
    cm = re.search(r"\bCOMMENT\s*=?\s*(%s)" % STR, opts, re.I)
    if cm:
        t["comment"] = sql_str(cm.group(1)).strip()
    for d in split_top(body):
        up = d.upper()
        if re.match(r"^(CONSTRAINT\s|PRIMARY\s+KEY|FOREIGN\s+KEY|UNIQUE\b|CHECK\b|KEY\s|INDEX\s|"
                    r"FULLTEXT\s|SPATIAL\s|EXCLUDE\s|LIKE\s)", up):
            apply_constraint(t, d)
            continue
        col = parse_coldef(d, enum_types)
        if col:
            t["columns"].append(col)
    return t


def parse_alter(sql, tables):
    m = re.match(r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(%s)\s+(.*)$" % QNAME, sql, re.I | re.S)
    if not m:
        return
    t = tables.get(tname(m.group(1)))
    if not t:
        return
    for cl in split_top(m.group(2)):
        c = cl.strip()
        up = c.upper()
        if up.startswith("ADD "):
            body = re.sub(r"^ADD\s+(?:COLUMN\s+)?", "", c, flags=re.I)
            if not apply_constraint(t, body) and up.startswith("ADD COLUMN"):
                col = parse_coldef(body, {})
                if col:
                    t["columns"].append(col)
        elif up.startswith(("MODIFY ", "CHANGE ")):
            body = re.sub(r"^(MODIFY|CHANGE)\s+(?:COLUMN\s+)?", "", c, flags=re.I)
            if up.startswith("CHANGE "):
                body = re.sub(r"^%s\s+" % NAME, "", body)
            col = parse_coldef(body, {})
            old = col and find_col(t, col["name"])
            if old:
                for k in ("nullable", "auto", "default", "comment", "unsigned", "type"):
                    if col[k] and col[k] != "YES":
                        old[k] = col[k]
        else:
            am = re.match(r"ALTER\s+(?:COLUMN\s+)?(%s)\s+(.*)$" % NAME, c, re.I | re.S)
            if not am:
                continue
            col = find_col(t, unq(am.group(1)))
            if not col:
                continue
            act = am.group(2)
            dm = re.match(r"SET\s+DEFAULT\s+(.*)$", act, re.I | re.S)
            if dm:
                col["default"] = dm.group(1).strip()
                if col["default"].lower().startswith("nextval("):
                    col["auto"] = "SERIAL (sequence)"
            elif re.match(r"SET\s+NOT\s+NULL", act, re.I):
                col["nullable"] = "NO"
            elif re.search(r"ADD\s+GENERATED\s+.*AS\s+IDENTITY", act, re.I | re.S):
                col["auto"] = "IDENTITY"


def parse_dump(text):
    stmts = scan_statements(text)
    bad = data_statements(stmts)
    if bad:
        return None, bad, None
    dialect = "mysql" if re.search(r"`|\bENGINE\s*=", text) else (
        "postgresql" if re.search(r"pg_dump|::regclass|SET\s+search_path|\bpublic\.", text, re.I)
        else "sql")
    enum_types, tables = {}, {}
    for ln, sql in stmts:
        m = re.match(r"CREATE\s+TYPE\s+(%s)\s+AS\s+ENUM\s*\((.*)\)\s*$" % QNAME, sql, re.I | re.S)
        if m:
            enum_types[tname(m.group(1)).split(".")[-1].lower()] = [sql_str(v) for v in re.findall(STR, m.group(2))]
    for ln, sql in stmts:
        if re.match(r"CREATE\s+(?:\w+\s+)*TABLE\s", sql, re.I) and not re.search(r"\bAS\s+SELECT\b", sql[:400], re.I):
            t = parse_create(ln, sql, enum_types)
            if t:
                tables[t["name"]] = t
    for ln, sql in stmts:
        up = sql[:40].upper()
        if up.startswith("ALTER TABLE"):
            parse_alter(sql, tables)
        elif re.match(r"CREATE\s+UNIQUE\s+INDEX", sql, re.I):
            m = re.search(r"\bON\s+(?:ONLY\s+)?(%s)\s*(?:USING\s+\w+\s*)?\(" % QNAME, sql, re.I)
            if m and tname(m.group(1)) in tables:
                inner, _ = paren_block(sql, m.end() - 1)
                tables[tname(m.group(1))]["uniques"].append(cols_of(inner))
        elif re.match(r"CREATE\s+INDEX", sql, re.I):
            m = re.search(r"\bON\s+(?:ONLY\s+)?(%s)\s*(?:USING\s+\w+\s*)?\(" % QNAME, sql, re.I)
            if m and tname(m.group(1)) in tables:
                inner, _ = paren_block(sql, m.end() - 1)
                tables[tname(m.group(1))]["indexes"].append(cols_of(inner))
        elif up.startswith("COMMENT ON"):
            m = re.match(r"COMMENT\s+ON\s+(TABLE|COLUMN)\s+(%s(?:\s*\.\s*%s){0,2})\s+IS\s+(%s)" % (NAME, NAME, STR),
                         sql, re.I | re.S)
            if not m:
                continue
            parts = [unq(p) for p in re.findall(NAME, m.group(2))]
            txt = sql_str(m.group(3)).strip()
            if m.group(1).upper() == "TABLE":
                t = tables.get(tname(".".join(parts)))
                if t:
                    t["comment"] = txt
            elif len(parts) >= 2:
                t = tables.get(tname(".".join(parts[:-1])))
                col = t and find_col(t, parts[-1])
                if col:
                    col["comment"] = txt
    # gom FK/PK inline
    for t in tables.values():
        for c in t["columns"]:
            if c["pk"] and c["name"] not in t["pks"]:
                t["pks"].append(c["name"])
            if c["ref"] and not any(f["column"] == c["name"] for f in t["fks"]):
                t["fks"].append({"column": c["name"], "ref_table": c["ref"][0], "ref_column": c["ref"][1]})
        for c in t["columns"]:
            if c["name"] in t["pks"]:
                c["nullable"] = "NO"
    return tables, [], dialect


def parse_sqlite(path, outdir):
    """Chi doc metadata (sqlite_master.sql + PRAGMA). KHONG SELECT du lieu dong."""
    import sqlite3
    con = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    ddl = ["-- DDL trich tu sqlite_master cua %s (khong co du lieu)" % os.path.basename(path)]
    for typ, name, sql in con.execute(
            "SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL "
            "AND name NOT LIKE 'sqlite_%' ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name"):
        ddl.append(sql.strip().rstrip(";") + ";")
    text = "\n\n".join(ddl) + "\n"
    schema_path = os.path.join(outdir, "sqlite-schema.sql")
    open(schema_path, "w", encoding="utf8").write(text)
    tables, _, _ = parse_dump(text)
    for name, t in tables.items():
        try:
            for cid, cname, ctype, notnull, dflt, pk in con.execute('PRAGMA table_info("%s")' % name):
                c = find_col(t, cname)
                if c and notnull:
                    c["nullable"] = "NO"
                if pk and cname not in t["pks"]:
                    t["pks"].append(cname)
            for r in con.execute('PRAGMA foreign_key_list("%s")' % name):
                if not any(f["column"] == r[3] for f in t["fks"]):
                    t["fks"].append({"column": r[3], "ref_table": r[2], "ref_column": r[4]})
        except Exception:
            pass
    con.close()
    return tables, schema_path, "sqlite"


# ---------------------------------------------------------------- suy ra Format / Max Length / Constraint
def base_type(ctype):
    return re.split(r"[\s(\[]", ctype.strip().lower(), maxsplit=1)[0].split(".")[-1].strip('"')


def max_length(c, dialect):
    t = c["type"].lower()
    m = re.match(r"^(?:national\s+)?(?:n?varchar2?|n?char|character(?:\s+varying)?|char\s+varying|"
                 r"varbinary|binary|bit(?:\s+varying)?|varbit|bpchar)\s*\(\s*(\d+)\s*\)", t)
    if m:
        return m.group(1)
    b = base_type(t)
    if b in MYSQL_TEXT_BYTES and dialect in ("mysql", "sql"):
        return MYSQL_TEXT_BYTES[b]
    if b in ("text", "varchar", "character", "bytea") and dialect in ("postgresql", "sqlite"):
        return "unlimited"
    return "—"


def fmt_of(c):
    t = c["type"].lower()
    b = base_type(t)
    if t.endswith("]"):
        return "array"
    if c["enum"]:
        return "set" if b == "set" else "enum"
    m = re.match(r"^(?:decimal|numeric|dec|fixed|number)\s*\(\s*(\d+)\s*(?:,\s*(\d+))?\s*\)", t)
    if m:
        return "%s,%s" % (m.group(1), m.group(2) or "0")
    if re.match(r"^(tinyint\s*\(\s*1\s*\)|bit\s*\(\s*1\s*\)|bool|boolean)", t) or b in ("bool", "boolean"):
        return "bool"
    frac = re.search(r"\(\s*(\d+)\s*\)", t)
    fs = "." + "f" * int(frac.group(1)) if frac and int(frac.group(1)) > 0 else ""
    if b == "date":
        return "YYYY-MM-DD"
    if b in ("datetime", "timestamp", "timestamptz", "smalldatetime", "datetime2"):
        tz = "+TZ" if ("with time zone" in t or b == "timestamptz") else ""
        return "YYYY-MM-DD HH:MM:SS%s%s" % (fs, tz)
    if b in ("time", "timetz"):
        return "HH:MM:SS%s%s" % (fs, "+TZ" if ("with time zone" in t or b == "timetz") else "")
    if b == "year":
        return "YYYY"
    if b == "interval":
        return "interval"
    if b in ("json", "jsonb"):
        return "json"
    if b in ("uuid", "uniqueidentifier"):
        return "uuid (8-4-4-4-12)"
    if b in INT_TYPES:
        return "integer"
    if b in ("decimal", "numeric", "dec", "money"):
        return "decimal"
    if b in ("float", "double", "real", "float4", "float8"):
        return "float"
    if b in ("blob", "tinyblob", "mediumblob", "longblob", "bytea", "binary", "varbinary"):
        return "binary"
    if b in ("inet", "cidr", "macaddr"):
        return b
    if b in ("char", "character", "varchar", "nvarchar", "nchar", "text", "tinytext",
             "mediumtext", "longtext", "string", "clob", "citext", "bpchar", "national"):
        return "text"
    return b or "UNKNOWN"


def constraint_of(c, t):
    out = []
    if c["unsigned"]:
        out.append("UNSIGNED")
    if c["auto"]:
        out.append(c["auto"])
    if c["unique"] or any(u == [c["name"]] for u in t["uniques"]):
        out.append("UNIQUE")
    for u in t["uniques"]:
        if len(u) > 1 and c["name"] in u:
            out.append("UNIQUE(%s)" % ",".join(u))
    if c["enum"]:
        out.append("%s: %s" % ("SET" if base_type(c["type"]) == "set" else "ENUM", " | ".join(c["enum"])))
    out += c["checks"]
    for ck in t["checks"]:
        if re.search(r"\b%s\b" % re.escape(c["name"]), ck):
            out.append("CHECK (%s)" % ck)
    if c["on_update"]:
        out.append("ON UPDATE %s" % c["on_update"])
    seen, res = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return "; ".join(res) or "—"


# ---------------------------------------------------------------- main
def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    ap.add_argument("--sqlite")
    ap.add_argument("--out", required=True, help="thu muc _internal (output vao <out>/recon/db/)")
    ap.add_argument("--ev-start", type=int, default=1)
    a = ap.parse_args()
    if not a.dump and not a.sqlite:
        print("Can --dump hoac --sqlite", file=sys.stderr)
        return 1

    outdir = os.path.join(a.out, "recon", "db")
    if a.dump:
        text = open(a.dump, encoding="utf8", errors="ignore").read()
        tables, bad, dialect = parse_dump(text)
        if tables is None:
            print("TU CHOI: dump co DU LIEU (%d statement INSERT/REPLACE/COPY, dong dau: L%s). "
                  "Khong doc, khong in noi dung dong nao.\n"
                  "Hay xin khach dump CHI SCHEMA:\n"
                  "  MySQL:      mysqldump --no-data <db> > schema.sql\n"
                  "  PostgreSQL: pg_dump --schema-only <db> > schema.sql"
                  % (len(bad), bad[0]), file=sys.stderr)
            return 3
        src = os.path.basename(a.dump)
        os.makedirs(outdir, exist_ok=True)
    else:
        os.makedirs(outdir, exist_ok=True)
        tables, schema_path, dialect = parse_sqlite(a.sqlite, outdir)
        src = os.path.basename(schema_path)

    today = datetime.date.today().isoformat()
    ev, ev_rows = a.ev_start, []
    for name in sorted(tables):
        t = tables[name]
        t["ev"] = "EV-%04d" % ev
        ev_rows.append([t["ev"], "db-query", "schema:%s#L%d" % (src, t["line"]), today, "—",
                        "recon/db/schema.json", "CREATE TABLE %s (cau truc, khong co du lieu)" % name])
        ev += 1

    trows, crows = [], []
    for name in sorted(tables):
        t = tables[name]
        fkmap = {f["column"]: "%s.%s" % (f["ref_table"], f["ref_column"]) for f in t["fks"]}
        fk = "; ".join("%s->%s.%s" % (f["column"], f["ref_table"], f["ref_column"]) for f in t["fks"]) or "—"
        imp = list(t["pks"]) + [f["column"] for f in t["fks"]]
        imp += [c["name"] for c in t["columns"] if constraint_of(c, t) != "—"]
        imp = list(dict.fromkeys(imp))[:8] or [c["name"] for c in t["columns"][:4]]
        note = "Purpose/Related Function dien sau khi doi chieu code (code-ref)"
        if t["options"]:
            note += " · " + t["options"][:120]
        trows.append([name, t["comment"] or S.UNKNOWN, ",".join(t["pks"]) or "—", fk,
                      ",".join(imp) or "—", S.UNKNOWN, S.UNKNOWN, t["ev"],
                      "Medium" if t["comment"] else "Low", note])
        for c in t["columns"]:
            crows.append([name, c["name"], c["type"],
                          "Yes" if c["name"] in t["pks"] else "No",
                          fkmap.get(c["name"], "—"), c["nullable"],
                          c["default"] or "—", max_length(c, dialect), fmt_of(c),
                          constraint_of(c, t), c["comment"] or S.UNKNOWN, S.UNKNOWN,
                          t["ev"], "Medium" if c["comment"] else "Low"])
            c["max_length"], c["format"], c["constraint"] = crows[-1][7:10]

    write_csv(os.path.join(outdir, "tables.csv"), S.SHEETS["03_DB_Tables"], trows)
    write_csv(os.path.join(outdir, "columns.csv"), S.SHEETS["04_DB_Columns"], crows)
    write_csv(os.path.join(outdir, "evidence.csv"), S.SHEETS["05_Evidence"], ev_rows)

    lines = ["-- Kiem tinh toan ven du lieu — input cho Bug List nhom 'Data'",
             "-- CHI SELECT COUNT, chay READ-ONLY. Moi dong tra ve n > 0 la mot ung vien bug.", ""]
    for name in sorted(tables):
        for f in tables[name]["fks"]:
            lines.append(
                "SELECT '%s.%s orphan' AS issue, COUNT(*) AS n FROM %s c "
                "LEFT JOIN %s p ON c.%s = p.%s WHERE c.%s IS NOT NULL AND p.%s IS NULL;"
                % (name, f["column"], name, f["ref_table"], f["column"],
                   f["ref_column"], f["column"], f["ref_column"]))
    open(os.path.join(outdir, "integrity-checks.sql"), "w", encoding="utf8").write("\n".join(lines) + "\n")

    json.dump({"source": src, "dialect": dialect, "tables": tables},
              open(os.path.join(outdir, "schema.json"), "w", encoding="utf8"),
              indent=2, ensure_ascii=False, default=list)

    print(json.dumps({"dialect": dialect, "tables": len(tables), "columns": len(crows),
                      "fks": sum(len(t["fks"]) for t in tables.values()),
                      "commented_columns": sum(1 for r in crows if r[10] != S.UNKNOWN),
                      "evidence": len(ev_rows), "next_ev": ev, "out": outdir}, indent=2))
    print("\nLUU Y: Purpose/Meaning = UNKNOWN tru khi DB co COMMENT. Dien bang bang chung code-ref, "
          "KHONG doan tu ten cot. Est Rows = UNKNOWN (khong dem dong du lieu).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
