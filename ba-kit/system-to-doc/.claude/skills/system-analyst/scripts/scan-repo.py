#!/usr/bin/env python3
"""Recon source code: endpoint BE, route FE, API call FE, batch/queue, bang DB. CHI DOC.

  python3 scan-repo.py <repo_root> --repo-id REPO-01 [--kind AUTO|FE|BE|FULLSTACK]
          --out <_internal> --ev-start N --api-start N

Output -> <_internal>/recon/code/<REPO-xx>/
  stack.json  routes.txt  routes.json  api.json  fe-routes.json  fe-api-calls.json
  batch.json  integrations.json  table-refs.json  evidence.csv  api-seed.csv
  skipped-sensitive.json   (chi TEN file nhay cam bi bo qua, khong bao gio noi dung)
stdout: JSON {counts, kind, next_ev, next_api, out}

Ho tro: Express/Koa/Fastify/Nest, Next.js (pages/api, app/**/route), Nuxt server/api,
SvelteKit, Laravel, Django/DRF, Flask, FastAPI, Spring, ASP.NET, Rails, Go (gin/echo/chi);
FE: React Router, vue-router, Angular, Next/Nuxt/SvelteKit file routing.

Ket qua la GOI Y (regex), khong phai ket luan: moi dong api-seed co Status='To verify'.
Khong bao gio mo .env / key / credential (xem SENSITIVE_* ben duoi, dong bo rules/SECURITY.md).
"""
import argparse
import bisect
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inv_schema as S  # noqa: E402

# ---------------------------------------------------------------- an toan
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", ".next", ".nuxt",
             ".svelte-kit", "target", "coverage", "__pycache__", ".venv", "venv",
             ".idea", ".vscode", ".gradle", "bin", "obj", "out", ".output", ".turbo",
             ".cache", "bower_components", "Pods", ".terraform"}
TEST_DIRS = {"__tests__", "__mocks__", "test", "tests", "spec", "e2e", "cypress",
             "playwright", "stories", "fixtures", "__fixtures__"}
TEST_FILE_RX = re.compile(r"\.(test|spec|stories|e2e|cy)\.[a-z]+$|_test\.(py|go)$|^test_.*\.py$")
ENV_OK = {".env.example", ".env.sample", ".env.template"}
SENSITIVE_EXT = (".pem", ".key", ".p8", ".p12", ".pfx", ".cer", ".keystore", ".jks",
                 ".mobileprovision", ".provisionprofile", ".sql", ".dump", ".db",
                 ".sqlite", ".sqlite3", ".sql.gz", ".bak")
SENSITIVE_NAMES = {".npmrc", ".yarnrc", ".yarnrc.yml", ".netrc", ".gitconfig", ".pgpass",
                   "google-services.json", "googleservice-info.plist", "key.properties",
                   "test-users.json", ".htpasswd", "credentials", "known_hosts"}
SENSITIVE_WORDS = ("secret", "credential", "token", "password", "passwd", "apikey",
                   "api_key", "service-account", "service_account", "serviceaccount",
                   "adminsdk", "private_key", "privatekey")
MAX_BYTES = 2 * 1024 * 1024

TEXT_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".py",
            ".php", ".rb", ".java", ".kt", ".go", ".cs", ".prisma", ".yml", ".yaml",
            ".cron", ".json", ".xml", ".gradle", ".toml", ".txt", ".mod")
TEXT_NAMES = {"crontab", "Gemfile", "Procfile"}


def sensitive_reason(rel):
    """Tra ve ly do neu file thuoc danh sach cam doc, nguoc lai None. Chi xet TEN/duong dan."""
    p = rel.replace(os.sep, "/")
    name = os.path.basename(p)
    low = name.lower()
    if low == ".env" or (low.startswith(".env.") and low not in ENV_OK) or low.endswith(".env"):
        return "env-file"
    if low in ENV_OK:
        return None
    if low.startswith(("id_rsa", "id_ed25519", "id_dsa", "id_ecdsa")):
        return "ssh-key"
    if low.endswith(SENSITIVE_EXT):
        return "key/cert/db-dump"
    if low in SENSITIVE_NAMES:
        return "credential-config"
    if "/.auth/" in "/" + p or p.startswith(".auth/") or "/.git/config" in "/" + p:
        return "auth-state"
    if any(w in low for w in SENSITIVE_WORDS):
        return "name-keyword"
    return None


# ---------------------------------------------------------------- tien ich text
class Src:
    def __init__(self, rel, text):
        self.rel = rel.replace(os.sep, "/")
        self.text = text
        self.nl = [m.start() for m in re.finditer("\n", text)]
        self.ext = os.path.splitext(rel)[1].lower()
        self.stem = os.path.splitext(os.path.basename(rel))[0]

    def line(self, pos):
        return bisect.bisect_left(self.nl, pos) + 1


def match_close(t, i, o="(", c=")", limit=30000, hash_comment=False):
    """t[i]==o -> vi tri dau dong tuong ung (bo qua string/comment), -1 neu khong thay."""
    d, j, n, q = 0, i, min(len(t), i + limit), None
    while j < n:
        ch = t[j]
        if q:
            if ch == "\\":
                j += 2
                continue
            if ch == q:
                q = None
        elif ch in "'\"`":
            q = ch
        elif ch == "/" and t[j + 1:j + 2] == "/":
            k = t.find("\n", j)
            j = n if k < 0 else k
            continue
        elif ch == "/" and t[j + 1:j + 2] == "*":
            k = t.find("*/", j + 2)
            j = n if k < 0 else k + 2
            continue
        elif ch == "#" and hash_comment:
            k = t.find("\n", j)
            j = n if k < 0 else k
            continue
        elif ch == o:
            d += 1
        elif ch == c:
            d -= 1
            if d == 0:
                return j
        j += 1
    return -1


def split_top(inner):
    """Tach chuoi theo dau phay o cap ngoai cung -> [(text, offset)]."""
    out, d, q, start, j = [], 0, None, 0, 0
    while j < len(inner):
        ch = inner[j]
        if q:
            if ch == "\\":
                j += 2
                continue
            if ch == q:
                q = None
        elif ch in "'\"`":
            q = ch
        elif ch in "([{":
            d += 1
        elif ch in ")]}":
            d -= 1
        elif ch == "," and d == 0:
            out.append((inner[start:j], start))
            start = j + 1
        j += 1
    if inner[start:].strip():
        out.append((inner[start:], start))
    return out


def call_args(t, open_idx, hash_comment=False):
    close = match_close(t, open_idx, hash_comment=hash_comment)
    if close < 0:
        close = min(len(t), open_idx + 2000)
    return [(a.strip(), open_idx + 1 + off + len(a) - len(a.lstrip()))
            for a, off in split_top(t[open_idx + 1:close])], close


LIT_RX = re.compile(r"""^[rRfFbBuU]?(['"`])(.*)\1$""", re.S)


def lit(s):
    m = LIT_RX.match((s or "").strip())
    return m.group(2) if m else None


def top_keys(t, open_idx, o="{", c="}"):
    """Key cap 1 cua object/array literal: {a: .., b: ..} hoac ['a' => ..]."""
    close = match_close(t, open_idx, o, c)
    if close < 0:
        return []
    keys = []
    for seg, _ in split_top(t[open_idx + 1:close]):
        m = re.match(r"""\s*(?://[^\n]*\n\s*)*['"]?([\w.*$\-]+)['"]?\s*(?::|=>)""", seg)
        if m and not m.group(1).startswith("..."):
            keys.append(m.group(1))
    return keys


def norm_path(p):
    if p is None:
        return None
    p = p.strip()
    p = re.sub(r"^\^|\$$|\\Z$", "", p)
    p = re.sub(r"\(\?P<(\w+)>[^)]*\)", r":\1", p)
    p = re.sub(r"<(?:\w+:)?(\w+)>", r":\1", p)
    p = re.sub(r"\{(\w+)(?::[^}]*)?\??\}", r":\1", p)
    p = re.sub(r"\[\[?\.\.\.(\w+)\]?\]", r":\1*", p)
    p = re.sub(r"\[(\w+)\]", r":\1", p)
    p = p.split("?")[0].split("#")[0]
    p = re.sub(r"/{2,}", "/", "/" + p.lstrip("/"))
    if len(p) > 1:
        p = p.rstrip("/")
    return p or "/"


def join_path(*parts):
    acc = ""
    for x in parts:
        if x is None or x == "":
            continue
        acc = acc.rstrip("/") + "/" + x.strip("/")
    return norm_path(acc or "/")


AUTH_RX = re.compile(r"(?i)(auth|jwt|passport|protect|login|guard|token|session|"
                     r"sanctum|permission|role|admin|verify|bearer|secured|ensure)")
METHODS = {"get", "post", "put", "patch", "delete"}


def mapm(m):
    m = (m or "").upper()
    return m if m in S.API_METHOD else "ANY"


def snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def plural(w):
    if w.endswith("y") and not w.endswith(("ay", "ey", "oy", "uy")):
        return w[:-1] + "ies"
    if w.endswith(("s", "x", "ch", "sh")):
        return w + "es"
    return w + "s"


# ---------------------------------------------------------------- repo context
class Repo:
    def __init__(self, root, rid):
        self.root = root
        self.rid = rid
        self.files = {}          # rel -> Src
        self.paths = []          # moi file (ke ca khong doc) -> dung cho file routing
        self.skipped = []
        self.skipped_large = []
        self.name_only = []
        self.manifests = {}
        self.deps = set()
        self.endpoints = []
        self.fe_routes = []
        self.fe_calls = []
        self.batch = []
        self.env_keys = {}
        self.class_idx = {}      # ten class -> [(rel,pos)]
        self.js_defs = {}        # ten ham -> [(rel,pos)]
        self.py_defs = {}
        self.schemas = {}        # ten schema zod/joi/yup -> (rel,pos,keys)
        self.models = {}         # model -> {table, locator, how}
        self.str_consts = {}     # ten hang so -> url
        self.base_url = ""       # axios.create({baseURL}) neu duy nhat va la path tuong doi

    def loc(self, src, pos_or_line, is_line=False):
        ln = pos_or_line if is_line else src.line(pos_or_line)
        return "%s:%s#L%d" % (self.rid, src.rel, ln)

    def find_class(self, name):
        hits = self.class_idx.get(name) or []
        return hits[0] if hits else None


def walk(repo):
    for dirpath, dirnames, filenames in os.walk(repo.root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, repo.root).replace(os.sep, "/")
            why = sensitive_reason(rel)
            if why:
                repo.skipped.append({"path": rel, "reason": why})
                if why == "name-keyword":
                    repo.name_only.append(rel)   # chi dung TEN cho file routing
                continue
            repo.paths.append(rel)
            if not (fn.endswith(TEXT_EXT) or fn in TEXT_NAMES or "cron" in fn.lower()):
                continue
            try:
                if os.path.getsize(fp) > MAX_BYTES:
                    repo.skipped_large.append(rel)
                    continue
                with open(fp, encoding="utf8", errors="ignore") as fh:
                    text = fh.read()
            except OSError:
                continue
            if "\x00" in text[:2000]:
                continue
            repo.files[rel] = Src(rel, text)


def is_test(rel):
    parts = rel.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or bool(TEST_FILE_RX.search(parts[-1]))


# ---------------------------------------------------------------- stack
FW_DEPS = {
    "express": ("BE", "Express"), "koa": ("BE", "Koa"), "@koa/router": ("BE", "Koa"),
    "fastify": ("BE", "Fastify"), "@nestjs/core": ("BE", "NestJS"), "hapi": ("BE", "Hapi"),
    "@hapi/hapi": ("BE", "Hapi"), "next": ("FULLSTACK", "Next.js"), "nuxt": ("FULLSTACK", "Nuxt"),
    "@sveltejs/kit": ("FULLSTACK", "SvelteKit"), "react": ("FE", "React"),
    "react-router-dom": ("FE", "React Router"), "react-router": ("FE", "React Router"),
    "vue": ("FE", "Vue"), "vue-router": ("FE", "vue-router"), "@angular/core": ("FE", "Angular"),
    "svelte": ("FE", "Svelte"), "axios": ("LIB", "axios"), "@prisma/client": ("LIB", "Prisma"),
    "prisma": ("LIB", "Prisma"), "typeorm": ("LIB", "TypeORM"), "sequelize": ("LIB", "Sequelize"),
    "mongoose": ("LIB", "Mongoose"), "node-cron": ("LIB", "node-cron"), "bull": ("LIB", "Bull"),
    "bullmq": ("LIB", "BullMQ"), "@nestjs/schedule": ("LIB", "Nest schedule"),
    "laravel/framework": ("BE", "Laravel"), "laravel/lumen-framework": ("BE", "Lumen"),
    "symfony/framework-bundle": ("BE", "Symfony"), "django": ("BE", "Django"),
    "djangorestframework": ("BE", "DRF"), "flask": ("BE", "Flask"), "fastapi": ("BE", "FastAPI"),
    "celery": ("LIB", "Celery"), "sqlalchemy": ("LIB", "SQLAlchemy"),
    "spring-boot": ("BE", "Spring Boot"), "spring-web": ("BE", "Spring"),
    "rails": ("BE", "Rails"), "whenever": ("LIB", "whenever"), "sidekiq": ("LIB", "Sidekiq"),
    "gin-gonic/gin": ("BE", "Gin"), "labstack/echo": ("BE", "Echo"), "go-chi/chi": ("BE", "chi"),
    "microsoft.aspnetcore": ("BE", "ASP.NET Core"),
}
MANIFESTS = {"package.json", "composer.json", "requirements.txt", "pom.xml", "build.gradle",
             "build.gradle.kts", "Gemfile", "go.mod", "pyproject.toml", "Pipfile"}


def read_stack(repo):
    for rel in repo.paths:
        name = os.path.basename(rel)
        if name not in MANIFESTS and not name.endswith(".csproj"):
            continue
        if rel.count("/") > 3:
            continue
        src = repo.files.get(rel)
        if src is None:
            fp = os.path.join(repo.root, rel)
            try:
                if os.path.getsize(fp) > MAX_BYTES:
                    continue
                src = Src(rel, open(fp, encoding="utf8", errors="ignore").read())
            except OSError:
                continue
        if name.endswith(".json"):
            try:
                d = json.loads(src.text)
            except ValueError:
                repo.manifests[rel] = "khong parse duoc"
                continue
            keep = {k: d.get(k) for k in ("name", "dependencies", "devDependencies", "require")
                    if k in d}
            repo.manifests[rel] = keep
            for k in ("dependencies", "devDependencies", "require", "require-dev"):
                repo.deps.update((d.get(k) or {}).keys())
        else:
            repo.manifests[rel] = src.text[:4000]
            low = src.text.lower()
            for dep in FW_DEPS:
                if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(dep), low):
                    repo.deps.add(dep)
            if "spring-boot" in low:
                repo.deps.add("spring-boot")
    fws = sorted({FW_DEPS[d][1] for d in repo.deps if d in FW_DEPS})
    return fws


def has(repo, *deps):
    return any(d in repo.deps for d in deps)


# ---------------------------------------------------------------- index pass
JS_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte")
CLASS_RX = re.compile(r"\bclass\s+([A-Za-z_]\w*)")
JS_DEF_RX = re.compile(
    r"(?:function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\()"
    r"|(?:(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::[^=\n]+)?=\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*(?::[^=]+)?=>|[A-Za-z_$][\w$]*\s*=>))"
    r"|(?:exports\.([A-Za-z_$][\w$]*)\s*=)"
    r"|(?:^[ \t]+(?:public\s+|private\s+|protected\s+|static\s+)*(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)\n]*\)\s*(?::[^{\n]+)?\{)", re.M)
JS_KW = {"if", "for", "while", "switch", "catch", "function", "return", "constructor", "else"}
SCHEMA_RX = re.compile(
    r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::[^=\n]+)?=\s*"
    r"(?:Joi|z|yup|Yup)\s*\.\s*object\s*\(\s*\{")
PY_DEF_RX = re.compile(r"^([ \t]*)(?:async\s+)?def\s+(\w+)\s*\(", re.M)
CONST_RX = re.compile(r"""(?:const|let|var|final\s+String|static\s+\w+)\s+([A-Za-z_$][\w$]*)\s*=\s*(['"`])((?:https?://|/)[^'"`\s]*)\2""")
OBJ_URL_RX = re.compile(r"""\b([A-Za-z_$][\w$]*)\s*:\s*(['"`])(/[^'"`\s]*)\2""")


def build_index(repo):
    seen_const = {}
    for rel, src in repo.files.items():
        t = src.text
        for m in CLASS_RX.finditer(t):
            repo.class_idx.setdefault(m.group(1), []).append((rel, m.start()))
        if src.ext in JS_EXT:
            for m in JS_DEF_RX.finditer(t):
                name = next((g for g in m.groups() if g), None)
                if name and name not in JS_KW:
                    repo.js_defs.setdefault(name, []).append((rel, m.start()))
            for m in SCHEMA_RX.finditer(t):
                repo.schemas[m.group(1)] = (rel, m.start(), top_keys(t, m.end() - 1))
        if src.ext == ".py":
            for m in PY_DEF_RX.finditer(t):
                repo.py_defs.setdefault(m.group(2), []).append((rel, m.start()))
        if src.ext in JS_EXT + (".java", ".kt", ".py", ".php"):
            for m in CONST_RX.finditer(t):
                seen_const.setdefault(m.group(1), set()).add(m.group(3))
            for m in OBJ_URL_RX.finditer(t):
                seen_const.setdefault(m.group(1), set()).add(m.group(3))
    repo.str_consts = {k: next(iter(v)) for k, v in seen_const.items() if len(v) == 1}
    bases = set()
    for src in repo.files.values():
        if src.ext in JS_EXT:
            bases.update(re.findall(r"""baseURL\s*:\s*['"`](/[^'"`]*)['"`]""", src.text))
    if len(bases) == 1:
        repo.base_url = bases.pop()


def resolve_js_import(repo, src, spec):
    if not spec.startswith((".", "@/", "~/")):
        return None
    if spec.startswith(("@/", "~/")):
        cands = ["src/" + spec[2:], spec[2:]]
    else:
        cands = [os.path.normpath(os.path.join(os.path.dirname(src.rel), spec)).replace(os.sep, "/")]
    for base in cands:
        for suf in ("", ".ts", ".js", ".tsx", ".jsx", ".mjs", ".cjs", ".vue",
                    "/index.ts", "/index.js", "/index.tsx", "/index.jsx"):
            if base + suf in repo.files:
                return base + suf
    return None


def py_block(t, pos):
    """Than ham/class Python tai pos (dong def/class) -> (start, end) theo thut dong."""
    ls = t.rfind("\n", 0, pos) + 1
    le = t.find("\n", ls)
    le = len(t) if le < 0 else le
    line = t[ls:le]
    indent = len(line) - len(line.lstrip())
    hm = re.compile(r":[ \t]*(#[^\n]*)?$", re.M).search(t, pos)
    scan = t.find("\n", hm.end()) if hm else le
    if scan < 0:
        return ls, len(t)
    for x in re.compile(r"\n([ \t]*)([^\s])").finditer(t, scan):
        if x.group(2) in ")#":
            continue
        if len(x.group(1)) <= indent:
            return ls, x.start()
    return ls, len(t)


def brace_body(t, pos, limit=20000):
    i = t.find("{", pos)
    if i < 0:
        return pos, pos
    j = match_close(t, i, "{", "}", limit=limit)
    return i, (j if j > 0 else min(len(t), i + 4000))


# ---------------------------------------------------------------- request hints
def hint(field, where, how, locator):
    return {"field": field, "in": where, "source": how, "locator": locator}


def js_body_hints(repo, src, start, end):
    t, out = src.text[start:end], []

    def add(f, w, how, off):
        out.append(hint(f, w, how, repo.loc(src, start + off)))
    for m in re.finditer(r"\b(?:req|request|ctx\.request|ctx)\.(body|query|params)\.([A-Za-z_$][\w$]*)", t):
        add(m.group(2), {"params": "path"}.get(m.group(1), m.group(1)), "req." + m.group(1), m.start())
    for m in re.finditer(r"\{([^{}]{1,300})\}\s*=\s*(?:await\s+)?(?:req|request|ctx\.request|ctx)\.(body|query|params|json\(\))", t):
        w = {"params": "path", "json()": "body"}.get(m.group(2), m.group(2))
        for name in re.findall(r"(?:^|,)\s*([A-Za-z_$][\w$]*)", m.group(1)):
            add(name, w, "destructure req." + m.group(2), m.start())
    for m in re.finditer(r"searchParams\.get\(\s*['\"](\w+)", t):
        add(m.group(1), "query", "searchParams", m.start())
    for m in re.finditer(r"\b(body|query|param|check|header)\(\s*['\"]([\w.\[\]*]+)['\"]", t):
        add(m.group(2), {"param": "path", "check": "body"}.get(m.group(1), m.group(1)),
            "express-validator", m.start())
    for m in re.finditer(r"\b(?:Joi|z|yup|Yup)\s*\.\s*object\s*\(\s*\{", t):
        for k in top_keys(src.text, start + m.end() - 1):
            add(k, "body", "inline schema", m.start())
    for m in re.finditer(r"\b([A-Za-z_$][\w$]*)\s*(?:\.(?:parse|safeParse|parseAsync|validate|validateAsync|validateSync)\(|\))", t):
        name = m.group(1)
        if name in repo.schemas:
            rel, pos, keys = repo.schemas[name]
            s2 = repo.files[rel]
            for k in keys:
                out.append(hint(k, "body", "schema " + name, repo.loc(s2, pos)))
    return out


def dto_fields(repo, cls):
    """Truong cua DTO/model (TS class-validator, Java, pydantic, PHP FormRequest)."""
    hit = repo.find_class(cls)
    if not hit:
        return [], None
    rel, pos = hit
    src = repo.files[rel]
    t = src.text
    if src.ext == ".py":
        s, e = py_block(t, pos)
        body = t[s:e]
        names = re.findall(r"^\s{2,8}(\w+)\s*:\s*[^=\n]", body, re.M)
    elif src.ext == ".php":
        i = t.find("function rules", pos)
        names = []
        if i > 0:
            j = t.find("[", i)
            if j > 0:
                names = top_keys(t, j, "[", "]")
    else:
        s, e = brace_body(t, pos)
        body = t[s + 1:e]
        if src.ext in (".java", ".kt", ".cs"):
            names = re.findall(r"(?:private|protected|public|val|var)\s+(?:final\s+)?(?:[\w<>\[\], ?]+\s+)?(\w+)\s*(?:[:=;]|\{\s*get)", body)
        else:
            names = re.findall(r"^\s*(?:readonly\s+|public\s+)?([A-Za-z_$][\w$]*)[?!]?\s*:\s*[^(\n]", body, re.M)
    names = [n for n in dict.fromkeys(names) if n not in ("return", "class", "static")]
    return names[:40], repo.loc(src, pos)


# ---------------------------------------------------------------- endpoint helpers
GENERIC_STEMS = {"index", "routes", "route", "router", "app", "server", "main", "api",
                 "urls", "web", "views", "controller", "controllers", "handler"}


def default_group(stem, path):
    if stem and stem.lower() not in GENERIC_STEMS and not stem.startswith("+"):
        return stem
    for seg in (path or "/").split("/"):
        if seg and not seg.startswith(":") and seg.lower() not in ("api", "v1", "v2", "v3"):
            return seg
    return "root"


def add_ep(repo, src, pos, method, path, handler, group, fw, auth=None, req=None,
           handler_loc=None, handler_file=None, prefix_key=None, line=None):
    ep = {"method": mapm(method), "path": path, "handler": handler or "UNKNOWN",
          "group": group, "framework": fw,
          "locator": repo.loc(src, line, True) if line else repo.loc(src, pos),
          "file": src.rel, "auth_hints": sorted(set(auth or [])),
          "request_hints": req or [],
          "handler_locator": handler_loc, "handler_file": handler_file or src.rel}
    if prefix_key:
        ep["_prefix_key"] = prefix_key
    repo.endpoints.append(ep)
    return ep


# ---------------------------------------------------------------- JS backends
BE_JS_RX = re.compile(r"""(?:require\(|from\s+)['"](?:express|koa|@koa/router|koa-router|fastify|@hapi/hapi|hapi|restify|hono)['"]|express\.Router\(|\bRouter\(\)|\(\s*req\s*,\s*res\b|\bctx\.body\b""")
EXPRESS_RX = re.compile(r"""\b([A-Za-z_$][\w$]*)\.(get|post|put|patch|delete|all|options|head)\s*\(\s*(['"`])(/[^'"`]*|\*)\3\s*,""")
CLIENT_RECV = {"axios", "http", "https", "fetch", "request", "superagent", "got", "ky",
               "client", "api", "instance", "this"}
MOUNT_RX = re.compile(r"""\.(?:use|register)\(\s*(['"`])(/[^'"`]*)\1\s*,\s*([^)]*?)\)""")
IMPORT_RX = re.compile(r"""(?:(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*require\(\s*['"]([^'"]+)['"]\s*\))|(?:import\s+([A-Za-z_$][\w$]*)\s*(?:,\s*\{[^}]*\})?\s+from\s+['"]([^'"]+)['"])""")


def is_be_js(src):
    return src.ext in JS_EXT and bool(BE_JS_RX.search(src.text))


def handler_info(repo, src, args):
    """args sau path -> (handler, middleware list, handler_locator, handler_file, (s,e,src))."""
    if not args:
        return "UNKNOWN", [], None, None, None
    last, lpos = args[-1]
    mids = [a for a, _ in args[:-1]]
    if re.match(r"^(async\s*)?(\(|function\b|[A-Za-z_$][\w$]*\s*=>)", last):
        s, e = brace_body(src.text, lpos)
        return "(inline)", mids, repo.loc(src, lpos), src.rel, (lpos, e, src)
    m = re.match(r"^([\w$.]+)", last)
    name = m.group(1) if m else last[:40]
    short = name.split(".")[-1]
    for rel, pos in repo.js_defs.get(short, []):
        s2 = repo.files[rel]
        s, e = brace_body(s2.text, pos)
        return name, mids, repo.loc(s2, pos), rel, (pos, e, s2)
    return name, mids, None, None, None


def scan_express(repo, src):
    t = src.text
    for m in EXPRESS_RX.finditer(t):
        recv = m.group(1)
        if recv in CLIENT_RECV:
            continue
        args, _ = call_args(t, m.start() + m.group(0).index("("))
        hargs = args[1:]
        handler, mids, hloc, hfile, body = handler_info(repo, src, hargs)
        auth = [x.split("(")[0][:40] for x in mids if AUTH_RX.search(x)]
        req = []
        for a, apos in hargs[:-1]:
            req += js_body_hints(repo, src, apos, apos + len(a))
        if body:
            s, e, bs = body
            req += js_body_hints(repo, bs, s, e)
        add_ep(repo, src, m.start(), m.group(2), m.group(4), handler,
               None, "Express/Koa", auth, req, hloc, hfile, prefix_key=src.rel)
    # router.route('/x').get(h).post(h)
    for m in re.finditer(r"""\.route\(\s*(['"`])(/[^'"`]*)\1\s*\)""", t):
        tail = t[m.end():m.end() + 600]
        for mm in re.finditer(r"^\s*\.(get|post|put|patch|delete|all)\s*\(", tail, re.M):
            add_ep(repo, src, m.start(), mm.group(1), m.group(2), "(chained)", None,
                   "Express", [], [], None, None, prefix_key=src.rel)
    # fastify.route({ method, url })
    for m in re.finditer(r"\.route\(\s*\{", t):
        close = match_close(t, m.end() - 1, "{", "}")
        obj = t[m.end():close if close > 0 else m.end() + 800]
        mu = re.search(r"""\burl\s*:\s*['"`]([^'"`]+)""", obj)
        mm = re.search(r"""\bmethod\s*:\s*\[?\s*['"](\w+)""", obj)
        if mu:
            hm = re.search(r"\bhandler\s*:\s*([\w$.]+)", obj)
            add_ep(repo, src, m.start(), mm.group(1) if mm else "ANY", mu.group(1),
                   hm.group(1) if hm else "(inline)", None, "Fastify",
                   ["preHandler"] if re.search(r"preHandler|onRequest", obj) else [],
                   js_body_hints(repo, src, m.start(), close if close > 0 else m.end() + 800),
                   prefix_key=src.rel)


def express_prefixes(repo):
    """app.use('/api', router) -> prefix theo file router (lan ngoai toi da 5 tang)."""
    parent = {}
    for rel, src in repo.files.items():
        if not is_be_js(src) and "fastify" not in src.text:
            continue
        imports = {}
        for m in IMPORT_RX.finditer(src.text):
            var, spec = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
            r = resolve_js_import(repo, src, spec)
            if r:
                imports[var] = r
        for m in MOUNT_RX.finditer(src.text):
            prefix, rest = m.group(2), m.group(3)
            target = None
            rq = re.search(r"""require\(\s*['"]([^'"]+)['"]""", rest)
            if rq:
                target = resolve_js_import(repo, src, rq.group(1))
            else:
                for var in reversed(re.findall(r"[A-Za-z_$][\w$]*", rest)):
                    if var in imports:
                        target = imports[var]
                        break
            if target and target != rel:
                parent[target] = (prefix, rel)

    def full(rel, depth=0):
        if rel not in parent or depth > 5:
            return ""
        p, par = parent[rel]
        return join_path(full(par, depth + 1), p)
    return {rel: full(rel) for rel in parent}


NEST_ROUTE_RX = re.compile(r"@(Get|Post|Put|Patch|Delete|All|Options|Head)\(\s*(?:(['\"`])([^'\"`]*)\2)?\s*\)")


def scan_nest(repo, src, global_prefix):
    t = src.text
    for cm in re.finditer(r"@Controller\(\s*(?:(['\"`])([^'\"`]*)\1|\{[^}]*?path\s*:\s*['\"]([^'\"]*)['\"][^}]*\})?\s*\)", t):
        prefix = cm.group(2) or cm.group(3) or ""
        km = re.compile(r"class\s+(\w+)").search(t, cm.end())
        if not km:
            continue
        cls = km.group(1)
        cls_auth = re.findall(r"@(UseGuards\([^)]*\)|Roles\([^)]*\)|ApiBearerAuth\(\))",
                              t[max(0, cm.start() - 400):km.start()])
        s, e = brace_body(t, km.end())
        prev_end = s
        for m in NEST_ROUTE_RX.finditer(t, s, e):
            nl = t.find("\n", m.end())
            hm = re.compile(r"^[ \t]*(?:public\s+|private\s+|protected\s+)?(?:async\s+)?([A-Za-z_]\w*)\s*\(",
                            re.M).search(t, nl if nl > 0 else m.end(), e)
            if not hm:
                continue
            name = hm.group(1)
            block = t[prev_end:hm.start()]
            auth = cls_auth + re.findall(r"@(UseGuards\([^)]*\)|Roles\([^)]*\)|Public\(\))", block)
            args, close = call_args(t, hm.end() - 1)
            req = []
            for a, apos in args:
                for pm in re.finditer(r"@(Query|Param|Body|Headers)\(\s*['\"](\w+)['\"]", a):
                    req.append(hint(pm.group(2), {"Param": "path", "Headers": "header"}.get(pm.group(1), pm.group(1).lower()),
                                    "@" + pm.group(1), repo.loc(src, apos)))
                bm = re.search(r"@(Body|Query)\(\s*\)\s*\w+\s*:\s*(\w+)", a)
                if bm:
                    fields, floc = dto_fields(repo, bm.group(2))
                    for f in fields:
                        req.append(hint(f, bm.group(1).lower(), "DTO " + bm.group(2), floc))
            bs, be = brace_body(t, close)
            prev_end = be
            path = join_path(global_prefix, prefix, m.group(3) or "")
            add_ep(repo, src, m.start(), m.group(1), path, "%s.%s" % (cls, name),
                   re.sub(r"Controller$", "", cls) or cls, "NestJS", auth, req,
                   repo.loc(src, hm.start()), src.rel)


def file_route_api(rel):
    """Next/Nuxt/SvelteKit API theo cau truc thu muc -> (path, method or None)."""
    m = re.search(r"(?:^|/)pages/(api/.+)\.(ts|js|mjs)$", rel)
    if m:
        return file_seg(m.group(1)), None
    m = re.search(r"(?:^|/)app/(.*?)/?route\.(ts|js|mjs)$", rel)
    if m:
        return file_seg(m.group(1)), None
    m = re.search(r"(?:^|/)server/(api|routes)/(.+)\.(ts|js|mjs)$", rel)
    if m:
        base = m.group(2)
        mm = re.search(r"\.(get|post|put|patch|delete)$", base)
        base = re.sub(r"\.(get|post|put|patch|delete)$", "", base)
        return file_seg(("api/" if m.group(1) == "api" else "") + base), (mm.group(1) if mm else None)
    m = re.search(r"(?:^|/)src/routes/(.*?)/?\+server\.(ts|js)$", rel)
    if m:
        return file_seg(m.group(1)), None
    return None, None


def file_seg(p):
    p = re.sub(r"(^|/)\([^)/]*\)", "", p)           # route group (x)
    p = re.sub(r"(^|/)@[^/]+", "", p)               # parallel slot
    p = re.sub(r"(^|/)(index|page|route)$", "", p)
    return norm_path(p)


def scan_file_api(repo, src):
    path, meth = file_route_api(src.rel)
    if path is None:
        return
    r = src.rel
    if ("pages/api/" in r or r.endswith(("route.ts", "route.js", "route.mjs"))) and not has(repo, "next"):
        if not r.endswith(("+server.ts", "+server.js")):
            return
    if "server/" in r and "pages/" not in r and "/app/" not in "/" + r and not has(repo, "nuxt", "nuxt3", "nitropack"):
        if not r.endswith(("+server.ts", "+server.js")):
            return
    if r.endswith(("+server.ts", "+server.js")) and not has(repo, "@sveltejs/kit"):
        return
    t = src.text
    methods = re.findall(r"export\s+(?:async\s+)?(?:function|const)\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b", t)
    if not methods:
        methods = sorted(set(re.findall(r"req\.method\s*===?\s*['\"](\w+)['\"]", t))) or [meth or "ANY"]
    auth = sorted(set(re.findall(r"\b(getServerSession|getSession|auth\(\)|withAuth|requireAuth|verifyToken|getToken|currentUser)\b", t)))
    for mth in dict.fromkeys(methods):
        mm = re.search(r"export\s+(?:async\s+)?(?:function|const)\s+%s\b" % mth, t)
        if mm:
            bs, be = brace_body(t, mm.end())
            req = js_body_hints(repo, src, mm.start(), be)
        else:
            req = js_body_hints(repo, src, 0, len(t))
        add_ep(repo, src, mm.start() if mm else 0, mth, path,
               mth if mm else "default", default_group(None, path.replace("/api", "", 1)),
               "file-routing", auth, req, None, src.rel, line=None if mm else 1)


# ---------------------------------------------------------------- PHP / Laravel
def scan_laravel(repo, src):
    t = src.text
    base = "api" if re.search(r"(^|/)routes/api\.php$", src.rel) else ""
    groups = []
    for gm in re.finditer(r"Route::[^;{]*?->group\(\s*(?:function\s*\([^)]*\)|fn\s*\(\))\s*(?:use\s*\([^)]*\)\s*)?\{", t):
        s = gm.end() - 1
        e = match_close(t, s, "{", "}")
        head = gm.group(0)
        groups.append((s, e if e > 0 else len(t), head))
    for gm in re.finditer(r"Route::group\(\s*\[([^\]]*)\]\s*,\s*function\s*\([^)]*\)\s*\{", t):
        s = gm.end() - 1
        e = match_close(t, s, "{", "}")
        groups.append((s, e if e > 0 else len(t), gm.group(0)))

    def ctx(pos):
        pre, mids, ctrl = [base], [], None
        for s, e, head in sorted(groups):
            if s < pos < e:
                p = re.search(r"prefix\(\s*['\"]([^'\"]*)|'prefix'\s*=>\s*['\"]([^'\"]*)", head)
                if p:
                    pre.append(p.group(1) or p.group(2))
                for mw in re.findall(r"middleware\(\s*\[?([^)\]]*)|'middleware'\s*=>\s*\[?([^\]]*?)\]?\s*[,\]]", head):
                    mids += [x.strip(" '\"") for x in "".join(mw).split(",") if x.strip(" '\"")]
                c = re.search(r"controller\(\s*([\w\\]+)::class", head)
                if c:
                    ctrl = c.group(1).split("\\")[-1]
        return pre, mids, ctrl

    for m in re.finditer(r"(?:Route::|\$router->|->)(get|post|put|patch|delete|any|options|match)\s*\(", t):
        st = max(t.rfind(";", 0, m.start()), t.rfind("{", 0, m.start()), t.rfind("}", 0, m.start())) + 1
        stmt_head = t[st:m.start()]
        if "Route" not in stmt_head and "$router" not in stmt_head and not m.group(0).startswith(("Route::", "$router")):
            continue
        args, close = call_args(t, m.end() - 1)
        if m.group(1) == "match":
            methods = re.findall(r"['\"](\w+)['\"]", args[0][0]) if args else ["ANY"]
            args = args[1:]
        else:
            methods = [m.group(1)]
        if not args or lit(args[0][0]) is None:
            continue
        path = lit(args[0][0])
        tail_end = t.find(";", close)
        stmt = t[st:tail_end if tail_end > 0 else close]
        pre, mids, gctrl = ctx(m.start())
        mids = mids + re.findall(r"middleware\(\s*\[?([^)\]]*)", stmt)
        auth = [x.strip(" '\"") for x in ",".join(mids).split(",") if AUTH_RX.search(x)]
        ctrl, meth = gctrl, None
        h = args[1][0] if len(args) > 1 else ""
        hm = re.search(r"\[\s*([\w\\]+)::class\s*,\s*['\"](\w+)['\"]", h) or \
            re.search(r"['\"]([\w\\]+)@(\w+)['\"]", h)
        if hm:
            ctrl, meth = hm.group(1).split("\\")[-1], hm.group(2)
        elif re.match(r"([\w\\]+)::class", h):
            ctrl, meth = re.match(r"([\w\\]+)::class", h).group(1).split("\\")[-1], "__invoke"
        elif lit(h) and gctrl:
            meth = lit(h)
        handler = "%s@%s" % (ctrl, meth) if ctrl and meth else ("(closure)" if "function" in h or "fn" in h else "UNKNOWN")
        hloc, hfile, req, cauth = laravel_controller(repo, ctrl, meth)
        for mt in methods:
            add_ep(repo, src, m.start(), mt, join_path(*(pre + [path])), handler,
                   ctrl or default_group(None, path), "Laravel", auth + cauth, req, hloc, hfile)
    for m in re.finditer(r"Route::(resource|apiResource)\(\s*['\"]([^'\"]+)['\"]\s*,\s*([\w\\]+)::class", t):
        ctrl = m.group(3).split("\\")[-1]
        stmt = t[m.start():t.find(";", m.start())]
        acts = [("index", "GET", ""), ("store", "POST", ""), ("show", "GET", "/:id"),
                ("update", "PUT", "/:id"), ("destroy", "DELETE", "/:id")]
        if m.group(1) == "resource":
            acts += [("create", "GET", "/create"), ("edit", "GET", "/:id/edit")]
        only = re.search(r"only\(\s*\[([^\]]*)\]", stmt)
        exc = re.search(r"except\(\s*\[([^\]]*)\]", stmt)
        pre, mids, _ = ctx(m.start())
        auth = [x for x in mids if AUTH_RX.search(x)]
        for act, mt, suf in acts:
            if only and act not in only.group(1):
                continue
            if exc and act in exc.group(1):
                continue
            hloc, hfile, req, cauth = laravel_controller(repo, ctrl, act)
            add_ep(repo, src, m.start(), mt, join_path(*(pre + [m.group(2) + suf])),
                   "%s@%s" % (ctrl, act), ctrl, "Laravel resource", auth + cauth, req, hloc, hfile)


def laravel_controller(repo, ctrl, meth):
    if not ctrl:
        return None, None, [], []
    hit = repo.find_class(ctrl)
    if not hit:
        return None, None, [], []
    rel, pos = hit
    src = repo.files[rel]
    t = src.text
    cauth = re.findall(r"\$this->middleware\(\s*['\"]([^'\"]+)", t)
    if not meth:
        return None, rel, [], cauth
    fm = re.search(r"function\s+%s\s*\(" % re.escape(meth), t)
    if not fm:
        return repo.loc(src, pos), rel, [], cauth
    args, close = call_args(t, fm.end() - 1)
    s, e = brace_body(t, close)
    body = t[s:e]
    req = []
    for a, apos in args:
        rm = re.match(r"([\w\\]+Request)\s+\$\w+", a)
        if rm and rm.group(1).split("\\")[-1] != "Request":
            fields, floc = dto_fields(repo, rm.group(1).split("\\")[-1])
            req += [hint(f, "body", "FormRequest " + rm.group(1), floc) for f in fields]
    for vm in re.finditer(r"(?:->validate|Validator::make)\(\s*(?:\$\w+(?:->all\(\))?\s*,\s*)?\[", body):
        for k in top_keys(t, s + vm.end() - 1, "[", "]"):
            req.append(hint(k, "body", "validate()", repo.loc(src, s + vm.start())))
    for im in re.finditer(r"\$request->(input|get|query|post|file|boolean|integer)\(\s*['\"]([\w.]+)", body):
        req.append(hint(im.group(2), "query" if im.group(1) == "query" else "body",
                        "$request->" + im.group(1), repo.loc(src, s + im.start())))
    return repo.loc(src, fm.start()), rel, req, cauth


# ---------------------------------------------------------------- Python
PY_ROUTE_RX = re.compile(r"^[ \t]*@(\w+)\.(get|post|put|patch|delete|route|api_route|api_view)\(", re.M)


def py_prefixes(repo):
    own, reg = {}, {}
    for rel, src in repo.files.items():
        if src.ext != ".py":
            continue
        for m in re.finditer(r"(\w+)\s*=\s*(?:APIRouter|Blueprint)\(([^)]*)\)", src.text):
            p = re.search(r"(?:url_)?prefix\s*=\s*['\"]([^'\"]*)", m.group(2))
            own[(rel, m.group(1))] = p.group(1) if p else ""
        for m in re.finditer(r"(?:include_router|register_blueprint)\(\s*([\w.]+)([^)]*)\)", src.text):
            p = re.search(r"(?:url_)?prefix\s*=\s*['\"]([^'\"]*)", m.group(2))
            if p:
                reg[m.group(1)] = p.group(1)
    return own, reg


def py_def_after(t, pos):
    m = re.compile(r"^[ \t]*(?:async\s+)?def\s+(\w+)\s*\(", re.M).search(t, pos)
    return m


def scan_py_routes(repo, src, own, reg):
    t = src.text
    for m in PY_ROUTE_RX.finditer(t):
        recv, kind = m.group(1), m.group(2)
        args, close = call_args(t, m.end() - 1, hash_comment=True)
        path = lit(args[0][0]) if args else None
        if path is None and args:
            pm = re.match(r"path\s*=\s*(.+)", args[0][0])
            path = lit(pm.group(1)) if pm else None
        if path is None or kind == "api_view":
            continue
        rest = " ".join(a for a, _ in args[1:])
        if kind in ("route", "api_route"):
            mm = re.search(r"methods\s*=\s*[\[(]([^\])]*)", rest)
            methods = re.findall(r"['\"](\w+)['\"]", mm.group(1)) if mm else ["GET"]
        else:
            methods = [kind]
        dm = py_def_after(t, close)
        if not dm:
            continue
        deco = t[m.start():dm.start()]
        auth = re.findall(r"@(\w*(?:login|auth|jwt|permission|role|token)\w*)", deco)
        auth += re.findall(r"Depends\(\s*(\w*(?:auth|user|token|current|admin)\w*)", deco + t[dm.start():dm.start() + 600])
        s, e = py_block(t, dm.start())
        body = t[s:e]
        req = py_req_hints(repo, src, s, body)
        sig_args, _ = call_args(t, dm.end() - 1, hash_comment=True)
        for a, apos in sig_args:
            am = re.match(r"(\w+)\s*:\s*([\w.\[\]]+)", a)
            if not am or am.group(1) in ("self", "request", "db", "session", "response", "background_tasks"):
                continue
            if "Depends" in a:
                continue
            typ = am.group(2)
            if typ[:1].isupper() and typ not in ("Optional", "List", "Request", "Response", "Session") and repo.find_class(typ):
                fields, floc = dto_fields(repo, typ)
                req += [hint(f, "body", "pydantic " + typ, floc) for f in fields]
            else:
                where = "path" if "{%s}" % am.group(1) in path else "query"
                req.append(hint(am.group(1), where, "signature", repo.loc(src, apos)))
        prefix = reg.get(recv, "") or next((reg[k] for k in reg if k.endswith("." + recv) and src.stem in k), "")
        full = join_path(prefix, own.get((src.rel, recv), ""), path)
        for mt in methods:
            add_ep(repo, src, m.start(), mt, full, dm.group(1),
                   default_group(src.stem, full), "Flask/FastAPI", auth, req,
                   repo.loc(src, dm.start()), src.rel)


def py_req_hints(repo, src, s, body):
    out = []
    for m in re.finditer(r"request\.(args|form|json|GET|POST|data|query_params|files|values)(?:\.get\(\s*|\[\s*)['\"](\w+)", body):
        where = "query" if m.group(1) in ("args", "GET", "query_params") else "body"
        out.append(hint(m.group(2), where, "request." + m.group(1), repo.loc(src, s + m.start())))
    return out


def scan_django(repo, src, prefix_of):
    t = src.text
    pre = prefix_of.get(src.rel, "")
    for m in re.finditer(r"\b(path|re_path|url)\(\s*", t):
        args, close = call_args(t, m.end() - 1, hash_comment=True)
        if len(args) < 2 or lit(args[0][0]) is None:
            continue
        h = args[1][0]
        if h.startswith("include("):
            continue
        p = lit(args[0][0])
        full = join_path(pre, p)
        hname = re.sub(r"\.as_view\(.*$", "", h).strip()
        short = hname.split(".")[-1]
        auth, req, hloc, hfile = django_view(repo, short)
        add_ep(repo, src, m.start(), "ANY", full, hname,
               default_group(None, full) if src.stem == "urls" else src.stem,
               "Django", auth, req, hloc, hfile)
    for m in re.finditer(r"\.register\(\s*r?['\"]([^'\"]*)['\"]\s*,\s*([\w.]+)", t):
        inc = re.search(r"path\(\s*r?['\"]([^'\"]*)['\"]\s*,\s*include\(\s*\w+\.urls", t)
        base = join_path(pre, inc.group(1) if inc else "", m.group(1))
        vs = m.group(2).split(".")[-1]
        auth, req, hloc, hfile = django_view(repo, vs)
        for suf in ("", "/:pk"):
            add_ep(repo, src, m.start(), "ANY", base + suf if base != "/" else suf or "/",
                   m.group(2), re.sub(r"ViewSet$", "", vs) or vs, "DRF router", auth, req, hloc, hfile)


def django_view(repo, name):
    hit = repo.find_class(name)
    if hit is None and name in repo.py_defs:
        hit = repo.py_defs[name][0]
    if not hit:
        return [], [], None, None
    rel, pos = hit
    src = repo.files[rel]
    t = src.text
    s, e = py_block(t, pos)
    deco_start = pos
    while True:
        prev = t.rfind("\n", 0, deco_start - 1)
        line = t[prev + 1:deco_start].strip()
        if line.startswith("@"):
            deco_start = prev + 1
        else:
            break
    block = t[deco_start:e]
    auth = re.findall(r"@(\w*(?:login_required|permission_required|auth\w*|user_passes_test))", block)
    auth += re.findall(r"permission_classes\s*=\s*[\[(]([^\])]*)", block)
    auth += re.findall(r"\b(LoginRequiredMixin|PermissionRequiredMixin)\b", t[pos:pos + 200])
    return auth, py_req_hints(repo, src, s, t[s:e]), repo.loc(src, pos), rel


def django_prefixes(repo):
    parent = {}
    for rel, src in repo.files.items():
        if not rel.endswith("urls.py"):
            continue
        for m in re.finditer(r"\b(?:path|re_path|url)\(\s*r?['\"]([^'\"]*)['\"]\s*,\s*include\(\s*['\"]([\w.]+)['\"]", src.text):
            mod = m.group(2).replace(".", "/") + ".py"
            target = next((r for r in repo.files if r == mod or r.endswith("/" + mod)), None)
            if target:
                parent[target] = (m.group(1), rel)

    def full(rel, depth=0):
        if rel not in parent or depth > 5:
            return ""
        p, par = parent[rel]
        return join_path(full(par, depth + 1), p)
    return {r: full(r) for r in parent}


# ---------------------------------------------------------------- Java/Kotlin/C# annotations
SPRING_M_RX = re.compile(r"@(Get|Post|Put|Patch|Delete|Request)Mapping\b(\s*\()?")


def ann_path(argtxt):
    if not argtxt:
        return ""
    m = re.search(r"(?:value|path)\s*=\s*\{?\s*\"([^\"]*)\"", argtxt) or re.search(r"\"([^\"]*)\"", argtxt)
    return m.group(1) if m else ""


def scan_spring(repo, src):
    t = src.text
    if not re.search(r"@(Rest)?Controller\b", t) or "@FeignClient" in t:
        return
    cm = re.search(r"\b(?:class|object)\s+(\w+)", t)
    if not cm:
        return
    cls = cm.group(1)
    head = t[:cm.start()]
    rm = list(re.finditer(r"@RequestMapping\s*\(([^)]*)\)", head))
    prefix = ann_path(rm[-1].group(1)) if rm else ""
    cls_auth = re.findall(r"@(PreAuthorize\([^)]*\)|Secured\([^)]*\)|RolesAllowed\([^)]*\))", head)
    prev_end = cm.end()
    for m in SPRING_M_RX.finditer(t, cm.end()):
        argtxt = ""
        end = m.end()
        if m.group(2):
            args, close = call_args(t, m.end() - 1)
            argtxt = ",".join(a for a, _ in args)
            end = close + 1
        kind = m.group(1)
        meth = kind
        if kind == "Request":
            mm = re.search(r"RequestMethod\.(\w+)", argtxt)
            meth = mm.group(1) if mm else "ANY"
        hm = re.compile(r"(?:fun\s+(\w+)\s*\(|(?:public|protected|private)?\s*[\w<>\[\], ?]+\s+(\w+)\s*\()").search(t, end)
        if not hm:
            continue
        name = hm.group(1) or hm.group(2)
        block = t[prev_end:hm.start()]
        auth = cls_auth + re.findall(r"@(PreAuthorize\([^)]*\)|Secured\([^)]*\)|RolesAllowed\([^)]*\))", block)
        sig, close = call_args(t, hm.end() - 1)
        req = []
        for a, apos in sig:
            for pm in re.finditer(r"@(RequestParam|PathVariable|RequestBody|RequestHeader)(?:\s*\(([^)]*)\))?\s+(?:final\s+)?(?:@\w+\s+)*([\w<>?,. \[\]]+?)\s+(\w+)\s*$", a.strip()):
                ann, aargs, typ, var = pm.groups()
                nm = re.search(r"\"([^\"]+)\"", aargs or "")
                where = {"RequestParam": "query", "PathVariable": "path", "RequestHeader": "header"}.get(ann, "body")
                if ann == "RequestBody":
                    fields, floc = dto_fields(repo, typ.split("<")[0].strip())
                    req += [hint(f, "body", "@RequestBody " + typ, floc) for f in fields] or \
                        [hint(var, "body", "@RequestBody", repo.loc(src, apos))]
                else:
                    req.append(hint(nm.group(1) if nm else var, where, "@" + ann, repo.loc(src, apos)))
        prev_end = brace_body(t, close)[1]
        add_ep(repo, src, m.start(), meth, join_path(prefix, ann_path(argtxt)),
               "%s.%s" % (cls, name), re.sub(r"Controller$", "", cls) or cls, "Spring",
               auth, req, repo.loc(src, hm.start()), src.rel)


def scan_aspnet(repo, src):
    t = src.text
    cm = re.search(r"class\s+(\w+)Controller\b", t)
    if not cm:
        return
    ctrl = cm.group(1)
    head = t[max(0, cm.start() - 600):cm.start()]
    rm = re.search(r"\[Route\(\s*\"([^\"]*)\"", head)
    prefix = (rm.group(1) if rm else "").replace("[controller]", ctrl.lower())
    cls_auth = re.findall(r"\[(Authorize[^\]]*)\]", head)
    prev_end = cm.end()
    for m in re.finditer(r"\[Http(Get|Post|Put|Patch|Delete)(?:\(\s*\"([^\"]*)\"[^)]*\))?\]", t):
        hm = re.compile(r"public\s+[^\n(]*?\s(\w+)\s*\(").search(t, m.end())
        if not hm:
            continue
        block = t[prev_end:hm.start()]
        sub = m.group(2) or (re.search(r"\[Route\(\s*\"([^\"]*)\"", block) or [None, ""])[1]
        auth = cls_auth + re.findall(r"\[(Authorize[^\]]*|AllowAnonymous)\]", block)
        sig, close = call_args(t, hm.end() - 1)
        req = []
        for a, apos in sig:
            pm = re.match(r"(?:\[From(Body|Query|Route|Header)[^\]]*\]\s*)?([\w<>?]+)\s+(\w+)", a)
            if pm:
                where = {"Body": "body", "Query": "query", "Route": "path", "Header": "header"}.get(pm.group(1) or "", "query")
                req.append(hint(pm.group(3), where, "param " + pm.group(2), repo.loc(src, apos)))
        prev_end = brace_body(t, close)[1]
        path = join_path(prefix, (sub or "").replace("[action]", hm.group(1)))
        add_ep(repo, src, m.start(), m.group(1), path, "%sController.%s" % (ctrl, hm.group(1)),
               ctrl, "ASP.NET", auth, req, repo.loc(src, hm.start()), src.rel)


def scan_go(repo, src):
    for m in re.finditer(r"\.(GET|POST|PUT|PATCH|DELETE|Get|Post|Put|Patch|Delete|HandleFunc|Handle)\(\s*\"(/[^\"]*)\"\s*,\s*([^)\n]*)", src.text):
        meth = m.group(1) if m.group(1) not in ("HandleFunc", "Handle") else "ANY"
        parts = [x.strip() for x in m.group(3).split(",") if x.strip()]
        h = parts[-1] if parts else "UNKNOWN"
        auth = [x for x in parts[:-1] if AUTH_RX.search(x)]
        add_ep(repo, src, m.start(), meth, norm_path(m.group(2)), h,
               default_group(src.stem, m.group(2)), "Go", auth, [], None, src.rel)


# ---------------------------------------------------------------- Rails
def scan_rails(repo, src):
    stack, out = [], []
    lines = src.text.split("\n")

    def prefix():
        return join_path(*[s for s in stack if s])
    RES = {"index": ("GET", ""), "create": ("POST", ""), "new": ("GET", "/new"),
           "show": ("GET", "/:id"), "edit": ("GET", "/:id/edit"), "update": ("PATCH", "/:id"),
           "destroy": ("DELETE", "/:id")}
    for i, raw in enumerate(lines, start=1):
        line = rb_strip_comment(raw).rstrip()
        s = line.strip()
        opens = bool(re.search(r"\bdo\s*(\|[^|]*\|)?\s*$", line))
        if re.match(r"^end\b", s):
            if stack:
                stack.pop()
            continue
        push = ""
        m = re.match(r"(resources|resource)\s+:(\w+)(.*)$", s)
        if m:
            single = m.group(1) == "resource"
            name = m.group(2)
            opts = m.group(3)
            acts = list(RES)
            om = re.search(r"only:\s*\[([^\]]*)\]|only:\s*:(\w+)", opts)
            em = re.search(r"except:\s*\[([^\]]*)\]", opts)
            if om:
                acts = [a for a in acts if a in (om.group(1) or om.group(2) or "")]
            if em:
                acts = [a for a in acts if a not in em.group(1)]
            ctrl = "/".join([x for x in stack if x and not x.startswith(":")] + [name])
            for a in acts:
                meth, suf = RES[a]
                if single:
                    suf = suf.replace("/:id", "")
                    if a == "index":
                        continue
                out.append((meth, join_path(prefix(), name + suf), "%s#%s" % (ctrl, a), name, i))
            push = name if single else name + "/:%s_id" % name.rstrip("s")
        m2 = re.match(r"(get|post|put|patch|delete|match)\s+['\"]([^'\"]+)['\"](.*)$", s)
        if m2:
            tm = re.search(r"(?:to:|=>)\s*['\"]([\w/]+#\w+)['\"]", m2.group(3))
            vm = re.search(r"via:\s*\[?:?(\w+)", m2.group(3))
            meth = m2.group(1) if m2.group(1) != "match" else (vm.group(1) if vm else "ANY")
            h = tm.group(1) if tm else "UNKNOWN"
            out.append((meth, join_path(prefix(), m2.group(2)), h, h.split("#")[0].split("/")[-1] if tm else default_group(None, m2.group(2)), i))
        m3 = re.match(r"root\s+(?:to:\s*)?['\"]([\w/]+#\w+)['\"]", s)
        if m3:
            out.append(("GET", prefix() or "/", m3.group(1), m3.group(1).split("#")[0], i))
        if opens:
            n = re.match(r"(?:namespace|scope)\s+(?:path:\s*)?['\":]?/?([\w/]+)", s)
            if s.startswith("member"):
                push = ":id"
            elif n and not re.match(r"scope\s+module:", s):
                push = n.group(1)
            stack.append(push)
    for meth, path, h, group, ln in out:
        auth, req, hloc, hfile = rails_controller(repo, h)
        add_ep(repo, src, 0, meth, path, h, group, "Rails", auth, req, hloc, hfile, line=ln)


def rb_strip_comment(line):
    q = None
    for i, ch in enumerate(line):
        if q:
            if ch == q:
                q = None
        elif ch in "'\"":
            q = ch
        elif ch == "#":
            return line[:i]
    return line


def rails_controller(repo, h):
    if "#" not in h:
        return [], [], None, None
    ctrl, act = h.split("#", 1)
    rel = "app/controllers/%s_controller.rb" % ctrl
    src = repo.files.get(rel)
    if not src:
        return [], [], None, None
    t = src.text
    auth = re.findall(r"before_action\s+:(\w*(?:auth|login|user|admin|require)\w*!?)", t)
    req = []
    for m in re.finditer(r"params\.require\(:(\w+)\)\.permit\(([^)]*)\)", t):
        for f in re.findall(r":(\w+)", m.group(2)):
            req.append(hint(f, "body", "strong params " + m.group(1), repo.loc(src, m.start())))
    dm = re.search(r"def\s+%s\b" % re.escape(act), t)
    if dm:
        end = t.find("\n  def ", dm.end())
        for m in re.finditer(r"params\[:(\w+)\]", t[dm.start():end if end > 0 else len(t)]):
            req.append(hint(m.group(1), "query", "params[]", repo.loc(src, dm.start() + m.start())))
    return auth, req, repo.loc(src, dm.start()) if dm else repo.loc(src, 0), rel


# ---------------------------------------------------------------- FE routes
ROUTER_FILE_RX = re.compile(r"react-router|createBrowserRouter|createHashRouter|createMemoryRouter|RouteObject|vue-router|createRouter|VueRouter|@angular/router|RouterModule|:\s*Routes\b")


def scan_fe_routes(repo, src):
    t = src.text
    if src.ext not in JS_EXT or is_be_js(src):
        return
    # JSX <Route>
    if "<Route" in t:
        stack = []
        for m in re.finditer(r"<Route\b|</Route\s*>", t):
            if m.group(0).startswith("</"):
                if stack:
                    stack.pop()
                continue
            j, d, q = m.end(), 0, None
            while j < len(t):
                ch = t[j]
                if q:
                    if ch == q:
                        q = None
                elif ch in "'\"`":
                    q = ch
                elif ch == "{":
                    d += 1
                elif ch == "}":
                    d -= 1
                elif ch == ">" and d == 0:
                    break
                j += 1
            tag = t[m.end():j]
            self_close = tag.rstrip().endswith("/")
            pm = re.search(r"""\bpath\s*=\s*(?:\{\s*)?['"`]([^'"`]*)['"`]""", tag)
            p = pm.group(1) if pm else ("" if re.search(r"\bindex\b", tag) else None)
            parent = next((x for x in reversed(stack) if x is not None), "")
            full = None
            if p is not None:
                full = p if p.startswith("/") or p == "*" else join_path(parent, p)
                cm = re.search(r"element\s*=\s*\{\s*<\s*([\w.]+)", tag) or \
                    re.search(r"(?:component|Component)\s*=\s*\{\s*([\w.]+)", tag)
                add_fe_route(repo, src, m.start(), full if full == "*" else norm_path(full),
                             cm.group(1) if cm else "UNKNOWN", "react-router")
            if not self_close:
                stack.append(full if full is not None else parent)
    # route objects (react-router / vue-router / angular)
    if ROUTER_FILE_RX.search(t):
        depth_at = bracket_depths(t)
        stack = []
        for m in re.finditer(r"""(?<![\w.])path\s*:\s*(['"`])([^'"`]*)\1""", t):
            if re.search(r"(push|replace|navigate|navigateTo|redirect)\s*\(\s*\{?[^;]{0,40}$", t[max(0, m.start() - 60):m.start()]):
                continue
            d = depth_at(m.start())
            while stack and stack[-1][0] >= d:
                stack.pop()
            parent = stack[-1][1] if stack else ""
            p = m.group(2)
            full = p if p.startswith("/") or p in ("*", "**") else join_path(parent, p)
            nxt = re.compile(r"(?<![\w.])path\s*:").search(t, m.end())
            win = t[m.end():min(nxt.start() if nxt else len(t), m.end() + 600)]
            cm = re.search(r"element\s*:\s*<\s*([\w.]+)", win) or \
                re.search(r"(?:component|Component|loadComponent)\s*:\s*(?:\(\)\s*=>\s*import\(\s*['\"]([^'\"]+)['\"]|([\w.]+))", win) or \
                re.search(r"lazy\s*:\s*\(\)\s*=>\s*import\(\s*['\"]([^'\"]+)", win) or \
                re.search(r"(redirect(?:To)?)\s*:", win) or re.search(r"loadChildren\s*:.*?import\(\s*['\"]([^'\"]+)", win)
            comp = next((g for g in cm.groups() if g), "UNKNOWN") if cm else "UNKNOWN"
            fw = "vue-router" if "vue-router" in t or src.ext == ".vue" else ("angular" if "@angular" in t else "router-object")
            norm = full if full in ("*", "**") else norm_path(full)
            add_fe_route(repo, src, m.start(), norm, comp, fw)
            stack.append((d, norm if norm not in ("*", "**") else parent))


def bracket_depths(t):
    marks, d, q, j = [], 0, None, 0
    while j < len(t):
        ch = t[j]
        if q:
            if ch == "\\":
                j += 2
                continue
            if ch == q:
                q = None
        elif ch in "'\"`":
            q = ch
        elif ch in "[{(":
            d += 1
            marks.append((j, d))
        elif ch in "]})":
            d -= 1
            marks.append((j, d))
        j += 1
    pos = [p for p, _ in marks]

    def at(i):
        k = bisect.bisect_left(pos, i) - 1
        return marks[k][1] if k >= 0 else 0
    return at


def add_fe_route(repo, src, pos, route, comp, fw, line=None):
    repo.fe_routes.append({"route": route, "component": comp, "file": src.rel if src else None,
                           "framework": fw,
                           "locator": "%s:%s#L%d" % (repo.rid, src.rel, line) if line else repo.loc(src, pos)})


def scan_file_pages(repo):
    nextjs, nuxt, kit = has(repo, "next"), has(repo, "nuxt", "nuxt3"), has(repo, "@sveltejs/kit")
    for rel in repo.paths + repo.name_only:
        r, fw = None, None
        if nextjs:
            m = re.search(r"(?:^|/)pages/(.+)\.(tsx|jsx|ts|js|mdx)$", rel)
            if m and not m.group(1).startswith("api/") and not os.path.basename(m.group(1)).startswith("_"):
                r, fw = file_seg(m.group(1)), "next-pages"
            m = re.search(r"(?:^|/)app/(.*?)/?page\.(tsx|jsx|ts|js|mdx)$", rel)
            if m:
                r, fw = file_seg(m.group(1)), "next-app"
        if nuxt and r is None:
            m = re.search(r"(?:^|/)pages/(.+)\.vue$", rel)
            if m:
                r, fw = file_seg(m.group(1)), "nuxt-pages"
        if kit and r is None:
            m = re.search(r"(?:^|/)src/routes/(.*?)/?\+page\.svelte$", rel)
            if m:
                r, fw = file_seg(m.group(1)), "sveltekit"
        if r is not None and "/components/" not in "/" + rel:
            repo.fe_routes.append({"route": r, "component": rel if rel not in repo.name_only else
                                   "(ten nhay cam - chua doc)", "file": rel, "framework": fw,
                                   "locator": "%s:%s#L1" % (repo.rid, rel)})


# ---------------------------------------------------------------- FE api calls
CALL_RX = re.compile(r"""(?<![\w$])([\w$][\w$.]*)\.(get|post|put|patch|delete|head)\s*(?:<[^>()]*>)?\s*\(""")
FETCH_RX = re.compile(r"""(?<![\w$.])(fetch|useFetch|\$fetch|ofetch|useSWR|useLazyFetch|ky)\s*(?:<[^>()]*>)?\s*\(""")
OBJCALL_RX = re.compile(r"""(?<![\w$.])(axios|request|\$\.ajax|http|api|client)\s*\(\s*\{""")
SKIP_RECV = {"router", "app", "server", "express", "fastify", "r", "Route", "map", "params",
             "searchParams", "headers", "cache", "localStorage", "sessionStorage", "cy",
             "formData", "store", "Cookies", "cookies", "url", "URL", "window.localStorage"}
ASSET_RX = re.compile(r"\.(png|jpe?g|svg|gif|webp|css|scss|ico|woff2?|ttf|map|html|md)$", re.I)


def url_from_arg(repo, a):
    a = (a or "").strip()
    if not a:
        return None, None
    note = None
    m = re.match(r"^`([^`]*)`", a)
    if m:
        u = m.group(1)
        u = re.sub(r"^\$\{[^}]*\}(?=/)", "", u)
        u = re.sub(r"\$\{([^}]*)\}", lambda x: ":" + (re.findall(r"[A-Za-z_]\w*", x.group(1)) or ["param"])[-1], u)
    else:
        parts = [p.strip() for p in re.split(r"\s\+\s", a)]
        u = ""
        for i, p in enumerate(parts):
            v = lit(p)
            if v is not None:
                u += v
            elif i == 0 and p in repo.str_consts:
                u += repo.str_consts[p]
                note = "const " + p
            elif i == 0 and "." in p and p.split(".")[-1] in repo.str_consts:
                u += repo.str_consts[p.split(".")[-1]]
                note = "const " + p
            elif i == 0 and re.match(r"^[A-Za-z_$][\w$.]*$", p) and re.search(r"(?i)base|api|host|url|endpoint", p):
                continue
            elif i > 0:
                u += ":" + (re.findall(r"[A-Za-z_]\w*", p) or ["param"])[-1]
            else:
                return None, None
    u = u.split("?")[0]
    if not u or not (u.startswith("/") or u.startswith("http")) or ASSET_RX.search(u):
        return None, None
    return u, note


def add_call(repo, src, pos, method, url, note, how):
    path = url
    if url.startswith("http"):
        m = re.match(r"https?://[^/]+(/.*)?$", url)
        path = (m.group(1) if m and m.group(1) else "/")
    elif how not in ("fetch", "useFetch", "$fetch", "ofetch", "useSWR", "useLazyFetch") and \
            repo.base_url and not url.startswith(repo.base_url.rstrip("/") + "/"):
        path = join_path(repo.base_url, url)
        note = ((note + "; ") if note else "") + "baseURL " + repo.base_url
    repo.fe_calls.append({"method": mapm(method), "url": url, "path": norm_path(path),
                          "file": src.rel, "locator": repo.loc(src, pos), "via": how,
                          "note": note or ""})


def scan_fe_calls(repo, src):
    if src.ext not in JS_EXT or is_be_js(src):
        return
    t = src.text
    local_maps = set(re.findall(r"\b([\w$]+)\s*=\s*new\s+(?:Map|WeakMap|Set|URLSearchParams|Headers|FormData)\b", t))
    for m in CALL_RX.finditer(t):
        recv = m.group(1)
        if recv in SKIP_RECV or recv.split(".")[-1] in SKIP_RECV or recv in local_maps:
            continue
        args, _ = call_args(t, m.end() - 1)
        if not args:
            continue
        u, note = url_from_arg(repo, args[0][0])
        if u:
            add_call(repo, src, m.start(), m.group(2), u, note, recv + "." + m.group(2))
    for m in FETCH_RX.finditer(t):
        args, _ = call_args(t, m.end() - 1)
        if not args:
            continue
        u, note = url_from_arg(repo, args[0][0])
        if not u:
            continue
        meth = "GET"
        if len(args) > 1:
            mm = re.search(r"method\s*:\s*['\"](\w+)", args[1][0])
            meth = mm.group(1) if mm else "GET"
        add_call(repo, src, m.start(), meth, u, note, m.group(1))
    for m in OBJCALL_RX.finditer(t):
        close = match_close(t, m.end() - 1, "{", "}")
        obj = t[m.end():close if close > 0 else m.end() + 600]
        um = re.search(r"\burl\s*:\s*([^,\n}]+)", obj)
        if not um:
            continue
        u, note = url_from_arg(repo, um.group(1))
        if u:
            mm = re.search(r"\b(?:method|type)\s*:\s*['\"](\w+)", obj)
            add_call(repo, src, m.start(), mm.group(1) if mm else "GET", u, note, m.group(1) + "({})")


# ---------------------------------------------------------------- batch / queue
def add_job(repo, src, pos, schedule, handler, kind, fw, line=None):
    repo.batch.append({"schedule": (schedule or "UNKNOWN").strip(), "handler": handler or "UNKNOWN",
                       "kind": kind, "framework": fw, "file": src.rel,
                       "locator": "%s:%s#L%d" % (repo.rid, src.rel, line) if line else repo.loc(src, pos)})


def next_name(t, pos, lang):
    if lang == "py":
        m = py_def_after(t, pos)
        return m.group(1) if m else "UNKNOWN"
    m = re.compile(r"(?:fun\s+(\w+)\s*\(|(?:public|protected|private|async)\s+[\w<>\[\], ?]*?\s*(\w+)\s*\(|^\s*(?:async\s+)?(\w+)\s*\()", re.M).search(t, pos)
    return next((g for g in m.groups() if g), "UNKNOWN") if m else "UNKNOWN"


def scan_batch(repo, src):
    t, rel, name = src.text, src.rel, os.path.basename(src.rel)
    lang = "py" if src.ext == ".py" else "x"
    if src.ext in JS_EXT:
        for m in re.finditer(r"""\bcron\.schedule\(\s*(['"`])([^'"`]+)\1\s*,\s*([^\n]*)""", t):
            h = re.match(r"([\w$.]+)\s*[,)]", m.group(3))
            add_job(repo, src, m.start(), m.group(2), h.group(1) if h else "(inline)", "BATCH", "node-cron")
        for m in re.finditer(r"""new\s+CronJob\(\s*(['"`])([^'"`]+)\1\s*,\s*([\w$.]+)?""", t):
            add_job(repo, src, m.start(), m.group(2), m.group(3) or "(inline)", "BATCH", "cron")
        for m in re.finditer(r"""(?:schedule\.scheduleJob|agenda\.every)\(\s*(['"`])([^'"`]+)\1\s*,\s*['"]?([\w$.\- ]+)?""", t):
            add_job(repo, src, m.start(), m.group(2), m.group(3) or "(inline)", "BATCH", "node-schedule/agenda")
        for m in re.finditer(r"""@(Cron|Interval|Timeout)\(\s*([^)]*)\)""", t):
            add_job(repo, src, m.start(), m.group(1) + " " + m.group(2).strip()[:60],
                    next_name(t, m.end(), lang), "BATCH", "@nestjs/schedule")
        for m in re.finditer(r"""repeat\s*:\s*\{\s*(?:cron|pattern)\s*:\s*['"]([^'"]+)""", t):
            add_job(repo, src, m.start(), m.group(1), "repeatable job", "BATCH", "bull")
        for m in re.finditer(r"""@Processor\(\s*['"]([^'"]+)""", t):
            add_job(repo, src, m.start(), "queue:" + m.group(1), next_name(t, m.end(), lang), "QUEUE", "Nest/Bull")
        for m in re.finditer(r"""new\s+Worker\(\s*['"]([^'"]+)['"]\s*,\s*([\w$.]+)?""", t):
            add_job(repo, src, m.start(), "queue:" + m.group(1), m.group(2) or "(inline)", "QUEUE", "BullMQ")
        for m in re.finditer(r"""\b(\w+)\.process\(\s*(?:['"]([^'"]+)['"]\s*,\s*)?(?:\d+\s*,\s*)?([\w$.]+)?""", t):
            if re.search(r"(?i)queue", m.group(1)):
                add_job(repo, src, m.start(), "queue:" + (m.group(2) or m.group(1)), m.group(3) or "(inline)", "QUEUE", "Bull")
        for m in re.finditer(r"""@(EventPattern|MessagePattern|RabbitSubscribe|SqsMessageHandler|OnEvent)\(\s*([^)]*)\)""", t):
            add_job(repo, src, m.start(), "event:" + m.group(2).strip()[:60], next_name(t, m.end(), lang), "QUEUE", m.group(1))
        for m in re.finditer(r"""\.subscribe\(\s*\{\s*topics?\s*:\s*\[?\s*['"]([^'"]+)""", t):
            add_job(repo, src, m.start(), "topic:" + m.group(1), "consumer", "QUEUE", "kafkajs")
        for m in re.finditer(r"""\.consume\(\s*['"]([^'"]+)""", t):
            add_job(repo, src, m.start(), "queue:" + m.group(1), "consumer", "QUEUE", "amqp")
    if src.ext == ".php":
        for m in re.finditer(r"(?:\$schedule->|Schedule::)(command|job|call|exec)\(", t):
            args, close = call_args(t, m.end() - 1)
            cmd = (lit(args[0][0]) or args[0][0][:60]) if args else "UNKNOWN"
            end = t.find(";", close)
            chain = re.findall(r"->(\w+)\(([^)]*)\)", t[close:end if end > 0 else close + 300])
            sched = " ".join("%s(%s)" % (k, v) if v else k for k, v in chain
                             if k not in ("withoutOverlapping", "onOneServer", "runInBackground",
                                          "timezone", "appendOutputTo", "sendOutputTo",
                                          "emailOutputTo", "description", "name")) or "UNKNOWN"
            add_job(repo, src, m.start(), sched, "%s %s" % (m.group(1), cmd), "BATCH", "Laravel scheduler")
        if re.search(r"implements\s+[^{]*ShouldQueue", t):
            cm = re.search(r"class\s+(\w+)", t)
            add_job(repo, src, cm.start() if cm else 0, "queue", cm.group(1) if cm else src.stem, "QUEUE", "Laravel queue")
    if src.ext in (".java", ".kt"):
        for m in re.finditer(r"@Scheduled\(([^)]*)\)", t):
            add_job(repo, src, m.start(), m.group(1).strip()[:80], next_name(t, m.end(), lang), "BATCH", "Spring @Scheduled")
        for m in re.finditer(r"@(KafkaListener|RabbitListener|JmsListener|SqsListener|StreamListener)\(([^)]*)\)", t):
            add_job(repo, src, m.start(), m.group(2).strip()[:80], next_name(t, m.end(), lang), "QUEUE", m.group(1))
    if src.ext == ".py":
        for m in re.finditer(r"""['"]task['"]\s*:\s*['"]([\w.]+)['"]""", t):
            win = t[max(0, m.start() - 300):m.end() + 300]
            sm = re.search(r"""['"]schedule['"]\s*:\s*([^\n]+?)\s*,?\s*$""", win, re.M)
            add_job(repo, src, m.start(), sm.group(1).rstrip(",") if sm else "UNKNOWN", m.group(1), "BATCH", "Celery beat")
        for m in re.finditer(r"add_periodic_task\(\s*([^,]+),\s*([\w.]+)", t):
            add_job(repo, src, m.start(), m.group(1), m.group(2), "BATCH", "Celery beat")
        for m in re.finditer(r"^[ \t]*@(?:\w+\.)?(shared_task|task|periodic_task|dramatiq\.actor|actor)\b(\([^)]*\))?", t, re.M):
            rm = re.search(r"run_every\s*=\s*([^,)]+)", m.group(2) or "")
            add_job(repo, src, m.start(), rm.group(1) if rm else "queue", next_name(t, m.end(), "py"),
                    "BATCH" if rm else "QUEUE", "Celery/dramatiq")
        for m in re.finditer(r"scheduler\.add_job\(\s*([\w.]+)\s*,\s*['\"](\w+)['\"]([^)]*)\)", t):
            add_job(repo, src, m.start(), m.group(2) + m.group(3)[:60], m.group(1), "BATCH", "APScheduler")
    if src.ext == ".rb":
        if rel.endswith("config/schedule.rb"):
            for m in re.finditer(r"every\s+([^\n]+?)\s+do\s*\n(.*?)\n\s*end", t, re.S):
                for c in re.finditer(r"(runner|rake|command)\s+['\"]([^'\"]+)", m.group(2)):
                    add_job(repo, src, m.start(), m.group(1), "%s %s" % (c.group(1), c.group(2)), "BATCH", "whenever")
        if re.search(r"include\s+Sidekiq::(Worker|Job)|<\s*(ApplicationJob|ActiveJob::Base)", t):
            cm = re.search(r"class\s+(\w+)", t)
            add_job(repo, src, cm.start() if cm else 0, "queue", cm.group(1) if cm else src.stem, "QUEUE", "Sidekiq/ActiveJob")
    if src.ext in (".yml", ".yaml"):
        if re.search(r"^kind:\s*CronJob", t, re.M):
            for m in re.finditer(r"^\s*schedule:\s*['\"]?([^'\"\n]+)", t, re.M):
                nm = re.search(r"^metadata:\s*\n\s+name:\s*(\S+)", t, re.M)
                add_job(repo, src, m.start(), m.group(1), nm.group(1) if nm else src.stem, "BATCH", "k8s CronJob")
        elif "/.github/workflows/" in "/" + rel:
            for m in re.finditer(r"-\s*cron:\s*['\"]([^'\"]+)", t):
                add_job(repo, src, m.start(), m.group(1), "workflow " + src.stem, "BATCH", "GitHub Actions")
        else:
            for m in re.finditer(r"^\s*cron:\s*['\"]?([^'\"\n]+)", t, re.M):
                win = t[max(0, m.start() - 200):m.end() + 200]
                cm = re.search(r"class:\s*['\"]?(\w[\w:]*)", win)
                add_job(repo, src, m.start(), m.group(1), cm.group(1) if cm else "UNKNOWN", "BATCH", "sidekiq-cron/yaml")
    if name == "crontab" or name.endswith(".cron") or "/cron.d/" in "/" + rel:
        for i, line in enumerate(t.split("\n"), start=1):
            m = re.match(r"^\s*((?:[\d*/,\-]+\s+){4}[\d*/,\-]+|@\w+)\s+(.+)$", line)
            if m and not line.strip().startswith("#"):
                cmd = re.sub(r"(?i)(password|token|secret|key)=\S+", r"\1=****", m.group(2).strip())
                add_job(repo, src, 0, m.group(1), cmd[:120], "BATCH", "crontab", line=i)


# ---------------------------------------------------------------- tables
SQL_RX = re.compile(r"""\b(?:FROM|INTO|UPDATE|JOIN)\s+[`"\[]?([A-Za-z_][\w]*)(?:[`"\]]?\.[`"\[]?([A-Za-z_]\w*))?""", re.I)
SQL_STOP = {"the", "a", "an", "this", "that", "which", "where", "select", "set", "values",
            "dual", "lateral", "unnest", "each", "my", "your", "our", "it", "to", "and", "or",
            "json", "jsonb", "table", "if", "not", "exists", "only", "unique", "with", "as", "on",
            "here", "there", "there", "now", "date", "now", "server", "client", "api"}


def build_models(repo):
    for rel, src in repo.files.items():
        t = src.text
        if src.ext == ".prisma":
            for m in re.finditer(r"^model\s+(\w+)\s*\{", t, re.M):
                s, e = brace_body(t, m.start())
                mm = re.search(r"@@map\(\s*\"([^\"]+)\"", t[s:e])
                repo.models[m.group(1)] = {"table": mm.group(1) if mm else m.group(1),
                                           "locator": repo.loc(src, m.start()),
                                           "how": "prisma @@map" if mm else "prisma model"}
            continue
        for rx, how in ((r"@Table\(\s*(?:name\s*=\s*)?['\"](\w+)['\"][^)]*\)[\s\S]{0,300}?class\s+(\w+)", "@Table"),
                        (r"@Entity\(\s*(?:['\"](\w+)['\"]|\{[^}]*name\s*:\s*['\"](\w+)['\"][^}]*\})?\s*\)[\s\S]{0,300}?class\s+(\w+)", "TypeORM @Entity"),
                        (r"@Entity\b(?!\()[\s\S]{0,300}?class\s+(\w+)", "JPA @Entity (inferred)")):
            for m in re.finditer(rx, t):
                g = m.groups()
                cls = g[-1]
                table = next((x for x in g[:-1] if x), None) or snake(cls)
                repo.models.setdefault(cls, {"table": table, "locator": repo.loc(src, m.start()), "how": how})
        if src.ext == ".php" and re.search(r"extends\s+(?:Model|Authenticatable|Pivot)\b", t):
            cm = re.search(r"class\s+(\w+)", t)
            tm = re.search(r"protected\s+\$table\s*=\s*['\"](\w+)", t)
            if cm:
                repo.models[cm.group(1)] = {"table": tm.group(1) if tm else plural(snake(cm.group(1))),
                                            "locator": repo.loc(src, (tm or cm).start()),
                                            "how": "$table" if tm else "eloquent default (inferred)"}
        if src.ext == ".py":
            for m in re.finditer(r"^class\s+(\w+)\((?:models\.Model|db\.Model|Model|Base|DeclarativeBase|SQLModel\s*,[^)]*table\s*=\s*True)\s*(?:,[^)]*)?\):", t, re.M):
                s, e = py_block(t, m.start())
                body = t[s:e]
                tm = re.search(r"(?:__tablename__|db_table)\s*=\s*['\"](\w+)", body)
                repo.models[m.group(1)] = {"table": tm.group(1) if tm else snake(m.group(1)),
                                           "locator": repo.loc(src, m.start()),
                                           "how": "__tablename__/db_table" if tm else "model default (inferred)"}
        if src.ext == ".rb" and re.search(r"<\s*(?:ApplicationRecord|ActiveRecord::Base)", t):
            cm = re.search(r"class\s+(\w+)", t)
            tm = re.search(r"self\.table_name\s*=\s*['\"](\w+)", t)
            if cm:
                repo.models[cm.group(1)] = {"table": tm.group(1) if tm else plural(snake(cm.group(1))),
                                            "locator": repo.loc(src, cm.start()),
                                            "how": "table_name" if tm else "AR default (inferred)"}
        if src.ext in JS_EXT:
            for m in re.finditer(r"(?:sequelize\.define|\.init)\(\s*['\"]?(\w+)['\"]?[\s\S]{0,800}?tableName\s*:\s*['\"](\w+)", t):
                repo.models.setdefault(m.group(1), {"table": m.group(2), "locator": repo.loc(src, m.start()), "how": "tableName"})
            for m in re.finditer(r"mongoose\.model\(\s*['\"](\w+)['\"]", t):
                repo.models.setdefault(m.group(1), {"table": plural(m.group(1).lower()), "locator": repo.loc(src, m.start()), "how": "mongoose (inferred)"})


def file_imports(repo, src):
    out = set()
    t = src.text
    if src.ext in JS_EXT:
        for m in re.finditer(r"""(?:from\s+|require\(\s*|import\(\s*)['"](\.[^'"]+|@/[^'"]+|~/[^'"]+)['"]""", t):
            r = resolve_js_import(repo, src, m.group(1))
            if r:
                out.add(r)
    elif src.ext in (".php", ".java", ".kt", ".cs"):
        for m in re.finditer(r"^(?:use|import)\s+([\w\\.]+)", t, re.M):
            hit = repo.find_class(re.split(r"[\\.]", m.group(1))[-1])
            if hit:
                out.add(hit[0])
        for m in re.finditer(r"(?:private|protected|public|readonly)\s+(?:readonly\s+)?(?:\w+\s*:\s*)?([A-Z]\w+(?:Service|Repository|Repo|Dao|Model|Store))\b", t):
            hit = repo.find_class(m.group(1))
            if hit:
                out.add(hit[0])
    elif src.ext == ".py":
        for m in re.finditer(r"^\s*from\s+(\.*[\w.]*)\s+import", t, re.M):
            mod = m.group(1)
            if mod.startswith("."):
                base = os.path.dirname(src.rel)
                for _ in range(len(mod) - len(mod.lstrip(".")) - 1):
                    base = os.path.dirname(base)
                cand = os.path.join(base, mod.lstrip(".").replace(".", "/")).replace(os.sep, "/")
            else:
                cand = mod.replace(".", "/")
            for c in (cand + ".py", cand + "/__init__.py"):
                hit = next((r for r in repo.files if r == c or r.endswith("/" + c)), None)
                if hit:
                    out.add(hit)
    out.discard(src.rel)
    return sorted(out)


def build_table_refs(repo):
    names = sorted(repo.models, key=len, reverse=True)
    model_rx = None
    if names:
        alt = "|".join(re.escape(n) for n in names)
        model_rx = re.compile(r"\b(%s)\b(?:::|\.objects\b|\.(?:where|find\w*|create\w*|update\w*|upsert|destroy|delete\w*|all|count\w*|aggregate|query|insert\w*|first\w*|paginate|joins|with|save|select)\b)|(?:getRepository|InjectRepository|Repository<|getCustomRepository)\(?\s*(%s)\b" % (alt, alt))
    lower_map = {n[:1].lower() + n[1:]: n for n in names}
    files = {}
    for rel, src in repo.files.items():
        if src.ext not in JS_EXT + (".py", ".php", ".rb", ".java", ".kt", ".go", ".cs") or is_test(rel):
            continue
        t = src.text
        refs = []
        for m in SQL_RX.finditer(t):
            ls = t.rfind("\n", 0, m.start()) + 1
            le = t.find("\n", m.end())
            line = t[ls:le if le > 0 else len(t)]
            low = line.strip().lower()
            if re.match(r"(import|from|export|package|using|use|require|//|#|\*|/\*)", low) and \
                    not re.search(r"\b(select|insert|update|delete)\b", low):
                continue
            kw = m.group(0).split()[0]
            sqlish = re.search(r"(?i)\bselect\b.+\bfrom\b|\binsert\s+into\b|\bupdate\s+\S+\s+set\b|"
                               r"\bdelete\s+from\b|\bjoin\b.+\bon\b", line)
            if not (kw.isupper() or sqlish):
                continue
            if not re.search(r"['\"`]", t[max(0, m.start() - 400):m.start()] + line):
                continue
            tb = m.group(2) or m.group(1)
            if tb.lower() in SQL_STOP or len(tb) < 2:
                continue
            refs.append({"table": tb, "locator": repo.loc(src, m.start()), "how": "sql"})
        if model_rx:
            for m in model_rx.finditer(t):
                n = m.group(1) or m.group(2)
                if n in repo.models and not repo.models[n]["locator"].startswith("%s:%s#" % (repo.rid, rel)):
                    refs.append({"table": repo.models[n]["table"], "locator": repo.loc(src, m.start()),
                                 "how": "orm " + n})
        for m in re.finditer(r"\bprisma\.(\w+)\.(?:find\w*|create\w*|update\w*|upsert|delete\w*|count|aggregate|groupBy)\b", t):
            n = lower_map.get(m.group(1))
            if n:
                refs.append({"table": repo.models[n]["table"], "locator": repo.loc(src, m.start()), "how": "prisma." + m.group(1)})
        for m in re.finditer(r"""(?:DB::table|knex|\.table|\.from)\(\s*['"](\w+)['"]""", t):
            refs.append({"table": m.group(1), "locator": repo.loc(src, m.start()), "how": "query-builder"})
        for name, md in repo.models.items():
            if md["locator"].startswith("%s:%s#" % (repo.rid, rel)):
                refs.append({"table": md["table"], "locator": md["locator"], "how": "model def (" + md["how"] + ")"})
        seen, uniq = set(), []
        for r in refs:
            k = (r["table"], r["how"])
            if k not in seen:
                seen.add(k)
                uniq.append(r)
        imps = file_imports(repo, src)
        if uniq or imps:
            files[rel] = {"tables": uniq, "imports": imps}
    return {"note": "GOI Y suy luan tu regex (sql/orm) — khong phai bang chung Confirmed",
            "models": repo.models, "files": files}


# ---------------------------------------------------------------- integrations
INTEGRATION_HINTS = {
    "stripe": "Payment", "paypal": "Payment", "gmo": "Payment", "braintree": "Payment",
    "sendgrid": "Email", "nodemailer": "Email", "ses": "Email", "mailgun": "Email",
    "firebase": "Push/Auth", "fcm": "Push", "onesignal": "Push", "s3": "Storage",
    "cloudinary": "Storage", "gcs": "Storage", "redis": "Cache", "elasticsearch": "Search",
    "algolia": "Search", "twilio": "SMS", "slack": "Chat", "line": "Chat",
    "oauth": "Auth", "saml": "Auth", "keycloak": "Auth", "auth0": "Auth", "cognito": "Auth",
    "sentry": "Monitoring", "datadog": "Monitoring", "kafka": "Queue", "rabbitmq": "Queue",
    "amqp": "Queue", "sqs": "Queue", "pusher": "Realtime", "socket.io": "Realtime",
    "google-analytics": "Analytics", "openai": "AI", "anthropic": "AI",
}
IMPORT_LINE_RX = re.compile(r"""^\s*(?:import|from|use|require|using)\b.*$|require\(\s*['"][^'"]+['"]\s*\)""", re.M)
HOST_RX = re.compile(r"https?://([a-z0-9][a-z0-9.-]*\.[a-z]{2,})(?![\w@:.-]*@)", re.I)
HOST_SKIP = re.compile(r"(?i)(localhost|example\.(com|org|jp)|127\.0\.0\.1|w3\.org|schema\.org|"
                       r"github\.com|npmjs|googleapis\.com/css|fonts\.|cdn|reactjs|vuejs|angular\.io|"
                       r"mozilla\.org|apache\.org|json-schema|xmlns|opensource|spdx|eslint)")


def scan_integrations(repo):
    hints = {}
    hay = [("manifest", " ".join(sorted(repo.deps)).lower(), None)]
    for rel, src in repo.files.items():
        if is_test(rel) or src.ext in (".json", ".txt", ".toml", ".xml", ".gradle", ".mod"):
            continue
        for m in IMPORT_LINE_RX.finditer(src.text):
            hay.append((rel, m.group(0).lower(), (src, m.start())))
    for key, kind in INTEGRATION_HINTS.items():
        rx = re.compile(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(key))
        for rel, txt, where in hay:
            if rx.search(txt):
                h = hints.setdefault(key, {"kind": kind, "hits": []})
                if len(h["hits"]) < 3:
                    h["hits"].append("manifest" if where is None else repo.loc(*where))
    hosts = {}
    for rel, src in repo.files.items():
        if is_test(rel) or src.ext in (".json", ".lock", ".xml", ".txt"):
            continue
        for m in HOST_RX.finditer(src.text):
            h = m.group(1).lower()
            if HOST_SKIP.search(h):
                continue
            hosts.setdefault(h, [])
            if len(hosts[h]) < 3:
                hosts[h].append(repo.loc(src, m.start()))
    env = {}
    for rel in repo.paths:
        if os.path.basename(rel).lower() in ENV_OK:
            try:
                with open(os.path.join(repo.root, rel), encoding="utf8", errors="ignore") as fh:
                    keys = re.findall(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_.]*)\s*=", fh.read(), re.M)
                env[rel] = sorted(set(keys))
            except OSError:
                pass
    hints["_env_keys"] = env
    hints["_external_hosts"] = hosts
    return hints


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--repo-id", required=True)
    ap.add_argument("--kind", default="AUTO", choices=["AUTO", "FE", "BE", "FULLSTACK"])
    ap.add_argument("--out", required=True, help="<ver>/_internal")
    ap.add_argument("--ev-start", type=int, default=1)
    ap.add_argument("--api-start", type=int, default=1)
    a = ap.parse_args()

    if not re.match(S.ID_PATTERNS["11_Repo"][1], a.repo_id):
        print("--repo-id phai dang REPO-01", file=sys.stderr)
        return 1
    if not os.path.isdir(a.repo):
        print("Khong thay repo: %s" % a.repo, file=sys.stderr)
        return 1
    root = os.path.abspath(a.repo)
    outdir = os.path.abspath(os.path.join(a.out, "recon", "code", a.repo_id))
    if outdir.startswith(root + os.sep):
        print("--out nam trong repo dang phan tich -> tu choi (chi doc)", file=sys.stderr)
        return 1
    os.makedirs(outdir, exist_ok=True)

    repo = Repo(root, a.repo_id)
    walk(repo)
    fws = read_stack(repo)
    build_index(repo)
    build_models(repo)

    gprefix = ""
    for src in repo.files.values():
        m = re.search(r"setGlobalPrefix\(\s*['\"]([^'\"]+)", src.text)
        if m:
            gprefix = m.group(1)
    own, reg = py_prefixes(repo)
    dj_pre = django_prefixes(repo)

    for rel, src in sorted(repo.files.items()):
        if is_test(rel):
            continue
        e = src.ext
        try:
            if e in JS_EXT:
                if is_be_js(src) or "fastify" in src.text:
                    scan_express(repo, src)
                if "@Controller(" in src.text:
                    scan_nest(repo, src, gprefix)
                scan_file_api(repo, src)
                scan_fe_routes(repo, src)
                scan_fe_calls(repo, src)
            elif e == ".php":
                if rel.startswith("routes/") or "/routes/" in rel:
                    scan_laravel(repo, src)
            elif e == ".py":
                scan_py_routes(repo, src, own, reg)
                if rel.endswith("urls.py"):
                    scan_django(repo, src, dj_pre)
            elif e in (".java", ".kt"):
                scan_spring(repo, src)
            elif e == ".cs":
                scan_aspnet(repo, src)
            elif e == ".go":
                scan_go(repo, src)
            elif rel.endswith("config/routes.rb"):
                scan_rails(repo, src)
            scan_batch(repo, src)
        except Exception as ex:  # 1 file loi khong lam hong ca lan quet
            print("canh bao: bo qua %s (%s)" % (rel, ex.__class__.__name__), file=sys.stderr)
    scan_file_pages(repo)

    # prefix express
    epre = express_prefixes(repo)
    for ep in repo.endpoints:
        k = ep.pop("_prefix_key", None)
        if k is not None:
            ep["path"] = join_path(epre.get(k, ""), ep["path"])
        ep["path"] = norm_path(ep["path"])
        if not ep.get("group"):
            ep["group"] = default_group(os.path.splitext(os.path.basename(ep["file"]))[0], ep["path"])
        seen, rq = set(), []
        for h in ep["request_hints"]:
            key = (h["field"], h["in"])
            if key not in seen and h["field"]:
                seen.add(key)
                rq.append(h)
        for pm in re.findall(r":(\w+)", ep["path"]):
            if (pm, "path") not in seen:
                rq.append(hint(pm, "path", "route param", ep["locator"]))
        ep["request_hints"] = rq[:60]

    def dedupe(items, key):
        seen, out = set(), []
        for x in items:
            k = key(x)
            if k not in seen:
                seen.add(k)
                out.append(x)
        return out
    repo.endpoints = dedupe(repo.endpoints, lambda x: (x["method"], x["path"], x["locator"]))
    repo.fe_routes = dedupe(repo.fe_routes, lambda x: (x["route"], x["locator"]))
    repo.fe_calls = dedupe(repo.fe_calls, lambda x: (x["method"], x["url"], x["locator"]))
    repo.batch = dedupe(repo.batch, lambda x: (x["schedule"], x["handler"], x["locator"]))

    # kind
    be = bool(repo.endpoints) or any(FW_DEPS.get(d, ("",))[0] == "BE" for d in repo.deps)
    fe = bool(repo.fe_routes) or any(FW_DEPS.get(d, ("",))[0] == "FE" for d in repo.deps)
    if any(FW_DEPS.get(d, ("",))[0] == "FULLSTACK" for d in repo.deps):
        fe = True
        be = be or any(ep["framework"] == "file-routing" for ep in repo.endpoints)
    kind = a.kind
    if kind == "AUTO":
        kind = "FULLSTACK" if (fe and be) else "BE" if be else "FE" if fe else \
            "BATCH" if repo.batch else "OTHER"

    # ids
    ev = a.ev_start
    api = a.api_start
    ev_rows, api_rows = [], []

    def new_ev(locator, note):
        nonlocal ev
        eid = "EV-%04d" % ev
        ev += 1
        ev_rows.append({"EV ID": eid, "Type": "code-ref", "Locator": locator, "Captured At": "",
                        "Actor/Role": "", "Artifact": "", "Note": note[:120]})
        return eid

    for ep in repo.endpoints:
        ep["ev"] = new_ev(ep["locator"], "BE %s %s (scan-repo)" % (ep["method"], ep["path"]))
        ep["api_id"] = "API-%03d" % api
        api += 1
        k = "WEBHOOK" if re.search(r"(?i)webhook", ep["path"]) else "API"
        fields = ", ".join(dict.fromkeys(h["field"] for h in ep["request_hints"]))[:200]
        api_rows.append({"API ID": ep["api_id"], "Group": ep["group"], "Kind": k,
                         "Method": ep["method"], "Path / Schedule": ep["path"],
                         "Summary": S.UNKNOWN,
                         "Auth": "; ".join(ep["auth_hints"])[:120] or S.UNKNOWN,
                         "Handler": ep["handler_locator"] or ep["locator"], "Repo": a.repo_id,
                         "Called By Screens": S.UNKNOWN, "Related Tables": S.UNKNOWN,
                         "Evidence": ep["ev"], "Status": "To verify", "Open Q": "—",
                         "Note": ("handler %s" % ep["handler"]) + ("; req: " + fields if fields else "")})
    for r in repo.fe_routes:
        r["ev"] = new_ev(r["locator"], "FE route %s (%s)" % (r["route"], r["framework"]))
    for c in repo.fe_calls:
        c["ev"] = new_ev(c["locator"], "FE call %s %s" % (c["method"], c["url"]))
    for j in repo.batch:
        j["ev"] = new_ev(j["locator"], "%s %s -> %s" % (j["kind"], j["schedule"], j["handler"]))
        j["api_id"] = "API-%03d" % api
        api += 1
        api_rows.append({"API ID": j["api_id"], "Group": "Batch" if j["kind"] == "BATCH" else "Queue",
                         "Kind": j["kind"], "Method": "CRON" if j["kind"] == "BATCH" else "EVENT",
                         "Path / Schedule": j["schedule"], "Summary": S.UNKNOWN, "Auth": "—",
                         "Handler": j["locator"], "Repo": a.repo_id,
                         "Called By Screens": S.UNKNOWN, "Related Tables": S.UNKNOWN,
                         "Evidence": j["ev"], "Status": "To verify", "Open Q": "—",
                         "Note": "%s (%s)" % (j["handler"], j["framework"])[:200]})

    def W(name, obj):
        with open(os.path.join(outdir, name), "w", encoding="utf8") as fh:
            if isinstance(obj, str):
                fh.write(obj)
            else:
                json.dump(obj, fh, indent=2, ensure_ascii=False)

    def C(name, cols, rows):
        with open(os.path.join(outdir, name), "w", encoding="utf8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow(r)

    stack = {"repo_id": a.repo_id, "kind": kind, "kind_arg": a.kind, "frameworks": fws,
             "manifests": repo.manifests}
    routes = sorted(set([e["path"] for e in repo.endpoints] + [r["route"] for r in repo.fe_routes]))
    W("stack.json", json.dumps(stack, indent=2, ensure_ascii=False)[:300000])
    W("routes.txt", "\n".join(routes) + ("\n" if routes else ""))
    W("routes.json", [{"route": e["path"], "method": e["method"], "locator": e["locator"]} for e in repo.endpoints] +
      [{"route": r["route"], "method": "PAGE", "locator": r["locator"]} for r in repo.fe_routes])
    W("api.json", repo.endpoints)
    W("fe-routes.json", repo.fe_routes)
    W("fe-api-calls.json", repo.fe_calls)
    W("batch.json", repo.batch)
    W("integrations.json", scan_integrations(repo))
    W("table-refs.json", build_table_refs(repo))
    W("skipped-sensitive.json", {"note": "Chi ten file — KHONG doc noi dung (rules/SECURITY.md)",
                                 "sensitive": repo.skipped, "too_large": repo.skipped_large})
    C("evidence.csv", S.SHEETS["05_Evidence"], ev_rows)
    C("api-seed.csv", S.SHEETS["07_API"], api_rows)

    print(json.dumps({
        "repo_id": a.repo_id, "kind": kind, "frameworks": fws,
        "counts": {"endpoints": len(repo.endpoints), "fe_routes": len(repo.fe_routes),
                   "fe_api_calls": len(repo.fe_calls), "batch": len(repo.batch),
                   "evidence_rows": len(ev_rows), "api_rows": len(api_rows),
                   "models": len(repo.models), "files_read": len(repo.files),
                   "skipped_sensitive": len(repo.skipped), "skipped_large": len(repo.skipped_large)},
        "next_ev": ev, "next_api": api, "out": outdir}, indent=2, ensure_ascii=False))
    if repo.skipped:
        print("LUU Y: %d file nhay cam bi bo qua (chi ghi ten) -> skipped-sensitive.json"
              % len(repo.skipped), file=sys.stderr)
    print("LUU Y: day la GOI Y tu code. Status='To verify' cho toi khi doi chieu UI/DB.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
