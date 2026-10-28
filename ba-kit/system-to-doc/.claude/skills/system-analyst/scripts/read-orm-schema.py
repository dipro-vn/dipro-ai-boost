#!/usr/bin/env python3
"""Recon DB TU CODE — doc TOAN BO schema ORM + migration trong 1 repo. CHI DOC.

  python3 read-orm-schema.py <repo> --repo-id REPO-01 --out <_internal> --ev-start N

Doc:
  Prisma   : **/*.prisma (model / enum / @@map / @map / @id / @@id / @unique / @default / @db.* / @relation)
             + prisma/migrations/*/migration.sql (replay theo thu tu)
  TypeORM  : class @Entity (+ cot ke thua tu class cha) @Column / @Primary*Column / @*DateColumn /
             @ManyToOne·@OneToOne + @JoinColumn; migration class (up(): queryRunner.query SQL,
             createTable / addColumn(s) / dropColumn / dropTable / renameColumn)
  SQL thuan: *.sql nam duoi thu muc migration(s) (bo file *down*), replay theo ten file
  shortcut: Sequelize / Knex / Django / Rails migration chua doc -> dung read-schema.py (dump) neu co.

Output -> <_internal>/recon/db-code/<REPO-xx>/
  tables.csv / columns.csv   header = 03_DB_Tables / 04_DB_Columns (cung format read-schema.py)
  evidence.csv               1 dong code-ref / bang (dinh nghia model / entity / CREATE TABLE)
  code-schema.csv            Table, Column, Origin, Source — DAU VAO gate schema (verify-db-doc --code-schema)
  schema.json · skipped.json (ten file bi bo qua vi ten nhay cam — khong doc noi dung)
stdout: JSON {tables, columns, models, migrations, mismatches, commit, next_ev, out}

Migration chi lay cau lenh DDL; INSERT/UPDATE du lieu trong migration bi bo qua, khong in ra.
Meaning = "Cần xác nhận" tru khi co doc comment (/// Prisma, comment: TypeORM, COMMENT ON) -> Confidence Medium.
"""
import argparse
import csv
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inv_schema as S  # noqa: E402


def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RS = _load("read_schema", "read-schema.py")
SR = _load("scan_repo", "scan-repo.py")

CODE_SCHEMA_COLS = ["Table", "Column", "Origin", "Source"]
MIG_DIR_RX = re.compile(r"(?:^|/)(?:migrations?|migrate|db/migrate|sql)(?:/|$)", re.I)
PRISMA_SCALAR = {"String", "Int", "BigInt", "Float", "Decimal", "Boolean", "DateTime", "Json", "Bytes"}
PRISMA_SQL = {
    "postgresql": {"String": "text", "Int": "integer", "BigInt": "bigint", "Float": "double precision",
                   "Decimal": "decimal(65,30)", "Boolean": "boolean", "DateTime": "timestamp(3)",
                   "Json": "jsonb", "Bytes": "bytea"},
    "mysql": {"String": "varchar(191)", "Int": "int", "BigInt": "bigint", "Float": "double",
              "Decimal": "decimal(65,30)", "Boolean": "tinyint(1)", "DateTime": "datetime(3)",
              "Json": "json", "Bytes": "longblob"},
}
TS_SQL = {"string": "varchar", "number": "integer", "boolean": "boolean", "Date": "timestamp"}


def new_col(name, ctype, nullable="YES"):
    return {"name": name, "type": ctype, "nullable": nullable, "default": "", "unsigned": False,
            "auto": "", "unique": False, "checks": [], "comment": "", "on_update": "", "enum": [],
            "ref": None, "pk": False}


class Sch:
    """Bang dang dung (format read-schema) + nguon cua tung bang / cot."""
    def __init__(self):
        self.tables = {}
        self.src = {}          # (table, col|None) -> {origin: locator}

    def mark(self, table, col, origin, loc):
        self.src.setdefault((table, col), {}).setdefault(origin, loc)

    def table(self, name, line=0):
        if name not in self.tables:
            self.tables[name] = RS.new_table(name, line)
        return self.tables[name]


# ---------------------------------------------------------------- file
def walk(root):
    """-> (files {rel: text}, skipped [rel]). .sql chi nhan khi nam trong thu muc migration."""
    files, skipped = {}, []
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SR.SKIP_DIRS)
        for fn in sorted(fns):
            rel = os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/")
            low = fn.lower()
            is_mig_sql = low.endswith(".sql") and MIG_DIR_RX.search(rel) and "down" not in low
            if not (low.endswith((".prisma", ".ts", ".js")) or is_mig_sql) or SR.is_test(rel):
                continue
            why = SR.sensitive_reason(rel)
            if why and not (is_mig_sql and why == "key/cert/db-dump"):
                skipped.append({"path": rel, "reason": why})
                continue
            fp = os.path.join(dp, fn)
            if os.path.getsize(fp) > SR.MAX_BYTES:
                skipped.append({"path": rel, "reason": "too-large"})
                continue
            text = open(fp, encoding="utf8", errors="ignore").read()
            if low.endswith((".ts", ".js")) and not re.search(r"@Entity\b|MigrationInterface|@\w*Column\(", text):
                continue
            files[rel] = text
    return files, skipped


def lineno(text, pos):
    return text.count("\n", 0, pos) + 1


# ---------------------------------------------------------------- SQL migration replay
def apply_sql(sch, sql_text, loc_of, origin, enums):
    """Replay DDL tren sch (CREATE / ALTER / DROP / RENAME / INDEX / COMMENT). loc_of(line) -> locator."""
    for ln, sql in RS.scan_statements(sql_text):
        up = sql.lstrip()[:60].upper()
        m = re.match(r"CREATE\s+TYPE\s+(%s)\s+AS\s+ENUM\s*\((.*)\)\s*$" % RS.QNAME, sql, re.I | re.S)
        if m:
            enums[RS.tname(m.group(1)).split(".")[-1].lower()] = [RS.sql_str(v) for v in re.findall(RS.STR, m.group(2))]
            continue
        m = re.match(r"ALTER\s+TYPE\s+(%s)\s+ADD\s+VALUE\s+(?:IF\s+NOT\s+EXISTS\s+)?(%s)" % (RS.QNAME, RS.STR), sql, re.I)
        if m:
            enums.setdefault(RS.tname(m.group(1)).split(".")[-1].lower(), []).append(RS.sql_str(m.group(2)))
            continue
        if re.match(r"CREATE\s+(?:\w+\s+)*TABLE\s", sql, re.I):
            t = RS.parse_create(ln, sql, enums)
            if t:
                sch.tables[t["name"]] = t
                sch.mark(t["name"], None, origin, loc_of(ln))
                for c in t["columns"]:
                    sch.mark(t["name"], c["name"], origin, loc_of(ln))
            continue
        m = re.match(r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(.+?)(?:\s+CASCADE|\s+RESTRICT)?\s*$", sql, re.I | re.S)
        if m:
            for q in RS.split_top(m.group(1)):
                sch.tables.pop(RS.tname(q), None)
            continue
        m = re.match(r"(?:ALTER\s+TABLE|RENAME\s+TABLE)\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(%s)\s+(?:RENAME\s+)?TO\s+(%s)\s*$"
                     % (RS.QNAME, RS.QNAME), sql, re.I)
        if m and RS.tname(m.group(1)) in sch.tables:
            old, new = RS.tname(m.group(1)), RS.tname(m.group(2))
            t = sch.tables.pop(old)
            t["name"] = new
            sch.tables[new] = t
            for (tb, c), v in list(sch.src.items()):
                if tb == old:
                    sch.src[(new, c)] = v
            continue
        if up.startswith("ALTER TABLE"):
            alter(sch, ln, sql, loc_of, origin)
        elif re.match(r"CREATE\s+(UNIQUE\s+)?INDEX", sql, re.I):
            m = re.search(r"\bON\s+(?:ONLY\s+)?(%s)\s*(?:USING\s+\w+\s*)?\(" % RS.QNAME, sql, re.I)
            if m and RS.tname(m.group(1)) in sch.tables:
                inner, _ = RS.paren_block(sql, m.end() - 1)
                key = "uniques" if re.match(r"CREATE\s+UNIQUE", sql, re.I) else "indexes"
                sch.tables[RS.tname(m.group(1))][key].append(RS.cols_of(inner))
        elif up.startswith("COMMENT ON"):
            RS_comment(sch, sql)


def RS_comment(sch, sql):
    m = re.match(r"COMMENT\s+ON\s+(TABLE|COLUMN)\s+(%s(?:\s*\.\s*%s){0,2})\s+IS\s+(%s)" % (RS.NAME, RS.NAME, RS.STR),
                 sql, re.I | re.S)
    if not m:
        return
    parts = [RS.unq(p) for p in re.findall(RS.NAME, m.group(2))]
    txt = RS.sql_str(m.group(3)).strip()
    if m.group(1).upper() == "TABLE":
        t = sch.tables.get(RS.tname(".".join(parts)))
        if t:
            t["comment"] = txt
    elif len(parts) >= 2:
        t = sch.tables.get(RS.tname(".".join(parts[:-1])))
        c = t and RS.find_col(t, parts[-1])
        if c:
            c["comment"] = txt


def alter(sch, ln, sql, loc_of, origin):
    m = re.match(r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(%s)\s+(.*)$" % RS.QNAME, sql, re.I | re.S)
    if not m:
        return
    name = RS.tname(m.group(1))
    t = sch.tables.get(name)
    if not t:
        return
    for cl in RS.split_top(m.group(2)):
        c, up = cl.strip(), cl.strip().upper()
        dm = re.match(r"DROP\s+(?:COLUMN\s+)?(?:IF\s+EXISTS\s+)?(%s)\s*(?:CASCADE|RESTRICT)?$" % RS.NAME, c, re.I)
        if dm and not re.match(r"DROP\s+(CONSTRAINT|INDEX|KEY|PRIMARY|FOREIGN|DEFAULT)\b", up):
            col = RS.unq(dm.group(1))
            t["columns"] = [x for x in t["columns"] if x["name"].lower() != col.lower()]
            continue
        rm = re.match(r"RENAME\s+(?:COLUMN\s+)?(%s)\s+TO\s+(%s)$" % (RS.NAME, RS.NAME), c, re.I)
        if rm:
            col = RS.find_col(t, RS.unq(rm.group(1)))
            if col:
                col["name"] = RS.unq(rm.group(2))
                sch.mark(name, col["name"], origin, loc_of(ln))
            continue
        am = re.match(r"ALTER\s+(?:COLUMN\s+)?(%s)\s+(DROP\s+NOT\s+NULL|(?:SET\s+DATA\s+)?TYPE\s+(.+))$" % RS.NAME, c, re.I | re.S)
        if am:
            col = RS.find_col(t, RS.unq(am.group(1)))
            if col and am.group(3):
                col["type"] = re.split(r"\s+USING\s+", am.group(3).strip(), flags=re.I)[0]
            elif col:
                col["nullable"] = "YES"
            continue
        if up.startswith("ADD ") and not re.match(r"ADD\s+(COLUMN|CONSTRAINT|PRIMARY|FOREIGN|UNIQUE|CHECK|INDEX|KEY)\b", up):
            c = "ADD COLUMN " + c[4:]                 # MySQL: ADD `col` ... (khong co chu COLUMN)
        before = {x["name"] for x in t["columns"]}
        RS.parse_alter("ALTER TABLE %s %s" % (m.group(1), c), sch.tables)
        for x in t["columns"]:
            if x["name"] not in before:
                sch.mark(name, x["name"], origin, loc_of(ln))


def mig_key(rel):
    d = re.match(r"(\d+)", os.path.basename(os.path.dirname(rel)) if rel.endswith("migration.sql") else os.path.basename(rel))
    return (int(d.group(1)) if d else float("inf"), rel)


# ---------------------------------------------------------------- TypeORM migration (TS)
def typeorm_migration(sch, rel, text, rid, enums):
    um = re.search(r"\b(?:public\s+)?async\s+up\s*\(", text)
    if not um:
        return False
    s, e = SR.brace_body(text, um.end())
    body = text[s:e]
    loc = lambda off: "%s:%s#L%d" % (rid, rel, lineno(text, s + off))
    for m in re.finditer(r"\.query\s*\(", body):
        args, _ = SR.call_args(body, m.end() - 1)
        sql = SR.lit(args[0][0]) if args else None
        if sql:
            base = m.start()
            apply_sql(sch, sql, lambda ln, b=base: loc(b), "typeorm-migration", enums)
    for m in re.finditer(r"\.(createTable|addColumns?|dropColumns?|dropTable|renameColumn|renameTable)\s*\(", body):
        args, _ = SR.call_args(body, m.end() - 1)
        vals = [a for a, _ in args]
        op, here = m.group(1), loc(m.start())
        if op == "createTable" and vals:
            nm = re.search(r"""\bname\s*:\s*['"]([\w.]+)['"]""", vals[0])
            if not nm:
                continue
            t = sch.table(nm.group(1))
            t["columns"] = []
            sch.mark(t["name"], None, "typeorm-migration", here)
            cm = re.search(r"\bcolumns\s*:\s*\[", vals[0])
            if cm:
                close = SR.match_close(vals[0], cm.end() - 1, "[", "]")
                for seg, _ in SR.split_top(vals[0][cm.end():close]):
                    add_table_column(sch, t, seg, here)
        elif op.startswith("addColumn") and len(vals) > 1:
            t = sch.tables.get((SR.lit(vals[0]) or "").split(".")[-1]) if SR.lit(vals[0]) else None
            if t:
                for seg in re.findall(r"new\s+TableColumn\(\s*(\{[\s\S]*?\})\s*\)", ",".join(vals[1:])):
                    add_table_column(sch, t, seg, here)
        elif op.startswith("dropColumn") and len(vals) > 1:
            t = sch.tables.get(SR.lit(vals[0]) or "")
            if t:
                gone = {x for x in re.findall(r"""['"](\w+)['"]""", ",".join(vals[1:]))}
                t["columns"] = [x for x in t["columns"] if x["name"] not in gone]
        elif op == "dropTable" and vals:
            sch.tables.pop(SR.lit(vals[0]) or "", None)
        elif op == "renameColumn" and len(vals) > 2:
            t = sch.tables.get(SR.lit(vals[0]) or "")
            col = t and RS.find_col(t, SR.lit(vals[1]) or "")
            if col and SR.lit(vals[2]):
                col["name"] = SR.lit(vals[2])
        elif op == "renameTable" and len(vals) > 1 and SR.lit(vals[0]) in sch.tables:
            t = sch.tables.pop(SR.lit(vals[0]))
            t["name"] = SR.lit(vals[1])
            sch.tables[t["name"]] = t
    return True


def add_table_column(sch, t, obj, loc):
    nm = re.search(r"""\bname\s*:\s*['"](\w+)['"]""", obj)
    if not nm:
        return
    ty = re.search(r"""\btype\s*:\s*['"]([\w ]+)['"]""", obj)
    ln = re.search(r"""\blength\s*:\s*['"]?(\d+)""", obj)
    c = new_col(nm.group(1), (ty.group(1) if ty else S.NEED_CONFIRM) + ("(%s)" % ln.group(1) if ln else ""),
                "YES" if re.search(r"isNullable\s*:\s*true", obj) else "NO")
    c["pk"] = bool(re.search(r"isPrimary\s*:\s*true", obj))
    c["unique"] = bool(re.search(r"isUnique\s*:\s*true", obj))
    if re.search(r"isGenerated\s*:\s*true", obj):
        c["auto"] = "GENERATED"
    t["columns"] = [x for x in t["columns"] if x["name"] != c["name"]] + [c]
    if c["pk"] and c["name"] not in t["pks"]:
        t["pks"].append(c["name"])
    sch.mark(t["name"], c["name"], "typeorm-migration", loc)


# ---------------------------------------------------------------- Prisma schema
def prisma(sch, files, rid):
    text_of = {r: t for r, t in files.items() if r.endswith(".prisma")}
    provider = "postgresql"
    enums, models = {}, {}
    for rel, t in text_of.items():
        pm = re.search(r"""datasource\s+\w+\s*\{[^}]*provider\s*=\s*['"](\w+)['"]""", t)
        if pm:
            provider = pm.group(1)
        for m in re.finditer(r"^enum\s+(\w+)\s*\{([^}]*)\}", t, re.M):
            enums[m.group(1)] = re.findall(r"^\s*(\w+)", re.sub(r"//[^\n]*", "", m.group(2)), re.M)
        for m in re.finditer(r"^model\s+(\w+)\s*\{", t, re.M):
            s, e = SR.brace_body(t, m.start())
            models[m.group(1)] = (rel, t, m.start(), s, e)
    # ten bang (@@map) can truoc de dung cho FK
    tname = {}
    for name, (rel, t, pos, s, e) in models.items():
        mm = re.search(r"""@@map\(\s*(?:name\s*:\s*)?["']([^"']+)["']""", t[s:e])
        tname[name] = mm.group(1) if mm else name
    defaults = PRISMA_SQL.get(provider, PRISMA_SQL["postgresql"])
    for name, (rel, t, pos, s, e) in models.items():
        body = t[s + 1:e]
        if re.search(r"^\s*@@ignore\b", body, re.M):
            continue
        tb = tname[name]
        tdoc = []
        for prev in reversed(t[:pos].rstrip("\n").split("\n")):   # chi /// sat ngay tren dong model
            if not prev.strip().startswith("///"):
                break
            tdoc.insert(0, prev.strip()[3:].strip())
        rows, doc, fields = [], [], {}
        off = s + 1
        for raw in body.split("\n"):
            line_no = lineno(t, off)
            off += len(raw) + 1
            line = raw.strip()
            if line.startswith("///"):
                doc.append(line[3:].strip())
                continue
            line = re.sub(r"\s//[^\n]*$", "", line)
            if not line or line.startswith("//"):
                doc = []
                continue
            if line.startswith("@@"):
                rows.append(("@@", line, line_no))
                continue
            fm = re.match(r"^(\w+)\s+(\w+(?:\.\w+)?(?:\([^)]*\))?)(\[\])?(\?)?\s*(.*)$", line)
            if fm:
                fields[fm.group(1)] = (fm.groups(), line_no, doc)
            doc = []
        t_obj = None
        fk_rel = []
        for fname, ((_, ftype, lst, opt, attrs), line_no, doc) in fields.items():
            if re.search(r"(?<!@)@ignore\b", attrs):
                continue
            base = ftype.split("(")[0]
            if base in models:            # quan he, khong phai cot
                rm = re.search(r"@relation\([^)]*fields\s*:\s*\[([^\]]*)\][^)]*references\s*:\s*\[([^\]]*)\]", attrs)
                if rm:
                    fk_rel.append(([x.strip() for x in rm.group(1).split(",")],
                                   [x.strip() for x in rm.group(2).split(",")], base))
                continue
            if t_obj is None:
                t_obj = sch.table(tb, lineno(t, pos))
                sch.mark(tb, None, "prisma-model", "%s:%s#L%d" % (rid, rel, lineno(t, pos)))
                if tdoc and not t_obj["comment"]:
                    t_obj["comment"] = " ".join(tdoc)[:200]
            cm = re.search(r"""@map\(\s*(?:name\s*:\s*)?["']([^"']+)["']""", attrs)
            cname = cm.group(1) if cm else fname
            col = RS.find_col(t_obj, cname)
            if not col:
                db = re.search(r"@db\.(\w+)(\([^)]*\))?", attrs)
                if db:
                    ctype = db.group(1).lower() + (db.group(2) or "").replace(" ", "")
                elif base in enums:
                    ctype = base
                elif base.startswith("Unsupported"):
                    ctype = re.sub(r"Unsupported\(\s*[\"']?([^\"')]+)[\"']?\s*\)", r"\1", ftype)
                else:
                    ctype = defaults.get(base, base)
                col = new_col(cname, ctype + ("[]" if lst else ""), "YES" if opt else "NO")
                t_obj["columns"].append(col)
            if base in enums and not col["enum"]:
                col["enum"] = enums[base]
            if "@id" in re.sub(r"@@\w+", "", attrs):
                col["pk"], col["nullable"] = True, "NO"
                if cname not in t_obj["pks"]:
                    t_obj["pks"].append(cname)
            if re.search(r"@unique\b", attrs):
                col["unique"] = True
            dm = re.search(r"@default\(", attrs)
            if dm and not col["default"]:
                close = SR.match_close(attrs, dm.end() - 1)
                dv = attrs[dm.end():close if close > 0 else len(attrs)]
                if dv.startswith("autoincrement"):
                    col["auto"] = col["auto"] or "AUTO_INCREMENT"
                else:
                    col["default"] = dv
            if "@updatedAt" in attrs and not col["on_update"]:
                col["on_update"] = "@updatedAt (Prisma)"
            if doc and not col["comment"]:
                col["comment"] = " ".join(doc)[:200]
            sch.mark(tb, cname, "prisma-model", "%s:%s#L%d" % (rid, rel, line_no))
        if t_obj is None:
            continue
        colname = {f: (re.search(r"""@map\(\s*["']([^"']+)""", v[0][4]) or [None, f])[1] for f, v in fields.items()}
        for kind, line, _ in rows:
            m = re.match(r"@@(id|unique|index)\(\s*(?:fields\s*:\s*)?\[([^\]]*)\]", line)
            if not m:
                continue
            cols = [colname.get(x.strip().split("(")[0], x.strip()) for x in m.group(2).split(",") if x.strip()]
            if m.group(1) == "id":
                t_obj["pks"] = cols
            elif cols not in t_obj[{"unique": "uniques", "index": "indexes"}[m.group(1)]]:
                t_obj[{"unique": "uniques", "index": "indexes"}[m.group(1)]].append(cols)
        for frm, to, target in fk_rel:
            tt = models.get(target)
            to_map = {}
            if tt:
                for f2, a2 in re.findall(r"^\s*(\w+)\s+\w+[^\n]*?@map\(\s*[\"']([^\"']+)", tt[1][tt[3]:tt[4]], re.M):
                    to_map[f2] = a2
            for a, b in zip(frm, to):
                ca = colname.get(a, a)
                if not any(f["column"] == ca for f in t_obj["fks"]):
                    t_obj["fks"].append({"column": ca, "ref_table": tname[target], "ref_column": to_map.get(b, b)})
    return len(models), provider


# ---------------------------------------------------------------- TypeORM entity
COL_DECOS = ("Column", "PrimaryGeneratedColumn", "PrimaryColumn", "CreateDateColumn", "UpdateDateColumn",
             "DeleteDateColumn", "VersionColumn", "ObjectIdColumn")
PROP_RX = re.compile(r"\s*(?:(?:public|private|protected|readonly|declare|override)\s+)*([A-Za-z_$][\w$]*)[?!]?\s*:\s*([^;=\n]+)")


def members(body):
    """[(decorators [(name, args)], prop, ts_type)] cua 1 than class."""
    out, i = [], 0
    while True:
        a = body.find("@", i)
        if a < 0:
            return out
        decos, j = [], a
        while True:
            dm = re.compile(r"\s*@(\w+)\s*").match(body, j)
            if not dm:
                break
            j = dm.end()
            args = ""
            if body[j:j + 1] == "(":
                close = SR.match_close(body, j)
                args, j = body[j + 1:close], close + 1
            decos.append((dm.group(1), args))
        pm = PROP_RX.match(body, j)
        if pm and decos:
            out.append((decos, pm.group(1), pm.group(2).strip()))
            j = pm.end()
        i = max(j, a + 1)


def typeorm_entities(sch, files, rid):
    snake = any("SnakeNamingStrategy" in t for t in files.values())
    classes = {}
    for rel, t in files.items():
        if not rel.endswith((".ts", ".js")):
            continue
        prev = 0
        for m in re.finditer(r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?", t):
            s, e = SR.brace_body(t, m.end())
            em = None
            for x in re.finditer(r"@Entity\(([^)]*)\)", t[prev:m.start()]):
                em = x                                 # @Entity giua class truoc va class nay
            prev = e
            classes[m.group(1)] = {"rel": rel, "t": t, "pos": m.start(), "body": (s, e), "parent": m.group(2),
                                   "entity": em}
    n = 0
    for cls, c in classes.items():
        if not c["entity"]:
            continue
        arg = c["entity"].group(1)
        nm = re.search(r"""^\s*['"]([\w.]+)['"]|\bname\s*:\s*['"]([\w.]+)['"]""", arg)
        tb = (nm.group(1) or nm.group(2)) if nm else SR.snake(cls)
        t_obj = sch.table(tb, lineno(c["t"], c["pos"]))
        sch.mark(tb, None, "typeorm-entity", "%s:%s#L%d" % (rid, c["rel"], lineno(c["t"], c["pos"])))
        n += 1
        chain, k = [], cls
        while k in classes and k not in chain and len(chain) < 6:
            chain.append(k)
            k = classes[k]["parent"]
        for k in chain:
            cc = classes[k]
            s, e = cc["body"]
            body = cc["t"][s + 1:e]
            for decos, prop, ts_type in members(body):
                names = [d for d, _ in decos]
                args = " ".join(a for _, a in decos)
                loc = "%s:%s#L%d" % (rid, cc["rel"], lineno(cc["t"], s + 1 + body.find(prop)))
                cname = None
                if any(d in COL_DECOS for d in names):
                    dargs = next(a for d, a in decos if d in COL_DECOS)
                    nmm = re.search(r"""\bname\s*:\s*['"](\w+)['"]""", dargs)
                    cname = nmm.group(1) if nmm else (SR.snake(prop) if snake else prop)
                    ty = re.search(r"""^\s*['"]([\w ]+)['"]|\btype\s*:\s*['"]([\w ]+)['"]""", dargs)
                    ln = re.search(r"""\blength\s*:\s*['"]?(\d+)""", dargs)
                    ctype = (ty.group(1) or ty.group(2)) if ty else TS_SQL.get(ts_type.split("|")[0].strip(), S.NEED_CONFIRM)
                    d0 = next(d for d in names if d in COL_DECOS)
                    if d0.endswith("DateColumn") and not ty:
                        ctype = "timestamp"
                    if d0 == "PrimaryGeneratedColumn" and not ty:
                        ctype = "uuid" if "uuid" in dargs else "integer"
                    col = RS.find_col(t_obj, cname) or new_col(cname, ctype + ("(%s)" % ln.group(1) if ln else ""))
                    if col not in t_obj["columns"]:
                        t_obj["columns"].append(col)
                    col["nullable"] = "YES" if re.search(r"nullable\s*:\s*true", dargs) or d0 == "DeleteDateColumn" else "NO"
                    if d0.startswith("Primary"):
                        col["pk"], col["nullable"] = True, "NO"
                        if cname not in t_obj["pks"]:
                            t_obj["pks"].append(cname)
                        if d0 == "PrimaryGeneratedColumn":
                            col["auto"] = "GENERATED"
                    if re.search(r"unique\s*:\s*true", dargs):
                        col["unique"] = True
                    dm = re.search(r"\bdefault\s*:\s*([^,}]+)", dargs)
                    if dm:
                        col["default"] = dm.group(1).strip()
                    cm = re.search(r"""\bcomment\s*:\s*['"]([^'"]+)['"]""", dargs)
                    if cm:
                        col["comment"] = cm.group(1)
                elif any(d in ("ManyToOne", "OneToOne") for d in names) and \
                        ("ManyToOne" in names or "JoinColumn" in names):
                    jargs = next((a for d, a in decos if d == "JoinColumn"), "")
                    nmm = re.search(r"""\bname\s*:\s*['"](\w+)['"]""", jargs)
                    cname = nmm.group(1) if nmm else (SR.snake(prop) + "_id" if snake else prop + "Id")
                    if not RS.find_col(t_obj, cname):
                        t_obj["columns"].append(new_col(cname, S.NEED_CONFIRM + " (FK)",
                                                        "YES" if "nullable: true" in args or "nullable:true" in args else "YES"))
                    tm = re.search(r"\(\s*\)\s*=>\s*(\w+)", args)
                    if tm:
                        c_t = tm.group(1)
                        ref = classes.get(c_t)
                        if ref and ref["entity"]:
                            a2 = ref["entity"].group(1)
                            n2 = re.search(r"""^\s*['"]([\w.]+)['"]|\bname\s*:\s*['"]([\w.]+)['"]""", a2)
                            rt = (n2.group(1) or n2.group(2)) if n2 else SR.snake(c_t)
                        else:
                            rt = SR.snake(c_t)
                        rc = re.search(r"""referencedColumnName\s*:\s*['"](\w+)['"]""", jargs)
                        if not any(f["column"] == cname for f in t_obj["fks"]):
                            t_obj["fks"].append({"column": cname, "ref_table": rt, "ref_column": rc.group(1) if rc else "id"})
                if cname:
                    sch.mark(tb, cname, "typeorm-entity", loc)
    return n


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--repo-id", required=True)
    ap.add_argument("--out", required=True, help="<ver>/_internal")
    ap.add_argument("--ev-start", type=int, default=1)
    a = ap.parse_args()
    if not re.match(S.ID_PATTERNS["11_Repo"][1], a.repo_id) or not os.path.isdir(a.repo):
        print("Can repo ton tai va --repo-id dang REPO-01", file=sys.stderr)
        return 1
    root = os.path.abspath(a.repo)
    outdir = os.path.abspath(os.path.join(a.out, "recon", "db-code", a.repo_id))
    if outdir.startswith(root + os.sep):
        print("--out nam trong repo dang phan tich -> tu choi (chi doc)", file=sys.stderr)
        return 1
    files, skipped = walk(root)

    # 1) migration replay = schema DB thuc (theo thu tu)
    mig = Sch()
    enums, n_mig = {}, 0
    for rel in sorted(files, key=mig_key):
        t = files[rel]
        if rel.endswith(".sql"):
            apply_sql(mig, t, lambda ln, r=rel: "%s:%s#L%d" % (a.repo_id, r, ln),
                      "prisma-migration" if "prisma/" in rel else "sql-migration", enums)
            n_mig += 1
        elif "MigrationInterface" in t and typeorm_migration(mig, rel, t, a.repo_id, enums):
            n_mig += 1
    for t in mig.tables.values():             # PK / FK khai inline trong cot (nhu parse_dump)
        for c in t["columns"]:
            if c["pk"] and c["name"] not in t["pks"]:
                t["pks"].append(c["name"])
            if c["ref"] and not any(f["column"] == c["name"] for f in t["fks"]):
                t["fks"].append({"column": c["name"], "ref_table": c["ref"][0], "ref_column": c["ref"][1]})
    # 2) model / entity = ORM dang khai (chong len, ghi them nguon)
    sch = mig
    n_prisma, provider = prisma(sch, files, a.repo_id)
    n_entity = typeorm_entities(sch, files, a.repo_id)
    dialect = "mysql" if provider == "mysql" else "postgresql"

    # 3) evidence + lech model <-> migration
    ev, ev_rows, cs_rows, mism = a.ev_start, [], [], []
    has_model, has_mig = bool(n_prisma or n_entity), bool(n_mig)

    def origins(tb, col):
        return sch.src.get((tb, col), {})
    for name in sorted(sch.tables):
        t = sch.tables[name]
        o = origins(name, None)
        loc = next((v for k, v in o.items() if k in ("prisma-model", "typeorm-entity")), None) or \
            next(iter(o.values()), "%s:(khong ro)" % a.repo_id)
        t["ev"] = "EV-%04d" % ev
        ev_rows.append([t["ev"], "code-ref", loc, "", "", "", "Bang %s (read-orm-schema: %s)" % (name, ",".join(sorted(o)))])
        ev += 1
        for c in t["columns"]:
            oc = origins(name, c["name"])
            cs_rows.append([name, c["name"], ";".join(sorted(oc)) or "migration", "; ".join(list(oc.values())[:2])])
            if has_model and has_mig:
                is_model = any(k in oc for k in ("prisma-model", "typeorm-entity"))
                is_mig = any(k.endswith("migration") for k in oc)
                if is_model != is_mig:
                    mism.append("%s.%s chi co trong %s" % (name, c["name"], "model" if is_model else "migration"))

    def note_of(t):
        o = origins(t["name"], None)
        return " · nguon code: " + ", ".join("%s %s" % (k, v) for k, v in o.items())[:200]
    trows, crows = RS.table_rows(sch.tables, dialect, note_of)

    os.makedirs(outdir, exist_ok=True)
    RS.write_csv(os.path.join(outdir, "tables.csv"), S.SHEETS["03_DB_Tables"], trows)
    RS.write_csv(os.path.join(outdir, "columns.csv"), S.SHEETS["04_DB_Columns"], crows)
    RS.write_csv(os.path.join(outdir, "evidence.csv"), S.SHEETS["05_Evidence"], ev_rows)
    RS.write_csv(os.path.join(outdir, "code-schema.csv"), CODE_SCHEMA_COLS, cs_rows)
    json.dump({"provider": provider, "tables": sch.tables, "mismatches": mism},
              open(os.path.join(outdir, "schema.json"), "w", encoding="utf8"), indent=2, ensure_ascii=False, default=list)
    json.dump({"note": "Chi ten file — KHONG doc noi dung (rules/SECURITY.md)", "skipped": skipped},
              open(os.path.join(outdir, "skipped.json"), "w", encoding="utf8"), indent=2, ensure_ascii=False)

    repo = SR.Repo(root, a.repo_id)
    SR.walk(repo)
    print(json.dumps({"repo_id": a.repo_id, "dialect": dialect, "tables": len(sch.tables), "columns": len(crows),
                      "prisma_models": n_prisma, "typeorm_entities": n_entity, "migrations": n_mig,
                      "fks": sum(len(t["fks"]) for t in sch.tables.values()),
                      "mismatches": len(mism), "skipped": len(skipped), "commit": SR.repo_commit(repo),
                      "next_ev": ev, "out": outdir}, indent=2))
    if mism:
        print("LECH model <-> migration (%d): %s" % (len(mism), "; ".join(mism[:10])), file=sys.stderr)
    if skipped:
        print("LUU Y: %d file bi bo qua vi ten nhay cam -> skipped.json (bang trong do co the bi thieu)" % len(skipped),
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
