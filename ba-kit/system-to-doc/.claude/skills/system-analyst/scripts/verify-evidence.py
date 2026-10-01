#!/usr/bin/env python3
"""GATE V1 — Evidence Ledger integrity.

  python3 verify-evidence.py <inventory.xlsx> [--root <_internal>] [--code-root <repo>] [--out report.md]

code-ref Locator: REPO-01:path#L88 hoac REPO-01:path#L88-L104 (path tuong doi goc repo,
goc repo lay tu 11_Repo.Path). --code-root chi dung cho locator cu khong co prefix REPO-xx.
db-query Locator: schema:<file>#L<n> (chi kiem dinh dang).
Chan "EV ma": EV duoc tro toi nhung khong ton tai, artifact khong co that,
code-ref khong phan giai ra file#line co that.
"""
import argparse
import os
import re
import sys

import inv_schema as S
from gate_report import Gate

CODE_REF = re.compile(
    r"^(?:(?P<repo>REPO-\d{2,}):)?(?P<path>[^#\s]+)#L(?P<a>\d+)(?:-L(?P<b>\d+))?$")
DB_REF = re.compile(r"^schema:[^#\s]+#L\d+$")
REF_COLS = [("01_Function", "Evidence"), ("02_Screen", "Screenshot EV"),
            ("03_DB_Tables", "Evidence"), ("04_DB_Columns", "Evidence"),
            ("06_OpenQuestions", "Reason / Evidence"), ("07_API", "Evidence"),
            ("07_API", "Handler"), ("08_API_Fields", "Evidence"),
            ("09_Integration", "Evidence")]


def resolve_code_ref(loc, repo_paths, root, code_root):
    """Tra ve (ok, loi). Kiem file ton tai va du so dong."""
    m = CODE_REF.match(loc or "")
    if not m:
        return False, "sai dinh dang REPO-xx:path#Lxx[-Lyy]"
    repo = m.group("repo")
    if repo:
        if repo not in repo_paths:
            return False, "%s khong co trong 11_Repo" % repo
        base = repo_paths[repo]
        if not os.path.isabs(base):
            base = os.path.join(root, base)
        if not os.path.isdir(base):
            return False, "%s.Path khong ton tai tren may (%s)" % (repo, repo_paths[repo])
    elif code_root:
        base = code_root
    else:
        return False, "thieu prefix REPO-xx: (hoac truyen --code-root cho locator cu)"
    fp = os.path.join(base, m.group("path"))
    if not os.path.isfile(fp):
        return False, "khong thay %s%s" % (repo + ":" if repo else "", m.group("path"))
    try:
        n = sum(1 for _ in open(fp, encoding="utf8", errors="ignore"))
    except OSError:
        return False, "khong doc duoc %s" % m.group("path")
    a, b = int(m.group("a")), int(m.group("b") or m.group("a"))
    if b < a:
        return False, "khoang dong nguoc L%d-L%d" % (a, b)
    if b > n:
        return False, "file chi co %d dong (< L%d)" % (n, b)
    return True, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory")
    ap.add_argument("--root", default=None,
                    help="Thu muc goc phan giai Artifact (mac dinh: thu muc chua inventory = _internal)")
    ap.add_argument("--code-root", default=None,
                    help="Chi cho locator cu khong co prefix REPO-xx")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    root = a.root or os.path.dirname(os.path.abspath(a.inventory))
    data = S.load(a.inventory)
    g = Gate("GATE V1 — Evidence Ledger")

    ev_rows = data["05_Evidence"]
    ids = [r.get("EV ID", "") for r in ev_rows]
    repo_paths = {r.get("Repo ID", ""): r.get("Path", "") for r in data["11_Repo"]}

    pat = re.compile(S.ID_PATTERNS["05_Evidence"][1])
    g.check(1, "EV ID dung dinh dang EV-NNNN", [i for i in ids if not pat.match(i)])
    g.check(2, "EV ID khong trung", sorted({i for i in ids if ids.count(i) > 1}))

    g.check(3, "Type thuoc enum cho phep",
            [(r["EV ID"], r.get("Type", "")) for r in ev_rows
             if r.get("Type", "") not in S.EVIDENCE_TYPE],
            fmt=lambda x: "%s=%s" % x)

    g.check(4, "Moi EV co Locator", [r["EV ID"] for r in ev_rows if not r.get("Locator")])

    missing_art = []
    for r in ev_rows:
        if r.get("Type") not in S.EVIDENCE_NEEDS_ARTIFACT:
            continue
        art = r.get("Artifact", "")
        if not art:
            missing_art.append("%s (trong Artifact)" % r["EV ID"])
        elif not os.path.exists(os.path.join(root, art)):
            missing_art.append("%s -> %s" % (r["EV ID"], art))
    g.check(5, "File artifact (screenshot/har/log) ton tai that", missing_art)

    bad_code = []
    for r in ev_rows:
        if r.get("Type") == "code-ref":
            ok, err = resolve_code_ref(r.get("Locator", ""), repo_paths, root, a.code_root)
            if not ok:
                bad_code.append("%s %s" % (r["EV ID"], err))
    g.check(6, "code-ref REPO-xx:path#Lxx phan giai duoc ra file/dong co that", bad_code)

    bad_web = []
    for r in ev_rows:
        if r.get("Type") in S.EVIDENCE_NEEDS_ARTIFACT:
            if not r.get("Captured At"):
                bad_web.append("%s thieu Captured At" % r["EV ID"])
            if not r.get("Actor/Role"):
                bad_web.append("%s thieu Actor/Role" % r["EV ID"])
    g.check(7, "Evidence quan sat co Captured At + Actor/Role", bad_web)

    # 8/9 — EV ma va EV mo coi; Handler dang locator tinh la tham chieu toi EV cung Locator
    known = set(ids)
    by_loc = {}
    for r in ev_rows:
        by_loc.setdefault(r.get("Locator", ""), []).append(r.get("EV ID", ""))
    referenced = {}
    handler_locs = []
    for sheet, col in REF_COLS:
        for r in data.get(sheet, []):
            raw = r.get(col, "")
            for tok in S.split_ids(raw):
                where = "%s!row%s" % (sheet, r["__row__"])
                if tok.startswith("EV-"):
                    referenced.setdefault(tok, []).append(where)
                elif col == "Handler" and CODE_REF.match(tok):
                    handler_locs.append((r.get("API ID", where), tok))
                    for ev in by_loc.get(tok, []):
                        referenced.setdefault(ev, []).append(where)
    ghosts = ["%s (%s)" % (ev, locs[0]) for ev, locs in sorted(referenced.items())
              if ev not in known]
    g.check(8, "Khong co EV ma (tro toi evidence khong ton tai)", ghosts)
    g.check(9, "Khong co EV mo coi", sorted(known - set(referenced)), level="WARN")

    g.check(10, "db-query Locator dung dinh dang schema:<file>#L<n>",
            ["%s=%s" % (r["EV ID"], r.get("Locator", "")) for r in ev_rows
             if r.get("Type") == "db-query" and not DB_REF.match(r.get("Locator", ""))])

    bad_h = []
    for api, loc in handler_locs:
        ok, err = resolve_code_ref(loc, repo_paths, root, a.code_root)
        if not ok:
            bad_h.append("%s %s" % (api, err))
    g.check(11, "07_API.Handler dang locator phan giai duoc", bad_h)

    return g.emit(a.out)


if __name__ == "__main__":
    sys.exit(main())
