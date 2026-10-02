#!/usr/bin/env python3
"""GATE V2 — Inventory coverage + truy vet (Function/Screen/API/Integration/Site/Repo).

  python3 verify-inventory.py <inventory.xlsx> \
      [--routes routes_REPO-01.txt --routes routes_REPO-02.txt] \
      [--crawled urls_WEB-01.txt --crawled urls_WEB-02.txt] [--out report.md]

--routes   : route lay tu scan-repo.py (1 route / dong, cho phep "GET /path"); lap lai moi repo
--crawled  : URL da crawl that (1 URL / dong); lap lai moi site

Chan: Confirmed khong co bang chung · muc chua chac khong khai Open Question · route/URL
bi bo sot · ID trung/nhay coc · tham chieu SC/F/API/WEB/REPO/table khong ton tai ·
Config Keys lo gia tri bi mat (gia tri luon bi che khi in ra).
"""
import argparse
import os
import re
import sys

import inv_schema as S
from gate_report import Gate

DASHES = ("—", "-")
SKIP_REF = ("—", "-", "N/A", S.UNKNOWN)
METHOD_PREFIX = re.compile(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|ANY|ALL)\s+", re.I)
CRED_URL = re.compile(r"://[^/\s:@]+:[^/\s@]+@")


def read_lists(paths):
    out = []
    for path in paths or []:
        if not path or not os.path.isfile(path):
            print("CANH BAO: khong doc duoc %s" % path, file=sys.stderr)
            continue
        for line in open(path, encoding="utf8"):
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def norm_route(r):
    """/orders/123 va /orders/:id ve cung dang de so sanh."""
    r = METHOD_PREFIX.sub("", (r or "").strip())
    r = re.sub(r"^https?://[^/]+", "", r)
    r = r.split("?")[0].split("#")[0].rstrip("/") or "/"
    r = re.sub(r"/(\d+|\{[^/]+\}|:[^/]+|\[[^/]+\])(?=/|$)", "/:id", r)
    return r.lower()


def mask(v):
    v = str(v)
    return (v[:2] + "****" + v[-2:]) if len(v) > 6 else "****"


def secret_issue(token):
    """Tra ve mo ta (da che) neu token khong phai ten key thuan, None neu OK."""
    if "=" in token:
        return "%s=**** (chua gia tri)" % token.split("=", 1)[0][:40]
    if "://" in token and CRED_URL.search(token):
        return "URL co credential (%s)" % mask(token)
    if len(token) >= 20 and re.fullmatch(r"[A-Za-z0-9+/_\-]+", token) \
            and not re.fullmatch(r"[A-Z0-9_]+", token):
        has_d = any(c.isdigit() for c in token)
        has_l = any(c.islower() for c in token)
        has_u = any(c.isupper() for c in token)
        n_d = sum(c.isdigit() for c in token)
        if has_d and (has_l or has_u) and ((has_l and has_u and n_d >= 3) or n_d >= 4):
            return "chuoi giong token ngau nhien (%s)" % mask(token)
    return None


def ids_ok(g, no, data, sheet):
    col, pat = S.ID_PATTERNS[sheet]
    ids = [r.get(col, "") for r in data[sheet]]
    rx = re.compile(pat)
    bad = [i or "(trong)" for i in ids if not rx.match(i)]
    dup = sorted({i for i in ids if i and ids.count(i) > 1})
    g.check(no, "%s: %s dung dinh dang va khong trung" % (sheet, col), bad + dup)
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory")
    ap.add_argument("--routes", action="append", default=[])
    ap.add_argument("--crawled", action="append", default=[])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    data = S.load(a.inventory)
    meta = S.meta(data)
    g = Gate("GATE V2 — Inventory coverage")

    funcs = data["01_Function"]
    screens = data["02_Screen"]
    tables = data["03_DB_Tables"]
    cols = data["04_DB_Columns"]
    questions = data["06_OpenQuestions"]
    apis = data["07_API"]
    fields = data["08_API_Fields"]
    exts = data["09_Integration"]
    sites = data["10_Site"]
    repos = data["11_Repo"]

    # 1..3 — dinh dang + trung lap ID
    fids = ids_ok(g, 1, data, "01_Function")
    sids = ids_ok(g, 2, data, "02_Screen")
    qids = ids_ok(g, 3, data, "06_OpenQuestions")
    evids = {r.get("EV ID", "") for r in data["05_Evidence"]}
    ev_type = {r.get("EV ID", ""): r.get("Type", "") for r in data["05_Evidence"]}
    fset, sset, qset = set(fids), set(sids), set(qids)

    # 4 — Function ID lien tuc
    nums = sorted(int(i.split("-")[1]) for i in fids if re.match(r"^F-\d+$", i))
    gaps = [("F-%03d" % n) for n in range(1, (nums[-1] if nums else 0) + 1) if n not in nums]
    g.check(4, "Function ID lien tuc, khong nhay coc", gaps)

    # 5 — enum
    enum_rules = [
        ("01_Function", "Function ID", "Status", S.FUNCTION_STATUS),
        ("02_Screen", "Screen ID", "Status", S.SCREEN_STATUS),
        ("02_Screen", "Screen ID", "Type", S.SCREEN_TYPE),
        ("06_OpenQuestions", "Q ID", "Type", S.QUESTION_TYPE),
        ("06_OpenQuestions", "Q ID", "Status", S.QUESTION_STATUS),
        ("07_API", "API ID", "Kind", S.API_KIND),
        ("07_API", "API ID", "Method", S.API_METHOD),
        ("07_API", "API ID", "Status", S.API_STATUS),
        ("08_API_Fields", "API ID", "Direction", S.API_FIELD_DIRECTION),
        ("08_API_Fields", "API ID", "In", S.API_FIELD_IN),
        ("09_Integration", "EXT ID", "Direction", S.INTEGRATION_DIRECTION),
        ("09_Integration", "EXT ID", "Status", S.INTEGRATION_STATUS),
        ("10_Site", "Site ID", "Crawl Mode", S.CRAWL_MODE),
        ("11_Repo", "Repo ID", "Kind", S.REPO_KIND),
    ]
    bad_enum = []
    for sheet, key, col, allowed in enum_rules:
        bad_enum += ["%s!%s %s=%s" % (sheet, r.get(key) or r["__row__"], col, r.get(col, ""))
                     for r in data[sheet] if r.get(col) not in allowed]
    g.check(5, "Moi cot enum dung gia tri cho phep", bad_enum)

    # 6 — Confirmed phai co bang chung
    g.check(6, "Moi chuc nang Confirmed co >=1 EV",
            [r["Function ID"] for r in funcs
             if r.get("Status") == "Confirmed"
             and not [e for e in S.split_ids(r.get("Evidence", "")) if e in evids]])

    # 7 — chua chac chan phai khai bao Open Question
    g.check(7, "Moi chuc nang chua Confirmed co Open Question tuong ung",
            ["%s (%s)" % (r["Function ID"], r.get("Status")) for r in funcs
             if r.get("Status") in ("To verify", "Inferred", "CONFLICT")
             and not [q for q in S.split_ids(r.get("Open Q", "")) if q in qset]])

    # 8 — Screen IDs cua Function phan giai duoc
    bad_link = []
    for r in funcs:
        raw = r.get("Screen IDs", "")
        if raw.strip() == S.NO_SCREEN:
            continue
        if not raw.strip():
            bad_link.append("%s bo trong Screen IDs" % r["Function ID"])
            continue
        bad_link += ["%s -> %s khong ton tai" % (r["Function ID"], sid)
                     for sid in S.split_ids(raw) if sid not in sset]
    g.check(8, "Screen IDs cua Function phan giai duoc (hoac khai 'SYSTEM — no screen')", bad_link)

    # 9 — Function IDs cua Screen phan giai duoc
    g.check(9, "Function IDs cua Screen phan giai duoc",
            ["%s -> %s" % (r["Screen ID"], f)
             for r in screens for f in S.split_ids(r.get("Function IDs", ""))
             if f not in fset])

    # 10 — Screenshot EV
    g.check(10, "Screenshot EV ton tai hoac khai bao NO IMAGE",
            [r["Screen ID"] for r in screens
             if S.NO_IMAGE not in r.get("Screenshot EV", "")
             and not [e for e in S.split_ids(r.get("Screenshot EV", "")) if e in evids]])

    # 11 — khong de o trong lang le
    required = {
        "01_Function": ["Module", "Function", "Primary Actor", "Description",
                        "Entry / Trigger", "Source", "Status"],
        "02_Screen": ["Site", "URL / Route", "Screen Name", "Type", "Actor", "Status"],
        "07_API": ["Group", "Kind", "Method", "Path / Schedule", "Summary", "Auth",
                   "Handler", "Repo", "Status"],
        "08_API_Fields": ["API ID", "Direction", "In", "Field", "Type", "Required"],
        "09_Integration": ["Name", "Kind", "Purpose", "Direction", "Used By",
                           "Config Keys", "Status"],
        "10_Site": ["Site Name", "URL", "Env", "Roles Observed", "Crawl Mode",
                    "FE Repo", "Screen Count"],
        "11_Repo": ["Path", "Kind", "Stack", "For Site"],
    }
    blanks = []
    for sheet, need in required.items():
        for r in data[sheet]:
            blanks += ["%s!row%s.%s" % (sheet, r["__row__"], c)
                       for c in need if not r.get(c, "").strip()]
    g.check(11, "Khong o trong lang le (thieu bang chung phai ghi UNKNOWN)", blanks)

    # 12 — nhat quan DB
    db_mode = meta.get("db_mode", "")
    if db_mode == "NONE":
        g.check(12, "db_mode=NONE thi 2 sheet DB phai rong",
                (["03_DB_Tables co %d dong" % len(tables)] if tables else []) +
                (["04_DB_Columns co %d dong" % len(cols)] if cols else []))
    elif db_mode in S.DB_MODE:
        g.check(12, "db_mode=%s thi phai co du lieu DB" % db_mode,
                [] if tables else ["03_DB_Tables rong"])
    else:
        g.fail(12, "Nhat quan DB", "00_Meta.db_mode=%r khong thuoc %s" % (db_mode, S.DB_MODE))

    # 13 — bang duoc nhac o Function phai ton tai
    tset = {r.get("Table", "") for r in tables}
    if db_mode != "NONE":
        g.check(13, "Related Tables cua Function ton tai trong 03_DB_Tables",
                ["%s -> %s" % (r["Function ID"], t) for r in funcs
                 for t in S.split_ids(r.get("Related Tables", ""))
                 if t not in tset and t not in SKIP_REF])
    else:
        g.ok(13, "Related Tables (bo qua — khong co DB)")

    # 14 — Meaning High confidence phai co code-ref
    g.check(14, "04_DB_Columns: Meaning confidence High phai co EV loai code-ref",
            ["%s.%s" % (r.get("Table", ""), r.get("Column", "")) for r in cols
             if r.get("Confidence") == "High"
             and "code-ref" not in [ev_type.get(e) for e in S.split_ids(r.get("Evidence", ""))]])

    # 15 — route trong code da duoc phu
    routes = read_lists(a.routes)
    missing_routes = []
    if routes:
        covered = {norm_route(r.get("Entry / Trigger", "")) for r in funcs}
        covered |= {norm_route(r.get("URL / Route", "")) for r in screens}
        covered |= {norm_route(r.get("Path / Schedule", "")) for r in apis}
        missing_routes = sorted({r for r in routes if norm_route(r) not in covered})
        g.check(15, "Moi route trong source code co mat trong inventory", missing_routes)
    else:
        g.warn(15, "Route coverage", "chua truyen --routes -> khong kiem duoc bo sot")

    # 16 — URL da crawl deu co mat o 02_Screen
    crawled = read_lists(a.crawled)
    if crawled:
        known = {norm_route(r.get("URL / Route", "")) for r in screens}
        # route co tham so khong phai so (vd /tenant/:code <- /tenant/KL): khop theo pattern cua man
        pats = [re.compile("^" + re.sub(r"/:[^/]+", "/[^/]+", re.escape(norm_route(r.get("URL / Route", "")))
                                        .replace(r"\:", ":")) + "$")
                for r in screens if ":" in r.get("URL / Route", "")]
        g.check(16, "Moi URL da crawl co mat trong 02_Screen",
                sorted({u for u in crawled if norm_route(u) not in known
                        and not any(p.match(norm_route(u)) for p in pats)}))
    else:
        g.warn(16, "Crawl coverage", "chua truyen --crawled")

    # 17..20 — ID cua sheet moi
    api_ids = ids_ok(g, 17, data, "07_API")
    ext_ids = ids_ok(g, 18, data, "09_Integration")
    site_ids = ids_ok(g, 19, data, "10_Site")
    repo_ids = ids_ok(g, 20, data, "11_Repo")
    aset, siteset, reposet = set(api_ids), set(site_ids), set(repo_ids)

    # 21 — API Confirmed phai co code-ref
    g.check(21, "API Confirmed co >=1 EV loai code-ref",
            [r["API ID"] for r in apis if r.get("Status") == "Confirmed"
             and "code-ref" not in [ev_type.get(e) for e in S.split_ids(r.get("Evidence", ""))
                                    if e in evids]])

    # 22 — API chua Confirmed phai co Open Q ton tai
    g.check(22, "API chua Confirmed co Open Question ton tai",
            ["%s (%s)" % (r["API ID"], r.get("Status")) for r in apis
             if r.get("Status") != "Confirmed"
             and not [q for q in S.split_ids(r.get("Open Q", "")) if q in qset]])

    # 23 — 08_API_Fields tro toi API co that
    g.check(23, "08_API_Fields: API ID ton tai trong 07_API",
            sorted({"row%s -> %s" % (r["__row__"], r.get("API ID")) for r in fields
                    if r.get("API ID") not in aset}))

    # 24 — 02_Screen.Site phan giai ve 10_Site
    g.check(24, "02_Screen.Site ton tai trong 10_Site",
            ["%s -> %s" % (r["Screen ID"], r.get("Site", "")) for r in screens
             if r.get("Site", "") not in siteset])

    # 25 — Screen Count khop thuc te
    per_site = {}
    for r in screens:
        per_site[r.get("Site", "")] = per_site.get(r.get("Site", ""), 0) + 1
    bad_cnt = []
    for r in sites:
        sid, raw = r.get("Site ID", ""), r.get("Screen Count", "")
        try:
            n = int(float(raw))
        except ValueError:
            bad_cnt.append("%s Screen Count=%r khong phai so" % (sid, raw))
            continue
        if n != per_site.get(sid, 0):
            bad_cnt.append("%s khai %d, 02_Screen co %d" % (sid, n, per_site.get(sid, 0)))
    g.check(25, "10_Site.Screen Count = so man hinh thuc te cua site", bad_cnt)

    # 26 — FE Repo / API Repo phan giai ve 11_Repo
    bad_repo = []
    for sheet, key, col in (("10_Site", "Site ID", "FE Repo"), ("07_API", "API ID", "Repo")):
        for r in data[sheet]:
            v = r.get(col, "").strip()
            if v in DASHES:
                continue
            for rid in S.split_ids(v) or [v]:
                if rid not in reposet:
                    bad_repo.append("%s %s.%s=%s" % (sheet, r.get(key), col, rid))
    g.check(26, "10_Site.FE Repo va 07_API.Repo ton tai trong 11_Repo (hoac '—')", bad_repo)

    # 27 — Called By Screens
    g.check(27, "07_API.Called By Screens tro toi Screen co that",
            ["%s -> %s" % (r["API ID"], s) for r in apis
             for s in S.split_ids(r.get("Called By Screens", ""))
             if s not in SKIP_REF and s not in sset])

    # 28 — Related Tables cua API
    if db_mode != "NONE":
        g.check(28, "07_API.Related Tables ton tai trong 03_DB_Tables",
                ["%s -> %s" % (r["API ID"], t) for r in apis
                 for t in S.split_ids(r.get("Related Tables", ""))
                 if t not in SKIP_REF and t not in tset])
    else:
        g.ok(28, "07_API.Related Tables (bo qua — khong co DB)")

    # 29 — Integration Confirmed co EV
    g.check(29, "09_Integration Confirmed co >=1 EV",
            [r["EXT ID"] for r in exts if r.get("Status") == "Confirmed"
             and not [e for e in S.split_ids(r.get("Evidence", "")) if e in evids]])

    # 30 — Config Keys chi la ten key
    leaks = []
    for r in exts:
        for tok in re.split(r"[;,\s]+", r.get("Config Keys", "")):
            if not tok:
                continue
            issue = secret_issue(tok)
            if issue:
                leaks.append("%s: %s" % (r.get("EXT ID"), issue))
    g.check(30, "09_Integration.Config Keys chi chua TEN key (khong gia tri/bi mat)", leaks)

    rc = g.emit(a.out)
    st = {}
    for r in funcs:
        st[r.get("Status", "?")] = st.get(r.get("Status", "?"), 0) + 1
    if routes:
        print("COVERAGE: %d/%d route · THIEU: %s" %
              (len(set(routes)) - len(missing_routes), len(set(routes)),
               missing_routes or "[]"), file=sys.stderr)
    print("EVIDENCE: %d EV · %s" % (len(evids), " · ".join("%s=%d" % kv for kv in sorted(st.items()))),
          file=sys.stderr)
    print("OPEN QUESTIONS: %d con Open" %
          sum(1 for r in questions if r.get("Status") == "Open"), file=sys.stderr)
    print("API: %d (Confirmed %d)" % (len(apis), sum(1 for r in apis if r.get("Status") == "Confirmed")),
          file=sys.stderr)
    print("SITES: %d" % len(sites), file=sys.stderr)
    print("REPOS: %d" % len(repos), file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main())
